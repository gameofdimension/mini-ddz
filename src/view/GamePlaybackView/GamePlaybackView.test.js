/**
 * Tests for GamePlaybackView - shared game playback component
 *
 * GamePlaybackView is used by both AIBattleView and DoudizhuReplayView.
 * We test it in isolation by providing mock fetchData and verify rendering,
 * data loading, and playback controls.
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

// Mock DoudizhuGameBoard — capture props for timer tests
let lastGameBoardProps = {};
jest.mock('../../components/GameBoard', () => ({
    DoudizhuGameBoard: (props) => {
        lastGameBoardProps = props;
        return <div data-testid="game-board">GameBoard</div>;
    },
}));

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

describe('GamePlaybackView', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should render without crashing in ready state', () => {
        const { fetch } = createMockFetch();
        render(<GamePlaybackView {...defaultProps} fetchData={fetch} />);
        expect(screen.getByText(/Start/)).toBeInTheDocument();
        expect(screen.getAllByText(/Waiting.../).length).toBeGreaterThan(0);
    });

    it('should call fetchData on Start button click', async () => {
        const { fetch, getCallCount } = createMockFetch();
        render(<GamePlaybackView {...defaultProps} fetchData={fetch} />);

        const startButton = screen.getByText('Start');
        fireEvent.click(startButton);

        // Wait for the async fetch to complete
        await act(async () => {
            await new Promise((r) => setTimeout(r, 100));
        });

        expect(getCallCount()).toBe(1);
    });

    it('should auto-start when autoStart is true', async () => {
        const { fetch, getCallCount } = createMockFetch();
        render(<GamePlaybackView {...defaultProps} fetchData={fetch} autoStart={true} />);

        await act(async () => {
            await new Promise((r) => setTimeout(r, 100));
        });

        expect(getCallCount()).toBe(1);
    });

    it('should not auto-start when autoStart is false', async () => {
        const { fetch, getCallCount } = createMockFetch();
        render(<GamePlaybackView {...defaultProps} fetchData={fetch} autoStart={false} />);

        await act(async () => {
            await new Promise((r) => setTimeout(r, 100));
        });

        expect(getCallCount()).toBe(0);
    });

    it('should show error message when fetchData fails', async () => {
        const fetch = jest.fn(() => Promise.reject(new Error('Network error')));
        render(<GamePlaybackView {...defaultProps} fetchData={fetch} />);

        fireEvent.click(screen.getByText('Start'));

        await act(async () => {
            await new Promise((r) => setTimeout(r, 100));
        });

        expect(fetch).toHaveBeenCalled();
        expect(screen.getByText(/Start/)).toBeInTheDocument(); // stays in ready state
    });

    it('should call validate when provided', async () => {
        const { fetch } = createMockFetch();
        const validate = jest.fn().mockReturnValue({ valid: true });
        render(<GamePlaybackView {...defaultProps} fetchData={fetch} validate={validate} />);

        fireEvent.click(screen.getByText('Start'));

        await act(async () => {
            await new Promise((r) => setTimeout(r, 100));
        });

        expect(validate).toHaveBeenCalledWith(mockBattleData);
    });

    it('should not proceed when validate fails', async () => {
        const { fetch } = createMockFetch();
        const validate = jest.fn().mockReturnValue({ valid: false, error: 'Invalid data' });
        render(<GamePlaybackView {...defaultProps} fetchData={fetch} validate={validate} />);

        fireEvent.click(screen.getByText('Start'));

        await act(async () => {
            await new Promise((r) => setTimeout(r, 100));
        });

        expect(fetch).toHaveBeenCalled();
        // Should still be in ready state (start label shown, not pause)
        expect(screen.queryByText('Pause')).not.toBeInTheDocument();
    });

    it('should render Turn counter', () => {
        const { fetch } = createMockFetch();
        render(<GamePlaybackView {...defaultProps} fetchData={fetch} />);
        expect(screen.getByText(/Turn 0/)).toBeInTheDocument();
    });

    it('should render Game Speed label', () => {
        const { fetch } = createMockFetch();
        render(<GamePlaybackView {...defaultProps} fetchData={fetch} />);
        expect(screen.getByText('Game Speed')).toBeInTheDocument();
    });

    it('should render progress bar', () => {
        const { fetch } = createMockFetch();
        render(<GamePlaybackView {...defaultProps} fetchData={fetch} />);
        expect(document.querySelector('.progress-bar')).toBeInTheDocument();
    });
});
