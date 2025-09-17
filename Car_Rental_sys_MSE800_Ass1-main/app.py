#Main file which manages all routes and connections between UI,Controllers and Database
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3, os

# Managers
from Controllers.car_manager import CarManager
from Controllers.manage_customer import CustomerManager
from Controllers.manage_bookings import BookingManager
from Controllers.manage_payments import PaymentManager
from Controllers.manage_reports import ReportManager
from Controllers.manage_settings import AdminManager
from database import create_connection

app = Flask(__name__, template_folder="webtemplates")
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads/payments"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ------------------ Utilities ------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS



BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "needcar.db")

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

# ------------------ Login Decorators ------------------
def admin_required(func):
    def wrapper(*args, **kwargs):
        if 'admin_id' not in session:
            flash("Admin login required", "warning")
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def customer_required(func):
    def wrapper(*args, **kwargs):
        if 'customer_id' not in session:
            flash("Customer login required", "warning")
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# ------------------ Managers ------------------
car_manager = CarManager()
customer_manager = CustomerManager()
booking_manager = BookingManager()
payment_manager = PaymentManager()
report_manager = ReportManager()
admin_manager = AdminManager()
customer_booking_manager = BookingManager()

# ------------------ User Registration and Login  ------------------
@app.route('/')
def homepage(): return render_template('homepage.html')

