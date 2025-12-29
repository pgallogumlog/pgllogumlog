# Workflow Selection Design Challenge - Briefing Document

## Challenge Overview
Design an optimal method for selecting the top 5 workflows from ~125 generated workflows per user prompt.

## System Context
- **Input**: User prompt describing automation needs + selected tier (Budget/Standard/Premium)
- **Generation**: Multi-temperature self-consistency creates ~125 workflows (5 temperatures × 5 workflows × 5 iterations, deduplicated to ~25-125 unique)
- **Challenge**: Select the best 5 workflows to present to the user
- **Goal**: Maximize user value, relevance, diversity, and feasibility

## Available Data
- **Dataset**: `real_5prompts.json`
- **Contains**: 15 test runs (5 distinct business prompts × 3 tiers)
- **Total workflows**: 1,875 workflows
- **Per prompt**: 125 workflows with full metadata

## Workflow Attributes
Each workflow includes:
- `name`: Workflow title
- `objective`: What it aims to achieve
- `description`: How it works
- `tools`: Array of automation tools/APIs used (e.g., n8n, Zapier, Make, APIs)
- `metrics`: Expected performance metrics (accuracy %, time savings, etc.)
- `feasibility`: High/Medium/Low

## Metadata Per Run
- `consensus_strength`: Strong/Moderate/Weak (from multi-temperature voting)
- `confidence_percent`: 0-100% confidence score
- `company`: Target company name
- `prompt`: User's original request

## Tier Characteristics
Based on analysis of the data:

**Budget Tier**:
- Focus: Simple, quick-win automations
- Tools: Common no-code platforms (Zapier, n8n, Make)
- Complexity: Lower tool count, straightforward integrations
- User expectation: Fast ROI, minimal setup

**Standard Tier**:
- Focus: Balanced sophistication and practicality
- Tools: Mix of no-code + some APIs
- Complexity: Moderate integration complexity
- User expectation: Comprehensive analysis with actionable insights

**Premium Tier**:
- Focus: Advanced, strategic automation opportunities
- Tools: Custom ML models, specialized APIs, enterprise platforms
- Complexity: Higher, may include custom development
- User expectation: Deep analysis, innovative solutions, competitive advantage

## Design Constraints
1. Must select exactly 5 workflows per user request
2. Must work across all three tiers (Budget, Standard, Premium)
3. Must be implementable in Python with minimal dependencies
4. Should leverage available workflow attributes and metadata
5. Should be explainable to users (why these 5?)

## Design Approaches to Consider

### Option A: BY-TIER Approach
Different selection criteria per tier:
- Budget: Prioritize feasibility + simplicity (tool count)
- Standard: Balance feasibility + impact (metrics)
- Premium: Prioritize innovation + sophistication (tool diversity, custom ML)

### Option B: HOLISTIC Approach
Same selection criteria across tiers, potentially with weighted parameters:
- Universal scoring formula considering: relevance, diversity, feasibility, metrics
- Tier affects weights but not fundamental selection logic

### Your Mission
1. Review the data in `real_5prompts.json`
2. Propose ONE distinct approach (either BY-TIER or HOLISTIC or hybrid)
3. Specify concrete selection algorithm with:
   - Scoring/ranking formula
   - Diversity mechanisms (avoid selecting 5 similar workflows)
   - Tie-breaking rules
   - Handling edge cases (e.g., all workflows have "High" feasibility)
4. Justify why your approach delivers highest quality results
5. Provide implementation pseudocode

## Evaluation Criteria
Your design will be evaluated on:
1. **Relevance**: Do selected workflows match user prompt?
2. **Diversity**: Do the 5 workflows cover different automation opportunities?
3. **Feasibility**: Are workflows practical and achievable?
4. **Tier Alignment**: Do results match tier expectations?
5. **Implementability**: Can this be coded efficiently in Python?
6. **Explainability**: Can we tell users WHY these 5 were chosen?

## Cross-Review Process
After all designers submit approaches, you will:
1. Review the other two designers' approaches
2. Identify strengths and weaknesses
3. Suggest improvements or highlight risks
4. Vote on which approach provides highest quality

## Deliverable Format
Submit a markdown document with:
- **Approach Name**: Descriptive title
- **Type**: BY-TIER or HOLISTIC
- **Core Algorithm**: Detailed selection logic
- **Scoring Formula**: Mathematical or programmatic
- **Diversity Mechanism**: How you ensure variety
- **Tier Handling**: How tiers affect selection (if at all)
- **Pseudocode**: Implementation outline
- **Justification**: Why this delivers best results
- **Example**: Apply to one prompt from real_5prompts.json and show the 5 selected workflows

## Timeline
- Design Phase: 30 minutes (review data + design approach)
- Cross-Review Phase: 15 minutes (evaluate other designs)
- Final Vote: 5 minutes

## Data Access
File path: `/c/Users/PeteG/PycharmProjects/learnClaude/workflow_system/data/real_5prompts.json`

Structure:
```json
{
  "metadata": {...},
  "data": {
    "Budget": {
      "prompt_<company>": {
        "test_id": "...",
        "company": "...",
        "prompt": "...",
        "workflow_count": 125,
        "consensus_strength": "...",
        "confidence_percent": ...,
        "workflows": [
          {
            "name": "...",
            "objective": "...",
            "description": "...",
            "tools": [...],
            "metrics": [...],
            "feasibility": "High|Medium|Low"
          },
          ...
        ]
      }
    },
    "Standard": {...},
    "Premium": {...}
  }
}
```

## Questions?
If anything is unclear, note it in your design document and proceed with reasonable assumptions.

Good luck, designers!
