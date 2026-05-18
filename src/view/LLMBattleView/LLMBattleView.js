import axios from 'axios';
import React, { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { douzeroDemoUrl } from '../../utils/config';
import { GamePlaybackView } from '../GamePlaybackView';

function LLMBattleView() {
    const { t } = useTranslation();
    const fetchData = useCallback(() => {
        return axios.post(`${douzeroDemoUrl}/generate_battle`, {landlord: "llm", down: "llm", up: "llm"}).then((res) => {
            if (res.data.status !== 0) {
                throw new Error(res.data.message || 'Failed to generate LLM battle');
            }
            return res.data.data;
        });
    }, []);

    return (
        <GamePlaybackView
            fetchData={fetchData}
            validate={null}
            autoStart={false}
            gameBoardProps={{ gamePlayable: false, showCardBack: false }}
            startLabel={t('game_playback.new_llm_battle')}
            errorMessage={t('errors.error_generating_battle')}
        />
    );
}

export default LLMBattleView;
