# manage_payments.py
from database import create_connection
import os
import sqlite3
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

class PaymentManager:
    """Singleton class to manage all payment-related database operations."""
    _instance = None

    def __new__(cls, upload_folder="static/uploads/payments"):
        if cls._instance is None:
            cls._instance = super(PaymentManager, cls).__new__(cls)
            cls._instance.__initialize(upload_folder)
        return cls._instance

    def __initialize(self, upload_folder):
        """Initialize database connection and upload folder once."""
        self._conn = create_connection()
        self._conn.row_factory = sqlite3.Row
        self._cursor = self._conn.cursor()
        self._upload_folder = upload_folder
        os.makedirs(self._upload_folder, exist_ok=True)

    # ---------------- Helpers ----------------
    def _execute(self, query, params=(), commit=False, fetchone=False, fetchall=False):
        """Centralized execute method for all queries."""
        self._cursor.execute(query, params)
        if commit:
            self._conn.commit()
        if fetchone:
            return self._cursor.fetchone()
        if fetchall:
            return self._cursor.fetchall()
        return self._cursor
    
    def _rows_to_dicts(self, rows):
        """Convert sqlite3.Row objects to list of dicts."""
        return [dict(r) for r in rows]

    def _is_allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    # ---------------- Admin / General ----------------
    def get_all_payments(self, search_query=None):
        sql = '''
            SELECT p.payment_id, cb.booking_id, 
                c.full_name AS customer, 
                car.make || ' ' || car.model AS car_name,
                p.amount, p.payment_date, p.status
            FROM Payment p
            JOIN CompletedBookings cb ON p.booking_id = cb.booking_id
            JOIN customers c ON cb.customer_id = c.customer_id
            JOIN car ON cb.car_id = car.car_id
        '''
        params = ()
        if search_query:
            sql += " WHERE c.full_name LIKE ? OR cb.booking_id LIKE ? OR p.payment_date LIKE ?"
            params = (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')

        rows = self._execute(sql, params, fetchall=True)
        return [dict(row) for row in rows]

    def get_payment(self, payment_id):
        return self._execute("SELECT * FROM Payment WHERE payment_id=?", (payment_id,), fetchone=True)

    def add_payment(self, booking_id, amount, payment_method, status='Pending'):
        cur = self._execute("""
            INSERT INTO Payment (booking_id, amount, payment_method, status) 
            VALUES (?, ?, ?, ?)
        """, (booking_id, amount, payment_method, status), commit=True)
        return cur.lastrowid

    def update_payment_status(self, payment_id, status):
        try:
            self._execute(
                "UPDATE Payment SET status=? WHERE payment_id=?",
                (status, payment_id),
                commit=True  # important
            )
            return True, None
        except Exception as e:
            return False, str(e)


    def delete_payment(self, payment_id):
        self._execute("DELETE FROM Payment WHERE payment_id=?", (payment_id,), commit=True)

    # ---------------- Customer ----------------
    def get_customer_payments(self, customer_id):
        """
        Fetch all payments for a customer, including car info and the current status.
        """
        sql = '''
            SELECT p.payment_id,
                cb.booking_id,
                car.make || ' ' || car.model AS car_name,
                p.amount,
                p.payment_date,
                p.payment_method,
                p.status
            FROM Payment p
            JOIN CompletedBookings cb ON p.booking_id = cb.booking_id
            JOIN car ON cb.car_id = car.car_id
            WHERE cb.customer_id = ?
            ORDER BY p.payment_date DESC
        '''
        rows = self._execute(sql, (customer_id,), fetchall=True)
        # Convert rows to list of dicts
        payments = [dict(row) for row in rows]
        return payments

    def upload_payment(self, customer_id, booking_id, file):
        if not file or not booking_id:
            return False, "Booking selection and file upload are required."

        if not self._is_allowed_file(file.filename):
            return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

        # Securely save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(self._upload_folder, filename)
        file.save(filepath)

        # Fetch booking details from CompletedBookings
        booking = self._execute("""
            SELECT 
                CB.booking_id,
                CB.start_date,
                CB.end_date,
                CB.fine_amount,
                C.rent_price_per_day,
                ((julianday(CB.end_date) - julianday(CB.start_date) + 1) * C.rent_price_per_day) AS rent_cost
            FROM CompletedBookings CB
            JOIN Car C ON CB.car_id = C.car_id
            WHERE CB.booking_id=? AND CB.customer_id=?
        """, (booking_id, customer_id), fetchone=True)

        if not booking:
            return False, "Invalid booking selected."

        rent_cost = booking['rent_cost'] or 0
        fine = booking['fine_amount'] or 0
        amount = rent_cost + fine

        self._execute("""
            INSERT INTO Payment (booking_id, amount, payment_method, status)
            VALUES (?, ?, ?, ?)
        """, (booking_id, amount, 'Online', 'Pending'), commit=True)

        return True, f"Payment of ${amount:.2f} uploaded successfully! Status is Pending."

    # ---------------- Reports ----------------
    def get_total_confirmed_revenue(self):
        result = self._execute("""
            SELECT IFNULL(SUM(amount), 0) AS total_revenue
            FROM Payment
            WHERE status = 'Paid'
        """, fetchone=True)
        return result['total_revenue']

    # ---------------- Dashboard Related Methods ----------------
    def get_recent_payments(self, limit=20):
        """
        Fetch recent completed bookings that have payments, including car name and customer name.
        """
        rows = self._execute("""
            SELECT p.payment_id,
                cb.booking_id,
                cb.customer_id,
                c.make || ' ' || c.model AS car_name,
                cust.full_name AS customer_name,
                p.amount,
                p.payment_date,
                p.status
            FROM Payment p
            JOIN CompletedBookings cb ON p.booking_id = cb.booking_id
            JOIN car c ON cb.car_id = c.car_id
            JOIN customers cust ON cb.customer_id = cust.customer_id
            ORDER BY p.payment_date DESC
            LIMIT ?
        """, (limit,), fetchall=True)
        return self._rows_to_dicts(rows)

    def is_booking_paid(self, booking_id):
        """Check if a specific booking already has a payment record."""
        result = self._execute(
            "SELECT 1 FROM Payment WHERE booking_id=? AND status='Paid'",
            (booking_id,), fetchone=True
        )
        return bool(result)

    def __del__(self):
        if hasattr(self, "_conn"):
            try:
                self._conn.close()
            except Exception:
                pass
