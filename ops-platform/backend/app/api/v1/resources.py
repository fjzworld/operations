from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.models.user import User
from app.models.resource import Resource, ResourceType, ResourceStatus
from app.schemas.resource import ResourceCreate, ResourceUpdate, ResourceInDB, ResourceMetrics, ResourceProbeRequest, ResourceProbeResponse, ResourceDeleteRequest
from app.api.v1.auth import get_current_active_user
from app.services.resource_detector import probe_server, SSHCredentials
from app.services.agent_deployer import deploy_agent, uninstall_agent
from app.core.security import create_access_token
from app.core.encryption import encrypt_string
from datetime import timedelta

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
    """
    Create a new resource.
    
    If SSH credentials (password or key) are provided:
    1. Probes the server to auto-detect hardware info (CPU, Memory, Disk, OS).
    2. Encrypts and saves credentials.
    3. Auto-deploys the monitoring agent.
    """
    # Check if resource name already exists
    if db.query(Resource).filter(Resource.name == resource_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource name already exists"
        )
    
    # Check if we should perform auto-discovery
    auto_discovery = False
    probe_info = None
    
    if resource_data.ip_address and (resource_data.ssh_password or resource_data.ssh_private_key):
        auto_discovery = True
        try:
            # 1. Probe Server
            print(f"Auto-probing server: {resource_data.ip_address}")
            credentials = SSHCredentials(
                host=resource_data.ip_address,
                port=resource_data.ssh_port,
                username=resource_data.ssh_username,
                password=resource_data.ssh_password,
                private_key=resource_data.ssh_private_key
            )
            probe_info = probe_server(credentials)
            
            # Update resource data with probed info
            if not resource_data.hostname: resource_data.hostname = probe_info.hostname
            if not resource_data.cpu_cores: resource_data.cpu_cores = probe_info.cpu_cores
            if not resource_data.memory_gb: resource_data.memory_gb = probe_info.memory_gb
            if not resource_data.disk_gb: resource_data.disk_gb = probe_info.disk_gb
            if not resource_data.os_type: resource_data.os_type = f"{probe_info.os_type} {probe_info.os_version}"
            
        except Exception as e:
            # If probing fails, we abort creation because the credentials might be wrong
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Server connection failed: {str(e)}"
            )

    # Prepare DB object
    db_resource_dict = resource_data.dict(exclude={
        "ssh_password", "ssh_private_key", "backend_url"
    })
    
    # Add encrypted credentials if available
    if resource_data.ssh_password:
        db_resource_dict["ssh_password_enc"] = encrypt_string(resource_data.ssh_password)
    if resource_data.ssh_private_key:
        db_resource_dict["ssh_private_key_enc"] = encrypt_string(resource_data.ssh_private_key)
        
    db_resource = Resource(**db_resource_dict)
    
    if auto_discovery:
        db_resource.status = ResourceStatus.ACTIVE
    
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    
    # 3. Deploy Agent (Async/Background ideally, but doing sync for simplicity now)
    if auto_discovery:
        try:
            print(f"Auto-deploying agent to {db_resource.name}...")
            # Generate Token
            access_token_expires = timedelta(days=365*10)
            api_token = create_access_token(
                data={"sub": current_user.username},
                expires_delta=access_token_expires
            )
            
            # Use provided backend URL or default
            backend_url = resource_data.backend_url or "http://ops-nginx/api/v1"
            
            success = deploy_agent(
                credentials=credentials,
                resource_id=db_resource.id,
                api_token=api_token,
                backend_url=backend_url
            )
            
            if success:
                print(f"Agent deployed successfully to {db_resource.name}")
            else:
                print(f"Agent deployment failed for {db_resource.name}")
                # We don't rollback creation, just warn
        except Exception as e:
            print(f"Error deploying agent: {e}")
    
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
    delete_request: Optional[ResourceDeleteRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete resource and optionally uninstall agent
    
    If delete_request is provided with SSH credentials, the agent will be uninstalled
    from the remote server before deleting the resource from the database.
    """
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
    
    # Try to uninstall agent if requested and credentials provided
    agent_uninstalled = False
    uninstall_error = None
    
    print(f"收到删除请求: resource_id={resource_id}, payload={delete_request}")
    
    if delete_request and delete_request.uninstall_agent and resource.ip_address:
        print(f"准备卸载 Agent: host={resource.ip_address}, user={delete_request.ssh_username}")
        try:
            credentials = SSHCredentials(
                host=resource.ip_address,
                port=delete_request.ssh_port,
                username=delete_request.ssh_username,
                password=delete_request.ssh_password,
                private_key=delete_request.ssh_private_key
            )
            
            print(f"正在从 {resource.ip_address} 卸载 Agent...")
            agent_uninstalled = uninstall_agent(credentials)
            
            if agent_uninstalled:
                print(f"✓ Agent 已从 {resource.ip_address} 卸载")
            else:
                print(f"⚠ Agent 卸载失败，但继续删除资源")
                uninstall_error = "Agent 卸载失败（可能已被手动删除）"
                
        except Exception as e:
            print(f"⚠ 卸载 Agent 时出错: {e}")
            uninstall_error = str(e)
            # 继续删除资源，即使 Agent 卸载失败
    
    # Delete resource from database
    db.delete(resource)
    db.commit()
    
    response = {
        "message": "资源已成功删除",
        "agent_uninstalled": agent_uninstalled
    }
    
    if uninstall_error:
        response["warning"] = f"资源已删除，但 Agent 卸载失败: {uninstall_error}"
    
    return response


@router.post("/{resource_id}/metrics")
async def update_resource_metrics(
    resource_id: int,
    metrics: ResourceMetrics,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update resource metrics and store historical data"""
    from app.models.metric import Metric, ProcessMetric
    
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    # Update current metrics on resource
    resource.cpu_usage = metrics.cpu_usage
    resource.memory_usage = metrics.memory_usage
    resource.disk_usage = metrics.disk_usage
    resource.last_seen = datetime.utcnow()
    
    # Store historical metrics
    metric_record = Metric(
        resource_id=resource_id,
        cpu_usage=metrics.cpu_usage,
        memory_usage=metrics.memory_usage,
        disk_usage=metrics.disk_usage,
        network_in=metrics.network_in or 0,
        network_out=metrics.network_out or 0
    )
    db.add(metric_record)
    
    # Store top processes if provided
    if metrics.top_processes:
        for proc in metrics.top_processes[:5]:  # Limit to top 5
            process_record = ProcessMetric(
                resource_id=resource_id,
                process_name=proc.get('name', 'unknown'),
                process_pid=proc.get('pid', 0),
                cpu_percent=proc.get('cpu_percent', 0),
                memory_percent=proc.get('memory_percent', 0)
            )
            db.add(process_record)
    
    db.commit()
    
    # Check for alert thresholds
    await check_alert_thresholds(resource, metrics, db)
    
    return {"message": "Metrics updated successfully"}


async def check_alert_thresholds(resource: Resource, metrics: ResourceMetrics, db: Session):
    """Check if metrics exceed alert thresholds"""
    from app.models.alert import Alert, AlertSeverity, AlertStatus
    
    # Query active alert rules for this resource
    # For now, use simple thresholds
    alerts_to_create = []
    
    if metrics.cpu_usage > 80:
        alerts_to_create.append({
            "resource_id": resource.id,
            "severity": AlertSeverity.CRITICAL if metrics.cpu_usage > 90 else AlertSeverity.WARNING,
            "message": f"High CPU usage on {resource.name}: {metrics.cpu_usage:.1f}%",
            "status": AlertStatus.FIRING
        })
    
    if metrics.memory_usage > 80:
        alerts_to_create.append({
            "resource_id": resource.id,
            "severity": AlertSeverity.CRITICAL if metrics.memory_usage > 90 else AlertSeverity.WARNING,
            "message": f"High memory usage on {resource.name}: {metrics.memory_usage:.1f}%",
            "status": AlertStatus.FIRING
        })
    
    if metrics.disk_usage > 85:
        alerts_to_create.append({
            "resource_id": resource.id,
            "severity": AlertSeverity.WARNING,
            "message": f"High disk usage on {resource.name}: {metrics.disk_usage:.1f}%",
            "status": AlertStatus.FIRING
        })
    
    for alert_data in alerts_to_create:
        alert = Alert(**alert_data)
        db.add(alert)
    
    if alerts_to_create:
        db.commit()


@router.get("/{resource_id}/metrics/history")
async def get_metrics_history(
    resource_id: int,
    hours: int = Query(24, ge=1, le=168),  # Last 24 hours by default, max 1 week
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get historical metrics for a resource"""
    from app.models.metric import Metric
    from datetime import timedelta
    
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    # Query metrics from last N hours
    since = datetime.utcnow() - timedelta(hours=hours)
    metrics = db.query(Metric).filter(
        Metric.resource_id == resource_id,
        Metric.timestamp >= since
    ).order_by(Metric.timestamp.asc()).all()
    
    return {
        "resource_id": resource_id,
        "resource_name": resource.name,
        "period_hours": hours,
        "data_points": len(metrics),
        "metrics": [
            {
                "timestamp": m.timestamp.isoformat(),
                "cpu_usage": m.cpu_usage,
                "memory_usage": m.memory_usage,
                "disk_usage": m.disk_usage,
                "network_in": m.network_in,
                "network_out": m.network_out
            }
            for m in metrics
        ]
    }


@router.get("/{resource_id}/processes")
async def get_top_processes(
    resource_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get latest top processes for a resource"""
    from app.models.metric import ProcessMetric
    from datetime import timedelta
    
    # Get processes from last 5 minutes
    since = datetime.utcnow() - timedelta(minutes=5)
    processes = db.query(ProcessMetric).filter(
        ProcessMetric.resource_id == resource_id,
        ProcessMetric.timestamp >= since
    ).order_by(ProcessMetric.timestamp.desc()).limit(10).all()
    
    return {
        "resource_id": resource_id,
        "processes": [
            {
                "name": p.process_name,
                "pid": p.process_pid,
                "cpu_percent": p.cpu_percent,
                "memory_percent": p.memory_percent,
                "timestamp": p.timestamp.isoformat()
            }
            for p in processes
        ]
    }
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


@router.post("/probe", response_model=ResourceProbeResponse)
async def probe_resource(
    probe_request: ResourceProbeRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Probe a remote server via SSH to auto-detect hardware specs
    Returns: CPU cores, memory, disk, OS info
    """
    try:
        credentials = SSHCredentials(
            host=probe_request.ip_address,
            port=probe_request.ssh_port,
            username=probe_request.ssh_username,
            password=probe_request.ssh_password,
            private_key=probe_request.ssh_private_key
        )
        
        # Execute probe
        server_info = probe_server(credentials)
        
        return ResourceProbeResponse(
            hostname=server_info.hostname,
            cpu_cores=server_info.cpu_cores,
            memory_gb=server_info.memory_gb,
            disk_gb=server_info.disk_gb,
            os_type=server_info.os_type,
            os_version=server_info.os_version,
            kernel_version=server_info.kernel_version
        )
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SSH连接失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"探测失败: {str(e)}"
        )


@router.post("/{resource_id}/deploy-agent")
async def deploy_monitoring_agent(
    resource_id: int,
    probe_request: ResourceProbeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deploy monitoring agent to remote server
    The agent will continuously report metrics to backend
    """
    # Verify resource exists
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    try:
        credentials = SSHCredentials(
            host=probe_request.ip_address,
            port=probe_request.ssh_port,
            username=probe_request.ssh_username,
            password=probe_request.ssh_password,
            private_key=probe_request.ssh_private_key
        )
        
        # Deploy agent
        # Generate a long-lived token for the agent (10 years)
        access_token_expires = timedelta(days=365*10)
        api_token = create_access_token(
            data={"sub": current_user.username},
            expires_delta=access_token_expires
        )
        
        # Use provided backend URL or default to internal network
        # If the request comes from frontend, it should provide the external URL
        backend_url = probe_request.backend_url or "http://ops-nginx/api/v1"
        
        success = deploy_agent(
            credentials=credentials,
            resource_id=resource_id,
            api_token=api_token,
            backend_url=backend_url
        )
        
        if success:
            # Update resource status
            resource.status = ResourceStatus.ACTIVE
            db.commit()
            
            return {"message": "Monitoring agent deployed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agent deployment failed"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"部署失败: {str(e)}"
        )
