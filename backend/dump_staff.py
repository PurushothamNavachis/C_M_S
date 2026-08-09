import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

async def main():
    async with SessionLocal() as db:
        res = await db.execute(select(User).options(selectinload(User.role)))
        users = res.scalars().all()
        print("--- USER ACCOUNTS ---")
        for u in users:
            if u.username in ['rec1', 'rec', 'doc2', 'doc1']:
                print(f"ID: {u.id} | Username: {u.username} | Email: {u.email} | Active: {u.is_active} | Role: {u.role.name} | DeletedAt: {u.deleted_at}")

if __name__ == "__main__":
    asyncio.run(main())
