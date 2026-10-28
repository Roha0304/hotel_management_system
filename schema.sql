-- ====================================================================
-- HOTEL ROOM RESERVATION & MANAGEMENT SYSTEM - DATABASE SCHEMA
-- Target DBMS: MySQL 8.0+
-- Standard: Normalized to Third Normal Form (3NF)
-- Features: Strict Unique Constraints (Email & Phone),
--           Room Photos (image_url), 25% Advance Payment Tracking,
--           Admin Cancellation Reason Logging, Triggers,
--           Stored Procedures (IN/OUT), and Cursor Routine.
-- ====================================================================

DROP DATABASE IF EXISTS hotel_management;
CREATE DATABASE hotel_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hotel_management;

-- --------------------------------------------------------------------
-- 1. ENTITY: USERS (Customers and Administrators)
-- Sequence: AUTO_INCREMENT starting at 1001
-- Unique Constraints: email and phone MUST be strictly UNIQUE
-- --------------------------------------------------------------------
CREATE TABLE users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  full_name VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  phone VARCHAR(20) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('customer', 'admin') NOT NULL DEFAULT 'customer',
  status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_users_role_status (role, status),
  INDEX idx_users_email (email),
  INDEX idx_users_phone (phone)
) ENGINE=InnoDB AUTO_INCREMENT=1001;

-- --------------------------------------------------------------------
-- 2. ENTITY: ROOMS (Physical Room Inventory with Sample Photos)
-- Sequence: AUTO_INCREMENT starting at 101
-- --------------------------------------------------------------------
CREATE TABLE rooms (
  room_id INT AUTO_INCREMENT PRIMARY KEY,
  room_number VARCHAR(10) NOT NULL UNIQUE,
  room_type ENUM('Standard', 'Deluxe', 'Suite', 'Family', 'Executive') NOT NULL,
  capacity TINYINT UNSIGNED NOT NULL,
  price_per_night DECIMAL(10, 2) NOT NULL,
  amenities VARCHAR(500),
  image_url VARCHAR(500),
  status ENUM('Available', 'Booked', 'Occupied', 'Maintenance', 'Inactive') NOT NULL DEFAULT 'Available',
  CONSTRAINT chk_room_capacity CHECK (capacity BETWEEN 1 AND 10),
  CONSTRAINT chk_room_price CHECK (price_per_night > 0),
  INDEX idx_rooms_type_status_price (room_type, status, price_per_night)
) ENGINE=InnoDB AUTO_INCREMENT=101;

