from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    appointment_id: Mapped[str] = mapped_column(String(36), ForeignKey("appointments.id", ondelete="CASCADE"), unique=True, nullable=False)
    symptoms: Mapped[str] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[str] = mapped_column(Text, nullable=True)
    doctor_notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    appointment: Mapped["Appointment"] = relationship("Appointment", back_populates="consultation")
    vitals: Mapped["Vitals"] = relationship("Vitals", back_populates="consultation", uselist=False)
    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="consultation", uselist=False)
    bill: Mapped["Bill"] = relationship("Bill", back_populates="consultation", uselist=False)
