"""Tests for utils/move_selector.py"""

from utils.move_selector import (
    common_handle,
    filter_type_1_single,
    filter_type_2_pair,
    filter_type_3_triple,
    filter_type_4_bomb,
    filter_type_6_3_1,
    filter_type_7_3_2,
    filter_type_8_serial_single,
    filter_type_9_serial_pair,
    filter_type_10_serial_triple,
    filter_type_11_serial_3_1,
    filter_type_12_serial_3_2,
    filter_type_13_4_2,
    filter_type_14_4_22,
)


class TestCommonHandle:
    """Test common_handle function."""

    def test_filter_higher_cards(self):
        """Test filtering cards higher than rival."""
        moves = [[5], [7], [9], [11]]
        rival_move = [7]
        result = common_handle(moves, rival_move)
        assert [5] not in result
        assert [7] not in result
        assert [9] in result
        assert [11] in result

    def test_no_higher_cards(self):
        """Test when no cards can beat rival."""
        moves = [[3], [4], [5]]
        rival_move = [10]
        result = common_handle(moves, rival_move)
        assert result == []

    def test_all_cards_higher(self):
        """Test when all cards can beat rival."""
        moves = [[8], [9], [10]]
        rival_move = [3]
        result = common_handle(moves, rival_move)
        assert len(result) == 3


class TestFilterType1Single:
    """Test filter_type_1_single function."""

    def test_filter_singles(self):
        """Test filtering single cards."""
        moves = [[3], [5], [7], [9]]
        rival_move = [6]
        result = filter_type_1_single(moves, rival_move)
        assert [3] not in result
        assert [5] not in result
        assert [7] in result
        assert [9] in result


class TestFilterType2Pair:
    """Test filter_type_2_pair function."""

    def test_filter_pairs(self):
        """Test filtering pairs."""
        moves = [[3, 3], [5, 5], [8, 8]]
        rival_move = [5, 5]
        result = filter_type_2_pair(moves, rival_move)
        assert [3, 3] not in result
        assert [5, 5] not in result
        assert [8, 8] in result


class TestFilterType3Triple:
    """Test filter_type_3_triple function."""

    def test_filter_triples(self):
        """Test filtering triples."""
        moves = [[4, 4, 4], [7, 7, 7], [10, 10, 10]]
        rival_move = [7, 7, 7]
        result = filter_type_3_triple(moves, rival_move)
        assert [4, 4, 4] not in result
        assert [7, 7, 7] not in result
        assert [10, 10, 10] in result


class TestFilterType4Bomb:
    """Test filter_type_4_bomb function."""

    def test_filter_bombs(self):
        """Test filtering bombs."""
        moves = [[5, 5, 5, 5], [9, 9, 9, 9], [13, 13, 13, 13]]
        rival_move = [9, 9, 9, 9]
        result = filter_type_4_bomb(moves, rival_move)
        assert [5, 5, 5, 5] not in result
        assert [9, 9, 9, 9] not in result
        assert [13, 13, 13, 13] in result


class TestFilterType6x3x1:
    """Test filter_type_6_3_1 function."""

    def test_filter_3_1(self):
        """Test filtering 3+1 combinations."""
        moves = [[7, 7, 7, 3], [9, 9, 9, 4], [12, 12, 12, 5]]
        rival_move = [9, 9, 9, 4]
        result = filter_type_6_3_1(moves, rival_move)
        # Check results - rival and lower should be filtered out
        assert [9, 9, 9, 4] not in result  # rival move should not be included
        # Higher move should be included (check sorted version since order may vary)
        has_higher = any(sorted(move) == [5, 12, 12, 12] for move in result)
        assert has_higher


class TestFilterType7x3x2:
    """Test filter_type_7_3_2 function."""

    def test_filter_3_2(self):
        """Test filtering 3+2 combinations."""
        moves = [[8, 8, 8, 3, 3], [10, 10, 10, 4, 4]]
        rival_move = [8, 8, 8, 3, 3]
        result = filter_type_7_3_2(moves, rival_move)
        # Check results - rival should be filtered out, higher should be included
        assert [8, 8, 8, 3, 3] not in result  # rival move should not be included
        # Higher move should be included (check sorted version)
        has_higher = any(sorted(move) == [4, 4, 10, 10, 10] for move in result)
        assert has_higher


