"""
app/schemas/__init__.py
Exports all Pydantic schemas for clean imports in API routers.
"""
from .user import UserCreate, UserLogin, UserOut, Token, TokenData
from .course import CourseCreate, CourseUpdate, CourseOut
from .timetable import TimetableEntryCreate, TimetableEntryOut
from .task import TaskCreate, TaskUpdate, TaskOut
from .dashboard import DashboardSummary
from .note import NoteCreate, NoteUpdate, NoteOut
from .planner import StudySessionCreate, StudySessionOut, PlannerScheduleItem, PlannerInsight, PlannerGenerateRequest
