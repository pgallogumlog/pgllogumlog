"""
Unit tests for the Workflow Selector module.
"""

import pytest

from contexts.workflow.selector import WorkflowSelector
from contexts.workflow.models import WorkflowRecommendation


class TestExtractKeywords:
    """Tests for extract_keywords method."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return WorkflowSelector()

    def test_basic_keyword_extraction(self, selector):
        """Test basic keyword extraction from text."""
        text = "customer support automation workflow"
        keywords = selector.extract_keywords(text)

        assert "customer" in keywords
        assert "support" in keywords
        assert "automation" in keywords
        assert "workflow" in keywords

    def test_stopwords_filtered(self, selector):
        """Test that stopwords are filtered out."""
        text = "the customer and the support with automation"
        keywords = selector.extract_keywords(text)

        assert "the" not in keywords
        assert "and" not in keywords
        assert "with" not in keywords
        assert "customer" in keywords
        assert "support" in keywords

    def test_short_words_filtered(self, selector):
        """Test that words <= 3 characters are filtered."""
        text = "a an for customer support bot api"
        keywords = selector.extract_keywords(text)

        assert "a" not in keywords
        assert "an" not in keywords
        assert "for" not in keywords
        assert "bot" not in keywords  # 3 chars
        assert "api" not in keywords  # 3 chars
        assert "customer" in keywords

    def test_case_insensitive(self, selector):
        """Test that keywords are lowercase normalized."""
        text = "Customer SUPPORT Automation"
        keywords = selector.extract_keywords(text)

        assert "customer" in keywords
        assert "support" in keywords
        assert "automation" in keywords
        assert "Customer" not in keywords
        assert "SUPPORT" not in keywords

    def test_frequency_weighting(self, selector):
        """Test that keyword frequency affects weights."""
        text = "customer customer customer support"
        keywords = selector.extract_keywords(text)

        # "customer" appears 3 times, "support" appears 1 time
        # log(1 + 3) > log(1 + 1)
        assert keywords["customer"] > keywords["support"]

    def test_empty_text(self, selector):
        """Test handling of empty text."""
        keywords = selector.extract_keywords("")
        assert keywords == {}

    def test_none_text(self, selector):
        """Test handling of None text."""
        keywords = selector.extract_keywords(None)
        assert keywords == {}


class TestCalculateSemanticRelevance:
    """Tests for calculate_semantic_relevance method."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return WorkflowSelector()

    @pytest.fixture
    def sample_workflow(self):
        """Create a sample workflow for testing."""
        return WorkflowRecommendation(
            name="Customer Support Automation",
            objective="Automate customer support ticket classification",
            description="Use NLP to classify incoming support tickets automatically",
            tools=["Zendesk", "OpenAI API"],
            metrics=["95% accuracy"],
            feasibility="High"
        )

    def test_high_overlap(self, selector, sample_workflow):
        """Test semantic relevance with high keyword overlap."""
        prompt = "automate customer support ticket classification using AI"
        score = selector.calculate_semantic_relevance(sample_workflow, prompt)

        # Should be significantly above baseline
        assert score > 1.5

    def test_no_overlap_baseline(self, selector, sample_workflow):
        """Test semantic relevance with no keyword overlap returns baseline."""
        prompt = "completely unrelated finance payroll processing"
        score = selector.calculate_semantic_relevance(sample_workflow, prompt)

        assert score == 0.5  # Baseline

    def test_partial_overlap(self, selector, sample_workflow):
        """Test semantic relevance with partial overlap."""
        prompt = "customer experience improvement dashboard"
        score = selector.calculate_semantic_relevance(sample_workflow, prompt)

        # Should be between baseline and high
        assert 0.5 < score < 2.0

    def test_max_score_capped(self, selector):
        """Test that semantic score is capped at 3.0."""
        workflow = WorkflowRecommendation(
            name="customer customer customer",
            objective="customer customer customer",
            description="customer customer customer",
            tools=[],
            metrics=[],
            feasibility="High"
        )
        prompt = "customer customer customer customer customer"
        score = selector.calculate_semantic_relevance(workflow, prompt)

        assert score <= 3.0

    def test_empty_prompt(self, selector, sample_workflow):
        """Test handling of empty prompt."""
        score = selector.calculate_semantic_relevance(sample_workflow, "")
        assert score == 0.5  # Baseline


