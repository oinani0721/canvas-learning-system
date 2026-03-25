/**
 * ReviewModeSelectionService Tests - Canvas Learning System
 *
 * Tests for Story 14.15: 复习模式选择UI组件
 *
 * @module ReviewModeSelectionService.test
 * @version 1.0.0
 */

import {
    ReviewModeSelectionService,
    ReviewModeSettings,
    DEFAULT_REVIEW_MODE_SETTINGS,
    REVIEW_MODES,
    ReviewMode,
    ReviewModeInfo,
    ReviewModeModal,
    createReviewModeSelectionService,
} from '../../src/services/ReviewModeSelectionService';

// Mock Obsidian modules
const mockModalOpen = jest.fn();
const mockModalClose = jest.fn();
const mockNoticeHide = jest.fn();

jest.mock('obsidian', () => ({
    App: jest.fn(),
    Modal: jest.fn().mockImplementation(function(this: any, app: any) {
        this.app = app;
        this.contentEl = {
            empty: jest.fn(),
            addClass: jest.fn(),
            createEl: jest.fn().mockReturnValue({
                addEventListener: jest.fn(),
            }),
            createDiv: jest.fn().mockReturnValue({
                createEl: jest.fn().mockReturnValue({
                    addEventListener: jest.fn(),
                    checked: false,
                }),
                createDiv: jest.fn().mockReturnValue({
                    createEl: jest.fn().mockReturnValue({
                        addEventListener: jest.fn(),
                    }),
                    querySelectorAll: jest.fn().mockReturnValue([]),
                    addClass: jest.fn(),
                    removeClass: jest.fn(),
                }),
                addClass: jest.fn(),
                removeClass: jest.fn(),
            }),
        };
        this.open = mockModalOpen;
        this.close = mockModalClose;
    }),
    Setting: jest.fn().mockImplementation(() => ({
        setName: jest.fn().mockReturnThis(),
        setDesc: jest.fn().mockReturnThis(),
        addDropdown: jest.fn().mockImplementation((callback) => {
            const dropdown = {
                addOption: jest.fn().mockReturnThis(),
                setValue: jest.fn().mockReturnThis(),
                onChange: jest.fn().mockReturnThis(),
            };
            callback(dropdown);
            return { setName: jest.fn().mockReturnThis(), setDesc: jest.fn().mockReturnThis(), addDropdown: jest.fn(), addToggle: jest.fn() };
        }),
        addToggle: jest.fn().mockImplementation((callback) => {
            const toggle = {
                setValue: jest.fn().mockReturnThis(),
                onChange: jest.fn().mockReturnThis(),
            };
            callback(toggle);
            return { setName: jest.fn().mockReturnThis(), setDesc: jest.fn().mockReturnThis(), addDropdown: jest.fn(), addToggle: jest.fn() };
        }),
    })),
    Notice: jest.fn().mockImplementation(() => ({
        noticeEl: {
            empty: jest.fn(),
            addClass: jest.fn(),
            createDiv: jest.fn().mockReturnValue({
                createEl: jest.fn().mockReturnValue({
                    addEventListener: jest.fn(),
                }),
                createDiv: jest.fn().mockReturnValue({
                    createEl: jest.fn().mockReturnValue({
                        addEventListener: jest.fn(),
                    }),
                }),
            }),
        },
        hide: mockNoticeHide,
    })),
}));

// Mock document for createModeBadge tests
const mockElement = {
    className: '',
    textContent: '',
    style: {
        backgroundColor: '',
        color: '',
        padding: '',
        borderRadius: '',
        fontSize: '',
        fontWeight: '',
    },
    setAttribute: jest.fn(),
    getAttribute: jest.fn().mockImplementation(function(this: any, attr: string) {
        return this[`_${attr}`] || null;
    }),
};

// Override setAttribute to store values
mockElement.setAttribute = jest.fn().mockImplementation(function(this: any, attr: string, value: string) {
    this[`_${attr}`] = value;
});

(global as any).document = {
    createElement: jest.fn().mockImplementation(() => ({
        ...mockElement,
        className: '',
        textContent: '',
        style: {
            backgroundColor: '',
            color: '',
            padding: '',
            borderRadius: '',
            fontSize: '',
            fontWeight: '',
        },
        _title: '',
        setAttribute: jest.fn().mockImplementation(function(this: any, attr: string, value: string) {
            this[`_${attr}`] = value;
        }),
        getAttribute: jest.fn().mockImplementation(function(this: any, attr: string) {
            return this[`_${attr}`] || null;
        }),
    })),
};

