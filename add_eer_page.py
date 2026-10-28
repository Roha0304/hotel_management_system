import xml.etree.ElementTree as ET

def build_eer_diagram():
    page_id = 'eer_diagram'
    page_name = 'EER Diagram (Exact Image Match)'
    diag = ET.Element('diagram', {'id': page_id, 'name': page_name})
    
    model = ET.SubElement(diag, 'mxGraphModel', {
        'dx': '1400', 'dy': '900', 'grid': '1', 'gridSize': '10', 'guides': '1',
        'tooltips': '1', 'connect': '1', 'arrows': '1', 'fold': '1', 'page': '1',
        'pageScale': '1', 'pageWidth': '1700', 'pageHeight': '1100',
        'background': '#ffffff', 'math': '0', 'shadow': '0'
    })
    
    root = ET.SubElement(model, 'root')
    ET.SubElement(root, 'mxCell', {'id': '0'})
    ET.SubElement(root, 'mxCell', {'id': '1', 'parent': '0'})
    
    cell_id = 500
    def get_id():
        nonlocal cell_id
        cell_id += 1
        return str(cell_id)

    def add_cell(value, style, x, y, w, h):
        cid = get_id()
        cell = ET.SubElement(root, 'mxCell', {
            'id': cid, 'value': value, 'style': style, 'parent': '1', 'vertex': '1'
        })
        ET.SubElement(cell, 'mxGeometry', {
            'x': str(x), 'y': str(y), 'width': str(w), 'height': str(h), 'as': 'geometry'
        })
        return cid

    def add_edge(source_id, target_id, label, style):
        cid = get_id()
        cell = ET.SubElement(root, 'mxCell', {
            'id': cid, 'value': label, 'style': style, 'parent': '1', 'edge': '1',
            'source': source_id, 'target': target_id
        })
        ET.SubElement(cell, 'mxGeometry', {'relative': '1', 'as': 'geometry'})
        return cid

    # Top Title
    add_cell(
        "<b><font style='font-size: 24px; color: #1e3a8a;'>Enhanced Entity-Relationship (EER) Diagram</font></b><br/>"
        "<i><font style='font-size: 14px; color: #475569;'>Hotel Room Booking and Reservation Management System (hotel_management)</font></i>",
        "text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;",
        400, 20, 800, 50
    )

    # Top Left Legend Box
    add_cell(
        "<div style='font-family: Arial, sans-serif; font-size: 11px;'>"
        "<span style='color: #dc2626; font-weight: bold;'>PK = Primary Key</span>&nbsp;&nbsp;&nbsp;&nbsp;"
        "<span style='color: #2563eb; font-weight: bold;'>FK = Foreign Key</span>&nbsp;&nbsp;&nbsp;&nbsp;"
        "<span style='color: #b45309; font-weight: bold;'>UQ = Unique Key</span><br/>"
        "<span style='color: #64748b; font-size: 10px;'>Relational Model: Normalized to Third Normal Form (3NF)</span>"
        "</div>",
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#cbd5e1;strokeWidth=1;align=left;spacingLeft=10;verticalAlign=middle;",
        60, 45, 340, 42
    )

    # Table card helper
    def create_table_card(title, header_bg, fields, x, y, w, h):
        content = f"<div style='margin-top: -6px;'><div style='background-color: {header_bg}; color: #ffffff; padding: 6px 10px; font-weight: bold; font-size: 13px; text-align: center; border-radius: 4px 4px 0 0; margin: -10px -10px 8px -10px;'>{title}</div>"
        content += "<div style='font-family: Consolas, monospace, sans-serif; font-size: 11px; line-height: 1.5; color: #1e293b; padding: 0 4px;'>"
        for f in fields:
            prefix = ""
            if f.startswith("PK"):
                prefix = "<b style='color: #dc2626;'>PK</b> "
                f = f[3:].strip()
            elif f.startswith("FK"):
                prefix = "<b style='color: #2563eb;'>FK</b> "
                f = f[3:].strip()
            else:
                prefix = "<span style='color: #94a3b8;'>•</span> "
            
            # Highlight UQ
            f = f.replace("(UQ)", "<b style='color: #b45309;'>(UQ)</b>")
            content += f"<div>{prefix}{f}</div>"
        content += "</div></div>"
        
        style = f"rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor={header_bg};strokeWidth=2;align=left;verticalAlign=top;spacingLeft=10;spacingTop=10;shadow=1;"
        return add_cell(content, style, x, y, w, h)

    # 1. USERS
    users_fields = [
        "PK user_id INT AUTO_INC",
        "username VARCHAR(50) (UQ)",
        "full_name VARCHAR(100)",
        "email VARCHAR(150) (UQ)",
        "phone VARCHAR(20) (UQ)",
        "password_hash VARCHAR(255)",
        "role ENUM('customer','admin')",
        "status ENUM('Active','Inactive')",
        "created_at TIMESTAMP"
    ]
    u_id = create_table_card("USERS (Guests & Admins)", "#1e5aa8", users_fields, 60, 115, 320, 310)

    # 2. BOOKINGS
    bookings_fields = [
        "PK booking_id INT AUTO_INC",
        "FK user_id INT (FK → users)",
        "FK room_id INT (FK → rooms)",
        "check_in DATE & check_in_time",
        "check_out DATE & check_out_time",
        "guest_count TINYINT",
        "total_amount DECIMAL(10,2)",
        "advance_paid DECIMAL(10,2) [25%]",
        "balance_amount DECIMAL(10,2) [75%]",
        "payment_mode ENUM('Card','UPI/QR'..)",
        "payment_status ENUM('Advance Paid'..)",
        "booking_status ENUM('Confirmed'..)",
        "cancelled_by ENUM('customer','admin')",
        "cancellation_reason VARCHAR(255)",
        "created_at TIMESTAMP"
    ]
    b_id = create_table_card("BOOKINGS (Reservations & 25% Advance)", "#c25e00", bookings_fields, 480, 145, 340, 440)

    # 3. ROOMS
    rooms_fields = [
        "PK room_id INT AUTO_INC",
        "room_number VARCHAR(10) (UQ)",
        "room_type ENUM('Standard'..)",
        "capacity TINYINT (1-10)",
        "price_per_night DECIMAL(10,2)",
        "amenities VARCHAR(500)",
        "image_url VARCHAR(500)",
        "status ENUM('Available'..)",
        "created_at TIMESTAMP"
    ]
    r_id = create_table_card("ROOMS (Physical Inventory)", "#1e6b37", rooms_fields, 920, 115, 320, 310)

    # 4. PAYMENTS
    payments_fields = [
        "PK pay_id INT AUTO_INC",
        "FK user_id INT (FK → users)",
        "FK room_id INT (FK → rooms)",
        "FK booking_id INT (FK → bookings)",
        "amount DECIMAL(10,2) [25% Adv]",
        "currency CHAR(3) DEFAULT 'INR'",
        "gateway_order_id VARCHAR(64) (UQ)",
        "gateway_payment_id VARCHAR(64)",
        "method VARCHAR(30)",
        "status ENUM('Created','Paid'..)",
        "created_at & updated_at"
    ]
    p_id = create_table_card("PAYMENTS (Transaction Ledger)", "#5c3a93", payments_fields, 60, 480, 320, 340)

    # 5. BOOKING_AUDIT
    audit_fields = [
        "PK audit_id BIGINT AUTO_INC",
        "FK booking_id INT (FK)",
        "action_type VARCHAR(30)",
        "old_status VARCHAR(30)",
        "new_status VARCHAR(30)",
        "details VARCHAR(255)",
        "changed_at TIMESTAMP"
    ]
    a_id = create_table_card("BOOKING_AUDIT (Trigger Logs)", "#3d4b5c", audit_fields, 920, 460, 320, 240)

    # 6. REPORT_ROOM_SUMMARY
    summary_fields = [
        "PK summary_id INT AUTO_INC",
        "room_type VARCHAR(50)",
        "total_rooms, available_rooms INT",
        "total_bookings, revenue, avg_rate"
    ]
    s_id = create_table_card("REPORT_ROOM_SUMMARY (Cursor)", "#824513", summary_fields, 920, 735, 320, 160)

    # Connectors & Cardinalities exactly matching the photo
    # USERS -> BOOKINGS (1 : N places)
    add_edge(
        u_id, b_id, "1 : N<br/><b>places</b>",
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#1e5aa8;strokeWidth=2;fontSize=11;fontColor=#1e5aa8;labelBackgroundColor=#ffffff;endArrow=block;endFill=1;"
    )

    # ROOMS -> BOOKINGS (1 : N reserved)
    add_edge(
        r_id, b_id, "1 : N<br/><b>reserved</b>",
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#1e6b37;strokeWidth=2;fontSize=11;fontColor=#1e6b37;labelBackgroundColor=#ffffff;endArrow=block;endFill=1;"
    )

    # BOOKINGS -> PAYMENTS (1 : 1 paid by)
    add_edge(
        b_id, p_id, "1 : 1<br/><b>paid by</b>",
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#5c3a93;strokeWidth=2;fontSize=11;fontColor=#5c3a93;labelBackgroundColor=#ffffff;endArrow=block;endFill=1;entryX=1;entryY=0.5;exitX=0;exitY=0.85;"
    )

    # BOOKINGS -> BOOKING_AUDIT (1 : N audits)
    add_edge(
        b_id, a_id, "1 : N<br/><b>audits</b>",
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#3d4b5c;strokeWidth=2;fontSize=11;fontColor=#3d4b5c;labelBackgroundColor=#ffffff;endArrow=block;endFill=1;exitX=1;exitY=0.85;entryX=0;entryY=0.5;"
    )

    return diag

