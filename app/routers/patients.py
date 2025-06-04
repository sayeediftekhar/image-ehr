from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from app.core.config import get_settings
import logging
import json
from datetime import datetime, date

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/patients", tags=["patients"])
templates = Jinja2Templates(directory="templates")

def get_db_connection():
    """Get database connection with improved error handling"""
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
    """Check if user is authenticated"""
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    return user

def safe_execute_query(cursor, query, params=None, fetch_one=False, fetch_all=False):
    """Safely execute database queries with error handling"""
    try:
        cursor.execute(query, params)
        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        return True
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return None

# 1. ROOT ROUTE - Patient List
@router.get("/", response_class=HTMLResponse)
def patients_list(request: Request):
    """Patient list page with analytics"""
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    conn = get_db_connection()
    if not conn:
        return HTMLResponse(content="<h1>Database connection failed</h1>", status_code=500)

    try:
        cursor = conn.cursor()

        # Get patient statistics with safe execution
        total_patients = 0
        result = safe_execute_query(cursor, "SELECT COUNT(*) FROM patients", fetch_one=True)
        if result:
            total_patients = result[0]

        today_registrations = 0
        result = safe_execute_query(cursor, 
            "SELECT COUNT(*) FROM patients WHERE DATE(created_at) = CURRENT_DATE", 
            fetch_one=True)
        if result:
            today_registrations = result[0]

        # Handle visits table gracefully
        today_visits = 0
        result = safe_execute_query(cursor,
            "SELECT COUNT(DISTINCT patient_id) FROM visits WHERE DATE(visit_date) = CURRENT_DATE",
            fetch_one=True)
        if result:
            today_visits = result[0]

        # Get recent patients with proper error handling
        patients_list = []
        patients = safe_execute_query(cursor, """
            SELECT p.id, p.patient_id, p.full_name, p.age, p.gender, p.phone, p.address,
                   COALESCE(c.name, 'Unknown') as clinic_name, p.created_at
            FROM patients p
            LEFT JOIN clinics c ON p.clinic_id = c.id
            ORDER BY p.created_at DESC
            LIMIT 20
        """, fetch_all=True)

        if patients:
            patients_list = [
                {
                    "id": patient[0],
                    "patient_id": patient[1],
                    "name": patient[2],  # full_name
                    "age": patient[3],
                    "gender": patient[4],
                    "phone": patient[5],
                    "address": patient[6],
                    "clinic_name": patient[7],
                    "created_at": patient[8],
                    "visit_count": 0
                }
                for patient in patients
            ]

        cursor.close()
        conn.close()

        return templates.TemplateResponse(
            "patients.html",
            {
                "request": request,
                "user": user,
                "total_patients": total_patients,
                "today_registrations": today_registrations,
                "today_visits": today_visits,
                "patients": patients_list
            }
        )
    except Exception as e:
        logger.error(f"Patients list error: {e}")
        if conn:
            conn.close()
        return HTMLResponse(content=f"<h1>Error loading patients: {e}</h1>", status_code=500)

# 2. SPECIFIC ROUTES (must come before dynamic routes)
@router.get("/new", response_class=HTMLResponse)
def new_patient_form(request: Request):
    """New patient registration form"""
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    conn = get_db_connection()
    if not conn:
        return HTMLResponse(content="<h1>Database connection failed</h1>", status_code=500)

    try:
        cursor = conn.cursor()

        # Get clinics with safe execution
        clinics = [(1, "Default Clinic")]  # Default fallback
        result = safe_execute_query(cursor, "SELECT id, name FROM clinics ORDER BY name", fetch_all=True)
        if result:
            clinics = result

        cursor.close()
        conn.close()

        return templates.TemplateResponse(
            "patient_form.html",
            {
                "request": request,
                "user": user,
                "clinics": clinics,
                "patient": None
            }
        )
    except Exception as e:
        logger.error(f"New patient form error: {e}")
        if conn:
            conn.close()
        return HTMLResponse(content=f"<h1>Error loading form: {e}</h1>", status_code=500)

