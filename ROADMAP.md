# Enterprise Agent Platform

## Sprint 1

- [x] Project setup
- [x] Settings
- [x] Planner Agent
- [x] Worker Orchestrator

## Sprint 2

- [x] Base Agent
- [x] Research Agent
- [x] Coding Agent
- [x] Agent Registry
- [x] Worker Orchestration for multiple agents sequential flow
- [x] Worker Orchestration for Dependency-aware concurrent DAG execution
  - [x] Plan / DAG Validation
  - [x] Concurrent DAG Executor
- [x] Task Failure Handling
  - [x] Task execution state
  - [x] Failure + blocked dependency handling
  - [x] Retry policies
  - [x] WorkflowResult / execution summary

## Sprint 3

- [x] Tool Calling
- [x] Building a Knowledge Retrieval System - Lexical Search
  - [x] Knowledge Domain Modeling
  - [x] Loading Documents
  - [x] Basic Keyword Search
  - [x] Ranking Search Results
  - [x] Multi-Term Queries
  - [x] Search Result Models
  - [x] Snippet Generation
  - [x] Why Keyword Search Eventually Fails - Lexical Search Limitations
  - [x] Search Evaluation & Benchmarks



## Sprint 4

- [x] Embeddings & Semantic Search
  - [x] What Are Embeddings? (Intuition)
  - [x] Vector Mathematics for AI Engineers
    - [x] Cosine Similarity
    - [x] Euclidean Distance
    - [x] Dot Product
  - [x] Embedding Repository
  - [x] Cosine Similarity
  - [x] Implement `EmbeddingService`  - OpenAI Embedding Service
  - [x] Connect Embeddings to `EmbeddingRepository`
  - [x] Integrate Semantic Search into `DocumentationService` 
  - [x] End-to-End Semantic Search Integration
  - [x] Build the Semantic Indexing Pipeline
  - [x] Semantic Index Lifecycle & Persistence
  - [x] Detect stale embeddings
  - [x] Index synchronization
  - [x] Wire the persisted index into startup/search



## Sprint 5

- [x] Vector Databases
  - [x] VectorStore protocol
  - [x] InMemoryVectorStore
  - [x] Qdrant
  - [x] Connect `EmbeddingRepository` → `VectorStore`



## Sprint 6

- [ ] Complete RAG
- [ ] Agent Memory



## Sprint 7

- [ ] Evaluation
- [ ] MCP  



## Sprint 8

- [ ] Multi-Agent Workflows



## Sprint 9

- [ ] Observability



## Sprint 10

- [ ] FastAPI



## Sprint 11

- [ ] Deployment



## Sprint 12 - Research prompt improvement

- [ ] Improve multi-search research strategy
- [ ] Validate evidence relevance
- [ ] Source quality/ranking
- [ ] Research retry strategy
- [ ] Research evaluation dataset
- [ ] Citation verification