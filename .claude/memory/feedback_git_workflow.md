---
name: git workflow
description: Branch + PR flow, no direct main commits, no gh CLI, no auto push, no Co-Authored-By
type: feedback
---

## Never commit directly to main

**Rule:** Always create a feature branch before committing. Never commit directly to main without explicit user approval.

**Why:** Maintains code review practices and keeps main branch stable. A past incident (2026-03-26) pushed test code directly to main without approval.

**How to apply:** Before any commit, verify the current branch is not main. Use branch + PR workflow for all changes.

## No gh CLI

**Rule:** Never use `gh` CLI commands (gh pr create, gh repo view, etc.).

**Why:** The environment doesn't have GitHub CLI installed.

**How to apply:** Use `git push` to push code. User will create PRs manually via GitHub web UI.

## No auto push

**Rule:** Never push to remote without being asked.

**Why:** User wants to control when code is pushed.

**How to apply:** Only push when the user explicitly requests it (e.g., "push", "create PR").

## No Co-Authored-By in commits

**Rule:** Do not include "Co-Authored-By: Claude ..." line in commit messages.

**Why:** User prefers cleaner commit history without co-author attribution.

**How to apply:** Omit the Co-Authored-By line when drafting commit messages.
