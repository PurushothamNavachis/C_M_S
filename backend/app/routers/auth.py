from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.auth import TokenSchema, LoginRequest, RefreshRequest
from app.schemas.user import UserRegister, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(schema: UserRegister, db: AsyncSession = Depends(get_db)):
    """Public self-registration API for patients."""
    auth_service = AuthService(db)
    return await auth_service.register_patient(schema)

@router.post("/login", response_model=TokenSchema)
async def login(request: Request, schema: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login API returning access token and refresh token."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate(schema.username_or_email, schema.password)
    
    # Retrieve client request headers for tracking session metadata
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    
    return await auth_service.create_tokens(user, ip_address=ip_address, user_agent=user_agent)

@router.post("/refresh", response_model=TokenSchema)
async def refresh(request: Request, schema: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a rotated access and refresh token pair."""
    auth_service = AuthService(db)
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    
    return await auth_service.refresh_session(
        schema.refresh_token, 
        ip_address=ip_address, 
        user_agent=user_agent
    )

@router.post("/logout")
async def logout(schema: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Revoke the refresh token on user logout."""
    auth_service = AuthService(db)
    await auth_service.revoke_token(schema.refresh_token)
    return {"detail": "Successfully logged out."}
