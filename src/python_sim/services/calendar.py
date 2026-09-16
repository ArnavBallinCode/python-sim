from dataclasses import asdict

from ..models import CalendarEvent
from .base import Service


class Calendar(Service):
    name = "calendar"

    def __init__(self):
        self.events_by_id: dict[str, CalendarEvent] = {}

    def create_event(self, *, title: str, start, end, attendees=None, calendar: str = "primary") -> CalendarEvent:
        self._before("create_event")
        iso = lambda value: value.isoformat() if hasattr(value, "isoformat") else str(value)
        event = CalendarEvent(self.ids.new("event"), title, iso(start), iso(end), tuple(attendees or ()), calendar)
        self.events_by_id[event.id] = event
        self.events.emit("calendar.event.created", {"event_id": event.id})
        return event

    def list_events(self, *, calendar: str | None = None) -> list[CalendarEvent]:
        return [event for event in self.events_by_id.values() if calendar is None or event.calendar == calendar]

    def snapshot_state(self):
        return {"events": {key: asdict(value) for key, value in self.events_by_id.items()}}

    def restore_state(self, data):
        self.events_by_id = {key: CalendarEvent(**value) for key, value in data.get("events", {}).items()}
