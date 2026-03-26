import React from 'react';
import { BrowserRouter as Router, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import { PvEDoudizhuDemoView } from './view/PvEView';
import { DoudizhuReplayView } from './view/ReplayView';
import { ReplayListView } from './view/ReplayListView';
import { AIBattleView } from './view/AIBattleView';

const navbarSubtitleMap = {
    '/': 'DouDizhu',
    '/replay/doudizhu': 'Doudizhu Replay',
    '/pve/doudizhu-demo': 'Doudizhu PvE Demo',
    '/ai-battle': '3 AI Battle',
};

function App() {
    return (
        <Router>
            <Navbar subtitleMap={navbarSubtitleMap} />
            <div style={{ marginTop: '75px' }}>
                <Route exact path="/" component={PvEDoudizhuDemoView} />
                <Route exact path="/replays" component={ReplayListView} />
                <Route path="/replay/doudizhu" component={DoudizhuReplayView} />
                <Route path="/pve/doudizhu-demo" component={PvEDoudizhuDemoView} />
                <Route path="/ai-battle" component={AIBattleView} />
            </div>
        </Router>
    );
}

export default App;
