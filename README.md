# Hotel Room Reservation and Management System (DBMS Mini Project)

A complete, college-ready Database Management System (DBMS) mini project developed with **Python, Flask, MySQL Server 8.0+, HTML5, CSS3, JavaScript, and Bootstrap 5**.

Normalized to **Third Normal Form (3NF)** and fully equipped with **Primary/Foreign Key Constraints, Check Constraints, Unique Constraints, Sequences, Indexes, Views, Stored Procedures, Automated Triggers, and Cursors**.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* **Python 3.10+** (Tested with Python 3.14)
* **MySQL Server 8.0+** (Running locally on port 3306)

### 2. Configure Environment (`.env`)
Create or edit `.env` in the project root:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=1234567890
DB_NAME=hotel_management
DB_PORT=3306
FLASK_SECRET_KEY=hotel-haven-secret-key-2026-secure-session
```

### 3. Initialize the Database
Open PowerShell in the project directory and run:
```powershell
Get-Content schema.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p1234567890
```
*(Or open `schema.sql` in MySQL Workbench and execute the full script).*

### 4. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 5. Run the Application
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your web browser.

---

## 🔑 Login Credentials (Common Login Portal)

The project features a **single, shared login page** at `http://127.0.0.1:5000/login`. The system automatically identifies the user's role and directs them to their respective dashboard:

| Role | Username / Email | Password | Destination Dashboard |
|:---|:---|:---|:---|
| **Administrator** | `admin` (or `admin@hotel.com`) | `admin123` | **Admin Control Center (`/admin`)** |
| **Guest Customer** | `john_doe` (or `john@example.com`) | `password123` | **Guest Reservations (`/dashboard`)** |
| **Guest Customer** | `priya_sharma` (or `priya@example.com`) | `password123` | **Guest Reservations (`/dashboard`)** |

*Note: New customers can also register at `/register`.*

---

## 🌟 Key Features

### 👤 Guest / Customer Experience
* **Multiple Room Categories:** Standard, Deluxe, Suite, Family, and Executive rooms.
* **Email OTP Verification on Sign Up (`/register`):** Live 6-digit OTP verification sent to the customer's email address with resend cooldown and instant verification before account creation.
* **Smart Date Availability Search:** Filter by check-in, check-out dates, room category, and guest count. Uses a correlated nested subquery (`NOT EXISTS`) to guarantee zero booking collisions.
* **Dynamic QR Code Payment (`/checkout`):**
  - Calculates stay cost and 25% advance amount dynamically according to room selection.
  - Automatically generates a scannable payment QR code bound to the machine's local Wi-Fi / LAN IP.
  - Openable directly on any mobile phone on the same Wi-Fi network.
  - Mobile payment sheet (`/pay/<order_id>`) supports dummy UPI (GPay/PhonePe/Paytm), Card, and Net Banking options.
  - Real-time desktop polling automatically detects phone payment completion and confirms the reservation.
* **Personal Dashboard:** Review booking history, stay periods, night duration, and total amount.
* **Booking Cancellation & Offline Refund:** Customers can cancel upcoming confirmed reservations (automatically triggering the database audit trail and setting payment status to Refunded).

### 👑 Administrator Management Center
* **Dashboard KPIs:** Real-time metrics for total inventory, available rooms, confirmed reservations, registered guests, and total recognized revenue.
* **Room Inventory Management (`/admin/rooms`):** Add new rooms, adjust nightly prices, edit amenities, and toggle maintenance status. Foreign key restrictions prevent deleting rooms tied to reservations.
* **Reservation Lifecycle Management (`/admin/bookings`):** Filter by status, perform guest check-in, check-out, or cancellation.
* **Customer Account Control (`/admin/users`):** View registered accounts and activate/deactivate customer access.
* **Financial & Occupancy Reports (`/admin/reports`):** Query monthly summaries directly from MySQL Views, analyze room category earnings via `GROUP BY`, and interactively execute stored procedures.
* **DBMS Diagnostics Hub (`/admin/database`):**
  - **Live Trigger Audit Trail:** Real-time log of changes captured by database triggers in `booking_audit`.
  - **Cursor Execution Runner:** Executes row-by-row procedural processing via `sp_process_occupancy_cursor()`.
  - **Views Inspector:** Inspects `vw_active_reservations` and `vw_room_inventory_status`.
  - **SQL Query Showcase:** Tabbed viva cheatsheet containing all required queries.

---

## 📊 Database Architecture & SQL Syllabus Checklist

All requirements from the academic DBMS evaluation criteria are implemented and verifiable:

