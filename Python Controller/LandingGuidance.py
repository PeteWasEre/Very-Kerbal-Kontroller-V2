from math import sin, cos, tan, pi
from Settings import *


def ldg_guidance_init(conn, vessel):
    # body = conn.space_center.CelestialBody(3)  # Kerbin
    body = vessel.orbit.body
    create_relative = conn.space_center.ReferenceFrame.create_relative

    # Define the threshold
    landing_latitude = -(0 + (2.0 / 60) + (55 / 60 / 60))
    landing_longitude = -(74 + (43.0 / 60) + (20 / 60 / 60))
    landing_altitude = 5

    # Determine landing site reference frame
    # (orientation: x=zenith, y=north, z=east)
    landing_position = body.surface_position(landing_latitude, landing_longitude, body.reference_frame)
    q_long = (
        0,
        sin(-landing_longitude * 0.5 * pi / 180),
        0,
        cos(-landing_longitude * 0.5 * pi / 180)
    )
    q_lat = (  # First two values here tune the slope and alignment of the beam to the runway. Manually tuned.
        0.0037,
        -0.001,
        sin(landing_latitude * 0.5 * pi / 180),
        cos(landing_latitude * 0.5 * pi / 180)
    )
    landing_reference_frame = \
        create_relative(
            create_relative(
                create_relative(
                    body.reference_frame,
                    landing_position,
                    q_long),
                (0, 0, 0),
                q_lat),
            (landing_altitude, 0, 0))

    return landing_reference_frame


def ldg_guidance_draw(conn, landing_reference_frame, scale):
    conn.drawing.clear()
    
    # Rwy 09
    ils_09_l_l = conn.drawing.add_line((0, c_ils_side_offset, 0),
                                       (tan((c_ils_slope - c_ils_slope_offset) * pi / 180) * c_ils_dist * scale,
                                        c_ils_side_offset, - c_ils_dist * scale),
                                       landing_reference_frame)
    ils_09_l_c = conn.drawing.add_line((0, c_ils_side_offset, 0),
                                       (tan(c_ils_slope * pi / 180) * c_ils_dist * scale,
                                        c_ils_side_offset, - c_ils_dist * scale),
                                       landing_reference_frame)
    ils_09_l_h = conn.drawing.add_line((0, c_ils_side_offset, 0),
                                       (tan((c_ils_slope + c_ils_slope_offset) * pi / 180) * c_ils_dist * scale,
                                        c_ils_side_offset, - c_ils_dist * scale),
                                       landing_reference_frame)
    ils_09_r_l = conn.drawing.add_line((0, - c_ils_side_offset, 0),
                                       (tan((c_ils_slope - c_ils_slope_offset) * pi / 180) * c_ils_dist * scale,
                                        -c_ils_side_offset, - c_ils_dist * scale),
                                       landing_reference_frame)
    ils_09_r_c = conn.drawing.add_line((0, - c_ils_side_offset, 0),
                                       (tan(c_ils_slope * pi / 180) * c_ils_dist * scale,
                                        -c_ils_side_offset, - c_ils_dist * scale),
                                       landing_reference_frame)
    ils_09_r_h = conn.drawing.add_line((0, - c_ils_side_offset, 0),
                                       (tan((c_ils_slope + c_ils_slope_offset) * pi / 180) * c_ils_dist * scale,
                                        -c_ils_side_offset, - c_ils_dist * scale),
                                       landing_reference_frame)

    ils_09_l_l.color = c_ils_l_col
    ils_09_l_c.color = c_ils_m_col
    ils_09_l_h.color = c_ils_h_col
    ils_09_r_l.color = c_ils_l_col
    ils_09_r_c.color = c_ils_m_col
    ils_09_r_h.color = c_ils_h_col

    ils_09_l_l.thickness = 5
    ils_09_l_c.thickness = 5
    ils_09_l_h.thickness = 5
    ils_09_r_l.thickness = 5
    ils_09_r_c.thickness = 5
    ils_09_r_h.thickness = 5
    
    # Rwy 27
    ils_27_l_l = conn.drawing.add_line((0, c_ils_side_offset, c_ils_offset),
                                       (tan((c_ils_slope - c_ils_slope_offset) * pi / 180) * c_ils_dist * scale,
                                        c_ils_side_offset, c_ils_offset + c_ils_dist * scale),
                                       landing_reference_frame)
    ils_27_l_c = conn.drawing.add_line((0, c_ils_side_offset, c_ils_offset),
                                       (tan(c_ils_slope * pi / 180) * c_ils_dist * scale,
                                        c_ils_side_offset, c_ils_offset + c_ils_dist * scale),
                                       landing_reference_frame)
    ils_27_l_h = conn.drawing.add_line((0, c_ils_side_offset, c_ils_offset),
                                       (tan((c_ils_slope + c_ils_slope_offset) * pi / 180) * c_ils_dist * scale,
                                        c_ils_side_offset, c_ils_offset + c_ils_dist * scale),
                                       landing_reference_frame)
    ils_27_r_l = conn.drawing.add_line((0, - c_ils_side_offset, c_ils_offset),
                                       (tan((c_ils_slope - c_ils_slope_offset) * pi / 180) * c_ils_dist * scale,
                                        -c_ils_side_offset, c_ils_offset + c_ils_dist * scale),
                                       landing_reference_frame)
    ils_27_r_c = conn.drawing.add_line((0, - c_ils_side_offset, c_ils_offset),
                                       (tan(c_ils_slope * pi / 180) * c_ils_dist * scale,
                                        -c_ils_side_offset, c_ils_offset + c_ils_dist * scale),
                                       landing_reference_frame)
    ils_27_r_h = conn.drawing.add_line((0, - c_ils_side_offset, c_ils_offset),
                                       (tan((c_ils_slope + c_ils_slope_offset) * pi / 180) * c_ils_dist * scale,
                                        -c_ils_side_offset, c_ils_offset + c_ils_dist * scale),
                                       landing_reference_frame)

    ils_27_l_l.color = c_ils_l_col
    ils_27_l_c.color = c_ils_m_col
    ils_27_l_h.color = c_ils_h_col
    ils_27_r_l.color = c_ils_l_col
    ils_27_r_c.color = c_ils_m_col
    ils_27_r_h.color = c_ils_h_col

    ils_27_l_l.thickness = 5
    ils_27_l_c.thickness = 5
    ils_27_l_h.thickness = 5
    ils_27_r_l.thickness = 5
    ils_27_r_c.thickness = 5
    ils_27_r_h.thickness = 5


def ldg_guidance_clear(conn):
    conn.drawing.clear()
