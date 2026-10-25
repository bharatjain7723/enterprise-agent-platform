# Enterprise Agent Platform

**A modular, tool-using AI agent platform for orchestrating workflows,
retrieving grounded knowledge, and evolving toward reliable enterprise
AI applications.**

> **Status:** Active development\
> **Current focus:** Agent orchestration, RAG, memory, reflection,
> evaluation, and production readiness.

## Why this project exists

Enterprise AI is more than connecting an LLM to a prompt. Useful systems
must coordinate work, retrieve relevant evidence, invoke tools through
clear interfaces, preserve task state, handle failures, and make
behavior testable.

The Enterprise Agent Platform is a hands-on engineering project
exploring those foundations. It follows a **workflow-first
architecture**: an orchestration layer owns execution and dependencies,
while agents focus on well-defined tasks and use explicit tools.

The initial application direction is an **AI Interview Copilot** for
software engineers. The project is being built as reusable platform
infrastructure rather than a one-off chatbot, with the aim of supporting
other knowledge-intensive workflows as it matures.

## What is implemented

-   **Agent abstractions and planning:** typed agent interfaces and
    structured task plans.
-   **Workflow orchestration:** DAG-based task execution, including
    concurrent execution where dependencies permit it.
-   **Runtime state and failure handling:** task-state tracking,
    blocked-task handling, and retry behavior.
-   **Tool foundation:** agents receive explicit capabilities rather
    than reaching directly into infrastructure.
-   **Semantic retrieval:** embedding-based indexing and persistence.
-   **Qdrant integration:** vector-store-backed retrieval foundation.
-   **Knowledge-base search / RAG:** documentation search exposed to the
    researcher through a tool interface.
-   **Structured models:** Pydantic models for tasks, plans, research
    results, and initial reflection data.
-   **Configuration and LLM abstraction:** centralized settings and a
    client boundary that separates model integration from agent logic.
-   **Memory foundation:** initial structured memory capability with
    memory integration tests.

This is an evolving implementation. Features that are still on the
roadmap are identified separately below.

## Architecture

``` mermaid
flowchart TD
    U[User / Application] --> O[Workflow Orchestrator]
    O --> P[Planner Agent]
    O --> R[Researcher Agent]
    O --> C[Coder Agent]
    P --> L[LLM Client Abstraction]
    R --> L
    C --> L
    R --> T[Knowledge-Base Search Tool]
    T --> Q[Embedding / Semantic Index]
    Q --> V[(Qdrant)]
    P --> M[Structured Task Plan]
    M --> O
    O --> S[Task State, Dependencies, Retries]
```

### Design principles

**The orchestrator owns coordination.** Agents do not directly call one
another. The workflow engine coordinates dependencies, execution, state,
and failure handling, keeping control flow explicit and inspectable.

**Agents use tools instead of coupling themselves to infrastructure.**
The researcher receives a knowledge-search tool rather than direct
access to Qdrant or repository internals. This separates reasoning from
retrieval implementation and creates clearer boundaries for testing and
future permissions.

**Typed contracts make behavior easier to reason about.** Pydantic
models define structured data for tasks, plans, research results, and
reflection-related data, reducing reliance on loosely structured text
between components.

**RAG is one capability, not the whole application.** Retrieval supports
agent workflows alongside orchestration, tools, and state; it is not
treated as a synonym for an AI system.

**Reliability before complexity.** The roadmap prioritizes explicit
execution semantics, failure paths, and tests before expanding into more
sophisticated agent collaboration.

## Technology

  Area                    Technology / approach
  ----------------------- ---------------------------------------------
  Language                Python
  Data contracts          Pydantic
  Vector database         Qdrant
  Retrieval               Embeddings and semantic search
  Agent architecture      Typed agent abstractions and explicit tools
  Workflow execution      DAG orchestration and runtime task state
  Dependency management   `uv`
  Quality checks          `pytest` and `pyright`

The project is modular by design. Treat specific model providers,
deployment infrastructure, and external integrations as supported only
when they are implemented and documented in the repository.

