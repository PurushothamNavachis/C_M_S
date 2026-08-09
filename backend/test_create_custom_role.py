import asyncio
from app.core.database import SessionLocal
from app.services.user import UserService
from app.schemas.user import UserCreate

async def main():
    async with SessionLocal() as db:
        user_service = UserService(db)
        schema = UserCreate(
            email="pharma1@gmail.com",
            username="pharma1",
            password="password123",
            role_name="PHARMACIST",
            mobile_number="9988776655"
        )
        print("Attempting to create user with brand new dynamic role 'PHARMACIST'...")
        try:
            user = await user_service.create_staff_user(schema)
            print("Dynamic Custom Role & User Created Successfully!")
            print(f"ID: {user.id} | Username: {user.username} | Role Name: {user.role.name} | Active: {user.is_active}")
        except Exception as e:
            print(f"Failed to create user: {e}")

if __name__ == "__main__":
    asyncio.run(main())
