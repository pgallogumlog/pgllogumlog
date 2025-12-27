# Technical Debt Log

**Project:** Workflow Automation System - Test Runner & HTML Results Browser
**Last Updated:** 2025-12-27
**Total Items:** 18 (0 P0, 7 P1, 5 P2, 6 P3)

---

## Priority Definitions

- **P0 (Critical):** Blocking bugs, system down, data loss
- **P1 (High):** Non-critical bugs, security gaps for production
- **P2 (Medium):** Missing tests, scalability issues, technical improvements
- **P3 (Low):** Nice-to-have features, UX enhancements

---

## P0 - Critical Issues

**Status:** None ✅

---

## P1 - High Priority

### [P1-001] Timestamp Parsing Bug in Filename Metadata
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Bug
- **Location:** `web/api/tests.py` line 310 (`_parse_filename_metadata()`)
- **Description:** Parser only extracts time portion (`parts[-2]`) from filename, missing date portion (`parts[-3]`)
- **Impact:** Timestamps fall back to file modification time (system still works but displays incorrect creation time)
- **Current Behavior:**
  ```python
  timestamp_str = parts[-2]  # Gets '145030' only
  ```
- **Expected Fix:**
  ```python
  timestamp_str = parts[-3] + '_' + parts[-2]  # Gets '20251227_145030'
  dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
  ```
- **Effort:** 15 minutes
- **Dependencies:** None
- **Blocker For:** Accurate timestamp display in results browser

---

### [P1-002] No Authentication on Delete Endpoints
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Security
- **Location:** `web/api/tests.py` endpoints (DELETE operations)
- **Description:** DELETE endpoints have no authentication - anyone with server access can delete files
- **Impact:** Unauthorized users can delete test results
- **Recommendation:**
  - Add authentication middleware to FastAPI
  - Require login or API key for DELETE operations
  - Consider session-based auth or JWT tokens
- **Effort:** 4-8 hours
- **Dependencies:** Authentication system design choice
- **Blocker For:** Production deployment

---

### [P1-003] No CSRF Protection on DELETE Operations
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Security
- **Location:** `web/api/tests.py` DELETE endpoints, `test_runner.html` JavaScript
- **Description:** DELETE operations vulnerable to CSRF attacks
- **Impact:** Malicious sites could trigger deletions if user is authenticated
- **Recommendation:**
  - Implement CSRF token generation and validation
  - Add CSRF token to all DELETE requests
  - Use FastAPI CSRF middleware or custom implementation
- **Effort:** 4 hours
- **Dependencies:** [P1-002] Authentication must be implemented first
- **Blocker For:** Production deployment

---

### [P1-004] No Rate Limiting
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Security / Performance
- **Location:** All API endpoints (especially DELETE)
- **Description:** No rate limiting allows spam/DOS attacks via repeated delete operations
- **Impact:** Server resources could be exhausted, legitimate users affected
- **Recommendation:**
  - Add rate limiting middleware (e.g., slowapi)
  - Limit to 10 deletes per minute per IP
  - Limit to 60 list requests per minute per IP
- **Effort:** 2-4 hours
- **Dependencies:** None
- **Blocker For:** Production deployment

---

### [P1-005] No Audit Logging for Deletions
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Security / Compliance
- **Location:** `web/api/tests.py` DELETE endpoints
- **Description:** File deletions not logged (who, when, what deleted)
- **Impact:** Cannot investigate security incidents, no accountability
- **Recommendation:**
  - Log all DELETE operations with structlog
  - Include: timestamp, user (when auth added), filename(s), IP address
  - Store in dedicated audit log file or database
- **Effort:** 2 hours
- **Dependencies:** [P1-002] for user identification
- **Blocker For:** Compliance requirements, production deployment

---

### [P1-006] No Content Security Policy Headers
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Security
- **Location:** `web/app.py` (FastAPI middleware)
- **Description:** HTML files served without CSP headers, could execute malicious scripts
- **Impact:** XSS attacks possible if HTML files contain malicious content
- **Recommendation:**
  - Add CSP middleware to FastAPI
  - Set restrictive CSP for served HTML files
  - Example: `Content-Security-Policy: default-src 'self'; script-src 'none'`
- **Effort:** 2 hours
- **Dependencies:** None
- **Blocker For:** Production deployment

---

