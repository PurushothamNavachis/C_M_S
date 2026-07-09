from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class LabAC(Base):
    __tablename__ = "lab_ac"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    qualification: Mapped[str] = mapped_column(String(150), nullable=True)
    license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="lab_ac")
