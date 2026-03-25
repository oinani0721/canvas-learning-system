/**
 * Plugin Error Tests - Canvas Review System
 *
 * Tests for error classification and conversion utilities.
 *
 * @module tests/errors/PluginError.test
 */

import {
    PluginError,
    NetworkError,
    CanvasParseError,
    APIError,
    ValidationError,
    ConfigurationError,
    TimeoutError,
    AgentExecutionError,
    isPluginError,
    toPluginError,
    ErrorSeverity
} from '../../src/errors/PluginError';

describe('PluginError', () => {
    describe('NetworkError', () => {
        it('should create a network error with status code', () => {
            const error = new NetworkError('Connection failed', 503);

            expect(error.name).toBe('NetworkError');
            expect(error.message).toBe('Connection failed');
            expect(error.statusCode).toBe(503);
            expect(error.severity).toBe('critical');
            expect(error.recoverable).toBe(true);
        });

        it('should create a network error without status code', () => {
            const error = new NetworkError('Network unavailable');

            expect(error.statusCode).toBeUndefined();
            expect(error.severity).toBe('critical');
        });

        it('should provide user-friendly message for timeout', () => {
            const error = new NetworkError('Request timeout', 408);
            expect(error.getUserMessage()).toContain('超时');
        });

        it('should provide user-friendly message for server errors', () => {
            const error = new NetworkError('Internal server error', 500);
            expect(error.getUserMessage()).toContain('服务器');
        });

        it('should include context in toJSON', () => {
            const error = new NetworkError('Failed', 500, { url: '/api/test' });
            const json = error.toJSON();

            expect(json.context).toBeDefined();
            expect((json.context as Record<string, unknown>).url).toBe('/api/test');
        });
    });

    describe('CanvasParseError', () => {
        it('should create a canvas parse error', () => {
            const error = new CanvasParseError(
                'Invalid JSON',
                '/path/to/canvas.canvas'
            );

            expect(error.name).toBe('CanvasParseError');
            expect(error.filePath).toBe('/path/to/canvas.canvas');
            expect(error.severity).toBe('critical');
            expect(error.recoverable).toBe(false); // Parse errors are not recoverable
        });

        it('should include file path in user message', () => {
            const error = new CanvasParseError(
                'Missing nodes field',
                '/vault/test.canvas'
            );

            const message = error.getUserMessage();
            expect(message).toContain('/vault/test.canvas');
            expect(message).toContain('Missing nodes field');
        });
    });

    describe('APIError', () => {
        it('should create API error with 4xx status (non-recoverable)', () => {
            const error = new APIError(
                'Not found',
                404,
                '/api/canvas/123'
            );

            expect(error.code).toBe(404);
            expect(error.apiEndpoint).toBe('/api/canvas/123');
            expect(error.severity).toBe('warning');
            expect(error.recoverable).toBe(false);
        });

        it('should create API error with 5xx status (recoverable)', () => {
            const error = new APIError(
                'Server error',
                500,
                '/api/decompose'
            );

            expect(error.severity).toBe('critical');
            expect(error.recoverable).toBe(true);
        });

        it('should provide user-friendly messages for common codes', () => {
            expect(new APIError('', 400, '').getUserMessage()).toContain('参数无效');
            expect(new APIError('', 401, '').getUserMessage()).toContain('未授权');
            expect(new APIError('', 403, '').getUserMessage()).toContain('拒绝');
            expect(new APIError('', 404, '').getUserMessage()).toContain('未找到');
            expect(new APIError('', 429, '').getUserMessage()).toContain('频繁');
        });
    });

    describe('ValidationError', () => {
        it('should create validation error', () => {
            const error = new ValidationError(
                'Invalid color value',
                'color'
            );

            expect(error.field).toBe('color');
            expect(error.severity).toBe('warning');
            expect(error.recoverable).toBe(false);
        });

        it('should include field in user message', () => {
            const error = new ValidationError('Must be positive', 'count');
            expect(error.getUserMessage()).toContain('count');
        });
    });

    describe('ConfigurationError', () => {
        it('should create configuration error', () => {
            const error = new ConfigurationError(
                'Invalid URL format',
                'apiUrl'
            );

            expect(error.settingKey).toBe('apiUrl');
            expect(error.recoverable).toBe(false);
        });
    });

    describe('TimeoutError', () => {
        it('should create timeout error', () => {
            const error = new TimeoutError(
                'Operation timed out',
                'decompose',
                30000
            );

            expect(error.operation).toBe('decompose');
            expect(error.timeoutMs).toBe(30000);
            expect(error.recoverable).toBe(true);
        });

        it('should format timeout in user message', () => {
            const error = new TimeoutError('Timeout', 'save', 5000);
            expect(error.getUserMessage()).toContain('5秒');
        });
    });

    describe('AgentExecutionError', () => {
        it('should create agent execution error', () => {
            const error = new AgentExecutionError(
                'Agent failed to respond',
                'basic-decomposition'
            );

            expect(error.agentName).toBe('basic-decomposition');
            expect(error.severity).toBe('critical');
            expect(error.recoverable).toBe(true);
        });
    });

    describe('isPluginError', () => {
        it('should return true for PluginError instances', () => {
            expect(isPluginError(new NetworkError('test'))).toBe(true);
            expect(isPluginError(new APIError('test', 400, '/'))).toBe(true);
            expect(isPluginError(new ValidationError('test', 'field'))).toBe(true);
        });

        it('should return false for non-PluginError', () => {
            expect(isPluginError(new Error('test'))).toBe(false);
            expect(isPluginError('string error')).toBe(false);
            expect(isPluginError(null)).toBe(false);
            expect(isPluginError(undefined)).toBe(false);
        });
    });

    describe('toPluginError', () => {
        it('should return PluginError as-is', () => {
            const original = new NetworkError('test');
            const result = toPluginError(original);
            expect(result).toBe(original);
        });

        it('should wrap Error in PluginError', () => {
            const original = new Error('test error');
            const result = toPluginError(original);

            expect(isPluginError(result)).toBe(true);
            expect(result.message).toBe('test error');
        });

        it('should convert TypeError to NetworkError', () => {
            const original = new TypeError('fetch failed');
            const result = toPluginError(original);

            expect(result).toBeInstanceOf(NetworkError);
        });

        it('should wrap string errors', () => {
            const result = toPluginError('string error');
            expect(isPluginError(result)).toBe(true);
            expect(result.message).toBe('string error');
        });

        it('should use default message for unknown types', () => {
            const result = toPluginError(123, 'Default message');
            expect(result.message).toBe('Default message');
        });
    });

    describe('toJSON', () => {
        it('should serialize error to JSON', () => {
            const error = new NetworkError('test', 500, { key: 'value' });
            const json = error.toJSON();

            expect(json.name).toBe('NetworkError');
            expect(json.message).toBe('test');
            expect(json.severity).toBe('critical');
            expect(json.recoverable).toBe(true);
            expect(json.stack).toBeDefined();
        });
    });
});
