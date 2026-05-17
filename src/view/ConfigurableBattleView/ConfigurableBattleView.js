import axios from 'axios';
import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import FormControl from '@material-ui/core/FormControl';
import InputLabel from '@material-ui/core/InputLabel';
import LinearProgress from '@material-ui/core/LinearProgress';
import MenuItem from '@material-ui/core/MenuItem';
import Paper from '@material-ui/core/Paper';
import Select from '@material-ui/core/Select';
import { Layout } from 'element-react';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import '../../assets/doudizhu.scss';
import '../../assets/gameview.scss';
import { DoudizhuGameBoard } from '../../components/GameBoard';
import { douzeroDemoUrl } from '../../utils/config';

const TURN_DELAY_MS = 800;

const AGENT_OPTIONS = [
    { value: 'deep', labelKey: 'configurable_battle.agent_deep' },
    { value: 'llm', labelKey: 'configurable_battle.agent_llm' },
    { value: 'random', labelKey: 'configurable_battle.agent_random' },
];

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
        lastAnalysis: '',
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
                lastAnalysis: '',
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
                        ? prev.lastAnalysis
                            + (prev.lastAnalysis ? '\n\n' : '')
                            + '[' + (next.playerInfo[step.playerIdx]?.agentInfo?.name || ('P' + step.playerIdx)) + '] '
                            + step.analysis
                        : prev.lastAnalysis;

                    if (step.gameOver) {
                        next.gameStatus = 'over';
                        const winnerInfo = next.playerInfo[step.winner];
                        if (winnerInfo) {
                            const role = t(winnerInfo.role === 'landlord'
                                ? 'doudizhu.landlord'
                                : 'doudizhu.landlord_down');
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

    const handleResume = useCallback(() => {
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
                lastAnalysis: '',
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
                        <FormControl key={key} style={{ margin: '12px', minWidth: 200 }}>
                            <InputLabel>{t(labelKey)}</InputLabel>
                            <Select
                                value={selections[key]}
                                onChange={(e) => setSelections(prev => ({ ...prev, [key]: e.target.value }))}
                            >
                                {AGENT_OPTIONS.map(opt => (
                                    <MenuItem key={opt.value} value={opt.value}>
                                        {t(opt.labelKey)}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
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
                <Layout.Row style={{ height: '540px' }}>
                    <Layout.Col style={{ height: '100%' }} span="16">
                        <div style={{ height: '100%' }}>
                            <Paper className={'doudizhu-gameboard-paper'} elevation={3}>
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
                    </Layout.Col>
                    <Layout.Col span="8" style={{ height: '100%' }}>
                        <Paper className={'doudizhu-probability-paper'} elevation={3} style={{ height: '100%', overflow: 'auto' }}>
                            <div style={{ padding: '16px' }}>
                                <div style={{ fontWeight: 'bold', marginBottom: '12px' }}>
                                    {t('configurable_battle.llm_analysis')}
                                </div>
                                <div
                                    ref={analysisRef}
                                    style={{ fontSize: '14px', lineHeight: '1.6', whiteSpace: 'pre-wrap', maxHeight: '480px', overflow: 'auto' }}
                                >
                                    {board.lastAnalysis || (board.thinking
                                        ? t('configurable_battle.waiting_analysis')
                                        : '')}
                                </div>
                            </div>
                        </Paper>
                    </Layout.Col>
                </Layout.Row>
            </div>

            {board.thinking && !board.paused && (
                <div className="live-battle-thinking">
                    <LinearProgress />
                </div>
            )}

            {board.paused && (
                <div className="live-battle-overlay">
                    <Button variant="contained" color="primary" onClick={handleResume}>
                        {t('configurable_battle.continue')}
                    </Button>
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
