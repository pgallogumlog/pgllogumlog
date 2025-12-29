# Designer B: Tier-Optimized Selection Strategy

## Approach Type
**BY-TIER** - Fundamentally different selection logic per tier

## Core Philosophy
One size does NOT fit all. Budget users need different workflows than Premium users. The selection algorithm should mirror user expectations and willingness to invest in complexity.

## Tier-Specific Algorithms

### Budget Tier: "Quick Wins First"

**Goal**: Maximize ROI velocity. Users want simple, proven automations they can deploy this week.

**Selection Logic**:
```
Priority Order:
1. Feasibility = "High" (mandatory filter)
2. Tool count ≤ 3 (prefer simplicity)
3. Contains at least one no-code platform (Zapier/n8n/Make/IFTTT)
4. Metrics show time savings (not just accuracy)

Scoring Formula:
Score = Feasibility(1.0) × SimplexityBonus × TimeROI × ToolFamiliarity

SimplexityBonus = 2.0 if ≤3 tools, else 1.0
TimeROI = 1.5 if metrics mention "time" or "faster" or "reduce", else 1.0
ToolFamiliarity = 1.3 if Zapier/n8n/Make present, else 1.0
```

**Diversity**: Ensure no 2 workflows use identical tool combinations

### Standard Tier: "Balanced Portfolio"

**Goal**: Show strategic thinking. Users want a mix of quick wins + strategic initiatives.

**Selection Logic**:
```
Build a portfolio:
- 2 "Quick Wins" (High feasibility, ≤4 tools)
- 2 "Strategic Plays" (Medium/High feasibility, impactful metrics)
- 1 "Innovation Bet" (Medium feasibility, advanced tech)

Scoring by Category:
Quick Wins: Feasibility × Simplicity × TimeROI
Strategic Plays: Metrics Impact × Business Value × Feasibility
Innovation Bet: TechSophistication × Feasibility × UniqueValue

TechSophistication = 2.0 if "Custom ML"|"AI"|"API" in tools, else 1.0
BusinessValue = keyword match for industry terms from prompt
```

**Diversity**: Each category must cover different business functions

### Premium Tier: "Competitive Advantage"

**Goal**: Demonstrate thought leadership. Users want innovative, differentiated solutions that competitors don't have.

**Selection Logic**:
```
Priority Order:
1. Innovation Score (custom ML, proprietary APIs, advanced analytics)
2. Competitive Differentiation (unique approach, not commodity)
3. Business Impact (metrics showing transformative results)
4. Feasibility (still matters, but Medium is acceptable)

Scoring Formula:
Score = InnovationScore × ImpactMultiplier × Uniqueness × FeasibilityFloor

InnovationScore = Count of advanced tech keywords × 0.5
  - Keywords: Custom, ML, AI, Neural, Predictive, Proprietary, Advanced Analytics
  - Range: [0.5, 3.0]

ImpactMultiplier = Max metric value / 50
  - E.g., "95% accuracy" → 95/50 = 1.9
  - E.g., "10x faster" → 500/50 = 10.0 (capped at 5.0)

Uniqueness = 2.0 if workflow name/approach is novel, else 1.0
  - Novel: Not a commodity (e.g., "Quantum Risk Analyzer" > "Email Notifications")

FeasibilityFloor = 1.0 if High, 0.6 if Medium, 0.2 if Low
  - Premium users accept complexity, but not impossibility
```

**Diversity**: Must cover at least 3 different innovation themes (ML/Analytics, Integration/API, Process Intelligence, etc.)

## Mathematical Formulation

### Budget Tier
```
Score_budget(w) = F(w) × S(w) × R(w) × T(w)

F(w) = 1.0 if feasibility="High", else 0 (hard filter)
S(w) = 2.0 if |tools| ≤ 3, else 1.0
R(w) = 1.5 if "time"|"faster"|"reduce" in metrics, else 1.0
T(w) = 1.3 if nocode_tool in tools, else 1.0

Max possible score: 3.9
```

### Standard Tier
```
Portfolio Selection (not single formula):

Quick Wins (select 2):
  Score_qw(w) = F(w) × S(w) × R(w)
  F(w) ∈ {1.0, 0.7}, S(w) ∈ {1.5, 1.0}, R(w) ∈ {1.5, 1.0}

Strategic Plays (select 2):
  Score_sp(w) = M(w) × B(w) × F(w)
  M(w) = avg(metrics_values) / 50, capped [0.5, 3.0]
  B(w) = business_keyword_matches / 5, capped [0.5, 2.0]
  F(w) ∈ {1.0, 0.7, 0.3}

Innovation Bet (select 1):
  Score_ib(w) = T(w) × F(w) × U(w)
  T(w) = advanced_tech_count × 0.5, range [0.5, 3.0]
  U(w) = 2.0 if unique approach, else 1.0
  F(w) ∈ {1.0, 0.7, 0.3}
```

