from app.db.context import get_db_cursor
import logging

logger = logging.getLogger(__name__)

def get_dashboard_stats():
    total_patients = 0
    total_login_logs = 0
    with get_db_cursor() as cur:
        try:
            cur.execute("SELECT COUNT(*) FROM patients")
            total_patients = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM login_logs")
            total_login_logs = cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {e}")
    return total_patients, total_login_logs