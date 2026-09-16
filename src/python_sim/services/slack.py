from dataclasses import asdict

from ..errors import NotFoundError
from ..models import SlackChannel, SlackMessage
from .base import Service


class Slack(Service):
    name = "slack"

    def __init__(self):
        self.channels: dict[str, SlackChannel] = {}
        self.messages_by_id: dict[str, SlackMessage] = {}

    def create_channel(self, name: str) -> SlackChannel:
        self._before("create_channel")
        channel = SlackChannel(self.ids.new("channel"), name, ())
        self.channels[channel.id] = channel
        self.events.emit("slack.channel.created", {"channel_id": channel.id})
        return channel

    def _channel(self, name: str) -> SlackChannel:
        channel = next((item for item in self.channels.values() if item.name == name), None)
        if channel is None:
            raise NotFoundError(f"channel {name} does not exist")
        return channel

    def send_message(self, *, channel: str, text: str, user: str = "agent") -> SlackMessage:
        target = self._channel(channel)
        message = SlackMessage(self.ids.new("slackmsg"), channel, user, text, self.events.clock.now().isoformat())
        self.messages_by_id[message.id] = message
        self.channels[target.id] = SlackChannel(target.id, target.name, (*target.message_ids, message.id))
        self.events.emit("slack.message.sent", {"message_id": message.id, "channel": channel})
        return message

    def messages(self, channel: str) -> list[SlackMessage]:
        target = self._channel(channel)
        return [self.messages_by_id[item_id] for item_id in target.message_ids]

    def snapshot_state(self):
        return {"channels": {key: asdict(value) for key, value in self.channels.items()}, "messages": {key: asdict(value) for key, value in self.messages_by_id.items()}}

    def restore_state(self, data):
        self.channels = {key: SlackChannel(**value) for key, value in data.get("channels", {}).items()}
        self.messages_by_id = {key: SlackMessage(**value) for key, value in data.get("messages", {}).items()}
