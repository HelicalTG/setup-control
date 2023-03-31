import datetime
import os
import time

from MultiVuDataFile import MultiVuDataFile as mvd

from measdev import MeasuringDevice


class DataWriter():
    temp_col = 'Temperature (K)'
    field_col = 'Field (Oe)'
    current_col = 'I (A)'
    COMMON_OUTPUT_COLUMNS = [temp_col, field_col, current_col]
    
    def __init__(self, path):
        self.path = path
        self.outputs = []
    
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
    
    def create_output_files(self, title: str, insert_params: dict, one_output=True, add_config=True, add_datetime=True):
        if insert_params == {}:
            insert_params = self.generateLabelsDict((), ())
        labels = ('R', 'cont') + insert_params['labels']
        template = self._add_labels_to_filename(self.name, labels)
        
        self._initialize_outputs(one_output)
        for device in self.devices:
            values = (device.name, device.contacts) + insert_params['values']
            filename = template.format(*values)
            if add_datetime:
                filename += '_t%s' % self._get_timpestamp()
            if add_config:
                additional_params = dict()
                try:
                    additional_params['Source Resistance (Ohms)'] = self.current_source.resistance
                except: pass
                additional_params['Source Current (A)'] = self.current_source.current
                device_info = self.getInstrumentConfig(addition=additional_params)
                new_title = title + device_info
            else:
                new_title = title
            filename += '.' + self.ext
            device.current_filename = os.path.join(self.path, filename)
            print(filename)
            device.output.create_file_and_write_header(device.current_filename, new_title)
            
    def save_datapoint(self, temperature, field):
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