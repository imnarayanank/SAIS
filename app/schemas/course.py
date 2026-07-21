"""
app/schemas/course.py
----------------------
Pydantic schemas for Course CRUD operations.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CourseCreate(BaseModel):
    name: str
    course_code: Optional[str] = None
    teacher: Optional[str] = None
    department: Optional[str] = None
    difficulty: Optional[str] = "Medium"
    hours_required: Optional[float] = 3.0
    course_type: Optional[str] = "Theory"
    color: Optional[str] = "#3B82F6"
    credits: Optional[float] = 3.0
    grade: Optional[str] = None


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    course_code: Optional[str] = None
    teacher: Optional[str] = None
    department: Optional[str] = None
    difficulty: Optional[str] = None
    hours_required: Optional[float] = None
    course_type: Optional[str] = None
    color: Optional[str] = None
    credits: Optional[float] = None
    grade: Optional[str] = None


class CourseOut(BaseModel):
    course_id: int
    user_id: int
    name: str
    course_code: Optional[str] = None
    teacher: Optional[str] = None
    department: Optional[str] = None
    difficulty: str
    hours_required: float
    course_type: str
    color: str
    credits: float
    grade: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
