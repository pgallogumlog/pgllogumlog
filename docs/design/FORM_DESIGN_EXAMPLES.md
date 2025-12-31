# AI Readiness Compass Form - Design Examples & Code Snippets

**Purpose**: Tactical examples for implementing the 5-question recommendation
**Audience**: Designer implementing form additions
**Date**: 2025-12-31

---

## 1. Question Format Examples

### Q1: Current AI Adoption (Radio Buttons)

#### Visual Design

```
How would you describe your current AI and automation adoption?

○ New to AI
  Little to no current AI/automation

○ Early Stage
  Some automation in 1-2 processes

○ Growing
  Multiple automated workflows in place

○ Advanced
  AI/automation is core to operations
```

#### HTML Implementation

```html
<div class="form-group">
  <label class="question-label">
    How would you describe your current AI and automation adoption?
    <span class="help-icon" title="This helps us recommend appropriate complexity level">?</span>
  </label>

  <div class="radio-group">
    <label class="radio-option">
      <input type="radio" name="ai_adoption" value="new" required>
      <span class="radio-text">
        <strong>New to AI</strong>
        <span class="option-description">Little to no current AI/automation</span>
      </span>
    </label>

    <label class="radio-option">
      <input type="radio" name="ai_adoption" value="early_stage">
      <span class="radio-text">
        <strong>Early Stage</strong>
        <span class="option-description">Some automation in 1-2 processes</span>
      </span>
    </label>

    <label class="radio-option">
      <input type="radio" name="ai_adoption" value="growing">
      <span class="radio-text">
        <strong>Growing</strong>
        <span class="option-description">Multiple automated workflows in place</span>
      </span>
    </label>

    <label class="radio-option">
      <input type="radio" name="ai_adoption" value="advanced">
      <span class="radio-text">
        <strong>Advanced</strong>
        <span class="option-description">AI/automation is core to operations</span>
      </span>
    </label>
  </div>
</div>
```

#### CSS Styling

```css
.question-label {
  display: block;
  margin-bottom: 1rem;
  color: #8892b0;
  font-weight: 500;
  font-size: 1rem;
}

.help-icon {
  display: inline-block;
  width: 16px;
  height: 16px;
  margin-left: 0.5rem;
  background: rgba(0,212,255,0.2);
  border: 1px solid rgba(0,212,255,0.4);
  border-radius: 50%;
  text-align: center;
  line-height: 16px;
  font-size: 0.75rem;
  color: #00d4ff;
  cursor: help;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.radio-option {
  display: flex;
  align-items: flex-start;
  padding: 1rem;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  background: rgba(255,255,255,0.02);
  cursor: pointer;
  transition: all 0.2s ease;
}

.radio-option:hover {
  border-color: rgba(0,212,255,0.3);
  background: rgba(0,212,255,0.05);
}

.radio-option input[type="radio"] {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  margin-top: 2px;
  margin-right: 1rem;
  cursor: pointer;
  accent-color: #00d4ff;
}

.radio-option input[type="radio"]:focus {
  outline: 2px solid #00d4ff;
  outline-offset: 2px;
}

.radio-text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.option-description {
  color: #5a6a8a;
  font-size: 0.85rem;
  font-weight: normal;
}

/* Selected state */
.radio-option input[type="radio"]:checked + .radio-text strong {
  color: #00d4ff;
}

.radio-option input[type="radio"]:checked {
  accent-color: #00d4ff;
}
```

#### JavaScript Behavior

```javascript
// Auto-scroll next section into view when radio selected
document.querySelectorAll('input[name="ai_adoption"]').forEach(radio => {
  radio.addEventListener('change', () => {
    // Show next question with delay for visual feedback
    setTimeout(() => {
      // Next question reveals here
    }, 200);
  });
});
```

---

### Q2: Technical Infrastructure (Range Slider)

#### Visual Design

```
How mature is your technical infrastructure?

[●──────────────────────────────]
Minimal                        Sophisticated
(Spreadsheets)              (APIs, Databases)

Current selection: Moderate
```

#### HTML Implementation

