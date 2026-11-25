# Sample 1: Clean code
clean_code = """def get_user_by_id(db_conn, user_id):
    cursor = db_conn.cursor()
    query = "SELECT id, username, email FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    cursor.close()
    return result
"""

# Sample 2: Security bug (SQL injection & Hardcoded key)
security_bug = """import os

API_KEY = "FAKE_SECRET_KEY_EX_12345"

def search_users(db_conn, search_term):
    cursor = db_conn.cursor()
    # Vulnerable to SQL injection
    query = f"SELECT * FROM users WHERE name LIKE '%{search_term}%'"
    cursor.execute(query)
    return cursor.fetchall()
"""

# Sample 3: Resource leak & Error handling issue
resource_leak_bug = """def load_config_file(filepath):
    try:
        f = open(filepath, 'r')
        data = f.read()
        return data
    except Exception:
        pass
    return None
"""

from pathlib import Path

sample_dir = Path("demo/samples")
sample_dir.mkdir(parents=True, exist_ok=True)

(sample_dir / "clean_sample.py").write_text(clean_code)
(sample_dir / "vulnerable_sample.py").write_text(security_bug)
(sample_dir / "resource_leak_sample.py").write_text(resource_leak_bug)

print("Demo samples created under demo/samples/")
