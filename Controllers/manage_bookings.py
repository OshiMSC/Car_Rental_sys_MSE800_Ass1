# This page act as a connector between database and all interfaces which manage CRUD operations related to customer and admin bookings:
import sqlite3
from database import create_connection
from datetime import datetime

class BookingManager:
    def __init__(self):
        self.conn = create_connection()
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    # ---------------- Customer Methods ----------------

    def get_available_cars(self, search_query=None, start_date=None, end_date=None):
        """Get all available cars. Optionally filter by search query and exclude cars already booked in the date range."""
        query = "SELECT * FROM car WHERE availability_status='Available'"
        params = []

        if search_query:
            query += " AND (make LIKE ? OR model LIKE ? OR plate_number LIKE ?)"
            like_query = f"%{search_query}%"
            params.extend([like_query, like_query, like_query])

        if start_date and end_date:
            query += """
                AND car_id NOT IN (
                    SELECT car_id FROM booking
                    WHERE status IN ('Pending', 'Confirmed')
                    AND NOT (end_date < ? OR start_date > ?)
                )
            """
            params.extend([start_date, end_date])

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_customer_bookings(self, customer_id):
        """Fetch all bookings for a customer (Pending + Confirmed + Cancelled)"""
        self.cursor.execute("""
            SELECT 
                b.booking_id,
                b.status,
                b.start_date,
                b.end_date,
                car.make || ' ' || car.model AS car_name
            FROM booking b
            JOIN car ON b.car_id = car.car_id
            WHERE b.customer_id = ?
            ORDER BY b.start_date ASC
        """, (customer_id,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    
    def create_booking(self, customer_id, car_id, start_date, end_date):
        """Create a new booking with status 'Pending' and mark car as unavailable."""
        self.cursor.execute("""
            INSERT INTO booking (customer_id, car_id, start_date, end_date, status)
            VALUES (?, ?, ?, ?, 'Pending')
        """, (customer_id, car_id, start_date, end_date))
        booking_id = self.cursor.lastrowid

        self.cursor.execute("UPDATE car SET availability_status='Unavailable' WHERE car_id=?", (car_id,))
        self.conn.commit()
        return booking_id

    def update_booking_status(self, booking_id, new_status):
        """Update booking status and adjust car availability if necessary."""
        self.cursor.execute("SELECT car_id FROM booking WHERE booking_id=?", (booking_id,))
        car = self.cursor.fetchone()
        if not car:
            return False

        self.cursor.execute("UPDATE booking SET status=? WHERE booking_id=?", (new_status, booking_id))

        if new_status in ('Cancelled', 'Completed'):
            self.cursor.execute("UPDATE car SET availability_status='Available' WHERE car_id=?", (car['car_id'],))

        self.conn.commit()
        return True

    def get_booking_history(self, customer_id):
        """Get customer's booking history with payments."""
        self.cursor.execute("""
            SELECT B.booking_id, C.make || ' ' || C.model AS car_name,
                   B.start_date, B.end_date, B.status, P.amount as fee
            FROM booking B
            JOIN car C ON B.car_id = C.car_id
            LEFT JOIN Payment P ON P.booking_id = B.booking_id
            WHERE B.customer_id=?
            ORDER BY B.start_date DESC
        """, (customer_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    # ---------------- Admin Methods ----------------

    def get_all_bookings(self, search_query=None):
        """Get all bookings with optional search filter."""
        query = """
            SELECT b.booking_id, c.full_name AS customer_name, 
                   car.make || ' ' || car.model AS car_name,
                   b.start_date, b.end_date, b.status
            FROM booking b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN car ON b.car_id = car.car_id
        """
        params = []

        if search_query:
            query += """
                WHERE c.full_name LIKE ? OR car.model LIKE ? 
                   OR car.make LIKE ? OR b.start_date LIKE ? OR b.end_date LIKE ?
            """
            like_query = f"%{search_query}%"
            params = [like_query, like_query, like_query, like_query, like_query]

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_pending_bookings(self):
        """Get all bookings with status 'Pending'."""
        self.cursor.execute("""
            SELECT 
                b.booking_id,
                c.full_name AS customer_name,
                car.make || ' ' || car.model AS car_name,
                b.start_date,
                b.end_date,
                b.status
            FROM booking b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN car ON b.car_id = car.car_id
            WHERE b.status='Pending'
            ORDER BY b.start_date ASC
        """)
        return [dict(row) for row in self.cursor.fetchall()]

    def add_booking(self, customer_id, car_id, start_date, end_date, status='Pending'):
        """Admin adds a booking manually."""
        self.cursor.execute("""
            INSERT INTO booking (customer_id, car_id, start_date, end_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, (customer_id, car_id, start_date, end_date, status))
        self.conn.commit()
        return self.cursor.lastrowid

    def delete_booking(self, booking_id):
        """Delete a booking."""
        self.cursor.execute("DELETE FROM booking WHERE booking_id=?", (booking_id,))
        self.conn.commit()

    def get_available_cars_admin(self, search_query=None):
        """Admin view of available cars."""
        query = "SELECT * FROM car WHERE availability_status='Available'"
        params = []

        if search_query:
            query += " AND (make LIKE ? OR model LIKE ?)"
            like_query = f"%{search_query}%"
            params = [like_query, like_query]

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_recent_bookings(self, limit=5):
        """Fetch recent bookings with customer name, car name, and status."""
        self.cursor.execute("""
            SELECT b.booking_id, c.full_name AS customer, 
                   car.make || ' ' || car.model AS car, 
                   b.start_date, b.end_date, b.status AS booking_status
            FROM booking b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN car car ON b.car_id = car.car_id
            ORDER BY b.booking_id DESC
            LIMIT ?
        """, (limit,))
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def get_total_revenue(self):
        self.cursor.execute("SELECT SUM(amount) FROM Payment WHERE status='Paid'")
        result = self.cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def get_total_cars(self):
        self.cursor.execute("SELECT COUNT(*) FROM car")
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def get_total_customers(self):
        self.cursor.execute("SELECT COUNT(*) FROM customers")
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def get_notifications(self, customer_id):
        self.cursor.execute("""
            SELECT message, created_at, is_read
            FROM Notifications
            WHERE customer_id=?
            ORDER BY created_at DESC
        """, (customer_id,))
        return self.cursor.fetchall()
    
    def get_customer_bookings_with_fine(self, customer_id):
        self.cursor.execute('''
            SELECT b.booking_id, c.make || ' ' || c.model AS car_name, 
                   b.total_cost,
                   f.fine_amount
            FROM booking b
            JOIN Car c ON b.car_id = c.car_id
            LEFT JOIN Fines f ON b.booking_id = f.booking_id
            WHERE b.customer_id = ?
              AND b.status IN ('Confirmed', 'Completed')
        ''', (customer_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    def __del__(self):
        self.conn.close()
