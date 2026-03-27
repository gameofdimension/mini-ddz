import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import Divider from '@material-ui/core/Divider';
import LinearProgress from '@material-ui/core/LinearProgress';
import Paper from '@material-ui/core/Paper';
import Slider from '@material-ui/core/Slider';
import NotInterestedIcon from '@material-ui/icons/NotInterested';
import PauseCircleOutlineRoundedIcon from '@material-ui/icons/PauseCircleOutlineRounded';
import PlayArrowRoundedIcon from '@material-ui/icons/PlayArrowRounded';
import ReplayRoundedIcon from '@material-ui/icons/ReplayRounded';
import SkipNextIcon from '@material-ui/icons/SkipNext';
import SkipPreviousIcon from '@material-ui/icons/SkipPrevious';
import { Layout, Loading, Message } from 'element-react';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import '../../assets/gameview.scss';
import { DoudizhuGameBoard } from '../../components/GameBoard';
import {
    card2SuiteAndRank,
    computeHandCardsWidth,
    deepCopy,
    doubleRaf,
    removeCards,
    translateCardData,
} from '../../utils';

const mainViewerId = 0;
const initConsiderationTime = 2000;
const considerationTimeDeduction = 200;

const createInitGameState = () => ({
    gameStatus: 'ready', // "ready", "playing", "paused", "over"
    playerInfo: [],
    hands: [],
    latestAction: [[], [], []],
    mainViewerId: mainViewerId,
    turn: 0,
    toggleFade: '',
    currentPlayer: null,
    considerationTime: initConsiderationTime,
    completedPercent: 0,
});

const cardStr2Arr = (cardStr) => {
    return cardStr === 'pass' || cardStr === '' ? 'pass' : cardStr.split(' ');
};

const gameSpeedMarks = [
    { value: -3, label: 'x0.125' },
    { value: -2, label: 'x0.25' },
    { value: -1, label: 'x0.5' },
    { value: 0, label: 'x1' },
    { value: 1, label: 'x2' },
    { value: 2, label: 'x4' },
    { value: 3, label: 'x8' },
];

