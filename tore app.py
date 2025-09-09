
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash[m
from flask import g[m
from car_manager import CarManager[m
# settings_manager.py
from database import create_connection[m
from manage_customer import CustomerManager[m
from manage_bookings import Booking[m
from manage_payments import Payment[m
from manage_reports import ReportManager[m
from werkzeug.security import check_password_hash, generate_password_hash[m

app = Flask(__name__, template_folder="webtemplates")[m
app.secret_key = "supersecretkey"  # CHANGE THIS[m
 [m
[31m-def get_db():[m
[31m-    if 'db' not in g:[m
[31m-        g.db = sqlite3.connect("needcar.db")[m
[31m-    return g.db[m
[31m-[m
[31m-[m
[31m-# ------------------------- HOME -------------------------[m
[31m-@app.route('/')[m
[31m-def homepage():[m
[31m-    return render_template('homepage.html')[m
[31m-[m
[31m-[m
[31m-# ------------------------- CUSTOMER REGISTER -------------------------[m
[31m-@app.route('/register', methods=['GET', 'POST'])[m
[31m-def customer_register():[m
[31m-    if request.method == 'POST':[m
[31m-        full_name = request.form['fullname']  # match RegisterUser.html[m
[31m-        email = request.form['email'][m
[31m-        phone = request.form['phone'][m
[31m-        address = request.form['address'][m
[31m-        license_number = request.form['license']  # match RegisterUser.html[m
[31m-        password = request.form['password'][m
[31m-[m
[31m-        password_hash = generate_password_hash(password)[m
[31m-[m
[31m-        conn = create_connection()[m
[31m-        cursor = conn.cursor()[m
[31m-[m
[31m-        try:[m
[31m-            cursor.execute([m
[31m-                "INSERT INTO customers (full_name, email, phone, address, license_number, password_hash) VALUES (?, ?, ?, ?, ?, ?)",[m
[31m-                (full_name, email, phone, address, license_number, password_hash)[m
[31m-            )[m
[31m-            conn.commit()[m
[31m-            flash("Registration successful! Please log in.", "success")[m
[31m-            return redirect(url_for('login'))[m
[31m-        except sqlite3.IntegrityError:[m
[31m-            flash("Email already registered. Try logging in.", "danger")[m
[31m-        finally:[m
[31m-            conn.close()[m
[31m-[m
[31m-    return render_template('RegisterUser.html')[m
[31m-[m
[31m-[m
[31m-# ------------------------- COMBINED LOGIN (Admin + Customer) -------------------------[m
[31m-@app.route('/login', methods=['GET', 'POST'])[m
[31m-def login():[m
[31m-    if request.method == 'POST':[m
[31m-        email = request.form['email'][m
[31m-        password = request.form['password'][m
[31m-        role = request.form['role']  # match login.html[m
[31m-[m
[31m-        conn = create_connection()[m
[31m-        cursor = conn.cursor()[m
[31m-[m
[31m-        if role == 'customer':[m
[31m-            cursor.execute("SELECT * FROM customers WHERE email = ?", (email,))[m
[31m-            user = cursor.fetchone()[m
[31m-            conn.close()[m
[31m-[m
[31m-            if user and check_password_hash(user["password_hash"], password):[m
[31m-                session['customer_id'] = user["customer_id"][m
[31m-                session['customer_name'] = user["full_name"][m
[31m-                flash(f"Welcome back, {user['full_name']}!", "success")[m
[31m-                return redirect(url_for('customer_dashboard'))[m
[31m-            else:[m
[31m-                flash("Invalid customer email or password.", "danger")[m
[31m-[m
[31m-        elif role == 'admin':[m
[31m-            cursor.execute("SELECT * FROM Admin WHERE email = ?", (email,))[m
[31m-            user = cursor.fetchone()[m
[31m-            conn.close()[m
[31m-[m
[31m-            if user and check_password_hash(user["password_hash"], password):[m
[31m-                session['admin_id'] = user["admin_id"][m
[31m-                session['admin_name'] = user["full_name"][m
[31m-                flash(f"Welcome, Admin {user['full_name']}!", "success")[m
[31m-                return redirect(url_for('admin_dashboard'))[m
[31m-            else:[m
[31m-                flash("Invalid admin email or password.", "danger")[m
[31m-[m
[31m-    return render_template('login.html')[m
[31m-[m
[31m-[m
[31m-# ------------------------- CUSTOMER DASHBOARD -------------------------[m
[31m-@app.route('/customer/dashboard')[m
[31m-def customer_dashboard():[m
[31m-    if 'customer_id' not in session:[m
[31m-        flash("Please log in first.", "warning")[m
[31m-        return redirect(url_for('login'))[m
[31m-    return render_template('customer/dashboard.html', name=session['customer_name'])[m
[31m-[m
[31m-[m
[31m-# ------------------------- ADMIN DASHBOARD -------------------------[m
[31m-# ------------------------- ADMIN DASHBOARD -------------------------[m
[31m-@app.route('/admin/dashboard')[m
[31m-def admin_dashboard():[m
[31m-    if 'admin_id' not in session:[m
[31m-        flash("Admin login required.", "warning")[m
[31m-        return redirect(url_for('login'))[m
[31m-    [m
[31m-    car_manager = CarManager()[m
[31m-    customer_manager = CustomerManager()[m
[31m-    booking_manager = Booking()[m
[31m-    payment_manager = Payment()[m
[31m-[m
[31m-    # Quick stats[m
[31m-    total_cars = len(car_manager.get_all_cars())[m
[31m-    total_customers = len(customer_manager.get_all_customers())[m
[31m-    total_bookings = len(booking_manager.get_all_bookings())[m
[31m-    [m
[31m-    # Total revenue (sum of all paid payments)[m
[31m-    conn = create_connection()[m
[31m-    cursor = conn.cursor()[m
[31m-    [m
[31m-    cursor.execute("""[m
[31m-        SELECT[m
[31m-            (SELECT COUNT(*) FROM car) AS total_cars,[m
[31m-            (SELECT COUNT(*) FROM customers) AS total_customers,[m
[31m-            (SELECT COUNT(*) FROM Booking) AS total_bookings,[m
[31m-            (SELECT SUM(amount) FROM Payment WHERE status='Paid') AS total_revenue[m
[31m-    """)[m
[31m-    stats = cursor.fetchone()[m
[31m-    total_cars = stats[0] or 0[m
[31m-    total_customers = stats[1] or 0[m
[31m-    total_bookings = stats[2] or 0[m
[31m-    total_revenue = stats[3] or 0.0[m
[31m-[m
[31m-    # Fetch all bookings with customer and car info[m
[31m-    cursor.execute("""[m
[31m-        SELECT [m
[31m-            b.booking_id, b.start_date, b.end_date, b.status AS booking_status,[m
[31m-            c.full_name AS customer_name,[m
[31m-            ca.make || ' ' || ca.model AS car_name,[m
[31m-            p.payment_id, p.status AS payment_status, p.amount[m
[31m-        FROM Booking b[m
[31m-        JOIN customers c ON b.customer_id = c.customer_id[m
[31m-        JOIN car ca ON b.car_id = ca.car_id[m
[31m-        LEFT JOIN Payment p ON b.booking_id = p.booking_id[m
[31m-        ORDER BY b.booking_id DESC[m
[31m-     """)[m
[31m-    bookings = [dict([m
[31m-        booking_id=row[0],[m
[31m-        start_date=row[1],[m
[31m-        end_date=row[2],[m
[31m-        booking_status=row[3],[m
[31m-        customer=row[4],[m
[31m-        car=row[5],[m
[31m-        payment_id=row[6],[m
[31m-        payment_status=row[7] or 'Pending',[m
[31m-        amount=row[8] or 0.0[m
[31m-    ) for row in cursor.fetchall()][m
[31m-[m
[31m-    conn.close()[m
[31m-[m
[31m-    return render_template([m
[31m-        'admin/admin_dashboard.html',[m
[31m-        name=session['admin_name'],[m
[31m-        total_cars=total_cars,[m
[31m-        total_customers=total_customers,[m
[31m-        total_bookings=total_bookings,[m
[31m-        total_revenue=total_revenue,[m
[31m-    