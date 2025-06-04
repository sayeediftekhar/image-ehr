from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from app.core.config import get_settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])
templates = Jinja2Templates(directory="templates")

def get_db_connection():
    try:
        cfg = get_settings()
        dsn_str = str(cfg.POSTGRES_DSN)
        conn = psycopg2.connect(dsn_str, connect_timeout=10)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

@router.get("/", response_class=HTMLResponse)
def billing_dashboard(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")

    conn = get_db_connection()
    if not conn:
        return HTMLResponse(content="<h1>Database connection failed</h1>", status_code=500)

    try:
        cursor = conn.cursor()

        # Get billing stats
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM bills WHERE DATE(created_at) = CURRENT_DATE AND status = 'paid'")
        today_revenue = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM bills WHERE status = 'pending'")
        pending_payments = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM bills
            WHERE EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)
            AND status = 'paid'
        """)
        monthly_total = cursor.fetchone()[0]

        # Get recent bills
        cursor.execute("""
            SELECT b.id, p.name, b.service_type, b.amount, b.status, b.created_at
            FROM bills b
            JOIN patients p ON b.patient_id = p.id
            ORDER BY b.created_at DESC LIMIT 10
        """)
        bills = cursor.fetchall()

        conn.close()

        bills_list = [
            {
                "id": bill[0],
                "patient_name": bill[1],
                "service": bill[2],
                "amount": bill[3],
                "status": bill[4],
                "date": bill[5]
            }
            for bill in bills
        ]

        return templates.TemplateResponse(
            "billing.html",
            {
                "request": request,
                "user": user,
                "today_revenue": today_revenue,
                "pending_payments": pending_payments,
                "monthly_total": monthly_total,
                "bills": bills_list
            }
        )
    except Exception as e:
        logger.error(f"Billing error: {e}")
        return HTMLResponse(content=f"<h1>Error: {e}</h1>", status_code=500)