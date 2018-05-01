# this function maps game state into bytes to transmit to the Arduino to set warning light status.


def output_mapping(output_buffer, conn, gear_list, sas_ovd):

    # Gear
    gear_up = 0
    gear_down = 0
    for gear in gear_list[0]:
        if gear() == conn.space_center.WheelState.retracted:
            gear_up += 1

        if gear() == conn.space_center.WheelState.deployed:
            gear_down += 1
    for gear in gear_list[1]:
        if gear() == conn.space_center.LegState.retracted:
            gear_up += 1

        if gear() == conn.space_center.LegState.deployed:
            gear_down += 1

    num_of_gears = len(gear_list[0]) + len(gear_list[1])
    if gear_up == num_of_gears or num_of_gears == 0:  # all gear are up or we have no gear!
        output_buffer[0] |= 2
    if gear_down == num_of_gears and num_of_gears > 0:  # all gear are down and we have gear
        output_buffer[0] |= 4

    if sas_ovd:
        output_buffer[0] |= 8
