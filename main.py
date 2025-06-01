from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import psycopg2
from dotenv import load_dotenv
import os
import logging
import requests
from datetime import datetime

# Add session middleware import
from starlette.middleware.sessions import SessionMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="IMAGE EHR",
    description="Multi-Clinic Management System",
    version="1.0.0"
)

# Add session middleware (set a strong secret key in production)
app.add_middleware(SessionMiddleware, secret_key="super-secret-key-123456")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Pydantic models
class UserCredentials(BaseModel):
    username: str
    password: str

# Database connection
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

def authenticate_user(username: str, password: str):
    logger.info(f"🔍 Attempting login for username: {username}")

    conn = get_db_connection()
    if not conn:
        logger.error("❌ Database connection failed")
        return None

    try:
        cursor = conn.cursor()
        query = """
            SELECT u.id, u.username, u.full_name, u.email, u.phone, u.role, u.clinic_id, c.name as clinic_name
            FROM users u
            LEFT JOIN clinics c ON u.clinic_id = c.id
            WHERE u.username = %s AND u.password = %s AND u.is_active = TRUE
        """
        cursor.execute(query, (username, password))
        result = cursor.fetchone()

        if result:
            user_data = {
                "id": result[0],
                "username": result[1],
                "full_name": result[2],
                "email": result[3],
                "phone": result[4],
                "role": result[5],
                "clinic_id": result[6],
                "clinic_name": result[7] if result[7] else "All Clinics",
                "has_emoc": result[5] in ['admin', 'manager', 'emoc_staff']
            }

            logger.info(f"✅ Login successful for {username}")
            return user_data

        logger.warning(f"❌ Invalid credentials for {username}")
        return None

    except Exception as e:
        logger.error(f"❌ Authentication error: {e}")
        return None
    finally:
        conn.close()

def get_location_from_ip(ip):
    try:
        url = f"http://ip-api.com/json/{ip}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success":
            return {
                "country": data.get("country"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "isp": data.get("isp"),
            }
        else:
            logger.warning(f"GeoIP API error: {data.get('message')}")
            return None
    except Exception as e:
        logger.error(f"GeoIP API request failed: {e}")
        return None

def log_login_attempt(username, ip_address, location_data, success, user_agent=None):
    """Log login attempt to database"""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO login_logs (username, ip_address, country, region, city, latitude, longitude, isp, success, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            username,
            ip_address,
            location_data.get("country") if location_data else None,
            location_data.get("region") if location_data else None,
            location_data.get("city") if location_data else None,
            location_data.get("lat") if location_data else None,
            location_data.get("lon") if location_data else None,
            location_data.get("isp") if location_data else None,
            success,
            user_agent
        ))
        conn.commit()
        logger.info(f"✅ Login attempt logged for {username}")
    except Exception as e:
        logger.error(f"❌ Error logging login attempt: {e}")
    finally:
        conn.close()

def update_user_last_login(username, ip_address, location_data):
    """Update user's last login information"""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET last_login_at = %s,
                last_login_ip = %s,
                last_login_country = %s,
                last_login_region = %s,
                last_login_city = %s,
                last_login_lat = %s,
                last_login_lon = %s,
                last_login_isp = %s
            WHERE username = %s
        """, (
            datetime.now(),
            ip_address,
            location_data.get("country") if location_data else None,
            location_data.get("region") if location_data else None,
            location_data.get("city") if location_data else None,
            location_data.get("lat") if location_data else None,
            location_data.get("lon") if location_data else None,
            location_data.get("isp") if location_data else None,
            username
        ))
        conn.commit()
        logger.info(f"✅ Last login updated for {username}")
    except Exception as e:
        logger.error(f"❌ Error updating last login: {e}")
    finally:
        conn.close()

# Routes
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, credentials: UserCredentials):
    logger.info(f"🚀 LOGIN ATTEMPT: username='{credentials.username}'")

    # Get user's IP address and user agent
    client_host = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")

    # Get location from IP
    location_data = get_location_from_ip(client_host)
    logger.info(f"User IP: {client_host}, Location: {location_data}")

    # Basic validation
    if not credentials.username or not credentials.password:
        log_login_attempt(credentials.username, client_host, location_data, False, user_agent)
        raise HTTPException(status_code=400, detail="Username and password are required")

    user = authenticate_user(credentials.username, credentials.password)

    if user:
        # Log successful login
        log_login_attempt(credentials.username, client_host, location_data, True, user_agent)

        # Update user's last login info
        update_user_last_login(credentials.username, client_host, location_data)

        # Set session
        request.session["user"] = user

        return {
            "message": "Login successful",
            "user": user,
            "location": location_data,
            "redirect": "/dashboard"
        }
    else:
        # Log failed login
        log_login_attempt(credentials.username, client_host, location_data, False, user_agent)
        logger.warning(f"❌ Login failed for {credentials.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    # Check if user is logged in
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    
    # Get some basic stats for the dashboard
    conn = get_db_connection()
    total_patients = 0
    total_login_logs = 0
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM patients")
            total_patients = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM login_logs")
            total_login_logs = cursor.fetchone()[0]
            
            conn.close()
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {e}")
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "user": user,
            "total_patients": total_patients,
            "total_login_logs": total_login_logs
        }
    )

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")

@app.get("/admin/users", response_class=HTMLResponse)
def admin_users(request: Request):
    # Protect this route
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
                "username": user[0],
                "full_name": user[1],
                "email": user[2],
                "phone": user[3],
                "role": user[4],
                "clinic_name": user[5] or "All Clinics",
                "last_login_at": user[6],
                "last_login_ip": user[7],
                "last_login_city": user[8],
                "last_login_country": user[9],
                "is_active": user[10]
            }
            for user in users
        ]
        # print(users_list)  # For debugging

        return templates.TemplateResponse(
            "admin_users.html",
            {"request": request, "users": users_list}
        )
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return HTMLResponse(content=f"<h1>Error fetching users: {e}</h1>", status_code=500)

@app.get("/admin/login-logs", response_class=HTMLResponse)
def admin_login_logs(request: Request):
    # Protect this route
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
            {"request": request, "logs": logs_list}
        )
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return HTMLResponse(content=f"<h1>Error fetching logs: {e}</h1>", status_code=500)

@app.get("/db-test")
def test_db():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
            user_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM clinics")
            clinic_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM patients")
            patient_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM login_logs")
            log_count = cursor.fetchone()[0]

            conn.close()

            return {
                "status": "✅ Database connection successful",
                "stats": {
                    "active_users": user_count,
                    "clinics": clinic_count,
                    "patients": patient_count,
                    "login_logs": log_count
                }
            }
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {"status": "❌ Database query failed", "error": str(e)}
    else:
        return {"status": "❌ Database connection failed"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "IMAGE EHR",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", reload=True)