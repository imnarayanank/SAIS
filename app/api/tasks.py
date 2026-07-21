"""
app/api/tasks.py
-----------------
Task/Assignment management routes.
Supports filtering by status, course, and sorting by deadline/priority.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timezone
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.task import Task
from ..models.course import Course
from ..schemas.task import TaskCreate, TaskUpdate, TaskOut

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


def task_to_out(task: Task) -> TaskOut:
    """Convert Task ORM to TaskOut schema, adding course name."""
    data = TaskOut.model_validate(task)
    if task.course:
        data.course_name = task.course.name
    return data


@router.get("/", response_model=List[TaskOut])
def list_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    course_id: Optional[int] = None,
    sort_by: str = Query("deadline", pattern="^(deadline|priority|created_at)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all tasks with optional filters.
    - status: Filter by task status
    - course_id: Filter by course
    - sort_by: Sort by deadline (default), priority, or created_at
    """
    query = db.query(Task).options(joinedload(Task.course)).filter(
        Task.user_id == current_user.user_id
    )

    if status_filter and status_filter.lower() != "all":
        query = query.filter(Task.status == status_filter)
    if course_id:
        query = query.filter(Task.course_id == course_id)

    tasks = query.all()

    # Sort
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if sort_by == "deadline":
        tasks.sort(key=lambda t: t.deadline or datetime(9999, 12, 31))
    elif sort_by == "priority":
        tasks.sort(key=lambda t: -t.priority)

    return [task_to_out(t) for t in tasks]


@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new task/assignment."""
    task = Task(**data.model_dump(), user_id=current_user.user_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    # Reload with course
    task = db.query(Task).options(joinedload(Task.course)).filter(Task.task_id == task.task_id).first()
    return task_to_out(task)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single task by ID."""
    task = db.query(Task).options(joinedload(Task.course)).filter(
        Task.task_id == task_id,
        Task.user_id == current_user.user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_to_out(task)


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a task (supports partial updates)."""
    task = db.query(Task).filter(
        Task.task_id == task_id,
        Task.user_id == current_user.user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    task = db.query(Task).options(joinedload(Task.course)).filter(Task.task_id == task_id).first()
    return task_to_out(task)


@router.patch("/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int,
    new_status: str = Query(..., pattern="^(Not Started|In Progress|Completed|Submitted)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Quick status update for a task (e.g., from Kanban-style UI)."""
    task = db.query(Task).filter(
        Task.task_id == task_id,
        Task.user_id == current_user.user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = new_status
    db.commit()
    task = db.query(Task).options(joinedload(Task.course)).filter(Task.task_id == task_id).first()
    return task_to_out(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a task."""
    task = db.query(Task).filter(
        Task.task_id == task_id,
        Task.user_id == current_user.user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
