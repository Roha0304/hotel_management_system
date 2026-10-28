-- ====================================================================
-- HOTEL ROOM RESERVATION & MANAGEMENT SYSTEM - SQL QUERY PORTFOLIO
-- Fulfills all query requirements from Academic DBMS Evaluation Sheet
-- Includes: Unique Constraints, 25% Advance Payments, Room Photos,
--           Admin Cancellation Reason Tracking, Views, Triggers,
--           Stored Procedures, and Cursors.
-- ====================================================================

USE hotel_management;

-- ====================================================================
-- 1. BASIC CRUD QUERIES
-- ====================================================================

-- 1.1 SELECT: Retrieve all available rooms with their photos & pricing
SELECT room_id, room_number, room_type, capacity, price_per_night, image_url, status
FROM rooms
WHERE status = 'Available'
ORDER BY price_per_night ASC;

-- 1.2 INSERT: Register a new customer with strictly verified and unique email and phone
INSERT INTO users (username, full_name, email, phone, password_hash, role, status)
VALUES ('ananya_roy', 'Ananya Roy', 'ananya@example.com', '+91 98765 01234', 
        'scrypt:32768:8:1$test$fakehashforquerydemo', 'customer', 'Active');

-- 1.3 UPDATE: Modify room price and maintenance status
UPDATE rooms
SET price_per_night = 2999.00, status = 'Maintenance'
WHERE room_number = '203';

-- 1.4 DELETE: Delete an inactive test user without bookings
DELETE FROM users 
WHERE username = 'ananya_roy' AND NOT EXISTS (
    SELECT 1 FROM bookings WHERE user_id = users.user_id
);

-- ====================================================================
-- 2. JOIN OPERATIONS & ADVANCE PAYMENT RECEIPTS
-- ====================================================================

-- 2.1 INNER JOIN: Combine Bookings, Users, and Rooms with 25% Advance Payment details
SELECT 
  b.booking_id,
  u.full_name AS guest_name,
  u.email,
  u.phone,
  r.room_number,
  r.room_type,
  b.check_in,
  b.check_out,
  DATEDIFF(b.check_out, b.check_in) AS total_nights,
  b.total_amount,
  b.advance_paid AS advance_paid_25_pct,
  b.balance_amount AS balance_due_75_pct,
  b.payment_mode,
  b.payment_status,
  b.booking_status
FROM bookings b
INNER JOIN users u ON b.user_id = u.user_id
INNER JOIN rooms r ON b.room_id = r.room_id
WHERE b.booking_status IN ('Confirmed', 'Checked In')
ORDER BY b.check_in ASC;

-- 2.2 LEFT OUTER JOIN: Room category inventory and financial performance
SELECT 
  r.room_type,
  COUNT(r.room_id) AS total_rooms,
  COUNT(b.booking_id) AS total_bookings_made,
  COALESCE(SUM(CASE WHEN b.booking_status IN ('Confirmed', 'Checked In', 'Checked Out') 
                    THEN b.total_amount ELSE 0 END), 0) AS recognized_revenue,
  COALESCE(SUM(CASE WHEN b.booking_status IN ('Confirmed', 'Checked In', 'Checked Out') 
                    THEN b.advance_paid ELSE 0 END), 0) AS total_advance_collected
FROM rooms r
LEFT JOIN bookings b ON r.room_id = b.room_id
GROUP BY r.room_type
ORDER BY recognized_revenue DESC;

-- ====================================================================
-- 3. NESTED QUERIES & SUBQUERIES
-- ====================================================================

-- 3.1 Correlated Subquery with NOT EXISTS (Date collision detection)
-- Finds all rooms that have NO overlapping active booking between 2026-10-20 and 2026-10-25
SELECT r.room_id, r.room_number, r.room_type, r.price_per_night, r.capacity, r.image_url
FROM rooms r
WHERE r.status = 'Available'
  AND NOT EXISTS (
    SELECT 1 FROM bookings b
    WHERE b.room_id = r.room_id
      AND b.booking_status IN ('Confirmed', 'Checked In')
      AND b.check_in < '2026-10-25'
      AND b.check_out > '2026-10-20'
  );

