"""
Unit tests for the Vote Counter module.
"""

import pytest

from contexts.workflow.voter import (
    count_votes,
    normalize_name,
    parse_markdown_table,
    parse_response,
)


class TestNormalizeName:
    """Tests for normalize_name function."""

    def test_lowercase(self):
        assert normalize_name("Customer Support Bot") == "customer support bot"

    def test_strip_whitespace(self):
        assert normalize_name("  Test Name  ") == "test name"

    def test_empty_string(self):
        assert normalize_name("") == ""

    def test_none_value(self):
        assert normalize_name(None) == ""


class TestParseMarkdownTable:
    """Tests for parse_markdown_table function."""

    def test_valid_table(self):
        response = """Some intro text

| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | Support Bot | Automate tickets | High volume | AI chatbot | n8n | Response time | High |
| 2 | Lead Scoring | Prioritize leads | Manual | ML model | Zapier | Conversion | Medium |

The answer is Support Bot"""

        workflows = parse_markdown_table(response)

        assert len(workflows) == 2
        assert workflows[0]["name"] == "Support Bot"
        assert workflows[1]["name"] == "Lead Scoring"

    def test_no_table(self):
        response = "This response has no table."
        workflows = parse_markdown_table(response)
        assert workflows == []

    def test_incomplete_table(self):
        response = """| # | Workflow Name |
|---|---------------|"""
        workflows = parse_markdown_table(response)
        assert workflows == []


class TestParseResponse:
    """Tests for parse_response function."""

    def test_valid_response(self):
        response = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | Support Bot | Automate tickets | High volume | AI chatbot | n8n | Response time | High |

The answer is Support Bot"""

        result = parse_response(response)

        assert result is not None
        assert result.answer == "Support Bot"
        assert len(result.workflows) == 1

    def test_no_answer(self):
        response = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | Support Bot | Automate tickets | High volume | AI chatbot | n8n | Response time | High |"""

        result = parse_response(response)
        assert result is None

    def test_empty_response(self):
        result = parse_response("")
        assert result is None

    def test_answer_with_period(self):
        response = "The answer is Customer Support Bot."
        result = parse_response(response)
        assert result is not None
        assert result.answer == "Customer Support Bot"


class TestCountVotes:
    """Tests for count_votes function."""

    def test_unanimous_consensus(self):
        responses = [
            "The answer is Support Bot",
            "The answer is Support Bot",
            "The answer is Support Bot",
        ]

        result = count_votes(responses, min_consensus_votes=2)

        assert result.final_answer == "Support Bot"  # Preserves Title Case from vote
        assert result.votes_for_winner == 3
        assert result.total_responses == 3
        assert result.confidence_percent == 100
        assert result.consensus_strength == "Strong"
        assert result.had_consensus is True

    def test_split_vote_with_consensus(self):
        responses = [
            "The answer is Support Bot",
            "The answer is Support Bot",
            "The answer is Lead Scoring",
        ]

        result = count_votes(responses, min_consensus_votes=2)

        assert result.final_answer == "Support Bot"  # Preserves Title Case from vote
        assert result.votes_for_winner == 2
        assert result.confidence_percent == 67
        assert result.consensus_strength == "Strong"
        assert result.had_consensus is True

    def test_no_consensus(self):
        responses = [
            "The answer is Support Bot",
            "The answer is Lead Scoring",
            "The answer is Report Gen",
        ]

        result = count_votes(responses, min_consensus_votes=2)

        assert result.final_answer == "No consensus"
        assert result.had_consensus is False

    def test_minimum_votes_required(self):
        responses = [
            "The answer is Support Bot",
        ]

        result = count_votes(responses, min_consensus_votes=2)

        assert result.final_answer == "No consensus"
        assert result.had_consensus is False

    def test_empty_responses(self):
        responses = []

        result = count_votes(responses, min_consensus_votes=2)

        assert result.final_answer == "No consensus"
        assert result.total_responses == 0
        assert result.had_consensus is False

    def test_moderate_consensus(self):
        responses = [
            "The answer is Support Bot",
            "The answer is Support Bot",
            "The answer is Lead Scoring",
            "The answer is Report Gen",
            "The answer is Email Triage",
        ]

        result = count_votes(responses, min_consensus_votes=2)

        assert result.final_answer == "Support Bot"  # Preserves Title Case from vote
        assert result.confidence_percent == 40
        assert result.consensus_strength == "Moderate"
