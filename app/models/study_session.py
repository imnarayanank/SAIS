"""
app/models/study_session.py
-----------------------------
StudySession ORM model.
Tracks time spent studying for a specific task.
Used by the AI planner to understand study patterns.
"""
from sqlalchemy import Column, Integer, Float, Date, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from ..core.database import Base


class StudySession(Base):
    __tablename__ = "study_sessions"

    session_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.task_id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    duration = Column(Float, nullable=False)  # hours
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    task = relationship("Task", back_populates="study_sessions")
