from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Scenario:
    name: str
    setup: Callable | None = None

    def apply(self, sim):
        if self.setup: self.setup(sim)
        return sim