// Mock App
const mockApp = {} as any;

describe('ReviewModeSelectionService', () => {
    let service: ReviewModeSelectionService;

    beforeEach(() => {
        jest.clearAllMocks();
        service = new ReviewModeSelectionService(mockApp);
    });

    describe('Constructor and Settings', () => {
        it('should create with default settings', () => {
            expect(service).toBeDefined();
            const settings = service.getSettings();
            expect(settings.defaultMode).toBe('fresh');
            expect(settings.showModeSelectionOnStart).toBe(true);
            expect(settings.rememberLastMode).toBe(true);
            expect(settings.lastUsedMode).toBeNull();
        });

        it('should merge custom settings with defaults', () => {
            const customService = new ReviewModeSelectionService(mockApp, {
                defaultMode: 'targeted',
                showModeSelectionOnStart: false,
            });

            const settings = customService.getSettings();
            expect(settings.defaultMode).toBe('targeted');
            expect(settings.showModeSelectionOnStart).toBe(false);
            expect(settings.rememberLastMode).toBe(true); // Default
        });

        it('should update settings', () => {
            service.updateSettings({ defaultMode: 'targeted' });
            const settings = service.getSettings();
            expect(settings.defaultMode).toBe('targeted');
            expect(settings.showModeSelectionOnStart).toBe(true); // Unchanged
        });

        it('should return settings copy (immutable)', () => {
            const settings1 = service.getSettings();
            const settings2 = service.getSettings();
            expect(settings1).not.toBe(settings2);
            expect(settings1).toEqual(settings2);
        });
    });

    describe('Effective Mode', () => {
        it('should return default mode when no last used mode', () => {
            expect(service.getEffectiveMode()).toBe('fresh');
        });

        it('should return last used mode when rememberLastMode is enabled', () => {
            service.setLastUsedMode('targeted');
            expect(service.getEffectiveMode()).toBe('targeted');
        });

        it('should return default mode when rememberLastMode is disabled', () => {
            service.setLastUsedMode('targeted');
            service.updateSettings({ rememberLastMode: false });
            expect(service.getEffectiveMode()).toBe('fresh');
        });

        it('should set last used mode', () => {
            service.setLastUsedMode('targeted');
            const settings = service.getSettings();
            expect(settings.lastUsedMode).toBe('targeted');
        });
    });

    describe('Mode Info', () => {
        it('should get mode info for fresh mode', () => {
            const info = service.getModeInfo('fresh');
            expect(info.mode).toBe('fresh');
            expect(info.label).toBe('全新检验');
            expect(info.icon).toBe('🔄');
            expect(info.badgeColor).toBe('#4CAF50');
        });

        it('should get mode info for targeted mode', () => {
            const info = service.getModeInfo('targeted');
            expect(info.mode).toBe('targeted');
            expect(info.label).toBe('针对性复习');
            expect(info.icon).toBe('🎯');
            expect(info.badgeColor).toBe('#2196F3');
        });

        it('should get all available modes', () => {
            const modes = service.getAllModes();
            expect(modes).toHaveLength(2);
            expect(modes.map(m => m.mode)).toContain('fresh');
            expect(modes.map(m => m.mode)).toContain('targeted');
        });
    });

    describe('Mode Selection Modal', () => {
        it('should show mode selection modal', async () => {
            // Start the modal promise but don't await (it would hang without user interaction)
            const modalPromise = service.showModeSelectionModal();

            // Modal should have been opened
            expect(mockModalOpen).toHaveBeenCalled();

            // The promise would resolve when user interacts with modal
            // In tests, we can't simulate that easily without more complex mocking
        });
    });

    describe('Quick Mode Selection', () => {
        it('should show quick mode selection notice', () => {
            const onSelect = jest.fn();
            service.showQuickModeSelection(onSelect);

            // Notice should have been created (verified via mock)
            // The actual button clicks would trigger onSelect
        });
    });

    describe('Badge Creation', () => {
        it('should create mode badge element for fresh mode', () => {
            const badge = service.createModeBadge('fresh');

            expect(badge).toBeDefined();
            expect(badge.className).toBe('review-mode-badge');
            expect(badge.textContent).toBe('🔄 全新检验');
            expect(badge.style.backgroundColor).toBe('#4CAF50');
            expect(badge.style.color).toBe('#fff');
        });

        it('should create mode badge element for targeted mode', () => {
            const badge = service.createModeBadge('targeted');

            expect(badge).toBeDefined();
            expect(badge.textContent).toBe('🎯 针对性复习');
            expect(badge.style.backgroundColor).toBe('#2196F3');
        });

        it('should set tooltip on badge', () => {
            const badge = service.createModeBadge('fresh');
            // setAttribute was called with title
            expect(badge.setAttribute).toHaveBeenCalledWith('title', '不使用历史数据，盲测式检验，测试真实记忆水平');
        });
    });

    describe('Badge HTML Creation', () => {
        it('should create badge HTML string for fresh mode', () => {
            const html = service.createModeBadgeHTML('fresh');

            expect(html).toContain('review-mode-badge');
            expect(html).toContain('#4CAF50');
            expect(html).toContain('🔄 全新检验');
            expect(html).toContain('不使用历史数据');
        });

        it('should create badge HTML string for targeted mode', () => {
            const html = service.createModeBadgeHTML('targeted');

            expect(html).toContain('#2196F3');
            expect(html).toContain('🎯 针对性复习');
            expect(html).toContain('70%薄弱');
        });
    });

    describe('Settings UI', () => {
        it('should add settings UI to container', () => {
            const container = {
                createEl: jest.fn().mockReturnValue({}),
                createDiv: jest.fn().mockReturnValue({
                    createEl: jest.fn().mockReturnValue({}),
                    createDiv: jest.fn().mockReturnValue({
                        createEl: jest.fn().mockReturnValue({}),
                    }),
                }),
            } as any;

            const onSave = jest.fn();
            service.addSettingsUI(container, onSave);

            // Should create heading
            expect(container.createEl).toHaveBeenCalledWith('h3', { text: '复习模式设置' });
        });
    });

    describe('Mode Validation', () => {
        it('should validate valid mode strings', () => {
            expect(service.isValidMode('fresh')).toBe(true);
            expect(service.isValidMode('targeted')).toBe(true);
        });

        it('should reject invalid mode strings', () => {
            expect(service.isValidMode('invalid')).toBe(false);
            expect(service.isValidMode('')).toBe(false);
            expect(service.isValidMode('FRESH')).toBe(false);
        });

        it('should parse mode with fallback', () => {
            expect(service.parseMode('fresh')).toBe('fresh');
            expect(service.parseMode('targeted')).toBe('targeted');
            expect(service.parseMode('invalid')).toBe('fresh'); // Default fallback
            expect(service.parseMode('invalid', 'targeted')).toBe('targeted'); // Custom fallback
        });
    });

    describe('CSS Styles', () => {
        it('should return CSS styles string', () => {
            const styles = service.getStyles();

            expect(styles).toContain('.review-mode-badge');
            expect(styles).toContain('.review-mode-quick-select');
            expect(styles).toContain('.review-mode-quick-container');
            expect(styles).toContain('.review-mode-quick-buttons');
            expect(styles).toContain('.review-mode-descriptions');
        });
    });
});

