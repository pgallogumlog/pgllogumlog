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
    rank_workflows_by_score,
    score_workflow,
    VoteResult,
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


class TestScoreWorkflow:
    """Tests for score_workflow function."""

    def test_high_feasibility_workflow(self):
        """Test workflow with high feasibility scores highest in feasibility component."""
        workflow = {
            "name": "Test Workflow",
            "feasibility": "High",
            "objective": "Automate tickets",
            "problems": "High volume",
            "how_it_works": "Simple chatbot",
            "tools": "n8n",
        }
        score = score_workflow(workflow)
        # High feasibility (40) + default impact (15) + default complexity (20) = 75
        assert score >= 70.0

    def test_low_feasibility_workflow(self):
        """Test workflow with low feasibility scores lower."""
        workflow = {
            "name": "Test Workflow",
            "feasibility": "Low",
            "objective": "Complex integration",
            "problems": "Legacy systems",
            "how_it_works": "Custom integration",
            "tools": "Multiple systems",
        }
        score = score_workflow(workflow)
        # Low feasibility (10) + low impact (15) + complex (10) = 35
        assert score <= 40.0

    def test_high_impact_keywords(self):
        """Test that high impact keywords boost score."""
        workflow = {
            "name": "Revenue Generator",
            "feasibility": "Medium",
            "objective": "Increase revenue significantly",
            "problems": "Critical cost savings needed",
            "how_it_works": "AI automation",
            "tools": "Standard",
        }
        score = score_workflow(workflow)
        # Medium feasibility (25) + high impact (30) + default complexity (20) = 75
        assert score >= 70.0

    def test_simple_complexity_boost(self):
        """Test that simple/straightforward keywords boost score."""
        workflow = {
            "name": "Simple Bot",
            "feasibility": "Medium",
            "objective": "Automate",
            "problems": "Manual work",
            "how_it_works": "Simple template-based solution",
            "tools": "Existing tools",
        }
        score = score_workflow(workflow)
        # Medium feasibility (25) + default impact (15) + simple complexity (30) = 70
        assert score >= 65.0

    def test_complex_workflow_penalty(self):
        """Test that complex workflows score lower."""
        workflow = {
            "name": "Complex System",
            "feasibility": "Medium",
            "objective": "Advanced integration",
            "problems": "Complex requirements",
            "how_it_works": "Custom advanced solution with multiple integrations",
            "tools": "Complex",
        }
        score = score_workflow(workflow)
        # Medium feasibility (25) + default impact (15) + complex (10) = 50
        assert score <= 55.0

    def test_empty_workflow_gets_default_score(self):
        """Test that empty workflow dict gets default scoring."""
        workflow = {}
        score = score_workflow(workflow)
        # Default feasibility (20) + default impact (15) + default complexity (20) = 55
        assert 50.0 <= score <= 60.0


