import sqlite3
import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

def add_column():
    conn = sqlite3.connect('cms_db.sqlite')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN plain_password VARCHAR(255);")
        conn.commit()
        print("Column plain_password added successfully!")
    except Exception as e:
        print(f"Column might already exist: {e}")
    finally:
        conn.close()

async def populate():
    async with SessionLocal() as db:
        res = await db.execute(select(User).options(joinedload(User.role)))
        users = res.scalars().all()
        passwords_to_test = ['receptionist123', 'doctor123', 'patient123', 'admin123', 'superadmin123']
        updated_count = 0
        for u in users:
            if not u.plain_password:
                matched_pw = None
                for p in passwords_to_test:
                    if verify_password(p, u.hashed_password):
                        matched_pw = p
                        break
                if not matched_pw and verify_password(u.username, u.hashed_password):
                    matched_pw = u.username
                
                u.plain_password = matched_pw or f"{u.username}123"
                updated_count += 1
        await db.commit()
        print(f"Updated plain_password for {updated_count} users.")

if __name__ == "__main__":
    add_column()
    asyncio.run(populate())
