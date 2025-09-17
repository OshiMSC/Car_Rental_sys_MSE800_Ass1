# backup_db.py
import sqlite3
from db_config import DB_PATH

BACKUP_FILE = "backup_data.sql"

def backup_database():
    conn = sqlite3.connect(DB_PATH)
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        for line in conn.iterdump():
            f.write("%s\n" % line)
    conn.close()
    print(f"✅ Backup complete! Data saved to {BACKUP_FILE}")

if __name__ == "__main__":
    backup_database()
