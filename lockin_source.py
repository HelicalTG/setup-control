class SR830CurrentSource():
    resistance = 0
    
    @property
    def current(self):
        return self.instrument.sine_voltage/self.resistance
    
    @current.setter
    def current(self, value):
        self.instrument.sine_voltage = value*self.resistance
    
    def __init__(self, source, resistance):
        assert (resistance > 0, 'Resistance <= 0')
        self.instrument = source
        self.resistance = resistance