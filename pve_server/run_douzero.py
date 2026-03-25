import itertools
import json
import uuid
import os
import random

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

from utils.move_generator import MovesGener
from utils import move_detector as md, move_selector as ms
from deep import DeepAgent

EnvCard2RealCard = {3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
                    8: '8', 9: '9', 10: 'T', 11: 'J', 12: 'Q',
                    13: 'K', 14: 'A', 17: '2', 20: 'X', 30: 'D'}

RealCard2EnvCard = {'3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                    '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12,
                    'K': 13, 'A': 14, '2': 17, 'X': 20, 'D': 30}

# Card suit mapping for replay data
Card2Suit = {
    '3': ['S3', 'H3', 'D3', 'C3'],
    '4': ['S4', 'H4', 'D4', 'C4'],
    '5': ['S5', 'H5', 'D5', 'C5'],
    '6': ['S6', 'H6', 'D6', 'C6'],
    '7': ['S7', 'H7', 'D7', 'C7'],
    '8': ['S8', 'H8', 'D8', 'C8'],
    '9': ['S9', 'H9', 'D9', 'C9'],
    'T': ['ST', 'HT', 'DT', 'CT'],
    'J': ['SJ', 'HJ', 'DJ', 'CJ'],
    'Q': ['SQ', 'HQ', 'DQ', 'CQ'],
    'K': ['SK', 'HK', 'DK', 'CK'],
    'A': ['SA', 'HA', 'DA', 'CA'],
    '2': ['S2', 'H2', 'D2', 'C2'],
    'X': ['BJ'],
    'D': ['RJ'],
}

pretrained_dir = 'pretrained/douzero_pretrained'
players = []
for position in ['landlord', 'landlord_down', 'landlord_up']:
    players.append(DeepAgent(position, pretrained_dir, use_onnx=True))

# Replay storage
REPLAYS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'replays')
os.makedirs(REPLAYS_DIR, exist_ok=True)


def _init_deck():
    """Initialize a standard Dou Dizhu deck"""
    deck = []
    # 4 suits * 13 ranks (3-A, 2)
    for rank in ['3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A', '2']:
        for suit in ['S', 'H', 'D', 'C']:
            deck.append(RealCard2EnvCard[rank])
    # Jokers
    deck.append(20)  # Black Joker (X)
    deck.append(30)  # Red Joker (D)
    return deck


def _deal_cards():
    """Deal cards for a game"""
    deck = _init_deck()
    random.shuffle(deck)
    
    # Landlord gets 20 cards, peasants get 17 each
    landlord_cards = sorted(deck[:20], reverse=True)
    landlord_down_cards = sorted(deck[20:37], reverse=True)
    landlord_up_cards = sorted(deck[37:54], reverse=True)
    three_landlord_cards = sorted(deck[:3], reverse=True)  # First 3 cards are landlord cards
    
    return {
        0: landlord_cards,
        1: landlord_down_cards,
        2: landlord_up_cards,
        'three_landlord_cards': three_landlord_cards
    }


def _cards_to_suit_format(cards):
    """Convert env cards to suit format for replay"""
    result = []
    card_counts = {}
    for card in cards:
        card_char = EnvCard2RealCard[card]
        if card_char not in card_counts:
            card_counts[card_char] = 0
        result.append(Card2Suit[card_char][card_counts[card_char]])
        card_counts[card_char] += 1
    return result


def _action_to_suit_format(action, player_hand_cards):
    """Convert action to suit format"""
    if action == [] or action == 'pass':
        return 'pass'
    
    result = []
    temp_hand = player_hand_cards.copy()
    for card in action:
        card_char = EnvCard2RealCard[card]
        # Find matching card in hand
        for i, hand_card in enumerate(temp_hand):
            if EnvCard2RealCard[hand_card] == card_char:
                result.append(Card2Suit[card_char][0])
                temp_hand.pop(i)
                break
    return ' '.join(result)


