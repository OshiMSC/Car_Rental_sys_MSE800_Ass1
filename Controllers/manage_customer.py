# manage_customer.py
from database import create_connection
from werkzeug.security import generate_password_hash
import sqlite3

class CustomerManager:
    """Singleton class to manage all customer-related database operations."""
    _instance = None   

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CustomerManager, cls).__new__(cls)
            cls._instance.__initialize()
        return cls._instance

    def __initialize(self):
        """Initialize database connection once (private)."""
        self.__conn = create_connection()
        self.__conn.row_factory = sqlite3.Row  # Ensures dict-like access for rows
        self.__cursor = self.__conn.cursor()

    def __execute(self, query, params=(), commit=False, fetchone=False, fetchall=False):
        """
        Private helper to execute queries safely and avoid duplicate code.
        """
        self.__cursor.execute(query, params)
        if commit:
            self.__conn.commit()
        if fetchone:
            return self.__cursor.fetchone()
        if fetchall:
            return self.__cursor.fetchall()
        return self.__cursor

    # ----------------- CRUD Methods -----------------

    def get_all_customers(self, search_query=None):
        """Retrieve all customers or filter by search query."""
        if search_query:
            query = """
                SELECT * FROM customers
                WHERE full_name LIKE ? OR email LIKE ? OR phone LIKE ? OR license_number LIKE ?
            """
            like_query = f"%{search_query}%"
            return self.__execute(query, (like_query, like_query, like_query, like_query), fetchall=True)
        return self.__execute("SELECT * FROM customers", fetchall=True)

    def add_customer(self, full_name, email, phone, address, license_number, password_hash):
        """Insert a new customer into the database."""
        query = """
            INSERT INTO customers (full_name, email, phone, address, license_number, password_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = self.__execute(query, (full_name, email, phone, address, license_number, password_hash), commit=True)
        return cursor.lastrowid

    def update_customerprofile(self, customer_id, email):
        """Update only the email of a customer."""
        query = "UPDATE customers SET email = ? WHERE customer_id = ?"
        cursor = self.__execute(query, (email, customer_id), commit=True)
        return cursor.rowcount
    
    def update_customer(self, customer_id, full_name, email, phone, address, license_number):
        try:
            self.cursor.execute('''
                UPDATE customers 
                SET full_name=?, email=?, phone=?, address=?, license_number=?
                WHERE customer_id=?
            ''', (full_name, email, phone, address, license_number, customer_id))
            self.conn.commit()
            return True, None
        except sqlite3.IntegrityError:
            return False, "Email already exists. Please use a different one."
        except Exception as e:
            return False, str(e)

    def delete_customer(self, customer_id):
        """Delete a customer by ID."""
        query = "DELETE FROM customers WHERE customer_id = ?"
        cursor = self.__execute(query, (customer_id,), commit=True)
        return cursor.rowcount

    def get_customer_by_id(self, customer_id):
        """Fetch a single customer's full profile details."""
        query = """
            SELECT customer_id, full_name, email, phone, address, license_number, password_hash
            FROM customers WHERE customer_id = ?
        """
        return self.__execute(query, (customer_id,), fetchone=True)

    def change_password(self, customer_id, new_password):
        """Change customer's password securely."""
        password_hash = generate_password_hash(new_password)
        query = "UPDATE customers SET password_hash=? WHERE customer_id=?"
        cursor = self.__execute(query, (password_hash, customer_id), commit=True)
        return cursor.rowcount

    def __del__(self):
        """Ensure DB connection closes only once."""
        if hasattr(self, "_CustomerManager__conn"):
            self.__conn.close()
