from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from app.core.config import get_settings
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/visits", tags=["visits"])
templates = Jinja2Templates(directory="templates")

def get_db_connection():
    try:
        cfg = get_settings()
        dsn_str = str(cfg.POSTGRES_DSN)
        conn = psycopg2.connect(dsn_str, connect_timeout=10)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def require_auth(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    return user

@router.get("/{visit_id}", response_class=HTMLResponse)
def visit_detail(request: Request, visit_id: int):
    """Visit detail page"""
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    conn = get_db_connection()
    if not conn:
        return HTMLResponse(content="<h1>Database connection failed</h1>", status_code=500)

    try:
        cursor = conn.cursor()
        
        # Get visit details
        query = """
            SELECT v.*, p.full_name as patient_name, p.patient_id,
                   COALESCE(u.full_name, 'Unknown') as doctor_name,
                   c.name as clinic_name
            FROM visits v
            LEFT JOIN patients p ON v.patient_id = p.id
            LEFT JOIN users u ON v.doctor_id = u.id
            LEFT JOIN clinics c ON v.clinic_id = c.id
            WHERE v.id = %s
        """
        cursor.execute(query, (visit_id,))
        visit = cursor.fetchone()
        
        if not visit:
            cursor.close()
            conn.close()
            return HTMLResponse(content="<h1>Visit not found</h1>", status_code=404)

        # Get prescriptions for this visit
        prescription_query = """
            SELECT id, medicine_name, dosage, frequency, duration, instructions, quantity, status
            FROM prescriptions 
            WHERE visit_id = %s
            ORDER BY prescribed_date DESC
        """
        cursor.execute(prescription_query, (visit_id,))
        prescriptions = cursor.fetchall()

        cursor.close()
        conn.close()

        # Parse vital signs JSON
        vital_signs = {}
        if visit[10]:  # vital_signs column
            try:
                vital_signs = json.loads(visit[10])
            except:
                vital_signs = {}

        visit_data = {
            "id": visit[0],
            "patient_id": visit[1],
            "doctor_id": visit[2],
            "clinic_id": visit[3],
            "visit_date": visit[4],
            "visit_type": visit[5],
            "chief_complaint": visit[6],
            "diagnosis": visit[7],
            "treatment": visit[8],
            "notes": visit[9],
            "vital_signs": vital_signs,
            "status": visit[11],
            "follow_up_date": visit[12],
            "created_at": visit[13],
            "updated_at": visit[14],
            "patient_name": visit[15],
            "patient_code": visit[16],
            "doctor_name": visit[17],
            "clinic_name": visit[18]
        }

        prescription_list = []
        for p in prescriptions:
            prescription_list.append({
                "id": p[0],
                "medicine_name": p[1],
                "dosage": p[2],
                "frequency": p[3],
                "duration": p[4],
                "instructions": p[5],
                "quantity": p[6],
                "status": p[7]
            })

        return templates.TemplateResponse(
            "visit_detail.html",
            {
                "request": request, 
                "user": user, 
                "visit": visit_data,
                "prescriptions": prescription_list
            }
        )
    except Exception as e:
        logger.error(f"Visit detail error: {e}")
        if conn:
            conn.close()
        return HTMLResponse(content=f"<h1>Error: {e}</h1>", status_code=500)