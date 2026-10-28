import os
import re
import json
import time
import socket
import io
import base64
import secrets
import smtplib
from email.message import EmailMessage
from datetime import date, datetime
from functools import wraps
from decimal import Decimal

from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
import requests

from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "hotel-haven-secret-key-2026-secure-session")

def get_db_config():
    """Build database connection parameters supporting both local MySQL and cloud providers (Railway, Render, TiDB, Aiven)."""
    db_url = os.environ.get("MYSQL_URL") or os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith(("mysql://", "mysql+mysqlconnector://")):
        if db_url.startswith("mysql+mysqlconnector://"):
            db_url = "mysql://" + db_url[len("mysql+mysqlconnector://"):]
        parsed = urlparse(db_url)
        cfg = {
            "host": parsed.hostname or "localhost",
            "user": parsed.username or "root",
            "password": parsed.password or "",
            "database": parsed.path.lstrip("/") if parsed.path else "hotel_management",
            "port": int(parsed.port) if parsed.port else 3306,
        }
    else:
        cfg = {
            "host": os.environ.get("DB_HOST") or os.environ.get("MYSQLHOST") or "localhost",
            "user": os.environ.get("DB_USER") or os.environ.get("MYSQLUSER") or "root",
            "password": os.environ.get("DB_PASSWORD") or os.environ.get("MYSQLPASSWORD") or "1234567890",
            "database": os.environ.get("DB_NAME") or os.environ.get("MYSQLDATABASE") or "hotel_management",
            "port": int(os.environ.get("DB_PORT") or os.environ.get("MYSQLPORT") or "3306"),
        }

    # SSL support for cloud databases (TiDB Cloud, Aiven, etc.)
    ssl_mode = os.environ.get("DB_SSL", "").lower()
    if ssl_mode in ("true", "1", "yes", "require"):
        cfg["ssl_disabled"] = False
    return cfg

DB_CONFIG = get_db_config()

METHOD_TO_MODE = {
    "card": "Credit/Debit Card",
    "upi": "UPI / QR",
    "netbanking": "Net Banking",
    "Credit/Debit Card": "Credit/Debit Card",
    "UPI / QR": "UPI / QR",
    "Net Banking": "Net Banking",
}

# ====================================================================
# DATABASE HELPER FUNCTIONS
# ====================================================================

def get_db():
    """Establish and return a MySQL connection."""
    cfg = get_db_config()
    return mysql.connector.connect(**cfg)

def query_all(sql, params=()):
    """Execute a SELECT query and return all rows as dictionaries."""
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def query_one(sql, params=()):
    """Execute a SELECT query and return the first row or None."""
    rows = query_all(sql, params)
    return rows[0] if rows else None

