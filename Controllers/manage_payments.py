# This page act as a connector between database and all interfaces which manage CRUD operations related to payment handling:
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
        """Handle the upload files of customers"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    # ---------------- Admin / General ----------------
    def get_all_payments(self, search_query=None):
        """Retrieve all payment details by search query."""
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
        """Retrieve all payment details and filter them by payment Id by search query."""
        conn = create_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Payment WHERE payment_id=?", (payment_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def add_payment(self, booking_id, amount, payment_method, status='Pending'):
        """Insert a new payment details into the database."""
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
        """Update a payment detail into the database."""
        if status not in ('Paid', 'Pending', 'Failed'):
            return False  # safeguard

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Payment SET status=? WHERE payment_id=?", (status, payment_id))
        conn.commit()
        conn.close()
        return True

    def delete_payment(self, payment_id):
        """Delete a payment detail from the database."""
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Payment WHERE payment_id=?", (payment_id,))
        conn.commit()
        conn.close()

    # ---------------- Customer ----------------
    def get_customer_payments(self, customer_id):
        """Retrive all the details of the payments done by customers from the database."""
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
        "Handle the functions of payment invoice uploading"
        if not file or not booking_id:
            return False, "Booking selection and file upload are required."

        if not self.allowed_file(file.filename):
            return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

        # Save file securely
        filename = secure_filename(file.filename)
        filepath = os.path.join(self.upload_folder, filename)
        file.save(filepath)

        conn = create_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # ✅ Fetch booking details from CompletedBookings (to include fine)
        cursor.execute("""
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
        """, (booking_id, customer_id))

        booking = cursor.fetchone()

        if not booking:
            conn.close()
            return False, "Invalid booking selected."

        # ✅ Calculate final amount (rent + fine)
        rent_cost = booking['rent_cost'] or 0
        fine = booking['fine_amount'] or 0
        amount = rent_cost + fine

        # ✅ Insert Payment record
        cursor.execute("""
            INSERT INTO Payment (booking_id, amount, payment_method, status)
            VALUES (?, ?, ?, ?)
        """, (booking_id, amount, 'Online', 'Pending'))
        conn.commit()
        conn.close()

        return True, f"Payment of ${amount:.2f} uploaded successfully! Status is Pending."


    # ---------------- Reports ----------------
    def get_total_confirmed_revenue(self):
        """Calculate the total revenue"""
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
    
    