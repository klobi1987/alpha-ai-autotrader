# Monitoring & Health Checks

## Overview

Alpha AI Autotrader includes a comprehensive monitoring system that tracks application performance, system resources, and trading metrics in real-time.

**Features**:
- ✅ Automatic request tracking
- ✅ Response time monitoring
- ✅ Error tracking and alerting
- ✅ System resource monitoring (CPU, memory, disk)
- ✅ Trading performance metrics
- ✅ AI usage and cost tracking
- ✅ WebSocket connection monitoring
- ✅ Health checks (basic + detailed)

---

## Quick Start

### 1. Install Dependencies

```bash
pip install psutil==5.9.8
```

### 2. Start Application

Monitoring is automatically enabled when you start the application:

```bash
python3 backend/api/main.py
```

You'll see:
```
✅ Monitoring middleware enabled
```

### 3. Access Monitoring Endpoints

**Public Health Check**:
```bash
curl http://localhost:8000/api/monitoring/health
```

**Detailed Health Check** (with system checks):
```bash
curl http://localhost:8000/api/monitoring/health/detailed
```

**Comprehensive Metrics** (requires authentication):
```bash
curl http://localhost:8000/api/monitoring/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Monitoring Endpoints

### Public Endpoints (No Authentication)

#### GET `/api/monitoring/health`

Basic health check - returns simple OK status.

**Use cases**:
- Load balancer health checks
- Uptime monitoring (UptimeRobot, Pingdom)
- Simple availability checks

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T10:00:00",
  "service": "Alpha AI Autotrader",
  "version": "1.0.0"
}
```

#### GET `/api/monitoring/health/detailed`

Detailed health check with system resource checks.