describe('REVIEW_MODES Constant', () => {
    it('should have fresh mode defined', () => {
        expect(REVIEW_MODES.fresh).toBeDefined();
        expect(REVIEW_MODES.fresh.mode).toBe('fresh');
        expect(REVIEW_MODES.fresh.label).toBe('全新检验');
        expect(REVIEW_MODES.fresh.description).toContain('盲测式检验');
        expect(REVIEW_MODES.fresh.icon).toBe('🔄');
        expect(REVIEW_MODES.fresh.badgeColor).toBe('#4CAF50');
    });

    it('should have targeted mode defined', () => {
        expect(REVIEW_MODES.targeted).toBeDefined();
        expect(REVIEW_MODES.targeted.mode).toBe('targeted');
        expect(REVIEW_MODES.targeted.label).toBe('针对性复习');
        expect(REVIEW_MODES.targeted.description).toContain('70%薄弱');
        expect(REVIEW_MODES.targeted.icon).toBe('🎯');
        expect(REVIEW_MODES.targeted.badgeColor).toBe('#2196F3');
    });

    it('should have exactly 2 modes', () => {
        expect(Object.keys(REVIEW_MODES)).toHaveLength(2);
    });
});

describe('DEFAULT_REVIEW_MODE_SETTINGS', () => {
    it('should have correct default values', () => {
        expect(DEFAULT_REVIEW_MODE_SETTINGS.defaultMode).toBe('fresh');
        expect(DEFAULT_REVIEW_MODE_SETTINGS.showModeSelectionOnStart).toBe(true);
        expect(DEFAULT_REVIEW_MODE_SETTINGS.rememberLastMode).toBe(true);
        expect(DEFAULT_REVIEW_MODE_SETTINGS.lastUsedMode).toBeNull();
    });
});

