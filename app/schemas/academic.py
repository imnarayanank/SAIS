"""
app/schemas/academic.py
------------------------
Pydantic schemas for AcademicRecord CRUD operations.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AcademicRecordCreate(BaseModel):
    semester_name: str
    sgpa: float
    cgpa: float
    total_credits: float


class AcademicRecordUpdate(BaseModel):
    semester_name: Optional[str] = None
    sgpa: Optional[float] = None
    cgpa: Optional[float] = None
    total_credits: Optional[float] = None


class AcademicRecordOut(BaseModel):
    id: int
    user_id: int
    semester_name: str
    sgpa: float
    cgpa: float
    total_credits: float
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
