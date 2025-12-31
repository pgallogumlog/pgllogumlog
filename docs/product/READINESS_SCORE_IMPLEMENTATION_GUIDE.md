# AI Readiness Score: Implementation Guide
## Technical Specification for Engineering Team

**Scope**: Implement AI Readiness Score (0-100) in 4 weeks
**Owner**: Architect + Engineering Lead
**Delivery**: Production-ready scoring with explainability

---

## PHASE 1: FORM EXPANSION (Week 1-2)

### Current State
Form at: `workflow_system/web/ui/templates/submit.html`

Existing fields:
```
✓ Company name
✓ Website (optional)
✓ Industry (dropdown)
✓ Company size (dropdown)
✓ Pain point (dropdown + text area)
✓ Contact email
✓ Contact name
✓ Tier selection
```

### New Fields to Add

**Section 2.5: Your Technology & Infrastructure** (Insert before "Choose Your Tier")

```html
<div class="form-section">
    <h2 class="section-title">
        <span class="section-number">2.5</span>
        Your Technology & Infrastructure
    </h2>
    <p style="color: #8892b0; margin-bottom: 1.5rem;">
        This helps us understand your environment and refine recommendations.
    </p>

    <!-- Question 1: Cloud Infrastructure -->
    <div class="form-group">
        <label>Does your organization use cloud infrastructure?</label>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="radio" name="has_cloud" value="yes" required>
                <span>Yes (AWS/Azure/GCP)</span>
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="radio" name="has_cloud" value="partial" required>
                <span>Partially</span>
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="radio" name="has_cloud" value="no" required>
                <span>No (on-premise only)</span>
            </label>
        </div>
    </div>

    <!-- Question 2: Automation Experience -->
    <div class="form-group">
        <label>Experience with automation/workflow tools</label>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="checkbox" name="automation_tools" value="zapier">
                <span>Zapier</span>
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="checkbox" name="automation_tools" value="n8n">
                <span>n8n</span>
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="checkbox" name="automation_tools" value="make">
                <span>Make</span>
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="checkbox" name="automation_tools" value="custom_code">
                <span>Custom API integrations</span>
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="checkbox" name="automation_tools" value="none">
                <span>None of the above</span>
            </label>
        </div>
    </div>

    <!-- Question 3: Implementation Timeline -->
    <div class="form-group">
        <label for="timeline">Implementation timeline</label>
        <select id="timeline" name="implementation_timeline" required>
            <option value="">Select your timeline...</option>
            <option value="immediate">Next 30 days</option>
            <option value="q1">Q1 2026</option>
            <option value="this_year">This year</option>
            <option value="flexible">Flexible/Exploratory</option>
        </select>
    </div>

    <!-- Question 4: Budget -->
    <div class="form-group">
        <label for="budget">Approximate automation budget</label>
        <select id="budget" name="automation_budget" required>
            <option value="">Select budget range...</option>
            <option value="0_5k">$0-5K (DIY/open source)</option>
            <option value="5_25k">$5-25K (SaaS platforms)</option>
            <option value="25_100k">$25-100K (serious implementation)</option>
            <option value="100k_plus">$100K+ (enterprise)</option>
        </select>
    </div>

    <!-- Question 5: Pain Point Volume -->
    <div class="form-group">
        <label for="volume">Approximate monthly volume of your main pain point</label>
        <select id="volume" name="pain_point_volume" required>
            <option value="">How often does this occur?</option>
            <option value="10_100">10-100 times/month</option>
            <option value="100_500">100-500 times/month</option>
            <option value="500_1000">500-1,000 times/month</option>
            <option value="1000_5000">1,000-5,000 times/month</option>
            <option value="5000_plus">5,000+ times/month</option>
        </select>
    </div>

    <!-- Question 6: Regulatory Constraints -->
    <div class="form-group">
        <label>Regulatory/compliance requirements</label>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="checkbox" name="regulations" value="hipaa">
                <span>HIPAA (Healthcare)</span>
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="checkbox" name="regulations" value="pci_dss">
                <span>PCI-DSS (Payments)</span>
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="checkbox" name="regulations" value="gdpr_ccpa">
                <span>GDPR/CCPA (Privacy)</span>
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="checkbox" name="regulations" value="sox">
                <span>SOX (Finance)</span>
            </label>
            <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                <input type="checkbox" name="regulations" value="none">
                <span>None</span>
            </label>
        </div>
    </div>

    <div class="info-box">
        <h4>Why we ask</h4>
        <p>This information helps us tailor recommendations to your specific environment and constraints. We use it to predict implementation feasibility and recommend the right tools for your setup.</p>
    </div>
</div>
```

