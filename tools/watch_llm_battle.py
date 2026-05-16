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
from deck import _assign_card_suits, _deal_cards
from deep import DeepAgent
from game import InfoSet, _get_legal_card_play_actions
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


# ---------------------------------------------------------------------------
# Game runner — reuses generate_ai_battle_data for correct game logic
# ---------------------------------------------------------------------------

def run_one_game(players, verbose=True):
    """Run a single game. Returns (winner_pos, turns, bombs, fallbacks).
    fallbacks: dict player_pos -> count of LLM fallback uses.
    """
    cards = _deal_cards()
    hands_suits = {0: _assign_card_suits(cards[0]), 1: _assign_card_suits(cards[1]), 2: _assign_card_suits(cards[2])}
    current_hands = {i: cards[i].copy() for i in range(3)}
    current_suits = {i: hands_suits[i].copy() for i in range(3)}
    init_hands_display = {i: " ".join(s for _, s in hands_suits[i]) for i in range(3)}

    if verbose:
        print("--- 初始手牌 ---")
        for i in range(3):
            print(f"  {ROLE_NAMES[i]} ({len(current_hands[i])}张): {cards_display(current_hands[i])}")
        print(f"  底牌: {cards_display(cards['three_landlord_cards'])}")
        print()

    current_player = 0
    last_move = []
    last_move_player = -1
    card_play_action_seq = [[], [], []]
    played_cards = [[], [], []]
    bomb_num = 0
    turn = 0
    max_turns = 200

    while turn < max_turns:
        if not current_hands[current_player]:
            break

        rival_move = last_move.copy() if last_move_player >= 0 and last_move_player != current_player else []
        legal_actions = _get_legal_card_play_actions(current_hands[current_player].copy(), rival_move)

        last_moves = [[], [], []]
        if last_move_player >= 0 and last_move:
            last_moves[last_move_player] = last_move.copy()

        infoset = InfoSet(
            player_position=current_player,
            player_hand_cards=current_hands[current_player].copy(),
            other_hand_cards=sorted(
                [c for i in range(3) if i != current_player for c in current_hands[i]], reverse=True
            ),
            num_cards_left=[len(current_hands[i]) for i in range(3)],
            three_landlord_cards=cards["three_landlord_cards"].copy(),
            card_play_action_seq=[a for pos in range(3) for a in card_play_action_seq[pos]],
            last_moves=last_moves,
            played_cards=[p.copy() for p in played_cards],
            bomb_num=bomb_num,
            rival_move=rival_move,
        )
        infoset.legal_actions = legal_actions

        is_llm = isinstance(players[current_player], LLMAgent)
        is_random = isinstance(players[current_player], RandomAgent)
        is_ai = is_llm or is_random

        if verbose:
            HL = "\033[1;36m" if is_ai else ""
            RST = "\033[0m" if is_ai else ""
            if is_llm:
                agent_type = "LLM"
            elif is_random:
                agent_type = "RND"
            else:
                agent_type = "Deep"
            print(f"{HL}--- 第 {turn + 1} 回合: {ROLE_NAMES[current_player]} [{agent_type}] ---{RST}")
            if is_llm:
                print(f"    正在思考 ({len(legal_actions)} 个合法动作)...")
                t0 = time.time()

        actions, confidences = players[current_player].act(infoset)
        action = actions[0] if actions else []

        # Defensive: validate action against legal_actions
        if action not in legal_actions:
            import random as _random
            print(f"\n  ⚠ ILLEGAL ACTION: {cards_display(action)} not in legal_actions", file=sys.stderr)
            action = _random.choice(legal_actions) if legal_actions else []
            actions = [action]
            confidences = [0.0]

        if not verbose:
            if is_llm:
                sys.stderr.write(f"\r  LLM thinking (turn {turn + 1}, {len(legal_actions)} actions)...")
                sys.stderr.flush()

        if is_llm and verbose:
            elapsed = time.time() - t0
            print(f"    思考耗时: {elapsed:.1f}s")

        if verbose:
            print(f"    手牌 ({len(current_hands[current_player])}张): {cards_display(current_hands[current_player])}")
            if rival_move:
                print(f"    对手出牌: {cards_display(rival_move)} ({move_type_display(rival_move)})")
            action_line = f"    → 出牌: {cards_display(action)}  [{move_type_display(action)}]"
            if not is_ai:
                conf = confidences[0] if confidences is not None and len(confidences) > 0 else 0.0
                action_line += f"  (预期收益: {conf:.4f})"
            HL2 = "\033[1;36m" if is_llm else ""
            RST2 = "\033[0m" if is_llm else ""
            print(f"{HL2}{action_line}{RST2}")

        if action:
            for card in action:
                if card in current_hands[current_player]:
                    current_hands[current_player].remove(card)
                for i, (c, _s) in enumerate(current_suits[current_player]):
                    if c == card:
                        current_suits[current_player].pop(i)
                        break
            last_move = action.copy()
            last_move_player = current_player
            played_cards[current_player].extend(action)

            move_type = md.get_move_type(action)
            if move_type["type"] in (md.TYPE_4_BOMB, md.TYPE_5_KING_BOMB):
                bomb_num += 1

        card_play_action_seq[current_player].append(action)

        if verbose:
            print(f"    剩余: {len(current_hands[current_player])}张")
            print()

        if not current_hands[current_player]:
            if verbose:
                print("=" * 60)
                if current_player == 0:
                    print("  地主胜利!")
                else:
                    print(f"  农民胜利! ({ROLE_NAMES[current_player]})")
                print(f"  总回合数: {turn + 1}")
                print(f"  炸弹数: {bomb_num}")
                print("=" * 60)
            fallbacks = {pos: p.fallback_count for pos, p in enumerate(players) if isinstance(p, LLMAgent) and p.fallback_count > 0}
            return current_player, turn + 1, bomb_num, fallbacks

        current_player = (current_player + 1) % 3
        turn += 1

    fallbacks = {pos: p.fallback_count for pos, p in enumerate(players) if isinstance(p, LLMAgent) and p.fallback_count > 0}
    return -1, turn, bomb_num, fallbacks


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

    agent_map = {"landlord": args.landlord, "down": args.down, "up": args.up}
    players = []
    for role_key in ("landlord", "down", "up"):
        pos = ROLE_POSITIONS[role_key]
        agent_type = agent_map[role_key]
        if agent_type == "llm":
            players.append(LLMAgent(pos, debug_log=args.log_llm_calls))
        elif agent_type == "deep":
            players.append(DeepAgent(["landlord", "landlord_down", "landlord_up"][pos], pretrained_dir, use_onnx=True))
        else:
            players.append(RandomAgent(pos))

    if verbose:
        print("=" * 60)
        print("  斗地主对战直播")
        print("=" * 60)
        print()
        for i, p in enumerate(players):
            if isinstance(p, LLMAgent):
                agent_label = "LLMAgent 🤖"
            elif isinstance(p, RandomAgent):
                agent_label = "RandomAgent 🎲"
            else:
                agent_label = "DeepAgent 🧠"
            print(f"  {ROLE_NAMES[i]:　<6} (Player {i}): {agent_label}")
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

        if args.rounds > 1:
            print(f"\n[Round {r + 1}/{args.rounds}]")

        t0 = time.time()
        winner, turns, bombs, fallbacks = run_one_game(players, verbose=verbose)
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
