from fastapi import APIRouter
import os
import psycopg2
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

def get_db_connection():
    """Database connection using POSTGRES_DSN"""
    try:
        cfg = get_settings()
        # Convert PostgresDsn object to string
        dsn_str = str(cfg.POSTGRES_DSN)
        conn = psycopg2.connect(dsn_str, connect_timeout=10)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

@router.get("/health")
def health_check():
    """Application health check"""
    return {
        "status": "healthy",
        "service": "IMAGE EHR",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@router.get("/db-test")
def test_database():
    """Database connection and stats test"""
    try:
        conn = get_db_connection()
        if not conn:
            return {"status": "❌ Database connection failed"}

        cursor = conn.cursor()

        # Get basic stats
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
        active_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM clinics")
        clinics = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM patients")
        patients = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM login_logs")
        login_logs = cursor.fetchone()[0]

        conn.close()

        return {
            "status": "✅ Database connection successful",
            "stats": {
                "active_users": active_users,
                "clinics": clinics,
                "patients": patients,
                "login_logs": login_logs
            }
        }
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return {
            "status": "❌ Database test failed",
            "error": str(e)
        }

@router.get("/debug-config")
def debug_config():
    """Debug configuration"""
    try:
        cfg = get_settings()
        dsn_str = str(cfg.POSTGRES_DSN)
        return {
            "postgres_dsn_prefix": dsn_str[:30] + "...",
            "secret_key_set": "YES" if cfg.SECRET_KEY else "NO",
            "app_name": cfg.APP_NAME,
            "dsn_type": type(cfg.POSTGRES_DSN).__name__
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }