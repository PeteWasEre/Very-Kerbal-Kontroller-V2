import krpc

from Utilities import is_set, map_flt_ctl
import Settings


def SAS_inputs(input_buffer, input_buffer_prev, vessel, mQ, sas_overide):
    if sas_overide:
        vessel.control.sas = False
    elif is_set(input_buffer[9], 2) != is_set(input_buffer_prev[9], 2) or not sas_overide:
        vessel.control.sas = is_set(input_buffer[9], 2)

    # need to handle exceptions here, not all modes are available at all times.
    if is_set(input_buffer[9], 1) and not is_set(input_buffer_prev[9], 1):  # SAS Set requested
        if is_set(input_buffer[8], 0):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.maneuver
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set SAS Mode - Maneuver'))
                pass
        elif is_set(input_buffer[8], 1):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.anti_target
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set SAS Mode - Anti-Target'))
                pass
        elif is_set(input_buffer[8], 2):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.target
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set SAS Mode - Target'))
                pass
        elif is_set(input_buffer[8], 3):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.anti_radial
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set SAS Mode - Anti-Radial'))
                pass
        elif is_set(input_buffer[8], 4):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.radial
            except krpc.client.RPCError:
                mQ.put((1, 'ould not set SAS Mode - Radial'))
                pass
        elif is_set(input_buffer[8], 5):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.anti_normal
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set SAS Mode - Anti-Normal'))
                pass
        elif is_set(input_buffer[8], 6):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.normal
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set SAS Mode - Normal'))
                pass
        elif is_set(input_buffer[8], 7):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.retrograde
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set SAS Mode - Retrograde'))
                pass
        elif is_set(input_buffer[9], 0):
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.prograde
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set SAS Mode - Prograde'))
                pass
        else:
            try:
                vessel.control.sas_mode = vessel.control.sas_mode.stability_assist
            except krpc.client.RPCError:
                mQ.put((1, 'Error: Could not set SAS Mode - Stability Assist'))
                pass


def flight_control_inputs(input_buffer, vessel, trim, thr_inhib):

    # Trims
    if is_set(input_buffer[10], 1):
        trim[0] = max(trim[0] - Settings.c_trim_mod_rate, -1)
    if is_set(input_buffer[10], 2):
        trim[0] = min(trim[0] + Settings.c_trim_mod_rate, 1)
    if is_set(input_buffer[10], 3):
        trim[1] = max(trim[1] - Settings.c_trim_mod_rate, -1)
    if is_set(input_buffer[10], 4):
        trim[1] = min(trim[1] + Settings.c_trim_mod_rate, 1)
    if is_set(input_buffer[10], 5):
        trim[2] = max(trim[2] - Settings.c_trim_mod_rate, -1)
    if is_set(input_buffer[10], 6):
        trim[2] = min(trim[2] + Settings.c_trim_mod_rate, 1)

    if is_set(input_buffer[10], 0):
        trim[0] = 0
        trim[1] = 0
        trim[2] = 0

    # Flight Controls
    if is_set(input_buffer[7], 6):
        x_fctl_fine = Settings.c_fctl_fine
    else:
        x_fctl_fine = 1

    if is_set(input_buffer[7], 2):  # EVA FC Mode - todo fix EVA controls!!!
        pitch = map_flt_ctl(input_buffer[20], Settings.c_fctl_db, trim[0], x_fctl_fine)
        yaw = map_flt_ctl(input_buffer[21], Settings.c_fctl_db, trim[1], x_fctl_fine)
        roll = map_flt_ctl(input_buffer[22], Settings.c_fctl_db, trim[2], x_fctl_fine)
        up = map_flt_ctl(input_buffer[23], Settings.c_fctl_db, 0, x_fctl_fine)
        right = map_flt_ctl(input_buffer[24], Settings.c_fctl_db, 0, x_fctl_fine)
        forward = map_flt_ctl(input_buffer[25], Settings.c_fctl_db, 0, x_fctl_fine)
        wheel_steering = 0
        wheel_throttle = 0

    elif is_set(input_buffer[7], 3):  # ROVER FC Mode
        pitch = map_flt_ctl(input_buffer[20], Settings.c_fctl_db, trim[0], x_fctl_fine)
        yaw = map_flt_ctl(input_buffer[21], Settings.c_fctl_db, trim[1], x_fctl_fine)
        roll = map_flt_ctl(input_buffer[22], Settings.c_fctl_db, trim[2], x_fctl_fine)
        up = 0
        right = 0
        forward = 0
        wheel_steering = map_flt_ctl(input_buffer[24], Settings.c_fctl_db, 0, x_fctl_fine)
        wheel_throttle = -map_flt_ctl(input_buffer[23], Settings.c_fctl_db, 0, x_fctl_fine)

    elif is_set(input_buffer[7], 4):  # ATMOS FC Mode
        pitch = map_flt_ctl(input_buffer[20], Settings.c_fctl_db, trim[0], x_fctl_fine)
        yaw = map_flt_ctl(input_buffer[22], Settings.c_fctl_db, trim[1], x_fctl_fine)
        roll = map_flt_ctl(input_buffer[21], Settings.c_fctl_db, trim[2], x_fctl_fine)
        up = 0
        right = 0
        forward = 0
        if is_set(input_buffer[11], 3):  # NWS ON
            wheel_steering = map_flt_ctl(input_buffer[24], Settings.c_fctl_db, 0, x_fctl_fine)
        else:
            wheel_steering = 0
        wheel_throttle = 0

    elif is_set(input_buffer[7], 5):  # ORBIT FC Mode
        pitch = map_flt_ctl(input_buffer[20], Settings.c_fctl_db, trim[0], x_fctl_fine)
        yaw = map_flt_ctl(input_buffer[21], Settings.c_fctl_db, trim[1], x_fctl_fine)
        roll = map_flt_ctl(input_buffer[22], Settings.c_fctl_db, trim[2], x_fctl_fine)
        up = map_flt_ctl(input_buffer[23], Settings.c_fctl_db, 0, x_fctl_fine)
        right = map_flt_ctl(input_buffer[24], Settings.c_fctl_db, 0, x_fctl_fine)
        forward = map_flt_ctl(input_buffer[25], Settings.c_fctl_db, 0, x_fctl_fine)
        wheel_steering = 0
        wheel_throttle = 0

    else:  # FC Mode is OFF
        pitch = 0
        yaw = 0
        roll = 0
        up = 0
        right = 0
        forward = 0
        wheel_steering = 0
        wheel_throttle = 0

    vessel.control.pitch = pitch
    vessel.control.yaw = yaw
    vessel.control.roll = roll
    vessel.control.up = up
    vessel.control.right = right
    vessel.control.forward = forward
    vessel.control.wheel_steering = wheel_steering
    vessel.control.wheel_throttle = wheel_throttle

    # Throttle
    throttle_mode = 0
    if is_set(input_buffer[9], 3):
        throttle_mode = 1
    if is_set(input_buffer[9], 4):
        throttle_mode = 0.75
    if is_set(input_buffer[9], 5):
        throttle_mode = 0.5
    if is_set(input_buffer[9], 6):
        throttle_mode = 0.25

    if not thr_inhib:
        if is_set(input_buffer[7], 3):  # ROVER FC Mode - throttle used to set steady fwd power but stick overrides.
            if vessel.control.wheel_throttle >= 0:
                vessel.control.wheel_throttle = max(vessel.control.wheel_throttle, input_buffer[26] / 255 * throttle_mode)
            vessel.control.throttle = 0
        else:
            vessel.control.wheel_throttle = 0
            vessel.control.throttle = input_buffer[26] / 255 * throttle_mode

    # return if controls in use so SAS can be overidden
    return (abs(pitch + abs(roll) + abs(yaw))) != 0


