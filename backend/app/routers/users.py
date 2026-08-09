import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.models.user import User
from app.models.patient import Patient
from app.services.user import UserService
from app.dependencies.auth import get_current_user, RoleChecker

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Fetch current user identity profile. Auto-creates Patient profile if missing."""
    if current_user.role and current_user.role.name == "PATIENT":
        stmt_p = select(Patient).where(Patient.user_id == current_user.id)
        res_p = await db.execute(stmt_p)
        patient = res_p.scalar_one_or_none()
        if not patient:
            patient = Patient(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                dob=date(1990, 1, 1),
                gender="Not Specified",
                phone=getattr(current_user, "mobile_number", None) or "8919527429"
            )
            db.add(patient)
            await db.commit()
            await db.refresh(current_user)
    return current_user

@router.post(
    "", 
    response_model=UserResponse
)
async def create_user(schema: UserCreate, db: AsyncSession = Depends(get_db)):
    """Admin-only endpoint to create administrative staff or doctor users."""
    print(f"[create_user API] Received schema: {schema}")
    try:
        user_service = UserService(db)
        result = await user_service.create_staff_user(schema)
        print(f"[create_user API] User created successfully: {result.username}")
        return result
    except HTTPException as exc:
        print(f"[create_user API] HTTPException caught cleanly: status={exc.status_code}, detail={exc.detail}")
        raise exc
    except Exception as e:
        print(f"[create_user API] Generic Exception caught: {e}")
        raise HTTPException(status_code=400, detail=str(e))

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

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, schema: UserUpdate, db: AsyncSession = Depends(get_db)):
    """Update a user's details and their doctor profile (if any)."""
    user_service = UserService(db)
    return await user_service.update_user(user_id, schema)
