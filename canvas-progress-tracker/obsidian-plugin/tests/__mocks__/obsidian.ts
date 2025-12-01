/**
 * Mock Obsidian module for testing
 *
 * Provides stub implementations of Obsidian classes used in the plugin.
 */

export class Notice {
  constructor(public message: string, public timeout?: number) {
    // Mock Notice - just store the message
  }
}

export class Plugin {
  app: any;
  manifest: any;

  async loadData(): Promise<any> {
    return {};
  }

  async saveData(data: any): Promise<void> {
    // Mock save
  }

  addCommand(command: any): void {
    // Mock add command
  }

  addRibbonIcon(icon: string, title: string, callback: () => void): HTMLElement {
    return document.createElement('div');
  }

  addSettingTab(tab: any): void {
    // Mock add setting tab
  }
}

export class PluginSettingTab {
  app: any;
  plugin: any;
  containerEl: any;

  constructor(app: any, plugin: any) {
    this.app = app;
    this.plugin = plugin;
    this.containerEl = document.createElement('div');
  }

  display(): void {
    // Mock display
  }

  hide(): void {
    // Mock hide
  }
}

export class Setting {
  constructor(containerEl: HTMLElement) {
    // Mock Setting
  }

  setName(name: string): this {
    return this;
  }

  setDesc(desc: string): this {
    return this;
  }

  addText(callback: (text: any) => any): this {
    return this;
  }

  addToggle(callback: (toggle: any) => any): this {
    return this;
  }

  addDropdown(callback: (dropdown: any) => any): this {
    return this;
  }
}

export const requestUrl = jest.fn();
