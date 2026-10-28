import xml.etree.ElementTree as ET

def create_er_diagram():
    mxfile = ET.Element('mxfile', {
        'host': 'app.diagrams.net',
        'modified': '2026-10-22T08:45:00.000Z',
        'agent': 'Antigravity DBMS Modeler',
        'version': '21.0.0',
        'type': 'device'
    })
    
    diagram = ET.SubElement(mxfile, 'diagram', {
        'id': 'hotel-room-booking-er',
        'name': 'Hotel Room Booking DBMS ER Diagram'
    })
    
    model = ET.SubElement(diagram, 'mxGraphModel', {
        'dx': '1600',
        'dy': '1100',
        'grid': '1',
        'gridSize': '10',
        'guides': '1',
        'tooltips': '1',
        'connect': '1',
        'arrows': '1',
        'fold': '1',
        'page': '1',
        'pageScale': '1',
        'pageWidth': '2600',
        'pageHeight': '1800',
        'background': '#ffffff',
        'math': '0',
        'shadow': '0'
    })
    
    root = ET.SubElement(model, 'root')
    ET.SubElement(root, 'mxCell', {'id': '0'})
    ET.SubElement(root, 'mxCell', {'id': '1', 'parent': '0'})
    
    cell_id = 100
    
    def get_id():
        nonlocal cell_id
        cell_id += 1
        return str(cell_id)

    def add_cell(value, style, x, y, w, h, parent='1', vertex='1', edge=None, source=None, target=None):
        cid = get_id()
        attribs = {
            'id': cid,
            'value': value,
            'style': style,
            'parent': parent
        }
        if vertex:
            attribs['vertex'] = vertex
        if edge:
            attribs['edge'] = edge
        if source:
            attribs['source'] = source
        if target:
            attribs['target'] = target
            
        cell = ET.SubElement(root, 'mxCell', attribs)
        geo = ET.SubElement(cell, 'mxGeometry', {
            'x': str(x),
            'y': str(y),
            'width': str(w),
            'height': str(h),
            'as': 'geometry'
        })
        if edge:
            geo.set('relative', '1')
        return cid

    def add_edge(source_id, target_id, label='', style='endArrow=none;html=1;rounded=0;strokeWidth=1.5;strokeColor=#333333;'):
        cid = get_id()
        cell = ET.SubElement(root, 'mxCell', {
            'id': cid,
            'value': label,
            'style': style,
            'parent': '1',
            'edge': '1',
            'source': source_id,
            'target': target_id
        })
        geo = ET.SubElement(cell, 'mxGeometry', {'relative': '1', 'as': 'geometry'})
        return cid

    # Styles
    title_style = "text;html=1;strokeColor=#23445d;fillColor=#1a4d2e;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=1;shadow=1;fontFamily=Helvetica;fontSize=18;fontColor=#ffffff;fontStyle=1;"
    subtitle_style = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;fontFamily=Helvetica;fontSize=12;fontColor=#475569;"
    
    entity_style = "rounded=0;whiteSpace=wrap;html=1;fontStyle=1;fontSize=15;fontFamily=Helvetica;fillColor=#dae8fc;strokeColor=#6c8ebf;strokeWidth=2.5;shadow=1;fontColor=#1e293b;"
    center_entity_style = "rounded=0;whiteSpace=wrap;html=1;fontStyle=1;fontSize=16;fontFamily=Helvetica;fillColor=#d5e8d4;strokeColor=#274e13;strokeWidth=3;shadow=1;fontColor=#0f3818;"
    weak_entity_style = "shape=ext;double=1;rounded=0;whiteSpace=wrap;html=1;fontStyle=1;fontSize=14;fontFamily=Helvetica;fillColor=#e1d5e7;strokeColor=#9673a6;strokeWidth=2;shadow=1;fontColor=#2d1537;"
    summary_entity_style = "rounded=0;whiteSpace=wrap;html=1;fontStyle=1;fontSize=14;fontFamily=Helvetica;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=2;shadow=1;fontColor=#453406;"
    
    rel_style = "rhombus;whiteSpace=wrap;html=1;fontStyle=1;fontSize=13;fontFamily=Helvetica;fillColor=#ffe6cc;strokeColor=#d79b00;strokeWidth=2;fontColor=#4d2600;shadow=1;"
    ident_rel_style = "shape=rhombus;double=1;whiteSpace=wrap;html=1;fontStyle=1;fontSize=13;fontFamily=Helvetica;fillColor=#e1d5e7;strokeColor=#9673a6;strokeWidth=2;fontColor=#2d1537;shadow=1;"
    
    pk_attr_style = "ellipse;whiteSpace=wrap;html=1;fontSize=11;fontStyle=5;fontFamily=Helvetica;fillColor=#d5e8d4;strokeColor=#274e13;strokeWidth=2;fontColor=#0f3818;shadow=0;"
    uk_attr_style = "ellipse;whiteSpace=wrap;html=1;fontSize=11;fontStyle=1;fontFamily=Helvetica;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=1.5;fontColor=#3d3100;shadow=0;"
    std_attr_style = "ellipse;whiteSpace=wrap;html=1;fontSize=11;fontFamily=Helvetica;fillColor=#f8fafc;strokeColor=#64748b;strokeWidth=1.2;fontColor=#1e293b;shadow=0;"
    derived_attr_style = "ellipse;dashed=1;dashPattern=3 3;whiteSpace=wrap;html=1;fontSize=11;fontStyle=2;fontFamily=Helvetica;fillColor=#fef2f2;strokeColor=#ef4444;strokeWidth=1.5;fontColor=#991b1b;shadow=0;"
    multi_attr_style = "shape=ellipse;double=1;whiteSpace=wrap;html=1;fontSize=11;fontFamily=Helvetica;fillColor=#f0fdf4;strokeColor=#16a34a;strokeWidth=1.5;fontColor=#14532d;shadow=0;"
    
    # ----------------------------------------------------
    # Header Banner
    # ----------------------------------------------------
    add_cell(
        "<b>HAVEN HOTEL & SUITES - ENTITY-RELATIONSHIP (ER) DIAGRAM</b><br/><span style='font-size:12px;font-weight:normal;'>Course: Database Management Systems (ETCS302) · Standard Chen Notation with Entities, Attributes, Relationships & Cardinalities</span>",
        title_style, 450, 40, 1600, 70
    )

    # ----------------------------------------------------
    # 1. ENTITY: USERS (Top-Left)
    # ----------------------------------------------------
    users_x, users_y = 380, 320
    users_id = add_cell("<b>USERS</b>", entity_style, users_x, users_y, 170, 70)
    
    # USERS Attributes
    user_attrs = [
        ("<u>user_id</u> (PK)", pk_attr_style, users_x - 220, users_y - 120, 125, 45),
        ("username (UK)", uk_attr_style, users_x - 240, users_y - 50, 125, 45),
        ("full_name", std_attr_style, users_x - 240, users_y + 20, 120, 42),
        ("email (UK)", uk_attr_style, users_x - 220, users_y + 90, 125, 45),
        ("phone (UK)", uk_attr_style, users_x - 170, users_y + 160, 125, 45),
        ("password_hash", std_attr_style, users_x - 30, users_y - 150, 120, 42),
        ("role", std_attr_style, users_x + 80, users_y - 150, 110, 42),
        ("status", std_attr_style, users_x + 190, users_y - 120, 110, 42),
        ("created_at", std_attr_style, users_x - 70, users_y + 180, 115, 42)
    ]
    
    for val, sty, ax, ay, aw, ah in user_attrs:
        aid = add_cell(val, sty, ax, ay, aw, ah)
        add_edge(users_id, aid)

    # ----------------------------------------------------
    # 2. ENTITY: ROOMS (Top-Right)
    # ----------------------------------------------------
    rooms_x, rooms_y = 1920, 320
    rooms_id = add_cell("<b>ROOMS</b>", entity_style, rooms_x, rooms_y, 170, 70)
    
    # ROOMS Attributes
    room_attrs = [
        ("<u>room_id</u> (PK)", pk_attr_style, rooms_x + 230, rooms_y - 120, 125, 45),
        ("room_number (UK)", uk_attr_style, rooms_x + 250, rooms_y - 50, 135, 45),
        ("room_type", std_attr_style, rooms_x + 250, rooms_y + 20, 120, 42),
        ("capacity", std_attr_style, rooms_x + 230, rooms_y + 90, 115, 42),
        ("price_per_night", std_attr_style, rooms_x + 180, rooms_y + 160, 125, 42),
        ("amenities", multi_attr_style, rooms_x - 80, rooms_y - 150, 125, 45),
        ("image_url", std_attr_style, rooms_x + 40, rooms_y - 150, 115, 42),
        ("status", std_attr_style, rooms_x + 150, rooms_y - 150, 110, 42)
    ]
    
    for val, sty, ax, ay, aw, ah in room_attrs:
        aid = add_cell(val, sty, ax, ay, aw, ah)
        add_edge(rooms_id, aid)

    # ----------------------------------------------------
    # 3. ENTITY: BOOKINGS (Center Master Transaction)
    # ----------------------------------------------------
    book_x, book_y = 1150, 720
    book_id = add_cell("<b>BOOKINGS</b>", center_entity_style, book_x, book_y, 200, 80)
    
    # BOOKINGS Attributes (Radiating around center)
    booking_attrs = [
        ("<u>booking_id</u> (PK)", pk_attr_style, book_x - 220, book_y - 110, 135, 46),
        ("check_in", std_attr_style, book_x - 170, book_y - 170, 115, 42),
        ("check_in_time", std_attr_style, book_x - 50, book_y - 190, 120, 42),
        ("check_out", std_attr_style, book_x + 80, book_y - 190, 115, 42),
        ("check_out_time", std_attr_style, book_x + 200, book_y - 170, 125, 42),
        ("guest_count", std_attr_style, book_x + 250, book_y - 110, 115, 42),
        
        ("total_amount", std_attr_style, book_x - 260, book_y - 40, 120, 42),
        ("advance_paid (25%)", std_attr_style, book_x - 270, book_y + 30, 135, 45),
        ("balance_amount (75%)", derived_attr_style, book_x - 260, book_y + 100, 145, 45),
        
        ("payment_mode", std_attr_style, book_x + 240, book_y - 40, 120, 42),
        ("payment_status", std_attr_style, book_x + 250, book_y + 30, 125, 42),
        ("booking_status", std_attr_style, book_x + 240, book_y + 100, 125, 42),
        
        ("cancelled_by", std_attr_style, book_x - 170, book_y + 180, 120, 42),
        ("cancellation_reason", std_attr_style, book_x - 40, book_y + 200, 140, 45),
        ("created_at", std_attr_style, book_x + 110, book_y + 180, 115, 42)
    ]
    
    for val, sty, ax, ay, aw, ah in booking_attrs:
        aid = add_cell(val, sty, ax, ay, aw, ah)
        add_edge(book_id, aid)

    # ----------------------------------------------------
    # 4. ENTITY: PAYMENTS (Bottom-Left)
    # ----------------------------------------------------
    pay_x, pay_y = 380, 1150
    pay_id = add_cell("<b>PAYMENTS</b>", entity_style, pay_x, pay_y, 170, 70)
    
    # PAYMENTS Attributes
    pay_attrs = [
        ("<u>pay_id</u> (PK)", pk_attr_style, pay_x - 210, pay_y - 100, 125, 45),
        ("gateway_order_id (UK)", uk_attr_style, pay_x - 250, pay_y - 30, 150, 45),
        ("gateway_payment_id (UK)", uk_attr_style, pay_x - 250, pay_y + 40, 155, 45),
        ("amount", std_attr_style, pay_x - 200, pay_y + 110, 115, 42),
        ("currency", std_attr_style, pay_x - 90, pay_y + 160, 110, 42),
        ("method", std_attr_style, pay_x + 30, pay_y + 160, 110, 42),
        ("status", std_attr_style, pay_x + 150, pay_y + 150, 110, 42),
        ("created_at", std_attr_style, pay_x - 60, pay_y - 140, 115, 42),
        ("updated_at", std_attr_style, pay_x + 60, pay_y - 140, 115, 42)
    ]
    
    for val, sty, ax, ay, aw, ah in pay_attrs:
        aid = add_cell(val, sty, ax, ay, aw, ah)
        add_edge(pay_id, aid)

    # ----------------------------------------------------
    # 5. WEAK ENTITY: BOOKING_AUDIT (Bottom-Right)
    # ----------------------------------------------------
    audit_x, audit_y = 1920, 1150
    audit_id = add_cell("<b>BOOKING_AUDIT</b>", weak_entity_style, audit_x, audit_y, 180, 70)
    
    # BOOKING_AUDIT Attributes
    audit_attrs = [
        ("<u>audit_id</u> (PK)", pk_attr_style, audit_x + 220, audit_y - 90, 125, 45),
        ("action_type", std_attr_style, audit_x + 240, audit_y - 20, 120, 42),
        ("old_status", std_attr_style, audit_x + 240, audit_y + 50, 115, 42),
        ("new_status", std_attr_style, audit_x + 210, audit_y + 120, 115, 42),
        ("details", std_attr_style, audit_x + 80, audit_y + 160, 120, 42),
        ("changed_at", std_attr_style, audit_x - 40, audit_y + 160, 115, 42)
    ]
    
    for val, sty, ax, ay, aw, ah in audit_attrs:
        aid = add_cell(val, sty, ax, ay, aw, ah)
        add_edge(audit_id, aid)

    # ----------------------------------------------------
    # 6. REPORTING ENTITY: REPORT_ROOM_SUMMARY (Right Center)
    # ----------------------------------------------------
    summary_x, summary_y = 2100, 725
    summary_id = add_cell("<b>REPORT_ROOM_SUMMARY</b><br/><span style='font-size:10px;font-weight:normal;'>[Cursor Derived]</span>", summary_entity_style, summary_x, summary_y, 190, 75)
    
    # REPORT_ROOM_SUMMARY Attributes
    sum_attrs = [
        ("<u>summary_id</u> (PK)", pk_attr_style, summary_x - 40, summary_y - 120, 135, 45),
        ("room_type", std_attr_style, summary_x + 80, summary_y - 120, 115, 42),
        ("total_rooms", std_attr_style, summary_x + 190, summary_y - 70, 115, 42),
        ("available_rooms", std_attr_style, summary_x + 210, summary_y, 120, 42),
        ("total_bookings", std_attr_style, summary_x + 210, summary_y + 70, 120, 42),
        ("total_revenue", std_attr_style, summary_x + 180, summary_y + 140, 120, 42),
        ("average_rate", std_attr_style, summary_x + 60, summary_y + 160, 115, 42),
        ("generated_at", std_attr_style, summary_x - 60, summary_y + 150, 115, 42)
    ]
    
    for val, sty, ax, ay, aw, ah in sum_attrs:
        aid = add_cell(val, sty, ax, ay, aw, ah)
        add_edge(summary_id, aid)

    # ----------------------------------------------------
    # RELATIONSHIPS (Diamonds) & CONNECTORS
    # ----------------------------------------------------
    
    # Rel 1: USERS ---<Places / Makes>---> BOOKINGS
    # 1:N cardinality
    rel_places_id = add_cell("<b>Places</b>", rel_style, 780, 520, 130, 75)
    add_edge(users_id, rel_places_id, "1 (0..N)", "endArrow=none;html=1;strokeWidth=2;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")
    add_edge(rel_places_id, book_id, "N (1..1)", "endArrow=none;html=1;strokeWidth=3;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")

    # Rel 2: ROOMS ---<Reserves>---> BOOKINGS
    # 1:N cardinality
    rel_reserves_id = add_cell("<b>Reserves</b>", rel_style, 1570, 520, 130, 75)
    add_edge(rooms_id, rel_reserves_id, "1 (0..N)", "endArrow=none;html=1;strokeWidth=2;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")
    add_edge(rel_reserves_id, book_id, "N (1..1)", "endArrow=none;html=1;strokeWidth=3;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")

    # Rel 3: BOOKINGS ---<Paid_Via>---> PAYMENTS
    # 1:1 / 1:N cardinality
    rel_paid_id = add_cell("<b>Paid_Via</b>", rel_style, 780, 930, 130, 75)
    add_edge(book_id, rel_paid_id, "1", "endArrow=none;html=1;strokeWidth=2.5;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")
    add_edge(rel_paid_id, pay_id, "1", "endArrow=none;html=1;strokeWidth=2.5;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")

    # Rel 4: BOOKINGS ===<Generates>===> BOOKING_AUDIT
    # Identifying relationship (Double diamond) for weak entity audit trail
    rel_gen_id = add_cell("<b>Generates</b>", ident_rel_style, 1570, 930, 140, 80)
    add_edge(book_id, rel_gen_id, "1", "endArrow=none;html=1;strokeWidth=2.5;strokeColor=#1e293b;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")
    add_edge(rel_gen_id, audit_id, "N", "endArrow=none;html=1;strokeWidth=3.5;strokeColor=#6b21a8;fontSize=12;fontStyle=1;labelBackgroundColor=#ffffff;")

    # Rel 5: ROOMS ---<Aggregated_In>---> REPORT_ROOM_SUMMARY
    # 1:1 category aggregation by cursor
    rel_agg_id = add_cell("<b>Aggregated_By</b><br/><span style='font-size:9px;'>[CURSOR]</span>", rel_style, 1960, 560, 130, 75)
    add_edge(rooms_id, rel_agg_id, "1", "endArrow=none;html=1;strokeWidth=1.5;dashed=1;strokeColor=#453406;fontSize=11;labelBackgroundColor=#ffffff;")
    add_edge(rel_agg_id, summary_id, "1", "endArrow=none;html=1;strokeWidth=1.5;dashed=1;strokeColor=#453406;fontSize=11;labelBackgroundColor=#ffffff;")

    # Direct FK link between USERS and PAYMENTS (for direct payment owner tracking)
    add_edge(users_id, pay_id, "Processed_For (1:N)", "endArrow=none;html=1;dashed=1;strokeWidth=1.2;strokeColor=#94a3b8;fontSize=10;fontColor=#64748b;edgeStyle=orthogonalEdgeStyle;curved=1;")

    # ----------------------------------------------------
    # DBMS ER NOTATION LEGEND (Bottom Banner)
    # ----------------------------------------------------
    leg_x, leg_y = 350, 1520
    add_cell("<b>DBMS CHEN ER NOTATION LEGEND</b>", "text;html=1;fontStyle=1;fontSize=13;fontFamily=Helvetica;fontColor=#1e293b;", leg_x, leg_y, 250, 30)
    
    # Legend items
    add_cell("<b>Entity Set</b>", entity_style, leg_x, leg_y + 35, 120, 45)
    add_cell("Strong Entity (e.g. USERS, ROOMS)", subtitle_style, leg_x + 130, leg_y + 45, 170, 25)
    
    add_cell("<b>Weak Entity</b>", weak_entity_style, leg_x + 320, leg_y + 35, 120, 45)
    add_cell("Existence-dependent Entity (e.g. AUDIT)", subtitle_style, leg_x + 450, leg_y + 45, 180, 25)

    add_cell("<b>Relationship</b>", rel_style, leg_x + 660, leg_y + 30, 110, 55)
    add_cell("Associates Entity Sets (1:N, 1:1)", subtitle_style, leg_x + 780, leg_y + 45, 160, 25)

    add_cell("<b>Identifying Rel.</b>", ident_rel_style, leg_x + 970, leg_y + 30, 120, 55)
    add_cell("Relates Weak Entity to Strong", subtitle_style, leg_x + 1100, leg_y + 45, 160, 25)

    add_cell("<u>Primary Key</u>", pk_attr_style, leg_x + 1280, leg_y + 35, 110, 42)
    add_cell("Key Attribute (Underlined)", subtitle_style, leg_x + 1400, leg_y + 45, 150, 25)

    add_cell("Derived Attr", derived_attr_style, leg_x + 1570, leg_y + 35, 105, 42)
    add_cell("Calculated (Dashed Oval)", subtitle_style, leg_x + 1685, leg_y + 45, 140, 25)

    add_cell("Multivalued", multi_attr_style, leg_x + 1845, leg_y + 35, 105, 42)
    add_cell("Multiple Values (Double Oval)", subtitle_style, leg_x + 1960, leg_y + 45, 150, 25)

    # Convert to XML string
    xml_str = ET.tostring(mxfile, encoding='utf-8', xml_declaration=True).decode('utf-8')
    return xml_str

if __name__ == '__main__':
    content = create_er_diagram()
    output_path = "d:/hotel_management_system/hotel_management_ER_diagram.drawio"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully generated:", output_path)
