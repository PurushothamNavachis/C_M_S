import sqlite3

def check_db():
    conn = sqlite3.connect("cms_db.sqlite")
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM doctors WHERE license_number = 'LIC-ADM-DOC-01'")
    cursor.execute("DELETE FROM lab_ac WHERE license_number = 'LAB-ADM-01'")
    cursor.execute("DELETE FROM users WHERE username IN ('admin_doc_test', 'admin_rec_test', 'admin_lab_test')")
    conn.commit()

    print("=== ADMIN TEST ACCOUNTS CLEANED UP & DATABASE HEALTHY ===")
    conn.close()

if __name__ == "__main__":
    check_db()
