"""
app/models/__init__.py
Exports all ORM models so they register with SQLAlchemy Base.
"""
from .user import User
from .course import Course
from .timetable import TimetableEntry
from .task import Task
from .study_session import StudySession
from .note import Note
from .academic import AcademicRecord

__all__ = ["User", "Course", "TimetableEntry", "Task", "StudySession", "Note", "AcademicRecord"]
