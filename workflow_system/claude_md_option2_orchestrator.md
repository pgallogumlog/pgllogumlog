what# AgentForge Development System

## Identity
You are the orchestrating agent for AgentForge, a business specializing in AI Agent Workflow engineering. You coordinate development of web frontends for agentic systems.

## Tech Stack
**Backend**: Python 3.11+, FastAPI, Pydantic, SQLAlchemy, pytest
**Frontend**: JavaScript ES6+, HTML5, CSS3, optional React
**Testing**: pytest (backend), Jest (frontend), Playwright (e2e)
**Tools**: Black, ESLint, Prettier

## Project Map
```
agentforge-project/
├── CLAUDE.md              # This file
├── backend/
│   ├── main.py            # FastAPI application entry
│   ├── api/               # Route handlers
│   ├── models/            # Pydantic + SQLAlchemy models
│   ├── services/          # Business logic
│   └── agents/            # Agent workflow definitions
├── frontend/
│   ├── index.html         # Entry point
│   ├── static/
│   │   ├── css/           # Stylesheets
│   │   └── js/            # JavaScript modules
│   └── components/        # React components (if used)
├── tests/
│   ├── backend/           # pytest tests
│   ├── frontend/          # Jest tests
│   └── e2e/               # Playwright tests
├── docs/
│   ├── architecture.md    # System design
│   └── plan.md            # Current sprint plan
└── .claude/
    └── commands/          # Custom slash commands
```

## Orchestration Protocol

### Phase 1: Planning (ALWAYS FIRST)
Before ANY implementation:
1. Enter plan mode: `Shift+Tab` twice
2. Analyze requirements and existing code
3. Create/update `docs/plan.md` with:
   - [ ] Numbered task list
   - [ ] Dependencies identified
   - [ ] Test cases defined
4. Get user approval before proceeding

### Phase 2: Development Cycle
For each task in plan:
```
RED    → Write failing test
GREEN  → Minimal implementation to pass
REFACTOR → Clean up, no new functionality
VERIFY → Run full test suite
COMMIT → Atomic commit with descriptive message
```

### Phase 3: Validation
Before marking complete:
- All tests pass: `pytest tests/ && npm test`
- Linting clean: `black --check . && npm run lint`
- Documentation updated if needed

## Subagent Delegation

### When to Use Subagents
- **Parallel research**: Multiple docs/APIs to investigate
- **Independent components**: Frontend + backend simultaneously
- **Verification**: Independent review of implementation
- **Complex debugging**: Isolated context for focused work

### Delegation Syntax
```
# Research delegation
"Dispatch a subagent to investigate [topic], return summary of findings"

# Implementation delegation  
"Use a subagent to implement [component] following specs in docs/plan.md"

# Verification delegation
"Have a subagent verify [implementation] against requirements, report issues"
```

### Subagent Context Isolation
Each subagent gets:
- This CLAUDE.md
- Relevant source files only
- Specific task instructions

Return to orchestrator:
- Completion status
- File changes made
- Issues encountered

## Extended Thinking Triggers
| Trigger | Budget | Use Case |
|---------|--------|----------|
| think | Standard | Simple planning |
| think hard | Extended | Architecture decisions |
| think harder | Deep | Complex refactoring |
| ultrathink | Maximum | Critical system design |

## Commands Reference
```bash
# Backend Development
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
pytest tests/backend/ -v --tb=short
pytest tests/backend/test_specific.py::test_name -v
python -m black backend/
python -m mypy backend/

# Frontend Development
npm run dev
npm run test -- --watch
npm run lint -- --fix
npm run build

# E2E Testing
npx playwright test
npx playwright test --headed  # Visual debugging

# Full Validation
./scripts/validate.sh  # Runs all checks
```

## Code Patterns

### FastAPI Endpoint
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1")

class ItemRequest(BaseModel):
    name: str
    value: int

@router.post("/items", response_model=ItemResponse)
async def create_item(
    request: ItemRequest,
    db: Session = Depends(get_db)
) -> ItemResponse:
    # Implementation
    pass
```

### Frontend API Call
```javascript
async function fetchData(endpoint) {
  try {
    const response = await fetch(`/api/v1/${endpoint}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

## Quality Gates
Before ANY commit:
- [ ] Tests pass for changed code
- [ ] No linting errors
- [ ] Types check (mypy for Python)
- [ ] plan.md task checked off
- [ ] Commit message follows: `type(scope): description`

## MCP Integration

### Configuration (.mcp.json)
```json
{
  "mcpServers": {
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    },
    "puppeteer": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-puppeteer@latest"]
    }
  }
}
```

### Available Servers
- **Context7**: Up-to-date library docs for FastAPI, React, etc.
- **Puppeteer**: Browser automation, screenshots, UI validation

### Visual Validation Workflow (Puppeteer)
For any frontend work, use this iteration loop:

1. **Implement** the UI component
2. **Start dev server**: `uvicorn backend.main:app --reload`
3. **Screenshot**: "Navigate to http://localhost:8000 and take a screenshot"
4. **Compare**: Claude evaluates against requirements or mockup
5. **Iterate**: Fix issues, screenshot again
6. **Approve**: When visual matches expectations, commit

#### Puppeteer Commands
```
"Navigate to http://localhost:8000/page and screenshot it"
"Click the button with id='submit' and screenshot the result"
"Fill the form field #email with 'test@example.com'"
"Screenshot the element with class='dashboard'"
"Take a full-page screenshot of the current view"
```

#### Visual Iteration Example
```
You: "Build a login form with email and password fields"

Claude:
1. Creates frontend/static/js/login.js
2. Updates index.html with form
3. Navigates to http://localhost:8000
4. Takes screenshot
5. Reviews: "The form renders but lacks styling"
6. Adds CSS
7. Screenshots again
8. Reviews: "Form is centered with proper spacing"
9. Reports: "Login form complete, ready for review"
```

## Error Recovery
When stuck or tests fail:
1. Stop and assess - don't keep trying same approach
2. Use subagent to investigate root cause independently
3. Check if plan needs revision
4. Consult documentation via Context7 MCP
5. If blocked >3 attempts, pause and report to user

## Forbidden Actions
- Skipping tests to "save time"
- Modifying unrelated files
- Large refactors without plan approval
- Ignoring failing tests
- Committing without running validators