### Update Backend Request Model

**File**: `workflow_system/web/api/workflows.py`

```python
class SubmitRequest(BaseModel):
    """Request from the AI Readiness Compass submission form."""

    # Existing fields
    company_name: str
    website: Optional[str] = None
    industry: str
    company_size: str
    pain_point: str
    prompt: str
    tier: str = "Standard"
    email: str
    contact_name: str

    # NEW FIELDS for readiness scoring
    has_cloud: Literal['yes', 'partial', 'no']
    automation_tools: list[str] = Field(default_factory=list)
    implementation_timeline: Literal['immediate', 'q1', 'this_year', 'flexible']
    automation_budget: Literal['0_5k', '5_25k', '25_100k', '100k_plus']
    pain_point_volume: Literal['10_100', '100_500', '500_1000', '1000_5000', '5000_plus']
    regulations: list[str] = Field(default_factory=list)
```

---

## PHASE 2: SCORING ENGINE (Week 2-3)

### New Directory Structure

```
workflow_system/contexts/readiness/
├── __init__.py
├── models.py              # AIReadinessScore, components
├── scoring_engine.py      # Main scoring logic
├── benchmarks.py          # Industry/size benchmarks (hardcoded data)
└── explainability.py      # Generate human-readable explanations
```

### models.py

```python
# workflow_system/contexts/readiness/models.py

from dataclasses import dataclass
from typing import Literal, Optional
from enum import Enum

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class ScoreComponent:
    """Breakdown of a score component."""
    name: str
    points: int  # Actual points earned
    max_points: int  # Maximum possible
    explanation: str

@dataclass
class AIReadinessScore:
    """Complete AI Readiness Score with breakdown."""

    # Core score
    overall_score: int  # 0-100

    # Component scores (out of 100, then weighted)
    user_input_score: int  # Pain + Tech + Budget + Timeline + Compliance
    benchmark_score: int  # How they compare to industry
    inference_score: int  # From website analysis (added later)

    # Confidence in the assessment
    confidence: ConfidenceLevel
    confidence_reason: str

    # Detailed breakdown
    pain_point_readiness: ScoreComponent  # 0-25 points
    technology_maturity: ScoreComponent   # 0-20 points
    business_fit: ScoreComponent          # 0-15 points
    industry_position: ScoreComponent     # 0-15 points
    inference_signals: Optional[ScoreComponent] = None  # 0-25 points (week 3)

    # Actionable insights
    executive_summary: str  # 1-2 sentence summary
    key_strengths: list[str]  # 3-5 things they do well
    key_gaps: list[str]  # 2-3 things to improve
    recommended_starting_workflows: list[str]  # Top 3 for their situation

    # Metadata
    run_id: str  # Link to workflow run
    calculated_at: datetime
    website_analyzed: bool = False
    public_research_used: bool = False

@dataclass
class ScoreExplanation:
    """Human-readable explanation of score."""
    score: int
    category: Literal['LAGGARD', 'FOLLOWER', 'LEADER', 'PIONEER']
    percentile: int  # vs industry
    summary: str
    next_steps: list[str]
```

### scoring_engine.py

