"""
app/schemas/planner.py
-----------------------
Pydantic schemas for the AI Study Planner and Study Sessions.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class StudySessionCreate(BaseModel):
    task_id: Optional[int] = None
    date: date
    duration: float  # hours
    notes: Optional[str] = None


class StudySessionOut(BaseModel):
    session_id: int
    task_id: Optional[int] = None
    user_id: int
    date: date
    duration: float
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PlannerScheduleItem(BaseModel):
    task_id: int
    task_title: str
    course_name: str
    course_color: str
    date: str
    start_time: str
    end_time: str
    compliance_probability: float
    difficulty: str


class PlannerInsight(BaseModel):
    focus_clusters: List[dict]
    compliance_weights: dict
    duration_multipliers: dict
    rl_slot_preferences: dict

class PlannerGenerateRequest(BaseModel):
    days_ahead: int = 7
    max_daily_hours: float = 6.0
