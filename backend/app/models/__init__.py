# app/models/__init__.py
from app.models.base import Base
from app.models.user import User, RefreshToken
from app.models.role import Role
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.consultation import Consultation
from app.models.vitals import Vitals
from app.models.medicine import Medicine
from app.models.prescription import Prescription
from app.models.prescription_item import PrescriptionItem
from app.models.laboratory_test import LaboratoryTest
from app.models.lab_report import LabReport
from app.models.bill import Bill
from app.models.payment import Payment
from app.models.settings import Settings