if __name__ == '__main__':
    eer_diag = build_eer_diagram()
    
    # 1. Save standalone EER diagram
    single_mx = ET.Element('mxfile', {
        'host': 'app.diagrams.net',
        'agent': 'Antigravity DBMS Modeler',
        'version': '21.0.0',
        'type': 'device'
    })
    single_mx.append(eer_diag)
    single_xml = ET.tostring(single_mx, encoding='utf-8', xml_declaration=True).decode('utf-8')
    with open('d:/hotel_management_system/hotel_management_EER_diagram.drawio', 'w', encoding='utf-8') as f:
        f.write(single_xml)
    print("Generated standalone EER diagram: d:/hotel_management_system/hotel_management_EER_diagram.drawio")

    # 2. Also append EER tab to the multi-tab drawio file
    try:
        master_tree = ET.parse('d:/hotel_management_system/hotel_management_ER_diagram.drawio')
        root = master_tree.getroot()
        # Check if already exists
        existing = root.find(".//diagram[@id='eer_diagram']")
        if existing is not None:
            root.remove(existing)
        root.append(eer_diag)
        updated_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')
        with open('d:/hotel_management_system/hotel_management_ER_diagram.drawio', 'w', encoding='utf-8') as f:
            f.write(updated_xml)
        print("Appended EER Diagram tab to d:/hotel_management_system/hotel_management_ER_diagram.drawio")
    except Exception as e:
        print("Error appending to multi-page:", e)
