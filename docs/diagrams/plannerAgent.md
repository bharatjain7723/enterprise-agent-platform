PlannerAgent()

       │
       ▼

PlannerAgent.__init__()

       │
       │ super().__init__()
       ▼

BaseAgent.__init__()

       │
       ├── self.name = "Planner"
       ├── self.description = "..."
       └── self.instructions = "..."

       │
       ▼

BaseAgent.__post_init__()

       │
       ▼

self.agent = Agent(...)

       │
       ▼

PlannerAgent ready