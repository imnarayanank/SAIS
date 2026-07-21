"""
app/api/timetable.py
---------------------
Timetable management routes.
Supports both manual entry and Excel file upload.
The Excel parser handles both row-per-class and grid formats.
"""
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..core.deps import get_current_user
from ..core.config import settings
from ..models.user import User
from ..models.timetable import TimetableEntry
from ..schemas.timetable import TimetableEntryCreate, TimetableEntryOut
from ..utils.excel_parser import parse_timetable_excel

router = APIRouter(prefix="/api/timetable", tags=["Timetable"])


def reconcile_timetable(user_id: int, db: Session):
    """Link timetable entries to courses to ensure consistency."""
    from ..models.course import Course
    courses = db.query(Course).filter(Course.user_id == user_id).all()
    if not courses:
        return

    entries = db.query(TimetableEntry).filter(
        TimetableEntry.user_id == user_id,
        TimetableEntry.course_id.is_(None)
    ).all()

    updated = False
    for entry in entries:
        if "free" in entry.subject_name.lower() or "free" in (entry.course_code or "").lower():
            continue

        subj_clean = entry.subject_name.strip().lower()
        code_clean = entry.course_code.strip().lower() if entry.course_code else ""

        for course in courses:
            c_code = course.course_code.strip().lower() if course.course_code else ""
            c_name = course.name.strip().lower()

            if (c_code and (c_code == subj_clean or c_code == code_clean)) or \
               (c_name == subj_clean or c_name == code_clean):
                entry.course_id = course.course_id
                updated = True
                break

    if updated:
        db.commit()


@router.get("/consistency")
def check_consistency(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check consistency between courses and timetable."""
    reconcile_timetable(current_user.user_id, db)

    all_entries = db.query(TimetableEntry).filter(
        TimetableEntry.user_id == current_user.user_id
    ).all()

    academic_entries = []
    matched = 0
    unmatched_list = []

    for e in all_entries:
        if "free" in e.subject_name.lower() or "free" in (e.course_code or "").lower():
            continue
        academic_entries.append(e)
        if e.course_id is not None:
            matched += 1
        else:
            unmatched_list.append({
                "timetable_id": e.timetable_id,
                "subject_name": e.subject_name,
                "course_code": e.course_code,
                "day": e.day,
                "start_time": e.start_time,
            })

    total = len(academic_entries)
    score = (matched / total * 100) if total > 0 else 100.0

    return {
        "consistency_score": round(score, 1),
        "total_academic_entries": total,
        "matched_entries": matched,
        "unmatched_entries": unmatched_list,
    }


@router.get("/", response_model=List[TimetableEntryOut])
def list_timetable(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all timetable entries for the current user, ordered by day and time."""
    reconcile_timetable(current_user.user_id, db)
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    entries = db.query(TimetableEntry).filter(
        TimetableEntry.user_id == current_user.user_id
    ).all()
    return sorted(entries, key=lambda e: (
        day_order.index(e.day) if e.day in day_order else 7,
        e.start_time or ""
    ))


@router.post("/", response_model=TimetableEntryOut, status_code=status.HTTP_201_CREATED)
def add_timetable_entry(
    data: TimetableEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually add a single timetable entry."""
    entry = TimetableEntry(**data.model_dump(), user_id=current_user.user_id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/upload", response_model=List[TimetableEntryOut])
async def upload_timetable_excel(
    file: UploadFile = File(...),
    replace_existing: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload an Excel (.xlsx) timetable file.
    Parses it automatically and stores entries in the database.
    If replace_existing=True, clears the current timetable first.
    """
    # Validate file type
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are supported.",
        )

    # Save file temporarily
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = os.path.join(upload_dir, f"timetable_{current_user.user_id}.xlsx")

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parse the Excel file
    try:
        parsed_entries = parse_timetable_excel(temp_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse Excel file: {str(e)}",
        )

    if not parsed_entries:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No timetable entries found. Please check your Excel file format.",
        )

    # Optionally clear existing timetable
    if replace_existing:
        db.query(TimetableEntry).filter(
            TimetableEntry.user_id == current_user.user_id
        ).delete()

    # Insert parsed entries
    created = []
    for entry_data in parsed_entries:
        entry = TimetableEntry(
            user_id=current_user.user_id,
            **entry_data,
        )
        db.add(entry)
        created.append(entry)

    db.commit()
    for entry in created:
        db.refresh(entry)
        
    reconcile_timetable(current_user.user_id, db)
    
    # We should refresh the entries again so they have the updated course_id
    for entry in created:
        db.refresh(entry)

    return created


@router.delete("/{timetable_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timetable_entry(
    timetable_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a single timetable entry."""
    entry = db.query(TimetableEntry).filter(
        TimetableEntry.timetable_id == timetable_id,
        TimetableEntry.user_id == current_user.user_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    db.delete(entry)
    db.commit()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_timetable(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear the entire timetable for the current user."""
    db.query(TimetableEntry).filter(
        TimetableEntry.user_id == current_user.user_id
    ).delete()
    db.commit()