**Checks**:
- CPU usage (< 80%)
- Memory usage (< 85%)
- Disk usage (< 90%)
- Error rate (< 5%)
- Response time (< 1000ms)

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T10:00:00",
  "uptime_seconds": 3600.5,
  "checks": [
    {
      "name": "cpu",
      "healthy": true,
      "value": "45.2%",
      "threshold": "< 80%"
    },
    {
      "name": "memory",
      "healthy": true,
      "value": "62.3%",
      "threshold": "< 85%"
    },
    {
      "name": "disk",
      "healthy": true,
      "value": "45.0%",
      "threshold": "< 90%"
    },
    {
      "name": "error_rate",
      "healthy": true,
      "value": "1.2%",
      "threshold": "< 5%"
    },
    {
      "name": "response_time",
      "healthy": true,
      "value": "125.5ms",
      "threshold": "< 1000ms"
    }
  ]
}
```

**Status values**:
- `healthy` - All checks passed
- `degraded` - One or more checks failed

#### GET `/api/monitoring/status`

Overall system status overview.

**Response**:
```json
{
  "status": "online",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "uptime_formatted": "1h 0m 0s",
  "timestamp": "2025-11-19T10:00:00",
  "environment": "production",
  "trading_enabled": false
}
```

---

### Protected Endpoints (Require Superuser Authentication)

All endpoints below require `Authorization: Bearer <token>` header with superuser permissions.

#### GET `/api/monitoring/metrics`

Comprehensive application metrics - everything in one endpoint.

**Response**:
```json
{
  "timestamp": "2025-11-19T10:00:00",
  "uptime": {
    "seconds": 3600.5,
    "formatted": "1h 0m 0s"
  },
  "requests": {
    "total": 1250,
    "successful": 1200,
    "failed": 50,
    "success_rate": 96.0,
    "requests_per_second": 0.35,
    "by_endpoint": {
      "GET /api/signals": 500,
      "GET /api/positions": 300,
      "POST /api/auth/login": 150
    },
    "by_status": {
      "200": 1100,
      "401": 30,
      "404": 10,
      "500": 10
    }
  },
  "response_times": {
    "avg_ms": 125.5,
    "p95_ms": 450.0,
    "p99_ms": 850.0,
    "slow_requests_count": 5
  },
  "websockets": {
    "active": 3,
    "total_connections": 25,
    "messages_sent": 1500,
    "messages_received": 800
  },
  "trading": {
    "total_trades": 45,
    "successful_trades": 38,
    "failed_trades": 7,
    "success_rate": 84.44,
    "total_pnl_usd": 1250.50
  },
  "ai": {
    "requests": 120,
    "tokens_used": 150000,
    "cost_usd": 2.45,
    "consensus_calls": 45
  },
  "errors": {
    "total": 50,
    "by_type": {
      "HTTPException": 30,
      "ValidationError": 15,
      "ConnectionError": 5
    },
    "recent_count": 50
  },
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 62.3,
    "memory_used_mb": 2048.5,
    "memory_total_mb": 16384.0,
    "disk_percent": 45.0,
    "disk_used_gb": 120.5,
    "disk_total_gb": 256.0
  }
}
```

#### GET `/api/monitoring/metrics/requests`

Detailed HTTP request metrics.

**Response**:
```json
{
  "timestamp": "2025-11-19T10:00:00",
  "total_requests": 1250,
  "successful_requests": 1200,
  "failed_requests": 50,
  "success_rate": 96.0,
  "requests_per_second": 0.35,
  "by_endpoint": {
    "GET /api/signals": 500,
    "GET /api/positions": 300
  },
  "by_status": {
    "200": 1100,
    "401": 30,
    "500": 10
  },
  "response_times": {
    "avg_ms": 125.5,
    "p95_ms": 450.0,
    "p99_ms": 850.0
  }
}
```

#### GET `/api/monitoring/metrics/slow-requests`

List of slow requests (>1 second).

**Response**:
```json
{
  "timestamp": "2025-11-19T10:00:00",
  "count": 5,
  "slow_requests": [
    {
      "endpoint": "/api/trading/scan",
      "method": "POST",
      "status_code": 200,
      "response_time_ms": 2150.5,
      "timestamp": "2025-11-19T09:55:00"
    }
  ]
}
```

#### GET `/api/monitoring/metrics/errors`

Detailed error metrics and recent errors.

**Response**:
```json
{
  "timestamp": "2025-11-19T10:00:00",
  "total_errors": 50,
  "error_rate": 4.0,
  "by_type": {
    "HTTPException": 30,
    "ValidationError": 15,
    "ConnectionError": 5
  },
  "recent_errors": [
    {
      "error": "HTTPException",
      "endpoint": "/api/positions/BTCUSDT/close",
      "status_code": 404,
      "timestamp": "2025-11-19T09:58:00"
    }
  ]
}
```

#### GET `/api/monitoring/metrics/trading`

Trading performance metrics.

**Response**:
```json
{
  "timestamp": "2025-11-19T10:00:00",
  "total_trades": 45,
  "successful_trades": 38,
  "failed_trades": 7,
  "success_rate": 84.44,
  "total_pnl_usd": 1250.50
}
```

#### GET `/api/monitoring/metrics/ai`

AI usage and cost tracking.

**Response**:
```json
{
  "timestamp": "2025-11-19T10:00:00",
  "ai_requests": 120,
  "tokens_used": 150000,
  "cost_usd": 2.45,
  "consensus_calls": 45,
  "avg_cost_per_request": 0.0204
}
```

#### GET `/api/monitoring/metrics/websockets`

WebSocket connection metrics.

**Response**:
```json
{
  "timestamp": "2025-11-19T10:00:00",
  "active_connections": 3,
  "total_connections": 25,
  "messages_sent": 1500,
  "messages_received": 800
}
```

#### GET `/api/monitoring/metrics/system`

System resource usage.

**Response**:
```json
{
  "timestamp": "2025-11-19T10:00:00",
  "cpu_percent": 45.2,
  "memory_percent": 62.3,
  "memory_used_mb": 2048.5,
  "memory_total_mb": 16384.0,
  "disk_percent": 45.0,
  "disk_used_gb": 120.5,
  "disk_total_gb": 256.0
}
```

#### POST `/api/monitoring/metrics/reset`

Reset all metrics (use with caution!).

**Response**:
```json
{
  "status": "success",
  "message": "All metrics have been reset",
  "timestamp": "2025-11-19T10:00:00"
}
```

---

## Automatic Monitoring

The monitoring system automatically tracks:

### 1. HTTP Requests

Every HTTP request is automatically tracked by `MonitoringMiddleware`:

- **Endpoint** - Which endpoint was called
- **Method** - GET, POST, PUT, DELETE, etc.
- **Status Code** - 200, 404, 500, etc.
- **Response Time** - How long it took (milliseconds)
- **Errors** - Exception type if request failed

**Example**:
```
GET /api/signals → 200 OK in 125ms
POST /api/positions/BTCUSDT/close → 404 Not Found in 50ms
```

### 2. Slow Requests

Requests taking >1 second are flagged as slow:

```
⚠️  Slow request: POST /api/trading/scan took 2150ms
```

Last 50 slow requests are kept in memory for analysis.

### 3. Errors

All errors are tracked with:
- Error type (HTTPException, ValidationError, etc.)
- Endpoint where error occurred
- Status code
- Timestamp

Last 100 errors are kept in memory.

### 4. Response Time Percentiles

Response times are tracked with:
- **Average** - Mean response time
- **P95** - 95th percentile (95% of requests faster than this)
- **P99** - 99th percentile (99% of requests faster than this)

**Example**:
```json
{
  "avg_ms": 125.5,
  "p95_ms": 450.0,  // 95% of requests < 450ms
  "p99_ms": 850.0   // 99% of requests < 850ms
}
```

---

## Manual Metrics Recording

You can manually record metrics in your code:

```python
from backend.core.metrics import get_metrics_collector

