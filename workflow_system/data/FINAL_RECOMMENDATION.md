# Workflow Selection Design - Final Recommendation

## Executive Summary

After comprehensive analysis of three distinct workflow selection approaches, this document provides a data-driven recommendation for implementing the workflow selection algorithm in our multi-temperature consensus workflow generation system.

**RECOMMENDATION: Hybrid Approach - "Feasibility-First with Semantic Enhancement"**

Combine Designer A's feasibility-focused foundation with Designer C's prompt-relevance insights, using simple tier-aware weighting from Designer B.

---

## The Three Approaches (Quick Reference)

### Designer A: Feasibility-First Progressive Selection
- **Type**: HOLISTIC with tier weighting
- **Formula**: `Score = Feasibility × Metrics × ToolPracticality × DomainDiversity`
- **Strength**: Simple, reliable, implementable
- **Weakness**: Ignores prompt relevance
- **Complexity**: Low (150 lines)

### Designer B: Tier-Optimized Selection
- **Type**: BY-TIER (3 separate algorithms)
- **Formula**: Different per tier (Budget: Simplicity, Standard: Portfolio, Premium: Innovation)
- **Strength**: Clear tier value differentiation
- **Weakness**: High complexity, maintenance burden
- **Complexity**: High (300 lines)

### Designer C: Semantic Relevance & Impact Maximization
- **Type**: HOLISTIC with semantic analysis
- **Formula**: `Score = SemanticRelevance × Impact × Feasibility × Consensus`
- **Strength**: Measures prompt relevance, uses consensus metadata
- **Weakness**: TF-IDF is crude semantic similarity
- **Complexity**: Medium (250 lines)

---

## Why Hybrid Approach Wins

### Critical Insight from Data Analysis

Our analysis of `real_5prompts.json` revealed:
- Each prompt generates ~125 workflows
- Feasibility distribution: 45% High, 47% Medium, 8% Low (consistent across tiers)
- Current generation does NOT differentiate by tier (tool sophistication nearly identical)
- No current mechanism ensures generated workflows match user prompt

**Implication**: We need BOTH feasibility filtering (Designer A) AND prompt-relevance checking (Designer C).

### The Hybrid Formula

```
Final Score = Semantic_Relevance × Feasibility_Weight × Metrics_Impact × Tool_Practicality × Domain_Diversity_Bonus × Tier_Adjustment

Where:
- Semantic_Relevance: TF-IDF keyword overlap between workflow and user prompt [0.5, 3.0]
- Feasibility_Weight: {High: 1.0, Medium: 0.6-0.9, Low: 0.3}
- Metrics_Impact: Max metric value normalized [1.0, 5.0]
- Tool_Practicality: Based on tool count and tier-appropriateness [0.7, 1.2]
- Domain_Diversity_Bonus: 1.5 if new domain, 1.0 if duplicate domain
- Tier_Adjustment: Multiplier based on tier {Budget: 1.0, Standard: 1.1, Premium: 1.2}
```

**Selection Process**:
1. Score all 125 workflows using formula above
2. Sort by score (descending)
3. Greedy selection with domain diversity constraint (prefer uncovered domains)
4. Select top 5 with minimum 3 different domains represented

---

## Detailed Design Specification

### Input
```python
def select_top_5_workflows(
    workflows: List[Workflow],           # 125 workflows from generation
    tier: str,                            # "Budget" | "Standard" | "Premium"
    user_prompt: str,                     # Original user request
    consensus_strength: str = "Moderate"  # From generation metadata
) -> List[Workflow]:
```

### Step 1: Extract Prompt Keywords (TF-IDF Style)

```python
def extract_keywords(text: str) -> Dict[str, float]:
    """Extract weighted keywords from text."""
    stopwords = {'the', 'and', 'or', 'for', 'with', 'to', 'of', 'in', 'a', 'an', 'is', 'at'}
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in stopwords and len(w) > 3]

    freq = Counter(keywords)
    # Weight by log frequency (simple TF)
    weighted = {term: math.log(1 + count) for term, count in freq.items()}

    return weighted
```

