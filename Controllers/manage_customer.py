# This page act as a connector between database and all interfaces which manage CRUD operations related to customer mostly by admin:
from database import create_connection
from werkzeug.security import generate_password_hash

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


    def add_customer(self, full_name, email, phone, address, license_number, password_hash):
        """Insert a new customer into the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO customers (full_name, email, phone, address, license_number, password_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (full_name, email, phone, address, license_number, password_hash))
        self.conn.commit()
        return cursor.lastrowid

    def update_customer(self, customer_id, email):
        """Update only the email of a customer."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE customers
            SET email = ?
            WHERE customer_id = ?
        """, (email, customer_id))
        self.conn.commit()
        return cursor.rowcount


    def delete_customer(self, customer_id):
        """Delete a customer by ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
        self.conn.commit()
        return cursor.rowcount
    
    def get_customer_by_id(self, customer_id):
        """Fetch a single customer's full profile details."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT customer_id, full_name, email, phone, address, license_number, password_hash
            FROM customers WHERE customer_id = ?
        """, (customer_id,))
        return cursor.fetchone()


    def change_password(self, customer_id, new_password):
        """Change customer's password securely."""
        cursor = self.conn.cursor()
        password_hash = generate_password_hash(new_password)
        cursor.execute("""
            UPDATE customers SET password_hash=? WHERE customer_id=?
        """, (password_hash, customer_id))
        self.conn.commit()
        return cursor.rowcount

    def __del__(self):
        self.conn.close()

