/**
 * Obsidian Mock - Canvas Review System Tests
 *
 * Mock implementations of Obsidian APIs for testing.
 */

export class Notice {
    message: string;
    timeout: number;

    constructor(message: string | DocumentFragment, timeout?: number) {
        this.message = typeof message === 'string' ? message : 'Fragment';
        this.timeout = timeout || 5000;
    }

    hide(): void {}
}

export class Modal {
    app: App;
    contentEl: HTMLElement;

    constructor(app: App) {
        this.app = app;
        this.contentEl = document.createElement('div');
    }

    open(): void {}
    close(): void {}
    onOpen(): void {}
    onClose(): void {}
}

export class Plugin {
    app: App;
    manifest: PluginManifest;

    constructor(app: App, manifest: PluginManifest) {
        this.app = app;
        this.manifest = manifest;
    }

    async loadData(): Promise<any> {
        return {};
    }

    async saveData(data: any): Promise<void> {}

    addCommand(command: Command): Command {
        return command;
    }

    addRibbonIcon(icon: string, title: string, callback: () => void): HTMLElement {
        return document.createElement('div');
    }

    addSettingTab(settingTab: PluginSettingTab): void {}

    registerEvent(event: any): void {}
    registerDomEvent(el: HTMLElement, event: string, callback: Function): void {}
    registerInterval(id: number): number {
        return id;
    }
}

export class PluginSettingTab {
    app: App;
    plugin: Plugin;
    containerEl: HTMLElement;

    constructor(app: App, plugin: Plugin) {
        this.app = app;
        this.plugin = plugin;
        this.containerEl = document.createElement('div');
    }

    display(): void {}
    hide(): void {}
}

export class Setting {
    containerEl: HTMLElement;
    settingEl: HTMLElement;
    nameEl: HTMLElement;
    descEl: HTMLElement;

    constructor(containerEl: HTMLElement) {
        this.containerEl = containerEl;
        this.settingEl = document.createElement('div');
        this.nameEl = document.createElement('div');
        this.descEl = document.createElement('div');
    }

    setName(name: string): this {
        this.nameEl.textContent = name;
        return this;
    }

    setDesc(desc: string): this {
        this.descEl.textContent = desc;
        return this;
    }

    addText(cb: (text: TextComponent) => void): this {
        cb(new TextComponent(document.createElement('input')));
        return this;
    }

    addButton(cb: (button: ButtonComponent) => void): this {
        cb(new ButtonComponent(document.createElement('button')));
        return this;
    }

    addToggle(cb: (toggle: ToggleComponent) => void): this {
        cb(new ToggleComponent(document.createElement('div')));
        return this;
    }

    addDropdown(cb: (dropdown: DropdownComponent) => void): this {
        cb(new DropdownComponent(document.createElement('select')));
        return this;
    }
}

export class TextComponent {
    inputEl: HTMLInputElement;
    private value: string = '';

    constructor(containerEl: HTMLElement) {
        this.inputEl = containerEl as HTMLInputElement;
    }

    setPlaceholder(placeholder: string): this {
        this.inputEl.placeholder = placeholder;
        return this;
    }

    setValue(value: string): this {
        this.value = value;
        this.inputEl.value = value;
        return this;
    }

    getValue(): string {
        return this.value;
    }

    onChange(callback: (value: string) => void): this {
        return this;
    }
}

export class ButtonComponent {
    buttonEl: HTMLButtonElement;

    constructor(containerEl: HTMLElement) {
        this.buttonEl = containerEl as HTMLButtonElement;
    }

    setButtonText(name: string): this {
        this.buttonEl.textContent = name;
        return this;
    }

    setClass(cls: string): this {
        this.buttonEl.className = cls;
        return this;
    }

    onClick(callback: () => void): this {
        return this;
    }

    setCta(): this {
        return this;
    }
}

export class ToggleComponent {
    toggleEl: HTMLElement;
    private value: boolean = false;

    constructor(containerEl: HTMLElement) {
        this.toggleEl = containerEl;
    }

    setValue(value: boolean): this {
        this.value = value;
        return this;
    }

    getValue(): boolean {
        return this.value;
    }

    onChange(callback: (value: boolean) => void): this {
        return this;
    }
}

export class DropdownComponent {
    selectEl: HTMLSelectElement;
    private value: string = '';

    constructor(containerEl: HTMLElement) {
        this.selectEl = containerEl as HTMLSelectElement;
    }

    addOption(value: string, display: string): this {
        return this;
    }

    setValue(value: string): this {
        this.value = value;
        return this;
    }

    getValue(): string {
        return this.value;
    }

    onChange(callback: (value: string) => void): this {
        return this;
    }
}

export interface App {
    workspace: Workspace;
    vault: Vault;
}

export interface Workspace {
    getActiveFile(): TFile | null;
}

export interface Vault {
    read(file: TFile): Promise<string>;
    modify(file: TFile, data: string): Promise<void>;
}

export interface TFile {
    path: string;
    name: string;
    extension: string;
}

export interface PluginManifest {
    id: string;
    name: string;
    version: string;
    minAppVersion: string;
    description: string;
    author: string;
    authorUrl?: string;
}

export interface Command {
    id: string;
    name: string;
    callback?: () => void;
    checkCallback?: (checking: boolean) => boolean | void;
}

// Create mock app
export function createMockApp(): App {
    return {
        workspace: {
            getActiveFile: () => null
        },
        vault: {
            read: async () => '{}',
            modify: async () => {}
        }
    };
}

// Create mock plugin
export function createMockPlugin(): Plugin {
    const app = createMockApp();
    const manifest: PluginManifest = {
        id: 'canvas-review-system',
        name: 'Canvas复习系统',
        version: '1.0.0',
        minAppVersion: '0.15.0',
        description: 'Test plugin',
        author: 'Test'
    };

    return new Plugin(app, manifest);
}
