import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password
from sqlalchemy.future import select

async def main():
    async with SessionLocal() as db:
        res = await db.execute(select(User))
        users = res.scalars().all()
        print("--- USER ACCOUNTS LIST ---")
        for u in users:
            test_pw = verify_password("doctor123", u.hashed_password) or verify_password("password123", u.hashed_password) or verify_password("doc123", u.hashed_password) or verify_password("admin123", u.hashed_password)
            print(f"Username: '{u.username}' | Email: '{u.email}' | Active: {u.is_active} | Valid Password Test: {test_pw}")

if __name__ == "__main__":
    asyncio.run(main())
