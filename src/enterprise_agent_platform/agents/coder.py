from enterprise_agent_platform.agents.base import BaseAgent
from enterprise_agent_platform.models.coder_result import CoderResult
from enterprise_agent_platform.prompts.coder import CODER_INSTRUCTIONS


class CoderAgent(BaseAgent[CoderResult]):
    def __init__(self) -> None:
        super().__init__(
            name="Coder",
            description="Writes code on the assigned task input",
            instructions=CODER_INSTRUCTIONS,
            output_type=CoderResult,
        )