```html
<div class="form-group">
  <label class="question-label">
    How mature is your technical infrastructure?
    <span class="help-icon" title="Select based on your current tools and systems">?</span>
  </label>

  <div class="slider-container">
    <input
      type="range"
      id="tech_infrastructure"
      name="tech_infrastructure"
      min="1"
      max="10"
      value="5"
      class="tech-slider"
      aria-label="Technical infrastructure maturity"
    >

    <div class="slider-labels">
      <span class="slider-start">Minimal<br>(Spreadsheets)</span>
      <span class="slider-middle">Moderate<br>(Modern Tools)</span>
      <span class="slider-end">Sophisticated<br>(APIs, DBs)</span>
    </div>
  </div>

  <div class="slider-value-display">
    <span id="tech-value-label">Moderate</span>
    <span class="slider-hint" id="tech-hint">
      You can use no-code platforms and some API integrations
    </span>
  </div>
</div>
```

#### CSS Styling

```css
.slider-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 1.5rem 0;
}

.tech-slider {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: linear-gradient(
    90deg,
    rgba(0,212,255,0.2) 0%,
    rgba(0,212,255,0.3) 33%,
    rgba(124,58,237,0.2) 100%
  );
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

/* Webkit browsers (Chrome, Safari, Edge) */
.tech-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00d4ff, #7c3aed);
  cursor: pointer;
  border: 2px solid rgba(255,255,255,0.2);
  box-shadow: 0 2px 8px rgba(0,212,255,0.3);
  transition: all 0.2s ease;
}

.tech-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 4px 12px rgba(0,212,255,0.5);
  transform: scale(1.1);
}

.tech-slider::-webkit-slider-thumb:active {
  transform: scale(0.95);
}

/* Firefox */
.tech-slider::-moz-range-thumb {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00d4ff, #7c3aed);
  cursor: pointer;
  border: 2px solid rgba(255,255,255,0.2);
  box-shadow: 0 2px 8px rgba(0,212,255,0.3);
}

/* Focus state for accessibility */
.tech-slider:focus {
  outline: 2px solid #00d4ff;
  outline-offset: 4px;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  color: #5a6a8a;
  font-size: 0.8rem;
  line-height: 1.3;
  text-align: center;
}

.slider-labels span {
  flex: 1;
}

.slider-value-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(0,212,255,0.05);
  border-radius: 6px;
  border: 1px solid rgba(0,212,255,0.1);
}

#tech-value-label {
  font-weight: 600;
  color: #00d4ff;
  font-size: 1.1rem;
}

.slider-hint {
  color: #8892b0;
  font-size: 0.85rem;
  text-align: right;
}
```

#### JavaScript Behavior

```javascript
const slider = document.getElementById('tech_infrastructure');
const valueLabel = document.getElementById('tech-value-label');
const hint = document.getElementById('tech-hint');

// Map numeric slider value to label and hint
const maturityLevels = {
  1: { label: 'Minimal', hint: 'You can use basic no-code tools like Zapier' },
  2: { label: 'Minimal', hint: 'You can use basic no-code tools like Zapier' },
  3: { label: 'Minimal', hint: 'You can use basic no-code tools like Zapier' },
  4: { label: 'Moderate', hint: 'You can use modern platforms and some API integrations' },
  5: { label: 'Moderate', hint: 'You can use modern platforms and some API integrations' },
  6: { label: 'Moderate', hint: 'You can use modern platforms and some API integrations' },
  7: { label: 'Sophisticated', hint: 'You can implement custom integrations and ML models' },
  8: { label: 'Sophisticated', hint: 'You can implement custom integrations and ML models' },
  9: { label: 'Sophisticated', hint: 'You can implement custom integrations and ML models' },
  10: { label: 'Sophisticated', hint: 'You can implement complex enterprise solutions' }
};

slider.addEventListener('input', (e) => {
  const value = parseInt(e.target.value);
  const { label, hint } = maturityLevels[value];

  valueLabel.textContent = label;
  hint.textContent = hint;

  // Optional: Send analytics
  trackFormInteraction('tech_infrastructure_changed', { value });
});

// Initialize on page load
const initialValue = parseInt(slider.value);
const { label, hint } = maturityLevels[initialValue];
valueLabel.textContent = label;
hint.textContent = hint;
```

---

### Q3: Organizational Change Readiness (Dropdown with Descriptions)

#### Visual Design