def _get_legal_card_play_actions(player_hand_cards, rival_move):
    mg = MovesGener(player_hand_cards)

    rival_type = md.get_move_type(rival_move)
    rival_move_type = rival_type['type']
    rival_move_len = rival_type.get('len', 1)
    moves = list()

    if rival_move_type == md.TYPE_0_PASS:
        moves = mg.gen_moves()

    elif rival_move_type == md.TYPE_1_SINGLE:
        all_moves = mg.gen_type_1_single()
        moves = ms.filter_type_1_single(all_moves, rival_move)

    elif rival_move_type == md.TYPE_2_PAIR:
        all_moves = mg.gen_type_2_pair()
        moves = ms.filter_type_2_pair(all_moves, rival_move)

    elif rival_move_type == md.TYPE_3_TRIPLE:
        all_moves = mg.gen_type_3_triple()
        moves = ms.filter_type_3_triple(all_moves, rival_move)

    elif rival_move_type == md.TYPE_4_BOMB:
        all_moves = mg.gen_type_4_bomb() + mg.gen_type_5_king_bomb()
        moves = ms.filter_type_4_bomb(all_moves, rival_move)

    elif rival_move_type == md.TYPE_5_KING_BOMB:
        moves = []

    elif rival_move_type == md.TYPE_6_3_1:
        all_moves = mg.gen_type_6_3_1()
        moves = ms.filter_type_6_3_1(all_moves, rival_move)

    elif rival_move_type == md.TYPE_7_3_2:
        all_moves = mg.gen_type_7_3_2()
        moves = ms.filter_type_7_3_2(all_moves, rival_move)

    elif rival_move_type == md.TYPE_8_SERIAL_SINGLE:
        all_moves = mg.gen_type_8_serial_single(repeat_num=rival_move_len)
        moves = ms.filter_type_8_serial_single(all_moves, rival_move)

    elif rival_move_type == md.TYPE_9_SERIAL_PAIR:
        all_moves = mg.gen_type_9_serial_pair(repeat_num=rival_move_len)
        moves = ms.filter_type_9_serial_pair(all_moves, rival_move)

    elif rival_move_type == md.TYPE_10_SERIAL_TRIPLE:
        all_moves = mg.gen_type_10_serial_triple(repeat_num=rival_move_len)
        moves = ms.filter_type_10_serial_triple(all_moves, rival_move)

    elif rival_move_type == md.TYPE_11_SERIAL_3_1:
        all_moves = mg.gen_type_11_serial_3_1(repeat_num=rival_move_len)
        moves = ms.filter_type_11_serial_3_1(all_moves, rival_move)

    elif rival_move_type == md.TYPE_12_SERIAL_3_2:
        all_moves = mg.gen_type_12_serial_3_2(repeat_num=rival_move_len)
        moves = ms.filter_type_12_serial_3_2(all_moves, rival_move)

    elif rival_move_type == md.TYPE_13_4_2:
        all_moves = mg.gen_type_13_4_2()
        moves = ms.filter_type_13_4_2(all_moves, rival_move)

    elif rival_move_type == md.TYPE_14_4_22:
        all_moves = mg.gen_type_14_4_22()
        moves = ms.filter_type_14_4_22(all_moves, rival_move)

    if rival_move_type not in [md.TYPE_0_PASS,
                               md.TYPE_4_BOMB, md.TYPE_5_KING_BOMB]:
        moves = moves + mg.gen_type_4_bomb() + mg.gen_type_5_king_bomb()

    if len(rival_move) != 0:  # rival_move is not 'pass'
        moves = moves + [[]]

    for m in moves:
        m.sort()

    moves.sort()
    moves = list(move for move, _ in itertools.groupby(moves))

    return moves


