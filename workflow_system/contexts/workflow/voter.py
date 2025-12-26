"""
Vote Counter - Self-Consistency Aggregator.

Aggregates multiple AI responses and determines consensus through voting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

import structlog

from contexts.workflow.models import ConsensusResult, WorkflowRecommendation

logger = structlog.get_logger()


@dataclass
class VoteResult:
    """Result from parsing a single response."""

    answer: str
    workflows: list[dict]


def fuzzy_match_score(name1: str, name2: str) -> float:
    """
    Calculate similarity score between two workflow names.

    Uses SequenceMatcher for Levenshtein-like distance comparison.

    Args:
        name1: First workflow name
        name2: Second workflow name

    Returns:
        Similarity score (0.0 to 1.0), where 1.0 is identical
    """
    if not name1 or not name2:
        return 0.0

    # Normalize both names first
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)

    if norm1 == norm2:
        return 1.0

    # Use SequenceMatcher for fuzzy comparison
    return SequenceMatcher(None, norm1, norm2).ratio()


def find_fuzzy_match(target_name: str, existing_names: list[str], threshold: float = 0.85) -> str | None:
    """
    Find the best fuzzy match for a workflow name in existing names.

    Args:
        target_name: The name to match
        existing_names: List of existing workflow names to match against
        threshold: Minimum similarity score to consider a match (default 0.85)

    Returns:
        The best matching name from existing_names, or None if no match above threshold
    """
    if not target_name or not existing_names:
        return None

    best_match = None
    best_score = 0.0

    for existing in existing_names:
        score = fuzzy_match_score(target_name, existing)
        if score > best_score:
            best_score = score
            best_match = existing

    if best_score >= threshold:
        logger.debug(
            "fuzzy_match_found",
            target=target_name,
            matched=best_match,
            score=round(best_score, 3),
        )
        return best_match

    return None


def validate_response_has_table(response: str) -> tuple[bool, str]:
    """
    Validate that a response contains a valid markdown table.

    Checks for:
    - Table header with expected columns
    - Separator row
    - At least one data row
    - "The answer is" line

    Args:
        response: Raw AI response text

    Returns:
        (is_valid, error_message) tuple
    """
    if not response:
        return False, "Empty response"

    # Check for table header marker
    if "| #" not in response or "Workflow Name" not in response:
        return False, "Missing table header (no '| #' or 'Workflow Name' found)"

    # Check for separator row (|---|---|...)
    if not re.search(r'\|[-\s]+\|[-\s]+\|', response):
        return False, "Missing table separator row"

    # Count table rows (lines starting with |)
    table_lines = [line for line in response.split('\n') if line.strip().startswith('|')]
    if len(table_lines) < 3:  # header + separator + at least 1 data row
        return False, f"Incomplete table: only {len(table_lines)} rows found (need at least 3)"

    # Check for "The answer is" line
    if not re.search(r"The answer is[:\s]", response, re.IGNORECASE):
        return False, "Missing 'The answer is' line"

    return True, ""


def normalize_name(name: str) -> str:
    """
    Normalize workflow name for voting comparison.

    Strips markdown formatting, quotes, punctuation, and normalizes case.
    This ensures votes for "**Support Bot**" and "Support Bot" are counted together.

    Handles:
    - Markdown: **bold**, *italic*, `code`
    - Quotes: "name" or 'name'
    - Brackets: [name]
    - Trailing punctuation: name. or name!
    - Multiple spaces and case normalization
    """
    if not name:
        return ""

    # Strip markdown formatting
    name = re.sub(r'\*\*(.+?)\*\*', r'\1', name)  # **bold**
    name = re.sub(r'\*(.+?)\*', r'\1', name)      # *italic*
    name = re.sub(r'`(.+?)`', r'\1', name)        # `code`

    # Strip brackets (anywhere in string)
    name = re.sub(r'\[(.+?)\]', r'\1', name)

    # Strip quotes (only at start/end)
    name = re.sub(r'^["\'](.+?)["\']$', r'\1', name)

    # Strip trailing punctuation (but preserve internal punctuation like hyphens)
    name = re.sub(r'[.,;:!?]+$', '', name)

    # Strip leading "The" or "A" or "An" (common article variations)
    name = re.sub(r'^(the|a|an)\s+', '', name, flags=re.IGNORECASE)

    # Normalize whitespace (collapse multiple spaces to single space)
    name = re.sub(r'\s+', ' ', name)

    # Normalize case
    return name.strip().lower()


def parse_response(response: str) -> VoteResult | None:
    """
    Parse a single self-consistency response.

    Extracts:
    1. The explicitly chosen answer: "The answer is <Workflow Name>"
    2. The markdown table with workflow details

    Args:
        response: Raw AI response text

    Returns:
        VoteResult with answer and parsed workflows, or None if invalid
    """
    if not response:
        logger.debug("vote_counter_empty_response")
        return None

    # Validate response has required structure before parsing
    is_valid, error_msg = validate_response_has_table(response)
    if not is_valid:
        logger.warning(
            "vote_counter_invalid_response_structure",
            error=error_msg,
            response_preview=response[:200] if response else ""
        )
        return None

    # Extract the answer: "The answer is: <Workflow Name>" or "The answer is <Workflow Name>"
    answer_match = re.search(r"The answer is[:\s]+(.+?)([.\n\r]+|$)", response, re.IGNORECASE)
    answer_name = ""
    if answer_match and answer_match.group(1):
        answer_name = answer_match.group(1).strip()

    if not answer_name:
        logger.debug("vote_counter_no_answer_found")
        return None

    # Parse markdown table if present
    workflows = parse_markdown_table(response)

    return VoteResult(answer=answer_name, workflows=workflows)


def parse_markdown_table(response: str) -> list[dict]:
    """
    Parse the markdown table from a response.

    Expected columns:
    | # | Workflow Name | Primary Objective | Problems/Opportunities |
    | How It Works | Tools/Integrations | Key Metrics | Feasibility |

    Args:
        response: Raw AI response text

    Returns:
        List of workflow dictionaries
    """
    # Find markdown table
    table_match = re.search(r"(\| *# *\|[\s\S]+?)(?:\n{2,}|\r?\n\r?\n|$)", response)
    if not table_match:
        return []

    table = table_match.group(1).strip()
    lines = [line.strip() for line in table.split("\n") if line.strip().startswith("|")]

    if len(lines) < 3:  # header + separator + at least one row
        return []

    # Skip header (lines[0]) and separator (lines[1])
    data_lines = lines[2:]
    workflows = []

    for line in data_lines:
        # Remove leading/trailing '|' then split
        cells = line.strip("|").split("|")
        cols = [c.strip() for c in cells]

        # Expect 8 columns
        if len(cols) < 8:
            continue

        workflows.append({
            "rank": cols[0],
            "name": cols[1],
            "objective": cols[2],
            "problems": cols[3],
            "how_it_works": cols[4],
            "tools": cols[5],
            "metrics": cols[6],
            "feasibility": cols[7],
        })

    return workflows


def count_votes(
    responses: list[str],
    min_consensus_votes: int = 3,
    valid_count: int = 0,
    invalid_count: int = 0,
    retry_count: int = 0,
) -> ConsensusResult:
    """
    Aggregate votes from multiple self-consistency responses.

    Args:
        responses: List of AI response strings
        min_consensus_votes: Minimum votes required for consensus

    Returns:
        ConsensusResult with final answer and statistics
    """
    vote_counts: dict[str, int] = {}
    vote_original_names: dict[str, str] = {}  # Map normalized -> first original name
    max_votes = 0
    winner_name = ""
    answers_seen: list[str] = []
    per_response_data: list[VoteResult] = []
    fuzzy_match_count = 0  # Track fuzzy matches for quality metrics

    # Process each response with fuzzy matching
    for response in responses:
        result = parse_response(response)
        if result is None:
            continue

        answers_seen.append(result.answer)
        per_response_data.append(result)

        key = normalize_name(result.answer)

        # Try fuzzy matching against existing vote keys
        existing_keys = list(vote_counts.keys())
        fuzzy_match = find_fuzzy_match(result.answer,
                                       [vote_original_names.get(k, k) for k in existing_keys],
                                       threshold=0.85)

        if fuzzy_match:
            # Found a fuzzy match - consolidate vote
            matched_key = normalize_name(fuzzy_match)
            vote_counts[matched_key] = vote_counts.get(matched_key, 0) + 1
            fuzzy_match_count += 1
            logger.debug(
                "vote_consolidated_by_fuzzy_match",
                original=result.answer,
                matched_to=fuzzy_match,
            )
        else:
            # New unique answer
            vote_counts[key] = vote_counts.get(key, 0) + 1
            vote_original_names[key] = result.answer

        # Track winner (use the key with most votes)
        for k, count in vote_counts.items():
            if count > max_votes:
                max_votes = count
                winner_name = vote_original_names.get(k, result.answer)

    # Calculate statistics
    total_responses = len(answers_seen)
    confidence_percent = 0
    consensus_strength = "Weak"

    if total_responses > 0 and max_votes > 0:
        confidence_percent = round((max_votes / total_responses) * 100)
        # Use integer percentage for cleaner threshold comparison
        if confidence_percent >= 67:
            consensus_strength = "Strong"
        elif confidence_percent >= 40:
            consensus_strength = "Moderate"

    # Determine final answer (requires minimum consensus)
    final_answer = "No consensus"
    had_consensus = False

    if max_votes >= min_consensus_votes and winner_name:
        final_answer = winner_name
        had_consensus = True
        logger.info(
            "vote_counter_consensus_reached",
            winner=winner_name,
            votes=max_votes,
            total=total_responses,
        )
    else:
        logger.warning(
            "vote_counter_no_consensus",
            max_votes=max_votes,
            total=total_responses,
            required=min_consensus_votes,
        )

    # Get workflows from winning response (or use ranked fallback)
    all_workflows: list[WorkflowRecommendation] = []
    canonical_final_answer = final_answer
    fallback_score: float | None = None

    if had_consensus:
        winner_key = normalize_name(final_answer)
        for result in per_response_data:
            if normalize_name(result.answer) == winner_key:
                all_workflows = _convert_workflows(result.workflows)
                # Use canonical name from workflow table (preserves Title Case)
                if all_workflows:
                    canonical_final_answer = all_workflows[0].name
                break
    elif per_response_data:
        # Fallback: use ranked scoring instead of just first response
        fallback_name, all_workflows = rank_workflows_by_score(per_response_data)
        canonical_final_answer = fallback_name

        # Calculate fallback score for the best workflow
        if all_workflows:
            # Get the best workflow's raw dict to score it
            best_workflow_raw = None
            for result in per_response_data:
                for wf in result.workflows:
                    if normalize_name(wf.get("name", "")) == normalize_name(fallback_name):
                        best_workflow_raw = wf
                        break
                if best_workflow_raw:
                    break

            if best_workflow_raw:
                fallback_score = score_workflow(best_workflow_raw)

        logger.info(
            "consensus_fallback_activated",
            method="ranked_scoring",
            selected_workflow=fallback_name,
            total_workflows_scored=len(all_workflows),
            fallback_score=round(fallback_score, 2) if fallback_score else None,
        )

    # Preserve original voting metrics for diagnostic logging
    original_confidence = confidence_percent
    original_strength = consensus_strength

    # Override metrics when fallback scoring is used
    if fallback_score is not None:
        # Cap fallback confidence at 85% (not from voting)
        capped_score = min(fallback_score, 85.0)
        confidence_percent = int(capped_score)

        # Update consensus strength to reflect fallback method
        if confidence_percent >= 75:
            consensus_strength = "Fallback - High Confidence"
        elif confidence_percent >= 60:
            consensus_strength = "Fallback - Medium Confidence"
        else:
            consensus_strength = "Fallback - Low Confidence"

        # Diagnostic logging to preserve voting metrics
        logger.info(
            "consensus_metrics_override",
            original_voting_confidence=original_confidence,
            original_voting_strength=original_strength,
            fallback_confidence=confidence_percent,
            fallback_strength=consensus_strength,
            raw_score=round(fallback_score, 2),
            capped_at_85=fallback_score > 85.0,
        )

    return ConsensusResult(
        final_answer=canonical_final_answer,
        total_responses=total_responses,
        votes_for_winner=max_votes,
        confidence_percent=confidence_percent,
        consensus_strength=consensus_strength,
        had_consensus=had_consensus,
        all_workflows=all_workflows,
        valid_responses=valid_count,
        invalid_responses=invalid_count,
        retried_responses=retry_count,
        fuzzy_matches=fuzzy_match_count
    )


def _convert_workflows(raw_workflows: list[dict]) -> list[WorkflowRecommendation]:
    """Convert raw workflow dicts to WorkflowRecommendation objects."""
    return [
        WorkflowRecommendation(
            name=w.get("name", ""),
            objective=w.get("objective", ""),
            tools=_parse_tools(w.get("tools", "")),
            description=w.get("how_it_works", ""),
            metrics=_parse_list(w.get("metrics", "")),
            feasibility=w.get("feasibility", ""),
        )
        for w in raw_workflows
    ]


def _parse_tools(tools_str: str) -> list[str]:
    """Parse tools string into list."""
    if isinstance(tools_str, list):
        return tools_str
    return [t.strip() for t in tools_str.split(",") if t.strip()]


def _parse_list(value: str) -> list[str]:
    """Parse comma-separated string into list."""
    if isinstance(value, list):
        return value
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def score_workflow(workflow: dict) -> float:
    """
    Score a workflow based on feasibility, impact, and complexity.

    Weighted scoring:
    - Feasibility: 40% (easier to implement = higher priority)
    - Impact/ROI: 30% (business value indicators)
    - Complexity: 30% (lower complexity = higher score)

    Args:
        workflow: Raw workflow dict with feasibility field

    Returns:
        Score from 0.0 to 100.0
    """
    score = 0.0

    # Feasibility score (40% weight)
    feasibility = workflow.get("feasibility", "").lower()
    if "high" in feasibility or "easy" in feasibility:
        score += 40.0
    elif "medium" in feasibility or "moderate" in feasibility:
        score += 25.0
    elif "low" in feasibility or "hard" in feasibility or "difficult" in feasibility:
        score += 10.0
    else:
        score += 20.0  # Default if unclear

    # Impact/ROI score (30% weight)
    # Higher impact keywords in objective or problems
    objective = workflow.get("objective", "").lower()
    problems = workflow.get("problems", "").lower()

    high_impact_keywords = ["critical", "major", "significant", "revenue", "cost savings", "efficiency"]
    medium_impact_keywords = ["important", "helpful", "useful", "improve"]

    impact_text = f"{objective} {problems}"
    if any(keyword in impact_text for keyword in high_impact_keywords):
        score += 30.0
    elif any(keyword in impact_text for keyword in medium_impact_keywords):
        score += 20.0
    else:
        score += 15.0  # Default

    # Complexity score (30% weight) - simpler is better
    how_it_works = workflow.get("how_it_works", "").lower()
    tools = workflow.get("tools", "").lower()

    # Complex indicators
    complex_keywords = ["custom", "complex", "advanced", "integration", "multiple systems"]
    simple_keywords = ["simple", "straightforward", "existing", "standard", "template"]

    complexity_text = f"{how_it_works} {tools}"
    if any(keyword in complexity_text for keyword in simple_keywords):
        score += 30.0
    elif any(keyword in complexity_text for keyword in complex_keywords):
        score += 10.0
    else:
        score += 20.0  # Default

    return score


def rank_workflows_by_score(all_responses_data: list[VoteResult]) -> tuple[str, list[WorkflowRecommendation]]:
    """
    Rank all workflows from all responses by weighted score.

    Used as fallback when consensus voting fails.

    Args:
        all_responses_data: List of VoteResult objects from all responses

    Returns:
        Tuple of (best_workflow_name, all_workflows_sorted)
    """
    if not all_responses_data:
        return "No consensus", []

    # Collect all workflows from all responses
    scored_workflows: list[tuple[float, dict]] = []

    for result in all_responses_data:
        for workflow in result.workflows:
            score = score_workflow(workflow)
            scored_workflows.append((score, workflow))

    # Sort by score descending
    scored_workflows.sort(key=lambda x: x[0], reverse=True)

    if not scored_workflows:
        return "No consensus", []

    # Get best workflow name
    best_workflow = scored_workflows[0][1]
    best_name = best_workflow.get("name", "No consensus")

    # Convert all workflows to WorkflowRecommendation objects
    all_workflows = _convert_workflows([w for _, w in scored_workflows])

    logger.info(
        "fallback_ranked_scoring",
        best_workflow=best_name,
        best_score=round(scored_workflows[0][0], 2),
        total_workflows=len(scored_workflows),
    )

    return best_name, all_workflows
