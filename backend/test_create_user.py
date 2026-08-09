import asyncio
from app.core.database import SessionLocal
from app.services.user import UserService
from app.schemas.user import UserCreate

async def main():
    async with SessionLocal() as db:
        user_service = UserService(db)
        schema = UserCreate(
            email="rec99@gmail.com",
            username="rec99",
            password="password123",
            role_name="RECEPTIONIST",
            mobile_number="8919527429"
        )
        print("Attempting to create staff user rec99...")
        try:
            user = await user_service.create_staff_user(schema)
            print("User created successfully!")
            print(f"ID: {user.id} | Username: {user.username} | Role: {user.role.name}")
        except Exception as e:
            print(f"Failed to create user: {e}")

if __name__ == "__main__":
    asyncio.run(main())
