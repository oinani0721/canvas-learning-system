/**
 * Canvas Learning System - Main View
 * Story 1.1: Plugin scaffold (AC-3)
 * Story 1.4: Routing between Dashboard and Canvas views (AC-7, Task 8.1)
 *
 * ItemView subclass that hosts the Svelte 5 root component (App.svelte).
 * Uses Svelte 5 mount()/unmount() API for lifecycle management.
 */

import { ItemView, type WorkspaceLeaf } from 'obsidian';
import { mount, unmount } from 'svelte';
import App from '../App.svelte';
import { canvasState } from '../stores/canvas-state';

export const VIEW_TYPE_CANVAS_LEARNING = 'canvas-learning-view';

export class MainView extends ItemView {
  private svelteComponent: Record<string, unknown> | null = null;

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

  async onOpen(): Promise<void> {
    const container = this.containerEl.children[1] as HTMLElement;
    container.empty();
    container.addClass('cl-root');

    this.svelteComponent = mount(App, {
      target: container,
    });
  }

  async onClose(): Promise<void> {
    if (this.svelteComponent) {
      unmount(this.svelteComponent);
      this.svelteComponent = null;
    }
    canvasState.dispose();
  }
}
