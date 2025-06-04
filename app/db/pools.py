import psycopg2
from psycopg2.pool import SimpleConnectionPool
from app.core.config import get_settings

settings = get_settings()

pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=str(settings.POSTGRES_DSN)  # <-- this is the fix
)