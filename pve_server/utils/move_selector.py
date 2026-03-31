"""Filter moves that can beat the rival's play, for each move type."""

import collections


def common_handle(moves, rival_move):
    new_moves = list()
    for move in moves:
        if move[0] > rival_move[0]:
            new_moves.append(move)
    return new_moves


def _filter_by_rank_at(moves, rival_move, index):
    """Filter moves where the sorted element at `index` beats the rival's."""
    rival_rank = sorted(rival_move)[index]
    return [move for move in moves if sorted(move)[index] > rival_rank]


def _filter_by_triple_rank(moves, rival_move):
    """Filter serial 3+1/3+2 moves by comparing max triple rank."""
    rival_rank = max(k for k, v in collections.Counter(rival_move).items() if v == 3)
    return [move for move in moves if max(k for k, v in collections.Counter(move).items() if v == 3) > rival_rank]


def filter_type_1_single(moves, rival_move):
    return common_handle(moves, rival_move)


def filter_type_2_pair(moves, rival_move):
    return common_handle(moves, rival_move)


def filter_type_3_triple(moves, rival_move):
    return common_handle(moves, rival_move)


def filter_type_4_bomb(moves, rival_move):
    return common_handle(moves, rival_move)


# No need to filter for type_5_king_bomb


def filter_type_6_3_1(moves, rival_move):
    return _filter_by_rank_at(moves, rival_move, 1)


def filter_type_7_3_2(moves, rival_move):
    return _filter_by_rank_at(moves, rival_move, 2)


def filter_type_8_serial_single(moves, rival_move):
    return common_handle(moves, rival_move)


def filter_type_9_serial_pair(moves, rival_move):
    return common_handle(moves, rival_move)


def filter_type_10_serial_triple(moves, rival_move):
    return common_handle(moves, rival_move)


def filter_type_11_serial_3_1(moves, rival_move):
    return _filter_by_triple_rank(moves, rival_move)


def filter_type_12_serial_3_2(moves, rival_move):
    return _filter_by_triple_rank(moves, rival_move)


def filter_type_13_4_2(moves, rival_move):
    return _filter_by_rank_at(moves, rival_move, 2)


def filter_type_14_4_22(moves, rival_move):
    rival_rank = next(k for k, v in collections.Counter(rival_move).items() if v == 4)
    return [move for move in moves if next(k for k, v in collections.Counter(move).items() if v == 4) > rival_rank]
