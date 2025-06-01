import psycopg2
from dotenv import load_dotenv
import os
import logging

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

def migrate_database():
    conn = get_db_connection()
    if not conn:
        logger.error("❌ Cannot connect to database")
        return False

    try:
        cursor = conn.cursor()

        # Add missing columns to clinics table
        logger.info("Adding missing columns to clinics table...")
        try:
            cursor.execute("ALTER TABLE clinics ADD COLUMN IF NOT EXISTS address TEXT")
            cursor.execute("ALTER TABLE clinics ADD COLUMN IF NOT EXISTS phone VARCHAR(20)")
            cursor.execute("ALTER TABLE clinics ADD COLUMN IF NOT EXISTS email VARCHAR(255)")
            cursor.execute("ALTER TABLE clinics ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            logger.info("✅ Clinics table updated")
        except Exception as e:
            logger.warning(f"Clinics table migration: {e}")

        # Add missing columns to users table
        logger.info("Adding missing columns to users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255)")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20)")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_ip VARCHAR(50)")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_country VARCHAR(100)")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_region VARCHAR(100)")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_city VARCHAR(100)")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_lat DECIMAL(10, 6)")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_lon DECIMAL(10, 6)")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_isp VARCHAR(255)")
            logger.info("✅ Users table updated")
        except Exception as e:
            logger.warning(f"Users table migration: {e}")

        # Create login_logs table
        logger.info("Creating login_logs table...")
        try:
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
            logger.info("✅ Login logs table created")
        except Exception as e:
            logger.warning(f"Login logs table creation: {e}")

        conn.commit()
        logger.info("✅ Database migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_sample_data():
    """Update existing data with missing information"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Update existing users with email and phone if they don't have them
        logger.info("Updating existing users with contact information...")

        users_updates = [
            ("admin", "admin@imageehr.com", "+1-555-1001"),
            ("manager1", "john.smith@imageehr.com", "+1-555-1002"),
            ("doctor1", "sarah.johnson@imageehr.com", "+1-555-1003"),
            ("nurse1", "emily.davis@imageehr.com", "+1-555-1004"),
            ("staff1", "michael.brown@imageehr.com", "+1-555-1005"),
            ("emoc1", "emoc@imageehr.com", "+1-555-1006"),
            ("receptionist1", "lisa.wilson@imageehr.com", "+1-555-1007"),
            ("manager2", "david.miller@imageehr.com", "+1-555-1008")
        ]

        for username, email, phone in users_updates:
            cursor.execute("""
                UPDATE users
                SET email = %s, phone = %s
                WHERE username = %s AND (email IS NULL OR email = '')
            """, (email, phone, username))

        # Update existing clinics with contact information
        logger.info("Updating existing clinics with contact information...")

        # First, get existing clinic IDs and names
        cursor.execute("SELECT id, name FROM clinics ORDER BY id")
        existing_clinics = cursor.fetchall()

        clinic_updates = [
            ("123 Main St, City Center", "+1-555-0101", "info@downtown-med.com"),
            ("456 West Ave, Westside", "+1-555-0102", "contact@westside-clinic.com"),
            ("789 Emergency Blvd, Hospital District", "+1-555-0103", "emergency@ecu-hospital.com"),
            ("321 Kids Lane, Family District", "+1-555-0104", "info@pediatric-center.com"),
            ("654 Elder St, Retirement Area", "+1-555-0105", "care@senior-facility.com")
        ]

        for i, (clinic_id, clinic_name) in enumerate(existing_clinics):
            if i < len(clinic_updates):
                address, phone, email = clinic_updates[i]
                cursor.execute("""
                    UPDATE clinics
                    SET address = %s, phone = %s, email = %s
                    WHERE id = %s AND (address IS NULL OR address = '')
                """, (address, phone, email, clinic_id))

        conn.commit()
        logger.info("✅ Sample data updated successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Error updating sample data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    logger.info("🚀 Migrating IMAGE EHR Database...")

    if migrate_database():
        logger.info("✅ Database migration completed")
        if update_sample_data():
            logger.info("✅ Sample data updated")
            logger.info("🎉 Migration completed successfully!")
        else:
            logger.warning("⚠️ Migration completed but sample data update failed")
    else:
        logger.error("❌ Migration failed")

if __name__ == "__main__":
    main()