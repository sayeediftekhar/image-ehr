import psycopg2
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", 5432),
            connect_timeout=10
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def create_tables():
    conn = get_db_connection()
    if not conn:
        logger.error("❌ Cannot connect to database")
        return False

    try:
        cursor = conn.cursor()

        # Create clinics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clinics (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address TEXT,
                phone VARCHAR(20),
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create users table with location tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20),
                role VARCHAR(50) NOT NULL,
                clinic_id INTEGER REFERENCES clinics(id),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login_at TIMESTAMP,
                last_login_ip VARCHAR(50),
                last_login_country VARCHAR(100),
                last_login_region VARCHAR(100),
                last_login_city VARCHAR(100),
                last_login_lat DECIMAL(10, 6),
                last_login_lon DECIMAL(10, 6),
                last_login_isp VARCHAR(255)
            )
        """)

        # Create patients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id SERIAL PRIMARY KEY,
                patient_id VARCHAR(50) UNIQUE NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                date_of_birth DATE,
                gender VARCHAR(10),
                phone VARCHAR(20),
                email VARCHAR(255),
                address TEXT,
                clinic_id INTEGER REFERENCES clinics(id),
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create login_logs table for detailed tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_logs (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(50),
                country VARCHAR(100),
                region VARCHAR(100),
                city VARCHAR(100),
                latitude DECIMAL(10, 6),
                longitude DECIMAL(10, 6),
                isp VARCHAR(255),
                success BOOLEAN NOT NULL,
                user_agent TEXT
            )
        """)

        conn.commit()
        logger.info("✅ Tables created successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def seed_data():
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Insert sample clinics
        clinics_data = [
            ("Downtown Medical Center", "123 Main St, City Center", "+1-555-0101", "info@downtown-med.com"),
            ("Westside Family Clinic", "456 West Ave, Westside", "+1-555-0102", "contact@westside-clinic.com"),
            ("Emergency Care Unit", "789 Emergency Blvd, Hospital District", "+1-555-0103", "emergency@ecu-hospital.com"),
            ("Pediatric Specialty Center", "321 Kids Lane, Family District", "+1-555-0104", "info@pediatric-center.com"),
            ("Senior Care Facility", "654 Elder St, Retirement Area", "+1-555-0105", "care@senior-facility.com")
        ]

        for clinic in clinics_data:
            cursor.execute("""
                INSERT INTO clinics (name, address, phone, email)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, clinic)

        # Insert sample users with email and phone
        users_data = [
            ("admin", "admin123", "System Administrator", "admin@imageehr.com", "+1-555-1001", "admin", None),
            ("manager1", "manager123", "John Smith", "john.smith@imageehr.com", "+1-555-1002", "manager", 1),
            ("doctor1", "doctor123", "Dr. Sarah Johnson", "sarah.johnson@imageehr.com", "+1-555-1003", "doctor", 1),
            ("nurse1", "nurse123", "Emily Davis", "emily.davis@imageehr.com", "+1-555-1004", "nurse", 1),
            ("staff1", "staff123", "Michael Brown", "michael.brown@imageehr.com", "+1-555-1005", "staff", 2),
            ("emoc1", "emoc123", "Emergency Coordinator", "emoc@imageehr.com", "+1-555-1006", "emoc_staff", 3),
            ("receptionist1", "recep123", "Lisa Wilson", "lisa.wilson@imageehr.com", "+1-555-1007", "receptionist", 1),
            ("manager2", "manager123", "David Miller", "david.miller@imageehr.com", "+1-555-1008", "manager", 2)
        ]

        for user in users_data:
            cursor.execute("""
                INSERT INTO users (username, password, full_name, email, phone, role, clinic_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """, user)

        # Insert sample patients
        patients_data = [
            ("P001", "Alice Johnson", "1985-03-15", "Female", "+1-555-2001", "alice.j@email.com", "123 Oak St", 1, 3),
            ("P002", "Bob Smith", "1978-07-22", "Male", "+1-555-2002", "bob.smith@email.com", "456 Pine Ave", 1, 3),
            ("P003", "Carol Davis", "1992-11-08", "Female", "+1-555-2003", "carol.d@email.com", "789 Elm Dr", 2, 5),
            ("P004", "David Wilson", "1965-05-30", "Male", "+1-555-2004", "david.w@email.com", "321 Maple Ln", 1, 3),
            ("P005", "Emma Brown", "2010-09-12", "Female", "+1-555-2005", "emma.parent@email.com", "654 Cedar St", 4, 3)
        ]

        for patient in patients_data:
            cursor.execute("""
                INSERT INTO patients (patient_id, full_name, date_of_birth, gender, phone, email, address, clinic_id, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (patient_id) DO NOTHING
            """, patient)

        conn.commit()
        logger.info("✅ Sample data inserted successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Error inserting sample data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    logger.info("🚀 Setting up IMAGE EHR Database...")

    if create_tables():
        logger.info("✅ Database tables created")
        if seed_data():
            logger.info("✅ Database setup completed successfully!")
            logger.info("📊 You can now test the connection with: python -c 'from main import test_db; print(test_db())'")
        else:
            logger.error("❌ Failed to seed data")
    else:
        logger.error("❌ Failed to create tables")

if __name__ == "__main__":
    main()