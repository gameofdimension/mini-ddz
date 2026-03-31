import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import Navbar from './Navbar';

// Mock react-i18next
jest.mock('react-i18next', () => ({
    useTranslation: () => ({
        t: (key) => key,
        i18n: {
            changeLanguage: jest.fn(),
        },
    }),
}));

const renderWithRouter = (history) => {
    return render(
        <Router history={history}>
            <Navbar subtitleMap={{ '/': 'DouDizhu' }} />
        </Router>
    );
};

describe('Navbar component', () => {
    it('should render the title "Mini DDZ"', () => {
        const history = createMemoryHistory();
        renderWithRouter(history);
        expect(screen.getByText('Mini DDZ')).toBeInTheDocument();
    });

    it('should render the AI Battle button', () => {
        const history = createMemoryHistory();
        renderWithRouter(history);
        expect(screen.getByText('nav.three_ai_battle')).toBeInTheDocument();
    });

    it('should render the Replay button', () => {
        const history = createMemoryHistory();
        renderWithRouter(history);
        expect(screen.getByText('nav.replay')).toBeInTheDocument();
    });

    it('should render language selector', () => {
        const history = createMemoryHistory();
        renderWithRouter(history);
        const select = screen.getByRole('combobox');
        expect(select).toBeInTheDocument();
    });

    it('should have correct language options', () => {
        const history = createMemoryHistory();
        renderWithRouter(history);
        expect(screen.getByText('中文')).toBeInTheDocument();
        expect(screen.getByText('English')).toBeInTheDocument();
    });

    it('should navigate to home when title is clicked', () => {
        const history = createMemoryHistory();
        history.push('/replays');
        renderWithRouter(history);

        const title = screen.getByText('Mini DDZ');
        fireEvent.click(title);

        expect(history.location.pathname).toBe('/');
    });

    it('should navigate to AI Battle page when AI Battle button is clicked', () => {
        const history = createMemoryHistory();
        renderWithRouter(history);

        const aiBattleButton = screen.getByText('nav.three_ai_battle').closest('div');
        fireEvent.click(aiBattleButton);

        expect(history.location.pathname).toBe('/ai-battle');
    });

    it('should navigate to replays page when Replay button is clicked', () => {
        const history = createMemoryHistory();
        renderWithRouter(history);

        const replayButton = screen.getByText('nav.replay').closest('div');
        fireEvent.click(replayButton);

        expect(history.location.pathname).toBe('/replays');
    });

    it('should call localStorage.setItem when language is changed', () => {
        const history = createMemoryHistory();
        renderWithRouter(history);

        const select = screen.getByRole('combobox');
        fireEvent.change(select, { target: { value: 'zh' } });

        expect(localStorage.setItem).toHaveBeenCalledWith('LOCALE', 'zh');
    });
});