def execute(sql, params=()):
    """Execute an INSERT, UPDATE, or DELETE query and return lastrowid / affected rows."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid if cur.lastrowid else cur.rowcount
    finally:
        cur.close()
        conn.close()

# Standard Check-in and Check-out Time Slot Choices
CHECK_IN_TIMES = [
    "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM",
    "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM",
    "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM", "08:00 PM"
]

CHECK_OUT_TIMES = [
    "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM",
    "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM",
    "04:00 PM", "05:00 PM", "06:00 PM"
]

def sync_room_status(room_id=None):
    """
    Synchronizes room inventory status ('Available', 'Booked', 'Occupied', 'Maintenance', 'Inactive')
    with actual customer bookings in real-time.
    """
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        if room_id:
            cur.execute("SELECT room_id, status FROM rooms WHERE room_id = %s", (room_id,))
        else:
            cur.execute("SELECT room_id, status FROM rooms")
        rooms_to_check = cur.fetchall()

        for r in rooms_to_check:
            rid = r["room_id"]
            curr = r["status"]
            # Preserve administrative Maintenance or Inactive
            if curr in ("Maintenance", "Inactive"):
                continue

            # 1. Active ongoing stay (Checked In)
            cur.execute("""
                SELECT booking_id FROM bookings
                WHERE room_id = %s AND booking_status = 'Checked In'
                  AND check_in <= CURDATE() AND check_out >= CURDATE()
                LIMIT 1
            """, (rid,))
            if cur.fetchone():
                if curr != "Occupied":
                    cur.execute("UPDATE rooms SET status = 'Occupied' WHERE room_id = %s", (rid,))
                continue

            # 2. Confirmed reservation (upcoming or current)
            cur.execute("""
                SELECT booking_id FROM bookings
                WHERE room_id = %s AND booking_status = 'Confirmed'
                  AND check_out >= CURDATE()
                LIMIT 1
            """, (rid,))
            if cur.fetchone():
                if curr != "Booked":
                    cur.execute("UPDATE rooms SET status = 'Booked' WHERE room_id = %s", (rid,))
            else:
                if curr in ("Booked", "Occupied"):
                    cur.execute("UPDATE rooms SET status = 'Available' WHERE room_id = %s", (rid,))

        conn.commit()
    except Exception as e:
        app.logger.error("Error synchronizing room status: %s", e)
    finally:
        cur.close()
        conn.close()

# ====================================================================
# VALIDATION HELPERS (EMAIL & PHONE NUMBER)
# ====================================================================

def is_valid_email(email):
    """Validate email format with standard pattern."""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email.strip()))

def clean_and_validate_phone(phone_str):
    """
    Validate phone number.
    Strips spaces, hyphens, and leading +91 / 0.
    Ensures 10 valid digits (standard Indian mobile format starting with 6, 7, 8, or 9).
    """
    digits = re.sub(r'[\s\-\(\)\+]', '', phone_str.strip())
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]
    
    if len(digits) == 10 and digits.isdigit() and digits[0] in '6789':
        return True, f"+91 {digits[:5]} {digits[5:]}"
    elif len(digits) == 10 and digits.isdigit():
        return True, f"+91 {digits}"
    return False, None

def get_local_ip():
    """
    Detect the local Wi-Fi / LAN IP address so smartphones on the same Wi-Fi
    network can access the QR payment page.
    """
    configured_host = os.environ.get("SERVER_HOST", "").strip()
    if configured_host and configured_host.lower() != "auto":
        return configured_host
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()
    return local_ip

def generate_qr_base64(data_text):
    """Generate a clean base64-encoded PNG QR code image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a4d2e", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def send_otp_email(to_email, otp):
    """
    Sends an actual OTP verification email to the user's inbox.
    Supports:
      1. Resend API (set RESEND_API_KEY in .env)
      2. Brevo / SMTP Relay (set SMTP_SERVER=smtp-relay.brevo.com, SMTP_USER, SMTP_PASSWORD)
    Returns (success_boolean, message).
    """
    if app.config.get("TESTING"):
        return True, "Test mode: OTP generated."

    plain_text = f"""Hello,

Thank you for registering at Haven Hotel & Suites!

Your One-Time Password (OTP) for email verification is:
{otp}

This code is valid for 10 minutes. Please enter it on the registration page to complete your account setup.

Warm regards,
Haven Hotel & Suites Team
"""
    html_text = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8faf9; margin: 0; padding: 24px;">
      <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <div style="background-color: #1a4d2e; padding: 24px; text-align: center; color: #ffffff;">
          <h1 style="margin: 0; font-size: 24px; letter-spacing: 1px;">HAVEN HOTEL & SUITES</h1>
          <p style="margin: 6px 0 0; font-size: 13px; opacity: 0.85;">Guest Account Email Verification</p>
        </div>
        <div style="padding: 32px 24px;">
          <h2 style="font-size: 18px; color: #1e293b; margin-top: 0;">Verify your email address</h2>
          <p style="font-size: 14px; line-height: 1.6; color: #475569;">
            Please enter the following 6-digit One-Time Password (OTP) to complete your account registration:
          </p>
          <div style="text-align: center; margin: 28px 0;">
            <div style="display: inline-block; background-color: #f1f8f4; border: 2px dashed #1a4d2e; border-radius: 8px; padding: 14px 32px;">
              <span style="font-size: 32px; font-weight: 700; letter-spacing: 8px; color: #1a4d2e; font-family: monospace;">{otp}</span>
            </div>
          </div>
          <p style="font-size: 13px; color: #64748b; line-height: 1.5; margin-bottom: 0;">
            <strong style="color: #334155;">Note:</strong> Valid for <strong>10 minutes</strong>. Do not share this OTP with anyone.
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    # --- 1. Standard SMTP / Gmail / Brevo (No domain restriction: sends to ANY email) ---
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "").strip().replace(" ", "")

    if smtp_user and smtp_password:
        smtp_from_raw = os.environ.get("SMTP_FROM", "").strip()
        if smtp_from_raw:
            smtp_from = smtp_from_raw if "<" in smtp_from_raw else f"Haven Hotel & Suites <{smtp_from_raw}>"
        else:
            smtp_from = f"Haven Hotel & Suites <{smtp_user}>"

        try:
            msg = EmailMessage()
            msg["Subject"] = f"Haven Hotel - Email Verification Code: {otp}"
            msg["From"] = smtp_from
            msg["To"] = to_email
            msg.set_content(plain_text)
            msg.add_alternative(html_text, subtype="html")

            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15) as server:
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            return True, "Verification email delivered to your inbox."
        except smtplib.SMTPAuthenticationError:
            app.logger.exception("SMTP authentication failed")
            return False, "SMTP authentication failed: Invalid email or App Password. If using Gmail, make sure to generate and use a 16-character Google App Password."
        except Exception as e:
            app.logger.exception("Failed to send verification email via SMTP")
            return False, f"Email delivery failed: {str(e)}"

    # --- 2. Resend API (Fallback if RESEND_API_KEY is configured) ---
    resend_key = os.environ.get("RESEND_API_KEY", "").strip()
    if resend_key:
        try:
            from_sender = os.environ.get("SMTP_FROM", "").strip() or "Haven Hotel <onboarding@resend.dev>"
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": from_sender,
                    "to": [to_email],
                    "subject": f"Haven Hotel - Email Verification Code: {otp}",
                    "html": html_text,
                    "text": plain_text
                },
                timeout=15
            )
            if resp.status_code in (200, 201):
                return True, "Verification email delivered to your inbox."
            err_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            err_msg = err_data.get("message", resp.text)
            return False, f"Resend API error: {err_msg}"
        except Exception as e:
            app.logger.exception("Failed to send email via Resend API")
            return False, f"Resend delivery failed: {str(e)}"

    return False, "Email service is not configured yet. Please configure your Gmail or Brevo credentials in .env to send actual OTP emails."

# ====================================================================
# AUTHENTICATION & ACCESS CONTROL DECORATORS
# ====================================================================

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in to continue.", "warning")
                return redirect(url_for("login"))
            if session.get("role") != role:
                abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator

# ====================================================================
# JINJA TEMPLATE FILTERS
# ====================================================================

@app.template_filter("money")
def money(value):
    try:
        return f"₹{Decimal(str(value)):,.2f}"
    except Exception:
        return f"₹{value}"

@app.template_filter("advance")
def advance(value):
    try:
        return f"₹{(Decimal(str(value)) * Decimal('0.25')):,.2f}"
    except Exception:
        return f"₹{value}"

@app.template_filter("format_date")
def format_date(value):
    if not value:
        return "—"
    if isinstance(value, (datetime, date)):
        return value.strftime("%d %b %Y")
    try:
        return datetime.fromisoformat(str(value)).strftime("%d %b %Y")
    except Exception:
        return str(value)

@app.context_processor
def inject_booking_defaults():
    return dict(
        check_in_times=CHECK_IN_TIMES,
        check_out_times=CHECK_OUT_TIMES
    )

# ====================================================================
# PUBLIC ROUTES
# ====================================================================

