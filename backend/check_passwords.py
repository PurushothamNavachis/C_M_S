import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

async def main():
    async with SessionLocal() as db:
        res = await db.execute(select(User).options(joinedload(User.role)))
        users = res.scalars().all()
        print("--- USER CREDENTIALS VALIDATION ---")
        passwords_to_test = ['receptionist123', 'doctor123', 'patient123', 'admin123', 'superadmin123']
        for u in users:
            matched_pw = None
            for p in passwords_to_test:
                if verify_password(p, u.hashed_password):
                    matched_pw = p
                    break
            # Also test username as password
            if not matched_pw and verify_password(u.username, u.hashed_password):
                matched_pw = u.username
            print(f"Username: '{u.username}' | Role: '{u.role.name if u.role else 'None'}' | Password: '{matched_pw or 'Unknown'}'")

if __name__ == "__main__":
    asyncio.run(main())
