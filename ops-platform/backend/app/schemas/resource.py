from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from app.models.resource import ResourceType, ResourceStatus


class ResourceBase(BaseModel):
    """Base resource schema"""
    name: str = Field(..., min_length=1, max_length=100)
    type: ResourceType
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    cpu_cores: Optional[int] = Field(None, ge=1)
    memory_gb: Optional[float] = Field(None, ge=0)
    disk_gb: Optional[float] = Field(None, ge=0)
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    tags: List[str] = []
    labels: Dict[str, str] = {}
    description: Optional[str] = None


class ResourceCreate(ResourceBase):
    """Schema for creating a resource"""
    pass


class ResourceUpdate(BaseModel):
    """Schema for updating a resource"""
    name: Optional[str] = None
    status: Optional[ResourceStatus] = None
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_gb: Optional[float] = None
    disk_gb: Optional[float] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    tags: Optional[List[str]] = None
    labels: Optional[Dict[str, str]] = None
    description: Optional[str] = None


class ResourceInDB(ResourceBase):
    """Schema for resource in database"""
    id: int
    status: ResourceStatus
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ResourceMetrics(BaseModel):
    """Resource metrics update"""
    cpu_usage: float = Field(..., ge=0, le=100)
    memory_usage: float = Field(..., ge=0, le=100)
    disk_usage: float = Field(..., ge=0, le=100)
