from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from prometheus_client import Gauge
from app.core.database import get_db
from app.models.user import User
from app.models.resource import Resource
from app.api.v1.auth import get_current_active_user

router = APIRouter()

# Define Prometheus metrics
resource_cpu_usage = Gauge('resource_cpu_usage_percent', 'CPU usage percentage', ['resource_id', 'resource_name'])
resource_memory_usage = Gauge('resource_memory_usage_percent', 'Memory usage percentage', ['resource_id', 'resource_name'])
resource_disk_usage = Gauge('resource_disk_usage_percent', 'Disk usage percentage', ['resource_id', 'resource_name'])
total_resources = Gauge('total_resources', 'Total number of resources')
active_resources = Gauge('active_resources', 'Number of active resources')


@router.get("/metrics/update")
async def update_metrics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update Prometheus metrics from database"""
    resources = db.query(Resource).all()
    
    # Update resource metrics
    for resource in resources:
        resource_cpu_usage.labels(
            resource_id=str(resource.id),
            resource_name=resource.name
        ).set(resource.cpu_usage)
        
        resource_memory_usage.labels(
            resource_id=str(resource.id),
            resource_name=resource.name
        ).set(resource.memory_usage)
        
        resource_disk_usage.labels(
            resource_id=str(resource.id),
            resource_name=resource.name
        ).set(resource.disk_usage)
    
    # Update totals
    total_resources.set(len(resources))
    active_resources.set(len([r for r in resources if r.status.value == "active"]))
    
    return {"message": "Metrics updated", "resources_count": len(resources)}


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dashboard monitoring data"""
    resources = db.query(Resource).all()
    
    # Calculate average usage
    if resources:
        avg_cpu = sum(r.cpu_usage for r in resources) / len(resources)
        avg_memory = sum(r.memory_usage for r in resources) / len(resources)
        avg_disk = sum(r.disk_usage for r in resources) / len(resources)
    else:
        avg_cpu = avg_memory = avg_disk = 0
    
    # Get top 5 resources by CPU usage
    top_cpu_resources = sorted(resources, key=lambda r: r.cpu_usage, reverse=True)[:5]
    
    return {
        "total_resources": len(resources),
        "average_cpu_usage": round(avg_cpu, 2),
        "average_memory_usage": round(avg_memory, 2),
        "average_disk_usage": round(avg_disk, 2),
        "top_cpu_resources": [
            {
                "id": r.id,
                "name": r.name,
                "cpu_usage": r.cpu_usage,
                "memory_usage": r.memory_usage
            }
            for r in top_cpu_resources
        ]
    }
