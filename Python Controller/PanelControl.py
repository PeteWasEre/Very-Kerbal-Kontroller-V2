import serial
import krpc
import time
import operator

import Settings
from Utilities import is_set, norm
from OutputFunctions import output_mapping
from InputFunctions import SAS_inputs, flight_control_inputs, camera_inputs
from LandingGuidance import ldg_guidance_draw, ldg_guidance_clear
from CNIA import cnia
from Autopilot import Autopilot


def panel_control(data_array, mQ):
    n_program_state = 1
    t_quickload_timer = 0
    t_frame_start_time = time.time()
    BA_input_buffer = bytearray()
    f_first_pass = 1
    x_trim = [0, 0, 0]
    throttle_inhib = False
    spd_err = 0
    spd_err_p = 0

    while 1:
        if time.time() - t_frame_start_time >= Settings.c_loop_frame_rate:
            # record the start of the processing so we can get timing data
            t_frame_start_time = time.time()

            # STATE = PANEL CONN - Connect to the panel
            if n_program_state == 1:
                mQ.put((0, 'Connecting to the panel....'))
                try:
                    ser = serial.Serial('COM3', 115200, timeout=0.1)
                    mQ.put((0, 'Connected to the panel'))
                    time.sleep(1)  # serial needs a little bit of time to initialise, otherwise later code - esp CNIA fails
                    n_program_state = 2
                except serial.serialutil.SerialException:
                    mQ.put((1, 'Could not connect to the panel'))
                    time.sleep(5)  # to avoid spamming the message queue
                    pass

            # STATE = GAME CONN - Connect to the KRPC Server
            if n_program_state == 2:
                mQ.put((0, 'Connecting to the game server....'))
                try:
                    conn = krpc.connect(name='Game Controller')
                    mQ.put((0, 'Connected to the game server'))
                    n_program_state = 3
                except ConnectionRefusedError:
                    mQ.put((1, 'Could not connect to the game server'))
                    pass

            # STATE = LINKING - Link to the active Vessel
            if n_program_state == 3 and conn.krpc.current_game_scene == conn.krpc.current_game_scene.flight:
                mQ.put((0, 'Connecting to the vessel....'))
                try:
                    vessel = conn.space_center.active_vessel
                    mQ.put((0, 'Linked to ' + vessel.name))
                    n_program_state = 4
                except krpc.client.RPCError:
                    mQ.put((1, 'Could not connect to a vessel'))
                    pass

            # STATE = Perform CNIA
            if n_program_state == 4:
                mQ.put((0, 'Starting CNIA...'))
                cnia(ser, conn, vessel)
                mQ.put((0, 'CNIA Complete'))
                n_program_state = 5

            # STATE = Streams and objects- setup data input streams and reused objects
            if n_program_state == 5:
                # Camera object
                cam = conn.space_center.camera

                # Part temperatures
                part_temp_list = []
                for x in vessel.parts.all:
                    temp = [conn.add_stream(getattr, x, 'temperature'), x.max_temperature, conn.add_stream(getattr, x, 'skin_temperature'), x.max_skin_temperature]
                    part_temp_list.append(temp)

                # Engine propellant status
                engine_propellant_status = []

                for x in [item for sublist in [p.propellants for p in vessel.parts.engines] for item in sublist]:
                    temp = [conn.add_stream(getattr, x, 'total_resource_available'), conn.add_stream(getattr, x, 'total_resource_capacity')]
                    engine_propellant_status.append(temp)

                # Monoprop and electricity status
                resources = vessel.resources_in_decouple_stage(vessel.control.current_stage)

                mono_status = [conn.add_stream(resources.amount, 'MonoPropellant'), conn.add_stream(resources.max, 'MonoPropellant')]

                elec_status = [conn.add_stream(resources.amount, 'ElectricCharge'), conn.add_stream(resources.max, 'ElectricCharge')]

                # Gear Status
                gear_status = []

                temp = []
                for x in vessel.parts.landing_gear:
                    temp.append(conn.add_stream(getattr, x, 'state'))

                gear_status.append(temp)
                temp = []
                for x in vessel.parts.landing_legs:
                    temp.append(conn.add_stream(getattr, x, 'state'))

                gear_status.append(temp)

                # Vessel and body list for map mode focus switching
                sorted_bodies = sorted(conn.space_center.bodies.items(), key=operator.itemgetter(1))
                map_view_list = [(vessel.name, vessel)]
                map_view_list.extend(sorted_bodies)

                mQ.put((0, 'Stream setup complete'))
                n_program_state = 6

            # STATE = RUNNING
            if n_program_state == 6:
                try:  # catch RPC errors as they generally result from a scene change. Make more specific KRPC issue 256

                    # Send data to the arduino request it to process inputs  - command byte = 0x00
                    BA_output_buffer = bytearray([0x00, 0x00, 0x00])
                    ser.write(BA_output_buffer)

                    # Now while the Arduino is busy with inputs we processes the outputs - comamand byte = 0x01
                    BA_output_buffer = bytearray([0x01, 0x00, 0x00])
                    output_mapping(BA_output_buffer, conn, part_temp_list, engine_propellant_status, mono_status, elec_status, gear_status)

                    # Make sure the Arduino has responded
                    while ser.in_waiting != 40:
                        pass

                    # read back the data from the arduino
                    BA_input_buffer_prev = BA_input_buffer
                    BA_input_buffer = ser.read(40)

                    # Now send the output date we calculated earlier
                    ser.write(BA_output_buffer)

                    if f_first_pass:  # On the first pass copy the data in to avoid an error.
                        BA_input_buffer_prev = BA_input_buffer
                        f_first_pass = 0

                    # Check the status of the Arduino
                    if BA_input_buffer[0] == 3:  # status of 00000011 is fully powered

                        # Action Groups
                        for i in range(0, 10):
                            if is_set(BA_input_buffer[int(i / 8) + 6], i % 8) and not is_set(BA_input_buffer_prev[int(i / 8) + 6], i % 8):
                                vessel.control.toggle_action_group((i + 1) % 10)

                        if is_set(BA_input_buffer[11], 7) and not is_set(BA_input_buffer_prev[11], 7):  # todo - Remove this when mux 0 pin A3 is resolved
                            vessel.control.toggle_action_group(3)

                        # Staging
                        if is_set(BA_input_buffer[7], 7) and not is_set(BA_input_buffer_prev[7], 7) and is_set(BA_input_buffer[9], 7):
                            vessel.control.activate_next_stage()
                            n_program_state = 5  # trigger a stream refresh!
                            # todo do we need this for decouple?

                        # Systems
                        if is_set(BA_input_buffer[11], 1) != is_set(BA_input_buffer_prev[11], 1):
                            vessel.control.lights = is_set(BA_input_buffer[11], 1)
                        if is_set(BA_input_buffer[11], 2) != is_set(BA_input_buffer_prev[11], 2):
                            vessel.control.rcs = is_set(BA_input_buffer[11], 2)
                        if is_set(BA_input_buffer[11], 4) != is_set(BA_input_buffer_prev[11], 4):
                            vessel.control.gear = not is_set(BA_input_buffer[11], 4)  # gear is opposite sense
                        if is_set(BA_input_buffer[11], 5) != is_set(BA_input_buffer_prev[11], 5) or (is_set(BA_input_buffer[11], 6) != is_set(BA_input_buffer_prev[11], 6)):
                            vessel.control.brakes = is_set(BA_input_buffer[11], 5) or is_set(BA_input_buffer[11], 6)

                        # Navball Mode
                        if is_set(BA_input_buffer[12], 1):
                            vessel.control.speed_mode = vessel.control.speed_mode.target
                        if is_set(BA_input_buffer[12], 2):
                            vessel.control.speed_mode = vessel.control.speed_mode.orbit
                        if is_set(BA_input_buffer[12], 3):
                            vessel.control.speed_mode = vessel.control.speed_mode.surface

                        # Landing Guidance
                        if is_set(BA_input_buffer[12], 4) and not is_set(BA_input_buffer_prev[12], 4):
                            ldg_guidance_draw(conn, vessel)
                        elif not is_set(BA_input_buffer[12], 4) and is_set(BA_input_buffer_prev[12], 4):
                            ldg_guidance_clear(conn)

                        # Autopiliot
                        spd_err_p = spd_err
                        throttle_inhib, spd_err = Autopilot(BA_input_buffer, BA_input_buffer_prev, vessel, spd_err_p, 100)

                        # Flight Control and Trims
                        sas_overide = flight_control_inputs(BA_input_buffer, vessel, x_trim, throttle_inhib)

                        # SAS
                        SAS_inputs(BA_input_buffer, BA_input_buffer_prev, vessel, mQ, sas_overide)

                        # Save/Load
                        if is_set(BA_input_buffer[1], 0) and not is_set(BA_input_buffer_prev[1], 0):
                            conn.space_center.quicksave()
                            conn.ui.message('Quicksaving...', duration=5)
                        if is_set(BA_input_buffer[1], 1) and not is_set(BA_input_buffer_prev[1], 1):
                            t_quickload_timer = time.time() + 5
                            conn.ui.message('Hold for 5 seconds to Quickload...', duration=5)

                        if not is_set(BA_input_buffer[1], 1):
                            t_quickload_timer = 0

                        if time.time() >= t_quickload_timer > 0:
                            conn.space_center.quickload()

                        # Warp
                        if is_set(BA_input_buffer[4], 7):
                            conn.space_center.physics_warp_factor = 0
                            conn.space_center.rails_warp_factor = 0
                        elif is_set(BA_input_buffer[5], 1) and not is_set(BA_input_buffer_prev[5], 1) and conn.space_center.physics_warp_factor == 0:
                            conn.space_center.rails_warp_factor = min(conn.space_center.rails_warp_factor + 1, conn.space_center.maximum_rails_warp_factor)
                        elif is_set(BA_input_buffer[5], 3) and not is_set(BA_input_buffer_prev[5], 3):
                            conn.space_center.rails_warp_factor = max(conn.space_center.rails_warp_factor - 1, 0)
                        elif is_set(BA_input_buffer[5], 5) and not is_set(BA_input_buffer_prev[5], 5) and conn.space_center.rails_warp_factor == 0:
                            conn.space_center.physics_warp_factor = min(conn.space_center.physics_warp_factor + 1, 3)
                        elif is_set(BA_input_buffer[5], 7) and not is_set(BA_input_buffer_prev[5], 7):
                            conn.space_center.physics_warp_factor = max(conn.space_center.physics_warp_factor - 1, 0)

                        # Clear Target
                        if is_set(BA_input_buffer[3], 1) and not is_set(BA_input_buffer_prev[3], 1):
                            conn.space_center.clear_target()

                        # Camera Control
                        if Settings.G_cam_change_timer > 0:
                            Settings.G_cam_change_timer = max(0, Settings.G_cam_change_timer - Settings.c_loop_frame_rate)
                        camera_inputs(cam, BA_input_buffer, mQ)

                        # Map focus
                        if cam.mode == cam.mode.map:
                            if cam.focussed_vessel is not None:
                                map_idx = [x[0] for x in map_view_list].index(cam.focussed_vessel.name)
                            elif cam.focussed_body is not None:
                                map_idx = [x[0] for x in map_view_list].index(cam.focussed_body.name)

                            map_idx_new = map_idx

                            if is_set(BA_input_buffer[2], 2) and not is_set(BA_input_buffer_prev[2], 2):
                                map_idx_new = (map_idx + 1) % len(map_view_list)
                            if is_set(BA_input_buffer[2], 0) and not is_set(BA_input_buffer_prev[2], 0):
                                map_idx_new = (map_idx - 1) % len(map_view_list)

                            if map_idx_new != map_idx:
                                if map_idx_new == 0:  # vessel
                                    cam.focussed_vessel = vessel
                                    cam.distance = cam.default_distance
                                else:
                                    cam.focussed_body = map_view_list[map_idx_new][1]
                                    cam.distance = cam.default_distance

                            if is_set(BA_input_buffer[2], 1) and not is_set(BA_input_buffer_prev[2], 1):  # always reset to te current vessel
                                cam.focussed_vessel = vessel
                                cam.distance = cam.default_distance

                        # Vessel Switch
                        if is_set(BA_input_buffer[2], 5) and not is_set(BA_input_buffer_prev[2], 5):
                            vessel_list = [v for v in conn.space_center.vessels if norm(v.position(vessel.reference_frame)) < 2000]
                            conn.space_center.active_vessel = vessel_list[(vessel_list.index(vessel) + 1) % len(vessel_list)]
                            n_program_state = 4
                        elif is_set(BA_input_buffer[2], 7) and not is_set(BA_input_buffer_prev[2], 7):
                            vessel_list = [v for v in conn.space_center.vessels if norm(v.position(vessel.reference_frame)) < 2000]
                            conn.space_center.active_vessel = vessel_list[(vessel_list.index(vessel) - 1) % len(vessel_list)]
                            n_program_state = 4

                        # put all the data onto the shared array for use by the GUI
                        for i in range(len(BA_input_buffer)):
                            data_array[i] = BA_input_buffer[i]

                except krpc.client.RPCError:
                    n_program_state = 3
                    mQ.put((1, 'Main Loop Error'))

            # Check for Overuns and send a warning.
            if (time.time() - t_frame_start_time) > Settings.c_loop_frame_rate * 1.1:
                mQ.put((1, 'OVERUN - ' + str(int((time.time() - t_frame_start_time) * 1000)) + 'ms'))
