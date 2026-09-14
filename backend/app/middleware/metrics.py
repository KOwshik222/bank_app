"""
Prometheus Metrics Middleware — records HTTP request counts, response latency, and error counts.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# In-memory metrics counters
_request_counts: dict[str, int] = {}
_request_durations: dict[str, list[float]] = {}
_status_counts: dict[int, int] = {}


class MetricsMiddleware(BaseHTTPMiddleware):
    """Tracks HTTP request counts and response latency."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        endpoint = request.url.path

        response: Response = await call_next(request)

        duration = time.time() - start_time
        status_code = response.status_code

        _request_counts[endpoint] = _request_counts.get(endpoint, 0) + 1
        _status_counts[status_code] = _status_counts.get(status_code, 0) + 1

        if endpoint not in _request_durations:
            _request_durations[endpoint] = []
        if len(_request_durations[endpoint]) < 1000:
            _request_durations[endpoint].append(duration)

        return response


def get_prometheus_metrics() -> str:
    """Generate Prometheus exposition text format."""
    lines = [
        "# HELP http_requests_total Total number of HTTP requests processed.",
        "# TYPE http_requests_total counter",
    ]
    for endpoint, count in _request_counts.items():
        lines.append(f'http_requests_total{{path="{endpoint}"}} {count}')

    lines.append("# HELP http_requests_status_total HTTP requests categorized by HTTP status code.")
    lines.append("# TYPE http_requests_status_total counter")
    for status_code, count in _status_counts.items():
        lines.append(f'http_requests_status_total{{status="{status_code}"}} {count}')

    return "\n".join(lines) + "\n"
