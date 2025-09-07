# manage_customer.py
from database import create_connection

class CustomerManager:
    def __init__(self):
        self.conn = create_connection()

    def get_all_customers(self, search_query=None):
        """Retrieve all customers or filter by search query."""
        cursor = self.conn.cursor()
        if search_query:
            query = """
                SELECT * FROM customers
                WHERE full_name LIKE ? OR email LIKE ? OR phone LIKE ? OR license_number LIKE ?
            """
            like_query = f"%{search_query}%"
            cursor.execute(query, (like_query, like_query, like_query, like_query))
        else:
            cursor.execute("SELECT * FROM customers")
        return cursor.fetchall()

    def get_customer_by_id(self, customer_id):
        """Fetch a single customer by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
        return cursor.fetchone()

    def add_customer(self, full_name, email, phone, address, license_number, password_hash):
        """Insert a new customer into the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO customers (full_name, email, phone, address, license_number, password_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (full_name, email, phone, address, license_number, password_hash))
        self.conn.commit()
        return cursor.lastrowid

    def update_customer(self, customer_id, full_name, email, phone, address, license_number):
        """Update customer details (excluding password)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE customers
            SET full_name = ?, email = ?, phone = ?, address = ?, license_number = ?
            WHERE customer_id = ?
        """, (full_name, email, phone, address, license_number, customer_id))
        self.conn.commit()
        return cursor.rowcount

    def delete_customer(self, customer_id):
        """Delete a customer by ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
        self.conn.commit()
        return cursor.rowcount

    def __del__(self):
        """Close DB connection when object is destroyed."""
        self.conn.close()
