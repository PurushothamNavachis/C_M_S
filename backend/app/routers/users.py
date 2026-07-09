from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.services.user import UserService
from app.dependencies.auth import get_current_user, RoleChecker

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Fetch current user identity profile."""
    return current_user

@router.post(
    "", 
    response_model=UserResponse
)
async def create_user(schema: UserCreate, db: AsyncSession = Depends(get_db)):
    """Admin-only endpoint to create administrative staff or doctor users."""
    user_service = UserService(db)
    return await user_service.create_staff_user(schema)

@router.get("", response_model=list[UserResponse])
async def list_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    return await user_service.list_users(skip, limit)

@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_active(user_id: str, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    return await user_service.toggle_active(user_id)

@router.delete("/{user_id}")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    await user_service.delete_user(user_id)
    return {"detail": "User successfully deleted"}
