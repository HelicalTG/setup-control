import time


class Timer():
    def __init__(self):
        self.start()
    
    @property
    def time(self):
        t =  time.perf_counter() - self.t0
        self.start()
        return t
    
    def start(self):
        self.t0 = time.perf_counter()


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
    
    def __init__(self, volt=.1, freq=777.7, phase=0.0, x=50e-6, y=1e-6):
        self.sine_voltage = volt
        self.frequency = freq
        self.phase = phase
        self.x = x
        self.y = y
    
    def snap(self):
        return (self.x, self.y)
    
    
class DummyDynacool():
    def __init__(self, *args, **kwargs):
        self.current_temperature = 300
        self.current_field = 0
        
        self.set_temperature = 300
        self.temperature_rate = 0
        self.set_field = 0
        self.field_rate = 0
        
        self.is_connection_open = False
    
    def __enter__(self):
        self.is_connection_open = True
        return self
        
    def __exit__(self, *args, **kwargs):
        self.is_connection_open = False
        return False
    
    def open(self):
        self.is_connection_open = True

    def closeServer(self):
        self.is_connection_open = False
        
    def closeClient(self):
        self.is_connection_open = False
        
    def _check_connection(self):
        if not self.is_connection_open:
            raise Exception('Connection to server is not open')
    
    def showStatus(self):
        self._check_connection()
        temp_now, status_temp = self.temperature, 'OK'
        field_now, status_field = self.field, 'OK'
        chamber = 'OK'
        message = '\nDynacool status:\n'
        message += f'Temp =  {temp_now:8.2f} K\t {status_temp}\n'
        message += f'Field = {field_now:8.2f} Oe\t {status_field:}\n'
        message += f'Chamber: {chamber}\n'
        print(message)
        
    def setTemperature(self, temp, *, rate, mode='fast settle'):
        self._check_connection()
        if mode not in ['fast settle', 'no overshoot']:
            raise Exception('Wrong temperature approach mode')
        
        if temp > self.current_temperature:
            rate = abs(rate)
        else:
            rate = -abs(rate)
        self.set_temperature = temp
        self.temperature_rate = rate
        self.temp_timer = Timer()
        
    def setField(self, field, *, rate, mode='linear', driven_mode='driven'):
        self._check_connection()
        if mode not in ['linear', 'no overshoot', 'oscillate']:
            raise Exception('Wrong field approach mode')
        if driven_mode not in ['driven', 'persistent']:
            raise Exception('Wrong driven mode')
            
        if field > self.field:
            rate = abs(rate)
        else:
            rate = -abs(rate)
        self.set_field = field
        self.field_rate = rate
        self.field_timer = Timer()
        
    @property
    def temperature(self):
        self._check_connection()
        try:
            delta_temp = self.temperature_rate/60*self.temp_timer.time
            if abs(delta_temp) < abs(self.set_temperature - self.current_temperature):
                self.current_temperature += delta_temp
            else:
                self.current_temperature = self.set_temperature
        except: pass
        return self.current_temperature
    
    @property
    def field(self):
        self._check_connection()
        try:
            delta_field = self.field_rate*self.field_timer.time
            if abs(delta_field) < abs(self.set_field - self.current_field):
                self.current_field += delta_field
            else:
                self.current_field = self.set_field
        except: pass
        return self.current_field

    def waitFor(self, param: str, wait_timeout=0, delay=0):
        self._check_connection()
        if param == 'temperature':
            while self.temperature != self.set_temperature:
                time.sleep(1)
        elif param == 'field':
            while self.field != self.set_field:
                time.sleep(1)
        elif param == 'both':
            while (self.temperature != self.set_temperature
                   and self.field != self.set_field):
                time.sleep(1)
        else:
            raise Exception('Wrong parameter to wait for')
        time.sleep(delay)