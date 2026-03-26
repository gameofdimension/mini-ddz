"""Tests for deep.py"""

import numpy as np
import pytest
import torch
from deep import Card2Column, NumOnes2Array, _get_one_hot_bomb, _process_action_seq


class TestCard2Column:
    """Test Card2Column mapping."""

    def test_card2column_exists(self):
        """Test that Card2Column mapping exists."""
        assert Card2Column is not None
        assert isinstance(Card2Column, dict)

    def test_low_cards_mapped(self):
        """Test low cards are mapped."""
        assert Card2Column[3] == 0
        assert Card2Column[4] == 1
        assert Card2Column[7] == 4

    def test_face_cards_mapped(self):
        """Test face cards are mapped."""
        assert Card2Column[11] == 8  # J
        assert Card2Column[12] == 9  # Q
        assert Card2Column[13] == 10  # K

    def test_high_cards_mapped(self):
        """Test high cards are mapped."""
        assert Card2Column[14] == 11  # A
        assert Card2Column[17] == 12  # 2
        assert Card2Column[20] == 13  # Black Joker
        assert Card2Column[30] == 14  # Red Joker


class TestNumOnes2Array:
    """Test NumOnes2Array mapping."""

    def test_zero_ones(self):
        """Test zero ones array."""
        arr = NumOnes2Array[0]
        assert np.array_equal(arr, np.array([0, 0, 0, 0]))

    def test_one_one(self):
        """Test one one array."""
        arr = NumOnes2Array[1]
        assert arr[0] == 1
        assert arr[1] == 0

    def test_four_ones(self):
        """Test four ones array (bomb)."""
        arr = NumOnes2Array[4]
        assert np.array_equal(arr, np.array([1, 1, 1, 1]))


class TestGetOneHotBomb:
    """Test _get_one_hot_bomb function."""

    def test_zero_bombs(self):
        """Test one-hot for zero bombs."""
        result = _get_one_hot_bomb(0)
        assert result[0] == 1
        assert result.dtype == np.float32

    def test_one_bomb(self):
        """Test one-hot for one bomb."""
        result = _get_one_hot_bomb(1)
        assert result[1] == 1

    def test_multiple_bombs(self):
        """Test one-hot for multiple bombs."""
        result = _get_one_hot_bomb(5)
        assert result[5] == 1

    def test_bomb_array_length(self):
        """Test that bomb array has correct length."""
        result = _get_one_hot_bomb(0)
        assert len(result) == 15


class TestProcessActionSeq:
    """Test _process_action_seq function."""

    def test_short_sequence(self):
        """Test processing short action sequence."""
        seq = [[3], [4], [5]]
        result = _process_action_seq(seq, length=15)
        assert len(result) == 15
        # First 12 should be empty, last 3 should be our cards
        assert result[12] == [3]
        assert result[13] == [4]
        assert result[14] == [5]

    def test_exact_length_sequence(self):
        """Test processing exact length sequence."""
        seq = [[] for _ in range(15)]
        result = _process_action_seq(seq, length=15)
        assert len(result) == 15

    def test_long_sequence(self):
        """Test processing long action sequence."""
        seq = [[i] for i in range(20)]
        result = _process_action_seq(seq, length=15)
        assert len(result) == 15