def generate_replay_data():
    """Generate a replay by running a game with DouZero AI"""
    # Deal cards
    cards = _deal_cards()
    hands = {
        0: cards[0].copy(),
        1: cards[1].copy(),
        2: cards[2].copy()
    }
    
    # Initialize replay data structure
    replay_data = {
        'playerInfo': [
            {'id': 0, 'index': 0, 'role': 'landlord', 'agentInfo': {'name': 'DouZero-Landlord'}},
            {'id': 1, 'index': 1, 'role': 'peasant', 'agentInfo': {'name': 'DouZero-Peasant'}},
            {'id': 2, 'index': 2, 'role': 'peasant', 'agentInfo': {'name': 'DouZero-Peasant'}}
        ],
        'initHands': [
            ' '.join(_cards_to_suit_format(cards[0])),
            ' '.join(_cards_to_suit_format(cards[1])),
            ' '.join(_cards_to_suit_format(cards[2]))
        ],
        'moveHistory': []
    }
    
    # Track current hands for each player
    current_hands = {
        0: cards[0].copy(),
        1: cards[1].copy(),
        2: cards[2].copy()
    }
    
    # Game state
    current_player = 0  # Landlord starts
    last_move = []  # Last non-pass move
    last_move_player = -1
    card_play_action_seq = [[], [], []]  # Actions for each position
    played_cards = [[], [], []]
    bomb_num = 0
    
    # Play until someone wins
    max_turns = 100  # Safety limit
    turn = 0
    
    while turn < max_turns:
        # Check if current player has won
        if len(current_hands[current_player]) == 0:
            break
        
        # Build info set for current player
        info_set = InfoSet()
        info_set.player_position = current_player
        info_set.player_hand_cards = current_hands[current_player].copy()
        
        # Calculate other hands
        other_hands = []
        for i in range(3):
            if i != current_player:
                other_hands.extend(current_hands[i])
        info_set.other_hand_cards = sorted(other_hands, reverse=True)
        
        # Calculate cards left
        info_set.num_cards_left = [len(current_hands[0]), len(current_hands[1]), len(current_hands[2])]
        
        # Three landlord cards
        info_set.three_landlord_cards = cards['three_landlord_cards'].copy()
        
        # Build action sequence
        flat_seq = []
        for pos in range(3):
            for action in card_play_action_seq[pos]:
                flat_seq.append(action)
        info_set.card_play_action_seq = flat_seq
        
        # Last moves
        info_set.last_moves = [[] for _ in range(3)]
        if last_move_player >= 0 and last_move:
            info_set.last_moves[last_move_player] = last_move.copy()
        
        # Played cards
        info_set.played_cards = [p.copy() for p in played_cards]
        
        # Bomb num
        info_set.bomb_num = bomb_num
        
        # Determine rival move
        rival_move = []
        if last_move_player >= 0 and last_move_player != current_player:
            rival_move = last_move.copy()
        info_set.rival_move = rival_move
        
        # Get legal actions
        info_set.legal_actions = _get_legal_card_play_actions(
            current_hands[current_player].copy(),
            rival_move
        )
        
        # Get action from AI
        actions, confidences = players[current_player].act(info_set)
        
        # Select best action
        action = actions[0] if actions else []
        
        # Record move
        move_record = {
            'playerIdx': current_player,
            'move': _action_to_suit_format(action, current_hands[current_player].copy()),
            'info': {
                'values': {''.join([EnvCard2RealCard[a] for a in actions[i]]): float(confidences[i]) 
                          for i in range(len(actions))}
            }
        }
        replay_data['moveHistory'].append(move_record)
        
        # Update game state
        if action != []:  # Not pass
            # Remove cards from hand
            for card in action:
                if card in current_hands[current_player]:
                    current_hands[current_player].remove(card)
            
            # Update last move
            last_move = action.copy()
            last_move_player = current_player
            
            # Update played cards
            played_cards[current_player].extend(action)
            
            # Check for bomb
            move_type = md.get_move_type(action)
            if move_type['type'] == md.TYPE_4_BOMB or move_type['type'] == md.TYPE_5_KING_BOMB:
                bomb_num += 1
        
        # Record action in sequence
        card_play_action_seq[current_player].append(action)
        
        # Check win condition
        if len(current_hands[current_player]) == 0:
            break
        
        # Next player
        current_player = (current_player + 1) % 3
        turn += 1
    
    return replay_data


