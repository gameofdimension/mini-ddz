/**
 * Tests for DoudizhuReplayView - Replay Data Validation
 *
 * Tests the validateReplayData function that checks if landlord has exactly 20 cards.
 */

import { validateReplayData } from '../../utils';

describe('validateReplayData', () => {
    const createValidReplayData = () => ({
        playerInfo: [
            { id: 0, index: 0, role: 'landlord', agentInfo: { name: 'Player' } },
            { id: 1, index: 1, role: 'peasant', agentInfo: { name: 'AI1' } },
            { id: 2, index: 2, role: 'peasant', agentInfo: { name: 'AI2' } },
        ],
        initHands: [
            // Landlord with 20 cards
            'S3 S4 S5 S6 S7 S8 S9 ST SJ SQ SK SA S2 H2 D2 C2 BJ RJ H3 H4',
            // Peasant with 17 cards
            'H5 H6 H7 H8 H9 HT HJ HQ HK HA D3 D4 D5 D6 D7 D8 D9',
            // Peasant with 17 cards
            'DT DJ DQ DK DA C3 C4 C5 C6 C7 C8 C9 CT CJ CQ CK CA',
        ],
        moveHistory: [{ playerIdx: 0, move: 'S3', info: {} }],
    });

    it('should return valid for replay data with landlord having 20 cards', () => {
        const result = validateReplayData(createValidReplayData());
        expect(result.valid).toBe(true);
        expect(result.landlordCardCount).toBe(20);
    });

    it('should return invalid when landlord has only 17 cards', () => {
        const data = createValidReplayData();
        // Remove 3 cards from landlord hand (20 -> 17)
        data.initHands[0] = 'S3 S4 S5 S6 S7 S8 S9 ST SJ SQ SK SA S2 H2 D2 C2 BJ';
        const result = validateReplayData(data);
        expect(result.valid).toBe(false);
        expect(result.landlordCardCount).toBe(17);
        expect(result.error).toContain('20 cards');
        expect(result.error).toContain('17');
    });

    it('should return invalid when landlord has 19 cards', () => {
        const data = createValidReplayData();
        // Remove 1 card from landlord hand (20 -> 19)
        data.initHands[0] = 'S3 S4 S5 S6 S7 S8 S9 ST SJ SQ SK SA S2 H2 D2 C2 BJ RJ H3';
        const result = validateReplayData(data);
        expect(result.valid).toBe(false);
        expect(result.landlordCardCount).toBe(19);
    });

    it('should return invalid when landlord has 21 cards', () => {
        const data = createValidReplayData();
        // Add 1 extra card to landlord hand (20 -> 21)
        data.initHands[0] = 'S3 S4 S5 S6 S7 S8 S9 ST SJ SQ SK SA S2 H2 D2 C2 BJ RJ H3 H4 H5';
        const result = validateReplayData(data);
        expect(result.valid).toBe(false);
        expect(result.landlordCardCount).toBe(21);
    });

    it('should handle landlord at different index positions', () => {
        const data = createValidReplayData();
        // Move landlord to index 1
        data.playerInfo = [
            { id: 0, index: 0, role: 'peasant', agentInfo: { name: 'AI1' } },
            { id: 1, index: 1, role: 'landlord', agentInfo: { name: 'Player' } },
            { id: 2, index: 2, role: 'peasant', agentInfo: { name: 'AI2' } },
        ];
        // Swap hands: landlord (20 cards) at index 1
        const temp = data.initHands[0];
        data.initHands[0] = data.initHands[1];
        data.initHands[1] = temp;

        const result = validateReplayData(data);
        expect(result.valid).toBe(true);
    });

    it('should return invalid for missing playerInfo', () => {
        const data = createValidReplayData();
        delete data.playerInfo;
        const result = validateReplayData(data);
        expect(result.valid).toBe(false);
        expect(result.error).toContain('Missing required replay data fields');
    });

    it('should return invalid for missing initHands', () => {
        const data = createValidReplayData();
        delete data.initHands;
        const result = validateReplayData(data);
        expect(result.valid).toBe(false);
        expect(result.error).toContain('Missing required replay data fields');
    });

    it('should return invalid when no landlord found', () => {
        const data = createValidReplayData();
        data.playerInfo = [
            { id: 0, index: 0, role: 'peasant', agentInfo: { name: 'AI1' } },
            { id: 1, index: 1, role: 'peasant', agentInfo: { name: 'AI2' } },
            { id: 2, index: 2, role: 'peasant', agentInfo: { name: 'AI3' } },
        ];
        const result = validateReplayData(data);
        expect(result.valid).toBe(false);
        expect(result.error).toContain('No landlord found');
    });

    it('should handle empty initHands gracefully', () => {
        const data = createValidReplayData();
        data.initHands[0] = '';
        const result = validateReplayData(data);
        expect(result.valid).toBe(false);
        expect(result.landlordCardCount).toBe(0);
    });

    it('should handle null/undefined input', () => {
        expect(validateReplayData(null).valid).toBe(false);
        expect(validateReplayData(undefined).valid).toBe(false);
        expect(validateReplayData({}).valid).toBe(false);
    });
});