```
How quickly can your organization implement changes?

[Select your implementation pace...]  ▼

[Dropdown open]
▼ We move slowly (6-12 month cycles)
  For: Regulated industries, large orgs

▼ We move at normal pace (3-6 months)
  For: Established mid-market companies

▼ We move quickly (1-3 months)
  For: Startups, agile teams

▼ We're very rapid (weeks)
  For: Tech-forward, venture-backed
```

#### HTML Implementation

```html
<div class="form-group">
  <label for="change_readiness" class="question-label">
    How quickly can your organization implement changes?
    <span class="help-icon" title="Select based on your typical project timeline">?</span>
  </label>

  <select
    id="change_readiness"
    name="change_readiness"
    class="custom-select"
    required
    aria-describedby="change-readiness-help"
  >
    <option value="">Select your implementation pace...</option>
    <option value="slow">We move slowly (6-12 month cycles)</option>
    <option value="normal">We move at normal pace (3-6 month cycles)</option>
    <option value="fast">We move quickly (1-3 month cycles)</option>
    <option value="very_fast">We're very rapid (weeks)</option>
  </select>

  <div id="change-readiness-help" class="select-help-text"></div>
</div>
```

#### CSS Styling

```css
.custom-select {
  width: 100%;
  padding: 0.75rem;
  background: rgba(255,255,255,0.1) url('data:image/svg+xml,...') no-repeat right 0.75rem center;
  background-size: 1.2em;
  padding-right: 2.5rem;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 8px;
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
  appearance: none;
  transition: all 0.2s ease;
}

.custom-select:hover {
  border-color: rgba(0,212,255,0.3);
  background-color: rgba(255,255,255,0.12);
}

.custom-select:focus {
  outline: none;
  border-color: #00d4ff;
  box-shadow: 0 0 0 3px rgba(0,212,255,0.1);
}

.custom-select option {
  background: #1a1a2e;
  color: #fff;
  padding: 0.5rem;
}

.custom-select option:checked {
  background: #00d4ff;
  color: #1a1a2e;
}

.select-help-text {
  margin-top: 0.5rem;
  color: #8892b0;
  font-size: 0.85rem;
  min-height: 1.2rem;
  transition: color 0.2s ease;
}

/* Dynamic help text shown on selection */
.select-help-text.show-guidance {
  color: #00d4ff;
  font-weight: 500;
}
```

#### JavaScript Behavior

```javascript
const changeSelect = document.getElementById('change_readiness');
const helpText = document.getElementById('change-readiness-help');

const helpGuidance = {
  slow: 'You'll benefit from a phased roadmap (Phase 1 → 6 months → Phase 2 → 6 months → Phase 3). We'll focus on automation that works with your change management process.',
  normal: 'We'll create a balanced 4-phase roadmap spanning 12-18 months. Gives your team time to adopt while maintaining momentum.',
  fast: 'We can recommend quick-win automations (1-month implementation) plus longer-term strategic workflows. Your roadmap will prioritize speed.',
  very_fast: 'We can suggest aggressive automation strategy with rapid iterations. Roadmap will focus on high-impact, quickly-implementable workflows.'
};

changeSelect.addEventListener('change', (e) => {
  const value = e.target.value;
  if (value && helpGuidance[value]) {
    helpText.textContent = helpGuidance[value];
    helpText.classList.add('show-guidance');
  } else {
    helpText.textContent = '';
    helpText.classList.remove('show-guidance');
  }
});
```

---

### Q4: Budget Constraints (Radio Buttons)

#### Visual Design

```
What's your comfort zone for implementation investment?

○ Keep it lean
  < $5K implementation budget
  (Good for: Quick wins, pilot projects)

○ Moderate investment
  $5K - $25K
  (Good for: Foundational automation program)

○ Significant investment
  $25K - $100K+
  (Good for: Comprehensive transformation)
```

#### HTML Implementation

