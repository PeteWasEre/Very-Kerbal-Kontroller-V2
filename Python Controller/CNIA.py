from Utilities import is_set


# This function takes care of the Controls Not In Agreement logic that ensures the panel is aligned
# with the vessel state on vessel change.


def cnia(input_buffer, conn, vessel):

    f_cnia_repeat = False

    # SAS
    if vessel.control.sas != is_set(input_buffer[3], 4):
        msg_line = 'Set SAS Power to ' + ['Off', 'On'][vessel.control.sas]
        f_cnia_repeat = True
        conn.ui.message(msg_line, duration=1)

    # Lights
    if vessel.control.lights != is_set(input_buffer[4], 6):
        msg_line = 'Set Lights to ' + ['Off', 'On'][vessel.control.lights]
        f_cnia_repeat = True
        conn.ui.message(msg_line, duration=1)

    # RCS
    if vessel.control.rcs != is_set(input_buffer[3], 3):
        msg_line = 'Set RCS to ' + ['Off', 'On'][vessel.control.rcs]
        f_cnia_repeat = True
        conn.ui.message(msg_line, duration=1)

    # Gear
    if vessel.control.gear == is_set(input_buffer[3], 0):  # Gear logic is reversed
        msg_line = 'Set Gear to ' + ['Up', 'Down'][vessel.control.gear]
        f_cnia_repeat = True
        conn.ui.message(msg_line, duration=1)

    # Park Brake
    if vessel.control.brakes != is_set(input_buffer[3], 1):
        msg_line = 'Set Park Brake to ' + ['Off', 'On'][vessel.control.brakes]
        f_cnia_repeat = True
        conn.ui.message(msg_line, duration=1)

    # Throttle
    if input_buffer[17] >= 3:
        msg_line = 'Set Throttle to Closed'
        f_cnia_repeat = True
        conn.ui.message(msg_line, duration=1)

    return f_cnia_repeat

