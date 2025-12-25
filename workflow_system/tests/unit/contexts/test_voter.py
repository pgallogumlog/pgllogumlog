"""
Unit tests for the Vote Counter module.
"""

import pytest

from contexts.workflow.voter import (
    count_votes,
    fuzzy_match_score,
    find_fuzzy_match,
    normalize_name,
    parse_markdown_table,
    parse_response,
    validate_response_has_table,
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

    def test_strip_bold_markdown(self):
        """Test stripping **bold** markdown formatting."""
        assert normalize_name("**Support Bot**") == "support bot"

    def test_strip_italic_markdown(self):
        """Test stripping *italic* markdown formatting."""
        assert normalize_name("*Support Bot*") == "support bot"

    def test_strip_code_markdown(self):
        """Test stripping `code` markdown formatting."""
        assert normalize_name("`Support Bot`") == "support bot"

    def test_strip_quotes(self):
        """Test stripping quotes from names."""
        assert normalize_name('"Support Bot"') == "support bot"
        assert normalize_name("'Support Bot'") == "support bot"

    def test_strip_trailing_punctuation(self):
        """Test stripping trailing punctuation."""
        assert normalize_name("Support Bot.") == "support bot"
        assert normalize_name("Support Bot!") == "support bot"
        assert normalize_name("Support Bot?") == "support bot"

    def test_combined_formatting(self):
        """Test stripping multiple formatting elements."""
        assert normalize_name("**Support Bot**.") == "support bot"
        assert normalize_name('"*Lead Scoring*"') == "lead scoring"

    def test_strip_brackets(self):
        """Test stripping square brackets."""
        assert normalize_name("[Support Bot]") == "support bot"
        assert normalize_name("[Lead Scoring System]") == "lead scoring system"

    def test_strip_articles(self):
        """Test stripping leading articles."""
        assert normalize_name("The Support Bot") == "support bot"
        assert normalize_name("A Lead Scoring System") == "lead scoring system"
        assert normalize_name("An Email Automation") == "email automation"

    def test_multiple_spaces(self):
        """Test collapsing multiple spaces."""
        assert normalize_name("Support  Bot") == "support bot"
        assert normalize_name("Lead   Scoring   System") == "lead scoring system"

    def test_comprehensive_normalization(self):
        """Test all normalization features together."""
        assert normalize_name("The **[Support Bot]**.") == "support bot"
        assert normalize_name('"A  Lead  Scoring  System"') == "lead scoring system"


class TestFuzzyMatching:
    """Tests for fuzzy matching functions."""

    def test_fuzzy_match_score_identical(self):
        """Test fuzzy match score for identical names."""
        assert fuzzy_match_score("Support Bot", "Support Bot") == 1.0

    def test_fuzzy_match_score_different_case(self):
        """Test fuzzy match score ignores case."""
        score = fuzzy_match_score("Support Bot", "SUPPORT BOT")
        assert score == 1.0

    def test_fuzzy_match_score_similar(self):
        """Test fuzzy match score for similar names."""
        score = fuzzy_match_score("Lead Scoring", "Lead Scorer")
        assert score > 0.75  # Should be reasonably high similarity

    def test_fuzzy_match_score_very_different(self):
        """Test fuzzy match score for very different names."""
        score = fuzzy_match_score("Lead Scoring", "Email Automation")
        assert score < 0.5  # Should be low similarity

    def test_fuzzy_match_score_empty_strings(self):
        """Test fuzzy match score with empty strings."""
        assert fuzzy_match_score("", "Support Bot") == 0.0
        assert fuzzy_match_score("Support Bot", "") == 0.0
        assert fuzzy_match_score("", "") == 0.0

    def test_find_fuzzy_match_exact(self):
        """Test finding exact fuzzy match."""
        existing = ["Support Bot", "Lead Scoring", "Email Automation"]
        match = find_fuzzy_match("Support Bot", existing)
        assert match == "Support Bot"

    def test_find_fuzzy_match_similar(self):
        """Test finding similar fuzzy match."""
        existing = ["Lead Scoring System", "Email Automation", "Support Bot"]
        match = find_fuzzy_match("Lead Scoring", existing, threshold=0.70)
        assert match == "Lead Scoring System"

    def test_find_fuzzy_match_no_match(self):
        """Test finding no fuzzy match when below threshold."""
        existing = ["Support Bot", "Email Automation"]
        match = find_fuzzy_match("Lead Scoring", existing, threshold=0.85)
        assert match is None

    def test_find_fuzzy_match_empty_list(self):
        """Test finding fuzzy match with empty list."""
        match = find_fuzzy_match("Support Bot", [])
        assert match is None


class TestValidateResponseHasTable:
    """Tests for validate_response_has_table function."""

    def test_valid_response(self):
        """Test validation of valid response with table and answer."""
        response = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|------------------------|--------------|-------------------|-------------|-------------|
| 1 | Support Bot | Automate tickets | High volume | AI chatbot | n8n | Response time | High |

The answer is: Support Bot"""
        is_valid, error = validate_response_has_table(response)
        assert is_valid is True
        assert error == ""

    def test_empty_response(self):
        """Test validation of empty response."""
        is_valid, error = validate_response_has_table("")
        assert is_valid is False
        assert "Empty response" in error

    def test_missing_table_header(self):
        """Test validation when table header is missing."""
        response = "Some text without a table\nThe answer is: Support Bot"
        is_valid, error = validate_response_has_table(response)
        assert is_valid is False
        assert "Missing table header" in error

    def test_missing_separator(self):
        """Test validation when separator row is missing."""
        response = """| # | Workflow Name | Primary Objective |
| 1 | Support Bot | Automate tickets |
The answer is: Support Bot"""
        is_valid, error = validate_response_has_table(response)
        assert is_valid is False
        assert "Missing table separator" in error

    def test_incomplete_table(self):
        """Test validation when table has too few rows."""
        response = """| # | Workflow Name | Primary Objective |
|---|---------------|-------------------|
The answer is: Support Bot"""
        is_valid, error = validate_response_has_table(response)
        assert is_valid is False
        assert "Incomplete table" in error

    def test_missing_answer_line(self):
        """Test validation when 'The answer is' line is missing."""
        response = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|------------------------|--------------|-------------------|-------------|-------------|
| 1 | Support Bot | Automate tickets | High volume | AI chatbot | n8n | Response time | High |"""
        is_valid, error = validate_response_has_table(response)
        assert is_valid is False
        assert "Missing 'The answer is' line" in error


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
        """Test that response with answer but no table is rejected."""
        response = "The answer is Customer Support Bot."
        result = parse_response(response)
        # Should be rejected due to missing table
        assert result is None

    def test_answer_with_period_and_table(self):
        """Test parsing answer with period when table is present."""
        response = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|------------------------|--------------|-------------------|-------------|-------------|
| 1 | Customer Support Bot | Automate tickets | High volume | AI chatbot | n8n | Response time | High |

The answer is Customer Support Bot."""
        result = parse_response(response)
        assert result is not None
        assert result.answer == "Customer Support Bot"


class TestCountVotes:
    """Tests for count_votes function."""

    # Helper to create a response with workflow table
    @staticmethod
    def _make_response(workflow_name: str) -> str:
        """Create a response with proper markdown table for testing."""
        return f"""| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | {workflow_name} | Automate tickets | High volume | AI chatbot | n8n | Response time | High |
| 2 | Other Workflow | Other objective | Other problems | Other method | Zapier | Other metric | Medium |

The answer is {workflow_name}"""

    def test_unanimous_consensus(self):
        responses = [
            self._make_response("Support Bot"),
            self._make_response("Support Bot"),
            self._make_response("Support Bot"),
        ]

        result = count_votes(responses, min_consensus_votes=3, min_consensus_percent=60)

        assert result.final_answer == "Support Bot"  # Preserves original capitalization
        assert result.votes_for_winner == 3
        assert result.total_responses == 3
        assert result.confidence_percent == 100
        assert result.consensus_strength == "Strong"
        assert result.had_consensus is True

    def test_split_vote_with_consensus(self):
        responses = [
            self._make_response("Support Bot"),
            self._make_response("Support Bot"),
            self._make_response("Lead Scoring"),
        ]

        result = count_votes(responses, min_consensus_votes=2, min_consensus_percent=60)

        assert result.final_answer == "Support Bot"  # Preserves original capitalization
        assert result.votes_for_winner == 2
        assert result.confidence_percent == 67
        assert result.consensus_strength == "Strong"
        assert result.had_consensus is True

    def test_no_consensus_uses_fallback(self):
        """Test that fallback ranking is used when consensus fails."""
        responses = [
            self._make_response("Support Bot"),
            self._make_response("Lead Scoring"),
            self._make_response("Report Gen"),
        ]

        result = count_votes(responses, min_consensus_votes=2, min_consensus_percent=60)

        # Phase 3: Fallback should select a workflow instead of "No consensus"
        assert result.final_answer != "No consensus"
        assert result.final_answer in ["Support Bot", "Lead Scoring", "Report Gen"]
        assert result.had_consensus is False
        assert result.fallback_mode is True
        assert result.selection_method == "ranked_fallback"
        assert "Consensus voting failed" in result.confidence_warning
        assert len(result.all_workflows) > 0

    def test_minimum_votes_required_uses_fallback(self):
        """Test that fallback ranking is used when minimum votes not met."""
        responses = [
            self._make_response("Support Bot"),
        ]

        result = count_votes(responses, min_consensus_votes=2, min_consensus_percent=60)

        # Phase 3: Should use fallback since only 1 vote < 2 required
        assert result.final_answer != "No consensus"
        assert result.final_answer == "Support Bot"
        assert result.had_consensus is False
        assert result.fallback_mode is True
        assert result.selection_method == "ranked_fallback"

    def test_empty_responses(self):
        responses = []

        result = count_votes(responses, min_consensus_votes=2, min_consensus_percent=60)

        assert result.final_answer == "No consensus"
        assert result.total_responses == 0
        assert result.had_consensus is False

    def test_moderate_consensus_below_threshold_uses_fallback(self):
        """Test that 40% confidence fails threshold but fallback is used."""
        responses = [
            self._make_response("Support Bot"),
            self._make_response("Support Bot"),
            self._make_response("Lead Scoring"),
            self._make_response("Report Gen"),
            self._make_response("Email Triage"),
        ]

        # With 60% threshold, 40% confidence should fail consensus but use fallback
        result = count_votes(responses, min_consensus_votes=2, min_consensus_percent=60)

        assert result.final_answer != "No consensus"
        assert result.confidence_percent == 40
        assert result.consensus_strength == "Moderate"
        assert result.had_consensus is False
        assert result.fallback_mode is True
        assert result.selection_method == "ranked_fallback"

    def test_moderate_consensus_with_lower_threshold(self):
        """Test moderate consensus passes with lower percent threshold."""
        responses = [
            self._make_response("Support Bot"),
            self._make_response("Support Bot"),
            self._make_response("Lead Scoring"),
            self._make_response("Report Gen"),
            self._make_response("Email Triage"),
        ]

        # With 40% threshold, 40% confidence should pass
        result = count_votes(responses, min_consensus_votes=2, min_consensus_percent=40)

        assert result.final_answer == "Support Bot"  # Preserves original capitalization
        assert result.confidence_percent == 40
        assert result.consensus_strength == "Moderate"
        assert result.had_consensus is True
