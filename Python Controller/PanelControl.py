import serial
import krpc
import time
import operator

from Settings import *
from Utilities import is_set, norm
from OutputFunctions import output_mapping
from InputFunctions import sas_inputs, flight_control_inputs
from LandingGuidance import ldg_guidance_init, ldg_guidance_draw, ldg_guidance_clear
from CNIA import cnia


def panel_control(data_array, mq):
    # initialise variables that need a starting state.
    n_program_state = 1
    t_quickload_timer = 0
    t_frame_start_time = time.time()
    ba_input_buffer = bytearray()
    f_first_pass = 1
    x_trim = [0, 0, 0]
    sas_overide = 0
    gear_status = 0
    heartbeat = 0

    while 1:
        if time.time() - t_frame_start_time >= c_loop_frame_rate:
            # record the start of the processing so we can get timing data
            t_frame_start_time = time.time()

            # STATE = PANEL CONN - Connect to the panel
            if n_program_state == 1:
                mq.put((0, 'Connecting to the panel....'))
                try:
                    ser = serial.Serial('COM3', 115200, timeout=0.1)
                    mq.put((0, 'Connected to the panel'))
                    time.sleep(1)  # serial needs a  bit of time to initialise, otherwise later code - esp CNIA fails
                    n_program_state = 2
                except serial.serialutil.SerialException:
                    mq.put((1, 'Could not connect to the panel'))
                    time.sleep(5)  # to avoid spamming the message queue
                    pass

            # STATE = GAME CONN - Connect to the KRPC Server
            if n_program_state == 2:
                mq.put((0, 'Connecting to the game server....'))
                try:
                    conn = krpc.connect(name='Game Controller')
                    mq.put((0, 'Connected to the game server'))
                    n_program_state = 3
                except ConnectionRefusedError:
                    mq.put((1, 'Could not connect to the game server'))
                    pass

            # STATE = LINKING - Link to the active Vessel
            if n_program_state == 3 and conn.krpc.current_game_scene == conn.krpc.current_game_scene.flight:
                mq.put((0, 'Connecting to the vessel....'))
                try:
                    vessel = conn.space_center.active_vessel
                    mq.put((0, 'Linked to ' + vessel.name))
                    n_program_state = 4
                except krpc.client.RPCError:
                    mq.put((1, 'Could not connect to a vessel'))
                    pass

            # STATE = Perform CNIA
            if n_program_state == 4:
                mq.put((0, 'Starting CNIA...'))
                cnia(ser, conn, vessel)
                mq.put((0, 'CNIA Complete'))
                n_program_state = 5

            # STATE = Streams and objects- setup data input streams and reused objects
            if n_program_state == 5:
                # Camera object
                cam = conn.space_center.camera

                # Create the camera mode list and set the initial index
                cam_modes = [cam.mode.automatic, cam.mode.free, cam.mode.chase, cam.mode.locked, cam.mode.orbital]
                cam_index = 0

                # Gear Status - only add deployable legs and wheels.
                gear_status = []
                temp = []

                for x in vessel.parts.wheels:
                    if x.deployable:
                        temp.append(conn.add_stream(getattr, x, 'state'))

                gear_status.append(temp)

                temp = []
                for x in vessel.parts.legs:
                    if x.deployable:
                        temp.append(conn.add_stream(getattr, x, 'state'))

                gear_status.append(temp)

                # Vessel and body list for map mode focus switching
                sorted_bodies = sorted(conn.space_center.bodies.items(), key=operator.itemgetter(1))
                map_view_list = [(vessel.name, vessel)]
                map_view_list.extend(sorted_bodies)

                # set the initial map index
                map_idx = 0

                # initialise the landing reference frame
                landing_reference_frame = ldg_guidance_init(conn, vessel)

                # reset the frame start time to avoid a false overun
                t_frame_start_time = time.time()

                f_first_pass = 1

                mq.put((0, 'Stream setup complete'))
                n_program_state = 6

            # STATE = RUNNING
            if n_program_state == 6:
                try:  # catch RPC errors as they generally result from a scene change. Make more specific KRPC issue 256

                    # Send data to the arduino request it to process inputs  - command byte = 0x00
                    ba_output_buffer = bytearray([0x00])
                    ser.write(ba_output_buffer)

                    # Now while the Arduino is busy with inputs we processes the outputs - command byte = 0x01
                    ba_output_buffer = bytearray([0x01])
                    output_mapping(ba_output_buffer, conn, gear_status, sas_overide)

                    # Make sure the Arduino has responded
                    while ser.in_waiting != c_input_buffer_size:
                        pass

                    # read back the data from the arduino
                    ba_input_buffer_prev = ba_input_buffer
                    ba_input_buffer = ser.read(c_input_buffer_size)

                    # Now send the output date we calculated earlier
                    ser.write(ba_output_buffer)

                    if f_first_pass:  # On the first pass copy the data in to avoid an error.
                        ba_input_buffer_prev = ba_input_buffer
                        heartbeat = 0
                        f_first_pass = 0

                    # Check the status of the Arduino
                    if ba_input_buffer[0] == 1:  # status of 00000011 is fully powered

                        # Action Groups
                        if is_set(ba_input_buffer[6], 3) and not is_set(ba_input_buffer_prev[6], 3):
                            vessel.control.toggle_action_group(6)
                        if is_set(ba_input_buffer[6], 4) and not is_set(ba_input_buffer_prev[6], 4):
                            vessel.control.toggle_action_group(7)
                        if is_set(ba_input_buffer[6], 5) and not is_set(ba_input_buffer_prev[6], 5):
                            vessel.control.toggle_action_group(8)
                        if is_set(ba_input_buffer[6], 6) and not is_set(ba_input_buffer_prev[6], 6):
                            vessel.control.toggle_action_group(9)
                        if is_set(ba_input_buffer[6], 7) and not is_set(ba_input_buffer_prev[6], 7):
                            vessel.control.toggle_action_group(0)
                        if is_set(ba_input_buffer[7], 0) and not is_set(ba_input_buffer_prev[7], 0):
                            vessel.control.toggle_action_group(1)
                        if is_set(ba_input_buffer[7], 1) and not is_set(ba_input_buffer_prev[7], 1):
                            vessel.control.toggle_action_group(2)
                        if is_set(ba_input_buffer[7], 2) and not is_set(ba_input_buffer_prev[7], 2):
                            vessel.control.toggle_action_group(3)
                        if is_set(ba_input_buffer[7], 3) and not is_set(ba_input_buffer_prev[7], 3):
                            vessel.control.toggle_action_group(4)
                        if is_set(ba_input_buffer[7], 4) and not is_set(ba_input_buffer_prev[7], 4):
                            vessel.control.toggle_action_group(5)

                        # Staging
                        if is_set(ba_input_buffer[4], 1) and not is_set(ba_input_buffer_prev[4], 1):
                            vessel.control.activate_next_stage()
                            n_program_state = 5  # trigger a stream refresh!
                            # todo do we need this for decouple?

                        # Systems
                        if is_set(ba_input_buffer[4], 6) != is_set(ba_input_buffer_prev[4], 6):
                            vessel.control.lights = is_set(ba_input_buffer[4], 6)
                        if is_set(ba_input_buffer[3], 3) != is_set(ba_input_buffer_prev[3], 3):
                            vessel.control.rcs = is_set(ba_input_buffer[3], 3)
                        if is_set(ba_input_buffer[3], 0) != is_set(ba_input_buffer_prev[3], 0):
                            vessel.control.gear = not is_set(ba_input_buffer[3], 0)  # gear is opposite sense
                        if is_set(ba_input_buffer[4], 2) != is_set(ba_input_buffer_prev[4], 2) or \
                                (is_set(ba_input_buffer[3], 1) != is_set(ba_input_buffer_prev[3], 1)):
                            vessel.control.brakes = is_set(ba_input_buffer[4], 2) or is_set(ba_input_buffer[3], 1)

                        # Navball Mode
                        if is_set(ba_input_buffer[4], 7):
                            vessel.control.speed_mode = vessel.control.speed_mode.orbit
                        elif is_set(ba_input_buffer[3], 5):
                            vessel.control.speed_mode = vessel.control.speed_mode.surface
                        else:
                            vessel.control.speed_mode = vessel.control.speed_mode.target

                        # Landing Guidance
                        if is_set(ba_input_buffer[4], 5) and not is_set(ba_input_buffer_prev[4], 5):
                            ldg_guidance_draw(conn, landing_reference_frame, c_ils_dist_scale)  # High Scale
                        elif (is_set(ba_input_buffer_prev[4], 5) and not is_set(ba_input_buffer[4], 5) or
                              is_set(ba_input_buffer_prev[4], 4) and not is_set(ba_input_buffer[4], 4)):
                            ldg_guidance_draw(conn, landing_reference_frame, 1)  # Low Scale
                        elif is_set(ba_input_buffer[4], 4) and not is_set(ba_input_buffer_prev[4], 4):
                            ldg_guidance_clear(conn)

                        # Flight Control and Trims
                        sas_overide_prev = sas_overide
                        sas_overide = flight_control_inputs(ba_input_buffer, vessel, x_trim)

                        # SAS
                        sas_inputs(ba_input_buffer, ba_input_buffer_prev, vessel, conn, sas_overide, sas_overide_prev)

                        # Save/Load/Pause
                        if is_set(ba_input_buffer[7], 7) and not is_set(ba_input_buffer_prev[7], 7):
                            conn.space_center.quicksave()
                            conn.ui.message('Quicksaving...', duration=5)

                        if is_set(ba_input_buffer[7], 6) and not is_set(ba_input_buffer_prev[7], 6):
                            t_quickload_timer = time.time() + 5
                            conn.ui.message('Hold for 5 seconds to Quickload...', duration=5)

                        if not is_set(ba_input_buffer[7], 6):
                            t_quickload_timer = 0

                        if time.time() >= t_quickload_timer > 0:
                            conn.space_center.quickload()

                        if is_set(ba_input_buffer[7], 5) and not is_set(ba_input_buffer_prev[7], 5):
                            conn.krpc.paused = not conn.krpc.paused

                        # Warp
                        if is_set(ba_input_buffer[8], 5):
                            conn.space_center.physics_warp_factor = 0
                            conn.space_center.rails_warp_factor = 0
                        elif is_set(ba_input_buffer[8], 1) and not is_set(ba_input_buffer_prev[8], 1) and \
                                conn.space_center.physics_warp_factor == 0:
                            conn.space_center.rails_warp_factor = min(conn.space_center.rails_warp_factor + 1,
                                                                      conn.space_center.maximum_rails_warp_factor)
                        elif is_set(ba_input_buffer[8], 2) and not is_set(ba_input_buffer_prev[8], 2):
                            conn.space_center.rails_warp_factor = max(conn.space_center.rails_warp_factor - 1, 0)
                        elif is_set(ba_input_buffer[8], 3) and not is_set(ba_input_buffer_prev[8], 3) and \
                                conn.space_center.rails_warp_factor == 0:
                            conn.space_center.physics_warp_factor = min(conn.space_center.physics_warp_factor + 1, 3)
                        elif is_set(ba_input_buffer[8], 4) and not is_set(ba_input_buffer_prev[8], 4):
                            conn.space_center.physics_warp_factor = max(conn.space_center.physics_warp_factor - 1, 0)

                        # Clear Target
                        if is_set(ba_input_buffer[4], 3) and not is_set(ba_input_buffer_prev[4], 3):
                            conn.space_center.clear_target()

                        # Camera Control
                        if is_set(ba_input_buffer[9], 4) and not is_set(ba_input_buffer_prev[9], 4):
                            cam.mode = cam.mode.map
                        elif is_set(ba_input_buffer[9], 1) and not is_set(ba_input_buffer_prev[9], 1):
                            cam.mode = cam.mode.automatic
                            cam_index = 0
                            cam.distance = cam.default_distance
                        elif ((is_set(ba_input_buffer_prev[9], 1) and not is_set(ba_input_buffer[9], 1)) or
                              (is_set(ba_input_buffer_prev[9], 4) and not is_set(ba_input_buffer[9], 4))):
                            cam.mode = cam.mode.iva

                        if cam.mode == cam.mode.map:
                            # Map focus
                            if is_set(ba_input_buffer[9], 6) and not is_set(ba_input_buffer_prev[9], 6):
                                map_test = True
                                while map_test:
                                    map_idx = (map_idx + 1) % len(map_view_list)
                                    if map_idx == 0:  # vessel
                                        cam.focussed_vessel = vessel
                                        map_test = False
                                    else:
                                        cam.focussed_body = map_view_list[map_idx][1]
                                        if cam.focussed_body is not None:
                                            map_test = False
                                cam.distance = cam.default_distance
                            if is_set(ba_input_buffer[9], 5) and not is_set(ba_input_buffer_prev[9], 5):
                                map_test = True
                                while map_test:
                                    map_idx = (map_idx - 1) % len(map_view_list)
                                    if map_idx == 0:  # vessel
                                        cam.focussed_vessel = vessel
                                        map_test = False
                                    else:
                                        cam.focussed_body = map_view_list[map_idx][1]
                                        if cam.focussed_body is not None:
                                            map_test = False
                                cam.distance = cam.default_distance

                            if is_set(ba_input_buffer[9], 7) and not is_set(ba_input_buffer_prev[9], 7):
                                # always reset to te current vessel
                                cam.focussed_vessel = vessel
                                cam.distance = cam.default_distance

                        elif cam.mode == cam.mode.iva:
                            pass
                        else:
                            # Camera Modes
                            if is_set(ba_input_buffer[8], 6) and not is_set(ba_input_buffer_prev[8], 6):
                                cam_test = True
                                while cam_test:  # iterate to skip over modes unavailable
                                    cam_index = (cam_index + 1) % len(cam_modes)
                                    cam.mode = cam_modes[cam_index]
                                    cam_test = cam.mode != cam_modes[cam_index]
                                cam.distance = cam.default_distance

                            if is_set(ba_input_buffer[8], 7) and not is_set(ba_input_buffer_prev[8], 7):
                                cam_test = True
                                while cam_test:  # iterate to skip over modes unavailable
                                    cam_index = (cam_index - 1) % len(cam_modes)
                                    cam.mode = cam_modes[cam_index]
                                    cam_test = cam.mode != cam_modes[cam_index]
                                cam.distance = cam.default_distance

                        # Vessel Switch
                        if is_set(ba_input_buffer[9], 3) and not is_set(ba_input_buffer_prev[9], 3):
                            vessel_list = [v for v in conn.space_center.vessels
                                           if norm(v.position(vessel.reference_frame)) < c_vessel_sw_dist]
                            conn.space_center.active_vessel = \
                                vessel_list[(vessel_list.index(vessel) + 1) % len(vessel_list)]
                            n_program_state = 3
                        elif is_set(ba_input_buffer[9], 2) and not is_set(ba_input_buffer_prev[9], 2):
                            vessel_list = [v for v in conn.space_center.vessels if
                                           norm(v.position(vessel.reference_frame)) < c_vessel_sw_dist]
                            conn.space_center.active_vessel = \
                                vessel_list[(vessel_list.index(vessel) - 1) % len(vessel_list)]
                            n_program_state = 3

                        # put all the data onto the shared array for use by the GUI
                        for i in range(len(ba_input_buffer)):
                            data_array[i] = ba_input_buffer[i]

                        # add a hearbeat to the status bit so the GUI can tell if we are alive
                        heartbeat = (heartbeat + 1) % 8
                        data_array[0] = data_array[0] | heartbeat << 2

                except krpc.client.RPCError:
                    n_program_state = 3
                    mq.put((1, 'Main Loop Error'))

            # Check for Overuns and send a warning.
            frame_time = (time.time() - t_frame_start_time)
            if frame_time > c_loop_frame_rate * 1.1:
                mq.put((1, 'OVERUN - ' + str(int(frame_time * 1000)) + 'ms'))
            data_array[19] = int(frame_time*1000)
