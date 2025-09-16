# car_manager.py
from database import create_connection

class CarManager:
    """Singleton class to manage all car-related database operations."""
    _instance = None  

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance of CarManager exists."""
        if cls._instance is None:
            cls._instance = super(CarManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the database connection only once."""
        if not hasattr(self, "_initialized"):
            self._conn = create_connection() 
            self._initialized = True

    def _get_cursor(self):
        """Private helper to create a new cursor safely."""
        return self._conn.cursor()

    # ---------------- CRUD Operations ----------------

    def get_all_cars(self, search_query=None):
        cursor = self._get_cursor()
        if search_query:
            query = """
                SELECT car_id, make, model,year,  plate_number, seats,rent_price_per_day, availability_status
                FROM car
                WHERE make LIKE ? OR model LIKE ?
            """
            like_query = f"%{search_query}%"
            cursor.execute(query, (like_query, like_query))
        else:
            cursor.execute("""
                SELECT car_id, make, model,year,plate_number,seats,rent_price_per_day, availability_status
                FROM car
            """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


    def add_car(self, make, model, year, plate_number, seats, daily_rate, availability=True):
        """Insert a new car into the database."""
        cursor = self._get_cursor()
        cursor.execute("""
            INSERT INTO car (make, model, year, plate_number, seats, rent_price_per_day, availability_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            make, model, year, plate_number, seats, daily_rate,
            "Available" if availability else "Unavailable"
        ))
        self._conn.commit()
        return cursor.lastrowid

    def update_car(self, car_id, make, model, year, plate_number, seats, daily_rate, availability=True):
        """Update car details."""
        cursor = self._get_cursor()
        cursor.execute("""
            UPDATE car
            SET make = ?, model = ?, year = ?, plate_number = ?, seats = ?, rent_price_per_day = ?, availability_status = ?
            WHERE car_id = ?
        """, (
            make, model, year, plate_number, seats, daily_rate,
            "Available" if availability else "Unavailable", car_id
        ))
        self._conn.commit()
        return cursor.rowcount

    def delete_car(self, car_id):
        """Delete a car by ID."""
        cursor = self._get_cursor()
        cursor.execute("DELETE FROM car WHERE car_id = ?", (car_id,))
        self._conn.commit()
        return cursor.rowcount

    def get_car_by_id(self, car_id):
        """Fetch a single car by ID."""
        cursor = self._get_cursor()
        cursor.execute("SELECT * FROM car WHERE car_id = ?", (car_id,))
        return cursor.fetchone()

    def get_available_cars(self, search_query=None):
        """Retrieve only cars with 'Available' status, optionally filtered by search query."""
        cursor = self._get_cursor()
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

    def get_available_favorites(self, customer_id):
        """Retrieve only available favorite cars for a given customer."""
        cursor = self._get_cursor()
        query = """
            SELECT c.car_id, c.make, c.model
            FROM car c
            JOIN FavoriteCars f ON f.car_id = c.car_id
            WHERE f.customer_id = ? AND c.availability_status = 'Available'
        """
        cursor.execute(query, (customer_id,))
        return cursor.fetchall()

    def __del__(self):
        """Close database connection when object is destroyed."""
        if hasattr(self, "_conn"):
            self._conn.close()
