from MultiPyVu import MultiVuClient as mvc

class DynacoolCryostat():
    def __init__(self, *args, **kwargs):
        self.dynacool = mvc.MultiVuClient(*args, **kwargs)
    
    def __enter__(self):
        self.dynacool.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        exit_without_error = self.dynacool.__exit__(exc_type, exc_value, exc_traceback)
        return exit_without_error
    
    def open(self):
        self.dynacool.__enter__()
    
    def closeClient(self):
        self.dynacool.close_client()
    
    def closeServer(self):
        self.dynacool.close_server()
               
    def showStatus(self):
        temp_now, status_temp = self.dynacool.get_temperature()
        field_now, status_field = self.dynacool.get_field()
        chamber = self.dynacool.get_chamber()
        message = '\nDynacool status:\n'
        message += f'Temp =  {temp_now:8.2f} K\t {status_temp}\n'
        message += f'Field = {field_now:8.2f} Oe\t {status_field:}\n'
        message += f'Chamber: {chamber}\n'
        print(message)
        
    def setTemperature(self, temperature, *, rate=3, approach='fast settle'):
        assert (1.8 <= temperature <= 400)
        assert ( 0 < rate <= 20)
        if approach == 'fast settle':
            approach = self.dynacool.temperature.approach_mode.fast_settle
        elif approach == 'no overshoot':
            approach = self.dynacool.temperature.approach_mode.no_overshoot
        else:
            raise Exception('Wrong temperature approach mode')
        self.dynacool.set_temperature(temperature, rate, approach)
     
    def setField(self, field, *, rate=80, approach='linear', mode='driven'):
        assert (abs(field) <= 140000)
        assert (0 < rate <= 150)
        if approach == 'linear':
            approach = self.dynacool.field.approach_mode.linear
        elif approach == 'no overshoot':
            approach = self.dynacool.field.approach_mode.no_overshoot
        elif approach == 'oscillate':
            approach = self.dynacool.field.approach_mode.oscillate
        else:
            raise Exception('Wrong field approach mode')
        if mode == 'driven':
            mode = self.dynacool.field.driven_mode.driven
        elif mode == 'persistent':
            mode = self.dynacool.field.driven_mode.persistent
        else:
            raise Exception('Wrong driven mode')
        self.dynacool.set_field(field, rate, approach, mode)
        
    @property
    def temperature(self):
        return self.dynacool.get_temperature()[0]
    
    @property
    def field(self):
        return self.dynacool.get_field()[0]
    
    def getTemperature(self):
        return self.temperature
    
    def getField(self):
        return self.field
    
    # @temperature.setter
    # def temperature(self, value):
    #     raise Exception('Use setTemperature() to change temperature')
    
    # @field.setter
    # def field(self, value):
    #     raise Exception('Use setField() temperature')

    def waitFor(self, parameter: str, delay=0, timeout=0):
        if parameter == 'temperature':
            subsystem = self.dynacool.subsystem.temperature
        elif parameter == 'field':
            subsystem = self.dynacool.subsystem.field
        elif parameter == 'both':
            subsystem = self.dynacool.subsystem.temperature | self.dynacool.subsystem.field
        else:
            raise Exception('Wrong parameter to wait for')
        self.dynacool.wait_for(delay_sec=delay, timeout_sec=timeout, bitmask=subsystem)
        
if __name__ == '__main__':
    import time
    host = "127.0.0.1"
    port = 5000
    
    with DynacoolCryostat(host, port) as ppms:
        ppms.showStatus()
        
        ppms.setTemperature(285, rate=10)
        time.sleep(0.5)
        print(f'Temperature = {ppms.getTemperature()} K')
        time.sleep(0.5)
        ppms.waitFor('temperature')
        time.sleep(0.5)
        print(f'Temperature = {ppms.getTemperature()} K')
        
        ppms.setField(100, rate=80)
        time.sleep(0.5)
        print(f'Field = {ppms.getField()} Oe')
        time.sleep(0.5)
        ppms.waitFor('field')
        time.sleep(0.5)
        print(f'Field = {ppms.getField()} Oe')