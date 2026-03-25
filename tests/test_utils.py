"""Tests for utils/utils.py"""
import pytest
import sys
import os

# Add pve_server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pve_server'))

from utils.utils import (
    MIN_SINGLE_CARDS, MIN_PAIRS, MIN_TRIPLES,
    TYPE_0_PASS, TYPE_1_SINGLE, TYPE_2_PAIR, TYPE_3_TRIPLE,
    TYPE_4_BOMB, TYPE_5_KING_BOMB, TYPE_6_3_1, TYPE_7_3_2,
    TYPE_8_SERIAL_SINGLE, TYPE_9_SERIAL_PAIR, TYPE_10_SERIAL_TRIPLE,
    TYPE_11_SERIAL_3_1, TYPE_12_SERIAL_3_2, TYPE_13_4_2, TYPE_14_4_22,
    TYPE_15_WRONG, PASS, CALL, RAISE, select
)


class TestConstants:
    """Test constant values."""

    def test_min_values(self):
        """Test minimum card values for sequences."""
        assert MIN_SINGLE_CARDS == 5
        assert MIN_PAIRS == 3
        assert MIN_TRIPLES == 2

    def test_action_types(self):
        """Test action type constants."""
        assert TYPE_0_PASS == 0
        assert TYPE_1_SINGLE == 1
        assert TYPE_2_PAIR == 2
        assert TYPE_3_TRIPLE == 3
        assert TYPE_4_BOMB == 4
        assert TYPE_5_KING_BOMB == 5
        assert TYPE_6_3_1 == 6
        assert TYPE_7_3_2 == 7
        assert TYPE_8_SERIAL_SINGLE == 8
        assert TYPE_9_SERIAL_PAIR == 9
        assert TYPE_10_SERIAL_TRIPLE == 10
        assert TYPE_11_SERIAL_3_1 == 11
        assert TYPE_12_SERIAL_3_2 == 12
        assert TYPE_13_4_2 == 13
        assert TYPE_14_4_22 == 14
        assert TYPE_15_WRONG == 15

    def test_betting_actions(self):
        """Test betting round action constants."""
        assert PASS == 0
        assert CALL == 1
        assert RAISE == 2


class TestSelect:
    """Test select function."""

    def test_select_single_card(self):
        """Test selecting 1 card from list."""
        cards = [1, 2, 3]
        result = select(cards, 1)
        assert [1] in result
        assert [2] in result
        assert [3] in result
        assert len(result) == 3

    def test_select_two_cards(self):
        """Test selecting 2 cards from list."""
        cards = [1, 2, 3]
        result = select(cards, 2)
        assert [1, 2] in result
        assert [1, 3] in result
        assert [2, 3] in result
        assert len(result) == 3

    def test_select_all_cards(self):
        """Test selecting all cards from list."""
        cards = [1, 2, 3]
        result = select(cards, 3)
        assert [1, 2, 3] in result
        assert len(result) == 1

    def test_select_empty_list(self):
        """Test selecting from empty list."""
        cards = []
        result = select(cards, 1)
        assert result == []

    def test_select_more_than_available(self):
        """Test selecting more cards than available."""
        cards = [1, 2]
        result = select(cards, 3)
        assert result == []

    def test_select_zero_cards(self):
        """Test selecting 0 cards."""
        cards = [1, 2, 3]
        result = select(cards, 0)
        assert [[]] == result