def camera_inputs(cam, input_buffer, mQ):

    # todo - fix camera distance and defaults
    if is_set(input_buffer[3], 3):
        cam.pitch = max(cam.pitch - Settings.c_camera_angle_rate, cam.min_pitch)
    if is_set(input_buffer[3], 5):
        cam.pitch = min(cam.pitch + Settings.c_camera_angle_rate, cam.max_pitch)
    if is_set(input_buffer[3], 7):
        cam.heading += Settings.c_camera_angle_rate
    if is_set(input_buffer[4], 1):
        cam.heading -= Settings.c_camera_angle_rate
    if is_set(input_buffer[4], 3):
        if cam.mode == cam.mode.map:
            cam.distance = max(cam.distance - Settings.c_camera_map_dist_rate, cam.min_distance)
        else:
            cam.distance = max(cam.distance - Settings.c_camera_dist_rate, cam.min_distance)
    if is_set(input_buffer[4], 5):
        if cam.mode == cam.mode.map:
            cam.distance = min(cam.distance + Settings.c_camera_map_dist_rate, cam.max_distance)
        else:
            cam.distance = min(cam.distance + Settings.c_camera_dist_rate, cam.max_distance)

    if is_set(input_buffer[2], 3) or Settings.G_cam_change_timer == 0:  # todo fix the setting of default distance
        try:
            cam.distance = cam.default_distance
            Settings.G_cam_change_timer = -1.0
        except krpc.client.RPCError:
            mQ.put((1, 'Could not set camera distance'))
            # todo - set default camera pitch and heading

    if is_set(input_buffer[3], 2):
        if cam.mode != cam.mode.iva:
            try:
                cam.mode = cam.mode.iva
                Settings.G_cam_change_timer = Settings.c_cam_change_time
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set Camera Mode - IVA'))
                pass
    elif is_set(input_buffer[3], 4):
        if cam.mode != cam.mode.map:
            try:
                cam.mode = cam.mode.map
                Settings.G_cam_change_timer = Settings.c_cam_change_time
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set Camera Mode - Map'))
                pass
    elif is_set(input_buffer[3], 6):
        if cam.mode != cam.mode.automatic:
            try:
                cam.mode = cam.mode.automatic
                Settings.G_cam_change_timer = Settings.c_cam_change_time
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set Camera Mode - Automatic'))
                pass
    elif is_set(input_buffer[4], 0):
        if cam.mode != cam.mode.chase:
            try:
                cam.mode = cam.mode.chase
                Settings.G_cam_change_timer = Settings.c_cam_change_time
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set Camera Mode - Chase'))
                pass
    elif is_set(input_buffer[4], 2):
        if cam.mode != cam.mode.locked:
            try:
                cam.mode = cam.mode.locked
                Settings.G_cam_change_timer = Settings.c_cam_change_time
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set Camera Mode - Locked'))
                pass
    elif is_set(input_buffer[4], 4):
        if cam.mode != cam.mode.orbital:
            try:
                cam.mode = cam.mode.orbital
                Settings.G_cam_change_timer = Settings.c_cam_change_time
            except krpc.client.RPCError:
                mQ.put((1, 'Could not set Camera Mode - Orbital'))
                pass
    elif cam.mode != cam.mode.free:
        try:
            cam.mode = cam.mode.free
            Settings.G_cam_change_timer = Settings.c_cam_change_time
        except krpc.client.RPCError:
            mQ.put((1, 'Could not set Camera Mode - Free'))
            pass
