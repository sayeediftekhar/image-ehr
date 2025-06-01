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

def reset_database():
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Drop existing tables
        logger.info("Dropping existing tables...")
        cursor.execute("DROP TABLE IF EXISTS login_logs CASCADE")
        cursor.execute("DROP TABLE IF EXISTS patients CASCADE")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE")
        cursor.execute("DROP TABLE IF EXISTS clinics CASCADE")

        conn.commit()
        logger.info("✅ Tables dropped successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Error dropping tables: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("🚨 RESETTING DATABASE - This will delete all data!")
    confirm = input("Are you sure? Type 'yes' to continue: ")

    if confirm.lower() == 'yes':
        if reset_database():
            logger.info("✅ Database reset completed")
            logger.info("Now run: python setup_database.py")
        else:
            logger.error("❌ Database reset failed")
    else:
        logger.info("❌ Reset cancelled")