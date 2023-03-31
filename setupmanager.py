import datetime
import time

import numpy as np

from data_writer import DataWriter


class SetupManager():
    def __init__(self, path, experiment_name, ext='dat'):
        os.makedirs(path, exist_ok=True)
        self.name = experiment_name
        self.ext = ext
        self.devices = dict()
        self.writer = DataWriter(path)
        
    def addMeasuringDevices(self, instruments, names, contact_pairs):
        self.writer.add_measuring_devices(instruments, names, contact_pairs)
    
    def addCryostat(self, cryostat):
        self.cryostat = cryostat
            
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
            self.cryostat.setTemperature(args, kwargs)
        else:
            raise Exception('No cryostat has been added')
            
    def getField(self):
        if hasattr(self, 'cryostat'):
            return self.cryostat.field
        else:
            raise Exception('No cryostat has been added')
    
    def setField(self, *args, **kwargs):
        if hasattr(self, 'cryostat'):
            self.cryostat.setField(args, kwargs)
        else:
            raise Exception ('No cryostat has been added')
    
    @staticmethod
    def _start_msg():
        now = datetime.datetime.now()
        return '[{}] '.format(now)
    
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
        elif sweep == 'Current':
            temperature = '{:.1f}K'.format(self.cryostat.temperature)
            field = '{:.2f}T'.format(self.cryostat.field/10000)
            time.sleep(0.5)
            params_new['labels'] += ('T=', 'H=')
            params_new['values'] += (temperature, field)
        if params != {}:
            try:
                params_new['labels'] += params['labels']
                params_new['values'] += params['values']
            except Exception as e:
                print('No labels or values is found in insertion parameters')
                print(e)
        return params_new
    
    def sweepTemperature(self, final_temperature, initial_temperature=None, *,
                         rate_to_final=3, rate_to_initial=5, mode='fast settle',
                         atol = 0.05, rtol=1e-16,
                         title='', insert_params={},
                         interval=0.27, waiting_before=60, waiting_after=60):
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
                self.cryostat.setTemperature(initial_temperature, rate=rate_to_initial, mode=mode)
                time.sleep(0.5)
                self.cryostat.waitFor('temperature', delay=waiting_before)
                time.sleep(0.5)
                temperature_now = self.cryostat.temperature
                msg = self._start_msg()
                msg += 'Initial temperature has reached'
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
        
        self.cryostat.setTemperature(final_temperature, rate=rate_to_final, mode=mode)
        time.sleep(0.5)
        temperature_now = self.cryostat.temperature
        # one loop takes approximately 60ms for ppms and two lock-ins
        while not np.isclose(temperature_now, final_temperature, atol=atol, rtol=rtol):
            temperature_now = self.cryostat.temperature
            field_now = self.cryostat.field
            self.writer.save_datapoint(temperature_now, field_now)
            time.sleep(interval)
            
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(initial_temperature, final_temperature)
        msg_finish += '\n\t\t\t     Waiting for temperature to stabilze'
        print(msg_finish)
        
        time.sleep(0.5)
        self.cryostat.waitFor('temperature', delay=waiting_after)
        print(self._start_msg() + 'Temperature has stabilized\n')
        time.sleep(0.5)
    
    def sweepField(self, final_field, initial_field=None, *,
                   rate_to_final=80, rate_to_initial=80,
                   mode='linear', driven_mode='driven',
                   atol = 1, rtol=1e-16,
                   title='', insert_params={},
                   interval=0.27, waiting_before=60, waiting_after=60):
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
                                       mode=mode, driven_mode=driven_mode)
                time.sleep(0.5)
                self.cryostat.waitFor('field', delay=waiting_before)
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
        
        self.cryostat.setField(final_field, rate=rate_to_final,
                               mode=mode, driven_mode=driven_mode)
        time.sleep(0.5)
        field_now = self.cryostat.field
        while not np.isclose(field_now, final_field, atol=atol, rtol=rtol):
            temperature_now = self.cryostat.temperature
            field_now = self.cryostat.field
            self.writer.save_datapoint(temperature_now, field_now)
            time.sleep(interval)
            
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(initial_field, final_field)
        msg_finish += '\n\t\t\t     Waiting for field to stabilze'
        print(msg_finish)
        
        time.sleep(0.5)
        self.cryostat.waitFor('field', delay=waiting_after)
        print(self._start_msg() + 'Field has stabilized\n')
        time.sleep(0.5)
     
    def sweepTime(self, title='', insert_params={}, interval=0.27):
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
                self.writer.save_datapoint(temperature_now, field_now)
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
    
    def _one_point_measurement(self, interval=0.27, title='', insert_params={}):
        self.create_output_files(title=title, insert_params=insert_params)
        field_now = self.cryostat.field
        temperature_now = self.cryostat.temperature
        self.writer.save_datapoint(temperature_now, field_now)
        time.sleep(interval)
           
    def doNMeasurements(self, N, *, interval=0.27, title='', insert_params={}):
        print()
        time.sleep(0.5)
        sweep_description = '{} measurements'
        
        msg_start = self._start_msg() + 'Start '
        msg_start += sweep_description.format(N)
        print(msg_start)
        
        if title == '':
            title = sweep_description.format(N)
        self.create_output_files(title=title, insert_params=insert_params)
        
        for _ in range(N):
            field_now = self.cryostat.field
            temperature_now = self.cryostat.temperature
            self.writer.save_datapoint(temperature_now, field_now)
            time.sleep(interval)
            
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(N)
        print(msg_finish + '\n')
        
    def measureForNSeconds(self, N, *, interval=0.27, title='', insert_params={}):
        print()
        time.sleep(0.5)
        sweep_description = 'measurements for {} seconds'
        
        msg_start = self._start_msg() + 'Start '
        msg_start += sweep_description.format(N)
        print(msg_start)
        
        if title == '':
            title = sweep_description.format(N)
        self.create_output_files(title=title, insert_params=insert_params)
        
        measurement_start = time.perf_counter()
        while True:
            field_now = self.cryostat.field
            temperature_now = self.cryostat.temperature
            self.writer.save_datapoint(temperature_now, field_now)
            time.sleep(interval)
            elapsed_time = time.perf_counter()
            if elapsed_time - measurement_start >= N:
                break
            
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(N)
        print(msg_finish + '\n')   
            
    def sweepCurrent(self, final_current, *, initial_current=0, step=50e-9, interval=0.27,
                     title='', insert_params={}, set_zero=True):
        time.sleep(0.5)
        sweep_description = 'current sweep from {:.2E} A to {:.2E} A'
        
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
            self.writer.save_datapoint(temperature_now, field_now)
            time.sleep(interval)
        msg_finish = self._start_msg() + 'Finish '
        msg_finish += sweep_description.format(initial_current, final_current)
        print(msg_finish)
        
        if set_zero:
            self.current_source.current = 0
            print(self._start_msg() + 'Current is set to zero\n')
        else:
            msg_warning = self._start_msg() + 'WARNING! Current is at final value '
            msg_warning += '({:.2f} A)\n'.format(self.current_source.current)
            print(msg_warning)
        
