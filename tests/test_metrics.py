"""
Alpha AI Autotrader - Metrics Tests
Tests for monitoring and metrics collection
"""
import pytest
from backend.core.metrics import MetricsCollector, get_metrics_collector


@pytest.fixture
def metrics():
    """Create a fresh metrics collector for each test"""
    return MetricsCollector()


class TestRequestMetrics:
    """Test HTTP request metrics tracking"""

    def test_record_successful_request(self, metrics):
        """Test recording a successful request"""
        metrics.record_request(
            endpoint="/api/signals",
            method="GET",
            status_code=200,
            response_time_ms=125.5
        )

        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.requests_by_endpoint["GET /api/signals"] == 1
        assert metrics.requests_by_status[200] == 1

    def test_record_failed_request(self, metrics):
        """Test recording a failed request"""
        metrics.record_request(
            endpoint="/api/positions/BTCUSDT",
            method="GET",
            status_code=404,
            response_time_ms=50.0,
            error="PositionNotFoundError"
        )

        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1
        assert metrics.errors_by_type["PositionNotFoundError"] == 1

    def test_record_multiple_requests(self, metrics):
        """Test recording multiple requests"""
        for i in range(10):
            metrics.record_request(
                endpoint=f"/api/test/{i}",
                method="GET",
                status_code=200 if i % 2 == 0 else 500,
                response_time_ms=100.0
            )

        assert metrics.total_requests == 10
        assert metrics.successful_requests == 5
        assert metrics.failed_requests == 5

    def test_slow_request_tracking(self, metrics):
        """Test tracking slow requests (>1s)"""
        metrics.record_request(
            endpoint="/api/slow",
            method="POST",
            status_code=200,
            response_time_ms=2500.0  # 2.5 seconds
        )

        assert len(metrics.slow_requests) == 1
        assert metrics.slow_requests[0]["response_time_ms"] == 2500.0

    def test_response_time_calculation(self, metrics):
        """Test average response time calculation"""
        response_times = [100, 200, 150, 300, 250]
        for i, rt in enumerate(response_times):
            metrics.record_request(
                endpoint=f"/api/test/{i}",
                method="GET",
                status_code=200,
                response_time_ms=rt
            )

        avg_time = metrics.get_avg_response_time()
        expected_avg = sum(response_times) / len(response_times)

        assert abs(avg_time - expected_avg) < 0.01  # Allow small floating point error


class TestRateMetrics:
    """Test rate calculations"""

    def test_success_rate(self, metrics):
        """Test success rate calculation"""
        # Record 8 successful and 2 failed requests
        for i in range(10):
            metrics.record_request(
                endpoint="/api/test",
                method="GET",
                status_code=200 if i < 8 else 500,
                response_time_ms=100.0
            )

        success_rate = metrics.get_success_rate()
        error_rate = metrics.get_error_rate()

        assert success_rate == 0.8  # 80%
        assert error_rate == 0.2  # 20%

    def test_success_rate_all_successful(self, metrics):
        """Test success rate with all successful requests"""
        for i in range(10):
            metrics.record_request(
                endpoint="/api/test",
                method="GET",
                status_code=200,
                response_time_ms=100.0
            )

        assert metrics.get_success_rate() == 1.0
        assert metrics.get_error_rate() == 0.0

    def test_success_rate_no_requests(self, metrics):
        """Test success rate with no requests"""
        assert metrics.get_success_rate() == 0.0
        assert metrics.get_error_rate() == 0.0


class TestWebSocketMetrics:
    """Test WebSocket connection metrics"""

    def test_record_websocket_connection(self, metrics):
        """Test recording WebSocket connection"""
        metrics.record_websocket_connection(connected=True)

        assert metrics.active_websockets == 1
        assert metrics.total_websocket_connections == 1

    def test_record_websocket_disconnection(self, metrics):
        """Test recording WebSocket disconnection"""
        metrics.record_websocket_connection(connected=True)
        metrics.record_websocket_connection(connected=False)

        assert metrics.active_websockets == 0
        assert metrics.total_websocket_connections == 1

    def test_multiple_websocket_connections(self, metrics):
        """Test multiple WebSocket connections"""
        for _ in range(5):
            metrics.record_websocket_connection(connected=True)

        assert metrics.active_websockets == 5
        assert metrics.total_websocket_connections == 5

    def test_websocket_messages(self, metrics):
        """Test WebSocket message tracking"""
        metrics.record_websocket_message(sent=True)
        metrics.record_websocket_message(sent=True)
        metrics.record_websocket_message(sent=False)

        assert metrics.websocket_messages_sent == 2
        assert metrics.websocket_messages_received == 1


class TestTradingMetrics:
    """Test trading performance metrics"""

    def test_record_successful_trade(self, metrics):
        """Test recording successful trade"""
        metrics.record_trade(success=True, pnl_usd=125.50)

        assert metrics.total_trades == 1
        assert metrics.successful_trades == 1
        assert metrics.failed_trades == 0
        assert metrics.total_pnl_usd == 125.50

    def test_record_failed_trade(self, metrics):
        """Test recording failed trade"""
        metrics.record_trade(success=False, pnl_usd=0.0)

        assert metrics.total_trades == 1
        assert metrics.successful_trades == 0
        assert metrics.failed_trades == 1
        assert metrics.total_pnl_usd == 0.0

    def test_cumulative_pnl(self, metrics):
        """Test cumulative PnL calculation"""
        trades = [
            (True, 100.0),
            (True, 50.0),
            (True, -25.0),
            (False, 0.0)
        ]

        for success, pnl in trades:
            metrics.record_trade(success=success, pnl_usd=pnl)

        assert metrics.total_pnl_usd == 125.0  # 100 + 50 - 25 + 0


