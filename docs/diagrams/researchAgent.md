EP-007A
ResearchAgent
     │
     ▼
LLM knowledge only

        ↓ learn limitation ↓



EP-007B
ResearchAgent
     │
     ▼
    Tool
     │
     ▼
Web/Search

        ↓ later ↓


EP-0XX
ResearchAgent
     │
     ├── Web Search
     ├── MCP
     ├── RAG
     └── Internal Knowledge




Updated Prompt:

                         Research Task
                              │
                              ▼
                      Do I understand it?
                       /             \
                     YES              NO
                      │                │
                      │          Report clarification
                      ▼              required
               Can I answer it?
                 /          \
               YES           PARTLY
                │              │
                │         Answer known parts
                │         Flag uncertainty
                ▼
          Do I have evidence?
             /         \
           YES          NO
            │            │
       Cite evidence    Explicitly say
                       unverified