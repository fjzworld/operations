from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.models.user import User
from app.models.resource import Resource, ResourceType, ResourceStatus
from app.schemas.resource import ResourceCreate, ResourceUpdate, ResourceInDB, ResourceMetrics
from app.api.v1.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[ResourceInDB])
async def list_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    resource_type: Optional[ResourceType] = None,
    status: Optional[ResourceStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all resources"""
    query = db.query(Resource)
    
    if resource_type:
        query = query.filter(Resource.type == resource_type)
    
    if status:
        query = query.filter(Resource.status == status)
    
    resources = query.offset(skip).limit(limit).all()
    return resources


@router.get("/{resource_id}", response_model=ResourceInDB)
async def get_resource(
    resource_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get resource by ID"""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    return resource


@router.post("/", response_model=ResourceInDB, status_code=status.HTTP_201_CREATED)
async def create_resource(
    resource_data: ResourceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new resource"""
    # Check if resource name already exists
    if db.query(Resource).filter(Resource.name == resource_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource name already exists"
        )
    
    # Create resource
    db_resource = Resource(**resource_data.dict())
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    
    return db_resource


@router.put("/{resource_id}", response_model=ResourceInDB)
async def update_resource(
    resource_id: int,
    resource_update: ResourceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update resource"""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    # Update fields
    update_data = resource_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resource, field, value)
    
    db.commit()
    db.refresh(resource)
    
    return resource


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete resource"""
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    db.delete(resource)
    db.commit()
    
    return {"message": "Resource deleted successfully"}


@router.post("/{resource_id}/metrics")
async def update_resource_metrics(
    resource_id: int,
    metrics: ResourceMetrics,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update resource metrics"""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    # Update metrics
    resource.cpu_usage = metrics.cpu_usage
    resource.memory_usage = metrics.memory_usage
    resource.disk_usage = metrics.disk_usage
    resource.last_seen = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Metrics updated successfully"}


@router.get("/stats/summary")
async def get_resource_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get resource statistics summary"""
    total = db.query(Resource).count()
    active = db.query(Resource).filter(Resource.status == ResourceStatus.ACTIVE).count()
    inactive = db.query(Resource).filter(Resource.status == ResourceStatus.INACTIVE).count()
    
    by_type = {}
    for resource_type in ResourceType:
        count = db.query(Resource).filter(Resource.type == resource_type).count()
        by_type[resource_type.value] = count
    
    return {
        "total": total,
        "active": active,
        "inactive": inactive,
        "by_type": by_type
    }
