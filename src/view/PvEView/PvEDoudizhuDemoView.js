import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@material-ui/core';
import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';
import Divider from '@material-ui/core/Divider';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import FormGroup from '@material-ui/core/FormGroup';
import Paper from '@material-ui/core/Paper';
import Slider from '@material-ui/core/Slider';
import Checkbox from '@material-ui/core/Checkbox';
import Switch from '@material-ui/core/Switch';
import NotInterestedIcon from '@material-ui/icons/NotInterested';
import { Layout } from 'element-react';
import React, { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import '../../assets/doudizhu.scss';
import '../../assets/gameview.scss';
import { DoudizhuGameBoard } from '../../components/GameBoard';
import {
    card2SuiteAndRank,
    computeHandCardsWidth,
    sortDoudizhuCards,
    translateCardData,
} from '../../utils';
import AgentSelector from '../../components/AgentSelector';
import { usePvEGame } from './usePvEGame';

const POSITIONS = [
    { key: 'landlord', labelKey: 'doudizhu.landlord' },
    { key: 'down', labelKey: 'doudizhu.landlord_down' },
    { key: 'up', labelKey: 'doudizhu.landlord_up' },
];

const gameSpeedMarks = [
    { value: 0, label: '0s' }, { value: 1, label: '1s' },
    { value: 2, label: '3s' }, { value: 3, label: '5s' },
    { value: 4, label: '10s' }, { value: 5, label: '30s' },
];

const gameSpeedMap = [
    { value: 0, delay: 0 }, { value: 1, delay: 1000 },
    { value: 2, delay: 3000 }, { value: 3, delay: 5000 },
    { value: 4, delay: 10000 }, { value: 5, delay: 30000 },
];

function PvEDoudizhuDemoView() {
    const { t, i18n } = useTranslation();
    const game = usePvEGame(t);
    const [showLlmAnalysis, setShowLlmAnalysis] = useState(false);
    const analysisRef = useRef(null);

    useEffect(() => {
        if (analysisRef.current) {
            analysisRef.current.scrollTop = analysisRef.current.scrollHeight;
        }
    }, [game.llmAnalysis]);

    const handleLocaleChange = (newLocale) => {
        localStorage.setItem('LOCALE', newLocale);
        i18n.changeLanguage(newLocale);
        game.setGameStatus('ready');
    };

    const changeApiPlayerDelay = (newVal) => {
        const found = gameSpeedMap.find(e => e.value === newVal);
        if (found) game.setApiPlayDelay(found.delay);
    };

    const sliderValueText = (value) => value;

    // ---- UI helpers ----

    const computePredictionCards = (cards, hands) => {
        let computedCards = [];
        if (cards.length > 0) {
            hands.forEach((card) => {
                const { rank } = card2SuiteAndRank(card);
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
                <div className={'non-card ' + game.toggleFade}>
                    <span>{t('doudizhu.pass')}</span>
                </div>
            );
        } else {
            return (
                <div className={'unselectable playingCards loose ' + game.toggleFade}>
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
        if (game.gameStatus !== 'ready') {
            if (game.hidePredictionArea) {
                return (
                    <div className={'playing'}>
                        <div className={'non-card'}><span>{t('hidden')}</span></div>
                    </div>
                );
            }
            return (
                <div className={'playing'}>
                    <div className="probability-move">
                        {game.predictionRes.prediction.length > idx ? (
                            computePredictionCards(game.predictionRes.prediction[idx][0].split(''), game.predictionRes.hands)
                        ) : (
                            <NotInterestedIcon fontSize="large" />
                        )}
                    </div>
                    {game.predictionRes.prediction.length > idx ? (
                        <div className={'non-card'} style={{ marginTop: '0px' }}>
                            <span>{`${t('doudizhu.expected_win_rate')}: ${(
                                Number(game.predictionRes.prediction[idx][1]) * 100
                            ).toFixed(2)}%`}</span>
                        </div>
                    ) : ''}
                </div>
            );
        } else {
            return <span className={'waiting'}>{t('waiting...')}</span>;
        }
    };

    return (
        <div>
            <Dialog
                disableBackdropClick
                open={game.isGameEndDialogOpen}
                onClose={game.handleCloseGameEndDialog}
                aria-labelledby="alert-dialog-title"
                aria-describedby="alert-dialog-description"
            >
                <DialogTitle id="alert-dialog-title" style={{ width: '200px' }}>
                    {game.gameEndTitle}
                </DialogTitle>
                <DialogContent>
                    <TableContainer className="doudizhu-statistic-table" component={Paper}>
                        <Table aria-label="statistic table">
                            <TableHead>
                                <TableRow>
                                    <TableCell>{t('doudizhu.role')}</TableCell>
                                    <TableCell>{t('doudizhu.win')}</TableCell>
                                    <TableCell>{t('doudizhu.total')}</TableCell>
                                    <TableCell>{t('doudizhu.win_rate')}</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {game.statisticRows.map((row) => (
                                    <TableRow key={'statistic-row-' + row.role}>
                                        <TableCell component="th" scope="row">{row.role}</TableCell>
                                        <TableCell>{row.win}</TableCell>
                                        <TableCell>{row.total}</TableCell>
                                        <TableCell>{row.winRate}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </DialogContent>
                <DialogActions>
                    <Button onClick={game.handleResetStatistics}>{t('reset')}</Button>
                    <Button
                        onClick={game.handleCloseGameEndDialog}
                        color="primary" variant="contained" autoFocus
                        style={{ margin: '16px' }}
                    >
                        {t('play_again')}
                    </Button>
                </DialogActions>
            </Dialog>
            {game.gameStatus === 'configuring' && (
                <div className="configurable-battle-container">
                    <Paper elevation={3} className="config-panel">
                        <h2>{t('configurable_battle.title')}</h2>
                        <p style={{ marginBottom: '16px' }}>
                            {t('doudizhu.role')}: {t(`doudizhu.${game.humanRole}`)}
                        </p>
                        {POSITIONS.filter(p => p.key !== game.humanRole).map(({ key, labelKey }) => (
                            <div key={key} style={{ margin: '12px 0' }}>
                                <div style={{ fontWeight: 600, marginBottom: '8px', fontSize: '14px', color: '#555' }}>
                                    {t(labelKey)} ({t('configurable_battle.agent')})
                                </div>
                                <AgentSelector
                                    value={game.agentTypes[key]}
                                    onChange={(v) => game.setAgentTypes(prev => ({ ...prev, [key]: v }))}
                                />
                            </div>
                        ))}
                        <div style={{ marginTop: '24px' }}>
                            <Button variant="contained" color="primary" onClick={game.handleStartGame}>
                                {t('configurable_battle.start_battle')}
                            </Button>
                        </div>
                    </Paper>
                </div>
            )}

            {game.gameStatus !== 'configuring' && (
                <div className={'doudizhu-view-container'}>
                    <Layout.Row style={{ height: '540px' }}>
                        <Layout.Col style={{ height: '100%' }} span="5">
                            <Paper className={'doudizhu-probability-paper'} elevation={3}>
                            {game.gameDataRef.current.playerInfo.length > 0 && game.gameState.currentPlayer !== null ? (
                                <div style={{ padding: '16px' }}>
                                    <span style={{ textAlign: 'center', marginBottom: '8px', display: 'block' }}>
                                        {t('doudizhu.three_landlord_cards')}
                                    </span>
                                    <div className="playingCards" style={{ display: 'flex', justifyContent: 'center' }}>
                                        {sortDoudizhuCards(game.gameDataRef.current.originalThreeLandlordCards, true).map((card) => {
                                            const [rankClass, suitClass, rankText, suitText] = translateCardData(card);
                                            return (
                                                <div
                                                    key={'probability-cards-' + rankText + '-' + suitText}
                                                    style={{ fontSize: '1.2em' }}
                                                    className={`card ${rankClass} full-content ${suitClass}`}
                                                >
                                                    <span className="rank">{rankText}</span>
                                                    <span className="suit">{suitText}</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            ) : (
                                <div style={{ height: '112px', padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <span>{t('waiting...')}</span>
                                </div>
                            )}
                            <Divider />
                            <div className={'probability-player'} style={{ height: '19px', textAlign: 'center' }}>
                                {game.gameDataRef.current.playerInfo.length > 0 && game.gameState.currentPlayer !== null ? (
                                    <span>
                                        {t(`doudizhu.${['landlord', 'landlord_down', 'landlord_up'][game.gameDataRef.current.playerInfo[game.gameState.currentPlayer].douzeroPlayerPosition]}`)}
                                    </span>
                                ) : (
                                    <span>{t('waiting...')}</span>
                                )}
                            </div>
                            <Divider />
                            <div className={'probability-table with-three-landlord-cards'}>
                                <div className={'probability-item'}>{computeProbabilityItem(0)}</div>
                                <div className={'probability-item'}>{computeProbabilityItem(1)}</div>
                                <div className={'probability-item'}>{computeProbabilityItem(2)}</div>
                            </div>
                        </Paper>
                    </Layout.Col>
                    <Layout.Col style={{ height: '100%' }} span="14">
                        <div style={{ height: '100%' }}>
                            <Paper className={'doudizhu-gameboard-paper'} elevation={3}>
                                <DoudizhuGameBoard
                                    showCardBack={game.gameStatus === 'playing' && game.hideRivalHand}
                                    handleSelectRole={game.handleSelectRole}
                                    isPassDisabled={game.isPassDisabled}
                                    isHintDisabled={game.isHintDisabled}
                                    gamePlayable={true}
                                    playerInfo={game.gameDataRef.current.playerInfo}
                                    hands={game.gameState.hands}
                                    selectedCards={game.selectedCards}
                                    handleSelectedCards={game.handleSelectedCards}
                                    latestAction={game.gameState.latestAction}
                                    mainPlayerId={game.mainPlayerId}
                                    currentPlayer={game.gameState.currentPlayer}
                                    considerationTime={game.considerationTime}
                                    turn={game.gameState.turn}
                                    toggleFade={game.toggleFade}
                                    gameStatus={game.gameStatus}
                                    handleMainPlayerAct={game.handleMainPlayerAct}
                                    handleLocaleChange={handleLocaleChange}
                                />
                            </Paper>
                        </div>
                    </Layout.Col>
                    <Layout.Col span="5" style={{ height: '100%' }}>
                        <Paper className={'doudizhu-probability-paper'} elevation={3} style={{ overflow: 'auto' }} ref={analysisRef}>
                            <div style={{ padding: '16px' }}>
                                <div style={{ fontWeight: 'bold', marginBottom: '12px' }}>
                                    {t('configurable_battle.llm_analysis')}
                                </div>
                                {showLlmAnalysis ? (
                                    game.llmAnalysis.length > 0 ? (
                                        game.llmAnalysis.map((item, i) => {
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
                                                        fontSize: '13px', lineHeight: '1.55', whiteSpace: 'pre-wrap',
                                                        wordBreak: 'break-word', overflowWrap: 'break-word',
                                                        color: '#333',
                                                    }}>
                                                        {item.text}
                                                    </div>
                                                </div>
                                            );
                                        })
                                    ) : (
                                        <div style={{ color: '#999', fontSize: '13px' }}>
                                            {t('configurable_battle.waiting_analysis')}
                                        </div>
                                    )
                                ) : (
                                    <div style={{ color: '#999', fontSize: '13px' }}>
                                        {t('doudizhu.llm_analysis_hidden')}
                                    </div>
                                )}
                            </div>
                        </Paper>
                    </Layout.Col>
                </Layout.Row>
                <div className="game-controller">
                    <Paper className={'game-controller-paper'} elevation={3}>
                        <Layout.Row style={{ height: '51px' }}>
                            <Layout.Col span="5" style={{ height: '51px', lineHeight: '48px' }}>
                                <FormGroup style={{ height: '100%' }}>
                                    <FormControlLabel
                                        style={{ textAlign: 'center', height: '100%', display: 'inline-block' }}
                                        className="switch-control"
                                        control={
                                            <Switch checked={!game.hidePredictionArea} onChange={game.toggleHidePredictionArea} />
                                        }
                                        label={t('doudizhu.ai_hand_faceup')}
                                    />
                                </FormGroup>
                            </Layout.Col>
                            <Layout.Col span="5" style={{ height: '51px', lineHeight: '48px' }}>
                                <FormGroup style={{ height: '100%' }}>
                                    <FormControlLabel
                                        style={{ textAlign: 'center', height: '100%', display: 'inline-block' }}
                                        control={
                                            <Checkbox checked={showLlmAnalysis} onChange={(e) => setShowLlmAnalysis(e.target.checked)} />
                                        }
                                        label={t('doudizhu.show_llm_analysis')}
                                    />
                                </FormGroup>
                            </Layout.Col>
                            <Layout.Col span="1" style={{ height: '100%', width: '1px' }}>
                                <Divider orientation="vertical" />
                            </Layout.Col>
                            <Layout.Col span="3" style={{ height: '51px', lineHeight: '51px', marginLeft: '-2px', marginRight: '-2px' }}>
                                <div style={{ textAlign: 'center' }}>{`${t('turn')} ${game.gameState.turn}`}</div>
                            </Layout.Col>
                            <Layout.Col span="1" style={{ height: '100%', width: '1px' }}>
                                <Divider orientation="vertical" />
                            </Layout.Col>
                            <Layout.Col span="9">
                                <div>
                                    <label className={'form-label-left'} style={{ width: '155px', lineHeight: '28px', fontSize: '15px' }}>
                                        {t('doudizhu.ai_thinking_time')}
                                    </label>
                                    <div style={{ marginLeft: '160px', marginRight: '30px' }}>
                                        <Slider
                                            value={gameSpeedMap.find(e => e.delay === game.apiPlayDelay).value}
                                            getAriaValueText={sliderValueText}
                                            onChange={(e, newVal) => changeApiPlayerDelay(newVal)}
                                            aria-labelledby="discrete-slider-custom"
                                            step={1} min={0} max={5} track={false}
                                            valueLabelDisplay="off" marks={gameSpeedMarks}
                                        />
                                    </div>
                                </div>
                            </Layout.Col>
                        </Layout.Row>
                    </Paper>
                </div>
            </div>
            )}
        </div>
    );
}

export default PvEDoudizhuDemoView;
