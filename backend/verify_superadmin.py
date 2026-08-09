import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password
from sqlalchemy.future import select

async def main():
    async with SessionLocal() as db:
        res = await db.execute(select(User).where(User.username == 'superadmin'))
        u = res.scalar_one_or_none()
        if u:
            print("User found:")
            print(f"Username: {u.username}")
            print(f"Active: {u.is_active}")
            print(f"Hashed password: {u.hashed_password}")
            
            # Test passwords
            passwords_to_test = ['superadmin123', 'superadmin', 'sunny123', 'admin123', 'password123']
            for p in passwords_to_test:
                match = verify_password(p, u.hashed_password)
                print(f"Testing password '{p}': {match}")
        else:
            print("superadmin user not found!")

if __name__ == "__main__":
    asyncio.run(main())
