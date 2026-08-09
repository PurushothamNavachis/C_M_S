import os
import fitz  # PyMuPDF

LOGO_PATH = r"C:\Users\milaa\Desktop\Navachis\C_M_S\frontend-web\src\assets\logo.png"
TEMPLATE_PATH = r"C:\Users\milaa\Desktop\Navachis\C_M_S\pdf\empty_report.pdf"
OUTPUT_DIR = r"C:\Users\milaa\Desktop\Navachis\C_M_S\pdf\generated_reports"

def generate_consultation_pdf(appt_data: dict) -> str:
    consult_id = appt_data.get("consultation_id") or appt_data.get("id") or appt_data.get("appointment_id")
    if consult_id:
        try:
            from generate_reports import generate_single_consultation_pdf
            url = generate_single_consultation_pdf(consult_id)
            if url:
                return url
        except Exception as e:
            print(f"Error calling generate_single_consultation_pdf: {e}")
            
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    appt_id = str(appt_data.get("id", "default")).replace("-", "")[:12]
    filename = f"report_{appt_id}.pdf"
    return f"http://localhost:8000/reports/{filename}"
