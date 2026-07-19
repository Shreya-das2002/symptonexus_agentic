from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship

from app.database import Base


class DomainLookup(Base):
    __tablename__ = "domain_lookups"

    domain_lookup_id = Column(Integer, primary_key=True, index=True)
    domain_type = Column(String(100), nullable=False, index=True)
    domain_name = Column(String(255), nullable=False)
    # PostgreSQL stores specialization lookup values as integer IDs.
    domain_value = Column(Integer, nullable=True)
    domain_details = Column(Text, nullable=True)


class Doctor(Base):
    __tablename__ = "doctors"

    doctor_id = Column(Integer, primary_key=True, index=True)
    doctor_no = Column(String(100), nullable=True)
    first_name = Column(String(255), nullable=False)
    middle_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone_no = Column(String(50), nullable=True)
    status = Column(
        ENUM("Active", "Inactive", name="enum_doctors_status", create_type=False),
        nullable=True,
    )
    created_on = Column(DateTime, nullable=True)
    created_by = Column(String(50), nullable=True)
    updated_by = Column(String(50), nullable=True)
    updated_on = Column(DateTime, nullable=True)

    details = relationship("DoctorDetail", back_populates="doctor", uselist=False)
    specializations = relationship("DoctorSpecialization", back_populates="doctor")


class DoctorDetail(Base):
    __tablename__ = "doctor_details"

    doctor_detail_id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id"), nullable=False, unique=True)
    dob = Column(String(50), nullable=True)
    gender = Column(Integer, nullable=True)
    experience = Column(String(50), nullable=True)
    sort_desc = Column(Text, nullable=True)
    licence_number = Column(String(255), nullable=True)
    registration_number = Column(String(255), nullable=True)
    current_address_id = Column(Integer, nullable=True)
    permanent_address_id = Column(Integer, nullable=True)

    doctor = relationship("Doctor", back_populates="details")


class DoctorSpecialization(Base):
    __tablename__ = "doctor_specializations"

    doctor_specialization_id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id"), nullable=False, index=True)
    specialization_id = Column(Integer, nullable=False)
    long_desc = Column(Text, nullable=True)
    status = Column(Integer, nullable=True)

    doctor = relationship("Doctor", back_populates="specializations")
