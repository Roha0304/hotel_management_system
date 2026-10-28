import xml.etree.ElementTree as ET

def get_base_styles():
    return {
        'title': "text;html=1;strokeColor=#23445d;fillColor=#1a4d2e;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=1;shadow=1;fontFamily=Helvetica;fontSize=17;fontColor=#ffffff;fontStyle=1;",
        'subtitle': "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;fontFamily=Helvetica;fontSize=11;fontColor=#475569;",
        'entity': "rounded=0;whiteSpace=wrap;html=1;fontStyle=1;fontSize=15;fontFamily=Helvetica;fillColor=#dae8fc;strokeColor=#6c8ebf;strokeWidth=2.5;shadow=1;fontColor=#1e293b;",
        'center_entity': "rounded=0;whiteSpace=wrap;html=1;fontStyle=1;fontSize=16;fontFamily=Helvetica;fillColor=#d5e8d4;strokeColor=#274e13;strokeWidth=3;shadow=1;fontColor=#0f3818;",
        'weak_entity': "shape=ext;double=1;rounded=0;whiteSpace=wrap;html=1;fontStyle=1;fontSize=14;fontFamily=Helvetica;fillColor=#e1d5e7;strokeColor=#9673a6;strokeWidth=2;shadow=1;fontColor=#2d1537;",
        'summary_entity': "rounded=0;whiteSpace=wrap;html=1;fontStyle=1;fontSize=14;fontFamily=Helvetica;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=2;shadow=1;fontColor=#453406;",
        'rel': "rhombus;whiteSpace=wrap;html=1;fontStyle=1;fontSize=13;fontFamily=Helvetica;fillColor=#ffe6cc;strokeColor=#d79b00;strokeWidth=2;fontColor=#4d2600;shadow=1;",
        'ident_rel': "shape=rhombus;double=1;whiteSpace=wrap;html=1;fontStyle=1;fontSize=13;fontFamily=Helvetica;fillColor=#e1d5e7;strokeColor=#9673a6;strokeWidth=2;fontColor=#2d1537;shadow=1;",
        'pk': "ellipse;whiteSpace=wrap;html=1;fontSize=11;fontStyle=5;fontFamily=Helvetica;fillColor=#d5e8d4;strokeColor=#274e13;strokeWidth=2;fontColor=#0f3818;shadow=0;",
        'uk': "ellipse;whiteSpace=wrap;html=1;fontSize=11;fontStyle=1;fontFamily=Helvetica;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=1.5;fontColor=#3d3100;shadow=0;",
        'std': "ellipse;whiteSpace=wrap;html=1;fontSize=11;fontFamily=Helvetica;fillColor=#f8fafc;strokeColor=#64748b;strokeWidth=1.2;fontColor=#1e293b;shadow=0;",
        'derived': "ellipse;dashed=1;dashPattern=3 3;whiteSpace=wrap;html=1;fontSize=11;fontStyle=2;fontFamily=Helvetica;fillColor=#fef2f2;strokeColor=#ef4444;strokeWidth=1.5;fontColor=#991b1b;shadow=0;",
        'multi': "shape=ellipse;double=1;whiteSpace=wrap;html=1;fontSize=11;fontFamily=Helvetica;fillColor=#f0fdf4;strokeColor=#16a34a;strokeWidth=1.5;fontColor=#14532d;shadow=0;"
    }

