"""
app/api/planner.py
-------------------
Router for the AI Study Planner endpoints.
Handles schedule generation and receiving training data (feedback logs).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.task import Task
from ..models.study_session import StudySession
from ..models.timetable import TimetableEntry
from ..schemas.planner import (
    PlannerScheduleItem, PlannerInsight, PlannerGenerateRequest,
    StudySessionCreate, StudySessionOut
)
from ..services.planner import generate_schedule, global_models

router = APIRouter(prefix="/api/planner", tags=["AI Planner"])

@router.get("/schedule", response_model=List[PlannerScheduleItem])
def get_study_schedule(
    days_ahead: int = 7,
    max_daily_hours: float = 6.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates an optimized AI study schedule for the user based on pending tasks and timetable constraints.
    Uses pure-Python ML optimization.
    """
    now = datetime.now()
    
    # 1. Get all pending tasks
    tasks = db.query(Task).filter(
        Task.user_id == current_user.user_id,
        Task.status.in_(["Not Started", "In Progress"])
    ).all()
    
    # 2. Get timetable entries for constraint checking
    timetable_entries = db.query(TimetableEntry).filter(
        TimetableEntry.user_id == current_user.user_id
    ).all()
    
    # 3. Generate schedule
    schedule = generate_schedule(
        tasks=tasks,
        timetable_entries=timetable_entries,
        start_date=now.date(),
        days_ahead=days_ahead,
        max_daily_hours=max_daily_hours
    )
    
    return schedule

@router.post("/log-session", response_model=StudySessionOut)
def log_study_session(
    data: StudySessionCreate,
    completed: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Log a study session and dynamically train the AI models.
    """
    session = StudySession(
        task_id=data.task_id,
        user_id=current_user.user_id,
        date=data.date,
        duration=data.duration,
        notes=data.notes
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # --- Online Learning ---
    # 1. Update Reinforcement Learning Slot Preferences
    dt = datetime.combine(data.date, datetime.min.time())
    day_of_week = dt.weekday()
    # Assume logged at current hour if time not specified
    hour = datetime.now().hour
    
    # Reward is 1.0 for completed session, -1.0 for missed/short session
    reward = 1.0 if completed and data.duration > 0 else -1.0
    global_models.rl.update(day_of_week, hour, reward)
    
    # 2. Update K-Means Clusters
    # We ideally refit K-Means on last N sessions. For lightweight, we can just trigger it here.
    recent_sessions = db.query(StudySession).filter(
        StudySession.user_id == current_user.user_id
    ).order_by(StudySession.created_at.desc()).limit(50).all()
    
    if len(recent_sessions) >= 3:
        # Prepare data: [hour (approx), duration]
        # Since date doesn't have hour, we mock it or extract from created_at
        cluster_data = []
        for s in recent_sessions:
            h = s.created_at.hour if s.created_at else 12.0
            cluster_data.append([float(h), float(s.duration)])
        global_models.clustering.fit(cluster_data)
        
    return session

@router.get("/analytics", response_model=PlannerInsight)
def get_planner_analytics(
    current_user: User = Depends(get_current_user)
):
    """
    Get the internal state and learned weights of the AI models.
    """
    return {
        "focus_clusters": [{"centroid": c} for c in global_models.clustering.centroids],
        "compliance_weights": {
            "bias": global_models.classification.w[0],
            "hour_of_day": global_models.classification.w[1],
            "workload": global_models.classification.w[2]
        },
        "duration_multipliers": {
            "bias": global_models.regression.w[0],
            "estimated_time": global_models.regression.w[1],
            "difficulty": global_models.regression.w[2],
            "priority": global_models.regression.w[3]
        },
        "rl_slot_preferences": {
            f"Day {d} Hour {h}": global_models.rl.get_q(d, h)
            for d, h in global_models.rl.q_table.keys()
        }
    }
