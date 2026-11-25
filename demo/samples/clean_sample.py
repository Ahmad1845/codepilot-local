def get_user_by_id(db_conn, user_id):
    cursor = db_conn.cursor()
    query = "SELECT id, username, email FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    cursor.close()
    return result
