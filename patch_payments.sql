USE hotel_management;

-- Support credit cards, UPI / QR, net banking, cash, and other payment modes
ALTER TABLE bookings
  MODIFY payment_mode ENUM('Credit/Debit Card','UPI / QR','Net Banking','Cash at Arrival','Wallet / Other')
  NOT NULL DEFAULT 'Credit/Debit Card';

CREATE TABLE IF NOT EXISTS payments (
  pay_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  room_id INT NOT NULL,
  check_in DATE NOT NULL,
  check_out DATE NOT NULL,
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