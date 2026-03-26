---
name: Git workflow preferences
description: Rules for git operations - no auto push, prefer amending current branch
type: feedback
---

**Rule:** Do not push to remote or create PRs unless explicitly requested.

**Why:** User wants to review changes before they are pushed. Automatic pushing bypasses review and can create unnecessary commits.

**How to apply:**
- Only push when user explicitly says "create PR", "push to remote", or similar
- When asked to fix issues or add tests, amend the current branch instead of creating new branches
- Keep changes local until user requests remote operations
