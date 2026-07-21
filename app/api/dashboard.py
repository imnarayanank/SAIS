"""
app/api/dashboard.py
---------------------
Dashboard summary endpoint.
Aggregates today's classes, pending tasks, deadlines, and workload score.
This is the first thing users see when they open the app.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone, date, timedelta
from typing import List
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.timetable import TimetableEntry
from ..models.task import Task
from ..models.course import Course
from ..schemas.dashboard import (
    DashboardSummary, TodayClass, UpcomingTask,
    AnalyticsSummary, StatusCount, DifficultyCount, CourseCredits, CourseTaskCount
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

DIFFICULTY_SCORE = {"Easy": 1, "Medium": 2, "Hard": 3}


def get_today_name() -> str:
    """Get today's day name (e.g., 'Monday')."""
    return datetime.now().strftime("%A")


def calculate_workload_score(tasks: List[Task]) -> float:
    """
    Calculate a workload score 0-100 based on:
    - Number of pending tasks
    - Their difficulty
    - Proximity to deadline
    """
    now = datetime.now()
    score = 0.0

    for task in tasks:
        if task.status in ("Completed", "Submitted"):
            continue

        difficulty_weight = DIFFICULTY_SCORE.get(task.difficulty, 2)
        time_weight = task.estimated_time or 1.0

        # Urgency multiplier based on deadline proximity
        urgency = 1.0
        if task.deadline:
            days_left = (task.deadline - now).days
            if days_left <= 0:
                urgency = 3.0  # Overdue
            elif days_left <= 2:
                urgency = 2.5
            elif days_left <= 5:
                urgency = 1.5
            elif days_left <= 7:
                urgency = 1.2

        score += difficulty_weight * time_weight * urgency

    # Normalize to 0-100 (max reasonable score ~50)
    return min(round((score / 50) * 100, 1), 100.0)


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the complete dashboard summary for the current user."""
    now = datetime.now()
    today_name = get_today_name()
    user_id = current_user.user_id

    # Today's classes (omitting free periods)
    today_entries = db.query(TimetableEntry).filter(
        TimetableEntry.user_id == user_id,
        TimetableEntry.day == today_name,
    ).all()
    today_entries.sort(key=lambda e: e.start_time or "")

    today_classes = [
        TodayClass(
            subject_name=e.subject_name,
            teacher=e.teacher,
            classroom=e.classroom,
            start_time=e.start_time,
            end_time=e.end_time,
            course_code=e.course_code,
            course_id=e.course_id,
            course_color=e.course.color if e.course else None,
        )
        for e in today_entries
        if not ("free" in e.subject_name.lower() or "free" in (e.course_code or "").lower())
    ]

    # All tasks
    all_tasks = db.query(Task).filter(Task.user_id == user_id).all()
    pending = [t for t in all_tasks if t.status not in ("Completed", "Submitted")]
    completed = [t for t in all_tasks if t.status in ("Completed", "Submitted")]

    # Overdue tasks
    overdue = [
        t for t in pending
        if t.deadline and t.deadline < now
    ]

    # Upcoming deadlines (next 7 days, sorted)
    next_week = now + timedelta(days=7)
    upcoming = [
        t for t in pending
        if t.deadline and now <= t.deadline <= next_week
    ]
    upcoming.sort(key=lambda t: t.deadline)

    # Load course names
    course_map = {c.course_id: c.name for c in db.query(Course).filter(Course.user_id == user_id).all()}

    upcoming_tasks = [
        UpcomingTask(
            task_id=t.task_id,
            title=t.title,
            deadline=t.deadline,
            difficulty=t.difficulty,
            status=t.status,
            priority=t.priority,
            course_name=course_map.get(t.course_id),
        )
        for t in upcoming[:8]  # Show max 8
    ]

    # Total courses
    total_courses = db.query(Course).filter(Course.user_id == user_id).count()

    # Workload score
    workload = calculate_workload_score(pending)

    # Calculate actual study hours logged today
    from ..models.study_session import StudySession
    today_hours = sum(s.duration for s in db.query(StudySession).filter(
        StudySession.user_id == user_id,
        StudySession.date == date.today(),
    ).all())

    return DashboardSummary(
        today_classes=today_classes,
        pending_tasks=len(pending),
        completed_tasks=len(completed),
        total_courses=total_courses,
        upcoming_deadlines=upcoming_tasks,
        overdue_tasks=len(overdue),
        today_study_hours=today_hours,
        weekly_workload_score=workload,
    )


@router.get("/analytics", response_model=AnalyticsSummary)
def get_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return rich analytics data for charts on the dashboard."""
    user_id = current_user.user_id

    all_tasks = db.query(Task).filter(Task.user_id == user_id).all()
    all_courses = db.query(Course).filter(Course.user_id == user_id).all()

    # ── Tasks by Status ──────────────────────────────
    status_map: dict = {}
    for t in all_tasks:
        status_map[t.status] = status_map.get(t.status, 0) + 1
    status_order = ["Not Started", "In Progress", "Completed", "Submitted"]
    tasks_by_status = [
        StatusCount(status=s, count=status_map.get(s, 0))
        for s in status_order
    ]

    # ── Tasks by Difficulty ──────────────────────────
    diff_map: dict = {}
    for t in all_tasks:
        diff_map[t.difficulty] = diff_map.get(t.difficulty, 0) + 1
    diff_order = ["Easy", "Medium", "Hard"]
    tasks_by_difficulty = [
        DifficultyCount(difficulty=d, count=diff_map.get(d, 0))
        for d in diff_order
    ]

    # ── Tasks by Course ──────────────────────────────
    course_map = {c.course_id: c.name for c in all_courses}
    course_task_data: dict = {}
    for t in all_tasks:
        cname = course_map.get(t.course_id, "Unassigned")
        if cname not in course_task_data:
            course_task_data[cname] = {"total": 0, "completed": 0, "pending": 0}
        course_task_data[cname]["total"] += 1
        if t.status in ("Completed", "Submitted"):
            course_task_data[cname]["completed"] += 1
        else:
            course_task_data[cname]["pending"] += 1
    tasks_by_course = [
        CourseTaskCount(name=name, **vals)
        for name, vals in sorted(course_task_data.items(), key=lambda x: -x[1]["total"])
    ]

    # ── Credits by Course ────────────────────────────
    credits_by_course = [
        CourseCredits(name=c.name[:20], credits=c.credits or 0.0)
        for c in sorted(all_courses, key=lambda c: -(c.credits or 0))
    ]
    total_credits = sum(c.credits or 0.0 for c in all_courses)

    # ── Completion Rate ──────────────────────────────
    total_tasks = len(all_tasks)
    done = sum(1 for t in all_tasks if t.status in ("Completed", "Submitted"))
    completion_rate = round((done / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    # ── Workload Score ───────────────────────────────
    pending_tasks = [t for t in all_tasks if t.status not in ("Completed", "Submitted")]
    workload = calculate_workload_score(pending_tasks)

    return AnalyticsSummary(
        tasks_by_status=tasks_by_status,
        tasks_by_difficulty=tasks_by_difficulty,
        tasks_by_course=tasks_by_course,
        credits_by_course=credits_by_course,
        completion_rate=completion_rate,
        total_credits=total_credits,
        total_tasks=total_tasks,
        weekly_workload_score=workload,
    )