@router.post("/create")
def create_patient(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    phone: str = Form(""),
    address: str = Form(""),
    clinic_id: int = Form(...),
    emergency_contact: str = Form(""),
    emergency_phone: str = Form("")
):
    """Create new patient with improved error handling"""
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()

        # Generate unique patient_id
        count_result = safe_execute_query(cursor, "SELECT COUNT(*) FROM patients", fetch_one=True)
        count = count_result[0] if count_result else 0
        patient_id_str = f"PAT{count + 1:06d}"

        # Insert new patient
        result = safe_execute_query(cursor, """
            INSERT INTO patients (patient_id, full_name, age, gender, phone, address, 
                                emergency_contact, emergency_phone, clinic_id, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (patient_id_str, name, age, gender, phone or None, address or None, 
              emergency_contact or None, emergency_phone or None, clinic_id, 
              user.get("id", 1), datetime.now()), fetch_one=True)

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create patient")

        new_patient_id = result[0]
        cursor.close()
        conn.close()

        return RedirectResponse(f"/patients/{new_patient_id}", status_code=303)
    except Exception as e:
        logger.error(f"Create patient error: {e}")
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"Error creating patient: {e}")

@router.get("/search", response_class=HTMLResponse)
def search_patients(request: Request, q: str = ""):
    """Search patients by name, phone, or patient ID"""
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    conn = get_db_connection()
    if not conn:
        return HTMLResponse(content="<h1>Database connection failed</h1>", status_code=500)

    try:
        cursor = conn.cursor()

        if q.strip():
            patients = safe_execute_query(cursor, """
                SELECT p.id, p.patient_id, p.full_name, p.age, p.gender, p.phone, p.address,
                       COALESCE(c.name, 'Unknown') as clinic_name, p.created_at
                FROM patients p
                LEFT JOIN clinics c ON p.clinic_id = c.id
                WHERE p.full_name ILIKE %s OR p.phone ILIKE %s OR p.patient_id ILIKE %s
                ORDER BY p.created_at DESC
                LIMIT 50
            """, (f"%{q}%", f"%{q}%", f"%{q}%"), fetch_all=True)
        else:
            patients = safe_execute_query(cursor, """
                SELECT p.id, p.patient_id, p.full_name, p.age, p.gender, p.phone, p.address,
                       COALESCE(c.name, 'Unknown') as clinic_name, p.created_at
                FROM patients p
                LEFT JOIN clinics c ON p.clinic_id = c.id
                ORDER BY p.created_at DESC
                LIMIT 20
            """, fetch_all=True)

        patients_list = []
        if patients:
            patients_list = [
                {
                    "id": patient[0],
                    "patient_id": patient[1],
                    "name": patient[2],
                    "age": patient[3],
                    "gender": patient[4],
                    "phone": patient[5],
                    "address": patient[6],
                    "clinic_name": patient[7],
                    "created_at": patient[8],
                    "visit_count": 0
                }
                for patient in patients
            ]

        cursor.close()
        conn.close()

        return templates.TemplateResponse(
            "patients.html",
            {
                "request": request,
                "user": user,
                "total_patients": len(patients_list),
                "today_registrations": 0,
                "today_visits": 0,
                "patients": patients_list,
                "search_query": q
            }
        )
    except Exception as e:
        logger.error(f"Search patients error: {e}")
        if conn:
            conn.close()
        return HTMLResponse(content=f"<h1>Search error: {e}</h1>", status_code=500)

# 3. DYNAMIC ROUTES (must come last)
@router.get("/{patient_id}/edit", response_class=HTMLResponse)
def edit_patient_form(request: Request, patient_id: int):
    """Edit patient form"""
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    conn = get_db_connection()
    if not conn:
        return HTMLResponse(content="<h1>Database connection failed</h1>", status_code=500)

    try:
        cursor = conn.cursor()

        # Get patient details
        patient = safe_execute_query(cursor, "SELECT * FROM patients WHERE id = %s", (patient_id,), fetch_one=True)

        if not patient:
            cursor.close()
            conn.close()
            return HTMLResponse(content="<h1>Patient not found</h1>", status_code=404)

        # Get clinics
        clinics = [(1, "Default Clinic")]
        result = safe_execute_query(cursor, "SELECT id, name FROM clinics ORDER BY name", fetch_all=True)
        if result:
            clinics = result

        cursor.close()
        conn.close()

        patient_data = {
            "id": patient[0],
            "patient_id": patient[1],
            "name": patient[2],  # full_name
            "age": patient[3],
            "gender": patient[4],
            "phone": patient[5],
            "address": patient[6],
            "emergency_contact": patient[7],
            "emergency_phone": patient[8],
            "clinic_id": patient[9]
        }

        return templates.TemplateResponse(
            "patient_form.html",
            {
                "request": request,
                "user": user,
                "clinics": clinics,
                "patient": patient_data
            }
        )
    except Exception as e:
        logger.error(f"Edit patient form error: {e}")
        if conn:
            conn.close()
        return HTMLResponse(content=f"<h1>Error loading patient: {e}</h1>", status_code=500)

@router.post("/{patient_id}/update")
def update_patient(
    request: Request,
    patient_id: int,
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    phone: str = Form(""),
    address: str = Form(""),
    clinic_id: int = Form(...),
    emergency_contact: str = Form(""),
    emergency_phone: str = Form("")
):
    """Update patient with improved error handling"""
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()

        result = safe_execute_query(cursor, """
            UPDATE patients 
            SET full_name = %s, age = %s, gender = %s, phone = %s, address = %s,
                clinic_id = %s, emergency_contact = %s, emergency_phone = %s,
                updated_at = %s
            WHERE id = %s
        """, (name, age, gender, phone or None, address or None, clinic_id,
              emergency_contact or None, emergency_phone or None,
              datetime.now(), patient_id))

        if not result:
            raise HTTPException(status_code=500, detail="Failed to update patient")

        cursor.close()
        conn.close()

        return RedirectResponse(f"/patients/{patient_id}", status_code=303)
    except Exception as e:
        logger.error(f"Update patient error: {e}")
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"Error updating patient: {e}")

@router.get("/{patient_id}", response_class=HTMLResponse)
def patient_detail(request: Request, patient_id: int):
    """Patient detail page with comprehensive information"""
    logger.info(f"Accessing patient detail for ID: {patient_id}")

    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    conn = get_db_connection()
    if not conn:
        logger.error("Database connection failed in patient detail")
        return HTMLResponse(content="<h1>Database connection failed</h1>", status_code=500)

    try:
        cursor = conn.cursor()

        # Get patient details with clinic information
        logger.info(f"Querying for patient ID: {patient_id}")
        patient = safe_execute_query(cursor, """
            SELECT p.id, p.patient_id, p.full_name, p.age, p.gender, p.phone, p.address,
                   p.emergency_contact, p.emergency_phone, p.clinic_id, p.created_by, p.created_at, p.updated_at,
                   COALESCE(c.name, 'Unknown') as clinic_name
            FROM patients p
            LEFT JOIN clinics c ON p.clinic_id = c.id
            WHERE p.id = %s
        """, (patient_id,), fetch_one=True)

        logger.info(f"Patient query result: {patient is not None}")

        if not patient:
            cursor.close()
            conn.close()
            logger.warning(f"No patient found with ID: {patient_id}")
            return HTMLResponse(content="<h1>Patient not found</h1>", status_code=404)

        # Get patient visits (handle gracefully if visits table doesn't exist)
        visits = []
        visits_result = safe_execute_query(cursor, """
            SELECT v.id, v.visit_date, v.diagnosis, v.treatment, v.notes,
                   COALESCE(u.full_name, 'Unknown') as doctor_name
            FROM visits v
            LEFT JOIN users u ON v.doctor_id = u.id
            WHERE v.patient_id = %s
            ORDER BY v.visit_date DESC
        """, (patient_id,), fetch_all=True)

        if visits_result:
            visits = [
                {
                    "id": visit[0],
                    "visit_date": visit[1],
                    "diagnosis": visit[2],
                    "treatment": visit[3],
                    "notes": visit[4],
                    "doctor_name": visit[5]
                }
                for visit in visits_result
            ]

        cursor.close()
        conn.close()

        patient_data = {
            "id": patient[0],
            "patient_id": patient[1],
            "name": patient[2],
            "age": patient[3],
            "gender": patient[4],
            "phone": patient[5],
            "address": patient[6],
            "emergency_contact": patient[7],
            "emergency_phone": patient[8],
            "clinic_id": patient[9],
            "created_at": patient[11],
            "updated_at": patient[12],
            "clinic_name": patient[13]
        }

        logger.info(f"Successfully loaded patient data for ID: {patient_id}")

        return templates.TemplateResponse(
            "patient_detail.html",
            {
                "request": request,
                "user": user,
                "patient": patient_data,
                "visits": visits
            }
        )
    except Exception as e:
        logger.error(f"Patient detail error: {e}")
        if conn:
            conn.close()
        return HTMLResponse(content=f"<h1>Error loading patient details: {e}</h1>", status_code=500)

@router.get("/{patient_id}/visit/new", response_class=HTMLResponse)
def new_visit_form(request: Request, patient_id: int):
    """New visit form for a patient"""
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    conn = get_db_connection()
    if not conn:
        return HTMLResponse(content="<h1>Database connection failed</h1>", status_code=500)

    try:
        cursor = conn.cursor()

        # Get patient details
        cursor.execute("SELECT id, patient_id, full_name FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()

        if not patient:
            cursor.close()
            conn.close()
            return HTMLResponse(content="<h1>Patient not found</h1>", status_code=404)

        cursor.close()
        conn.close()

        patient_data = {
            "id": patient[0],
            "patient_id": patient[1],
            "name": patient[2]
        }

        return templates.TemplateResponse(
            "visit_form.html",
            {
                "request": request, 
                "user": user, 
                "patient": patient_data,
                "today": date.today().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"New visit form error: {e}")
        if conn:
            conn.close()
        return HTMLResponse(content=f"<h1>Error: {e}</h1>", status_code=500)

@router.post("/{patient_id}/visit/create")
def create_visit(
    request: Request,
    patient_id: int,
    visit_date: str = Form(...),
    visit_type: str = Form("consultation"),
    chief_complaint: str = Form(""),
    diagnosis: str = Form(...),
    treatment: str = Form(...),
    notes: str = Form(""),
    follow_up_date: str = Form(""),
    # Vital signs
    blood_pressure: str = Form(""),
    temperature: str = Form(""),
    pulse: str = Form(""),
    weight: str = Form(""),
    height: str = Form(""),
    oxygen_saturation: str = Form("")
):
    """Create new visit"""
    user = require_auth(request)
    if isinstance(user, RedirectResponse):
        return user

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()

        # Parse dates
        visit_datetime = datetime.strptime(visit_date, "%Y-%m-%d")
        follow_up = None
        if follow_up_date:
            follow_up = datetime.strptime(follow_up_date, "%Y-%m-%d").date()

        # Prepare vital signs JSON
        vital_signs = {}
        if blood_pressure: vital_signs["blood_pressure"] = blood_pressure
        if temperature: vital_signs["temperature"] = temperature
        if pulse: vital_signs["pulse"] = pulse
        if weight: vital_signs["weight"] = weight
        if height: vital_signs["height"] = height
        if oxygen_saturation: vital_signs["oxygen_saturation"] = oxygen_saturation

        vital_signs_json = json.dumps(vital_signs) if vital_signs else None

        cursor.execute("""
            INSERT INTO visits (
                patient_id, doctor_id, clinic_id, visit_date, visit_type,
                chief_complaint, diagnosis, treatment, notes, vital_signs,
                follow_up_date, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            patient_id, user.get("id", 1), user.get("clinic_id", 1), 
            visit_datetime, visit_type, chief_complaint, diagnosis, 
            treatment, notes, vital_signs_json, follow_up, datetime.now()
        ))

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create visit")

        return RedirectResponse(f"/patients/{patient_id}", status_code=303)
    except Exception as e:
        logger.error(f"Create visit error: {e}")
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"Error creating visit: {e}")

# Additional utility route for debugging
@router.get("/debug/{patient_id}")
def debug_patient(request: Request, patient_id: int):
    """Debug route to check patient data"""
    conn = get_db_connection()
    if not conn:
        return {"error": "Database connection failed"}

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()
        cursor.close()
        conn.close()

        return {
            "patient_id": patient_id,
            "found": patient is not None,
            "data": patient if patient else None
        }
    except Exception as e:
        if conn:
            conn.close()
        return {"error": str(e)}
