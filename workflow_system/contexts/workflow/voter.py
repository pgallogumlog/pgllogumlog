"""
Vote Counter - Self-Consistency Aggregator.

Aggregates multiple AI responses and determines consensus through voting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import structlog

from contexts.workflow.models import ConsensusResult, WorkflowRecommendation

logger = structlog.get_logger()


@dataclass
class VoteResult:
    """Result from parsing a single response."""

    answer: str
    workflows: list[dict]


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


def count_votes(
    responses: list[str],
    min_consensus_votes: int = 2,
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
    max_votes = 0
    winner_name = ""
    answers_seen: list[str] = []
    per_response_data: list[VoteResult] = []

    # Process each response
    for response in responses:
        result = parse_response(response)
        if result is None:
            continue

        answers_seen.append(result.answer)
        per_response_data.append(result)

        key = normalize_name(result.answer)
        vote_counts[key] = vote_counts.get(key, 0) + 1

        if vote_counts[key] > max_votes:
            max_votes = vote_counts[key]
            winner_name = result.answer

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

    # Get workflows from winning response (or first response as fallback)
    all_workflows: list[WorkflowRecommendation] = []
    canonical_final_answer = final_answer

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
        # Fallback: use first response's workflows
        all_workflows = _convert_workflows(per_response_data[0].workflows)

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
        fuzzy_matches=0,  # Will be updated in Phase 4
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
