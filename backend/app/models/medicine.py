from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    generic_name: Mapped[str] = mapped_column(String(150), nullable=True)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