@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        try:
            # Player postion
            player_position = request.form.get('player_position')
            if player_position not in ['0', '1', '2']:
                return jsonify({'status': 1, 'message': 'player_position must be 0, 1, or 2'})
            player_position = int(player_position)

            # Player hand cards
            player_hand_cards = [RealCard2EnvCard[c] for c in request.form.get('player_hand_cards')]
            if player_position == 0:
                if len(player_hand_cards) < 1 or len(player_hand_cards) > 20:
                    return jsonify({'status': 2, 'message': 'the number of hand cards should be 1-20'})
            else:
                if len(player_hand_cards) < 1 or len(player_hand_cards) > 17:
                    return jsonify({'status': 3, 'message': 'the number of hand cards should be 1-17'})

            # Number cards left
            num_cards_left = [int(request.form.get('num_cards_left_landlord')), int(request.form.get('num_cards_left_landlord_down')), int(request.form.get('num_cards_left_landlord_up'))]
            if num_cards_left[player_position] != len(player_hand_cards):
                return jsonify({'status': 4, 'message': 'the number of cards left do not align with hand cards'})
            if num_cards_left[0] < 0 or num_cards_left[1] < 0 or num_cards_left[2] < 0 or num_cards_left[0] > 20 or num_cards_left[1] > 17 or num_cards_left[2] > 17:
                return jsonify({'status': 5, 'message': 'the number of cards left not in range'})

            # Three landlord cards
            three_landlord_cards = [RealCard2EnvCard[c] for c in request.form.get('three_landlord_cards')]
            if len(three_landlord_cards) < 0 or len(three_landlord_cards) > 3:
                return jsonify({'status': 6, 'message': 'the number of landlord cards should be 0-3'})

            # Card play sequence
            if request.form.get('card_play_action_seq') == '':
                card_play_action_seq = []
            else:
                card_play_action_seq = [[RealCard2EnvCard[c] for c in cards] for cards in request.form.get('card_play_action_seq').split(',')]

            # Other hand cards
            other_hand_cards = [RealCard2EnvCard[c] for c in request.form.get('other_hand_cards')]
            if len(other_hand_cards) != sum(num_cards_left) - num_cards_left[player_position]:
                return jsonify({'status': 7, 'message': 'the number of the other hand cards do not align with the number of cards left'})

            # Last moves
            last_moves = []
            for field in ['last_move_landlord', 'last_move_landlord_down', 'last_move_landlord_up']:
                last_moves.append([RealCard2EnvCard[c] for c in request.form.get(field)])

            # Played cards
            played_cards = []
            for field in ['played_cards_landlord', 'played_cards_landlord_down', 'played_cards_landlord_up']:
                played_cards.append([RealCard2EnvCard[c] for c in request.form.get(field)])

            # Bomb Num
            bomb_num = int(request.form.get('bomb_num'))

            # InfoSet
            info_set = InfoSet()
            info_set.player_position = player_position
            info_set.player_hand_cards = player_hand_cards
            info_set.num_cards_left = num_cards_left
            info_set.three_landlord_cards = three_landlord_cards
            info_set.card_play_action_seq = card_play_action_seq
            info_set.other_hand_cards = other_hand_cards
            info_set.last_moves = last_moves
            info_set.played_cards = played_cards
            info_set.bomb_num = bomb_num

            # Get rival move and legal_actions
            rival_move = []
            if len(card_play_action_seq) != 0:
                if len(card_play_action_seq[-1]) == 0:
                    rival_move = card_play_action_seq[-2]
                else:
                    rival_move = card_play_action_seq[-1]
            info_set.rival_move = rival_move
            info_set.legal_actions = _get_legal_card_play_actions(player_hand_cards, rival_move)

            # Prediction
            actions, actions_confidence = players[player_position].act(info_set)
            actions = [''.join([EnvCard2RealCard[a] for a in action]) for action in actions]
            result = {}
            win_rates = {}
            for i in range(len(actions)):
                # Here, we calculate the win rate
                win_rate = max(actions_confidence[i], -1)
                win_rate = min(win_rate, 1)
                win_rates[actions[i]] = str(round((win_rate + 1) / 2, 4))
                result[actions[i]] = str(round(actions_confidence[i], 6))

            ############## DEBUG ################
            if app.debug:
                print('--------------- DEBUG START --------------')
                command = 'curl --data "'
                parameters = []
                for key in request.form:
                    parameters.append(key+'='+request.form.get(key))
                    print(key+':', request.form.get(key))
                command += '&'.join(parameters)
                command += '" "http://127.0.0.1:5000/predict"'
                print('Command:', command)
                print('Rival Move:', rival_move)
                print('legal_actions:', info_set.legal_actions)
                print('Result:', result)
                print('--------------- DEBUG END --------------')
            ############## DEBUG ################
            return jsonify({'status': 0, 'message': 'success', 'result': result, 'win_rates': win_rates})
        except:
            import traceback
            traceback.print_exc()
            return jsonify({'status': -1, 'message': 'unkown error'})