class TestAIMetrics:
    """Test AI usage metrics"""

    def test_record_ai_request(self, metrics):
        """Test recording AI request"""
        metrics.record_ai_request(
            tokens=1500,
            cost_usd=0.02,
            is_consensus=False
        )

        assert metrics.ai_requests == 1
        assert metrics.ai_tokens_used == 1500
        assert metrics.ai_cost_usd == 0.02
        assert metrics.consensus_calls == 0

    def test_record_consensus_call(self, metrics):
        """Test recording consensus call"""
        metrics.record_ai_request(
            tokens=3000,
            cost_usd=0.05,
            is_consensus=True
        )

        assert metrics.ai_requests == 1
        assert metrics.consensus_calls == 1

    def test_cumulative_ai_cost(self, metrics):
        """Test cumulative AI cost calculation"""
        calls = [
            (1000, 0.01, False),
            (1500, 0.02, True),
            (2000, 0.03, False),
        ]

        for tokens, cost, is_consensus in calls:
            metrics.record_ai_request(
                tokens=tokens,
                cost_usd=cost,
                is_consensus=is_consensus
            )

        assert metrics.ai_requests == 3
        assert metrics.ai_tokens_used == 4500
        assert abs(metrics.ai_cost_usd - 0.06) < 0.001  # Floating point precision
        assert metrics.consensus_calls == 1


class TestHealthStatus:
    """Test health check functionality"""

    def test_health_status_all_healthy(self, metrics):
        """Test health status when all checks pass"""
        # Simulate healthy metrics
        for _ in range(100):
            metrics.record_request(
                endpoint="/api/test",
                method="GET",
                status_code=200,
                response_time_ms=100.0
            )

        health = metrics.get_health_status()

        assert health["status"] == "healthy"
        assert "checks" in health
        assert len(health["checks"]) > 0

    def test_health_status_with_errors(self, metrics):
        """Test health status with high error rate"""
        # Simulate high error rate (>5%)
        for i in range(100):
            metrics.record_request(
                endpoint="/api/test",
                method="GET",
                status_code=500 if i < 10 else 200,  # 10% error rate
                response_time_ms=100.0
            )

        health = metrics.get_health_status()

        # Should be degraded due to high error rate
        assert health["status"] == "degraded"


class TestMetricsSummary:
    """Test comprehensive metrics summary"""

    def test_get_metrics_summary(self, metrics):
        """Test getting comprehensive metrics summary"""
        # Record some activity
        metrics.record_request("/api/test", "GET", 200, 100.0)
        metrics.record_trade(success=True, pnl_usd=50.0)
        metrics.record_ai_request(tokens=1000, cost_usd=0.01)

        summary = metrics.get_metrics_summary()

        assert "timestamp" in summary
        assert "uptime" in summary
        assert "requests" in summary
        assert "response_times" in summary
        assert "websockets" in summary
        assert "trading" in summary
        assert "ai" in summary
        assert "errors" in summary
        assert "system" in summary

    def test_uptime_formatting(self, metrics):
        """Test uptime formatting"""
        uptime_seconds = 3665  # 1h 1m 5s
        formatted = metrics._format_uptime(uptime_seconds)

        assert "1h" in formatted
        assert "1m" in formatted
        assert "5s" in formatted


class TestPercentileCalculations:
    """Test response time percentile calculations"""

    def test_p95_calculation(self, metrics):
        """Test P95 response time calculation"""
        # Record 100 requests with increasing response times
        for i in range(100):
            metrics.record_request(
                endpoint="/api/test",
                method="GET",
                status_code=200,
                response_time_ms=float(i + 1)  # 1ms to 100ms
            )

        p95 = metrics.get_p95_response_time()

        # P95 should be around 95ms (95th percentile)
        assert 94 <= p95 <= 96

    def test_p99_calculation(self, metrics):
        """Test P99 response time calculation"""
        # Record 100 requests with increasing response times
        for i in range(100):
            metrics.record_request(
                endpoint="/api/test",
                method="GET",
                status_code=200,
                response_time_ms=float(i + 1)
            )

        p99 = metrics.get_p99_response_time()

        # P99 should be around 99ms (99th percentile)
        assert 98 <= p99 <= 100


class TestMetricsReset:
    """Test metrics reset functionality"""

    def test_reset_metrics(self, metrics):
        """Test resetting all metrics"""
        # Record some activity
        metrics.record_request("/api/test", "GET", 200, 100.0)
        metrics.record_trade(success=True, pnl_usd=50.0)
        metrics.record_ai_request(tokens=1000, cost_usd=0.01)

        # Reset metrics
        metrics.reset_metrics()

        # All metrics should be reset to 0/empty
        assert metrics.total_requests == 0
        assert metrics.total_trades == 0
        assert metrics.ai_requests == 0
        assert len(metrics.response_times) == 0


class TestGlobalMetricsCollector:
    """Test global metrics collector singleton"""

    def test_get_metrics_collector_singleton(self):
        """Test that get_metrics_collector returns same instance"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2  # Same instance
