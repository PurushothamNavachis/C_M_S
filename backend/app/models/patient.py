from datetime import date
from sqlalchemy import String, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    blood_group: Mapped[str] = mapped_column(String(10), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    emergency_contact_name: Mapped[str] = mapped_column(String(100), nullable=True)
    emergency_contact_phone: Mapped[str] = mapped_column(String(20), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="patient")
    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="patient")
    lab_reports: Mapped[list["LabReport"]] = relationship("LabReport", back_populates="patient")
    bills: Mapped[list["Bill"]] = relationship("Bill", back_populates="patient")
