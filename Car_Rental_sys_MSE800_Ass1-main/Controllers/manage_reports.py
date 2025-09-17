# manage_reports.py
import sqlite3
from database import create_connection

class ReportManager:
    """Singleton class to manage all report-related database operations."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ReportManager, cls).__new__(cls)
            cls._instance.__initialize()
        return cls._instance

    def __initialize(self):
        """Initialize database connection once (Singleton)"""
        self.__conn = create_connection()
        self.__conn.row_factory = sqlite3.Row
        self.__cursor = self.__conn.cursor()

    # ---------------- Private Helper ----------------
    def __execute(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        self.__cursor.execute(query, params)
        if commit:
            self.__conn.commit()
        if fetchone:
            return self.__cursor.fetchone()
        if fetchall:
            return self.__cursor.fetchall()
        return self.__cursor

    # ---------------- Reports Summary ----------------
    def get_total_cars(self):
        result = self.__execute("SELECT COUNT(*) FROM car", fetchone=True)
        return result[0] if result else 0

    def get_total_customers(self):
        result = self.__execute("SELECT COUNT(*) FROM customers", fetchone=True)
        return result[0] if result else 0

    def get_total_bookings(self):
        result = self.__execute("SELECT COUNT(*) FROM Booking", fetchone=True)
        return result[0] if result else 0

    def get_total_revenue(self):
        result = self.__execute("SELECT SUM(amount) FROM Payment WHERE status='Paid'", fetchone=True)
        return result[0] if result[0] else 0.0

    # ---------------- Report Actions ----------------
    def save_report(self, admin_id, report_type, notes=""):
        self.__execute(
            "INSERT INTO Report (admin_id, report_type, notes) VALUES (?, ?, ?)",
            (admin_id, report_type, notes),
            commit=True
        )

    def get_bookings_report(self, from_date=None, to_date=None):
        query = """
            SELECT b.booking_id, c.full_name as customer, car.make || ' ' || car.model as car,
                   b.start_date, b.status
            FROM booking b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN car ON b.car_id = car.car_id
        """
        params = []
        if from_date and to_date:
            query += " WHERE b.start_date BETWEEN ? AND ?"
            params = [from_date, to_date]

        query += " ORDER BY b.start_date DESC"
        rows = self.__execute(query, params, fetchall=True)

        return [
            {
                "booking_id": r["booking_id"],
                "customer": r["customer"],
                "car": r["car"],
                "date": r["start_date"],
                "status": r["status"],
            }
            for r in rows
        ]

    def get_payments_report(self, from_date=None, to_date=None):
        query = """
            SELECT p.payment_id, c.full_name as customer, p.amount, p.payment_date, p.status
            FROM Payment p
            JOIN booking b ON p.booking_id = b.booking_id
            JOIN customers c ON b.customer_id = c.customer_id
        """
        params = []
        if from_date and to_date:
            query += " WHERE p.payment_date BETWEEN ? AND ?"
            params = [from_date, to_date]

        query += " ORDER BY p.payment_date DESC"
        rows = self.__execute(query, params, fetchall=True)

        return [
            {
                "payment_id": r["payment_id"],
                "customer": r["customer"],
                "amount": r["amount"],
                "date": r["payment_date"],
                "status": r["status"],
            }
            for r in rows
        ]

    # ---------------- Revenue Breakdown ----------------
    def get_daily_revenue(self):
        rows = self.__execute("""
            SELECT date(payment_date) AS day, IFNULL(SUM(amount),0) AS total
            FROM Payment
            WHERE status='Paid'
            GROUP BY day
            ORDER BY day ASC
        """, fetchall=True)
        return [{"day": r["day"], "total": r["total"]} for r in rows]

    def get_weekly_revenue(self):
        rows = self.__execute("""
            SELECT strftime('%Y-%W', payment_date) AS week, IFNULL(SUM(amount),0) AS total
            FROM Payment
            WHERE status='Paid'
            GROUP BY week
            ORDER BY week ASC
        """, fetchall=True)
        return [{"week": r["week"], "total": r["total"]} for r in rows]

    def get_monthly_revenue(self):
        rows = self.__execute("""
            SELECT strftime('%Y-%m', payment_date) AS month, IFNULL(SUM(amount),0) AS total
            FROM Payment
            WHERE status='Paid'
            GROUP BY month
            ORDER BY month ASC
        """, fetchall=True)
        return [{"month": r["month"], "total": r["total"]} for r in rows]

    def __del__(self):
        if hasattr(self, "_ReportManager__conn"):
            self.__conn.close()
