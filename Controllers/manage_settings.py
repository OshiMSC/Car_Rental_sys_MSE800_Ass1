# This page act as a connector between database and all interfaces which manage CRUD operations related to manage Admin profile:
from database import create_connection
from werkzeug.security import check_password_hash, generate_password_hash

class SettingsManager:
    def __init__(self):
        pass

    def get_settings(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SystemSettings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tax_fee REAL NOT NULL
            )
        """)

        cursor.execute("SELECT email FROM Admin LIMIT 1")
        admin = cursor.fetchone()
        email = admin['email'] if admin else ''

        cursor.execute("SELECT tax_fee FROM SystemSettings LIMIT 1")
        tax_row = cursor.fetchone()
        tax_fee = tax_row[0] if tax_row else 0.0

        conn.close()
        return {"email": email, "tax": tax_fee}

    def verify_current_password(self, current_password):
        """Checks if current password matches stored admin password."""
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM Admin LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if not row:
            return False

        stored_hash = row['password_hash'] if 'password_hash' in row.keys() else row[0]
        return check_password_hash(stored_hash, current_password)

    def update_settings(self, email, password, tax):
        conn = create_connection()
        cursor = conn.cursor()

        # Update admin email & password (if provided)
        if password:
            password_hash = generate_password_hash(password)
            cursor.execute("UPDATE Admin SET email = ?, password_hash = ? WHERE admin_id = 1", (email, password_hash))
        else:
            cursor.execute("UPDATE Admin SET email = ? WHERE admin_id = 1", (email,))

        cursor.execute("SELECT COUNT(*) FROM SystemSettings")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO SystemSettings (tax_fee) VALUES (?)", (tax,))
        else:
            cursor.execute("UPDATE SystemSettings SET tax_fee = ? WHERE id = 1", (tax,))

        conn.commit()
        conn.close()
