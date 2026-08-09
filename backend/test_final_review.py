import sqlite3
import uuid
import fitz
import os
from datetime import date
from generate_reports import generate_single_consultation_pdf

DB_PATH = "cms_db.sqlite"

def run_final_review_test():
    print("=" * 60)
    print("STARTING COMPLETE AUTOMATED SELF-REVIEW VALIDATION TEST")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get test patient & doctor
    patient_row = cursor.execute("SELECT p.id as p_id, u.username as p_name FROM patients p JOIN users u ON p.user_id = u.id LIMIT 1").fetchone()
    doctor_row = cursor.execute("SELECT d.id as d_id, u.username as d_name FROM doctors d JOIN users u ON d.user_id = u.id LIMIT 1").fetchone()
    
    patient_id = patient_row['p_id']
    patient_name = patient_row['p_name']
    doctor_id = doctor_row['d_id']
    doctor_name = doctor_row['d_name']
    
    test_appt_id = "test_review_appt_" + str(uuid.uuid4())[:8]
    test_consult_id = "test_review_cons_" + str(uuid.uuid4())[:8]
    
    # 1. Patient Booking Details
    patient_symptoms = "Cold and Congestion, High Fever / Chills"
    patient_note = "Need urgent morning appointment"
    symptoms_db_text = f"{patient_symptoms} | Note: {patient_note}"
    
    cursor.execute("""
        INSERT INTO appointments (id, patient_id, doctor_id, appointment_date, time_slot, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, '10:00 AM', 'Requested', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (test_appt_id, patient_id, doctor_id, str(date.today())))
    
    cursor.execute("""
        INSERT INTO consultations (id, appointment_id, symptoms, diagnosis, doctor_notes, created_at, updated_at)
        VALUES (?, ?, ?, 'Pending Consultation', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (test_consult_id, test_appt_id, symptoms_db_text, f"Patient Note: {patient_note} | Preference: cancel"))
    conn.commit()
    
    # Check 1: Initial PDF Report
    pdf_url_1 = generate_single_consultation_pdf(test_consult_id)
    pdf_path = os.path.join(r"C:\Users\milaa\Desktop\Navachis\C_M_S\pdf\generated_reports", f"Consultation_{patient_name.replace(' ', '_')}_{test_consult_id[:4]}.pdf")
    
    doc1 = fitz.open(pdf_path)
    text1 = doc1[0].get_text()
    doc1.close()
    
    print("\n[PHASE 1] Initial PDF Text (Patient booked, Doctor not prescribed yet):")
    print("-" * 50)
    print(text1)
    print("-" * 50)
    
    assert "1. CUSTOMER ENTRIES" in text1
    assert "Cold and Congestion, High Fever / Chills" in text1
    assert "Need urgent morning appointment" in text1
    assert "2. DOCTOR PRESCRIPTION" in text1
    
    # 2. Doctor fills out prescription form in Doctor Portal
    doc_diagnosis = "Viral Upper Respiratory Tract Infection"
    doc_meds = "Tab. Paracetamol 650mg - 1 tab tid, Cap. Amoxicillin 500mg - 1 cap tid"
    doc_directions = "Take after meals. Rest well for 3 days and drink warm water."
    doc_lab_tests = ["Complete Blood Count (CBC)", "C-Reactive Protein (CRP)"]
    
    # Simulate API save_consultation logic
    if "Patient Note:" in f"Patient Note: {patient_note} | Preference: cancel":
        updated_doc_notes = f"Patient Note: {patient_note} | Preference: cancel\nDirections: {doc_directions}"
    else:
        updated_doc_notes = doc_directions
        
    cursor.execute("""
        UPDATE consultations
        SET symptoms = ?, diagnosis = ?, doctor_notes = ?
        WHERE id = ?
    """, (symptoms_db_text, doc_diagnosis, updated_doc_notes, test_consult_id))
    
    p_notes_db = f"{doc_meds}\nLAB_TESTS: {', '.join(doc_lab_tests)}"
    cursor.execute("""
        INSERT INTO prescriptions (id, consultation_id, notes, created_at, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, ("p_" + str(uuid.uuid4())[:8], test_consult_id, p_notes_db))
    
    cursor.execute("UPDATE appointments SET status = 'Doctor Completed' WHERE id = ?", (test_appt_id,))
    conn.commit()
    
    # Check 2: Updated PDF Report after Doctor prescribes
    pdf_url_2 = generate_single_consultation_pdf(test_consult_id)
    doc2 = fitz.open(pdf_path)
    text2 = doc2[0].get_text()
    doc2.close()
    
    print("\n[PHASE 2] Updated PDF Text (After Doctor prescribed):")
    print("-" * 50)
    print(text2)
    print("-" * 50)
    
    # Assertions for Phase 2
    assert "Cold and Congestion, High Fever / Chills" in text2, "FAIL: Patient symptoms lost after doctor prescription!"
    assert "Need urgent morning appointment" in text2, "FAIL: Patient note lost after doctor prescription!"
    assert "Viral Upper Respiratory Tract Infection" in text2, "FAIL: Doctor diagnosis missing in PDF!"
    assert "Tab. Paracetamol 650mg" in text2, "FAIL: Doctor medication details missing in PDF!"
    assert "Complete Blood Count (CBC)" in text2, "FAIL: Doctor lab test 1 missing in PDF!"
    assert "C-Reactive Protein (CRP)" in text2, "FAIL: Doctor lab test 2 missing in PDF!"
    assert "Take after meals. Rest well for 3 days" in text2, "FAIL: Doctor directions missing in PDF!"
    
    # Clean up test rows
    cursor.execute("DELETE FROM prescriptions WHERE consultation_id = ?", (test_consult_id,))
    cursor.execute("DELETE FROM consultations WHERE id = ?", (test_consult_id,))
    cursor.execute("DELETE FROM appointments WHERE id = ?", (test_appt_id,))
    conn.commit()
    conn.close()
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        
    print("\n" + "=" * 60)
    print("SUCCESS: SELF-REVIEW VERIFICATION PASSED WITH 0 ERRORS!")
    print("=" * 60)

if __name__ == "__main__":
    run_final_review_test()