```python
# workflow_system/contexts/readiness/scoring_engine.py

from datetime import datetime
from typing import Optional
import structlog

from web.api.workflows import SubmitRequest
from .models import AIReadinessScore, ScoreComponent, ConfidenceLevel
from .benchmarks import INDUSTRY_BENCHMARKS, COMPANY_SIZE_BASELINES

logger = structlog.get_logger()

class AIReadinessScorer:
    """Calculates AI Readiness Score from user input."""

    def __init__(self, request: SubmitRequest, run_id: str):
        self.request = request
        self.run_id = run_id

    def calculate_score(self) -> AIReadinessScore:
        """Calculate full AI Readiness Score with components."""

        logger.info("calculating_readiness_score", company=self.request.company_name)

        # Calculate each component
        pain_point_score = self._score_pain_point()
        tech_maturity_score = self._score_technology()
        business_fit_score = self._score_business_fit()
        industry_benchmark = self._score_industry_position()

        # Weight components (total: 100 points)
        user_input_total = (
            pain_point_score.points +
            tech_maturity_score.points +
            business_fit_score.points +
            industry_benchmark.points
        )

        # Calculate overall score
        overall_score = min(int(user_input_total), 100)
        confidence = self._assess_confidence()

        # Build result
        result = AIReadinessScore(
            overall_score=overall_score,
            user_input_score=user_input_total,
            benchmark_score=industry_benchmark.points,
            confidence=confidence['level'],
            confidence_reason=confidence['reason'],
            pain_point_readiness=pain_point_score,
            technology_maturity=tech_maturity_score,
            business_fit=business_fit_score,
            industry_position=industry_benchmark,
            executive_summary=self._generate_executive_summary(overall_score),
            key_strengths=self._extract_strengths(overall_score),
            key_gaps=self._extract_gaps(overall_score),
            recommended_starting_workflows=self._recommend_workflows(),
            run_id=self.run_id,
            calculated_at=datetime.now(),
            website_analyzed=False,  # Will be true in Phase 3
        )

        logger.info(
            "readiness_score_calculated",
            company=self.request.company_name,
            score=overall_score,
            confidence=confidence['level'],
        )

        return result

    def _score_pain_point(self) -> ScoreComponent:
        """Score pain point readiness (0-25 points)."""
        base_score = 10

        # Volume scoring (0-10 points)
        volume_map = {
            '10_100': 5,
            '100_500': 8,
            '500_1000': 10,
            '1000_5000': 12,
            '5000_plus': 15,
        }
        volume_score = volume_map.get(self.request.pain_point_volume, 0)

        # Pain point type (implicit in industry/company size)
        # Manual, repetitive processes = higher readiness
        type_bonus = 5  # Assume reasonable pain point from form selection

        points = min(base_score + volume_score + type_bonus, 25)

        return ScoreComponent(
            name="Pain Point Readiness",
            points=points,
            max_points=25,
            explanation=f"High-volume process ({self.request.pain_point_volume}) = good automation candidate"
        )

    def _score_technology(self) -> ScoreComponent:
        """Score technology maturity (0-20 points)."""
        base_score = 8

        # Cloud infrastructure (0-7 points)
        cloud_map = {'yes': 7, 'partial': 4, 'no': 1}
        cloud_score = cloud_map.get(self.request.has_cloud, 0)

        # Automation experience (0-5 points)
        automation_experience = len([t for t in self.request.automation_tools if t != 'none'])
        automation_score = min(automation_experience * 2, 5)

        points = min(base_score + cloud_score + automation_score, 20)

        return ScoreComponent(
            name="Technology Maturity",
            points=points,
            max_points=20,
            explanation=f"Cloud-ready: {self.request.has_cloud}, Automation experience: {len(self.request.automation_tools)} tools"
        )

    def _score_business_fit(self) -> ScoreComponent:
        """Score business fit (0-15 points)."""
        base_score = 8

        # Timeline (0-4 points)
        timeline_map = {
            'immediate': -3,  # Too rushed = mistakes
            'q1': 3,
            'this_year': 4,
            'flexible': 2,
        }
        timeline_score = timeline_map.get(self.request.implementation_timeline, 0)

        # Budget (0-7 points)
        budget_map = {
            '0_5k': 1,
            '5_25k': 4,
            '25_100k': 6,
            '100k_plus': 7,
        }
        budget_score = budget_map.get(self.request.automation_budget, 0)

        # Compliance complexity (0-4 points, negative)
        regulation_complexity = len(self.request.regulations)
        compliance_penalty = min(regulation_complexity * 1, 4)

        points = max(base_score + timeline_score + budget_score - compliance_penalty, 0)
        points = min(points, 15)

        return ScoreComponent(
            name="Business Fit",
            points=points,
            max_points=15,
            explanation=f"Timeline: {self.request.implementation_timeline}, Budget: {self.request.automation_budget}, Regulations: {len(self.request.regulations)}"
        )

    def _score_industry_position(self) -> ScoreComponent:
        """Score vs industry benchmarks (0-15 points)."""
        base_score = 8

        # Get industry baseline
        industry_data = INDUSTRY_BENCHMARKS.get(
            self.request.industry,
            INDUSTRY_BENCHMARKS['Other']
        )
        industry_avg = industry_data['typical_readiness']

        # Get company size baseline
        size_baseline = COMPANY_SIZE_BASELINES.get(
            self.request.company_size,
            50
        )

        # Score relative to industry average
        if size_baseline > industry_avg:
            percentile_bonus = 5  # Above average for size
        elif size_baseline < industry_avg - 10:
            percentile_bonus = -3  # Below average
        else:
            percentile_bonus = 0  # In line with peers

        points = min(base_score + percentile_bonus, 15)
        points = max(points, 5)  # Never below 5 (baseline)

        return ScoreComponent(
            name="Industry Position",
            points=points,
            max_points=15,
            explanation=f"Size baseline: {size_baseline}/100, Industry avg: {industry_avg}/100"
        )

    def _assess_confidence(self) -> dict:
        """Assess confidence in score."""
        # All user-provided inputs = HIGH confidence
        return {
            'level': ConfidenceLevel.HIGH,
            'reason': 'Based on detailed company information from your submission'
        }

    def _generate_executive_summary(self, score: int) -> str:
        """Generate 1-2 sentence summary."""
        industry = self.request.industry
        size = self.request.company_size

        if score >= 80:
            return f"Strong AI automation candidate. Your company size and infrastructure suggest quick implementation wins are achievable in {industry}."
        elif score >= 65:
            return f"Solid foundation for AI automation. {industry} companies like yours typically start with workflow automation in 8-12 weeks."
        elif score >= 50:
            return f"Moderate readiness. Focus first on building automation experience and team capability before scaling across {industry} operations."
        else:
            return f"Early-stage for automation. Starting small with proven tools and team training will build foundation for broader AI initiatives."

    def _extract_strengths(self, score: int) -> list[str]:
        """Extract key strengths from scores."""
        strengths = []

        if self.request.has_cloud == 'yes':
            strengths.append("Cloud infrastructure ready for modern integrations")

        if len(self.request.automation_tools) > 0:
            strengths.append(f"Team experience with {', '.join(self.request.automation_tools)}")

        if self.request.pain_point_volume in ['1000_5000', '5000_plus']:
            strengths.append("High process volume = strong ROI potential for automation")

        if self.request.automation_budget in ['25_100k', '100k_plus']:
            strengths.append("Sufficient budget to implement and support solutions")

        # Return top 3
        return strengths[:3] if strengths else ["Willing to explore AI automation strategies"]

    def _extract_gaps(self, score: int) -> list[str]:
        """Extract key gaps from scores."""
        gaps = []

        if self.request.has_cloud == 'no':
            gaps.append("Legacy infrastructure requires careful integration planning")

        if len([t for t in self.request.automation_tools if t != 'none']) == 0:
            gaps.append("Team lacks hands-on automation platform experience")

        if len(self.request.regulations) > 2:
            gaps.append("Regulatory complexity requires compliance-first approach")

        if self.request.automation_budget == '0_5k':
            gaps.append("Limited budget suggests starting with lowest-cost solutions")

        # Return top 2
        return gaps[:2] if gaps else []

    def _recommend_workflows(self) -> list[str]:
        """Recommend starting workflows based on industry and pain point."""
        # Simplified logic - would be more sophisticated in production
        pain_point = self.request.pain_point
        industry = self.request.industry

        # Industry-specific recommendations
        recommendations_map = {
            'Professional Services': [
                'Lead Qualification & Routing',
                'Proposal Generation',
                'Time Entry & Expense Capture',
            ],
            'Healthcare': [
                'Patient Intake Form Processing',
                'Appointment Reminder Sending',
                'Insurance Verification',
            ],
            'Financial Services': [
                'KYC Data Collection',
                'Compliance Document Management',
                'Trade Order Processing',
            ],
            'Retail': [
                'Customer Inquiry Routing',
                'Inventory Alert Processing',
                'Return Request Automation',
            ],
            'Manufacturing': [
                'Purchase Order Processing',
                'Quality Inspection Data Entry',
                'Supply Chain Notifications',
            ],
        }

        default = [
            'Manual Data Entry Reduction',
            'Email Triage & Routing',
            'Report Generation Automation',
        ]

        return recommendations_map.get(industry, default)

    async def analyze_with_website(self, website_analysis) -> AIReadinessScore:
        """[Week 3] Enhance score with website analysis."""
        # To be implemented in Phase 3
        pass
```

