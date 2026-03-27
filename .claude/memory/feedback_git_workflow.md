---
name: git workflow
description: Branch + PR flow, no direct main commits, no gh CLI, no auto push, no Co-Authored-By, no amending
type: feedback
---

## Never commit directly to main

**Rule:** Always create a feature branch before committing. Never commit directly to main without explicit user approval.

**Why:** Maintains code review practices and keeps main branch stable. A past incident (2026-03-26) pushed test code directly to main without approval.

**How to apply:**
- Always create a feature branch before committing: `git checkout -b feature/xxx`
- Never run `git push origin main`
- Get explicit user approval before committing to main
- Exceptions: hotfixes, maintenance tasks with explicit approval

## No gh CLI

**Rule:** Never use `gh` CLI commands (gh pr create, gh repo view, etc.).

**Why:** The environment doesn't have GitHub CLI installed.

**How to apply:** Use `git push` to push code. User will create PRs manually via GitHub web UI.

## Push policy

**Rule:** "create a PR" implies authorization to push the branch to remote, since push is a necessary prerequisite for manual PR creation via GitHub web UI. Do not push in other contexts without explicit request.

**Why:** User wants to control when code is pushed and prefers a clean commit history per logical change. But asking to "create a PR" logically requires the branch to be on remote, and `gh` CLI is unavailable.

**How to apply:** When user says "create a PR" or "commit and create a PR", push the branch to remote after committing. For other scenarios, only push when explicitly asked (e.g., "push").

## No Co-Authored-By in commits

**Rule:** Do not include "Co-Authored-By: Claude ..." line in commit messages.

**Why:** User prefers cleaner commit history without co-author attribution.

**How to apply:** Omit the Co-Authored-By line when drafting commit messages.

## No amending commits

**Rule:** Never amend previous commits. Always create new commits for fixes.

**Why:** User prefers a clean commit history per logical change — each commit should be a distinct, immutable record.

**How to apply:** For any follow-up fix, even small ones on the same branch, create a new commit instead of amending.

## Hooks use stdin JSON

**Rule:** Claude Code hooks receive tool input as JSON on stdin, not as shell variables like `${file}`.

**Why:** A previous hook used `${file}` to get the edited file path, but this variable is never set by Claude Code, so the hook silently did nothing.

**How to apply:** Always use `jq -r '.tool_input.file_path'` to extract file paths from stdin in hook scripts.
