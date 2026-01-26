from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.task import Task
from app.api.v1.auth import get_current_active_user

router = APIRouter()


@router.get("/tasks")
async def list_tasks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all automation tasks"""
    tasks = db.query(Task).all()
    return tasks


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get task by ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.post("/tasks/{task_id}/execute")
async def execute_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Execute a task manually"""
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # TODO: Implement task execution via Celery
    return {"message": "Task execution queued", "task_id": task_id}
