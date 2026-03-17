/**
 * Canvas Learning System - Setup Wizard Modal
 * Story 1.2: Setup Wizard (AC-1, AC-2, AC-6)
 *
 * Obsidian Modal subclass that hosts the SetupWizard Svelte 5 component.
 * Uses mount()/unmount() lifecycle for Svelte 5 compatibility.
 */

import { type App, Modal } from 'obsidian';
import { mount, unmount } from 'svelte';
import type { ApiClient } from '../../services/api-client';
import SetupWizard from './SetupWizard.svelte';

export class SetupWizardModal extends Modal {
  private svelteComponent: ReturnType<typeof mount> | null = null;

  constructor(
    app: App,
    private apiClient: ApiClient,
    private onSetupComplete: () => void,
  ) {
    super(app);
  }

  onOpen(): void {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass('cl-sys-wizard-modal');

    this.svelteComponent = mount(SetupWizard, {
      target: contentEl,
      props: {
        app: this.app,
        apiClient: this.apiClient,
        onComplete: () => {
          this.onSetupComplete();
          this.close();
        },
      },
    });
  }

  onClose(): void {
    if (this.svelteComponent) {
      unmount(this.svelteComponent);
      this.svelteComponent = null;
    }
    const { contentEl } = this;
    contentEl.empty();
  }
}
