/**
 * Canvas Learning System - Plugin Settings Type Definitions
 *
 * Settings interface for the Obsidian plugin configuration.
 *
 * @source Story 13.3 - 插件设置集成
 */

/**
 * Plugin settings interface
 * @source Story 13.3 Dev Notes - 插件设置集成
 */
export interface CanvasReviewPluginSettings {
  /**
   * Base URL for the FastAPI backend
   * @default 'http://localhost:8000/api/v1'
   */
  apiBaseUrl: string;

  /**
   * Request timeout in milliseconds
   * @default 30000
   */
  requestTimeout: number;

  /**
   * Maximum number of retries for failed requests
   * @default 3
   */
  maxRetries: number;

  /**
   * Base delay for retry backoff in milliseconds
   * @default 1000
   */
  retryBackoffMs: number;

  /**
   * Whether to show notifications for API errors
   * @default true
   */
  showErrorNotifications: boolean;

  /**
   * Whether to enable debug logging
   * @default false
   */
  debugMode: boolean;
}

/**
 * Default plugin settings
 * @source Story 13.3 Dev Notes - 默认配置
 */
export const DEFAULT_SETTINGS: CanvasReviewPluginSettings = {
  apiBaseUrl: 'http://localhost:8000/api/v1',
  requestTimeout: 30000,
  maxRetries: 3,
  retryBackoffMs: 1000,
  showErrorNotifications: true,
  debugMode: false,
};