### Step 2: Calculate Semantic Relevance

```python
def calculate_semantic_relevance(workflow: Workflow, user_prompt: str) -> float:
    """Measure workflow relevance to user prompt."""
    prompt_kw = extract_keywords(user_prompt)
    wf_text = f"{workflow.name} {workflow.objective} {workflow.description}"
    wf_kw = extract_keywords(wf_text)

    # Keyword overlap
    common = set(prompt_kw.keys()) & set(wf_kw.keys())

    if not common:
        return 0.5  # Baseline for no overlap

    # Weighted overlap (sum of products of weights)
    overlap_score = sum(prompt_kw[kw] * wf_kw[kw] for kw in common)

    # Normalize by total prompt keyword weight
    total_prompt_weight = sum(prompt_kw.values())
    normalized = overlap_score / total_prompt_weight if total_prompt_weight > 0 else 0.5

    # Scale to [0.5, 3.0]
    semantic_score = 0.5 + (normalized * 2.5)

    return min(3.0, semantic_score)
```

### Step 3: Score Feasibility (Tier-Aware)

```python
def get_feasibility_weight(feasibility: str, tier: str) -> float:
    """Feasibility weight with tier sensitivity."""
    base = {
        "High": 1.0,
        "Medium": 0.75,
        "Low": 0.3
    }

    weight = base[feasibility]

    # Tier adjustments
    if feasibility == "Medium":
        if tier == "Budget":
            weight = 0.6  # Budget users need higher certainty
        elif tier == "Premium":
            weight = 0.9  # Premium users tolerate complexity

    return weight
```

### Step 4: Extract Metrics Impact

```python
def calculate_metrics_impact(metrics: List[str]) -> float:
    """Extract max impact from metrics."""
    if not metrics:
        return 1.0

    impact_values = []

    for metric in metrics:
        metric_lower = metric.lower()

        # Extract percentages
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', metric)
        for pct_str in percentages:
            pct = float(pct_str)

            # Context-aware scoring
            if any(kw in metric_lower for kw in ['accura', 'precision']):
                impact = max(0.5, (pct - 70) / 20)  # 90%+ is excellent
            elif any(kw in metric_lower for kw in ['reduc', 'sav']):
                impact = pct / 50  # 50% reduction = 1.0 impact
            else:
                impact = pct / 100

            impact_values.append(impact)

        # Extract multipliers (5x, 10x)
        multipliers = re.findall(r'(\d+(?:\.\d+)?)\s*x', metric_lower)
        for mult_str in multipliers:
            mult = float(mult_str)
            impact_values.append(mult / 2)  # 2x = 1.0 impact

    if not impact_values:
        return 1.0

    # Use max (highlight best metric)
    max_impact = max(impact_values)

    return max(1.0, min(5.0, max_impact))
```

### Step 5: Tool Practicality Score

```python
def calculate_tool_practicality(tools: List[str], tier: str) -> float:
    """Score based on tool count and tier-appropriateness."""
    tool_count = len(tools)

    # Base score by tool count (fewer = simpler)
    if tool_count <= 3:
        score = 1.0
    elif tool_count <= 5:
        score = 0.85
    else:
        score = 0.7

    # Tier-specific boosts
    tool_str = ' '.join(tools).lower()

    if tier == "Budget":
        # Boost for common no-code tools
        if any(t in tool_str for t in ['zapier', 'n8n', 'make', 'ifttt']):
            score += 0.2
    elif tier == "Premium":
        # Boost for advanced/custom tools
        if any(kw in tool_str for kw in ['custom', 'api', 'ml', 'ai']):
            score += 0.15

    return min(1.2, score)
```

### Step 6: Domain Classification