@app.route("/")
def index():
    """Landing page: showcases hotel room categories, photos, and features."""
    rooms = query_all("""
        SELECT 
          room_type, 
          MIN(price_per_night) AS price, 
          COUNT(*) AS room_count,
          MAX(capacity) AS capacity, 
          MIN(image_url) AS image_url,
          GROUP_CONCAT(DISTINCT amenities SEPARATOR ', ') AS amenities
        FROM rooms 
        WHERE status = 'Available'
        GROUP BY room_type 
        ORDER BY price ASC
    """)
    return render_template("index.html", rooms=rooms)

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Common login page for both customer and admin.
    Accepts either Email or Username.
    """
    if session.get("user_id"):
        return redirect(url_for("admin_dashboard" if session.get("role") == "admin" else "dashboard"))

    if request.method == "POST":
        login_input = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Lookup by email OR username
        user = query_one("""
            SELECT user_id, username, full_name, email, password_hash, role, status 
            FROM users 
            WHERE LOWER(email) = LOWER(%s) OR LOWER(username) = LOWER(%s)
        """, (login_input, login_input))

        if user and user["status"] == "Active" and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["name"] = user["full_name"]
            session["email"] = user["email"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['full_name']}! Signed in as {user['role'].title()}.", "success")
            return redirect(url_for("admin_dashboard" if user["role"] == "admin" else "dashboard"))

        if user and user["status"] != "Active":
            flash("Your account has been deactivated by the administrator.", "danger")
        else:
            flash("Invalid username/email or password. Please try again.", "danger")

    return render_template("login.html")

@app.route("/send_otp", methods=["POST"])
def send_otp():
    """
    Generates and dispatches a 6-digit OTP to the email entered on the registration form.
    Verifies email uniqueness before sending.
    """
    email = request.form.get("email", "").strip().lower()
    if not email or not is_valid_email(email):
        return jsonify(success=False, message="Please enter a valid email address first."), 400

    existing = query_one("SELECT user_id FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
    if existing:
        return jsonify(success=False, message="This email is already registered. Please sign in instead."), 409

    otp = f"{secrets.randbelow(900000) + 100000}"
    session["reg_otp"] = otp
    session["reg_email"] = email
    session["reg_otp_expiry"] = time.time() + 600  # 10 minutes
    session["reg_otp_verified"] = False

    success, msg = send_otp_email(email, otp)
    if not success:
        return jsonify(success=False, message=msg), 500

    test_otp = otp if app.config.get("TESTING") else None

    return jsonify(
        success=True,
        message=f"Verification OTP sent to {email}! Please check your email inbox.",
        test_otp=test_otp
    )

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    """Validates the 6-digit OTP code entered on the registration page."""
    email = request.form.get("email", "").strip().lower()
    otp = request.form.get("otp", "").strip()

    if not email or not otp:
        return jsonify(success=False, message="Both email and OTP code are required."), 400

    stored_otp = session.get("reg_otp")
    stored_email = session.get("reg_email")
    stored_expiry = session.get("reg_otp_expiry", 0)

    if not stored_otp or stored_email != email:
        return jsonify(success=False, message="No OTP was requested for this email. Click 'Send OTP' first."), 400

    if time.time() > stored_expiry:
        return jsonify(success=False, message="This OTP has expired. Please request a new one."), 400

    if stored_otp != otp:
        return jsonify(success=False, message="Incorrect OTP. Please check your inbox and try again."), 400

    session["reg_otp_verified"] = True
    return jsonify(success=True, message="Email verified successfully! You may now complete registration.")

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Registration page: creates customer accounts.
    Strictly verifies email format, email ownership via OTP, phone format, and uniqueness.
    """
    if request.method == "POST":
        name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        phone_raw = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        # 1. Check required fields
        if not name or not email or not phone_raw or not password:
            flash("All fields (Name, Username, Email, Phone, Password) are mandatory.", "danger")
            return render_template("register.html")

        # 2. Email format validation
        if not is_valid_email(email):
            flash("Please enter a valid email address (e.g. name@domain.com).", "danger")
            return render_template("register.html")

        # 2b. Strict Email OTP Verification check
        otp_input = request.form.get("otp", "").strip()
        is_verified = (session.get("reg_otp_verified") is True and session.get("reg_email") == email)
        if not is_verified:
            stored_otp = session.get("reg_otp")
            stored_email = session.get("reg_email")
            stored_expiry = session.get("reg_otp_expiry", 0)
            if stored_otp and stored_otp == otp_input and stored_email == email and time.time() <= stored_expiry:
                is_verified = True
                session["reg_otp_verified"] = True
            else:
                flash("Please verify your email address using the OTP code sent to your email.", "danger")
                return render_template("register.html")

        # 3. Phone format validation
        is_phone_ok, formatted_phone = clean_and_validate_phone(phone_raw)
        if not is_phone_ok:
            flash("Please enter a valid 10-digit mobile number (e.g. 9876543210).", "danger")
            return render_template("register.html")

        # 4. Password validation
        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
            return render_template("register.html")

        if not username:
            username = email.split("@")[0]

        # 5. Uniqueness validation in MySQL
        existing_user = query_one("""
            SELECT username, email, phone FROM users 
            WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s) OR phone = %s
        """, (username, email, formatted_phone))

        if existing_user:
            if existing_user["username"].lower() == username:
                flash(f"The username '{username}' is already in use. Please select a different one.", "danger")
            elif existing_user["email"].lower() == email:
                flash(f"The email '{email}' is already registered. Please sign in or use another email.", "danger")
            elif existing_user["phone"] == formatted_phone:
                flash(f"The mobile number '{phone_raw}' is already registered with another account.", "danger")
            return render_template("register.html")

        try:
            execute("""
                INSERT INTO users (username, full_name, email, phone, password_hash, role, status)
                VALUES (%s, %s, %s, %s, %s, 'customer', 'Active')
            """, (username, name, email, formatted_phone, generate_password_hash(password)))

            # Clear registration OTP session data
            session.pop("reg_otp", None)
            session.pop("reg_email", None)
            session.pop("reg_otp_expiry", None)
            session.pop("reg_otp_verified", None)

            flash("Registration successful! Your email and phone have been verified. Please sign in.", "success")
            return redirect(url_for("login"))
        except Error as e:
            flash(f"Account registration error: {str(e)}", "danger")

    return render_template("register.html")

