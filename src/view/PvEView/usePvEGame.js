import axios from 'axios';
import qs from 'query-string';
import { useEffect, useRef, useState } from 'react';
import { douzeroDemoUrl } from '../../utils/config';
import { createInitialGameData } from '../../utils/gameData';
import {
    card2SuiteAndRank,
    deepCopy,
    isDoudizhuBomb,
    prepareReplayInitHands,
    sortDoudizhuCards,
} from '../../utils';

const initConsiderationTime = 30000;
const considerationTimeDeduction = 1000;
const mainPlayerId = 0;

const POS_KEY = { 0: 'landlord', 1: 'down', 2: 'up' };

const cardArr2DouzeroFormat = (cards) => {
    return cards
        .map((card) => {
            if (card === 'RJ') return 'D';
            if (card === 'BJ') return 'X';
            return card[1];
        })
        .join('');
};

const timeout = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const saveReplayToBackend = async (replayData) => {
    try {
        const response = await axios.post(`${douzeroDemoUrl}/save_replay`, replayData);
        if (response.data.status === 0) {
            console.log('Replay saved successfully:', response.data.replay_id);
        } else {
            console.error('Failed to save replay:', response.data.message);
        }
    } catch (error) {
        console.error('Error saving replay:', error);
    }
};

export function usePvEGame(t) {
    // Lazy-initialized game data ref
    const gameDataRef = useRef(null);
    if (gameDataRef.current === null) {
        gameDataRef.current = createInitialGameData();
    }
    const gd = gameDataRef.current;

    const gameStateTimeoutRef = useRef(null);

    const [gameStatus, setGameStatus] = useState(
        localStorage.getItem('LOCALE') ? 'ready' : 'localeSelection'
    );
    const gameStatusRef = useRef(gameStatus);
    gameStatusRef.current = gameStatus;

    const [apiPlayDelay, setApiPlayDelay] = useState(3000);
    const [isGameEndDialogOpen, setIsGameEndDialogOpen] = useState(false);
    const [considerationTime, setConsiderationTime] = useState(initConsiderationTime);
    const [toggleFade, setToggleFade] = useState('');
    const [gameState, setGameState] = useState({
        hands: [[], [], []],
        latestAction: [[], [], []],
        currentPlayer: null,
        turn: 0,
    });
    const [selectedCards, setSelectedCards] = useState([]);
    const [isPassDisabled, setIsPassDisabled] = useState(true);
    const [isHintDisabled, setIsHintDisabled] = useState(true);
    const [predictionRes, setPredictionRes] = useState({ prediction: [], hands: [] });
    const [llmAnalysis, setLlmAnalysis] = useState([]);
    const [hideRivalHand, setHideRivalHand] = useState(true);
    const [hidePredictionArea, setHidePredictionArea] = useState(true);
    const [statisticRows, setStatisticRows] = useState([]);
    const [agentTypes, setAgentTypes] = useState({ landlord: 'deep', down: 'deep', up: 'deep' });
    const [gameEndTitle, setGameEndTitle] = useState('');

    const humanDouzeroPos = gd.playerInfo[mainPlayerId]?.douzeroPlayerPosition;
    const humanRole = humanDouzeroPos !== undefined && humanDouzeroPos >= 0
        ? POS_KEY[humanDouzeroPos] : 'landlord';

    // ---- game logic ----

    const proceedNextTurn = async (playingCard, rankOnly = true) => {
        const cp = gameState.currentPlayer;

        if (gd.playerInfo[cp].role === 'landlord' && gd.threeLandlordCards.length > 0) {
            let playingCardCopy;
            if (rankOnly) playingCardCopy = playingCard.slice();
            else
                playingCardCopy = playingCard.map((card) => {
                    const { rank } = card2SuiteAndRank(card);
                    return rank;
                });
            gd.threeLandlordCards = gd.threeLandlordCards.filter((card) => {
                const { rank } = card2SuiteAndRank(card);
                const idx = playingCardCopy.indexOf(rank);
                if (idx >= 0) {
                    playingCardCopy.splice(idx, 1);
                    return false;
                } else return true;
            });
        }

        if ((cp + 1) % 3 === mainPlayerId) {
            gd.hintIdx = -1;
            const playerHandCards = cardArr2DouzeroFormat(gameState.hands[mainPlayerId].slice().reverse());
            let rivalMove = '';
            if (playingCard.length === 0) {
                rivalMove = cardArr2DouzeroFormat(sortDoudizhuCards(gd.gameHistory[gd.gameHistory.length - 1], true));
            } else {
                rivalMove = rankOnly ? playingCard.join('') : cardArr2DouzeroFormat(playingCard);
            }
            const apiRes = await axios.post(`${douzeroDemoUrl}/legal`, qs.stringify({
                player_hand_cards: playerHandCards,
                rival_move: rivalMove,
            }));
            const data = apiRes.data;
            gd.legalActions = {
                turn: gameState.turn + 1,
                actions: data.legal_action.split(','),
            };
            setIsHintDisabled(data.legal_action === '');
            setIsPassDisabled(playingCard.length === 0 && gd.gameHistory[gd.gameHistory.length - 1].length === 0);
        }

        if (cp !== mainPlayerId) {
            const pos = gd.playerInfo[cp].douzeroPlayerPosition;
            if (agentTypes[POS_KEY[pos]] !== 'llm') {
                await timeout(apiPlayDelay);
            }
        }

        setToggleFade('fade-out');

        let newGameState = deepCopy(gameState);
        const currentHand = newGameState.hands[cp];
        let newHand;
        let newLatestAction = [];
        if (playingCard.length === 0) {
            newHand = currentHand;
            newLatestAction = 'pass';
        } else if (rankOnly) {
            newHand = currentHand.filter((card) => {
                if (playingCard.length === 0) return true;
                const { rank } = card2SuiteAndRank(card);
                const idx = playingCard.indexOf(rank);
                if (idx >= 0) {
                    playingCard.splice(idx, 1);
                    newLatestAction.push(card);
                    return false;
                }
                return true;
            });
        } else {
            newLatestAction = playingCard.slice();
            newHand = currentHand.filter((card) => {
                if (playingCard.length === 0) return true;
                const idx = playingCard.indexOf(card);
                if (idx >= 0) {
                    playingCard.splice(idx, 1);
                    return false;
                }
                return true;
            });
        }

        const newHistoryRecord = sortDoudizhuCards(newLatestAction === 'pass' ? [] : newLatestAction, true);
        switch (gd.playerInfo[cp].douzeroPlayerPosition) {
            case 0:
                gd.lastMoveLandlord = newHistoryRecord;
                gd.playedCardsLandlord = gd.playedCardsLandlord.concat(newHistoryRecord);
                break;
            case 1:
                gd.lastMoveLandlordDown = newHistoryRecord;
                gd.playedCardsLandlordDown = gd.playedCardsLandlordDown.concat(newHistoryRecord);
                break;
            case 2:
                gd.lastMoveLandlordUp = newHistoryRecord;
                gd.playedCardsLandlordUp = gd.playedCardsLandlordUp.concat(newHistoryRecord);
                break;
            default:
                break;
        }
        gd.gameHistory.push(newHistoryRecord);
        if (isDoudizhuBomb(newHistoryRecord)) gd.bombNum++;

        const moveRecord = {
            playerIdx: cp,
            move: newLatestAction === 'pass' ? 'pass' : newLatestAction.join(' '),
            info: {},
        };
        gd.moveHistory.push(moveRecord);

        newGameState.latestAction[cp] = newLatestAction;
        newGameState.hands[cp] = newHand;
        newGameState.currentPlayer = (cp + 1) % 3;
        newGameState.turn++;
        if (newHand.length === 0) {
            setGameStatus('over');
        }
        setGameState(newGameState);
        setToggleFade('fade-in');
        setTimeout(() => setToggleFade(''), 200);

        if (gameStateTimeoutRef.current) {
            clearTimeout(gameStateTimeoutRef.current);
        }

        if (newHand.length === 0) {
            setHideRivalHand(false);
            const winner = gd.playerInfo[cp];

            const storedStats = localStorage.getItem('GAME_STATISTICS');
            const stats = storedStats ? JSON.parse(storedStats) : {
                totalGameNum: 0, totalWinNum: 0,
                landlordGameNum: 0, landlordWinNum: 0,
                landlordUpGameNum: 0, landlordUpWinNum: 0,
                landlordDownGameNum: 0, landlordDownWinNum: 0,
            };

            stats.totalGameNum += 1;
            switch (gd.playerInfo[mainPlayerId].douzeroPlayerPosition) {
                case 0:
                    stats.landlordGameNum += 1;
                    if (winner.role === gd.playerInfo[mainPlayerId].role) {
                        stats.totalWinNum += 1; stats.landlordWinNum += 1;
                    }
                    break;
                case 1:
                    stats.landlordDownGameNum += 1;
                    if (winner.role === gd.playerInfo[mainPlayerId].role) {
                        stats.totalWinNum += 1; stats.landlordDownWinNum += 1;
                    }
                    break;
                case 2:
                    stats.landlordUpGameNum += 1;
                    if (winner.role === gd.playerInfo[mainPlayerId].role) {
                        stats.totalWinNum += 1; stats.landlordUpWinNum += 1;
                    }
                    break;
                default:
                    break;
            }
            localStorage.setItem('GAME_STATISTICS', JSON.stringify(stats));

            setTimeout(() => {
                setGameEndTitle(
                    winner.role === 'peasant' ? t('doudizhu.peasants_win') : t('doudizhu.landlord_win')
                );
                setStatisticRows([
                    {
                        role: t('doudizhu.landlord'), win: stats.landlordWinNum,
                        total: stats.landlordGameNum,
                        winRate: stats.landlordGameNum
                            ? ((stats.landlordWinNum / stats.landlordGameNum) * 100).toFixed(2) + '%' : '-',
                    },
                    {
                        role: t('doudizhu.landlord_up'), win: stats.landlordUpWinNum,
                        total: stats.landlordUpGameNum,
                        winRate: stats.landlordUpGameNum
                            ? ((stats.landlordUpWinNum / stats.landlordUpGameNum) * 100).toFixed(2) + '%' : '-',
                    },
                    {
                        role: t('doudizhu.landlord_down'), win: stats.landlordDownWinNum,
                        total: stats.landlordDownGameNum,
                        winRate: stats.landlordDownGameNum
                            ? ((stats.landlordDownWinNum / stats.landlordDownGameNum) * 100).toFixed(2) + '%' : '-',
                    },
                    {
                        role: t('doudizhu.all'), win: stats.totalWinNum,
                        total: stats.totalGameNum,
                        winRate: stats.totalGameNum
                            ? ((stats.totalWinNum / stats.totalGameNum) * 100).toFixed(2) + '%' : '-',
                    },
                ]);
                setIsGameEndDialogOpen(true);

                const replayData = {
                    playerInfo: gd.playerInfo.map(p => ({
                        id: p.id, index: p.index, role: p.role,
                        agentInfo: p.agentInfo || { name: p.index === mainPlayerId ? 'Player' : 'DouZero' },
                    })),
                    initHands: (gd.replayInitHands || gd.initHands).map(hand => hand.join(' ')),
                    moveHistory: gd.moveHistory,
                    source: 'pve',
                };
                saveReplayToBackend(replayData);
            }, 2000);
        } else {
            setConsiderationTime(initConsiderationTime);
            if (initConsiderationTime === considerationTime) gameStateTimer();
        }
    };

    const requestApiPlay = async () => {
        const cp = gameState.currentPlayer;
        const playerPos = gd.playerInfo[cp].douzeroPlayerPosition;
        const playerHandCards = cardArr2DouzeroFormat(gameState.hands[cp].slice().reverse());
        const numCardsLeftLandlord = gameState.hands[gd.playerInfo.find(p => p.douzeroPlayerPosition === 0).index].length;
        const numCardsLeftDown = gameState.hands[gd.playerInfo.find(p => p.douzeroPlayerPosition === 1).index].length;
        const numCardsLeftUp = gameState.hands[gd.playerInfo.find(p => p.douzeroPlayerPosition === 2).index].length;
        const threeLandlord = cardArr2DouzeroFormat(gd.originalThreeLandlordCards.slice().reverse());
        const cardPlayActionSeq = gd.gameHistory.map(cards => cardArr2DouzeroFormat(cards)).join(',');
        const otherHandCards = cardArr2DouzeroFormat(sortDoudizhuCards(
            gameState.hands[(cp + 1) % 3].concat(gameState.hands[(cp + 2) % 3]), true));
        const lastMoveLandlord = cardArr2DouzeroFormat(gd.lastMoveLandlord.slice().reverse());
        const lastMoveDown = cardArr2DouzeroFormat(gd.lastMoveLandlordDown.slice().reverse());
        const lastMoveUp = cardArr2DouzeroFormat(gd.lastMoveLandlordUp.slice().reverse());
        const bombNum = gd.bombNum;
        const playedLandlord = cardArr2DouzeroFormat(gd.playedCardsLandlord);
        const playedDown = cardArr2DouzeroFormat(gd.playedCardsLandlordDown);
        const playedUp = cardArr2DouzeroFormat(gd.playedCardsLandlordUp);

        const requestBody = {
            player_position: playerPos,
            player_hand_cards: playerHandCards,
            num_cards_left_landlord: numCardsLeftLandlord,
            num_cards_left_landlord_down: numCardsLeftDown,
            num_cards_left_landlord_up: numCardsLeftUp,
            three_landlord_cards: threeLandlord,
            card_play_action_seq: cardPlayActionSeq,
            other_hand_cards: otherHandCards,
            last_move_landlord: lastMoveLandlord,
            last_move_landlord_down: lastMoveDown,
            last_move_landlord_up: lastMoveUp,
            bomb_num: bombNum,
            played_cards_landlord: playedLandlord,
            played_cards_landlord_down: playedDown,
            played_cards_landlord_up: playedUp,
            agent_type: agentTypes[POS_KEY[playerPos]],
        };

        try {
            const apiRes = await axios.post(`${douzeroDemoUrl}/predict`, qs.stringify(requestBody));
            const data = apiRes.data;

            if (data.status !== 0) {
                if (data.status === -1) {
                    const handCards = cardArr2DouzeroFormat(gameState.hands[cp].slice().reverse());
                    let rivalMove = '';
                    if (gd.gameHistory[gd.gameHistory.length - 1].length > 0) {
                        rivalMove = cardArr2DouzeroFormat(sortDoudizhuCards(gd.gameHistory[gd.gameHistory.length - 1], true));
                    } else if (gd.gameHistory.length >= 2 && gd.gameHistory[gd.gameHistory.length - 2].length > 0) {
                        rivalMove = cardArr2DouzeroFormat(sortDoudizhuCards(gd.gameHistory[gd.gameHistory.length - 2], true));
                    }
                    const legalApiRes = await axios.post(`${douzeroDemoUrl}/legal`, qs.stringify({
                        player_hand_cards: handCards, rival_move: rivalMove,
                    }));
                    if (legalApiRes.data.legal_action === '') {
                        proceedNextTurn([]);
                        setPredictionRes({
                            prediction: [['', t('doudizhu.only_choice')]],
                            hands: gameState.hands[cp].slice(),
                        });
                    } else if (legalApiRes.data.legal_action.split(',').length === 1) {
                        proceedNextTurn(legalApiRes.data.legal_action.split(''));
                        setPredictionRes({
                            prediction: [[legalApiRes.data.legal_action, t('doudizhu.only_choice')]],
                            hands: gameState.hands[cp].slice(),
                        });
                    }
                }
            } else {
                let bestAction = '';
                if (data.result && Object.keys(data.result).length > 0) {
                    const sortedResult = Object.entries(data.result).sort((a, b) => Number(b[1]) - Number(a[1]));
                    setPredictionRes({
                        prediction: sortedResult.map(r => [r[0], data.win_rates[r[0]]]),
                        hands: gameState.hands[cp].slice(),
                    });
                    if (data.analysis) {
                        const posKey = POS_KEY[playerPos];
                        const labelMap = { deep: 'DouZero', llm: 'LLM', random: 'Random' };
                        const agentName = labelMap[agentTypes[posKey]] || agentTypes[posKey];
                        setLlmAnalysis(prev => [...prev, {
                            agentName,
                            playerIdx: playerPos,
                            text: data.analysis,
                        }]);
                    }
                    if (Object.keys(data.result).length === 1) {
                        bestAction = Object.keys(data.result)[0];
                    } else {
                        bestAction = Object.keys(data.result)[0];
                        let bestConf = Number(data.result[Object.keys(data.result)[0]]);
                        for (let i = 1; i < Object.keys(data.result).length; i++) {
                            if (Number(data.result[Object.keys(data.result)[i]]) > bestConf) {
                                bestAction = Object.keys(data.result)[i];
                                bestConf = Number(data.result[Object.keys(data.result)[i]]);
                            }
                        }
                    }
                }
                proceedNextTurn(bestAction.split(''));
            }
        } catch (err) {
            // silently fail
        }
    };

    const gameStateTimer = () => {
        const scheduledTurn = gameState.turn;
        const scheduledPlayer = gameState.currentPlayer;
        clearTimeout(gameStateTimeoutRef.current);
        gameStateTimeoutRef.current = setTimeout(() => {
            if (gameState.turn !== scheduledTurn || gameState.currentPlayer !== scheduledPlayer) {
                return;
            }
            let currentTime = considerationTime;
            if (currentTime > 0) {
                currentTime -= considerationTimeDeduction;
                currentTime = Math.max(currentTime, 0);
                setConsiderationTime(currentTime);
            } else {
                if (gameState.currentPlayer !== mainPlayerId && gameStatusRef.current === 'playing') {
                    setConsiderationTime(initConsiderationTime);
                    gameStateTimer();
                } else if (gameState.currentPlayer === mainPlayerId && gameStatusRef.current === 'playing') {
                    if (gd.legalActions.turn === gameState.turn && gd.legalActions.actions.length > 0) {
                        const autoPlayRanks = gd.legalActions.actions[0].split('');
                        let autoPlayCards = [];
                        gameState.hands[mainPlayerId].forEach((card) => {
                            const { rank } = card2SuiteAndRank(card);
                            const idx = autoPlayRanks.indexOf(rank);
                            if (idx >= 0) {
                                autoPlayRanks.splice(idx, 1);
                                autoPlayCards.push(card);
                            }
                        });
                        if (autoPlayCards.length > 0) {
                            proceedNextTurn(autoPlayCards, false);
                        } else {
                            proceedNextTurn([], false);
                        }
                    } else {
                        proceedNextTurn([], false);
                    }
                }
            }
        }, considerationTimeDeduction);
    };

    const startGame = async () => {
        setGameStatus('playing');
        const newGameState = deepCopy(gameState);
        newGameState.currentPlayer = gd.playerInfo.find(e => e.role === 'landlord').index;
        newGameState.hands = gd.initHands.map(e => sortDoudizhuCards(e));

        if (newGameState.currentPlayer === mainPlayerId) {
            const handCards = cardArr2DouzeroFormat(newGameState.hands[mainPlayerId].slice().reverse());
            const apiRes = await axios.post(`${douzeroDemoUrl}/legal`, qs.stringify({
                player_hand_cards: handCards, rival_move: '',
            }));
            gd.legalActions = { turn: 0, actions: apiRes.data.legal_action.split(',') };
            setIsHintDisabled(apiRes.data.legal_action === '');
        }

        setGameState(newGameState);
        gameStateTimer();
    };

    // ---- event handlers ----

    const handleSelectedCards = (cards) => {
        let newSelected = selectedCards.slice();
        cards.forEach((card) => {
            if (newSelected.indexOf(card) >= 0) {
                newSelected.splice(newSelected.indexOf(card), 1);
            } else {
                newSelected.push(card);
            }
        });
        setSelectedCards(newSelected);
    };

    const handleSelectRole = (role) => {
        const template = [
            { id: 0, index: 0, role: 'peasant', douzeroPlayerPosition: -1 },
            { id: 1, index: 1, role: 'peasant', douzeroPlayerPosition: -1 },
            { id: 2, index: 2, role: 'peasant', douzeroPlayerPosition: -1 },
        ];
        switch (role) {
            case 'landlord_up':
                gd.playerInfo = deepCopy(template); gd.playerInfo[1].role = 'landlord'; break;
            case 'landlord':
                gd.playerInfo = deepCopy(template); gd.playerInfo[0].role = 'landlord'; break;
            case 'landlord_down':
                gd.playerInfo = deepCopy(template); gd.playerInfo[2].role = 'landlord'; break;
            default: break;
        }
        const landlordIdx = gd.playerInfo.find(p => p.role === 'landlord').index;
        gd.playerInfo[landlordIdx].douzeroPlayerPosition = 0;
        gd.playerInfo[(landlordIdx + 1) % 3].douzeroPlayerPosition = 1;
        gd.playerInfo[(landlordIdx + 2) % 3].douzeroPlayerPosition = 2;
        gd.replayInitHands = prepareReplayInitHands(gd.initHands, gd.threeLandlordCards, landlordIdx);
        gd.initHands[landlordIdx] = gd.initHands[landlordIdx].concat(gd.threeLandlordCards.slice());
        setGameStatus('configuring');
    };

    const handleStartGame = () => {
        for (let i = 0; i < 3; i++) {
            const p = gd.playerInfo[i];
            if (i === mainPlayerId) {
                p.agentInfo = { name: 'Player' };
            } else {
                const posKey = POS_KEY[p.douzeroPlayerPosition];
                const labelMap = { deep: 'DouZero', llm: 'LLM', random: 'Random' };
                p.agentInfo = { name: `${labelMap[agentTypes[posKey]] || agentTypes[posKey]}` };
            }
        }
        setGameStatus('playing');
    };

    const handleMainPlayerAct = (type) => {
        switch (type) {
            case 'play': {
                if (gameState.turn === gd.legalActions.turn) {
                    if (gd.legalActions.actions.indexOf(
                        cardArr2DouzeroFormat(sortDoudizhuCards(selectedCards, true))) >= 0) {
                        proceedNextTurn(selectedCards, false);
                    } else {
                        setSelectedCards([]);
                    }
                }
                break;
            }
            case 'pass': {
                proceedNextTurn([], false);
                setSelectedCards([]);
                break;
            }
            case 'deselect': {
                setSelectedCards([]);
                break;
            }
            case 'hint': {
                if (gameState.turn === gd.legalActions.turn) {
                    setSelectedCards([]);
                    gd.hintIdx++;
                    if (gd.hintIdx >= gd.legalActions.actions.length) gd.hintIdx = 0;
                    const hintRanks = gd.legalActions.actions[gd.hintIdx].split('');
                    let hintCards = [];
                    gameState.hands[gameState.currentPlayer].forEach((card) => {
                        const { rank } = card2SuiteAndRank(card);
                        const idx = hintRanks.indexOf(rank);
                        if (idx >= 0) {
                            hintRanks.splice(idx, 1);
                            hintCards.push(card);
                        }
                    });
                    setSelectedCards(hintCards);
                }
                break;
            }
            default: break;
        }
    };

    const toggleHidePredictionArea = () => {
        setHideRivalHand(!hideRivalHand);
        setHidePredictionArea(!hidePredictionArea);
    };

    const handleResetStatistics = () => {
        localStorage.removeItem('GAME_STATISTICS');
        setStatisticRows([
            { role: t('doudizhu.landlord'), win: 0, total: 0, winRate: '-' },
            { role: t('doudizhu.landlord_up'), win: 0, total: 0, winRate: '-' },
            { role: t('doudizhu.landlord_down'), win: 0, total: 0, winRate: '-' },
            { role: t('doudizhu.all'), win: 0, total: 0, winRate: '-' },
        ]);
    };

    const handleCloseGameEndDialog = () => {
        const fresh = createInitialGameData();
        Object.assign(gd, fresh);
        gameStateTimeoutRef.current = null;
        setConsiderationTime(initConsiderationTime);
        setToggleFade('');
        setIsPassDisabled(true);
        setIsHintDisabled(true);
        setGameState({ hands: [[], [], []], latestAction: [[], [], []], currentPlayer: null, turn: 0 });
        setSelectedCards([]);
        setPredictionRes({ prediction: [], hands: [] });
        setLlmAnalysis([]);
        setHideRivalHand(hidePredictionArea);
        setGameStatus('ready');
        setIsGameEndDialogOpen(false);
    };

    // ---- effects ----

    useEffect(() => {
        if (gameStatusRef.current === 'playing') gameStateTimer();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [considerationTime]);

    useEffect(() => {
        if (gameState.currentPlayer !== null && gameStatusRef.current === 'playing') {
            if (gameState.currentPlayer !== mainPlayerId) {
                requestApiPlay();
            } else {
                setPredictionRes({ prediction: [], hands: [] });
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [gameState.currentPlayer]);

    useEffect(() => {
        if (gameStatus === 'playing') startGame();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [gameStatus]);

    return {
        // state
        gameState, gameStatus, setGameStatus, considerationTime, setConsiderationTime,
        toggleFade, selectedCards, isPassDisabled, isHintDisabled,
        predictionRes, hideRivalHand, hidePredictionArea,
        llmAnalysis, setLlmAnalysis,
        statisticRows, agentTypes, setAgentTypes,
        isGameEndDialogOpen, gameEndTitle,
        apiPlayDelay, setApiPlayDelay,
        // refs
        gameDataRef, gameStatusRef,
        // constants
        mainPlayerId, humanRole,
        // handlers
        handleSelectedCards, handleSelectRole, handleStartGame,
        handleMainPlayerAct, handleResetStatistics, handleCloseGameEndDialog,
        toggleHidePredictionArea,
    };
}