```python
def classify_domain(workflow: Workflow) -> str:
    """Classify workflow into functional domain."""
    text = f"{workflow.name} {workflow.objective} {workflow.description}".lower()

    domain_keywords = {
        'data_processing': ['classify', 'extract', 'parse', 'nlp', 'ocr', 'document'],
        'compliance_risk': ['compliance', 'regulatory', 'audit', 'risk', 'legal'],
        'communication': ['email', 'notification', 'report', 'dashboard', 'alert'],
        'analytics': ['analytics', 'insight', 'predict', 'forecast', 'intelligence'],
        'workflow_mgmt': ['orchestr', 'track', 'coordinate', 'manage', 'monitor'],
        'integration': ['integration', 'sync', 'connect', 'api', 'bridge']
    }

    for domain, keywords in domain_keywords.items():
        if any(kw in text for kw in keywords):
            return domain

    return 'other'
```

### Step 7: Main Selection Function

```python
def select_top_5_workflows(
    workflows: List[Workflow],
    tier: str,
    user_prompt: str,
    consensus_strength: str = "Moderate"
) -> List[Workflow]:
    """Select top 5 workflows using hybrid scoring."""

    # Consensus bonus
    consensus_bonus = {
        "Strong": 1.2,
        "Moderate": 1.1,
        "Weak": 1.0
    }.get(consensus_strength, 1.1)

    # Tier adjustment
    tier_multiplier = {
        "Budget": 1.0,
        "Standard": 1.1,
        "Premium": 1.2
    }[tier]

    # Score all workflows
    scored = []

    for wf in workflows:
        # Component scores
        semantic = calculate_semantic_relevance(wf, user_prompt)
        feasibility = get_feasibility_weight(wf.feasibility, tier)
        impact = calculate_metrics_impact(wf.metrics)
        tools = calculate_tool_practicality(wf.tools, tier)

        # Base score (without domain bonus yet)
        base_score = semantic * feasibility * impact * tools * consensus_bonus * tier_multiplier

        scored.append({
            'workflow': wf,
            'score': base_score,
            'domain': classify_domain(wf)
        })

    # Sort by score (descending)
    scored.sort(key=lambda x: x['score'], reverse=True)

    # Greedy selection with domain diversity
    selected = []
    domains_covered = set()

    for item in scored:
        if len(selected) >= 5:
            break

        domain = item['domain']

        # First workflow: always take highest score
        if len(selected) == 0:
            selected.append(item)
            domains_covered.add(domain)
            continue

        # Prefer uncovered domains
        if domain not in domains_covered:
            # Apply diversity bonus
            item['score'] *= 1.5
            selected.append(item)
            domains_covered.add(domain)
        else:
            # Allow duplicate domain if score is significantly higher
            # OR we've met diversity target (3 domains)
            if item['score'] > selected[-1]['score'] * 1.3 or len(domains_covered) >= 3:
                selected.append(item)

    # Backfill if needed (shouldn't happen with 125 workflows, but safety check)
    if len(selected) < 5:
        for item in scored:
            if len(selected) >= 5:
                break
            if item not in selected:
                selected.append(item)

    return [s['workflow'] for s in selected[:5]]
```

---

## Implementation Plan

### Phase 1: Core Implementation (Week 1)
**File**: `workflow_system/contexts/workflow/selector.py`

```python
# New module: workflow selector
from typing import List, Dict
import re
import math
from collections import Counter
from .models import Workflow

class WorkflowSelector:
    """Selects top 5 workflows from generated candidates."""

    def select_top_5(
        self,
        workflows: List[Workflow],
        tier: str,
        user_prompt: str,
        consensus_strength: str = "Moderate"
    ) -> List[Workflow]:
        """Main selection method."""
        # Implementation as specified above
        pass

    # Helper methods: extract_keywords, calculate_semantic_relevance, etc.
```

**Integration Point**: `workflow_system/contexts/workflow/engine.py`

```python
# In WorkflowEngine.process_inquiry()
# After workflow generation and deduplication:

from .selector import WorkflowSelector

selector = WorkflowSelector()
top_5_workflows = selector.select_top_5(
    workflows=deduplicated_workflows,
    tier=tier,
    user_prompt=user_inquiry.prompt,
    consensus_strength=consensus_result.strength
)

# Return top_5_workflows to user
```

