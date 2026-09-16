import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .clock import SimulatedClock
from .errors import SnapshotError
from .events import EventBus
from .faults import FaultInjector
from .ids import IdGenerator
from .services.base import ServiceProtocol
from .services.calendar import Calendar
from .services.database import Database
from .services.github import GitHub
from .services.gmail import Gmail
from .services.slack import Slack
from .services.stripe import Stripe
from .tools import Tool
from .world import WorldState


class Simulation:
    SNAPSHOT_VERSION = 2

    def __init__(self, *, seed: int = 0, start=None):
        self.clock = SimulatedClock(start)
        self.ids = IdGenerator(seed)
        self.event_ids = IdGenerator(seed)
        self.events = EventBus(self.clock, self.event_ids)
        self.faults = FaultInjector()
        self.world = WorldState.empty()
        self.services: dict[str, ServiceProtocol] = {}
        self.gmail: Gmail
        self.database: Database
        self.stripe: Stripe
        self.github: GitHub
        self.slack: Slack
        self.calendar: Calendar
        for service in (Gmail(), Database(), Stripe(), GitHub(), Slack(), Calendar()):
            self.register_service(service.name, service)

    def register_service(self, name, service):
        if not name or name in self.services:
            raise ValueError(f"service name is empty or already registered: {name!r}")
        if not hasattr(service, "bind") or not hasattr(service, "snapshot_state"):
            raise TypeError("service must implement bind() and snapshot_state()")
        service.bind(self.world, self.events, self.ids, self.faults)
        self.services[name] = service
        setattr(self, name, service)
        return service

    def run(self, scenario):
        return scenario.apply(self)

    def tools(self) -> list[Tool]:
        return [
            Tool("gmail.search", "Search received and sent email.", {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}, False, self.gmail.search),
            Tool("gmail.get_email", "Read one email by ID.", {"type": "object", "properties": {"email_id": {"type": "string"}}, "required": ["email_id"]}, False, self.gmail.get_email),
            Tool("gmail.mark_as_read", "Mark an email as read.", {"type": "object", "properties": {"email_id": {"type": "string"}}, "required": ["email_id"]}, True, self.gmail.mark_as_read),
            Tool("gmail.send_email", "Send an email to a recipient.", {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "subject", "body"]}, True, self.gmail.send_email),
            Tool("database.get_order", "Look up an order by ID or order number.", {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}, False, self.database.get_order),
            Tool("database.find_payments", "Find payments belonging to an order.", {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}, False, self.database.find_payments),
            Tool("stripe.list_payments", "List payments for an order or customer.", {"type": "object", "properties": {"order_id": {"type": "string"}, "customer_id": {"type": "string"}}}, False, self.stripe.list_payments),
            Tool("stripe.refund_payment", "Refund a payment.", {"type": "object", "properties": {"payment_id": {"type": "string"}, "amount": {"type": "integer"}}, "required": ["payment_id"]}, True, self.stripe.refund_payment),
        ]

    def snapshot(self) -> dict[str, Any]:
        return {"version": self.SNAPSHOT_VERSION, "world": deepcopy(self.world.snapshot()), "services": {name: deepcopy(service.snapshot_state()) for name, service in self.services.items()}, "clock": self.clock.snapshot(), "ids": {"seed": self.ids.seed, "count": self.ids.count}, "event_ids": {"seed": self.event_ids.seed, "count": self.event_ids.count}, "events": deepcopy(self.events.snapshot()), "faults": deepcopy(self.faults.snapshot())}

    def restore(self, snapshot: dict[str, Any]) -> None:
        try:
            if snapshot.get("version") != self.SNAPSHOT_VERSION:
                raise SnapshotError(f"unsupported snapshot version: {snapshot.get('version')!r}")
            new_world = WorldState.restore(deepcopy(snapshot["world"]))
            new_clock = SimulatedClock()
            new_clock.restore(snapshot["clock"])
            for key in ("seed", "count"):
                if not isinstance(snapshot["ids"][key], int) or not isinstance(snapshot["event_ids"][key], int):
                    raise TypeError("invalid ID generator state")
            if set(snapshot["services"]) != set(self.services):
                raise ValueError("snapshot services do not match registered services")
            events = deepcopy(snapshot["events"])
            if not isinstance(events, list):
                raise TypeError("snapshot events must be a list")
            if not isinstance(snapshot.get("faults", {}), dict):
                raise TypeError("snapshot faults must be an object")
        except SnapshotError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise SnapshotError(f"invalid snapshot: {exc}") from exc

        old = self.snapshot()
        try:
            self.world = new_world
            self.clock.restore(new_clock.snapshot())
            self.ids.seed, self.ids.count = snapshot["ids"]["seed"], snapshot["ids"]["count"]
            self.event_ids.seed, self.event_ids.count = snapshot["event_ids"]["seed"], snapshot["event_ids"]["count"]
            self.events.clock = self.clock
            self.events.restore(events)
            self.faults.restore(deepcopy(snapshot.get("faults", {})))
            for name, service in self.services.items():
                service.bind(self.world, self.events, self.ids, self.faults)
                service.restore_state(deepcopy(snapshot["services"][name]))
        except Exception as exc:
            self._restore_unchecked(old)
            raise SnapshotError(f"could not restore snapshot: {exc}") from exc

    def _restore_unchecked(self, snapshot):
        self.world = WorldState.restore(deepcopy(snapshot["world"]))
        self.clock.restore(snapshot["clock"])
        self.ids.seed, self.ids.count = snapshot["ids"]["seed"], snapshot["ids"]["count"]
        self.event_ids.seed, self.event_ids.count = snapshot["event_ids"]["seed"], snapshot["event_ids"]["count"]
        self.events.clock = self.clock
        self.events.restore(deepcopy(snapshot["events"]))
        self.faults.restore(deepcopy(snapshot.get("faults", {})))
        for name, service in self.services.items():
            service.bind(self.world, self.events, self.ids, self.faults)
            service.restore_state(deepcopy(snapshot["services"][name]))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.snapshot(), indent=2) + "\n", encoding="utf-8")

    def load(self, path: str | Path) -> None:
        try:
            snapshot = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SnapshotError(f"could not read snapshot: {exc}") from exc
        self.restore(snapshot)
