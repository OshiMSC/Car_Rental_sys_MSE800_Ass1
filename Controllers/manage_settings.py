from database import create_connection
from werkzeug.security import check_password_hash, generate_password_hash

from database import create_connection
import sqlite3
from werkzeug.security import generate_password_hash

class AdminManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AdminManager, cls).__new__(cls)
            cls._instance.__initialize()
        return cls._instance

    def __initialize(self):
        self.conn = create_connection()
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    # Get admin profile by ID
    def get_admin_by_id(self, admin_id):
        self.cursor.execute("SELECT * FROM Admin WHERE admin_id=?", (admin_id,))
        return self.cursor.fetchone()

    # Update admin profile
    def update_profile(self, admin_id, full_name, email):
        self.cursor.execute(
            "UPDATE Admin SET full_name=?, email=? WHERE admin_id=?",
            (full_name, email, admin_id)
        )
        self.conn.commit()

    # Change admin password
    def change_password(self, admin_id, new_password):
        hashed_password = generate_password_hash(new_password)
        self.cursor.execute(
            "UPDATE Admin SET password_hash=? WHERE admin_id=?",
            (hashed_password, admin_id)
        )
        self.conn.commit()
