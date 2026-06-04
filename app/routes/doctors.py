from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.doctor_service import DoctorService


router = APIRouter(prefix="/api", tags=["Doctors"])


@router.get("/specializations")
def get_specializations(db: Session = Depends(get_db)):
    service = DoctorService(db)
    return {"success": True, "data": service.get_specializations()}


@router.get("/doctors/search")
def search_doctors(
    specialization: str | None = Query(default=None),
    category: str | None = Query(default=None),
    query: str | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    service = DoctorService(db)
    specialization_value = specialization or category
    doctors = service.search_doctors(
        specialization=specialization_value,
        query=query,
        limit=limit,
    )
    return {"success": True, "count": len(doctors), "data": doctors}