```html
<div class="form-group">
  <label class="question-label">
    What's your comfort zone for implementation investment?
    <span class="help-icon" title="This helps us recommend appropriately-scoped solutions">?</span>
  </label>

  <div class="radio-group">
    <label class="radio-option budget-option">
      <input type="radio" name="budget_zone" value="lean" required>
      <div class="radio-text">
        <strong>Keep it lean</strong>
        <span class="option-price">&lt; $5K</span>
        <span class="option-description">Good for: Quick wins, pilot projects</span>
      </div>
    </label>

    <label class="radio-option budget-option">
      <input type="radio" name="budget_zone" value="moderate">
      <div class="radio-text">
        <strong>Moderate investment</strong>
        <span class="option-price">$5K - $25K</span>
        <span class="option-description">Good for: Foundational automation program</span>
      </div>
    </label>

    <label class="radio-option budget-option">
      <input type="radio" name="budget_zone" value="significant">
      <div class="radio-text">
        <strong>Significant investment</strong>
        <span class="option-price">$25K - $100K+</span>
        <span class="option-description">Good for: Comprehensive transformation</span>
      </div>
    </label>
  </div>
</div>
```

#### CSS Addition

```css
.budget-option .option-price {
  display: block;
  color: #00d4ff;
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0.25rem 0;
}
```

---

### Q5: Success Definition (Radio + Optional Text)

#### Visual Design

```
What would success look like for your company in 12 months?

○ Massive time savings
  We need to free up 40+ hours/week of manual work
  [Optional: Hours/week currently spent: _____]

○ Faster processes
  Speed up our bottleneck operations
  [Optional: Current timeline: _____ → Desired: _____]

○ Better quality
  Reduce errors, improve consistency
  [Optional: Current error rate: _____]

○ Revenue impact
  Enable new capabilities or upsell opportunities
  [Optional: Potential revenue opportunity: $_____]

○ Compliance/Risk
  Reduce compliance burden or mitigate risk
  [Optional: Specific compliance challenge: _____]
```

#### HTML Implementation

```html
<div class="form-group">
  <label class="question-label">
    What would success look like for your company in 12 months?
    <span class="help-icon" title="This focuses your recommendations on your real business goals">?</span>
  </label>

  <div class="radio-group">
    <!-- Option 1: Time Savings -->
    <div class="success-option">
      <label class="radio-option">
        <input type="radio" name="success_metric" value="time_savings"
               onchange="toggleSuccessDetail(this)">
        <div class="radio-text">
          <strong>Massive time savings</strong>
          <span class="option-description">
            We need to free up 40+ hours/week of manual work
          </span>
        </div>
      </label>
      <div class="success-detail" id="time_savings_detail" style="display: none;">
        <div class="detail-input-group">
          <label for="time_savings_hours">
            Hours/week currently spent on manual work:
          </label>
          <input type="number" id="time_savings_hours"
                 name="time_savings_hours"
                 placeholder="e.g., 20, 40"
                 min="1" max="168">
        </div>
      </div>
    </div>

    <!-- Option 2: Faster Processes -->
    <div class="success-option">
      <label class="radio-option">
        <input type="radio" name="success_metric" value="faster_processes"
               onchange="toggleSuccessDetail(this)">
        <div class="radio-text">
          <strong>Faster processes</strong>
          <span class="option-description">
            Speed up our bottleneck operations
          </span>
        </div>
      </label>
      <div class="success-detail" id="faster_processes_detail" style="display: none;">
        <div class="detail-input-group">
          <label for="current_timeline">Current timeline:</label>
          <input type="text" id="current_timeline"
                 name="current_timeline"
                 placeholder="e.g., 5 days, 2 weeks">
          <label for="desired_timeline">Desired timeline:</label>
          <input type="text" id="desired_timeline"
                 name="desired_timeline"
                 placeholder="e.g., 1 day, 24 hours">
        </div>
      </div>
    </div>

    <!-- Option 3: Better Quality -->
    <div class="success-option">
      <label class="radio-option">
        <input type="radio" name="success_metric" value="better_quality"
               onchange="toggleSuccessDetail(this)">
        <div class="radio-text">
          <strong>Better quality</strong>
          <span class="option-description">
            Reduce errors, improve consistency
          </span>
        </div>
      </label>
      <div class="success-detail" id="better_quality_detail" style="display: none;">
        <div class="detail-input-group">
          <label for="error_rate">Current error rate or quality issue:</label>
          <textarea id="error_rate" name="error_rate"
                    placeholder="e.g., 5% manual data entry errors, inconsistent formatting"
                    rows="2"></textarea>
        </div>
      </div>
    </div>

    <!-- Option 4: Revenue Impact -->
    <div class="success-option">
      <label class="radio-option">
        <input type="radio" name="success_metric" value="revenue_impact"
               onchange="toggleSuccessDetail(this)">
        <div class="radio-text">
          <strong>Revenue impact</strong>
          <span class="option-description">
            Enable new capabilities or upsell opportunities
          </span>
        </div>
      </label>
      <div class="success-detail" id="revenue_impact_detail" style="display: none;">
        <div class="detail-input-group">
          <label for="revenue_opportunity">Potential revenue opportunity:</label>
          <div class="input-prefix">
            <span>$</span>
            <input type="number" id="revenue_opportunity"
                   name="revenue_opportunity"
                   placeholder="e.g., 100000"
                   min="0">
          </div>
        </div>
      </div>
    </div>

    <!-- Option 5: Compliance/Risk -->
    <div class="success-option">
      <label class="radio-option">
        <input type="radio" name="success_metric" value="compliance_risk"
               onchange="toggleSuccessDetail(this)">
        <div class="radio-text">
          <strong>Compliance/Risk</strong>
          <span class="option-description">
            Reduce compliance burden or mitigate risk
          </span>
        </div>
      </label>
      <div class="success-detail" id="compliance_risk_detail" style="display: none;">
        <div class="detail-input-group">
          <label for="compliance_challenge">Specific compliance challenge:</label>
          <textarea id="compliance_challenge" name="compliance_challenge"
                    placeholder="e.g., Manual audit trail maintenance, HIPAA compliance tracking"
                    rows="2"></textarea>
        </div>
      </div>
    </div>
  </div>
</div>
```

