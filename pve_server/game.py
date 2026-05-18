"""Game logic: InfoSet, legal move computation, and AI battle generation."""

import itertools
import logging
from typing import Any, Dict, List

from card_maps import EnvCard2RealCard
from deck import _action_to_suit_format, _assign_card_suits, _deal_cards
from deep import DeepAgent
from llm_agent import LLMAgent
from random_agent import RandomAgent
from utils.move_generator import MovesGener

from utils import move_detector as md
from utils import move_selector as ms

logger = logging.getLogger(__name__)

# Move type → (generator_method_name, filter_function, has_repeat_num)
_MOVE_DISPATCH: Dict[int, tuple] = {
    md.TYPE_1_SINGLE: ("gen_type_1_single", ms.filter_type_1_single, False),
    md.TYPE_2_PAIR: ("gen_type_2_pair", ms.filter_type_2_pair, False),
    md.TYPE_3_TRIPLE: ("gen_type_3_triple", ms.filter_type_3_triple, False),
    md.TYPE_4_BOMB: ("gen_type_4_bomb", ms.filter_type_4_bomb, False),
    md.TYPE_6_3_1: ("gen_type_6_3_1", ms.filter_type_6_3_1, False),
    md.TYPE_7_3_2: ("gen_type_7_3_2", ms.filter_type_7_3_2, False),
    md.TYPE_8_SERIAL_SINGLE: ("gen_type_8_serial_single", ms.filter_type_8_serial_single, True),
    md.TYPE_9_SERIAL_PAIR: ("gen_type_9_serial_pair", ms.filter_type_9_serial_pair, True),
    md.TYPE_10_SERIAL_TRIPLE: ("gen_type_10_serial_triple", ms.filter_type_10_serial_triple, True),
    md.TYPE_11_SERIAL_3_1: ("gen_type_11_serial_3_1", ms.filter_type_11_serial_3_1, True),
    md.TYPE_12_SERIAL_3_2: ("gen_type_12_serial_3_2", ms.filter_type_12_serial_3_2, True),
    md.TYPE_13_4_2: ("gen_type_13_4_2", ms.filter_type_13_4_2, False),
    md.TYPE_14_4_22: ("gen_type_14_4_22", ms.filter_type_14_4_22, False),
}

# Move types where bombs cannot be added as extra options
_NO_BOMB_EXTRA = {md.TYPE_0_PASS, md.TYPE_4_BOMB, md.TYPE_5_KING_BOMB}


class InfoSet:
    """Game state snapshot for AI decision-making."""

    def __init__(
        self,
        player_position=None,
        player_hand_cards=None,
        num_cards_left=None,
        three_landlord_cards=None,
        card_play_action_seq=None,
        other_hand_cards=None,
        legal_actions=None,
        rival_move=None,
        last_moves=None,
        played_cards=None,
        bomb_num=None,
    ):
        self.player_position = player_position
        self.player_hand_cards = player_hand_cards
        self.num_cards_left = num_cards_left
        self.three_landlord_cards = three_landlord_cards
        self.card_play_action_seq = card_play_action_seq
        self.other_hand_cards = other_hand_cards
        self.legal_actions = legal_actions
        self.rival_move = rival_move
        self.last_moves = last_moves
        self.played_cards = played_cards
        self.bomb_num = bomb_num


def _flatten_action_seq(card_play_action_seq: List[List[List[int]]]) -> List[List[int]]:
    """Interleave per-player action sequences by turn order (P0, P1, P2, ...).

    *card_play_action_seq* is ``[p0_actions, p1_actions, p2_actions]`` where
    each sub-list holds one player's actions in chronological order.
    """
    n0, n1, n2 = len(card_play_action_seq[0]), len(card_play_action_seq[1]), len(card_play_action_seq[2])
    assert n0 >= n1 and n0 >= n2, f"P0 should have most actions, got {n0}/{n1}/{n2}"
    seq: List[List[int]] = []
    for i in range(n0):
        for pos in range(3):
            if i < len(card_play_action_seq[pos]):
                seq.append(card_play_action_seq[pos][i])
    return seq


