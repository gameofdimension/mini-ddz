import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

// Mock react-i18next
jest.mock('react-i18next', () => ({
    useTranslation: () => ({
        t: (key) => key,
        i18n: { changeLanguage: jest.fn() },
    }),
    withTranslation: () => (Component) => (props) => <Component {...props} t={(key) => key} />,
}));

// Mock all view components with simple text
jest.mock('./view/PvEView', () => ({
    PvEDoudizhuDemoView: () => <div data-testid="pve-view">PvE View</div>,
}));

jest.mock('./view/ReplayView', () => ({
    DoudizhuReplayView: () => <div data-testid="replay-view">Replay View</div>,
}));

jest.mock('./view/ReplayListView', () => ({
    ReplayListView: () => <div data-testid="replay-list-view">Replay List View</div>,
}));

jest.mock('./view/AIBattleView', () => ({
    AIBattleView: () => <div data-testid="ai-battle-view">AI Battle View</div>,
}));

describe('App component', () => {
    it('should render without crashing', () => {
        // Basic smoke test
        const { container } = render(<App />);
        expect(container).toBeInTheDocument();
    });

    it('should contain the Navbar with Mini DDZ title', () => {
        const { getByText } = render(<App />);
        expect(getByText('Mini DDZ')).toBeInTheDocument();
    });

    it('should contain navigation buttons', () => {
        const { getByText } = render(<App />);
        expect(getByText('nav.three_ai_battle')).toBeInTheDocument();
        expect(getByText('nav.replay')).toBeInTheDocument();
    });

    it('should contain language selector options', () => {
        const { getByText } = render(<App />);
        expect(getByText('中文')).toBeInTheDocument();
        expect(getByText('English')).toBeInTheDocument();
    });
});
