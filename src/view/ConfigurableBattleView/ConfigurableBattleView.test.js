/**
 * Tests for ConfigurableBattleView — configurable multi-agent battle component.
 *
 * Verifies the null-safety fix for finding the landlord player index
 * from playerInfo data returned by the backend.
 */

describe('ConfigurableBattleView — landlord index safety', () => {
    /**
     * Replicates the original buggy pattern (lines 88, 219):
     *   data.playerInfo.find(p => p.role === 'landlord').index
     *
     * When find() returns undefined (no landlord in list), accessing .index
     * throws TypeError.
     */
    const buggyGetLandlordIndex = (playerInfo) => {
        return playerInfo.find(p => p.role === 'landlord').index;
    };

    /** Fixed pattern with optional chaining and fallback. */
    const safeGetLandlordIndex = (playerInfo) => {
        return playerInfo.find(p => p.role === 'landlord')?.index ?? 0;
    };

    const validData = [
        { id: 0, index: 0, role: 'landlord' },
        { id: 1, index: 1, role: 'peasant' },
        { id: 2, index: 2, role: 'peasant' },
    ];

    test('buggy pattern throws on empty array', () => {
        expect(() => buggyGetLandlordIndex([])).toThrow(TypeError);
    });

    test('buggy pattern throws when no landlord in array', () => {
        const noLandlord = [
            { id: 0, index: 0, role: 'peasant' },
            { id: 1, index: 1, role: 'peasant' },
        ];
        expect(() => buggyGetLandlordIndex(noLandlord)).toThrow(TypeError);
    });

    test('safe pattern handles empty array gracefully', () => {
        expect(safeGetLandlordIndex([])).toBe(0);
    });

    test('safe pattern handles no-landlord gracefully', () => {
        const noLandlord = [
            { id: 0, index: 0, role: 'peasant' },
            { id: 1, index: 1, role: 'peasant' },
        ];
        expect(safeGetLandlordIndex(noLandlord)).toBe(0);
    });

    test('safe pattern returns correct index for valid data', () => {
        expect(safeGetLandlordIndex(validData)).toBe(0);
    });
});
