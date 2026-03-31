"""Flask application for DouZero Dou Dizhu AI backend."""

import logging
import os
import uuid

from card_maps import EnvCard2RealCard, RealCard2EnvCard
from deep import DeepAgent
from flask import Flask, jsonify, request
from flask_cors import CORS
from game import InfoSet, _get_legal_card_play_actions, generate_ai_battle_data
from replay_db import delete_replay, get_replay, list_replays, save_replay

app = Flask(__name__)
CORS(app)
logger = logging.getLogger(__name__)

# Lazy-loaded AI players
_players = None


def _get_players():
    global _players
    if _players is None:
        pretrained_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pretrained", "douzero_pretrained")
        _players = [
            DeepAgent(pos, pretrained_dir, use_onnx=True) for pos in ["landlord", "landlord_down", "landlord_up"]
        ]
    return _players


@app.route("/predict", methods=["POST"])
def predict():
    try:
        player_position = request.form.get("player_position")
        if player_position not in ["0", "1", "2"]:
            return jsonify({"status": 1, "message": "player_position must be 0, 1, or 2"})
        player_position = int(player_position)

        raw_hand = request.form.get("player_hand_cards")
        if not raw_hand:
            return jsonify({"status": 1, "message": "player_hand_cards is required"})
        player_hand_cards = [RealCard2EnvCard[c] for c in raw_hand]
        if player_position == 0:
            if len(player_hand_cards) < 1 or len(player_hand_cards) > 20:
                return jsonify({"status": 2, "message": "the number of hand cards should be 1-20"})
        else:
            if len(player_hand_cards) < 1 or len(player_hand_cards) > 17:
                return jsonify({"status": 3, "message": "the number of hand cards should be 1-17"})

        try:
            num_cards_left = [
                int(request.form.get("num_cards_left_landlord", 0)),
                int(request.form.get("num_cards_left_landlord_down", 0)),
                int(request.form.get("num_cards_left_landlord_up", 0)),
            ]
        except (ValueError, TypeError):
            return jsonify({"status": 5, "message": "num_cards_left must be integers"})
        if num_cards_left[player_position] != len(player_hand_cards):
            return jsonify(
                {
                    "status": 4,
                    "message": "the number of cards left do not align with hand cards",
                }
            )
        if (
            num_cards_left[0] < 0
            or num_cards_left[1] < 0
            or num_cards_left[2] < 0
            or num_cards_left[0] > 20
            or num_cards_left[1] > 17
            or num_cards_left[2] > 17
        ):
            return jsonify({"status": 5, "message": "the number of cards left not in range"})

        raw_landlord = request.form.get("three_landlord_cards")
        if not raw_landlord:
            three_landlord_cards = []
        else:
            three_landlord_cards = [RealCard2EnvCard[c] for c in raw_landlord]
        if len(three_landlord_cards) > 3:
            return jsonify({"status": 6, "message": "the number of landlord cards should be 0-3"})

        if request.form.get("card_play_action_seq") == "":
            card_play_action_seq = []
        else:
            card_play_action_seq = [
                [RealCard2EnvCard[c] for c in cards] for cards in request.form.get("card_play_action_seq").split(",")
            ]

        raw_other = request.form.get("other_hand_cards")
        if not raw_other:
            other_hand_cards = []
        else:
            other_hand_cards = [RealCard2EnvCard[c] for c in raw_other]
        if len(other_hand_cards) != sum(num_cards_left) - num_cards_left[player_position]:
            return jsonify(
                {
                    "status": 7,
                    "message": "the number of the other hand cards do not align with the number of cards left",
                }
            )

        last_moves = []
        for field in ["last_move_landlord", "last_move_landlord_down", "last_move_landlord_up"]:
            last_moves.append([RealCard2EnvCard[c] for c in request.form.get(field)])

        played_cards = []
        for field in [
            "played_cards_landlord",
            "played_cards_landlord_down",
            "played_cards_landlord_up",
        ]:
            played_cards.append([RealCard2EnvCard[c] for c in request.form.get(field)])

        try:
            bomb_num = int(request.form.get("bomb_num", 0))
        except (ValueError, TypeError):
            return jsonify({"status": 5, "message": "bomb_num must be an integer"})

        info_set = InfoSet(
            player_position=player_position,
            player_hand_cards=player_hand_cards,
            num_cards_left=num_cards_left,
            three_landlord_cards=three_landlord_cards,
            card_play_action_seq=card_play_action_seq,
            other_hand_cards=other_hand_cards,
            last_moves=last_moves,
            played_cards=played_cards,
            bomb_num=bomb_num,
        )

        rival_move = []
        if card_play_action_seq:
            if not card_play_action_seq[-1]:
                rival_move = card_play_action_seq[-2]
            else:
                rival_move = card_play_action_seq[-1]
        info_set.rival_move = rival_move
        info_set.legal_actions = _get_legal_card_play_actions(player_hand_cards, rival_move)

        actions, actions_confidence = _get_players()[player_position].act(info_set)
        actions = ["".join([EnvCard2RealCard[a] for a in action]) for action in actions]
        result = {}
        win_rates = {}
        for i in range(len(actions)):
            win_rate = max(actions_confidence[i], -1)
            win_rate = min(win_rate, 1)
            win_rates[actions[i]] = str(round((win_rate + 1) / 2, 4))
            result[actions[i]] = str(round(actions_confidence[i], 6))

        if app.debug:
            logger.debug("Rival Move: %s", rival_move)
            logger.debug("legal_actions: %s", info_set.legal_actions)
            logger.debug("Result: %s", result)
            for key in request.form:
                logger.debug("%s: %s", key, request.form.get(key))

        return jsonify({"status": 0, "message": "success", "result": result, "win_rates": win_rates})
    except Exception:
        logger.exception("Error in /predict")
        return jsonify({"status": -1, "message": "unknown error"})