@app.route("/logout")
def logout():
    """Clear session and log out."""
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))

@app.route("/rooms")
def rooms():
    """
    Room discovery & search.
    Keeps room inventory synchronized in real-time, displays live availability status
    (Available vs Booked), and filters rooms with no overlapping reservations for selected dates.
    """
    sync_room_status()

    room_type = request.args.get("room_type", "").strip()
    check_in = request.args.get("check_in", "")
    check_in_time = request.args.get("check_in_time", "12:00 PM")
    check_out = request.args.get("check_out", "")
    check_out_time = request.args.get("check_out_time", "11:00 AM")
    guests = request.args.get("guests", "1")
    sort = request.args.get("sort", "price_asc")
    status_filter = request.args.get("status_filter", "")

    params = []
    sql = "SELECT * FROM rooms r WHERE r.status != 'Inactive'"

    if status_filter == "available":
        sql += " AND r.status = 'Available'"

    if room_type:
        sql += " AND r.room_type = %s"
        params.append(room_type)

    if guests.isdigit() and int(guests) > 0:
        sql += " AND r.capacity >= %s"
        params.append(int(guests))

    if check_in and check_out:
        try:
            start = date.fromisoformat(check_in)
            end = date.fromisoformat(check_out)
            if end <= start:
                flash("Check-out date must be strictly after check-in date.", "warning")
            elif start < date.today():
                flash("Check-in date cannot be in the past.", "warning")
            else:
                # Correlated subquery with NOT EXISTS (Key DBMS Requirement)
                sql += """ AND NOT EXISTS (
                    SELECT 1 FROM bookings b 
                    WHERE b.room_id = r.room_id
                      AND b.booking_status IN ('Confirmed', 'Checked In')
                      AND b.check_in < %s AND b.check_out > %s
                )"""
                params.extend([end, start])
        except ValueError:
            flash("Please enter valid dates in YYYY-MM-DD format.", "warning")

    if sort == "price_desc":
        sql += " ORDER BY r.price_per_night DESC"
    elif sort == "capacity_desc":
        sql += " ORDER BY r.capacity DESC"
    else:
        sql += " ORDER BY r.price_per_night ASC"

    room_list = query_all(sql, tuple(params))
    return render_template(
        "rooms.html", 
        rooms=room_list, 
        room_type=room_type,
        check_in=check_in,
        check_in_time=check_in_time,
        check_out=check_out, 
        check_out_time=check_out_time,
        guests=guests,
        sort=sort,
        status_filter=status_filter,
        today=date.today()
    )

# ====================================================================
# CHECKOUT & 25% ADVANCE PAYMENT WORKFLOW
# ====================================================================

@app.route("/checkout/<int:room_id>", methods=["GET", "POST"])
@role_required("customer")
def checkout(room_id):
    """
    Checkout page for room booking.
    Calculates stay rate and 25% advance amount, generates a dynamic QR code
    containing the local Wi-Fi payment URL for phone scanning and dummy payment.
    """
    sync_room_status(room_id)
    check_in = request.args.get("check_in") or request.form.get("check_in", "")
    check_in_time = request.args.get("check_in_time") or request.form.get("check_in_time", "12:00 PM")
    check_out = request.args.get("check_out") or request.form.get("check_out", "")
    check_out_time = request.args.get("check_out_time") or request.form.get("check_out_time", "11:00 AM")
    guests = request.args.get("guests") or request.form.get("guests", "1")

    room = query_one("SELECT * FROM rooms WHERE room_id = %s", (room_id,))
    if not room or room["status"] in ("Maintenance", "Inactive"):
        flash("The selected room is currently unavailable.", "danger")
        return redirect(url_for("rooms"))

    try:
        start = date.fromisoformat(check_in)
        end = date.fromisoformat(check_out)
        guests_num = int(guests)
        if start < date.today() or end <= start or guests_num < 1:
            raise ValueError
    except (ValueError, TypeError):
        flash("Please choose valid future dates and guest count before proceeding to checkout.", "warning")
        return redirect(url_for("rooms", check_in=check_in, check_in_time=check_in_time, check_out=check_out, check_out_time=check_out_time, guests=guests))

    if guests_num > room["capacity"]:
        flash(f"Room capacity exceeded. This room accommodates up to {room['capacity']} guests.", "danger")
        return redirect(url_for("rooms"))

    # Overlapping conflict check: Ensure room is NOT already booked for these dates
    conflict = query_one("""
        SELECT COUNT(*) AS conflict_count FROM bookings
        WHERE room_id = %s AND booking_status IN ('Confirmed', 'Checked In')
          AND check_in < %s AND check_out > %s
    """, (room_id, end, start))
    if conflict and conflict["conflict_count"] > 0:
        flash(f"Room {room['room_number']} has already been booked by another guest for these dates. Please choose another room or different dates.", "danger")
        return redirect(url_for("rooms"))

    nights = (end - start).days
    total_amount = room["price_per_night"] * nights
    # Calculate 25% advance and 75% balance
    advance_amount = round(total_amount * Decimal("0.25"), 2)
    balance_amount = total_amount - advance_amount

    # Reuse existing active pending order or create a new one
    existing_pay = query_one("""
        SELECT * FROM payments 
        WHERE user_id = %s AND room_id = %s AND check_in = %s AND check_out = %s 
          AND check_in_time = %s AND check_out_time = %s
          AND amount = %s AND status = 'Created'
        ORDER BY pay_id DESC LIMIT 1
    """, (session["user_id"], room_id, start, end, check_in_time, check_out_time, advance_amount))

    if existing_pay:
        order_id = existing_pay["gateway_order_id"]
    else:
        order_id = f"ORD-QR-r{room_id}-u{session['user_id']}-{int(datetime.now().timestamp())}-{secrets.token_hex(2).upper()}"
        execute("""
            INSERT INTO payments (user_id, room_id, check_in, check_in_time, check_out, check_out_time, guest_count,
                                  total_amount, amount, gateway_order_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Created')
        """, (session["user_id"], room_id, start, check_in_time, end, check_out_time, guests_num, total_amount, advance_amount, order_id))

    # Detect local network IP so phone on the same Wi-Fi can open payment request
    server_ip = get_local_ip()
    host_header = request.host
    port = host_header.split(":")[1] if ":" in host_header else "5000"
    payment_url = f"http://{server_ip}:{port}/pay/{order_id}"
    qr_code_base64 = generate_qr_base64(payment_url)

    return render_template(
        "checkout.html",
        room=room,
        check_in=check_in,
        check_in_time=check_in_time,
        check_out=check_out,
        check_out_time=check_out_time,
        guests=guests_num,
        nights=nights,
        total_amount=total_amount,
        advance_amount=advance_amount,
        balance_amount=balance_amount,
        order_id=order_id,
        payment_url=payment_url,
        qr_code_base64=qr_code_base64,
        server_ip=server_ip
    )