### Premium Tier
```
Score_premium(w) = I(w) × M(w) × U(w) × F(w)

I(w) = count(advanced_keywords in tools) × 0.5, range [0.5, 3.0]
M(w) = max(extract_numbers(metrics)) / 50, capped [0.5, 5.0]
U(w) = 2.0 if novel_workflow(w), else 1.0
F(w) = {1.0: High, 0.6: Medium, 0.2: Low}

Max possible score: 30.0
```

## Diversity Mechanisms

### Budget Tier
**Tool Combination Uniqueness**: No two workflows can have the exact same tool set
- E.g., if Workflow 1 = [Zapier, Gmail], Workflow 2 cannot be [Zapier, Gmail]
- Ensures users see different implementation patterns

### Standard Tier
**Categorical Diversity**: Portfolio categories (Quick Win, Strategic, Innovation) are mutually exclusive
**Business Function Coverage**: Each category must address different business areas
- Track covered functions: {data_processing, compliance, communication, analytics, operations}
- Penalize selecting 2 workflows in same function within same category

### Premium Tier
**Innovation Theme Diversity**: Workflows must represent different innovation approaches
- Themes: ML/AI, Advanced Analytics, Custom Integration, Process Intelligence, Predictive Systems
- Select maximum 2 workflows per theme
- Priority to theme leaders (highest score in that theme)

## Tier Handling Philosophy

**Why BY-TIER?**

1. **User Expectations Differ Fundamentally**:
   - Budget: "Show me easy wins I can implement this month"
   - Standard: "Give me a balanced roadmap"
   - Premium: "Challenge me with innovative thinking"

2. **Value Proposition Varies**:
   - Budget: Speed to value
   - Standard: Strategic planning
   - Premium: Competitive differentiation

3. **Risk Tolerance Varies**:
   - Budget: Low risk (must be proven)
   - Standard: Moderate risk (mix of proven + new)
   - Premium: Higher risk acceptable (innovation requires experimentation)

4. **Resource Availability**:
   - Budget: Small teams, limited technical expertise
   - Standard: Medium teams, some technical capacity
   - Premium: Can hire/train for complex implementations

## Pseudocode Implementation

