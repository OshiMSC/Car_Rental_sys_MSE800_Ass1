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
    
    def _rows_to_dicts(self, rows):
        columns = [desc[0] for desc in self._cursor.description]
        return [dict(zip(columns, row)) for row in rows]

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
        """
        Fetch all completed bookings with customer, car, rent cost, fine, and total cost.
        Can filter by start and end dates.
        """
        sql = """
            SELECT 
                CB.completed_id,
                CB.booking_id,
                C.full_name AS customer,
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
            WHERE 1=1
        """

        params = []
        if from_date:
            sql += " AND CB.start_date >= ?"
            params.append(from_date)
        if to_date:
            sql += " AND CB.end_date <= ?"
            params.append(to_date)

        sql += " ORDER BY CB.start_date ASC"

        rows = self._execute(sql, tuple(params), fetchall=True)
        
        # Convert rows to list of dicts and calculate total_cost
        bookings = []
        for row in rows:
            row = dict(row)
            row['total_cost'] = (row['rent_cost'] or 0) + (row['fine_amount'] or 0)
            bookings.append(row)

        return bookings

    def get_payments_report(self, from_date=None, to_date=None):
        """
        Fetch all payments with customer name, amount, date, and status.
        Can filter by date range.
        """
        sql = """
            SELECT 
                P.payment_id,
                P.booking_id,
                C.full_name AS customer,
                P.amount,
                P.payment_date,
                P.status
            FROM Payment P
            JOIN booking B ON P.booking_id = B.booking_id
            JOIN customers C ON B.customer_id = C.customer_id
            WHERE 1=1
        """

        params = []
        if from_date:
            sql += " AND P.payment_date >= ?"
            params.append(from_date)
        if to_date:
            sql += " AND P.payment_date <= ?"
            params.append(to_date)

        sql += " ORDER BY P.payment_date DESC"

        rows = self._execute(sql, tuple(params), fetchall=True)
        
        # Convert rows to list of dicts
        payments = [dict(row) for row in rows]

        return payments



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
