# restore_db.py
import sqlite3
from db_config import DB_PATH

BACKUP_FILE = "backup_data.sql"

def restore_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing tables before restoring
    cursor.executescript("""
        PRAGMA foreign_keys = OFF;
        BEGIN TRANSACTION;
    """)
    conn.commit()

    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        sql = f.read()
        cursor.executescript(sql)

    conn.commit()
    conn.close()
    print(f"Restore complete! Data loaded from {BACKUP_FILE}")

if __name__ == "__main__":
    restore_database()
