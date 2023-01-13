from dynacoolclient import DynacoolClient
from MultiVuDataFile import MultiVuDataFile as mvd
from pymeasure.instruments.srs import SR830
import datetime
import numpy as np
import os
import time

class MeasurementSetup():
    def __init__(self, main_folder, sample_name, *, ppms_address=(), lockins=dict()):
        self.sample_folder = os.path.join(main_folder, sample_name)
        os.makedirs(self.sample_folder, exist_ok=True)
        
        if lockins != dict():
            self.lockins = lockins
        if len(ppms_address) > 0:
            self.ppms_address = ppms_address
        
        self.temp_col = 'Temperature (K)'
        self.field_col = 'Field (Oe)'
        self.x_col = 'X (V)'
        self.y_col = 'Y (V)'
        self.resis_col = 'Resistance (Ohms)'
        self.OUTPUT_COLUMNS = [self.temp_col, self.field_col,
                               self.x_col, self.y_col, self.resis_col]
        
    def connectInstruments(self):
        if hasattr(self, 'lockins'):
            self.lockin_xx = SR830(self.lockins['xx'])
            self.lockin_xy = SR830(self.lockins['xy'])
        if hasattr(self, 'ppms_address'):
            self.ppms = DynacoolClient(self.ppms_address['host'], self.ppms_address['port'])
            self.ppms.open()
        
    @staticmethod    
    def generateFilename(template, params):
        now = datetime.datetime.now()
        current_time = f'{now.year}-{now.month}-{now.day} {now.hour}-{now.minute}-{now.second}'
        temp_name = template.format(**params)
        
        filename = temp_name[:-4] + '_{}'.format(current_time) + temp_name[-4:]
        return filename
        
    @staticmethod
    def getLockinConfig(lockin):
        config = dict()
        config['Sine Out (V)'] = str(lockin.sine_voltage)
        config['Frequency (Hz)'] = str(lockin.frequency)
        config['Phase (Deg)'] = str(lockin.phase)
        config['Sensitivity (V)'] = str(lockin.sensitivity)
        config['Time Constant (s)'] = str(lockin.time_constant)
        config['Filter Slope (dB/oct)'] = str(lockin.filter_slope)
        config['Filter Synchronous'] = str(lockin.filter_synchronous)
        config['Input Config'] = lockin.input_config
        config['Input Grounding'] = lockin.input_grounding
        config['Input Coupling'] = lockin.input_coupling
        config['Input Notch'] = lockin.input_notch_config
        config['Input Reserve'] = lockin.reserve
        config['Reference Source'] = lockin.reference_source
        config['Reference Source Trigger'] = lockin.reference_source_trigger
        return config

    def initializeSetup(self, output_filenames=dict(), resistance=1_000_000):
        self.current = self.lockin_xx.sine_voltage/resistance
        
        self.output_xx = mvd.MultiVuDataFile()
        self.output_xy = mvd.MultiVuDataFile()
        self.output_xx.add_multiple_columns(self.OUTPUT_COLUMNS)
        self.output_xy.add_multiple_columns(self.OUTPUT_COLUMNS)
        
        config_xx = self.getLockinConfig(self.lockin_xx)
        config_xy = self.getLockinConfig(self.lockin_xy)
        config_xx['Resistance (Ohms)'] = resistance
        config_xx['Current (A)'] = self.current
        
        comment_xx = [f'{key}: {value}' for (key, value) in config_xx.items()]
        comment_xx = '\n; Lock-in settings:\n;' + '\n; '.join(comment_xx)
        comment_xy = [f'{key}: {value}' for (key, value) in config_xy.items()]
        comment_xy = '\n; Lock-in settings:\n;' + '\n; '.join(comment_xy)
        
        filename_xx = os.path.join(self.sample_folder, output_filenames['xx'])
        filename_xy = os.path.join(self.sample_folder, output_filenames['xy'])
        self.output_xx.create_file_and_write_header(filename_xx, comment_xx)
        self.output_xy.create_file_and_write_header(filename_xy, comment_xy)

    def shutdownSetup(self):
        self.lockin_xx.shutdown()
        self.lockin_xy.shutdown()
        self.ppms.close_server()
        
    def __exit__(self):
        self.shutdownSetup()
        
    def saveDatapoint(self, temperature_now, field_now, *, with_lockins):
        # collect data
        # temp_now = ppms.getTemperature()
        # field_now = ppms.getField()
        if with_lockins:
            x_now_xx, y_now_xx = self.lockin_xx.snap()
            x_now_xy, y_now_xy = self.lockin_xy.snap()
            # put x, y into 'xx' file
            self.output_xx.set_value(self.x_col, x_now_xx)
            self.output_xx.set_value(self.y_col, y_now_xx)
            # put x, y into 'xy' file
            self.output_xy.set_value(self.x_col, x_now_xy)
            self.output_xy.set_value(self.y_col, y_now_xy)
            # calculate resistances
            resis_now_xx = x_now_xx/self.current
            resis_now_xy = x_now_xy/self.current
            # put resistances into file
            self.output_xx.set_value(self.resis_col, resis_now_xx)
            self.output_xy.set_value(self.resis_col, resis_now_xy)
        # put temperature into files
        self.output_xx.set_value(self.temp_col, temperature_now)
        self.output_xy.set_value(self.temp_col, temperature_now)
        # put field into files
        self.output_xx.set_value(self.field_col, field_now)
        self.output_xy.set_value(self.field_col, field_now)
        # write datapoint into files
        self.output_xx.write_data()
        self.output_xy.write_data()
    
    def sweepTemperature(self, initial, end, *, rate_init, rate_end,
                         mode='fast settle', sleep=0.27,
                         waiting_before=60, waiting_after=60,
                         with_lockins=True):
        self.ppms.setTemperature(initial, rate=rate_init, mode=mode)
        self.ppms.waitFor('temperature', delay_after=waiting_before)
        
        self.ppms.setTemperature(end, rate=rate_end, mode=mode)
        temperature_now = self.ppms.getTemperature()
        # one loop takes approximately 60ms
        while not np.isclose(temperature_now, end, atol=0.1, rtol=1e-16):
            temperature_now = self.ppms.getTemperature()
            field_now = self.ppms.getField()
            self.saveDatapoint(temperature_now, field_now)
            time.sleep(sleep)
        self.ppms.waitFor('temperature', delay_after=waiting_after)
        
    def sweepField(self, initial, end, *, rate_init, rate_end,
                   mode='linear', driven_mode='driven',
                   sleep=0, waiting_before=60, waiting_after=60):
        print('Enter the function')
        self.ppms.setField(initial, rate=rate_init, mode=mode)
        print('Set field to initial value')
        time.sleep(0.5)
        print('Waiting initial field: Start')
        self.ppms.waitFor('field', delay_after=waiting_before)
        print('Waiting initial field: Stop')
        time.sleep(0.5)
        print('Set field to end value')
        self.ppms.setField(end, rate=rate_end, mode=mode, driven_mode=driven_mode)
        time.sleep(0.5)
        print('Getting the value of the field to enter the loop')
        field_now = self.ppms.getField()
        # one loop takes approximately 60ms
        while not np.isclose(field_now, end, atol=1, rtol=1e-16):
            temperature_now = self.ppms.getTemperature()
            field_now = self.ppms.getField()
            self.saveDatapoint(temperature_now, field_now)
            time.sleep(sleep)
        print('Waiting end field: Start')
        self.ppms.waitFor('field', delay_after=waiting_after)
        print('Waiting end field: Stop')
        print('Sweep is finished')
        
    def sweepTime(self, sleep=0.27):
        # one loop takes approximately 60ms
        try:
            print('\nStarting measurement over time')
            while True:
                field_now = self.ppms.getField()
                temperature_now = self.ppms.getTemperature()
                self.saveDatapoint(temperature_now, field_now)
                time.sleep(sleep)
        except KeyboardInterrupt:
            print('Measurement finished')
            
    def dummySweep(self, sleep)


