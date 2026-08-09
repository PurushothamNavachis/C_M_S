import sqlite3
import fitz  # PyMuPDF
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cms_db.sqlite")
TEMPLATE_PATH = r"C:\Users\milaa\Desktop\Navachis\C_M_S\pdf\empty_report.pdf"
OUTPUT_DIR = r"C:\Users\milaa\Desktop\Navachis\C_M_S\pdf\generated_reports"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

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
    WHERE c.id = ? OR c.appointment_id = ?
    ORDER BY c.updated_at DESC, c.created_at DESC
    LIMIT 1
    """
    cursor.execute(query, (consult_id, consult_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    logo_path = r"C:\Users\milaa\Desktop\Navachis\C_M_S\frontend-web\src\assets\logo.png"
    if os.path.exists(logo_path):
        page.insert_image(fitz.Rect(40, 25, 170, 70), filename=logo_path)

    # Top Right Header Info (Customer ID & Date)
    cust_id_str = f"Customer ID: #{row['patient_id'][:8].upper()}"
    date_str = f"Date: {row['appointment_date']}"
    page.insert_text(fitz.Point(380, 45), cust_id_str, fontname="Helvetica-Bold", fontsize=10)
    page.insert_text(fitz.Point(380, 60), date_str, fontname="Helvetica", fontsize=10)

    # Top Header Divider Line
    page.draw_line(fitz.Point(40, 80), fitz.Point(555, 80), color=(0.1, 0.1, 0.1), width=1.5)

    y = 110

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
    
    y += 15

    # ==========================================
    # SECTION 1: CUSTOMER ENTRIES
    # ==========================================
    page, y = write_text(page, doc, "1. CUSTOMER ENTRIES", left_x, y, bold=True, size=12)
    y += 4

    # Parse Customer Symptoms & Notes
    raw_symptoms = row['symptoms'] or ""
    cust_symptoms = "None"
    cust_notes = "None"

    if " | Note: " in raw_symptoms:
        parts = raw_symptoms.split(" | Note: ")
        if parts[0].strip() and parts[0].strip() != "None reported":
            cust_symptoms = parts[0].strip()
        if parts[1].strip() and parts[1].strip().lower() not in ["none", "null"]:
            cust_notes = parts[1].strip()
    elif raw_symptoms.startswith("Note: "):
        note_val = raw_symptoms.replace("Note: ", "").strip()
        if note_val and note_val.lower() not in ["none", "null"]:
            cust_notes = note_val
    elif raw_symptoms.strip() and raw_symptoms.strip() != "None reported" and raw_symptoms.strip() != "General Walk-in Consultation":
        cust_symptoms = raw_symptoms.strip()

    if cust_notes == "None" and row['doctor_notes']:
        dn = row['doctor_notes']
        if "Patient Note:" in dn:
            p_note = dn.split("Patient Note:")[1].split("|")[0].split("\n")[0].strip()
            if p_note and p_note.lower() not in ["none", "null", ""]:
                cust_notes = p_note

    page, y = write_text(page, doc, "Symptoms:", left_x + 10, y, bold=True, size=10)
    page, y = insert_wrapped_text(page, doc, cust_symptoms, left_x + 20, y, size=10)
    y += 4

    page, y = write_text(page, doc, "Notes to the Doctor:", left_x + 10, y, bold=True, size=10)
    page, y = insert_wrapped_text(page, doc, cust_notes, left_x + 20, y, size=10)
    y += 15

    # ==========================================
    # SECTION 2: DOCTOR PRESCRIPTION
    # ==========================================
    page, y = write_text(page, doc, "2. DOCTOR PRESCRIPTION", left_x, y, bold=True, size=12)
    y += 4

    # 1. Diagnosis / Notes
    raw_diag = (row['diagnosis'] or "").strip()
    doc_diagnosis = raw_diag if (raw_diag and raw_diag.lower() != "pending consultation") else "None"
    page, y = write_text(page, doc, "Diagnosis / Notes:", left_x + 10, y, bold=True, size=10)
    page, y = insert_wrapped_text(page, doc, doc_diagnosis, left_x + 20, y, size=10)
    y += 4

    # 2. Medication Details & Lab Tests from prescriptions table
    cursor.execute("SELECT notes FROM prescriptions WHERE consultation_id = ?", (row['consult_id'],))
    p_rows = cursor.fetchall()
    medication_list = []
    prescribed_lab_tests = []
    
    for pr in p_rows:
        if pr and pr['notes']:
            text = pr['notes'].strip()
            if "LAB_TESTS:" in text:
                parts = text.split("LAB_TESTS:")
                if parts[0].strip() and not parts[0].strip().startswith("Prescription & Clinical Directions"):
                    medication_list.append(parts[0].strip())
                for t in parts[1].strip().split(","):
                    t_clean = t.strip()
                    if t_clean and t_clean not in prescribed_lab_tests:
                        prescribed_lab_tests.append(t_clean)
            elif text and not text.startswith("Prescription & Clinical Directions"):
                medication_list.append(text)

    doc_medications = "\n".join(medication_list) if medication_list else "None"
    page, y = write_text(page, doc, "Medication Details:", left_x + 10, y, bold=True, size=10)
    page, y = insert_wrapped_text(page, doc, doc_medications, left_x + 20, y, size=10)
    y += 4

    # 3. Lab Tests (selected by the doctor for this specific patient)
    lab_tests_list = []
    for t_clean in prescribed_lab_tests:
        if t_clean and t_clean not in lab_tests_list:
            lab_tests_list.append(t_clean)

    cursor.execute("""
        SELECT DISTINCT lt.test_name 
        FROM lab_reports lr
        JOIN laboratory_tests lt ON lr.test_id = lt.id
        WHERE lr.patient_id = ?
    """, (row['patient_id'],))
    db_tests = cursor.fetchall()
    for t in db_tests:
        if t['test_name'] and t['test_name'] not in lab_tests_list:
            lab_tests_list.append(t['test_name'])

    page, y = write_text(page, doc, "Lab Tests:", left_x + 10, y, bold=True, size=10)
    if lab_tests_list:
        for t_name in lab_tests_list:
            page, y = write_text(page, doc, f"- {t_name}", left_x + 20, y, size=10)
    else:
        page, y = write_text(page, doc, "None", left_x + 20, y, size=10)
    y += 4

    # 4. Directions for Use
    raw_doc_notes = (row['doctor_notes'] or "").strip()
    doc_directions = "None"
    if "\nDirections:" in raw_doc_notes:
        dirs = raw_doc_notes.split("\nDirections:")[1].strip()
        if dirs and dirs.lower() != "none":
            doc_directions = dirs
    elif raw_doc_notes and "Follow doctor directions" not in raw_doc_notes:
        if "Patient Note:" in raw_doc_notes and "| Preference:" in raw_doc_notes:
            pref_split = raw_doc_notes.split("| Preference:")
            if len(pref_split) > 1 and pref_split[1].strip():
                clean_pref_rest = pref_split[1].strip()
                lines = [l.strip() for l in clean_pref_rest.split("\n") if l.strip()]
                if len(lines) > 1 and lines[1] and lines[1] not in ["cancel", "reschedule"]:
                    doc_directions = lines[1]
        elif not raw_doc_notes.startswith("Patient Note:"):
            doc_directions = raw_doc_notes

    page, y = write_text(page, doc, "Directions for Use:", left_x + 10, y, bold=True, size=10)
    page, y = insert_wrapped_text(page, doc, doc_directions, left_x + 20, y, size=10)

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

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    logo_path = r"C:\Users\milaa\Desktop\Navachis\C_M_S\frontend-web\src\assets\logo.png"
    if os.path.exists(logo_path):
        page.insert_image(fitz.Rect(40, 25, 170, 70), filename=logo_path)

    req_date = str(p['req_date']) if p['req_date'] else '2026-07-13'

    # Top Right Header Info (Customer ID & Date)
    cust_id_str = f"Customer ID: #{p['patient_id'][:8].upper()}"
    date_str = f"Date: {req_date}"
    page.insert_text(fitz.Point(380, 45), cust_id_str, fontname="Helvetica-Bold", fontsize=10)
    page.insert_text(fitz.Point(380, 60), date_str, fontname="Helvetica", fontsize=10)

    # Top Header Divider Line
    page.draw_line(fitz.Point(40, 80), fitz.Point(555, 80), color=(0.1, 0.1, 0.1), width=1.5)

    y = 110

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
