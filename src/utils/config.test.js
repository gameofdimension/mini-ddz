import { apiUrl, douzeroDemoUrl } from './config';

describe('utils/config.js', () => {
    describe('apiUrl', () => {
        it('should export the API URL', () => {
            expect(apiUrl).toBe('http://127.0.0.1:8000');
        });
    });

    describe('douzeroDemoUrl', () => {
        it('should export the DouZero demo URL', () => {
            expect(douzeroDemoUrl).toBe('http://127.0.0.1:5050');
        });
    });
});
