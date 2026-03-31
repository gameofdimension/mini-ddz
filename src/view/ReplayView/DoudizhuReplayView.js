import axios from 'axios';
import React, { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { douzeroDemoUrl } from '../../utils/config';
import { validateReplayData } from '../../utils';
import { GamePlaybackView } from '../GamePlaybackView';

function DoudizhuReplayView() {
    const { t } = useTranslation();
    const fetchData = useCallback(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const replayId = urlParams.get('replay_id');
        if (!replayId) {
            return Promise.reject(new Error('No replay_id in URL'));
        }
        return axios.get(`${douzeroDemoUrl}/replay/${replayId}`).then((res) => {
            if (res.data.status !== 0) {
                throw new Error(res.data.message || 'Failed to load replay');
            }
            return res.data.data;
        });
    }, []);

    return (
        <GamePlaybackView
            fetchData={fetchData}
            validate={validateReplayData}
            autoStart={true}
            gameBoardProps={{}}
            startLabel={t('game_playback.restart')}
            errorMessage={t('errors.error_loading_replay')}
        />
    );
}

export default DoudizhuReplayView;