class DiagramBuilder:
    def __init__(self, page_id, page_name, width=1800, height=1100):
        self.page_id = page_id
        self.page_name = page_name
        self.width = width
        self.height = height
        self.cell_id = 100
        
        self.diagram_elem = ET.Element('diagram', {'id': page_id, 'name': page_name})
        self.model = ET.SubElement(self.diagram_elem, 'mxGraphModel', {
            'dx': '1400', 'dy': '900', 'grid': '1', 'gridSize': '10', 'guides': '1',
            'tooltips': '1', 'connect': '1', 'arrows': '1', 'fold': '1', 'page': '1',
            'pageScale': '1', 'pageWidth': str(width), 'pageHeight': str(height),
            'background': '#ffffff', 'math': '0', 'shadow': '0'
        })
        self.root = ET.SubElement(self.model, 'root')
        ET.SubElement(self.root, 'mxCell', {'id': '0'})
        ET.SubElement(self.root, 'mxCell', {'id': '1', 'parent': '0'})
        self.styles = get_base_styles()

    def get_id(self):
        self.cell_id += 1
        return str(self.cell_id)

    def add_cell(self, value, style, x, y, w, h, parent='1', vertex='1', edge=None, source=None, target=None):
        cid = self.get_id()
        attribs = {'id': cid, 'value': value, 'style': style, 'parent': parent}
        if vertex: attribs['vertex'] = vertex
        if edge: attribs['edge'] = edge
        if source: attribs['source'] = source
        if target: attribs['target'] = target
        cell = ET.SubElement(self.root, 'mxCell', attribs)
        geo = ET.SubElement(cell, 'mxGeometry', {
            'x': str(x), 'y': str(y), 'width': str(w), 'height': str(h), 'as': 'geometry'
        })
        if edge: geo.set('relative', '1')
        return cid

    def add_edge(self, source_id, target_id, label='', style='endArrow=none;html=1;rounded=0;strokeWidth=1.5;strokeColor=#333333;'):
        cid = self.get_id()
        cell = ET.SubElement(self.root, 'mxCell', {
            'id': cid, 'value': label, 'style': style, 'parent': '1', 'edge': '1',
            'source': source_id, 'target': target_id
        })
        ET.SubElement(cell, 'mxGeometry', {'relative': '1', 'as': 'geometry'})
        return cid

    def add_legend(self, leg_x=120, leg_y=950):
        self.add_cell("<b>DBMS ER NOTATION LEGEND</b>", "text;html=1;fontStyle=1;fontSize=12;fontFamily=Helvetica;fontColor=#1e293b;", leg_x, leg_y, 200, 25)
        self.add_cell("<b>Entity Set</b>", self.styles['entity'], leg_x, leg_y + 30, 95, 38)
        self.add_cell("Strong Entity", self.styles['subtitle'], leg_x + 100, leg_y + 36, 100, 25)

        self.add_cell("<b>Weak Entity</b>", self.styles['weak_entity'], leg_x + 210, leg_y + 30, 95, 38)
        self.add_cell("Weak Entity", self.styles['subtitle'], leg_x + 310, leg_y + 36, 90, 25)

        self.add_cell("<b>Relationship</b>", self.styles['rel'], leg_x + 410, leg_y + 26, 95, 46)
        self.add_cell("Relationship (1:N, 1:1)", self.styles['subtitle'], leg_x + 510, leg_y + 36, 130, 25)

        self.add_cell("<b>Identifying</b>", self.styles['ident_rel'], leg_x + 650, leg_y + 26, 95, 46)
        self.add_cell("Identifying Rel.", self.styles['subtitle'], leg_x + 750, leg_y + 36, 110, 25)

        self.add_cell("<u>Primary Key</u>", self.styles['pk'], leg_x + 870, leg_y + 30, 95, 36)
        self.add_cell("Primary Key", self.styles['subtitle'], leg_x + 970, leg_y + 36, 90, 25)

        self.add_cell("Derived Attr", self.styles['derived'], leg_x + 1070, leg_y + 30, 95, 36)
        self.add_cell("Derived (Dashed)", self.styles['subtitle'], leg_x + 1170, leg_y + 36, 100, 25)

        self.add_cell("Multivalued", self.styles['multi'], leg_x + 1280, leg_y + 30, 95, 36)
        self.add_cell("Multivalued (Double)", self.styles['subtitle'], leg_x + 1380, leg_y + 36, 120, 25)


