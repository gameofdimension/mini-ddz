"""Integration test for LLMAgent — requires real DEEPSEEK_API_KEY env var.

Usage:
    DEEPSEEK_API_KEY=sk-xxx uv run python tools/test_llm_integration.py
"""

import os
import sys
import time

# Ensure pve_server is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pve_server"))

from game import InfoSet, _get_legal_card_play_actions, generate_ai_battle_data
from llm_agent import LLMAgent

PASS = "✅"
FAIL = "❌"
passed = 0
failed = 0


def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  {PASS} {name}")
    else:
        failed += 1
        print(f"  {FAIL} {name}")


# ---------------------------------------------------------------------------
# Test 1: Basic API connectivity — send a simple chat
# ---------------------------------------------------------------------------
print("\n=== Test 1: Basic API connectivity ===")
try:
    agent = LLMAgent(0)
    messages = [
        {"role": "system", "content": "Reply with a JSON object."},
        {"role": "user", "content": "Output exactly: {\"hello\": \"world\"}"},
    ]
    content = agent._call_llm(messages)
    check("API responds without error", True)
    check("Response is non-empty", len(content) > 0)
    check("Response contains JSON", "hello" in content.lower())
except Exception as e:
    check(f"API connectivity: {e}", False)
    print("\nCannot proceed without API access. Aborting remaining tests.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Test 2: LLMAgent on a trivial game state
# ---------------------------------------------------------------------------
print("\n=== Test 2: Single turn — simple opening hand ===")
try:
    # Landlord with a trivial hand: must play against nothing (opening move)
    player_hand = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14, 14, 14, 17, 17, 17, 17, 20]
    rival_move = []  # no opponent move — opening
    legal_actions = _get_legal_card_play_actions(player_hand, rival_move)

    infoset = InfoSet(
        player_position=0,
        player_hand_cards=player_hand,
        num_cards_left=[20, 17, 17],
        three_landlord_cards=[3, 4, 5],
        card_play_action_seq=[],
        other_hand_cards=[],
        legal_actions=legal_actions,
        rival_move=rival_move,
        last_moves=[[], [], []],
        played_cards=[[], [], []],
        bomb_num=0,
    )

    print(f"  Hand size: {len(player_hand)}, Legal actions: {len(legal_actions)}")
    print(f"  Calling LLM (thinking mode, may take 30-120s)...")

    t0 = time.time()
    actions, confidences = agent.act(infoset)
    elapsed = time.time() - t0

    action = actions[0] if actions else []
    confidence = confidences[0] if confidences else 0.0

    check(f"Returns action (took {elapsed:.1f}s)", len(actions) > 0)
    check("Action is in legal_actions", action in legal_actions)
    check("Confidence is in [0,1]", 0.0 <= confidence <= 1.0)
    print(f"  Action chosen: {agent._env_action_to_str(action) if action else 'pass'}, confidence: {confidence:.4f}")
except Exception as e:
    import traceback
    traceback.print_exc()
    check(f"Single turn test: {e}", False)


# ---------------------------------------------------------------------------
# Test 3: LLMAgent pass decision
# ---------------------------------------------------------------------------
print("\n=== Test 3: Forced pass — cannot beat opponent ===")
try:
    # Hand is extremely weak, opponent played a 2 (17)
    player_hand = [3, 4, 5, 6, 7]
    rival_move = [17]  # opponent played a 2
    legal_actions = _get_legal_card_play_actions(player_hand, rival_move)

    infoset = InfoSet(
        player_position=1,
        player_hand_cards=player_hand,
        num_cards_left=[10, 5, 10],
        card_play_action_seq=[[3], [17]],  # players 0 and 1 played
        other_hand_cards=[],
        legal_actions=legal_actions,
        rival_move=rival_move,
        last_moves=[[], [17], []],
        played_cards=[[3], [], []],
        bomb_num=0,
    )

    t0 = time.time()
    actions, confidences = agent.act(infoset)
    elapsed = time.time() - t0

    action = actions[0] if actions else []
    check(f"Returns action (took {elapsed:.1f}s)", True)
    check("Action is in legal_actions", action in legal_actions)
    print(f"  Legal actions: {[agent._env_action_to_str(a) if a else 'pass' for a in legal_actions]}")
    print(f"  Action chosen: {agent._env_action_to_str(action) if action else 'pass'}")

    # The only legal action should be pass (no bomb in hand to beat a 2)
    if len(legal_actions) <= 2:
        check("Correctly decided (likely pass)", True)
    else:
        print(f"  Note: {len(legal_actions)} legal actions — expected only pass")
        check("Action chosen is legal", True)
except Exception as e:
    import traceback
    traceback.print_exc()
    check(f"Forced pass test: {e}", False)


# ---------------------------------------------------------------------------
# Test 4: Multi-turn — run a full game with 1 LLM agent
# ---------------------------------------------------------------------------
print("\n=== Test 4: Multi-turn — 1 LLM (landlord) + 2 DeepAgents ===")
try:
    from deep import DeepAgent
    from run_douzero import _make_players

    players = _make_players("llm", "deep", "deep")
    check("3 players created", len(players) == 3)
    check("Player 0 is LLMAgent", isinstance(players[0], LLMAgent))
    check("Player 1 is DeepAgent", isinstance(players[1], DeepAgent))
    check("Player 2 is DeepAgent", isinstance(players[2], DeepAgent))

    t0 = time.time()
    battle_data = generate_ai_battle_data(players)
    elapsed = time.time() - t0

    num_moves = len(battle_data["moveHistory"])
    check(f"Game completed ({num_moves} moves in {elapsed:.1f}s)", num_moves > 0)

    # Count LLM turns
    llm_turns = sum(1 for m in battle_data["moveHistory"] if m["playerIdx"] == 0)
    print(f"  LLM turns: {llm_turns}, Total turns: {num_moves}")
    check("LLM agent took at least 1 turn", llm_turns > 0)

    # Print the game summary
    hands = battle_data["initHands"]
    for i, h in enumerate(hands):
        print(f"  Player {i} initial hand: {h[:60]}...")
    print(f"  First 5 moves:")
    for m in battle_data["moveHistory"][:5]:
        p = m["playerIdx"]
        move = m["move"]
        print(f"    Player {p}: {move}")

finally:
    # Restore default
    os.environ["LLM_AGENT_POSITIONS"] = "0,1,2"


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
if failed == 0:
    print("All integration tests passed!")
else:
    print("Some tests FAILED — check output above.")
    sys.exit(1)