### benchmarks.py

```python
# workflow_system/contexts/readiness/benchmarks.py

INDUSTRY_BENCHMARKS = {
    'Professional Services': {
        'typical_readiness': 72,
        'avg_team_size': 5,
        'common_pain_points': [
            'Lead qualification and follow-up',
            'Proposal generation',
            'Time and expense tracking',
        ],
    },
    'Healthcare': {
        'typical_readiness': 58,
        'avg_team_size': 3,
        'common_pain_points': [
            'Patient intake processing',
            'Insurance verification',
            'Appointment management',
        ],
    },
    'Financial Services': {
        'typical_readiness': 75,
        'avg_team_size': 7,
        'common_pain_points': [
            'KYC data verification',
            'Compliance monitoring',
            'Trade processing',
        ],
    },
    'Retail': {
        'typical_readiness': 62,
        'avg_team_size': 4,
        'common_pain_points': [
            'Inventory management',
            'Customer inquiry response',
            'Return processing',
        ],
    },
    'Manufacturing': {
        'typical_readiness': 68,
        'avg_team_size': 6,
        'common_pain_points': [
            'Purchase order processing',
            'Quality control data',
            'Supply chain tracking',
        ],
    },
    'Technology': {
        'typical_readiness': 78,
        'avg_team_size': 8,
        'common_pain_points': [
            'Customer onboarding',
            'Support ticket routing',
            'Resource allocation',
        ],
    },
    'Other': {
        'typical_readiness': 65,
        'avg_team_size': 4,
        'common_pain_points': [
            'Manual data processing',
            'Document management',
            'Email overload',
        ],
    },
}

COMPANY_SIZE_BASELINES = {
    '1-50': 45,
    '51-200': 55,
    '201-500': 62,
    '501-1000': 68,
    '1001-5000': 72,
    '5000+': 75,
}
```

