from sqlalchemy import String, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    department_id: Mapped[str] = mapped_column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    specialization: Mapped[str] = mapped_column(String(150), nullable=False)
    license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    consultation_fee: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="doctor")
    department: Mapped["Department"] = relationship("Department", back_populates="doctors")
    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="doctor")