class TestRankWorkflowsByScore:
    """Tests for rank_workflows_by_score function."""

    def test_ranks_by_combined_score(self):
        """Test that workflows are ranked by total score."""
        responses = [
            VoteResult(
                answer="High Feasibility Bot",
                workflows=[
                    {
                        "name": "High Feasibility Bot",
                        "feasibility": "High",
                        "objective": "Critical revenue generation",
                        "problems": "Significant cost",
                        "how_it_works": "Simple automation",
                        "tools": "Standard",
                        "metrics": "ROI",
                    }
                ],
            ),
            VoteResult(
                answer="Low Feasibility Complex",
                workflows=[
                    {
                        "name": "Low Feasibility Complex",
                        "feasibility": "Low",
                        "objective": "Minor improvement",
                        "problems": "Small issue",
                        "how_it_works": "Complex custom integration",
                        "tools": "Multiple systems",
                        "metrics": "Accuracy",
                    }
                ],
            ),
        ]

        best_name, all_workflows = rank_workflows_by_score(responses)

        # High feasibility workflow should win
        assert best_name == "High Feasibility Bot"
        assert len(all_workflows) == 2
        # First workflow should be the highest scored
        assert all_workflows[0].name == "High Feasibility Bot"

    def test_handles_empty_responses(self):
        """Test graceful handling of empty responses."""
        best_name, all_workflows = rank_workflows_by_score([])

        assert best_name == "No consensus"
        assert all_workflows == []

    def test_handles_responses_with_no_workflows(self):
        """Test handling of responses that have empty workflow lists."""
        responses = [
            VoteResult(answer="Test", workflows=[]),
            VoteResult(answer="Test2", workflows=[]),
        ]

        best_name, all_workflows = rank_workflows_by_score(responses)

        assert best_name == "No consensus"
        assert all_workflows == []

    def test_scores_multiple_workflows_per_response(self):
        """Test that all workflows from all responses are scored."""
        responses = [
            VoteResult(
                answer="Workflow A",
                workflows=[
                    {
                        "name": "Workflow A",
                        "feasibility": "High",
                        "objective": "Important",
                        "problems": "Volume",
                        "how_it_works": "Simple",
                        "tools": "n8n",
                        "metrics": "Time",
                    },
                    {
                        "name": "Workflow B",
                        "feasibility": "Medium",
                        "objective": "Useful",
                        "problems": "Manual",
                        "how_it_works": "Standard",
                        "tools": "Zapier",
                        "metrics": "Accuracy",
                    },
                ],
            ),
            VoteResult(
                answer="Workflow C",
                workflows=[
                    {
                        "name": "Workflow C",
                        "feasibility": "Low",
                        "objective": "Nice to have",
                        "problems": "Minor",
                        "how_it_works": "Complex",
                        "tools": "Custom",
                        "metrics": "Speed",
                    }
                ],
            ),
        ]

        best_name, all_workflows = rank_workflows_by_score(responses)

        # Should have all 3 workflows
        assert len(all_workflows) == 3
        # Workflow A should rank highest (high feasibility)
        assert best_name == "Workflow A"


class TestCountVotesFallback:
    """Tests for fallback scoring when consensus fails."""

    def test_uses_ranked_fallback_when_no_consensus(self):
        """Test that ranked scoring is used when voting fails to reach consensus."""
        table_template = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | {name} | {objective} | {problems} | {how} | {tools} | {metrics} | {feasibility} |

The answer is {name}"""

        # Three different workflows - no consensus possible
        responses = [
            table_template.format(
                name="High Value Bot",
                objective="Critical revenue generation",
                problems="Significant cost savings",
                how="Simple automation",
                tools="n8n",
                metrics="ROI",
                feasibility="High",
            ),
            table_template.format(
                name="Medium Workflow",
                objective="Useful improvement",
                problems="Manual work",
                how="Standard process",
                tools="Zapier",
                metrics="Time",
                feasibility="Medium",
            ),
            table_template.format(
                name="Complex System",
                objective="Minor optimization",
                problems="Small issue",
                how="Complex custom integration",
                tools="Multiple systems",
                metrics="Accuracy",
                feasibility="Low",
            ),
        ]

        result = count_votes(responses, min_consensus_votes=3)

        # Should NOT have consensus (3 different answers)
        assert result.had_consensus is False

        # Should use ranked fallback and pick highest-scored workflow
        # "High Value Bot" has: High feasibility + high impact keywords + simple
        assert result.final_answer == "High Value Bot"

        # Should have all workflows available
        assert len(result.all_workflows) >= 3

        # NEW: Metrics should be overridden with fallback scoring confidence
        # High Value Bot scores: High feasibility (40) + high impact (30) + simple (30) = 100
        # Capped at 85%
        assert result.confidence_percent == 85
        assert result.consensus_strength == "Fallback - High Confidence"

    def test_fallback_metrics_override_with_high_score(self):
        """Test that fallback overrides metrics with high confidence when score is high."""
        table_template = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | {name} | {objective} | {problems} | {how} | {tools} | {metrics} | {feasibility} |

The answer is {name}"""

        # All different answers - no consensus (1/5 votes each = 20% voting confidence)
        # Use sufficiently different names to avoid fuzzy matching
        responses = [
            table_template.format(
                name="Premium Revenue Bot",
                objective="Major revenue impact",
                problems="Critical efficiency gains",
                how="Simple template",
                tools="Standard",
                metrics="ROI",
                feasibility="High",
            ),
            table_template.format(
                name="Data Processing Engine",
                objective="Minor",
                problems="Small",
                how="Complex",
                tools="Custom",
                metrics="Time",
                feasibility="Low",
            ),
            table_template.format(
                name="Email Automation System",
                objective="Minor",
                problems="Small",
                how="Complex",
                tools="Custom",
                metrics="Speed",
                feasibility="Low",
            ),
            table_template.format(
                name="Lead Scoring Tool",
                objective="Minor",
                problems="Small",
                how="Complex",
                tools="Custom",
                metrics="Accuracy",
                feasibility="Low",
            ),
            table_template.format(
                name="Report Generator",
                objective="Minor",
                problems="Small",
                how="Complex",
                tools="Custom",
                metrics="Quality",
                feasibility="Low",
            ),
        ]

        result = count_votes(responses, min_consensus_votes=3)

        # Voting confidence would be 20% (1/5)
        # But fallback should override with high scoring confidence
        assert result.had_consensus is False
        assert result.final_answer == "Premium Revenue Bot"

        # Premium Revenue Bot: High (40) + Major/Critical (30) + Simple (30) = 100, capped at 85
        assert result.confidence_percent == 85
        assert result.consensus_strength == "Fallback - High Confidence"

    def test_fallback_metrics_override_with_medium_score(self):
        """Test that fallback shows medium confidence for medium-scored workflows."""
        table_template = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | {name} | {objective} | {problems} | {how} | {tools} | {metrics} | {feasibility} |

