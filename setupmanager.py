import datetime
import os
import time

import numpy as np
from MultiVuDataFile import MultiVuDataFile as mvd


class MeasuringDevice():
    def __init__(self, instrument, name: str, contact_pair: str):
        self.instrument = instrument
        self.name = name
        self.contacts = contact_pair


class SetupManager():
    temp_col = 'Temperature (K)'
    field_col = 'Field (Oe)'
    x_col = 'X (V)'
    y_col = 'Y (V)'
    current_col = 'I (A)'
    resis_col = 'Resistance (Ohms)'
    OUTPUT_COLUMNS = [temp_col, field_col, x_col, y_col, current_col, resis_col]
    
    def __init__(self, path, experiment_name, ext='dat'):
        os.makedirs(path, exist_ok=True)
        self.path = path
        self.name = experiment_name
        self.ext = ext
        self.devices = []
        
    def addMeasuringDevices(self, instruments, names, contact_pairs):
        for (instrument, name, contact_pair) in zip(instruments, names, contact_pairs):
            try:
                x, y = instrument.snap()
                x + y
            except:
                msg = 'ERROR!\n'
                msg += f'Instrument name={name}; contacts={contact_pair}\n'
                msg += 'The instrument either does not have a "snap" method'
                msg += 'or returned result can not be unpacked correctly'
                print(msg)
            instr = MeasuringDevice(instrument, name, contact_pair)
            self.devices.append(instr)
    
    def addCurrentSource(self, get_magnitude, resistance=0.0, kind='voltage'):
        try:
            1 - get_magnitude
        except:
            print('Magnitude collector returns not a numeric result')
            
        if kind == 'voltage':
            try:
                1/resistance
                self.get_current = lambda : get_magnitude/resistance
                self.source_resistance = resistance
            except:
                print('Resistance is incorrect')  
        elif kind == 'current':
            self.get_current = get_magnitude
    
    def addCryostat(self, cryostat):
        self.cryostat = cryostat
        # if is_magnet:
        #     self.magnet = cryostat
    
    # def addMagnet(self, magnet):
    #     self.magnet = magnet
    
    @staticmethod
    def generateLabelsDict(labels, values):
        parameters = dict()
        parameters['labels'] = labels
        parameters['values'] = values
        return parameters
        
    @staticmethod
    def _add_labels_to_filename(template: str, labels):
        for label in labels:
            insert = '_%s{}' % label
            template = template + insert
        return template
    
    def _initialize_outputs(self):
        for device in self.devices:
            device.output = mvd.MultiVuDataFile()
            device.output.add_multiple_columns(self.OUTPUT_COLUMNS)
    
    def createFiles(self, title: str, insert_params: dict, add_config=True, add_datetime=True):
        labels = ('R', 'cont') + insert_params['labels']
        template = self._add_labels_to_filename(self.name, labels)
        
        self._initialize_outputs()
        for device in self.devices:
            values = (device.name, device.contacts) + insert_params['values']
            filename = template.format(*values)
            if add_datetime:
                now = datetime.datetime.now()
                current_time = f'{now.year}-{now.month}-{now.day}_'
                current_time += f'{now.hour}-{now.minute}-{now.second}.{now.microsecond}'
                filename += '_t%s' % current_time
            if add_config:
                additional_params = dict()
                additional_params['Source Resistance (Ohms)'] = self.source_resistance
                additional_params['Source Current (A)'] = self.get_current()
                device_info = device.instrument.getConfig(addition=additional_params)
                new_title = title + device_info
            else:
                new_title = title
            filename += '.' + self.ext
            device.current_filename = os.path.join(self.path, filename)
            print(filename)
            device.output.create_file_and_write_header(device.current_filename, new_title)
            
    def saveDatapoint(self, temperature, field):
        # temperature = self.cryostat.temperature_getter
        # field = self.magnet.field
        for device in self.devices:
            x, y = device.instrument.snap()
            current = self.get_current()
            sample_resistance = x/current
            device.output.set_value(self.x_col, x)
            device.output.set_value(self.y_col, y)
            device.output.set_value(self.current_col, current)
            device.output.set_value(self.resis_col, sample_resistance)
        
        for device in self.devices:
            device.output.set_value(self.temp_col, temperature)
            device.output.set_value(self.field_col, field)
            device.output.write_data()
            
    def _add_sweep_to_params(self, params: dict, sweep: str):
        params_new = {'labels':('sweep',), 'values':(sweep,)}
        if sweep == 'Temp':
            field = '{:.2f}T'.format(self.cryostat.field_getter/10000)
            time.sleep(0.5)
            params_new['labels'] += ('H=',)
            params_new['values'] += (field,)
        elif sweep == 'Field':
            temperature = '{:.1f}K'.format(self.cryostat.temperature_getter)
            time.sleep(0.5)
            params_new['labels'] += ('T=',)
            params_new['values'] += (temperature,) 
        if params != {}:
            try:
                params_new['labels'] += params['labels']
                params_new['values'] += params['values']
            except Exception as e:
                print('No labels or values is found in insertion parameters')
                print(e)
        return params_new
    
    @staticmethod
    def _start_msg():
        now = datetime.datetime.now()
        return '[{}] '.format(now)
    
    def sweepTemperature(self, end_temp, initial_temp=None, *,
                         rate_to_end=3, rate_to_init=5, mode='fast settle',
                         atol = 0.05, rtol=1e-16,
                         title='', insert_params={},
                         sleep_between=0.27, waiting_before=60, waiting_after=60):
        time.sleep(0.5)
        temperature_now = self.cryostat.temperature_getter
        time.sleep(0.5)
        sweep_description = 'temperature sweep from {:.1f} K to {:.1f} K'
        
        if initial_temp is not None:
            if not np.isclose(temperature_now, initial_temp, atol=atol, rtol=rtol):
                msg = self._start_msg()
                msg += 'Start changing the temperature to the initial value {:.1f} K'.format(initial_temp)
                msg += ' (current: {:.1f} K)'.format(temperature_now)
                print(msg)
                self.cryostat.setTemperature(initial_temp, rate=rate_to_init, mode=mode)
                time.sleep(0.5)
                self.cryostat.waitFor('temperature', delay=waiting_before)
                time.sleep(0.5)
                temperature_now = self.cryostat.temperature_getter
                msg = self._start_msg()
                msg += 'Initial temperature has reached'
                print(msg)
                time.sleep(0.5)
        else:
            initial_temp = temperature_now        
        msg_start = self._start_msg() + 'Start '
        msg_start += sweep_description.format(initial_temp, end_temp)
        print(msg_start)
        
        if title == '':
            title = sweep_description.format(initial_temp, end_temp)
        insert_params = self._add_sweep_to_params(insert_params, sweep='Temp')
        self.createFiles(title=title, insert_params=insert_params)
        
        self.cryostat.setTemperature(end_temp, rate=rate_to_end, mode=mode)
        time.sleep(0.5)
        temperature_now = self.cryostat.temperature_getter
        # one loop takes approximately 60ms
        while not np.isclose(temperature_now, end_temp, atol=atol, rtol=rtol):
            temperature_now = self.cryostat.temperature_getter
            field_now = self.cryostat.field_getter
            self.saveDatapoint(temperature_now, field_now)
            time.sleep(sleep_between)
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(initial_temp, end_temp)
        msg_finish += '\n\t\t\t     Waiting for temperature to stabilze'
        print(msg_finish)
        
        time.sleep(0.5)
        self.cryostat.waitFor('temperature', delay=waiting_after)
        print(self._start_msg() + 'Temperature has stabilized\n')
        time.sleep(0.5)
    
    def sweepField(self, end_field, initial_field=None, *,
                   rate_to_end=80, rate_to_init=80,
                   mode='linear', driven_mode='driven',
                   atol = 0.05, rtol=1e-16,
                   title='', insert_params={},
                   sleep_between=0.27, waiting_before=60, waiting_after=60):
        time.sleep(0.5)
        field_now = self.cryostat.field_getter
        time.sleep(0.5)
        sweep_description = 'field sweep from {:.0f} Oe to {:.0f} Oe'
        
        if initial_field is not None:
            if not np.isclose(field_now, initial_field, atol=atol, rtol=rtol):
                msg = self._start_msg()
                msg += 'Start changing the field to the initial value {:.0f} Oe'.format(initial_field)
                msg += ' (current: {:.0f} Oe)'.format(field_now)
                print(msg)
                self.cryostat.setField(initial_field, rate=rate_to_init,
                                       mode=mode, driven_mode=driven_mode)
                time.sleep(0.5)
                self.cryostat.waitFor('field', delay=waiting_before)
                time.sleep(0.5)
                field_now = self.cryostat.field_getter
                msg = self._start_msg()
                msg += 'Initial field has reached'
                print(msg)
                time.sleep(0.5)
        else:
            initial_field = field_now
                
        msg_start = self._start_msg() + 'Start '
        msg_start += sweep_description.format(initial_field, end_field)
        print(msg_start)
            
        if title == '':
            title = sweep_description.format(initial_field, end_field)
        insert_params = self._add_sweep_to_params(insert_params, sweep='Field')
        self.createFiles(title=title, insert_params=insert_params)
        
        self.cryostat.setField(end_field, rate=rate_to_end,
                               mode=mode, driven_mode=driven_mode)
        time.sleep(0.5)
        field_now = self.cryostat.field_getter
        while not np.isclose(field_now, end_field, atol=atol, rtol=rtol):
            temperature_now = self.cryostat.temperature_getter
            field_now = self.cryostat.field_getter
            self.saveDatapoint(temperature_now, field_now)
            time.sleep(sleep_between)
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(initial_field, end_field)
        msg_finish += '\n\t\t\t     Waiting for field to stabilze'
        print(msg_finish)
        
        time.sleep(0.5)
        self.cryostat.waitFor('field', delay=waiting_after)
        print(self._start_msg() + 'Field has stabilized\n')
        time.sleep(0.5)
     
    def sweepTime(self, title='', insert_params={}, sleep_between=0.27):
        sweep_description = 'sweep over time'
        # one loop takes approximately 60ms
        try:
            msg_start = self._start_msg() + 'Start '
            msg_start += sweep_description
            print(msg_start)
            
            if title == '':
                title = sweep_description
            insert_params = self._add_sweep_to_params(insert_params, sweep='Time')
            self.createFiles(title=title, insert_params=insert_params)
            
            while True:
                field_now = self.cryostat.field_getter
                temperature_now = self.cryostat.temperature_getter
                self.saveDatapoint(temperature_now, field_now)
                time.sleep(sleep_between)
        except KeyboardInterrupt:
            print('\t\t\t     Terminated by user (keyboard interruption)')
        except Exception as e:
            print('\t\t\t     Sweep is interrupted by exception')
            print(e)
        finally:
            msg_finish = self._start_msg() + 'Finish '
            msg_finish += sweep_description
            print(msg_finish + '\n')
    
    def _one_point_measurement(self, sleep_between=0.27):
        field_now = self.cryostat.field_getter
        temperature_now = self.cryostat.temperature_getter
        self.saveDatapoint(temperature_now, field_now)
        time.sleep(sleep_between)
           
    def _generate_points(self, N, *, sleep_between=0.27, title='test', insert_params):
        self.createFiles(title=title, insert_params=insert_params)
        for _ in range(N):
            field_now = self.cryostat.field_getter
            temperature_now = self.cryostat.temperature_getter
            self.saveDatapoint(temperature_now, field_now)
            time.sleep(sleep_between)
    
        
