from pymeasure.instruments.srs import SR830

class Lockin(SR830):
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
    
    def getConfig(self, line_start='\n; ', sep='\n; ', addition = dict()):
        config_dict = self._get_config()
        if len(addition) > 0:
            config_dict.update(addition)
        config_list = [f'{key}: {value}' for (key, value) in config_dict.items()]
        config = line_start + 'Lock-in configuration: '
        config += line_start + sep.join(config_list)
        return config