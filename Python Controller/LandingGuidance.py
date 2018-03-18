def ldg_guidance_draw(conn, vessel):  # todo rebuild this when KRPC 3.7 is available to use custome reference frames.
    conn.drawing.clear()

    v1_start = (158095.3939033646, -478.99761794020907, -578869.7132278137)
    v2_start = (158094.96184479096, -538.996063121335, -578869.7134211722)
    v1l_end = (139184.84695719907, -342.79930986318584, -585527.6834731719)
    v1m_end = (139278.06869656406, -343.45641409607947, -585866.255670956)
    v1h_end = (139371.60232570115, -344.14248819162003, -586205.9386240399)
    v2l_end = (139184.35853335817, -402.79511157271287, -585527.523517651)
    v2m_end = (139277.66372229127, -403.45750069248425, -585866.328863767)
    v2h_end = (139371.1656752824, -404.1432818151327, -586205.927123417)

    l_col = (255, 0, 0)
    m_col = (255, 255, 255)
    h_col = (255, 255, 0)

    l1l = conn.drawing.add_line(v1_start, v1l_end, vessel.orbit.body.reference_frame)
    l1m = conn.drawing.add_line(v1_start, v1m_end, vessel.orbit.body.reference_frame)
    l1h = conn.drawing.add_line(v1_start, v1h_end, vessel.orbit.body.reference_frame)
    l2l = conn.drawing.add_line(v2_start, v2l_end, vessel.orbit.body.reference_frame)
    l2m = conn.drawing.add_line(v2_start, v2m_end, vessel.orbit.body.reference_frame)
    l2h = conn.drawing.add_line(v2_start, v2h_end, vessel.orbit.body.reference_frame)

    l1l.color = l_col
    l1m.color = m_col
    l1h.color = h_col
    l2l.color = l_col
    l2m.color = m_col
    l2h.color = h_col

    l1l.thickness = 5
    l1m.thickness = 5
    l1h.thickness = 5
    l2l.thickness = 5
    l2m.thickness = 5
    l2h.thickness = 5


def ldg_guidance_clear(conn):
    conn.drawing.clear()