-- 3.2 Subquery with IN: High-value guests who have made bookings above ₹10,000
SELECT user_id, full_name, email, phone
FROM users
WHERE user_id IN (
    SELECT DISTINCT user_id 
    FROM bookings 
    WHERE total_amount >= 10000.00
);

-- 3.3 Scalar Subquery: Comparison against average nightly price
SELECT room_number, room_type, price_per_night,
       (SELECT ROUND(AVG(price_per_night), 2) FROM rooms) AS hotel_avg_rate,
       ROUND(price_per_night - (SELECT AVG(price_per_night) FROM rooms), 2) AS price_differential
FROM rooms
ORDER BY price_differential DESC;

-- ====================================================================
-- 4. AGGREGATE FUNCTIONS & GROUP BY WITH HAVING
-- ====================================================================

-- 4.1 Room Category Aggregation with HAVING clause
SELECT 
  room_type,
  COUNT(*) AS total_rooms,
  MIN(price_per_night) AS minimum_price,
  MAX(price_per_night) AS maximum_price,
  ROUND(AVG(price_per_night), 2) AS average_price
FROM rooms
GROUP BY room_type
HAVING COUNT(*) >= 2
ORDER BY average_price DESC;

-- 4.2 Booking Status & Payment Breakdown
SELECT 
  booking_status,
  COUNT(*) AS reservation_count,
  ROUND(AVG(DATEDIFF(check_out, check_in)), 1) AS avg_duration_days,
  SUM(total_amount) AS total_value,
  SUM(advance_paid) AS total_advance_collected,
  ROUND(AVG(total_amount), 2) AS avg_value_per_stay
FROM bookings
GROUP BY booking_status;

-- ====================================================================
-- 5. DATABASE VIEWS
-- ====================================================================

-- 5.1 Query the Monthly Booking & Revenue Summary View
SELECT * FROM vw_monthly_booking_summary;

-- 5.2 Query the Detailed Reservations View (Includes Advance & Cancellation reason)
SELECT booking_id, guest_name, room_type, room_number, check_in, check_out, 
       total_amount, advance_paid, balance_amount, booking_status, cancelled_by, cancellation_reason
FROM vw_active_reservations;

-- 5.3 Query the Room Inventory Status View
SELECT * FROM vw_room_inventory_status;

-- ====================================================================
-- 6. STORED PROCEDURES & ADVANCED ROUTINES
-- ====================================================================

-- 6.1 Call Monthly Booking Summary Stored Procedure
CALL sp_monthly_booking_summary(2026, 10);

-- 6.2 Call Stored Procedure with IN and OUT parameters
CALL sp_get_room_type_stats('Deluxe', @v_total, @v_avail, @v_avg, @v_bookings);
SELECT @v_total AS Total_Rooms, @v_avail AS Available_Rooms, 
       @v_avg AS Average_Price, @v_bookings AS Total_Bookings;

-- 6.3 Call CURSOR Stored Procedure (Row-by-Row calculation into report_room_summary)
CALL sp_process_occupancy_cursor();

-- Verify rows populated by Cursor:
SELECT * FROM report_room_summary ORDER BY total_revenue DESC;

-- ====================================================================
-- 7. DATABASE TRIGGERS & ADMIN CANCELLATION LOGGING
-- ====================================================================

-- 7.1 Verify Audit records generated automatically by Trigger on Insert and Update:
SELECT audit_id, booking_id, action_type, old_status, new_status, details, changed_at
FROM booking_audit
ORDER BY audit_id DESC;

-- 7.2 Admin cancels a booking with unavoidable operational reasons:
UPDATE bookings 
SET booking_status = 'Cancelled',
    cancelled_by = 'admin',
    cancellation_reason = 'Cancelled by Hotel Administration due to unavoidable operational/maintenance reasons.',
    payment_status = 'Refunded'
WHERE booking_id = 5004;

-- Check trigger output capturing the cancellation and logged reason:
SELECT * FROM booking_audit WHERE booking_id = 5004;

-- ====================================================================
-- 8. INDEXES & UNIQUE CONSTRAINTS
-- ====================================================================

-- Inspect all indexes defined on the users table (including unique phone & email):
SHOW INDEX FROM users;

-- Inspect all indexes defined on the bookings table:
SHOW INDEX FROM bookings;