class TestFilterType8SerialSingle:
    """Test filter_type_8_serial_single function."""

    def test_filter_serial_single(self):
        """Test filtering serial singles."""
        moves = [[3, 4, 5, 6, 7], [5, 6, 7, 8, 9]]
        rival_move = [4, 5, 6, 7, 8]
        result = filter_type_8_serial_single(moves, rival_move)
        assert [3, 4, 5, 6, 7] not in result
        assert [5, 6, 7, 8, 9] in result


class TestFilterType9SerialPair:
    """Test filter_type_9_serial_pair function."""

    def test_filter_serial_pair(self):
        """Test filtering serial pairs."""
        moves = [[4, 4, 5, 5, 6, 6], [6, 6, 7, 7, 8, 8]]
        rival_move = [5, 5, 6, 6, 7, 7]
        result = filter_type_9_serial_pair(moves, rival_move)
        assert [4, 4, 5, 5, 6, 6] not in result
        assert [6, 6, 7, 7, 8, 8] in result


class TestFilterType10SerialTriple:
    """Test filter_type_10_serial_triple function."""

    def test_filter_serial_triple(self):
        """Test filtering serial triples."""
        moves = [[5, 5, 5, 6, 6, 6], [7, 7, 7, 8, 8, 8]]
        rival_move = [6, 6, 6, 7, 7, 7]
        result = filter_type_10_serial_triple(moves, rival_move)
        assert [5, 5, 5, 6, 6, 6] not in result
        assert [7, 7, 7, 8, 8, 8] in result


class TestFilterType11Serial3x1:
    """Test filter_type_11_serial_3_1 function."""

    def test_filter_serial_3_1(self):
        """Test filtering serial 3+1 combinations."""
        moves = [[5, 5, 5, 6, 6, 6, 3, 4], [7, 7, 7, 8, 8, 8, 3, 4]]
        rival_move = [5, 5, 5, 6, 6, 6, 3, 4]
        result = filter_type_11_serial_3_1(moves, rival_move)
        assert [5, 5, 5, 6, 6, 6, 3, 4] not in result
        assert [7, 7, 7, 8, 8, 8, 3, 4] in result


class TestFilterType12Serial3x2:
    """Test filter_type_12_serial_3_2 function."""

    def test_filter_serial_3_2(self):
        """Test filtering serial 3+2 combinations."""
        moves = [[5, 5, 5, 6, 6, 6, 3, 3, 4, 4], [7, 7, 7, 8, 8, 8, 3, 3, 4, 4]]
        rival_move = [5, 5, 5, 6, 6, 6, 3, 3, 4, 4]
        result = filter_type_12_serial_3_2(moves, rival_move)
        assert [5, 5, 5, 6, 6, 6, 3, 3, 4, 4] not in result
        assert [7, 7, 7, 8, 8, 8, 3, 3, 4, 4] in result


class TestFilterType13x4x2:
    """Test filter_type_13_4_2 function."""

    def test_filter_4_2(self):
        """Test filtering 4+2 combinations."""
        moves = [[7, 7, 7, 7, 3, 4], [9, 9, 9, 9, 3, 4]]
        rival_move = [7, 7, 7, 7, 3, 4]
        result = filter_type_13_4_2(moves, rival_move)
        # Check results - rival should be filtered out, higher should be included
        assert [7, 7, 7, 7, 3, 4] not in result  # rival move should not be included
        # Higher move should be included (check sorted version)
        has_higher = any(sorted(move) == [3, 4, 9, 9, 9, 9] for move in result)
        assert has_higher


class TestFilterType14x4x22:
    """Test filter_type_14_4_22 function."""

    def test_filter_4_22(self):
        """Test filtering 4+22 combinations."""
        moves = [[7, 7, 7, 7, 3, 3, 4, 4], [9, 9, 9, 9, 3, 3, 4, 4]]
        rival_move = [7, 7, 7, 7, 3, 3, 4, 4]
        result = filter_type_14_4_22(moves, rival_move)
        assert [7, 7, 7, 7, 3, 3, 4, 4] not in result
        assert [9, 9, 9, 9, 3, 3, 4, 4] in result
