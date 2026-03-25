/**
 * HttpCommandExecutor - HTTP-based command executor for Claude Code API
 *
 * Implements AC-1, AC-5: HTTP command execution with retry mechanism.
 * Features:
 * - POST requests to Claude Code API
 * - Timeout control (default 30 seconds)
 * - Exponential backoff retry (max 3 retries)
 * - Request headers and authentication support
 *
 * @module HttpCommandExecutor
 * @version 1.0.0
 *
 * Source: Story 13.4 Dev Notes - HTTP Command Executor
 */

import {
  ICommandExecutor,
  ExecuteOptions,
  CommandResult,
  CommandExecutionError,
  CommandErrorCode,
} from '../types/ReviewTypes';

// ============================================================================
// Constants
// ============================================================================

/** Default timeout in milliseconds */
const DEFAULT_TIMEOUT = 30000;

/** Maximum retry attempts */
const MAX_RETRIES = 3;

/** Base delay for exponential backoff (ms) */
const BASE_RETRY_DELAY = 1000;

/** Plugin version for API requests */
const PLUGIN_VERSION = '1.0.0';

// ============================================================================
// Types
// ============================================================================

/**
 * Configuration for HttpCommandExecutor
 */
export interface HttpExecutorConfig {
  /** Base URL for the Claude Code API */
  baseUrl: string;
  /** API key for authentication (optional) */
  apiKey?: string;
  /** Default timeout in milliseconds */
  defaultTimeout?: number;
  /** Maximum retry attempts */
  maxRetries?: number;
  /** Custom headers to include */
  customHeaders?: Record<string, string>;
}

/**
 * API request payload structure
 */
interface ApiPayload {
  command: string;
  format: string;
  timeout: number;
  parseOutput: boolean;
  context: {
    source: string;
    version: string;
    [key: string]: unknown;
  };
  input?: string;
}

/**
 * API response structure
 */
interface ApiResponse {
  success: boolean;
  output?: string;
  error?: string;
  executionTime?: number;
}

// ============================================================================
// HttpCommandExecutor Class
// ============================================================================

/**
 * HTTP-based command executor for Claude Code API
 *
 * Implements the ICommandExecutor interface with support for:
 * - HTTP POST requests
 * - Timeout control
 * - Exponential backoff retry
 * - Authentication
 *
 * Source: Story 13.4 Dev Notes - HTTP Executor Implementation
 */
export class HttpCommandExecutor implements ICommandExecutor {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly defaultTimeout: number;
  private readonly maxRetries: number;
  private readonly customHeaders: Record<string, string>;

  /**
   * Create a new HttpCommandExecutor
   *
   * @param config - Executor configuration
   */
  constructor(config: HttpExecutorConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = config.apiKey;
    this.defaultTimeout = config.defaultTimeout ?? DEFAULT_TIMEOUT;
    this.maxRetries = config.maxRetries ?? MAX_RETRIES;
    this.customHeaders = config.customHeaders ?? {};
  }

  // ==========================================================================
  // Public Methods
  // ==========================================================================