#### CSS Styling

```css
.success-option {
  display: flex;
  flex-direction: column;
  margin-bottom: 1rem;
}

.success-option .radio-option {
  margin-bottom: 0.75rem;
}

.success-detail {
  display: none;
  margin-left: 2.5rem;
  padding: 1rem;
  background: rgba(0,212,255,0.05);
  border-left: 2px solid #00d4ff;
  border-radius: 0 8px 8px 0;
  animation: slideInDetails 0.2s ease-out;
}

.success-detail.show {
  display: block;
}

@keyframes slideInDetails {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.detail-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-input-group label {
  color: #8892b0;
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}

.detail-input-group input,
.detail-input-group textarea {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 6px;
  padding: 0.5rem;
  color: #fff;
  font-size: 0.9rem;
}

.input-prefix {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.input-prefix span {
  color: #00d4ff;
  font-weight: 600;
}

.input-prefix input {
  flex: 1;
}
```

#### JavaScript Behavior

```javascript
function toggleSuccessDetail(radio) {
  // Hide all details
  document.querySelectorAll('.success-detail').forEach(detail => {
    detail.classList.remove('show');
    detail.style.display = 'none';
  });

  // Show selected detail
  if (radio.value) {
    const detailId = `${radio.value}_detail`;
    const detail = document.getElementById(detailId);
    if (detail) {
      detail.classList.add('show');
      detail.style.display = 'block';

      // Auto-focus first input for accessibility
      const firstInput = detail.querySelector('input, textarea');
      if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
      }
    }
  }
}
```

---

## 2. Progressive Disclosure Implementation

### HTML Structure for Progressive Reveal

```html
<!-- Assessment Scope Section (Hidden Initially) -->
<div class="form-section" id="assessment-scope-section"
     style="display: none; animation: slideDown 0.3s ease-out;">
  <h2 class="section-title">
    <span class="section-number">2.5</span>
    Assessment Scope
  </h2>
  <p class="section-description">
    A few quick questions help us personalize your recommendations.
    <span class="time-estimate">(About 2 minutes)</span>
  </p>

  <!-- Progress indicator -->
  <div class="progress-bar">
    <div class="progress-fill" style="width: 0%;"></div>
  </div>

  <!-- All 5 questions here -->
  <!-- Q1, Q2, Q3, Q4, Q5... -->
</div>

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### JavaScript: When to Reveal

```javascript
// Watch for when "Your Challenge" section is complete
function checkChallengeSectionComplete() {
  const painPointSelect = document.getElementById('painPoint');
  const promptTextarea = document.getElementById('prompt');

  const isPainPointFilled = painPointSelect.value !== '';
  const isPromptFilled = promptTextarea.value.trim().length > 20;

  return isPainPointFilled && isPromptFilled;
}

