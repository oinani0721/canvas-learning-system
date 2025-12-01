/**
 * Canvas Review System - Manager Index
 *
 * Exports for manager classes:
 * - Story 13.2: DataManager (placeholder), CanvasFileManager, CanvasBackupManager
 * - Story 13.3: CommandWrapper
 * - Story 13.4: UIManager
 * - Story 13.5: ContextMenuManager, BackupProtectionManager, HotkeyManager
 *
 * @module managers
 * @version 1.1.0
 */

// Story 13.2 Managers
export { CanvasFileManager } from './CanvasFileManager';
export { CanvasBackupManager } from './CanvasBackupManager';

// Story 13.4 Managers
export { CommandWrapper, createCommandWrapper, createMockCommandWrapper } from './CommandWrapper';

// Story 13.5 Managers
export { ContextMenuManager } from './ContextMenuManager';
export type { MenuActionRegistry, MenuActionCallback } from './ContextMenuManager';
export { BackupProtectionManager } from './BackupProtectionManager';
export { HotkeyManager, RECOMMENDED_HOTKEYS, formatHotkey } from './HotkeyManager';
export type { CommandCallback, EditorCheckCallback } from './HotkeyManager';

// Placeholder interfaces for future implementations

/**
 * DataManager interface - Story 13.2
 */
export interface IDataManager {
    initialize(): Promise<void>;
    cleanup(): void;
}

/**
 * CommandWrapper interface - Story 13.3
 */
export interface ICommandWrapper {
    initialize(): Promise<void>;
    cleanup(): void;
    executeCommand(command: string, args?: Record<string, unknown>): Promise<unknown>;
}

/**
 * UIManager interface - Story 13.4
 */
export interface IUIManager {
    initialize(): Promise<void>;
    cleanup(): void;
    showDashboard(): void;
}

/**
 * SyncManager interface - Story 13.5
 */
export interface ISyncManager {
    initialize(): Promise<void>;
    cleanup(): void;
    startAutoSync(intervalMs: number): void;
    stopAutoSync(): void;
    syncNow(): Promise<void>;
}

// Export placeholder classes (to be replaced in future stories)
export class DataManager implements IDataManager {
    async initialize(): Promise<void> {
        console.log('DataManager: Placeholder initialized');
    }
    cleanup(): void {
        console.log('DataManager: Placeholder cleanup');
    }
}

// Note: CommandWrapper exported from ./CommandWrapper (Story 13.4 - real impl)

export class UIManager implements IUIManager {
    async initialize(): Promise<void> {
        console.log('UIManager: Placeholder initialized');
    }
    cleanup(): void {
        console.log('UIManager: Placeholder cleanup');
    }
    showDashboard(): void {
        console.log('UIManager: Placeholder showDashboard');
    }
}

export class SyncManager implements ISyncManager {
    private intervalId: number | null = null;

    async initialize(): Promise<void> {
        console.log('SyncManager: Placeholder initialized');
    }
    cleanup(): void {
        this.stopAutoSync();
        console.log('SyncManager: Placeholder cleanup');
    }
    startAutoSync(intervalMs: number): void {
        console.log(`SyncManager: Placeholder startAutoSync ${intervalMs}ms`);
    }
    stopAutoSync(): void {
        if (this.intervalId !== null) {
            window.clearInterval(this.intervalId);
            this.intervalId = null;
        }
        console.log('SyncManager: Placeholder stopAutoSync');
    }
    async syncNow(): Promise<void> {
        console.log('SyncManager: Placeholder syncNow');
    }
}