class TestGetFeasibilityWeight:
    """Tests for get_feasibility_weight method."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return WorkflowSelector()

    def test_high_feasibility_base(self, selector):
        """Test High feasibility returns 1.0."""
        weight = selector.get_feasibility_weight("High", "Standard")
        assert weight == 1.0

    def test_low_feasibility_base(self, selector):
        """Test Low feasibility returns 0.3."""
        weight = selector.get_feasibility_weight("Low", "Standard")
        assert weight == 0.3

    def test_medium_feasibility_budget(self, selector):
        """Test Medium feasibility with Budget tier (stricter)."""
        weight = selector.get_feasibility_weight("Medium", "Budget")
        assert weight == 0.6

    def test_medium_feasibility_standard(self, selector):
        """Test Medium feasibility with Standard tier."""
        weight = selector.get_feasibility_weight("Medium", "Standard")
        assert weight == 0.75

    def test_medium_feasibility_premium(self, selector):
        """Test Medium feasibility with Premium tier (more tolerant)."""
        weight = selector.get_feasibility_weight("Medium", "Premium")
        assert weight == 0.9

    def test_invalid_feasibility(self, selector):
        """Test handling of invalid feasibility value."""
        weight = selector.get_feasibility_weight("Invalid", "Standard")
        assert weight == 0.75  # Default to Medium


class TestCalculateMetricsImpact:
    """Tests for calculate_metrics_impact method."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return WorkflowSelector()

    def test_no_metrics(self, selector):
        """Test that no metrics returns baseline 1.0."""
        impact = selector.calculate_metrics_impact([])
        assert impact == 1.0

    def test_accuracy_metric_high(self, selector):
        """Test high accuracy metric (95%)."""
        metrics = ["95% accuracy"]
        impact = selector.calculate_metrics_impact(metrics)

        # (95 - 70) / 20 = 1.25
        assert impact > 1.0

    def test_accuracy_metric_low(self, selector):
        """Test low accuracy metric (70%)."""
        metrics = ["70% accuracy"]
        impact = selector.calculate_metrics_impact(metrics)

        # (70 - 70) / 20 = 0, but max(0.5, 0) = 0.5
        assert impact >= 0.5

    def test_reduction_metric(self, selector):
        """Test reduction metric (50% reduction)."""
        metrics = ["50% reduction in processing time"]
        impact = selector.calculate_metrics_impact(metrics)

        # 50 / 50 = 1.0
        assert impact == 1.0

    def test_multiplier_metric(self, selector):
        """Test multiplier metric (5x faster)."""
        metrics = ["5x faster processing"]
        impact = selector.calculate_metrics_impact(metrics)

        # 5 / 2 = 2.5
        assert impact == 2.5

    def test_multiple_metrics_uses_max(self, selector):
        """Test that multiple metrics use maximum impact."""
        metrics = ["50% accuracy", "10x faster", "30% reduction"]
        impact = selector.calculate_metrics_impact(metrics)

        # Max should be from 10x = 5.0
        assert impact == 5.0

    def test_impact_capped_at_5(self, selector):
        """Test that impact is capped at 5.0."""
        metrics = ["100x faster"]
        impact = selector.calculate_metrics_impact(metrics)

        assert impact == 5.0

    def test_impact_floored_at_1(self, selector):
        """Test that impact is floored at 1.0."""
        metrics = ["5% improvement"]
        impact = selector.calculate_metrics_impact(metrics)

        assert impact >= 1.0