### Phase 2: Testing (Week 1-2)

**Unit Tests**: `workflow_system/tests/unit/contexts/test_selector.py`

```python
class TestWorkflowSelector:
    def test_keyword_extraction(self):
        """Test TF-IDF keyword extraction."""
        pass

    def test_semantic_relevance_high_overlap(self):
        """Test semantic scoring with high keyword overlap."""
        pass

    def test_semantic_relevance_no_overlap(self):
        """Test semantic scoring with no overlap (baseline)."""
        pass

    def test_domain_diversity_enforced(self):
        """Ensure selected workflows cover >=3 domains."""
        pass

    def test_tier_budget_prefers_simple(self):
        """Budget tier should prefer High feasibility + simple tools."""
        pass

    def test_tier_premium_tolerates_complexity(self):
        """Premium tier should accept Medium feasibility."""
        pass

    def test_selects_exactly_5(self):
        """Always returns exactly 5 workflows."""
        pass
```

**Integration Tests**: Use `real_5prompts.json` data

```python
def test_selection_on_real_data():
    """Test selection on actual generated workflows."""
    with open('data/real_5prompts.json', 'r') as f:
        data = json.load(f)

    selector = WorkflowSelector()

    # Test Budget tier
    budget_data = data['data']['Budget']['prompt_latham_&_watkins_llp']
    selected = selector.select_top_5(
        workflows=budget_data['workflows'],
        tier='Budget',
        user_prompt=budget_data['prompt'],
        consensus_strength=budget_data['consensus_strength']
    )

    assert len(selected) == 5
    # Check domain diversity
    domains = [classify_domain(wf) for wf in selected]
    assert len(set(domains)) >= 3
```

### Phase 3: Validation (Week 2)

**Manual Review**: For each tier and prompt in `real_5prompts.json`:
1. Run selector
2. Review selected 5 workflows
3. Validate:
   - ✓ Relevant to user prompt?
   - ✓ Diverse functional coverage?
   - ✓ Appropriate feasibility for tier?
   - ✓ High-impact metrics?

**Create Validation Report**: `data/selection_validation_report.md`

### Phase 4: Iteration (Week 3)

Based on validation:
- Tune scoring weights if needed
- Adjust domain diversity constraint (currently min=3)
- Refine tier multipliers

---

## Success Metrics

### Quantitative
1. **Domain Diversity**: ≥80% of selections cover 3+ different domains
2. **Feasibility Distribution**:
   - Budget: ≥70% High feasibility
   - Standard: ≥50% High feasibility
   - Premium: ≥40% High feasibility (accepts more Medium)
3. **Semantic Relevance**: Average semantic score ≥1.5 for selected workflows
4. **Metrics Coverage**: ≥80% of selected workflows have quantitative metrics

### Qualitative
1. **User Satisfaction**: "These workflows match my needs" (future user survey)
2. **Implementation Rate**: % of selected workflows users actually implement (track in future)
3. **Expert Review**: Internal team review of selections - "Would I recommend these?"

---

## Future Enhancements (Phase 5+)

### Short-Term (1-2 months)
1. **A/B Testing**: Test hybrid approach vs. Designer A alone - does semantic layer improve outcomes?
2. **Consensus Weighting**: Use consensus_strength more granularly (per-workflow consensus from generation)
3. **Metrics Parsing**: Improve extraction of complex metrics (e.g., "95% accuracy with <5% false positives")

