from sqlalchemy import String, and_, func, or_
from sqlalchemy.orm import Session

from app.models import Doctor, DoctorDetail, DoctorSpecialization, DomainLookup


CATEGORY_ALIASES = {
    "skin": "Dermatologist",
    "diabetic": "General Physician",
    "diabetes": "General Physician",
    "sugar": "General Physician",
    "child": "Pediatrician",
    "kids": "Pediatrician",
    "baby": "Pediatrician",
    "eye": "Ophthalmologist",
    "ear": "ENT Specialist",
    "nose": "ENT Specialist",
    "throat": "ENT Specialist",
    "mental": "Psychiatrist",
    "heart": "Cardiologist",
    "bone": "Orthopedic",
    "joint": "Orthopedic",
    "women": "Gynecologist",
    "pregnancy": "Gynecologist",
    "teeth": "Dentist",
    "tooth": "Dentist",
}


def normalize_specialization_input(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().lower()
    return CATEGORY_ALIASES.get(cleaned, value.strip())


class DoctorService:
    def __init__(self, db: Session):
        self.db = db

    def get_specializations(self) -> list[dict]:
        rows = (
            self.db.query(DomainLookup)
            .filter(DomainLookup.domain_type == "specialization")
            .order_by(DomainLookup.domain_name.asc())
            .all()
        )

        return [
            {
                "id": row.domain_lookup_id,
                "name": row.domain_name,
                "value": row.domain_value,
                "details": row.domain_details,
            }
            for row in rows
        ]

    def search_doctors(
        self,
        specialization: str | None = None,
        query: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        specialization = normalize_specialization_input(specialization)

        q = (
            self.db.query(
                Doctor.doctor_id,
                Doctor.first_name,
                Doctor.middle_name,
                Doctor.last_name,
                Doctor.email,
                Doctor.phone_no,
                Doctor.status,
                DoctorDetail.experience,
                DoctorDetail.sort_desc,
                DoctorDetail.gender,
                func.group_concat(func.distinct(DomainLookup.domain_name)).label("specializations"),
            )
            .outerjoin(DoctorDetail, Doctor.doctor_id == DoctorDetail.doctor_id)
            .outerjoin(DoctorSpecialization, Doctor.doctor_id == DoctorSpecialization.doctor_id)
            .outerjoin(
                DomainLookup,
                and_(
                    DomainLookup.domain_type == "specialization",
                    DomainLookup.domain_value == func.cast(DoctorSpecialization.specialization_id, String),
                ),
            )
            .group_by(
                Doctor.doctor_id,
                Doctor.first_name,
                Doctor.middle_name,
                Doctor.last_name,
                Doctor.email,
                Doctor.phone_no,
                Doctor.status,
                DoctorDetail.experience,
                DoctorDetail.sort_desc,
                DoctorDetail.gender,
            )
        )

        filters = [
            DoctorSpecialization.status == "1",
            Doctor.status == "Active",
        ]

        if specialization:
            filters.append(func.lower(DomainLookup.domain_name) == specialization.lower())

        if query and not specialization:
            like_query = f"%{query.strip()}%"
            filters.append(
                or_(
                    Doctor.first_name.ilike(like_query),
                    Doctor.middle_name.ilike(like_query),
                    Doctor.last_name.ilike(like_query),
                    Doctor.email.ilike(like_query),
                    Doctor.phone_no.ilike(like_query),
                    DomainLookup.domain_name.ilike(like_query),
                    DoctorDetail.sort_desc.ilike(like_query),
                )
            )

        q = q.filter(and_(*filters))

        rows = q.limit(limit).all()

        results: list[dict] = []
        for row in rows:
            full_name = " ".join(
                part for part in [row.first_name, row.middle_name, row.last_name] if part
            )
            specializations = row.specializations.split(",") if row.specializations else []

            results.append(
                {
                    "doctor_id": row.doctor_id,
                    "full_name": full_name,
                    "email": row.email,
                    "phone_no": row.phone_no,
                    "status": row.status,
                    "experience": row.experience,
                    "short_desc": row.sort_desc,
                    "gender": row.gender,
                    "specialization": specializations,
                }
            )

        return results