@app.route('/register', methods=['GET','POST'])
def customer_register():
    if request.method=='POST':
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        license_no = request.form['license']
        password = generate_password_hash(request.form['password'])
        try:
            with create_connection() as conn:
                conn.execute(
                    "INSERT INTO customers (full_name,email,phone,address,license_number,password_hash) VALUES (?,?,?,?,?,?)",
                    (fullname,email,phone,address,license_no,password)
                )
            flash("Registration successful! Login now.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already exists!", "danger")
    return render_template('RegisterUser.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        with create_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 🔹 Check if email exists in either customers or admins
            cursor.execute("SELECT * FROM customers WHERE email=?", (email,))
            customer = cursor.fetchone()

            cursor.execute("SELECT * FROM Admin WHERE email=?", (email,))
            admin = cursor.fetchone()

            if role == "customer":
                if not customer and admin:
                    flash("This email belongs to an Admin account. Please select Admin role.", "warning")
                elif not customer:
                    flash("No customer found with that email.", "danger")
                elif not check_password_hash(customer['password_hash'], password):
                    flash("Incorrect password for customer account.", "danger")
                else:
                    session['customer_id'] = customer['customer_id']
                    session['customer_name'] = customer['full_name']
                    flash(f"Welcome {customer['full_name']}!", "success")
                    return redirect(url_for('customer_dashboard'))

            elif role == "admin":
                if not admin and customer:
                    flash("This email belongs to a Customer account. Please select Customer role.", "warning")
                elif not admin:
                    flash("No admin found with that email.", "danger")
                elif not check_password_hash(admin['password_hash'], password):
                    flash("Incorrect password for admin account.", "danger")
                else:
                    session['admin_id'] = admin['admin_id']
                    session['admin_name'] = admin['full_name']
                    flash(f"Welcome Admin {admin['full_name']}!", "success")
                    return redirect(url_for('admin_dashboard'))

            else:
                flash("Invalid role selected. Please choose Customer or Admin.", "danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for('login'))



# ------------------------- ADMIN PROFILE -------------------------
@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_profile():
    admin_id = session['admin_id']

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')

        if full_name and email:
            admin_manager.update_profile(admin_id, full_name, email)
            flash("Profile updated successfully.", "success")
        else:
            flash("Full name and email cannot be empty.", "danger")

    admin = admin_manager.get_admin_by_id(admin_id)
    return render_template('admin/settings.html', admin=admin)

@app.route('/admin/change_password', methods=['POST'])
@admin_required
def change_admin_password():
    admin_id = session['admin_id']

    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not new_password or not confirm_password:
        flash("Password fields cannot be empty.", "danger")
        return redirect(url_for('admin_profile'))

    if new_password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for('admin_profile'))

    admin_manager.change_password(admin_id, new_password)
    flash("Password changed successfully.", "success")
    return redirect(url_for('admin_profile'))

#-------------------------- END ADMIN PROFILE ------------------------ 
# ------------------------- ADMIN DASHBOARD -------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash("Admin login required.", "warning")
        return redirect(url_for('login'))

    # Fetch stats
    total_cars = booking_manager.get_total_cars()
    total_customers = booking_manager.get_total_customers()
    total_bookings = len(booking_manager.get_all_bookings())
    total_revenue = payment_manager.get_total_confirmed_revenue()

    # Recent bookings and payments
    recent_bookings = booking_manager.get_recent_bookings(limit=10)
    recent_payments = payment_manager.get_recent_payments(limit=7)

    return render_template(
        'admin/admin_dashboard.html',
        name=session['admin_name'],
        total_cars=total_cars,
        total_customers=total_customers,
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        bookings=recent_bookings,
        recent_payments=recent_payments
    )

# ------------------------- END ADMIN DASHBOARD -------------------------
#---------------------- CAR DETAILS MANAGEMENT -------------------------
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
@admin_required
def edit_customer(customer_id):
    customer_manager = CustomerManager()

    full_name = request.form['full_name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    license_number = request.form['license_number']

    success, error = customer_manager.update_customer(
        customer_id, full_name, email, phone, address, license_number
    )

    if success:
        flash("Customer updated successfully!", "success")
    else:
        flash(f"Error updating customer: {error}", "danger")

    return redirect(url_for('manage_customers', edit_id=customer_id))


# DELETE CUSTOMER ---------------------

@app.route('/admin/delete_customer/<int:customer_id>', methods=['POST'])
@admin_required
def delete_customer(customer_id):
    customer_manager.delete_customer(customer_id)
    flash("Customer deleted successfully!", "success")
    return redirect(url_for('manage_customers'))

# ---------------------- END CUSTOMER MANAGEMENT -------------------------

#---------------------------------MANAGE BOOKINGS ------------------------


# HANDLE BOOKINGS OF EACH CUSTOMER ---------------------
@app.route('/customer/bookings', methods=['GET'])
@customer_required
def customer_bookings():
    customer_id = session["customer_id"]

    # Get customer bookings
    booked_cars = booking_manager.get_customer_bookings(customer_id)

    # Search and date filters
    search_query = request.args.get('q')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Get available cars using singleton manager method
    available_cars = booking_manager.get_available_cars(
        search_query=search_query,
        start_date=start_date,
        end_date=end_date
    )

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
@customer_required
def add_favorite():
    customer_id = session["customer_id"]
    car_id = request.form.get("car_id")
    success, error = booking_manager.add_favorite_car(customer_id, car_id)
    if success:
        flash("Car added to favorites!", "success")
    else:
        flash(f"Error adding favorite: {error}", "danger")
    return redirect(request.referrer or url_for("customer_bookings"))

#GET ALL THE BOOKINGS OF EACH CAR ------------------------

@app.route('/api/car/<int:car_id>/bookings')
def get_car_bookings(car_id):
    bookings = booking_manager.get_car_bookings(car_id)

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
@customer_required
def car_calendar():
    cars = car_manager.get_all_cars()
    return render_template('customer/car_calendar.html', cars=cars)

#COST ESTIMATOR AND CAR COMPARISON TOOL-------------------------
@app.route('/customer/tools')
@customer_required
def customer_tools():
    cars = car_manager.get_all_cars()
    return render_template('customer/tools.html', cars=cars)

#GET THE DETAILS OF RETURENED CARS AND APPLY FINES

@app.route('/return_car/<int:booking_id>', methods=['POST'])
@admin_required
def return_car(booking_id):
    return_date_str = request.form['return_date']
    fine_amount = float(request.form['fine_amount'])

    success, error = booking_manager.return_car(booking_id, return_date_str, fine_amount)
    if success:
        flash(f"Car returned successfully! Fine: ${fine_amount}", "success")
    else:
        flash(f"Error returning car: {error}", "danger")

    return redirect(url_for('admin_manage_bookings'))

#INSERT NEW BOOKING FROM ADMIN VIEW------------------------
@app.route('/admin/add_booking', methods=['POST'])
@admin_required
def add_booking():

    customer_id = request.form['customer_id']
    car_id = request.form['car_id']
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    success, error = booking_manager.add_booking(customer_id, car_id, start_date, end_date)
    if success:
        flash("Booking added successfully!", "success")
    else:
        flash(f"Error adding booking: {error}", "danger")

    return redirect(url_for('admin_manage_bookings'))


# ---------------- Admin Routes ----------------

@app.route('/admin/manage_bookings', methods=['GET'])
@admin_required
def admin_manage_bookings():

    pending_requests = booking_manager.get_pending_bookings()
    confirmed_bookings = booking_manager.get_confirmed_bookings()
    completed_bookings = booking_manager.get_completed_bookings()
    available_cars = car_manager.get_available_cars()
    recent_payments = payment_manager.get_recent_payments(limit=10)

    return render_template(
        'admin/manage_bookings.html',
        pending_requests=pending_requests,
        available_cars=available_cars,
        confirmed_bookings=confirmed_bookings, 
        completed_bookings=completed_bookings,
        recent_payments=recent_payments
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

@app.route("/admin/car_calendar")
def admin_car_calendar():
    cars = CarManager().get_all_cars()  # fetch all cars for dropdown
    return render_template("admin/car_calendar.html", cars=cars)


#---------------END OF BOOKING MANAGEMENT --------------------------

#----------------PAYMENT MANAGEMENT -------------------------------
@app.route('/admin/payments')
def payments():
    search_query = request.args.get('q', '')
    payments = payment_manager.get_all_payments(search_query)
    return render_template('/admin/payments.html', payments=payments)

#UPDATE PAYMENT STATUS------------------------

@app.route('/admin/payments/update/<int:payment_id>', methods=['POST'])
def update_payment(payment_id):
    status = request.form['status']
    payment_manager.update_payment_status(payment_id, status)
    return redirect(url_for('payments'))

#DELETE PAYMENT RECORD ------------------------

@app.route('/admin/payments/delete/<int:payment_id>')
def delete_payment(payment_id):
    payment_manager.delete_payment(payment_id)
    return redirect(url_for('payments'))

#---------------- END OF PAYMENT MANAGEMENT -------------------------

#------------------REPORT MANAGEMENT ------------------------------

@app.route('/admin/reports')
@admin_required
def reports():
    

    # -------------------- Totals --------------------
    total_cars = report_manager.get_total_cars()
    total_customers = report_manager.get_total_customers()
    total_bookings = report_manager.get_total_bookings()
    total_revenue = report_manager.get_total_revenue()

    # -------------------- Date Filters --------------------
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    bookings_report = report_manager.get_bookings_report(from_date, to_date)
    payments_report = report_manager.get_payments_report(from_date, to_date)

    # -------------------- Revenue Breakdown --------------------
    daily_revenue = report_manager.get_daily_revenue()
    weekly_revenue = report_manager.get_weekly_revenue()
    monthly_revenue = report_manager.get_monthly_revenue()

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

@app.route('/customer/dashboard')
def customer_dashboard():
    if 'customer_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    customer_id = session['customer_id']
    search_query = request.args.get('q', '')

    # ---------------- Customer Info ----------------
    cm = CustomerManager()
    customer = cm.get_customer_by_id(customer_id)

    bm = BookingManager()  
    # ---------------- Customer Stats ----------------
    total_bookings = bm.get_total_bookings_for_customer(customer_id)
    upcoming_rentals = bm.get_upcoming_rentals_for_customer(customer_id)
    total_favorites = bm.get_total_favorites_for_customer(customer_id)

    # ---------------- Favorite Cars ----------------
    favorite_cars = bm.get_favorite_cars_for_customer(customer_id)
    favorite_notifications = bm.get_available_favorites_for_customer(customer_id)

    # ---------------- Available Cars & Bookings ----------------
    available_cars = bm.get_available_cars(search_query)
    bookings = bm.get_booking_history(customer_id)
    notifications = bm.get_notifications(customer_id)

    return render_template(
        '/customer/dashboard.html',
        name=session['customer_name'],
        customer=customer,
        available_cars=available_cars,
        bookings=bookings,
        notifications=notifications,
        total_bookings=total_bookings,
        upcoming_rentals=upcoming_rentals,
        total_favorites=total_favorites,
        favorite_cars=favorite_cars,
        favorite_notifications=favorite_notifications
    )


#------------------------ MANAGE CUSTOMER PAYMENTS------------------------------

payment_manager = PaymentManager(upload_folder="static/uploads/payments")

@app.route('/customer/payments')
def customer_payments():
    if 'customer_id' not in session:
        return redirect(url_for('login'))

    customer_id = session['customer_id']

    # Get customer payments
    payments = payment_manager.get_customer_payments(customer_id)

    # Get completed bookings with costs already calculated
    pending_bookings = booking_manager.get_pending_completed_bookings_for_customer(customer_id)

    return render_template(
        'customer/customer_payments.html',
        payments=payments,
        bookings=pending_bookings
    )


# HANDLE CUSTOMER BANK TRANSFER UPLOAD ------------------------------
@app.route('/customer/payments/upload', methods=['POST'])
def upload_payment():
    if 'customer_id' not in session:
        return redirect(url_for('login'))

    customer_id = session['customer_id']
    booking_id = request.form.get('booking_id')
    file = request.files.get('payment_proof')

    success, message = payment_manager.upload_payment(customer_id, booking_id, file)
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
        email = request.form.get("email")
        # Only update email
        customer_manager.update_customer(customer_id, email=email)
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


for rule in app.url_map.iter_rules():
    print(rule.endpoint, rule.rule)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