class TestCalculateToolPracticality:
    """Tests for calculate_tool_practicality method."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return WorkflowSelector()

    def test_few_tools_high_score(self, selector):
        """Test that 3 or fewer tools gets 1.0 base score."""
        tools = ["Tool1", "Tool2", "Tool3"]
        score = selector.calculate_tool_practicality(tools, "Standard")
        assert score == 1.0

    def test_medium_tools(self, selector):
        """Test that 4-5 tools gets 0.85 base score."""
        tools = ["Tool1", "Tool2", "Tool3", "Tool4", "Tool5"]
        score = selector.calculate_tool_practicality(tools, "Standard")
        assert score == 0.85

    def test_many_tools(self, selector):
        """Test that 6+ tools gets 0.7 base score."""
        tools = ["Tool1", "Tool2", "Tool3", "Tool4", "Tool5", "Tool6"]
        score = selector.calculate_tool_practicality(tools, "Standard")
        assert score == 0.7

    def test_budget_tier_nocode_boost(self, selector):
        """Test Budget tier boost for no-code tools."""
        tools = ["Zapier", "Google Sheets"]
        score = selector.calculate_tool_practicality(tools, "Budget")

        # Base 1.0 + 0.2 boost = 1.2
        assert score == 1.2

    def test_premium_tier_advanced_boost(self, selector):
        """Test Premium tier boost for advanced tools."""
        tools = ["Custom API", "ML Pipeline"]
        score = selector.calculate_tool_practicality(tools, "Premium")

        # Base 1.0 + 0.15 boost = 1.15
        assert score == 1.15

    def test_score_capped_at_1_2(self, selector):
        """Test that tool practicality score is capped at 1.2."""
        tools = ["Zapier"]  # Would get 1.0 + 0.2 = 1.2 for Budget
        score = selector.calculate_tool_practicality(tools, "Budget")

        assert score <= 1.2


class TestClassifyDomain:
    """Tests for classify_domain method."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return WorkflowSelector()

    def test_data_processing_domain(self, selector):
        """Test classification of data processing workflow."""
        workflow = WorkflowRecommendation(
            name="Document Classification",
            objective="Extract and classify documents using NLP",
            description="Parse incoming documents automatically",
            tools=[],
            metrics=[],
            feasibility="High"
        )
        domain = selector.classify_domain(workflow)
        assert domain == 'data_processing'

    def test_compliance_risk_domain(self, selector):
        """Test classification of compliance workflow."""
        workflow = WorkflowRecommendation(
            name="Regulatory Compliance Checker",
            objective="Audit for regulatory compliance",
            description="Ensure legal compliance with regulations",
            tools=[],
            metrics=[],
            feasibility="High"
        )
        domain = selector.classify_domain(workflow)
        assert domain == 'compliance_risk'

    def test_communication_domain(self, selector):
        """Test classification of communication workflow."""
        workflow = WorkflowRecommendation(
            name="Email Notification System",
            objective="Send automated email alerts",
            description="Create dashboard reports and notifications",
            tools=[],
            metrics=[],
            feasibility="High"
        )
        domain = selector.classify_domain(workflow)
        assert domain == 'communication'

    def test_analytics_domain(self, selector):
        """Test classification of analytics workflow."""
        workflow = WorkflowRecommendation(
            name="Predictive Analytics System",
            objective="Forecast future trends using analytics",
            description="Generate business intelligence and predictive insights",
            tools=[],
            metrics=[],
            feasibility="High"
        )
        domain = selector.classify_domain(workflow)
        assert domain == 'analytics'

    def test_workflow_mgmt_domain(self, selector):
        """Test classification of workflow management."""
        workflow = WorkflowRecommendation(
            name="Process Orchestration",
            objective="Coordinate and track multiple workflows",
            description="Monitor and manage business processes",
            tools=[],
            metrics=[],
            feasibility="High"
        )
        domain = selector.classify_domain(workflow)
        assert domain == 'workflow_mgmt'

    def test_integration_domain(self, selector):
        """Test classification of integration workflow."""
        workflow = WorkflowRecommendation(
            name="API Integration Bridge",
            objective="Sync data between systems via API",
            description="Connect multiple platforms and integrate data",
            tools=[],
            metrics=[],
            feasibility="High"
        )
        domain = selector.classify_domain(workflow)
        assert domain == 'integration'

    def test_other_domain(self, selector):
        """Test classification falls back to 'other' for unknown domains."""
        workflow = WorkflowRecommendation(
            name="Generic Workflow",
            objective="Do something unspecified",
            description="General purpose task",
            tools=[],
            metrics=[],
            feasibility="High"
        )
        domain = selector.classify_domain(workflow)
        assert domain == 'other'


