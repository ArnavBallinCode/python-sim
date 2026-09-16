"""The authoritative, serializable world state."""

from dataclasses import asdict, dataclass, replace
from typing import Any

from .models import (
    CalendarEvent,
    Customer,
    Email,
    Order,
    Payment,
    Refund,
    SlackChannel,
    SlackMessage,
)


@dataclass
class WorldState:
    customers: dict[str, Customer]
    orders: dict[str, Order]
    payments: dict[str, Payment]
    refunds: dict[str, Refund]
    emails: dict[str, Email]
    slack_channels: dict[str, SlackChannel]
    slack_messages: dict[str, SlackMessage]
    calendar_events: dict[str, CalendarEvent]

    @classmethod
    def empty(cls) -> "WorldState":
        return cls({}, {}, {}, {}, {}, {}, {}, {})

    def snapshot(self) -> dict[str, Any]:
        return {field: {key: asdict(value) for key, value in getattr(self, field).items()} for field in self.__dataclass_fields__}

    @classmethod
    def restore(cls, data: dict[str, Any]) -> "WorldState":
        required = set(cls.__dataclass_fields__)
        if set(data) != required:
            raise ValueError("invalid world snapshot: expected all world collections")
        models = {
            "customers": Customer, "orders": Order, "payments": Payment, "refunds": Refund,
            "emails": Email, "slack_channels": SlackChannel, "slack_messages": SlackMessage,
            "calendar_events": CalendarEvent,
        }
        values = {}
        for field, model in models.items():
            if not isinstance(data[field], dict):
                raise TypeError(f"invalid world snapshot: {field} must be an object")
            try:
                restored = {}
                for key, raw_value in data[field].items():
                    value = dict(raw_value)
                    for tuple_field in (
                        "payment_ids", "recipients", "labels", "message_ids", "attendees",
                    ):
                        if tuple_field in value:
                            value[tuple_field] = tuple(value[tuple_field])
                    restored[key] = model(**value)
                values[field] = restored
            except (TypeError, KeyError) as exc:
                raise ValueError(f"invalid world snapshot: malformed {field}") from exc
        return cls(**values)

    def add_payment_to_order(self, order_id: str, payment_id: str) -> None:
        order = self.orders[order_id]
        self.orders[order_id] = replace(order, payment_ids=(*order.payment_ids, payment_id))
