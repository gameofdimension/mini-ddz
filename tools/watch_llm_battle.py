"""Watch a live Dou Dizhu battle with configurable agents per role.

Usage:
    DEEPSEEK_API_KEY=sk-xxx uv run python tools/watch_llm_battle.py
    DEEPSEEK_API_KEY=sk-xxx uv run python tools/watch_llm_battle.py --landlord llm --down deep --up deep
    DEEPSEEK_API_KEY=sk-xxx uv run python tools/watch_llm_battle.py --compact --rounds 10
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pve_server"))

from card_maps import EnvCard2RealCard
from deep import DeepAgent
from game import _get_legal_card_play_actions, init_game, step_game
from llm_agent import LLMAgent
from random_agent import RandomAgent

from utils import move_detector as md

# ---------------------------------------------------------------------------
# Card display helpers
# ---------------------------------------------------------------------------

CARD_NAMES = {
    "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
    "T": "10", "J": "J", "Q": "Q", "K": "K", "A": "A", "2": "2",
    "X": "小王", "D": "大王",
}

ROLE_NAMES = {0: "地主", 1: "地主下家", 2: "地主上家"}

MOVE_TYPE_NAMES = {
    md.TYPE_0_PASS: "不出",
    md.TYPE_1_SINGLE: "单张",
    md.TYPE_2_PAIR: "对子",
    md.TYPE_3_TRIPLE: "三不带",
    md.TYPE_4_BOMB: "炸弹",
    md.TYPE_5_KING_BOMB: "王炸",
    md.TYPE_6_3_1: "三带一",
    md.TYPE_7_3_2: "三带二",
    md.TYPE_8_SERIAL_SINGLE: "顺子",
    md.TYPE_9_SERIAL_PAIR: "连对",
    md.TYPE_10_SERIAL_TRIPLE: "飞机不带",
    md.TYPE_11_SERIAL_3_1: "飞机带单",
    md.TYPE_12_SERIAL_3_2: "飞机带双",
    md.TYPE_13_4_2: "四带二",
    md.TYPE_14_4_22: "四带两对",
}

ROLE_POSITIONS = {"landlord": 0, "down": 1, "up": 2}


def cards_display(env_cards):
    if not env_cards:
        return "不出"
    return " ".join(CARD_NAMES[EnvCard2RealCard[c]] for c in sorted(env_cards, reverse=True))


def move_type_display(env_cards):
    if not env_cards:
        return MOVE_TYPE_NAMES[md.TYPE_0_PASS]
    move_type = md.get_move_type(env_cards)
    return MOVE_TYPE_NAMES.get(move_type["type"], f"未知(move_type={move_type})")


def _get_agent_label(player, role_key):
    """Return a human-readable label for an agent instance."""
    if isinstance(player, LLMAgent):
        return f"LLM-{role_key}"
    if isinstance(player, RandomAgent):
        return f"Random-{role_key}"
    if isinstance(player, DeepAgent):
        return f"DouZero-{role_key}"
    return f"Unknown-{role_key}"


# ---------------------------------------------------------------------------
# Game runner — uses init_game + step_game from game.py
# ---------------------------------------------------------------------------

def run_one_game(players, verbose=True):
    """Run a single game. Returns (winner_pos, turns, bombs, fallbacks).
    fallbacks: dict player_pos -> count of LLM fallback uses.
    """
    init_data, gs = init_game(players)
    gs["max_turns"] = 200  # match previous behaviour

    cards = gs["cards"]

    if verbose:
        print("--- 初始手牌 ---")
        for i in range(3):
            hand = gs["current_hands_plain"][i]
            print(f"  {ROLE_NAMES[i]} ({len(hand)}张): {cards_display(hand)}")
        print(f"  底牌: {cards_display(cards['three_landlord_cards'])}")
        print()

    while True:
        cp = gs["current_player"]
        hand_before = gs["current_hands_plain"][cp]

        if not hand_before:
            break

        # Determine agent type for display
        is_llm = isinstance(players[cp], LLMAgent)
        is_random = isinstance(players[cp], RandomAgent)
        is_ai = is_llm or is_random

        # Compute legal actions for display (step_game computes them too, but we
        # need the count before the call for the "thinking" message)
        last_move = gs["last_move"]
        last_move_player = gs["last_move_player"]
        rival_move = last_move.copy() if last_move_player >= 0 and last_move_player != cp else []
        legal_actions = _get_legal_card_play_actions(hand_before.copy(), rival_move)

        turn = gs["turn"]

        if verbose:
            if is_llm:
                agent_type = "LLM"
            elif is_random:
                agent_type = "RND"
            else:
                agent_type = "Deep"
            hl = "\033[1;36m" if is_ai else ""
            rst = "\033[0m" if is_ai else ""
            print(f"{hl}--- 第 {turn + 1} 回合: {ROLE_NAMES[cp]} [{agent_type}] ---{rst}")
            if is_llm:
                print(f"    正在思考 ({len(legal_actions)} 个合法动作)...")

        t0 = time.time()
        step = step_game(players, gs)

        # Extract the chosen action from game state (env format, from card_play_action_seq)
        action = gs["card_play_action_seq"][cp][-1]

        # Validate action is legal (defence against agent bugs)
        if action not in legal_actions:
            raise RuntimeError(
                f"ILLEGAL ACTION: {cards_display(action)} not in legal_actions. "
                f"Player {cp} ({ROLE_NAMES[cp]}), turn {turn + 1}. "
                f"rival_move: {cards_display(rival_move)}. "
                f"hand: {cards_display(hand_before)}. "
                f"legal: {[cards_display(a) for a in legal_actions]}"
            )

        if not verbose:
            if is_llm:
                sys.stderr.write(f"\r  LLM thinking (turn {step['turn']}, {len(legal_actions)} actions)...")
                sys.stderr.flush()

        elapsed = time.time() - t0

        if verbose:
            if is_llm:
                print(f"    思考耗时: {elapsed:.1f}s")
            hand_after = gs["current_hands_plain"][cp]
            print(f"    手牌 ({len(hand_before)}张): {cards_display(hand_before)}")
            if rival_move:
                print(f"    对手出牌: {cards_display(rival_move)} ({move_type_display(rival_move)})")
            action_line = f"    → 出牌: {cards_display(action)}  [{move_type_display(action)}]"
            if not is_ai and step["info"]["values"]:
                val = list(step["info"]["values"].values())[0]
                action_line += f"  (预期收益: {val:.4f})"
            hl2 = "\033[1;36m" if is_llm else ""
            rst2 = "\033[0m" if is_llm else ""
            print(f"{hl2}{action_line}{rst2}")
            print(f"    剩余: {len(hand_after)}张")
            print()

        if step["gameOver"]:
            winner = step["winner"]
            if verbose:
                print("=" * 60)
                if winner == 0:
                    print("  地主胜利!")
                else:
                    print(f"  农民胜利! ({ROLE_NAMES[winner]})")
                print(f"  总回合数: {step['turn']}")
                print(f"  炸弹数: {step['bombNum']}")
                print("=" * 60)
            fallbacks = {pos: p.fallback_count for pos, p in enumerate(players)
                         if isinstance(p, LLMAgent) and p.fallback_count > 0}
            return winner, step["turn"], step["bombNum"], fallbacks

    fallbacks = {pos: p.fallback_count for pos, p in enumerate(players)
                 if isinstance(p, LLMAgent) and p.fallback_count > 0}
    return -1, gs["turn"], gs["bomb_num"], fallbacks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Watch a live Dou Dizhu battle")
    parser.add_argument("--landlord", choices=["llm", "deep", "random"], default="llm")
    parser.add_argument("--down", choices=["llm", "deep", "random"], default="llm")
    parser.add_argument("--up", choices=["llm", "deep", "random"], default="llm")
    parser.add_argument("--compact", action="store_true",
                        help="Suppress per-turn output, only show summary")
    parser.add_argument("--log-llm-calls", action="store_true",
                        help="Save every LLM API request and response to logs/llm_calls/")
    parser.add_argument("--rounds", type=int, default=1,
                        help="Number of games to run (default: 1)")
    args = parser.parse_args()

    verbose = not args.compact

    pretrained_dir = os.path.join(os.path.dirname(__file__), "..", "pve_server", "pretrained", "douzero_pretrained")
    pretrained_dir = os.path.abspath(pretrained_dir)

    def _make_player(pos, role_key):
        agent_type = agent_map[role_key]
        if agent_type == "llm":
            return LLMAgent(pos)
        elif agent_type == "deep":
            return DeepAgent(["landlord", "landlord_down", "landlord_up"][pos], pretrained_dir, use_onnx=True)
        else:
            return RandomAgent(pos)

    agent_map = {"landlord": args.landlord, "down": args.down, "up": args.up}
    players = [_make_player(ROLE_POSITIONS[k], k) for k in ("landlord", "down", "up")]

    if verbose:
        print("=" * 60)
        print("  斗地主对战直播")
        print("=" * 60)
        print()
        for i, p in enumerate(players):
            agent_label = _get_agent_label(p, {0: "landlord", 1: "down", 2: "up"}[i])
            print(f"  {ROLE_NAMES[i]}  (Player {i}): {agent_label}")
        print()

    total_turns = 0
    total_time = 0.0
    total_fallbacks = {}
    win_counts = {}  # agent_type -> count, e.g. {"llm": 3, "deep": 2, "random": 1}

    def _agent_name(pos):
        """Return the agent type name for a position: llm, deep, or random."""
        role_key = {0: "landlord", 1: "down", 2: "up"}[pos]
        return agent_map[role_key]

    for r in range(args.rounds):
        for p in players:
            if hasattr(p, "fallback_count"):
                p.fallback_count = 0
            if args.log_llm_calls and hasattr(p, "start_call_log"):
                p.start_call_log()

        if args.rounds > 1:
            print(f"\n[Round {r + 1}/{args.rounds}]")

        t0 = time.time()
        try:
            winner, turns, bombs, fallbacks = run_one_game(players, verbose=verbose)
        except RuntimeError as e:
            elapsed = time.time() - t0
            print(f"\n  ❌ ILLEGAL ACTION DETECTED, aborting round: {e}", file=sys.stderr)
            continue
        elapsed = time.time() - t0
        total_time += elapsed
        total_turns += turns
        for pos, count in fallbacks.items():
            total_fallbacks[pos] = total_fallbacks.get(pos, 0) + count

        if not verbose:
            sys.stderr.write("\r" + " " * 50 + "\r")
            sys.stderr.flush()

        # Track wins by agent type
        if winner in (0, 1, 2):
            winner_type = _agent_name(winner)
            win_counts[winner_type] = win_counts.get(winner_type, 0) + 1

        if args.rounds > 1 or args.compact:
            if elapsed < 1:
                time_str = f"{elapsed * 1000:.0f}ms"
            else:
                time_str = f"{elapsed:.1f}s"
            winner_label = "地主" if winner == 0 else "农民" if winner in (1, 2) else "超时"
            fb_str = ""
            if fallbacks:
                fb_parts = [f"{ROLE_NAMES[p]}:{c}" for p, c in fallbacks.items()]
                fb_str = f", LLM兜底: {{{', '.join(fb_parts)}}}"
            print(f"  #{r + 1}: {winner_label}胜 ({_agent_name(winner) if winner >= 0 else 'n/a'}), {turns}回合, {bombs}炸, {time_str}{fb_str}")

    if args.rounds > 1:
        if total_time < 1:
            total_str = f"{total_time * 1000:.0f}ms"
            avg_str = f"{total_time / args.rounds * 1000:.0f}ms/局"
        else:
            total_str = f"{total_time:.0f}s"
            avg_str = f"{total_time / args.rounds:.1f}s/局"
        print(f"\n{'=' * 50}")
        print(f"  总计: {args.rounds} 局, {total_str}")
        print(f"  平均: {total_turns / args.rounds:.1f} 回合, {avg_str}")
        for role_key in ("landlord", "down", "up"):
            pos = ROLE_POSITIONS[role_key]
            print(f"  {ROLE_NAMES[pos]} ({agent_map[role_key]})")
        win_parts = [f"{t}:{c}" for t, c in sorted(win_counts.items())]
        print(f"  胜率: {{{', '.join(win_parts)}}}")
        if total_fallbacks:
            fb_parts = [f"{ROLE_NAMES[p]}:{c}" for p, c in total_fallbacks.items()]
            print(f"  LLM 兜底总计: {{{', '.join(fb_parts)}}}")


if __name__ == "__main__":
    main()
