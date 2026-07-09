from datetime import datetime
from sqlalchemy import String, ForeignKey, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    bill_id: Mapped[str] = mapped_column(String(36), ForeignKey("bills.id", ondelete="CASCADE"), nullable=False)
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    bill: Mapped["Bill"] = relationship("Bill", back_populates="payments")
