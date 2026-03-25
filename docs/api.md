# API Documentation

## Backend Configuration

The default configuration for the backend server is defined in `/src/utils/config.js`:

```javascript
const apiUrl = 'http://127.0.0.1:8000';
const douzeroDemoUrl = 'http://127.0.0.1:5000';
```

Currently, only the `douzeroDemoUrl` (port 5000) is used for the PvE Flask server.

## REST API of Backend

The Flask backend provides the following endpoints for the Dou Dizhu PvE and replay functionality.

### POST /predict

Get AI prediction for the current game state.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `player_position` | int | Player position (0=landlord, 1=landlord_down, 2=landlord_up) |
| `player_hand_cards` | string | Current hand cards (e.g., "3456789TJQKA2X") |
| `num_cards_left_landlord` | int | Number of cards left for landlord |
| `num_cards_left_landlord_down` | int | Number of cards left for landlord_down |
| `num_cards_left_landlord_up` | int | Number of cards left for landlord_up |
| `three_landlord_cards` | string | Three landlord cards |
| `card_play_action_seq` | string | Card play action sequence, comma-separated |
| `other_hand_cards` | string | Other players' hand cards combined |
| `last_move_landlord` | string | Last move by landlord |
| `last_move_landlord_down` | string | Last move by landlord_down |
| `last_move_landlord_up` | string | Last move by landlord_up |
| `bomb_num` | int | Number of bombs played so far |
| `played_cards_landlord` | string | Cards played by landlord so far |
| `played_cards_landlord_down` | string | Cards played by landlord_down so far |
| `played_cards_landlord_up` | string | Cards played by landlord_up so far |

**Response:**
```json
{
  "status": 0,
  "message": "success",
  "result": {
    "345": "-0.123456",
    "pass": "-0.789012"
  },
  "win_rates": {
    "345": "0.4383",
    "pass": "0.1055"
  }
}
```

### POST /legal

Get legal moves for given hand cards and rival move.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `player_hand_cards` | string | Current hand cards |
| `rival_move` | string | The move to beat (empty string if first move) |

**Response:**
```json
{
  "status": 0,
  "message": "success",
  "legal_action": "345,3,4,5,pass"
}
```

### GET /generate_replay

Generate a new AI vs AI replay.

**Response:**
```json
{
  "status": 0,
  "message": "success",
  "replay_id": "a1b2c3d4",
  "data": {
    "replay_id": "a1b2c3d4",
    "playerInfo": [
      {"id": 0, "index": 0, "role": "landlord", "agentInfo": {"name": "DouZero-Landlord"}},
      {"id": 1, "index": 1, "role": "peasant", "agentInfo": {"name": "DouZero-Peasant"}},
      {"id": 2, "index": 2, "role": "peasant", "agentInfo": {"name": "DouZero-Peasant"}}
    ],
    "initHands": ["S3 H3 D3 C3 ...", "S4 H4 D4 C4 ...", "S5 H5 D5 C5 ..."],
    "moveHistory": [
      {
        "playerIdx": 0,
        "move": "S3 H3 D3",
        "info": {
          "values": {
            "333": 0.85,
            "33": 0.72,
            "3": 0.65
          }
        }
      }
    ]
  }
}
```

### GET /replay/<replay_id>

Get a replay by its ID.

**Response:**
```json
{
  "status": 0,
  "message": "success",
  "data": {
    "replay_id": "a1b2c3d4",
    "playerInfo": [...],
    "initHands": [...],
    "moveHistory": [...]
  }
}
```

### GET /list_replays

List all available replays.

**Response:**
```json
{
  "status": 0,
  "message": "success",
  "replays": [
    {"replay_id": "a1b2c3d4", "created": 1234567890},
    {"replay_id": "e5f6g7h8", "created": 1234567880}
  ]
}
```

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 0 | Success |
| -1 | Unknown error |
| 1 | Invalid player_position (must be 0, 1, or 2) |
| 2 | Invalid number of hand cards for landlord (should be 1-20) |
| 3 | Invalid number of hand cards for peasant (should be 1-17) |
| 4 | Number of cards left does not align with hand cards |
| 5 | Number of cards left not in valid range |
| 6 | Invalid number of landlord cards (should be 0-3) |
| 7 | Number of other hand cards does not align |

## Card Encoding

Cards are encoded using single characters:

| Card | Encoding |
|------|----------|
| 3-10 | 3, 4, 5, 6, 7, 8, 9, T |
| Jack | J |
| Queen | Q |
| King | K |
| Ace | A |
| 2 | 2 |
| Black Joker | X |
| Red Joker | D |

Suit format for display: `S3` (Spade 3), `H3` (Heart 3), `D3` (Diamond 3), `C3` (Club 3), `BJ` (Black Joker), `RJ` (Red Joker).
