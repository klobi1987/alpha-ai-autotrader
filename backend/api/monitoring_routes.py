"""
Alpha AI Autotrader - Monitoring Routes
Health checks, metrics, and status endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from ..core.metrics import get_metrics_collector
from ..core.config import get_settings
from .auth import get_current_superuser
from ..models.database import User

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])
settings = get_settings()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint

    Returns simple OK status - useful for load balancers and uptime monitoring
    No authentication required
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Alpha AI Autotrader",
        "version": settings.app_version
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with system checks

    Checks:
    - CPU usage
    - Memory usage
    - Disk usage
    - Error rate
    - Response time

    No authentication required (but could be added if needed)
    """
    metrics = get_metrics_collector()
    health_status = metrics.get_health_status()

    return health_status


@router.get("/metrics")
async def get_metrics(current_user: User = Depends(get_current_superuser)):
    """
    Get comprehensive application metrics

    Requires superuser authentication

    Returns:
    - Request statistics
    - Response time metrics
    - WebSocket statistics
    - Trading performance
    - AI usage and costs
    - Error tracking
    - System resource usage
    """
    metrics = get_metrics_collector()
    summary = metrics.get_metrics_summary()

    return summary


@router.get("/metrics/requests")
async def get_request_metrics(current_user: User = Depends(get_current_superuser)):
    """
    Get detailed request metrics

    Requires superuser authentication
    """
    metrics = get_metrics_collector()

    return {
        "timestamp": datetime.now().isoformat(),
        "total_requests": metrics.total_requests,
        "successful_requests": metrics.successful_requests,
        "failed_requests": metrics.failed_requests,
        "success_rate": round(metrics.get_success_rate() * 100, 2),
        "requests_per_second": round(metrics.get_request_rate(), 2),
        "by_endpoint": dict(sorted(
            metrics.requests_by_endpoint.items(),
            key=lambda x: x[1],
            reverse=True
        )),
        "by_status": dict(metrics.requests_by_status),
        "response_times": {
            "avg_ms": round(metrics.get_avg_response_time(), 2),
            "p95_ms": round(metrics.get_p95_response_time(), 2),
            "p99_ms": round(metrics.get_p99_response_time(), 2)
        }
    }


@router.get("/metrics/slow-requests")
async def get_slow_requests(current_user: User = Depends(get_current_superuser)):
    """
    Get list of slow requests (>1 second)

    Requires superuser authentication
    """
    metrics = get_metrics_collector()
    slow_requests = metrics.get_slow_requests()

    return {
        "timestamp": datetime.now().isoformat(),
        "count": len(slow_requests),
        "slow_requests": slow_requests
    }


@router.get("/metrics/errors")
async def get_error_metrics(current_user: User = Depends(get_current_superuser)):
    """
    Get detailed error metrics

    Requires superuser authentication
    """
    metrics = get_metrics_collector()
    recent_errors = metrics.get_recent_errors()

    return {
        "timestamp": datetime.now().isoformat(),
        "total_errors": metrics.failed_requests,
        "error_rate": round(metrics.get_error_rate() * 100, 2),
        "by_type": dict(sorted(
            metrics.errors_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        )),
        "recent_errors": recent_errors
    }


@router.get("/metrics/trading")
async def get_trading_metrics(current_user: User = Depends(get_current_superuser)):
    """
    Get trading performance metrics

    Requires superuser authentication
    """
    metrics = get_metrics_collector()

    return {
        "timestamp": datetime.now().isoformat(),
        "total_trades": metrics.total_trades,
        "successful_trades": metrics.successful_trades,
        "failed_trades": metrics.failed_trades,
        "success_rate": round(
            metrics.successful_trades / metrics.total_trades * 100, 2
        ) if metrics.total_trades > 0 else 0,
        "total_pnl_usd": round(metrics.total_pnl_usd, 2)
    }


@router.get("/metrics/ai")
async def get_ai_metrics(current_user: User = Depends(get_current_superuser)):
    """
    Get AI usage and cost metrics

    Requires superuser authentication
    """
    metrics = get_metrics_collector()

    return {
        "timestamp": datetime.now().isoformat(),
        "ai_requests": metrics.ai_requests,
        "tokens_used": metrics.ai_tokens_used,
        "cost_usd": round(metrics.ai_cost_usd, 4),
        "consensus_calls": metrics.consensus_calls,
        "avg_cost_per_request": round(
            metrics.ai_cost_usd / metrics.ai_requests, 4
        ) if metrics.ai_requests > 0 else 0
    }


@router.get("/metrics/websockets")
async def get_websocket_metrics(current_user: User = Depends(get_current_superuser)):
    """
    Get WebSocket connection metrics

    Requires superuser authentication
    """
    metrics = get_metrics_collector()

    return {
        "timestamp": datetime.now().isoformat(),
        "active_connections": metrics.active_websockets,
        "total_connections": metrics.total_websocket_connections,
        "messages_sent": metrics.websocket_messages_sent,
        "messages_received": metrics.websocket_messages_received
    }


@router.get("/metrics/system")
async def get_system_metrics(current_user: User = Depends(get_current_superuser)):
    """
    Get system resource metrics

    Requires superuser authentication
    """
    metrics = get_metrics_collector()
    system_metrics = metrics._get_system_metrics()

    return {
        "timestamp": datetime.now().isoformat(),
        **system_metrics
    }


@router.get("/status")
async def get_status():
    """
    Get overall system status

    Public endpoint showing basic system health
    """
    metrics = get_metrics_collector()
    uptime_seconds = metrics.get_uptime_seconds()

    return {
        "status": "online",
        "version": settings.app_version,
        "uptime_seconds": uptime_seconds,
        "uptime_formatted": metrics._format_uptime(uptime_seconds),
        "timestamp": datetime.now().isoformat(),
        "environment": "development" if settings.debug else "production",
        "trading_enabled": settings.enable_auto_trading
    }


@router.post("/metrics/reset")
async def reset_metrics(current_user: User = Depends(get_current_superuser)):
    """
    Reset all metrics (use with caution!)

    Requires superuser authentication

    This will clear all collected metrics data. Use only for testing or
    after maintenance windows.
    """
    metrics = get_metrics_collector()
    metrics.reset_metrics()

    logger.warning(f"Metrics reset by user: {current_user.username}")

    return {
        "status": "success",
        "message": "All metrics have been reset",
        "timestamp": datetime.now().isoformat()
    }
