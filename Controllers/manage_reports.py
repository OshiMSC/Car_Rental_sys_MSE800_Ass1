# This page act as a connector between database and all interfaces which manage CRUD operations related to report generating:
import sqlite3
from database import create_connection

class ReportManager:
    def __init__(self):
        self.conn = create_connection()
        self.cursor = self.conn.cursor()

    def get_total_cars(self):
        self.cursor.execute("SELECT COUNT(*) FROM car")
        return self.cursor.fetchone()[0]

    def get_total_customers(self):
        self.cursor.execute("SELECT COUNT(*) FROM customers")
        return self.cursor.fetchone()[0]

    def get_total_bookings(self):
        self.cursor.execute("SELECT COUNT(*) FROM Booking")
        return self.cursor.fetchone()[0]

    def get_total_revenue(self):
        self.cursor.execute("SELECT SUM(amount) FROM Payment WHERE status='Paid'")
        total = self.cursor.fetchone()[0]
        return total if total else 0.0

  
    def save_report(self, admin_id, report_type, notes=""):
        self.cursor.execute(
            "INSERT INTO Report (admin_id, report_type, notes) VALUES (?, ?, ?)",
            (admin_id, report_type, notes)
        )
        self.conn.commit()

    def __init__(self):
        self.conn = create_connection()
        self.cursor = self.conn.cursor()

    def get_bookings_report(self, from_date=None, to_date=None):
        query = """
            SELECT b.booking_id, c.full_name as customer, car.make || ' ' || car.model as car,
                   b.start_date, b.status
            FROM Booking b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN car ON b.car_id = car.car_id
        """
        params = []
        if from_date and to_date:
            query += " WHERE b.start_date BETWEEN ? AND ?"
            params = [from_date, to_date]

        query += " ORDER BY b.start_date DESC"
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        bookings = []
        for r in rows:
            bookings.append({
                "booking_id": r[0],
                "customer": r[1],
                "car": r[2],
                "date": r[3],
                "status": r[4]
            })
        return bookings

    def get_payments_report(self, from_date=None, to_date=None):
        query = """
            SELECT p.payment_id, c.full_name as customer, p.amount, p.payment_date, p.status
            FROM Payment p
            JOIN Booking b ON p.booking_id = b.booking_id
            JOIN customers c ON b.customer_id = c.customer_id
        """
        params = []
        if from_date and to_date:
            query += " WHERE p.payment_date BETWEEN ? AND ?"
            params = [from_date, to_date]

        query += " ORDER BY p.payment_date DESC"
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        payments = []
        for r in rows:
            payments.append({
                "payment_id": r[0],
                "customer": r[1],
                "amount": r[2],
                "date": r[3],
                "status": r[4]
            })
        return payments