```python
def select_top_5_workflows(workflows, tier, prompt):
    if tier == "Budget":
        return select_budget_tier(workflows)
    elif tier == "Standard":
        return select_standard_tier(workflows, prompt)
    else:  # Premium
        return select_premium_tier(workflows)

def select_budget_tier(workflows):
    # Hard filter: High feasibility only
    candidates = [w for w in workflows if w.feasibility == "High"]

    # Score each
    scored = []
    for wf in candidates:
        simplexity = 2.0 if len(wf.tools) <= 3 else 1.0
        time_roi = 1.5 if has_time_savings(wf.metrics) else 1.0
        tool_fam = 1.3 if has_nocode_tool(wf.tools) else 1.0

        score = 1.0 * simplexity * time_roi * tool_fam
        scored.append((wf, score))

    # Sort by score
    scored.sort(key=lambda x: x[1], reverse=True)

    # Select top 5 with unique tool combinations
    selected = []
    tool_combos_used = set()

    for wf, score in scored:
        tool_combo = frozenset(wf.tools)
        if tool_combo not in tool_combos_used:
            selected.append(wf)
            tool_combos_used.add(tool_combo)

            if len(selected) == 5:
                break

    # Backfill if needed
    for wf, score in scored:
        if len(selected) >= 5:
            break
        if wf not in selected:
            selected.append(wf)

    return selected[:5]

def select_standard_tier(workflows, prompt):
    business_keywords = extract_industry_terms(prompt)

    # Score by category
    quick_wins = []
    strategic_plays = []
    innovation_bets = []

    for wf in workflows:
        # Quick Win scoring
        if wf.feasibility == "High" and len(wf.tools) <= 4:
            f = 1.0 if wf.feasibility == "High" else 0.7
            s = 1.5 if len(wf.tools) <= 3 else 1.0
            r = 1.5 if has_time_savings(wf.metrics) else 1.0
            qw_score = f * s * r
            quick_wins.append((wf, qw_score, "quick_win"))

        # Strategic Play scoring
        if wf.feasibility in ["High", "Medium"]:
            m = calculate_metrics_impact(wf.metrics)
            b = count_business_keywords(wf, business_keywords)
            f = {"High": 1.0, "Medium": 0.7, "Low": 0.3}[wf.feasibility]
            sp_score = m * b * f
            strategic_plays.append((wf, sp_score, "strategic"))

        # Innovation Bet scoring
        if has_advanced_tech(wf.tools):
            t = count_advanced_tech(wf.tools) * 0.5
            f = {"High": 1.0, "Medium": 0.7, "Low": 0.3}[wf.feasibility]
            u = 2.0 if is_novel(wf) else 1.0
            ib_score = t * f * u
            innovation_bets.append((wf, ib_score, "innovation"))

    # Select portfolio
    quick_wins.sort(key=lambda x: x[1], reverse=True)
    strategic_plays.sort(key=lambda x: x[1], reverse=True)
    innovation_bets.sort(key=lambda x: x[1], reverse=True)

    portfolio = []

    # 2 Quick Wins (different functions)
    functions_used = set()
    for wf, score, cat in quick_wins:
        func = classify_function(wf)
        if func not in functions_used:
            portfolio.append(wf)
            functions_used.add(func)
            if len([p for p in portfolio if classify_function(p) in functions_used]) >= 2:
                break

    # 2 Strategic Plays (different functions from quick wins)
    for wf, score, cat in strategic_plays:
        func = classify_function(wf)
        if func not in functions_used and wf not in portfolio:
            portfolio.append(wf)
            functions_used.add(func)
            if len(portfolio) >= 4:
                break

    # 1 Innovation Bet
    for wf, score, cat in innovation_bets:
        if wf not in portfolio:
            portfolio.append(wf)
            break

    return portfolio[:5]

def select_premium_tier(workflows):
    scored = []

    for wf in workflows:
        # Innovation score
        innovation = count_advanced_tech(wf.tools) * 0.5
        innovation = max(0.5, min(3.0, innovation))

        # Impact multiplier
        impact = extract_max_metric(wf.metrics) / 50
        impact = max(0.5, min(5.0, impact))

        # Uniqueness
        uniqueness = 2.0 if is_novel(wf) else 1.0

        # Feasibility floor
        feasibility = {"High": 1.0, "Medium": 0.6, "Low": 0.2}[wf.feasibility]

        score = innovation * impact * uniqueness * feasibility
        theme = classify_innovation_theme(wf)

        scored.append((wf, score, theme))

    # Sort by score
    scored.sort(key=lambda x: x[1], reverse=True)

    # Select with theme diversity
    selected = []
    theme_counts = {}

    for wf, score, theme in scored:
        if theme_counts.get(theme, 0) < 2:
            selected.append(wf)
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

            if len(selected) == 5:
                break

    return selected[:5]

# Helper functions
def has_time_savings(metrics):
    text = ' '.join(metrics).lower()
    return any(kw in text for kw in ['time', 'faster', 'reduce', 'speed'])

def has_nocode_tool(tools):
    tool_str = ' '.join(tools).lower()
    return any(t in tool_str for t in ['zapier', 'n8n', 'make', 'ifttt'])

def has_advanced_tech(tools):
    tool_str = ' '.join(tools).lower()
    return any(kw in tool_str for kw in ['custom', 'ml', 'ai', 'neural', 'api'])

def count_advanced_tech(tools):
    tool_str = ' '.join(tools).lower()
    keywords = ['custom', 'ml', 'ai', 'neural', 'predictive', 'proprietary', 'advanced']
    return sum(1 for kw in keywords if kw in tool_str)

def is_novel(workflow):
    # Heuristic: check if name contains advanced/unique terms
    novel_terms = ['quantum', 'neural', 'cognitive', 'intelligent', 'adaptive', 'predictive']
    name_lower = workflow.name.lower()
    return any(term in name_lower for term in novel_terms)

def classify_function(workflow):
    # Same as Designer A's classify_domain
    text = f"{workflow.name} {workflow.objective}".lower()
    if any(kw in text for kw in ['data', 'classification', 'extraction']):
        return "data"
    elif any(kw in text for kw in ['compliance', 'risk', 'regulatory']):
        return "compliance"
    elif any(kw in text for kw in ['communication', 'email', 'notification']):
        return "communication"
    elif any(kw in text for kw in ['analytics', 'intelligence', 'insights']):
        return "analytics"
    else:
        return "operations"

def classify_innovation_theme(workflow):
    tools_str = ' '.join(workflow.tools).lower()
    desc = workflow.description.lower()

    if 'ml' in tools_str or 'ai' in tools_str or 'neural' in tools_str:
        return "ml_ai"
    elif 'analytics' in desc or 'insight' in desc or 'intelligence' in desc:
        return "advanced_analytics"
    elif 'api' in tools_str or 'custom' in tools_str:
        return "custom_integration"
    elif 'predict' in desc or 'forecast' in desc:
        return "predictive_systems"
    else:
        return "process_intelligence"

def extract_max_metric(metrics):
    import re
    numbers = []
    for metric in metrics:
        nums = re.findall(r'(\d+)', metric)
        numbers.extend([float(n) for n in nums])
    return max(numbers) if numbers else 50

def calculate_metrics_impact(metrics):
    nums = extract_max_metric(metrics)
    return max(0.5, min(3.0, nums / 50))

def extract_industry_terms(prompt):
    # Extract domain-specific nouns from prompt
    # Simplified: split and filter
    words = prompt.lower().split()
    stopwords = {'the', 'and', 'for', 'based', 'on', 'top', 'ai'}
    return [w for w in words if len(w) > 4 and w not in stopwords]

def count_business_keywords(workflow, keywords):
    text = f"{workflow.name} {workflow.description}".lower()
    matches = sum(1 for kw in keywords if kw in text)
    return max(0.5, min(2.0, matches / 5))
```

