# Project Report Guide: Hotel Room Reservation and Management System

Use this as the structure for the written college report. Add your own name, roll number, department, college, guide, and screenshots after running the application.

## 1. Abstract
The Hotel Room Reservation and Management System is a web-based database application designed to streamline room discovery, reservation, and hotel administration. It uses Flask for application logic and MySQL for persistent storage. Customers can register, log in, browse room categories, check availability for a date range, reserve rooms, and manage their reservations. Administrators can manage room inventory, update booking status, review customer accounts, and view reports. Relational constraints, transactions, indexes, a stored procedure, a view, and an audit trigger support data integrity and reporting.

## 2. Problem statement
Manual hotel reservation processes can result in duplicate bookings, inconsistent inventory, slow availability checks, and difficulty tracking reservations. A centralized reservation system is required to store customer, room, and booking information consistently, prevent overlapping active reservations for the same room, and provide role-based interfaces for customers and administrators.

## 3. Objectives
- Design a relational database normalized to Third Normal Form.
- Implement customer registration and shared role-based login.
- Support room search and date-based reservation.
- Provide an administrator interface for inventory, bookings, accounts, and reports.
- Demonstrate CRUD, joins, nested queries, aggregates, indexes, a view, a stored procedure, and a trigger.

## 4. Scope
The project supports one hotel/property and a single-room-per-booking reservation flow. Payment gateway integration, online check-in identity verification, notifications, and multi-property management are outside the current scope.

## 5. ER diagram
Use the Mermaid ER diagram in `README.md`. Recreate it in draw.io, Lucidchart, or ERDPlus if your instructor requires a separately exported diagram image.

## 6. Relational schema and keys
- USERS(user_id PK, full_name, email UNIQUE, phone, password_hash, role, status, created_at)
- ROOMS(room_id PK, room_number UNIQUE, room_type, capacity, price_per_night, amenities, status)
- BOOKINGS(booking_id PK, user_id FK, room_id FK, check_in, check_out, guest_count, total_amount, booking_status, created_at)
- BOOKING_AUDIT(audit_id PK, booking_id, old_status, new_status, changed_at, changed_by)

## 7. Normalization
Explain 1NF, 2NF, and 3NF using the notes in README.md. In particular, customer data is not duplicated in bookings and room details are not duplicated in booking records. `total_amount` is a booking-time snapshot of the agreed price.

## 8. Implementation
Document how the MySQL schema was created, how Flask connects to MySQL, how passwords are hashed, and how role-based decorators restrict routes.

## 9. SQL features demonstrated
- CRUD: registration, room management, booking creation, status updates, cancellation.
- JOIN: booking/customer/room tables.
- Nested query: `NOT EXISTS` for availability.
- Aggregate functions: `COUNT`, `SUM`, `COALESCE`.
- `GROUP BY` and report queries.
- Indexes on room filters and booking lookups.
- View: `vw_monthly_booking_summary`.
- Stored procedure: `sp_monthly_booking_summary`.
- Trigger: `trg_booking_status_audit`.

## 10. Test cases
1. Register a customer with a unique email — account should be created.
2. Register with an existing email — system should show an error.
3. Login with customer credentials — customer dashboard should appear.
4. Login with admin credentials — admin dashboard should appear.
5. Try to open `/admin` as a customer — access should be denied.
6. Search a room by dates — rooms with overlapping confirmed bookings should not appear.
7. Book a room with valid dates — reservation and total should be stored.
8. Attempt overlapping booking — system should reject it.
9. Cancel a future confirmed booking — status should become Cancelled.
10. Update a booking status as admin — audit row should be written.
11. Add a room with duplicate room number — database unique constraint should reject it.
12. Run monthly report — aggregate result should be displayed.

## 11. Results and screenshots
Insert screenshots of the landing page, login page, customer dashboard, room search, booking confirmation, admin dashboard, room inventory, booking management, SQL query outputs, and ER diagram.

## 12. Conclusion
The project demonstrates how a normalized relational database and a role-based web interface can improve the consistency and accessibility of hotel reservation operations. MySQL constraints protect key data relationships, while indexes, a reporting view, a stored procedure, and an audit trigger demonstrate core DBMS capabilities. The Flask interface provides distinct workflows for customers and administrators through a common login system.
