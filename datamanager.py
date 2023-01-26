from MultiVuDataFile import MultiVuDataFile as mvd
import datetime
from collections import OrderedDict
import os
import time


class DummyLockin():
    sensitivity = 1E-3
    time_constant = 0.3
    filter_slope = 24
    filter_synchronous = True
    input_config = 'A-B'
    input_grounding = 'float'
    input_coupling = 'temp'
    input_notch_config = 'temp'
    reserve = 'temp'
    reference_source = 'temp'
    reference_source_trigger = 'temp'
    
    def __init__(self, volt=1., freq=777.7, phase=0.0):
        self.sine_voltage = volt
        self.frequency = freq
        self.phase = phase
        
    def _get_config(self):
        config = dict()
        config['Sine Out (V)'] = str(self.sine_voltage)
        config['Frequency (Hz)'] = str(self.frequency)
        config['Phase (Deg)'] = str(self.phase)
        config['Sensitivity (V)'] = str(self.sensitivity)
        config['Time Constant (s)'] = str(self.time_constant)
        config['Filter Slope (dB/oct)'] = str(self.filter_slope)
        config['Filter Synchronous'] = str(self.filter_synchronous)
        config['Input Config'] = self.input_config
        config['Input Grounding'] = self.input_grounding
        config['Input Coupling'] = self.input_coupling
        config['Input Notch'] = self.input_notch_config
        config['Input Reserve'] = self.reserve
        config['Reference Source'] = self.reference_source
        config['Reference Source Trigger'] = self.reference_source_trigger
        return config
    
    def getConfig(self, line_start='\n; ', sep='\n; '):
        config_dict = self._get_config()
        config_list = [f'{key}: {value}' for (key, value) in config_dict.items()]
        config = line_start + 'Lock-in configuration: '
        config += line_start + sep.join(config_list)
        return config
    

class MeasuringDevice():
    def __init__(self, instrument, name: str, contact_pair: str):
        self.instrument = instrument
        self.name = name
        self.contacts = contact_pair


class DataManager():
    def __init__(self, path, experiment_name, ext='dat'):
        self.path = path
        self.name = experiment_name
        self.ext = ext
        self.devices = []
        
    def addDevices(self, instruments, names, contact_pairs):
        for (instrument, name, contact_pair) in zip(instruments, names, contact_pairs):
            instr = MeasuringDevice(instrument, name, contact_pair)
            self.devices.append(instr)
        
    @staticmethod
    def _add_parameters(template: str, parameters: dict):
        for (print_name, substitute_name) in parameters.items():
            insert = '_%s{%s}' % (print_name, substitute_name)
            template = template + insert
        return template
    
    def _initialize_outputs(self):
        temp_col = 'Temperature (K)'
        field_col = 'Field (Oe)'
        x_col = 'X (V)'
        y_col = 'Y (V)'
        current_col = 'I (A)'
        resis_col = 'Resistance (Ohms)'
        OUTPUT_COLUMNS = [temp_col, field_col, x_col, y_col, current_col, resis_col]
        for device in self.devices:
            device.output = mvd.MultiVuDataFile()
            device.output.add_multiple_columns(OUTPUT_COLUMNS)
    
    def createFiles(self, title: str, parameters: dict, values: dict, add_datetime=True):
        params = OrderedDict()
        params['R'] = 'direction'
        params['cont'] = 'contacts'
        params.update(parameters)
        template = self._add_parameters(self.name, params)
        
        self._initialize_outputs()
        for device in self.devices:
            vals = OrderedDict()
            vals['direction'] = device.name
            vals['contacts'] = device.contacts
            vals.update(values)
            filename = template.format(**vals)
            if add_datetime:
                now = datetime.datetime.now()
                current_time = f'{now.year}-{now.month}-{now.day}_'
                current_time += f'{now.hour}-{now.minute}-{now.second}.{now.microsecond}'
                filename += '_t%s' % current_time
            filename += '.' + self.ext
            device.current_filename = os.path.join(self.path, filename)
            print(device.current_filename)
            device_info = device.instrument.getConfig()
            device.output.create_file_and_write_header(device.current_filename, title + device_info)
            
    def saveDatapoint(self, temperature, field):
        for device in self.devices:
            x, y = device.instrument.snap()
            current = x/device.resistance
            resistance = x/current
            device.output.set_value(self.x_col, x)
            device.output.set_value(self.y_col, y)
            device.output.set_value(self.current_col, current)
            device.output.set_value(self.resis_col, resistance)
        
        for device in self.devices:
            device.output.set_value(self.temp_col, temperature)
            device.output.set_value(self.field_col, field)
            
    def _generate_points(self, N):
        temp_col = 'Temperature (K)'
        field_col = 'Field (Oe)'
        x_col = 'X (V)'
        y_col = 'Y (V)'
        current_col = 'I (A)'
        resis_col = 'Resistance (Ohms)'
        for _ in range(N):
            for device in self.devices:
                device.output.set_value(temp_col, 300)
                device.output.set_value(field_col, 10000)
                device.output.set_value(x_col, 130)
                device.output.set_value(y_col, 11)
                device.output.set_value(current_col, 1e-6)
                device.output.set_value(resis_col, 30)
                device.output.write_data()
    
        
if __name__ == '__main__':
    path = r'D:'
    manager = DataManager(path=path, experiment_name='test_sample')
    lockin_xx = DummyLockin(1, 500)
    lockin_xy = DummyLockin(0.05)
    lockin_xx2 = DummyLockin(111, 888)
    lockin_xy2 = DummyLockin(0.001, 33)
    manager.addDevices([lockin_xx, lockin_xy, lockin_xx2, lockin_xy2],
                       ['xx', 'xy', 'xx', 'xy'],
                       ['23', '26', '67', '36'])
    
    print_names = ['T=', 'H=', 'Deg=']
    substitute_names = ['temperature', 'field', 'angle']
    substitute_values = ['1.8K', '14T', '30.0']
    
    parameters = dict(zip(print_names, substitute_names))
    values = dict(zip(substitute_names, substitute_values))
    manager.createFiles(title='test to check file creation', parameters=parameters, values=values)
    manager._generate_points(5)
    # time.sleep(2)
    manager.createFiles(title='test to check file creation', parameters=parameters, values=values)
    manager._generate_points(30)
    # manager.closeFiles()