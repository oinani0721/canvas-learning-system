import { ItemView, WorkspaceLeaf } from 'obsidian';

export const VIEW_TYPE_CANVAS_LEARNING = 'canvas-learning-view';

export class CanvasLearningView extends ItemView {
	constructor(leaf: WorkspaceLeaf) {
		super(leaf);
	}

	getViewType(): string {
		return VIEW_TYPE_CANVAS_LEARNING;
	}

	getDisplayText(): string {
		return 'Canvas Learning';
	}

	getIcon(): string {
		return 'graduation-cap';
	}

	async onOpen() {
		const container = this.contentEl;
		container.empty();
		container.addClass('canvas-learning-view');

		container.createEl('h3', { text: 'Canvas Learning System' });
		container.createEl('p', {
			text: 'Open a .canvas file to see its nodes.',
			cls: 'canvas-learning-hint',
		});
	}

	async onClose() {
		this.contentEl.empty();
	}
}
