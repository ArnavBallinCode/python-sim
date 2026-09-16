from collections import defaultdict, deque

from .errors import (
    HttpError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    SimulationTimeoutError,
)


class FaultInjector:
    """Deterministic one-shot failures reusable by every service."""

    def __init__(self):
        self._queues: dict[str, deque[str | int]] = defaultdict(deque)

    def fail_next(self, service: str, failure: str | int) -> None:
        self._queues[service].append(failure)

    def consume(self, service: str) -> str | int | None:
        return self._queues[service].popleft() if self._queues[service] else None

    def snapshot(self):
        return {service: list(queue) for service, queue in self._queues.items() if queue}

    def restore(self, data):
        self._queues.clear()
        for service, failures in data.items():
            self._queues[service].extend(failures)

    @staticmethod
    def raise_for(failure: str | int) -> None:
        if isinstance(failure, int):
            raise HttpError(failure)
        failures = {
            "timeout": SimulationTimeoutError("simulated timeout"),
            "service_unavailable": ServiceUnavailableError("simulated service unavailable"),
            "permission_denied": PermissionDeniedError("simulated permission denied"),
            "rate_limited": RateLimitError("simulated rate limit"),
            "429": RateLimitError("simulated HTTP 429"),
            "500": HttpError(500),
        }
        if failure not in failures:
            raise ValueError(f"unknown simulated failure: {failure}")
        raise failures[failure]
