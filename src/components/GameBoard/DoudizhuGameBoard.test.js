import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import DoudizhuGameBoard from './DoudizhuGameBoard';

// Mock react-i18next
jest.mock('react-i18next', () => ({
    withTranslation: () => (Component) => {
        const WrappedComponent = (props) => {
            return <Component {...props} t={(key) => key} />;
        };
        WrappedComponent.displayName = `withTranslation(${Component.displayName || Component.name})`;
        return WrappedComponent;
    },
}));

// Mock images
jest.mock('../../assets/images/Portrait/Landlord_wName.png', () => 'landlord.png');
jest.mock('../../assets/images/Portrait/Peasant_wName.png', () => 'peasant.png');
jest.mock('../../assets/images/Portrait/Player.png', () => 'player.png');

const defaultProps = {
    playerInfo: [
        { id: 0, index: 0, role: 'landlord', agentInfo: { name: 'Player' } },
        { id: 1, index: 1, role: 'peasant', agentInfo: { name: 'AI1' } },
        { id: 2, index: 2, role: 'peasant', agentInfo: { name: 'AI2' } },
    ],
    hands: [
        ['S3', 'H4', 'D5'],
        ['S6', 'H7', 'D8'],
        ['S9', 'HT', 'DJ'],
    ],
    selectedCards: [],
    handleSelectedCards: jest.fn(),
    latestAction: [[], [], []],
    mainPlayerId: 0,
    currentPlayer: 0,
    considerationTime: 30000,
    turn: 1,
    toggleFade: '',
    gameStatus: 'playing',
    gamePlayable: true,
    handleMainPlayerAct: jest.fn(),
    handleSelectRole: jest.fn(),
    handleLocaleChange: jest.fn(),
    isPassDisabled: false,
    isHintDisabled: false,
    showCardBack: false,
    runNewTurn: jest.fn(),
};

describe('DoudizhuGameBoard component', () => {
    it('should render without crashing', () => {
        render(<DoudizhuGameBoard {...defaultProps} />);
        expect(document.querySelector('.doudizhu-wrapper')).toBeInTheDocument();
    });

    it('should render player portraits', () => {
        render(<DoudizhuGameBoard {...defaultProps} />);
        // Should have 3 player portraits
        const images = screen.getAllByRole('img');
        expect(images.length).toBeGreaterThan(0);
    });

    it('should render action buttons when game is playable and current player is main player', () => {
        render(<DoudizhuGameBoard {...defaultProps} />);
        expect(screen.getByText('doudizhu.hint')).toBeInTheDocument();
        expect(screen.getByText('doudizhu.pass')).toBeInTheDocument();
        expect(screen.getByText('doudizhu.play')).toBeInTheDocument();
    });

    it('should not render action buttons when game is not playable', () => {
        render(<DoudizhuGameBoard {...defaultProps} gamePlayable={false} />);
        expect(screen.queryByText('doudizhu.hint')).not.toBeInTheDocument();
    });

    it('should render timer when current player matches main player', () => {
        render(<DoudizhuGameBoard {...defaultProps} />);
        // Timer should show 30 seconds (30000ms / 1000, ceiling)
        expect(screen.getByText('30')).toBeInTheDocument();
    });

    it('should render role selection buttons when game status is ready', () => {
        render(<DoudizhuGameBoard {...defaultProps} gameStatus="ready" />);
        // Check for the landlord button text
        expect(screen.getByText('doudizhu.play_as_landlord')).toBeInTheDocument();
    });

    it('should render locale selection buttons when game status is localeSelection', () => {
        render(<DoudizhuGameBoard {...defaultProps} gameStatus="localeSelection" />);
        expect(screen.getByText('中文开始游戏')).toBeInTheDocument();
        expect(screen.getByText('Start Game in English')).toBeInTheDocument();
    });

    it('should call handleSelectRole when role button is clicked', () => {
        const handleSelectRole = jest.fn();
        render(<DoudizhuGameBoard {...defaultProps} gameStatus="ready" handleSelectRole={handleSelectRole} />);

        const landlordButton = screen.getByText('doudizhu.play_as_landlord');
        fireEvent.click(landlordButton);

        expect(handleSelectRole).toHaveBeenCalledWith('landlord');
    });

    it('should call handleLocaleChange when locale button is clicked', () => {
        const handleLocaleChange = jest.fn();
        render(<DoudizhuGameBoard {...defaultProps} gameStatus="localeSelection" handleLocaleChange={handleLocaleChange} />);

        const zhButton = screen.getByText('中文开始游戏');
        fireEvent.click(zhButton);

        expect(handleLocaleChange).toHaveBeenCalledWith('zh');
    });

    it('should call handleMainPlayerAct when play button is clicked with cards selected', () => {
        const handleMainPlayerAct = jest.fn();
        render(<DoudizhuGameBoard {...defaultProps} handleMainPlayerAct={handleMainPlayerAct} selectedCards={['S3']} />);

        const playButton = screen.getByText('doudizhu.play').closest('button');
        fireEvent.click(playButton);

        // Play button should be called with 'play' when cards are selected
        expect(handleMainPlayerAct).toHaveBeenCalledWith('play');
    });

    it('should call handleMainPlayerAct when pass button is clicked', () => {
        const handleMainPlayerAct = jest.fn();
        render(<DoudizhuGameBoard {...defaultProps} handleMainPlayerAct={handleMainPlayerAct} />);

        const passButton = screen.getByText('doudizhu.pass');
        fireEvent.click(passButton);

        expect(handleMainPlayerAct).toHaveBeenCalledWith('pass');
    });

    it('should call handleMainPlayerAct when hint button is clicked', () => {
        const handleMainPlayerAct = jest.fn();
        render(<DoudizhuGameBoard {...defaultProps} handleMainPlayerAct={handleMainPlayerAct} />);

        const hintButton = screen.getByText('doudizhu.hint');
        fireEvent.click(hintButton);

        expect(handleMainPlayerAct).toHaveBeenCalledWith('hint');
    });

    it('should display "waiting..." when playerInfo is empty', () => {
        render(<DoudizhuGameBoard {...defaultProps} playerInfo={[]} />);
        expect(screen.getAllByText('waiting...').length).toBeGreaterThan(0);
    });

    it('should display pass action correctly', () => {
        const props = {
            ...defaultProps,
            latestAction: [[], 'pass', []],
            currentPlayer: 1,
        };
        render(<DoudizhuGameBoard {...props} />);
    });

    it('should show blur background when game is ready and playable', () => {
        render(<DoudizhuGameBoard {...defaultProps} gameStatus="ready" />);
        const background = document.getElementById('gameboard-background');
        expect(background).toHaveClass('blur-background');
    });

    it('should disable play button when no cards are selected', () => {
        render(<DoudizhuGameBoard {...defaultProps} selectedCards={[]} />);
        const playButton = screen.getByText('doudizhu.play').closest('button');
        expect(playButton).toBeDisabled();
    });

    it('should enable play button when cards are selected', () => {
        render(<DoudizhuGameBoard {...defaultProps} selectedCards={['S3']} />);
        const playButton = screen.getByText('doudizhu.play').closest('button');
        expect(playButton).not.toBeDisabled();
    });
});
