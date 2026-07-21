"""
app/schemas/timetable.py
-------------------------
Pydantic schemas for Timetable entries.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TimetableEntryCreate(BaseModel):
    course_id: Optional[int] = None
    subject_name: str
    course_code: Optional[str] = None
    teacher: Optional[str] = None
    classroom: Optional[str] = None
    day: str
    start_time: str
    end_time: str


class TimetableEntryOut(BaseModel):
    timetable_id: int
    course_id: Optional[int] = None
    user_id: int
    subject_name: str
    course_code: Optional[str] = None
    teacher: Optional[str] = None
    classroom: Optional[str] = None
    day: str
    start_time: str
    end_time: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
