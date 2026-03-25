import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useHistory } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Paper from '@material-ui/core/Paper';
import Button from '@material-ui/core/Button';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import PlayArrowIcon from '@material-ui/icons/PlayArrow';
import RefreshIcon from '@material-ui/icons/Refresh';
import { Layout, Loading, Message } from 'element-react';
import { douzeroDemoUrl } from '../../utils/config';
import '../../assets/gameview.scss';

function ReplayListView() {
    const { t } = useTranslation();
    const history = useHistory();
    const [replays, setReplays] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchReplays = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${douzeroDemoUrl}/list_replays`);
            if (response.data.status === 0) {
                setReplays(response.data.replays);
            } else {
                Message.error(t('failed_to_load_replays'));
            }
        } catch (error) {
            console.error('Error fetching replays:', error);
            Message.error(t('failed_to_load_replays'));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchReplays();
    }, []);

    const handlePlayReplay = (replayId) => {
        history.push(`/replay/doudizhu?replay_id=${replayId}`);
    };

    const formatDate = (timestamp) => {
        const date = new Date(timestamp * 1000);
        return date.toLocaleString();
    };

    return (
        <div className="replay-list-container" style={{ padding: '20px' }}>
            <Layout.Row style={{ marginBottom: '20px' }}>
                <Layout.Col span="24">
                    <Paper elevation={3} style={{ padding: '20px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h2 style={{ margin: 0 }}>{t('replay_list')}</h2>
                            <Button
                                variant="contained"
                                color="primary"
                                startIcon={<RefreshIcon />}
                                onClick={fetchReplays}
                                disabled={loading}
                            >
                                {t('refresh')}
                            </Button>
                        </div>
                    </Paper>
                </Layout.Col>
            </Layout.Row>

            <Layout.Row>
                <Layout.Col span="24">
                    <Paper elevation={3}>
                        <TableContainer>
                            <Table aria-label="replay list table">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>{t('replay_id')}</TableCell>
                                        <TableCell>{t('created_at')}</TableCell>
                                        <TableCell align="center">{t('actions')}</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {replays.length === 0 && !loading ? (
                                        <TableRow>
                                            <TableCell colSpan={3} align="center">
                                                {t('no_replays')}
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        replays.map((replay) => (
                                            <TableRow key={replay.replay_id}>
                                                <TableCell>{replay.replay_id}</TableCell>
                                                <TableCell>{formatDate(replay.created)}</TableCell>
                                                <TableCell align="center">
                                                    <Button
                                                        variant="outlined"
                                                        color="primary"
                                                        size="small"
                                                        startIcon={<PlayArrowIcon />}
                                                        onClick={() => handlePlayReplay(replay.replay_id)}
                                                    >
                                                        {t('play')}
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </TableContainer>
                        {loading && (
                            <div style={{ padding: '40px', textAlign: 'center' }}>
                                <Loading text={t('loading...')} />
                            </div>
                        )}
                    </Paper>
                </Layout.Col>
            </Layout.Row>
        </div>
    );
}

export default ReplayListView;