---

## PHASE 3: WORKFLOW INTEGRATION (Week 3-4)

### Update WorkflowResult Model

**File**: `workflow_system/contexts/workflow/models.py`

Add to `WorkflowResult`:
```python
from contexts.readiness.models import AIReadinessScore

@dataclass
class WorkflowResult:
    # ... existing fields ...

    # NEW: AI Readiness Score
    readiness_score: Optional[AIReadinessScore] = None
```

### Update submit_assessment Endpoint

**File**: `workflow_system/web/api/workflows.py`

```python
from contexts.readiness.scoring_engine import AIReadinessScorer

@router.post("/submit", response_model=SubmitResponse)
async def submit_assessment(request: SubmitRequest):
    """Enhanced with readiness scoring."""
    container = get_container()

    run_id = str(uuid.uuid4())

    logger.info("assessment_submitted", run_id=run_id, company=request.company_name)

    try:
        # CALCULATE READINESS SCORE FIRST
        scorer = AIReadinessScorer(request, run_id)
        readiness_score = scorer.calculate_score()

        logger.info("readiness_score_calculated", run_id=run_id, score=readiness_score.overall_score)

        # Build comprehensive prompt that references readiness score
        full_prompt = f"""Company: {request.company_name}
Industry: {request.industry}
Company Size: {request.company_size}
Website: {request.website or 'Not provided'}
AI Readiness Score: {readiness_score.overall_score}/100

{readiness_score.executive_summary}

Primary Pain Point: {request.pain_point}

Detailed Description:
{request.prompt}

Please analyze this business and recommend the top AI automation workflows that would provide the most value. Focus on practical, implementable solutions using tools like n8n, Zapier, or Make.

Starting point recommendations based on this company's profile:
{', '.join(readiness_score.recommended_starting_workflows)}
"""

        # Process through WorkflowEngine (unchanged)
        engine = WorkflowEngine(
            ai_provider=container.ai_provider(),
            temperatures=container.settings.temperatures,
            min_consensus_votes=container.settings.sc_min_consensus_votes,
        )

        inquiry = EmailInquiry(
            message_id=f"submit-{request.company_name.lower().replace(' ', '-')}",
            from_email=request.email,
            from_name=request.contact_name,
            subject=f"AI Assessment: {request.company_name}",
            body=full_prompt,
        )

        # Process workflow
        result, qa_result = await engine.process_inquiry(
            inquiry=inquiry,
            tier=request.tier,
        )

        # ATTACH READINESS SCORE TO RESULT
        result.readiness_score = readiness_score

        # Send email with readiness score included
        await deliver_workflow_via_email(
            result=result,
            inquiry=inquiry,
            email_client=container.email_client(),
            recipient=request.email,
        )

        return SubmitResponse(
            run_id=run_id,
            status="processing_complete",
            message=f"Your AI Readiness Assessment for {request.company_name} has been processed.",
            tier=request.tier,
            email=request.email,
        )

    except Exception as e:
        logger.error("assessment_failed", run_id=run_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")
```

