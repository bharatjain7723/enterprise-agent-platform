import asyncio
from pprint import pprint

from dotenv import load_dotenv

from enterprise_agent_platform.evaluation.llm_judge import (
    LLMJudgeEvaluator,
)
from enterprise_agent_platform.models.evaluation import EvaluationCase

load_dotenv()


async def main() -> None:
    evaluator = LLMJudgeEvaluator.from_agents_sdk()

    case = EvaluationCase(
        id="cache-demo",
        input="What does functools.lru_cache do?",
        expected_facts=[
            "It caches function results.",
            "It can reuse cached results for repeated calls.",
        ],
    )

    candidate_answer = (
        "functools.lru_cache caches the results of a function so "
        "subsequent calls with the same arguments can reuse them "
        "instead of recomputing the result."
    )

    result = await evaluator.evaluate(case, candidate_answer)

    pprint(result.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
