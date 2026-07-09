from sqlalchemy import String, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Vitals(Base):
    __tablename__ = "vitals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    consultation_id: Mapped[str] = mapped_column(String(36), ForeignKey("consultations.id", ondelete="CASCADE"), unique=True, nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=True)
    blood_pressure: Mapped[str] = mapped_column(String(20), nullable=True)
    temperature_f: Mapped[float] = mapped_column(Float, nullable=True)

    # Relationships
    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="vitals")
