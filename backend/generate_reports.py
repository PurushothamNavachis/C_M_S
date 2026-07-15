import sqlite3
import fitz  # PyMuPDF
import os

DB_PATH = "cms_db.sqlite"
TEMPLATE_PATH = r"C:\Users\milaa\Desktop\Navachis\C_M_S\pdf\empty_report.pdf"
OUTPUT_DIR = r"C:\Users\milaa\Desktop\Navachis\C_M_S\pdf\generated_reports"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def add_new_page(doc, template_path):
    temp_doc = fitz.open(template_path)
    doc.insert_pdf(temp_doc, from_page=0, to_page=0)
    return doc[-1]

def write_text(page, doc, text, x, y, font="Helvetica", size=11, bold=False):
    if y > 780:
        page = add_new_page(doc, TEMPLATE_PATH)
        y = 160  # Reset Y to below the header on the new page
    
    fontname = "Helvetica"
    if bold: fontname = "Helvetica-Bold"
    
    # insert text
    page.insert_text(fitz.Point(x, y), str(text), fontname=fontname, fontsize=size)
    return page, y + size + 8

def insert_wrapped_text(page, doc, text, x, y, width=450, size=11):
    # Basic text wrap simulation using insert_textbox
    if not text:
        return page, y
    
    # Estimate height (very rough: 15 points per line)
    chars_per_line = width / (size * 0.5)
    lines = max(1, len(str(text)) / chars_per_line)
    box_height = int(lines * (size + 5) + 10)
    
    if y + box_height > 780:
        page = add_new_page(doc, TEMPLATE_PATH)
        y = 160
        
    rect = fitz.Rect(x, y, x + width, y + box_height)
    page.insert_textbox(rect, str(text), fontname="Helvetica", fontsize=size)
    return page, y + box_height + 5

