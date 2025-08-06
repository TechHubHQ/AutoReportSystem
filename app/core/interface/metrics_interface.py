import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from app.config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SystemMetric:
    """System metric data structure"""
    metric_type: str
    value: float
    unit: str
    timestamp: datetime


class SystemMetricsCollector:
    """Collect and manage system metrics"""

    @staticmethod
    def get_cpu_usage() -> SystemMetric:
        """Get current CPU usage percentage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        return SystemMetric(
            metric_type="cpu",
            value=cpu_percent,
            unit="%",
            timestamp=datetime.now()
        )

    @staticmethod
    def get_memory_usage() -> SystemMetric:
        """Get current memory usage percentage"""
        memory = psutil.virtual_memory()
        return SystemMetric(
            metric_type="memory",
            value=memory.percent,
            unit="%",
            timestamp=datetime.now()
        )

    @staticmethod
    def get_disk_usage() -> SystemMetric:
        """Get current disk usage percentage"""
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        return SystemMetric(
            metric_type="disk",
            value=disk_percent,
            unit="%",
            timestamp=datetime.now()
        )

    @staticmethod
    def get_network_io() -> Dict[str, SystemMetric]:
        """Get network I/O statistics"""
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': SystemMetric(
                metric_type="network_sent",
                value=net_io.bytes_sent / (1024 * 1024),  # Convert to MB
                unit="MB",
                timestamp=datetime.now()
            ),
            'bytes_recv': SystemMetric(
                metric_type="network_recv",
                value=net_io.bytes_recv / (1024 * 1024),  # Convert to MB
                unit="MB",
                timestamp=datetime.now()
            )
        }

    @classmethod
    def get_all_metrics(cls) -> Dict[str, SystemMetric]:
        """Get all system metrics at once"""
        metrics = {}

        try:
            metrics['cpu'] = cls.get_cpu_usage()
            metrics['memory'] = cls.get_memory_usage()
            metrics['disk'] = cls.get_disk_usage()

            network_metrics = cls.get_network_io()
            metrics.update(network_metrics)

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

        return metrics


async def get_current_system_status() -> Dict:
    """Get current system status for dashboard"""
    try:
        collector = SystemMetricsCollector()
        metrics = collector.get_all_metrics()

        # Determine system health status
        cpu_usage = metrics.get('cpu', SystemMetric(
            'cpu', 0, '%', datetime.now())).value
        memory_usage = metrics.get('memory', SystemMetric(
            'memory', 0, '%', datetime.now())).value
        disk_usage = metrics.get('disk', SystemMetric(
            'disk', 0, '%', datetime.now())).value

        # Calculate overall health score
        health_score = 100
        if cpu_usage > 80:
            health_score -= 30
        elif cpu_usage > 60:
            health_score -= 15

        if memory_usage > 85:
            health_score -= 25
        elif memory_usage > 70:
            health_score -= 10

        if disk_usage > 90:
            health_score -= 20
        elif disk_usage > 80:
            health_score -= 10

        # Determine status
        if health_score >= 80:
            status = "healthy"
            status_color = "#4CAF50"
        elif health_score >= 60:
            status = "warning"
            status_color = "#FF9800"
        else:
            status = "critical"
            status_color = "#F44336"

        return {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'health_score': max(0, health_score),
            'status': status,
            'status_color': status_color,
            'timestamp': datetime.now().isoformat(),
            'alerts': generate_system_alerts(cpu_usage, memory_usage, disk_usage)
        }

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'health_score': 0,
            'status': 'unknown',
            'status_color': '#666666',
            'timestamp': datetime.now().isoformat(),
            'alerts': ['Unable to retrieve system metrics']
        }


def generate_system_alerts(cpu: float, memory: float, disk: float) -> List[str]:
    """Generate system alerts based on metrics"""
    alerts = []

    if cpu > 90:
        alerts.append("🔴 Critical: CPU usage is very high")
    elif cpu > 80:
        alerts.append("🟡 Warning: CPU usage is high")

    if memory > 90:
        alerts.append("🔴 Critical: Memory usage is very high")
    elif memory > 80:
        alerts.append("🟡 Warning: Memory usage is high")

    if disk > 95:
        alerts.append("🔴 Critical: Disk space is almost full")
    elif disk > 85:
        alerts.append("🟡 Warning: Disk space is running low")

    if not alerts:
        alerts.append("✅ All systems operating normally")

    return alerts


async def get_historical_metrics(hours: int = 24) -> Dict:
    """Get historical system metrics (simulated for now)"""
    try:
        # Generate sample historical data
        # In a real implementation, this would fetch from a database
        current_time = datetime.now()
        historical_data = []

        for i in range(hours):
            timestamp = current_time - timedelta(hours=i)

            # Simulate some variation in metrics
            import random
            base_cpu = 45 + random.randint(-20, 30)
            base_memory = 60 + random.randint(-25, 25)
            base_disk = 70 + random.randint(-10, 10)

            historical_data.append({
                'timestamp': timestamp.isoformat(),
                'cpu_usage': max(0, min(100, base_cpu)),
                'memory_usage': max(0, min(100, base_memory)),
                'disk_usage': max(0, min(100, base_disk))
            })

        # Reverse to get chronological order
        historical_data.reverse()

        return {
            'data': historical_data,
            'period_hours': hours,
            'data_points': len(historical_data)
        }

    except Exception as e:
        logger.error(f"Error getting historical metrics: {e}")
        return {
            'data': [],
            'period_hours': hours,
            'data_points': 0
        }


async def get_system_info() -> Dict:
    """Get basic system information"""
    try:
        # Get system information
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = psutil.boot_time()

        return {
            'cpu_cores': cpu_count,
            'cpu_frequency': f"{cpu_freq.current:.0f} MHz" if cpu_freq else "Unknown",
            'total_memory': f"{memory.total / (1024**3):.1f} GB",
            'total_disk': f"{disk.total / (1024**3):.1f} GB",
            'system_uptime': str(timedelta(seconds=datetime.now().timestamp() - boot_time)),
            'python_version': f"{psutil.version_info}",
            'platform': psutil.WINDOWS if hasattr(psutil, 'WINDOWS') else 'Unix-like'
        }

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {
            'cpu_cores': 'Unknown',
            'cpu_frequency': 'Unknown',
            'total_memory': 'Unknown',
            'total_disk': 'Unknown',
            'system_uptime': 'Unknown',
            'python_version': 'Unknown',
            'platform': 'Unknown'
        }
