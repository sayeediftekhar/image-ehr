import psycopg2
from dotenv import load_dotenv
import os
import sys

load_dotenv()

def setup_database():
    print("🚀 Starting IMAGE EHR Database Setup...")
    
    try:
        # Connect to database
        print("📡 Connecting to Neon database...")
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", 5432)
        )
        
        cursor = conn.cursor()
        print("✅ Database connection successful!")
        
        # Drop existing tables if they exist
        print("🗑️  Dropping existing tables...")
        cursor.execute("DROP TABLE IF EXISTS patients CASCADE")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE")
        cursor.execute("DROP TABLE IF EXISTS clinics CASCADE")
        print("✅ Existing tables dropped!")
        
        # Create clinics table
        print("🏢 Creating clinics table...")
        cursor.execute("""
            CREATE TABLE clinics (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                location VARCHAR(200),
                phone VARCHAR(20),
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create users table
        print("👤 Creating users table...")
        cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'manager', 'emoc_staff', 'counselor', 'staff')),
                clinic_id INTEGER REFERENCES clinics(id),
                email VARCHAR(100),
                phone VARCHAR(20),
                is_active BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create patients table
        print("👥 Creating patients table...")
        cursor.execute("""
            CREATE TABLE patients (
                id SERIAL PRIMARY KEY,
                patient_id VARCHAR(20) UNIQUE NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                age INTEGER CHECK (age > 0 AND age < 150),
                gender VARCHAR(10) CHECK (gender IN ('Male', 'Female', 'Other')),
                phone VARCHAR(20),
                address TEXT,
                emergency_contact VARCHAR(100),
                emergency_phone VARCHAR(20),
                clinic_id INTEGER REFERENCES clinics(id),
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample clinics
        print("🏥 Inserting sample clinics...")
        cursor.execute("""
            INSERT INTO clinics (name, location, phone, email) VALUES
            ('Nasirabad Clinic', 'Nasirabad, Chittagong', '01711111111', 'nasirabad@imageehr.com'),
            ('Jalalabad Clinic', 'Jalalabad, Sylhet', '01722222222', 'jalalabad@imageehr.com'),
            ('Dhanmondi Clinic', 'Dhanmondi, Dhaka', '01733333333', 'dhanmondi@imageehr.com')
        """)
        
        # Insert sample users
        print("👨‍⚕️ Inserting sample users...")
        cursor.execute("""
            INSERT INTO users (username, password, full_name, role, clinic_id, email, phone) VALUES
            ('admin', 'admin123', 'System Administrator', 'admin', NULL, 'admin@imageehr.com', '01700000000'),
            ('manager_cl1', 'manager123', 'Dr. Nasirabad Manager', 'manager', 1, 'manager.nasirabad@imageehr.com', '01711111111'),
            ('manager_cl2', 'manager123', 'Dr. Jalalabad Manager', 'manager', 2, 'manager.jalalabad@imageehr.com', '01722222222'),
            ('emoc_cl1', 'emoc123', 'Nasirabad EMOC Staff', 'emoc_staff', 1, 'emoc.nasirabad@imageehr.com', '01711111112'),
            ('emoc_cl2', 'emoc123', 'Jalalabad EMOC Staff', 'emoc_staff', 2, 'emoc.jalalabad@imageehr.com', '01722222223'),
            ('counselor_cl1', 'outdoor123', 'Nasirabad Counselor', 'counselor', 1, 'counselor.nasirabad@imageehr.com', '01711111113'),
            ('counselor_cl2', 'outdoor123', 'Jalalabad Counselor', 'counselor', 2, 'counselor.jalalabad@imageehr.com', '01722222224'),
            ('staff_cl1', 'staff123', 'Nasirabad Staff', 'staff', 1, 'staff.nasirabad@imageehr.com', '01711111114')
        """)
        
        # Insert sample patients
        print("🤱 Inserting sample patients...")
        cursor.execute("""
            INSERT INTO patients (patient_id, full_name, age, gender, phone, address, emergency_contact, emergency_phone, clinic_id, created_by) VALUES
            ('P001', 'Sarah Ahmed', 28, 'Female', '01712345678', 'Nasirabad, Chittagong', 'Husband - Ahmed Ali', '01712345679', 1, 2),
            ('P002', 'Fatima Khan', 32, 'Female', '01798765432', 'Jalalabad, Sylhet', 'Sister - Rashida Khan', '01798765433', 2, 3),
            ('P003', 'Rashida Begum', 25, 'Female', '01687654321', 'Nasirabad, Chittagong', 'Mother - Amina Begum', '01687654322', 1, 2),
            ('P004', 'Amina Khatun', 30, 'Female', '01576543210', 'Jalalabad, Sylhet', 'Husband - Karim Uddin', '01576543211', 2, 3),
            ('P005', 'Salma Akter', 26, 'Female', '01465432109', 'Nasirabad, Chittagong', 'Father - Abdul Rahman', '01465432110', 1, 4)
        """)
        
        # Create indexes for better performance
        print("📊 Creating database indexes...")
        cursor.execute("CREATE INDEX idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX idx_users_clinic_id ON users(clinic_id)")
        cursor.execute("CREATE INDEX idx_patients_patient_id ON patients(patient_id)")
        cursor.execute("CREATE INDEX idx_patients_clinic_id ON patients(clinic_id)")
        cursor.execute("CREATE INDEX idx_patients_created_at ON patients(created_at)")
        
        # Commit all changes
        conn.commit()
        print("💾 All changes committed!")
        
        # Verify setup
        print("\n📋 Verifying database setup...")
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM clinics")
        clinic_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        
        print(f"✅ Active Users: {user_count}")
        print(f"✅ Clinics: {clinic_count}")
        print(f"✅ Patients: {patient_count}")
        
        # Show sample data
        print("\n👥 Sample Users:")
        cursor.execute("""
            SELECT u.username, u.full_name, u.role, c.name as clinic_name 
            FROM users u 
            LEFT JOIN clinics c ON u.clinic_id = c.id 
            WHERE u.is_active = TRUE
            ORDER BY u.role, u.username
        """)
        users = cursor.fetchall()
        
        for user in users:
            clinic = user[3] if user[3] else "All Clinics"
            print(f"   • {user[0]} ({user[1]}) - {user[2]} at {clinic}")
        
        print("\n🏥 Sample Clinics:")
        cursor.execute("SELECT name, location, phone FROM clinics ORDER BY name")
        clinics = cursor.fetchall()
        
        for clinic in clinics:
            print(f"   • {clinic[0]} - {clinic[1]} ({clinic[2]})")
        
        conn.close()
        
        print("\n🎉 DATABASE SETUP COMPLETED SUCCESSFULLY!")
        print("\n🔐 Login Credentials:")
        print("   • Admin: admin / admin123")
        print("   • Manager: manager_cl1 / manager123")
        print("   • EMOC Staff: emoc_cl1 / emoc123")
        print("   • Counselor: counselor_cl1 / outdoor123")
        print("\n🚀 You can now start the server with: uvicorn main:app --reload")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()