# This page act as a connector between database and all interfaces which manage CRUD operations related to cars:
from database import create_connection

class CarManager:
    def __init__(self):
        self.conn = create_connection()

    def get_all_cars(self, search_query=None):
        """Retrieve all cars or filter by search query."""
        cursor = self.conn.cursor()
        if search_query:
            query = """
                SELECT * FROM car
                WHERE make LIKE ? OR model LIKE ? OR plate_number LIKE ?
            """
            like_query = f"%{search_query}%"
            cursor.execute(query, (like_query, like_query, like_query))
        else:
            cursor.execute("SELECT * FROM car")
        return cursor.fetchall()

    def add_car(self, make, model, year, plate_number, seats, daily_rate, availability=True):
        """Insert a new car into the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO car (make, model, year, plate_number, seats, rent_price_per_day, availability_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            make, model, year, plate_number, seats, daily_rate,
            "Available" if availability else "Unavailable"
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_car(self, car_id, make, model, year, plate_number, seats, daily_rate, availability=True):
        """Update car details."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE car
            SET make = ?, model = ?, year = ?, plate_number = ?, seats = ?, rent_price_per_day = ?, availability_status = ?
            WHERE car_id = ?
        """, (
            make, model, year, plate_number, seats, daily_rate,
            "Available" if availability else "Unavailable", car_id
        ))
        self.conn.commit()
        return cursor.rowcount

    def delete_car(self, car_id):
        """Delete a car by ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM car WHERE car_id = ?", (car_id,))
        self.conn.commit()
        return cursor.rowcount

    def get_car_by_id(self, car_id):
        """Fetch a single car by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM car WHERE car_id = ?", (car_id,))
        return cursor.fetchone()
    
    def get_available_cars(self, search_query=None):
        """Retrieve only cars with 'Available' status, optionally filtered by search query."""
        cursor = self.conn.cursor()
        if search_query:
            query = """
                SELECT * FROM car
                WHERE availability_status = 'Available' AND 
                      (make LIKE ? OR model LIKE ? OR plate_number LIKE ?)
            """
            like_query = f"%{search_query}%"
            cursor.execute(query, (like_query, like_query, like_query))
        else:
            cursor.execute("SELECT * FROM car WHERE availability_status = 'Available'")
        
        # Return as list of dictionaries for easier template rendering
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_available_favorites(self):
        """Retrieve only available favorite cars of the each customer filtered by search query."""
        query = """
            SELECT c.car_id, c.make, c.model
            FROM car c
            JOIN FavoriteCars f ON f.car_id = c.car_id
            WHERE f.customer_id = ? AND c.is_available = 1
        """
        self.cursor.execute(query, (self.customer_id,))
        return self.cursor.fetchall()

    def __del__(self):
        """Close database connection when object is destroyed."""
        self.conn.close()
