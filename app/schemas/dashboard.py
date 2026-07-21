"""
app/schemas/dashboard.py
-------------------------
Schema for the dashboard summary endpoint.
Aggregates data from multiple tables for the home screen.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TodayClass(BaseModel):
    subject_name: str
    teacher: Optional[str]
    classroom: Optional[str]
    start_time: str
    end_time: str
    course_code: Optional[str]
    course_id: Optional[int] = None
    course_color: Optional[str] = None


class UpcomingTask(BaseModel):
    task_id: int
    title: str
    deadline: Optional[datetime]
    difficulty: str
    status: str
    priority: int
    course_name: Optional[str]


class DashboardSummary(BaseModel):
    today_classes: List[TodayClass]
    pending_tasks: int
    completed_tasks: int
    total_courses: int
    upcoming_deadlines: List[UpcomingTask]
    overdue_tasks: int
    today_study_hours: float
    weekly_workload_score: float  # 0-100


# ── Analytics Schemas ─────────────────────────────────

class CourseCredits(BaseModel):
    name: str
    credits: float


class CourseTaskCount(BaseModel):
    name: str
    total: int
    completed: int
    pending: int


class StatusCount(BaseModel):
    status: str
    count: int


class DifficultyCount(BaseModel):
    difficulty: str
    count: int


class AnalyticsSummary(BaseModel):
    tasks_by_status: List[StatusCount]
    tasks_by_difficulty: List[DifficultyCount]
    tasks_by_course: List[CourseTaskCount]
    credits_by_course: List[CourseCredits]
    completion_rate: float      # 0–100
    total_credits: float
    total_tasks: int
    weekly_workload_score: float
