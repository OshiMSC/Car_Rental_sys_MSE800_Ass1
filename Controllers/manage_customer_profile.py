# customer_manager.py
from database import create_connection
from werkzeug.security import generate_password_hash

class CustomerManager:
    def __init__(self):
        self.conn = create_connection()

    def get_customer_by_id(self, customer_id):
        """Fetch a single customer's full profile details."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT customer_id, full_name, email, phone, address, license_number, created_at
    FROM customers WHERE customer_id = ?
        """, (customer_id,))
        return cursor.fetchone()

    def update_customer_profile(self, customer_id, full_name, email, phone, address, license_number):
        """Update customer's profile details (excluding password)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE customers
            SET full_name=?, email=?, phone=?, address=?, license_number=?
            WHERE customer_id=?
        """, (full_name, email, phone, address, license_number, customer_id))
        self.conn.commit()
        return cursor.rowcount

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
