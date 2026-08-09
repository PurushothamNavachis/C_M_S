import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.future import select

async def main():
    async with SessionLocal() as db:
        res = await db.execute(select(User))
        users = res.scalars().all()
        print("Updating user statuses to active...")
        for u in users:
            u.is_active = True
            if u.username == 'doc1':
                u.hashed_password = get_password_hash('doctor123')
                print("Set password for 'doc1' to 'doctor123' and is_active=True")
            elif u.username == 'admin':
                u.hashed_password = get_password_hash('admin123')
                print("Set password for 'admin' to 'admin123' and is_active=True")
            elif u.username == 'superadmin':
                u.hashed_password = get_password_hash('superadmin123')
                print("Set password for 'superadmin' to 'superadmin123' and is_active=True")
            elif u.username == 'receptionist':
                u.hashed_password = get_password_hash('receptionist123')
                print("Set password for 'receptionist' to 'receptionist123' and is_active=True")
            else:
                print(f"Ensured user '{u.username}' is_active=True")
        
        await db.commit()
        print("All users updated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
