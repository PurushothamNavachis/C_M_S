import uuid
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import get_password_hash
from app.dependencies.auth import get_current_user
from app.models import (
    User, Role, Patient, Doctor, Appointment, Consultation, Vitals,
    Medicine, Prescription, PrescriptionItem, LaboratoryTest, LabReport, Bill, Payment
)
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/clinical", tags=["Clinical Operations"])

# --- SCHEMAS ---
class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    phone: str
    email: EmailStr
    blood_group: str | None = None
    address: str | None = None
    booking_source: str | None = "Frontdesk"

class AppointmentCreate(BaseModel):
    patient_name: str
    doctor_name: str
    time_slot: str
    status: str = "Scheduled"

class ConsultationCreate(BaseModel):
    appointment_id: str
    symptoms: str | None = None
    diagnosis: str | None = None
    doctor_notes: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    blood_pressure: str | None = None
    temperature_f: float | None = None
    prescription_notes: str | None = None
    lab_tests: list[str] = []

# --- ENDPOINTS ---

@router.post("/patients")
async def register_patient(schema: PatientCreate, db: AsyncSession = Depends(get_db)):
    # 1. Check if user already exists
    stmt = select(User).where(User.email == schema.email)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    # 2. Get/Create Patient Role
    stmt_role = select(Role).where(Role.name == "PATIENT")
    role_res = await db.execute(stmt_role)
    role = role_res.scalar_one_or_none()
    if not role:
        role = Role(id=str(uuid.uuid4()), name="PATIENT", description="Patient user role")
        db.add(role)
        await db.flush()

    # 3. Create User
    new_user = User(
        id=str(uuid.uuid4()),
        email=schema.email,
        username=schema.name.replace(" ", "").lower() + str(uuid.uuid4())[:4],
        hashed_password=get_password_hash("patient_default_pass_123"), # default temp pass
        role_id=role.id,
        is_active=True
    )
    db.add(new_user)
    await db.flush()

    # 4. Create Patient profile
    # Calculate DOB from age roughly
    dob_year = datetime.now().year - schema.age
    dummy_dob = date(dob_year, 1, 1)

    new_patient = Patient(
        id=str(uuid.uuid4()),
        user_id=new_user.id,
        dob=dummy_dob,
        gender=schema.gender,
        blood_group=schema.blood_group,
        phone=schema.phone,
        address=schema.address,
        booking_source=schema.booking_source or "Frontdesk"
    )
    db.add(new_patient)
    await db.commit()

    return {"message": "Patient registered successfully", "patient_id": new_patient.id, "name": schema.name}

@router.get("/patients")
async def list_patients(db: AsyncSession = Depends(get_db)):
    stmt = select(Patient).options(selectinload(Patient.user))
    res = await db.execute(stmt)
    patients = res.scalars().all()
    return [
        {
            "id": p.id,
            "user_id": p.user_id,
            "name": p.user.username if p.user else "Patient",
            "email": p.user.email if p.user else "",
            "phone": p.phone,
            "gender": p.gender,
            "blood_group": p.blood_group,
            "address": p.address,
            "plain_password": p.user.plain_password if p.user else "patient123",
            "booking_source": getattr(p, "booking_source", None) or "Online Booking"
        }
        for p in patients
    ]

