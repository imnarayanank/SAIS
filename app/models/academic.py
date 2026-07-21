"""
app/models/academic.py
-----------------------
Academic Record ORM model.
Stores user's CGPA and SGPA per semester.
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..core.database import Base


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    semester_name = Column(String(100), nullable=False) # e.g. "Fall 2026" or "Semester 1"
    sgpa = Column(Float, nullable=False)
    cgpa = Column(Float, nullable=False)
    total_credits = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="academic_records")
