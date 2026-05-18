import React from 'react';
import { BrowserRouter as Router, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import { PvEDoudizhuDemoView } from './view/PvEView';
import { DoudizhuReplayView } from './view/ReplayView';
import { ReplayListView } from './view/ReplayListView';
import { LLMBattleView } from './view/LLMBattleView';
import { ConfigurableBattleView } from './view/ConfigurableBattleView';

const navbarSubtitleMap = {
    '/': 'DouDizhu',
    '/replay/doudizhu': 'Doudizhu Replay',
    '/pve/doudizhu-demo': 'Doudizhu PvE Demo',
    '/llm-battle': '3 LLM Battle',
    '/custom-battle': 'Custom Battle',
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
                <Route path="/llm-battle" component={LLMBattleView} />
                <Route path="/custom-battle" component={ConfigurableBattleView} />
            </div>
        </Router>
    );
}

export default App;
