import sqlite3

DB_PATH = "cms_db.sqlite"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE lab_reports ADD COLUMN status VARCHAR(50) DEFAULT 'PENDING';")
    conn.commit()
    print("Column status added to lab_reports successfully!")
except Exception as e:
    print(f"Error migrating lab_reports: {e}")
finally:
    conn.close()