metrics = get_metrics_collector()

# Record a trade
metrics.record_trade(success=True, pnl_usd=125.50)

# Record AI request
metrics.record_ai_request(
    tokens=1500,
    cost_usd=0.02,
    is_consensus=True
)

# Record WebSocket connection
metrics.record_websocket_connection(connected=True)

# Record WebSocket message
metrics.record_websocket_message(sent=True)
```

---

## Integration with External Tools

### Prometheus

Metrics can be exposed in Prometheus format (optional enhancement):

```python
# Future enhancement - Prometheus exporter
@router.get("/metrics/prometheus")
async def prometheus_metrics():
    """Export metrics in Prometheus format"""
    # Implementation here
    pass
```

### Grafana

Create dashboards in Grafana by:
1. Setting up Prometheus to scrape metrics
2. Importing Alpha AI Autotrader dashboard
3. Configuring alerts

### Uptime Monitoring

Configure your uptime monitoring service to check:

**Endpoint**: `GET /api/monitoring/health`
**Expected Response**: HTTP 200 with `{"status": "healthy"}`
**Check Interval**: 1-5 minutes

**Services**:
- UptimeRobot
- Pingdom
- StatusCake
- Better Uptime

### Alerting

Set up alerts based on health checks:

**Alert Conditions**:
- `/api/monitoring/health/detailed` returns `"status": "degraded"`
- CPU usage > 80%
- Memory usage > 85%
- Disk usage > 90%
- Error rate > 5%
- Response time > 1000ms

**Alert Channels**:
- Email
- SMS
- Telegram (already integrated)
- Discord webhook
- PagerDuty
- Slack

---

## Monitoring Best Practices

### 1. Regular Health Checks

Set up automated health checks every 1-5 minutes:

```bash
# Cron job to check health every 5 minutes
*/5 * * * * curl -f http://localhost:8000/api/monitoring/health || echo "Service down!" | mail -s "Alert" admin@example.com
```

### 2. Dashboard

Create a simple dashboard showing:
- Current status (healthy/degraded)
- Uptime
- Request rate
- Error rate
- Response time (avg, p95, p99)
- System resources (CPU, memory, disk)
- Trading performance

### 3. Alerting Thresholds

Configure alerts for:
- **Critical**: Service down, error rate >10%, disk >95%
- **Warning**: CPU >80%, memory >85%, error rate >5%
- **Info**: Slow requests, high AI costs

### 4. Log Retention

Metrics are kept in memory with:
- Last 1000 request response times
- Last 50 slow requests
- Last 100 errors
- 60 minutes of metrics history

For long-term storage, export to:
- Prometheus
- InfluxDB
- CloudWatch
- DataDog

### 5. Performance Impact

Monitoring adds minimal overhead:
- **Middleware**: <1ms per request
- **Memory**: ~10-50MB for metrics storage
- **CPU**: <1% additional usage

---

## Troubleshooting

### High Error Rate

If error rate >5%:

1. Check recent errors:
   ```bash
   curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/api/monitoring/metrics/errors
   ```

2. Review logs:
   ```bash
   tail -f logs/alpha_autotrader.log
   ```

3. Look for patterns in error types

### Slow Response Times

If avg response time >500ms:

1. Check slow requests:
   ```bash
   curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/api/monitoring/metrics/slow-requests
   ```

2. Identify slow endpoints
3. Check system resources (CPU, memory)
4. Review database queries
5. Check external API calls (MEXC, LunarCrush)

### High System Resources

If CPU >80% or memory >85%:

1. Check system metrics:
   ```bash
   curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/api/monitoring/metrics/system
   ```

2. Review active processes
3. Check for memory leaks
4. Scale horizontally (add more instances)
5. Optimize database queries

### Service Degraded

If health check returns `"status": "degraded"`:

1. Check detailed health:
   ```bash
   curl http://localhost:8000/api/monitoring/health/detailed
   ```

2. Identify which check failed
3. Address the specific issue
4. Monitor until status returns to `"healthy"`

---

## API Documentation

Full interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Filter by tag "Monitoring" to see all monitoring endpoints.

---

## Next Steps

1. ✅ Monitoring system implemented
2. ⏳ Set up external monitoring (UptimeRobot, etc.)
3. ⏳ Configure alerting (Telegram, email)
4. ⏳ Create Grafana dashboards
5. ⏳ Export metrics to Prometheus

---

**Questions?** Check logs in `logs/alpha_autotrader.log` or API docs at `/docs`
