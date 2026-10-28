"""
Cloud Database Setup Script for Hotel Management System
Usage:
    python setup_cloud_db.py

This script reads database connection credentials from environment variables:
    MYSQLHOST / DB_HOST
    MYSQLUSER / DB_USER
    MYSQLPASSWORD / DB_PASSWORD
    MYSQLDATABASE / DB_NAME
    MYSQLPORT / DB_PORT
    (or MYSQL_URL / DATABASE_URL)
and initializes the database tables, views, triggers, sample rooms, and admin user.
"""
import os
import re
from urllib.parse import urlparse
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_db_config():
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

    ssl_mode = os.environ.get("DB_SSL", "").lower()
    if ssl_mode in ("true", "1", "yes", "require"):
        cfg["ssl_disabled"] = False
    return cfg

def split_sql_statements(sql_text):
    """Parses SQL text into individual statements, properly handling DELIMITER blocks."""
    statements = []
    current_delimiter = ';'
    current_stmt = []
    
    lines = sql_text.splitlines()
    for line in lines:
        stripped = line.strip()
        
        # Check for DELIMITER change
        if stripped.upper().startswith('DELIMITER '):
            current_delimiter = stripped.split()[1]
            continue
            
        # Skip pure comments outside statements
        if not current_stmt and (stripped.startswith('--') or stripped.startswith('/*') or not stripped):
            continue
            
        current_stmt.append(line)
        
        # Check if line ends with delimiter
        if stripped.endswith(current_delimiter):
            stmt_text = '\n'.join(current_stmt)
            # Remove trailing delimiter
            if current_delimiter != ';':
                stmt_text = stmt_text[:-(len(current_delimiter))].strip()
            else:
                stmt_text = stmt_text[:-1].strip()
                
            if stmt_text:
                statements.append(stmt_text)
            current_stmt = []
            
    if current_stmt:
        remaining = '\n'.join(current_stmt).strip()
        if remaining:
            statements.append(remaining)
            
    return statements

def run_setup():
    cfg = get_db_config()
    print("=" * 60)
    print("  HOTEL MANAGEMENT SYSTEM - CLOUD DATABASE INITIALIZER")
    print(f"  Target Host    : {cfg['host']}")
    print(f"  Target User    : {cfg['user']}")
    print(f"  Target Database: {cfg['database']}")
    print(f"  Target Port    : {cfg['port']}")
    print("=" * 60)

    schema_file = os.path.join(os.path.dirname(__file__), "schema.sql")
    if not os.path.exists(schema_file):
        print(f"❌ Error: {schema_file} not found!")
        return

    with open(schema_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    statements = split_sql_statements(sql_content)
    print(f"Loaded {len(statements)} SQL commands from schema.sql")

    try:
        conn = mysql.connector.connect(**cfg)
        cur = conn.cursor()
        print("Connected successfully to MySQL!")
        
        executed = 0
        skipped = 0
        for i, stmt in enumerate(statements, 1):
            stmt_clean = stmt.strip()
            # If target database is predefined in cloud (e.g. 'railway'), skip DROP/CREATE DATABASE
            if re.match(r"^DROP\s+DATABASE", stmt_clean, re.IGNORECASE) or \
               re.match(r"^CREATE\s+DATABASE", stmt_clean, re.IGNORECASE) or \
               re.match(r"^USE\s+", stmt_clean, re.IGNORECASE):
                skipped += 1
                continue
                
            try:
                cur.execute(stmt_clean)
                executed += 1
            except Exception as stmt_err:
                # Triggers/procedures might fail if privileges are restricted on certain free clouds
                print(f"⚠️ Statement {i} notice: {stmt_err} (Continuing...)")
        
        conn.commit()
        cur.close()
        conn.close()
        print("\n" + "=" * 60)
        print(f"✅ Setup Completed! Executed {executed} statements ({skipped} database-level statements skipped).")
        print("   Database is now ready with tables, rooms, views, and procedures!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        print("\nPlease verify your connection credentials in .env or environment variables.")

if __name__ == "__main__":
    run_setup()
