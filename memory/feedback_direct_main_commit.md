---
name: No direct main commits
description: Never commit directly to main branch without explicit approval
type: feedback
---

**Rule:** Never commit directly to the main branch.

**Why:** Direct commits to main bypass code review and can introduce instability.

**How to apply:**
- Always create a feature branch first
- Get explicit user approval before committing to main
- Even for test code, always use branch workflow

**Exception:** This happened on 2026-03-26 when adding frontend unit tests. The commit was pushed directly to main without approval.
