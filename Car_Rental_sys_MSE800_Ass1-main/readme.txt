🚗 Car Rental System (Flask Web App)

📖 Description

This is a web-based Car Rental System developed using Python (Flask).
It enables customers to view available cars, make bookings, manage favorites, and track rentals.
Admins can manage cars, approve/reject bookings, and analyze revenue.
The project uses SQLite as a lightweight database and Bootstrap + FullCalendar for a clean, responsive UI.

✨ Features
    👤 Customer Features
    🚘 View available cars with details
    📅 Book cars with start & end dates
    📝 See booking history & upcoming rentals
    ❤️ Save favorite cars + get availability notifications
    🔍 Filter cars with search
    🗓️ Calendar view for car availability

🛠️ Admin Features

    ➕ Add, ✏️ update, ❌ delete cars
    ✅ Approve / ❌ reject bookings
    📊 View revenue stats (daily, weekly, monthly)
    👥 Manage customers & bookings
    🗓️ Calendar monitoring for all cars

🔒 Additional Features

    🔐 Secure login with hashed passwords (Werkzeug)
    ⚡ Flash messages for user feedback
    📱 Mobile-responsive UI with Bootstrap
    📅 Car availability visualization (FullCalendar)

🛠️ Technologies Used

    Backend: Python 3.13, Flask
    Database: SQLite
    Frontend: HTML, CSS, Bootstrap 5
    Calendar: FullCalendar 6
    Security: Werkzeug password hashing
    Other: JavaScript (for dynamic interactions)

⚙️ Setup Instructions

    1️⃣ Clone the repository

    - git clone <your-repo-url>
    - cd <project-folder>

    3️⃣ Install dependencies
    Ensure you have Python 3.9+ installed.
        - pip install Flask==2.3.5
        - pip install Werkzeug==2.3.7

    4️⃣ Initialize the Database

        - python database.py

    5️⃣ Run the Application

        - python app.py

    6️⃣ Open in Browser
        👉 http://127.0.0.1:5000/

🗄️ Database Backup & Restore (⚠️ Important)

When you download the project from GitHub, the database (needcar.db) may sometimes be empty.
To avoid issues, I included backup & restore scripts:

    ▶️ Restore Data (if DB is empty)
        - python restore_db.py

✅ This will re-insert the sample cars, customers, and bookings from a backup file into needcar.db.
So the system will work immediately with test data.

    💾 Backup Current Data 
        - python backup_db.py

✅ This will dump all your current database content into a backup text file.
Useful if you want to preserve data before sharing or resetting.

📝 Notes

    - sqlite3 and datetime are part of Python’s standard library → no installation required.
    - Bootstrap & FullCalendar are included via CDN → no extra setup needed.

User Credentials:
    ADMIN:
        - User Name: admin@needcar.com
        - Password: admin123
    USER 01 : 
        - User Name: oshadeedasanayake@gmail.com
        - Password: oshi@123
    NEW USER :
        - User Name: user@gmail.com
        - Password: user@123
