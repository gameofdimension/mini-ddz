---
name: No gh CLI available
description: GitHub CLI (gh) is not installed - use git commands only
type: feedback
---

**Rule:** Never use `gh` CLI commands (gh pr create, gh repo view, etc.)

**Why:** The environment doesn't have GitHub CLI installed.

**How to apply:** For any GitHub operations:
- Use `git push` to push code
- User will manually create PRs via GitHub web UI
- Do not attempt to run any `gh` commands