class TestDeepAgent:
    """Test DeepAgent class."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model for testing."""

        class MockModel:
            def __init__(self, position, model_dir, use_onnx):
                self.position = position
                self.model_dir = model_dir
                self.use_onnx = use_onnx

            def run(self, output_names, input_feed):
                return [[0.5, 0.3, 0.2]]

            def forward(self, z, x):
                return torch.tensor([[0.5], [0.3], [0.2]])

            def __call__(self, z, x):
                return self.forward(z, x)

        return MockModel

    def test_deep_agent_init_landlord(self, monkeypatch, mock_model):
        """Test DeepAgent initialization for landlord."""
        import deep

        monkeypatch.setattr(
            deep,
            "_load_model",
            lambda pos, model_dir, use_onnx: mock_model(pos, model_dir, use_onnx),
        )

        from deep import DeepAgent

        agent = DeepAgent("landlord", "/tmp/test", use_onnx=False)
        assert agent is not None
        assert hasattr(agent, "model")
        assert agent.use_onnx is False

    def test_deep_agent_init_landlord_up(self, monkeypatch, mock_model):
        """Test DeepAgent initialization for landlord_up."""
        import deep

        monkeypatch.setattr(
            deep,
            "_load_model",
            lambda pos, model_dir, use_onnx: mock_model(pos, model_dir, use_onnx),
        )

        from deep import DeepAgent

        agent = DeepAgent("landlord_up", "/tmp/test", use_onnx=False)
        assert hasattr(agent, "model")

    def test_cards2array_empty(self, monkeypatch, mock_model):
        """Test converting empty cards to array."""
        import deep

        monkeypatch.setattr(
            deep,
            "_load_model",
            lambda pos, model_dir, use_onnx: mock_model(pos, model_dir, use_onnx),
        )

        from deep import DeepAgent

        agent = DeepAgent("landlord", "/tmp/test", use_onnx=False)
        result = agent.cards2array([])
        assert len(result) == 54
        assert np.all(result == 0)

    def test_cards2array_with_cards(self, monkeypatch, mock_model):
        """Test converting cards to array."""
        import deep

        monkeypatch.setattr(
            deep,
            "_load_model",
            lambda pos, model_dir, use_onnx: mock_model(pos, model_dir, use_onnx),
        )

        from deep import DeepAgent

        agent = DeepAgent("landlord", "/tmp/test", use_onnx=False)
        # Test with a 3 of spades (value 3)
        result = agent.cards2array([3])
        assert len(result) == 54

    def test_cards2array_with_jokers(self, monkeypatch, mock_model):
        """Test converting jokers."""
        import deep

        monkeypatch.setattr(
            deep,
            "_load_model",
            lambda pos, model_dir, use_onnx: mock_model(pos, model_dir, use_onnx),
        )

        from deep import DeepAgent

        agent = DeepAgent("landlord", "/tmp/test", use_onnx=False)
        result = agent.cards2array([20, 30])
        assert len(result) == 54
        # Last two positions are jokers
        assert result[52] == 1  # Black joker
        assert result[53] == 1  # Red joker

    def test_get_one_hot_array(self, monkeypatch, mock_model):
        """Test one-hot encoding for card counts."""
        import deep

        monkeypatch.setattr(
            deep,
            "_load_model",
            lambda pos, model_dir, use_onnx: mock_model(pos, model_dir, use_onnx),
        )

        from deep import DeepAgent

        agent = DeepAgent("landlord", "/tmp/test", use_onnx=False)
        result = agent.get_one_hot_array(5, 20)
        assert result[4] == 1  # 5th position (index 4) should be 1
        assert len(result) == 20

    def test_action_seq_list2array(self, monkeypatch, mock_model):
        """Test converting action sequence to array."""
        import deep

        monkeypatch.setattr(
            deep,
            "_load_model",
            lambda pos, model_dir, use_onnx: mock_model(pos, model_dir, use_onnx),
        )

        from deep import DeepAgent

        agent = DeepAgent("landlord", "/tmp/test", use_onnx=False)
        seq = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
        result = agent.action_seq_list2array(seq)
        # Result should be reshaped to (5, 162)
        assert result.shape == (5, 162)

    def test_act_landlord(self, monkeypatch, mock_model):
        """Test act method for landlord."""
        import deep

        monkeypatch.setattr(
            deep,
            "_load_model",
            lambda pos, model_dir, use_onnx: mock_model(pos, model_dir, use_onnx),
        )

        from deep import DeepAgent

        class MockInfoSet:
            def __init__(self):
                self.player_position = 0  # landlord
                self.player_hand_cards = [3, 4, 5, 6, 7]
                self.num_cards_left = [20, 17, 17]
                self.three_landlord_cards = []
                self.card_play_action_seq = []
                self.other_hand_cards = [8, 9, 10]
                self.played_cards = [[], [], []]
                self.bomb_num = 0
                self.rival_move = []
                self.legal_actions = [[3], [4], [5]]
                self.last_moves = [[], [], []]

        agent = DeepAgent("landlord", "/tmp/test", use_onnx=False)
        infoset = MockInfoSet()
        actions, confidences = agent.act(infoset)
        assert isinstance(actions, list)
        # confidences can be list or numpy array
        assert hasattr(confidences, "__len__")

    def test_act_farmer(self, monkeypatch, mock_model):
        """Test act method for farmer."""
        import deep

        monkeypatch.setattr(
            deep,
            "_load_model",
            lambda pos, model_dir, use_onnx: mock_model(pos, model_dir, use_onnx),
        )

        from deep import DeepAgent

        class MockInfoSet:
            def __init__(self):
                self.player_position = 1  # farmer (landlord_down)
                self.player_hand_cards = [3, 4, 5, 6, 7]
                self.num_cards_left = [20, 17, 17]
                self.three_landlord_cards = []
                self.card_play_action_seq = []
                self.other_hand_cards = [8, 9, 10]
                self.played_cards = [[], [], []]
                self.bomb_num = 0
                self.rival_move = []
                self.legal_actions = [[3], [4], [5]]
                self.last_moves = [[], [], []]

        agent = DeepAgent("landlord_down", "/tmp/test", use_onnx=False)
        infoset = MockInfoSet()
        actions, confidences = agent.act(infoset)
        assert isinstance(actions, list)
        # confidences can be list or numpy array
        assert hasattr(confidences, "__len__")