@app.route('/legal', methods=['POST'])
def legal():
    if request.method == 'POST':
        try:
            player_hand_cards = [RealCard2EnvCard[c] for c in request.form.get('player_hand_cards')]
            rival_move = [RealCard2EnvCard[c] for c in request.form.get('rival_move')]
            legal_actions = _get_legal_card_play_actions(player_hand_cards, rival_move)
            legal_actions = ','.join([''.join([EnvCard2RealCard[a] for a in action]) for action in legal_actions])
            return jsonify({'status': 0, 'message': 'success', 'legal_action': legal_actions})
        except:
            import traceback
            traceback.print_exc()
            return jsonify({'status': -1, 'message': 'unkown error'})


@app.route('/generate_replay', methods=['GET'])
def generate_replay():
    """Generate a new replay by running a game with DouZero AI"""
    try:
        replay_data = generate_replay_data()
        replay_id = str(uuid.uuid4())[:8]
        replay_data['replay_id'] = replay_id
        
        # Save to file
        replay_path = os.path.join(REPLAYS_DIR, f'{replay_id}.json')
        with open(replay_path, 'w') as f:
            json.dump(replay_data, f)
        
        return jsonify({
            'status': 0,
            'message': 'success',
            'replay_id': replay_id,
            'data': replay_data
        })
    except:
        import traceback
        traceback.print_exc()
        return jsonify({'status': -1, 'message': 'failed to generate replay'})


@app.route('/replay/<replay_id>', methods=['GET'])
def get_replay(replay_id):
    """Get a replay by ID"""
    try:
        replay_path = os.path.join(REPLAYS_DIR, f'{replay_id}.json')
        if not os.path.exists(replay_path):
            return jsonify({'status': -1, 'message': 'replay not found'})
        
        with open(replay_path, 'r') as f:
            replay_data = json.load(f)
        
        return jsonify({
            'status': 0,
            'message': 'success',
            'data': replay_data
        })
    except:
        import traceback
        traceback.print_exc()
        return jsonify({'status': -1, 'message': 'failed to load replay'})


@app.route('/list_replays', methods=['GET'])
def list_replays():
    """List all available replays"""
    try:
        replays = []
        for filename in os.listdir(REPLAYS_DIR):
            if filename.endswith('.json'):
                replay_id = filename[:-5]
                replay_path = os.path.join(REPLAYS_DIR, filename)
                with open(replay_path, 'r') as f:
                    data = json.load(f)
                    replays.append({
                        'replay_id': replay_id,
                        'created': os.path.getctime(replay_path)
                    })
        
        # Sort by creation time (newest first)
        replays.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'status': 0,
            'message': 'success',
            'replays': replays
        })
    except:
        import traceback
        traceback.print_exc()
        return jsonify({'status': -1, 'message': 'failed to list replays'})


class InfoSet(object):

    def __init__(self):
        self.player_position = None
        self.player_hand_cards = None
        self.num_cards_left = None
        self.three_landlord_cards = None
        self.card_play_action_seq = None
        self.other_hand_cards = None
        self.legal_actions = None
        self.rival_move = None
        self.last_moves = None
        self.played_cards = None
        self.bomb_num = None


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='DouZero backend')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    app.run(debug=args.debug)