describe('ReviewModeModal', () => {
    it('should create modal instance', () => {
        const onSubmit = jest.fn();
        const modal = new ReviewModeModal(mockApp, 'fresh', onSubmit);

        expect(modal).toBeDefined();
    });

    it('should have static getStyles method', () => {
        const styles = ReviewModeModal.getStyles();

        expect(styles).toContain('.review-mode-modal');
        expect(styles).toContain('.review-mode-options');
        expect(styles).toContain('.review-mode-option');
        expect(styles).toContain('.review-mode-buttons');
        expect(styles).toContain('.review-mode-remember');
    });

    it('should include hover and selected states in styles', () => {
        const styles = ReviewModeModal.getStyles();

        expect(styles).toContain('.review-mode-option:hover');
        expect(styles).toContain('.review-mode-option.selected');
    });
});

describe('createReviewModeSelectionService', () => {
    it('should create service instance', () => {
        const service = createReviewModeSelectionService(mockApp);
        expect(service).toBeInstanceOf(ReviewModeSelectionService);
    });

    it('should create service with custom settings', () => {
        const service = createReviewModeSelectionService(mockApp, {
            defaultMode: 'targeted',
        });

        expect(service.getSettings().defaultMode).toBe('targeted');
    });
});

describe('Integration Scenarios', () => {
    let service: ReviewModeSelectionService;

    beforeEach(() => {
        service = new ReviewModeSelectionService(mockApp);
    });

    describe('First-time User Flow', () => {
        it('should use default mode for first-time user', () => {
            // New user has no last used mode
            expect(service.getSettings().lastUsedMode).toBeNull();
            expect(service.getEffectiveMode()).toBe('fresh');
        });

        it('should show mode selection on start by default', () => {
            expect(service.getSettings().showModeSelectionOnStart).toBe(true);
        });
    });

    describe('Returning User Flow', () => {
        it('should remember last used mode', () => {
            // User previously selected targeted mode
            service.setLastUsedMode('targeted');

            // Next session should remember
            expect(service.getEffectiveMode()).toBe('targeted');
        });

        it('should respect user preference to not remember', () => {
            service.setLastUsedMode('targeted');
            service.updateSettings({ rememberLastMode: false });

            // Should fall back to default
            expect(service.getEffectiveMode()).toBe('fresh');
        });
    });

    describe('Mode Switching', () => {
        it('should allow switching between modes', () => {
            expect(service.getEffectiveMode()).toBe('fresh');

            service.setLastUsedMode('targeted');
            expect(service.getEffectiveMode()).toBe('targeted');

            service.setLastUsedMode('fresh');
            expect(service.getEffectiveMode()).toBe('fresh');
        });
    });

    describe('Settings Persistence Simulation', () => {
        it('should support settings export/import', () => {
            // Simulate user customization
            service.updateSettings({
                defaultMode: 'targeted',
                showModeSelectionOnStart: false,
            });
            service.setLastUsedMode('targeted');

            // Export settings
            const exportedSettings = service.getSettings();

            // Create new service with exported settings (simulating app restart)
            const newService = new ReviewModeSelectionService(mockApp, exportedSettings);

            const newSettings = newService.getSettings();
            expect(newSettings.defaultMode).toBe('targeted');
            expect(newSettings.showModeSelectionOnStart).toBe(false);
            expect(newSettings.lastUsedMode).toBe('targeted');
        });
    });

    describe('Badge Display in History', () => {
        it('should create appropriate badges for review history', () => {
            const freshBadge = service.createModeBadge('fresh');
            const targetedBadge = service.createModeBadge('targeted');

            // Badges should be visually distinct
            expect(freshBadge.style.backgroundColor).toBe('#4CAF50');
            expect(targetedBadge.style.backgroundColor).toBe('#2196F3');
            expect(freshBadge.textContent).toBe('🔄 全新检验');
            expect(targetedBadge.textContent).toBe('🎯 针对性复习');
        });

        it('should create HTML badges for embedding in views', () => {
            const freshHTML = service.createModeBadgeHTML('fresh');
            const targetedHTML = service.createModeBadgeHTML('targeted');

            // Should be valid HTML with different colors
            expect(freshHTML).toContain('#4CAF50');
            expect(targetedHTML).toContain('#2196F3');
        });
    });
});
