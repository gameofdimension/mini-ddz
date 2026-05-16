"""Tests for llm_agent.py."""

import json
from unittest.mock import MagicMock, patch

import pytest
from game import InfoSet
from llm_agent import LLMAgent


@pytest.fixture
def mock_config(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")


class TestCardConversion:
    def test_env_action_to_str_normal(self, mock_config):
        agent = LLMAgent(0)
        assert agent._env_action_to_str([3, 4, 5]) == "345"
        assert agent._env_action_to_str([14, 14, 14, 14]) == "AAAA"
        assert agent._env_action_to_str([17]) == "2"
        assert agent._env_action_to_str([20, 30]) == "XD"

    def test_env_action_to_str_empty(self, mock_config):
        agent = LLMAgent(0)
        assert agent._env_action_to_str([]) == ""

    def test_str_to_env_action_normal(self, mock_config):
        agent = LLMAgent(0)
        assert agent._str_to_env_action("345") == [3, 4, 5]
        assert agent._str_to_env_action("AAAA") == [14, 14, 14, 14]

    def test_str_to_env_action_pass(self, mock_config):
        agent = LLMAgent(0)
        assert agent._str_to_env_action("") == []
        assert agent._str_to_env_action("pass") == []


class TestParseResponse:
    def test_valid_response(self, mock_config):
        agent = LLMAgent(0)
        content = json.dumps({"analysis": "play straight", "action": "345", "confidence": 0.9})
        action, conf = agent._parse_response(content, [[3, 4, 5], [6], []])
        assert action == [3, 4, 5]
        assert conf == 0.9

    def test_pass_response(self, mock_config):
        agent = LLMAgent(0)
        content = json.dumps({"analysis": "better to pass", "action": "", "confidence": 0.8})
        action, conf = agent._parse_response(content, [[], [3, 4, 5]])
        assert action == []
        assert conf == 0.8

    def test_invalid_json_raises(self, mock_config):
        agent = LLMAgent(0)
        with pytest.raises(ValueError, match="Invalid JSON"):
            agent._parse_response("not json", [[3]])

    def test_illegal_action_raises(self, mock_config):
        agent = LLMAgent(0)
        content = json.dumps({"analysis": "test", "action": "999"})
        with pytest.raises(ValueError, match="not in"):
            agent._parse_response(content, [[3, 4, 5]])

    def test_missing_confidence_defaults(self, mock_config):
        agent = LLMAgent(0)
        content = json.dumps({"analysis": "test", "action": "3"})
        action, conf = agent._parse_response(content, [[3]])
        assert action == [3]
        assert conf == 0.0


class TestBuildUserMessage:
    def test_basic_message(self, mock_config):
        agent = LLMAgent(0)
        infoset = InfoSet(
            player_position=0,
            player_hand_cards=[3, 4, 5, 14, 14, 14, 14, 17],
            num_cards_left=[8, 8, 8],
            three_landlord_cards=[3, 4, 5],
            card_play_action_seq=[],
            other_hand_cards=[],
            legal_actions=[[3], [4], [5], [14, 14, 14, 14], []],
            rival_move=[],
            last_moves=[[], [], []],
            played_cards=[[], [], []],
            bomb_num=0,
        )
        msg = agent._build_user_message(infoset)
        assert "Player 0: landlord, Player 1: peasant" in msg
        assert "Player 0 (landlord)" in msg
        assert "2 A A A A 5 4 3" in msg
        assert "Player 0: 8, Player 1: 8, Player 2: 8" in msg
        assert "pass" in msg
        assert "AAAA" in msg


class TestFallbackAction:
    def test_returns_first_legal_action(self, mock_config):
        agent = LLMAgent(0)
        actions, confs = agent._fallback_action([[3], [4], []])
        assert actions == [[3]]
        assert confs == [0.0]

    def test_empty_legal_actions(self, mock_config):
        agent = LLMAgent(0)
        actions, confs = agent._fallback_action([])
        assert actions == [[]]
        assert confs == [0.0]


class TestAct:
    def test_successful_call(self, mock_config):
        agent = LLMAgent(0)
        legal_actions = [[3, 4, 5], [6], []]
        infoset = InfoSet(
            player_position=0,
            player_hand_cards=[3, 4, 5, 6],
            num_cards_left=[4, 0, 0],
            card_play_action_seq=[],
            other_hand_cards=[],
            legal_actions=legal_actions,
            rival_move=[],
            last_moves=[[], [], []],
            played_cards=[[], [], []],
            bomb_num=0,
        )

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({"analysis": "go", "action": "345", "confidence": 0.9})))
        ]

        with patch.object(agent, "_client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_response
            actions, confs = agent.act(infoset)

        assert actions == [[3, 4, 5]]
        assert confs == [0.9]

    def test_fallback_on_api_error(self, mock_config):
        agent = LLMAgent(0)
        legal_actions = [[6], []]
        infoset = InfoSet(
            player_position=0,
            player_hand_cards=[6],
            num_cards_left=[1, 0, 0],
            card_play_action_seq=[],
            other_hand_cards=[],
            legal_actions=legal_actions,
            rival_move=[],
            last_moves=[[], [], []],
            played_cards=[[], [], []],
            bomb_num=0,
        )

        with patch.object(agent, "_call_llm", side_effect=RuntimeError("API down")):
            actions, confs = agent.act(infoset)

        assert actions == [[6]]
        assert confs == [0.0]
