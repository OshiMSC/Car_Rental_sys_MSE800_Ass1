import sqlite3
from database import create_connection
from datetime import datetime

class BookingManager:
    """Singleton class to manage all booking-related database operations."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._conn = create_connection()
        self._conn.row_factory = sqlite3.Row
        self._cursor = self._conn.cursor()

    # ----------------- Utility Methods -----------------

    def _execute(self, query, params=(), commit=False, fetchone=False, fetchall=False):
        try:
            self._cursor.execute(query, params)
            if commit:
                self._conn.commit()
            if fetchone:
                return self._cursor.fetchone()
            if fetchall:
                return self._cursor.fetchall()
            return self._cursor
        except Exception:
            try:
                self._conn.rollback()
            except Exception:
                pass
            raise

    def _rows_to_dicts(self, rows):
        return [dict(r) for r in rows]

    # ---------------- Customer Methods ----------------

    def get_customer_bookings(self, customer_id):
        rows = self._execute("""
            SELECT 
                b.booking_id,
                b.status,
                b.start_date,
                b.end_date,
                car.make || ' ' || car.model AS car_name
            FROM booking b
            JOIN car ON b.car_id = car.car_id
            WHERE b.customer_id = ? AND b.status IN ('Confirmed', 'Pending')
            ORDER BY 
                CASE b.status
                    WHEN 'Pending' THEN 1
                    WHEN 'Confirmed' THEN 2
                    ELSE 3
                END,
                b.start_date DESC
        """, (customer_id,), fetchall=True)
        return self._rows_to_dicts(rows)

    def create_booking(self, customer_id, car_id, start_date, end_date):
        cur = self._execute("""
            INSERT INTO booking (customer_id, car_id, start_date, end_date, status)
            VALUES (?, ?, ?, ?, 'Pending')
        """, (customer_id, car_id, start_date, end_date), commit=True)
        booking_id = cur.lastrowid

        # Mark car unavailable immediately
        self._execute("UPDATE car SET availability_status='Unavailable' WHERE car_id=?",
                      (car_id,), commit=True)
        return booking_id

    def update_booking_status(self, booking_id, new_status):
        car = self._execute("SELECT car_id FROM booking WHERE booking_id=?",
                            (booking_id,), fetchone=True)
        if not car:
            return False

        self._execute("UPDATE booking SET status=? WHERE booking_id=?",
                      (new_status, booking_id), commit=True)

        if new_status in ('Cancelled', 'Completed'):
            self._execute("UPDATE car SET availability_status='Available' WHERE car_id=?",
                          (car['car_id'],), commit=True)
        return True

    def get_booking_history(self, customer_id):
        rows = self._execute("""
            SELECT B.booking_id, C.make || ' ' || C.model AS car_name,
                   B.start_date, B.end_date, B.status, P.amount as fee
            FROM booking B
            JOIN car C ON B.car_id = C.car_id
            LEFT JOIN Payment P ON P.booking_id = B.booking_id
            WHERE B.customer_id=?
            ORDER BY B.start_date DESC
        """, (customer_id,), fetchall=True)
        return self._rows_to_dicts(rows)

    # ---------------- Admin Methods ----------------

    def get_all_bookings(self, search_query=None):
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
            query += " WHERE c.full_name LIKE ? OR car.model LIKE ? OR car.make LIKE ? OR b.start_date LIKE ? OR b.end_date LIKE ?"
            like_query = f"%{search_query}%"
            params = [like_query]*5

        rows = self._execute(query, params, fetchall=True)
        return self._rows_to_dicts(rows)

    def get_pending_bookings(self):
        rows = self._execute("""
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
        """, fetchall=True)
        return self._rows_to_dicts(rows)

    def add_booking(self, customer_id, car_id, start_date, end_date, status='Confirmed'):
        try:
            cur = self._execute("""
                INSERT INTO booking (customer_id, car_id, start_date, end_date, status)
                VALUES (?, ?, ?, ?, ?)
            """, (customer_id, car_id, start_date, end_date, status), commit=True)
            booking_id = cur.lastrowid
            self._execute(
                "UPDATE car SET availability_status='Unavailable' WHERE car_id=?",
                (car_id,), commit=True
            )
            return True, booking_id
        except Exception as e:
            return False, str(e)

    def delete_booking(self, booking_id):
        self._execute("DELETE FROM booking WHERE booking_id=?", (booking_id,), commit=True)

    def get_available_cars_admin(self, search_query=None):
        query = "SELECT * FROM car WHERE availability_status='Available'"
        params = []
        if search_query:
            query += " AND (make LIKE ? OR model LIKE ?)"
            params = [f"%{search_query}%", f"%{search_query}%"]
        rows = self._execute(query, params, fetchall=True)
        return self._rows_to_dicts(rows)

    def get_recent_bookings(self, limit=10):
        rows = self._execute("""
            SELECT 
                b.booking_id,
                b.start_date,
                b.end_date,
                b.status AS booking_status,
                c.full_name AS customer_name,
                ca.make || ' ' || ca.model AS car_name,
                p.payment_id,
                p.status AS payment_status,
                p.amount
            FROM Booking b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN car ca ON b.car_id = ca.car_id
            LEFT JOIN Payment p ON b.booking_id = p.booking_id
            ORDER BY b.booking_id DESC
            LIMIT ?
        """, (limit,), fetchall=True)
        return self._rows_to_dicts(rows)

    def get_total_revenue(self):
        result = self._execute("SELECT SUM(amount) FROM Payment WHERE status='Paid'", fetchone=True)
        return result[0] if result and result[0] else 0

    def get_total_cars(self):
        result = self._execute("SELECT COUNT(*) FROM car", fetchone=True)
        return result[0] if result else 0

    def get_total_customers(self):
        result = self._execute("SELECT COUNT(*) FROM customers", fetchone=True)
        return result[0] if result else 0

    def get_notifications(self, customer_id):
        rows = self._execute("""
            SELECT message, created_at, is_read
            FROM Notifications
            WHERE customer_id=?
            ORDER BY created_at DESC
        """, (customer_id,), fetchall=True)
        return self._rows_to_dicts(rows)

    def get_customer_bookings_with_fine(self, customer_id):
        rows = self._execute("""
            SELECT b.booking_id, c.make || ' ' || c.model AS car_name, 
                   b.total_cost,
                   cb.fine_amount
            FROM booking b
            JOIN Car c ON b.car_id = c.car_id
            LEFT JOIN CompletedBookings cb ON b.booking_id = cb.booking_id
            WHERE b.customer_id = ? AND b.status IN ('Confirmed', 'Completed')
        """, (customer_id,), fetchall=True)
        return self._rows_to_dicts(rows)

    def get_pending_completed_bookings_for_customer(self, customer_id):
        """
        Fetch completed bookings for a customer that do not have a payment yet.
        Calculates rent_cost and total_cost.
        """
        rows = self._execute("""
            SELECT 
                CB.booking_id,
                C.make || ' ' || C.model AS car_name,
                C.rent_price_per_day,
                CB.fine_amount,
                ((julianday(CB.end_date) - julianday(CB.start_date) + 1) * C.rent_price_per_day) AS rent_cost
            FROM CompletedBookings CB
            JOIN Car C ON CB.car_id = C.car_id
            WHERE CB.customer_id=? 
            AND CB.booking_id NOT IN (SELECT booking_id FROM Payment)
            ORDER BY CB.start_date ASC
        """, (customer_id,), fetchall=True)

        bookings = []
        for row in rows:
            row = dict(row)
            row['total_cost'] = (row['rent_cost'] or 0) + (row['fine_amount'] or 0)
            bookings.append(row)

        return bookings


    def get_available_cars(self, search_query=None, start_date=None, end_date=None):
        query = """
            SELECT * FROM car
            WHERE car_id NOT IN (
                SELECT car_id FROM booking
                WHERE status IN ('Confirmed', 'Pending')
                AND (? IS NULL OR start_date <= ? AND end_date >= ?)
            )
        """
        params = [start_date, end_date, end_date]
        if search_query:
            query += " AND (make LIKE ? OR model LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        rows = self._execute(query, params, fetchall=True)
        return self._rows_to_dicts(rows)

    # ---------------- Admin Booking Stats ----------------

    def get_confirmed_bookings(self):
        rows = self._execute("""
            SELECT b.booking_id, c.full_name AS customer_name, 
                   car.make || ' ' || car.model AS car_name, b.start_date, b.end_date
            FROM booking b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN car ON b.car_id = car.car_id
            WHERE b.status='Confirmed'
        """, fetchall=True)
        return self._rows_to_dicts(rows)

    def get_completed_bookings(self):
        """
        Fetch all completed bookings with rent, fine, and total cost.
        """
        rows = self._execute("""
            SELECT 
                CB.completed_id,
                CB.booking_id,
                C.full_name AS customer_name,
                Car.make || ' ' || Car.model AS car_name,
                Car.rent_price_per_day,
                CB.start_date,
                CB.end_date,
                CB.return_date,
                CB.fine_amount,
                ((julianday(CB.end_date) - julianday(CB.start_date) + 1) * Car.rent_price_per_day) AS rent_cost
            FROM CompletedBookings CB
            JOIN Car ON CB.car_id = Car.car_id
            JOIN customers C ON CB.customer_id = C.customer_id
            ORDER BY CB.start_date ASC
        """, fetchall=True)

        bookings = []
        for row in rows:
            row = dict(row)
            row['total_cost'] = (row['rent_cost'] or 0) + (row['fine_amount'] or 0)
            bookings.append(row)

        return bookings


    # ---------------- Customer Favorites ----------------

    def add_favorite_car(self, customer_id, car_id):
        try:
            self._execute(
                "INSERT OR IGNORE INTO FavoriteCars (customer_id, car_id) VALUES (?, ?)",
                (customer_id, car_id),
                commit=True
            )
            return True, None
        except Exception as e:
            return False, str(e)

    def get_car_bookings(self, car_id):
        rows = self._execute(
            "SELECT start_date, end_date FROM booking WHERE car_id=?",
            (car_id,), fetchall=True
        )
        return self._rows_to_dicts(rows)

    def return_car(self, booking_id, return_date_str, fine_amount):
            booking = self._execute(
                "SELECT * FROM booking WHERE booking_id=?",
                (booking_id,), fetchone=True
            )
            if not booking:
                return False, "Booking not found"

            # Convert dates to datetime objects
            start_date = datetime.strptime(booking['start_date'], "%Y-%m-%d")
            end_date = datetime.strptime(booking['end_date'], "%Y-%m-%d")
            return_date = datetime.strptime(return_date_str, "%Y-%m-%d")

            # ❌ Case 1: Return before booking start
            if return_date < start_date:
                return False, "Return date cannot be before the booking start date."

            # ✅ Case 2: Return on or before booking end (normal return, no fine)
            if return_date <= end_date:
                fine_amount = 0.0
            # ✅ Case 3: Return after booking end (late return → fine applied)
            else:
                late_days = (return_date - end_date).days
                fine_amount = fine_amount if fine_amount > 0 else late_days * 20  

            # --- NEW: calculate base cost ---
            car = self._execute(
                "SELECT rent_price_per_day FROM car WHERE car_id=?",
                (booking['car_id'],), fetchone=True
            )
            if not car:
                return False, "Car not found"

            rental_days = (end_date - start_date).days + 1  # inclusive
            cost = rental_days * car['rent_price_per_day']

            # total cost = rental cost + fine
            total_cost = cost + fine_amount

            # Save into CompletedBookings
            self._execute("""
                INSERT INTO CompletedBookings
                        (booking_id, customer_id, car_id, start_date, end_date, return_date, cost, fine_amount, total_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                booking['booking_id'], booking['customer_id'], booking['car_id'],
                booking['start_date'], booking['end_date'], return_date_str,
                cost, fine_amount, total_cost
            ), commit=True)

            # Remove from active bookings
            self._execute(
                "DELETE FROM booking WHERE booking_id=?",
                (booking_id,), commit=True
            )
            return True, None


    # ---------------- Dashboard Related Methods ----------------

    def get_total_bookings_for_customer(self, customer_id):
        result = self._execute(
            "SELECT COUNT(*) FROM booking WHERE customer_id=?",
            (customer_id,), fetchone=True
        )
        return result[0] if result else 0

    def get_upcoming_rentals_for_customer(self, customer_id):
        today = datetime.today().date()
        result = self._execute(
            "SELECT COUNT(*) FROM booking WHERE customer_id=? AND start_date >= ?",
            (customer_id, today), fetchone=True
        )
        return result[0] if result else 0

    def get_total_favorites_for_customer(self, customer_id):
        result = self._execute(
            "SELECT COUNT(*) FROM FavoriteCars WHERE customer_id=?",
            (customer_id,), fetchone=True
        )
        return result[0] if result else 0

    def get_favorite_cars_for_customer(self, customer_id):
        rows = self._execute("""
            SELECT c.car_id, c.make, c.model, c.year, c.seats, c.rent_price_per_day
            FROM FavoriteCars f
            JOIN car c ON f.car_id = c.car_id
            WHERE f.customer_id = ?
            ORDER BY f.created_at DESC
        """, (customer_id,), fetchall=True)
        return self._rows_to_dicts(rows)

    def get_available_favorites_for_customer(self, customer_id):
        rows = self._execute("""
            SELECT c.*
            FROM FavoriteCars f
            JOIN Car c ON c.car_id = f.car_id
            WHERE f.customer_id=? AND c.availability_status='Available'
        """, (customer_id,), fetchall=True)
        return self._rows_to_dicts(rows)