import Avatar from '@material-ui/core/Avatar';
import Button from '@material-ui/core/Button';
import Chip from '@material-ui/core/Chip';
import { Layout } from 'element-react';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { withTranslation } from 'react-i18next';
import '../../assets/doudizhu.scss';
import Landlord_wName from '../../assets/images/Portrait/Landlord_wName.png';
import Peasant_wName from '../../assets/images/Portrait/Peasant_wName.png';
import PlaceHolderPlayer from '../../assets/images/Portrait/Player.png';
import { computeHandCardsWidth, millisecond2Second, sortDoudizhuCards, translateCardData } from '../../utils';

function DoudizhuGameBoard({
    playerInfo,
    hands,
    selectedCards = [],
    handleSelectedCards,
    latestAction,
    mainPlayerId,
    currentPlayer,
    considerationTime,
    turn,
    toggleFade,
    gameStatus,
    gamePlayable,
    handleMainPlayerAct,
    handleSelectRole,
    handleLocaleChange,
    isPassDisabled,
    isHintDisabled,
    showCardBack,
    runNewTurn,
    t,
}) {
    const [highlightedCards, setHighlightedCards] = useState([]);
    const isSelectingCardsRef = useRef(false);
    const selectingCardsRef = useRef({ start: null, cards: [] });
    const prevTurnRef = useRef(turn);

    // componentDidUpdate: call runNewTurn when turn changes
    useEffect(() => {
        if (
            runNewTurn &&
            prevTurnRef.current !== turn &&
            turn !== 0 &&
            gameStatus === 'playing'
        ) {
            runNewTurn({ turn: prevTurnRef.current });
        }
        prevTurnRef.current = turn;
    }, [turn, gameStatus, runNewTurn]);

    const computePlayerPortrait = useCallback(
        (playerId, playerIdx) => {
            if (playerInfo.length > 0 && playerIdx >= 0 && playerIdx < playerInfo.length) {
                const player = playerInfo[playerIdx];
                const chipTitle =
                    player && player.agentInfo && player.agentInfo.name ? '' : 'ID';
                const chipLabel =
                    player && player.agentInfo && player.agentInfo.name
                        ? player.agentInfo.name
                        : playerId;
                return playerInfo[playerIdx].role === 'landlord' ? (
                    <div>
                        <img src={Landlord_wName} alt={'Landlord'} height="70%" width="70%" />
                        <Chip
                            style={{ maxWidth: '135px' }}
                            avatar={chipTitle ? <Avatar>{chipTitle}</Avatar> : undefined}
                            label={chipLabel}
                            color="primary"
                        />
                    </div>
                ) : (
                    <div>
                        <img src={Peasant_wName} alt={'Peasant'} height="70%" width="70%" />
                        <Chip
                            style={{ maxWidth: '135px' }}
                            avatar={chipTitle ? <Avatar>{chipTitle}</Avatar> : undefined}
                            label={chipLabel}
                            color="primary"
                        />
                    </div>
                );
            } else
                return (
                    <div>
                        <img src={PlaceHolderPlayer} alt={'Player'} height="70%" width="70%" />
                        <Chip avatar={<Avatar>ID</Avatar>} label={playerId} color="primary" />
                    </div>
                );
        },
        [playerInfo],
    );

    const handleContainerMouseLeave = useCallback(() => {
        if (!gamePlayable) return;
        if (isSelectingCardsRef.current) {
            isSelectingCardsRef.current = false;
            selectingCardsRef.current = { start: null, cards: [] };
            setHighlightedCards([]);
        }
    }, [gamePlayable]);

    const handleContainerMouseUp = useCallback(() => {
        if (!gamePlayable) return;
        if (isSelectingCardsRef.current) {
            isSelectingCardsRef.current = false;
            handleSelectedCards(selectingCardsRef.current.cards);
            selectingCardsRef.current = { start: null, cards: [] };
            setHighlightedCards([]);
        } else {
            handleMainPlayerAct('deselect');
        }
    }, [gamePlayable, handleSelectedCards, handleMainPlayerAct]);

    const handleCardMouseDown = useCallback((card, idx) => {
        isSelectingCardsRef.current = true;
        selectingCardsRef.current.start = idx;
        selectingCardsRef.current.cards = [card];
        setHighlightedCards([card]);
    }, []);

    const handleCardMouseOver = useCallback((allCards, card, idx) => {
        if (isSelectingCardsRef.current) {
            let tmpCards;
            if (idx > selectingCardsRef.current.start) {
                tmpCards = allCards.slice(selectingCardsRef.current.start, idx + 1);
            } else if (idx < selectingCardsRef.current.start) {
                tmpCards = allCards.slice(idx, selectingCardsRef.current.start + 1);
            } else {
                tmpCards = [card];
            }
            selectingCardsRef.current = { ...selectingCardsRef.current, cards: tmpCards };
            setHighlightedCards(tmpCards);
        }
    }, []);

    const computeSingleLineHand = useCallback(
        (inputCards, fadeClassName = '', cardSelectable = false) => {
            const cards = inputCards === 'pass' ? inputCards : sortDoudizhuCards(inputCards);
            if (cards === 'pass') {
                return (
                    <div className="non-card">
                        <span>{t('doudizhu.pass')}</span>
                    </div>
                );
            } else {
                return (
                    <div
                        className={`playingCards loose ${fadeClassName} ${
                            gameStatus === 'playing' && gamePlayable && cardSelectable
                                ? 'selectable'
                                : 'unselectable'
                        }`}
                    >
                        <ul className="hand" style={{ width: computeHandCardsWidth(cards.length, 12) }}>
                            {cards.map((card, idx) => {
                                const [rankClass, suitClass, rankText, suitText] = translateCardData(card);
                                let selected = false;
                                if (gamePlayable && cardSelectable) {
                                    selected = selectedCards.indexOf(card) >= 0;
                                }

                                return (
                                    <li key={`handCard-${card}`}>
                                        <label
                                            onMouseDown={(e) => {
                                                e.stopPropagation();
                                                cardSelectable && handleCardMouseDown(card, idx);
                                            }}
                                            onMouseOver={(e) => {
                                                e.stopPropagation();
                                                cardSelectable && handleCardMouseOver(cards, card, idx);
                                            }}
                                            className={`card ${rankClass} ${suitClass} ${selected ? 'selected' : ''} ${
                                                cardSelectable && highlightedCards.includes(card)
                                                    ? 'user-selecting'
                                                    : ''
                                            }`}
                                        >
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
        },
        [gameStatus, gamePlayable, selectedCards, highlightedCards, t, handleCardMouseDown, handleCardMouseOver],
    );

    const computeSideHand = useCallback(
        (cards) => {
            if (cards === 'pass') {
                return (
                    <div className="non-card">
                        <span>{t('doudizhu.pass')}</span>
                    </div>
                );
            }
            const sorted = sortDoudizhuCards(cards);
            let upCards;
            let downCards = [];
            if (sorted.length > 10) {
                upCards = sorted.slice(0, 10);
                downCards = sorted.slice(10);
            } else {
                upCards = sorted;
            }
            return (
                <div>
                    <div className="player-hand-up">
                        <div className="playingCards unselectable loose">
                            <ul className="hand">
                                {upCards.map((card) => {
                                    const [rankClass, suitClass, rankText, suitText] = translateCardData(card);
                                    return (
                                        <li key={`handCard-${card}`}>
                                            <label
                                                className={`card ${
                                                    showCardBack ? 'back ' : `${rankClass} ${suitClass}`
                                                }`}
                                            >
                                                <span className="rank">{rankText}</span>
                                                <span className="suit">{suitText}</span>
                                            </label>
                                        </li>
                                    );
                                })}
                            </ul>
                        </div>
                    </div>
                    <div className="player-hand-down">
                        <div className="playingCards unselectable loose">
                            <ul className="hand">
                                {downCards.map((card) => {
                                    const [rankClass, suitClass, rankText, suitText] = translateCardData(card);
                                    return (
                                        <li key={`handCard-${card}`}>
                                            <label
                                                className={`card ${
                                                    showCardBack ? 'back ' : `${rankClass} ${suitClass}`
                                                }`}
                                            >
                                                <span className="rank">{rankText}</span>
                                                <span className="suit">{suitText}</span>
                                            </label>
                                        </li>
                                    );
                                })}
                            </ul>
                        </div>
                    </div>
                </div>
            );
        },
        [showCardBack, t],
    );

    const playerDecisionArea = useCallback(
        (playerIdx) => {
            let fadeClassName = '';
            if (toggleFade === 'fade-out' && (playerIdx + 2) % 3 === currentPlayer)
                fadeClassName = 'fade-out';
            else if (toggleFade === 'fade-in' && (playerIdx + 1) % 3 === currentPlayer)
                fadeClassName = 'scale-fade-in';
            if (currentPlayer === playerIdx) {
                if (mainPlayerId === playerInfo[currentPlayer].id) {
                    return (
                        <div className={'main-player-action-wrapper'}>
                            <div style={{ marginRight: '2em' }} className={'timer ' + fadeClassName}>
                                <div className="timer-text">{millisecond2Second(considerationTime)}</div>
                            </div>
                            {gamePlayable ? (
                                <>
                                    <Button
                                        disabled={isHintDisabled || gameStatus !== 'playing'}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleMainPlayerAct('hint');
                                        }}
                                        style={{ marginRight: '2em' }}
                                        variant="contained"
                                        color="primary"
                                    >
                                        {t('doudizhu.hint')}
                                    </Button>
                                    <Button
                                        disabled={isPassDisabled || gameStatus !== 'playing'}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleMainPlayerAct('pass');
                                        }}
                                        style={{ marginRight: '2em' }}
                                        variant="contained"
                                        color="primary"
                                    >
                                        {t('doudizhu.pass')}
                                    </Button>
                                    <Button
                                        disabled={
                                            !selectedCards ||
                                            selectedCards.length === 0 ||
                                            gameStatus !== 'playing'
                                        }
                                        onClick={(e) => {
                                            console.log('play', e.stopPropagation);
                                            e.stopPropagation();
                                            handleMainPlayerAct('play');
                                        }}
                                        variant="contained"
                                        color="primary"
                                    >
                                        {t('doudizhu.play')}
                                    </Button>
                                </>
                            ) : undefined}
                        </div>
                    );
                } else {
                    return (
                        <div className={'timer ' + fadeClassName}>
                            <div className="timer-text">{millisecond2Second(considerationTime)}</div>
                        </div>
                    );
                }
            } else {
                return computeSingleLineHand(latestAction[playerIdx], fadeClassName);
            }
        },
        [toggleFade, currentPlayer, mainPlayerId, playerInfo, considerationTime, gamePlayable, isHintDisabled, isPassDisabled, selectedCards, gameStatus, handleMainPlayerAct, t, computeSingleLineHand, latestAction],
    );

    // compute the id as well as index in list for every player
    const bottomId = mainPlayerId;
    const found = playerInfo.find((element) => element.id === bottomId);
    const bottomIdx = found ? found.index : -1;
    const rightIdx = bottomIdx >= 0 ? (bottomIdx + 1) % 3 : -1;
    const leftIdx = rightIdx >= 0 ? (rightIdx + 1) % 3 : -1;
    let rightId = -1;
    let leftId = -1;
    if (rightIdx >= 0 && leftIdx >= 0) {
        let found2 = playerInfo.find((element) => element.index === rightIdx);
        if (found2) rightId = found2.id;
        found2 = playerInfo.find((element) => element.index === leftIdx);
        if (found2) leftId = found2.id;
    }

    return (
        <div
            className="doudizhu-wrapper"
            onMouseLeave={(e) => {
                e.stopPropagation();
                handleContainerMouseLeave();
            }}
            onClick={(e) => {
                e.stopPropagation();
                handleContainerMouseUp();
            }}
        >
            <div
                id={'gameboard-background'}
                className={
                    (gameStatus === 'ready' || gameStatus === 'localeSelection') && gamePlayable
                        ? 'blur-background'
                        : undefined
                }
            >
                <div id={'left-player'}>
                    <div className="player-main-area">
                        <div className="player-info">{computePlayerPortrait(leftId, leftIdx)}</div>
                        {leftIdx >= 0 ? (
                            computeSideHand(hands[leftIdx])
                        ) : (
                            <div className="player-hand-placeholder">
                                <span>{t('waiting...')}</span>
                            </div>
                        )}
                    </div>
                    <div className="played-card-area">{leftIdx >= 0 ? playerDecisionArea(leftIdx) : ''}</div>
                </div>
                <div id={'right-player'}>
                    <div className="player-main-area">
                        <div className="player-info">{computePlayerPortrait(rightId, rightIdx)}</div>
                        {rightIdx >= 0 ? (
                            computeSideHand(hands[rightIdx])
                        ) : (
                            <div className="player-hand-placeholder">
                                <span>{t('waiting...')}</span>
                            </div>
                        )}
                    </div>
                    <div className="played-card-area">{rightIdx >= 0 ? playerDecisionArea(rightIdx) : ''}</div>
                </div>
                <div id={'bottom-player'}>
                    <div className="played-card-area">
                        {bottomIdx >= 0 ? playerDecisionArea(bottomIdx) : ''}
                    </div>
                    <div className="player-main-area">
                        <div className="player-info">{computePlayerPortrait(bottomId, bottomIdx)}</div>
                        {bottomIdx >= 0 ? (
                            <div className="player-hand">
                                {computeSingleLineHand(hands[bottomIdx], '', true)}
                            </div>
                        ) : (
                            <div className="player-hand-placeholder">
                                <span>{t('waiting...')}</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
            {gamePlayable && gameStatus === 'ready' && (
                <Layout.Row
                    type="flex"
                    style={{
                        position: 'absolute',
                        top: 0,
                        height: '100%',
                        width: '100%',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center',
                    }}
                >
                    <Button
                        onClick={() => handleSelectRole('landlord_up')}
                        style={{ width: '225px', justifyContent: 'space-evenly' }}
                        variant="contained"
                        color="primary"
                        startIcon={<img src={Peasant_wName} alt="Peasant" width="48px" height="48px" />}
                    >
                        {t('doudizhu.play_as_peasant')}
                        <br />({t('doudizhu.landlord_up')})
                    </Button>
                    <Button
                        onClick={() => handleSelectRole('landlord')}
                        style={{
                            width: '225px',
                            justifyContent: 'space-evenly',
                            marginTop: '20px',
                            marginBottom: '20px',
                        }}
                        variant="contained"
                        color="primary"
                        startIcon={<img src={Landlord_wName} alt="Peasant" width="48px" height="48px" />}
                    >
                        {t('doudizhu.play_as_landlord')}
                    </Button>
                    <Button
                        onClick={() => handleSelectRole('landlord_down')}
                        style={{ width: '225px', justifyContent: 'space-evenly' }}
                        variant="contained"
                        color="primary"
                        startIcon={<img src={Peasant_wName} alt="Peasant" width="48px" height="48px" />}
                    >
                        {t('doudizhu.play_as_peasant')}
                        <br />({t('doudizhu.landlord_down')})
                    </Button>
                </Layout.Row>
            )}
            {gamePlayable && gameStatus === 'localeSelection' && (
                <Layout.Row
                    type="flex"
                    style={{
                        position: 'absolute',
                        top: 0,
                        height: '100%',
                        width: '100%',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center',
                    }}
                >
                    <Button
                        onClick={() => handleLocaleChange('zh')}
                        style={{ width: '225px', padding: '15px' }}
                        variant="contained"
                        color="primary"
                    >
                        中文开始游戏
                    </Button>
                    <Button
                        onClick={() => handleLocaleChange('en')}
                        style={{ width: '225px', padding: '15px', marginTop: '20px' }}
                        variant="contained"
                        color="primary"
                    >
                        Start Game in English
                    </Button>
                </Layout.Row>
            )}
        </div>
    );
}

export default withTranslation()(DoudizhuGameBoard);