def build_part1():
    b = DiagramBuilder('part1', 'Part 1 - Core Reservations Subsystem', 1800, 1100)
    s = b.styles

    b.add_cell(
        "<b>PART 1: CORE ROOM RESERVATION & BOOKING SUBSYSTEM</b><br/><span style='font-size:12px;font-weight:normal;'>Hotel Management System · Entity Sets: USERS, ROOMS, BOOKINGS (Peter Chen Notation)</span>",
        s['title'], 250, 30, 1300, 60
    )

    # USERS Entity
    u_x, u_y = 230, 450
    uid = b.add_cell("<b>USERS</b>", s['entity'], u_x, u_y, 160, 70)
    user_attrs = [
        ("<u>user_id</u> (PK)", s['pk'], u_x - 170, u_y - 120, 120, 44),
        ("username (UK)", s['uk'], u_x - 190, u_y - 50, 125, 44),
        ("full_name", s['std'], u_x - 190, u_y + 20, 120, 42),
        ("email (UK)", s['uk'], u_x - 190, u_y + 90, 125, 44),
        ("phone (UK)", s['uk'], u_x - 160, u_y + 160, 125, 44),
        ("password_hash", s['std'], u_x - 30, u_y - 150, 120, 42),
        ("role", s['std'], u_x + 80, u_y - 150, 105, 42),
        ("status", s['std'], u_x + 180, u_y - 120, 105, 42),
        ("created_at", s['std'], u_x - 20, u_y + 180, 115, 42)
    ]
    for val, sty, ax, ay, aw, ah in user_attrs:
        aid = b.add_cell(val, sty, ax, ay, aw, ah)
        b.add_edge(uid, aid)

    # BOOKINGS Entity
    bk_x, bk_y = 780, 445
    bkid = b.add_cell("<b>BOOKINGS</b>", s['center_entity'], bk_x, bk_y, 190, 80)
    booking_attrs = [
        ("<u>booking_id</u> (PK)", s['pk'], bk_x - 120, bk_y - 170, 130, 45),
        ("check_in", s['std'], bk_x + 30, bk_y - 190, 110, 42),
        ("check_in_time", s['std'], bk_x + 160, bk_y - 180, 120, 42),
        ("check_out", s['std'], bk_x - 120, bk_y - 100, 115, 42),
        ("check_out_time", s['std'], bk_x + 180, bk_y - 110, 125, 42),
        ("guest_count", s['std'], bk_x + 200, bk_y - 40, 110, 42),
        ("total_amount", s['std'], bk_x - 140, bk_y + 110, 115, 42),
        ("advance_paid (25%)", s['std'], bk_x - 20, bk_y + 130, 135, 44),
        ("balance_amount (75%)", s['derived'], bk_x + 140, bk_y + 120, 145, 45),
        ("booking_status", s['std'], bk_x - 110, bk_y + 180, 120, 42),
        ("cancelled_by", s['std'], bk_x + 30, bk_y + 200, 115, 42),
        ("cancellation_reason", s['std'], bk_x + 160, bk_y + 190, 140, 44),
        ("created_at", s['std'], bk_x + 40, bk_y + 260, 115, 42)
    ]
    for val, sty, ax, ay, aw, ah in booking_attrs:
        aid = b.add_cell(val, sty, ax, ay, aw, ah)
        b.add_edge(bkid, aid)

    # ROOMS Entity
    r_x, r_y = 1350, 450
    rid = b.add_cell("<b>ROOMS</b>", s['entity'], r_x, r_y, 160, 70)
    room_attrs = [
        ("<u>room_id</u> (PK)", s['pk'], r_x + 180, r_y - 120, 120, 44),
        ("room_number (UK)", s['uk'], r_x + 200, r_y - 50, 130, 44),
        ("room_type", s['std'], r_x + 200, r_y + 20, 115, 42),
        ("capacity", s['std'], r_x + 190, r_y + 90, 110, 42),
        ("price_per_night", s['std'], r_x + 160, r_y + 160, 125, 42),
        ("amenities", s['multi'], r_x - 70, r_y - 150, 120, 44),
        ("image_url", s['std'], r_x + 50, r_y - 150, 110, 42),
        ("status", s['std'], r_x + 160, r_y - 140, 105, 42)
    ]
    for val, sty, ax, ay, aw, ah in room_attrs:
        aid = b.add_cell(val, sty, ax, ay, aw, ah)
        b.add_edge(rid, aid)

    # Relationships
    rel_places = b.add_cell("<b>Places</b>", s['rel'], 510, 450, 120, 70)
    b.add_edge(uid, rel_places, "1 (0..N)", "endArrow=none;html=1;strokeWidth=2;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")
    b.add_edge(rel_places, bkid, "N (1..1)", "endArrow=none;html=1;strokeWidth=3;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")

    rel_reserves = b.add_cell("<b>Reserves</b>", s['rel'], 1090, 450, 120, 70)
    b.add_edge(rid, rel_reserves, "1 (0..N)", "endArrow=none;html=1;strokeWidth=2;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")
    b.add_edge(rel_reserves, bkid, "N (1..1)", "endArrow=none;html=1;strokeWidth=3;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")

    b.add_legend(160, 940)
    return b.diagram_elem


