import axios from 'axios';
import React, { useCallback } from 'react';
import { douzeroDemoUrl } from '../../utils/config';
import { GamePlaybackView } from '../GamePlaybackView';

function AIBattleView() {
    const fetchData = useCallback(() => {
        return axios.get(`${douzeroDemoUrl}/generate_ai_battle`).then((res) => {
            if (res.data.status !== 0) {
                throw new Error(res.data.message || 'Failed to generate AI battle');
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
            startLabel="New Battle"
            errorMessage="Error in generating AI battle"
        />
    );
}

export default AIBattleView;
