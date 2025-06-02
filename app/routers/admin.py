from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

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

@router.get("/users", response_class=HTMLResponse)
def admin_users(request: Request):
    """Admin user management page"""
    # Check admin access
    user = request.session.get("user")
    if not user or user.get("role") != "admin":
        return RedirectResponse("/login")

    conn = get_db_connection()
    if not conn:
        return HTMLResponse(content="<h1>Database connection failed</h1>", status_code=500)

    try:
        cursor = conn.cursor()
        query = """
        SELECT u.username, u.full_name, u.email, u.phone, u.role,
               c.name as clinic_name, u.last_login_at, u.last_login_ip,
               u.last_login_city, u.last_login_country, u.is_active
        FROM users u
        LEFT JOIN clinics c ON u.clinic_id = c.id
        ORDER BY u.last_login_at DESC NULLS LAST
        """
        cursor.execute(query)
        users = cursor.fetchall()
        conn.close()

        users_list = [
            {
                "username": user_row[0],
                "full_name": user_row[1],
                "email": user_row[2],
                "phone": user_row[3],
                "role": user_row[4],
                "clinic_name": user_row[5] or "All Clinics",
                "last_login_at": user_row[6],
                "last_login_ip": user_row[7],
                "last_login_city": user_row[8],
                "last_login_country": user_row[9],
                "is_active": user_row[10]
            }
            for user_row in users
        ]

        return templates.TemplateResponse(
            "admin_users.html",
            {"request": request, "users": users_list, "user": user}
        )
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return HTMLResponse(content=f"<h1>Error fetching users: {e}</h1>", status_code=500)

@router.get("/login-logs", response_class=HTMLResponse)
def admin_login_logs(request: Request):
    """Admin login logs page"""
    # Check admin access
    user = request.session.get("user")
    if not user or user.get("role") != "admin":
        return RedirectResponse("/login")

    conn = get_db_connection()
    if not conn:
        return HTMLResponse(content="<h1>Database connection failed</h1>", status_code=500)

    try:
        cursor = conn.cursor()
        query = """
        SELECT username, login_time, ip_address, city, country, success, user_agent
        FROM login_logs
        ORDER BY login_time DESC
        LIMIT 100
        """
        cursor.execute(query)
        logs = cursor.fetchall()
        conn.close()

        logs_list = [
            {
                "username": log[0],
                "login_time": log[1],
                "ip_address": log[2],
                "city": log[3],
                "country": log[4],
                "success": log[5],
                "user_agent": log[6]
            }
            for log in logs
        ]

        return templates.TemplateResponse(
            "admin_login_logs.html",
            {"request": request, "logs": logs_list, "user": user}
        )
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return HTMLResponse(content=f"<h1>Error fetching logs: {e}</h1>", status_code=500)