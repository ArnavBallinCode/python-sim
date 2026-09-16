"""Typed public models returned by the simulator."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Customer:
    id: str
    email: str
    name: str | None = None


@dataclass(frozen=True, slots=True)
class Order:
    id: str
    number: str
    customer_id: str
    amount: int
    currency: str
    status: str
    payment_ids: tuple[str, ...]
    created_at: str


@dataclass(frozen=True, slots=True)
class Payment:
    id: str
    customer_id: str
    order_id: str | None
    amount: int
    currency: str
    status: str
    refunded_amount: int
    created_at: str


@dataclass(frozen=True, slots=True)
class Refund:
    id: str
    payment_id: str
    amount: int
    currency: str
    status: str
    created_at: str


@dataclass(frozen=True, slots=True)
class Email:
    id: str
    thread_id: str
    sender: str
    recipients: tuple[str, ...]
    subject: str
    body: str
    labels: tuple[str, ...]
    read: bool
    created_at: str


@dataclass(frozen=True, slots=True)
class SlackMessage:
    id: str
    channel: str
    user: str
    text: str
    created_at: str


@dataclass(frozen=True, slots=True)
class SlackChannel:
    id: str
    name: str
    message_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CalendarEvent:
    id: str
    title: str
    start: str
    end: str
    attendees: tuple[str, ...]
    calendar: str


@dataclass(frozen=True, slots=True)
class Repository:
    id: str
    owner: str
    name: str
    description: str
    issue_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Issue:
    id: str
    number: int
    owner: str
    repo: str
    title: str
    body: str
    state: str
    created_at: str
