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
        address=schema.address
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
            "name": p.user.username, # fallback to username
            "email": p.user.email,
            "phone": p.phone,
            "gender": p.gender,
            "blood_group": p.blood_group,
            "address": p.address
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
    doctor = res_d.scalar_one_or_none()

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
        selectinload(Appointment.doctor).selectinload(Doctor.user)
    )
    res = await db.execute(stmt)
    appts = res.scalars().all()
    return [
        {
            "id": a.id,
            "patientName": a.patient.user.username,
            "doctorName": a.doctor.user.username,
            "time": a.time_slot,
            "status": a.status
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
    # 1. Create Consultation
    consult_id = str(uuid.uuid4())
    new_consult = Consultation(
        id=consult_id,
        appointment_id=schema.appointment_id,
        symptoms=schema.symptoms,
        diagnosis=schema.diagnosis,
        doctor_notes=schema.doctor_notes
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
    if schema.prescription_notes:
        new_prescription = Prescription(
            id=str(uuid.uuid4()),
            consultation_id=consult_id,
            notes=schema.prescription_notes
        )
        db.add(new_prescription)

    # 4. Mark appointment completed
    stmt = update(Appointment).where(Appointment.id == schema.appointment_id).values(status="Completed")
    await db.execute(stmt)
    
    await db.commit()
    return {"message": "Consultation records saved successfully", "consultation_id": consult_id}


# --- PATIENT ACTIONS ENDPOINTS ---

class ConsultationRequest(BaseModel):
    department: str | None = None
    symptoms: list[str] = []
    date: str
    time: str
    preference: str

class LabRequest(BaseModel):
    tests: list[str]

@router.post("/patient-actions/consultation-request")
async def create_patient_consultation_request(
    schema: ConsultationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Find patient associated with current user
    stmt_p = select(Patient).where(Patient.user_id == current_user.id)
    res_p = await db.execute(stmt_p)
    patient = res_p.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=400, detail="Current user does not have a patient profile")
        
    # 2. Find doctor or create placeholder for specialization
    spec = schema.department or "General Physician"
    stmt_d = select(Doctor).where(Doctor.specialization.ilike(spec))
    res_d = await db.execute(stmt_d)
    doctor = res_d.scalar_one_or_none()
    
    if not doctor:
        stmt_role_doc = select(Role).where(Role.name == "DOCTOR")
        role_res_doc = await db.execute(stmt_role_doc)
        role_doc = role_res_doc.scalar_one_or_none()
        if not role_doc:
            role_doc = Role(id=str(uuid.uuid4()), name="DOCTOR", description="Doctor role")
            db.add(role_doc)
            await db.flush()
            
        doc_uname = f"dr_{spec.replace(' ', '').replace('/', '').lower()}"
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
            license_number=f"LIC-{str(uuid.uuid4())[:8]}",
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
    
    # 5. Create Consultation record with symptoms
    new_consult = Consultation(
        id=str(uuid.uuid4()),
        appointment_id=new_appt.id,
        symptoms=", ".join(schema.symptoms),
        diagnosis="Pending Consultation",
        doctor_notes=f"Preference: {schema.preference}"
    )
    db.add(new_consult)
    await db.commit()
    
    return {"message": "Consultation Request saved successfully in database", "appointment_id": new_appt.id}

@router.post("/patient-actions/lab-request")
async def create_patient_lab_request(
    schema: LabRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Find patient associated with current user
    stmt_p = select(Patient).where(Patient.user_id == current_user.id)
    res_p = await db.execute(stmt_p)
    patient = res_p.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=400, detail="Current user does not have a patient profile")
        
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
