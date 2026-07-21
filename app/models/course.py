"""
app/models/course.py
---------------------
Course ORM model. Each course belongs to a user.
Stores academic details including difficulty and course type.
"""
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum


class DifficultyLevel(str, enum.Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class CourseType(str, enum.Enum):
    THEORY = "Theory"
    PROGRAMMING = "Programming"
    LAB = "Lab"
    MATHEMATICS = "Mathematics"
    PROJECT = "Project"


class Course(Base):
    __tablename__ = "courses"

    course_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String(200), nullable=False)
    course_code = Column(String(50), nullable=True)
    teacher = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    difficulty = Column(String(10), default="Medium")
    hours_required = Column(Float, default=3.0)
    course_type = Column(String(20), default="Theory")
    color = Column(String(7), default="#3B82F6")  # Hex color for UI
    credits = Column(Float, default=3.0)
    grade = Column(String(5), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="courses")
    timetable_entries = relationship("TimetableEntry", back_populates="course", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="course")
    notes = relationship("Note", back_populates="course")
