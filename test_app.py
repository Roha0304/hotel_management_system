import unittest
import json
from datetime import date, timedelta
from app import app, is_valid_email, clean_and_validate_phone, execute, query_one

class HotelSystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        # Clean any prior test bookings > 5005
        execute("DELETE FROM bookings WHERE booking_id > 5005")

    def tearDown(self):
        execute("DELETE FROM bookings WHERE booking_id > 5005")

    def test_01_landing_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'HAVEN HOTEL', res.data)
        self.assertIn(b'Room', res.data)
        print("[PASS] Landing page loads successfully")

    def test_02_email_and_phone_validation(self):
        # Email format
        self.assertTrue(is_valid_email("test@example.com"))
        self.assertTrue(is_valid_email("guest.user@hotel.co.in"))
        self.assertFalse(is_valid_email("invalid-email"))
        self.assertFalse(is_valid_email("user@no-domain"))

        # Phone format
        ok1, p1 = clean_and_validate_phone("9876543210")
        self.assertTrue(ok1)
        self.assertEqual(p1, "+91 98765 43210")

        ok2, p2 = clean_and_validate_phone("+91 91234-56789")
        self.assertTrue(ok2)

        ok_bad, _ = clean_and_validate_phone("12345")
        self.assertFalse(ok_bad)

        print("[PASS] Email and phone validation helpers work accurately")

    def test_03_registration_email_otp_and_validation(self):
        # Test invalid email format
        r1 = self.client.post('/register', data={
            'full_name': 'Test User',
            'username': 'test_user_invalid',
            'email': 'bad_email',
            'phone': '9876543210',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'valid email address', r1.data)

        # Test invalid phone number
        r2 = self.client.post('/register', data={
            'full_name': 'Test User',
            'username': 'test_user_invalid',
            'email': 'valid@example.com',
            'phone': '123',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'valid 10-digit mobile number', r2.data)

        # Test duplicate email rejection on /send_otp
        r_dup = self.client.post('/send_otp', data={'email': 'john@example.com'})
        self.assertEqual(r_dup.status_code, 409)

        # Test request OTP for a new email
        new_email = "newguest@havenhotel.test"
        r_otp = self.client.post('/send_otp', data={'email': new_email})
        self.assertEqual(r_otp.status_code, 200)
        data_otp = json.loads(r_otp.data)
        self.assertTrue(data_otp['success'])
        self.assertIn('test_otp', data_otp)
        otp_code = data_otp['test_otp']
        self.assertEqual(len(otp_code), 6)

        # Test verifying with invalid OTP
        r_ver_bad = self.client.post('/verify_otp', data={'email': new_email, 'otp': '000000'})
        self.assertEqual(r_ver_bad.status_code, 400)

        # Test verifying with valid OTP
        r_ver_ok = self.client.post('/verify_otp', data={'email': new_email, 'otp': otp_code})
        self.assertEqual(r_ver_ok.status_code, 200)
        data_ver = json.loads(r_ver_ok.data)
        self.assertTrue(data_ver['success'])

        print("[PASS] Registration email OTP generation and verification enforced successfully")

    def test_04_qr_code_payment_flow_and_mobile_processing(self):
        # 1. Login as customer
        self.client.post('/login', data={'email': 'john_doe', 'password': 'password123'})
        today = date.today()
        ci = (today + timedelta(days=20)).isoformat()
        co = (today + timedelta(days=22)).isoformat()

        # 2. Open checkout page
        r_chk = self.client.get(f'/checkout/101?check_in={ci}&check_out={co}&guests=2')
        self.assertEqual(r_chk.status_code, 200)
        self.assertIn(b'Advance Amount (25%)', r_chk.data)
        self.assertIn(b'Scan & Pay Advance', r_chk.data)
        self.assertIn(b'data:image/png;base64,', r_chk.data)
        self.assertNotIn(b'razorpay', r_chk.data.lower())

        # Extract order id from payments table
        pay_order = query_one("""
            SELECT gateway_order_id, amount FROM payments 
            WHERE room_id = 101 AND status = 'Created' 
            ORDER BY pay_id DESC LIMIT 1
        """)
        self.assertIsNotNone(pay_order)
        order_id = pay_order["gateway_order_id"]

        # 3. Check mobile payment request page on same Wi-Fi
        r_mobile = self.client.get(f'/pay/{order_id}')
        self.assertEqual(r_mobile.status_code, 200)
        self.assertIn(b'PAYMENT REQUEST', r_mobile.data)
        self.assertIn(b'Approve & Pay', r_mobile.data)

        # 4. Check payment status before payment
        r_stat1 = self.client.get(f'/api/payment_status/{order_id}')
        data1 = json.loads(r_stat1.data)
        self.assertEqual(data1['status'], 'Created')

        # 5. Process dummy payment from mobile phone
        r_pay = self.client.post(f'/process_dummy_payment/{order_id}', data={
            'action': 'approve',
            'method': 'UPI / QR'
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(r_pay.status_code, 200)
        data_pay = json.loads(r_pay.data)
        self.assertTrue(data_pay['success'])
        self.assertEqual(data_pay['status'], 'Paid')
        booking_id = data_pay['booking_id']

        # 6. Polling endpoint now reports Paid and confirmed booking ID
        r_stat2 = self.client.get(f'/api/payment_status/{order_id}')
        data2 = json.loads(r_stat2.data)
        self.assertEqual(data2['status'], 'Paid')
        self.assertEqual(data2['booking_id'], booking_id)

        # 7. Old razorpay webhook must be completely gone (404)
        r_hook = self.client.post('/razorpay_webhook', data='{}')
        self.assertEqual(r_hook.status_code, 404)

        print("[PASS] Dynamic QR Code generation, Wi-Fi mobile payment, and desktop polling verified successfully")

    def test_05_admin_cancellation_reason_visibility(self):
        # Login as customer John Doe who has a cancelled booking (#5003) by Admin
        self.client.get('/logout')
        res = self.client.post('/login', data={'email': 'john_doe', 'password': 'password123'}, follow_redirects=True)
        self.assertIn(b'Cancelled by Hotel Administration', res.data)
        self.assertIn(b'unavoidable operational/maintenance reasons', res.data)
        self.assertIn(b'refunded', res.data)
        print("[PASS] Admin cancellation notice and unavoidable reason visible on guest dashboard")

    def test_06_complete_registration_and_login_with_otp(self):
        execute("DELETE FROM users WHERE email = 'testguest@havenhotel.test'")
        test_email = "testguest@havenhotel.test"

        # 1. Request OTP
        r_otp = self.client.post('/send_otp', data={'email': test_email})
        self.assertEqual(r_otp.status_code, 200)
        otp = json.loads(r_otp.data)['test_otp']

        # 2. Try to register with wrong OTP -> rejected
        r_bad = self.client.post('/register', data={
            'full_name': 'Test Guest',
            'username': 'test_guest_otp',
            'email': test_email,
            'otp': '999999',
            'phone': '9876543219',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'verify your email address using the OTP code', r_bad.data)

        # 3. Register with correct OTP -> success and redirected to login
        r_ok = self.client.post('/register', data={
            'full_name': 'Test Guest',
            'username': 'test_guest_otp',
            'email': test_email,
            'otp': otp,
            'phone': '9876543219',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Registration successful', r_ok.data)

        # 4. Login with newly registered credentials
        r_login = self.client.post('/login', data={
            'email': 'test_guest_otp',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Welcome back, Test Guest', r_login.data)
        print("[PASS] Full registration cycle with OTP verification and login completed successfully")

        # Clean up test user
        execute("DELETE FROM users WHERE email = %s", (test_email,))

    def test_07_checkin_checkout_time_and_booked_room_availability(self):
        # 1. Login as customer A (john_doe, user_id=1002)
        self.client.post('/login', data={'email': 'john_doe', 'password': 'password123'})
        
        # Test /rooms displays check-in time and check-out time slots
        r_rooms = self.client.get('/rooms')
        self.assertEqual(r_rooms.status_code, 200)
        self.assertIn(b'Check-in: 08:00 AM', r_rooms.data)
        self.assertIn(b'Check-out: 11:00 AM', r_rooms.data)

        # 2. Book Room 102 (room_id=102) with 09:00 AM check-in and 12:00 PM check-out
        today = date.today()
        ci = (today + timedelta(days=10)).isoformat()
        co = (today + timedelta(days=12)).isoformat()

        # Open checkout with custom time slots
        r_chk = self.client.get(f'/checkout/102?check_in={ci}&check_in_time=09:00+AM&check_out={co}&check_out_time=12:00+PM&guests=2')
        self.assertEqual(r_chk.status_code, 200)
        self.assertIn(b'09:00 AM', r_chk.data)
        self.assertIn(b'12:00 PM', r_chk.data)

        # Extract order id from payments table
        pay = query_one("SELECT * FROM payments WHERE room_id = 102 AND status = 'Created' ORDER BY pay_id DESC LIMIT 1")
        self.assertIsNotNone(pay)
        order_id = pay['gateway_order_id']
        self.assertEqual(pay['check_in_time'], '09:00 AM')
        self.assertEqual(pay['check_out_time'], '12:00 PM')

        # Approve payment
        r_pay = self.client.post(
            f'/process_dummy_payment/{order_id}',
            data={'action': 'approve', 'method': 'UPI / QR'},
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(r_pay.status_code, 200)
        pay_json = json.loads(r_pay.data)
        self.assertTrue(pay_json['success'])
        booking_id = pay_json['booking_id']

        # Verify Room 102 status is now 'Booked'
        r_room102 = query_one("SELECT status FROM rooms WHERE room_id = 102")
        self.assertEqual(r_room102['status'], 'Booked')

        # 3. User B browses rooms: Room 102 is marked Booked and booking form is disabled
        self.client.get('/logout')
        r_rooms_b = self.client.get('/rooms')
        self.assertEqual(r_rooms_b.status_code, 200)
        self.assertIn(b'Room 102 is Currently Booked', r_rooms_b.data)

        # 4. In Admin Dashboard, Room 102 shows 'Booked'
        self.client.post('/login', data={'email': 'admin', 'password': 'admin123'})
        r_admin = self.client.get('/admin')
        self.assertEqual(r_admin.status_code, 200)
        self.assertIn(b'Booked', r_admin.data)

        # In Admin Rooms, Room 102 has the 'Booked' badge
        r_admin_rooms = self.client.get('/admin/rooms')
        self.assertEqual(r_admin_rooms.status_code, 200)
        self.assertIn(b'<span class="badge bg-danger"><i class="fa-solid fa-lock me-1"></i> Booked</span>', r_admin_rooms.data)

        # 5. Clean up test booking and verify room reverts to Available
        execute("DELETE FROM bookings WHERE booking_id = %s", (booking_id,))
        from app import sync_room_status
        sync_room_status(102)
        r_after = query_one("SELECT status FROM rooms WHERE room_id = 102")
        self.assertEqual(r_after['status'], 'Available')
        print("[PASS] Check-in/out time slot selection and room availability sync verified successfully")

if __name__ == '__main__':
    unittest.main()
