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
    normalized_prompt: str | None = None,
) -> ConsensusResult:
    """
    Aggregate votes from multiple self-consistency responses.

    Args:
        responses: List of AI response strings
        min_consensus_votes: Minimum votes required for consensus
        valid_count: Number of valid responses
        invalid_count: Number of invalid responses
        retry_count: Number of retried responses
        normalized_prompt: Optional normalized prompt for semantic relevance in fallback.
                          Typically the normalized/rewritten prompt from the input rewriter.
                          Used to boost workflows that match the user's question.

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
    raw_workflows: list[WorkflowRecommendation] = []  # Store all workflows before deduplication
    canonical_final_answer = final_answer
    fallback_score: float | None = None

    if had_consensus:
        # Collect ALL workflows from ALL responses (e.g., 5 temps × 25 workflows = 125 total)
        all_raw_workflows: list[dict] = []
        for result in per_response_data:
            all_raw_workflows.extend(result.workflows)

        # Convert ALL raw workflows to WorkflowRecommendation objects (for data analysis)
        raw_workflows = _convert_workflows(all_raw_workflows)

        # Rank all workflows by vote count and select top 5
        top_workflows_raw = select_top_workflows_by_votes(
            all_workflows=all_raw_workflows,
            per_response_data=per_response_data,
            vote_counts=vote_counts,
            top_n=5,
            normalized_prompt=normalized_prompt,
        )

        # Convert to WorkflowRecommendation objects
        all_workflows = _convert_workflows(top_workflows_raw)

        # Use canonical name from top workflow (preserves Title Case)
        if all_workflows:
            canonical_final_answer = all_workflows[0].name
    elif per_response_data:
        # Fallback: use ranked scoring instead of just first response
        fallback_name, all_workflows = rank_workflows_by_score(per_response_data, normalized_prompt)
        canonical_final_answer = fallback_name

        # Collect ALL raw workflows for fallback mode too
        all_raw_workflows_fallback: list[dict] = []
        for result in per_response_data:
            all_raw_workflows_fallback.extend(result.workflows)
        raw_workflows = _convert_workflows(all_raw_workflows_fallback)

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
                fallback_score = score_workflow(best_workflow_raw, normalized_prompt)

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
        fuzzy_matches=fuzzy_match_count,
        raw_workflows=raw_workflows  # All 25 workflows before deduplication
    )


def select_top_workflows_by_votes(
    all_workflows: list[dict],
    per_response_data: list[VoteResult],
    vote_counts: dict[str, int],
    top_n: int = 5,
    normalized_prompt: str | None = None,
) -> list[dict]:
    """
    Select top N workflows by vote count across all responses.

    Used when consensus is reached to rank all workflows from all temperature
    responses by their vote counts and return the top N.

    Args:
        all_workflows: All workflow dicts from all responses (e.g., 125 workflows from 5×25)
        per_response_data: List of VoteResult objects from all responses
        vote_counts: Dictionary mapping normalized workflow names to vote counts
        top_n: Number of top workflows to return (default 5)

    Returns:
        List of top N workflow dicts ranked by vote count (descending)
    """
    if not all_workflows:
        return []

    # Build mapping: workflow dict → vote count
    workflow_vote_map: list[tuple[int, dict]] = []

    for workflow in all_workflows:
        workflow_name = workflow.get("name", "")
        if not workflow_name:
            continue

        # Find vote count for this workflow using normalized name
        # Use only exact normalized match (no fuzzy matching here to avoid false positives)
        # Fuzzy matching already happened in count_votes() when building vote_counts
        normalized_name = normalize_name(workflow_name)
        votes = vote_counts.get(normalized_name, 0)

        workflow_vote_map.append((votes, workflow))

    # Calculate scores for all workflows to enable tiebreaking
    # Includes semantic relevance scoring when normalized_prompt is provided
    # This ensures workflows are ranked by: (1) votes, (2) quality+relevance, (3) name
    workflow_score_map: list[tuple[int, float, dict]] = []
    for votes, workflow in workflow_vote_map:
        score = score_workflow(workflow, normalized_prompt=normalized_prompt)
        workflow_score_map.append((votes, score, workflow))

    # Sort by: (1) Vote count DESC, (2) Score DESC, (3) Name alphabetically
    # This ensures deterministic ordering with quality-based tiebreaking
    workflow_score_map.sort(
        key=lambda x: (-x[0], -x[1], x[2].get("name", ""))
    )

    # Select top N DISTINCT workflows (deduplication using normalized name matching)
    selected_workflows: list[dict] = []
    selected_normalized_names: set[str] = set()
    duplicate_count = 0

    for votes, score, workflow in workflow_score_map:
        if len(selected_workflows) >= top_n:
            break

        workflow_name = workflow.get("name", "")
        if not workflow_name:
            continue

        # Use normalized name for exact deduplication
        # This handles "Email Automation" vs "**Email Automation**" as duplicates
        # but keeps "Workflow 1" and "Workflow 10" as distinct
        normalized_name = normalize_name(workflow_name)

        if normalized_name in selected_normalized_names:
            # Skip duplicate workflow
            duplicate_count += 1
            logger.debug(
                "workflow_duplicate_skipped",
                duplicate=workflow_name,
                normalized=normalized_name,
                votes=votes,
                score=round(score, 2),
            )
            continue

        # This is a unique workflow - add it
        selected_workflows.append(workflow)
        selected_normalized_names.add(normalized_name)

    # Update logging to reflect new behavior
    logger.info(
        "select_top_workflows_by_votes",
        total_workflows=len(all_workflows),
        top_n=top_n,
        selected_unique=len(selected_workflows),
        duplicates_skipped=duplicate_count,
        top_workflow=selected_workflows[0].get("name") if selected_workflows else None,
        top_votes=workflow_score_map[0][0] if workflow_score_map else 0,
        top_score=round(workflow_score_map[0][1], 2) if workflow_score_map else 0.0,
    )

    return selected_workflows


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


def _calculate_semantic_relevance(prompt: str, workflow_text: str) -> float:
    """
    Calculate semantic relevance between user's prompt and workflow.

    Uses keyword overlap with stopword filtering.

    Args:
        prompt: User's original question
        workflow_text: Workflow name + objective + problems combined

    Returns:
        Relevance score from 0.0 to 1.0
    """
    # Validate inputs - type and emptiness
    if not isinstance(prompt, str) or not isinstance(workflow_text, str):
        logger.warning(
            "semantic_relevance_invalid_input_type",
            prompt_type=type(prompt).__name__,
            workflow_text_type=type(workflow_text).__name__,
        )
        return 0.0

    # Handle empty or whitespace-only inputs
    if not prompt.strip() or not workflow_text.strip():
        return 0.0

    # Common stopwords to ignore
    stopwords = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "can", "i", "you", "we",
        "they", "them", "their", "this", "that", "these", "those", "what",
        "which", "who", "when", "where", "why", "how", "need", "help", "want",
    }

    # Extract keywords from prompt (normalize and filter stopwords)
    prompt_lower = prompt.lower()
    prompt_words = set(
        word.strip(".,!?;:()[]{}\"'")
        for word in prompt_lower.split()
        if len(word) > 2 and word not in stopwords
    )

    # Extract keywords from workflow text
    workflow_lower = workflow_text.lower()
    workflow_words = set(
        word.strip(".,!?;:()[]{}\"'")
        for word in workflow_lower.split()
        if len(word) > 2 and word not in stopwords
    )

    if not prompt_words:
        return 0.0

    # Calculate overlap ratio (Jaccard similarity)
    intersection = prompt_words & workflow_words
    union = prompt_words | workflow_words

    if not union:
        return 0.0

    jaccard = len(intersection) / len(union)

    # Also calculate what percentage of prompt keywords are found
    coverage = len(intersection) / len(prompt_words)

    # Blend both metrics (favor coverage - did we address the question?)
    relevance = (jaccard * 0.3) + (coverage * 0.7)

    return min(relevance, 1.0)


def score_workflow(workflow: dict, normalized_prompt: str | None = None) -> float:
    """
    Score a workflow based on feasibility, impact, complexity, and semantic relevance.

    Weighted scoring (when semantic relevance is used):
    - Feasibility: 35% (easier to implement = higher priority)
    - Impact/ROI: 25% (business value indicators)
    - Complexity: 20% (lower complexity = higher score)
    - Semantic Relevance: 20% (matches user's question)

    Weighted scoring (when no prompt provided):
    - Feasibility: 40%
    - Impact/ROI: 30%
    - Complexity: 30%

    Args:
        workflow: Raw workflow dict with feasibility field
        normalized_prompt: Optional normalized prompt for semantic matching.
                          Typically the normalized prompt from the input rewriter.
                          Used to boost workflows that address the user's question.

    Returns:
        Score from 0.0 to 100.0
    """
    score = 0.0

    # Check if semantic relevance will be used
    use_semantic = normalized_prompt and normalized_prompt.strip()

    # Adjust weights based on whether semantic relevance is used
    if use_semantic:
        feasibility_high, feasibility_med, feasibility_low, feasibility_default = 35.0, 22.0, 9.0, 17.0
        impact_high, impact_med, impact_default = 25.0, 17.0, 12.0
        complexity_simple, complexity_complex, complexity_default = 20.0, 7.0, 13.0
    else:
        # Original weights (sum to 100%)
        feasibility_high, feasibility_med, feasibility_low, feasibility_default = 40.0, 25.0, 10.0, 20.0
        impact_high, impact_med, impact_default = 30.0, 20.0, 15.0
        complexity_simple, complexity_complex, complexity_default = 30.0, 10.0, 20.0

    # Feasibility score
    feasibility = workflow.get("feasibility", "").lower()
    if "high" in feasibility or "easy" in feasibility:
        score += feasibility_high
    elif "medium" in feasibility or "moderate" in feasibility:
        score += feasibility_med
    elif "low" in feasibility or "hard" in feasibility or "difficult" in feasibility:
        score += feasibility_low
    else:
        score += feasibility_default

    # Impact/ROI score
    objective = workflow.get("objective", "").lower()
    problems = workflow.get("problems", "").lower()

    high_impact_keywords = ["critical", "major", "significant", "revenue", "cost savings", "efficiency"]
    medium_impact_keywords = ["important", "helpful", "useful", "improve"]

    impact_text = f"{objective} {problems}"
    if any(keyword in impact_text for keyword in high_impact_keywords):
        score += impact_high
    elif any(keyword in impact_text for keyword in medium_impact_keywords):
        score += impact_med
    else:
        score += impact_default

    # Complexity score - simpler is better
    how_it_works = workflow.get("how_it_works", "").lower()
    tools = workflow.get("tools", "").lower()

    complex_keywords = ["custom", "complex", "advanced", "integration", "multiple systems"]
    simple_keywords = ["simple", "straightforward", "existing", "standard", "template"]

    complexity_text = f"{how_it_works} {tools}"
    if any(keyword in complexity_text for keyword in simple_keywords):
        score += complexity_simple
    elif any(keyword in complexity_text for keyword in complex_keywords):
        score += complexity_complex
    else:
        score += complexity_default

    # Semantic Relevance score (20% weight) - only if normalized_prompt provided
    if use_semantic:
        relevance_score = _calculate_semantic_relevance(
            prompt=normalized_prompt,
            workflow_text=f"{workflow.get('name', '')} {objective} {problems}",
        )
        score += relevance_score * 20.0  # Scale 0-1 to 0-20 points

    return score


def rank_workflows_by_score(
    all_responses_data: list[VoteResult],
    normalized_prompt: str | None = None,
) -> tuple[str, list[WorkflowRecommendation]]:
    """
    Rank all workflows from all responses by weighted score.

    Used as fallback when consensus voting fails.

    Args:
        all_responses_data: List of VoteResult objects from all responses
        normalized_prompt: Optional normalized prompt for semantic relevance.
                          Typically the normalized prompt from the input rewriter.

    Returns:
        Tuple of (best_workflow_name, all_workflows_sorted)
    """
    if not all_responses_data:
        return "No consensus", []

    # Collect all workflows from all responses
    scored_workflows: list[tuple[float, dict]] = []

    for result in all_responses_data:
        for workflow in result.workflows:
            score = score_workflow(workflow, normalized_prompt)
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
        semantic_matching=normalized_prompt is not None,
    )

    return best_name, all_workflows
