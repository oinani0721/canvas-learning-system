/**
 * NodeColorChangeWatcher Tests - Canvas Learning System
 *
 * Tests for Story 30.6: Node Color Change Memory Trigger
 *
 * Test Coverage:
 * - Color mapping for all 4 mastery levels (Task 6.1)
 * - Color change detection / diff algorithm (Task 6.2)
 * - Debounce accumulation (Task 6.3)
 * - Batch merge logic (Task 6.4)
 * - Silent degradation on API failure (Task 6.5)
 *
 * @module NodeColorChangeWatcher.test
 * @version 1.0.0
 * @source Story 30.6: docs/stories/30.6.story.md
 */

import {
    NodeColorChangeWatcher,
    NodeColorChangeWatcherSettings,
    DEFAULT_NODE_COLOR_WATCHER_SETTINGS,
    createNodeColorChangeWatcher,
    ColorMasteryLevel,
    ColorChangeEvent,
} from '../../src/services/NodeColorChangeWatcher';
import { TFile } from '../__mocks__/obsidian';

// Mock requestUrl from Obsidian
const mockRequestUrl = jest.fn();
jest.mock('obsidian', () => ({
    ...jest.requireActual('../__mocks__/obsidian'),
    requestUrl: (...args: any[]) => mockRequestUrl(...args),
}));

// ============================================================================
// Mock App with Vault.on/offref support
// ============================================================================

interface EventRef {
    event: string;
    callback: (file: TFile) => void;
}

/**
 * Create a mock App with Vault event support
 */
function createMockApp() {
    const eventListeners: Map<string, Array<(file: TFile) => void>> = new Map();
    let eventRefCounter = 0;
    const eventRefs: Map<number, { event: string; callback: (file: TFile) => void }> = new Map();

    const mockVault = {
        _files: new Map<string, string>(),

        on: jest.fn((event: string, callback: (file: TFile) => void) => {
            if (!eventListeners.has(event)) {
                eventListeners.set(event, []);
            }
            eventListeners.get(event)!.push(callback);

            // Return an EventRef object
            const refId = ++eventRefCounter;
            eventRefs.set(refId, { event, callback });
            return refId;
        }),

        offref: jest.fn((ref: number) => {
            const eventRef = eventRefs.get(ref);
            if (eventRef) {
                const listeners = eventListeners.get(eventRef.event);
                if (listeners) {
                    const index = listeners.indexOf(eventRef.callback);
                    if (index > -1) {
                        listeners.splice(index, 1);
                    }
                }
                eventRefs.delete(ref);
            }
        }),

        read: jest.fn(async (file: TFile) => {
            const content = mockVault._files.get(file.path);
            if (content === undefined) {
                throw new Error(`File not found: ${file.path}`);
            }
            return content;
        }),

        // Test helper: trigger modify event (async to handle async callbacks)
        _triggerModify: async (file: TFile): Promise<void> => {
            const listeners = eventListeners.get('modify') || [];
            await Promise.all(listeners.map(cb => cb(file)));
        },

        // Test helper: set file content
        _setFile: (path: string, content: string) => {
            mockVault._files.set(path, content);
        },

        // Test helper: clear all
        _clear: () => {
            mockVault._files.clear();
            eventListeners.clear();
            eventRefs.clear();
        },

        // Test helper: get listener count
        _getListenerCount: (event: string) => {
            return (eventListeners.get(event) || []).length;
        },
    };

    return {
        vault: mockVault,
        workspace: {},
    } as any;
}

