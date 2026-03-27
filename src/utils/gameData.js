import {
    fullDoudizhuDeck,
    shuffleArray,
    sortDoudizhuCards,
} from './index';

/**
 * Creates a fresh set of initial game data for a new round.
 * Used by PvEDoudizhuDemoView to initialize its ref-based game state.
 */
export function createInitialGameData() {
    const shuffled = shuffleArray(fullDoudizhuDeck.slice());
    const three = shuffleArray(sortDoudizhuCards(shuffled.slice(0, 3)));
    return {
        shuffledDeck: shuffled,
        threeLandlordCards: three,
        originalThreeLandlordCards: three.slice(),
        initHands: [shuffled.slice(3, 20), shuffled.slice(20, 37), shuffled.slice(37, 54)],
        replayInitHands: null,
        playerInfo: [],
        gameHistory: [],
        bombNum: 0,
        lastMoveLandlord: [],
        lastMoveLandlordDown: [],
        lastMoveLandlordUp: [],
        playedCardsLandlord: [],
        playedCardsLandlordDown: [],
        playedCardsLandlordUp: [],
        legalActions: { turn: -1, actions: [] },
        hintIdx: -1,
        gameEndDialogTitle: '',
        moveHistory: [],
    };
}
