from typing import Any

from enterprise_agent_platform.agents.base import BaseAgent
from enterprise_agent_platform.models.worker_type import WorkerType


class AgentRegistry:
    """Registry containing the worker agents available to the platform."""

    def __init__(self) -> None:
        self._agents: dict[WorkerType, BaseAgent[Any]] = {}

    def register(
        self,
        worker_type: WorkerType,
        agent: BaseAgent[Any],
    ) -> None:
        """Register an agent for a worker type."""

        if worker_type in self._agents:
            raise ValueError(f"Agent already registered for worker type: {worker_type.value}")

        self._agents[worker_type] = agent

    def get(self, worker_type: WorkerType) -> BaseAgent[Any]:
        """Return the agent registered for the given worker type."""

        if worker_type not in self._agents:
            raise KeyError(f"No agent registered for worker type: {worker_type.value}")

        return self._agents[worker_type]

    def contains(self, worker_type: WorkerType) -> bool:
        """Return whether an agent is registered for the worker type."""

        return worker_type in self._agents
