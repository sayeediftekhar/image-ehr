from app.db.context import get_db_cursor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def authenticate_user(username: str, password: str):
    with get_db_cursor() as cur:
        query = """
            SELECT u.id, u.username, u.full_name, u.email, u.phone, u.role, u.clinic_id, c.name as clinic_name
            FROM users u
            LEFT JOIN clinics c ON u.clinic_id = c.id
            WHERE u.username = %s AND u.password = %s AND u.is_active = TRUE
        """
        cur.execute(query, (username, password))
        result = cur.fetchone()
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
            return user_data
        return None

def log_login_attempt(username, ip_address, location_data, success, user_agent=None):
    with get_db_cursor() as cur:
        cur.execute("""
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

def update_user_last_login(username, ip_address, location_data):
    with get_db_cursor() as cur:
        cur.execute("""
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