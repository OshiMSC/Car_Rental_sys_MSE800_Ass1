import sqlite3

# Connect to your database
conn = sqlite3.connect("needcar.db")
cursor = conn.cursor()

# Insert missing customer with customer_id = 1
cursor.execute("""
INSERT INTO customers (customer_id, full_name, email, phone, address, license_number, password_hash)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    1,
    "Arebhy Ghaneshan",
    "arebhy123@gmail.com",
    "+640225016789",
    "No:3/20,Domett Ave,Epsom",
    "DL0001",
    "arebhy123" 
))


conn.commit()
conn.close()

print("Customer with ID 1 inserted successfully!")

conn.close()
