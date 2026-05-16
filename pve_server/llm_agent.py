"""LLMAgent: Play Dou Dizhu via DeepSeek LLM API."""

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, cast

from card_maps import EnvCard2RealCard, RealCard2EnvCard
from llm_config import get_llm_config
from openai import APIStatusError, APITimeoutError, OpenAI

logger = logging.getLogger(__name__)

_FAILURE_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs", "llm_failures")
_CALL_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs", "llm_calls")


def _save_failed_request(messages: List[Dict[str, str]], error: str, position: int,
                         response_content: str | None = None) -> None:
    """Save the LLM request that failed for later analysis."""
    os.makedirs(_FAILURE_LOG_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filepath = os.path.join(_FAILURE_LOG_DIR, f"fail_p{position}_{ts}.json")
    payload: Dict[str, Any] = {
        "timestamp": ts,
        "position": position,
        "error": error,
        "messages": messages,
    }
    if response_content is not None:
        payload["response_content"] = response_content
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.warning("Saved failed request to %s", filepath)


def _save_call_log(filepath: str, call_idx: int, messages: List[Dict[str, str]],
                   response_content: str | None, elapsed_ms: float, error: str | None) -> None:
    """Append one LLM API call to a JSONL log file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    payload: Dict[str, Any] = {
        "call_index": call_idx,
        "elapsed_ms": round(elapsed_ms, 1),
        "messages": messages,
    }
    if response_content is not None:
        payload["response_content"] = response_content
    if error is not None:
        payload["error"] = error
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


SYSTEM_PROMPT = """You are an expert Dou Dizhu (Chinese Poker) player. Analyze the game state and choose the best move from the provided legal actions.

## Card Encoding
Each card is a single character: 3, 4, 5, 6, 7, 8, 9, T(10), J, Q, K, A, 2, X(Small Joker), D(Big Joker).

## Game Rules Summary
- 54-card deck. 3 players: one landlord (20 cards) vs two peasants (17 cards each).
- Card ranks (low to high): 3 < 4 < 5 < 6 < 7 < 8 < 9 < T < J < Q < K < A < 2 < X < D
- Move types: single, pair, triple, triple+single, triple+pair, bomb (4 of a kind), king bomb (X+D), serial single (5+ consecutive), serial pair (3+ consecutive pairs), serial triple (2+ consecutive triples), serial triple+single, serial triple+pair, four+two singles, four+two pairs.
- To beat the last opponent move, play a higher-ranked combination of the same move type, OR a bomb (4 of a kind) / king bomb (X+D). Bombs beat non-bomb moves. King bomb beats all.
- "pass" in the legal actions list means you may skip. If "pass" is NOT in the list, you MUST play a card combination from the list.
- Goal: be the first to empty your hand.

## Output Format
Respond with a JSON object only:
{"analysis": "brief strategy reasoning", "action": "<card_string>", "confidence": 0.0-1.0}

- "action": concatenated card codes for the chosen move, e.g. "345" for a 3-4-5 straight, "33" for a pair of 3s, "pass" for skip.
- Pick ONLY from the provided legal actions list."""

USER_MESSAGE_TEMPLATE = """## Players
Player 0: landlord, Player 1: peasant (landlord_down), Player 2: peasant (landlord_up)

## Your Position
Player {position} ({role})

## Your Hand
{hand_str}

## Cards Remaining
{cards_left}

## Bombs Played
{bomb_num}

## Last Opponent Move
{rival_str}

## Play History
{history_str}

## Legal Actions
{legal_str}

Choose the single best action from the legal actions list above."""


class LLMAgent:
    """Plays Dou Dizhu by querying the DeepSeek LLM API.

    Implements the same ``act(infoset) -> (actions, confidences)`` interface
    as DeepAgent so it can be used as a drop-in replacement.
    """

    def __init__(self, position: int, debug_log: bool = False):
        """Initialise the agent for the given player position.

        Args:
            position: 0 for landlord, 1 for landlord_down, 2 for landlord_up.
            debug_log: if True, save every API call (request+response) to disk.
        """
        if position not in (0, 1, 2):
            raise ValueError(f"Invalid position {position}, must be 0, 1, or 2")

        self.position = position
        config = get_llm_config()
        self._client = OpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
        )
        self._model = config["model"]
        self._timeout = config["timeout"]
        self._max_retries = config["max_retries"]
        self.fallback_count = 0
        self._call_count = 0

        if debug_log:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            self._call_log_path = os.path.join(_CALL_LOG_DIR, f"p{position}_{ts}.jsonl")
        else:
            self._call_log_path = None

    # ------------------------------------------------------------------
    # Card encoding helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _env_action_to_str(action: List[int]) -> str:
        """Convert an env-format action list to a display string.

        Example: ``[3, 4, 5]`` → ``"345"``.  An empty list → ``""``.
        """
        if not action:
            return ""
        return "".join(EnvCard2RealCard[c] for c in sorted(action))

    @staticmethod
    def _str_to_env_action(action_str: str) -> List[int]:
        """Convert a display string back to an env-format action list.

        Example: ``"345"`` → ``[3, 4, 5]``.  ``""`` or ``"pass"`` → ``[]``.
        """
        if not action_str or action_str.lower() == "pass":
            return []
        return [RealCard2EnvCard[c] for c in action_str]

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

    def _build_user_message(self, infoset: Any) -> str:
        """Build the user-message prompt from the current InfoSet."""
        # -- position & role
        position = infoset.player_position
        role = "landlord" if position == 0 else "peasant"

        # -- hand (descending rank order)
        hand_cards = sorted(infoset.player_hand_cards, reverse=True)
        hand_str = " ".join(EnvCard2RealCard[c] for c in hand_cards)

        # -- cards remaining per player
        cards_left = infoset.num_cards_left
        cards_left_str = ", ".join(f"Player {i}: {cards_left[i]}" for i in range(3))

        # -- bomb count
        bomb_num = infoset.bomb_num

        # -- last opponent move
        rival_move = infoset.rival_move
        rival_str = LLMAgent._env_action_to_str(rival_move) if rival_move else "none"

        # -- play history (flattened sequence: p0, p1, p2, p0, …)
        action_seq = infoset.card_play_action_seq
        if action_seq:
            lines: List[str] = []
            for i, action in enumerate(action_seq):
                pid = i % 3
                label = LLMAgent._env_action_to_str(action) if action else "pass"
                lines.append(f"Player {pid}: {label}")
            history_str = "\n".join(lines)
        else:
            history_str = "none"

        # -- legal actions
        legal_parts: List[str] = []
        for action in infoset.legal_actions:
            legal_parts.append(LLMAgent._env_action_to_str(action) if action else "pass")
        legal_str = ", ".join(legal_parts)

        return USER_MESSAGE_TEMPLATE.format(
            position=position,
            role=role,
            hand_str=hand_str,
            cards_left=cards_left_str,
            bomb_num=bomb_num,
            rival_str=rival_str,
            history_str=history_str,
            legal_str=legal_str,
        )

    # ------------------------------------------------------------------
    # LLM communication
    # ------------------------------------------------------------------

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Call the DeepSeek API with retries and exponential backoff.

        Tries up to max_retries times (default 3) with delays 1s, 2s, 4s, …
        Raises the last error if all attempts fail.
        """
        last_error: Optional[Exception] = None
        total_attempts = self._max_retries  # total attempts (1 initial + retries)

        for attempt in range(total_attempts):
            t0 = time.time()
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    extra_body={"thinking": {"type": "enabled"}},
                    timeout=self._timeout,
                )
                content = response.choices[0].message.content
                if not content:
                    raise RuntimeError("LLM returned empty response content")
                if self._call_log_path is not None:
                    elapsed = (time.time() - t0) * 1000
                    self._call_count += 1
                    _save_call_log(self._call_log_path, self._call_count, messages, cast(str, content), elapsed, None)
                return cast(str, content)
            except Exception as exc:
                # Save request on timeout for later analysis
                if isinstance(exc, APITimeoutError):
                    _save_failed_request(messages, str(exc), self.position)

                # Only retry on transient errors (5xx, network issues)
                if isinstance(exc, APIStatusError) and exc.status_code < 500:
                    raise
                last_error = exc
                if attempt < self._max_retries - 1:
                    delay = 2**attempt  # 1, 2, 4, … seconds
                    logger.warning(
                        "LLM API call failed (attempt %d/%d): %s. Retrying in %ds…",
                        attempt + 1,
                        total_attempts,
                        exc,
                        delay,
                    )
                    time.sleep(delay)

        assert last_error is not None
        if self._call_log_path is not None:
            elapsed = (time.time() - t0) * 1000
            self._call_count += 1
            _save_call_log(self._call_log_path, self._call_count, messages, None, elapsed, str(last_error))
        raise last_error

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(
        self, content: str, legal_actions: List[List[int]]
    ) -> Tuple[List[int], float]:
        """Parse the LLM JSON response and validate against legal actions.

        Returns:
            ``(action_list, confidence)`` where *action_list* is one of the
            *legal_actions* entries.

        Raises:
            ValueError: if the JSON is invalid or the action is not legal.
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON response from LLM: {exc}") from exc

        action_str = data.get("action") or ""
        confidence = data.get("confidence", 0.0)

        if not isinstance(action_str, str):
            raise ValueError(
                f"Expected 'action' to be a string, got {type(action_str).__name__}"
            )
        if not isinstance(confidence, (int, float)):
            raise ValueError(
                f"Expected 'confidence' to be a number, got {type(confidence).__name__}"
            )

        action = self._str_to_env_action(action_str)

        # Normalize to string for comparison (handles unsorted LLM output)
        target_str = self._env_action_to_str(action)
        legal_strs = [self._env_action_to_str(a) for a in legal_actions]

        if target_str not in legal_strs:
            raise ValueError(
                f"LLM chose action '{action_str}' which is not in "
                f"legal actions: {legal_strs}"
            )

        # Return the exact list from legal_actions (preserves canonical ordering)
        for legal_action in legal_actions:
            if self._env_action_to_str(legal_action) == target_str:
                return legal_action, float(confidence)

        # Should be unreachable
        raise ValueError(f"Action '{action_str}' not found in legal actions")

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    def _fallback_action(
        self, legal_actions: List[List[int]]
    ) -> Tuple[List[List[int]], List[float]]:
        """Return the first legal action with confidence 0.0."""
        logger.warning(
            "LLMAgent falling back to first legal action. "
            "Legal actions: %s",
            [self._env_action_to_str(a) for a in legal_actions],
        )
        self.fallback_count += 1
        fallback = legal_actions[0] if legal_actions else []
        return [fallback], [0.0]

    # ------------------------------------------------------------------
    # Main interface
    # ------------------------------------------------------------------

    def act(self, infoset: Any) -> Tuple[List[List[int]], List[float]]:
        """Choose an action given the current game state.

        Returns:
            ``(actions, confidences)`` matching the **DeepAgent** interface.
            *actions* is a list of action-lists (typically one entry) and
            *confidences* is the corresponding list of confidence floats.
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": self._build_user_message(infoset)},
        ]
        content: Optional[str] = None
        try:
            content = self._call_llm(messages)
            action, confidence = self._parse_response(content, infoset.legal_actions)
            return [action], [confidence]
        except Exception as exc:
            logger.warning(
                "LLMAgent.act failed for player %d. Falling back.", self.position,
                exc_info=True,
            )
            _save_failed_request(messages, str(exc), self.position, response_content=content)
            return self._fallback_action(infoset.legal_actions)
