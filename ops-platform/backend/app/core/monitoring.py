from prometheus_client import Gauge

# Define Prometheus Metrics
# Labels: resource_id, resource_name, ip_address

CPU_USAGE = Gauge(
    'opspro_cpu_usage_percent', 
    'CPU Usage Percentage', 
    ['resource_id', 'resource_name', 'ip_address']
)

MEMORY_USAGE = Gauge(
    'opspro_memory_usage_percent', 
    'Memory Usage Percentage', 
    ['resource_id', 'resource_name', 'ip_address']
)

DISK_USAGE = Gauge(
    'opspro_disk_usage_percent', 
    'Disk Usage Percentage', 
    ['resource_id', 'resource_name', 'ip_address']
)

NETWORK_IN = Gauge(
    'opspro_network_in_mb', 
    'Network Incoming Traffic (MB/s)', 
    ['resource_id', 'resource_name', 'ip_address']
)

NETWORK_OUT = Gauge(
    'opspro_network_out_mb', 
    'Network Outgoing Traffic (MB/s)', 
    ['resource_id', 'resource_name', 'ip_address']
)

def update_metrics(resource_id: str, resource_name: str, ip_address: str, metrics: dict):
    """
    Update Prometheus metrics for a resource
    """
    labels = {
        'resource_id': str(resource_id),
        'resource_name': resource_name,
        'ip_address': ip_address
    }
    
    if 'cpu_usage' in metrics:
        CPU_USAGE.labels(**labels).set(metrics['cpu_usage'])
        
    if 'memory_usage' in metrics:
        MEMORY_USAGE.labels(**labels).set(metrics['memory_usage'])
        
    if 'disk_usage' in metrics:
        DISK_USAGE.labels(**labels).set(metrics['disk_usage'])
        
    if 'network_in' in metrics:
        NETWORK_IN.labels(**labels).set(metrics.get('network_in', 0))
        
    if 'network_out' in metrics:
        NETWORK_OUT.labels(**labels).set(metrics.get('network_out', 0))
