# LLMAgent Design

**Date**: 2026-05-16
**Status**: Approved

## Overview

Add a new `LLMAgent` class that plays Dou Dizhu via LLM HTTP API (DeepSeek `deepseek-v4-pro`).
Same `act(infoset)` interface as `DeepAgent`, but intelligence comes from a remote LLM instead of a
local ONNX model.

## Architecture

```
pve_server/
├── llm_agent.py          # NEW - LLMAgent class + LLM API call logic
├── llm_config.py         # NEW - env var configuration reader
├── run_douzero.py        # MODIFY - add /generate_llm_battle endpoint
└── game.py               # MODIFY - accept pluggable agent factory

src/
├── App.js                # MODIFY - add /llm-battle route
└── view/
    └── LLMBattleView/    # NEW - thin wrapper component
        ├── index.js
        └── LLMBattleView.js
```

## LLMAgent

### Interface (matches DeepAgent)

```python
class LLMAgent:
    def __init__(self, position: int): ...
    def act(self, infoset: InfoSet) -> Tuple[List[List[int]], List[float]]:
        # Returns (actions, confidences) — top 1 action
```

### act() Flow

```
infoset → build_prompt() → call_llm_api() → parse_response() → validate_action() → return
              │                  │                │                  │
              │           retry 3x + backoff   extract JSON       match against
              │           on failure →          action field       legal_actions
              │           fallback rule                            │
              │           + log event                              │
              │                                                    │
              └──────────────── fallback on failure ───────────────┘
```

### Prompt Design

**System prompt**: Dou Dizhu rules, card encoding (3-9, T, J, Q, K, A, 2, X, D), output format.

**User message** contains:
- Current position and role (landlord/peasant)
- Hand cards (display format, e.g., `3 4 5 T J Q K A 2 X`)
- Three landlord bonus cards (if position 0)
- Full play history: per round: `Player {idx} played: {cards}`
- Remaining card counts per player
- Bomb count
- Opponent's last move (rival_move in display format)
- Legal actions list (all valid moves from `_get_legal_card_play_actions`, in display format)

### LLM Response Format

Request:
```json
{
    "model": "deepseek-v4-pro",
    "messages": [...],
    "response_format": {"type": "json_object"},
    "reasoning_effort": "high",
    "extra_body": {"thinking": {"type": "enabled"}}
}
```

Expected JSON response:
```json
{
    "reasoning": "analysis of opponent hand type...",
    "action": ["3", "4", "5"],
    "confidence": 0.85
}
```

`action: []` means pass. Parsed action is validated against `infoset.legal_actions`.
If validation fails, fall back to the first legal action and log a warning.

## Configuration

All via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEEPSEEK_API_KEY` | (required) | API key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | API base URL |
| `LLM_MODEL` | `deepseek-v4-pro` | Model name |
| `LLM_AGENT_POSITIONS` | `0,1,2` | Comma-separated positions that use LLMAgent. Remaining positions use DeepAgent. |

## Error Handling

1. Network/API error → exponential backoff retry (max 3, intervals: 1s/2s/4s)
2. Retries exhausted OR JSON parse failure OR action validation failure →
   `logging.warning()` records the event → returns fallback action (first legal action, confidence 0.0)
3. Timeout per API call: 30s

## Backend Endpoint

`GET /generate_llm_battle`

- Same logic as `/generate_ai_battle` but uses `_get_llm_players()` which reads
  `LLM_AGENT_POSITIONS` to decide agent type per position
- `source` field set to `"llm_battle"`
- Returns same JSON shape: `{status, battle_id, data: {playerInfo, initHands, moveHistory}}`

## Frontend

- Route `/llm-battle` → `LLMBattleView` component (~30 lines, isomorphic to `AIBattleView`)
- `fetchData` calls `GET /generate_llm_battle`
- Reuses `GamePlaybackView` for playback, `gamePlayable: false` (spectator-only)
- Start button labeled "New LLM Battle"
