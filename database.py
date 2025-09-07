import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "needcar.db"

def create_connection():
    conn = sqlite3.connect(DB_NAME,check_same_thread=False)
    conn.row_factory = sqlite3.Row  # so we can access rows like dicts
    return conn


def create_admin_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Admin (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def create_customer_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            license_number TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def create_car_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS car (
            car_id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            plate_number TEXT UNIQUE NOT NULL,
            seats INTEGER NOT NULL,
            rent_price_per_day REAL NOT NULL,
            availability_status TEXT CHECK(availability_status IN ('Available','Unavailable')) DEFAULT 'Available'
        )
    ''')
    conn.commit()
    conn.close()


def create_booking_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Booking (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status TEXT CHECK(status IN ('Pending','Confirmed','Cancelled','Completed')) DEFAULT 'Pending',
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY(car_id) REFERENCES car(car_id)
        )
    ''')
    conn.commit()
    conn.close()


def create_payment_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(''' 
         CREATE TABLE IF NOT EXISTS Payment (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            payment_method TEXT CHECK(payment_method IN ('Card','Cash','Online')) NOT NULL,
            status TEXT CHECK(status IN ('Paid','Pending','Failed')) DEFAULT 'Pending',
            FOREIGN KEY(booking_id) REFERENCES Booking(booking_id)          
        )
    ''')
    conn.commit()
    conn.close()


def create_report_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Report (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY(admin_id) REFERENCES Admin(admin_id)
        )
    ''')
    conn.commit()
    conn.close()


def insert_default_admin():
    conn = create_connection()
    cursor = conn.cursor()

    # Check if any admin exists
    cursor.execute("SELECT * FROM Admin LIMIT 1")
    admin = cursor.fetchone()

    if not admin:
        default_name = "System Admin"
        default_email = "admin@needcar.com"
        default_password = "admin123"  # CHANGE THIS in production!
        password_hash = generate_password_hash(default_password)

        cursor.execute('''
            INSERT INTO Admin (full_name, email, password_hash)
            VALUES (?, ?, ?)
        ''', (default_name, default_email, password_hash))

        conn.commit()
        print(f"✅ Default admin created -> Email: {default_email} | Password: {default_password}")
    else:
        print("ℹ️ Admin already exists, skipping default admin creation.")

    conn.close()

def create_system_settings_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SystemSettings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tax_fee REAL NOT NULL
        )
    ''')
    # Ensure one default row exists
    cursor.execute('SELECT COUNT(*) FROM SystemSettings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO SystemSettings (tax_fee) VALUES (?)', (10.0,))
    conn.commit()
    conn.close()


def setup_database():
    create_admin_table()
    create_customer_table()
    create_car_table()
    create_booking_table()
    create_payment_table()
    create_report_table()
    insert_default_admin()
    create_system_settings_table()
    print("Database setup complete.")


if __name__ == "__main__":
    setup_database()