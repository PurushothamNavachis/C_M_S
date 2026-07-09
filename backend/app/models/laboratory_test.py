from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class LaboratoryTest(Base):
    __tablename__ = "laboratory_tests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    test_name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