### [P1-007] No Unit Tests for Helper Functions
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Testing
- **Location:** `web/api/tests.py` helper functions
- **Description:** `_validate_filename()`, `_parse_filename_metadata()`, `_get_results_dir()` only tested via integration tests
- **Impact:** Edge cases harder to test, refactoring risky
- **Recommendation:**
  - Create `tests/unit/web/test_api_tests.py`
  - Add unit tests for each helper function
  - Test edge cases: malformed filenames, encoding issues, etc.
- **Effort:** 4 hours
- **Dependencies:** None
- **Blocker For:** None (good practice)

---

## P2 - Medium Priority

### [P2-001] No Pagination for Results List
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Scalability / Performance
- **Location:** `web/api/tests.py` `list_html_results()`, `test_runner.html`
- **Description:** All results returned at once - slow with 1000+ files
- **Impact:** Page load slow, UI cluttered, high bandwidth usage
- **Recommendation:**
  - Add pagination to GET /api/tests/results
  - Query params: `?page=1&per_page=20`
  - Update UI with "Load More" or page navigation
  - Default: 50 results per page
- **Effort:** 6 hours
- **Dependencies:** None
- **Blocker For:** Large-scale testing (100+ test runs)

---

### [P2-002] No Disk Space Management
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Operations / Scalability
- **Location:** `test_results/` directory, needs new cleanup service
- **Description:** HTML files accumulate indefinitely (1000 tests = ~40MB)
- **Impact:** Disk space exhaustion over time
- **Recommendation:**
  - Add scheduled cleanup task (delete files older than 7 days)
  - Add disk space monitoring endpoint
  - Add warning in UI when test_results/ exceeds 100MB
  - Could use FastAPI background tasks or cron job
- **Effort:** 4 hours
- **Dependencies:** None
- **Blocker For:** Long-term production use

---

### [P2-003] No File Size Limits
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Security / Operations
- **Location:** `contexts/testing/orchestrator.py` `_save_html_proposal()`
- **Description:** No validation of HTML file size before saving
- **Impact:** Maliciously large proposals could fill disk
- **Recommendation:**
  - Add max file size check (e.g., 10MB per file)
  - Reject or truncate oversized proposals
  - Log warning for large files
- **Effort:** 2 hours
- **Dependencies:** None
- **Blocker For:** Protection against disk fill attacks

---

### [P2-004] No Symlink Attack Test
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Testing / Security
- **Location:** `tests/integration/test_api.py`
- **Description:** Path verification should block symlink attacks but untested
- **Impact:** Unknown if symlink attacks actually blocked
- **Recommendation:**
  - Add test: Create symlink to `/etc/passwd`, verify access denied
  - Implementation: `os.symlink('/etc/passwd', 'test_results/malicious.html')`
  - Expected: Path verification catches symlink target outside directory
- **Effort:** 1 hour
- **Dependencies:** None
- **Blocker For:** Security certification

---

### [P2-005] No Visual Regression Tests
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Testing
- **Location:** Needs new test file for Puppeteer
- **Description:** UI changes not validated programmatically
- **Impact:** CSS changes could break layout unnoticed
- **Recommendation:**
  - Use Puppeteer MCP for screenshot comparisons
  - Test: Test Runner page, Results Browser section
  - Store baseline screenshots, compare on changes
- **Effort:** 6 hours
- **Dependencies:** Puppeteer MCP setup
- **Blocker For:** UI stability guarantees

---

## P3 - Low Priority (Nice to Have)

### [P3-001] No Filtering or Search
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Feature / UX
- **Location:** `web/api/tests.py` `list_html_results()`, `test_runner.html`
- **Description:** Cannot filter results by tier, company, date range
- **Impact:** Hard to find specific results in large lists
- **Recommendation:**
  - Add query params: `?tier=Standard&company=Acme&after=2025-12-01`
  - Add filter UI: Dropdowns for tier, text input for company search
  - Add date range picker
- **Effort:** 8 hours
- **Dependencies:** None
- **Blocker For:** None

---

### [P3-002] No Custom Sorting Options
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Feature / UX
- **Location:** `web/api/tests.py` `list_html_results()`, `test_runner.html`
- **Description:** Results only sorted by timestamp descending
- **Impact:** Cannot sort by tier, company, file size
- **Recommendation:**
  - Add query params: `?sort_by=tier&sort_order=asc`
  - Add sort dropdown in UI header
  - Options: timestamp, tier, company, size
