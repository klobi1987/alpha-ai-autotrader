"""
Alpha AI Autotrader - Monitoring & Metrics System
Collects application metrics, health status, and performance data
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
import time
import psutil
import os
from loguru import logger


@dataclass
class MetricsSnapshot:
    """Point-in-time metrics snapshot"""
    timestamp: datetime
    request_count: int
    error_count: int
    avg_response_time: float
    active_connections: int
    cpu_percent: float
    memory_percent: float
    disk_percent: float


class MetricsCollector:
    """
    Collects and aggregates application metrics
    Thread-safe metrics collection for monitoring and alerting
    """

    def __init__(self, retention_minutes: int = 60):
        """
        Initialize metrics collector

        Args:
            retention_minutes: How long to keep metrics history (default: 60 min)
        """
        self.retention_minutes = retention_minutes
        self.start_time = datetime.now()

        # Request metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.requests_by_endpoint: Dict[str, int] = defaultdict(int)
        self.requests_by_status: Dict[int, int] = defaultdict(int)

        # Response time tracking (moving window)
        self.response_times: deque = deque(maxlen=1000)  # Last 1000 requests
        self.slow_requests: List[Dict[str, Any]] = []  # Track slow requests

        # Error tracking
        self.errors_by_type: Dict[str, int] = defaultdict(int)
        self.recent_errors: deque = deque(maxlen=100)  # Last 100 errors

        # WebSocket metrics
        self.active_websockets = 0
        self.total_websocket_connections = 0
        self.websocket_messages_sent = 0
        self.websocket_messages_received = 0

        # Trading metrics
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.total_pnl_usd = 0.0

        # AI/ML metrics
        self.ai_requests = 0
        self.ai_tokens_used = 0
        self.ai_cost_usd = 0.0
        self.consensus_calls = 0

        # System metrics history
        self.metrics_history: deque = deque(maxlen=retention_minutes)
        self.last_snapshot_time = datetime.now()

    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        error: Optional[str] = None
    ):
        """Record an HTTP request"""
        self.total_requests += 1
        self.requests_by_endpoint[f"{method} {endpoint}"] += 1
        self.requests_by_status[status_code] += 1
        self.response_times.append(response_time_ms)

        if status_code >= 200 and status_code < 400:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        # Track slow requests (>1s)
        if response_time_ms > 1000:
            self.slow_requests.append({
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "timestamp": datetime.now().isoformat()
            })
            # Keep only last 50 slow requests
            if len(self.slow_requests) > 50:
                self.slow_requests.pop(0)

        # Record error if present
        if error:
            self.errors_by_type[error] += 1
            self.recent_errors.append({
                "error": error,
                "endpoint": endpoint,
                "status_code": status_code,
                "timestamp": datetime.now().isoformat()
            })

    def record_websocket_connection(self, connected: bool = True):
        """Record WebSocket connection/disconnection"""
        if connected:
            self.active_websockets += 1
            self.total_websocket_connections += 1
        else:
            self.active_websockets = max(0, self.active_websockets - 1)

    def record_websocket_message(self, sent: bool = True):
        """Record WebSocket message"""
        if sent:
            self.websocket_messages_sent += 1
        else:
            self.websocket_messages_received += 1

    def record_trade(self, success: bool, pnl_usd: float = 0.0):
        """Record a trade execution"""
        self.total_trades += 1
        if success:
            self.successful_trades += 1
            self.total_pnl_usd += pnl_usd
        else:
            self.failed_trades += 1

    def record_ai_request(
        self,
        tokens: int = 0,
        cost_usd: float = 0.0,
        is_consensus: bool = False
    ):
        """Record an AI API request"""
        self.ai_requests += 1
        self.ai_tokens_used += tokens
        self.ai_cost_usd += cost_usd
        if is_consensus:
            self.consensus_calls += 1

    def take_snapshot(self) -> MetricsSnapshot:
        """Take a snapshot of current metrics"""
        # Calculate average response time
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0
        )

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        snapshot = MetricsSnapshot(
            timestamp=datetime.now(),
            request_count=self.total_requests,
            error_count=self.failed_requests,
            avg_response_time=avg_response_time,
            active_connections=self.active_websockets,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent
        )

        # Add to history
        self.metrics_history.append(snapshot)
        self.last_snapshot_time = datetime.now()

        return snapshot

    def get_uptime_seconds(self) -> float:
        """Get application uptime in seconds"""
        return (datetime.now() - self.start_time).total_seconds()

    def get_request_rate(self) -> float:
        """Get requests per second"""
        uptime = self.get_uptime_seconds()
        return self.total_requests / uptime if uptime > 0 else 0

    def get_error_rate(self) -> float:
        """Get error rate (0-1)"""
        return (
            self.failed_requests / self.total_requests
            if self.total_requests > 0 else 0
        )

    def get_success_rate(self) -> float:
        """Get success rate (0-1)"""
        return 1.0 - self.get_error_rate()

    def get_avg_response_time(self) -> float:
        """Get average response time in milliseconds"""
        return (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0
        )

    def get_p95_response_time(self) -> float:
        """Get 95th percentile response time"""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[index] if index < len(sorted_times) else 0

    def get_p99_response_time(self) -> float:
        """Get 99th percentile response time"""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.99)
        return sorted_times[index] if index < len(sorted_times) else 0

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        uptime_seconds = self.get_uptime_seconds()

        return {
            "timestamp": datetime.now().isoformat(),
            "uptime": {
                "seconds": uptime_seconds,
                "formatted": self._format_uptime(uptime_seconds)
            },
            "requests": {
                "total": self.total_requests,
                "successful": self.successful_requests,
                "failed": self.failed_requests,
                "success_rate": round(self.get_success_rate() * 100, 2),
                "requests_per_second": round(self.get_request_rate(), 2),
                "by_endpoint": dict(sorted(
                    self.requests_by_endpoint.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]),  # Top 10 endpoints
                "by_status": dict(self.requests_by_status)
            },
            "response_times": {
                "avg_ms": round(self.get_avg_response_time(), 2),
                "p95_ms": round(self.get_p95_response_time(), 2),
                "p99_ms": round(self.get_p99_response_time(), 2),
                "slow_requests_count": len(self.slow_requests)
            },
            "websockets": {
                "active": self.active_websockets,
                "total_connections": self.total_websocket_connections,
                "messages_sent": self.websocket_messages_sent,
                "messages_received": self.websocket_messages_received
            },
            "trading": {
                "total_trades": self.total_trades,
                "successful_trades": self.successful_trades,
                "failed_trades": self.failed_trades,
                "success_rate": round(
                    self.successful_trades / self.total_trades * 100, 2
                ) if self.total_trades > 0 else 0,
                "total_pnl_usd": round(self.total_pnl_usd, 2)
            },
            "ai": {
                "requests": self.ai_requests,
                "tokens_used": self.ai_tokens_used,
                "cost_usd": round(self.ai_cost_usd, 4),
                "consensus_calls": self.consensus_calls
            },
            "errors": {
                "total": self.failed_requests,
                "by_type": dict(sorted(
                    self.errors_by_type.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]),  # Top 10 error types
                "recent_count": len(self.recent_errors)
            },
            "system": self._get_system_metrics()
        }

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "memory_used_mb": round(memory.used / 1024 / 1024, 2),
            "memory_total_mb": round(memory.total / 1024 / 1024, 2),
            "disk_percent": round(disk.percent, 2),
            "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
            "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 2)
        }

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status with checks

        Returns:
            Dict with status and checks
        """
        checks = []
        overall_healthy = True

        # Check CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_healthy = cpu_percent < 80
        checks.append({
            "name": "cpu",
            "healthy": cpu_healthy,
            "value": f"{cpu_percent}%",
            "threshold": "< 80%"
        })
        if not cpu_healthy:
            overall_healthy = False

        # Check memory
        memory = psutil.virtual_memory()
        memory_healthy = memory.percent < 85
        checks.append({
            "name": "memory",
            "healthy": memory_healthy,
            "value": f"{memory.percent}%",
            "threshold": "< 85%"
        })
        if not memory_healthy:
            overall_healthy = False

        # Check disk
        disk = psutil.disk_usage('/')
        disk_healthy = disk.percent < 90
        checks.append({
            "name": "disk",
            "healthy": disk_healthy,
            "value": f"{disk.percent}%",
            "threshold": "< 90%"
        })
        if not disk_healthy:
            overall_healthy = False

        # Check error rate
        error_rate = self.get_error_rate()
        error_rate_healthy = error_rate < 0.05  # < 5%
        checks.append({
            "name": "error_rate",
            "healthy": error_rate_healthy,
            "value": f"{error_rate * 100:.2f}%",
            "threshold": "< 5%"
        })
        if not error_rate_healthy:
            overall_healthy = False

        # Check response time
        avg_response_time = self.get_avg_response_time()
        response_time_healthy = avg_response_time < 1000  # < 1s
        checks.append({
            "name": "response_time",
            "healthy": response_time_healthy,
            "value": f"{avg_response_time:.2f}ms",
            "threshold": "< 1000ms"
        })
        if not response_time_healthy:
            overall_healthy = False

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": self.get_uptime_seconds(),
            "checks": checks
        }

    def get_slow_requests(self) -> List[Dict[str, Any]]:
        """Get list of slow requests"""
        return self.slow_requests

    def get_recent_errors(self) -> List[Dict[str, Any]]:
        """Get list of recent errors"""
        return list(self.recent_errors)

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")

        return " ".join(parts)

    def reset_metrics(self):
        """Reset all metrics (use with caution)"""
        logger.warning("Resetting all metrics")
        self.__init__(retention_minutes=self.retention_minutes)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
