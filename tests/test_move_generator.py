"""Tests for utils/move_generator.py"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pve_server'))

from utils.move_generator import MovesGener


class TestMovesGenerInit:
    """Test MovesGener initialization."""

    def test_empty_hand(self):
        """Test with empty hand."""
        mg = MovesGener([])
        assert mg.cards_list == []
        assert dict(mg.cards_dict) == {}

    def test_single_card(self):
        """Test with single card."""
        mg = MovesGener([5])
        assert mg.cards_list == [5]
        assert mg.cards_dict[5] == 1

    def test_multiple_cards(self):
        """Test with multiple cards."""
        mg = MovesGener([3, 3, 4, 5, 5, 5])
        assert mg.cards_dict[3] == 2
        assert mg.cards_dict[4] == 1
        assert mg.cards_dict[5] == 3

    def test_full_hand(self):
        """Test with full hand of cards."""
        cards = [3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5]
        mg = MovesGener(cards)
        assert mg.cards_dict[3] == 4
        assert mg.cards_dict[4] == 4
        assert mg.cards_dict[5] == 4


class TestGenType1Single:
    """Test gen_type_1_single method."""

    def test_single_from_empty(self):
        """Test generating singles from empty hand."""
        mg = MovesGener([])
        result = mg.gen_type_1_single()
        assert result == []

    def test_single_from_one_card(self):
        """Test generating singles from one card."""
        mg = MovesGener([5])
        result = mg.gen_type_1_single()
        assert [5] in result

    def test_single_from_multiple(self):
        """Test generating singles from multiple cards."""
        mg = MovesGener([3, 4, 5])
        result = mg.gen_type_1_single()
        assert [3] in result
        assert [4] in result
        assert [5] in result
        assert len(result) == 3

    def test_single_duplicates_removed(self):
        """Test that duplicates are removed."""
        mg = MovesGener([3, 3, 4, 4])
        result = mg.gen_type_1_single()
        assert len(result) == 2


class TestGenType2Pair:
    """Test gen_type_2_pair method."""

    def test_pair_from_empty(self):
        """Test generating pairs from empty hand."""
        mg = MovesGener([])
        result = mg.gen_type_2_pair()
        assert result == []

    def test_pair_no_pairs(self):
        """Test generating pairs when no pairs exist."""
        mg = MovesGener([3, 4, 5])
        result = mg.gen_type_2_pair()
        assert result == []

    def test_pair_with_pairs(self):
        """Test generating pairs."""
        mg = MovesGener([3, 3, 4, 4, 5])
        result = mg.gen_type_2_pair()
        assert [3, 3] in result
        assert [4, 4] in result
        assert len(result) == 2

    def test_pair_with_triples(self):
        """Test generating pairs when triples exist."""
        mg = MovesGener([5, 5, 5])
        result = mg.gen_type_2_pair()
        assert [5, 5] in result


class TestGenType3Triple:
    """Test gen_type_3_triple method."""

    def test_triple_from_empty(self):
        """Test generating triples from empty hand."""
        mg = MovesGener([])
        result = mg.gen_type_3_triple()
        assert result == []

    def test_triple_no_triples(self):
        """Test when no triples exist."""
        mg = MovesGener([3, 3, 4, 4])
        result = mg.gen_type_3_triple()
        assert result == []

    def test_triple_with_triples(self):
        """Test generating triples."""
        mg = MovesGener([5, 5, 5, 6, 6, 6])
        result = mg.gen_type_3_triple()
        assert [5, 5, 5] in result
        assert [6, 6, 6] in result

    def test_triple_with_bomb(self):
        """Test generating triples when bomb exists."""
        mg = MovesGener([7, 7, 7, 7])
        result = mg.gen_type_3_triple()
        assert [7, 7, 7] in result


class TestGenType4Bomb:
    """Test gen_type_4_bomb method."""

    def test_bomb_from_empty(self):
        """Test generating bombs from empty hand."""
        mg = MovesGener([])
        result = mg.gen_type_4_bomb()
        assert result == []

    def test_bomb_no_bombs(self):
        """Test when no bombs exist."""
        mg = MovesGener([3, 3, 3, 4, 4, 4])
        result = mg.gen_type_4_bomb()
        assert result == []

    def test_bomb_with_bombs(self):
        """Test generating bombs."""
        mg = MovesGener([5, 5, 5, 5, 7, 7, 7, 7])
        result = mg.gen_type_4_bomb()
        assert [5, 5, 5, 5] in result
        assert [7, 7, 7, 7] in result


class TestGenType5KingBomb:
    """Test gen_type_5_king_bomb method."""

    def test_king_bomb_no_jokers(self):
        """Test when no jokers."""
        mg = MovesGener([3, 4, 5])
        result = mg.gen_type_5_king_bomb()
        assert result == []

    def test_king_bomb_one_joker(self):
        """Test with one joker."""
        mg = MovesGener([20, 3, 4, 5])
        result = mg.gen_type_5_king_bomb()
        assert result == []

    def test_king_bomb_both_jokers(self):
        """Test with both jokers."""
        mg = MovesGener([20, 30, 3, 4, 5])
        result = mg.gen_type_5_king_bomb()
        assert [20, 30] in result


class TestGenType6_3_1:
    """Test gen_type_6_3_1 method."""

    def test_3_1_from_empty(self):
        """Test from empty hand."""
        mg = MovesGener([])
        result = mg.gen_type_6_3_1()
        assert result == []

    def test_3_1_valid(self):
        """Test valid 3+1 combinations."""
        mg = MovesGener([5, 5, 5, 3, 4])
        result = mg.gen_type_6_3_1()
        # Check that result contains the expected combinations (order may vary)
        assert len(result) > 0
        has_3_kicker = any(sorted(move) == [3, 5, 5, 5] for move in result)
        has_4_kicker = any(sorted(move) == [4, 5, 5, 5] for move in result)
        assert has_3_kicker
        assert has_4_kicker


class TestGenType7_3_2:
    """Test gen_type_7_3_2 method."""

    def test_3_2_from_empty(self):
        """Test from empty hand."""
        mg = MovesGener([])
        result = mg.gen_type_7_3_2()
        assert result == []

    def test_3_2_valid(self):
        """Test valid 3+2 combinations."""
        mg = MovesGener([5, 5, 5, 3, 3])
        result = mg.gen_type_7_3_2()
        # Check that result contains expected combination (order may vary)
        assert len(result) > 0
        has_combination = any(sorted(move) == [3, 3, 5, 5, 5] for move in result)
        assert has_combination


class TestGenType8SerialSingle:
    """Test gen_type_8_serial_single method."""

    def test_serial_single_no_valid(self):
        """Test when no valid serial exists."""
        mg = MovesGener([3, 4, 5, 6])  # Only 4 cards, need 5
        result = mg.gen_type_8_serial_single()
        assert result == []

    def test_serial_single_valid(self):
        """Test valid serial singles."""
        mg = MovesGener([3, 4, 5, 6, 7, 8])
        result = mg.gen_type_8_serial_single()
        # Should include [3,4,5,6,7], [4,5,6,7,8], [3,4,5,6,7,8]
        assert [3, 4, 5, 6, 7] in result
        assert [4, 5, 6, 7, 8] in result
        assert [3, 4, 5, 6, 7, 8] in result

    def test_serial_single_with_repeat_num(self):
        """Test with specific repeat_num."""
        mg = MovesGener([3, 4, 5, 6, 7, 8])
        result = mg.gen_type_8_serial_single(repeat_num=5)
        assert [3, 4, 5, 6, 7] in result
        assert [4, 5, 6, 7, 8] in result
        assert [3, 4, 5, 6, 7, 8] not in result


class TestGenType9SerialPair:
    """Test gen_type_9_serial_pair method."""

    def test_serial_pair_no_valid(self):
        """Test when no valid serial pair exists."""
        mg = MovesGener([3, 3, 4, 4])  # Only 2 pairs, need 3
        result = mg.gen_type_9_serial_pair()
        assert result == []

    def test_serial_pair_valid(self):
        """Test valid serial pairs."""
        mg = MovesGener([3, 3, 4, 4, 5, 5])
        result = mg.gen_type_9_serial_pair()
        assert [3, 3, 4, 4, 5, 5] in result


class TestGenType10SerialTriple:
    """Test gen_type_10_serial_triple method."""

    def test_serial_triple_no_valid(self):
        """Test when no valid serial triple exists."""
        mg = MovesGener([3, 3, 3])  # Only 1 triple, need 2
        result = mg.gen_type_10_serial_triple()
        assert result == []

    def test_serial_triple_valid(self):
        """Test valid serial triples."""
        mg = MovesGener([3, 3, 3, 4, 4, 4])
        result = mg.gen_type_10_serial_triple()
        assert [3, 3, 3, 4, 4, 4] in result


class TestGenType11Serial3_1:
    """Test gen_type_11_serial_3_1 method."""

    def test_serial_3_1_valid(self):
        """Test valid serial 3+1."""
        mg = MovesGener([3, 3, 3, 4, 4, 4, 5, 6])
        result = mg.gen_type_11_serial_3_1()
        # Should have combinations with different kicker cards
        assert len(result) > 0


class TestGenType12Serial3_2:
    """Test gen_type_12_serial_3_2 method."""

    def test_serial_3_2_valid(self):
        """Test valid serial 3+2."""
        mg = MovesGener([3, 3, 3, 4, 4, 4, 5, 5, 6, 6])
        result = mg.gen_type_12_serial_3_2()
        assert len(result) > 0


class TestGenType13_4_2:
    """Test gen_type_13_4_2 method."""

    def test_4_2_with_bomb(self):
        """Test 4+2 with bomb."""
        mg = MovesGener([7, 7, 7, 7, 3, 4])
        result = mg.gen_type_13_4_2()
        assert len(result) > 0

    def test_4_2_no_bomb(self):
        """Test when no bomb exists."""
        mg = MovesGener([7, 7, 7, 3, 4])
        result = mg.gen_type_13_4_2()
        assert result == []


class TestGenType14_4_22:
    """Test gen_type_14_4_22 method."""

    def test_4_22_with_bomb_and_pairs(self):
        """Test 4+22 with bomb and pairs."""
        mg = MovesGener([7, 7, 7, 7, 3, 3, 4, 4])
        result = mg.gen_type_14_4_22()
        assert len(result) > 0


class TestGenMoves:
    """Test gen_moves method."""

    def test_gen_moves_comprehensive(self):
        """Test generating all possible moves."""
        mg = MovesGener([3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 7, 7])
        result = mg.gen_moves()
        # Should include singles, pairs, triples, bombs, etc.
        assert len(result) > 0
        # Check for singles
        assert any(len(m) == 1 and m[0] == 3 for m in result)
        # Check for pairs
        assert any(len(m) == 2 and m == [3, 3] for m in result)
        # Check for bombs
        assert any(len(m) == 4 and m == [7, 7, 7, 7] for m in result)
