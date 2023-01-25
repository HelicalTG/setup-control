from MultiVuDataFile import MultiVuDataFile as mvd
from pymeasure.instruments.srs import SR830

class Lockin(SR830):
    def __init__(self, name, output):
        self.name = name
        self.output = mvd.MultiVuDataFile()
    
    def getConfig(self):
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