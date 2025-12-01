/**
 * Canvas Learning System - Obsidian Plugin
 * Merged from Story 13.2 (Canvas API) + Story 13.4 (CommandWrapper)
 *
 * Main entry point for the plugin's Canvas API and Command Wrapper layers.
 *
 * @module canvas-progress-tracker
 * @version 1.0.0
 */

// ============================================================================
// Type Exports
// ============================================================================
export * from './types/canvas';
export * from './types/ReviewTypes';

// ============================================================================
// Utility Exports
// ============================================================================
export * from './utils/canvas-helpers';
export * from './utils/CommandUtils';

// ============================================================================
// Cache Exports
// ============================================================================
export { CommandCache } from './cache/CommandCache';

// ============================================================================
// Manager Exports
// ============================================================================
export { CanvasFileManager, CanvasOperationResult } from './managers/CanvasFileManager';
export { CanvasBackupManager, BackupConfig } from './managers/CanvasBackupManager';
export {
  CommandWrapper,
  createCommandWrapper,
  createMockCommandWrapper,
  type CommandWrapperConfig,
} from './managers/CommandWrapper';

// ============================================================================
// API Exports
// ============================================================================
export { CanvasNodeAPI } from './api/CanvasNodeAPI';
export { CanvasEdgeAPI } from './api/CanvasEdgeAPI';

// ============================================================================
// Executor Exports
// ============================================================================
export {
  HttpCommandExecutor,
  MockCommandExecutor,
  type HttpExecutorConfig,
} from './executors/HttpCommandExecutor';

// ============================================================================
// Parser Exports
// ============================================================================
export { ReviewOutputParser } from './parsers/ReviewOutputParser';
export { GenerateReviewOutputParser } from './parsers/GenerateReviewOutputParser';
export { CompleteReviewOutputParser } from './parsers/CompleteReviewOutputParser';
