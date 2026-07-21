"""
app/models/timetable.py
------------------------
TimetableEntry ORM model.
Each entry represents a single class slot in the weekly schedule.
Parsed from Excel uploads or added manually.
"""
from sqlalchemy import Column, Integer, String, Time, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from ..core.database import Base


class TimetableEntry(Base):
    __tablename__ = "timetable"

    timetable_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.course_id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    # Class details
    subject_name = Column(String(200), nullable=False)
    course_code = Column(String(50), nullable=True)
    teacher = Column(String(100), nullable=True)
    classroom = Column(String(100), nullable=True)
    day = Column(String(20), nullable=False)  # Monday, Tuesday, etc.
    start_time = Column(String(10), nullable=False)  # HH:MM format
    end_time = Column(String(10), nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="timetable_entries")
    course = relationship("Course", back_populates="timetable_entries")
