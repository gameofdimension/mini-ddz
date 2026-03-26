import {
    removeCards,
    deepCopy,
    translateCardData,
    millisecond2Second,
    debounce,
    computeHandCardsWidth,
    card2SuiteAndRank,
    fullDoudizhuDeck,
    fullDoudizhuDeckIndex,
    sortDoudizhuCards,
    isDoudizhuBomb,
    shuffleArray,
} from './index';

describe('utils/index.js', () => {
    describe('removeCards', () => {
        it('should return copy of hands when cards is "pass"', () => {
            const hands = ['S3', 'H4', 'D5'];
            const result = removeCards('pass', hands);
            expect(result).toEqual(['S3', 'H4', 'D5']);
            expect(result).not.toBe(hands); // Should be a copy
        });

        it('should remove single card from hands', () => {
            const hands = ['S3', 'H4', 'D5'];
            const result = removeCards(['H4'], hands);
            expect(result).toEqual(['S3', 'D5']);
        });

        it('should remove multiple cards from hands', () => {
            const hands = ['S3', 'H4', 'D5', 'C6'];
            const result = removeCards(['H4', 'C6'], hands);
            expect(result).toEqual(['S3', 'D5']);
        });

        it('should return false when card not in hands', () => {
            const hands = ['S3', 'H4', 'D5'];
            const result = removeCards(['S7'], hands);
            expect(result).toBe(false);
        });

        it('should return false when partially matching', () => {
            const hands = ['S3', 'H4'];
            const result = removeCards(['S3', 'H5'], hands);
            expect(result).toBe(false);
        });

        it('should handle empty cards array', () => {
            const hands = ['S3', 'H4'];
            const result = removeCards([], hands);
            expect(result).toEqual(['S3', 'H4']);
        });
    });

    describe('deepCopy', () => {
        it('should create a deep copy of an object', () => {
            const obj = { a: 1, b: { c: 2 } };
            const copy = deepCopy(obj);
            expect(copy).toEqual(obj);
            expect(copy).not.toBe(obj);
            expect(copy.b).not.toBe(obj.b);
        });

        it('should create a deep copy of an array', () => {
            const arr = [1, [2, 3], { a: 4 }];
            const copy = deepCopy(arr);
            expect(copy).toEqual(arr);
            expect(copy).not.toBe(arr);
            expect(copy[1]).not.toBe(arr[1]);
        });

        it('should handle null', () => {
            expect(deepCopy(null)).toBeNull();
        });

        it('should handle primitive values', () => {
            expect(deepCopy(42)).toBe(42);
            expect(deepCopy('string')).toBe('string');
            expect(deepCopy(true)).toBe(true);
        });
    });

    describe('translateCardData', () => {
        it('should translate Red Joker (RJ)', () => {
            const result = translateCardData('RJ');
            expect(result).toEqual(['big', 'joker', '+', 'Joker']);
        });

        it('should translate Black Joker (BJ)', () => {
            const result = translateCardData('BJ');
            expect(result).toEqual(['little', 'joker', '-', 'Joker']);
        });

        it('should translate regular cards with number rank', () => {
            const result = translateCardData('H3');
            expect(result[0]).toBe('rank-3');
            expect(result[1]).toBe('hearts');
            expect(result[2]).toBe('3');
            expect(result[3]).toBe('\u2665');
        });

        it('should translate card with T (10) rank', () => {
            const result = translateCardData('ST');
            expect(result[0]).toBe('rank-10');
            expect(result[1]).toBe('spades');
            expect(result[2]).toBe('10');
        });

        it('should translate all suits correctly', () => {
            expect(translateCardData('H5')[1]).toBe('hearts');
            expect(translateCardData('D5')[1]).toBe('diams');
            expect(translateCardData('S5')[1]).toBe('spades');
            expect(translateCardData('C5')[1]).toBe('clubs');
        });

        it('should translate face cards correctly', () => {
            const jack = translateCardData('HJ');
            expect(jack[0]).toBe('rank-j');
            expect(jack[2]).toBe('J');

            const queen = translateCardData('HQ');
            expect(queen[0]).toBe('rank-q');
            expect(queen[2]).toBe('Q');

            const king = translateCardData('HK');
            expect(king[0]).toBe('rank-k');
            expect(king[2]).toBe('K');

            const ace = translateCardData('HA');
            expect(ace[0]).toBe('rank-a');
            expect(ace[2]).toBe('A');
        });
    });

    describe('millisecond2Second', () => {
        it('should convert milliseconds to seconds (ceiling)', () => {
            expect(millisecond2Second(1000)).toBe(1);
            expect(millisecond2Second(1500)).toBe(2);
            expect(millisecond2Second(100)).toBe(1);
            expect(millisecond2Second(0)).toBe(0);
        });
    });

    describe('debounce', () => {
        beforeEach(() => {
            jest.useFakeTimers();
        });

        afterEach(() => {
            jest.useRealTimers();
        });

        it('should debounce function calls', () => {
            const mockFn = jest.fn();
            const debouncedFn = debounce(mockFn, 100);

            debouncedFn();
            debouncedFn();
            debouncedFn();

            expect(mockFn).not.toHaveBeenCalled();

            jest.advanceTimersByTime(100);

            expect(mockFn).toHaveBeenCalledTimes(1);
        });

        it('should call immediately when immediate is true', () => {
            const mockFn = jest.fn();
            const debouncedFn = debounce(mockFn, 100, true);

            debouncedFn();

            expect(mockFn).toHaveBeenCalledTimes(1);
        });

        it('should pass arguments correctly', () => {
            const mockFn = jest.fn();
            const debouncedFn = debounce(mockFn, 100);

            debouncedFn('arg1', 'arg2');
            jest.advanceTimersByTime(100);

            expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2');
        });
    });

    describe('computeHandCardsWidth', () => {
        it('should return 0 for 0 cards', () => {
            expect(computeHandCardsWidth(0, 12)).toBe(0);
        });

        it('should compute width for single card', () => {
            const result = computeHandCardsWidth(1, 12);
            expect(result).toBeGreaterThan(0);
        });

        it('should compute width for multiple cards', () => {
            const result1 = computeHandCardsWidth(5, 12);
            const result2 = computeHandCardsWidth(10, 12);
            expect(result2).toBeGreaterThan(result1);
        });
    });

    describe('card2SuiteAndRank', () => {
        it('should parse Black Joker (BJ)', () => {
            expect(card2SuiteAndRank('BJ')).toEqual({ suite: null, rank: 'X' });
        });

        it('should parse Black Joker (B)', () => {
            expect(card2SuiteAndRank('B')).toEqual({ suite: null, rank: 'X' });
        });

        it('should parse Red Joker (RJ)', () => {
            expect(card2SuiteAndRank('RJ')).toEqual({ suite: null, rank: 'D' });
        });

        it('should parse Red Joker (R)', () => {
            expect(card2SuiteAndRank('R')).toEqual({ suite: null, rank: 'D' });
        });

        it('should parse regular card', () => {
            expect(card2SuiteAndRank('H5')).toEqual({ suite: 'H', rank: '5' });
            expect(card2SuiteAndRank('ST')).toEqual({ suite: 'S', rank: 'T' });
        });
    });

    describe('fullDoudizhuDeck', () => {
        it('should contain 54 cards', () => {
            expect(fullDoudizhuDeck).toHaveLength(54);
        });

        it('should contain both jokers', () => {
            expect(fullDoudizhuDeck).toContain('RJ');
            expect(fullDoudizhuDeck).toContain('BJ');
        });
    });

    describe('fullDoudizhuDeckIndex', () => {
        it('should have index for all cards', () => {
            expect(Object.keys(fullDoudizhuDeckIndex)).toHaveLength(54);
        });

        it('should have RJ as highest (54) and D3 as lowest (1)', () => {
            expect(fullDoudizhuDeckIndex['RJ']).toBe(54);
            expect(fullDoudizhuDeckIndex['D3']).toBe(1);
        });
    });

    describe('sortDoudizhuCards', () => {
        it('should sort cards in descending order by default', () => {
            const cards = ['S3', 'RJ', 'H5'];
            const result = sortDoudizhuCards(cards);
            expect(result[0]).toBe('RJ');
            expect(result[2]).toBe('S3');
        });

        it('should sort cards in ascending order when specified', () => {
            const cards = ['RJ', 'S3', 'H5'];
            const result = sortDoudizhuCards(cards, true);
            expect(result[0]).toBe('S3');
            expect(result[2]).toBe('RJ');
        });

        it('should not modify original array', () => {
            const cards = ['S3', 'RJ', 'H5'];
            const originalOrder = [...cards];
            sortDoudizhuCards(cards);
            expect(cards).toEqual(originalOrder);
        });
    });

    describe('isDoudizhuBomb', () => {
        it('should identify rocket (joker bomb) - RJ + BJ', () => {
            expect(isDoudizhuBomb(['RJ', 'BJ'])).toBe(true);
            expect(isDoudizhuBomb(['BJ', 'RJ'])).toBe(true);
        });

        it('should identify four-of-a-kind bomb', () => {
            expect(isDoudizhuBomb(['S3', 'H3', 'D3', 'C3'])).toBe(true);
            expect(isDoudizhuBomb(['SA', 'HA', 'DA', 'CA'])).toBe(true);
        });

        it('should return false for non-bomb cards', () => {
            expect(isDoudizhuBomb(['S3', 'H4'])).toBe(false);
            expect(isDoudizhuBomb(['S3', 'H3', 'D3'])).toBe(false);
            expect(isDoudizhuBomb(['S3'])).toBe(false);
            expect(isDoudizhuBomb(['RJ', 'S3'])).toBe(false);
        });

        it('should return false for invalid lengths', () => {
            expect(isDoudizhuBomb(['S3'])).toBe(false);
            expect(isDoudizhuBomb(['S3', 'H3', 'D3'])).toBe(false);
            expect(isDoudizhuBomb(['S3', 'H3', 'D3', 'C3', 'S4'])).toBe(false);
        });
    });

    describe('shuffleArray', () => {
        it('should return an array of same length', () => {
            const arr = [1, 2, 3, 4, 5];
            const shuffled = shuffleArray(arr);
            expect(shuffled).toHaveLength(arr.length);
        });

        it('should contain all original elements', () => {
            const arr = [1, 2, 3, 4, 5];
            const shuffled = shuffleArray(arr);
            expect(shuffled.sort()).toEqual(arr.sort());
        });

        it('should not modify original array', () => {
            const arr = [1, 2, 3, 4, 5];
            const originalArr = [...arr];
            shuffleArray(arr);
            expect(arr).toEqual(originalArr);
        });

        it('should handle empty array', () => {
            expect(shuffleArray([])).toEqual([]);
        });

        it('should handle single element array', () => {
            expect(shuffleArray([1])).toEqual([1]);
        });
    });
});
