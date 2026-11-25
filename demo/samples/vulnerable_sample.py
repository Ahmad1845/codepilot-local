import os

API_KEY = "FAKE_SECRET_KEY_EX_12345"

def search_users(db_conn, search_term):
    cursor = db_conn.cursor()
    # Vulnerable to SQL injection
    query = f"SELECT * FROM users WHERE name LIKE '%{search_term}%'"
    cursor.execute(query)
    return cursor.fetchall()
