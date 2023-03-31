import clr

# load the C# .dll supplied by Quantum Design
clr.AddReference('QDInstrument')

# import the C# classes for interfacing with the PPMS
from QuantumDesign.QDInstrument import QDInstrumentBase, QDInstrumentFactory

ChamberStatus = QDInstrumentBase.ChamberStatus
ChamberStatusString = QDInstrumentBase.ChamberStatusString

TemperatureStatus = QDInstrumentBase.TemperatureStatus
TemperatureApproach = QDInstrumentBase.TemperatureApproach
TemperatureStatusString = QDInstrumentBase.TemperatureStatusString

FieldApproach = QDInstrumentBase.FieldApproach
FieldMode = QDInstrumentBase.FieldMode
FieldStatus = QDInstrumentBase.FieldStatus
FieldStatusString = QDInstrumentBase.FieldStatusString

PositionMode = QDInstrumentBase.PositionMode
PositionStatus = QDInstrumentBase.PositionStatus


class DynacoolDLL:
    """A class to interface with Quantum Design instruments.

    This class is a thin wrapper around the C# QuantumDesign.QDInstrument.QDInstrumentBase class
    provided in the QDInstrument.dll file.
    """

    def __init__(self, ip_address, port=11000, remote=True):
        self.dynacool = QDInstrumentFactory.GetQDInstrument(
            QDInstrumentBase.QDInstrumentType.DynaCool,
            remote, ip_address, port)

    def showStatus(self):
        print(self.getTemperature())
        print(self.getField())
        print(self.getPosition())
        print(self.getChamber())
        message = '\nDynacool status:\n' + '-'*30 + '\n'
        message += f'{"Temperature":<12} {self.temperature:>12.2f} K\n'
        message += f'{"Field":<12} {self.field:>12.2f} Oe\n'
        message += f'{"Position":<12} {self.position:>12.2f} Deg\n'
        # message += f'Chamber: {chamber}\n'
        print(message)
    
    def getTemperature(self):
        """Returns the instrument temperature in Kelvin.

        Parameters are from:
        GetTemperature(ref double Temperature, ref QDInstrumentBase.TemperatureStatus Status)
        """
        answer = self.dynacool.GetTemperature(0, TemperatureStatus(0))
        status = int(answer[2])
        return (*answer[:2], status)

    def setTemperature(self, temperature, *, rate, approach='fast settle'):
        """Ramps the instrument temperature to the set point.

        Parameters are from:
        SetTemperature(double Temperature, double Rate, QDInstrumentBase.TemperatureApproach Approach)

        :param temp: Desired temperature in Kelvin
        :param rate: Temperature ramp rate in Kelvin/min.
        :return: None
        """
        assert (1.8 <= temperature <= 400)
        assert ( 0 < rate <= 20)
        if approach == 'fast settle':
            approach = TemperatureApproach.FastSettle
        elif approach == 'no overshoot':
            approach = TemperatureApproach.NoOvershoot
        else:
            raise Exception('Wrong temperature approach mode')
        return self.dynacool.SetTemperature(temperature, rate, approach)

    def getField(self):
        """Returns the Magnetic field in Gauss.

        Parameters are from:
        GetField(ref double Field, ref QDInstrumentBase.FieldStatus Status)

        :return: Field in Gauss.
        """
        answer = self.dynacool.GetField(0, FieldStatus(0))
        status = int(answer[2])
        return (*answer[:2], status)

    def setField(self, field, *, rate, approach='linear', mode='driven'):
        """Ramps the instrument magnetic field to the set point.

        Parameters are from:
        SetField(double Field, double Rate, QDInstrumentBase.FieldApproach Approach, QDInstrumentBase.FieldMode Mode)

        :param field: Set point of the applied magnetic field in Gauss.
        :param rate:  Ramp rate of the applied magnetic field in Gauss/sec.
        :return: None
        """
        
        assert (abs(field) <= 140000)
        assert (0 < rate <= 150)
        if approach == 'linear':
            approach = FieldApproach.Linear
        elif approach == 'no overshoot':
            approach = FieldApproach.NoOvershoot
        elif approach == 'oscillate':
            approach = FieldApproach.Oscillate
        else:
            raise Exception('Wrong field approach mode')
        if mode == 'driven':
            mode = FieldMode.Driven
        elif mode == 'persistent':
            mode = FieldMode.Persistent
        else:
            raise Exception('Wrong driven mode')
        return self.dynacool.SetField(field, rate, approach, mode)

    def getPosition(self):
        """Retrieves the position of the rotator.

        GetPosition(string Axis, ref double Position, ref QDInstrumentBase.PositionStatus Status)

        "Horizontal Rotator" seems to be the name that one should pass to GetPosition, as
        observed in the WaitConditionReached function.
        """
        answer = self.dynacool.GetPosition("Horizontal Rotator", 0, PositionStatus(0))
        status = int(answer[2])
        return (*answer[:2], status)

    def setPosition(self, position, speed):
        """Ramps the instrument position to the set point.

        Parameters are from:
        SetPosition(string Axis, double Position, double Speed, QDInstrumentBase.PositionMode Mode)

        :param position: Position on the rotator to move to.
        :param speed: Rate of change of position on the rotator.
        """
        return self.dynacool.SetPosition("Horizontal Rotator", position, speed, PositionStatus(0))

    def getChamber(self):
        answer = self.dynacool.GetChamber(ChamberStatus(0))
        status = int(answer[1])
        return (*answer[:1], status)
    
    def waitFor(self, parameters, delay=5, timeout=600):        
        """
        Prevents other processes from executing while the QD instrument magnetic field
        is settling down.

        :param delay: Length of time to wait after wait condition achieved in seconds.
        :param timeout: Length of time to wait to achieve wait condition in seconds.
        :return: 0 when complete.
        """
        
        subsystems = ['temperature', 'field', 'position']
        for param in parameters:
            if param not in subsystems:
                raise Exception(f'Unknown {param} parameter')
            
        bool_key = [False, False, False, False]
        for (i, subsystem) in subsystems:
            if subsystem in parameters:
                bool_key[i] = True
        
        return self.dynacool.WaitFor(*bool_key, delay, timeout)
    
    @property
    def temperature(self):
        return self.dynacool.GetTemperature(0, TemperatureStatus(0))[1]
    
    @property
    def field(self):
        return self.dynacool.GetField(0, FieldStatus(0))[1]
    
    @property
    def position(self):
        return self.dynacool.GetPosition("Horizontal Rotator", 0, PositionStatus(0))[1]
    
    
if __name__ == '__main__':
    dyna = DynacoolDLL('127.0.0.1', remote=False)
    dyna.showStatus()
    dyna.setTemperature(280, rate=10)
    # print(dyna.getTemperature()[1])