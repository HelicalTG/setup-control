import datetime
import os
import time

from MultiVuDataFile import MultiVuDataFile as mvd

from measdev import MeasuringDevice


class DataWriter():
    temp_col = 'Temperature (K)'
    field_col = 'Field (Oe)'
    current_col = 'I (A)'
    pos_col = 'Position (Deg)'
    COMMON_OUTPUT_COLUMNS = [temp_col, field_col, current_col, pos_col]
    
    def __init__(self, path, name):
        self.path = path
        self.devices = []
    
    def add_measuring_devices(self, instruments, names, contact_pairs):
        for (instrument, name, contact_pair) in zip(instruments, names, contact_pairs):
            try:
                x, y = instrument.snap()
                x + y
            except:
                msg = f'Instrument name={name}; contacts={contact_pair}\n'
                msg += 'The instrument either does not have a "snap" method'
                msg += 'or returned result can not be unpacked correctly'
                raise Exception(msg)
            instr = MeasuringDevice(instrument, name, contact_pair)
            self.devices.append(instr)
    
    def generateLabelsDict(labels, values):
        parameters = dict()
        parameters['labels'] = labels
        parameters['values'] = values
        return parameters
        
    
    
    def _initialize_outputs(self, one_output=True):
        if one_output:
            output = mvd.MultiVuDataFile()
            output.add_multiple_columns(self.COMMON_OUTPUT_COLUMNS)
            for device in self.devices:
                device.output = output
                device.output.add_multiple_columns(device.columns)
        else:    
            for device in self.devices:
                device.output = mvd.MultiVuDataFile()
                device.output.add_multiple_columns(self.COMMON_OUTPUT_COLUMNS)
                device.output.add_multiple_columns(device.columns)
    
    @staticmethod
    def _get_timpestamp():
        now = datetime.datetime.now()
        timestamp = f'{now.year}-{now.month}-{now.day}_'
        timestamp += f'{now.hour}-{now.minute}-{now.second}.{now.microsecond}'
        return timestamp
    
    def create_files(self):
        pass
    
    
            
    def save_datapoint(self, temperature, field, position=0.0):
        current = self.current_source.current
        for device in self.devices:
            x, y = device.instrument.snap()
            sample_resistance = x/current
            device.output.set_value(device.x_col, x)
            device.output.set_value(device.y_col, y)
            device.output.set_value(self.current_col, current)
            device.output.set_value(device.resis_col, sample_resistance)
        
        for device in self.devices:
            device.output.set_value(self.temp_col, temperature)
            device.output.set_value(self.field_col, field)
            device.output.set_value(self.pos_col, position)
            device.output.write_data()
    
    # def save_datapoint_to_one_output(self, temperature, field):
    #     current = self.current_source.current
    #     for device in self.devices:
    #         x, y = device.instrument.snap()
    #         sample_resistance = x/current
    #         device.output.set_value(device.x_col, x)
    #         device.output.set_value(device.y_col, y)
    #         device.output.set_value(self.current_col, current)
    #         device.output.set_value(device.resis_col, sample_resistance)
        
    #     for device in self.devices:
    #         device.output.set_value(self.temp_col, temperature)
    #         device.output.set_value(self.field_col, field)
    #         device.output.write_data()