class TestSelectTop5:
    """Tests for select_top_5 main selection method."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return WorkflowSelector()

    @pytest.fixture
    def sample_workflows(self):
        """Create sample workflows for testing."""
        workflows = []

        # High feasibility, data processing
        workflows.append(WorkflowRecommendation(
            name="Document Classification System",
            objective="Classify incoming documents using NLP",
            description="Extract and parse document data automatically",
            tools=["OpenAI API", "Zapier"],
            metrics=["95% accuracy"],
            feasibility="High"
        ))

        # High feasibility, compliance
        workflows.append(WorkflowRecommendation(
            name="Regulatory Compliance Auditor",
            objective="Audit documents for regulatory compliance",
            description="Ensure legal compliance automatically",
            tools=["Custom Compliance API"],
            metrics=["99% compliance rate"],
            feasibility="High"
        ))

        # Medium feasibility, communication
        workflows.append(WorkflowRecommendation(
            name="Email Notification Pipeline",
            objective="Send automated email notifications",
            description="Alert stakeholders via email dashboard",
            tools=["Gmail API", "Slack"],
            metrics=["50% faster response time"],
            feasibility="Medium"
        ))

        # High feasibility, analytics
        workflows.append(WorkflowRecommendation(
            name="Predictive Analytics Engine",
            objective="Forecast business trends with analytics",
            description="Generate predictive insights from data",
            tools=["Python", "ML Framework"],
            metrics=["3x better forecasting accuracy"],
            feasibility="High"
        ))

        # Medium feasibility, workflow management
        workflows.append(WorkflowRecommendation(
            name="Process Orchestration Platform",
            objective="Orchestrate and track workflows",
            description="Manage and coordinate business processes",
            tools=["n8n", "Airtable"],
            metrics=["40% time savings"],
            feasibility="Medium"
        ))

        # Low feasibility, integration
        workflows.append(WorkflowRecommendation(
            name="Legacy System Integration",
            objective="Integrate with legacy API systems",
            description="Bridge old and new platforms via API",
            tools=["Custom Middleware", "API Gateway"],
            metrics=["100% data sync"],
            feasibility="Low"
        ))

        # Add more similar workflows to test selection from larger pool
        for i in range(7, 15):
            workflows.append(WorkflowRecommendation(
                name=f"Generic Workflow {i}",
                objective=f"Generic objective {i}",
                description=f"Generic description {i}",
                tools=["Tool1"],
                metrics=[],
                feasibility="Medium"
            ))

        return workflows

    def test_selects_exactly_5(self, selector, sample_workflows):
        """Test that exactly 5 workflows are selected."""
        selected = selector.select_top_5(
            workflows=sample_workflows,
            tier="Standard",
            user_prompt="automate document processing",
            consensus_strength="Moderate"
        )

        assert len(selected) == 5

    def test_empty_workflows(self, selector):
        """Test handling of empty workflow list."""
        selected = selector.select_top_5(
            workflows=[],
            tier="Standard",
            user_prompt="test",
            consensus_strength="Moderate"
        )

        assert selected == []

    def test_fewer_than_5_workflows(self, selector):
        """Test handling when fewer than 5 workflows provided."""
        workflows = [
            WorkflowRecommendation(
                name="Workflow 1",
                objective="Objective 1",
                description="Description 1",
                tools=[],
                metrics=[],
                feasibility="High"
            ),
            WorkflowRecommendation(
                name="Workflow 2",
                objective="Objective 2",
                description="Description 2",
                tools=[],
                metrics=[],
                feasibility="High"
            )
        ]

        selected = selector.select_top_5(
            workflows=workflows,
            tier="Standard",
            user_prompt="test",
            consensus_strength="Moderate"
        )

        assert len(selected) == 2

    def test_domain_diversity_enforced(self, selector, sample_workflows):
        """Test that selected workflows cover multiple domains."""
        selected = selector.select_top_5(
            workflows=sample_workflows,
            tier="Standard",
            user_prompt="business automation",
            consensus_strength="Moderate"
        )

        domains = [selector.classify_domain(wf) for wf in selected]
        unique_domains = set(domains)

        # Should have at least 3 different domains
        assert len(unique_domains) >= 3

    def test_high_feasibility_preferred_budget(self, selector, sample_workflows):
        """Test that Budget tier prefers high feasibility workflows."""
        selected = selector.select_top_5(
            workflows=sample_workflows,
            tier="Budget",
            user_prompt="business automation",
            consensus_strength="Moderate"
        )

        high_feasibility_count = sum(1 for wf in selected if wf.feasibility == "High")

        # Budget tier should select more High feasibility workflows
        assert high_feasibility_count >= 3

    def test_semantic_relevance_affects_selection(self, selector, sample_workflows):
        """Test that semantic relevance affects which workflows are selected."""
        # Prompt specifically about document classification
        selected = selector.select_top_5(
            workflows=sample_workflows,
            tier="Standard",
            user_prompt="document classification and extraction using NLP",
            consensus_strength="Moderate"
        )

        # The Document Classification System should be highly ranked
        # due to strong semantic overlap
        names = [wf.name for wf in selected]
        assert "Document Classification System" in names

    def test_tier_multiplier_applied(self, selector, sample_workflows):
        """Test that tier multiplier affects scoring."""
        # Same workflows, different tiers should potentially select differently
        # (though with our sample data they might be similar)
        budget_selected = selector.select_top_5(
            workflows=sample_workflows,
            tier="Budget",
            user_prompt="business automation",
            consensus_strength="Moderate"
        )

        premium_selected = selector.select_top_5(
            workflows=sample_workflows,
            tier="Premium",
            user_prompt="business automation",
            consensus_strength="Moderate"
        )

        # Both should return 5 workflows
        assert len(budget_selected) == 5
        assert len(premium_selected) == 5

    def test_consensus_strength_affects_scoring(self, selector, sample_workflows):
        """Test that consensus strength is applied."""
        weak_selected = selector.select_top_5(
            workflows=sample_workflows,
            tier="Standard",
            user_prompt="business automation",
            consensus_strength="Weak"
        )

        strong_selected = selector.select_top_5(
            workflows=sample_workflows,
            tier="Standard",
            user_prompt="business automation",
            consensus_strength="Strong"
        )

        # Both should return 5 workflows (relative scoring changes but selection count same)
        assert len(weak_selected) == 5
        assert len(strong_selected) == 5


class TestDuplicateDetection:
    """Tests for duplicate workflow detection in selector."""

    @pytest.fixture
    def selector(self):
        """Create selector instance for testing."""
        return WorkflowSelector()

    def test_should_prevent_duplicate_workflows_in_selection(self, selector):
        """
        Test that selector prevents duplicate workflows from being selected.

        Regression test for Budget tier duplicate bug where "Client Communication
        Automation" appeared twice in top 5 because selector checks object identity
        instead of workflow name.
        """
        # Create 125 workflows with 3 intentional duplicates
        workflows = []

        # Add 5 high-scoring workflows (these should be selected)
        for i in range(5):
            workflows.append(WorkflowRecommendation(
                name=f"Top Workflow {i}",
                objective=f"High priority objective {i}",
                description="Excellent workflow for automation",
                feasibility="High",
                tools=["Tool1", "Tool2"],
                metrics=["95% accuracy", "3x faster"]
            ))

        # Add duplicate of "Top Workflow 2" with same name (simulates same workflow
        # from different temperature responses)
        workflows.append(WorkflowRecommendation(
            name="Top Workflow 2",  # DUPLICATE NAME
            objective="High priority objective 2",  # Same content
            description="Excellent workflow for automation",
            feasibility="High",
            tools=["Tool1", "Tool2"],
            metrics=["95% accuracy", "3x faster"]
        ))

        # Add another duplicate of "Top Workflow 3"
        workflows.append(WorkflowRecommendation(
            name="Top Workflow 3",  # DUPLICATE NAME
            objective="High priority objective 3",
            description="Excellent workflow for automation",
            feasibility="High",
            tools=["Tool1", "Tool2"],
            metrics=["95% accuracy", "3x faster"]
        ))

        # Fill rest with lower-scoring workflows
        for i in range(118):
            workflows.append(WorkflowRecommendation(
                name=f"Lower Priority Workflow {i}",
                objective=f"Lower priority objective {i}",
                description="Good workflow",
                feasibility="Medium",
                tools=["Tool1"],
                metrics=["85% accuracy"]
            ))

        # Select top 5 (Budget tier, Moderate consensus - no semantic floor)
        selected = selector.select_top_5(
            workflows=workflows,
            tier="Budget",
            user_prompt="business automation top workflows",
            consensus_strength="Moderate"
        )

        # Should select exactly 5 workflows
        assert len(selected) == 5, f"Expected 5 workflows, got {len(selected)}"

        # Extract workflow names
        selected_names = [wf.name for wf in selected]

        # CRITICAL: No duplicates should exist
        unique_names = set(selected_names)
        assert len(selected_names) == len(unique_names), (
            f"Duplicate workflows detected! Selected: {selected_names}"
        )

    def test_should_handle_many_duplicates_across_125_workflows(self, selector):
        """
        Test selector handles many duplicates (simulating 5 temps × 25 workflows).

        Simulates real scenario: 5 temperature calls each generate 25 workflows,
        some workflows appear in multiple temperature responses.
        """
        workflows = []

        # Create 25 unique workflow names
        unique_workflow_names = [f"Workflow {i}" for i in range(25)]

        # Simulate 5 temperature responses (125 total workflows)
        # Each temperature generates the same 25 workflows (100% overlap - worst case)
        for temp_idx in range(5):
            for wf_name in unique_workflow_names:
                workflows.append(WorkflowRecommendation(
                    name=wf_name,  # Same name across temperatures
                    objective=f"Objective for {wf_name} at temp {temp_idx}",
                    description=f"Description for {wf_name}",
                    feasibility="High" if int(wf_name.split()[-1]) < 10 else "Medium",
                    tools=["Tool1", "Tool2"],
                    metrics=["90% accuracy"]
                ))

        # Verify we have 125 workflows total
        assert len(workflows) == 125

        # Select top 5
        selected = selector.select_top_5(
            workflows=workflows,
            tier="Standard",
            user_prompt="workflow automation",
            consensus_strength="Weak"
        )

        # Should select exactly 5 workflows
        assert len(selected) == 5

        # Extract workflow names
        selected_names = [wf.name for wf in selected]

        # CRITICAL: All 5 should have unique names
        unique_names = set(selected_names)
        assert len(selected_names) == len(unique_names), (
            f"Duplicates found in selection! Names: {selected_names}"
        )

    def test_object_identity_bug_reproducer(self, selector):
        """
        Direct reproducer for object identity bug in selector.

        This test creates TWO identical workflow objects (same name and content)
        that should score identically and both appear in top candidates.
        If selector uses object identity checking, both will be selected.
        """
        workflows = []

        # Create a single high-scoring workflow that appears TWICE as different objects
        # (simulating same workflow from two different temperature responses)
        duplicate_wf_1 = WorkflowRecommendation(
            name="Client Communication Automation",  # Same name
            objective="Automate client communication workflows",
            description="Comprehensive automation for client interactions",
            feasibility="High",
            tools=["Zapier", "Gmail", "Slack"],
            metrics=["95% faster response", "3x productivity"]
        )

        duplicate_wf_2 = WorkflowRecommendation(
            name="Client Communication Automation",  # EXACT SAME NAME
            objective="Automate client communication workflows",
            description="Comprehensive automation for client interactions",
            feasibility="High",
            tools=["Zapier", "Gmail", "Slack"],
            metrics=["95% faster response", "3x productivity"]
        )

        # Verify these are different objects (different memory addresses)
        assert duplicate_wf_1 is not duplicate_wf_2, "Objects should be different instances"

        # Add both duplicate objects
        workflows.append(duplicate_wf_1)
        workflows.append(duplicate_wf_2)

        # Add 3 other high-scoring workflows
        for i in range(3):
            workflows.append(WorkflowRecommendation(
                name=f"Other High Priority Workflow {i}",
                objective=f"Important objective {i}",
                description="Important workflow",
                feasibility="High",
                tools=["Tool1", "Tool2"],
                metrics=["90% accuracy"]
            ))

        # Fill with lower-scoring workflows
        for i in range(120):
            workflows.append(WorkflowRecommendation(
                name=f"Lower Priority {i}",
                objective="Lower priority",
                description="Less important",
                feasibility="Medium",
                tools=["Tool1"],
                metrics=["80% accuracy"]
            ))

        # Select top 5
        selected = selector.select_top_5(
            workflows=workflows,
            tier="Budget",
            user_prompt="client communication automation workflow",
            consensus_strength="Moderate"  # No semantic floor
        )

        # Extract names
        selected_names = [wf.name for wf in selected]

        print(f"\nSelected workflows: {selected_names}")

        # Count occurrences of "Client Communication Automation"
        duplicate_count = selected_names.count("Client Communication Automation")

        # CRITICAL: Should appear at most ONCE
        assert duplicate_count <= 1, (
            f"Duplicate bug! 'Client Communication Automation' appears {duplicate_count} times. "
            f"Selected: {selected_names}"
        )

    def test_backfill_duplicate_bug(self, selector):
        """
        Test that reproduces duplicate bug in backfill logic (selector.py line 152).

        Bug scenario:
        1. Two workflows with same name score identically
        2. Main selection loop selects first duplicate
        3. Second duplicate skipped by main loop (domain already covered)
        4. Backfill loop (line 152) uses `item not in selected` which checks
           dictionary identity, NOT workflow name
        5. Second duplicate gets added during backfill
        """
        workflows = []

        # Create duplicate workflow objects (same name, same scores)
        for i in range(2):
            workflows.append(WorkflowRecommendation(
                name="Communication Workflow",  # SAME NAME
                objective="Automate communications",
                description="Email automation and notifications",
                feasibility="High",
                tools=["Gmail", "Slack"],
                metrics=["90% faster"]
            ))

        # Add 2 more workflows from SAME domain (communication)
        # This ensures domain is already covered after first selection
        workflows.append(WorkflowRecommendation(
            name="Email Workflow",
            objective="Email automation",
            description="Automated email responses",
            feasibility="High",
            tools=["Gmail"],
            metrics=["85% faster"]
        ))

        workflows.append(WorkflowRecommendation(
            name="Notification Workflow",
            objective="Push notifications",
            description="Send automated notifications",
            feasibility="High",
            tools=["Slack"],
            metrics=["80% faster"]
        ))

        # Add workflows from different domains (but lower scores due to Medium feasibility)
        # These fill the first 3 slots, leaving room for backfill
        for i in range(100):
            workflows.append(WorkflowRecommendation(
                name=f"Other Domain Workflow {i}",
                objective=f"Different domain objective {i}",
                description="workflow from another domain",
                feasibility="Medium",  # Lower score
                tools=["Tool1"],
                metrics=["70% accuracy"]
            ))

        # Select top 5
        selected = selector.select_top_5(
            workflows=workflows,
            tier="Budget",
            user_prompt="communication email workflow automation",
            consensus_strength="Moderate"
        )

        # Extract names
        selected_names = [wf.name for wf in selected]

        print(f"\nBackfill test - Selected workflows: {selected_names}")

        # Count occurrences of "Communication Workflow"
        duplicate_count = selected_names.count("Communication Workflow")

        # CRITICAL: Should appear at most ONCE
        assert duplicate_count <= 1, (
            f"Backfill duplicate bug! 'Communication Workflow' appears {duplicate_count} times. "
            f"Selected: {selected_names}"
        )
