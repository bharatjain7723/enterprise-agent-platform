from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BaseAgent(ABC):
    """Base class implemented by every platform agent."""

    name: str
    description: str

    @abstractmethod
    async def run(self, user_input: str) -> str:
        """Execute the agent."""
