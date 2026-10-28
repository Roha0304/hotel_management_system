USE hotel_management;

-- 1. Extend room status to include 'Booked' and 'Occupied'
ALTER TABLE rooms 
  MODIFY status ENUM('Available','Booked','Occupied','Maintenance','Inactive') 
  NOT NULL DEFAULT 'Available';

-- 2. Add check_in_time and check_out_time to bookings table
ALTER TABLE bookings 
  ADD COLUMN check_in_time VARCHAR(20) NOT NULL DEFAULT '12:00 PM' AFTER check_in,
  ADD COLUMN check_out_time VARCHAR(20) NOT NULL DEFAULT '11:00 AM' AFTER check_out;

-- 3. Add check_in_time and check_out_time to payments table
ALTER TABLE payments 
  ADD COLUMN check_in_time VARCHAR(20) NOT NULL DEFAULT '12:00 PM' AFTER check_in,
  ADD COLUMN check_out_time VARCHAR(20) NOT NULL DEFAULT '11:00 AM' AFTER check_out;
