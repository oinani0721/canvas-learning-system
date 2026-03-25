import { Notice, Plugin, WorkspaceLeaf } from 'obsidian';
import { DEFAULT_SETTINGS, CanvasLearningSettingTab } from './settings';
import type { CanvasLearningSettings } from './settings';
import { CanvasLearningView, VIEW_TYPE_CANVAS_LEARNING } from './canvas-learning-view';

/**
 * Canvas Learning System - Obsidian Plugin
 *
 * M0: Minimal scaffold from official sample-plugin template.
 * Validates that the plugin loads, settings persist, and ribbon icon works.
 */
export default class CanvasLearningPlugin extends Plugin {
	settings: CanvasLearningSettings;

	async onload() {
		await this.loadSettings();

		// Register the sidebar view
		this.registerView(
			VIEW_TYPE_CANVAS_LEARNING,
			(leaf) => new CanvasLearningView(leaf),
		);

		// Ribbon icon — opens the sidebar panel
		this.addRibbonIcon('graduation-cap', 'Canvas Learning System', () => {
			this.activateView();
		});

		// Status bar — shows backend connection status
		const statusBarEl = this.addStatusBarItem();
		statusBarEl.setText('CLS: ready');

		// Settings tab
		this.addSettingTab(new CanvasLearningSettingTab(this.app, this));

		console.log('[Canvas Learning] Plugin loaded successfully');
	}

	onunload() {
		console.log('[Canvas Learning] Plugin unloaded');
	}

	async activateView() {
		const { workspace } = this.app;
		const existing = workspace.getLeavesOfType(VIEW_TYPE_CANVAS_LEARNING);
		const first = existing[0];

		if (first) {
			workspace.revealLeaf(first);
			return;
		}

		const leaf = workspace.getRightLeaf(false);
		if (leaf) {
			await leaf.setViewState({ type: VIEW_TYPE_CANVAS_LEARNING, active: true });
			workspace.revealLeaf(leaf);
		}
	}

	async loadSettings() {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings() {
		await this.saveData(this.settings);
	}
}
