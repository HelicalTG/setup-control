import datetime
import time
import os

from MultiVuDataFile import MultiVuDataFile as mvd
from measdev import MeasuringDevice

import numpy as np


class SetupManager():
    temp_col = 'Temperature (K)'
    field_col = 'Field (Oe)'
    current_col = 'I (A)'
    pos_col = 'Position (Deg)'
    COMMON_OUTPUT_COLUMNS = [temp_col, field_col, current_col, pos_col]
    
    def __init__(self, path, experiment_name, ext='dat'):
        os.makedirs(path, exist_ok=True)
        self.base_path = path
        self.output_path = path
        self.name = experiment_name
        self.ext = ext
        self.devices = []
    
    def changeFolder(self, path):
        os.makedirs(path, exist_ok=True)
        self.output_path = path
    
    def add_measuring_devices(self, instruments, names, contact_pairs):
        for (instrument, name, contact_pair) in zip(instruments, names, contact_pairs):
            try:
                x, y = instrument.snap()
                _ = x + y
                # raise Exception()
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
    
    def create_output_files(self, title='', insert_params=dict(),
                            one_output=False, add_config=True, add_datetime=True):
        if insert_params == dict():
            insert_params = self.generateLabelsDict((), ())
        labels = ('R', 'cont') + insert_params['labels']
        template = self._add_labels_to_filename(self.name, labels)
        
        self._initialize_outputs(one_output=one_output)
        
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
                device_info = device.getInstrumentConfig(addition=additional_params)
                new_title = title + device_info
            else:
                new_title = title
            filename += '.' + self.ext
            device.current_filename = os.path.join(self.output_path, filename)
            print(filename)
            device.output.create_file_and_write_header(device.current_filename, new_title)
        
    def addMeasuringDevices(self, instruments, names, contact_pairs):
        self.add_measuring_devices(instruments, names, contact_pairs)
    
    def addCryostat(self, cryostat):
        self.cryostat = cryostat
    
    def addRotator(self, rotator):
        self.rotator = rotator
           
    def addCurrentSource(self, source):
        self.current_source = source
        
    def getCurrent(self):
        if hasattr(self, 'current_source'):
            return self.current_source.current
        else:
            raise Exception('No current source has been added')
    
    def setCurrent(self, value):
        if hasattr(self, 'current_source'):
            self.current_source.current = value
        else:
            raise Exception('No current source has been added')
        
    def getTemperature(self):
        if hasattr(self, 'cryostat'):
            return self.cryostat.temperature
        else:
            raise Exception('No cryostat has been added')
    
    def setTemperature(self, *args, **kwargs):
        if hasattr(self, 'cryostat'):
            self.cryostat.setTemperature(*args, **kwargs)
        else:
            raise Exception('No cryostat has been added')
    
    def getPosition(self):
        if hasattr(self, 'rotator'):
            return self.rotator.position
        else:
            raise Exception('No rotator has been added')
    
    def setPosition(self, position, *, speed=3.0):
        if hasattr(self, 'rotator'):
            self.rotator.setPosition(position, speed=speed)
        else:
            raise Exception('No rotator has been added')
            
    def getField(self):
        if hasattr(self, 'cryostat'):
            return self.cryostat.field
        else:
            raise Exception('No cryostat has been added')
    
    def setField(self, *args, **kwargs):
        if hasattr(self, 'cryostat'):
            self.cryostat.setField(*args, **kwargs)
        else:
            raise Exception ('No cryostat has been added')
        
    @staticmethod
    def generateLabelsDict(labels, values):
        parameters = dict()
        parameters['labels'] = labels
        parameters['values'] = values
        return parameters
    
    @staticmethod
    def _start_msg():
        now = datetime.datetime.now()
        return '[{}] '.format(now)
    
    @staticmethod
    def _add_labels_to_filename(template: str, labels):
        for label in labels:
            insert = '_%s{}' % label
            template = template + insert
        return template
    
    def _add_sweep_label_to_params(self, params: dict, sweep: str):
        params_new = {'labels':('sweep',), 'values':(sweep,)}
        if sweep == 'Temp':
            field = '{:.2f}T'.format(self.cryostat.field/10000)
            time.sleep(0.5)
            params_new['labels'] += ('H=',)
            params_new['values'] += (field,)
        elif sweep == 'Field':
            temperature = '{:.1f}K'.format(self.cryostat.temperature)
            time.sleep(0.5)
            params_new['labels'] += ('T=',)
            params_new['values'] += (temperature,)
        elif (sweep == 'Position') or (sweep == 'Time') or (sweep == 'Current'):
            temperature = '{:.1f}K'.format(self.cryostat.temperature)
            field = '{:.2f}T'.format(self.cryostat.field/10000)
            time.sleep(0.5)
            params_new['labels'] += ('T=', 'H=')
            params_new['values'] += (temperature, field)
        
        if not sweep == 'Position':
            if hasattr(self, 'rotator'):
                pos = '{:.1f}Deg'.format(self.rotator.position)
                params_new['labels'] += ('Deg=',)
                params_new['values'] += (pos,)
                
        if params != {}:
            try:
                params_new['labels'] += params['labels']
                params_new['values'] += params['values']
            except Exception as e:
                print('No labels or values is found in insertion parameters')
                print(e)
        return params_new
    
    def sweepTemperature(self, final_temperature, initial_temperature=None, *,
                         rate_to_final=3, rate_to_initial=5, approach='fast settle',
                         atol = 0.05, rtol=1e-16,
                         title='', insert_params={}, interval=0.27, 
                         waiting_before=60, waiting_after=60, timeout=0):
        sweep_folder = os.path.join(self.base_path, 'temperature_sweeps')
        self.changeFolder(sweep_folder)
        print()
        time.sleep(0.5)
        temperature_now = self.cryostat.temperature
        time.sleep(0.5)
        sweep_description = 'temperature sweep from {:.1f} K to {:.1f} K'
        
        if initial_temperature is not None:
            if not np.isclose(temperature_now, initial_temperature, atol=atol, rtol=rtol):
                msg = self._start_msg()
                msg += 'Start changing the temperature to the initial value {:.1f} K'.format(initial_temperature)
                msg += ' (current: {:.1f} K)'.format(temperature_now)
                print(msg)
                self.cryostat.setTemperature(initial_temperature, rate=rate_to_initial, approach=approach)
                time.sleep(0.5)
                self.cryostat.waitFor('temperature', delay=waiting_before, timeout=timeout)
                time.sleep(0.5)
                temperature_now = self.cryostat.temperature
                msg = self._start_msg()
                msg += 'Initial temperature reached'
                print(msg)
                time.sleep(0.5)
        else:
            initial_temperature = temperature_now
                 
        msg_start = self._start_msg() + 'Start '
        msg_start += sweep_description.format(initial_temperature, final_temperature)
        print(msg_start)
        
        if title == '':
            title = sweep_description.format(initial_temperature, final_temperature)
        insert_params = self._add_sweep_label_to_params(insert_params, sweep='Temp')
        self.create_output_files(title=title, insert_params=insert_params)
        
        self.cryostat.setTemperature(final_temperature, rate=rate_to_final, approach=approach)
        time.sleep(0.5)
        temperature_now = self.cryostat.temperature
        # one loop takes approximately 60ms for ppms and two lock-ins
        while not np.isclose(temperature_now, final_temperature, atol=atol, rtol=rtol):
            temperature_now = self.cryostat.temperature
            field_now = self.cryostat.field
            self.save_datapoint(temperature_now, field_now)
            time.sleep(interval)
            
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(initial_temperature, final_temperature)
        msg_finish += '\n\t\t\t     Waiting for temperature to stabilze'
        print(msg_finish)
        
        time.sleep(0.5)
        self.cryostat.waitFor('temperature', delay=waiting_after, timeout=timeout)
        print(self._start_msg() + 'Temperature has stabilized\n')
        time.sleep(0.5)
    
    def sweepField(self, final_field, initial_field=None, *,
                   rate_to_final=80, rate_to_initial=80,
                   approach='linear', mode='driven',
                   atol = 1, rtol=1e-16,
                   title='', insert_params={}, interval=0.27, 
                   waiting_before=60, waiting_after=60, timeout=0):
        sweep_folder = os.path.join(self.base_path, 'field_sweeps')
        self.changeFolder(sweep_folder)
        print()
        time.sleep(0.5)
        field_now = self.cryostat.field
        time.sleep(0.5)
        sweep_description = 'field sweep from {:.0f} Oe to {:.0f} Oe'
        
        if initial_field is not None:
            if not np.isclose(field_now, initial_field, atol=atol, rtol=rtol):
                msg = self._start_msg()
                msg += 'Start changing the field to the initial value {:.0f} Oe'.format(initial_field)
                msg += ' (current: {:.0f} Oe)'.format(field_now)
                print(msg)
                self.cryostat.setField(initial_field, rate=rate_to_initial,
                                       approach=approach, mode=mode)
                time.sleep(0.5)
                self.cryostat.waitFor('field', delay=waiting_before, timeout=timeout)
                time.sleep(0.5)
                field_now = self.cryostat.field
                msg = self._start_msg()
                msg += 'Initial field has reached'
                print(msg)
                time.sleep(0.5)
        else:
            initial_field = field_now
                
        msg_start = self._start_msg() + 'Start '
        msg_start += sweep_description.format(initial_field, final_field)
        print(msg_start)
            
        if title == '':
            title = sweep_description.format(initial_field, final_field)
        insert_params = self._add_sweep_label_to_params(insert_params, sweep='Field')
        self.create_output_files(title=title, insert_params=insert_params)
        
        self.cryostat.setField(final_field, rate=rate_to_final, approach=approach, mode=mode)
        time.sleep(0.5)
        field_now = self.cryostat.field
        while not np.isclose(field_now, final_field, atol=atol, rtol=rtol):
            temperature_now = self.cryostat.temperature
            field_now = self.cryostat.field
            self.save_datapoint(temperature_now, field_now)
            time.sleep(interval)
            
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(initial_field, final_field)
        msg_finish += '\n\t\t\t     Waiting for field to stabilze'
        print(msg_finish)
        
        time.sleep(0.5)
        self.cryostat.waitFor('field', delay=waiting_after, timeout=timeout)
        print(self._start_msg() + 'Field has stabilized\n')
        time.sleep(0.5)
     
    def sweepTime(self, title='', insert_params={}, interval=0.27):
        sweep_folder = os.path.join(self.base_path, 'time_sweeps')
        self.changeFolder(sweep_folder)
        print()
        sweep_description = 'sweep over time'
        # one loop takes approximately 60ms
        try:
            msg_start = self._start_msg() + 'Start '
            msg_start += sweep_description
            msg_start += "\n\t\t\t     Press 'Ctrl+C' to stop the sweep"
            print(msg_start)
            
            if title == '':
                title = sweep_description
            insert_params = self._add_sweep_label_to_params(insert_params, sweep='Time')
            self.create_output_files(title=title, insert_params=insert_params)
            
            while True:
                field_now = self.cryostat.field
                temperature_now = self.cryostat.temperature
                self.save_datapoint(temperature_now, field_now)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print('\t\t\t     Terminated by user (keyboard interruption)')
        except Exception as e:
            print('\t\t\t     Sweep is interrupted by exception')
            print(e)
        finally:
            msg_finish = self._start_msg() + 'Finish '
            msg_finish += sweep_description
            print(msg_finish + '\n')
    
    def _one_point_measurement(self, interval=0.27):
        field_now = self.cryostat.field
        temperature_now = self.cryostat.temperature
        position_now = self.rotator.position
        
        self.save_datapoint(temperature_now, field_now, position_now)
        time.sleep(interval)
           
    def doNMeasurements(self, N, *, interval=0.27, title='', insert_params={}):
        sweep_folder = os.path.join(self.base_path, 'time_sweeps')
        self.changeFolder(sweep_folder)
        print()
        time.sleep(0.5)
        sweep_description = '{} measurements'
        
        msg_start = self._start_msg() + 'Start '
        msg_start += sweep_description.format(N)
        print(msg_start)
        
        if title == '':
            title = sweep_description.format(N)
        insert_params = self._add_sweep_label_to_params(insert_params, sweep='Time')
        self.create_output_files(title=title, insert_params=insert_params)
        
        for _ in range(N):
            field_now = self.cryostat.field
            temperature_now = self.cryostat.temperature
            self.save_datapoint(temperature_now, field_now)
            time.sleep(interval)
            
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(N)
        print(msg_finish + '\n')
        
    def measureForNSeconds(self, N, *, interval=0.27, title='', insert_params={}):
        sweep_folder = os.path.join(self.base_path, 'time_sweeps')
        self.changeFolder(sweep_folder)
        print()
        time.sleep(0.5)
        sweep_description = 'measurements for {} seconds'
        
        msg_start = self._start_msg() + 'Start '
        msg_start += sweep_description.format(N)
        print(msg_start)
        
        if title == '':
            title = sweep_description.format(N)
        insert_params = self._add_sweep_label_to_params(insert_params, sweep='Time')
        self.create_output_files(title=title, insert_params=insert_params)
        
        measurement_start = time.perf_counter()
        while True:
            field_now = self.cryostat.field
            temperature_now = self.cryostat.temperature
            self.save_datapoint(temperature_now, field_now)
            time.sleep(interval)
            elapsed_time = time.perf_counter()
            if elapsed_time - measurement_start >= N:
                break
            
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(N)
        print(msg_finish + '\n')   
            
    def sweepCurrent(self, final_current, *, initial_current=0, step=50e-9,
                     interval=0.5, points_per_current=3,
                     title='', insert_params={}, set_zero=True):
        sweep_folder = os.path.join(self.base_path, 'current_sweeps')
        self.changeFolder(sweep_folder)
        print()
        time.sleep(0.5)
        sweep_description = 'current sweep from {:.2E} A to {:.2E} A'
        
        current_now = self.current_source.current
        if not np.isclose(current_now, initial_current, atol=step, rtol=1e-16):
            msg = self._start_msg()
            msg += 'Start changing the current to the initial value {:.2E} A'.format(initial_current)
            msg += ' (current: {:.2E} A)'.format(current_now)
            print(msg)
            current_range = np.arange(current_now, initial_current + step, step)
            for current in current_range:
                self.current_source.current = current
                time.sleep(interval)
            time.sleep(1)
            current_now = self.current_source.current
            msg = self._start_msg()
            msg += 'Initial current reached'
            print(msg)
            time.sleep(0.5)
        
        msg_start = self._start_msg() + 'Start '
        msg_start += sweep_description.format(initial_current, final_current)
        print(msg_start)
        
        if title == '':
            title = sweep_description.format(initial_current, final_current)
        insert_params = self._add_sweep_label_to_params(insert_params, sweep='Current')
        self.create_output_files(title=title, insert_params=insert_params)
        
        field_now = self.cryostat.field
        temperature_now = self.cryostat.temperature
        current_range = np.arange(initial_current, final_current + step, step)
        
        for current in current_range:
            self.current_source.current = current
            for _ in range(points_per_current):
                field_now = self.cryostat.field
                temperature_now = self.cryostat.temperature
                self.save_datapoint(temperature_now, field_now)
                time.sleep(interval)
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(initial_current, final_current)
        print(msg_finish)
        
        if set_zero:
            msg = self._start_msg() + 'Start changing current to zero'
            print(msg)
            current_range = np.arange(final_current, -step, -step)
            for current in current_range:
                self.current_source.current = current
                time.sleep(interval)
            msg = self._start_msg() + 'Current is set to zero\n'
            print(msg)
        else:
            msg_warning = self._start_msg() + 'WARNING! Current is at final value '
            msg_warning += '({:.2E} A)\n'.format(self.current_source.current)
            print(msg_warning)
        
    def sweepPosition(self, final_position, initial_position=None, *,
                         speed_to_final=3, speed_to_initial=5,
                         atol = 0.02, rtol=1e-16,
                         title='', insert_params={},
                         interval=0.27, waiting_before=60, waiting_after=60):
        sweep_folder = os.path.join(self.base_path, 'position_sweeps')
        self.changeFolder(sweep_folder)
        print()
        time.sleep(0.5)
        position_now = self.rotator.position
        time.sleep(0.5)
        sweep_description = 'position sweep from {:.2f} Deg to {:.2f} Deg'
        
        if initial_position is not None:
            if not np.isclose(position_now, initial_position, atol=atol, rtol=rtol):
                msg = self._start_msg()
                msg += 'Start changing the position to the initial value {:.2f} Deg'.format(initial_position)
                msg += ' (current: {:.2f} Deg)'.format(position_now)
                print(msg)
                self.rotator.setPosition(initial_position, speed=speed_to_initial)
                time.sleep(waiting_before)
                time.sleep(0.5)
                position_now = self.rotator.position
                msg = self._start_msg()
                msg += 'Initial position reached'
                print(msg)
                time.sleep(0.5)
        else:
            initial_position = position_now
                 
        msg_start = self._start_msg() + 'Start '
        msg_start += sweep_description.format(initial_position, final_position)
        print(msg_start)
        
        if title == '':
            title = sweep_description.format(initial_position, final_position)
        insert_params = self._add_sweep_label_to_params(insert_params, sweep='Position')
        self.create_output_files(title=title, insert_params=insert_params)
        
        self.rotator.setPosition(final_position, speed=speed_to_final)
        time.sleep(0.5)
        position_now = self.rotator.position
        # one loop takes approximately 60ms for ppms and two lock-ins
        while not np.isclose(position_now, final_position, atol=atol, rtol=rtol):
            position_now = self.rotator.position
            temperature_now = self.cryostat.temperature
            field_now = self.cryostat.field
            self.save_datapoint(temperature_now, field_now, position_now)
            time.sleep(interval)
            
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(initial_position, final_position)
        msg_finish += '\n\t\t\t     Waiting for position (why?)'
        print(msg_finish)
        
        time.sleep(waiting_after)
        print(self._start_msg() + 'Position settled\n')
        time.sleep(0.5)
        
    def measurePositions(self, positions, *, speed=3.0,
                         temperature=None, field=None, points_per_position=3, 
                         atol=0.02, rtol=1e-16, title='', insert_params={},
                         interval=0.27, delay=60, timeout=0, set_zero=False):
        sweep_folder = os.path.join(self.base_path, 'position_sweeps')
        self.changeFolder(sweep_folder)
        print()
        time.sleep(0.5)
        temperature_now = self.cryostat.temperature
        field_now = self.cryostat.field
        time.sleep(0.5)
        sweep_description = 'measure positions [{:.2f} .. {:.2f}] Deg at {:.2f} K {:.2f} Oe'
        if (temperature is not None) and (field is not None):
            if not np.isclose(temperature_now, temperature, atol=0.5, rtol=1e-16):
                msg = self._start_msg()
                msg += 'Setting temperature to the target value {:.1f} K'.format(temperature)
                msg += ' (current: {:.1f} K)'.format(temperature_now)
                print(msg)
                self.cryostat.setTemperature(temperature)
            if not np.isclose(field_now, field, atol=5, rtol=1e-16):
                msg = self._start_msg()
                msg += 'Setting field to the target value {:.0f} Oe'.format(field)
                msg += ' (current: {:.0f} Oe)'.format(field_now)
                print(msg)
                self.cryostat.setField(field)
            time.sleep(0.5)
            self.cryostat.waitFor('both', delay=delay, timeout=timeout)
            msg = self._start_msg()
            msg += 'Target temperature and field reached'
            print(msg)
        elif temperature is not None:
            msg = self._start_msg()
            msg += 'Setting temperature to the target value {:.1f} K'.format(temperature)
            msg += ' (current: {:.1f} K)'.format(temperature_now)
            print(msg)
            self.cryostat.setTemperature(temperature)
            time.sleep(0.5)
            self.cryostat.waitFor('temperature', delay=delay, timeout=timeout)
            msg = self._start_msg()
            msg += 'Target temperature reached'
            print(msg)
        elif field is not None:
            msg = self._start_msg()
            msg += 'Setting field to the target value {:.0f} Oe'.format(field)
            msg += ' (current: {:.0f} Oe)'.format(field_now)
            print(msg)
            self.cryostat.setField(field)
            time.sleep(0.5)
            self.cryostat.waitFor('field', delay=delay, timeout=timeout)
            msg = self._start_msg()
            msg += 'Target field reached'
            print(msg)
        
        time.sleep(0.5)
        temperature_now = self.cryostat.temperature
        field_now = self.cryostat.field
        position_now = self.rotator.position
        
        initial_position = positions[0]
        final_position = positions[-1]
        if not np.isclose(initial_position, position_now, atol=atol, rtol=rtol):
            msg = self._start_msg()
            msg += 'Setting position to the initial value {:.2f} Deg'.format(initial_position)
            msg += ' (current: {:.2f} Deg)'.format(position_now)
            print(msg)
            self.rotator.setPosition(initial_position, speed=speed)
            waiting_time = abs(initial_position - position_now)/speed
            time.sleep(waiting_time + 30)
            position_now = self.rotator.position
            msg = self._start_msg()
            msg += 'Initial position reached'
            print(msg)
            time.sleep(0.5)
        
        msg_start = self._start_msg() + 'Start '
        msg_start += sweep_description.format(initial_position, final_position, temperature_now, field_now)
        print(msg_start)
        
        if title == '':
            title = sweep_description.format(initial_position, final_position, temperature_now, field_now)
        insert_params = self._add_sweep_label_to_params(insert_params, sweep='Position')
        self.create_output_files(title=title, insert_params=insert_params)
        
        for position in positions:
            self.rotator.setPosition(position, speed=speed)
            time.sleep(1.25)
            for _ in range(points_per_position):
                field_now = self.cryostat.field
                temperature_now = self.cryostat.temperature
                position_now = self.rotator.position
                self.save_datapoint(temperature_now, field_now, position_now)
                time.sleep(interval)
        
        if set_zero:
            print(self._start_msg() + 'Start changing the position to zero')
            self.rotator.setPosition(0.0, speed=speed)
            waiting_time = abs(final_position)/speed
            time.sleep(waiting_time + 30)
            print(self._start_msg() + 'Position is set to zero\n')
        else:
            msg_warning = self._start_msg() + 'Position is at final value '
            msg_warning += '({:.2f} Deg)\n'.format(self.rotator.position)
            print(msg_warning)
        
        
        
