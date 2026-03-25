# User Guide

## PvE Mode (Human vs AI)

### Starting a Game
1. Open the application at [http://127.0.0.1:3000/](http://127.0.0.1:3000/)
2. Select your preferred language (English or Chinese) if prompted
3. Choose your role:
   - **Landlord**: Plays first with 20 cards
   - **Landlord Up**: Peasant position, plays after landlord
   - **Landlord Down**: Peasant position, plays before landlord
4. Click "Start Game" to begin

### Playing the Game
- **Your Turn**: Select cards from your hand by clicking on them
- **Play**: Click the "Play" button to play selected cards
- **Pass**: Click "Pass" if you cannot or choose not to play
- **Hint**: Click "Hint" to see suggested moves
- **Deselect**: Click "Deselect" to clear your selection

### Game Settings
- **Game Speed**: Adjust the AI thinking time (0s to 30s)
- **Show/Hide AI Cards**: Toggle to reveal/hide opponent cards and AI predictions

### Statistics
Your game statistics are automatically saved to browser local storage:
- Win rate by role (Landlord, Landlord Up, Landlord Down)
- Total games played and won
- Click "Reset" in the game end dialog to clear statistics

## Replay Mode

### Watching a Replay
1. Navigate to [http://127.0.0.1:3000/replay/doudizhu](http://127.0.0.1:3000/replay/doudizhu)
2. Click "Start" to generate and watch a new AI vs AI replay

### Replay Controls
- **Play/Pause**: Control the replay playback
- **Restart**: Start a new replay
- **Previous/Next**: Navigate between moves when paused
- **Speed**: Adjust playback speed (0.125x to 8x)

### Understanding the Display
- **Left Panel**: Game board showing all players' cards and actions
- **Right Panel**: AI predictions showing:
  - Current player's role
  - Top 3 predicted moves with expected win rates
  - Three landlord cards

## Troubleshooting

### Cannot connect to backend
- Make sure the Flask server is running on port 5000
- Check that `pve_server/run_douzero.py` is started
- Verify the backend URL in `src/utils/config.js`

### Models not found
- Pre-trained models should be in `pve_server/pretrained/douzero_pretrained/`
- The repository includes the necessary model files

### Frontend not loading
- Ensure Node.js dependencies are installed (`npm install`)
- Check that no other service is using port 3000