  /**
   * Execute a command via HTTP API
   *
   * Implements exponential backoff retry mechanism.
   * Source: Story 13.4 Dev Notes - Retry Mechanism
   *
   * @param command - Command to execute
   * @param options - Execution options
   * @returns Command result
   * @throws CommandExecutionError if all retries fail
   */
  async execute(command: string, options?: ExecuteOptions): Promise<CommandResult> {
    const timeout = options?.timeout ?? this.defaultTimeout;
    let lastError: Error | undefined;
    let retryCount = 0;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const startTime = Date.now();
        const response = await this.attemptExecution(command, options, timeout);
        const executionTime = Date.now() - startTime;

        return {
          success: response.success,
          output: response.output,
          error: response.error,
          metadata: {
            executionTime,
            cacheHit: false,
            retryCount,
          },
        };
      } catch (error) {
        lastError = error as Error;
        retryCount = attempt;

        // Don't retry on certain errors
        if (this.isNonRetryableError(error)) {
          throw this.wrapError(error as Error);
        }

        // Wait before retry (exponential backoff)
        if (attempt < this.maxRetries) {
          const delay = this.calculateBackoffDelay(attempt);
          await this.sleep(delay);
        }
      }
    }

    // All retries exhausted
    throw new CommandExecutionError(
      `Command execution failed after ${this.maxRetries} retries: ${lastError?.message}`,
      'RETRY_EXHAUSTED',
      lastError
    );
  }

  // ==========================================================================
  // Private Methods - Execution
  // ==========================================================================

  /**
   * Attempt to execute a command
   *
   * @param command - Command to execute
   * @param options - Execution options
   * @param timeout - Request timeout
   * @returns API response
   */
  private async attemptExecution(
    command: string,
    options: ExecuteOptions | undefined,
    timeout: number
  ): Promise<ApiResponse> {
    // Validate command
    this.validateCommand(command);

    // Build request payload
    const payload = this.buildPayload(command, options, timeout);

    // Build headers
    const headers = this.buildHeaders();

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(`${this.baseUrl}/api/execute`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      // Handle HTTP errors
      if (!response.ok) {
        throw this.handleHttpError(response);
      }

      // Parse response
      const data = await response.json() as ApiResponse;
      return data;
    } catch (error) {
      // Handle abort (timeout)
      if ((error as Error).name === 'AbortError') {
        throw new CommandExecutionError(
          `Command timed out after ${timeout}ms`,
          'TIMEOUT'
        );
      }

      // Handle network errors
      if (error instanceof TypeError && (error as TypeError).message.includes('fetch')) {
        throw new CommandExecutionError(
          `Network error: ${(error as Error).message}`,
          'NETWORK_ERROR',
          error as Error
        );
      }

      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // ==========================================================================
  // Private Methods - Request Building
  // ==========================================================================

  /**
   * Validate command string
   *
   * @param command - Command to validate
   * @throws CommandExecutionError if invalid
   */
  private validateCommand(command: string): void {
    if (!command || typeof command !== 'string') {
      throw new CommandExecutionError(
        'Command must be a non-empty string',
        'VALIDATION_ERROR'
      );
    }

    // Check for potentially dangerous patterns (command injection prevention)
    const dangerousPatterns = [/[;&|`$]/, /\n/, /\r/];
    for (const pattern of dangerousPatterns) {
      if (pattern.test(command)) {
        throw new CommandExecutionError(
          'Command contains potentially dangerous characters',
          'VALIDATION_ERROR'
        );
      }
    }
  }

  /**
   * Build API request payload
   *
   * @param command - Command to execute
   * @param options - Execution options
   * @param timeout - Request timeout
   * @returns Request payload
   */
  private buildPayload(
    command: string,
    options: ExecuteOptions | undefined,
    timeout: number
  ): ApiPayload {
    const payload: ApiPayload = {
      command,
      format: 'json',
      timeout,
      parseOutput: options?.parseOutput ?? true,
      context: {
        source: 'obsidian-plugin',
        version: PLUGIN_VERSION,
        ...options?.context,
      },
    };

    if (options?.input) {
      payload.input = options.input;
    }

    return payload;
  }

  /**
   * Build request headers
   *
   * @returns Headers object
   */
  private buildHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-Client-Version': PLUGIN_VERSION,
      ...this.customHeaders,
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    return headers;
  }

  // ==========================================================================
  // Private Methods - Error Handling
  // ==========================================================================

  /**
   * Handle HTTP error responses
   *
   * @param response - Fetch response
   * @returns Error to throw
   */
  private handleHttpError(response: Response): CommandExecutionError {
    const status = response.status;
    let code: CommandErrorCode = 'UNKNOWN';
    let message = `HTTP error ${status}`;

    switch (status) {
      case 401:
      case 403:
        code = 'UNAUTHORIZED';
        message = 'Authentication failed or access denied';
        break;
      case 404:
        code = 'NOT_FOUND';
        message = 'API endpoint not found';
        break;
      case 408:
        code = 'TIMEOUT';
        message = 'Request timed out on server';
        break;
      case 500:
      case 502:
      case 503:
      case 504:
        code = 'NETWORK_ERROR';
        message = `Server error: ${status}`;
        break;
    }

    return new CommandExecutionError(message, code);
  }

  /**
   * Check if an error is non-retryable
   *
   * @param error - Error to check
   * @returns True if error should not be retried
   */
  private isNonRetryableError(error: unknown): boolean {
    if (error instanceof CommandExecutionError) {
      const nonRetryableCodes: CommandErrorCode[] = [
        'VALIDATION_ERROR',
        'UNAUTHORIZED',
        'NOT_FOUND',
      ];
      return nonRetryableCodes.includes(error.code);
    }
    return false;
  }

  /**
   * Wrap an error in CommandExecutionError
   *
   * @param error - Error to wrap
   * @returns Wrapped error
   */
  private wrapError(error: Error): CommandExecutionError {
    if (error instanceof CommandExecutionError) {
      return error;
    }
    return new CommandExecutionError(error.message, 'UNKNOWN', error);
  }

  // ==========================================================================
  // Private Methods - Utilities
  // ==========================================================================

  /**
   * Calculate exponential backoff delay
   *
   * @param attempt - Current attempt number (0-based)
   * @returns Delay in milliseconds
   */
  private calculateBackoffDelay(attempt: number): number {
    // Exponential backoff: 1s, 2s, 4s, ...
    return Math.pow(2, attempt) * BASE_RETRY_DELAY;
  }

  /**
   * Sleep for a specified duration
   *
   * @param ms - Duration in milliseconds
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// ============================================================================
// Mock Executor for Testing
// ============================================================================

/**
 * Mock command executor for testing purposes
 *
 * Source: Story 13.4 Dev Notes - Mock Testing
 */
export class MockCommandExecutor implements ICommandExecutor {
  private responses: Map<string, CommandResult> = new Map();
  private executionHistory: Array<{ command: string; options?: ExecuteOptions }> = [];

  /**
   * Set a mock response for a command
   *
   * @param command - Command to mock
   * @param response - Response to return
   */
  setResponse(command: string, response: CommandResult): void {
    this.responses.set(command, response);
  }

  /**
   * Get execution history
   *
   * @returns Array of executed commands
   */
  getExecutionHistory(): Array<{ command: string; options?: ExecuteOptions }> {
    return [...this.executionHistory];
  }

  /**
   * Clear mock responses and history
   */
  clear(): void {
    this.responses.clear();
    this.executionHistory = [];
  }

  /**
   * Execute a mocked command
   *
   * @param command - Command to execute
   * @param options - Execution options
   * @returns Mocked command result
   * @throws Error if no mock response is set
   */
  async execute(command: string, options?: ExecuteOptions): Promise<CommandResult> {
    this.executionHistory.push({ command, options });

    const response = this.responses.get(command);
    if (!response) {
      throw new CommandExecutionError(
        `No mock response set for command: ${command}`,
        'NOT_FOUND'
      );
    }

    return response;
  }
}
