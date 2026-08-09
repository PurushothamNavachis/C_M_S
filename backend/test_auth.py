import asyncio
import sys
import os
import bcrypt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select

async def reset_all():
    async with SessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        new_hash = get_password_hash("admin123")
        for u in users:
            u.hashed_password = new_hash
            u.is_active = True
        await db.commit()
        print(f"Successfully updated {len(users)} user accounts to password: admin123")

if __name__ == "__main__":
    asyncio.run(reset_all())
