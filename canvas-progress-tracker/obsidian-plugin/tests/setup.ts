/**
 * Jest Test Setup - Canvas Review System
 *
 * Global test setup and configuration.
 */

// Mock console methods to reduce noise during tests
const originalConsole = { ...console };

beforeAll(() => {
    // Suppress console output during tests
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'warn').mockImplementation(() => {});
    jest.spyOn(console, 'info').mockImplementation(() => {});
    // Keep error visible for debugging
    // jest.spyOn(console, 'error').mockImplementation(() => {});
});

afterAll(() => {
    // Restore console
    console.log = originalConsole.log;
    console.warn = originalConsole.warn;
    console.info = originalConsole.info;
});

// Global test timeout
jest.setTimeout(10000);

// Add custom matchers if needed
expect.extend({
    toBePluginError(received) {
        const pass = received && received.constructor &&
            received.constructor.prototype instanceof Error &&
            'severity' in received;

        return {
            pass,
            message: () =>
                `expected ${received} ${pass ? 'not ' : ''}to be a PluginError`
        };
    }
});

// Declare custom matchers for TypeScript
declare global {
    namespace jest {
        interface Matchers<R> {
            toBePluginError(): R;
        }
    }
}