# ====================================================================
# DYNAMIC QR CODE DUMMY PAYMENT SYSTEM (SAME WI-FI)
# ====================================================================

@app.route("/pay/<order_id>")
def pay_mobile(order_id):
    """
    Mobile payment request screen opened when scanning the QR code from a phone.
    Accessible on the local network (same Wi-Fi).
    """
    pay = query_one("""
        SELECT p.*, r.room_number, r.room_type, r.capacity, r.price_per_night, r.image_url, r.amenities,
               u.full_name AS guest_name, u.email AS guest_email, u.phone AS guest_phone
        FROM payments p
        JOIN rooms r ON p.room_id = r.room_id
        JOIN users u ON p.user_id = u.user_id
        WHERE p.gateway_order_id = %s
    """, (order_id,))

    if not pay:
        return render_template("error.html", code=404, message="Payment request not found or expired."), 404

    nights = (pay["check_out"] - pay["check_in"]).days
    balance_amount = pay["total_amount"] - pay["amount"]

    return render_template(
        "pay_mobile.html",
        pay=pay,
        nights=nights,
        balance_amount=balance_amount,
        already_paid=(pay["status"] == "Paid")
    )


@app.route("/process_dummy_payment/<order_id>", methods=["POST"])
def process_dummy_payment(order_id):
    """
    Processes the dummy payment submitted from the mobile phone payment sheet.
    Re-verifies room availability, updates payments table to Paid, and creates confirmed booking.
    """
    action = request.form.get("action", "approve")
    method = request.form.get("method", "UPI / QR")
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json

    if action == "decline":
        execute("UPDATE payments SET status = 'Failed' WHERE gateway_order_id = %s AND status = 'Created'", (order_id,))
        if is_ajax:
            return jsonify(success=False, status="Failed", message="Payment request was declined.")
        flash("Payment request was cancelled.", "info")
        return redirect(url_for("pay_mobile", order_id=order_id))

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cur.execute("SELECT * FROM payments WHERE gateway_order_id = %s FOR UPDATE", (order_id,))
        pay = cur.fetchone()

        if not pay:
            conn.rollback()
            return jsonify(success=False, message="Payment order not found."), 404

        if pay["status"] == "Paid":
            conn.rollback()
            if is_ajax:
                return jsonify(
                    success=True,
                    status="Paid",
                    booking_id=pay["booking_id"],
                    tx_ref=pay["gateway_payment_id"],
                    amount=float(pay["amount"]),
                    method=pay["method"]
                )
            return redirect(url_for("pay_mobile", order_id=order_id))

        if pay["status"] == "Failed":
            cur.execute("UPDATE payments SET status = 'Created' WHERE pay_id = %s", (pay["pay_id"],))

        # Check room availability
        cur.execute("SELECT * FROM rooms WHERE room_id = %s FOR UPDATE", (pay["room_id"],))
        room = cur.fetchone()
        cur.execute("""
            SELECT COUNT(*) AS c FROM bookings
            WHERE room_id = %s AND booking_status IN ('Confirmed', 'Checked In')
              AND check_in < %s AND check_out > %s
        """, (pay["room_id"], pay["check_out"], pay["check_in"]))
        clash = cur.fetchone()["c"] > 0

        if not room or room["status"] in ("Maintenance", "Inactive") or clash:
            cur.execute("UPDATE payments SET status = 'Failed' WHERE pay_id = %s", (pay["pay_id"],))
            conn.commit()
            return jsonify(success=False, message="Room is no longer available for these dates."), 409

        # Generate dummy transaction ID
        tx_ref = f"PAY-QR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        balance = pay["total_amount"] - pay["amount"]
        payment_mode = METHOD_TO_MODE.get(method, "UPI / QR")
        cin_time = pay.get("check_in_time") or "12:00 PM"
        cout_time = pay.get("check_out_time") or "11:00 AM"

        # Create confirmed reservation in bookings
        cur.execute("""
            INSERT INTO bookings (user_id, room_id, check_in, check_in_time, check_out, check_out_time, guest_count,
                total_amount, advance_paid, balance_amount, payment_mode, payment_status, booking_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Advance Paid', 'Confirmed')
        """, (pay["user_id"], pay["room_id"], pay["check_in"], cin_time, pay["check_out"], cout_time,
              pay["guest_count"], pay["total_amount"], pay["amount"], balance, payment_mode))
        booking_id = cur.lastrowid

        # Update payment record with booking_id and Paid status
        cur.execute("""
            UPDATE payments 
            SET status = 'Paid', gateway_payment_id = %s, method = %s, booking_id = %s
            WHERE pay_id = %s
        """, (tx_ref, payment_mode, booking_id, pay["pay_id"]))

        # Mark room status as 'Booked' immediately
        cur.execute("UPDATE rooms SET status = 'Booked' WHERE room_id = %s", (pay["room_id"],))

        conn.commit()

        if is_ajax:
            return jsonify(
                success=True,
                status="Paid",
                booking_id=booking_id,
                tx_ref=tx_ref,
                amount=float(pay["amount"]),
                method=payment_mode
            )

        flash(f"Payment successful! Booking #{booking_id} confirmed.", "success")
        return redirect(url_for("pay_mobile", order_id=order_id))

    except Exception:
        conn.rollback()
        app.logger.exception("process_dummy_payment failed for order %s", order_id)
        return jsonify(success=False, message="Internal server error processing payment."), 500
    finally:
        cur.close()
        conn.close()


