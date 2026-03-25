/**
 * ApiError Tests - Canvas Review System
 *
 * Tests for ApiError class and isRetryable functionality.
 *
 * @source Story 21.5.5 - AC 3: 可重试错误提供重试按钮
 * @source ADR-009: RETRYABLE_ERROR_TYPES
 * @module tests/api/ApiError.test
 */

import { ApiError, ErrorType } from '../../src/api/types';

describe('ApiError', () => {
  describe('constructor', () => {
    it('should create error with all parameters', () => {
      const error = new ApiError(
        'Server error occurred',
        'HttpError5xx',
        500,
        { endpoint: '/api/test' },
        'BUG-12345678',
        'AIProviderError'
      );

      expect(error.name).toBe('ApiError');
      expect(error.message).toBe('Server error occurred');
      expect(error.type).toBe('HttpError5xx');
      expect(error.statusCode).toBe(500);
      expect(error.details).toEqual({ endpoint: '/api/test' });
      expect(error.bugId).toBe('BUG-12345678');
      expect(error.backendErrorType).toBe('AIProviderError');
    });

    it('should create error with minimal parameters', () => {
      const error = new ApiError('Simple error', 'UnknownError');

      expect(error.message).toBe('Simple error');
      expect(error.type).toBe('UnknownError');
      expect(error.statusCode).toBeUndefined();
      expect(error.details).toBeUndefined();
      expect(error.bugId).toBeUndefined();
      expect(error.backendErrorType).toBeUndefined();
    });

    it('should be instanceof Error', () => {
      const error = new ApiError('Test', 'NetworkError');
      expect(error).toBeInstanceOf(Error);
    });

    it('should be instanceof ApiError', () => {
      const error = new ApiError('Test', 'NetworkError');
      expect(error).toBeInstanceOf(ApiError);
    });
  });

  describe('isRetryable - AC3', () => {
    it('should return true for NetworkError', () => {
      const error = new ApiError('Network failed', 'NetworkError');
      expect(error.isRetryable).toBe(true);
    });

    it('should return true for TimeoutError', () => {
      const error = new ApiError('Request timeout', 'TimeoutError');
      expect(error.isRetryable).toBe(true);
    });

    it('should return true for HttpError5xx', () => {
      const error = new ApiError('Internal server error', 'HttpError5xx', 500);
      expect(error.isRetryable).toBe(true);
    });

    it('should return false for HttpError4xx', () => {
      const error = new ApiError('Bad request', 'HttpError4xx', 400);
      expect(error.isRetryable).toBe(false);
    });

    it('should return false for ValidationError', () => {
      const error = new ApiError('Invalid data', 'ValidationError');
      expect(error.isRetryable).toBe(false);
    });

    it('should return false for UnknownError', () => {
      const error = new ApiError('Unknown', 'UnknownError');
      expect(error.isRetryable).toBe(false);
    });
  });

  describe('isRetryable comprehensive tests', () => {
    const retryableTypes: ErrorType[] = ['NetworkError', 'TimeoutError', 'HttpError5xx'];
    const nonRetryableTypes: ErrorType[] = ['HttpError4xx', 'ValidationError', 'UnknownError'];

    retryableTypes.forEach((type) => {
      it(`should return true for ${type}`, () => {
        const error = new ApiError(`Test ${type}`, type);
        expect(error.isRetryable).toBe(true);
      });
    });

    nonRetryableTypes.forEach((type) => {
      it(`should return false for ${type}`, () => {
        const error = new ApiError(`Test ${type}`, type);
        expect(error.isRetryable).toBe(false);
      });
    });
  });

  describe('getUserFriendlyMessage', () => {
    it('should return friendly message for NetworkError', () => {
      const error = new ApiError('Connection refused', 'NetworkError');
      expect(error.getUserFriendlyMessage()).toContain('无法连接到服务器');
    });

    it('should return friendly message for TimeoutError', () => {
      const error = new ApiError('Timeout', 'TimeoutError');
      expect(error.getUserFriendlyMessage()).toContain('超时');
    });

    it('should return friendly message for HttpError4xx', () => {
      const error = new ApiError('Not found', 'HttpError4xx', 404);
      expect(error.getUserFriendlyMessage()).toContain('请求参数错误');
    });

    it('should return friendly message for HttpError5xx', () => {
      const error = new ApiError('Internal error', 'HttpError5xx', 500);
      expect(error.getUserFriendlyMessage()).toContain('服务器错误');
    });

    it('should return friendly message for ValidationError', () => {
      const error = new ApiError('Invalid', 'ValidationError', undefined, { field: 'email' });
      expect(error.getUserFriendlyMessage()).toContain('数据验证失败');
    });

    it('should include backend error type prefix when present', () => {
      const error = new ApiError(
        'AI failed',
        'HttpError5xx',
        500,
        undefined,
        undefined,
        'AIProviderError'
      );
      expect(error.getUserFriendlyMessage()).toContain('[AIProviderError]');
    });

    it('should not include prefix when backend error type is missing', () => {
      const error = new ApiError('Server error', 'HttpError5xx', 500);
      expect(error.getUserFriendlyMessage()).not.toContain('[');
    });
  });

  describe('getFormattedMessage', () => {
    it('should include bug_id when present', () => {
      const error = new ApiError(
        'Server error',
        'HttpError5xx',
        500,
        undefined,
        'BUG-ABCD1234'
      );

      const formatted = error.getFormattedMessage();
      expect(formatted).toContain('[Bug ID: BUG-ABCD1234]');
    });

    it('should not include bug_id when not present', () => {
      const error = new ApiError('Network error', 'NetworkError');

      const formatted = error.getFormattedMessage();
      expect(formatted).not.toContain('Bug ID');
    });

    it('should include user friendly message', () => {
      const error = new ApiError('Network failed', 'NetworkError');

      const formatted = error.getFormattedMessage();
      expect(formatted).toContain('无法连接到服务器');
    });
  });

  describe('specific HTTP status codes', () => {
    const statusCodes = [
      { status: 400, type: 'HttpError4xx' as ErrorType, retryable: false },
      { status: 401, type: 'HttpError4xx' as ErrorType, retryable: false },
      { status: 403, type: 'HttpError4xx' as ErrorType, retryable: false },
      { status: 404, type: 'HttpError4xx' as ErrorType, retryable: false },
      { status: 422, type: 'HttpError4xx' as ErrorType, retryable: false },
      { status: 429, type: 'HttpError4xx' as ErrorType, retryable: false },
      { status: 500, type: 'HttpError5xx' as ErrorType, retryable: true },
      { status: 502, type: 'HttpError5xx' as ErrorType, retryable: true },
      { status: 503, type: 'HttpError5xx' as ErrorType, retryable: true },
      { status: 504, type: 'HttpError5xx' as ErrorType, retryable: true },
    ];

    statusCodes.forEach(({ status, type, retryable }) => {
      it(`should handle HTTP ${status} correctly`, () => {
        const error = new ApiError(`HTTP ${status}`, type, status);

        expect(error.statusCode).toBe(status);
        expect(error.isRetryable).toBe(retryable);
      });
    });
  });

  describe('prototype chain', () => {
    it('should maintain prototype chain for instanceof checks', () => {
      const error = new ApiError('Test', 'NetworkError');

      // These should all work due to Object.setPrototypeOf
      expect(error instanceof ApiError).toBe(true);
      expect(error instanceof Error).toBe(true);
    });

    it('should have proper error name', () => {
      const error = new ApiError('Test', 'NetworkError');
      expect(error.name).toBe('ApiError');
    });

    it('should have stack trace', () => {
      const error = new ApiError('Test', 'NetworkError');
      expect(error.stack).toBeDefined();
    });
  });
});
