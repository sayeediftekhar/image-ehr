from contextlib import contextmanager
from app.db.pools import pool

@contextmanager
def get_db_cursor():
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            yield cur
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)