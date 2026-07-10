import uuid
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, RefreshToken
from app.models.role import Role
from app.models.patient import Patient
from app.schemas.user import UserCreate, UserRegister
from app.repositories.user import UserRepository, RoleRepository, RefreshTokenRepository
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.exceptions import EntityAlreadyExistsException, CredentialsException, EntityNotFoundException

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.token_repo = RefreshTokenRepository(db)

    async def register_patient(self, schema: UserRegister) -> User:
        # Check duplicate
        if await self.user_repo.get_by_email(schema.email):
            raise EntityAlreadyExistsException("User", schema.email)
        if await self.user_repo.get_by_username(schema.username):
            raise EntityAlreadyExistsException("User", schema.username)

        # Get patient role
        patient_role = await self.role_repo.get_by_name("PATIENT")
        if not patient_role:
            # Seed dynamically if not present
            patient_role = Role(
                id=str(uuid.uuid4()),
                name="PATIENT",
                description="Default self-registered patient access"
            )
            await self.role_repo.create(patient_role)
        
        new_user = User(
            id=str(uuid.uuid4()),
            email=schema.email,
            username=schema.username,
            hashed_password=get_password_hash(schema.password),
            role_id=patient_role.id,
            mobile_number=schema.mobile_number,
            is_active=True
        )
        await self.user_repo.create(new_user)
        
        # Create corresponding Patient profile
        new_patient = Patient(
            id=str(uuid.uuid4()),
            user_id=new_user.id,
            dob=date(1990, 1, 1), # Default DOB
            gender="Not Specified", # Default Gender
            blood_group=schema.blood_group,
            phone=schema.mobile_number or "Not Provided"
        )
        self.db.add(new_patient)
        
        await self.db.commit()
        return await self.user_repo.get_by_id_with_role(new_user.id)

    async def authenticate(self, username_or_email: str, password: str) -> User:
        user = await self.user_repo.get_by_email(username_or_email)
        if not user:
            user = await self.user_repo.get_by_username(username_or_email)
        
        if not user or not verify_password(password, user.hashed_password) or not user.is_active:
            raise CredentialsException("Invalid credentials or inactive user account.")
        return user

    async def create_tokens(
        self, 
        user: User, 
        ip_address: str | None = None, 
        user_agent: str | None = None
    ) -> dict[str, str]:
        # Issue JWT Access & Refresh
        access_token = create_access_token(subject=user.id, role=user.role.name)
        refresh_token_str = create_refresh_token(subject=user.id)

        # Save to database
        new_refresh = RefreshToken(
            id=str(uuid.uuid4()),
            token=refresh_token_str,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            ip_address=ip_address,
            user_agent=user_agent
        )
        await self.token_repo.create(new_refresh)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer"
        }

    async def refresh_session(
        self, 
        refresh_token_str: str, 
        ip_address: str | None = None, 
        user_agent: str | None = None
    ) -> dict[str, str]:
        # Validate refresh token database entry
        db_token = await self.token_repo.get_by_token(refresh_token_str)
        if not db_token or db_token.is_revoked or db_token.expires_at < datetime.utcnow():
            if db_token and not db_token.is_revoked:
                db_token.is_revoked = True
                db_token.revoked_reason = "Token expired"
            raise CredentialsException("Invalid or expired refresh token")

        user = db_token.user
        if not user or not user.is_active:
            raise CredentialsException("User account is inactive.")

        # Revoke current token (rotation strategy)
        db_token.is_revoked = True
        db_token.revoked_reason = f"Rotated on refresh at {datetime.utcnow()}"

        # Generate new tokens
        return await self.create_tokens(user, ip_address, user_agent)

    async def revoke_token(self, refresh_token_str: str) -> None:
        db_token = await self.token_repo.get_by_token(refresh_token_str)
        if db_token:
            db_token.is_revoked = True
            db_token.revoked_reason = "User logged out"
