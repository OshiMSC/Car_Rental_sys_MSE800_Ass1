Car Rental System (Flask Web App)
Description:
This is a web-based car rental system developed using Python and Flask. It enables customers to view available cars, make bookings, manage their favorites, and track upcoming rentals.
Admins have the capability to manage cars, approve or reject bookings, and view revenue statistics. The system utilizes SQLite for database management and incorporates Bootstrap for responsive design, 
along with FullCalendar for visualizing car availability.

1. Features
    1.1Customer Features

        - View available cars with detailed information.
        - Book cars with start and end dates.
        - See booking history and upcoming rentals.
        - Save favorite cars and receive notifications when they become available.
        - Filter cars using search functionality.
        - Calendar view to check car availability.

    1.2 Admin Features

    - Add, update, or delete cars.
    - Approve or reject booking requests.
    - View revenue statistics (daily, weekly, monthly) with charts.
    - Manage customers and their bookings.
    - Calendar view for monitoring car availability.

2. Additional Features

    - Secure login system using hashed passwords with Werkzeug.
    - Flash messages to notify users about operations.
    - Responsive and user-friendly UI with Bootstrap.
    - Integration with FullCalendar for visual availability management.

3. Technologies Used

    - Backend: Python 3.13, Flask
    - Database: SQLite
    - Frontend: HTML, CSS, Bootstrap 5
    - Calendar: FullCalendar 6
    - Password Security: Werkzeug
    - Others: JavaScript for dynamic interactions

4. Setup Instructions
 Initialize the Database
    - Run the database setup script to create all necessary tables:
            python database.py
    - Run the Application
            python app.py
    - Open in Browser
            http://127.0.0.1:5000/

            Setup Instructions

Clone the repository

git clone <your-repo-url>
cd <project-folder>


Create a Python virtual environment

python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows


Install dependencies

pip install -r requirements.txt


Run the application

python app.py


Access the application
Open your browser and go to: http://127.0.0.1:5000/

requirements.txt
Flask==2.3.5
Werkzeug==2.3.7


Notes:

sqlite3 and datetime are part of Python standard library; no installation needed.

Bootstrap and FullCalendar are included via CDN, so no local installation is required.
