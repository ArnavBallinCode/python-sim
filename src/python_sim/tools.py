from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    side_effect: bool
    _callable: Callable[..., Any]

    @property
    def schema(self) -> dict[str, Any]:
        """JSON-schema input description for this tool."""
        return self.parameters

    def call(self, **arguments: Any) -> Any:
        return self._callable(**arguments)

    def openai_schema(self) -> dict[str, Any]:
        return {"type": "function", "function": {"name": self.name, "description": self.description, "parameters": self.parameters}}
