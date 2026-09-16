from ..errors import NotFoundError
from ..models import Email
from .base import Service


class Gmail(Service):
    name = "gmail"

    def receive_email(self, *, from_: str, to: str | list[str] = "agent@example.com", subject: str = "", body: str = "", thread_id: str | None = None) -> Email:
        self._before("receive_email")
        return self._create_email(from_, to, subject, body, thread_id, ("INBOX", "UNREAD"), False, "email.received")

    def send_email(self, *, to: str | list[str], subject: str, body: str, from_: str = "agent@example.com", thread_id: str | None = None) -> Email:
        self._before("send_email")
        return self._create_email(from_, to, subject, body, thread_id, ("SENT",), True, "email.sent")

    def _create_email(self, sender, to, subject, body, thread_id, labels, read, event_type):
        recipients = (to,) if isinstance(to, str) else tuple(to)
        email = Email(self.ids.new("email"), thread_id or self.ids.new("thread"), sender, recipients, subject, body, labels, read, self.events.clock.now().isoformat())
        self.world.emails[email.id] = email
        self.events.emit(event_type, {"email_id": email.id, "thread_id": email.thread_id})
        return email

    def get_email(self, email_id: str) -> Email:
        self._before("get_email")
        try:
            return self.world.emails[email_id]
        except KeyError as exc:
            raise NotFoundError(f"email {email_id} does not exist") from exc

    def search(self, query: str = "") -> list[Email]:
        self._before("search")
        query = query.lower()
        return [email for email in self.world.emails.values() if query in f"{email.sender} {email.subject} {email.body}".lower()]

    def inbox(self) -> list[Email]:
        return [email for email in self.world.emails.values() if "INBOX" in email.labels]

    def sent_mail(self) -> list[Email]:
        return [email for email in self.world.emails.values() if "SENT" in email.labels]

    def mark_as_read(self, email_id: str) -> Email:
        self._before("mark_as_read")
        email = self.get_email(email_id)
        updated = Email(email.id, email.thread_id, email.sender, email.recipients, email.subject, email.body, email.labels, True, email.created_at)
        self.world.emails[email_id] = updated
        self.events.emit("email.read", {"email_id": email_id})
        return updated

    def delete_email(self, email_id: str) -> None:
        self._before("delete_email")
        self.get_email(email_id)
        del self.world.emails[email_id]
        self.events.emit("email.deleted", {"email_id": email_id})