@app.route("/api/payment_status/<order_id>")
def payment_status(order_id):
    """
    Polling endpoint used by desktop checkout to automatically detect
    when payment is confirmed from the user's phone on Wi-Fi.
    """
    pay = query_one("""
        SELECT status, booking_id, gateway_payment_id, amount 
        FROM payments 
        WHERE gateway_order_id = %s
    """, (order_id,))

    if not pay:
        return jsonify(status="NotFound"), 404

    # If completed, set flash message in session for when the desktop redirects to dashboard
    if pay["status"] == "Paid" and session.get("user_id"):
        flash(f"🎉 Booking #{pay['booking_id']} confirmed! Your 25% advance payment was received via QR Code. The remaining balance is payable at check-in.", "success")

    return jsonify(
        status=pay["status"],
        booking_id=pay["booking_id"],
        payment_id=pay["gateway_payment_id"],
        amount=float(pay["amount"])
    )


def refund_booking_payment(booking_id):
    """Refund the online advance of a cancelled booking (offline dummy gateway)."""
    pay = query_one("SELECT * FROM payments WHERE booking_id = %s AND status = 'Paid'", (booking_id,))
    if not pay:
        return "none"
    try:
        execute("UPDATE payments SET status = 'Refunded' WHERE pay_id = %s", (pay["pay_id"],))
        return "refunded"
    except Exception:
        app.logger.exception("Refund failed for booking %s", booking_id)
        return "failed"


@app.route("/book/<int:room_id>", methods=["POST"])
@role_required("customer")
def book_room(room_id):
    """Redirects the customer from the room listing directly to the checkout screen."""
    check_in = request.form.get("check_in", "")
    check_in_time = request.form.get("check_in_time", "12:00 PM")
    check_out = request.form.get("check_out", "")
    check_out_time = request.form.get("check_out_time", "11:00 AM")
    guests = request.form.get("guests", "1")
    return redirect(url_for(
        "checkout",
        room_id=room_id,
        check_in=check_in,
        check_in_time=check_in_time,
        check_out=check_out,
        check_out_time=check_out_time,
        guests=guests
    ))

# ====================================================================
# CUSTOMER DASHBOARD & CANCELLATION
# ====================================================================

@app.route("/dashboard")
@role_required("customer")
def dashboard():
    """
    Customer Dashboard: reservations overview, advance payment tracking,
    and admin cancellation reason notice.
    """
    sync_room_status()
    user_id = session["user_id"]
    
    bookings = query_all("""
        SELECT 
          b.booking_id, 
          b.room_id, 
          b.check_in, 
          b.check_in_time,
          b.check_out, 
          b.check_out_time,
          DATEDIFF(b.check_out, b.check_in) AS total_nights,
          b.guest_count, 
          b.total_amount, 
          b.advance_paid,
          b.balance_amount,
          b.payment_mode,
          b.payment_status,
          b.booking_status, 
          b.cancelled_by,
          b.cancellation_reason,
          b.created_at,
          r.room_number, 
          r.room_type, 
          r.price_per_night, 
          r.amenities,
          r.image_url
        FROM bookings b 
        JOIN rooms r ON r.room_id = b.room_id
        WHERE b.user_id = %s 
        ORDER BY b.created_at DESC
    """, (user_id,))

    stats = query_one("""
        SELECT 
          COUNT(*) AS total_bookings,
          SUM(booking_status = 'Confirmed') AS confirmed_bookings,
          SUM(booking_status = 'Checked In') AS active_stays,
          COALESCE(SUM(CASE WHEN booking_status = 'Checked Out' THEN total_amount
                  WHEN booking_status IN ('Confirmed', 'Checked In') THEN advance_paid
                  ELSE 0 END), 0) AS total_spent,
          COALESCE(SUM(advance_paid), 0) AS total_advance_paid
        FROM bookings
        WHERE user_id = %s
    """, (user_id,))

    rooms = query_all("SELECT * FROM rooms WHERE status='Available' ORDER BY price_per_night ASC")

    return render_template("dashboard.html", bookings=bookings, stats=stats, rooms=rooms, today=date.today())

@app.route("/cancel/<int:booking_id>", methods=["POST"])
@role_required("customer")
def cancel_booking(booking_id):
    """
    Cancel an upcoming confirmed booking by the guest.
    Fires trigger trg_booking_status_audit and syncs room availability.
    """
    b_info = query_one("SELECT room_id FROM bookings WHERE booking_id = %s AND user_id = %s", (booking_id, session["user_id"]))
    reason = "Cancelled by Guest due to change of personal travel plans."
    changed = execute("""
        UPDATE bookings 
        SET booking_status = 'Cancelled', cancelled_by = 'customer', 
            cancellation_reason = %s, payment_status = 'Refunded'
        WHERE booking_id = %s 
          AND user_id = %s 
          AND booking_status = 'Confirmed' 
          AND check_in >= CURDATE()
    """, (reason, booking_id, session["user_id"]))

    if changed:
        if b_info:
            sync_room_status(b_info["room_id"])
        outcome = refund_booking_payment(booking_id)
        if outcome == "failed":
            flash(f"Booking #{booking_id} is cancelled, but the automatic refund failed. The hotel will refund you manually.", "warning")
        elif outcome == "none":
            flash(f"Booking #{booking_id} has been cancelled. No online payment was found for it, so the hotel will settle any advance with you directly.", "info")
        else:
            flash(f"Booking #{booking_id} has been cancelled. Your advance refund has been initiated and takes a few working days to reach you.", "info")
    else:
        flash("This booking cannot be cancelled (it may already be past or active).", "warning")

    return redirect(url_for("dashboard"))

