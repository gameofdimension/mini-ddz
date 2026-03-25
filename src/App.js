import React from 'react';
import { BrowserRouter as Router, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import { PvEDoudizhuDemoView } from './view/PvEView';
import { DoudizhuReplayView } from './view/ReplayView';

const navbarSubtitleMap = {
    '/': 'DouDizhu',
    '/replay/doudizhu': 'Doudizhu Replay',
    '/pve/doudizhu-demo': 'Doudizhu PvE Demo',
};

function App() {
    return (
        <Router>
            <Navbar subtitleMap={navbarSubtitleMap} />
            <div style={{ marginTop: '75px' }}>
                <Route exact path="/" component={PvEDoudizhuDemoView} />
                <Route path="/replay/doudizhu" component={DoudizhuReplayView} />
                <Route path="/pve/doudizhu-demo" component={PvEDoudizhuDemoView} />
            </div>
        </Router>
    );
}

export default App;