- [x] **Problem Statement:** Clear formulation for hospitality domain.
- [x] **Database Design:** Entities (`users`, `rooms`, `bookings`, `payments`, `booking_audit`, `report_room_summary`).
- [x] **ER Diagram:** Mermaid diagram and relational entity mappings.
- [x] **3NF Normalization:** Zero partial or transitive dependencies.
- [x] **Constraints:** Primary Keys, Foreign Keys (`ON UPDATE CASCADE ON DELETE RESTRICT`), Unique constraints, and CHECK constraints (`capacity`, `price`, `dates`, `guests`, `total`).
- [x] **Sequences:** `AUTO_INCREMENT` offsets (`users` starts at 1001, `rooms` at 101, `bookings` at 5001).
- [x] **Basic CRUD:** SELECT, INSERT, UPDATE, DELETE queries in `queries.sql`.
- [x] **JOIN Operations:** `INNER JOIN` (guest booking receipts) and `LEFT OUTER JOIN` (category performance).
- [x] **Nested Queries & Subqueries:** Correlated `NOT EXISTS` date availability check, `IN` subqueries, and scalar comparisons against hotel averages.
- [x] **Aggregates & GROUP BY:** `COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()` with `HAVING COUNT(*) >= 2`.
- [x] **Views:** `vw_monthly_booking_summary`, `vw_active_reservations`, `vw_room_inventory_status`.
- [x] **Indexes:** Composite performance indexes on `bookings(room_id, check_in, check_out, booking_status)` and `rooms(room_type, status, price_per_night)`.
- [x] **Stored Procedures:**
  - `sp_monthly_booking_summary(p_year, p_month)`
  - `sp_get_room_type_stats(p_room_type, OUT ...)` (with IN and OUT parameters).
- [x] **Database Triggers:**
  - `trg_booking_insert_audit` (AFTER INSERT ON bookings)
  - `trg_booking_status_audit` (AFTER UPDATE ON bookings)
- [x] **Cursor Routine:**
  - `sp_process_occupancy_cursor()` (Row-by-row iteration across room categories).
- [x] **User Interface:** Clean, responsive Flask frontend with Bootstrap 5.
- [x] **Comprehensive Documentation:** `PROJECT_REPORT.md` and `DOCUMENTATION.md`.

---

## 🧪 Running Automated Unit Tests

Run the built-in test suite to verify all endpoints, RBAC permissions, and database operations:
```bash
python test_app.py
```

Expected output:
```text
[PASS] Landing page loads successfully
[PASS] Email and phone validation helpers work accurately
[PASS] Registration email OTP generation and verification enforced successfully
[PASS] Dynamic QR Code generation, Wi-Fi mobile payment, and desktop polling verified successfully
[PASS] Admin cancellation notice and unavoidable reason visible on guest dashboard
[PASS] Full registration cycle with OTP verification and login completed successfully
Ran 6 tests in 0.976s - OK
```

---

## 📁 Project Structure

```text
hotel_management_system/
├── .env                       # Database credentials, SMTP settings & server host config
├── .env.example               # Example configuration template
├── app.py                     # Main Flask web application, QR payment logic & API routing
├── create_admin.py            # CLI script to provision administrators
├── queries.sql                # Complete portfolio of SQL queries for evaluation
├── schema.sql                 # MySQL 3NF schema, triggers, procedures, views & seed data
├── test_app.py                # Automated test suite (6 comprehensive unit tests)
├── test_email.py              # CLI utility to test actual email OTP delivery
├── requirements.txt           # Python package requirements (Flask, mysql-connector, qrcode, pillow, requests)
├── README.md                  # Project overview and instructions
├── PROJECT_REPORT.md          # Comprehensive academic project report
├── static/
│   ├── css/
│   │   └── style.css          # Modern styling and custom components
│   └── js/
│       └── main.js            # Frontend interactivity
└── templates/
    ├── base.html              # Base layout with responsive navigation & alerts
    ├── index.html             # Landing page with room showcase
    ├── login.html             # Shared login portal with quick demo helpers
    ├── register.html          # Customer registration form with live Email OTP verification
    ├── checkout.html          # Reservation checkout with dynamic Wi-Fi Payment QR Code
    ├── pay_mobile.html        # Mobile payment sheet for smartphones on same Wi-Fi
    ├── dashboard.html         # Customer personal reservations dashboard
    ├── rooms.html             # Room catalog, search filters & booking forms
    ├── admin_dashboard.html   # Administrator KPI overview & control hub
    ├── admin_rooms.html       # Room inventory management (Add/Edit/Delete)
    ├── admin_bookings.html    # Booking management & status lifecycle
    ├── admin_users.html       # Customer accounts management
    ├── admin_reports.html     # Financial reports & stored procedure executor
    ├── admin_database.html    # DBMS Diagnostics Hub (Triggers, Cursors, Views)
    └── error.html             # HTTP 403/404/500 error pages
```
