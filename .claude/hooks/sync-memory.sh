#!/bin/bash
# Sync project memory to repo's .claude/memory/ whenever a memory file is written/edited.
# Claude Code project memory lives at ~/.claude/projects/<project-hash>/memory/
# This hook copies changes to the repo's .claude/memory/ so they can be committed to git.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

SRC_DIR="$HOME/.claude/projects/-Users-felix01-yu-Work-mini-ddz/memory"
DST_DIR="/Users/felix01.yu/Work/mini-ddz/.claude/memory"

if [[ "$FILE_PATH" == "$SRC_DIR/"* ]]; then
  filename=$(basename "$FILE_PATH")
  cp "$FILE_PATH" "$DST_DIR/$filename"
fi
