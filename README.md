# Mini DDZ

This is a GUI visualization tool for the [DouZero](https://github.com/kwai/DouZero) project. RLCard-Showdown provides a PvE (Player vs Environment) module where you can play against the DouZero AI interactively, and a replay module where you can watch AI vs AI games. The frontend is developed with [React](https://reactjs.org/). The backend is based on [Flask](https://flask.palletsprojects.com/).

*   DouZero Project: [https://github.com/kwai/DouZero](https://github.com/kwai/DouZero)
*   Online Demo: [https://www.douzero.org/](https://www.douzero.org/)

## Installation

RLCard-Showdown has separated frontend and backend.

### Prerequisite

To set up the frontend, you should make sure you have [Node.js](https://nodejs.org/) and NPM installed. Normally you just need to manually install Node.js, and the NPM package would be automatically installed together with Node.js for you. Please refer to its official website for installation of Node.js.

You can run the following commands to verify the installation:
```
node -v
npm -v
```

For backend, make sure that you have **Python 3.9+** installed. The project uses [uv](https://github.com/astral-sh/uv) for Python package management.

### Install Frontend and Backend

1. Clone the repository:
```
git clone https://github.com/datamllab/rlcard-showdown.git
cd rlcard-showdown
```

2. Install frontend dependencies:
```
npm install
```

3. Install Python dependencies using uv:
```
uv sync
```

Or if you prefer using pip:
```
pip install -e .
```

### Run RLCard-Showdown

1. Start the PvE server (Flask backend) with DouZero models:
```
cd pve_server
python run_douzero.py
```

The PvE backend will run at [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

2. In a new terminal, start the frontend:
```
npm start
```

You can access the application at [http://127.0.0.1:3000/](http://127.0.0.1:3000/).

**Available Pages:**
- PvE Demo (Human vs AI): [http://127.0.0.1:3000/](http://127.0.0.1:3000/) or [http://127.0.0.1:3000/pve/doudizhu-demo](http://127.0.0.1:3000/pve/doudizhu-demo)
- AI Replay: [http://127.0.0.1:3000/replay/doudizhu](http://127.0.0.1:3000/replay/doudizhu)

## Features

### 1. PvE Mode (Human vs AI)
Play Dou Dizhu against the DouZero AI:
- Choose your role: Landlord, Landlord Up, or Landlord Down
- Real-time AI predictions with win rate estimation
- Adjustable game speed
- Game statistics tracking
- Support for both English and Chinese

### 2. Replay Mode
Watch AI vs AI games:
- Auto-generated replays from DouZero AI matches
- Step-by-step playback with speed control
- View AI's predicted moves and expected win rates
- Pause, resume, and navigate through game history

## Project Structure

```
rlcard-showdown/
├── src/                    # React frontend source code
│   ├── components/         # React components
│   ├── view/              # Page views (PvE, Replay)
│   ├── utils/             # Utility functions and config
│   └── locales/           # i18n translations (en, zh)
├── pve_server/            # Flask backend for PvE
│   ├── run_douzero.py     # Main Flask server
│   ├── deep.py            # Deep learning model wrapper
│   ├── models.py          # Model definitions
│   ├── utils/             # Game logic utilities
│   └── pretrained/        # Pre-trained DouZero models
├── docs/                  # Documentation
├── public/                # Static assets
├── package.json           # NPM dependencies
└── pyproject.toml         # Python project configuration
```

## API Endpoints

The Flask backend provides the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | Get AI prediction for current game state |
| `/legal` | POST | Get legal moves for given hand cards and rival move |
| `/generate_replay` | GET | Generate a new AI vs AI replay |
| `/replay/<replay_id>` | GET | Get replay data by ID |
| `/list_replays` | GET | List all available replays |

## Demos

![doudizhu-pve](docs/imgs/doudizhu-replay.png)

## Cite DouZero

If you use this project in your research, please cite the DouZero paper:

```bibtex
@article{zha2021douzero,
  title={DouZero: Mastering DouDizhu with Self-Play Deep Reinforcement Learning},
  author={Zha, Daochen and Xie, Jingru and Ma, Wenye and Zhang, Sheng and Lian, Xiangru and Hu, Xia and Liu, Ji},
  journal={arXiv preprint arXiv:2103.00239},
  year={2021}
}
```

## Contact Us

If you have any questions or feedback, feel free to open an issue on GitHub.

## Acknowledgements

We would like to thank JJ World Network Technology Co., LTD for the generous support, [Chieh-An Tsai](https://anntsai.myportfolio.com/) for user interface design, and [Lei Pan](https://github.com/lpan18) for the help in visualizations.
