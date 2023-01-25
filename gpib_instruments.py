import pyvisa


rm = pyvisa.ResourceManager()
addresses = rm.list_resources()
if len(addresses) == 0:
    print('No instruments detected')
else:
    print('Connected instruments (GPIB):')
    for address in addresses:
        instrument = rm.open_resource(address)
        instrument_id = instrument.query('*IDN?').rstrip()
        print(f'  {address}\t({instrument_id})')
# print('\n'.join(instruments))