### Medium-Term (3-6 months)
1. **Embeddings**: Replace TF-IDF with sentence-transformers for true semantic similarity
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('all-MiniLM-L6-v2')

   def semantic_similarity(prompt, workflow_text):
       embeddings = model.encode([prompt, workflow_text])
       similarity = cosine_similarity(embeddings[0], embeddings[1])
       return similarity  # 0-1 scale
   ```

2. **LLM-Assisted Relevance**: Optional AI scoring for semantic relevance
   ```python
   def llm_relevance_score(workflow, prompt):
       response = claude.complete(f"""
       User prompt: {prompt}
       Workflow: {workflow.name} - {workflow.objective}

       Rate relevance 1-10. Output only the number.
       """)
       return int(response) / 10  # Normalize to 0-1
   ```

3. **User Feedback Loop**: Track which workflows get implemented → learn preferences
   - Store: (workflow_features, user_tier, was_implemented: bool)
   - Train simple classifier to predict implementation likelihood
   - Boost selection scores for "likely to implement" workflows

### Long-Term (6-12 months)
1. **Personalization**: User history, industry, company size → personalized weights
2. **Multi-Objective Optimization**: Pareto frontier of feasibility vs. impact vs. novelty
3. **Explainable AI**: Generate natural language explanations for why each workflow was selected

---

## Risk Mitigation

### Risk 1: TF-IDF Semantic Scoring is Too Crude
**Mitigation**:
- Start with TF-IDF, validate with manual review
- If semantic scoring doesn't improve outcomes, remove it (fall back to Designer A)
- Plan upgrade path to embeddings (already documented above)

### Risk 2: Tier Differentiation Insufficient
**Mitigation**:
- Current approach uses tier-aware feasibility weights + tier multipliers
- If users complain Premium "looks like Budget", can add Designer B's innovation scoring
- Modular design allows easy addition of tier-specific components

### Risk 3: Domain Classification is Inaccurate
**Mitigation**:
- Keyword-based classification works for common domains (legal, finance, etc.)
- Manual review during validation will catch misclassifications
- Can expand keyword lists based on real workflow data
- Future: Use embeddings + clustering for automatic domain discovery

### Risk 4: Not Enough Feasible Workflows (Especially Budget)
**Mitigation**:
- Current design uses soft weighting, not hard filters (unlike Designer B)
- If Budget tier can't find 5 High feasibility workflows, will select Medium with penalty
- Backfill logic ensures 5 workflows always returned
- Monitor feasibility distribution in production → adjust generation if needed

---

## Decision Rationale Summary

**Why Not Designer A Alone?**
- Missing prompt relevance - critical gap
- Data shows 125 workflows per prompt - need relevance filter

**Why Not Designer B Alone?**
- Over-engineered (3 algorithms for marginal benefit)
- High maintenance burden
- Tier differentiation should happen in generation, not selection

**Why Not Designer C Alone?**
- TF-IDF is crude (but better than nothing)
- Diversity constraint feels bolted-on
- No clear feasibility prioritization for Budget users

**Why Hybrid?**
- Combines best of all three:
  - Designer A: Feasibility focus + domain diversity
  - Designer C: Semantic relevance + consensus awareness
  - Designer B: Tier-aware weighting (implemented simply)
- Balanced complexity (medium, not high)
- Clear evolution path (TF-IDF → embeddings → LLM-assisted)
- Modular design allows A/B testing components

---

## Conclusion

The **Hybrid "Feasibility-First with Semantic Enhancement"** approach delivers:

✅ **Prompt Relevance**: Semantic scoring ensures workflows match user needs
✅ **Implementability**: Feasibility weighting prioritizes actionable workflows
✅ **Diversity**: Domain-based selection ensures breadth of coverage
✅ **Tier Awareness**: Simple weighting differentiates without over-complexity
✅ **Impact Focus**: Max-metric approach highlights exceptional opportunities
✅ **Explainability**: Clear scoring formula, user-facing narratives
✅ **Maintainability**: Single algorithm with modular components
✅ **Evolution Path**: Can enhance with embeddings/LLM without rewrite

**Next Step**: Implement Phase 1 core functionality, validate with manual review of `real_5prompts.json` selections.

**Owner**: Development team
**Timeline**: 2-3 weeks (implementation + testing + validation)
**Success Criteria**: ≥80% of manual reviews rate selections as "relevant and valuable"