@app.route("/legal", methods=["POST"])
def legal():
    try:
        raw_hand = request.form.get("player_hand_cards", "")
        raw_rival = request.form.get("rival_move", "")
        if not raw_hand:
            return jsonify({"status": 1, "message": "player_hand_cards is required"})
        player_hand_cards = [RealCard2EnvCard[c] for c in raw_hand]
        rival_move = [RealCard2EnvCard[c] for c in raw_rival] if raw_rival else []
        legal_actions = _get_legal_card_play_actions(player_hand_cards, rival_move)
        legal_actions = ",".join(["".join([EnvCard2RealCard[a] for a in action]) for action in legal_actions])
        return jsonify({"status": 0, "message": "success", "legal_action": legal_actions})
    except Exception:
        logger.exception("Error in /legal")
        return jsonify({"status": -1, "message": "unknown error"})


@app.route("/generate_ai_battle", methods=["GET"])
def generate_ai_battle():
    """Generate a new replay by running a game with AI"""
    try:
        battle_data = generate_ai_battle_data(_get_players())
        battle_id = str(uuid.uuid4())[:8]
        battle_data["battle_id"] = battle_id
        battle_data["source"] = "ai_battle"

        if save_replay(battle_id, battle_data):
            return jsonify({"status": 0, "message": "success", "battle_id": battle_id, "data": battle_data})
        else:
            return jsonify({"status": -1, "message": "failed to save replay"})
    except Exception:
        logger.exception("Error in /generate_ai_battle")
        return jsonify({"status": -1, "message": "failed to generate replay"})


@app.route("/save_replay", methods=["POST"])
def save_replay_endpoint():
    """Save a replay from user game"""
    try:
        replay_data = request.get_json()
        if not replay_data:
            return jsonify({"status": 1, "message": "no data provided"})

        player_info = replay_data.get("playerInfo", [])
        init_hands = replay_data.get("initHands", [])

        if not player_info or len(player_info) != 3:
            return jsonify({"status": 2, "message": "invalid playerInfo: must have 3 players"})

        if not init_hands or len(init_hands) != 3:
            return jsonify({"status": 3, "message": "invalid initHands: must have 3 hands"})

        landlord_info = next((p for p in player_info if p.get("role") == "landlord"), None)
        if landlord_info:
            landlord_idx = landlord_info.get("index", 0)
            landlord_hand = init_hands[landlord_idx] if landlord_idx < len(init_hands) else ""
            landlord_card_count = len(landlord_hand.split()) if landlord_hand else 0
            if landlord_card_count != 20:
                return jsonify(
                    {
                        "status": 4,
                        "message": f"invalid landlord hand: expected 20 cards, got {landlord_card_count}",
                    }
                )

        replay_id = str(uuid.uuid4())[:8]
        replay_data["replay_id"] = replay_id

        if save_replay(replay_id, replay_data):
            return jsonify({"status": 0, "message": "success", "replay_id": replay_id})
        else:
            return jsonify({"status": -1, "message": "failed to save replay"})
    except Exception:
        logger.exception("Error in /save_replay")
        return jsonify({"status": -1, "message": "failed to save replay"})


@app.route("/replay/<replay_id>", methods=["GET"])
def get_replay_by_id(replay_id):
    """Get a replay by ID"""
    try:
        replay_data = get_replay(replay_id)
        if replay_data is None:
            return jsonify({"status": -1, "message": "replay not found"})

        return jsonify({"status": 0, "message": "success", "data": replay_data})
    except Exception:
        logger.exception("Error in /replay")
        return jsonify({"status": -1, "message": "failed to load replay"})


@app.route("/list_replays", methods=["GET"])
def list_all_replays():
    """List all available replays, optionally filtered by source"""
    try:
        source = request.args.get("source")
        replays = list_replays(limit=100, source=source)

        return jsonify({"status": 0, "message": "success", "replays": replays})
    except Exception:
        logger.exception("Error in /list_replays")
        return jsonify({"status": -1, "message": "failed to list replays"})


@app.route("/delete_replay/<replay_id>", methods=["DELETE"])
def delete_replay_by_id(replay_id):
    """Delete a replay by ID"""
    try:
        if delete_replay(replay_id):
            return jsonify({"status": 0, "message": "success"})
        else:
            return jsonify({"status": -1, "message": "failed to delete replay"})
    except Exception:
        logger.exception("Error in /delete_replay")
        return jsonify({"status": -1, "message": "failed to delete replay"})


def main():
    import argparse

    parser = argparse.ArgumentParser(description="DouZero backend")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5050, help="Port to bind to (default: 5050)")
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