def build_part2():
    b = DiagramBuilder('part2', 'Part 2 - Billing & Financial Transactions', 1800, 1100)
    s = b.styles

    b.add_cell(
        "<b>PART 2: BILLING & PAYMENT GATEWAY SUBSYSTEM</b><br/><span style='font-size:12px;font-weight:normal;'>Hotel Management System · Entity Sets: USERS, BOOKINGS, PAYMENTS (Peter Chen Notation)</span>",
        s['title'], 250, 30, 1300, 60
    )

    # USERS
    u_x, u_y = 280, 280
    uid = b.add_cell("<b>USERS</b>", s['entity'], u_x, u_y, 160, 70)
    user_attrs = [
        ("<u>user_id</u> (PK)", s['pk'], u_x - 170, u_y - 80, 120, 44),
        ("full_name", s['std'], u_x - 180, u_y - 10, 120, 42),
        ("email (UK)", s['uk'], u_x - 180, u_y + 60, 125, 44),
        ("phone (UK)", s['uk'], u_x - 150, u_y + 130, 125, 44),
        ("role", s['std'], u_x - 20, u_y - 120, 105, 42),
        ("status", s['std'], u_x + 90, u_y - 120, 105, 42)
    ]
    for val, sty, ax, ay, aw, ah in user_attrs:
        aid = b.add_cell(val, sty, ax, ay, aw, ah)
        b.add_edge(uid, aid)

    # BOOKINGS
    bk_x, bk_y = 1250, 280
    bkid = b.add_cell("<b>BOOKINGS</b>", s['center_entity'], bk_x, bk_y, 180, 70)
    booking_attrs = [
        ("<u>booking_id</u> (PK)", s['pk'], bk_x + 200, bk_y - 90, 130, 45),
        ("total_amount", s['std'], bk_x + 220, bk_y - 20, 120, 42),
        ("advance_paid (25%)", s['std'], bk_x + 220, bk_y + 50, 135, 44),
        ("balance_amount (75%)", s['derived'], bk_x + 200, bk_y + 120, 145, 45),
        ("payment_mode", s['std'], bk_x + 70, bk_y - 120, 120, 42),
        ("payment_status", s['std'], bk_x - 60, bk_y - 120, 125, 42),
        ("booking_status", s['std'], bk_x + 100, bk_y + 160, 120, 42)
    ]
    for val, sty, ax, ay, aw, ah in booking_attrs:
        aid = b.add_cell(val, sty, ax, ay, aw, ah)
        b.add_edge(bkid, aid)

    # Relationship: Places
    rel_places = b.add_cell("<b>Places</b>", s['rel'], 770, 280, 120, 70)
    b.add_edge(uid, rel_places, "1 (0..N)", "endArrow=none;html=1;strokeWidth=2;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")
    b.add_edge(rel_places, bkid, "N (1..1)", "endArrow=none;html=1;strokeWidth=3;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")

    # PAYMENTS
    p_x, p_y = 760, 640
    pid = b.add_cell("<b>PAYMENTS</b>", s['entity'], p_x, p_y, 180, 75)
    pay_attrs = [
        ("<u>pay_id</u> (PK)", s['pk'], p_x - 180, p_y - 60, 125, 45),
        ("gateway_order_id (UK)", s['uk'], p_x - 220, p_y + 10, 150, 45),
        ("gateway_payment_id (UK)", s['uk'], p_x - 220, p_y + 80, 155, 45),
        ("amount", s['std'], p_x - 160, p_y + 150, 115, 42),
        ("currency", s['std'], p_x - 30, p_y + 180, 110, 42),
        ("method", s['std'], p_x + 90, p_y + 180, 110, 42),
        ("status", s['std'], p_x + 200, p_y + 150, 110, 42),
        ("created_at", s['std'], p_x + 220, p_y + 80, 115, 42),
        ("updated_at", s['std'], p_x + 210, p_y + 10, 115, 42)
    ]
    for val, sty, ax, ay, aw, ah in pay_attrs:
        aid = b.add_cell(val, sty, ax, ay, aw, ah)
        b.add_edge(pid, aid)

    # Relationship: Paid_Via (BOOKINGS -> PAYMENTS)
    rel_paid = b.add_cell("<b>Paid_Via</b>", s['rel'], 1050, 490, 130, 70)
    b.add_edge(bkid, rel_paid, "1", "endArrow=none;html=1;strokeWidth=2.5;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")
    b.add_edge(rel_paid, pid, "1", "endArrow=none;html=1;strokeWidth=2.5;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")

    # Relationship: Authorizes / Processed_For (USERS -> PAYMENTS)
    rel_auth = b.add_cell("<b>Authorizes</b>", s['rel'], 490, 490, 130, 70)
    b.add_edge(uid, rel_auth, "1", "endArrow=none;html=1;strokeWidth=2;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")
    b.add_edge(rel_auth, pid, "N", "endArrow=none;html=1;strokeWidth=2;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")

    b.add_legend(160, 940)
    return b.diagram_elem