The answer is {name}"""

        # All medium-quality workflows, no consensus
        # Use different names to avoid fuzzy matching
        # Design workflows to score in medium range (60-74)
        responses = [
            table_template.format(
                name="Invoice Processing",
                objective="Process invoices",  # No high-impact keywords
                problems="Manual entry",
                how="Automation workflow",  # Neutral complexity
                tools="Zapier",
                metrics="Time",
                feasibility="Medium",  # 25 points
            ),
            table_template.format(
                name="Customer Onboarding",
                objective="Onboard customers",  # No high-impact keywords
                problems="Process time",
                how="Automated flow",  # Neutral complexity
                tools="n8n",
                metrics="Speed",
                feasibility="Medium",  # 25 points
            ),
            table_template.format(
                name="Report Distribution",
                objective="Send reports",  # No high-impact keywords
                problems="Manual distribution",
                how="Scheduled automation",  # Neutral complexity
                tools="Make",
                metrics="Efficiency",
                feasibility="Medium",  # 25 points
            ),
        ]

        result = count_votes(responses, min_consensus_votes=3)

        assert result.had_consensus is False

        # Best workflow scores: Medium (25) + default impact (15) + default complexity (20) = 60
        assert 60 <= result.confidence_percent <= 74
        assert result.consensus_strength == "Fallback - Medium Confidence"

    def test_fallback_confidence_capped_at_85_percent(self):
        """Test that fallback confidence is capped at 85% even if score is higher."""
        table_template = """| # | Workflow Name | Primary Objective | Problems/Opportunities | How It Works | Tools/Integrations | Key Metrics | Feasibility |
|---|---------------|-------------------|----------------------|--------------|-------------------|-------------|-------------|
| 1 | {name} | {objective} | {problems} | {how} | {tools} | {metrics} | {feasibility} |

The answer is {name}"""

        # Perfect workflow: High + Critical + Simple = 100 points
        responses = [
            table_template.format(
                name="Perfect Workflow",
                objective="Critical revenue generation with significant cost savings",
                problems="Major efficiency gains",
                how="Simple straightforward template",
                tools="Existing standard tools",
                metrics="ROI",
                feasibility="High",
            ),
            table_template.format(
                name="Bad Workflow",
                objective="Minor",
                problems="Small",
                how="Complex",
                tools="Custom",
                metrics="Time",
                feasibility="Low",
            ),
            table_template.format(
                name="Another Bad",
                objective="Minor",
                problems="Small",
                how="Complex",
                tools="Custom",
                metrics="Speed",
                feasibility="Low",
            ),
        ]

        result = count_votes(responses, min_consensus_votes=3)

        assert result.had_consensus is False
        assert result.final_answer == "Perfect Workflow"

        # Even though score would be 100, cap at 85
        assert result.confidence_percent == 85
        assert result.consensus_strength == "Fallback - High Confidence"
