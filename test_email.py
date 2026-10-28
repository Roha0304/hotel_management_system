import os
import sys
from dotenv import load_dotenv

load_dotenv()

from app import send_otp_email

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_email = sys.argv[1].strip()
    else:
        target_email = input("Enter email address to send test OTP to: ").strip()

    if not target_email:
        print("Error: No email address provided.")
        sys.exit(1)

    print(f"\nAttempting to send test OTP to: {target_email}...")
    success, msg = send_otp_email(target_email, "123456")

    if success:
        print(f"\n[SUCCESS] {msg}")
        print("Please check your email inbox (and spam folder just in case)!")
    else:
        print(f"\n[FAILED] {msg}")
        print("\nPlease check your credentials in .env file.")