describe('NodeColorChangeWatcher', () => {
    let mockApp: ReturnType<typeof createMockApp>;
    let watcher: NodeColorChangeWatcher;

    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        mockApp = createMockApp();
        watcher = new NodeColorChangeWatcher(mockApp, {
            enabled: true,
            debounceMs: 100, // Short for testing
            enableLogging: false,
        });
    });

    afterEach(() => {
        watcher.stop();
        mockApp.vault._clear();
        jest.useRealTimers();
    });

    // ========================================================================
    // Task 6.1: Test color mapping for all 4 mastery levels
    // ========================================================================

    describe('Color Mapping (Task 6.1)', () => {
        it('should map red (1) to NOT_UNDERSTOOD', () => {
            // Access private method via any cast
            const level = (watcher as any).mapColorToLevel('1');
            expect(level).toBe(ColorMasteryLevel.NOT_UNDERSTOOD);
        });

        it('should map green (2) to MASTERED', () => {
            const level = (watcher as any).mapColorToLevel('2');
            expect(level).toBe(ColorMasteryLevel.MASTERED);
        });

        it('should map purple (3) to PENDING_VERIFICATION', () => {
            const level = (watcher as any).mapColorToLevel('3');
            expect(level).toBe(ColorMasteryLevel.PENDING_VERIFICATION);
        });

        it('should map yellow (6) to LEARNING', () => {
            const level = (watcher as any).mapColorToLevel('6');
            expect(level).toBe(ColorMasteryLevel.LEARNING);
        });

        it('should default to LEARNING for unknown colors (4, 5)', () => {
            expect((watcher as any).mapColorToLevel('4')).toBe(ColorMasteryLevel.LEARNING);
            expect((watcher as any).mapColorToLevel('5')).toBe(ColorMasteryLevel.LEARNING);
        });

        it('should validate color codes correctly', () => {
            expect((watcher as any).isValidColor('1')).toBe(true);
            expect((watcher as any).isValidColor('6')).toBe(true);
            expect((watcher as any).isValidColor('7')).toBe(false);
            expect((watcher as any).isValidColor('')).toBe(false);
            expect((watcher as any).isValidColor('invalid')).toBe(false);
        });
    });

    // ========================================================================
    // Task 6.2: Test color change detection (diff algorithm)
    // ========================================================================

    describe('Color Change Detection (Task 6.2)', () => {
        it('should detect new node with color', () => {
            const canvasData = {
                nodes: [{ id: 'node1', type: 'text', color: '1', text: 'Test node' }],
            };

            const changes = (watcher as any).detectColorChanges('test.canvas', canvasData);

            expect(changes).toHaveLength(1);
            expect(changes[0].nodeId).toBe('node1');
            expect(changes[0].newColor).toBe('1');
            expect(changes[0].oldColor).toBeNull();
            expect(changes[0].newLevel).toBe(ColorMasteryLevel.NOT_UNDERSTOOD);
            expect(changes[0].oldLevel).toBeNull();
        });

        it('should detect color change from red to green', () => {
            // First call: set initial state (red)
            (watcher as any).detectColorChanges('test.canvas', {
                nodes: [{ id: 'node1', type: 'text', color: '1' }],
            });

            // Second call: change color to green
            const changes = (watcher as any).detectColorChanges('test.canvas', {
                nodes: [{ id: 'node1', type: 'text', color: '2' }],
            });

            expect(changes).toHaveLength(1);
            expect(changes[0].oldColor).toBe('1');
            expect(changes[0].newColor).toBe('2');
            expect(changes[0].oldLevel).toBe(ColorMasteryLevel.NOT_UNDERSTOOD);
            expect(changes[0].newLevel).toBe(ColorMasteryLevel.MASTERED);
        });

        it('should not detect change when color is unchanged', () => {
            // First call: set initial state
            (watcher as any).detectColorChanges('test.canvas', {
                nodes: [{ id: 'node1', type: 'text', color: '1' }],
            });

            // Second call: same color
            const changes = (watcher as any).detectColorChanges('test.canvas', {
                nodes: [{ id: 'node1', type: 'text', color: '1' }],
            });

            expect(changes).toHaveLength(0);
        });

        it('should detect multiple color changes', () => {
            // First call: set initial state
            (watcher as any).detectColorChanges('test.canvas', {
                nodes: [
                    { id: 'node1', type: 'text', color: '1' },
                    { id: 'node2', type: 'text', color: '3' },
                ],
            });

            // Second call: change both colors
            const changes = (watcher as any).detectColorChanges('test.canvas', {
                nodes: [
                    { id: 'node1', type: 'text', color: '2' },
                    { id: 'node2', type: 'text', color: '6' },
                ],
            });

            expect(changes).toHaveLength(2);
            expect(changes[0].nodeId).toBe('node1');
            expect(changes[1].nodeId).toBe('node2');
        });

        it('should ignore nodes without color', () => {
            const canvasData = {
                nodes: [
                    { id: 'node1', type: 'text', text: 'No color' },
                    { id: 'node2', type: 'text', color: '1', text: 'Has color' },
                ],
            };

            const changes = (watcher as any).detectColorChanges('test.canvas', canvasData);

            expect(changes).toHaveLength(1);
            expect(changes[0].nodeId).toBe('node2');
        });

        it('should track separate state per canvas file', () => {
            // Set state for canvas1
            (watcher as any).detectColorChanges('canvas1.canvas', {
                nodes: [{ id: 'node1', color: '1' }],
            });

            // Set state for canvas2
            (watcher as any).detectColorChanges('canvas2.canvas', {
                nodes: [{ id: 'node1', color: '2' }],
            });

            // Change canvas1 - should detect change
            const changes1 = (watcher as any).detectColorChanges('canvas1.canvas', {
                nodes: [{ id: 'node1', color: '3' }],
            });
            expect(changes1).toHaveLength(1);
            expect(changes1[0].oldColor).toBe('1');

            // Change canvas2 - should detect change based on canvas2's state
            const changes2 = (watcher as any).detectColorChanges('canvas2.canvas', {
                nodes: [{ id: 'node1', color: '6' }],
            });
            expect(changes2).toHaveLength(1);
            expect(changes2[0].oldColor).toBe('2');
        });

        it('should include canvasPath in events', () => {
            const changes = (watcher as any).detectColorChanges('my-canvas.canvas', {
                nodes: [{ id: 'node1', color: '1' }],
            });

            expect(changes[0].canvasPath).toBe('my-canvas.canvas');
        });

        it('should include nodeText when available', () => {
            const changes = (watcher as any).detectColorChanges('test.canvas', {
                nodes: [{ id: 'node1', color: '1', text: 'My concept text' }],
            });

            expect(changes[0].nodeText).toBe('My concept text');
        });
    });

    // ========================================================================
    // Task 6.3: Test debounce accumulation
    // ========================================================================

    describe('Debounce Accumulation (Task 6.3)', () => {
        it('should accumulate changes during debounce window', async () => {
            const postSpy = jest.spyOn(watcher as any, 'postColorChangeEvents').mockResolvedValue(undefined);

            // Setup initial state
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));

            watcher.start();

            // Trigger first change
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            // Should have pending changes
            expect(watcher.getPendingChangesCount()).toBe(1);

            // Trigger second change before debounce timeout
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '3' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            // Should have 2 pending changes
            expect(watcher.getPendingChangesCount()).toBe(2);

            // API should not have been called yet
            expect(postSpy).not.toHaveBeenCalled();

            // Advance time past debounce
            jest.advanceTimersByTime(150);
            await Promise.resolve();

            // Now API should have been called with both changes
            expect(postSpy).toHaveBeenCalledTimes(1);
            expect(watcher.getPendingChangesCount()).toBe(0);
        });

        it('should reset debounce timer on new changes', async () => {
            const postSpy = jest.spyOn(watcher as any, 'postColorChangeEvents').mockResolvedValue(undefined);

            // Setup
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));
            watcher.start();

            // First change
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            // Advance time but not past debounce
            jest.advanceTimersByTime(50);

            // Second change - should reset timer
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '3' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            // Advance 50ms more (total 100ms from first change)
            jest.advanceTimersByTime(50);
            await Promise.resolve();

            // Should NOT have been called yet (timer was reset)
            expect(postSpy).not.toHaveBeenCalled();

            // Advance remaining time
            jest.advanceTimersByTime(100);
            await Promise.resolve();

            // Now should be called
            expect(postSpy).toHaveBeenCalledTimes(1);
        });
    });

    // ========================================================================
    // Task 6.4: Test batch merge logic
    // ========================================================================

    describe('Batch Merge Logic (Task 6.4)', () => {
        it('should batch multiple nodes from same canvas', async () => {
            const postSpy = jest.spyOn(watcher as any, 'postColorChangeEvents').mockResolvedValue(undefined);

            // Setup with multiple nodes
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [
                    { id: 'node1', color: '1' },
                    { id: 'node2', color: '1' },
                    { id: 'node3', color: '1' },
                ],
            }));
            watcher.start();

            // Change all nodes at once
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [
                    { id: 'node1', color: '2' },
                    { id: 'node2', color: '3' },
                    { id: 'node3', color: '6' },
                ],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            // Wait for debounce
            jest.advanceTimersByTime(150);
            await Promise.resolve();

            // Should be called once with all 3 changes
            expect(postSpy).toHaveBeenCalledTimes(1);
            const callArgs = postSpy.mock.calls[0][0] as ColorChangeEvent[];
            expect(callArgs).toHaveLength(3);
        });

        it('should batch changes from multiple canvases', async () => {
            const postSpy = jest.spyOn(watcher as any, 'postColorChangeEvents').mockResolvedValue(undefined);

            // Setup multiple canvases
            mockApp.vault._setFile('canvas1.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));
            mockApp.vault._setFile('canvas2.canvas', JSON.stringify({
                nodes: [{ id: 'node2', color: '1' }],
            }));
            watcher.start();

            // Change canvas1
            mockApp.vault._setFile('canvas1.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('canvas1.canvas'));

            // Change canvas2 (within debounce window)
            mockApp.vault._setFile('canvas2.canvas', JSON.stringify({
                nodes: [{ id: 'node2', color: '3' }],
            }));
            await mockApp.vault._triggerModify(new TFile('canvas2.canvas'));

            // Wait for debounce
            jest.advanceTimersByTime(150);
            await Promise.resolve();

            // Should batch both changes
            expect(postSpy).toHaveBeenCalledTimes(1);
            const callArgs = postSpy.mock.calls[0][0] as ColorChangeEvent[];
            expect(callArgs).toHaveLength(2);
            expect(callArgs.map(c => c.canvasPath)).toContain('canvas1.canvas');
            expect(callArgs.map(c => c.canvasPath)).toContain('canvas2.canvas');
        });
    });

    // ========================================================================
    // Task 6.5: Test silent degradation on API failure
    // ========================================================================

    describe('Silent Degradation (Task 6.5)', () => {
        it('should not throw on API failure', async () => {
            // Mock API failure
            mockRequestUrl.mockRejectedValue(new Error('Network error'));

            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));
            watcher.start();

            // Trigger change
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            // Wait for debounce - should not throw
            jest.advanceTimersByTime(150);
            await Promise.resolve();

            // Watcher should still be running
            expect(watcher.isActive()).toBe(true);
        });

        it('should handle timeout gracefully', async () => {
            // Create watcher with very short timeout
            watcher = new NodeColorChangeWatcher(mockApp, {
                enabled: true,
                debounceMs: 100,
                timeout: 10, // Very short timeout
                enableLogging: false,
            });

            // Mock slow API
            mockRequestUrl.mockImplementation(() =>
                new Promise(resolve => setTimeout(resolve, 1000))
            );

            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));
            watcher.start();

            // Trigger change
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            // Wait for debounce + timeout
            jest.advanceTimersByTime(200);
            await Promise.resolve();

            // Should handle timeout gracefully
            expect(watcher.isActive()).toBe(true);
        });

        it('should clear pending changes even on failure', async () => {
            mockRequestUrl.mockRejectedValue(new Error('API error'));

            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));
            watcher.start();

            // Trigger change
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            expect(watcher.getPendingChangesCount()).toBe(1);

            // Wait for debounce
            jest.advanceTimersByTime(150);
            await Promise.resolve();

            // Pending changes should be cleared even on failure
            expect(watcher.getPendingChangesCount()).toBe(0);
        });
    });

    // ========================================================================
    // Watcher Lifecycle Tests
    // ========================================================================

    describe('Watcher Lifecycle', () => {
        it('should start and register event listener', () => {
            watcher.start();

            expect(watcher.isActive()).toBe(true);
            expect(mockApp.vault.on).toHaveBeenCalledWith('modify', expect.any(Function));
        });

        it('should not start when disabled', () => {
            watcher.updateSettings({ enabled: false });
            watcher.start();

            expect(watcher.isActive()).toBe(false);
            expect(mockApp.vault.on).not.toHaveBeenCalled();
        });

        it('should not start twice', () => {
            watcher.start();
            watcher.start();

            expect(mockApp.vault.on).toHaveBeenCalledTimes(1);
        });

        it('should stop and remove event listener', () => {
            watcher.start();
            const initialListenerCount = mockApp.vault._getListenerCount('modify');
            expect(initialListenerCount).toBe(1);

            watcher.stop();

            expect(watcher.isActive()).toBe(false);
            expect(mockApp.vault.offref).toHaveBeenCalled();
        });

        it('should flush pending changes on stop', async () => {
            const postSpy = jest.spyOn(watcher as any, 'postColorChangeEvents').mockResolvedValue(undefined);

            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1' }],
            }));
            watcher.start();

            // Trigger change
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            expect(watcher.getPendingChangesCount()).toBe(1);

            // Stop should flush
            watcher.stop();
            await Promise.resolve();

            expect(postSpy).toHaveBeenCalled();
        });

        it('should clear state correctly', () => {
            // Build up some state
            (watcher as any).detectColorChanges('test.canvas', {
                nodes: [{ id: 'node1', color: '1' }],
            });
            (watcher as any).accumulateChanges([{ nodeId: 'test' } as ColorChangeEvent]);

            expect(watcher.getPendingChangesCount()).toBe(1);

            watcher.clearState();

            expect(watcher.getPendingChangesCount()).toBe(0);
        });

        it('should toggle watcher when enabled setting changes', () => {
            watcher.start();
            expect(watcher.isActive()).toBe(true);

            watcher.updateSettings({ enabled: false });
            expect(watcher.isActive()).toBe(false);

            watcher.updateSettings({ enabled: true });
            expect(watcher.isActive()).toBe(true);
        });
    });

    // ========================================================================
    // Constructor and Default Settings
    // ========================================================================

    describe('Constructor and Settings', () => {
        it('should create with default settings', () => {
            const defaultWatcher = new NodeColorChangeWatcher(mockApp);
            expect(defaultWatcher).toBeDefined();
        });

        it('should merge custom settings with defaults', () => {
            const customWatcher = new NodeColorChangeWatcher(mockApp, {
                debounceMs: 1000,
                timeout: 2000,
            });

            expect(customWatcher).toBeDefined();
        });

        it('should use factory function', () => {
            const factoryWatcher = createNodeColorChangeWatcher(mockApp, { enabled: false });
            expect(factoryWatcher).toBeDefined();
            expect(factoryWatcher.isActive()).toBe(false);
        });
    });

    // ========================================================================
    // API Payload Format Tests
    // ========================================================================

    describe('API Payload Format', () => {
        it('should format payload correctly for batch endpoint', async () => {
            mockRequestUrl.mockResolvedValue({ status: 200 });

            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '1', text: 'Test concept' }],
            }));
            watcher.start();

            // Seed initial state
            await mockApp.vault._triggerModify(new TFile('test.canvas'));
            jest.advanceTimersByTime(150);
            await Promise.resolve();
            mockRequestUrl.mockClear();

            // Trigger change
            mockApp.vault._setFile('test.canvas', JSON.stringify({
                nodes: [{ id: 'node1', color: '2', text: 'Test concept' }],
            }));
            await mockApp.vault._triggerModify(new TFile('test.canvas'));

            // Wait for debounce
            jest.advanceTimersByTime(150);
            await Promise.resolve();

            expect(mockRequestUrl).toHaveBeenCalledWith({
                url: expect.stringContaining('/memory/episodes/batch'),
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: expect.any(String),
            });

            // Parse the body
            const callArg = mockRequestUrl.mock.calls[0][0];
            const body = JSON.parse(callArg.body);

            expect(body.events).toBeDefined();
            expect(body.events).toHaveLength(1);
            expect(body.events[0].event_type).toBe('color_changed');
            expect(body.events[0].canvas_path).toBe('test.canvas');
            expect(body.events[0].node_id).toBe('node1');
            expect(body.events[0].metadata.old_color).toBe('1');
            expect(body.events[0].metadata.new_color).toBe('2');
            expect(body.events[0].metadata.old_level).toBe(ColorMasteryLevel.NOT_UNDERSTOOD);
            expect(body.events[0].metadata.new_level).toBe(ColorMasteryLevel.MASTERED);
            expect(body.events[0].metadata.node_text).toBe('Test concept');
        });
    });

    // ========================================================================
    // Edge Cases
    // ========================================================================

    describe('Edge Cases', () => {
        it('should handle empty canvas', () => {
            const changes = (watcher as any).detectColorChanges('test.canvas', {
                nodes: [],
            });
            expect(changes).toHaveLength(0);
        });

        it('should handle canvas without nodes property', () => {
            const changes = (watcher as any).detectColorChanges('test.canvas', {});
            expect(changes).toHaveLength(0);
        });

        it('should handle invalid JSON gracefully', async () => {
            mockApp.vault._setFile('test.canvas', 'not valid json');
            watcher.start();

            // Should not throw
            await mockApp.vault._triggerModify(new TFile('test.canvas'));
            await Promise.resolve();

            expect(watcher.isActive()).toBe(true);
        });

        it('should only process .canvas files', async () => {
            const postSpy = jest.spyOn(watcher as any, 'postColorChangeEvents').mockResolvedValue(undefined);

            watcher.start();

            // Trigger modify for non-canvas file
            await mockApp.vault._triggerModify(new TFile('test.md'));

            jest.advanceTimersByTime(150);
            await Promise.resolve();

            expect(postSpy).not.toHaveBeenCalled();
        });
    });
});