@router.post("/appointments")
async def create_appointment(schema: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    # Find patient
    stmt_patient = select(Patient).join(User).where(User.username.ilike(schema.patient_name) | User.email.ilike(schema.patient_name))
    res_p = await db.execute(stmt_patient)
    patient = res_p.scalar_one_or_none()
    
    # If not found, create a placeholder patient user
    if not patient:
        stmt_role = select(Role).where(Role.name == "PATIENT")
        role_res = await db.execute(stmt_role)
        role = role_res.scalar_one_or_none()
        if not role:
            role = Role(id=str(uuid.uuid4()), name="PATIENT", description="Patient user role")
            db.add(role)
            await db.flush()

        new_user = User(
            id=str(uuid.uuid4()),
            email=f"{schema.patient_name.replace(' ', '').lower()}@placeholder.com",
            username=schema.patient_name.replace(" ", "").lower(),
            hashed_password=get_password_hash("patient_default_pass_123"),
            role_id=role.id,
            is_active=True
        )
        db.add(new_user)
        await db.flush()

        patient = Patient(
            id=str(uuid.uuid4()),
            user_id=new_user.id,
            dob=date(1990, 1, 1),
            gender="Male",
            phone="555-0100"
        )
        db.add(patient)
        await db.flush()

    # Find or Create Doctor placeholder
    stmt_doc = select(Doctor).join(User).where(User.username.ilike(schema.doctor_name))
    res_d = await db.execute(stmt_doc)
    doctor = res_d.scalars().first()

    if not doctor:
        stmt_role_doc = select(Role).where(Role.name == "DOCTOR")
        role_res_doc = await db.execute(stmt_role_doc)
        role_doc = role_res_doc.scalar_one_or_none()
        if not role_doc:
            role_doc = Role(id=str(uuid.uuid4()), name="DOCTOR", description="Doctor role")
            db.add(role_doc)
            await db.flush()

        new_doc_user = User(
            id=str(uuid.uuid4()),
            email=f"{schema.doctor_name.replace(' ', '').lower()}@clinic.com",
            username=schema.doctor_name.replace(" ", "").lower(),
            hashed_password=get_password_hash("doctor_default_pass_123"),
            role_id=role_doc.id,
            is_active=True
        )
        db.add(new_doc_user)
        await db.flush()

        doctor = Doctor(
            id=str(uuid.uuid4()),
            user_id=new_doc_user.id,
            specialization="General Practice",
            license_number=f"LIC-{str(uuid.uuid4())[:8]}",
            consultation_fee=50.0
        )
        db.add(doctor)
        await db.flush()

    new_appt = Appointment(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=date.today(),
        time_slot=schema.time_slot,
        status=schema.status
    )
    db.add(new_appt)
    await db.commit()

    return {"message": "Appointment created", "appointment_id": new_appt.id}

@router.get("/appointments")
async def list_appointments(db: AsyncSession = Depends(get_db)):
    stmt = select(Appointment).options(
        selectinload(Appointment.patient).selectinload(Patient.user),
        selectinload(Appointment.doctor).selectinload(Doctor.user),
        selectinload(Appointment.consultation)
    ).order_by(Appointment.appointment_date.desc(), Appointment.time_slot.desc())
    res = await db.execute(stmt)
    appts = list(res.scalars().all())
    status_order = {
        "Doctor Completed": 1,
        "Requested": 2,
        "Checked In": 2,
        "Scheduled": 3,
        "Finalized": 4,
        "Completed": 4,
        "Cancelled": 5
    }
    appts.sort(key=lambda a: (status_order.get(a.status, 99), str(a.appointment_date), a.time_slot))
    return [
        {
            "id": a.id,
            "patientName": a.patient.user.username if (a.patient and a.patient.user) else "Patient",
            "patientId": a.patient_id,
            "patientMobile": a.patient.phone if a.patient else "",
            "doctorName": a.doctor.user.username if (a.doctor and a.doctor.user) else "Unassigned",
            "doctor_id": a.doctor_id,
            "doctorUserId": a.doctor.user_id if (a.doctor and a.doctor.user_id) else None,
            "doctorSpecialization": a.doctor.specialization if a.doctor else "N/A",
            "date": str(a.appointment_date),
            "requestedDate": a.created_at.strftime("%Y-%m-%d") if (hasattr(a, "created_at") and a.created_at) else str(a.appointment_date),
            "time": a.time_slot,
            "status": a.status,
            "symptoms": a.consultation.symptoms if a.consultation else "",
            "diagnosis": a.consultation.diagnosis if a.consultation else "",
            "doctorNotes": a.consultation.doctor_notes if a.consultation else "",
            "consultationId": a.consultation.id if a.consultation else None,
            "reportUrl": a.consultation.uploaded_file_url if a.consultation else None
        }
        for a in appts
    ]

@router.get("/patients/{patient_id}/appointments")
async def get_patient_appointments(patient_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Appointment).where(Appointment.patient_id == patient_id).options(
        selectinload(Appointment.patient).selectinload(Patient.user),
        selectinload(Appointment.doctor).selectinload(Doctor.user),
        selectinload(Appointment.consultation)
    ).order_by(Appointment.appointment_date.desc())
    res = await db.execute(stmt)
    appts = list(res.scalars().all())
    return [
        {
            "id": a.id,
            "patientName": a.patient.user.username if (a.patient and a.patient.user) else "Patient",
            "patientId": a.patient_id,
            "doctorName": a.doctor.user.username if (a.doctor and a.doctor.user) else "Unassigned Doctor",
            "doctorSpecialization": a.doctor.specialization if a.doctor else "General Physician",
            "date": str(a.appointment_date),
            "time": a.time_slot,
            "status": a.status,
            "symptoms": a.consultation.symptoms if a.consultation else "",
            "preference": a.consultation.doctor_notes if a.consultation else "",
            "patientNotes": a.consultation.doctor_notes if a.consultation else ""
        }
        for a in appts
    ]

@router.patch("/appointments/{appointment_id}/status")
async def update_appointment_status(appointment_id: str, status: str, db: AsyncSession = Depends(get_db)):
    stmt = update(Appointment).where(Appointment.id == appointment_id).values(status=status)
    await db.execute(stmt)
    await db.commit()
    return {"message": "Appointment status updated"}

@router.post("/consultations")
async def save_consultation(schema: ConsultationCreate, db: AsyncSession = Depends(get_db)):
    # 1. Upsert Consultation
    stmt = select(Consultation).where(Consultation.appointment_id == schema.appointment_id)
    res = await db.execute(stmt)
    existing_consult = res.scalar_one_or_none()
    
    if existing_consult:
        # Preserve original patient note suffix in existing_consult.symptoms if present
        if existing_consult.symptoms and " | Note: " in existing_consult.symptoms:
            note_suffix = " | Note: " + existing_consult.symptoms.split(" | Note: ")[1]
            clean_sym = (schema.symptoms or "").split(" | Note: ")[0].strip()
            if clean_sym:
                existing_consult.symptoms = f"{clean_sym}{note_suffix}"
        elif schema.symptoms and schema.symptoms.strip():
            existing_consult.symptoms = schema.symptoms.strip()

        if schema.diagnosis and schema.diagnosis.strip():
            existing_consult.diagnosis = schema.diagnosis.strip()

        if schema.doctor_notes and schema.doctor_notes.strip():
            if "Patient Note:" in (existing_consult.doctor_notes or ""):
                p_note_base = existing_consult.doctor_notes.split("\nDirections:")[0]
                existing_consult.doctor_notes = f"{p_note_base}\nDirections: {schema.doctor_notes.strip()}"
            else:
                existing_consult.doctor_notes = schema.doctor_notes.strip()
        consult_id = existing_consult.id
    else:
        consult_id = str(uuid.uuid4())
        new_consult = Consultation(
            id=consult_id,
            appointment_id=schema.appointment_id,
            symptoms=schema.symptoms or "None reported",
            diagnosis=schema.diagnosis or "None",
            doctor_notes=schema.doctor_notes or "None"
        )
        db.add(new_consult)
        
    await db.flush()

    # 2. Save Vitals if provided
    if schema.height_cm or schema.weight_kg or schema.blood_pressure or schema.temperature_f:
        new_vitals = Vitals(
            id=str(uuid.uuid4()),
            consultation_id=consult_id,
            height_cm=schema.height_cm,
            weight_kg=schema.weight_kg,
            blood_pressure=schema.blood_pressure,
            temperature_f=schema.temperature_f
        )
        db.add(new_vitals)

    # 3. Save Prescription if notes are provided
    if schema.prescription_notes or schema.lab_tests:
        p_notes = schema.prescription_notes or ""
        if schema.lab_tests:
            p_notes += f"\nLAB_TESTS: {', '.join(schema.lab_tests)}"

        stmt_p = select(Prescription).where(Prescription.consultation_id == consult_id)
        res_p = await db.execute(stmt_p)
        existing_p = res_p.scalar_one_or_none()
        if existing_p:
            existing_p.notes = p_notes
        else:
            new_prescription = Prescription(
                id=str(uuid.uuid4()),
                consultation_id=consult_id,
                notes=p_notes
            )
            db.add(new_prescription)

    # 3b. Create LabReport entries for each selected test
    if schema.lab_tests:
        stmt_apt = select(Appointment).where(Appointment.id == schema.appointment_id)
        res_apt = await db.execute(stmt_apt)
        apt_obj = res_apt.scalar_one_or_none()
        if apt_obj and apt_obj.patient_id:
            for test_name in schema.lab_tests:
                if not test_name or not test_name.strip():
                    continue
                test_clean = test_name.strip()
                stmt_lt = select(LaboratoryTest).where(LaboratoryTest.test_name.ilike(test_clean))
                res_lt = await db.execute(stmt_lt)
                lt_obj = res_lt.scalar_one_or_none()
                if not lt_obj:
                    lt_obj = LaboratoryTest(
                        id=str(uuid.uuid4()),
                        test_name=test_clean,
                        category="Diagnostic",
                        price=100.0
                    )
                    db.add(lt_obj)
                    await db.flush()

                new_lr = LabReport(
                    id=str(uuid.uuid4()),
                    patient_id=apt_obj.patient_id,
                    test_id=lt_obj.id,
                    status="Requested/Pending Sample Collection"
                )
                db.add(new_lr)

    # 4. Mark appointment completed
    stmt = update(Appointment).where(Appointment.id == schema.appointment_id).values(status="Doctor Completed")
    await db.execute(stmt)
    await db.commit()
    
    # Generate updated PDF report with the newly submitted genuine consultation & prescription data
    pdf_url = None
    try:
        from generate_reports import generate_single_consultation_pdf
        pdf_url = generate_single_consultation_pdf(consult_id)
    except Exception as e:
        print(f"Error generating PDF report during save_consultation: {e}")

    return {
        "message": "Consultation records saved successfully and submitted to receptionist",
        "consultation_id": consult_id,
        "uploadedFileUrl": pdf_url
    }


# --- PATIENT ACTIONS ENDPOINTS ---

class ConsultationRequest(BaseModel):
    department: str | None = None
    symptoms: list[str] = []
    date: str
    time: str
    preference: str
    patient_note: str | None = None

class LabRequest(BaseModel):
    tests: list[str]

@router.post("/patient-actions/consultation-request")
async def create_patient_consultation_request(
    schema: ConsultationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Find or auto-create patient profile associated with current user
    stmt_p = select(Patient).where(Patient.user_id == current_user.id)
    res_p = await db.execute(stmt_p)
    patient = res_p.scalar_one_or_none()
    if not patient:
        patient = Patient(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            dob=date(1990, 1, 1),
            gender="Not Specified",
            phone=getattr(current_user, "mobile_number", None) or "8919527429"
        )
        db.add(patient)
        await db.flush()
        
    # 2. Find doctor or fallback to existing doctor/create placeholder safely
    spec_raw = (schema.department or "").strip()
    if not spec_raw or "None Selected" in spec_raw or "General Practice" in spec_raw:
        spec = "General Physician"
    else:
        spec = spec_raw
        
    stmt_d = select(Doctor).where(Doctor.specialization.ilike(f"%{spec}%"))
    res_d = await db.execute(stmt_d)
    doctor = res_d.scalars().first()
    
    if not doctor:
        stmt_d_any = select(Doctor)
        res_d_any = await db.execute(stmt_d_any)
        doctor = res_d_any.scalars().first()
        
    if not doctor:
        stmt_role_doc = select(Role).where(Role.name == "DOCTOR")
        role_res_doc = await db.execute(stmt_role_doc)
        role_doc = role_res_doc.scalar_one_or_none()
        if not role_doc:
            role_doc = Role(id=str(uuid.uuid4()), name="DOCTOR", description="Doctor role")
            db.add(role_doc)
            await db.flush()
            
        unique_suffix = str(uuid.uuid4())[:8]
        doc_uname = f"dr_auto_{unique_suffix}"
        new_doc_user = User(
            id=str(uuid.uuid4()),
            email=f"{doc_uname}@clinic.com",
            username=doc_uname,
            hashed_password=get_password_hash("doctor_default_pass_123"),
            role_id=role_doc.id,
            is_active=True
        )
        db.add(new_doc_user)
        await db.flush()
        
        doctor = Doctor(
            id=str(uuid.uuid4()),
            user_id=new_doc_user.id,
            specialization=spec,
            license_number=f"LIC-{unique_suffix}",
            consultation_fee=50.0
        )
        db.add(doctor)
        await db.flush()
        
    # 3. Parse Date
    try:
        appt_date = datetime.strptime(schema.date, "%Y-%m-%d").date()
    except ValueError:
        appt_date = date.today()
        
    # 4. Create Appointment
    new_appt = Appointment(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=appt_date,
        time_slot=schema.time,
        status="Requested"
    )
    db.add(new_appt)
    await db.flush()
    
    # 5. Create Consultation record with symptoms & optional patient note
    symptoms_text = ", ".join(schema.symptoms)
    if schema.patient_note and schema.patient_note.strip():
        if symptoms_text:
            symptoms_text += f" | Note: {schema.patient_note.strip()}"
        else:
            symptoms_text = f"Note: {schema.patient_note.strip()}"

    new_consult = Consultation(
        id=str(uuid.uuid4()),
        appointment_id=new_appt.id,
        symptoms=symptoms_text,
        diagnosis="Pending Consultation",
        doctor_notes=f"Patient Note: {schema.patient_note.strip() if schema.patient_note else 'None'} | Preference: {schema.preference}"
    )
    db.add(new_consult)
    await db.commit()
    
    # Generate initial PDF report immediately with 2-section layout
    try:
        from generate_reports import generate_single_consultation_pdf
        pdf_url = generate_single_consultation_pdf(new_consult.id)
        new_consult.uploaded_file_url = pdf_url
        await db.commit()
    except Exception as e:
        print(f"Error generating initial PDF report in booking: {e}")

    return {"message": "Consultation Request saved successfully in database", "appointment_id": new_appt.id}

@router.post("/patient-actions/lab-request")
async def create_patient_lab_request(
    schema: LabRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Find or auto-create patient profile associated with current user
    stmt_p = select(Patient).where(Patient.user_id == current_user.id)
    res_p = await db.execute(stmt_p)
    patient = res_p.scalar_one_or_none()
    if not patient:
        patient = Patient(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            dob=date(1990, 1, 1),
            gender="Not Specified",
            phone=getattr(current_user, "mobile_number", None) or "8919527429"
        )
        db.add(patient)
        await db.flush()
        
    created_reports = []
    
    # 2. Iterate through each test requested
    for tname in schema.tests:
        # Find or create LaboratoryTest
        stmt_t = select(LaboratoryTest).where(LaboratoryTest.test_name.ilike(tname))
        res_t = await db.execute(stmt_t)
        lab_test = res_t.scalar_one_or_none()
        
        if not lab_test:
            lab_test = LaboratoryTest(
                id=str(uuid.uuid4()),
                test_name=tname,
                description=f"Requested diagnostic lab test: {tname}",
                price=30.0
            )
            db.add(lab_test)
            await db.flush()
            
        # Create LabReport record
        report = LabReport(
            id=str(uuid.uuid4()),
            patient_id=patient.id,
            test_id=lab_test.id,
            result_value="Requested/Pending Sample Collection",
            uploaded_file_url=None
        )
        db.add(report)
        created_reports.append(report.id)
        
    await db.commit()
    return {"message": f"Successfully created {len(created_reports)} lab request records in database.", "report_ids": created_reports}

@router.get("/lab-requests")
async def list_lab_requests(db: AsyncSession = Depends(get_db)):
    stmt = select(LabReport).options(
        selectinload(LabReport.patient).selectinload(Patient.user),
        selectinload(LabReport.test)
    )
    res = await db.execute(stmt)
    reports = res.scalars().all()
    return [
        {
            "id": r.id,
            "patientName": r.patient.user.username,
            "testName": r.test.test_name,
            "status": r.result_value
        }
        for r in reports
    ]

@router.patch("/appointments/{appointment_id}/assign-doctor")
async def assign_doctor(
    appointment_id: str,
    doctor_id: str,
    time: str = None,
    time_slot: str = None,
    date: str = None,
    db: AsyncSession = Depends(get_db)
):
    # Validate doctor_id exists
    clean_doc_id = doctor_id.strip() if doctor_id else ""
    if not clean_doc_id or clean_doc_id in ("undefined", "null", "None"):
        stmt_d = select(Doctor)
        res_d = await db.execute(stmt_d)
        valid_doc = res_d.scalars().first()
        if valid_doc:
            clean_doc_id = valid_doc.id
        else:
            raise HTTPException(status_code=400, detail="No active doctor found to assign.")
    else:
        stmt_chk = select(Doctor).where(Doctor.id == clean_doc_id)
        res_chk = await db.execute(stmt_chk)
        if not res_chk.scalar_one_or_none():
            stmt_d = select(Doctor)
            res_d = await db.execute(stmt_d)
            valid_doc = res_d.scalars().first()
            if valid_doc:
                clean_doc_id = valid_doc.id

    values = {"doctor_id": clean_doc_id, "status": "Scheduled"}
    effective_time = time_slot or time
    if effective_time:
        values["time_slot"] = effective_time
    if date:
        try:
            values["appointment_date"] = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            pass
    stmt = update(Appointment).where(Appointment.id == appointment_id).values(**values)
    await db.execute(stmt)
    await db.commit()
    return {"message": "Doctor assigned and appointment scheduled"}

@router.patch("/lab-requests/{report_id}/status")
async def update_lab_request_status(report_id: str, status: str, db: AsyncSession = Depends(get_db)):
    stmt = update(LabReport).where(LabReport.id == report_id).values(result_value=status)
    await db.execute(stmt)
    await db.commit()
    return {"message": "Lab report status updated successfully"}

class LabReportUpdate(BaseModel):
    status: str | None = None
    uploaded_file_url: str | None = None

@router.patch("/lab-reports/{report_id}")
async def update_lab_report(report_id: str, schema: LabReportUpdate, db: AsyncSession = Depends(get_db)):
    values = {}
    if schema.status is not None:
        values["result_value"] = schema.status
    if schema.uploaded_file_url is not None:
        values["uploaded_file_url"] = schema.uploaded_file_url
        
    if values:
        stmt = update(LabReport).where(LabReport.id == report_id).values(**values)
        await db.execute(stmt)
        await db.commit()
    return {"message": "Lab report updated successfully"}

@router.get("/patients/{patient_id}/consultations")
async def get_patient_consultations(patient_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Consultation).join(Appointment).where(Appointment.patient_id == patient_id).options(
        selectinload(Consultation.appointment).selectinload(Appointment.doctor).selectinload(Doctor.user)
    )
    res = await db.execute(stmt)
    consultations = list(res.scalars().all())
    status_order = {
        "Doctor Completed": 1,
        "Requested": 2,
        "Checked In": 2,
        "Scheduled": 3,
        "Finalized": 4,
        "Completed": 4,
        "Cancelled": 5
    }
    consultations.sort(key=lambda c: (status_order.get(c.appointment.status, 99), str(c.appointment.appointment_date), c.appointment.time_slot))
    return [
        {
            "id": c.id,
            "date": str(c.appointment.appointment_date),
            "timeSlot": c.appointment.time_slot,
            "doctorName": c.appointment.doctor.user.username if (c.appointment.doctor and c.appointment.doctor.user) else "N/A",
            "symptoms": c.symptoms,
            "diagnosis": c.diagnosis,
            "doctorNotes": c.doctor_notes,
            "status": c.appointment.status,
            "uploadedFileUrl": c.uploaded_file_url
        }
        for c in consultations
    ]

@router.get("/patients/{patient_id}/lab-requests")
async def get_patient_lab_requests(patient_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(LabReport).where(LabReport.patient_id == patient_id).options(
        selectinload(LabReport.test)
    )
    res = await db.execute(stmt)
    reports = res.scalars().all()
    if not reports:
        return []
    
    # Group lab reports by booking date
    grouped: dict[str, list] = {}
    for r in reports:
        d_str = str(r.created_at.date()) if r.created_at else "N/A"
        if d_str not in grouped:
            grouped[d_str] = []
        grouped[d_str].append(r)
    
    result_list = []
    for d_str, group in grouped.items():
        test_names = [r.test.test_name for r in group if r.test]
        combined_names = ", ".join(test_names)
        first_r = group[0]
        result_list.append({
            "id": first_r.id,
            "testName": combined_names,
            "resultValue": first_r.result_value or "Booked",
            "status": first_r.status,
            "date": d_str,
            "uploadedFileUrl": first_r.uploaded_file_url
        })
    
    status_order = {
        "COMPLETED": 1,
        "PENDING": 2,
        "APPROVED": 3,
        "FINALIZED": 4,
        "CANCELLED": 5
    }
    result_list.sort(key=lambda r: status_order.get(r["status"], 99))
    
    return result_list

@router.post("/appointments/{appointment_id}/approve")
async def approve_appointment(appointment_id: str, db: AsyncSession = Depends(get_db)):
    stmt = update(Appointment).where(Appointment.id == appointment_id).values(status="Scheduled")
    await db.execute(stmt)
    await db.commit()
    return {"message": "Appointment approved successfully"}

@router.post("/appointments/{appointment_id}/cancel")
async def cancel_appointment(appointment_id: str, db: AsyncSession = Depends(get_db)):
    stmt = update(Appointment).where(Appointment.id == appointment_id).values(status="Cancelled")
    await db.execute(stmt)
    await db.commit()
    return {"message": "Appointment cancelled successfully"}

@router.post("/lab-requests/group/{patient_id}/{date}/approve")
async def approve_lab_request_group(patient_id: str, date: str, db: AsyncSession = Depends(get_db)):
    stmt = select(LabReport).where(LabReport.patient_id == patient_id)
    res = await db.execute(stmt)
    reports = res.scalars().all()
    for r in reports:
        if r.created_at and str(r.created_at.date()) == date:
            r.status = "APPROVED"
    await db.commit()
    return {"message": "Lab requests approved successfully"}

@router.post("/lab-requests/group/{patient_id}/{date}/cancel")
async def cancel_lab_request_group(patient_id: str, date: str, db: AsyncSession = Depends(get_db)):
    stmt = select(LabReport).where(LabReport.patient_id == patient_id)
    res = await db.execute(stmt)
    reports = res.scalars().all()
    for r in reports:
        if r.created_at and str(r.created_at.date()) == date:
            r.status = "CANCELLED"
            r.result_value = "Cancelled"
    await db.commit()
    return {"message": "Lab requests cancelled successfully"}

class ConsultSubmit(BaseModel):
    symptoms: str | None = None
    diagnosis: str | None = None
    doctor_notes: str | None = None

@router.post("/consultations/{consultation_id}/submit")
async def submit_consultation(consultation_id: str, schema: ConsultSubmit, db: AsyncSession = Depends(get_db)):
    stmt_c = select(Consultation).where(Consultation.id == consultation_id).options(selectinload(Consultation.appointment))
    res_c = await db.execute(stmt_c)
    consultation = res_c.scalar_one_or_none()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    consultation.symptoms = schema.symptoms
    consultation.diagnosis = schema.diagnosis
    consultation.doctor_notes = schema.doctor_notes
    consultation.appointment.status = "Doctor Completed"
    
    await db.commit()
    return {"message": "Consultation details submitted to receptionist"}

@router.post("/consultations/{consultation_id}/finalize")
async def finalize_consultation(consultation_id: str, db: AsyncSession = Depends(get_db)):
    stmt_c = select(Consultation).where(Consultation.id == consultation_id).options(selectinload(Consultation.appointment))
    res_c = await db.execute(stmt_c)
    consultation = res_c.scalar_one_or_none()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    consultation.appointment.status = "Finalized"
    await db.commit()
    
    # Import and run PyMuPDF generator on-demand
    from generate_reports import generate_single_consultation_pdf
    pdf_url = generate_single_consultation_pdf(consultation_id)
    
    return {"message": "Consultation finalized and report PDF generated", "uploadedFileUrl": pdf_url}

class LabSubmit(BaseModel):
    result_value: str

@router.post("/lab-requests/group/{patient_id}/{date}/submit")
async def submit_lab_report_group(patient_id: str, date: str, schema: LabSubmit, db: AsyncSession = Depends(get_db)):
    stmt = select(LabReport).where(LabReport.patient_id == patient_id)
    res = await db.execute(stmt)
    reports = res.scalars().all()
    
    for r in reports:
        if r.created_at and str(r.created_at.date()) == date:
            r.status = "COMPLETED"
            r.result_value = schema.result_value
            
    await db.commit()
    return {"message": "Lab reports submitted to receptionist"}

class LabFinalize(BaseModel):
    result_value: str

@router.post("/lab-requests/group/{patient_id}/{date}/finalize")
async def finalize_lab_report_group(patient_id: str, date: str, schema: LabFinalize, db: AsyncSession = Depends(get_db)):
    stmt = select(LabReport).where(LabReport.patient_id == patient_id)
    res = await db.execute(stmt)
    reports = res.scalars().all()
    
    for r in reports:
        if r.created_at and str(r.created_at.date()) == date:
            r.status = "FINALIZED"
            r.result_value = schema.result_value
            
    await db.commit()
    
    # Import and run PyMuPDF generator on-demand
    return {"message": "Lab reports finalized and PDF generated", "uploadedFileUrl": pdf_url}

class ReportPayload(BaseModel):
    id: Optional[str] = None
    customer_id: Optional[str] = "#4FA35E42"
    date: Optional[str] = "2026-07-23"
    patient_name: str
    dob: Optional[str] = "1990-01-01"
    gender: Optional[str] = "Not Specified"
    contact: Optional[str] = "8919527429"
    doctor_name: Optional[str] = "dr_generalphysician"
    specialization: Optional[str] = "General Physician"
    prescriptions: Optional[str] = "Paracetamol 500mg"
    doctor_notes: Optional[str] = "Follow-up in 3 days if symptoms persist."
    preference: Optional[str] = "anyway"
    symptoms: Optional[str] = "High Fever / Chills"
    diagnosis: Optional[str] = "Clinical Consultation Completed"

@router.post("/reports/generate")
async def generate_and_save_report(payload: ReportPayload, db: AsyncSession = Depends(get_db)):
    from app.utils.pdf_generator import generate_consultation_pdf
    
    data_dict = payload.model_dump()
    pdf_url = generate_consultation_pdf(data_dict)
    
    # Update consultation record if found
    if payload.id:
        stmt_con = select(Consultation).where(
            (Consultation.id == payload.id) | (Consultation.appointment_id == payload.id)
        )
        res_con = await db.execute(stmt_con)
        con = res_con.scalars().first()
        if con:
            con.uploaded_file_url = pdf_url

    # Save into LabReport database table so it persists for Patient Details & Patient Portal
    lab_report = LabReport(
        status="Completed",
        result_value=f"Diagnosis: {data_dict['diagnosis']} | Prescriptions: {data_dict['prescriptions']}",
        uploaded_file_url=pdf_url
    )
    
    # Attempt to associate with patient by name if available
    if payload.patient_name:
        stmt = select(Patient).join(Patient.user).where(User.username.ilike(payload.patient_name.strip()))
        res = await db.execute(stmt)
        patient = res.scalars().first()
        if patient:
            lab_report.patient_id = patient.id
        
    db.add(lab_report)
    await db.commit()
    
    return {"message": "Report generated and saved to database successfully", "uploadedFileUrl": pdf_url}
