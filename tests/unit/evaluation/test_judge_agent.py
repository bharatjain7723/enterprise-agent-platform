from enterprise_agent_platform.agents.judge import JudgeAgent
from enterprise_agent_platform.models.judge_assessment import JudgeAssessment
from enterprise_agent_platform.prompts.judge import JUDGE_INSTRUCTIONS


def test_judge_agent_configuration() -> None:
    judge = JudgeAgent()

    assert judge.name == "Evaluation Judge"
    assert judge.description == ("Evaluates AI-generated answers against reference facts")
    assert judge.instructions == JUDGE_INSTRUCTIONS
    assert judge.output_type is JudgeAssessment
    assert judge.agent.name == "Evaluation Judge"
