import asyncio

from dotenv import load_dotenv

from enterprise_agent_platform.agents.coder import CoderAgent

load_dotenv()


async def main():
    coder = CoderAgent()

    result = await coder.run(
        """
        Create a Python module for managing interview questions.

        Requirements:

        - Create an InterviewQuestion dataclass with:
        - id
        - question
        - difficulty
        - topic

        - Create an InterviewQuestionRepository class.
        - The repository should support:
        - adding a question
        - getting a question by ID
        - listing questions by topic
        - Store questions in memory.
        - Raise appropriate errors when a question doesn't exist.
        - Include unit tests using unittest.
        """
    )

    print(result)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
