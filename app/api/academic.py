"""
app/api/academic.py
--------------------
Academic Record management CRUD routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.academic import AcademicRecord
from ..schemas.academic import AcademicRecordCreate, AcademicRecordUpdate, AcademicRecordOut

router = APIRouter(prefix="/api/academic", tags=["Academic Records"])


@router.get("/", response_model=List[AcademicRecordOut])
def list_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all academic records for the current user, ordered by creation date."""
    return db.query(AcademicRecord).filter(AcademicRecord.user_id == current_user.user_id).order_by(AcademicRecord.created_at.asc()).all()


@router.post("/", response_model=AcademicRecordOut, status_code=status.HTTP_201_CREATED)
def create_record(
    data: AcademicRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new academic record."""
    record = AcademicRecord(**data.model_dump(), user_id=current_user.user_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{record_id}", response_model=AcademicRecordOut)
def update_record(
    record_id: int,
    data: AcademicRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an academic record."""
    record = db.query(AcademicRecord).filter(
        AcademicRecord.id == record_id,
        AcademicRecord.user_id == current_user.user_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an academic record."""
    record = db.query(AcademicRecord).filter(
        AcademicRecord.id == record_id,
        AcademicRecord.user_id == current_user.user_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(record)
    db.commit()
