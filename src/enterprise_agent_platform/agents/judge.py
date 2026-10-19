from enterprise_agent_platform.agents.base import BaseAgent
from enterprise_agent_platform.models.judge_assessment import JudgeAssessment
from enterprise_agent_platform.prompts.judge import JUDGE_INSTRUCTIONS


class JudgeAgent(BaseAgent[JudgeAssessment]):
    def __init__(self, model: str | None = None) -> None:
        super().__init__(
            name="Evaluation Judge",
            description="Evaluates AI-generated answers against reference facts",
            instructions=JUDGE_INSTRUCTIONS,
            output_type=JudgeAssessment,
            model=model,
        )
