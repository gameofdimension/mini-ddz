---
name: Git workflow preferences
description: Rules for git operations - no auto push, prefer new commits over amend
type: feedback
---

**Rule:** Do not push to remote or create PRs unless explicitly requested.

**Why:** User wants to review changes before they are pushed. Automatic pushing bypasses review and can create unnecessary commits.

**How to apply:**
- Only push when user explicitly says "create PR", "push to remote", or similar
- Keep changes local until user requests remote operations

**Rule:** On already-pushed branches, create new commits instead of using `--amend`.

**Why:** Amending pushed commits requires force push (`--force-with-lease`), which is risky and can cause issues for others who may have pulled the branch.

**How to apply:**
- If a branch has been pushed, always use `git commit` (not `--amend`) for additional changes
- Only use `--amend` for commits that haven't been pushed yet
