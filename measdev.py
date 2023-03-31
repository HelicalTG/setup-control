class MeasuringDevice():
    def __init__(self, instrument, name: str, contact_pair: str):
        self.instrument = instrument
        self.name = name
        self.contacts = contact_pair
        self.fullname = name + contact_pair
        self.x_col = f'X_{self.fullname} (V)'
        self.y_col = f'Y_{self.fullname} (V)'
        self.resis_col = f'Resistance_{self.fullname} (Ohms)'
        
    @property
    def columns(self):
        return [self.x_col, self.y_col, self.resis_col]
    
    def _get_instrument_config(self):
        config = dict()
        config['Sine Out (V)'] = str(self.instrument.sine_voltage)
        config['Frequency (Hz)'] = str(self.instrument.frequency)
        config['Phase (Deg)'] = str(self.instrument.phase)
        config['Sensitivity (V)'] = str(self.instrument.sensitivity)
        config['Time Constant (s)'] = str(self.instrument.time_constant)
        config['Filter Slope (dB/oct)'] = str(self.instrument.filter_slope)
        config['Filter Synchronous'] = str(self.instrument.filter_synchronous)
        config['Input Config'] = self.instrument.input_config
        config['Input Grounding'] = self.instrument.input_grounding
        config['Input Coupling'] = self.instrument.input_coupling
        config['Input Notch'] = self.instrument.input_notch_config
        config['Input Reserve'] = self.instrument.reserve
        config['Reference Source'] = self.instrument.reference_source
        config['Reference Source Trigger'] = self.instrument.reference_source_trigger
        return config
    
    def getInstrumentConfig(self, line_start='\n; ', sep='\n; ', addition = dict()):
        config_dict = self._get_instrument_config()
        if len(addition) > 0:
            config_dict.update(addition)
        config_list = [f'{key}: {value}' for (key, value) in config_dict.items()]
        config = line_start + 'Lock-in configuration: '
        config += line_start + sep.join(config_list)
        return config