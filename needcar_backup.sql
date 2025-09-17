PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE Admin (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
INSERT INTO "Admin" VALUES(1,'System Admin','admin@needcar.com','scrypt:32768:8:1$2LbAnMZMNnQpxkt9$8476424044edf8118a7f8b7a30e440bb97c11c805199152483c7c128a93df8cd66ab751ce41a2548d74b5bb3dc4be00e5ce79a317d3e64ecf9dd3b81b5b09205');
CREATE TABLE Booking (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status TEXT CHECK(status IN ('Pending','Confirmed','Cancelled','Completed')) DEFAULT 'Pending',
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY(car_id) REFERENCES car(car_id)
        );
INSERT INTO "Booking" VALUES(2,1,7,'2025-09-17','2025-09-18','Cancelled');
INSERT INTO "Booking" VALUES(3,1,6,'2025-09-17','2025-09-20','Cancelled');
INSERT INTO "Booking" VALUES(6,3,4,'2025-09-11','2025-09-13','Cancelled');
INSERT INTO "Booking" VALUES(11,3,8,'2025-10-09','2025-10-11','Pending');
CREATE TABLE CompletedBookings (
            completed_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            return_date DATE NOT NULL,
            fine_amount REAL DEFAULT 0,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY(car_id) REFERENCES car(car_id)
        );
INSERT INTO "CompletedBookings" VALUES(1,1,1,4,'2025-09-11','2025-09-13','2025-09-10',0.0);
INSERT INTO "CompletedBookings" VALUES(2,4,3,5,'2025-09-23','2025-09-25','2025-09-10',0.0);
INSERT INTO "CompletedBookings" VALUES(3,5,3,6,'2025-09-26','2025-09-27','2025-09-29',40.0);
INSERT INTO "CompletedBookings" VALUES(4,8,3,4,'2025-09-29','2025-09-30','2025-09-30',0.0);
INSERT INTO "CompletedBookings" VALUES(5,9,3,4,'2025-09-29','2025-09-30','2025-10-02',40.0);
INSERT INTO "CompletedBookings" VALUES(6,10,3,5,'2025-10-01','2025-10-03','2025-10-04',20.0);
INSERT INTO "CompletedBookings" VALUES(7,7,3,3,'2025-09-17','2025-09-19','2025-09-12',0.0);
CREATE TABLE FavoriteCars (
            favorite_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(customer_id, car_id) -- Avoid duplicate favorites
        );
INSERT INTO "FavoriteCars" VALUES(1,3,2,'2025-09-09 11:59:14');
CREATE TABLE Favorites (
            favorite_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            UNIQUE(customer_id, car_id),
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY(car_id) REFERENCES car(car_id)
        );
CREATE TABLE Notifications (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        );
CREATE TABLE Payment (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            payment_method TEXT CHECK(payment_method IN ('Card','Cash','Online')) NOT NULL,
            status TEXT CHECK(status IN ('Paid','Pending','Failed')) DEFAULT 'Pending',
            FOREIGN KEY(booking_id) REFERENCES Booking(booking_id)          
        );
INSERT INTO "Payment" VALUES(1,4,100.0,'2025-09-08 13:05:48','Online','Paid');
INSERT INTO "Payment" VALUES(2,7,500.0,'2025-09-09 10:42:23','Online','Paid');
INSERT INTO "Payment" VALUES(3,5,540.0,'2025-09-16 08:54:10','Online','Pending');
CREATE TABLE Ratings (
            rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            UNIQUE(customer_id, car_id),
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY(car_id) REFERENCES car(car_id)
        );
CREATE TABLE Report (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY(admin_id) REFERENCES Admin(admin_id)
        );
INSERT INTO "Report" VALUES(1,1,'Bookings & Payments Report','2025-09-06 00:57:38','Generated report from start to now');
INSERT INTO "Report" VALUES(2,1,'Bookings & Payments Report','2025-09-06 00:57:43','Generated report from start to now');
INSERT INTO "Report" VALUES(3,1,'Bookings & Payments Report','2025-09-06 00:58:51','Generated report from start to now');
INSERT INTO "Report" VALUES(4,1,'Bookings & Payments Report','2025-09-06 06:00:54','Generated report from start to now');
INSERT INTO "Report" VALUES(5,1,'Bookings & Payments Report','2025-09-06 06:01:10','Generated report from start to now');
INSERT INTO "Report" VALUES(6,1,'Bookings & Payments Report','2025-09-06 09:12:00','Generated report from start to now');
INSERT INTO "Report" VALUES(7,1,'Bookings & Payments Report','2025-09-08 09:15:31','Generated report from start to now');
INSERT INTO "Report" VALUES(8,1,'Bookings & Payments Report','2025-09-08 09:42:13','Generated report from start to now');
INSERT INTO "Report" VALUES(9,1,'Bookings & Payments Report','2025-09-09 11:03:50','Generated report from start to now');
INSERT INTO "Report" VALUES(10,1,'Bookings & Payments Report','2025-09-09 11:04:24','Generated report from start to now');
INSERT INTO "Report" VALUES(11,1,'Bookings & Payments Report','2025-09-09 11:04:37','Generated report from start to now');
CREATE TABLE SystemSettings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tax_fee REAL NOT NULL
        );