function updateAssessmentScopeVisibility() {
  const assessmentScope = document.getElementById('assessment-scope-section');
  const isComplete = checkChallengeSectionComplete();

  if (isComplete && assessmentScope.style.display === 'none') {
    // Reveal with animation
    assessmentScope.style.display = 'block';

    // Smooth scroll into view
    setTimeout(() => {
      assessmentScope.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      });
    }, 100);
  }
}

// Monitor changes in Challenge section
document.getElementById('painPoint').addEventListener('change', updateAssessmentScopeVisibility);
document.getElementById('prompt').addEventListener('input', updateAssessmentScopeVisibility);

// Also check on page load (in case user goes back)
document.addEventListener('DOMContentLoaded', updateAssessmentScopeVisibility);
```

---

## 3. Form Data Collection & Submission

### Updated Form Data Structure

```javascript
// When form is submitted, collect all data including assessment scope
const formData = {
  // Existing fields
  company_name: document.getElementById('companyName').value,
  website: document.getElementById('website').value,
  industry: document.getElementById('industry').value,
  company_size: document.getElementById('companySize').value,
  pain_point: document.getElementById('painPoint').value,
  prompt: document.getElementById('prompt').value,
  tier: document.querySelector('input[name="tier"]:checked').value,
  email: document.getElementById('email').value,
  contact_name: document.getElementById('name').value,

  // NEW: Assessment scope questions
  ai_adoption: document.querySelector('input[name="ai_adoption"]:checked')?.value || null,
  tech_infrastructure: document.getElementById('tech_infrastructure').value,
  change_readiness: document.getElementById('change_readiness').value,
  budget_zone: document.querySelector('input[name="budget_zone"]:checked')?.value || null,
  success_metric: document.querySelector('input[name="success_metric"]:checked')?.value || null,

  // Optional detail fields for success metric
  time_savings_hours: document.getElementById('time_savings_hours')?.value || null,
  current_timeline: document.getElementById('current_timeline')?.value || null,
  desired_timeline: document.getElementById('desired_timeline')?.value || null,
  error_rate: document.getElementById('error_rate')?.value || null,
  revenue_opportunity: document.getElementById('revenue_opportunity')?.value || null,
  compliance_challenge: document.getElementById('compliance_challenge')?.value || null,
};
```

### Form Validation Enhancement

```javascript
function validateAssessmentScope() {
  const errors = [];

  // Assessment scope questions are required
  if (!document.querySelector('input[name="ai_adoption"]:checked')) {
    errors.push('Please select your AI adoption level');
  }

  if (!document.getElementById('tech_infrastructure').value) {
    errors.push('Please select your technical infrastructure level');
  }

  if (!document.getElementById('change_readiness').value) {
    errors.push('Please select your implementation pace');
  }

  if (!document.querySelector('input[name="budget_zone"]:checked')) {
    errors.push('Please select your budget zone');
  }

  if (!document.querySelector('input[name="success_metric"]:checked')) {
    errors.push('Please select your success metric');
  }

  return errors;
}

// Enhance existing form submission
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  // Existing validation
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  // NEW: Validate assessment scope if visible
  const assessmentScope = document.getElementById('assessment-scope-section');
  if (assessmentScope.style.display !== 'none') {
    const scopeErrors = validateAssessmentScope();
    if (scopeErrors.length > 0) {
      alert(scopeErrors.join('\n'));
      return;
    }
  }

  // ... continue with submission
});
```

---

## 4. Accessibility Specifications

### ARIA Attributes

```html
<!-- Radio group with proper ARIA -->
<fieldset>
  <legend class="question-label">
    How would you describe your current AI and automation adoption?
  </legend>

  <div role="radiogroup" aria-required="true" aria-label="AI adoption level">
    <label class="radio-option">
      <input type="radio" name="ai_adoption" value="new"
             aria-describedby="ai-adoption-help">
      <span class="radio-text">
        <strong>New to AI</strong>
        <span id="ai-adoption-help">Little to no current AI/automation</span>
      </span>
    </label>
    <!-- More options... -->
  </div>
