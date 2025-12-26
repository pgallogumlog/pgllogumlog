"""
Unit tests for the Vote Counter module.
"""

import pytest

from contexts.workflow.voter import (
    count_votes,
    find_fuzzy_match,
    fuzzy_match_score,
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


class TestFuzzyMatchScore:
    """Tests for fuzzy_match_score function."""

    def test_identical_names(self):
        score = fuzzy_match_score("Customer Support Bot", "Customer Support Bot")
        assert score == 1.0

    def test_identical_after_normalization(self):
        # Should be identical after normalization (markdown, case)
        score = fuzzy_match_score("**Customer Support Bot**", "Customer Support Bot")
        assert score == 1.0

    def test_high_similarity(self):
        # "Lead Scoring" vs "Lead Scorer" should be very similar (but below 0.85)
        score = fuzzy_match_score("Lead Scoring", "Lead Scorer")
        assert 0.75 < score < 0.85

    def test_moderate_similarity(self):
        # Some overlap but clearly different
        score = fuzzy_match_score("Customer Support", "Customer Service")
        assert 0.5 < score < 0.9

    def test_low_similarity(self):
        # Completely different
        score = fuzzy_match_score("Lead Scoring", "Email Automation")
        assert score < 0.5

    def test_empty_strings(self):
        assert fuzzy_match_score("", "") == 0.0
        assert fuzzy_match_score("Test", "") == 0.0
        assert fuzzy_match_score("", "Test") == 0.0

    def test_none_values(self):
        assert fuzzy_match_score(None, None) == 0.0
        assert fuzzy_match_score("Test", None) == 0.0
        assert fuzzy_match_score(None, "Test") == 0.0

    def test_case_insensitive(self):
        # Should normalize case before comparison
        score = fuzzy_match_score("LEAD SCORING", "lead scoring")
        assert score == 1.0

    def test_whitespace_normalization(self):
        # Should normalize multiple spaces
        score = fuzzy_match_score("Lead  Scoring", "Lead Scoring")
        assert score == 1.0

    def test_minor_typo(self):
        # Single character difference
        score = fuzzy_match_score("Lead Scoring", "Lead Scorring")
        assert score > 0.80


class TestFindFuzzyMatch:
    """Tests for find_fuzzy_match function."""

    def test_exact_match_found(self):
        existing = ["Customer Support Bot", "Lead Scoring", "Email Automation"]
        match = find_fuzzy_match("Customer Support Bot", existing, threshold=0.85)
        assert match == "Customer Support Bot"

    def test_fuzzy_match_found_above_threshold(self):
        existing = ["Customer Support Bot", "Lead Scoring", "Email Automation"]
        match = find_fuzzy_match("Customer Support", existing, threshold=0.70)
        assert match == "Customer Support Bot"

    def test_no_match_below_threshold(self):
        existing = ["Customer Support Bot", "Lead Scoring", "Email Automation"]
        match = find_fuzzy_match("Invoice Processing", existing, threshold=0.85)
        assert match is None

    def test_returns_best_match(self):
        existing = ["Lead Scoring", "Lead Scorer", "Lead Generation"]
        # "Lead Scoring System" should match "Lead Scoring" best
        match = find_fuzzy_match("Lead Scoring System", existing, threshold=0.70)
        assert match == "Lead Scoring"

    def test_empty_existing_names(self):
        match = find_fuzzy_match("Test", [], threshold=0.85)
        assert match is None

    def test_empty_target_name(self):
        existing = ["Customer Support Bot"]
        match = find_fuzzy_match("", existing, threshold=0.85)
        assert match is None

    def test_markdown_formatting_matches(self):
        existing = ["Customer Support Bot"]
        # Should match despite markdown formatting
        match = find_fuzzy_match("**Customer Support Bot**", existing, threshold=0.85)
        assert match == "Customer Support Bot"

    def test_case_variation_matches(self):
        existing = ["Lead Scoring System"]
        match = find_fuzzy_match("lead scoring system", existing, threshold=0.85)
        assert match == "Lead Scoring System"

    def test_threshold_adjustment(self):
        existing = ["Customer Support"]
        # Should match with lower threshold
        match_low = find_fuzzy_match("Customer Service", existing, threshold=0.60)
        assert match_low == "Customer Support"

        # Should NOT match with higher threshold
        match_high = find_fuzzy_match("Customer Service", existing, threshold=0.90)
        assert match_high is None


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
        response = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | Support Bot | Automate tickets | High volume | AI chatbot | n8n | Response time | High |

The answer is Customer Support Bot."""
        result = parse_response(response)
        assert result is not None
        assert result.answer == "Customer Support Bot"


class TestCountVotes:
    """Tests for count_votes function."""

    def test_unanimous_consensus(self):
        table_response = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | Support Bot | Automate tickets | High volume | AI chatbot | n8n | Response time | High |

The answer is Support Bot"""

        responses = [
            table_response,
            table_response,
            table_response,
        ]

        result = count_votes(responses, min_consensus_votes=2)

        assert result.final_answer == "Support Bot"  # Preserves Title Case from vote
        assert result.votes_for_winner == 3
        assert result.total_responses == 3
        assert result.confidence_percent == 100
        assert result.consensus_strength == "Strong"
        assert result.had_consensus is True

    def test_split_vote_with_consensus(self):
        support_bot = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | Support Bot | Automate tickets | High volume | AI chatbot | n8n | Response time | High |

The answer is Support Bot"""

        lead_scoring = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | Lead Scoring | Prioritize leads | Manual | ML model | Zapier | Conversion | Medium |

The answer is Lead Scoring"""

        responses = [
            support_bot,
            support_bot,
            lead_scoring,
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
        table_template = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | {name} | {objective} | {problems} | {how} | {tools} | {metrics} | {feasibility} |

The answer is {name}"""

        responses = [
            table_template.format(name="Support Bot", objective="Automate", problems="Volume", how="AI", tools="n8n", metrics="Time", feasibility="High"),
            table_template.format(name="Support Bot", objective="Automate", problems="Volume", how="AI", tools="n8n", metrics="Time", feasibility="High"),
            table_template.format(name="Lead Scoring", objective="Prioritize", problems="Manual", how="ML", tools="Zapier", metrics="Conv", feasibility="Med"),
            table_template.format(name="Report Gen", objective="Automate", problems="Time", how="AI", tools="Make", metrics="Speed", feasibility="High"),
            table_template.format(name="Email Triage", objective="Sort", problems="Volume", how="AI", tools="n8n", metrics="Accuracy", feasibility="Med"),
        ]

        result = count_votes(responses, min_consensus_votes=2)

        assert result.final_answer == "Support Bot"  # Preserves Title Case from vote
        assert result.confidence_percent == 40
        assert result.consensus_strength == "Moderate"

    def test_fuzzy_matching_consolidates_similar_votes(self):
        """Test that fuzzy matching consolidates similar workflow names into one vote."""
        table_template = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | {name} | {objective} | {problems} | {how} | {tools} | {metrics} | {feasibility} |

The answer is {name}"""

        # Use names that are >85% similar for consolidation
        # "Email Automation Bot" vs "Email Automation" should consolidate
        responses = [
            table_template.format(name="Email Automation Bot", objective="Automate", problems="Volume", how="AI", tools="n8n", metrics="Time", feasibility="High"),
            table_template.format(name="Email Automation", objective="Automate", problems="Volume", how="AI", tools="n8n", metrics="Time", feasibility="High"),
            table_template.format(name="Email Automation Bot", objective="Automate", problems="Volume", how="AI", tools="n8n", metrics="Time", feasibility="High"),
        ]

        result = count_votes(responses, min_consensus_votes=2)

        # Should reach consensus by consolidating similar votes
        assert result.had_consensus is True
        assert result.votes_for_winner >= 2
        assert result.fuzzy_matches >= 1  # At least one vote was consolidated

    def test_fuzzy_matching_respects_threshold(self):
        """Test that fuzzy matching doesn't consolidate dissimilar names."""
        table_template = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | {name} | {objective} | {problems} | {how} | {tools} | {metrics} | {feasibility} |

The answer is {name}"""

        # These are clearly different workflows - should NOT consolidate
        responses = [
            table_template.format(name="Lead Scoring", objective="Prioritize", problems="Manual", how="ML", tools="Zapier", metrics="Conv", feasibility="High"),
            table_template.format(name="Email Automation", objective="Automate", problems="Volume", how="AI", tools="n8n", metrics="Time", feasibility="High"),
            table_template.format(name="Invoice Processing", objective="Process", problems="Manual", how="OCR", tools="Make", metrics="Accuracy", feasibility="Med"),
        ]

        result = count_votes(responses, min_consensus_votes=2)

        # Should NOT reach consensus - workflows are too different
        assert result.had_consensus is False
        assert result.fuzzy_matches == 0  # No votes consolidated

    def test_fuzzy_matching_preserves_first_vote_name(self):
        """Test that fuzzy matching preserves the canonical name from first vote."""
        table_template = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | {name} | {objective} | {problems} | {how} | {tools} | {metrics} | {feasibility} |

The answer is {name}"""

        # First vote is "Customer Support Bot" - this should be the canonical name
        responses = [
            table_template.format(name="Customer Support Bot", objective="Automate", problems="Volume", how="AI", tools="n8n", metrics="Time", feasibility="High"),
            table_template.format(name="Customer Support", objective="Automate", problems="Volume", how="AI", tools="n8n", metrics="Time", feasibility="High"),
            table_template.format(name="Customer Support Automation", objective="Automate", problems="Volume", how="AI", tools="n8n", metrics="Time", feasibility="High"),
        ]

        result = count_votes(responses, min_consensus_votes=2)

        # Should use name from workflow table (Title Case preserved)
        assert result.had_consensus is True
        assert "Customer Support" in result.final_answer

    def test_fuzzy_matching_with_markdown_formatting(self):
        """Test that fuzzy matching handles markdown-formatted workflow names."""
        table_template = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | {name} | {objective} | {problems} | {how} | {tools} | {metrics} | {feasibility} |

The answer is {vote_name}"""

        # Same workflow but one has markdown formatting in the vote
        responses = [
            table_template.format(name="Lead Scoring", objective="Prioritize", problems="Manual", how="ML", tools="Zapier", metrics="Conv", feasibility="High", vote_name="Lead Scoring"),
            table_template.format(name="Lead Scoring", objective="Prioritize", problems="Manual", how="ML", tools="Zapier", metrics="Conv", feasibility="High", vote_name="**Lead Scoring**"),
            table_template.format(name="Lead Scoring", objective="Prioritize", problems="Manual", how="ML", tools="Zapier", metrics="Conv", feasibility="High", vote_name="Lead Scoring"),
        ]

        result = count_votes(responses, min_consensus_votes=2)

        # Should consolidate despite markdown in vote
        assert result.had_consensus is True
        assert result.votes_for_winner == 3
        assert result.final_answer == "Lead Scoring"  # No markdown in final answer

    def test_fuzzy_matching_quality_metrics(self):
        """Test that fuzzy_matches metric is properly tracked."""
        table_template = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | {name} | {objective} | {problems} | {how} | {tools} | {metrics} | {feasibility} |

The answer is {name}"""

        # All three should consolidate via fuzzy matching
        responses = [
            table_template.format(name="Email Automation", objective="Automate", problems="Volume", how="AI", tools="n8n", metrics="Time", feasibility="High"),
            table_template.format(name="Email Automation Bot", objective="Automate", problems="Volume", how="AI", tools="n8n", metrics="Time", feasibility="High"),  # Fuzzy match
            table_template.format(name="Email Automation", objective="Automate", problems="Volume", how="AI", tools="n8n", metrics="Time", feasibility="High"),  # Fuzzy match
        ]

        result = count_votes(responses, min_consensus_votes=2)

        # Should track fuzzy matches (2nd and 3rd responses match to 1st)
        assert result.fuzzy_matches == 2
        assert result.total_responses == 3
        assert result.votes_for_winner == 3
