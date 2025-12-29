"""
Workflow selection module using hybrid feasibility-first with semantic enhancement.

This module implements the hybrid workflow selection algorithm that combines:
- Semantic relevance (TF-IDF keyword matching)
- Feasibility weighting (tier-aware)
- Metrics impact extraction
- Tool practicality scoring
- Domain diversity enforcement
"""

import re
import math
from collections import Counter
from typing import Dict, List, Set

from .models import WorkflowRecommendation
from .voter import normalize_name


class WorkflowSelector:
    """Selects top 5 workflows from generated candidates using hybrid scoring approach."""

    # Domain classification keywords
    DOMAIN_KEYWORDS = {
        'data_processing': ['classify', 'extract', 'parse', 'nlp', 'ocr', 'document'],
        'compliance_risk': ['compliance', 'regulatory', 'audit', 'risk', 'legal'],
        'communication': ['email', 'notification', 'report', 'dashboard', 'alert'],
        'analytics': ['analytics', 'insight', 'predict', 'forecast', 'intelligence'],
        'workflow_mgmt': ['orchestr', 'track', 'coordinate', 'manage', 'monitor'],
        'integration': ['integration', 'sync', 'connect', 'api', 'bridge']
    }

    # English stopwords for keyword extraction
    STOPWORDS = {
        'the', 'and', 'or', 'for', 'with', 'to', 'of', 'in', 'a', 'an',
        'is', 'at', 'by', 'on', 'be', 'as', 'it', 'this', 'that', 'are',
        'was', 'were', 'been', 'have', 'has', 'had', 'from', 'but', 'not'
    }

    def __init__(self):
        """Initialize the workflow selector."""
        pass

    def select_top_5(
        self,
        workflows: List[WorkflowRecommendation],
        tier: str,
        user_prompt: str,
        consensus_strength: str = "Moderate"
    ) -> List[WorkflowRecommendation]:
        """
        Select top 5 workflows using hybrid scoring approach.

        Args:
            workflows: List of workflow recommendations (typically ~125 from generation)
            tier: Subscription tier ("Budget" | "Standard" | "Premium")
            user_prompt: Original user request/prompt
            consensus_strength: Consensus strength from generation ("Strong" | "Moderate" | "Weak")

        Returns:
            List of exactly 5 selected workflow recommendations
        """
        if not workflows:
            return []

        if len(workflows) <= 5:
            return workflows[:5]

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
        }.get(tier, 1.0)

        # Score all workflows
        scored = []

        for wf in workflows:
            # Component scores
            semantic = self.calculate_semantic_relevance(wf, user_prompt)
            feasibility = self.get_feasibility_weight(wf.feasibility, tier)
            impact = self.calculate_metrics_impact(wf.metrics)
            tools = self.calculate_tool_practicality(wf.tools, tier)

            # Base score (without domain bonus yet)
            base_score = semantic * feasibility * impact * tools * consensus_bonus * tier_multiplier

            scored.append({
                'workflow': wf,
                'score': base_score,
                'domain': self.classify_domain(wf),
                'semantic': semantic  # Store for relevance filtering
            })

        # Sort by score (descending)
        scored.sort(key=lambda x: x['score'], reverse=True)

        # Greedy selection with domain diversity
        selected = []
        domains_covered: Set[str] = set()
        selected_normalized_names: Set[str] = set()  # Track workflow names to prevent duplicates

        # Only apply semantic floor during fallback mode (weak consensus)
        # When we have strong/moderate consensus, voting already validated relevance
        # When we have weak consensus (fallback scoring), use semantic floor to filter irrelevant workflows
        apply_semantic_floor = len(workflows) >= 50 and consensus_strength == "Weak"

        for item in scored:
            if len(selected) >= 5:
                break

            # Skip workflows with low semantic relevance when we have plenty to choose from
            # (< 0.65 indicates weak keyword overlap with user prompt)
            # Note: 0.5 is baseline (no overlap), 3.0 is max (high overlap)
            # Threshold filters workflows with minimal relevance to user's specific need
            if apply_semantic_floor and item['semantic'] < 0.65:
                continue

            # Skip duplicate workflows (same name already selected)
            workflow_name = item['workflow'].name
            normalized_name = normalize_name(workflow_name)
            if normalized_name in selected_normalized_names:
                continue

            domain = item['domain']

            # First workflow: always take highest score
            if len(selected) == 0:
                selected.append(item)
                domains_covered.add(domain)
                selected_normalized_names.add(normalized_name)
                continue

            # Prefer uncovered domains
            if domain not in domains_covered:
                # Apply diversity bonus
                item['score'] *= 1.5
                selected.append(item)
                domains_covered.add(domain)
                selected_normalized_names.add(normalized_name)
            else:
                # Allow duplicate domain if score is significantly higher
                # OR we've met diversity target (3 domains)
                if len(selected) > 0 and (item['score'] > selected[-1]['score'] * 1.3 or len(domains_covered) >= 3):
                    selected.append(item)
                    selected_normalized_names.add(normalized_name)

        # Backfill if needed (shouldn't happen with many workflows, but safety check)
        if len(selected) < 5:
            for item in scored:
                if len(selected) >= 5:
                    break

                # Check normalized name to prevent duplicates (not object identity)
                workflow_name = item['workflow'].name
                normalized_name = normalize_name(workflow_name)

                # Skip if already selected or fails semantic floor
                if normalized_name in selected_normalized_names:
                    continue
                if apply_semantic_floor and item['semantic'] < 0.65:
                    continue

                # Add workflow to backfill
                selected.append(item)
                selected_normalized_names.add(normalized_name)

        return [s['workflow'] for s in selected[:5]]

    def extract_keywords(self, text: str) -> Dict[str, float]:
        """
        Extract weighted keywords from text using TF-IDF style weighting.

        Args:
            text: Input text to extract keywords from

        Returns:
            Dictionary mapping keywords to their weighted scores
        """
        if not text:
            return {}

        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in self.STOPWORDS and len(w) > 3]

        # Count frequencies
        freq = Counter(keywords)

        # Weight by log frequency (simple TF)
        weighted = {term: math.log(1 + count) for term, count in freq.items()}

        return weighted

    def calculate_semantic_relevance(
        self,
        workflow: WorkflowRecommendation,
        user_prompt: str
    ) -> float:
        """
        Measure workflow relevance to user prompt using keyword overlap.

        Args:
            workflow: Workflow recommendation to score
            user_prompt: Original user request

        Returns:
            Semantic relevance score in range [0.5, 3.0]
        """
        prompt_kw = self.extract_keywords(user_prompt)
        wf_text = f"{workflow.name} {workflow.objective} {workflow.description}"
        wf_kw = self.extract_keywords(wf_text)

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

    def get_feasibility_weight(self, feasibility: str, tier: str) -> float:
        """
        Get feasibility weight with tier sensitivity.

        Args:
            feasibility: Feasibility level ("High" | "Medium" | "Low")
            tier: Subscription tier

        Returns:
            Feasibility weight multiplier
        """
        base = {
            "High": 1.0,
            "Medium": 0.75,
            "Low": 0.3
        }

        weight = base.get(feasibility, 0.75)

        # Tier adjustments
        if feasibility == "Medium":
            if tier == "Budget":
                weight = 0.6  # Budget users need higher certainty
            elif tier == "Premium":
                weight = 0.9  # Premium users tolerate complexity

        return weight

    def calculate_metrics_impact(self, metrics: List[str]) -> float:
        """
        Extract max impact from metrics list.

        Args:
            metrics: List of metric strings (e.g., "95% accuracy", "3x faster")

        Returns:
            Impact score in range [1.0, 5.0]
        """
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

    def calculate_tool_practicality(self, tools: List[str], tier: str) -> float:
        """
        Score based on tool count and tier-appropriateness.

        Args:
            tools: List of tools required for workflow
            tier: Subscription tier

        Returns:
            Tool practicality score in range [0.7, 1.2]
        """
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

    def classify_domain(self, workflow: WorkflowRecommendation) -> str:
        """
        Classify workflow into functional domain.

        Args:
            workflow: Workflow recommendation to classify

        Returns:
            Domain name (e.g., 'data_processing', 'compliance_risk', 'other')
        """
        text = f"{workflow.name} {workflow.objective} {workflow.description}".lower()

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return domain

        return 'other'
