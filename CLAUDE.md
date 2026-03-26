# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mini DDZ is a Dou Dizhu (Chinese Poker) PvE demo with a full-stack architecture:
- **Frontend**: React 16.x + Material-UI + i18next (supports EN/ZH)
- **Backend**: Flask + Flask-CORS
- **AI Engine**: PyTorch + ONNX Runtime (DouZero reinforcement learning model)

## Common Commands

### Frontend (React)
```bash
npm install        # Install frontend dependencies
npm start          # Start dev server (port 3000)
npm run build      # Production build
npm test           # Run React tests
```

### Backend (Python)
```bash
uv sync                                 # Install Python dependencies
uv run python pve_server/run_douzero.py # Start Flask server (port 5050)
uv run pytest                           # Run tests
uv run pytest --cov                     # Run tests with coverage
uv run ruff check --fix                 # Lint and auto-fix
uv run ruff format                      # Format code
uv run mypy pve_server/                 # Type checking
```

## Architecture

```
mini-ddz/
├── src/                    # React Frontend
│   ├── App.js              # Route definitions
│   ├── components/         # Reusable UI components
│   ├── view/               # Page-level views (PvE, Replay, AI Battle)
│   ├── utils/config.js     # API URL configuration
│   └── locales/            # i18n translations (en/zh)
│
├── pve_server/             # Flask Backend
│   ├── run_douzero.py      # Main server + API endpoints
│   ├── deep.py             # DeepAgent - AI model wrapper
│   ├── models.py           # PyTorch LSTM model definitions
│   ├── replay_db.py        # SQLite replay storage
│   └── utils/              # Move generation/detection/selection
│
├── tests/                  # Python test suite
└── docs/                   # Documentation
```

### Key Frontend Views
- `/pve/doudizhu-demo` - Player vs AI game
- `/replay/doudizhu` - Game replay viewer
- `/replays` - List of saved replays
- `/ai-battle` - 3 AI auto-battle demo

### Backend API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/predict` | POST | Get AI prediction for game state |
| `/legal` | POST | Get legal moves given hand and opponent action |
| `/generate_ai_battle` | GET | Generate AI vs AI game |
| `/replay/<id>` | GET | Get replay by ID |
| `/list_replays` | GET | List all replays |
| `/save_replay` | POST | Save game replay |
| `/delete_replay/<id>` | DELETE | Delete replay |

### AI Model Files
- Landlord: `pve_server/pretrained/douzero_pretrained/landlord.ckpt`
- Landlord up: `pve_server/pretrained/douzero_pretrained/landlord_up.ckpt`
- Landlord down: `pve_server/pretrained/douzero_pretrained/landlord_down.ckpt`

## Card Encoding

**Internal (AI)**: 3-9, T(10), J, Q, K, A, 2, X(small joker), D(big joker)

**Display (Frontend)**: S(spade), H(heart), D(diamond), C(club) + number, BJ(black joker), RJ(red joker)

## Development Notes

- Backend runs on port 5050, frontend on port 3000
- CORS is enabled for local development
- Player positions: 0=landlord, 1=landlord_down, 2=landlord_up
- Pre-commit hooks run ruff and mypy
