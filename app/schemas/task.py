"""
app/schemas/task.py
--------------------
Pydantic schemas for Task/Assignment management.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskCreate(BaseModel):
    course_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    estimated_time: Optional[float] = 1.0
    difficulty: Optional[str] = "Medium"
    status: Optional[str] = "Not Started"
    priority: Optional[int] = 3


class TaskUpdate(BaseModel):
    course_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    estimated_time: Optional[float] = None
    difficulty: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None


class TaskOut(BaseModel):
    task_id: int
    course_id: Optional[int] = None
    user_id: int
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    estimated_time: float
    difficulty: str
    status: str
    priority: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    course_name: Optional[str] = None  # Joined from course

    model_config = {"from_attributes": True}
