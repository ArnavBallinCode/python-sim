from datetime import datetime, timedelta, timezone

UTC = timezone.utc


class SimulatedClock:
    def __init__(self, start: datetime | None = None):
        if start is None:
            start = datetime(2026, 1, 1, tzinfo=UTC)
        if start.tzinfo is None or start.utcoffset() is None:
            raise ValueError("start must be timezone-aware")
        self._now = start.astimezone(UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, *, seconds=0, minutes=0, hours=0, days=0) -> datetime:
        self._now += timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        return self._now

    def snapshot(self) -> str:
        return self._now.isoformat()

    def restore(self, value: str) -> None:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("snapshot clock must be timezone-aware")
        self._now = parsed.astimezone(UTC)
