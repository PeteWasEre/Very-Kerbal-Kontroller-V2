# this function maps game state into bytes to transmit to the Arduino to set warning light status.


def output_mapping(output_buffer, conn, temps_list, prop_list, mono_list, elec_list, gear_list):
    # Left Lights
    # Fuel Warning and Caution
    # the propellant list is a list of propellants as a list of (current amount, max amount)
    for fuel in prop_list:
        if fuel[0]() == 0 and fuel[1]() > 0:
            output_buffer[1] |= 1 << 0
        else:
            try:
                if fuel[0]() / fuel[1]() < 0.2:
                    output_buffer[1] |= 1 << 2
            except ZeroDivisionError:  # catch where fuel max is 0 if we have no space for it
                pass

    # Monoprop Warning and Caution
    # The monoprop list is a list containing (current amount, max amount)
    if mono_list[0]() == 0 and mono_list[1]() > 0:
        output_buffer[1] |= 1 << 1
    else:
        try:
            if mono_list[0]() / mono_list[1]() < 0.2:
                output_buffer[1] |= 1 << 3
        except ZeroDivisionError:  # catch case where max mono prop is 0
            pass

    # Right Lights
    # Battery Warning and Caution
    # The elec list is a list containing (current amount, max amount)
    if elec_list[0]() == 0 and elec_list[1]() > 0:
        output_buffer[2] |= 1 << 1
    else:
        try:
            if elec_list[0]() / elec_list[1]() < 0.2:
                output_buffer[2] |= 1 << 3
        except ZeroDivisionError:  # catch case where max mono prop is 0
            pass

    # Overheat Warning and caution
    # The temps list is a list per part of (core temp, max core temp, skin temp, max skin temp)
    # The current temps are stream objects, whereas the max temps are values
    for temp in temps_list:
        if (temp[0]() / temp[1]) > 0.5 or (temp[2]() / temp[3]) > 0.5:
            output_buffer[2] |= 1 << 0
        if (temp[0]() / temp[1]) > 0.3 or (temp[2]() / temp[3]) > 0.3:
            output_buffer[2] |= 1 << 2

    # Gear
    gear_up = 0
    gear_down = 0
    for gear in gear_list[0]:
        if gear() == conn.space_center.LandingGearState.retracted:
            gear_up += 1

        if gear() == conn.space_center.LandingGearState.deployed:
            gear_down += 1
    for gear in gear_list[1]:
        if gear() == conn.space_center.LandingLegState.retracted:
            gear_up += 1

        if gear() == conn.space_center.LandingLegState.deployed:
            gear_down += 1

    num_of_gears = len(gear_list[0]) + len(gear_list[1])
    if gear_up == num_of_gears or num_of_gears == 0:  # all gear are up or we have no gear!
        output_buffer[2] |= 1 << 4
    if gear_down == num_of_gears and num_of_gears > 0:  # all gear are down and we have gear
        output_buffer[2] |= 1 << 5