def generate_single_consultation_pdf(consult_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
    SELECT 
        c.id as consult_id, c.symptoms, c.diagnosis, c.doctor_notes,
        p.id as patient_id, pu.username as patient_name, p.dob, p.gender, p.phone as patient_phone,
        du.username as doctor_name, d.specialization, a.appointment_date
    FROM consultations c
    JOIN appointments a ON c.appointment_id = a.id
    JOIN patients p ON a.patient_id = p.id
    JOIN users pu ON p.user_id = pu.id
    LEFT JOIN doctors d ON a.doctor_id = d.id
    LEFT JOIN users du ON d.user_id = du.id
    WHERE c.id = ?
    """
    cursor.execute(query, (consult_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    doc = fitz.open(TEMPLATE_PATH)
    page = doc[0]

    # Top Right Header Info (Customer ID & Date)
    cust_id_str = f"Customer ID: #{row['patient_id'][:8].upper()}"
    date_str = f"Date: {row['appointment_date']}"
    page.insert_text(fitz.Point(380, 65), cust_id_str, fontname="Helvetica-Bold", fontsize=10)
    page.insert_text(fitz.Point(380, 78), date_str, fontname="Helvetica", fontsize=10)

    y = 160

    # Header
    page, y = write_text(page, doc, "CUSTOMER REQUEST - CONSULT", 200, y, bold=True, size=14)
    y += 20

    # Patient & Doctor Info
    left_x = 50
    right_x = 320
    
    dob_str = str(row['dob']) if row['dob'] else '-'
    
    page, _ = write_text(page, doc, f"Name: {row['patient_name']}", left_x, y, bold=True)
    page, y = write_text(page, doc, f"Doctor Name: {row['doctor_name'] or 'N/A'}", right_x, y, bold=True)
    
    page, _ = write_text(page, doc, f"Date of Birth: {dob_str}", left_x, y)
    page, y = write_text(page, doc, f"Specialization: {row['specialization'] or 'N/A'}", right_x, y)
    
    page, y = write_text(page, doc, f"Gender: {row['gender']}", left_x, y)
    page, y = write_text(page, doc, f"Contact: {row['patient_phone']}", left_x, y)
    
    y += 30

    # Prescriptions
    page, y = write_text(page, doc, "Prescriptions -", left_x, y, bold=True)
    cursor.execute("""
        SELECT m.name as medication_name, pi.dosage, pi.duration_days 
        FROM prescriptions pr
        JOIN prescription_items pi ON pr.id = pi.prescription_id
        JOIN medicines m ON pi.medicine_id = m.id
        WHERE pr.consultation_id = ?
    """, (row['consult_id'],))
    prescriptions = cursor.fetchall()
    if prescriptions:
        for p in prescriptions:
            page, y = write_text(page, doc, f"- {p['medication_name']} | {p['dosage']} | {p['duration_days']} days", left_x + 10, y)
    y += 15

    # Doctor Notes
    page, y = write_text(page, doc, "Doctor Notes -", left_x, y, bold=True)
    if row['doctor_notes']:
        page, y = insert_wrapped_text(page, doc, row['doctor_notes'], left_x, y)
    y += 10

    # Symptoms
    page, y = write_text(page, doc, "Symptoms -", left_x, y, bold=True)
    if row['symptoms']:
        page, y = insert_wrapped_text(page, doc, row['symptoms'], left_x, y)
    y += 10

    # Diagnosis
    page, y = write_text(page, doc, "Diagnosis -", left_x, y, bold=True)
    if row['diagnosis']:
        page, y = insert_wrapped_text(page, doc, row['diagnosis'], left_x, y)

    pdf_filename = f"Consultation_{row['patient_name'].replace(' ', '_')}_{row['consult_id'][:4]}.pdf"
    output_path = os.path.join(OUTPUT_DIR, pdf_filename)
    doc.save(output_path)
    doc.close()
    
    file_url = f"http://localhost:8000/reports/{pdf_filename}"
    cursor.execute("UPDATE consultations SET uploaded_file_url = ? WHERE id = ?", (file_url, consult_id))
    conn.commit()
    conn.close()
    
    print(f"Generated {output_path} and saved URL to DB: {file_url}")
    return file_url

def generate_single_lab_report_pdf(patient_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
    SELECT DISTINCT p.id as patient_id, pu.username as name, p.dob, p.gender, p.phone, DATE(lr.created_at) as req_date
    FROM lab_reports lr
    JOIN patients p ON lr.patient_id = p.id
    JOIN users pu ON p.user_id = pu.id
    WHERE p.id = ?
    """
    cursor.execute(query, (patient_id,))
    p = cursor.fetchone()
    if not p:
        conn.close()
        return None

    doc = fitz.open(TEMPLATE_PATH)
    page = doc[0]

    req_date = str(p['req_date']) if p['req_date'] else '2026-07-13'

    # Top Right Header Info (Customer ID & Date)
    cust_id_str = f"Customer ID: #{p['patient_id'][:8].upper()}"
    date_str = f"Date: {req_date}"
    page.insert_text(fitz.Point(380, 65), cust_id_str, fontname="Helvetica-Bold", fontsize=10)
    page.insert_text(fitz.Point(380, 78), date_str, fontname="Helvetica", fontsize=10)

    y = 160

    # Header
    page, y = write_text(page, doc, "CUSTOMER REQUEST - LAB TEST", 200, y, bold=True, size=14)
    y += 20

    left_x = 50
    dob_str = str(p['dob']) if p['dob'] else '-'
    page, y = write_text(page, doc, f"Name: {p['name']}", left_x, y, bold=True)
    page, y = write_text(page, doc, f"Date of Birth: {dob_str}", left_x, y)
    page, y = write_text(page, doc, f"Gender: {p['gender']}", left_x, y)
    page, y = write_text(page, doc, f"Contact: {p['phone']}", left_x, y)
    y += 30

    page, y = write_text(page, doc, "Diagnostic Lab Tests:", left_x, y, bold=True)
    y += 10

    # Table Column Headers
    page, _ = write_text(page, doc, "Test Name", left_x, y, bold=True, size=11)
    page, y = write_text(page, doc, "Result / Status", 320, y, bold=True, size=11)
    y += 5

    cursor.execute("""
        SELECT lt.test_name, lr.result_value 
        FROM lab_reports lr
        JOIN laboratory_tests lt ON lr.test_id = lt.id
        WHERE lr.patient_id = ?
    """, (patient_id,))
    tests = cursor.fetchall()

    for t in tests:
        result = t['result_value'] if t['result_value'] else 'Booked'
        page, _ = write_text(page, doc, t['test_name'], left_x, y, size=10)
        page, y = write_text(page, doc, result, 320, y, size=10)

    pdf_filename = f"LabReport_{p['name'].replace(' ', '_')}.pdf"
    output_path = os.path.join(OUTPUT_DIR, pdf_filename)
    doc.save(output_path)
    doc.close()
    
    file_url = f"http://localhost:8000/reports/{pdf_filename}"
    cursor.execute("UPDATE lab_reports SET uploaded_file_url = ? WHERE patient_id = ?", (file_url, patient_id))
    conn.commit()
    conn.close()
    
    print(f"Generated {output_path} and saved URL to DB: {file_url}")
    return file_url

if __name__ == "__main__":
    # If run directly, generate everything for fallback/seeding purposes
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM consultations")
    for r in cursor.fetchall():
        generate_single_consultation_pdf(r['id'])
        
    cursor.execute("SELECT DISTINCT patient_id FROM lab_reports")
    for r in cursor.fetchall():
        generate_single_lab_report_pdf(r['patient_id'])
        
    conn.close()
    print("Fallback complete: Generated all PDFs.")
