from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr

class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: str | None = Field(None, max_length=255)

class RoleResponse(RoleBase):
    model_config = ConfigDict(from_attributes=True)
    id: str

class DoctorProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    specialization: str
    license_number: str
    consultation_fee: float
    experience_years: int

class LabACProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    qualification: str | None = None
    license_number: str | None = None
    experience_years: int | None = None

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    mobile_number: str | None = Field(None, max_length=20)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)
    role_name: str = Field("PATIENT", description="Name of the role assigned to the user")
    specialization: str | None = None
    qualification: str | None = None
    license_number: str | None = None
    consultation_fee: float | None = None
    experience_years: int | None = None

class UserRegister(UserBase):
    password: str = Field(..., min_length=6, max_length=128)

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    is_active: bool
    role: RoleResponse
    doctor: DoctorProfileResponse | None = None
    lab_ac: LabACProfileResponse | None = None
    created_at: datetime
    updated_at: datetime

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=50)
    password: str | None = Field(None, min_length=6, max_length=128)
    mobile_number: str | None = Field(None, max_length=20)
    specialization: str | None = None
    qualification: str | None = None
    license_number: str | None = None
    consultation_fee: float | None = None
    experience_years: int | None = None