# ====================================================================
# ADMINISTRATOR ROUTES
# ====================================================================

@app.route("/admin")
@role_required("admin")
def admin_dashboard():
    """Admin Dashboard: overarching KPIs, analytics, and recent reservations."""
    sync_room_status()
    stats = query_one("""
        SELECT 
          (SELECT COUNT(*) FROM rooms) AS total_rooms,
          (SELECT COUNT(*) FROM rooms WHERE status='Available') AS available_rooms,
          (SELECT COUNT(*) FROM rooms WHERE status IN ('Booked', 'Occupied')) AS booked_rooms,
          (SELECT COUNT(*) FROM bookings WHERE booking_status='Confirmed') AS confirmed_bookings,
          (SELECT COUNT(*) FROM users WHERE role='customer') AS total_customers,
          (SELECT COALESCE(SUM(CASE WHEN booking_status = 'Checked Out' THEN total_amount
                          WHEN booking_status IN ('Confirmed', 'Checked In') THEN advance_paid
                          ELSE 0 END), 0) FROM bookings) AS revenue,
          (SELECT COALESCE(SUM(advance_paid), 0) FROM bookings 
           WHERE booking_status IN ('Confirmed', 'Checked In', 'Checked Out')) AS advance_revenue
    """)

    recent = query_all("""
        SELECT 
          b.booking_id, 
          u.full_name, 
          u.email,
          r.room_number, 
          r.room_type, 
          r.image_url,
          b.check_in, 
          b.check_in_time,
          b.check_out, 
          b.check_out_time,
          DATEDIFF(b.check_out, b.check_in) AS total_nights,
          b.total_amount, 
          b.advance_paid,
          b.balance_amount,
          b.payment_mode,
          b.booking_status,
          b.cancelled_by,
          b.cancellation_reason,
          b.created_at
        FROM bookings b 
        JOIN users u ON b.user_id = u.user_id
        JOIN rooms r ON b.room_id = r.room_id 
        ORDER BY b.created_at DESC 
        LIMIT 10
    """)
    return render_template("admin_dashboard.html", stats=stats, bookings=recent)

