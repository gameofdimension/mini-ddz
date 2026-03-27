import { douzeroDemoUrl } from './config';

describe('utils/config.js', () => {
    describe('douzeroDemoUrl', () => {
        it('should export the DouZero demo URL', () => {
            expect(douzeroDemoUrl).toBe('http://127.0.0.1:5050');
        });
    });
});
