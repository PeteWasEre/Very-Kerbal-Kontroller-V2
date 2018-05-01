from time import sleep

from Utilities import is_set, map_flt_ctl
import Settings


def sas_inputs(input_buffer, input_buffer_prev, vessel, conn, sas_overide, sas_overide_prev):
    prev_sas_mode = vessel.control.sas_mode

    if is_set(input_buffer[3], 4):
        if sas_overide:
            vessel.control.sas = False
        else:
            vessel.control.sas = True
            if sas_overide_prev:
                # need to add a small delay here as the game forces to STAB mod immediately on power on
                sleep(Settings.c_sas_reset_delay)
                vessel.control.sas_mode = prev_sas_mode
    else:
        vessel.control.sas = False

    # need to handle exceptions here, not all modes are available at all times.
    if is_set(input_buffer[3], 6) and not is_set(input_buffer_prev[3], 6):  # SAS Set requested
        if is_set(input_buffer[3], 7):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.maneuver
            except RuntimeError:
                conn.ui.message('SAS Mode - Maneuver - Not Available', duration=3)
        elif is_set(input_buffer[2], 7):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.anti_target
            except RuntimeError:
                conn.ui.message('SAS Mode - Anti-Target - Not Available', duration=3)
                pass
        elif is_set(input_buffer[2], 6):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.target
            except RuntimeError:
                conn.ui.message('SAS Mode - Target - Not Available', duration=3)
                pass
        elif is_set(input_buffer[2], 5):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.anti_radial
            except RuntimeError:
                conn.ui.message('SAS Mode - Anti-Radial - Not Available', duration=3)
                pass
        elif is_set(input_buffer[2], 4):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.radial
            except RuntimeError:
                conn.ui.message('SAS Mode - Radial - Not Available', duration=3)
                pass
        elif is_set(input_buffer[2], 3):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.anti_normal
            except RuntimeError:
                conn.ui.message('SAS Mode - Anti-Normal - Not Available', duration=3)
                pass
        elif is_set(input_buffer[2], 2):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.normal
            except RuntimeError:
                conn.ui.message('SAS Mode - Normal - Not Available', duration=3)
                pass
        elif is_set(input_buffer[2], 1):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.retrograde
            except RuntimeError:
                conn.ui.message('SAS Mode - Retrograde - Not Available', duration=3)
                pass
        elif is_set(input_buffer[2], 0):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.prograde
            except RuntimeError:
                conn.ui.message('SAS Mode - Prograde - Not Available', duration=3)
                pass
        else:
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.stability_assist
            except RuntimeError:
                conn.ui.message('SAS Mode - Stability Assist - Not Available', duration=3)
                pass


