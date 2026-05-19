"""LLMAgent: Play Dou Dizhu via DeepSeek LLM API."""

import json
import logging
import os
import threading
import time
from datetime import datetime
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
    ts = datetime.now().strftime("%Y%m%dT%H%M%SZ")
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


SYSTEM_PROMPT = """你是一名斗地主高手。请分析当前游戏状态，从提供的合法出牌中选择最佳行动。

## 牌编码
每张牌用一个字符表示：3, 4, 5, 6, 7, 8, 9, T(10), J, Q, K, A, 2, X(小王), D(大王)。

## 游戏规则概要
- 54张牌，3名玩家：1名地主（20张牌）对 2名农民（各17张牌）。
- 牌的大小（从小到大）：3 < 4 < 5 < 6 < 7 < 8 < 9 < T < J < Q < K < A < 2 < X < D
- 出牌类型：单张、对子、三张、三带一、三带二、炸弹（四张相同）、王炸（X+D）、顺子（5张及以上连续单张）、连对（3对及以上连续对子）、飞机（2组及以上连续三张）、飞机带单、飞机带双、四带二单、四带二双。
- 要压过对手的牌，必须打出同类型且更大的牌，或使用炸弹（四张相同）/ 王炸（X+D）。炸弹可压非炸弹牌型。王炸最大。
- 合法出牌列表中包含"pass"表示可以不出。如果列表中没有"pass"，则你必须从列表中选一种牌型出牌。
- 目标：最先出完手中所有牌。

## 输出格式
只回复一个 JSON 对象：
{"analysis": "简要策略分析", "action": "<牌编码字符串>", "confidence": 0.0-1.0}

- "action"：所选牌型的牌编码拼接，如 "345" 表示顺子 3-4-5，"33" 表示对 3，"pass" 表示不出。
- 只能从提供的合法出牌列表中选择。"""

USER_MESSAGE_TEMPLATE = """## 玩家
玩家 0：地主，玩家 1：农民（地主下家），玩家 2：农民（地主上家）

## 你的位置
玩家 {position}（{role}）

## 三张地主牌
{landlord_cards}

## 出牌历史
{history_str}

## 你的手牌
{hand_str}

## 各玩家剩余牌数
{cards_left}

## 已出炸弹数
{bomb_num}

## 上一手对手出的牌
{rival_str}

## 合法出牌
{legal_str}

从以上合法出牌列表中选择最佳出牌。"""


class LLMAgent:
    """Plays Dou Dizhu by querying the DeepSeek LLM API.

    Implements the same ``act(infoset) -> (actions, confidences)`` interface
    as DeepAgent so it can be used as a drop-in replacement.
    """

    def __init__(self, position: int):
        """Initialise the agent for the given player position.

        Args:
            position: 0 for landlord, 1 for landlord_down, 2 for landlord_up.
        """
        if position not in (0, 1, 2):
            raise ValueError(f"Invalid position {position}, must be 0, 1, or 2")

        self.position = position
        self._lock = threading.Lock()
        config = get_llm_config()
        self._client = OpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
        )
        self._model = config["model"]
        self._timeout = config["timeout"]
        self._max_retries = config["max_retries"]
        self.fallback_count = 0
        self.last_analysis = ""
        self._call_count = 0
        self._call_log_path: Optional[str] = None

    def start_call_log(self) -> None:
        """Begin logging every API call (request+response) to a new JSONL file."""
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        self._call_log_path = os.path.join(_CALL_LOG_DIR, f"p{self.position}_{ts}.jsonl")
        self._call_count = 0

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
        role = "地主" if position == 0 else "农民"

        # -- three landlord cards (always 3 cards, visible to all players)
        landlord_cards = infoset.three_landlord_cards
        assert landlord_cards, "three_landlord_cards should always be present"
        landlord_str = " ".join(EnvCard2RealCard[c] for c in sorted(landlord_cards, reverse=True))

        # -- hand (descending rank order)
        hand_cards = sorted(infoset.player_hand_cards, reverse=True)
        hand_str = " ".join(EnvCard2RealCard[c] for c in hand_cards)

        # -- cards remaining per player
        cards_left = infoset.num_cards_left
        cards_left_str = ", ".join(f"玩家{i}: {cards_left[i]}" for i in range(3))

        # -- bomb count
        bomb_num = infoset.bomb_num

        # -- last opponent move
        rival_move = infoset.rival_move
        rival_str = LLMAgent._env_action_to_str(rival_move) if rival_move else "无"

        # -- play history (flattened sequence: p0, p1, p2, p0, ...)
        action_seq = infoset.card_play_action_seq
        if action_seq:
            lines: List[str] = []
            for i, action in enumerate(action_seq):
                pid = i % 3
                label = LLMAgent._env_action_to_str(action) if action else "pass"
                lines.append(f"玩家{pid}: {label}")
            history_str = "\n".join(lines)
        else:
            history_str = "无"

        # -- legal actions
        legal_parts: List[str] = []
        for action in infoset.legal_actions:
            legal_parts.append(LLMAgent._env_action_to_str(action) if action else "pass")
        legal_str = ", ".join(legal_parts)

        return USER_MESSAGE_TEMPLATE.format(
            position=position,
            role=role,
            landlord_cards=landlord_str,
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

        Tries up to max_retries times (default 3) with delays 1s, 2s, 4s, ...
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
                    delay = 2**attempt  # 1, 2, 4, ... seconds
                    logger.warning(
                        "LLM API call failed (attempt %d/%d): %s. Retrying in %ds...",
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
        with self._lock:
            self.fallback_count += 1
        self.last_analysis = ""
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
            # Extract analysis text before parsing (so it's available even on parse failure)
            try:
                data = json.loads(content) if content else {}
                self.last_analysis = data.get("analysis", "") or ""
            except json.JSONDecodeError:
                self.last_analysis = ""
            action, confidence = self._parse_response(content, infoset.legal_actions)
            return [action], [confidence]
        except Exception as exc:
            logger.warning(
                "LLMAgent.act failed for player %d. Falling back.", self.position,
                exc_info=True,
            )
            _save_failed_request(messages, str(exc), self.position, response_content=content)
            return self._fallback_action(infoset.legal_actions)
