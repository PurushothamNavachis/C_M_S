from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    prescription_id: Mapped[str] = mapped_column(String(36), ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False)
    medicine_id: Mapped[str] = mapped_column(String(36), ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="items")
    medicine: Mapped["Medicine"] = relationship("Medicine")
