---
phase: 03
slug: user-interaction
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-15
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already in project) |
| **Config file** | pytest.ini or pyproject.toml |
| **Quick run command** | `pytest tests/test_group_chat.py -x -v` |
| **Full suite command** | `pytest tests/ -x --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run unit tests for mention detection
- **After every plan wave:** Run integration tests for full flow
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 3 | USER-01 | unit | `pytest tests/test_mention.py::test_specific_bot_mention -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 3 | USER-01 | unit | `pytest tests/test_mention.py::test_all_mention -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 3 | USER-01 | unit | `pytest tests/test_mention.py::test_case_insensitive -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 3 | USER-02 | integration | `pytest tests/test_group_chat.py::test_user_message_with_mention -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_mention.py` — unit tests for _filter_bots_by_mentions method
- [ ] `tests/conftest.py` — shared fixtures (if needed)
- [ ] pytest already installed in project

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | - | - | - |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending / approved 2026-03-15
