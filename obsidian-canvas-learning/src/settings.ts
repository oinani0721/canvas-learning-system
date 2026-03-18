import { App, PluginSettingTab, Setting } from 'obsidian';
import type CanvasLearningPlugin from './main';

export interface CanvasLearningSettings {
	backendUrl: string;
}

export const DEFAULT_SETTINGS: CanvasLearningSettings = {
	backendUrl: 'http://localhost:8001',
};

export class CanvasLearningSettingTab extends PluginSettingTab {
	plugin: CanvasLearningPlugin;

	constructor(app: App, plugin: CanvasLearningPlugin) {
		super(app, plugin);
		this.plugin = plugin;
	}

	display(): void {
		const { containerEl } = this;
		containerEl.empty();

		containerEl.createEl('h2', { text: 'Canvas Learning System' });

		new Setting(containerEl)
			.setName('Backend URL')
			.setDesc('FastAPI backend address (default: http://localhost:8001)')
			.addText((text) =>
				text
					.setPlaceholder('http://localhost:8001')
					.setValue(this.plugin.settings.backendUrl)
					.onChange(async (value) => {
						this.plugin.settings.backendUrl = value;
						await this.plugin.saveSettings();
					}),
			);
	}
}
