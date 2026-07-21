"""
app/models/task.py
-------------------
Task/Assignment ORM model.
Tracks assignments with deadlines, difficulty, and status.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.course_id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    estimated_time = Column(Float, default=1.0)  # hours
    difficulty = Column(String(10), default="Medium")  # Easy/Medium/Hard
    status = Column(String(20), default="Not Started")
    # Not Started / In Progress / Completed / Submitted
    priority = Column(Integer, default=3)  # 1 (low) to 5 (critical)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="tasks")
    course = relationship("Course", back_populates="tasks")
    study_sessions = relationship("StudySession", back_populates="task", cascade="all, delete-orphan")
