from sqlalchemy import String, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False)
    consultation_id: Mapped[str] = mapped_column(String(36), ForeignKey("consultations.id", ondelete="SET NULL"), nullable=True)
    consultation_fee: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    medicine_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    lab_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    grand_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Unpaid", nullable=False)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="bills")
    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="bill")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="bill", cascade="all, delete-orphan")
