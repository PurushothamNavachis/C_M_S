import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

async def main():
    async with SessionLocal() as db:
        res = await db.execute(select(User).options(selectinload(User.role)))
        users = res.scalars().all()
        print("--- DATABASE USERS DUMP ---")
        for u in users:
            print(f"Username: '{u.username}' | Email: '{u.email}' | Role: '{u.role.name if u.role else 'None'}' | Active: {u.is_active} | PwHash: {u.hashed_password[:20]}... | DeletedAt: {u.deleted_at}")

if __name__ == "__main__":
    asyncio.run(main())