def _get_legal_card_play_actions(player_hand_cards: List[int], rival_move: List[int]) -> List[List[int]]:
    """Return all legal moves given a hand and the rival's last play."""
    mg = MovesGener(player_hand_cards)

    rival_type = md.get_move_type(rival_move)
    rival_move_type = rival_type["type"]
    rival_move_len = rival_type.get("len", 1)
    moves = []

    if rival_move_type == md.TYPE_0_PASS:
        moves = mg.gen_moves()
    elif rival_move_type == md.TYPE_5_KING_BOMB:
        moves = []
    elif rival_move_type == md.TYPE_4_BOMB:
        moves = ms.filter_type_4_bomb(mg.gen_type_4_bomb() + mg.gen_type_5_king_bomb(), rival_move)
    elif rival_move_type in _MOVE_DISPATCH:
        gen_name, filter_fn, has_repeat = _MOVE_DISPATCH[rival_move_type]
        gen_method = getattr(mg, gen_name)
        all_moves = gen_method(repeat_num=rival_move_len) if has_repeat else gen_method()
        moves = filter_fn(all_moves, rival_move)

    if rival_move_type not in _NO_BOMB_EXTRA:
        moves = moves + mg.gen_type_4_bomb() + mg.gen_type_5_king_bomb()

    if rival_move:
        moves = moves + [[]]

    for m in moves:
        m.sort()

    moves.sort()
    moves = list(move for move, _ in itertools.groupby(moves))

    return moves


def _get_agent_label(player: Any, role: str) -> str:
    """Return a human-readable label for an agent instance."""
    if isinstance(player, LLMAgent):
        return f"LLM-{role}"
    if isinstance(player, RandomAgent):
        return f"Random-{role}"
    if isinstance(player, DeepAgent):
        return f"DouZero-{role}"
    return f"Unknown-{role}"


def _build_init_replay_data(players: list, hands_with_suits: Dict[int, list]) -> Dict[str, Any]:
    """Build the static initial portion of replay data (no moveHistory)."""
    return {
        "playerInfo": [
            {"id": 0, "index": 0, "role": "landlord", "agentInfo": {"name": _get_agent_label(players[0], "Landlord")}},
            {"id": 1, "index": 1, "role": "peasant", "agentInfo": {"name": _get_agent_label(players[1], "Peasant")}},
            {"id": 2, "index": 2, "role": "peasant", "agentInfo": {"name": _get_agent_label(players[2], "Peasant")}},
        ],
        "initHands": [
            " ".join([suit for _, suit in hands_with_suits[0]]),
            " ".join([suit for _, suit in hands_with_suits[1]]),
            " ".join([suit for _, suit in hands_with_suits[2]]),
        ],
        "moveHistory": [],
    }


def init_game(players: list) -> tuple:
    """Deal cards, assign suits, create initial game state.

    Returns:
        ``(init_data, game_state)`` where *init_data* has playerInfo, initHands,
        three_landlord_cards (internal format); *game_state* is a mutable dict
        that gets passed to :func:`step_game`.
    """
    cards = _deal_cards()

    hands_with_suits = {
        0: _assign_card_suits(cards[0]),
        1: _assign_card_suits(cards[1]),
        2: _assign_card_suits(cards[2]),
    }

    init_data = _build_init_replay_data(players, hands_with_suits)
    init_data["three_landlord_cards"] = cards["three_landlord_cards"].copy()

    game_state = {
        "cards": cards,
        "current_hands_plain": {0: cards[0].copy(), 1: cards[1].copy(), 2: cards[2].copy()},
        "current_hands_with_suits": {
            0: hands_with_suits[0].copy(),
            1: hands_with_suits[1].copy(),
            2: hands_with_suits[2].copy(),
        },
        "current_player": 0,
        "last_move": [],
        "last_move_player": -1,
        "card_play_action_seq": [[], [], []],
        "latest_actions": ["", "", ""],  # suit format strings per player
        "played_cards": [[], [], []],
        "bomb_num": 0,
        "turn": 0,
        "max_turns": 100,
    }

    return init_data, game_state