def build_part3():
    b = DiagramBuilder('part3', 'Part 3 - Auditing & Business Intelligence', 1800, 1100)
    s = b.styles

    b.add_cell(
        "<b>PART 3: AUDIT LOGGING & BUSINESS INTELLIGENCE SUBSYSTEM</b><br/><span style='font-size:12px;font-weight:normal;'>Hotel Management System · Entity Sets: BOOKING_AUDIT (Weak), REPORT_ROOM_SUMMARY, BOOKINGS, ROOMS</span>",
        s['title'], 250, 30, 1300, 60
    )

    # Left Section Title
    b.add_cell("<b>AUTOMATED AUDIT TRAIL (TRIGGER SYSTEM)</b>", "text;html=1;fontStyle=1;fontSize=13;fontFamily=Helvetica;fontColor=#6b21a8;align=center;", 200, 120, 450, 30)

    # BOOKINGS (Audit Subject)
    bk_x, bk_y = 320, 270
    bkid = b.add_cell("<b>BOOKINGS</b>", s['center_entity'], bk_x, bk_y, 180, 70)
    booking_attrs = [
        ("<u>booking_id</u> (PK)", s['pk'], bk_x - 170, bk_y - 80, 130, 45),
        ("booking_status", s['std'], bk_x - 180, bk_y - 10, 120, 42),
        ("cancelled_by", s['std'], bk_x - 180, bk_y + 60, 115, 42),
        ("cancellation_reason", s['std'], bk_x - 160, bk_y + 130, 140, 44),
        ("total_amount", s['std'], bk_x - 20, bk_y - 110, 115, 42),
        ("created_at", s['std'], bk_x + 90, bk_y - 110, 115, 42)
    ]
    for val, sty, ax, ay, aw, ah in booking_attrs:
        aid = b.add_cell(val, sty, ax, ay, aw, ah)
        b.add_edge(bkid, aid)

    # Identifying Relationship: Generates
    rel_gen = b.add_cell("<b>Generates</b>", s['ident_rel'], 345, 440, 130, 75)
    b.add_edge(bkid, rel_gen, "1", "endArrow=none;html=1;strokeWidth=2.5;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")

    # BOOKING_AUDIT (Weak Entity)
    a_x, a_y = 320, 610
    aid = b.add_cell("<b>BOOKING_AUDIT</b>", s['weak_entity'], a_x, a_y, 180, 70)
    b.add_edge(rel_gen, aid, "N", "endArrow=none;html=1;strokeWidth=3.5;strokeColor=#6b21a8;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")

    audit_attrs = [
        ("<u>audit_id</u> (PK)", s['pk'], a_x - 180, a_y - 60, 125, 45),
        ("action_type", s['std'], a_x - 190, a_y + 10, 120, 42),
        ("old_status", s['std'], a_x - 180, a_y + 80, 115, 42),
        ("new_status", s['std'], a_x - 100, a_y + 140, 115, 42),
        ("details", s['std'], a_x + 40, a_y + 140, 120, 42),
        ("changed_at", s['std'], a_x + 160, a_y + 110, 115, 42)
    ]
    for val, sty, ax, ay, aw, ah in audit_attrs:
        c_aid = b.add_cell(val, sty, ax, ay, aw, ah)
        b.add_edge(aid, c_aid)

    # Middle Divider Line
    b.add_cell("", "line;strokeWidth=2;direction=south;strokeColor=#cbd5e1;dashed=1;", 870, 130, 10, 750)

    # Right Section Title
    b.add_cell("<b>EXECUTIVE ANALYTICS & CURSOR REPORTING</b>", "text;html=1;fontStyle=1;fontSize=13;fontFamily=Helvetica;fontColor=#b45309;align=center;", 1100, 120, 450, 30)

    # ROOMS (Subject of Aggregation)
    r_x, r_y = 1250, 270
    rid = b.add_cell("<b>ROOMS</b>", s['entity'], r_x, r_y, 180, 70)
    room_attrs = [
        ("<u>room_id</u> (PK)", s['pk'], r_x + 200, r_y - 80, 125, 44),
        ("room_number (UK)", s['uk'], r_x + 210, r_y - 10, 130, 44),
        ("room_type", s['std'], r_x + 210, r_y + 60, 115, 42),
        ("price_per_night", s['std'], r_x + 180, r_y + 130, 125, 42),
        ("status", s['std'], r_x + 100, r_y - 110, 110, 42),
        ("capacity", s['std'], r_x - 20, r_y - 110, 110, 42)
    ]
    for val, sty, ax, ay, aw, ah in room_attrs:
        c_aid = b.add_cell(val, sty, ax, ay, aw, ah)
        b.add_edge(rid, c_aid)

    # Relationship: Aggregated_By
    rel_agg = b.add_cell("<b>Aggregated_By</b><br/><span style='font-size:9px;'>[CURSOR]</span>", s['rel'], 1275, 440, 130, 75)
    b.add_edge(rid, rel_agg, "1", "endArrow=none;html=1;strokeWidth=1.8;dashed=1;strokeColor=#453406;fontSize=11;labelBackgroundColor=#ffffff;")

    # REPORT_ROOM_SUMMARY
    rep_x, rep_y = 1230, 610
    repid = b.add_cell("<b>REPORT_ROOM_SUMMARY</b><br/><span style='font-size:10px;font-weight:normal;'>[Cursor Derived]</span>", s['summary_entity'], rep_x, rep_y, 220, 75)
    b.add_edge(rel_agg, repid, "1", "endArrow=none;html=1;strokeWidth=1.8;dashed=1;strokeColor=#453406;fontSize=11;labelBackgroundColor=#ffffff;")

    summary_attrs = [
        ("<u>summary_id</u> (PK)", s['pk'], rep_x + 240, rep_y - 60, 135, 45),
        ("room_type", s['std'], rep_x + 260, rep_y + 10, 115, 42),
        ("total_rooms", s['std'], rep_x + 250, rep_y + 80, 115, 42),
        ("available_rooms", s['std'], rep_x + 190, rep_y + 140, 120, 42),
        ("total_bookings", s['std'], rep_x + 60, rep_y + 150, 120, 42),
        ("total_revenue", s['std'], rep_x - 70, rep_y + 150, 120, 42),
        ("average_rate", s['std'], rep_x - 170, rep_y + 120, 115, 42),
        ("generated_at", s['std'], rep_x - 180, rep_y + 50, 115, 42)
    ]
    for val, sty, ax, ay, aw, ah in summary_attrs:
        c_aid = b.add_cell(val, sty, ax, ay, aw, ah)
        b.add_edge(repid, c_aid)

    b.add_legend(160, 940)
    return b.diagram_elem


