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


def validate_response_has_table(response: str) -> tuple[bool, str]:
    """
    Validate that a response contains a valid markdown table.

    Checks for:
    - Table header with expected columns
    - Separator row
    - At least one data row

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

    # Extract the answer: "The answer is <Workflow Name>"
    answer_match = re.search(r"The answer is\s+(.+?)([.\n\r]+|$)", response, re.IGNORECASE)
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


def _score_feasibility(feasibility: str) -> float:
    """Score feasibility from workflow data (0-100)."""
    feasibility_lower = feasibility.lower().strip()
    if "high" in feasibility_lower or "easy" in feasibility_lower:
        return 100.0
    elif "medium" in feasibility_lower or "moderate" in feasibility_lower:
        return 60.0
    elif "low" in feasibility_lower or "hard" in feasibility_lower or "difficult" in feasibility_lower:
        return 30.0
    return 50.0  # Default if unclear


def _score_roi_potential(objective: str, problems: str) -> float:
    """Score ROI potential based on objective and problems (0-100)."""
    # Higher score for automation, efficiency, cost reduction keywords
    text = (objective + " " + problems).lower()
    score = 50.0  # Base score

    # High ROI indicators
    if any(word in text for word in ["automate", "automation", "eliminate", "reduce cost"]):
        score += 20
    if any(word in text for word in ["revenue", "growth", "sales", "conversion"]):
        score += 15
    if any(word in text for word in ["efficiency", "productivity", "save time"]):
        score += 10
    if any(word in text for word in ["scale", "scalable", "high volume"]):
        score += 5

    return min(score, 100.0)


def _score_implementation_complexity(tools: str, how_it_works: str) -> float:
    """Score implementation complexity - lower complexity = higher score (0-100)."""
    text = (tools + " " + how_it_works).lower()
    score = 70.0  # Base score (moderate complexity)

    # Low complexity indicators (increase score)
    if any(tool in text for tool in ["n8n", "zapier", "make", "airtable"]):
        score += 15  # No-code tools are easier
    if "api" in text and "custom" not in text:
        score += 10  # Standard APIs easier than custom

    # High complexity indicators (decrease score)
    if any(word in text for word in ["custom", "build", "develop", "train model"]):
        score -= 20
    if any(word in text for word in ["ml", "machine learning", "ai model", "nlp"]):
        score -= 15
    if "integration" in text and "multiple" in text:
        score -= 10

    return max(min(score, 100.0), 0.0)


def rank_workflows_by_criteria(workflows: list[WorkflowRecommendation]) -> WorkflowRecommendation:
    """
    Rank workflows using weighted criteria when consensus fails.

    Criteria weights:
    - Feasibility: 40%
    - ROI potential: 30%
    - Implementation complexity: 30%

    Args:
        workflows: List of workflow recommendations

    Returns:
        Top-ranked workflow
    """
    if not workflows:
        raise ValueError("Cannot rank empty workflow list")

    scored_workflows = []

    for wf in workflows:
        # Score each criterion (0-100)
        feasibility_score = _score_feasibility(wf.feasibility)
        roi_score = _score_roi_potential(wf.objective, wf.description)
        complexity_score = _score_implementation_complexity(
            ", ".join(wf.tools) if isinstance(wf.tools, list) else str(wf.tools),
            wf.description
        )

        # Weighted total
        total_score = (
            feasibility_score * 0.40 +
            roi_score * 0.30 +
            complexity_score * 0.30
        )

        scored_workflows.append((total_score, wf))

        logger.debug(
            "workflow_scored",
            name=wf.name,
            feasibility=feasibility_score,
            roi=roi_score,
            complexity=complexity_score,
            total=round(total_score, 2),
        )

    # Sort by score descending
    scored_workflows.sort(key=lambda x: x[0], reverse=True)

    top_workflow = scored_workflows[0][1]
    top_score = scored_workflows[0][0]

    logger.info(
        "workflow_ranked_selection",
        winner=top_workflow.name,
        score=round(top_score, 2),
    )

    return top_workflow


def count_votes(
    responses: list[str],
    min_consensus_votes: int = 3,
    min_consensus_percent: int = 60,
    valid_count: int = 0,
    invalid_count: int = 0,
    retry_count: int = 0,
) -> ConsensusResult:
    """
    Aggregate votes from multiple self-consistency responses.

    Args:
        responses: List of AI response strings
        min_consensus_votes: Minimum votes required for consensus (default 3)
        min_consensus_percent: Minimum percentage required for consensus (default 60)

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

    # Get workflows from winning response (or first response as fallback)
    # We need this before consensus check for winner validation
    # CRITICAL: Also collect ALL workflows from ALL responses for comprehensive fallback
    all_workflows: list[WorkflowRecommendation] = []
    all_workflows_comprehensive: list[WorkflowRecommendation] = []
    winner_key = normalize_name(winner_name) if winner_name else ""

    # Collect ALL workflows from ALL responses (up to 25 workflows total)
    for result in per_response_data:
        all_workflows_comprehensive.extend(_convert_workflows(result.workflows))

    # Get winner's workflows for consensus validation
    if winner_key:
        for result in per_response_data:
            if normalize_name(result.answer) == winner_key:
                all_workflows = _convert_workflows(result.workflows)
                break

    if not all_workflows and per_response_data:
        # Fallback: use first response's workflows for validation
        all_workflows = _convert_workflows(per_response_data[0].workflows)

    # DEBUG: Log workflow count before consensus logic
    logger.info(
        "vote_counter_workflows_extracted",
        workflow_count=len(all_workflows),
        total_responses=len(per_response_data),
        winner_name=winner_name,
    )

    # Determine final answer (requires dual threshold: votes AND percent)
    final_answer = "No consensus"
    had_consensus = False

    # Check dual threshold
    meets_vote_threshold = max_votes >= min_consensus_votes
    meets_percent_threshold = confidence_percent >= min_consensus_percent

    # CRITICAL: Check if we have workflows to validate against
    if not all_workflows:
        logger.error(
            "vote_counter_no_workflows_parsed",
            winner_name=winner_name,
            votes=max_votes,
            total_responses=len(per_response_data),
            message="Cannot validate consensus - no workflows were parsed from responses. AI may have skipped markdown table.",
        )
        # Force consensus to fail - cannot validate without workflow data
        meets_vote_threshold = False

    if meets_vote_threshold and meets_percent_threshold and winner_name:
        # Validate winner exists in parsed workflows and get the canonical name
        canonical_name = None
        for w in all_workflows:
            if normalize_name(w.name) == winner_key:
                canonical_name = w.name
                break

        if canonical_name:
            final_answer = canonical_name  # Use the name from the workflow table (proper capitalization)
            had_consensus = True
            logger.info(
                "vote_counter_consensus_reached",
                winner=canonical_name,
                votes=max_votes,
                total=total_responses,
                confidence=confidence_percent,
            )
        else:
            logger.warning(
                "vote_counter_winner_not_in_workflows",
                winner=winner_name,
                workflow_names=[w.name for w in all_workflows[:5]],
            )
    else:
        logger.warning(
            "vote_counter_no_consensus",
            max_votes=max_votes,
            total=total_responses,
            confidence=confidence_percent,
            required_votes=min_consensus_votes,
            required_percent=min_consensus_percent,
            meets_vote_threshold=meets_vote_threshold,
            meets_percent_threshold=meets_percent_threshold,
        )

    # Phase 3: Ranked Fallback when consensus fails
    fallback_mode = False
    confidence_warning = ""
    selection_method = "consensus"

    # DEBUG: Log fallback decision point
    logger.info(
        "vote_counter_fallback_decision",
        had_consensus=had_consensus,
        workflow_count=len(all_workflows),
        comprehensive_workflow_count=len(all_workflows_comprehensive),
        will_use_fallback=not had_consensus and len(all_workflows_comprehensive) > 0,
    )

    if not had_consensus and all_workflows_comprehensive:
        # Use ranked selection as fallback - score ALL workflows from ALL responses
        try:
            top_workflow = rank_workflows_by_criteria(all_workflows_comprehensive)
            final_answer = top_workflow.name
            fallback_mode = True
            selection_method = "ranked_fallback"
            confidence_warning = (
                f"Consensus voting failed ({confidence_percent}% confidence, {max_votes}/{total_responses} votes). "
                f"Selected '{final_answer}' using weighted criteria (Feasibility 40%, ROI 30%, Complexity 30%) "
                f"across all {len(all_workflows_comprehensive)} workflows from {total_responses} responses. "
                f"Recommend manual review before implementation."
            )
            logger.info(
                "vote_counter_fallback_used",
                selected_workflow=final_answer,
                confidence=confidence_percent,
                votes=max_votes,
                total=total_responses,
                workflows_scored=len(all_workflows_comprehensive),
            )
        except Exception as e:
            logger.error(
                "vote_counter_fallback_failed",
                error=str(e),
                workflow_count=len(all_workflows_comprehensive),
                error_type=type(e).__name__,
            )
            # Keep "No consensus" as final_answer

    # DEBUG: Log final result
    logger.info(
        "vote_counter_final_result",
        final_answer=final_answer,
        had_consensus=had_consensus,
        fallback_mode=fallback_mode,
        selection_method=selection_method,
        workflow_count=len(all_workflows),
    )

    return ConsensusResult(
        final_answer=final_answer,  # Already has proper capitalization from workflow table
        total_responses=total_responses,
        votes_for_winner=max_votes,
        confidence_percent=confidence_percent,
        consensus_strength=consensus_strength,
        had_consensus=had_consensus,
        all_workflows=all_workflows,
        fallback_mode=fallback_mode,
        confidence_warning=confidence_warning,
        selection_method=selection_method,
        # Phase C: Quality metrics
        valid_responses=valid_count,
        invalid_responses=invalid_count,
        retried_responses=retry_count,
        fuzzy_matches=fuzzy_match_count,
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
