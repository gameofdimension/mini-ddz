"""Tests for utils/move_detector.py"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pve_server'))

from utils.move_detector import is_continuous_seq, get_move_type
from utils.utils import (
    TYPE_0_PASS, TYPE_1_SINGLE, TYPE_2_PAIR, TYPE_3_TRIPLE,
    TYPE_4_BOMB, TYPE_5_KING_BOMB, TYPE_6_3_1, TYPE_7_3_2,
    TYPE_8_SERIAL_SINGLE, TYPE_9_SERIAL_PAIR, TYPE_10_SERIAL_TRIPLE,
    TYPE_11_SERIAL_3_1, TYPE_12_SERIAL_3_2, TYPE_13_4_2, TYPE_14_4_22,
    TYPE_15_WRONG
)


class TestIsContinuousSeq:
    """Test is_continuous_seq function."""

    def test_continuous_sequence(self):
        """Test valid continuous sequences."""
        assert is_continuous_seq([3, 4, 5]) is True
        assert is_continuous_seq([3, 4, 5, 6, 7]) is True
        assert is_continuous_seq([10, 11, 12]) is True

    def test_single_card_is_continuous(self):
        """Test single card is considered continuous."""
        assert is_continuous_seq([5]) is True

    def test_two_card_sequence(self):
        """Test two consecutive cards."""
        assert is_continuous_seq([3, 4]) is True

    def test_not_continuous(self):
        """Test non-continuous sequences."""
        assert is_continuous_seq([3, 5]) is False
        assert is_continuous_seq([3, 4, 6]) is False
        assert is_continuous_seq([3, 3, 4]) is False

    def test_empty_sequence(self):
        """Test empty sequence."""
        assert is_continuous_seq([]) is True


class TestGetMoveType:
    """Test get_move_type function."""

    def test_pass(self):
        """Test pass move."""
        result = get_move_type([])
        assert result['type'] == TYPE_0_PASS

    def test_single_card(self):
        """Test single card moves."""
        result = get_move_type([3])
        assert result['type'] == TYPE_1_SINGLE
        assert result['rank'] == 3

        result = get_move_type([14])  # Ace
        assert result['type'] == TYPE_1_SINGLE
        assert result['rank'] == 14

    def test_pair(self):
        """Test pair moves."""
        result = get_move_type([5, 5])
        assert result['type'] == TYPE_2_PAIR
        assert result['rank'] == 5

    def test_king_bomb(self):
        """Test king bomb (both jokers)."""
        result = get_move_type([20, 30])
        assert result['type'] == TYPE_5_KING_BOMB

    def test_two_cards_not_pair(self):
        """Test two different cards that don't form king bomb."""
        result = get_move_type([3, 4])
        assert result['type'] == TYPE_15_WRONG

    def test_triple(self):
        """Test triple moves."""
        result = get_move_type([7, 7, 7])
        assert result['type'] == TYPE_3_TRIPLE
        assert result['rank'] == 7

    def test_triple_wrong(self):
        """Test invalid triple."""
        result = get_move_type([7, 7, 8])
        assert result['type'] == TYPE_15_WRONG

    def test_bomb(self):
        """Test bomb (four of a kind)."""
        result = get_move_type([9, 9, 9, 9])
        assert result['type'] == TYPE_4_BOMB
        assert result['rank'] == 9

    def test_three_plus_one(self):
        """Test 3+1 combination."""
        result = get_move_type([6, 6, 6, 3])
        assert result['type'] == TYPE_6_3_1
        assert result['rank'] == 6

    def test_invalid_three_plus_one(self):
        """Test invalid 3+1 combination."""
        result = get_move_type([6, 6, 7, 8])
        assert result['type'] == TYPE_15_WRONG

    def test_three_plus_two(self):
        """Test 3+2 combination."""
        result = get_move_type([8, 8, 8, 3, 3])
        assert result['type'] == TYPE_7_3_2
        assert result['rank'] == 8

    def test_serial_single(self):
        """Test serial single (straight)."""
        result = get_move_type([3, 4, 5, 6, 7])
        assert result['type'] == TYPE_8_SERIAL_SINGLE
        assert result['rank'] == 3
        assert result['len'] == 5

        result = get_move_type([5, 6, 7, 8, 9, 10, 11])
        assert result['type'] == TYPE_8_SERIAL_SINGLE
        assert result['len'] == 7

    def test_serial_pair(self):
        """Test serial pair."""
        result = get_move_type([4, 4, 5, 5, 6, 6])
        assert result['type'] == TYPE_9_SERIAL_PAIR
        assert result['rank'] == 4
        assert result['len'] == 3

    def test_serial_triple(self):
        """Test serial triple."""
        result = get_move_type([5, 5, 5, 6, 6, 6])
        assert result['type'] == TYPE_10_SERIAL_TRIPLE
        assert result['rank'] == 5
        assert result['len'] == 2

    def test_serial_3_1(self):
        """Test serial 3+1."""
        result = get_move_type([5, 5, 5, 6, 6, 6, 3, 4])
        assert result['type'] == TYPE_11_SERIAL_3_1
        assert result['rank'] == 5
        assert result['len'] == 2

    def test_serial_3_2(self):
        """Test serial 3+2."""
        result = get_move_type([5, 5, 5, 6, 6, 6, 3, 3, 4, 4])
        assert result['type'] == TYPE_12_SERIAL_3_2
        assert result['rank'] == 5
        assert result['len'] == 2

    def test_four_plus_two(self):
        """Test four plus two single cards."""
        result = get_move_type([7, 7, 7, 7, 3, 4])
        assert result['type'] == TYPE_13_4_2
        assert result['rank'] == 7

        result = get_move_type([7, 7, 7, 7, 3, 3])
        assert result['type'] == TYPE_13_4_2
        assert result['rank'] == 7

    def test_four_plus_two_pairs(self):
        """Test four plus two pairs."""
        result = get_move_type([7, 7, 7, 7, 3, 3, 4, 4])
        assert result['type'] == TYPE_14_4_22
        assert result['rank'] == 7

        # Two bombs
        result = get_move_type([7, 7, 7, 7, 8, 8, 8, 8])
        assert result['type'] == TYPE_14_4_22
        assert result['rank'] == 8

    def test_wrong_moves(self):
        """Test invalid moves."""
        # Random combination
        result = get_move_type([3, 5, 7])
        assert result['type'] == TYPE_15_WRONG

        # Five different cards not continuous
        result = get_move_type([3, 4, 5, 7, 9])
        assert result['type'] == TYPE_15_WRONG
