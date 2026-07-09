from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class LabReport(Base):
    __tablename__ = "lab_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    test_id: Mapped[str] = mapped_column(String(36), ForeignKey("laboratory_tests.id", ondelete="RESTRICT"), nullable=False)
    result_value: Mapped[str] = mapped_column(Text, nullable=True)
    uploaded_file_url: Mapped[str] = mapped_column(String(512), nullable=True)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="lab_reports")
    test: Mapped["LaboratoryTest"] = relationship("LaboratoryTest")
