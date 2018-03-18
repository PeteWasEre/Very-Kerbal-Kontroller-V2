from Utilities import is_set
from time import sleep

# This function takes care of the Controls Not In Agreement logic that ensures the panel is algined with the vessel state on vessel change.
# The function blocks until the state is consistent to avoid issues when the panel state takes over the vessel.


def cnia(ser, conn, vessel):
    f_cnia_repeat = True

    while f_cnia_repeat:
        # we need to get a state reading from the panel. Send a 0 value to get a switch reading back
        output_buffer = bytearray([0x00, 0x00, 0x00])
        ser.write(output_buffer)
        # Give the arduino time to do its processing and return the data.
        while ser.in_waiting != 40:  # Seems to work but needs a timeout/ error catch
            pass

        input_buffer = ser.read(40)

        f_cnia_repeat = False
        # SAS
        if vessel.control.sas != is_set(input_buffer[9], 2):
            msg_line = 'Set SAS Power to ' + ['Off', 'On'][vessel.control.sas]
            f_cnia_repeat = True
            conn.ui.message(msg_line, duration=1)

        # Lights
        if vessel.control.lights != is_set(input_buffer[11], 1):
            msg_line = 'Set Lights to ' + ['Off', 'On'][vessel.control.lights]
            f_cnia_repeat = True
            conn.ui.message(msg_line, duration=1)

        # RCS
        if vessel.control.rcs != is_set(input_buffer[11], 2):
            msg_line = 'Set RCS to ' + ['Off', 'On'][vessel.control.rcs]
            f_cnia_repeat = True
            conn.ui.message(msg_line, duration=1)

        # Gear
        if vessel.control.gear == is_set(input_buffer[11], 4):  # Gear logic is reversed
            msg_line = 'Set Gear to ' + ['Up', 'Down'][vessel.control.gear]
            f_cnia_repeat = True
            conn.ui.message(msg_line, duration=1)

        # Park Brake
        if vessel.control.brakes != is_set(input_buffer[11], 6):
            msg_line = 'Set Park Brake to ' + ['Off', 'On'][vessel.control.brakes]
            f_cnia_repeat = True
            conn.ui.message(msg_line, duration=1)

        # Throttle
        if input_buffer[26] >= 3:
            msg_line = 'Set Throttle to Closed'
            f_cnia_repeat = True
            conn.ui.message(msg_line, duration=1)

        sleep(0.8)

    conn.ui.message('CNIA Complete', duration=5)
