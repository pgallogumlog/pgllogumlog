# AI Team Personas

This folder contains system prompts for the AI agent team that develops and manages the SaaS product.

## Team Structure

```
┌─────────────────────────────────────────────────────────┐
│                    STAKEHOLDER (You)                     │
│                   Vision & Decisions                     │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                        COO                               │
│     Coordination, Prioritization, Progress Tracking      │
└───┬─────────┬─────────────┬─────────────┬───────────────┘
    │         │             │             │
┌───▼───┐ ┌───▼───┐   ┌─────▼─────┐ ┌─────▼─────┐
│  PM   │ │ Arch  │   │ Designer  │ │Orchestrator│
│       │ │       │   │           │ │            │
│ What  │ │ How   │   │ Experience│ │ Execution  │
│ & Why │ │(Tech) │   │ & Interface│ │ & Delivery │
└───────┘ └───────┘   └───────────┘ └────────────┘
```

## Personas

| File | Role | Primary Focus |
|------|------|---------------|
| [coo.md](coo.md) | Chief Operating Officer | Team coordination, prioritization, progress tracking |
| [product-manager.md](product-manager.md) | Product Manager | Requirements, user stories, backlog, success metrics |
| [architect.md](architect.md) | Architect | Technical design, system patterns, feasibility |
| [designer.md](designer.md) | Designer | UI/UX, user flows, visual design, accessibility |
| [orchestrator.md](orchestrator.md) | Orchestrator | Task execution, implementation coordination |

## How to Use

### Starting a Session

1. **For strategic planning or status reviews**, start with COO:
   ```
   Read personas/coo.md and adopt that role. Here's our current state: [paste sprint board]
   ```

2. **For specific domain work**, go directly to the specialist:
   ```
   Read personas/architect.md and adopt that role. I need to design [feature].
   ```

### Switching Personas

When you need to switch agents mid-conversation:
```
Switch to the [Role] persona from personas/[file].md.
Context from previous agent: [brief summary]
```

### Persona Handoffs

When COO delegates to another agent, use this pattern:
```
The COO has delegated this task:
- Objective: [what's needed]
- Context: [why it matters]
- Constraints: [boundaries]
- Expected output: [deliverable format]

Adopt the [Role] persona from personas/[file].md and complete this task.
```

## Maintaining State

Personas work best with persistent context. Maintain these artifacts:

### Sprint Board (for COO)
```markdown
## Current Sprint: [Goal]
### In Progress
- [ ] Item - Owner - Status
### Blocked
- [ ] Item - Blocker
### Done
- [x] Item - Outcome
### Backlog
1. Next item
2. Following item
```

### Decision Log
```markdown
| Date | Decision | Rationale | Made By |
|------|----------|-----------|---------|
| YYYY-MM-DD | [Decision] | [Why] | [Persona] |
```

### Technical Decisions (for Architect)
```markdown
## ADR-001: [Title]
- Status: [Proposed/Accepted/Deprecated]
- Context: [Why this decision is needed]
- Decision: [What was decided]
- Consequences: [Trade-offs]
```

## Tips for Effective Multi-Agent Sessions

1. **Let COO delegate** - Don't bypass the COO for cross-cutting work
2. **Provide context on handoffs** - Each agent should know what happened before
3. **Keep specialists focused** - Don't ask the Architect about UX or the Designer about database schemas
4. **Document decisions** - Capture rationale so future sessions have context
5. **Trust the structure** - The overhead pays off for complex multi-step initiatives

## Customizing Personas

Each persona file has sections you can customize:
- **Identity**: Core role definition
- **Responsibilities**: What they own
- **Decision Authority**: What they can decide vs. escalate
- **Communication Style**: How they report and interact
- **Anti-Patterns**: What to avoid

Modify these to match your product domain and working style.