if __name__ == '__main__':
    from dummies import DummyLockin, DummyDynacool
    from dynacoolclient import DynacoolClient
    
    measurements_path = r'C:\MeasurementData\Dynacool'
    experiment_name = 'test_sample'
    
    host = "127.0.0.1"
    port = 5000
    
    experiment_folder = os.path.join(measurements_path, experiment_name)
    setup = SetupManager(path=experiment_folder, experiment_name=experiment_name)
    
    ppms = DynacoolClient(host=host, port=port)
    ppms.open()
    lockin_xx = DummyLockin()
    lockin_xy = DummyLockin()
    lockin_xx2 = DummyLockin()
    lockin_xy2 = DummyLockin()
    
    setup.addMeasuringDevices([lockin_xx, lockin_xy, lockin_xx2, lockin_xy2],
                              ['xx', 'xy', 'xx', 'xy'],
                              ['23', '26', '67', '37'])
    setup.addCurrentSource(lockin_xx.sine_voltage, 1_000_000)
    setup.addCryostat(ppms)
    
    parameters = setup.generateLabelsDict(('T=', 'H=', 'Deg='),
                                          ('1.8K', '14T', '30.0'))
    # setup._generate_points(5, insert_params=parameters)
    # time.sleep(2)
    # setup._generate_points(30, insert_params=parameters)
    
    # setup.sweepTime(sleep_between=0.33)
    setup.sweepTemperature(290, initial_temp=300,
                           rate_to_end=20, rate_to_init=20, 
                           waiting_after=0, waiting_before=0, sleep_between=0.33)
    # setup.sweepField(10000, initial_field=-10000,
    #                  rate_to_end=80, rate_to_init=80,
    #                  waiting_after=0, waiting_before=0, sleep_between=0.1)
    