## Repository structure

The core package lives under `src/enterprise_agent_platform/`. Key
modules include:

``` text
src/enterprise_agent_platform/
├── agents/
│   ├── base.py
│   └── planner.py
├── core/
│   └── settings.py
├── llm/
│   └── client.py
├── orchestration/
│   └── worker.py
└── ...
```

This is a representative view of the core modules, not an exhaustive
listing. Consult the repository for the current structure of models,
tools, and retrieval components.

## Getting started

### Prerequisites

-   A Python version compatible with `pyproject.toml`
-   [`uv`](https://docs.astral.sh/uv/)
-   LLM provider credentials if required by the example or workflow
-   Qdrant configured according to the current project settings for
    vector-retrieval workflows

### Install dependencies

``` bash
uv sync
```

### Run quality checks

``` bash
uv run pytest
uv run pyright
```

Check the repository's configuration and examples for the current entry
point and required environment variables. Credentials and service
configuration depend on the workflow being exercised.

## Engineering questions explored

The project focuses on practical questions that arise when moving from
an agent demo toward a dependable application:

-   How should a plan be represented as a typed, executable task graph?
-   How can independent tasks run concurrently without violating
    dependency order?
-   What should happen when a task fails, is retried, or is blocked by
    an upstream failure?
-   How can agents access knowledge without coupling themselves to a
    particular vector database?
-   How should retrieval, orchestration, and model behavior be tested
    independently?
-   What boundaries are needed for memory, reflection, evaluation,
    guardrails, and external tool protocols?

These are engineering questions being addressed incrementally---not a
claim that every production capability is already complete.

## Roadmap

-   [x] Core package, settings, and LLM-client abstraction
-   [x] Typed agent foundation and planner
-   [x] Workflow orchestration and task dependency execution
-   [x] Runtime task state, failure / blocked handling, and retries
-   [x] Tool foundation
-   [x] Embeddings, semantic indexing, and Qdrant-backed retrieval
-   [x] Knowledge-base search exposed through a researcher tool
-   [x] Initial memory capability and memory integration tests
-   [x] Reflection data models
-   [x] Complete and validate the reflection execution loop
-   [x] Evaluation harness for task quality, retrieval quality, and
    regression testing
-   [x] Guardrails and explicit safety / permission boundaries
-   [ ] MCP integration
-   [ ] More advanced multi-agent collaboration
-   [ ] Production readiness: observability, deployment, reliability,
    security, and cost / latency measurement
-   [ ] End-to-end AI Interview Copilot workflow with measurable
    acceptance criteria

**Keep this checklist synchronized with the code before publishing.**
The current project notes confirm memory integration tests passed and
reflection models were implemented with tests and `pyright` passing;
they do not establish that all future roadmap capabilities are complete.

## Quality and scope

Automated tests and static type checking are part of the development
workflow. The memory milestone's integration tests and the
reflection-model milestone's tests and `pyright` check were reported
passing during development. This does not mean every workflow, provider,
or production deployment path has been validated.

The scope is deliberately focused: build explainable foundations for
orchestration, tools, retrieval, and reliability instead of accumulating
frameworks or features without a clear purpose.

## Who this project is for

The project is relevant to work in:

-   Forward Deployed Engineer (FDE) and Forward Deployed Software
    Engineer roles
-   Applied AI and AI Solutions Engineering
-   Agentic application engineering
-   Enterprise RAG and knowledge assistants
-   Production-oriented LLM application architecture

The goal is not to claim that a prototype is already a production
platform. It is to make the engineering decisions, working foundations,
trade-offs, tests, and remaining work easy for a reviewer to understand.

## Current status

This project is under active development. Implemented capabilities are
listed separately from planned work. Before using this repository as a
portfolio artifact, run the documented checks and keep this README
aligned with the code.

------------------------------------------------------------------------

*Built as a focused engineering project to learn, test, and explain the
foundations of reliable enterprise AI systems.*
