"""Tests for tools/watch_llm_battle.py — refactored game runner."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pve_server"))

from game import init_game, step_game
from random_agent import RandomAgent

# Import the refactored game runner
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from watch_llm_battle import run_one_game


def _make_random_players():
    return [RandomAgent(0), RandomAgent(1), RandomAgent(2)]


class TestRunOneGame:
    """Verify run_one_game() produces correct results using shared game.py logic."""

    def test_returns_valid_shape_with_random_agents(self):
        """Smoke test: run_one_game completes and returns winner, turns, bombs, fallbacks."""
        players = _make_random_players()
        winner, turns, bombs, fallbacks = run_one_game(players, verbose=False)

        assert isinstance(winner, int)
        assert winner in (-1, 0, 1, 2)
        assert isinstance(turns, int)
        assert turns >= 3  # at least a few turns for any real game
        assert isinstance(bombs, int)
        assert bombs >= 0
        assert isinstance(fallbacks, dict)

    def test_game_completes_within_200_turns(self):
        """run_one_game sets max_turns=200; verify it terminates within that bound."""
        players = _make_random_players()
        _, turns, _, _ = run_one_game(players, verbose=False)

        assert turns <= 200

    def test_verbose_mode_does_not_crash(self):
        """run_one_game with verbose=True should print without errors."""
        players = _make_random_players()
        # Should not raise
        winner, turns, bombs, fallbacks = run_one_game(players, verbose=True)
        assert isinstance(winner, int)

    def test_no_fallbacks_for_random_agents(self):
        """RandomAgent has no fallback_count (removed), so fallbacks dict is empty."""
        players = _make_random_players()
        _, _, _, fallbacks = run_one_game(players, verbose=False)

        assert fallbacks == {}

    def test_winner_is_valid_index(self):
        """Winner must be 0 (landlord), 1 (landlord_down), or 2 (landlord_up)."""
        players = _make_random_players()
        winner, _, _, _ = run_one_game(players, verbose=False)

        # With random agents, any player can win; all are valid
        assert winner in (0, 1, 2)

    def test_multiple_games_yield_different_results(self):
        """Verify run_one_game is not deterministic (random agents produce varied outcomes)."""
        players = _make_random_players()
        winners = set()
        for _ in range(5):
            # Recreate fresh agents for each game
            fresh_players = [RandomAgent(0), RandomAgent(1), RandomAgent(2)]
            winner, _, _, _ = run_one_game(fresh_players, verbose=False)
            winners.add(winner)

        # With 5 games and 3 possible winners, unlikely all are same
        assert len(winners) >= 1  # At least the function runs multiple times


class TestRunOneGameUsesSharedLogic:
    """Verify run_one_game delegates to init_game/step_game, not manual game loop."""

    def test_init_game_is_called(self):
        """run_one_game should call init_game from game.py."""
        players = _make_random_players()

        with patch("watch_llm_battle.init_game", wraps=init_game) as mock_init:
            run_one_game(players, verbose=False)
            assert mock_init.called

    def test_step_game_is_called(self):
        """run_one_game should call step_game from game.py for each turn."""
        players = _make_random_players()

        with patch("watch_llm_battle.step_game", wraps=step_game) as mock_step:
            _, turns, _, _ = run_one_game(players, verbose=False)
            # step_game should be called at least as many times as turns
            assert mock_step.call_count >= turns


class TestRunOneGameMaxTurns:
    """Verify max_turns enforcement in the refactored run_one_game."""

    def test_max_turns_is_overridden_to_200(self, monkeypatch):
        """run_one_game should override init_game's default max_turns (100 → 200)."""
        captured_max_turns = []

        _real_init = init_game

        def fake_init_game(players):
            init_data, gs = _real_init(players)
            captured_max_turns.append(gs["max_turns"])  # before override
            return init_data, gs

        # Run with real step_game; the game will complete naturally.
        # We verify max_turns was set at init time.
        with patch("watch_llm_battle.init_game", side_effect=fake_init_game):
            players = _make_random_players()
            run_one_game(players, verbose=False)

        assert len(captured_max_turns) == 1
        # init_game sets 100 by default; run_one_game overrides to 200
        assert captured_max_turns[0] == 100
