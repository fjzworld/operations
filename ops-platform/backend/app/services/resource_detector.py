"""
Resource auto-detection service via SSH
Detects CPU, Memory, Disk, OS info from remote servers
"""
import paramiko
import re
from typing import Dict, Optional
from pydantic import BaseModel


class SSHCredentials(BaseModel):
    """SSH connection credentials"""
    host: str
    port: int = 22
    username: str
    password: Optional[str] = None
    private_key: Optional[str] = None


class ServerInfo(BaseModel):
    """Detected server information"""
    hostname: str
    cpu_cores: int
    memory_gb: float
    disk_gb: float
    os_type: str
    os_version: str
    kernel_version: str


class ResourceDetector:
    """Auto-detect server resources via SSH"""
    
    def __init__(self, credentials: SSHCredentials):
        self.credentials = credentials
        self.client: Optional[paramiko.SSHClient] = None
    
    def connect(self) -> None:
        """Establish SSH connection"""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if self.credentials.private_key:
                # Use private key authentication
                key = paramiko.RSAKey.from_private_key_file(self.credentials.private_key)
                self.client.connect(
                    hostname=self.credentials.host,
                    port=self.credentials.port,
                    username=self.credentials.username,
                    pkey=key,
                    timeout=10
                )
            else:
                # Use password authentication
                self.client.connect(
                    hostname=self.credentials.host,
                    port=self.credentials.port,
                    username=self.credentials.username,
                    password=self.credentials.password,
                    timeout=10
                )
        except Exception as e:
            raise ConnectionError(f"SSH connection failed: {str(e)}")
    
    def execute_command(self, command: str) -> str:
        """Execute command on remote server"""
        if not self.client:
            raise RuntimeError("SSH client not connected")
        
        stdin, stdout, stderr = self.client.exec_command(command)
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        
        if error and "command not found" in error.lower():
            raise RuntimeError(f"Command failed: {error}")
        
        return output
    
    def detect_hostname(self) -> str:
        """Get server hostname"""
        return self.execute_command("hostname")
    
    def detect_cpu_cores(self) -> int:
        """Detect CPU core count"""
        try:
            # Linux: nproc or /proc/cpuinfo
            output = self.execute_command("nproc")
            return int(output)
        except:
            try:
                output = self.execute_command("grep -c ^processor /proc/cpuinfo")
                return int(output)
            except:
                # Fallback: assume 1 core
                return 1
    
    def detect_memory_gb(self) -> float:
        """Detect total memory in GB"""
        try:
            # Linux: Read from /proc/meminfo
            output = self.execute_command("grep MemTotal /proc/meminfo | awk '{print $2}'")
            mem_kb = int(output)
            return round(mem_kb / (1024 * 1024), 2)  # Convert KB to GB
        except:
            try:
                # Alternative: use free command
                output = self.execute_command("free -g | grep Mem | awk '{print $2}'")
                return float(output)
            except:
                return 0.0
    
    def detect_disk_gb(self) -> float:
        """Detect total disk space in GB"""
        try:
            # Get root partition size
            output = self.execute_command("df -BG / | tail -1 | awk '{print $2}' | sed 's/G//'")
            return float(output)
        except:
            return 0.0
    
    def detect_os_info(self) -> Dict[str, str]:
        """Detect OS type and version"""
        try:
            # Try /etc/os-release (most modern Linux distros)
            output = self.execute_command("cat /etc/os-release")
            
            os_type = "Linux"
            os_version = "Unknown"
            
            # Parse os-release
            for line in output.split('\n'):
                if line.startswith('NAME='):
                    os_type = line.split('=')[1].strip('"')
                elif line.startswith('VERSION='):
                    os_version = line.split('=')[1].strip('"')
            
            # Get kernel version
            kernel_version = self.execute_command("uname -r")
            
            return {
                "os_type": os_type,
                "os_version": os_version,
                "kernel_version": kernel_version
            }
        except:
            # Fallback: use uname
            try:
                uname_output = self.execute_command("uname -a")
                return {
                    "os_type": "Linux" if "Linux" in uname_output else "Unix",
                    "os_version": "Unknown",
                    "kernel_version": uname_output.split()[2] if len(uname_output.split()) > 2 else "Unknown"
                }
            except:
                return {
                    "os_type": "Unknown",
                    "os_version": "Unknown",
                    "kernel_version": "Unknown"
                }
    
    def probe(self) -> ServerInfo:
        """
        Full server detection process
        Returns complete server information
        """
        try:
            self.connect()
            
            hostname = self.detect_hostname()
            cpu_cores = self.detect_cpu_cores()
            memory_gb = self.detect_memory_gb()
            disk_gb = self.detect_disk_gb()
            os_info = self.detect_os_info()
            
            return ServerInfo(
                hostname=hostname,
                cpu_cores=cpu_cores,
                memory_gb=memory_gb,
                disk_gb=disk_gb,
                os_type=os_info["os_type"],
                os_version=os_info["os_version"],
                kernel_version=os_info["kernel_version"]
            )
        finally:
            self.close()
    
    def close(self) -> None:
        """Close SSH connection"""
        if self.client:
            self.client.close()


def probe_server(credentials: SSHCredentials) -> ServerInfo:
    """
    Convenience function to probe a server
    
    Args:
        credentials: SSH connection credentials
    
    Returns:
        ServerInfo: Detected server information
    
    Raises:
        ConnectionError: If SSH connection fails
        RuntimeError: If detection commands fail
    """
    detector = ResourceDetector(credentials)
    return detector.probe()
