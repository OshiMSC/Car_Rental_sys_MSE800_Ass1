# This page act as a main handler of the system which handle all routes of the user interfaces and send data to the relevant interfaces.
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import g
from datetime import datetime
from Controllers.car_manager import CarManager
from database import create_connection
from Controllers.manage_customer import CustomerManager
from Controllers.manage_bookings import BookingManager
from Controllers.manage_payments import Payment
from Controllers.manage_reports import ReportManager
from Controllers.manage_settings import SettingsManager
import os
from werkzeug.utils import secure_filename
from flask import jsonify

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__, template_folder="webtemplates")
app.secret_key = "supersecretkey" 

UPLOAD_FOLDER = "static/uploads/payments" # All the payment invoices done by customer is stored in this folder
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect("needcar.db")
    return g.db


# ------------------------- HOME PAGE-------------------------
@app.route('/')
def homepage():
    return render_template('homepage.html')


# ------------------------- REGISTER A NEW CUSTOMER -------------------------
@app.route('/register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        full_name = request.form['fullname']  
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        license_number = request.form['license']  
        password = request.form['password']

        password_hash = generate_password_hash(password)

        conn = create_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO customers (full_name, email, phone, address, license_number, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (full_name, email, phone, address, license_number, password_hash)
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already registered. Try logging in.", "danger")
        finally:
            conn.close()

    return render_template('RegisterUser.html')


# ------------------------- USER LOGIN MANAGEMENT -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  

        conn = create_connection()
        cursor = conn.cursor()

        if role == 'customer':
            cursor.execute("SELECT * FROM customers WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user["password_hash"], password):
                session['customer_id'] = user["customer_id"]
                session['customer_name'] = user["full_name"]
                flash(f"Welcome back, {user['full_name']}!", "success")
                return redirect(url_for('customer_dashboard'))
            else:
                flash("Invalid customer email or password.", "danger")

        elif role == 'admin':
            cursor.execute("SELECT * FROM Admin WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user["password_hash"], password):
                session['admin_id'] = user["admin_id"]
                session['admin_name'] = user["full_name"]
                flash(f"Welcome, Admin {user['full_name']}!", "success")
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid admin email or password.", "danger")

    return render_template('login.html')

# ------------------------- ADMIN PROFILE -------------------------
@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_profile():
    # Ensure admin is logged in
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    admin_id = session['admin_id']
    conn = create_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')

        if full_name and email:
            cursor.execute("""
                UPDATE Admin SET full_name=?, email=? WHERE admin_id=?
            """, (full_name, email, admin_id))
            conn.commit()
            flash("Profile updated successfully.", "success")
        else:
            flash("Full name and email cannot be empty.", "danger")

    cursor.execute("SELECT * FROM Admin WHERE admin_id=?", (admin_id,))
    admin = cursor.fetchone()
    conn.close()

    return render_template('admin/settings.html', admin=admin)

@app.route('/admin/change_password', methods=['POST'])
def change_admin_password():
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    admin_id = session['admin_id']
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not new_password or not confirm_password:
        flash("Password fields cannot be empty.", "danger")
        return redirect(url_for('admin_profile'))

    if new_password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for('admin_profile'))

    hashed_password = generate_password_hash(new_password)

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Admin SET password_hash=? WHERE admin_id=?", (hashed_password, admin_id))
    conn.commit()
    conn.close()

    flash("Password changed successfully.", "success")
    return redirect(url_for('admin_profile'))

#-------------------------- END ADMIN PROFILE ------------------------ 
# ------------------------- ADMIN DASHBOARD -------------------------
manager = BookingManager()
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash("Admin login required.", "warning")
        return redirect(url_for('login'))
    
    total_cars = manager.get_total_cars()
    total_customers = manager.get_total_customers()
    total_bookings = len(manager.get_all_bookings())
    recent_bookings = manager.get_recent_bookings(limit=5)

    payment_manager = Payment()
    total_revenue = payment_manager.get_total_confirmed_revenue()

    # SHOW RECENT PAYMENTS
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.payment_id, p.booking_id, p.amount, p.payment_date, p.status,
               c.make || ' ' || c.model AS car_name
        FROM Payment p
        JOIN Booking b ON p.booking_id = b.booking_id
        JOIN car c ON b.car_id = c.car_id
        ORDER BY p.payment_date DESC
        LIMIT 7
    """)
    recent_payments = cursor.fetchall()
    conn.close()

    conn = create_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # DATA FOR STAT CARDS
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM car) AS total_cars,
            (SELECT COUNT(*) FROM customers) AS total_customers,
            (SELECT COUNT(*) FROM Booking) AS total_bookings,
            (SELECT SUM(amount) FROM Payment WHERE status='Paid') AS total_revenue
    """)
    stats = cursor.fetchone()
    total_cars = stats["total_cars"] or 0
    total_customers = stats["total_customers"] or 0
    total_bookings = stats["total_bookings"] or 0
    total_revenue = stats["total_revenue"] or 0.0

    # SHOW RECENT BOOKINGS
    cursor.execute("""
        SELECT 
            b.booking_id,
            b.start_date,
            b.end_date,
            b.status AS booking_status,
            c.full_name AS customer_name,
            ca.make || ' ' || ca.model AS car_name,
            p.payment_id,
            p.status AS payment_status,
            p.amount
        FROM Booking b
        JOIN customers c ON b.customer_id = c.customer_id
        JOIN car ca ON b.car_id = ca.car_id
        LEFT JOIN Payment p ON b.booking_id = p.booking_id
        ORDER BY b.booking_id DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    bookings = [dict(row) for row in rows]

    print(f"DEBUG: {len(bookings)} recent bookings fetched for admin dashboard")

    conn.close()

    return render_template(
        'admin/admin_dashboard.html',
        name=session['admin_name'],
        total_cars=total_cars,
        total_customers=total_customers,
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        bookings=recent_bookings,
        recent_payments=recent_payments)

@app.route('/admin/payments/update/<int:payment_id>', methods=['POST'])
def update_payment_dashboard(payment_id):
    if 'admin_id' not in session:
        flash("Admin login required.", "warning")
        return redirect(url_for('login'))
    status = request.form['status']
    payment_manager = Payment()
    payment_manager.update_payment_status(payment_id, status)
    flash(f"Payment #{payment_id} updated successfully.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/payments/delete/<int:payment_id>')
def delete_payment_dashboard(payment_id):
    if 'admin_id' not in session:
        flash("Admin login required.", "warning")
        return redirect(url_for('login'))
    payment_manager = Payment()
    payment_manager.delete_payment(payment_id)
    flash(f"Payment #{payment_id} deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))

# ------------------------- END ADMIN DASHBOARD -------------------------
#---------------------- CAR DETAILS MANAGEMENT -------------------------
car_manager = CarManager()
@app.route('/admin/manage_cars', methods=['GET'])
def manage_cars():
    search_query = request.args.get('q')
    cars = car_manager.get_all_cars(search_query)

    car_list = [
        {
            "car_id": car["car_id"],
            "make": car["make"],
            "model": car["model"],
            "year": car["year"],
            "plate": car["plate_number"],
            "seats": car["seats"],
            "daily_rate": car["rent_price_per_day"],
            "available": (car["availability_status"] == "Available")
        }
        for car in cars
    ]

    return render_template('/admin/manage_cars.html', cars=car_list)

# ADD CAR ------------------------------------
@app.route('/admin/add_car', methods=['POST'])
def add_car():
    make = request.form.get('make')
    model = request.form.get('model')
    year = int(request.form.get('year'))
    plate_number = request.form.get('plate')
    seats = int(request.form.get('seats'))
    daily_rate = float(request.form.get('rent_price_per_day'))
    availability = 'available' in request.form  
    print("DEBUG: availability checkbox value =", availability)
    car_manager.add_car(make, model, year, plate_number, seats, daily_rate, availability)
    flash("Car added successfully!", "success")
    return redirect(url_for('manage_cars'))

# EDIT CAR--------------------------------------

@app.route('/admin/edit_car/<int:car_id>', methods=['POST'])
def edit_car(car_id):
    make = request.form.get('make')
    model = request.form.get('model')
    year = int(request.form.get('year'))
    plate_number = request.form.get('plate')
    seats = int(request.form.get('seats'))
    daily_rate = float(request.form.get('rent_price_per_day'))
    availability = 'available' in request.form

    car_manager.update_car(car_id, make, model, year, plate_number, seats, daily_rate, availability)
    flash("Car updated successfully!", "success")
    return redirect(url_for('manage_cars'))

# DELETE CAR---------------------

@app.route('/admin/delete_car/<int:car_id>', methods=['POST'])
def delete_car(car_id):
    car_manager.delete_car(car_id)
    flash("Car deleted successfully!", "success")
    return redirect(url_for('manage_cars'))

#---------------------- END OF CAR DETAILS MANAGEMENT -------------------------

#--------------------------------MANAGE CUSTOMER DETAILS ----------------------------
customer_manager = CustomerManager()

@app.route('/admin/manage_customers', methods=['GET'])
def manage_customers():
    search_query = request.args.get('q')
    customers = customer_manager.get_all_customers(search_query)
    return render_template('/admin/manage_customers.html', customers=customers)

# ADD CUSTOMER ---------------------

@app.route('/admin/add_customer', methods=['POST'])
def add_customer():
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    license_number = request.form.get('license_number')
    raw_password = request.form.get('password_hash')  # (already hashed before inserting)
    password_hash = generate_password_hash(raw_password)
    customer_manager.add_customer(full_name, email, phone, address, license_number, password_hash)
    flash("Customer added successfully!", "success")
    return redirect(url_for('manage_customers'))

# EDIT CUSTOMER ---------------------

@app.route('/admin/edit_customer/<int:customer_id>', methods=['POST'])
def edit_customer(customer_id):
    full_name = request.form['full_name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    license_number = request.form['license_number']

    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE customers 
            SET full_name=?, email=?, phone=?, address=?, license_number=?
            WHERE customer_id=?
        ''', (full_name, email, phone, address, license_number, customer_id))
        conn.commit()
        conn.close()
        flash("Customer updated successfully!", "success")
    except sqlite3.IntegrityError:
        flash("Email already exists. Please use a different one.", "danger")
    except Exception as e:
        flash(f" Error updating customer: {e}","danger")
    return redirect(url_for('manage_customers',edit_id=customer_id))

# DELETE CUSTOMER ---------------------

@app.route('/admin/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    customer_manager.delete_customer(customer_id)
    flash("Customer deleted successfully!", "success")
    return redirect(url_for('manage_customers'))

# ---------------------- END CUSTOMER MANAGEMENT -------------------------

#---------------------------------MANAGE BOOKINGS ------------------------

booking_manager = BookingManager()

# HANDLE BOOKINGS OF EACH CUSTOMER ---------------------
@app.route('/customer/bookings', methods=['GET'])
def customer_bookings():
    if "customer_id" not in session:
        return redirect(url_for("login"))

    customer_id = session["customer_id"]

    conn = create_connection()
    cursor = conn.cursor()

    # Get all bookings for this customer including Pending
    cursor.execute("""
        SELECT b.booking_id, c.make || ' ' || c.model AS car_name,
               b.start_date, b.end_date, b.status
        FROM Booking b
        JOIN car c ON b.car_id = c.car_id
        WHERE b.customer_id = ? AND b.status IN ('Confirmed', 'Pending')
        ORDER BY 
            CASE b.status
                WHEN 'Pending' THEN 1
                WHEN 'Confirmed' THEN 2
                ELSE 3
            END,
            b.start_date DESC
    """, (customer_id,))
    booked_cars = cursor.fetchall()

    conn.close()

    search_query = request.args.get('q')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    available_cars = booking_manager.get_available_cars(
        search_query=search_query,
        start_date=start_date,
        end_date=end_date
    )
    
    booked_cars = booking_manager.get_customer_bookings(customer_id)
    return render_template(
        'customer/customer_bookings.html',
        available_cars=available_cars,
        booked_cars=booked_cars
    )

# MAKE A BOOKING ---------------------
@app.route('/customer/book_car', methods=['POST'])
def book_car():
   
    customer_id = session.get('customer_id')  
    if not customer_id:
        flash("You must be logged in to book a car.", "danger")
        return redirect(url_for('login'))
    car_id = request.form.get('car_id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        if end_dt < start_dt:
            flash("End date cannot be before start date.", "danger")
            return redirect(url_for('customer_bookings'))
    except Exception:
        flash("Invalid date format.", "danger")
        return redirect(url_for('customer_bookings'))

    # Check if car is already booked in that period
    existing_bookings = customer_booking_manager.get_all_bookings(car_id)
    for b in existing_bookings:
        b_start = datetime.strptime(b['start_date'], '%Y-%m-%d').date()
        b_end = datetime.strptime(b['end_date'], '%Y-%m-%d').date()
        if not (end_dt < b_start or start_dt > b_end) and b['status'] in ('Pending', 'Confirmed'):
            flash("Sorry, this car is already booked for the selected dates.", "danger")
            return redirect(url_for('customer_bookings'))

   
    booking_id = customer_booking_manager.create_booking(customer_id, car_id, start_date, end_date)
    flash(f"Booking request #{booking_id} submitted successfully!", "success")
    return redirect(url_for('customer_bookings'))

# ADD CUSTOMER FAVOURIE CARS ---------------------

@app.route("/customer/add_favorite", methods=["POST"])
def add_favorite():
    if "customer_id" not in session:
        return redirect(url_for("login"))

    customer_id = session["customer_id"]
    car_id = request.form.get("car_id")

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT OR IGNORE INTO FavoriteCars (customer_id, car_id) VALUES (?, ?)",
            (customer_id, car_id)
        )
        conn.commit()
        flash("Car added to favorites!", "success")
    except Exception as e:
        flash(f"Error adding favorite: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(request.referrer or url_for("customer_bookings"))

#GET ALL THE BOOKINGS OF EACH CAR ------------------------

@app.route('/api/car/<int:car_id>/bookings')
def get_car_bookings(car_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT start_date, end_date
        FROM booking
        WHERE car_id = ?
    """, (car_id,))
    bookings = cursor.fetchall()
    conn.close()

    events = []
    for b in bookings:
        events.append({
            "title": "Booked",
            "start": b["start_date"],
            "end": b["end_date"],
            "display": "background", 
            "color": "#f1b2b2"
        })
    return jsonify(events)

#MAINTAIN CAR AVAILABILITY IN A CALENDAR ------------------------

@app.route('/customer/car_calendar')
def car_calendar():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT car_id, make, model FROM Car")
    cars = cursor.fetchall()
    conn.close()
    return render_template('customer/car_calendar.html', cars=cars)


# ---------------- Admin Routes ----------------

@app.route('/admin/manage_bookings', methods=['GET'])
def admin_manage_bookings():
    # Search query from frontend
    search_query = request.args.get('q')

    pending_requests = booking_manager.get_pending_bookings()
    available_cars = booking_manager.get_available_cars_admin(search_query=search_query)

    return render_template(
        'admin/manage_bookings.html',
        pending_requests=pending_requests,
        available_cars=available_cars
    )

@app.route('/admin/update_booking/<int:booking_id>', methods=['POST'])
def update_booking(booking_id):
    new_status = request.form.get('status')
    if new_status not in ('Pending', 'Confirmed', 'Cancelled', 'Completed'):
        flash("Invalid status.", "danger")
    else:
        success = booking_manager.update_booking_status(booking_id, new_status)
        if success:
            flash(f"Booking #{booking_id} updated to {new_status}.", "success")
        else:
            flash(f"Booking #{booking_id} not found.", "danger")
    return redirect(url_for('admin_manage_bookings'))

@app.route('/admin/delete_booking/<int:booking_id>', methods=['POST'])
def delete_booking(booking_id):
    booking_manager.delete_booking(booking_id)
    flash(f"Booking #{booking_id} deleted.", "success")
    return redirect(url_for('manage_bookings'))



#---------------END OF BOOKING MANAGEMENT --------------------------

#----------------PAYMENT MANAGEMENT -------------------------------
@app.route('/admin/payments')
def payments():
    search_query = request.args.get('q', '')
    payment_manager = Payment()
    payments = payment_manager.get_all_payments(search_query)
    return render_template('/admin/payments.html', payments=payments)

#UPDATE PAYMENT STATUS------------------------

@app.route('/admin/payments/update/<int:payment_id>', methods=['POST'])
def update_payment(payment_id):
    status = request.form['status']
    payment_manager = Payment()
    payment_manager.update_payment_status(payment_id, status)
    return redirect(url_for('payments'))

#DELETE PAYMENT RECORD ------------------------

@app.route('/admin/payments/delete/<int:payment_id>')
def delete_payment(payment_id):
    payment_manager = Payment()
    payment_manager.delete_payment(payment_id)
    return redirect(url_for('payments'))

#---------------- END OF PAYMENT MANAGEMENT -------------------------

#------------------REPORT MANAGEMENT ------------------------------

@app.route('/admin/reports')
def reports():
    conn = create_connection()
    cursor = conn.cursor()

    # -------------------- Total counts --------------------
    cursor.execute("SELECT COUNT(*) AS total FROM car")
    total_cars = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM customers")
    total_customers = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM booking")
    total_bookings = cursor.fetchone()['total']

    cursor.execute("SELECT IFNULL(SUM(amount), 0) AS total FROM Payment WHERE status='Paid'")
    total_revenue = cursor.fetchone()['total']

    # -------------------- Filters --------------------
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    bookings_query = """
        SELECT b.booking_id, c.full_name AS customer, car.make || ' ' || car.model AS car_name,
               b.start_date, b.end_date, b.status
        FROM booking b
        JOIN customers c ON b.customer_id = c.customer_id
        JOIN car ON b.car_id = car.car_id
    """

    payments_query = """
        SELECT p.payment_id, c.full_name AS customer, p.amount, p.payment_date, p.status
        FROM Payment p
        JOIN booking b ON p.booking_id = b.booking_id
        JOIN customers c ON b.customer_id = c.customer_id
    """

    params = ()
    if from_date and to_date:
        bookings_query += " WHERE b.start_date BETWEEN ? AND ?"
        payments_query += " WHERE p.payment_date BETWEEN ? AND ?"
        params = (from_date, to_date)

    bookings_query += " ORDER BY b.start_date DESC"
    payments_query += " ORDER BY p.payment_date DESC"

    cursor.execute(bookings_query, params)
    bookings_report = cursor.fetchall()

    cursor.execute(payments_query, params)
    payments_report = cursor.fetchall()

    # -------------------- Revenue Breakdown --------------------
    # DAILY REVENUE-----------------------
    cursor.execute("""
        SELECT date(payment_date) AS day, IFNULL(SUM(amount),0) AS total
        FROM Payment
        WHERE status='Paid'
        GROUP BY day
        ORDER BY day ASC
    """)
    daily_revenue = cursor.fetchall()

    # WEEKLY REVENUE ---------------------------
    cursor.execute("""
        SELECT strftime('%Y-%W', payment_date) AS week, IFNULL(SUM(amount),0) AS total
        FROM Payment
        WHERE status='Paid'
        GROUP BY week
        ORDER BY week ASC
    """)
    weekly_revenue = cursor.fetchall()

    # MONTHLY REVENUE --------------------------
    cursor.execute("""
        SELECT strftime('%Y-%m', payment_date) AS month, IFNULL(SUM(amount),0) AS total
        FROM Payment
        WHERE status='Paid'
        GROUP BY month
        ORDER BY month ASC
    """)
    monthly_revenue = cursor.fetchall()

    conn.close()

    return render_template(
        'admin/reports.html',
        total_cars=total_cars,
        total_customers=total_customers,
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        bookings_report=bookings_report,
        payments_report=payments_report,
        daily_revenue=daily_revenue,
        weekly_revenue=weekly_revenue,
        monthly_revenue=monthly_revenue
    )

#-----------------------END OF THE PAYEMENT MANAGEMENT --------------------------
# ------------------------- CUSTOMER DASHBOARD -------------------------
customer_booking_manager = BookingManager()
@app.route('/customer/dashboard')
def customer_dashboard():
    if 'customer_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))
    customer_id = session.get('customer_id', 1)  
    search_query = request.args.get('q', '')

    cm = CustomerManager()
    customer = cm.get_customer_by_id(customer_id)
    customer_id = session["customer_id"]
    conn = create_connection()
    cursor = conn.cursor()
    
# TOTAL BOOKINGS OF THE CUSTOMER---------------------------------
    cursor.execute("SELECT COUNT(*) FROM booking WHERE customer_id = ?", (customer_id,))
    total_bookings = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM booking
        WHERE customer_id = ? AND start_date >= ?
    """, (customer_id, datetime.today().date()))
    upcoming_rentals = cursor.fetchone()[0]
    
# FAVOURITE CARS OF THE CUSTOMER
    cursor.execute("SELECT COUNT(*) FROM FavoriteCars WHERE customer_id = ?", (customer_id,))
    total_favorites = cursor.fetchone()[0]

    cursor.execute("""
        SELECT c.car_id, c.make, c.model, c.year, c.seats, c.rent_price_per_day
        FROM FavoriteCars f
        JOIN car c ON f.car_id = c.car_id
        WHERE f.customer_id = ?
        ORDER BY f.created_at DESC
    """, (customer_id,))
    favorite_cars = cursor.fetchall()

    cursor.execute("""
        SELECT c.* FROM FavoriteCars f
        JOIN Car c ON c.car_id = f.car_id
        WHERE f.customer_id=? AND c.availability_status='Available'
    """, (customer_id,))
    favorite_notifications = cursor.fetchall()

    conn.close()


    cars = BookingManager().get_available_cars(search_query)
    bookings = BookingManager().get_booking_history(customer_id)
    notifications = BookingManager().get_notifications(customer_id)
    return render_template('/customer/dashboard.html', name=session['customer_name'],customer=customer,available_cars=cars,bookings=bookings,notifications=notifications,total_bookings=total_bookings,
        favorite_cars = favorite_cars ,upcoming_rentals=upcoming_rentals,total_favorites =total_favorites,favorite_notifications=favorite_notifications)

#------------------- END OF THE CUSTOMER DASHBOARD -----------------------------
#------------------------ MANAGE CUSTOMER PAYMENTS------------------------------

payment_manager = Payment(upload_folder="static/uploads/payments")


@app.route('/customer/payments')
def customer_payments():
    if 'customer_id' not in session:
        return redirect(url_for('login'))

    customer_id = session['customer_id']
    payments = payment_manager.get_customer_payments(customer_id)

    # Fetch bookings with total cost calculation
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            B.booking_id,
            C.make || ' ' || C.model AS car_name,
            C.rent_price_per_day,
            (julianday(B.end_date) - julianday(B.start_date)) * C.rent_price_per_day AS total_cost
        FROM Booking B
        JOIN car C ON B.car_id = C.car_id
        WHERE B.customer_id=? 
          AND B.booking_id NOT IN (SELECT booking_id FROM Payment)
        ORDER BY B.start_date ASC
    """, (customer_id,))
    bookings = cursor.fetchall()
    conn.close()
    return render_template('customer/customer_payments.html', payments=payments, bookings=bookings)

# HANDLE CUSTOMER BANK TRANSFER UPLOAD ------------------------------
payment = Payment()  
@app.route('/customer/payments/upload', methods=['POST'])
def upload_payment():
    if 'customer_id' not in session:
        return redirect(url_for('login'))

    customer_id = session['customer_id']
    booking_id = request.form.get('booking_id')
    file = request.files.get('payment_proof')

    success, message = payment.upload_payment(customer_id, booking_id, file)
    flash(message, "success" if success else "danger")
    return redirect(url_for('customer_payments'))

#------------------------- END OF CUSTOMER PAYMENTS ----------------------------

#------------------------- MANAGE CUSTOMER PROFILE-----------------------------
@app.route("/customer/profile", methods=["GET", "POST"])
def customer_profile():

    if "customer_id" not in session:
        flash("Please log in to access your profile", "warning")
        return redirect(url_for("login"))

    customer_id = session["customer_id"]
    customer = customer_manager.get_customer_by_id(customer_id)

    if request.method == "POST":
       
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        license_number = request.form.get("license_number")

        customer_manager.update_customer(
            customer_id, full_name, email, phone, address, license_number
        )
        flash("Profile updated successfully!", "success")
        return redirect(url_for("customer_profile"))

    return render_template("customer/customer_profile.html", customer=customer)

# --- Change Password Route -----------------
@app.route("/customer/change-password", methods=["POST"])
def change_customer_password():
    if "customer_id" not in session:
        flash("Please log in to change your password", "warning")
        return redirect(url_for("customer_login"))

    customer_id = session["customer_id"]
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if new_password != confirm_password:
        flash("Passwords do not match!", "danger")
        return redirect(url_for("customer_profile"))

    customer_manager.change_password(customer_id, new_password)
    flash("Password updated successfully!", "success")
    return redirect(url_for("customer_profile"))
#-------------------------END CUSTOMER PROFILE -------------------------------

# ------------------------- LOGOUT FUNCTION------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

for rule in app.url_map.iter_rules():
    print(rule.endpoint, rule.rule)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
