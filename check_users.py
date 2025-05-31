import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def check_users():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()

    # Check all users
    cursor.execute("SELECT username, password_hash, full_name, role FROM users;")
    users = cursor.fetchall()

    print("Users in database:")
    for user in users:
        print(f"Username: {user[0]}, Password: {user[1]}, Name: {user[2]}, Role: {user[3]}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_users()

def check_tables():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()

    # Check tables
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public';
    """)
    tables = cursor.fetchall()

    print("\nTables in database:")
    for table in tables:
        print(f"- {table[0]}")

    cursor.close()
    conn.close()

# Update the main section
if __name__ == "__main__":
    check_tables()
    check_users()