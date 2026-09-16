class SimulationError(Exception):
    """Base class for expected simulator failures."""


class NotFoundError(SimulationError):
    pass


class ValidationError(SimulationError):
    pass


class PermissionDeniedError(SimulationError):
    pass


class ConflictError(SimulationError):
    pass


class ServiceUnavailableError(SimulationError):
    pass


class RateLimitError(SimulationError):
    pass


class SimulationTimeoutError(SimulationError):
    pass


class HttpError(SimulationError):
    def __init__(self, status_code: int, message: str | None = None):
        self.status_code = status_code
        super().__init__(message or f"simulated HTTP {status_code}")


class SnapshotError(SimulationError):
    pass