def flight_control_inputs(input_buffer, vessel, trim):

    # Trims
    if is_set(input_buffer[1], 0):
        trim[0] = max(trim[0] - Settings.c_trim_mod_rate, -1)
    if is_set(input_buffer[1], 1):
        trim[0] = min(trim[0] + Settings.c_trim_mod_rate, 1)
    if is_set(input_buffer[1], 6):
        trim[1] = max(trim[1] - Settings.c_trim_mod_rate, -1)
    if is_set(input_buffer[1], 5):
        trim[1] = min(trim[1] + Settings.c_trim_mod_rate, 1)
    if is_set(input_buffer[1], 2):
        trim[2] = max(trim[2] - Settings.c_trim_mod_rate, -1)
    if is_set(input_buffer[1], 3):
        trim[2] = min(trim[2] + Settings.c_trim_mod_rate, 1)

    if is_set(input_buffer[1], 4):
        trim[0] = 0
        trim[1] = 0
        trim[2] = 0

    # Flight Controls
    if is_set(input_buffer[4], 0):
        x_fctl_fine = Settings.c_fctl_fine
    else:
        x_fctl_fine = 1

    if is_set(input_buffer[5], 0):  # EVA FC Mode - todo fix EVA controls!!!
        (pitch_raw, pitch) = (0, 0)
        (yaw_raw, yaw) = (0, 0)
        (roll_raw, roll) = (0, 0)
        (up_raw, up) = (0, 0)
        (right_raw, right) = (0, 0)
        (forward_raw, forward) = (0, 0)
        (wheel_steering_raw, wheel_steering) = (0, 0)
        (wheel_throttle_raw, wheel_throttle) = (0, 0)

    elif is_set(input_buffer[5], 1):  # ROVER FC Mode
        (pitch_raw, pitch) = map_flt_ctl(input_buffer[11], Settings.c_fctl_db, trim[0], x_fctl_fine)
        (yaw_raw, yaw) = map_flt_ctl(input_buffer[12], Settings.c_fctl_db, trim[1], x_fctl_fine)
        (roll_raw, roll) = map_flt_ctl(input_buffer[13], Settings.c_fctl_db, trim[2], x_fctl_fine)
        (up_raw, up) = (0, 0)
        (right_raw, right) = (0, 0)
        (forward_raw, forward) = (0, 0)
        (wheel_steering_raw, wheel_steering) = map_flt_ctl(input_buffer[15], Settings.c_fctl_db, 0, x_fctl_fine)
        (wheel_throttle_raw, wheel_throttle) = map_flt_ctl(input_buffer[14], Settings.c_fctl_db, 0, x_fctl_fine)

    elif is_set(input_buffer[5], 2):  # ATMOS FC Mode
        (pitch_raw, pitch) = map_flt_ctl(input_buffer[11], Settings.c_fctl_db, trim[0], x_fctl_fine)
        (yaw_raw, yaw) = map_flt_ctl(input_buffer[13], Settings.c_fctl_db, trim[1], x_fctl_fine)
        (roll_raw, roll) = map_flt_ctl(input_buffer[12], Settings.c_fctl_db, trim[2], x_fctl_fine)
        (up_raw, up) = (0, 0)
        (right_raw, right) = (0, 0)
        (forward_raw, forward) = (0, 0)
        if is_set(input_buffer[3], 2):  # NWS ON
            (wheel_steering_raw, wheel_steering) = map_flt_ctl(input_buffer[15], Settings.c_fctl_db, 0, x_fctl_fine)
        else:
            (wheel_steering_raw, wheel_steering) = (0, 0)
        (wheel_throttle_raw, wheel_throttle) = (0, 0)

    elif is_set(input_buffer[5], 3):  # ORBIT FC Mode
        (pitch_raw, pitch) = map_flt_ctl(input_buffer[11], Settings.c_fctl_db, trim[0], x_fctl_fine)
        (yaw_raw, yaw) = map_flt_ctl(input_buffer[12], Settings.c_fctl_db, trim[1], x_fctl_fine)
        (roll_raw, roll) = map_flt_ctl(input_buffer[13], Settings.c_fctl_db, trim[2], x_fctl_fine)
        (up_raw, up) = map_flt_ctl(input_buffer[14], Settings.c_fctl_db, 0, x_fctl_fine)
        (right_raw, right) = map_flt_ctl(input_buffer[15], Settings.c_fctl_db, 0, x_fctl_fine)
        (forward_raw, forward) = map_flt_ctl(input_buffer[16], Settings.c_fctl_db, 0, x_fctl_fine)
        (wheel_steering_raw, wheel_steering) = (0, 0)
        (wheel_throttle_raw, wheel_throttle) = (0, 0)

    else:  # FC Mode is OFF
        (pitch_raw, pitch) = (0, 0)
        (yaw_raw, yaw) = (0, 0)
        (roll_raw, roll) = (0, 0)
        (up_raw, up) = (0, 0)
        (right_raw, right) = (0, 0)
        (forward_raw, forward) = (0, 0)
        (wheel_steering_raw, wheel_steering) = (0, 0)
        (wheel_throttle_raw, wheel_throttle) = (0, 0)

    vessel.control.pitch = pitch
    vessel.control.yaw = yaw
    vessel.control.roll = roll
    vessel.control.up = up
    vessel.control.right = right
    vessel.control.forward = forward
    vessel.control.wheel_steering = wheel_steering

    # Throttle
    throttle_mode = 0
    if is_set(input_buffer[5], 4):
        throttle_mode = 1
    if is_set(input_buffer[5], 5):
        throttle_mode = 0.75
    if is_set(input_buffer[5], 6):
        throttle_mode = 0.5
    if is_set(input_buffer[5], 7):
        throttle_mode = 0.25

    if is_set(input_buffer[5], 1):  # ROVER FC Mode - throttle used to set steady fwd power but stick overrides.
        if -wheel_throttle < 0:
            vessel.control.wheel_throttle = -wheel_throttle
        else:
            vessel.control.wheel_throttle = max(-wheel_throttle, input_buffer[17] / 255 * throttle_mode)
        vessel.control.throttle = 0
    else:
        vessel.control.wheel_throttle = 0
        vessel.control.throttle = input_buffer[17] / 255 * throttle_mode

    # return if controls in use so SAS can be overridden
    return(abs(pitch_raw) > Settings.c_fctl_db or
           abs(roll_raw) > Settings.c_fctl_db or
           abs(yaw_raw) > Settings.c_fctl_db)
