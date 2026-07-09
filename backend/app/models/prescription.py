from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    consultation_id: Mapped[str] = mapped_column(String(36), ForeignKey("consultations.id", ondelete="CASCADE"), unique=True, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="prescription")
    items: Mapped[list["PrescriptionItem"]] = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")
