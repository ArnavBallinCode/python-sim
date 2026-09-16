from typing import Any, Protocol

from ..errors import ValidationError


class ServiceProtocol(Protocol):
    name: str

    def bind(self, world, events, ids, faults) -> None: ...
    def snapshot_state(self) -> dict[str, Any]: ...
    def restore_state(self, data: dict[str, Any]) -> None: ...


class Service:
    name = "service"

    def bind(self, world, events, ids, faults) -> None:
        self.world, self.events, self.ids, self.faults = world, events, ids, faults

    def fail_next(self, failure: str | int) -> None:
        self.faults.fail_next(self.name, failure)

    def _before(self, operation: str) -> None:
        failure = self.faults.consume(self.name)
        if failure is not None:
            self.events.emit("service.call.failed", {"service": self.name, "operation": operation, "failure": failure})
            self.faults.raise_for(failure)

    def snapshot_state(self) -> dict[str, Any]:
        return {}

    def restore_state(self, data: dict[str, Any]) -> None:
        if data:
            raise ValueError(f"{self.name} does not support custom snapshot state")

    @staticmethod
    def _require_text(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{field} must be a non-empty string")
        return value
