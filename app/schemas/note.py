"""
app/schemas/note.py
--------------------
Pydantic schemas for Notes management.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NoteCreate(BaseModel):
    course_id: Optional[int] = None
    title: str = "Untitled note"
    content: Optional[str] = None
    tags: Optional[str] = None
    is_favourite: bool = False


class NoteUpdate(BaseModel):
    course_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    is_favourite: Optional[bool] = None


class NoteOut(BaseModel):
    note_id: int
    course_id: Optional[int] = None
    user_id: int
    title: str
    content: Optional[str] = None
    tags: Optional[str] = None
    is_favourite: bool
    attachments: Optional[str] = None  # JSON string of attachment list
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
