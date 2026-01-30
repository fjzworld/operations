import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.resource import Resource
from app.api.v1.auth import get_current_active_user
import httpx
import os

logger = logging.getLogger(__name__)
router = APIRouter()

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

# --- Prometheus Proxy Endpoints ---

@router.get("/query")
async def query_prometheus(
    query: str,
    time: float = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Proxy query to Prometheus (Instant Query)
    Example: query=opspro_cpu_usage_percent
    """
    params = {"query": query}
    if time:
        params["time"] = time
        
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params=params)
            return resp.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Prometheus connection failed: {e}")

@router.get("/query_range")
async def query_range_prometheus(
    query: str,
    start: float,
    end: float,
    step: int = 60,
    current_user: User = Depends(get_current_active_user)
):
    """
    Proxy query to Prometheus (Range Query)
    Example: query=opspro_cpu_usage_percent&start=1700000000&end=1700003600&step=60
    """
    params = {
        "query": query,
        "start": start,
        "end": end,
        "step": step
    }
        
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{PROMETHEUS_URL}/api/v1/query_range", params=params)
            return resp.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Prometheus connection failed: {e}")

# --- Existing Dashboard Endpoint (Legacy/Hybrid) ---

@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard monitoring data from Prometheus
    """
    async with httpx.AsyncClient() as client:
        try:
            # Prepare queries
            queries = {
                "total_online": "count(opspro_cpu_usage_percent)",
                "avg_cpu": "avg(opspro_cpu_usage_percent)",
                "avg_mem": "avg(opspro_memory_usage_percent)",
                "total_net_in": "sum(opspro_network_in_mb)",
                "total_net_out": "sum(opspro_network_out_mb)",
                "top_cpu": "topk(5, opspro_cpu_usage_percent)",
                "all_nodes": "opspro_cpu_usage_percent"
            }
            
            results = {}
            for key, q in queries.items():
                resp = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": q})
                data = resp.json()
                if data["status"] == "success" and data["data"]["result"]:
                    results[key] = data["data"]["result"]
                else:
                    results[key] = []

            # Process results
            # Helper to get scalar value
            def get_scalar(key, default=0.0):
                if results.get(key) and len(results[key]) > 0:
                    return float(results[key][0]["value"][1])
                return default

            # Process All Nodes for Heatmap
            all_resources_status = []
            if results.get("all_nodes"):
                for item in results["all_nodes"]:
                    metric = item["metric"]
                    cpu_val = float(item["value"][1])
                    
                    status = "normal"
                    if cpu_val > 80: status = "critical"
                    elif cpu_val > 50: status = "warning"
                    
                    all_resources_status.append({
                        "id": metric.get("resource_id", "0"),
                        "name": metric.get("resource_name", "Unknown"),
                        "ip": metric.get("ip_address", ""),
                        "cpu": round(cpu_val, 1),
                        "status": status
                    })

            # Process Top 5
            top_cpu_resources = []
            if results.get("top_cpu"):
                for item in results["top_cpu"]:
                    # item = {"metric": {"resource_id": "1", "resource_name": "foo", ...}, "value": [ts, "12.3"]}
                    metric = item["metric"]
                    value = float(item["value"][1])
                    top_cpu_resources.append({
                        "id": metric.get("resource_id", "0"),
                        "name": metric.get("resource_name", "Unknown"),
                        "cpu_usage": round(value, 1),
                        # Memory usage is tricky to map without a join, we skip it for now or query separately
                        "memory_usage": 0 
                    })
                # Sort again because Prometheus topk sort might be unstable or we want to be sure
                top_cpu_resources.sort(key=lambda x: x["cpu_usage"], reverse=True)

            # Get database total count (including offline)
            total_db_resources = db.query(Resource).count()

            return {
                "total_resources": total_db_resources,
                "online_resources": int(get_scalar("total_online")),
                "average_cpu_usage": round(get_scalar("avg_cpu"), 1),
                "average_memory_usage": round(get_scalar("avg_mem"), 1),
                "total_network_traffic": round(get_scalar("total_net_in") + get_scalar("total_net_out"), 1),
                "top_cpu_resources": top_cpu_resources,
                "all_resources_status": all_resources_status
            }

        except Exception as e:
            logger.error(f"Dashboard data fetch failed: {e}", exc_info=True)
            # Fallback to DB if Prometheus fails
            resources = db.query(Resource).all()
            if resources:
                avg_cpu = sum(r.cpu_usage for r in resources) / len(resources)
            else:
                avg_cpu = 0
            return {
                "total_resources": len(resources),
                "online_resources": 0,
                "average_cpu_usage": round(avg_cpu, 1),
                "error": str(e)
            }
