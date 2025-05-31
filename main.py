from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import psycopg2
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="IMAGE EHR", 
    description="Multi-Clinic Management System",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Pydantic models
class UserCredentials(BaseModel):
    username: str
    password: str

# Database connection with better error handling
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
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
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
            SELECT u.username, u.full_name, u.role, u.clinic_id, c.name as clinic_name
            FROM users u
            LEFT JOIN clinics c ON u.clinic_id = c.id
            WHERE u.username = %s AND u.password = %s AND u.is_active = TRUE
        """
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        
        logger.info(f"🔍 Query result: {result}")
        
        if result:
            user_data = {
                "username": result[0],
                "full_name": result[1],
                "role": result[2],
                "clinic_id": result[3],
                "clinic_name": result[4] if result[4] else "All Clinics",
                "has_emoc": result[2] in ['admin', 'manager', 'emoc_staff']
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

# Routes
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(credentials: UserCredentials):
    logger.info(f"🚀 LOGIN ATTEMPT: username='{credentials.username}'")
    
    # Basic validation
    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    if len(credentials.username) > 50 or len(credentials.password) > 100:
        raise HTTPException(status_code=400, detail="Invalid credentials format")
    
    user = authenticate_user(credentials.username, credentials.password)
    
    if user:
        logger.info(f"✅ Login successful for {credentials.username}")
        return {
            "message": "Login successful", 
            "user": user,
            "timestamp": "2024-06-01T10:00:00Z"
        }
    else:
        logger.warning(f"❌ Login failed for {credentials.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/db-test")
def test_db():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Test queries
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM clinics")
            clinic_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM patients")
            patient_count = cursor.fetchone()[0]
            
            # Test a join query
            cursor.execute("""
                SELECT u.username, u.role, c.name as clinic_name 
                FROM users u 
                LEFT JOIN clinics c ON u.clinic_id = c.id 
                WHERE u.is_active = TRUE
                LIMIT 5
            """)
            sample_users = cursor.fetchall()
            
            conn.close()
            
            return {
                "status": "✅ Database connection successful",
                "stats": {
                    "active_users": user_count,
                    "clinics": clinic_count,
                    "patients": patient_count
                },
                "sample_users": [
                    {"username": user[0], "role": user[1], "clinic": user[2] or "All Clinics"}
                    for user in sample_users
                ],
                "database_info": {
                    "host": os.getenv("DB_HOST"),
                    "database": os.getenv("DB_NAME"),
                    "environment": os.getenv("ENVIRONMENT", "development")
                }
            }
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {
                "status": "❌ Database query failed", 
                "error": str(e)
            }
    else:
        return {
            "status": "❌ Database connection failed",
            "error": "Could not establish connection to database"
        }

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
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )