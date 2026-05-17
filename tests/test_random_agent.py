"""Tests for random_agent.py."""

import pytest
from game import InfoSet
from random_agent import RandomAgent


class TestRandomAgent:
    def test_invalid_position_raises(self):
        with pytest.raises(ValueError, match="Invalid position"):
            RandomAgent(5)

    def test_act_returns_legal_action(self):
        agent = RandomAgent(0)
        legal_actions = [[3, 4, 5], [6], []]
        infoset = InfoSet(legal_actions=legal_actions)
        actions, confidences = agent.act(infoset)
        assert actions[0] in legal_actions
        assert confidences == [0.0]

    def test_act_empty_legal_actions(self):
        agent = RandomAgent(1)
        infoset = InfoSet(legal_actions=[])
        actions, confidences = agent.act(infoset)
        assert actions == [[]]
        assert confidences == [0.0]
