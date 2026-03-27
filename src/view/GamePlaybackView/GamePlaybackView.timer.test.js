/**
 * Timer countdown tests for GamePlaybackView
 *
 * Uses fake timers to control setTimeout and verify the two-branch
 * timer logic: decrement+reschedule during countdown, generate state
 * without rescheduling when time hits 0.
 *
 * Timing constants from GamePlaybackView:
 *   initConsiderationTime = 2000, considerationTimeDeduction = 200
 *   At speed 0: 10 ticks × 200ms countdown + 1 tick × 200ms to trigger
 *   state generation = 2200ms per turn
 */

import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';

// Mock react-i18next
jest.mock('react-i18next', () => ({
    withTranslation: () => (Component) => {
        const WrappedComponent = (props) => <Component {...props} t={(key) => key} />;
        WrappedComponent.displayName = `withTranslation(${Component.displayName || Component.name})`;
        return WrappedComponent;
    },
}));

// Mock images
jest.mock('../../assets/images/Portrait/Landlord_wName.png', () => 'landlord.png');
jest.mock('../../assets/images/Portrait/Peasant_wName.png', () => 'peasant.png');
jest.mock('../../assets/images/Portrait/Player.png', () => 'player.png');

// Mock element-react components
jest.mock('element-react', () => ({
    Layout: { Row: ({ children, ...props }) => <div {...props}>{children}</div>, Col: ({ children, ...props }) => <div {...props}>{children}</div> },
    Loading: ({ children, loading }) => <div>{loading ? 'Loading...' : children}</div>,
    Message: jest.fn(),
}));

// Mock @material-ui/core components
jest.mock('@material-ui/core/Button', () => {
    const MockButton = ({ children, onClick, startIcon, ...props }) => <button {...props} onClick={onClick}>{startIcon}{children}</button>;
    MockButton.displayName = 'Button';
    return MockButton;
});
jest.mock('@material-ui/core/Dialog', () => {
    const MockDialog = ({ children, ...props }) => props.open ? <div>{children}</div> : null;
    MockDialog.displayName = 'Dialog';
    return MockDialog;
});
jest.mock('@material-ui/core/DialogActions', () => ({ children }) => <div>{children}</div>);
jest.mock('@material-ui/core/DialogContent', () => ({ children }) => <div>{children}</div>);
jest.mock('@material-ui/core/DialogContentText', () => ({ children }) => <div>{children}</div>);
jest.mock('@material-ui/core/DialogTitle', () => ({ children }) => <div>{children}</div>);
jest.mock('@material-ui/core/Divider', () => () => <hr />);
jest.mock('@material-ui/core/LinearProgress', () => ({ value }) => <div className="linear-progress" data-value={value} />);
jest.mock('@material-ui/core/Paper', () => ({ children, className, ...props }) => <div className={className} {...props}>{children}</div>);
jest.mock('@material-ui/core/Slider', () => ({ value, onChange, marks }) => <input type="range" min={-3} max={3} value={value} onChange={onChange} />);

// Mock @material-ui/icons
jest.mock('@material-ui/icons/NotInterested', () => () => <span>NotInterested</span>);
jest.mock('@material-ui/icons/PauseCircleOutlineRounded', () => () => <span>PauseIcon</span>);
jest.mock('@material-ui/icons/PlayArrowRounded', () => () => <span>PlayIcon</span>);
jest.mock('@material-ui/icons/ReplayRounded', () => () => <span>ReplayIcon</span>);
jest.mock('@material-ui/icons/SkipNext', () => () => <span>SkipNext</span>);
jest.mock('@material-ui/icons/SkipPrevious', () => () => <span>SkipPrev</span>);

// Mock DoudizhuGameBoard — capture props for fade-out test
// Replicate the real component's useEffect that calls runNewTurn on turn change.
// Use useLayoutEffect (synchronous) instead of useEffect (async via MessageChannel)
// because fake timers don't control MessageChannel, so useEffect wouldn't fire.
let lastGameBoardProps = {};
let mockPrevTurnRef = { current: 0 };
jest.mock('../../components/GameBoard', () => {
    const React = require('react');
    return {
        DoudizhuGameBoard: (props) => {
            React.useLayoutEffect(() => {
                if (
                    props.runNewTurn &&
                    mockPrevTurnRef.current !== props.turn &&
                    props.turn !== 0 &&
                    props.gameStatus === 'playing'
                ) {
                    props.runNewTurn({ turn: mockPrevTurnRef.current });
                }
                mockPrevTurnRef.current = props.turn;
            }, [props.turn, props.gameStatus, props.runNewTurn]);
            lastGameBoardProps = props;
            return React.createElement('div', { 'data-testid': 'game-board' }, 'GameBoard');
        },
    };
});

