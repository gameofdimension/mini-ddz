import React, { useState, useEffect } from "react";
import AppBar from "@material-ui/core/AppBar";
import ReplayIcon from "@material-ui/icons/Replay";
import TranslateIcon from "@material-ui/icons/Translate";
import SportsEsportsIcon from "@material-ui/icons/SportsEsports";
import { useHistory } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

function Navbar() {
    const history = useHistory();
    const { i18n } = useTranslation();
    const [locale, setLocale] = useState(localStorage.getItem('LOCALE') || 'en');

    useEffect(() => {
        // Sync with localStorage on mount
        const savedLocale = localStorage.getItem('LOCALE') || 'en';
        if (savedLocale !== locale) {
            setLocale(savedLocale);
        }
    }, []);

    const handleLocaleChange = (newLocale) => {
        setLocale(newLocale);
        localStorage.setItem('LOCALE', newLocale);
        i18n.changeLanguage(newLocale);
    };

    return (
        <AppBar position="fixed" className={"header-bar-wrapper"}>
            <div className={"header-bar"}>
                <div className={"title"} onClick={() => history.push('/')} style={{ cursor: 'pointer' }}>
                    <div className={"title-text"}>Mini DDZ</div>
                </div>
                <div className={"stretch"} />
                <div className="ai-battle-info" onClick={() => history.push('/ai-battle')} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', marginRight: '20px', padding: '6px 12px', backgroundColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '4px', transition: 'background-color 0.3s' }}>
                    <div className="ai-battle-icon" style={{ marginRight: '5px' }}><SportsEsportsIcon /></div>
                    <div className="ai-battle-text" style={{ fontWeight: 'bold' }}>3 AI 对战</div>
                </div>
                <div className="replay-info" onClick={() => history.push('/replays')} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', marginRight: '20px' }}>
                    <div className="replay-icon" style={{ marginRight: '5px' }}><ReplayIcon /></div>
                    <div className="replay-text">回放</div>
                </div>
                <div className="locale-info" style={{ display: 'flex', alignItems: 'center' }}>
                    <TranslateIcon style={{ width: '1.2rem', height: '1.2rem', marginRight: '5px' }} />
                    <select
                        value={locale}
                        onChange={(e) => handleLocaleChange(e.target.value)}
                        style={{ 
                            background: 'transparent', 
                            border: '1px solid rgba(255,255,255,0.5)', 
                            color: 'white',
                            padding: '2px 5px',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        <option value="zh" style={{ color: 'black' }}>中文</option>
                        <option value="en" style={{ color: 'black' }}>English</option>
                    </select>
                </div>
            </div>
        </AppBar>
    );
}

export default Navbar;
