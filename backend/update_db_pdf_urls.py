import sqlite3
import os

DB_PATH = "cms_db.sqlite"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Update Consultations
cursor.execute("""
    SELECT c.id as consult_id, pu.username as patient_name
    FROM consultations c
    JOIN appointments a ON c.appointment_id = a.id
    JOIN patients p ON a.patient_id = p.id
    JOIN users pu ON p.user_id = pu.id
""")
consults = cursor.fetchall()

for c in consults:
    pdf_filename = f"Consultation_{c['patient_name'].replace(' ', '_')}_{c['consult_id'][:4]}.pdf"
    file_url = f"http://localhost:8000/reports/{pdf_filename}"
    cursor.execute("UPDATE consultations SET uploaded_file_url = ? WHERE id = ?", (file_url, c['consult_id']))
    print(f"Updated consultation {c['consult_id']} with URL: {file_url}")

# Update Lab Reports
cursor.execute("""
    SELECT DISTINCT p.id as patient_id, pu.username as name
    FROM lab_reports lr
    JOIN patients p ON lr.patient_id = p.id
    JOIN users pu ON p.user_id = pu.id
""")
labs = cursor.fetchall()

for l in labs:
    pdf_filename = f"LabReport_{l['name'].replace(' ', '_')}.pdf"
    file_url = f"http://localhost:8000/reports/{pdf_filename}"
    cursor.execute("UPDATE lab_reports SET uploaded_file_url = ? WHERE patient_id = ?", (file_url, l['patient_id']))
    print(f"Updated lab reports for patient {l['name']} with URL: {file_url}")

conn.commit()
conn.close()
print("Successfully linked all generated PDF reports to database records!")
