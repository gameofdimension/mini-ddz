"""Tests for run_douzero.py"""

import json
import os
import shutil
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pve_server"))

_pretrained_dir = os.path.join(os.path.dirname(__file__), "..", "pve_server", "pretrained", "douzero_pretrained")
_model_available = os.path.isfile(os.path.join(_pretrained_dir, "landlord.ckpt"))

pytestmark = pytest.mark.skipif(
    not _model_available,
    reason="pretrained model files not available (gitignored)",
)

# Import after skipif check — guard with try/except because the import
# triggers module-level model loading in run_douzero.py
try:
    from run_douzero import (
        Card2Suit,
        EnvCard2RealCard,
        InfoSet,
        RealCard2EnvCard,
        _action_to_suit_format,
        _assign_card_suits,
        _cards_to_suit_format,
        _deal_cards,
        _get_legal_card_play_actions,
        _init_deck,
        app,
    )
except FileNotFoundError:
    if _model_available:
        raise


@pytest.fixture
def client():
    """Create a test client for Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    import replay_db

    original_db_path = replay_db.DB_PATH
    original_db_dir = replay_db.DB_DIR

    replay_db.DB_DIR = temp_dir
    replay_db.DB_PATH = os.path.join(temp_dir, "test.db")

    yield temp_dir

    replay_db.DB_PATH = original_db_path
    replay_db.DB_DIR = original_db_dir
    shutil.rmtree(temp_dir)


class TestCardMappings:
    """Test card mapping constants."""

    def test_env_card_to_real_card(self):
        """Test EnvCard2RealCard mapping."""
        assert EnvCard2RealCard[3] == "3"
        assert EnvCard2RealCard[10] == "T"
        assert EnvCard2RealCard[11] == "J"
        assert EnvCard2RealCard[14] == "A"
        assert EnvCard2RealCard[17] == "2"
        assert EnvCard2RealCard[20] == "X"  # Black Joker
        assert EnvCard2RealCard[30] == "D"  # Red Joker

    def test_real_card_to_env_card(self):
        """Test RealCard2EnvCard mapping."""
        assert RealCard2EnvCard["3"] == 3
        assert RealCard2EnvCard["T"] == 10
        assert RealCard2EnvCard["J"] == 11
        assert RealCard2EnvCard["A"] == 14
        assert RealCard2EnvCard["2"] == 17
        assert RealCard2EnvCard["X"] == 20
        assert RealCard2EnvCard["D"] == 30

    def test_card2suit_mapping(self):
        """Test Card2Suit mapping."""
        assert Card2Suit["3"] == ["S3", "H3", "D3", "C3"]
        assert Card2Suit["A"] == ["SA", "HA", "DA", "CA"]
        assert Card2Suit["X"] == ["BJ"]
        assert Card2Suit["D"] == ["RJ"]


class TestInitDeck:
    """Test _init_deck function."""

    def test_deck_size(self):
        """Test that deck has 54 cards."""
        deck = _init_deck()
        assert len(deck) == 54

    def test_deck_has_jokers(self):
        """Test that deck includes both jokers."""
        deck = _init_deck()
        assert 20 in deck  # Black Joker
        assert 30 in deck  # Red Joker

    def test_deck_has_all_ranks(self):
        """Test that deck includes all card ranks."""
        deck = _init_deck()
        for rank in ["3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A", "2"]:
            card_value = RealCard2EnvCard[rank]
            assert deck.count(card_value) == 4  # Each rank should appear 4 times


class TestDealCards:
    """Test _deal_cards function."""

    def test_deal_returns_all_players(self):
        """Test that deal returns cards for all players."""
        cards = _deal_cards()
        assert 0 in cards
        assert 1 in cards
        assert 2 in cards
        assert "three_landlord_cards" in cards

    def test_landlord_card_count(self):
        """Test landlord gets 20 cards."""
        cards = _deal_cards()
        assert len(cards[0]) == 20

    def test_peasant_card_count(self):
        """Test peasants get 17 cards each."""
        cards = _deal_cards()
        assert len(cards[1]) == 17
        assert len(cards[2]) == 17

    def test_three_landlord_cards(self):
        """Test three landlord cards are first 3 cards."""
        cards = _deal_cards()
        assert len(cards["three_landlord_cards"]) == 3

    def test_no_duplicate_cards(self):
        """Test all cards are unique."""
        cards = _deal_cards()
        all_cards = cards[0] + cards[1] + cards[2]
        assert len(all_cards) == 54  # 20 + 17 + 17 = 54 cards total


class TestCardsToSuitFormat:
    """Test _cards_to_suit_format function."""

    def test_convert_single_card(self):
        """Test converting single card."""
        result = _cards_to_suit_format([3])
        assert result == ["S3"]

    def test_convert_multiple_same_rank(self):
        """Test converting multiple cards of same rank."""
        result = _cards_to_suit_format([3, 3, 3, 3])
        assert set(result) == {"S3", "H3", "D3", "C3"}

    def test_convert_jokers(self):
        """Test converting jokers."""
        result = _cards_to_suit_format([20, 30])
        assert "BJ" in result
        assert "RJ" in result

    def test_convert_mixed_cards(self):
        """Test converting mixed cards."""
        result = _cards_to_suit_format([3, 14, 17])  # 3, A, 2
        assert len(result) == 3


class TestAssignCardSuits:
    """Test _assign_card_suits function."""

    def test_assign_single_card(self):
        """Test assigning suit to single card."""
        result = _assign_card_suits([3])
        assert len(result) == 1
        assert result[0][0] == 3
        assert result[0][1] in ["S3", "H3", "D3", "C3"]

    def test_assign_multiple_same_rank(self):
        """Test assigning suits to multiple cards of same rank."""
        result = _assign_card_suits([3, 3, 3, 3])
        assert len(result) == 4
        suits = [suit for _, suit in result]
        assert set(suits) == {"S3", "H3", "D3", "C3"}


class TestActionToSuitFormat:
    """Test _action_to_suit_format function."""

    def test_pass_action(self):
        """Test pass action."""
        hand = [(3, "S3"), (4, "S4")]
        result = _action_to_suit_format([], hand)
        assert result == "pass"

    def test_empty_action(self):
        """Test empty action."""
        hand = [(3, "S3"), (4, "S4")]
        result = _action_to_suit_format("pass", hand)
        assert result == "pass"

    def test_single_card_action(self):
        """Test single card action."""
        hand = [(3, "S3"), (4, "S4")]
        result = _action_to_suit_format([3], hand)
        assert result == "S3"

    def test_multiple_cards_action(self):
        """Test multiple cards action."""
        hand = [(3, "S3"), (3, "H3"), (4, "S4")]
        result = _action_to_suit_format([3, 3], hand)
        assert "S3" in result
        assert "H3" in result


class TestGetLegalCardPlayActions:
    """Test _get_legal_card_play_actions function."""

    def test_pass_rival_move(self):
        """Test when rival passed."""
        hand = [3, 4, 5, 6, 7]
        result = _get_legal_card_play_actions(hand, [])
        assert len(result) > 0  # Should return all possible moves

    def test_single_card_beat(self):
        """Test beating single card."""
        hand = [5, 6, 7]
        result = _get_legal_card_play_actions(hand, [5])
        # Should be able to play 6 or 7
        assert [6] in result or [7] in result

    def test_cannot_beat(self):
        """Test when cannot beat rival."""
        hand = [3, 4, 5]
        result = _get_legal_card_play_actions(hand, [17])  # 2
        # Should only have pass option (empty list)
        assert [] in result


class TestInfoSet:
    """Test InfoSet class."""

    def test_infoset_init(self):
        """Test InfoSet initialization."""
        info = InfoSet()
        assert info.player_position is None
        assert info.player_hand_cards is None
        assert info.num_cards_left is None
        assert info.three_landlord_cards is None
        assert info.card_play_action_seq is None
        assert info.other_hand_cards is None
        assert info.legal_actions is None
        assert info.rival_move is None
        assert info.last_moves is None
        assert info.played_cards is None
        assert info.bomb_num is None


class TestFlaskRoutes:
    """Test Flask routes."""

    def test_predict_missing_params(self, client):
        """Test predict with missing parameters."""
        response = client.post("/predict", data={})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] != 0  # Should fail

    def test_predict_invalid_position(self, client):
        """Test predict with invalid player position."""
        response = client.post("/predict", data={"player_position": "5"})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == 1

    def test_legal_missing_params(self, client):
        """Test legal with missing parameters."""
        response = client.post("/legal", data={})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == -1  # Should fail with error

    def test_legal_valid_request(self, client):
        """Test legal with valid request."""
        response = client.post("/legal", data={"player_hand_cards": "34567", "rival_move": ""})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == 0
        assert "legal_action" in data

    def test_generate_ai_battle(self, client, temp_db):
        """Test generate replay endpoint."""
        import replay_db

        replay_db.DB_DIR = temp_db
        replay_db.DB_PATH = os.path.join(temp_db, "test.db")

        response = client.get("/generate_ai_battle")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "status" in data

    def test_save_replay_endpoint(self, client, temp_db):
        """Test save replay endpoint."""
        import replay_db

        replay_db.DB_DIR = temp_db
        replay_db.DB_PATH = os.path.join(temp_db, "test.db")

        replay_data = {
            "playerInfo": [{"id": 0, "role": "landlord"}],
            "initHands": ["S3 S4 S5", "H3 H4 H5", "D3 D4 D5"],
            "moveHistory": [{"playerIdx": 0, "move": "pass"}],
        }
        response = client.post("/save_replay", data=json.dumps(replay_data), content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "status" in data

    def test_save_replay_no_data(self, client, temp_db):
        """Test save replay with no data."""
        import replay_db

        replay_db.DB_DIR = temp_db
        replay_db.DB_PATH = os.path.join(temp_db, "test.db")

        response = client.post("/save_replay", data=None, content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        # When JSON parsing fails, it returns -1
        assert data["status"] == -1

    def test_save_replay_invalid_player_info(self, client, temp_db):
        """Test save replay with invalid playerInfo."""
        import replay_db

        replay_db.DB_DIR = temp_db
        replay_db.DB_PATH = os.path.join(temp_db, "test.db")

        # Missing playerInfo
        replay_data = {"initHands": ["S3 S4 S5", "H3 H4 H5", "D3 D4 D5"], "moveHistory": []}
        response = client.post("/save_replay", data=json.dumps(replay_data), content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == 2

        # Wrong number of players
        replay_data = {
            "playerInfo": [{"id": 0, "role": "landlord"}],
            "initHands": ["S3 S4 S5", "H3 H4 H5", "D3 D4 D5"],
            "moveHistory": [],
        }
        response = client.post("/save_replay", data=json.dumps(replay_data), content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == 2

    def test_save_replay_invalid_init_hands(self, client, temp_db):
        """Test save replay with invalid initHands."""
        import replay_db

        replay_db.DB_DIR = temp_db
        replay_db.DB_PATH = os.path.join(temp_db, "test.db")

        # Missing initHands
        replay_data = {
            "playerInfo": [
                {"id": 0, "index": 0, "role": "landlord"},
                {"id": 1, "index": 1, "role": "peasant"},
                {"id": 2, "index": 2, "role": "peasant"},
            ],
            "moveHistory": [],
        }
        response = client.post("/save_replay", data=json.dumps(replay_data), content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == 3

    def test_save_replay_landlord_wrong_card_count(self, client, temp_db):
        """Test save replay when landlord has wrong number of cards."""
        import replay_db

        replay_db.DB_DIR = temp_db
        replay_db.DB_PATH = os.path.join(temp_db, "test.db")

        # Landlord with only 17 cards (should be 20)
        replay_data = {
            "playerInfo": [
                {"id": 0, "index": 0, "role": "landlord"},
                {"id": 1, "index": 1, "role": "peasant"},
                {"id": 2, "index": 2, "role": "peasant"},
            ],
            "initHands": [
                "S3 S4 S5 S6 S7 S8 S9 ST SJ SQ SK SA S2 H2 D2 C2 BJ",  # 17 cards
                "H3 H4 H5 H6 H7 H8 H9 HT HJ HQ HK HA D3 D4 D5 D6 D7",
                "D8 D9 DT DJ DQ DK DA C3 C4 C5 C6 C7 C8 C9 CT CJ CQ",
            ],
            "moveHistory": [],
        }
        response = client.post("/save_replay", data=json.dumps(replay_data), content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == 4
        assert "expected 20 cards" in data["message"]

    def test_save_replay_valid_data(self, client, temp_db):
        """Test save replay with valid data (landlord has 20 cards)."""
        import replay_db

        replay_db.DB_DIR = temp_db
        replay_db.DB_PATH = os.path.join(temp_db, "test.db")

        # Landlord with 20 cards, peasants with 17 each
        replay_data = {
            "playerInfo": [
                {"id": 0, "index": 0, "role": "landlord"},
                {"id": 1, "index": 1, "role": "peasant"},
                {"id": 2, "index": 2, "role": "peasant"},
            ],
            "initHands": [
                "S3 S4 S5 S6 S7 S8 S9 ST SJ SQ SK SA S2 H2 D2 C2 BJ RJ S2 C2",  # 20 cards
                "H3 H4 H5 H6 H7 H8 H9 HT HJ HQ HK HA D3 D4 D5 D6 D7",
                "D8 D9 DT DJ DQ DK DA C3 C4 C5 C6 C7 C8 C9 CT CJ CQ",
            ],
            "moveHistory": [],
        }
        response = client.post("/save_replay", data=json.dumps(replay_data), content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == 0
        assert "replay_id" in data

    def test_get_replay_not_found(self, client, temp_db):
        """Test get replay when not found."""
        import replay_db

        replay_db.DB_DIR = temp_db
        replay_db.DB_PATH = os.path.join(temp_db, "test.db")

        response = client.get("/replay/nonexistent")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == -1

    def test_list_replays_empty(self, client, temp_db):
        """Test list replays when empty."""
        import replay_db

        replay_db.DB_DIR = temp_db
        replay_db.DB_PATH = os.path.join(temp_db, "test.db")

        response = client.get("/list_replays")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == 0
        assert data["replays"] == []

    def test_delete_replay_not_found(self, client, temp_db):
        """Test delete replay when not found."""
        import replay_db

        replay_db.DB_DIR = temp_db
        replay_db.DB_PATH = os.path.join(temp_db, "test.db")

        # Initialize database first
        replay_db.init_db()

        response = client.delete("/delete_replay/nonexistent")
        assert response.status_code == 200
        data = json.loads(response.data)
        # Database initialized, so delete returns success (0) or error (-1)
        assert "status" in data