@app.route("/admin/rooms", methods=["GET", "POST"])
@role_required("admin")
def admin_rooms():
    """Admin: Room inventory management (Add, Edit, Delete, Filter)."""
    sync_room_status()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            try:
                execute("""
                    INSERT INTO rooms (room_number, room_type, capacity, price_per_night, amenities, image_url, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    request.form["room_number"].strip(),
                    request.form["room_type"],
                    int(request.form["capacity"]),
                    Decimal(request.form["price_per_night"]),
                    request.form.get("amenities", "").strip(),
                    request.form.get("image_url", "").strip() or "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80",
                    request.form["status"]
                ))
                flash("Room successfully added to inventory.", "success")
            except (Error, ValueError, KeyError):
                flash("Could not add room: Room number must be unique and valid.", "danger")

        elif action == "update":
            try:
                execute("""
                    UPDATE rooms 
                    SET room_type = %s, capacity = %s, price_per_night = %s, amenities = %s, image_url = %s, status = %s 
                    WHERE room_id = %s
                """, (
                    request.form["room_type"],
                    int(request.form["capacity"]),
                    Decimal(request.form["price_per_night"]),
                    request.form.get("amenities", "").strip(),
                    request.form.get("image_url", "").strip(),
                    request.form["status"],
                    int(request.form["room_id"])
                ))
                flash("Room details updated successfully.", "success")
            except (Error, ValueError, KeyError):
                flash("Could not update room.", "danger")

        elif action == "delete":
            try:
                execute("DELETE FROM rooms WHERE room_id = %s", (int(request.form["room_id"]),))
                flash("Room deleted from inventory.", "success")
            except Error:
                flash("Room cannot be deleted because reservations reference it (Foreign Key Restrict). Change status to 'Inactive' instead.", "warning")

        return redirect(url_for("admin_rooms"))

    room_list = query_all("SELECT * FROM rooms ORDER BY room_number ASC")
    return render_template("admin_rooms.html", rooms=room_list)

@app.route("/admin/bookings", methods=["GET", "POST"])
@role_required("admin")
def admin_bookings():
    """
    Admin: Booking management.
    Status change to 'Cancelled' logs the unavoidable admin operational reason.
    """
    if request.method == "POST":
        try:
            booking_id = int(request.form["booking_id"])
            new_status = request.form["booking_status"]
            cancellation_reason = request.form.get("cancellation_reason", "").strip()
            booking = query_one("SELECT room_id FROM bookings WHERE booking_id = %s", (booking_id,))

            if new_status == "Cancelled":
                if not cancellation_reason:
                    cancellation_reason = "Cancelled by Hotel Administration due to unavoidable operational/maintenance reasons."
                execute("""
                    UPDATE bookings 
                    SET booking_status = %s, cancelled_by = 'admin', 
                        cancellation_reason = %s, payment_status = 'Refunded'
                    WHERE booking_id = %s
                """, (new_status, cancellation_reason, booking_id))
                flash(f"Booking #{booking_id} cancelled by Admin. Reason: '{cancellation_reason}'. Advance refund initiated.", "warning")
            elif new_status == "Checked Out":
                execute("""
                    UPDATE bookings 
                    SET booking_status = %s, payment_status = 'Fully Paid', balance_amount = 0.00 
                    WHERE booking_id = %s
                """, (new_status, booking_id))
                flash(f"Booking #{booking_id} marked Checked Out. Final balance settled.", "success")
            else:
                execute("UPDATE bookings SET booking_status = %s WHERE booking_id = %s", (new_status, booking_id))
                flash(f"Booking #{booking_id} status updated to '{new_status}'.", "success")

            if booking:
                sync_room_status(booking["room_id"])
        except (Error, ValueError, KeyError) as e:
            flash(f"Could not update booking: {str(e)}", "danger")
        return redirect(url_for("admin_bookings"))

    status_filter = request.args.get("status", "")
    params = []
    sql = """
        SELECT 
          b.*, 
          u.full_name, 
          u.email, 
          u.phone,
          r.room_number, 
          r.room_type,
          r.image_url,
          DATEDIFF(b.check_out, b.check_in) AS total_nights
        FROM bookings b 
        JOIN users u ON b.user_id = u.user_id 
        JOIN rooms r ON b.room_id = r.room_id
    """
    if status_filter:
        sql += " WHERE b.booking_status = %s"
        params.append(status_filter)
    sql += " ORDER BY b.created_at DESC"

    booking_list = query_all(sql, tuple(params))
    return render_template("admin_bookings.html", bookings=booking_list, status_filter=status_filter)

@app.route("/admin/users")
@role_required("admin")
def admin_users():
    """Admin: Registered customer and admin accounts."""
    users = query_all("""
        SELECT 
          u.user_id, 
          u.username, 
          u.full_name, 
          u.email, 
          u.phone, 
          u.role, 
          u.status, 
          u.created_at,
          COUNT(b.booking_id) AS total_reservations
        FROM users u
        LEFT JOIN bookings b ON u.user_id = b.user_id
        GROUP BY u.user_id
        ORDER BY u.created_at DESC
    """)
    return render_template("admin_users.html", users=users)

@app.route("/admin/users/<int:user_id>/status", methods=["POST"])
@role_required("admin")
def admin_user_status(user_id):
    """Admin: Activate or Deactivate customer accounts."""
    status = request.form.get("status")
    if status not in ("Active", "Inactive"):
        abort(400)
    execute("UPDATE users SET status = %s WHERE user_id = %s AND role = 'customer'", (status, user_id))
    flash("Customer account access status updated.", "success")
    return redirect(url_for("admin_users"))

@app.route("/admin/reports", methods=["GET", "POST"])
@role_required("admin")
def admin_reports():
    """
    Admin: Business Reports and Stored Procedure Execution.
    """
    monthly = query_all("SELECT * FROM vw_monthly_booking_summary ORDER BY booking_month DESC LIMIT 12")

    room_types = query_all("""
        SELECT
          r.room_type,
          COUNT(b.booking_id) AS bookings,
          COALESCE(SUM(CASE WHEN b.booking_status = 'Checked Out' THEN b.total_amount
                            WHEN b.booking_status IN ('Confirmed', 'Checked In') THEN b.advance_paid
                            ELSE 0 END), 0) AS revenue,
          (SELECT ROUND(AVG(r2.price_per_night), 2)
             FROM rooms r2 WHERE r2.room_type = r.room_type) AS avg_rate
        FROM rooms r
        LEFT JOIN bookings b ON r.room_id = b.room_id
        GROUP BY r.room_type
        ORDER BY revenue DESC
    """)

    proc_result = None
    proc_year = request.form.get("proc_year", str(date.today().year))
    proc_month = request.form.get("proc_month", str(date.today().month))

    if request.method == "POST" and "run_proc" in request.form:
        conn = get_db()
        try:
            cur = conn.cursor(dictionary=True)
            cur.callproc("sp_monthly_booking_summary", [int(proc_year), int(proc_month)])
            for res in cur.stored_results():
                proc_result = res.fetchone()
            flash(f"Executed stored procedure sp_monthly_booking_summary({proc_year}, {proc_month}) successfully.", "success")
        except Error as e:
            flash(f"Error executing procedure: {str(e)}", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template(
        "admin_reports.html", 
        monthly=monthly, 
        room_types=room_types,
        proc_result=proc_result,
        proc_year=proc_year,
        proc_month=proc_month
    )

@app.route("/admin/database", methods=["GET", "POST"])
@role_required("admin")
def admin_database():
    """
    Admin: Database & SQL Diagnostics Hub.
    Live visibility of Triggers, Cursors, Views, and Queries.
    """
    cursor_results = None

    if request.method == "POST" and request.form.get("action") == "run_cursor":
        conn = get_db()
        try:
            cur = conn.cursor(dictionary=True)
            cur.callproc("sp_process_occupancy_cursor")
            for res in cur.stored_results():
                cursor_results = res.fetchall()
            flash("Successfully executed CURSOR routine sp_process_occupancy_cursor()! Table report_room_summary recalculated row-by-row.", "success")
        except Error as e:
            flash(f"Error executing cursor procedure: {str(e)}", "danger")
        finally:
            cur.close()
            conn.close()

    if cursor_results is None:
        cursor_results = query_all("SELECT * FROM report_room_summary ORDER BY total_revenue DESC")

    audit_logs = query_all("SELECT * FROM booking_audit ORDER BY changed_at DESC LIMIT 25")
    active_reservations = query_all("SELECT * FROM vw_active_reservations ORDER BY booking_id DESC LIMIT 10")
    room_inventory = query_all("SELECT * FROM vw_room_inventory_status")

    return render_template(
        "admin_database.html",
        audit_logs=audit_logs,
        cursor_results=cursor_results,
        active_reservations=active_reservations,
        room_inventory=room_inventory
    )

# ====================================================================
# ERROR HANDLERS
# ====================================================================

@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="Access Denied: You do not have permission to view this resource."), 403

@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="Page Not Found: The requested URL was not found on this server."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message=f"Internal Server Error: {str(e)}"), 500

if __name__ == "__main__":
    try:
        sync_room_status()
    except Exception as e:
        app.logger.warning("Initial room status sync notice: %s", e)

    local_ip = get_local_ip()
    print("\n" + "=" * 65)
    print("  HAVEN HOTEL & SUITES - RESERVATION & MANAGEMENT SYSTEM")
    print(f"  Local Access  : http://127.0.0.1:5000")
    print(f"  Network / Wi-Fi Access: http://{local_ip}:5000")
    print("  (Connect phone to the same Wi-Fi network to scan payment QR)")
    print("=" * 65 + "\n")

    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)





