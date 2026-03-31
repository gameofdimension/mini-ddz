import { douzeroDemoUrl } from './config';

describe('utils/config.js', () => {
    describe('douzeroDemoUrl', () => {
        it('should export the DouZero demo URL', () => {
            expect(douzeroDemoUrl).toBeDefined();
        });

        it('should fall back to localhost when env var is not set', () => {
            // In test env, REACT_APP_API_URL is typically not set,
            // so it should fall back to the default
            expect(douzeroDemoUrl).toBe('http://127.0.0.1:5050');
        });
    });
});