function GamePlaybackView({
    fetchData,
    validate = null,
    autoStart = false,
    gameBoardProps = {},
    startLabel = 'Start',
    errorMessage = 'Error loading game data',
}) {
    const [gameInfo, setGameInfo] = useState(createInitGameState());
    const [gameSpeed, setGameSpeed] = useState(0);
    const [gameEndDialog, setGameEndDialog] = useState(false);
    const [gameEndDialogText, setGameEndDialogText] = useState('');
    const [fullScreenLoading, setFullScreenLoading] = useState(false);

    const gameStateTimeoutRef = useRef(null);
    const moveHistoryRef = useRef([]);
    const gameStateHistoryRef = useRef([]);

    // --- Data loading ---

    const loadGameData = useCallback(() => {
        moveHistoryRef.current = [];
        gameStateHistoryRef.current = [];
        if (gameStateTimeoutRef.current) {
            window.clearTimeout(gameStateTimeoutRef.current);
            gameStateTimeoutRef.current = null;
        }

        setFullScreenLoading(true);
        setGameSpeed(0);

        fetchData()
            .then((battleData) => {
                if (validate) {
                    const validation = validate(battleData);
                    if (!validation.valid) {
                        setFullScreenLoading(false);
                        Message({
                            message: validation.error,
                            type: 'error',
                            showClose: true,
                            duration: 5000,
                        });
                        return;
                    }
                }

                // Pre-process move history
                const moveHistory = battleData.moveHistory;
                for (const historyItem of moveHistory) {
                    if (historyItem.info && !Array.isArray(historyItem.info)) {
                        if ('probs' in historyItem.info) {
                            historyItem.info.probs = Object.entries(historyItem.info.probs).sort(
                                (a, b) => Number(b[1]) - Number(a[1]),
                            );
                        } else if ('values' in historyItem.info) {
                            historyItem.info.values = Object.entries(historyItem.info.values).sort(
                                (a, b) => Number(b[1]) - Number(a[1]),
                            );
                        }
                    }
                }
                moveHistoryRef.current = moveHistory;

                let newGameInfo = createInitGameState();
                newGameInfo.gameStatus = 'playing';
                newGameInfo.playerInfo = battleData.playerInfo;
                newGameInfo.hands = battleData.initHands.map((element) => cardStr2Arr(element));
                newGameInfo.currentPlayer = battleData.playerInfo.find((element) => {
                    return element.role === 'landlord';
                }).index;
                gameStateHistoryRef.current.push(newGameInfo);

                setGameInfo(newGameInfo);
                setFullScreenLoading(false);
            })
            .catch(() => {
                setFullScreenLoading(false);
                Message({
                    message: errorMessage,
                    type: 'error',
                    showClose: true,
                });
            });
    }, [fetchData, validate, errorMessage]);

    // Start timer after data is loaded
    useEffect(() => {
        if (gameInfo.gameStatus === 'playing' && moveHistoryRef.current.length > 0 && gameInfo.playerInfo.length > 0) {
            if (gameStateTimeoutRef.current) {
                window.clearTimeout(gameStateTimeoutRef.current);
                gameStateTimeoutRef.current = null;
            }
            gameStateTimer();
        }
    }, [gameInfo.playerInfo.length]);

    // Auto-start on mount
    useEffect(() => {
        if (autoStart) {
            loadGameData();
        }
    }, [autoStart, loadGameData]);

    // --- Game state generation ---

    const generateNewState = useCallback(() => {
        let newGameInfo = deepCopy(gameInfo);
        if (gameInfo.turn === moveHistoryRef.current.length) return newGameInfo;
        if (gameInfo.turn + 1 < gameStateHistoryRef.current.length) {
            newGameInfo = deepCopy(gameStateHistoryRef.current[gameInfo.turn + 1]);
        } else {
            let newMove = moveHistoryRef.current[gameInfo.turn];
            if (newMove.playerIdx === gameInfo.currentPlayer) {
                newGameInfo.latestAction[newMove.playerIdx] = cardStr2Arr(
                    Array.isArray(newMove.move) ? newMove.move.join(' ') : newMove.move,
                );
                newGameInfo.turn++;
                newGameInfo.currentPlayer = (newGameInfo.currentPlayer + 1) % 3;
                const remainedCards = removeCards(
                    newGameInfo.latestAction[newMove.playerIdx],
                    newGameInfo.hands[newMove.playerIdx],
                );
                if (remainedCards !== false) {
                    newGameInfo.hands[newMove.playerIdx] = remainedCards;
                } else {
                    Message({
                        message: "Cannot find cards in move from player's hand",
                        type: 'error',
                        showClose: true,
                    });
                }
                if (remainedCards.length === 0) {
                    doubleRaf(() => {
                        const winner = gameInfo.playerInfo.find((element) => {
                            return element.index === newMove.playerIdx;
                        });
                        if (winner) {
                            newGameInfo.gameStatus = 'over';
                            setGameInfo({ ...newGameInfo });
                            if (winner.role === 'landlord')
                                setTimeout(() => {
                                    setGameEndDialog(true);
                                    setGameEndDialogText('Landlord Wins');
                                }, 200);
                            else
                                setTimeout(() => {
                                    setGameEndDialog(true);
                                    setGameEndDialogText('Peasants Win');
                                }, 200);
                        } else {
                            Message({
                                message: 'Error in finding winner',
                                type: 'error',
                                showClose: true,
                            });
                        }
                    });
                    return newGameInfo;
                }
                newGameInfo.considerationTime = initConsiderationTime;
                newGameInfo.completedPercent += 100.0 / (moveHistoryRef.current.length - 1);
            } else {
                Message({
                    message: 'Mismatched current player index',
                    type: 'error',
                    showClose: true,
                });
            }
            if (newGameInfo.turn === gameStateHistoryRef.current.length) {
                gameStateHistoryRef.current.push(newGameInfo);
            } else {
                Message({
                    message: 'inconsistent game state history length and turn number',
                    type: 'error',
                    showClose: true,
                });
            }
        }
        return newGameInfo;
    }, [gameInfo]);

    // --- Timer ---

    const gameStateTimer = useCallback(() => {
        gameStateTimeoutRef.current = setTimeout(() => {
            setGameInfo((prev) => {
                let currentConsiderationTime = prev.considerationTime;
                if (currentConsiderationTime > 0) {
                    currentConsiderationTime -= considerationTimeDeduction * Math.pow(2, gameSpeed);
                    currentConsiderationTime = currentConsiderationTime < 0 ? 0 : currentConsiderationTime;
                    if (currentConsiderationTime === 0 && gameSpeed < 2) {
                        return { ...prev, considerationTime: currentConsiderationTime, toggleFade: 'fade-out' };
                    }
                    return { ...prev, considerationTime: currentConsiderationTime };
                }
                return prev;
            });

            // We use a separate effect to react to considerationTime reaching 0
        }, considerationTimeDeduction);
    }, [gameSpeed]);

    // Trigger new state when considerationTime reaches 0
    useEffect(() => {
        if (gameInfo.considerationTime === 0 && gameInfo.gameStatus === 'playing' && moveHistoryRef.current.length > 0) {
            const newGameInfo = generateNewState();
            if (newGameInfo.gameStatus === 'over') return;
            newGameInfo.gameStatus = 'playing';
            if (gameInfo.toggleFade === 'fade-out') {
                newGameInfo.toggleFade = 'fade-in';
            }
            setGameInfo(newGameInfo);
        }
    }, [gameInfo.considerationTime, gameInfo.gameStatus, gameInfo.toggleFade, generateNewState]);

    // Clear toggleFade after animation
    useEffect(() => {
        if (gameInfo.toggleFade !== '' && gameInfo.gameStatus === 'playing') {
            const timer = setTimeout(() => {
                setGameInfo((prev) => ({ ...prev, toggleFade: '' }));
            }, 200);
            return () => clearTimeout(timer);
        }
    }, [gameInfo.toggleFade, gameInfo.gameStatus]);

    // --- Playback controls ---

    const runNewTurn = useCallback(() => {
        gameStateTimer();
    }, [gameStateTimer]);

    const pausePlayback = useCallback(() => {
        if (gameStateTimeoutRef.current) {
            window.clearTimeout(gameStateTimeoutRef.current);
            gameStateTimeoutRef.current = null;
        }
        setGameInfo((prev) => ({ ...prev, gameStatus: 'paused' }));
    }, []);

    const resumePlayback = useCallback(() => {
        gameStateTimer();
        setGameInfo((prev) => ({ ...prev, gameStatus: 'playing' }));
    }, [gameStateTimer]);

    const go2PrevGameState = useCallback(() => {
        if (gameInfo.turn <= 0) return;
        const prevGameInfo = deepCopy(gameStateHistoryRef.current[gameInfo.turn - 1]);
        prevGameInfo.gameStatus = 'paused';
        prevGameInfo.toggleFade = '';
        setGameInfo(prevGameInfo);
    }, [gameInfo.turn]);

    const go2NextGameState = useCallback(() => {
        if (gameInfo.turn >= moveHistoryRef.current.length) return;
        const newGameInfo = generateNewState();
        if (newGameInfo.gameStatus === 'over') return;
        newGameInfo.gameStatus = 'paused';
        newGameInfo.toggleFade = '';
        setGameInfo(newGameInfo);
    }, [gameInfo.turn, generateNewState]);

    const handleCloseGameEndDialog = useCallback(() => {
        setGameEndDialog(false);
        setGameEndDialogText('');
    }, []);

    // --- Render helpers ---

    const gameStatusButton = (status) => {
        switch (status) {
            case 'ready':
                return (
                    <Button
                        className={'status-button'}
                        variant={'contained'}
                        startIcon={<PlayArrowRoundedIcon />}
                        color="primary"
                        onClick={() => loadGameData()}
                    >
                        {startLabel}
                    </Button>
                );
            case 'playing':
                return (
                    <Button
                        className={'status-button'}
                        variant={'contained'}
                        startIcon={<PauseCircleOutlineRoundedIcon />}
                        color="secondary"
                        onClick={() => pausePlayback()}
                    >
                        Pause
                    </Button>
                );
            case 'paused':
                return (
                    <Button
                        className={'status-button'}
                        variant={'contained'}
                        startIcon={<PlayArrowRoundedIcon />}
                        color="primary"
                        onClick={() => resumePlayback()}
                    >
                        Resume
                    </Button>
                );
            case 'over':
                return (
                    <Button
                        className={'status-button'}
                        variant={'contained'}
                        startIcon={<ReplayRoundedIcon />}
                        color="primary"
                        onClick={() => loadGameData()}
                    >
                        {startLabel}
                    </Button>
                );
            default:
                alert(`undefined game status: ${status}`);
        }
    };

    const computePredictionCards = (cards, hands) => {
        let computedCards = [];
        if (cards.length > 0) {
            hands.forEach((card) => {
                let { rank } = card2SuiteAndRank(card);
                if (rank === 'X') rank = 'B';
                else if (rank === 'D') rank = 'R';
                const idx = cards.indexOf(rank);
                if (idx >= 0) {
                    cards.splice(idx, 1);
                    computedCards.push(card);
                }
            });
        } else {
            computedCards = 'pass';
        }

        if (computedCards === 'pass') {
            return (
                <div className={'non-card ' + gameInfo.toggleFade}>
                    <span>{'PASS'}</span>
                </div>
            );
        } else {
            return (
                <div className={'unselectable playingCards loose ' + gameInfo.toggleFade}>
                    <ul className="hand" style={{ width: computeHandCardsWidth(computedCards.length, 10) }}>
                        {computedCards.map((card) => {
                            const [rankClass, suitClass, rankText, suitText] = translateCardData(card);
                            return (
                                <li key={`handCard-${card}`}>
                                    <label className={`card ${rankClass} ${suitClass}`} href="/#">
                                        <span className="rank">{rankText}</span>
                                        <span className="suit">{suitText}</span>
                                    </label>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            );
        }
    };

    const computeProbabilityItem = (idx) => {
        if (gameInfo.gameStatus !== 'ready' && gameInfo.turn < moveHistoryRef.current.length) {
            let currentMove = null;
            if (gameInfo.turn !== moveHistoryRef.current.length) {
                currentMove = moveHistoryRef.current[gameInfo.turn];
            }

            let style = {};
            let probabilities = null;
            let probabilityItemType = null;

            if (currentMove) {
                if (Array.isArray(currentMove.info)) {
                    probabilityItemType = 'Rule';
                } else {
                    if ('probs' in currentMove.info) {
                        probabilityItemType = 'Probability';
                        probabilities = idx < currentMove.info.probs.length ? currentMove.info.probs[idx] : null;
                    } else if ('values' in currentMove.info) {
                        probabilityItemType = 'Expected payoff';
                        probabilities = idx < currentMove.info.values.length ? currentMove.info.values[idx] : null;
                    } else {
                        probabilityItemType = 'Rule';
                    }
                }
            }

            style['backgroundColor'] = currentMove !== null ? '#fff' : '#bdbdbd';

            return (
                <div className={'playing'} style={style}>
                    <div className="probability-move">
                        {probabilities ? (
                            computePredictionCards(
                                probabilities[0] === 'pass' ? [] : probabilities[0].split(''),
                                gameInfo.hands[currentMove.playerIdx],
                            )
                        ) : (
                            <NotInterestedIcon fontSize="large" />
                        )}
                    </div>
                    {probabilities ? (
                        <div className={'non-card ' + gameInfo.toggleFade}>
                            <span>
                                {probabilityItemType === 'Rule'
                                    ? 'Rule Based'
                                    : probabilityItemType === 'Probability'
                                    ? `Probability ${(probabilities[1] * 100).toFixed(2)}%`
                                    : `Expected payoff: ${probabilities[1].toFixed(4)}`}
                            </span>
                        </div>
                    ) : (
                        ''
                    )}
                </div>
            );
        } else {
            return <span className={'waiting'}>Waiting...</span>;
        }
    };

    const sliderValueText = (value) => value;

    return (
        <div>
            <Dialog
                open={gameEndDialog}
                onClose={handleCloseGameEndDialog}
                aria-labelledby="alert-dialog-title"
                aria-describedby="alert-dialog-description"
            >
                <DialogTitle id="alert-dialog-title" style={{ width: '200px' }}>
                    {'Game Ends!'}
                </DialogTitle>
                <DialogContent>
                    <DialogContentText id="alert-dialog-description">
                        {gameEndDialogText}
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseGameEndDialog} color="primary" autoFocus>
                        OK
                    </Button>
                </DialogActions>
            </Dialog>
            <div className={'doudizhu-view-container'}>
                <Layout.Row style={{ height: '540px' }}>
                    <Layout.Col style={{ height: '100%' }} span="17">
                        <div style={{ height: '100%' }}>
                            <Paper className={'doudizhu-gameboard-paper'} elevation={3}>
                                <DoudizhuGameBoard
                                    playerInfo={gameInfo.playerInfo}
                                    hands={gameInfo.hands}
                                    latestAction={gameInfo.latestAction}
                                    mainPlayerId={gameInfo.mainViewerId}
                                    currentPlayer={gameInfo.currentPlayer}
                                    considerationTime={gameInfo.considerationTime}
                                    turn={gameInfo.turn}
                                    runNewTurn={runNewTurn}
                                    toggleFade={gameInfo.toggleFade}
                                    gameStatus={gameInfo.gameStatus}
                                    {...gameBoardProps}
                                />
                            </Paper>
                        </div>
                    </Layout.Col>
                    <Layout.Col span="7" style={{ height: '100%' }}>
                        <Paper className={'doudizhu-probability-paper'} elevation={3}>
                            <div className={'probability-player'}>
                                {gameInfo.playerInfo.length > 0 ? (
                                    <span>
                                        Current Player: {gameInfo.currentPlayer}
                                        <br />
                                        Role: {gameInfo.playerInfo[gameInfo.currentPlayer].role}
                                    </span>
                                ) : (
                                    <span>Waiting...</span>
                                )}
                            </div>
                            <Divider />
                            <div className={'probability-table'}>
                                <div className={'probability-item'}>{computeProbabilityItem(0)}</div>
                                <div className={'probability-item'}>{computeProbabilityItem(1)}</div>
                                <div className={'probability-item'}>{computeProbabilityItem(2)}</div>
                            </div>
                        </Paper>
                    </Layout.Col>
                </Layout.Row>
                <div className="progress-bar">
                    <LinearProgress variant="determinate" value={gameInfo.completedPercent} />
                </div>
                <Loading loading={fullScreenLoading}>
                    <div className="game-controller">
                        <Paper className={'game-controller-paper'} elevation={3}>
                            <Layout.Row style={{ height: '51px' }}>
                                <Layout.Col span="7" style={{ height: '51px', lineHeight: '48px' }}>
                                    <div>
                                        <Button
                                            variant="contained"
                                            color="primary"
                                            disabled={gameInfo.gameStatus !== 'paused' || gameInfo.turn === 0}
                                            onClick={go2PrevGameState}
                                        >
                                            <SkipPreviousIcon />
                                        </Button>
                                        {gameStatusButton(gameInfo.gameStatus)}
                                        <Button
                                            variant="contained"
                                            color="primary"
                                            disabled={gameInfo.gameStatus !== 'paused'}
                                            onClick={go2NextGameState}
                                        >
                                            <SkipNextIcon />
                                        </Button>
                                    </div>
                                </Layout.Col>
                                <Layout.Col span="1" style={{ height: '100%', width: '1px' }}>
                                    <Divider orientation="vertical" />
                                </Layout.Col>
                                <Layout.Col
                                    span="3"
                                    style={{
                                        height: '51px',
                                        lineHeight: '51px',
                                        marginLeft: '-1px',
                                        marginRight: '-1px',
                                    }}
                                >
                                    <div style={{ textAlign: 'center' }}>{`Turn ${gameInfo.turn}`}</div>
                                </Layout.Col>
                                <Layout.Col span="1" style={{ height: '100%', width: '1px' }}>
                                    <Divider orientation="vertical" />
                                </Layout.Col>
                                <Layout.Col span="14">
                                    <div>
                                        <label className={'form-label-left'}>Game Speed</label>
                                        <div style={{ marginLeft: '100px', marginRight: '10px' }}>
                                            <Slider
                                                value={gameSpeed}
                                                getAriaValueText={sliderValueText}
                                                onChange={(e, newVal) => setGameSpeed(newVal)}
                                                aria-labelledby="discrete-slider-custom"
                                                step={1}
                                                min={-3}
                                                max={3}
                                                track={false}
                                                valueLabelDisplay="off"
                                                marks={gameSpeedMarks}
                                            />
                                        </div>
                                    </div>
                                </Layout.Col>
                            </Layout.Row>
                        </Paper>
                    </div>
                </Loading>
            </div>
        </div>
    );
}

export default GamePlaybackView;