-- --------------------------------------------------------------------
-- 3. ENTITY: BOOKINGS (Reservations with 25% Advance & Admin Cancellation Reason)
-- Sequence: AUTO_INCREMENT starting at 5001
-- --------------------------------------------------------------------
CREATE TABLE bookings (
  booking_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  room_id INT NOT NULL,
  check_in DATE NOT NULL,
  check_in_time VARCHAR(20) NOT NULL DEFAULT '12:00 PM',
  check_out DATE NOT NULL,
  check_out_time VARCHAR(20) NOT NULL DEFAULT '11:00 AM',
  guest_count TINYINT UNSIGNED NOT NULL DEFAULT 1,
  total_amount DECIMAL(10, 2) NOT NULL,
  advance_paid DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  balance_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  payment_mode ENUM('Credit/Debit Card', 'UPI / QR', 'Net Banking', 'Cash at Arrival') NOT NULL DEFAULT 'Credit/Debit Card',
  payment_status ENUM('Advance Paid', 'Fully Paid', 'Pending', 'Refunded') NOT NULL DEFAULT 'Advance Paid',
  booking_status ENUM('Confirmed', 'Cancelled', 'Checked In', 'Checked Out') NOT NULL DEFAULT 'Confirmed',
  cancelled_by ENUM('customer', 'admin') NULL,
  cancellation_reason VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_booking_user FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_booking_room FOREIGN KEY (room_id) REFERENCES rooms(room_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_booking_dates CHECK (check_out > check_in),
  CONSTRAINT chk_booking_guests CHECK (guest_count > 0),
  CONSTRAINT chk_booking_total CHECK (total_amount >= 0),
  CONSTRAINT chk_booking_advance CHECK (advance_paid >= 0),
  INDEX idx_booking_room_dates_status (room_id, check_in, check_out, booking_status),
  INDEX idx_booking_user_created (user_id, created_at),
  INDEX idx_booking_status_dates (booking_status, check_in, check_out)
) ENGINE=InnoDB AUTO_INCREMENT=5001;

-- --------------------------------------------------------------------
-- 4. ENTITY: BOOKING_AUDIT (Audit Trail populated by Triggers)
-- --------------------------------------------------------------------
CREATE TABLE booking_audit (
  audit_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  booking_id INT NOT NULL,
  action_type VARCHAR(30) NOT NULL,
  old_status VARCHAR(30),
  new_status VARCHAR(30) NOT NULL,
  details VARCHAR(255),
  changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_audit_booking (booking_id, changed_at)
) ENGINE=InnoDB;

ALTER TABLE bookings
  MODIFY payment_mode ENUM('Credit/Debit Card','UPI / QR','Net Banking','Cash at Arrival','Wallet / Other')
  NOT NULL DEFAULT 'Credit/Debit Card';

CREATE TABLE IF NOT EXISTS payments (
  pay_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  room_id INT NOT NULL,
  check_in DATE NOT NULL,
  check_in_time VARCHAR(20) NOT NULL DEFAULT '12:00 PM',
  check_out DATE NOT NULL,
  check_out_time VARCHAR(20) NOT NULL DEFAULT '11:00 AM',
  guest_count TINYINT UNSIGNED NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  amount DECIMAL(10,2) NOT NULL,                 -- the 25% advance charged online
  currency CHAR(3) NOT NULL DEFAULT 'INR',
  gateway_order_id VARCHAR(64) NOT NULL UNIQUE,
  gateway_payment_id VARCHAR(64) NULL UNIQUE,
  method VARCHAR(30) NULL,
  status ENUM('Created','Paid','Failed','Refunded','Refund Pending') NOT NULL DEFAULT 'Created',
  booking_id INT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_pay_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
  CONSTRAINT fk_pay_room FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE RESTRICT,
  CONSTRAINT fk_pay_booking FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE SET NULL,
  INDEX idx_pay_booking (booking_id),
  INDEX idx_pay_user (user_id)
) ENGINE=InnoDB;

-- --------------------------------------------------------------------
-- 5. ENTITY: REPORT_ROOM_SUMMARY (Populated row-by-row via CURSOR)
-- --------------------------------------------------------------------
CREATE TABLE report_room_summary (
  summary_id INT AUTO_INCREMENT PRIMARY KEY,
  room_type VARCHAR(50) NOT NULL,
  total_rooms INT NOT NULL DEFAULT 0,
  available_rooms INT NOT NULL DEFAULT 0,
  total_bookings INT NOT NULL DEFAULT 0,
  total_revenue DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  average_rate DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ====================================================================
-- VIEWS (Pre-computed relational projections & aggregations)
-- ====================================================================

-- View 1: Monthly booking & revenue summary
CREATE OR REPLACE VIEW vw_monthly_booking_summary AS
SELECT 
  DATE_FORMAT(created_at, '%Y-%m') AS booking_month,
  COUNT(*) AS total_bookings,
  SUM(booking_status = 'Confirmed') AS confirmed_bookings,
  SUM(booking_status = 'Checked In') AS checked_in_bookings,
  SUM(booking_status = 'Checked Out') AS checked_out_bookings,
  SUM(booking_status = 'Cancelled') AS cancelled_bookings,
  COALESCE(SUM(CASE WHEN booking_status IN ('Confirmed', 'Checked In', 'Checked Out') 
                    THEN total_amount ELSE 0 END), 0) AS recognized_revenue,
  COALESCE(SUM(CASE WHEN booking_status IN ('Confirmed', 'Checked In', 'Checked Out') 
                    THEN advance_paid ELSE 0 END), 0) AS total_advance_collected
FROM bookings
GROUP BY DATE_FORMAT(created_at, '%Y-%m');

-- View 2: Detailed Reservations with User, Room & Payment Joins
CREATE OR REPLACE VIEW vw_active_reservations AS
SELECT 
  b.booking_id,
  b.user_id,
  u.full_name AS guest_name,
  u.email AS guest_email,
  u.phone AS guest_phone,
  r.room_id,
  r.room_number,
  r.room_type,
  r.price_per_night,
  r.image_url,
  b.check_in,
  b.check_out,
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
  b.created_at
FROM bookings b
JOIN users u ON b.user_id = u.user_id
JOIN rooms r ON b.room_id = r.room_id;

-- View 3: Room Inventory & Occupancy Summary
CREATE OR REPLACE VIEW vw_room_inventory_status AS
SELECT 
  r.room_type,
  COUNT(r.room_id) AS total_rooms,
  SUM(r.status = 'Available') AS available_rooms,
  SUM(r.status = 'Maintenance') AS maintenance_rooms,
  SUM(r.status = 'Inactive') AS inactive_rooms,
  MIN(r.price_per_night) AS min_price,
  MAX(r.price_per_night) AS max_price,
  ROUND(AVG(r.price_per_night), 2) AS avg_price
FROM rooms r
GROUP BY r.room_type;

-- ====================================================================
-- ADVANCED FEATURES: TRIGGERS, STORED PROCEDURES & CURSOR
-- ====================================================================

DELIMITER $$

-- --------------------------------------------------------------------
-- TRIGGER 1: trg_booking_insert_audit
-- Automatically logs new bookings to the audit trail
-- --------------------------------------------------------------------
CREATE TRIGGER trg_booking_insert_audit
AFTER INSERT ON bookings
FOR EACH ROW
BEGIN
  INSERT INTO booking_audit (booking_id, action_type, old_status, new_status, details)
  VALUES (
    NEW.booking_id, 
    'BOOKING_CREATED', 
    NULL, 
    NEW.booking_status, 
    CONCAT('Initial booking created for Room ID ', NEW.room_id, ' by User ID ', NEW.user_id, 
           ' with advance paid ₹', NEW.advance_paid)
  );
END$$

-- --------------------------------------------------------------------
-- TRIGGER 2: trg_booking_status_audit
-- Automatically audits any status update on bookings
-- --------------------------------------------------------------------
CREATE TRIGGER trg_booking_status_audit
AFTER UPDATE ON bookings
FOR EACH ROW
BEGIN
  IF OLD.booking_status <> NEW.booking_status THEN
    INSERT INTO booking_audit (booking_id, action_type, old_status, new_status, details)
    VALUES (
      NEW.booking_id,
      'STATUS_CHANGED',
      OLD.booking_status,
      NEW.booking_status,
      CASE 
        WHEN NEW.booking_status = 'Cancelled' AND NEW.cancellation_reason IS NOT NULL 
          THEN CONCAT('Status: ', OLD.booking_status, ' -> Cancelled (Reason: ', NEW.cancellation_reason, ')')
        ELSE CONCAT('Status updated from ', OLD.booking_status, ' to ', NEW.booking_status)
      END
    );
  END IF;
END$$

-- --------------------------------------------------------------------
-- STORED PROCEDURE 1: sp_monthly_booking_summary
-- Repetitive administrative task: compute summary metrics for a given year & month
-- --------------------------------------------------------------------
CREATE PROCEDURE sp_monthly_booking_summary(IN p_year INT, IN p_month INT)
BEGIN
  SELECT 
    COUNT(*) AS total_bookings,
    SUM(booking_status = 'Confirmed') AS confirmed_count,
    SUM(booking_status = 'Checked In') AS checked_in_count,
    SUM(booking_status = 'Checked Out') AS checked_out_count,
    SUM(booking_status = 'Cancelled') AS cancelled_count,
    COALESCE(SUM(CASE WHEN booking_status IN ('Confirmed', 'Checked In', 'Checked Out') 
                      THEN total_amount ELSE 0 END), 0) AS recognized_revenue,
    COALESCE(SUM(CASE WHEN booking_status IN ('Confirmed', 'Checked In', 'Checked Out') 
                      THEN advance_paid ELSE 0 END), 0) AS total_advance_collected
  FROM bookings
  WHERE YEAR(created_at) = p_year AND MONTH(created_at) = p_month;
END$$

-- --------------------------------------------------------------------
-- STORED PROCEDURE 2: sp_get_room_type_stats (With IN and OUT parameters)
-- Computes real-time room statistics for a requested room type
-- --------------------------------------------------------------------
CREATE PROCEDURE sp_get_room_type_stats(
  IN p_room_type VARCHAR(50),
  OUT p_total_rooms INT,
  OUT p_available_rooms INT,
  OUT p_avg_price DECIMAL(10,2),
  OUT p_total_bookings INT
)
BEGIN
  SELECT COUNT(*), SUM(status = 'Available'), COALESCE(AVG(price_per_night), 0)
  INTO p_total_rooms, p_available_rooms, p_avg_price
  FROM rooms
  WHERE room_type = p_room_type;

  SELECT COUNT(*)
  INTO p_total_bookings
  FROM bookings b
  JOIN rooms r ON b.room_id = r.room_id
  WHERE r.room_type = p_room_type;
END$$

-- --------------------------------------------------------------------
-- CURSOR STORED PROCEDURE: sp_process_occupancy_cursor
-- Demonstrates row-by-row processing using a MySQL CURSOR.
-- --------------------------------------------------------------------
CREATE PROCEDURE sp_process_occupancy_cursor()
BEGIN
  DECLARE v_done INT DEFAULT 0;
  DECLARE v_room_type VARCHAR(50);
  DECLARE v_total_rooms INT DEFAULT 0;
  DECLARE v_available_rooms INT DEFAULT 0;
  DECLARE v_total_bookings INT DEFAULT 0;
  DECLARE v_total_revenue DECIMAL(12,2) DEFAULT 0.00;
  DECLARE v_avg_rate DECIMAL(10,2) DEFAULT 0.00;

  DECLARE room_cursor CURSOR FOR
    SELECT DISTINCT room_type FROM rooms ORDER BY room_type;

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

  DELETE FROM report_room_summary;

  OPEN room_cursor;

  cursor_loop: LOOP
    FETCH room_cursor INTO v_room_type;
    IF v_done = 1 THEN
      LEAVE cursor_loop;
    END IF;

    SELECT 
      COUNT(*),
      SUM(status = 'Available'),
      ROUND(AVG(price_per_night), 2)
    INTO 
      v_total_rooms,
      v_available_rooms,
      v_avg_rate
    FROM rooms
    WHERE room_type = v_room_type;

    SELECT 
      COUNT(b.booking_id),
      COALESCE(SUM(CASE WHEN b.booking_status IN ('Confirmed', 'Checked In', 'Checked Out') THEN b.total_amount ELSE 0 END), 0)
    INTO 
      v_total_bookings,
      v_total_revenue
    FROM rooms r
    LEFT JOIN bookings b ON r.room_id = b.room_id
    WHERE r.room_type = v_room_type;

    INSERT INTO report_room_summary (
      room_type, total_rooms, available_rooms, total_bookings, total_revenue, average_rate, generated_at
    ) VALUES (
      v_room_type, v_total_rooms, v_available_rooms, v_total_bookings, v_total_revenue, v_avg_rate, NOW()
    );
  END LOOP cursor_loop;

  CLOSE room_cursor;

  SELECT * FROM report_room_summary ORDER BY total_revenue DESC;
END$$

DELIMITER ;

-- ====================================================================
-- SEED DATA (Ready for Viva & Instant Demo)
-- ====================================================================

-- 1. Insert Default Accounts with strictly UNIQUE emails and UNIQUE phone numbers
INSERT INTO users (username, full_name, email, phone, password_hash, role, status) VALUES
('admin', 'Hotel Administrator', 'admin@hotel.com', '+91 9876543210', 'scrypt:32768:8:1$rx3oGV7tlCSNZsHk$3df3350014c8b185e79010606592bd2d9abdbefaf0b836a3c95d9089b14d364b36e0573e4f314924d5b40ba0141bb9f5b8e9ca4d9824a3b4daa1a56688ae02f1', 'admin', 'Active'),
('john_doe', 'John Doe', 'john@example.com', '+91 9123456780', 'scrypt:32768:8:1$qAarM028yZ1mRres$d768d9e71063527e789f11444ea0630b66735299f9edf5642c28a71e805c70388c596a061a653a4f396c112b36464403479d410c4bc40c3a80d65cf20feb08d2', 'customer', 'Active'),
('priya_sharma', 'Priya Sharma', 'priya@example.com', '+91 9988776655', 'scrypt:32768:8:1$qAarM028yZ1mRres$d768d9e71063527e789f11444ea0630b66735299f9edf5642c28a71e805c70388c596a061a653a4f396c112b36464403479d410c4bc40c3a80d65cf20feb08d2', 'customer', 'Active'),
('rahul_verma', 'Rahul Verma', 'rahul@example.com', '+91 9456123789', 'scrypt:32768:8:1$qAarM028yZ1mRres$d768d9e71063527e789f11444ea0630b66735299f9edf5642c28a71e805c70388c596a061a653a4f396c112b36464403479d410c4bc40c3a80d65cf20feb08d2', 'customer', 'Active');

-- 2. Insert Room Inventory with sample photos for EVERY room
INSERT INTO rooms (room_number, room_type, capacity, price_per_night, amenities, image_url, status) VALUES
('101', 'Standard', 2, 1800.00, 'Free Wi-Fi, 32" LED TV, AC, Queen Bed, Attached Bathroom, Coffee Maker', 'https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=800&q=80', 'Available'),
('102', 'Standard', 2, 1800.00, 'Free Wi-Fi, 32" LED TV, AC, Twin Beds, Attached Bathroom, Work Desk', 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80', 'Available'),
('103', 'Standard', 1, 1500.00, 'Free Wi-Fi, 32" LED TV, AC, Single Bed, Attached Bathroom, Reading Lamp', 'https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80', 'Available'),
('201', 'Deluxe', 2, 2800.00, 'Free Wi-Fi, 43" 4K Smart TV, Climate Control, King Bed, Mini Fridge, Garden View', 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80', 'Available'),
('202', 'Deluxe', 3, 3200.00, 'Free Wi-Fi, 43" 4K Smart TV, Climate Control, King Bed + Sofa Bed, Balcony, Mini Fridge', 'https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=800&q=80', 'Available'),
('203', 'Deluxe', 2, 2800.00, 'Free Wi-Fi, 43" 4K Smart TV, AC, King Bed, Rainfall Shower, Mini Bar', 'https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=800&q=80', 'Maintenance'),
('301', 'Suite', 3, 5200.00, 'High-Speed Wi-Fi, 55" OLED TV, Master Bedroom, Separate Living Room, City Skyline View, Mini Bar', 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80', 'Available'),
('302', 'Suite', 4, 6200.00, 'High-Speed Wi-Fi, 55" OLED TV, 2 Bedrooms, Jacuzzi Bathtub, Living Lounge, Complimentary Breakfast', 'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=800&q=80', 'Available'),
('401', 'Family', 5, 4500.00, 'High-Speed Wi-Fi, 50" Smart TV, 2 Queen Beds + 1 Single Bed, Kids Play Area, Dining Nook', 'https://images.unsplash.com/photo-1595576508898-0ad5c879a061?auto=format&fit=crop&w=800&q=80', 'Available'),
('402', 'Family', 6, 5200.00, 'High-Speed Wi-Fi, 50" Smart TV, 3 Queen Beds, 2 Attached Bathrooms, Refrigerator, Microwave', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80', 'Available'),
('501', 'Executive', 2, 7500.00, 'Ultra High-Speed Wi-Fi, 65" Curved TV, Presidential Bedding, Private Workspace, Executive Lounge Access, Butler Service', 'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=800&q=80', 'Available'),
('502', 'Executive', 2, 7500.00, 'Ultra High-Speed Wi-Fi, 65" Curved TV, Panoramic Glass View, Executive Lounge Access, Complimentary Airport Shuttle', 'https://images.unsplash.com/photo-1568495248636-6432b97bd949?auto=format&fit=crop&w=800&q=80', 'Available');

-- 3. Insert Starter Bookings with 25% Advance Paid & 75% Balance
INSERT INTO bookings (
  user_id, room_id, check_in, check_out, guest_count, total_amount, advance_paid, balance_amount, 
  payment_mode, payment_status, booking_status, cancelled_by, cancellation_reason, created_at
) VALUES
((SELECT user_id FROM users WHERE username='john_doe'), (SELECT room_id FROM rooms WHERE room_number='101'), 
 DATE_SUB(CURDATE(), INTERVAL 15 DAY), DATE_SUB(CURDATE(), INTERVAL 12 DAY), 2, 5400.00, 1350.00, 4050.00, 
 'Credit/Debit Card', 'Fully Paid', 'Checked Out', NULL, NULL, DATE_SUB(NOW(), INTERVAL 16 DAY)),

((SELECT user_id FROM users WHERE username='priya_sharma'), (SELECT room_id FROM rooms WHERE room_number='201'), 
 DATE_SUB(CURDATE(), INTERVAL 5 DAY), DATE_SUB(CURDATE(), INTERVAL 2 DAY), 2, 8400.00, 2100.00, 6300.00, 
 'UPI / QR', 'Fully Paid', 'Checked Out', NULL, NULL, DATE_SUB(NOW(), INTERVAL 6 DAY)),

((SELECT user_id FROM users WHERE username='john_doe'), (SELECT room_id FROM rooms WHERE room_number='301'), 
 DATE_ADD(CURDATE(), INTERVAL 2 DAY), DATE_ADD(CURDATE(), INTERVAL 5 DAY), 2, 15600.00, 3900.00, 11700.00, 
 'Net Banking', 'Refunded', 'Cancelled', 'admin', 'Cancelled by Hotel Administration due to unavoidable operational/maintenance reasons.', DATE_SUB(NOW(), INTERVAL 1 DAY)),

((SELECT user_id FROM users WHERE username='rahul_verma'), (SELECT room_id FROM rooms WHERE room_number='401'), 
 DATE_ADD(CURDATE(), INTERVAL 7 DAY), DATE_ADD(CURDATE(), INTERVAL 10 DAY), 4, 13500.00, 3375.00, 10125.00, 
 'Credit/Debit Card', 'Advance Paid', 'Confirmed', NULL, NULL, NOW()),

((SELECT user_id FROM users WHERE username='priya_sharma'), (SELECT room_id FROM rooms WHERE room_number='102'), 
 DATE_SUB(CURDATE(), INTERVAL 25 DAY), DATE_SUB(CURDATE(), INTERVAL 22 DAY), 2, 5400.00, 1350.00, 4050.00, 
 'UPI / QR', 'Refunded', 'Cancelled', 'customer', 'Cancelled by Guest due to change of personal travel plans.', DATE_SUB(NOW(), INTERVAL 26 DAY));