import GamePlaybackView from './GamePlaybackView';

const mockBattleData = {
    playerInfo: [
        { id: 0, index: 0, role: 'landlord', agentInfo: { name: 'AI1' } },
        { id: 1, index: 1, role: 'peasant', agentInfo: { name: 'AI2' } },
        { id: 2, index: 2, role: 'peasant', agentInfo: { name: 'AI3' } },
    ],
    initHands: [
        'S3 S4 S5 S6 S7 S8 S9 ST SJ SQ SK SA S2 H2 D2 C2 BJ RJ H3 H4',
        'H5 H6 H7 H8 H9 HT HJ HQ HK HA D3 D4 D5 D6 D7 D8 D9',
        'DT DJ DQ DK DA C3 C4 C5 C6 C7 C8 C9 CT CJ CQ CK CA',
    ],
    moveHistory: [
        { playerIdx: 0, move: 'S3', info: {} },
        { playerIdx: 1, move: 'pass', info: {} },
        { playerIdx: 2, move: 'H5', info: {} },
    ],
};

const createMockFetch = () => {
    let callCount = 0;
    const fetch = jest.fn(() => {
        callCount++;
        return Promise.resolve(mockBattleData);
    });
    return { fetch, getCallCount: () => callCount };
};

const defaultProps = {
    autoStart: false,
    startLabel: 'Start',
    errorMessage: 'Error loading game data',
};

const startGame = async () => {
    mockPrevTurnRef.current = 0;
    const { fetch } = createMockFetch();
    render(<GamePlaybackView {...defaultProps} fetchData={fetch} />);

    // Click Start triggers loadGameData → fetchData (resolved Promise)
    // Flush microtask and React state updates inside a single act
    await act(async () => {
        fireEvent.click(screen.getByText('Start'));
        jest.runAllTicks();
    });
};

describe('Timer countdown logic', () => {
    it('should not advance turn during countdown', async () => {
        jest.useFakeTimers();
        await startGame();
        expect(screen.getByText(/Turn 0/)).toBeInTheDocument();

        // Advance one tick (200ms) — still counting down
        act(() => {
            jest.advanceTimersByTime(200);
        });

        expect(screen.getByText(/Turn 0/)).toBeInTheDocument();
        jest.useRealTimers();
    });

    it('should advance turn after full countdown cycle', async () => {
        jest.useFakeTimers();
        await startGame();

        // Full countdown: 10 ticks to reach 0 + 1 tick to trigger state generation = 2200ms
        act(() => {
            jest.advanceTimersByTime(2200);
        });

        expect(screen.getByText(/Turn 1/)).toBeInTheDocument();
        jest.useRealTimers();
    });

    it('should advance exactly one turn per cycle (no double-generation)', async () => {
        jest.useFakeTimers();
        await startGame();

        // Advance past one cycle + one extra tick
        act(() => {
            jest.advanceTimersByTime(2400);
        });

        // Turn should be exactly 1, not 2 — proves timer stops after state generation
        expect(screen.getByText(/Turn 1/)).toBeInTheDocument();
        jest.useRealTimers();
    });

    it('should progress through all 3 moves', async () => {
        jest.useFakeTimers();
        await startGame();

        // Advance one complete cycle at a time.
        // Each cycle: timer counts down (2200ms) → generates state → React re-renders
        // → useLayoutEffect calls runNewTurn → starts next cycle's timer.
        // Separate act() calls are required so React can flush re-renders between cycles.
        for (let i = 0; i < 3; i++) {
            act(() => {
                jest.advanceTimersByTime(2200);
            });
        }

        expect(screen.getByText(/Turn 3/)).toBeInTheDocument();
        jest.useRealTimers();
    });

    it('should set fade-out when considerationTime reaches 0 at speed < 2', async () => {
        jest.useFakeTimers();
        lastGameBoardProps = {};
        await startGame();

        // 10 ticks × 200ms = 2000ms — considerationTime hits 0, fade-out set
        act(() => {
            jest.advanceTimersByTime(2000);
        });

        expect(lastGameBoardProps.toggleFade).toBe('fade-out');
        jest.useRealTimers();
    });
});