- **Effort:** 4 hours
- **Dependencies:** None
- **Blocker For:** None

---

### [P3-003] No Bulk Selection for Delete
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Feature / UX
- **Location:** `web/api/tests.py`, `test_runner.html`
- **Description:** Can only delete one file at a time (or all)
- **Impact:** Tedious to delete subset of results
- **Recommendation:**
  - Add checkboxes to result cards
  - Add "Delete Selected" button
  - Extend DELETE endpoint to accept array of filenames
  - Add "Select All" / "Select None" helpers
- **Effort:** 6 hours
- **Dependencies:** None
- **Blocker For:** None

---

### [P3-004] No Download as ZIP
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Feature / UX
- **Location:** Needs new endpoint in `web/api/tests.py`
- **Description:** Cannot download multiple results at once
- **Impact:** Must open each HTML file individually
- **Recommendation:**
  - Add `GET /api/tests/results/download` endpoint
  - Accept query params for filtering (or all)
  - Use Python `zipfile` module to create archive
  - Stream ZIP file to browser
- **Effort:** 4 hours
- **Dependencies:** None
- **Blocker For:** None

---

### [P3-005] No Result Preview
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** Feature / UX
- **Location:** `web/api/tests.py`, `test_runner.html`
- **Description:** Must open full HTML to see content
- **Impact:** Extra click, new tab required
- **Recommendation:**
  - Parse HTML to extract workflow summary metadata
  - Add expandable preview in result card
  - Show: Company, recommendation summary, workflow count, phase count
  - Click "View Full" to open complete HTML
- **Effort:** 6 hours
- **Dependencies:** HTML parsing logic
- **Blocker For:** None

---

### [P3-006] No Relative Timestamps
- **Status:** Open
- **Added:** 2025-12-27
- **Category:** UX
- **Location:** `test_runner.html` JavaScript (timestamp formatting)
- **Description:** Shows absolute time only (2025-12-27T14:50:30)
- **Impact:** Harder to see recent results at a glance
- **Recommendation:**
  - Add relative time display: "2 hours ago", "Yesterday", "3 days ago"
  - Use JavaScript library (e.g., date-fns) or custom implementation
  - Show absolute time on hover (tooltip)
- **Effort:** 2 hours
- **Dependencies:** None
- **Blocker For:** None

---

## Summary by Priority

| Priority | Open | In Progress | Resolved | Total |
|----------|------|-------------|----------|-------|
| P0       | 0    | 0           | 0        | 0     |
| P1       | 7    | 0           | 0        | 7     |
| P2       | 5    | 0           | 0        | 5     |
| P3       | 6    | 0           | 0        | 6     |
| **Total**| **18**| **0**      | **0**    | **18**|

---

## Production Readiness Checklist

**Current Level: 3 (Observable)**

To reach **Level 4 (Resilient):**
- [ ] [P1-004] Add rate limiting
- [ ] [P2-002] Implement disk space management
- [ ] [P2-003] Add file size limits

To reach **Level 5 (Secure):**
- [ ] [P1-002] Implement authentication
- [ ] [P1-003] Add CSRF protection
- [ ] [P1-004] Add rate limiting
- [ ] [P1-005] Implement audit logging
- [ ] [P1-006] Add CSP headers

---

## Next Actions

**Immediate (This Week):**
1. [P1-001] Fix timestamp parsing bug (15 min) - Quick win
2. [P1-007] Add unit tests for helpers (4 hours) - Good practice

**Before Production (Next Sprint):**
1. [P1-002] Implement authentication (8 hours)
2. [P1-003] Add CSRF protection (4 hours)
3. [P1-004] Add rate limiting (4 hours)
4. [P1-005] Add audit logging (2 hours)
5. [P1-006] Add CSP headers (2 hours)

**Future Enhancements (Backlog):**
- [P2-001] Pagination (when >50 test results exist)
- [P3-001] Filtering (when user requests it)
- [P3-003] Bulk selection (when user feedback indicates need)

---

## Notes

- All items discovered during HTML Results Browser implementation (2025-12-27)
- Feature is fully functional despite these items
- Security items (P1-002 through P1-006) critical only for production deployment
- Development/testing environment safe to use as-is
- Timestamp bug ([P1-001]) should be fixed soon for data accuracy

---

**Maintained by:** Claude Code Development Team
**Review Frequency:** Weekly or after major changes
