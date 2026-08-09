import uuid
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.role import Role
from app.models.doctor import Doctor
from app.models.lab_ac import LabAC
from app.schemas.user import UserCreate, UserUpdate
from app.repositories.user import UserRepository, RoleRepository
from app.core.security import get_password_hash
from app.core.exceptions import EntityAlreadyExistsException, EntityNotFoundException

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)

    async def get_user_by_id(self, user_id: str) -> User:
        user = await self.user_repo.get_by_id_with_role(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)
        return user

    async def create_staff_user(self, schema: UserCreate) -> User:
        try:
            # Check duplicate user
            if await self.user_repo.get_by_email(schema.email):
                raise HTTPException(status_code=400, detail=f"User with email '{schema.email}' already exists.")
            if await self.user_repo.get_by_username(schema.username):
                raise HTTPException(status_code=400, detail=f"User with username '{schema.username}' already exists.")

            target_lic = schema.license_number.strip() if (schema.license_number and schema.license_number.strip()) else None

            if schema.role_name.upper() == "DOCTOR" and target_lic:
                stmt_d = select(Doctor).where(func.lower(Doctor.license_number) == target_lic.lower())
                res_d = await self.db.execute(stmt_d)
                if res_d.scalars().first():
                    raise HTTPException(status_code=400, detail=f"Doctor license number '{target_lic}' is already in use. Please enter a unique license number.")

            if schema.role_name.upper() == "LAB_AC" and target_lic:
                stmt_l = select(LabAC).where(func.lower(LabAC.license_number) == target_lic.lower())
                res_l = await self.db.execute(stmt_l)
                if res_l.scalars().first():
                    raise HTTPException(status_code=400, detail=f"Lab staff license number '{target_lic}' is already in use. Please enter a unique license number.")

            # Fetch designated role
            role = await self.role_repo.get_by_name(schema.role_name.upper())
            if not role:
                role = Role(
                    id=str(uuid.uuid4()),
                    name=schema.role_name.upper(),
                    description=f"Automated creation of {schema.role_name} role"
                )
                await self.role_repo.create(role)

            new_user = User(
                id=str(uuid.uuid4()),
                email=schema.email,
                username=schema.username,
                mobile_number=schema.mobile_number,
                specialization=schema.specialization,
                hashed_password=get_password_hash(schema.password),
                plain_password=schema.password,
                role_id=role.id,
                is_active=True
            )
            await self.user_repo.create(new_user)
            await self.db.flush()

            if schema.role_name.upper() == "DOCTOR":
                new_doctor = Doctor(
                    id=str(uuid.uuid4()),
                    user_id=new_user.id,
                    specialization=schema.specialization or "General Practice",
                    license_number=target_lic or f"LIC-{str(uuid.uuid4())[:8].upper()}",
                    consultation_fee=schema.consultation_fee or 0.0,
                    experience_years=schema.experience_years or 0
                )
                self.db.add(new_doctor)
            elif schema.role_name.upper() == "LAB_AC":
                new_lab_ac = LabAC(
                    id=str(uuid.uuid4()),
                    user_id=new_user.id,
                    qualification=schema.qualification or "Assistant",
                    license_number=target_lic or f"LAB-{str(uuid.uuid4())[:8].upper()}",
                    experience_years=schema.experience_years or 0
                )
                self.db.add(new_lab_ac)

            await self.db.commit()
            return await self.user_repo.get_by_id_with_role(new_user.id)
        except HTTPException:
            await self.db.rollback()
            self.db.expunge_all()
            raise
        except (IntegrityError, Exception) as err:
            await self.db.rollback()
            self.db.expunge_all()
            err_str = str(err)
            if "doctors.license_number" in err_str or "lab_ac.license_number" in err_str or "license_number" in err_str:
                raise HTTPException(status_code=400, detail=f"License number '{schema.license_number or 'provided'}' is already in use. Please enter a unique license number.")
            if "users.email" in err_str or "email" in err_str:
                raise HTTPException(status_code=400, detail=f"Email '{schema.email}' is already registered.")
            if "users.username" in err_str or "username" in err_str:
                raise HTTPException(status_code=400, detail=f"Username '{schema.username}' is already taken.")
            raise HTTPException(status_code=400, detail=f"Failed to create user account: {err_str}")

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        return await self.user_repo.get_all_with_role(skip, limit)

    async def toggle_active(self, user_id: str) -> User:
        user = await self.get_user_by_id(user_id)
        user.is_active = not user.is_active
        await self.db.commit()
        return await self.get_user_by_id(user_id)

    async def delete_user(self, user_id: str) -> None:
        user = await self.get_user_by_id(user_id)
        # Soft delete
        import datetime
        user.deleted_at = datetime.datetime.utcnow()
        await self.db.commit()

    async def update_user(self, user_id: str, schema: UserUpdate) -> User:
        user = await self.get_user_by_id(user_id)
        
        if schema.username is not None and schema.username != user.username:
            if await self.user_repo.get_by_username(schema.username):
                raise EntityAlreadyExistsException("User", schema.username)
        if schema.email is not None and schema.email != user.email:
            if await self.user_repo.get_by_email(schema.email):
                raise EntityAlreadyExistsException("User", schema.email)

        if schema.username is not None:
            user.username = schema.username
        if schema.email is not None:
            user.email = schema.email
        if schema.mobile_number is not None:
            user.mobile_number = schema.mobile_number
        if schema.specialization is not None:
            user.specialization = schema.specialization
        if schema.password is not None and schema.password.strip() != "":
            from app.core.security import get_password_hash
            user.hashed_password = get_password_hash(schema.password)
            user.plain_password = schema.password
            
        # Update profile based on role
        if user.role.name == "PATIENT":
            if user.patient:
                if schema.mobile_number is not None:
                    user.patient.phone = schema.mobile_number
                if schema.blood_group is not None:
                    user.patient.blood_group = schema.blood_group
        elif user.role.name == "DOCTOR":
            if not user.doctor:
                # If doctor record is missing, create one dynamically
                from app.models.doctor import Doctor
                import uuid
                doctor = Doctor(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    specialization=schema.specialization or "General Practice",
                    license_number=schema.license_number or f"LIC-{str(uuid.uuid4())[:8].upper()}",
                    consultation_fee=schema.consultation_fee or 0.0,
                    experience_years=schema.experience_years or 0
                )
                self.db.add(doctor)
            else:
                if schema.specialization is not None:
                    user.doctor.specialization = schema.specialization
                if schema.license_number is not None:
                    user.doctor.license_number = schema.license_number
                if schema.consultation_fee is not None:
                    user.doctor.consultation_fee = schema.consultation_fee
                if schema.experience_years is not None:
                    user.doctor.experience_years = schema.experience_years
        elif user.role.name == "LAB_AC":
            if not user.lab_ac:
                from app.models.lab_ac import LabAC
                import uuid
                lab_ac = LabAC(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    qualification=schema.qualification or "Assistant",
                    license_number=schema.license_number or f"LAB-{str(uuid.uuid4())[:8].upper()}",
                    experience_years=schema.experience_years or 0
                )
                self.db.add(lab_ac)
            else:
                if schema.qualification is not None:
                    user.lab_ac.qualification = schema.qualification
                if schema.license_number is not None:
                    user.lab_ac.license_number = schema.license_number
                if schema.experience_years is not None:
                    user.lab_ac.experience_years = schema.experience_years
                    
        await self.db.commit()
        return await self.get_user_by_id(user.id)
