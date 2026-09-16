from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Event:
    event_id: str
    type: str
    timestamp: str
    payload: dict[str, Any]
    correlation_id: str | None = None
    causation_id: str | None = None
    actor: str = "system"

    @property
    def name(self) -> str:
        return self.type


class EventBus:
    def __init__(self, clock, ids):
        self.clock = clock
        self.ids = ids
        self._handlers: dict[str, list[Callable[[Event], None]]] = {}
        self._history: list[Event] = []
        self._context: list[dict[str, str | None]] = []

    def on(self, event_type: str, handler: Callable[[Event], None]) -> Callable[[], None]:
        self._handlers.setdefault(event_type, []).append(handler)

        def unsubscribe() -> None:
            if handler in self._handlers.get(event_type, []):
                self._handlers[event_type].remove(handler)

        return unsubscribe

    @contextmanager
    def context(self, *, correlation_id: str | None = None, actor: str = "agent") -> Iterator[str]:
        correlation_id = correlation_id or self.ids.new("cor")
        self._context.append({"correlation_id": correlation_id, "actor": actor})
        try:
            yield correlation_id
        finally:
            self._context.pop()

    def emit(self, event_type: str, payload: dict[str, Any] | None = None, *,
             correlation_id: str | None = None, causation_id: str | None = None,
             actor: str | None = None) -> Event:
        context = self._context[-1] if self._context else {}
        correlation_id = correlation_id if correlation_id is not None else context.get("correlation_id")
        if causation_id is None and correlation_id:
            prior = next((e for e in reversed(self._history) if e.correlation_id == correlation_id), None)
            causation_id = prior.event_id if prior else None
        event = Event(self.ids.new("evt"), event_type, self.clock.now().isoformat(), payload or {},
                      correlation_id, causation_id, actor or context.get("actor") or "system")
        self._history.append(event)
        for handler in tuple(self._handlers.get(event_type, [])) + tuple(self._handlers.get("*", [])):
            handler(event)
        return event

    def history(self, event_type: str | None = None) -> list[Event]:
        return [event for event in self._history if event_type is None or event.type == event_type]

    def snapshot(self) -> list[dict[str, Any]]:
        return [asdict(event) for event in self._history]

    def restore(self, data: list[dict[str, Any]]) -> None:
        try:
            self._history = [Event(**item) for item in data]
        except (TypeError, KeyError) as exc:
            raise ValueError("invalid event history snapshot") from exc
