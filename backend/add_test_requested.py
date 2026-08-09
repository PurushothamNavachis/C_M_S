import asyncio
import uuid
from datetime import date
from app.core.database import SessionLocal
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.doctor import Doctor
from sqlalchemy.future import select

async def main():
    async with SessionLocal() as db:
        res_p = await db.execute(select(Patient))
        patient = res_p.scalars().first()
        if not patient:
            print("No patient found!")
            return
            
        res_d = await db.execute(select(Doctor))
        doctor = res_d.scalars().first()
        if not doctor:
            print("No doctor found!")
            return
            
        new_appt = Appointment(
            id=str(uuid.uuid4()),
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_date=date(2026, 7, 30),
            time_slot="10:00",
            status="Requested"
        )
        db.add(new_appt)
        await db.commit()
        print(f"Created Requested appointment for 2026-07-30 with ID: {new_appt.id}")

if __name__ == "__main__":
    asyncio.run(main())
