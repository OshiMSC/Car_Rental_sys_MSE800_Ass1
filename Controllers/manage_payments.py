from database import create_connection
import os
from werkzeug.utils import secure_filename
import sqlite3

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

class Payment:
    def __init__(self, upload_folder="static/uploads/payments"):
        self.upload_folder = upload_folder
        os.makedirs(self.upload_folder, exist_ok=True)

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    # ---------------- Admin / General ----------------
    def get_all_payments(self, search_query=None):
        conn = create_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = '''
            SELECT p.payment_id, b.booking_id, c.full_name AS customer, p.amount, 
                   p.payment_date, p.status
            FROM Payment p
            JOIN booking b ON p.booking_id = b.booking_id
            JOIN customers c ON b.customer_id = c.customer_id
        '''
        params = ()
        if search_query:
            sql += " WHERE c.full_name LIKE ? OR b.booking_id LIKE ? OR p.payment_date LIKE ?"
            params = (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')

        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        return results

    def get_payment(self, payment_id):
        conn = create_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Payment WHERE payment_id=?", (payment_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def add_payment(self, booking_id, amount, payment_method, status='Pending'):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Payment (booking_id, amount, payment_method, status) VALUES (?, ?, ?, ?)",
            (booking_id, amount, payment_method, status)
        )
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def update_payment_status(self, payment_id, status):
        if status not in ('Paid', 'Pending', 'Failed'):
            return False  # safeguard

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Payment SET status=? WHERE payment_id=?", (status, payment_id))
        conn.commit()
        conn.close()
        return True

    def delete_payment(self, payment_id):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Payment WHERE payment_id=?", (payment_id,))
        conn.commit()
        conn.close()

    # ---------------- Customer ----------------
    def get_customer_payments(self, customer_id):
        conn = create_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
            SELECT p.payment_id, p.booking_id, c.make || ' ' || c.model AS car_name,
                   p.amount, p.payment_date, p.payment_method, p.status
            FROM Payment p
            JOIN booking b ON p.booking_id = b.booking_id
            JOIN car c ON b.car_id = c.car_id
            WHERE b.customer_id = ?
            ORDER BY p.payment_date DESC
        """
        cursor.execute(query, (customer_id,))
        results = cursor.fetchall()
        conn.close()
        return results

    def upload_payment(self, customer_id, booking_id, file):
        if not file or not booking_id:
            return False, "Booking selection and file upload are required."

        if not self.allowed_file(file.filename):
            return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(self.upload_folder, filename)
        file.save(filepath)

        # Fetch booking details
        conn = create_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                B.booking_id, 
                B.start_date, 
                B.end_date, 
                C.rent_price_per_day,
                (julianday(B.end_date) - julianday(B.start_date)) * C.rent_price_per_day AS total_cost
            FROM booking B
            JOIN car C ON B.car_id = C.car_id
            WHERE B.booking_id=? AND B.customer_id=?
        """, (booking_id, customer_id))
        booking = cursor.fetchone()

        if not booking:
            conn.close()
            return False, "Invalid booking selected."

        amount = booking['total_cost']

        cursor.execute("""
            INSERT INTO Payment (booking_id, amount, payment_method, status)
            VALUES (?, ?, ?, ?)
        """, (booking_id, amount, 'Online', 'Pending'))
        conn.commit()
        conn.close()

        return True, f"Payment of ${amount:.2f} uploaded successfully! Status is Pending."

    # ---------------- Reports ----------------
    def get_total_confirmed_revenue(self):
        conn = create_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT IFNULL(SUM(amount), 0) AS total_revenue
            FROM Payment
            WHERE status = 'Paid'
        """)
        result = cursor.fetchone()
        conn.close()
        return result['total_revenue']
