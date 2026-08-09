import sqlite3

def check_db():
    conn = sqlite3.connect("cms_db.sqlite")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    users = cursor.execute("""
        SELECT u.username, u.email, u.plain_password, r.name as role_name 
        FROM users u 
        JOIN roles r ON u.role_id = r.id 
        WHERE u.deleted_at IS NULL
    """).fetchall()

    print(f"=== TOTAL ACTIVE ACCOUNTS IN SYSTEM: {len(users)} ===")
    for u in users:
        print(f"Role: {u['role_name']:<15} | Username: {u['username']:<20} | Email: {u['email']:<30} | Password: {u['plain_password']}")

    conn.close()

if __name__ == "__main__":
    check_db()
