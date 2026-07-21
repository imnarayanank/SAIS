"""
app/api/courses.py
-------------------
Course management CRUD routes.
All routes are protected — requires authenticated user.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
import uuid
from ..core.database import get_db
from ..core.config import settings
from ..core.deps import get_current_user
from ..models.user import User
from ..models.course import Course
from ..schemas.course import CourseCreate, CourseUpdate, CourseOut
from ..utils.excel_parser import parse_courses_excel

router = APIRouter(prefix="/api/courses", tags=["Courses"])

# Color palette for auto-assigning colors to new courses
COURSE_COLORS = [
    "#3B82F6", "#8B5CF6", "#EC4899", "#10B981",
    "#F59E0B", "#EF4444", "#06B6D4", "#84CC16",
]


@router.get("/", response_model=List[CourseOut])
def list_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all courses for the current user."""
    return db.query(Course).filter(Course.user_id == current_user.user_id).all()


@router.post("/upload", response_model=List[CourseOut], status_code=status.HTTP_201_CREATED)
def upload_courses(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload an Excel file to extract courses."""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"courses_{file_id}.xlsx")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        parsed_courses = parse_courses_excel(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
        
    created_courses = []
    
    for i, data in enumerate(parsed_courses):
        code = data.get("course_code")
        name = data["name"]
        
        # Check if course already exists for this user
        existing_course = None
        if code:
            existing_course = db.query(Course).filter(
                Course.user_id == current_user.user_id,
                Course.course_code == code
            ).first()
        else:
            existing_course = db.query(Course).filter(
                Course.user_id == current_user.user_id,
                Course.name == name
            ).first()
            
        if existing_course:
            # Update fields if provided
            if data.get("teacher"):
                existing_course.teacher = data.get("teacher")
            if data.get("course_type"):
                existing_course.course_type = data.get("course_type")
            if data.get("credits") is not None:
                existing_course.credits = data.get("credits")
                existing_course.hours_required = data.get("credits")
            created_courses.append(existing_course)
        else:
            # Create new course
            color = COURSE_COLORS[len(created_courses) % len(COURSE_COLORS)]
            course = Course(
                user_id=current_user.user_id,
                name=name,
                course_code=code,
                teacher=data.get("teacher"),
                course_type=data.get("course_type", "Theory"),
                credits=data.get("credits", 3.0),
                color=color,
                difficulty="Medium",
                hours_required=data.get("credits", 3.0)
            )
            db.add(course)
            created_courses.append(course)

    db.commit()
    for c in created_courses:
        db.refresh(c)
        
    return created_courses


@router.post("/", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new course."""
    # Auto-assign a color if not provided
    if data.color == "#3B82F6":
        count = db.query(Course).filter(Course.user_id == current_user.user_id).count()
        data.color = COURSE_COLORS[count % len(COURSE_COLORS)]

    course = Course(**data.model_dump(), user_id=current_user.user_id)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/{course_id}", response_model=CourseOut)
def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single course by ID."""
    course = db.query(Course).filter(
        Course.course_id == course_id,
        Course.user_id == current_user.user_id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.put("/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a course (partial updates supported)."""
    course = db.query(Course).filter(
        Course.course_id == course_id,
        Course.user_id == current_user.user_id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a course and all related entries (cascade)."""
    course = db.query(Course).filter(
        Course.course_id == course_id,
        Course.user_id == current_user.user_id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db.delete(course)
    db.commit()
