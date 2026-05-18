import axios from 'axios';
import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import Paper from '@material-ui/core/Paper';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import '../../assets/doudizhu.scss';
import '../../assets/gameview.scss';
import AgentSelector from '../../components/AgentSelector';
import { DoudizhuGameBoard } from '../../components/GameBoard';
import { douzeroDemoUrl } from '../../utils/config';

const TURN_DELAY_MS = 2000;
const PAUSE_COUNTDOWN = 10; // seconds
const PAUSE_COUNTDOWN_INTERVAL = 200; // ms per tick for smooth animation

const POSITIONS = [
    { key: 'landlord', labelKey: 'doudizhu.landlord' },
    { key: 'down', labelKey: 'doudizhu.landlord_down' },
    { key: 'up', labelKey: 'doudizhu.landlord_up' },
];

function cardStr2Arr(cardStr) {
    if (cardStr == null) return 'pass';
    if (Array.isArray(cardStr)) return cardStr;
    if (typeof cardStr !== 'string') return 'pass';
    return cardStr === 'pass' || cardStr === '' ? 'pass' : cardStr.split(' ');
}

function createInitBoard() {
    return {
        playerInfo: [],
        hands: [[], [], []],
        latestAction: [[], [], []],
        currentPlayer: 0,
        considerationTime: 2000,
        turn: 0,
        gameStatus: 'ready',  // 'ready' | 'playing' | 'paused' | 'over'
        thinking: false,
        lastAnalysis: [],
        paused: false,
    };
}

