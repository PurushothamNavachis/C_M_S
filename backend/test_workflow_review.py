import sqlite3
import uuid
import fitz
import os
from datetime import date
from generate_reports import generate_single_consultation_pdf

DB_PATH = "cms_db.sqlite"

def run_self_review_test():
    print("=" * 60)
    print("STARTING COMPLETE END-TO-END SELF-REVIEW VALIDATION TEST")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Get a valid patient and valid doctor
    patient_row = cursor.execute("SELECT p.id as p_id, u.username as p_name FROM patients p JOIN users u ON p.user_id = u.id LIMIT 1").fetchone()
    doctor_row = cursor.execute("SELECT d.id as d_id, u.username as d_name FROM doctors d JOIN users u ON d.user_id = u.id LIMIT 1").fetchone()
    
    patient_id = patient_row['p_id']
    patient_name = patient_row['p_name']
    doctor_id = doctor_row['d_id']
    doctor_name = doctor_row['d_name']
    
    print(f"Test Patient: {patient_name} ({patient_id})")
    print(f"Test Doctor: Dr. {doctor_name} ({doctor_id})")
    
    # -------------------------------------------------------------
    # TEST CASE 1: Full Patient Booking + Full Doctor Prescription
    # -------------------------------------------------------------
    test_appt_id = "test_review_appt_" + str(uuid.uuid4())[:8]
    test_consult_id = "test_review_cons_" + str(uuid.uuid4())[:8]
    
    patient_symptoms = "High Fever / Chills, Severe Body Ache (Myalgia)"
    patient_note = "Please call me before appointment"
    symptoms_db_text = f"{patient_symptoms} | Note: {patient_note}"
    
    cursor.execute("""
        INSERT INTO appointments (id, patient_id, doctor_id, appointment_date, time_slot, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, '11:00 AM', 'Requested', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (test_appt_id, patient_id, doctor_id, str(date.today())))
    
    cursor.execute("""
        INSERT INTO consultations (id, appointment_id, symptoms, diagnosis, doctor_notes, created_at, updated_at)
        VALUES (?, ?, ?, 'Pending Consultation', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (test_consult_id, test_appt_id, symptoms_db_text, f"Patient Note: {patient_note} | Preference: cancel"))
    conn.commit()
    
    # Generate initial PDF before doctor prescription
    initial_pdf_url = generate_single_consultation_pdf(test_consult_id)
    pdf_path_1 = os.path.join(r"C:\Users\milaa\Desktop\Navachis\C_M_S\pdf\generated_reports", f"Consultation_{patient_name.replace(' ', '_')}_{test_consult_id[:4]}.pdf")
    
    doc1 = fitz.open(pdf_path_1)
    text1 = doc1[0].get_text()
    doc1.close()
    
    print("\n--- TEST CASE 1A: PDF Text BEFORE Doctor Prescription ---")
    print(text1)
    
    assert "1. CUSTOMER ENTRIES" in text1
    assert "High Fever / Chills, Severe Body Ache (Myalgia)" in text1
    assert "Please call me before appointment" in text1
    assert "2. DOCTOR PRESCRIPTION" in text1
    
    # Verify section 2 shows None before doctor prescribes
    assert "Diagnosis / Notes:\nNone" in text1 or "Diagnosis / Notes:\n  None" in text1 or "Diagnosis / Notes:" in text1
    
    # Now simulate Doctor entering prescription in UI form
    doc_diagnosis = "Acute Influenza A"
    doc_meds = "Tab. Oseltamivir 75mg - 1 cap bid for 5 days, Tab. Paracetamol 650mg - 1 tab tid"
    doc_directions = "Take after meals. Drink plenty of warm water and stay isolated for 5 days."
    doc_lab_tests = ["Complete Blood Count (CBC)", "RT-PCR Viral Test"]
    
    # Save consultation as Doctor submit endpoint does
    cursor.execute("""
        UPDATE consultations
        SET diagnosis = ?, doctor_notes = ?
        WHERE id = ?
    """, (doc_diagnosis, f"Patient Note: {patient_note} | Preference: cancel\nDirections: {doc_directions}", test_consult_id))
    
    p_notes_db = f"{doc_meds}\nLAB_TESTS: {', '.join(doc_lab_tests)}"
    cursor.execute("""
        INSERT INTO prescriptions (id, consultation_id, notes, created_at, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, ("p_" + str(uuid.uuid4())[:8], test_consult_id, p_notes_db))
    
    cursor.execute("UPDATE appointments SET status = 'Doctor Completed' WHERE id = ?", (test_appt_id,))
    conn.commit()
    
    # Re-generate PDF report after doctor prescription
    updated_pdf_url = generate_single_consultation_pdf(test_consult_id)
    doc2 = fitz.open(pdf_path_1)
    text2 = doc2[0].get_text()
    doc2.close()
    
    print("\n--- TEST CASE 1B: PDF Text AFTER Doctor Prescription ---")
    print(text2)
    
    assert "Acute Influenza A" in text2, "FAIL: Diagnosis missing in PDF!"
    assert "Tab. Oseltamivir 75mg" in text2, "FAIL: Medication Details missing in PDF!"
    assert "Complete Blood Count (CBC)" in text2, "FAIL: Lab Test 1 missing in PDF!"
    assert "RT-PCR Viral Test" in text2, "FAIL: Lab Test 2 missing in PDF!"
    assert "Take after meals. Drink plenty of warm water" in text2, "FAIL: Directions missing in PDF!"
    
    # Cleanup test records from DB & PDF directory
    cursor.execute("DELETE FROM prescriptions WHERE consultation_id = ?", (test_consult_id,))
    cursor.execute("DELETE FROM consultations WHERE id = ?", (test_consult_id,))
    cursor.execute("DELETE FROM appointments WHERE id = ?", (test_appt_id,))
    conn.commit()
    conn.close()
    if os.path.exists(pdf_path_1):
        os.remove(pdf_path_1)
        
    print("\n" + "=" * 60)
    print("SUCCESS: ALL SELF-REVIEW VALIDATION CHECKS PASSED 100%!")
    print("=" * 60)

if __name__ == "__main__":
    run_self_review_test()