def main():
    p1 = build_part1()
    p2 = build_part2()
    p3 = build_part3()

    # 1. Multi-page DrawIO file containing all 3 parts + master
    mxfile = ET.Element('mxfile', {
        'host': 'app.diagrams.net',
        'modified': '2026-10-22T09:00:00.000Z',
        'agent': 'Antigravity DBMS Modeler',
        'version': '21.0.0',
        'type': 'device'
    })

    # Read the master diagram from existing file if available
    try:
        master_tree = ET.parse('d:/hotel_management_system/hotel_management_ER_diagram.drawio')
        master_diag = master_tree.getroot().find('diagram')
        if master_diag is not None:
            master_diag.set('id', 'master')
            master_diag.set('name', 'Complete Master ER Diagram')
    except Exception as e:
        master_diag = None

    mxfile.append(p1)
    mxfile.append(p2)
    mxfile.append(p3)
    if master_diag is not None:
        mxfile.append(master_diag)

    multi_xml = ET.tostring(mxfile, encoding='utf-8', xml_declaration=True).decode('utf-8')
    with open('d:/hotel_management_system/hotel_management_ER_diagram.drawio', 'w', encoding='utf-8') as f:
        f.write(multi_xml)
    print("Updated: d:/hotel_management_system/hotel_management_ER_diagram.drawio with 4 pages (Part 1, Part 2, Part 3, Master).")

    # 2. Individual standalone files for each part
    for idx, (p_elem, fname) in enumerate([
        (p1, 'd:/hotel_management_system/hotel_management_ER_Part1_Reservations.drawio'),
        (p2, 'd:/hotel_management_system/hotel_management_ER_Part2_Billing.drawio'),
        (p3, 'd:/hotel_management_system/hotel_management_ER_Part3_Audit_Analytics.drawio')
    ], 1):
        single_mx = ET.Element('mxfile', {
            'host': 'app.diagrams.net',
            'agent': 'Antigravity DBMS Modeler',
            'version': '21.0.0',
            'type': 'device'
        })
        single_mx.append(p_elem)
        single_xml = ET.tostring(single_mx, encoding='utf-8', xml_declaration=True).decode('utf-8')
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(single_xml)
        print(f"Generated standalone: {fname}")

if __name__ == '__main__':
    main()