def step_game(players: list, gs: dict) -> dict:
    """Run one turn of the game, update *gs* in place.

    Returns a dict with the move record and derived UI state that the frontend
    needs to update the game board.
    """
    cp = gs["current_player"]
    hands_plain = gs["current_hands_plain"]
    hands_suits = gs["current_hands_with_suits"]

    cards = gs["cards"]
    last_move = gs["last_move"]
    last_move_player = gs["last_move_player"]
    card_play_action_seq = gs["card_play_action_seq"]
    played_cards = gs["played_cards"]
    bomb_num = gs["bomb_num"]
    turn = gs["turn"]
    max_turns = gs["max_turns"]

    if turn >= max_turns or not hands_plain[cp]:
        return _step_game_over_response(gs)

    info_set = InfoSet(
        player_position=cp,
        player_hand_cards=hands_plain[cp].copy(),
        other_hand_cards=sorted(
            [c for i in range(3) if i != cp for c in hands_plain[i]], reverse=True
        ),
        num_cards_left=[len(hands_plain[i]) for i in range(3)],
        three_landlord_cards=cards["three_landlord_cards"].copy(),
        card_play_action_seq=_flatten_action_seq(card_play_action_seq),
        last_moves=[[] for _ in range(3)],
        played_cards=[p.copy() for p in played_cards],
        bomb_num=bomb_num,
        rival_move=last_move.copy() if last_move_player >= 0 and last_move_player != cp else [],
    )

    if last_move_player >= 0 and last_move:
        info_set.last_moves[last_move_player] = last_move.copy()

    info_set.legal_actions = _get_legal_card_play_actions(
        hands_plain[cp].copy(), info_set.rival_move
    )

    actions, confidences = players[cp].act(info_set)
    action = actions[0] if actions else []

    # Agent protocol: act(info_set) -> (actions, confidences)
    # Optional: LLMAgent also exposes last_analysis for display
    llm_analysis = ""
    if isinstance(players[cp], LLMAgent):
        llm_analysis = players[cp].last_analysis or ""

    move_suit = _action_to_suit_format(action, hands_suits[cp])

    if action:
        for card in action:
            if card in hands_plain[cp]:
                hands_plain[cp].remove(card)
            for i, (c, _s) in enumerate(hands_suits[cp]):
                if c == card:
                    hands_suits[cp].pop(i)
                    break

        gs["last_move"] = action.copy()
        gs["last_move_player"] = cp
        played_cards[cp].extend(action)

        move_type = md.get_move_type(action)
        if move_type["type"] in (md.TYPE_4_BOMB, md.TYPE_5_KING_BOMB):
            bomb_num += 1
            gs["bomb_num"] = bomb_num

        gs["latest_actions"][cp] = move_suit
    else:
        gs["latest_actions"][cp] = "pass"

    card_play_action_seq[cp].append(action)

    game_over = not hands_plain[cp]
    if game_over:
        return {
            "playerIdx": cp,
            "move": move_suit,
            "info": {
                "values": {
                    "".join([EnvCard2RealCard[a] for a in actions[i]]): float(confidences[i])
                    for i in range(len(actions))
                }
            },
            "analysis": llm_analysis,
            "hands": [_suits_to_str(hands_suits[i]) for i in range(3)],
            "latestAction": list(gs["latest_actions"]),
            "currentPlayer": cp,
            "bombNum": bomb_num,
            "turn": turn + 1,
            "gameOver": True,
            "winner": cp,
        }

    gs["current_player"] = (cp + 1) % 3
    gs["turn"] = turn + 1

    return {
        "playerIdx": cp,
        "move": move_suit,
        "info": {
            "values": {
                "".join([EnvCard2RealCard[a] for a in actions[i]]): float(confidences[i])
                for i in range(len(actions))
            }
        },
        "analysis": llm_analysis,
        "hands": [_suits_to_str(hands_suits[i]) for i in range(3)],
        "latestAction": list(gs["latest_actions"]),
        "currentPlayer": gs["current_player"],
        "bombNum": bomb_num,
        "turn": gs["turn"],
        "gameOver": False,
        "winner": None,
    }


def _suits_to_str(hand_with_suits: list) -> str:
    """Join a suit-format hand list into a space-separated string."""
    return " ".join(suit for _, suit in hand_with_suits)


def _step_game_over_response(gs: dict) -> dict:
    """Build a gameOver response when the game is already over."""
    hands_suits = gs["current_hands_with_suits"]
    return {
        "playerIdx": gs["current_player"],
        "move": "pass",
        "info": {"values": {}},
        "analysis": "",
        "hands": [_suits_to_str(hands_suits[i]) for i in range(3)],
        "latestAction": list(gs["latest_actions"]),
        "currentPlayer": gs["current_player"],
        "bombNum": gs["bomb_num"],
        "turn": gs["turn"],
        "gameOver": True,
        "winner": None,
    }


def generate_ai_battle_data(players: list) -> Dict[str, Any]:
    """Generate a replay by running a complete game.

    Args:
        players: List of 3 agent instances [landlord, landlord_down, landlord_up]

    Returns:
        Replay data dictionary.
    """
    init_data, gs = init_game(players)
    del init_data["three_landlord_cards"]

    replay_data: Dict[str, Any] = {
        "playerInfo": init_data["playerInfo"],
        "initHands": init_data["initHands"],
        "moveHistory": [],
    }

    max_turns = gs["max_turns"]
    turn = 0
    while turn < max_turns:
        if not gs["current_hands_plain"][gs["current_player"]]:
            break

        step = step_game(players, gs)
        move_record = {
            "playerIdx": step["playerIdx"],
            "move": step["move"],
            "info": step["info"],
        }
        replay_data["moveHistory"].append(move_record)

        if step["gameOver"]:
            break

        turn = gs["turn"]

    return replay_data