if __name__ == '__main__':
    import os

    from pymeasure.instruments.srs import SR830

    from dummies import DummyDynacool, DummyLockin
    from dynacool import DynacoolCryostat
    from lockin_source import SR830CurrentSource
    
    measurements_path = r'C:\MeasurementData\Dynacool'
    experiment_name = 'test_sample'
    
    host = "127.0.0.1"
    port = 5000
    
    with DummyDynacool(host=host, port=port) as ppms:
    # with DynacoolCryostat(host=host, port=port) as ppms:
    # ppms = DummyDynacool(host=host, port=port)
    # ppms.open()
        ppms.showStatus()
    
        experiment_folder = os.path.join(measurements_path, experiment_name)
        setup = SetupManager(path=experiment_folder, experiment_name=experiment_name)
        
        lockin_xx = DummyLockin()
        lockin_xy = DummyLockin()
        lockin_xx2 = DummyLockin()
        lockin_xy2 = DummyLockin()
        current_source = SR830CurrentSource(lockin_xx, 1_000_000)
        
        setup.addMeasuringDevices([lockin_xx, lockin_xy, lockin_xx2, lockin_xy2],
                                ['xx', 'xy', 'xx', 'xy'],
                                ['23', '26', '67', '37'])
        setup.addCurrentSource(current_source)
        setup.addCryostat(ppms)
        
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
    # ppms.closeServer()