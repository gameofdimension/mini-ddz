#!/bin/bash
# Auto-format Python files in pve_server/ and tests/ after Edit/Write.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

if [[ "$FILE_PATH" == *.py ]] && ([[ "$FILE_PATH" == */pve_server/* ]] || [[ "$FILE_PATH" == */tests/* ]]); then
  uv run ruff format "$FILE_PATH"
  uv run ruff check --fix "$FILE_PATH"
fi
