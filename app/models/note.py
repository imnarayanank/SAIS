"""
app/models/note.py
-------------------
Note ORM model.
Supports rich text content, tags, and file attachments.
Linked to a course for organization.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Note(Base):
    __tablename__ = "notes"

    note_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.course_id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)  # Rich HTML content
    tags = Column(String(500), nullable=True)  # Comma-separated
    is_favourite = Column(Boolean, default=False)
    attachments = Column(Text, nullable=True)  # JSON array of file paths

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="notes")
    course = relationship("Course", back_populates="notes")
