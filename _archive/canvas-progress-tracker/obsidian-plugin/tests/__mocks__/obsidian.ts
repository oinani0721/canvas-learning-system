/**
 * Obsidian API Mock for Testing
 * Story 13.2: Canvas API集成
 *
 * Mocks the Obsidian API types and classes used in the Canvas API layer.
 */

// Mock TFile class
export class TFile {
  path: string;
  basename: string;
  extension: string;
  name: string;
  stat: { mtime: number; ctime: number; size: number };
  vault: any = null; // Added for compatibility
  parent: TFolder | null = null; // Added for compatibility

  constructor(path: string) {
    this.path = path;
    const parts = path.split('/');
    const filename = parts[parts.length - 1];
    this.name = filename;
    const nameParts = filename.split('.');
    this.extension = nameParts.pop() || '';
    this.basename = nameParts.join('.');
    this.stat = { mtime: Date.now(), ctime: Date.now(), size: 1024 };
  }
}

// Mock TFolder class
export class TFolder {
  path: string;
  name: string;
  children: (TFile | TFolder)[] = [];
  vault: any = null;
  parent: TFolder | null = null;

  constructor(path: string) {
    this.path = path;
    const parts = path.split('/');
    this.name = parts[parts.length - 1] || '';
  }

  isRoot(): boolean {
    return this.path === '' || this.path === '/';
  }
}

// Mock TAbstractFile
export class TAbstractFile {
  path: string;

  constructor(path: string) {
    this.path = path;
  }
}

// Mock Vault class
export class Vault {
  private files: Map<string, string> = new Map();
  private folders: Set<string> = new Set();

  async read(file: TFile): Promise<string> {
    const content = this.files.get(file.path);
    if (content === undefined) {
      throw new Error(`File not found: ${file.path}`);
    }
    return content;
  }

  async modify(file: TFile, content: string): Promise<void> {
    if (!this.files.has(file.path)) {
      throw new Error(`File not found: ${file.path}`);
    }
    this.files.set(file.path, content);
  }

  async create(path: string, content: string): Promise<TFile> {
    if (this.files.has(path)) {
      throw new Error(`File already exists: ${path}`);
    }
    this.files.set(path, content);
    return new TFile(path);
  }

  async delete(file: TAbstractFile): Promise<void> {
    this.files.delete(file.path);
    this.folders.delete(file.path);
  }

  async createFolder(path: string): Promise<void> {
    this.folders.add(path);
  }

  getAbstractFileByPath(path: string): TAbstractFile | null {
    if (this.files.has(path)) {
      return new TFile(path);
    }
    if (this.folders.has(path)) {
      return new TFolder(path);
    }
    return null;
  }

  // Test helpers
  _setFile(path: string, content: string): void {
    this.files.set(path, content);
  }

  _setFolder(path: string): void {
    this.folders.add(path);
  }

  _clear(): void {
    this.files.clear();
    this.folders.clear();
  }
}

// Mock Notice class
export class Notice {
  message: string;
  duration?: number;

  constructor(message: string, duration?: number) {
    this.message = message;
    this.duration = duration;
    // In tests, we might want to capture notices
    console.log(`[Notice] ${message}`);
  }
}

// Mock Events class
export class Events {
  private events: Map<string, Function[]> = new Map();

  on(name: string, callback: Function): void {
    if (!this.events.has(name)) {
      this.events.set(name, []);
    }
    this.events.get(name)!.push(callback);
  }

  off(name: string, callback: Function): void {
    const callbacks = this.events.get(name);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  trigger(name: string, ...data: any[]): void {
    const callbacks = this.events.get(name);
    if (callbacks) {
      callbacks.forEach((cb) => cb(...data));
    }
  }
}

// Mock Plugin class
export class Plugin {
  app: any;
  private _pluginData: Record<string, unknown> = {};

  constructor() {
    this.app = {
      vault: new Vault(),
      workspace: {},
    };
  }

  onload(): void {}
  onunload(): void {}

  addCommand(command: any): void {}
  addRibbonIcon(icon: string, title: string, callback: () => void): void {}
  registerEvent(event: any): void {}

  // Story 21.5.5: loadData/saveData for ErrorHistoryManager
  async loadData(): Promise<Record<string, unknown> | null> {
    return this._pluginData;
  }

  async saveData(data: Record<string, unknown>): Promise<void> {
    this._pluginData = data;
  }

  // Test helper to clear plugin data
  _clearData(): void {
    this._pluginData = {};
  }

  // Test helper to set plugin data
  _setData(data: Record<string, unknown>): void {
    this._pluginData = data;
  }
}

// Mock Menu class
// ✅ Verified from @obsidian-canvas Skill (Context Menus)
export class Menu {
  private items: MenuItem[] = [];
  private separators: number[] = [];

  addItem(callback: (item: MenuItem) => void): this {
    const item = new MenuItem();
    callback(item);
    this.items.push(item);
    return this;
  }

  addSeparator(): this {
    this.separators.push(this.items.length);
    return this;
  }

  // Test helpers
  _getItems(): MenuItem[] {
    return this.items;
  }

  _getSeparatorCount(): number {
    return this.separators.length;
  }
}

// Mock MenuItem class
export class MenuItem {
  private _title: string = '';
  private _icon: string | null = null;
  private _clickCallback: (() => void) | null = null;
  private _disabled: boolean = false;

  setTitle(title: string): this {
    this._title = title;
    return this;
  }

  setIcon(icon: string): this {
    this._icon = icon;
    return this;
  }

  onClick(callback: () => void): this {
    this._clickCallback = callback;
    return this;
  }

  setDisabled(disabled: boolean): this {
    this._disabled = disabled;
    return this;
  }

  // Test helpers
  _getTitle(): string {
    return this._title;
  }

  _getIcon(): string | null {
    return this._icon;
  }

  _click(): void {
    if (this._clickCallback) {
      this._clickCallback();
    }
  }
}

// Mock Editor class
export class Editor {
  private _selection: string = '';
  private _content: string = '';

  getSelection(): string {
    return this._selection;
  }

  replaceSelection(replacement: string): void {
    this._selection = replacement;
  }

  getValue(): string {
    return this._content;
  }

  setValue(content: string): void {
    this._content = content;
  }

  // Test helpers
  _setSelection(selection: string): void {
    this._selection = selection;
  }

  _setContent(content: string): void {
    this._content = content;
  }
}

// Mock MarkdownView class
export class MarkdownView {
  file: TFile | null;
  editor: Editor;

  constructor(file: TFile | null = null) {
    this.file = file;
    this.editor = new Editor();
  }
}

// Mock EventRef type
export interface EventRef {
  event: string;
  callback: Function;
}

// Export App interface mock
export interface App {
  vault: Vault;
  workspace: any;
}