## Justification

### Why This Delivers Best Results

1. **Respects User Context**: Different payment tiers = different user needs. BY-TIER design acknowledges this reality.

2. **Optimizes for Tier Goals**:
   - Budget: Maximize implementation success rate (high feasibility, simplicity)
   - Standard: Balance quick wins with strategic vision (portfolio approach)
   - Premium: Maximize competitive differentiation (innovation focus)

3. **Clear Value Differentiation**: Users paying more get fundamentally different analysis, not just "more of the same"

4. **Portfolio Theory (Standard)**: Standard tier uses portfolio construction (2-2-1 split) from investment theory - balance risk/return

5. **Innovation Focus (Premium)**: Premium tier actively seeks novel approaches, not commodity solutions - justifies premium pricing

6. **Data-Informed**: Analysis showed no tier differentiation in current generation - this selection layer adds the necessary differentiation

## Example Application

Using: Premium tier, Latham & Watkins LLP prompt

**Top 5 Selected**:

1. **Cognitive Contract Analyzer** (Innovation Theme: ML/AI)
   - Tools: [Custom NLP, TensorFlow, Legal Ontology API]
   - Innovation: 3 advanced keywords × 0.5 = 1.5
   - Impact: 96% accuracy → 96/50 = 1.92
   - Uniqueness: Novel ("Cognitive") = 2.0
   - Feasibility: Medium = 0.6
   - Score: 1.5 × 1.92 × 2.0 × 0.6 = 3.46

2. **Predictive Timeline Forecaster** (Theme: Predictive Systems)
   - Tools: [Prophet ML, Custom API, Jira Integration]
   - Innovation: 2 × 0.5 = 1.0
   - Impact: 15x accuracy → 5.0 (capped)
   - Uniqueness: Novel ("Predictive") = 2.0
   - Feasibility: Medium = 0.6
   - Score: 1.0 × 5.0 × 2.0 × 0.6 = 6.0

3. **Multi-Jurisdiction Risk Synthesizer** (Theme: Advanced Analytics)
   - Tools: [Custom Analytics Engine, Legal DB API, Tableau]
   - Innovation: 1 × 0.5 = 0.5 (minimum)
   - Impact: 98% coverage → 1.96
   - Uniqueness: Standard = 1.0
   - Feasibility: High = 1.0
   - Score: 0.5 × 1.96 × 1.0 × 1.0 = 0.98

4. **Intelligent Document Router** (Theme: ML/AI - 2nd in theme)
   - Tools: [Custom ML Model, Azure AI, n8n]
   - Innovation: 2 × 0.5 = 1.0
   - Impact: 99% routing accuracy → 1.98
   - Uniqueness: Standard = 1.0
   - Feasibility: High = 1.0
   - Score: 1.0 × 1.98 × 1.0 × 1.0 = 1.98

5. **Cross-Border Compliance Orchestrator** (Theme: Process Intelligence)
   - Tools: [Custom Workflow Engine, API Integrations, Compliance DB]
   - Innovation: 1 × 0.5 = 0.5
   - Impact: 5x compliance speed → 5.0 (capped)
   - Uniqueness: Standard = 1.0
   - Feasibility: Medium = 0.6
   - Score: 0.5 × 5.0 × 1.0 × 0.6 = 1.5

**Theme Distribution**: ✓ ML/AI (2), Predictive (1), Analytics (1), Process (1) - Good diversity

## Strengths
- Clear differentiation by tier
- Portfolio approach for Standard tier is sophisticated
- Premium tier actively seeks innovation
- Each tier optimized for its user persona

## Potential Weaknesses
- More complex implementation (3 separate algorithms)
- Harder to maintain (changes require updating 3 code paths)
- "Novel" workflow detection is heuristic-based
- May over-filter Budget tier (only High feasibility allowed)

## Implementation Complexity
**Medium-High** - Three distinct algorithms, portfolio construction logic, ~300 lines of code
