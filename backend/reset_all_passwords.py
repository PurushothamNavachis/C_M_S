import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

async def main():
    async with SessionLocal() as db:
        res = await db.execute(select(User).options(joinedload(User.role)))
        users = res.scalars().all()
        print("--- RESETTING ALL USER PASSWORDS TO STANDARD PRESETS ---")
        for u in users:
            role_name = u.role.name if u.role else 'None'
            new_pass = None
            if role_name == 'SUPER_ADMIN':
                new_pass = 'superadmin123'
            elif role_name == 'ADMIN':
                new_pass = 'admin123'
            elif role_name == 'RECEPTIONIST':
                new_pass = 'receptionist123'
            elif role_name == 'DOCTOR':
                new_pass = 'doctor123'
            elif role_name == 'PATIENT':
                new_pass = 'patient123'
            elif role_name == 'LAB_AC':
                new_pass = 'lab123'
            else:
                new_pass = 'password123' # default fallback
                
            u.hashed_password = get_password_hash(new_pass)
            u.is_active = True # Force active status
            print(f"Username: '{u.username}' | Role: '{role_name}' | Set Password: '{new_pass}'")
            
        await db.commit()
        print("All passwords reset and committed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
