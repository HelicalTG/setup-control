from MultiPyVu.MultiVuClient import MultiVuClient

class DynacoolClient(MultiVuClient):
    def showStatus(self):
        temp_now, status_temp = self.get_temperature()
        field_now, status_field = self.get_field()
        chamber = self.get_chamber()
        message = '\nDynacool status:\n'
        message += f'Temp = {temp_now:10.2f} K\t {status_temp}\n'
        message += f'Field = {field_now:8.2f} Oe\t {status_field:}\n'
        message += f'Chamber: {chamber}\n'
        print(message)
        
    def setTemperature(self, temp, *, rate, mode='fast settle'):
        assert (1.8 <= temp <= 400)
        assert ( 0 < rate <= 20)
        if mode == 'fast settle':
            mode = self.temperature.approach_mode.fast_settle
        elif mode == 'no overshoot':
            mode = self.temperature.approach_mode.no_overshoot
        else:
            raise Exception('Wrong temperature approach mode')
        self.set_temperature(temp, rate, mode)
     
    def setField(self, field, *, rate, mode='linear', driven_mode='driven'):
        assert (abs(field)<=140000)
        assert (0 < rate <= 150)
        if mode == 'linear':
            mode = self.field.approach_mode.linear
        elif mode == 'no overshoot':
            mode = self.field.approach_mode.no_overshoot
        elif mode == 'oscillate':
            mode = self.field.approach_mode.oscillate
        else:
            raise Exception('Wrong field approach mode')
        if driven_mode == 'driven':
            driven_mode = self.field.driven_mode.driven
        elif driven_mode == 'persistent':
            driven_mode = self.field.driven_mode.persistent
        else:
            raise Exception('Wrong driven mode')
        self.set_field(field, rate, mode, driven_mode)
        
    def getTemperature(self):
        return self.get_temperature()[0]
    
    def getField(self):
        return self.get_field()[0]

    def waitFor(self, param: str, wait_timeout=0, delay_after=0):
        if param == 'temperature':
            system = self.subsystem.temperature
        elif param == 'field':
            system = self.subsystem.field
        elif param == 'both':
            system = self.subsystem.temperature | self.subsystem.field
        else:
            raise Exception('Wrong parameter to wait for')
        self.wait_for(delay_sec=delay_after, timeout_sec=wait_timeout, bitmask=system)
        
if __name__ == '__main__':
    host = "127.0.0.1"
    port = 5000
    
    ppms = DynacoolClient(host, port)
    ppms.open()
    ppms.showStatus()
    
    ppms.setTemperature(285, rate=20)
    print(f'Temperature = {ppms.getTemperature()} K')
    ppms.waitFor('temperature')
    print(f'Temperature = {ppms.getTemperature()} K')
    
    ppms.setField(100, rate=80)
    print(f'Field = {ppms.getField()} Oe')
    ppms.waitFor('field')
    print(f'Field = {ppms.getField()} Oe')
    
    ppms.close_server()