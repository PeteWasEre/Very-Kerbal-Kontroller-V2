from Utilities import is_set, bytes2int


def Autopilot(inputs, inputs_prev, vessel, err_p, dt):
    thr_inhib = False
    tgt_speed = 0
    err = 0

    if is_set(inputs[29], 1):
        # Autopilot is on and in the running state
        if (is_set(inputs[29], 2) and not is_set(inputs_prev[29], 2) or is_set(inputs[29], 3) and not is_set(inputs_prev[29], 3)):
            vessel.auto_pilot.reference_frame = vessel.surface_reference_frame
            vessel.auto_pilot.target_pitch_and_heading(bytes2int([inputs[35], inputs[36]]), bytes2int([inputs[33], inputs[34]]))
            vessel.auto_pilot.engage()

        elif (not is_set(inputs[29], 2) and not is_set(inputs[29], 3)):
            vessel.auto_pilot.disengage()

        vessel.auto_pilot.target_pitch_and_heading(bytes2int([inputs[35], inputs[36]]), bytes2int([inputs[33], inputs[34]]))

        if (is_set(inputs[29], 4) ):
            thr_inhib = True
            tgt_speed = bytes2int([inputs[37], inputs[38]])
            err = tgt_speed - vessel.flight(vessel.orbit.body.reference_frame).speed
            spd_err_dt = (err_p-err)/(dt/1000)
            C1 = inputs[19]/255/10
            C2 = inputs[26]/255/10
            vessel.control.throttle = vessel.control.throttle + C1 * err + -C2 * spd_err_dt

            print(C1,C2)

    return thr_inhib, err