</fieldset>

<!-- Slider with proper ARIA -->
<div class="form-group">
  <label for="tech_infrastructure">Technical Infrastructure</label>
  <input
    type="range"
    id="tech_infrastructure"
    aria-label="Technical infrastructure maturity"
    aria-valuemin="1"
    aria-valuemax="10"
    aria-valuenow="5"
    aria-valuetext="Moderate"
  >
</div>
```

### Keyboard Navigation

```css
/* Ensure all interactive elements are focusable */
input, select, textarea, button, [role="button"], [role="radio"] {
  outline: 2px solid transparent;
  outline-offset: 2px;
}

/* Visible focus state (never remove outline) */
input:focus,
select:focus,
textarea:focus,
button:focus,
[role="radio"]:focus {
  outline: 2px solid #00d4ff;
  outline-offset: 2px;
}

/* Focus visible for keyboard users only */
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
button:focus-visible {
  outline: 2px solid #00d4ff;
  outline-offset: 2px;
}
```

---

## 5. Mobile Responsiveness

### Responsive Adjustments

```css
/* Mobile: Stack options vertically */
@media (max-width: 600px) {
  .radio-group {
    gap: 0.5rem;
  }

  .radio-option {
    padding: 0.75rem;
  }

  .radio-option input[type="radio"] {
    width: 18px;
    height: 18px;
  }

  /* Make touch targets larger on mobile */
  .radio-option {
    min-height: 44px;
  }

  /* Slider takes full width on mobile */
  .slider-container {
    margin: 1rem 0;
  }

  /* Stack slider labels on mobile */
  .slider-labels {
    flex-direction: column;
    gap: 0.5rem;
    text-align: left;
  }

  /* Success details adjust on mobile */
  .success-detail {
    margin-left: 0;
    margin-top: 0.5rem;
    padding-left: 0.75rem;
  }

  /* Form fields full width */
  input[type="text"],
  input[type="number"],
  textarea {
    font-size: 16px; /* Prevents zoom on iOS */
  }
}

/* Tablet: Some optimization */
@media (max-width: 768px) {
  .detail-input-group {
    gap: 0.4rem;
  }

  .option-description {
    font-size: 0.8rem;
  }
}
```

---

## 6. Analytics & Tracking

### Event Tracking Implementation

```javascript
// Track form interactions for metrics
function trackFormEvent(eventName, data = {}) {
  // Send to analytics service (Google Analytics, Mixpanel, etc.)
  if (typeof gtag !== 'undefined') {
    gtag('event', eventName, {
      event_category: 'form',
      event_label: 'ai_readiness_compass',
      ...data
    });
  }
}

// Track when assessment scope reveals
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.target.id === 'assessment-scope-section'
        && mutation.target.style.display !== 'none') {
      trackFormEvent('assessment_scope_revealed');
    }
  });
});

observer.observe(document.getElementById('assessment-scope-section'),
  { attributes: true, attributeFilter: ['style'] });

// Track each question completion
document.querySelectorAll('input[name^="ai_adoption"], input[name^="budget_zone"]').forEach(radio => {
  radio.addEventListener('change', (e) => {
    trackFormEvent('form_question_answered', {
      question: e.target.name,
      value: e.target.value
    });
  });
});

// Track form submission time
let formStartTime = Date.now();
form.addEventListener('submit', async (e) => {
  const completionTime = Date.now() - formStartTime;
  trackFormEvent('form_submitted', {
    completion_time_ms: completionTime,
    tier: document.querySelector('input[name="tier"]:checked').value
  });
});
```

---

## Summary of Files to Update

1. **`web/ui/templates/submit.html`** - Add HTML markup for 5 questions
2. **`web/ui/templates/submit.html` (styles)** - Add CSS for new components
3. **`web/ui/templates/submit.html` (scripts)** - Add JavaScript for behaviors
4. **`web/api/workflows.py`** - Update API model to accept new fields
5. **`contexts/workflow/models.py`** - Add fields to form model
6. **`contexts/workflow/prompts.py`** - Update AI prompts to reference new data

**Total implementation scope**: ~500 lines of code (HTML + CSS + JS) + API updates

---
