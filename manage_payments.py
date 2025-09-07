from database import create_connection

class Payment:
    def __init__(self):
        self.conn = create_connection()
        self.cursor = self.conn.cursor()

    def get_all_payments(self, search_query=None):
        """Retrieve all payments with optional search by customer name, booking id, or date."""
        sql = '''
            SELECT p.payment_id, b.booking_id, c.full_name AS customer, p.amount, 
                   p.payment_date, p.status
            FROM Payment p
            JOIN Booking b ON p.booking_id = b.booking_id
            JOIN customers c ON b.customer_id = c.customer_id
        '''
        params = ()
        if search_query:
            sql += '''
                WHERE c.full_name LIKE ? OR b.booking_id LIKE ? OR p.payment_date LIKE ?
            '''
            params = (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')
        
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def get_payment(self, payment_id):
        self.cursor.execute("SELECT * FROM Payment WHERE payment_id=?", (payment_id,))
        return self.cursor.fetchone()

    def add_payment(self, booking_id, amount, payment_method, status='Pending'):
        self.cursor.execute(
            "INSERT INTO Payment (booking_id, amount, payment_method, status) VALUES (?, ?, ?, ?)",
            (booking_id, amount, payment_method, status)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_payment_status(self, payment_id, status):
        self.cursor.execute("UPDATE Payment SET status=? WHERE payment_id=?", (status, payment_id))
        self.conn.commit()

    def delete_payment(self, payment_id):
        self.cursor.execute("DELETE FROM Payment WHERE payment_id=?", (payment_id,))
        self.conn.commit()

    def __del__(self):
        self.conn.close()