if __name__ == '__main__':
    import os

    from pymeasure.instruments.srs import SR830

    from dummies import DummyDynacool, DummyLockin
    from dynacool import DynacoolCryostat
    from dynacooldll import DynacoolDLL
    from lockin_source import SR830CurrentSource
    
    measurements_path = r'C:\MeasurementData\Dynacool'
    experiment_name = 'test_sample'
    experiment_folder = os.path.join(measurements_path, experiment_name)
    
    host = "127.0.0.1"
    port = 5000
    
    with DummyDynacool(host=host, port=port) as ppms:
    # with DynacoolCryostat(host=host, port=port) as ppms:
    # ppms = DummyDynacool(host=host, port=port)
    # ppms.open()
        ppms.showStatus()
    
        setup = SetupManager(path=experiment_folder, experiment_name=experiment_name)
        
        lockin_xx = DummyLockin()
        lockin_xy = DummyLockin()
        lockin_xx2 = DummyLockin()
        lockin_xy2 = DummyLockin()
        current_source = SR830CurrentSource(lockin_xx, 1_000_000)
        
        rotator = DynacoolDLL('127.0.0.1', remote=False)
        rotator.showStatus()
        
        setup.addMeasuringDevices([lockin_xx, lockin_xy, lockin_xx2, lockin_xy2],
                                ['xx', 'xy', 'xx', 'xy'],
                                ['23', '26', '67', '37'])
        setup.addCurrentSource(current_source)
        setup.addCryostat(ppms)
        setup.addRotator(rotator)
        
        parameters = setup.generateLabelsDict(('T=', 'H=', 'Deg='),
                                            ('1.8K', '14T', '30.0'))
        setup.doNMeasurements(5, insert_params=parameters)
        
        setup.sweepTime(interval=0.33)
        setup.sweepTemperature(final_temperature=280, rate_to_final=20,
                               initial_temperature=290, rate_to_initial=20, 
                               waiting_after=0, waiting_before=0, interval=0.33)
        setup.sweepField(final_field=500, rate_to_final=80,
                         initial_field=-500, rate_to_initial=80,
                        waiting_after=0, waiting_before=0, interval=0.33)
        setup.sweepCurrent(final_current=2e-6, initial_current=-0.5e-6, interval=0.01)
        setup.measureForNSeconds(10)
        setup.sweepPosition(final_position=90, speed_to_final=3,
                            initial_position=40, speed_to_initial=3,
                            waiting_after=10, waiting_before=10, interval=0.33)
        # %%timeit
        # setup.writer.create_output_files(title='test_one_point')
        # setup._one_point_measurement()
        
    # ppms.closeServer()