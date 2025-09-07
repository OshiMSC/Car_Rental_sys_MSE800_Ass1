from database import create_connection

class Booking:
    def __init__(self):
        self.conn = create_connection()
        self.cursor = self.conn.cursor()

    def get_all_bookings(self, search_query=None):
        """Retrieve all bookings, optionally filtered by search query."""
        sql = '''
            SELECT b.booking_id, c.full_name AS customer, car.model AS car, 
                   b.start_date, b.end_date, b.status
            FROM Booking b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN car car ON b.car_id = car.car_id
        '''
        params = ()
        if search_query:
            sql += '''
                WHERE c.full_name LIKE ? OR car.model LIKE ? OR b.start_date LIKE ? OR b.end_date LIKE ?
            '''
            params = (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')
        
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def get_booking(self, booking_id):
        """Retrieve a single booking by ID."""
        self.cursor.execute("SELECT * FROM Booking WHERE booking_id=?", (booking_id,))
        return self.cursor.fetchone()

    def add_booking(self, customer_id, car_id, start_date, end_date, status='Pending'):
        """Add a new booking."""
        self.cursor.execute(
            "INSERT INTO Booking (customer_id, car_id, start_date, end_date, status) VALUES (?, ?, ?, ?, ?)",
            (customer_id, car_id, start_date, end_date, status)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_booking(self, booking_id, status):
        """Update the status of a booking."""
        self.cursor.execute("UPDATE Booking SET status=? WHERE booking_id=?", (status, booking_id))
        self.conn.commit()

    def delete_booking(self, booking_id):
        """Delete a booking by ID."""
        self.cursor.execute("DELETE FROM Booking WHERE booking_id=?", (booking_id,))
        self.conn.commit()

    def __del__(self):
        self.conn.close()
