"""Game logic: InfoSet, legal move computation, and AI battle generation."""

import itertools
import logging
from typing import Any, Dict, List

from card_maps import EnvCard2RealCard
from deck import _action_to_suit_format, _assign_card_suits, _deal_cards
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


def generate_ai_battle_data(players: list) -> Dict[str, Any]:
    """Generate a replay by running a game with DouZero AI.

    Args:
        players: List of 3 DeepAgent instances [landlord, landlord_down, landlord_up]

    Returns:
        Replay data dictionary.
    """
    cards = _deal_cards()

    hands_with_suits = {
        0: _assign_card_suits(cards[0]),
        1: _assign_card_suits(cards[1]),
        2: _assign_card_suits(cards[2]),
    }

    replay_data: Dict[str, Any] = {
        "playerInfo": [
            {"id": 0, "index": 0, "role": "landlord", "agentInfo": {"name": "DouZero-Landlord"}},
            {"id": 1, "index": 1, "role": "peasant", "agentInfo": {"name": "DouZero-Peasant"}},
            {"id": 2, "index": 2, "role": "peasant", "agentInfo": {"name": "DouZero-Peasant"}},
        ],
        "initHands": [
            " ".join([suit for _, suit in hands_with_suits[0]]),
            " ".join([suit for _, suit in hands_with_suits[1]]),
            " ".join([suit for _, suit in hands_with_suits[2]]),
        ],
        "moveHistory": [],
    }

    current_hands_with_suits = {
        0: hands_with_suits[0].copy(),
        1: hands_with_suits[1].copy(),
        2: hands_with_suits[2].copy(),
    }
    current_hands_plain = {0: cards[0].copy(), 1: cards[1].copy(), 2: cards[2].copy()}

    current_player = 0
    last_move: List[int] = []
    last_move_player = -1
    card_play_action_seq: List[List[List[int]]] = [[], [], []]
    played_cards: List[List[int]] = [[], [], []]
    bomb_num = 0
    max_turns = 100
    turn = 0

    while turn < max_turns:
        if not current_hands_plain[current_player]:
            break

        info_set = InfoSet(
            player_position=current_player,
            player_hand_cards=current_hands_plain[current_player].copy(),
            other_hand_cards=sorted(
                [c for i in range(3) if i != current_player for c in current_hands_plain[i]],
                reverse=True,
            ),
            num_cards_left=[len(current_hands_plain[i]) for i in range(3)],
            three_landlord_cards=cards["three_landlord_cards"].copy(),
            card_play_action_seq=[a for pos in range(3) for a in card_play_action_seq[pos]],
            last_moves=[[] for _ in range(3)],
            played_cards=[p.copy() for p in played_cards],
            bomb_num=bomb_num,
            rival_move=last_move.copy() if last_move_player >= 0 and last_move_player != current_player else [],
        )

        if last_move_player >= 0 and last_move:
            info_set.last_moves[last_move_player] = last_move.copy()

        info_set.legal_actions = _get_legal_card_play_actions(
            current_hands_plain[current_player].copy(), info_set.rival_move
        )

        actions, confidences = players[current_player].act(info_set)
        action = actions[0] if actions else []

        move_record = {
            "playerIdx": current_player,
            "move": _action_to_suit_format(action, current_hands_with_suits[current_player]),
            "info": {
                "values": {
                    "".join([EnvCard2RealCard[a] for a in actions[i]]): float(confidences[i])
                    for i in range(len(actions))
                }
            },
        }
        replay_data["moveHistory"].append(move_record)

        if action:
            for card in action:
                if card in current_hands_plain[current_player]:
                    current_hands_plain[current_player].remove(card)
                for i, (c, _s) in enumerate(current_hands_with_suits[current_player]):
                    if c == card:
                        current_hands_with_suits[current_player].pop(i)
                        break

            last_move = action.copy()
            last_move_player = current_player
            played_cards[current_player].extend(action)

            move_type = md.get_move_type(action)
            if move_type["type"] in (md.TYPE_4_BOMB, md.TYPE_5_KING_BOMB):
                bomb_num += 1

        card_play_action_seq[current_player].append(action)

        if not current_hands_plain[current_player]:
            break

        current_player = (current_player + 1) % 3
        turn += 1

    return replay_data