function ConfigurableBattleView() {
    const { t } = useTranslation();
    const [selections, setSelections] = useState({ landlord: 'deep', down: 'deep', up: 'deep' });
    const [sessionId, setSessionId] = useState(null);
    const [board, setBoard] = useState(createInitBoard);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [gameEndDialog, setGameEndDialog] = useState(false);
    const [gameEndText, setGameEndText] = useState('');

    const pollingRef = useRef(false);
    const analysisRef = useRef(null);
    const [pauseCountdown, setPauseCountdown] = useState(0);
    const [pauseProgress, setPauseProgress] = useState(1);
    const countdownRef = useRef(null);
    const countdownEndRef = useRef(0);

    // --- Config phase handlers ---

    const handleStart = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await axios.post(`${douzeroDemoUrl}/live-battle/start`, selections);
            if (res.data.status !== 0) {
                throw new Error(res.data.message || 'Failed to start battle');
            }
            const { session_id, data } = res.data;
            setSessionId(session_id);
            setBoard({
                playerInfo: data.playerInfo,
                hands: data.initHands.map(cardStr2Arr),
                latestAction: [[], [], []],
                currentPlayer: data.playerInfo.find(p => p.role === 'landlord')?.index ?? 0,
                considerationTime: 2000,
                turn: 0,
                gameStatus: 'playing',
                thinking: true,
                lastAnalysis: [],
                paused: false,
            });
            pollingRef.current = true;
            setLoading(false);
        } catch (err) {
            setError(err.message || 'Unknown error');
            setLoading(false);
        }
    }, [selections]);

    // --- Polling loop ---

    useEffect(() => {
        if (!sessionId || board.gameStatus !== 'playing' || board.paused) return;

        let cancelled = false;

        const poll = async () => {
            try {
                const res = await axios.post(`${douzeroDemoUrl}/live-battle/${sessionId}/next`);
                if (cancelled) return;

                if (res.data.status !== 0) {
                    throw new Error(res.data.message || 'Failed to get next turn');
                }

                const step = res.data;
                setBoard(prev => {
                    const next = { ...prev };
                    next.latestAction = step.latestAction.map(cardStr2Arr);
                    next.hands = step.hands.map(cardStr2Arr);
                    next.currentPlayer = step.currentPlayer;
                    next.turn = step.turn;
                    next.thinking = !step.gameOver;
                    // Pause after LLM agent plays so the user can read the analysis
                    next.paused = !!step.analysis && !step.gameOver;
                    next.lastAnalysis = step.analysis
                        ? [...prev.lastAnalysis, {
                            agentName: next.playerInfo[step.playerIdx]?.agentInfo?.name || ('P' + step.playerIdx),
                            playerIdx: step.playerIdx,
                            text: step.analysis,
                        }]
                        : prev.lastAnalysis;

                    if (step.gameOver) {
                        next.gameStatus = 'over';
                        const winnerInfo = next.playerInfo[step.winner];
                        if (winnerInfo) {
                            const role = winnerInfo.role === 'landlord'
                                ? t('doudizhu.landlord')
                                : winnerInfo.index === 1
                                    ? t('doudizhu.landlord_down')
                                    : t('doudizhu.landlord_up');
                            setGameEndText(`${role} (${winnerInfo.agentInfo.name}) ${t('game_playback.game_ends')}`);
                        } else {
                            setGameEndText(t('game_playback.game_ends'));
                        }
                        setGameEndDialog(true);
                    }

                    return next;
                });
            } catch (err) {
                if (!cancelled) {
                    setError(err.message || 'Network error');
                    setBoard(prev => ({ ...prev, gameStatus: 'over', thinking: false }));
                }
            }
        };

        const pollWithDelay = async () => {
            await poll();
            if (!cancelled) {
                setTimeout(() => {
                    if (!cancelled && pollingRef.current) {
                        pollWithDelay();
                    }
                }, TURN_DELAY_MS);
            }
        };

        pollWithDelay();

        return () => {
            cancelled = true;
            pollingRef.current = false;
        };
    }, [sessionId, board.gameStatus, board.paused, t]);

    // Auto-scroll analysis panel to bottom when new analysis is added
    useEffect(() => {
        if (analysisRef.current) {
            analysisRef.current.scrollTop = analysisRef.current.scrollHeight;
        }
    }, [board.lastAnalysis]);

    // Countdown timer: auto-resume after PAUSE_COUNTDOWN seconds
    useEffect(() => {
        if (board.paused) {
            const totalTicks = (PAUSE_COUNTDOWN * 1000) / PAUSE_COUNTDOWN_INTERVAL;
            let tick = totalTicks;
            countdownEndRef.current = Date.now() + PAUSE_COUNTDOWN * 1000;
            setPauseCountdown(PAUSE_COUNTDOWN);
            setPauseProgress(1);

            countdownRef.current = setInterval(() => {
                tick -= 1;
                if (tick <= 0) {
                    clearInterval(countdownRef.current);
                    countdownRef.current = null;
                    pollingRef.current = true;
                    setBoard(b => ({ ...b, paused: false, thinking: true }));
                    return;
                }
                const remaining = Math.ceil(tick * PAUSE_COUNTDOWN_INTERVAL / 1000);
                setPauseCountdown(remaining);
                setPauseProgress(tick / totalTicks);
            }, PAUSE_COUNTDOWN_INTERVAL);
        } else {
            setPauseCountdown(0);
            setPauseProgress(1);
        }
        return () => {
            if (countdownRef.current) {
                clearInterval(countdownRef.current);
                countdownRef.current = null;
            }
        };
    }, [board.paused]);

    const handleResume = useCallback(() => {
        if (countdownRef.current) {
            clearInterval(countdownRef.current);
            countdownRef.current = null;
        }
        pollingRef.current = true;
        setBoard(prev => ({ ...prev, paused: false, thinking: true }));
    }, []);

    const handleBackToConfig = useCallback(() => {
        pollingRef.current = false;
        setSessionId(null);
        setBoard(createInitBoard());
        setError(null);
        setGameEndDialog(false);
    }, []);

    const handleNewBattle = useCallback(async () => {
        pollingRef.current = false;
        setGameEndDialog(false);
        setError(null);
        setBoard(createInitBoard());
        setSessionId(null);

        // Start a fresh battle with the same selections
        setLoading(true);
        try {
            const res = await axios.post(`${douzeroDemoUrl}/live-battle/start`, selections);
            if (res.data.status !== 0) {
                throw new Error(res.data.message || 'Failed to start battle');
            }
            const { session_id, data } = res.data;
            setSessionId(session_id);
            setBoard({
                playerInfo: data.playerInfo,
                hands: data.initHands.map(cardStr2Arr),
                latestAction: [[], [], []],
                currentPlayer: data.playerInfo.find(p => p.role === 'landlord')?.index ?? 0,
                considerationTime: 2000,
                turn: 0,
                gameStatus: 'playing',
                thinking: true,
                lastAnalysis: [],
                paused: false,
            });
            pollingRef.current = true;
            setLoading(false);
        } catch (err) {
            setError(err.message || 'Unknown error');
            setLoading(false);
        }
    }, [selections]);

    const handleCloseDialog = useCallback(() => {
        setGameEndDialog(false);
    }, []);

    // --- Config phase ---

    if (!sessionId) {
        return (
            <div className="configurable-battle-container">
                <Paper elevation={3} className="config-panel">
                    <h2>{t('configurable_battle.title')}</h2>
                    {POSITIONS.map(({ key, labelKey }) => (
                        <div key={key} style={{ margin: '12px 0' }}>
                            <div style={{ fontWeight: 600, marginBottom: '8px', fontSize: '14px', color: '#555' }}>
                                {t(labelKey)}
                            </div>
                            <AgentSelector
                                value={selections[key]}
                                onChange={(v) => setSelections(prev => ({ ...prev, [key]: v }))}
                            />
                        </div>
                    ))}
                    <div style={{ marginTop: '24px' }}>
                        <Button
                            variant="contained"
                            color="primary"
                            onClick={handleStart}
                            disabled={loading}
                        >
                            {loading ? t('loading...') : t('configurable_battle.start_battle')}
                        </Button>
                        {error && <p style={{ color: 'red', marginTop: '12px' }}>{error}</p>}
                    </div>
                </Paper>
            </div>
        );
    }

    // --- Live phase ---

    return (
        <div>
            <div className="live-battle-banner">
                <span className="live-battle-agents">
                    {t('doudizhu.landlord')}: {t(`configurable_battle.agent_${selections.landlord}`)}
                    {' | '}
                    {t('doudizhu.landlord_down')}: {t(`configurable_battle.agent_${selections.down}`)}
                    {' | '}
                    {t('doudizhu.landlord_up')}: {t(`configurable_battle.agent_${selections.up}`)}
                </span>
                <Button
                    variant="outlined"
                    size="small"
                    onClick={handleBackToConfig}
                    style={{ marginLeft: '16px' }}
                >
                    {t('configurable_battle.change_agents')}
                </Button>
            </div>

            <div className={'doudizhu-view-container'}>
                <div style={{ height: '540px', display: 'flex', justifyContent: 'center', gap: '8px' }}>
                    <div style={{ flex: '0 0 750px', height: '100%' }}>
                        <Paper className={'doudizhu-gameboard-paper'} elevation={3} style={{ height: '100%', margin: 0 }}>
                            <DoudizhuGameBoard
                                playerInfo={board.playerInfo}
                                hands={board.hands}
                                latestAction={board.latestAction}
                                mainPlayerId={0}
                                currentPlayer={board.currentPlayer}
                                considerationTime={board.considerationTime}
                                turn={board.turn}
                                gameStatus={board.thinking ? 'playing' : board.gameStatus}
                                gamePlayable={false}
                                showCardBack={false}
                            />
                        </Paper>
                    </div>
                    <div style={{ flex: '0 0 260px', height: '100%' }}>
                        <Paper className={'doudizhu-probability-paper'} elevation={3} style={{ height: '100%', margin: 0, overflow: 'auto' }}>
                            <div style={{ padding: '16px' }}>
                                <div style={{ fontWeight: 'bold', marginBottom: '12px' }}>
                                    {t('configurable_battle.llm_analysis')}
                                </div>
                                <div ref={analysisRef} style={{ maxHeight: '480px', overflow: 'auto' }}>
                                    {board.lastAnalysis.length > 0 ? (
                                        board.lastAnalysis.map((item, i) => {
                                            const colors = {
                                                0: { border: '#1976d2', bg: '#e3f2fd', label: '#1565c0' },
                                                1: { border: '#2e7d32', bg: '#e8f5e9', label: '#1b5e20' },
                                                2: { border: '#e65100', bg: '#fff3e0', label: '#bf360c' },
                                            };
                                            const c = colors[item.playerIdx] || colors[0];
                                            return (
                                                <div key={i} style={{
                                                    borderLeft: `3px solid ${c.border}`,
                                                    backgroundColor: c.bg,
                                                    marginBottom: '10px',
                                                    padding: '8px 10px',
                                                    borderRadius: '0 4px 4px 0',
                                                }}>
                                                    <div style={{
                                                        fontWeight: 700, fontSize: '12px',
                                                        color: c.label, marginBottom: '4px',
                                                    }}>
                                                        {item.agentName}
                                                    </div>
                                                    <div style={{
                                                        fontSize: '13px', lineHeight: '1.55',
                                                        whiteSpace: 'pre-wrap', color: '#333',
                                                    }}>
                                                        {item.text}
                                                    </div>
                                                </div>
                                            );
                                        })
                                    ) : (
                                        board.thinking ? t('configurable_battle.waiting_analysis') : ''
                                    )}
                                </div>
                            </div>
                        </Paper>
                    </div>
                </div>
            </div>

            {board.paused && (
                <div className="live-battle-overlay">
                    <div style={{ width: '260px', margin: '0 auto' }}>
                        <div style={{
                            height: '4px', backgroundColor: '#e0e0e0', borderRadius: '2px',
                            marginBottom: '10px', overflow: 'hidden',
                        }}>
                            <div style={{
                                height: '100%', width: `${pauseProgress * 100}%`,
                                backgroundColor: '#1976d2', borderRadius: '2px',
                                transition: 'width 0.2s linear',
                            }} />
                        </div>
                        <Button variant="contained" color="primary" onClick={handleResume} fullWidth>
                            {t('configurable_battle.continue')} ({pauseCountdown}s)
                        </Button>
                    </div>
                </div>
            )}

            {board.gameStatus === 'over' && (
                <div className="live-battle-overlay">
                    <Button variant="contained" color="primary" onClick={handleNewBattle}>
                        {t('configurable_battle.new_battle')}
                    </Button>
                </div>
            )}

            <Dialog open={gameEndDialog} onClose={handleCloseDialog}>
                <DialogTitle>{t('game_playback.game_ends')}</DialogTitle>
                <DialogContent>
                    <DialogContentText>{gameEndText}</DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleNewBattle} color="primary">
                        {t('configurable_battle.new_battle')}
                    </Button>
                    <Button onClick={handleCloseDialog} color="primary">
                        {t('game_playback.ok')}
                    </Button>
                </DialogActions>
            </Dialog>
        </div>
    );
}

export default ConfigurableBattleView;
