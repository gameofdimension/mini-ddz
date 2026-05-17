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

    def test_no_fallback_count_attribute(self):
        """RandomAgent has no fallback path, so fallback_count should not exist."""
        agent = RandomAgent(0)
        assert not hasattr(agent, "fallback_count")

    def test_only_essential_attributes(self):
        """RandomAgent should have a minimal interface — just position and act."""
        agent = RandomAgent(2)
        assert agent.position == 2
        assert callable(agent.act)
        public_attrs = [k for k in vars(agent) if not k.startswith("_")]
        assert public_attrs == ["position"]
