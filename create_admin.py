"""Create an administrator account. Run: python create_admin.py"""
import getpass
import os
import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

cfg = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "1234567890"),
    "database": os.getenv("DB_NAME", "hotel_management"),
    "port": int(os.getenv("DB_PORT", "3306")),
}

print("=== Create Hotel Management Administrator ===")
name = input("Admin full name: ").strip()
username = input("Admin username (e.g. admin_su): ").strip().lower()
email = input("Admin email: ").strip().lower()
password = getpass.getpass("Admin password (minimum 6 characters): ")

if not name or not email or len(password) < 6:
    raise SystemExit("Name/email are required and password must have at least 6 characters.")

if not username:
    username = email.split("@")[0]

try:
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (username, full_name, email, password_hash, role, status)
        VALUES (%s, %s, %s, %s, 'admin', 'Active')
    """, (username, name, email, generate_password_hash(password)))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Administrator '{name}' (@{username}) created successfully! Sign in through http://127.0.0.1:5000/login")
except Exception as e:
    print(f"Error creating administrator: {e}")