### Update HTML Report Template

**File**: `shared/delivery.py` - Update email template to include readiness score

Add to the HTML report:

```html
<section style="background: linear-gradient(90deg, #e0f2ff 0%, #e6f0ff 100%); padding: 2rem; margin: 2rem 0; border-radius: 12px;">
    <h2 style="color: #0066cc; margin-top: 0;">Your AI Readiness Score</h2>

    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
            <div style="font-size: 48px; font-weight: bold; color: #0066cc;">
                {readiness_score.overall_score}
            </div>
            <div style="color: #666; font-size: 14px;">
                out of 100 ({readiness_score.industry_position.explanation})
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 16px; color: #666; margin-bottom: 0.5rem;">Confidence Level</div>
            <div style="font-size: 20px; font-weight: bold; color: #00aa00;">
                {readiness_score.confidence}
            </div>
        </div>
    </div>

    <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem;">
        <h3 style="color: #333; margin-top: 0;">What This Means</h3>
        <p style="color: #666; line-height: 1.6;">
            {readiness_score.executive_summary}
        </p>

        <h3 style="color: #333;">Your Strengths</h3>
        <ul style="color: #666;">
            {% for strength in readiness_score.key_strengths %}
                <li>{{ strength }}</li>
            {% endfor %}
        </ul>

        <h3 style="color: #333;">Areas to Address</h3>
        <ul style="color: #666;">
            {% for gap in readiness_score.key_gaps %}
                <li>{{ gap }}</li>
            {% endfor %}
        </ul>

        <h3 style="color: #333;">Recommended Starting Workflows</h3>
        <ol style="color: #666;">
            {% for workflow in readiness_score.recommended_starting_workflows %}
                <li>{{ workflow }}</li>
            {% endfor %}
        </ol>
    </div>

    <div style="background: #f9f9f9; padding: 1rem; border-left: 4px solid #0066cc; margin-bottom: 1.5rem;">
        <p style="color: #666; font-size: 13px; margin: 0;">
            <strong>How we calculated this score:</strong>
            {% for component in [readiness_score.pain_point_readiness, readiness_score.technology_maturity, readiness_score.business_fit, readiness_score.industry_position] %}
                • {{ component.name }}: {{ component.points }}/{{ component.max_points }} ({{ component.explanation }}) <br>
            {% endfor %}
        </p>
    </div>
</section>
```

---

## TESTING CHECKLIST

- [ ] Unit tests for `AIReadinessScorer` (high/medium/low scores)
- [ ] Integration test: SubmitRequest → ReadinessScore → HTML email
- [ ] Manual testing: Verify score appears in email
- [ ] Verify score calculation logic with edge cases:
  - Small startup with huge problem volume
  - Large enterprise with no automation experience
  - Highly regulated business with tight budget
- [ ] Test form validation on new fields
- [ ] Test HTML email rendering with score section

---

## DEPLOYMENT CHECKLIST

- [ ] Database migration (if storing scores)
- [ ] Deploy form changes
- [ ] Deploy scoring engine
- [ ] Update HTML email template
- [ ] Monitor for errors in `submit_assessment` endpoint
- [ ] Verify scores appear in sent emails

---

## Success Metrics

By end of Week 4:
- All users receive readiness score in their report
- Score breakdowns visible in HTML email
- Score included in Premium tier strategy narrative
- Zero errors in scoring calculation
- All test cases passing

