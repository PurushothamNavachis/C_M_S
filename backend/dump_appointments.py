import asyncio
from app.core.database import SessionLocal
from app.models.appointment import Appointment
from sqlalchemy.future import select

async def main():
    async with SessionLocal() as db:
        res = await db.execute(select(Appointment))
        appts = res.scalars().all()
        print("--- DATABASE APPOINTMENTS DUMP ---")
        for a in appts:
            print(f"ID: {a.id} | PatientID: {a.patient_id} | Date: {a.appointment_date} | Time: {a.time_slot} | Status: {a.status} | CreatedAt: {a.created_at}")

if __name__ == "__main__":
    asyncio.run(main())