INSERT INTO "SystemSettings" VALUES(1,10.0);
CREATE TABLE car (
            car_id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            plate_number TEXT UNIQUE NOT NULL,
            seats INTEGER NOT NULL,
            rent_price_per_day REAL NOT NULL,
            availability_status TEXT CHECK(availability_status IN ('Available','Unavailable')) DEFAULT 'Available'
        );
INSERT INTO "car" VALUES(2,'Toyota','Corolla',2021,'ABC123',4,150.0,'Available');
INSERT INTO "car" VALUES(3,'Honda','Civic',2024,'XYZ789',4,250.0,'Unavailable');
INSERT INTO "car" VALUES(4,'Mazda','CX-5',2019,'MZD-456',4,250.0,'Unavailable');
INSERT INTO "car" VALUES(5,'Nissan','X-Trail',2008,'NST-654',5,100.0,'Unavailable');
INSERT INTO "car" VALUES(6,'Hyundai','Elantra',2009,'HYN-987',4,250.0,'Unavailable');
INSERT INTO "car" VALUES(7,'Suzuki','Swift',2010,'SZK-753',4,200.0,'Available');
INSERT INTO "car" VALUES(8,'Tesla','Model 3',2001,'TSL-159',4,300.0,'Unavailable');
INSERT INTO "car" VALUES(9,'Kia','Sportage',2021,'KIA-7467',4,200.0,'Available');
CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            license_number TEXT NOT NULL,
            password_hash TEXT NOT NULL
        );
INSERT INTO "customers" VALUES(1,'Arebhy Ghaneshan','arebhy123@gmail.com','+640225016789','No:3/20,Domett Ave,Epsom','DL0001','arebhy123');
INSERT INTO "customers" VALUES(2,'Nirmala Pathirana','nirmala@gmail.com','0225012415','Residence Balmoral , 2 Dunbar Road','HJ 5678','admin123');
INSERT INTO "customers" VALUES(3,'Oshadee Kaushalya','oshadeedasanayake@gmail.com','+64225012439','Residence Balmoral , 2 Dunbar Road','KJ 8047','scrypt:32768:8:1$EPcx4oFi5PCINZJ3$169845c11bc02fe8ceb2cace7f4ee8a62518352f8d4f4ac969e5f09f2d65f88b4bab6a8216cd1eff936beaae232802ef2bb320187295a31b25c5a5f66a5b5afd');
INSERT INTO "customers" VALUES(4,'Alice Johnson','alice.johnson@example.com','+64-210123456','123 Queen Street, Auckland','DL123456','scrypt:32768:8:1$rKRsY25l5jhKQIhk$1456d8f9229b75d79eef62270295f5fd5fdeae54cc637ab0bd9f7419a8f50d034f3c617506c91987bf1f4afb31490d34323f686aa941c7e20a5d3fcc8fb0ebb8');
INSERT INTO "customers" VALUES(5,'Charlie Lee','charlie.lee@example.com','+64-220987654','78 Victoria Ave, Christchurch','DL789654','scrypt:32768:8:1$XnS5PSR2MX1xsvrL$723b645dc58021c3987de9ca4d5ba0685ff77250b10d7b6b89bcd24f62eb5fdd7cd85d1c49c30e13b7c22d9d75de67486d1338b3ed354389f166f288f61a07d3');
INSERT INTO "customers" VALUES(6,'Ethan Brown','ethan.brown@example.com','+64-227654321','6 Cuba Street, Wellington','DL456987','scrypt:32768:8:1$UHPBhufYtRDOtOt7$97bfc14147ce8310b7e7e555ec42dd295ec0a76db508b20c62ce22b59e2f25511e850c9b0cb06be1cb8beae32da85b8e754696b48be8e9d0045b72c773a637b8');
INSERT INTO "customers" VALUES(7,'George Clark','george.clark@example.com','+64-226666666','89 Broadway, Newmarket','DL147258','scrypt:32768:8:1$IWAAezpevllgm3UC$a453aaf92189bb7483949237524ebc1406d22d459d3720a434669303a4603b8bd9ac186103e8a26669ed479280583597f720b4a9dade50868f76094ba3a616a7');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('Admin',1);
INSERT INTO "sqlite_sequence" VALUES('customers',7);
INSERT INTO "sqlite_sequence" VALUES('car',9);
INSERT INTO "sqlite_sequence" VALUES('Report',11);
INSERT INTO "sqlite_sequence" VALUES('SystemSettings',1);
INSERT INTO "sqlite_sequence" VALUES('Booking',11);
INSERT INTO "sqlite_sequence" VALUES('Payment',3);
INSERT INTO "sqlite_sequence" VALUES('FavoriteCars',1);
INSERT INTO "sqlite_sequence" VALUES('CompletedBookings',7);
COMMIT;
