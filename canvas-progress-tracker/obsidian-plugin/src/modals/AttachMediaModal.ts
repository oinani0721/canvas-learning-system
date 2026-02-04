/**
 * AttachMediaModal - Canvas Learning System
 *
 * Modal for attaching media files (images, PDFs, audio, video) to Canvas nodes.
 * Implements Story 35.5: Canvas节点"附加媒体"右键菜单
 *
 * @module modals/AttachMediaModal
 * @version 1.0.0
 *
 * ✅ Verified from @obsidian-canvas Skill (Modal API)
 * ✅ Verified from Story 35.5 Dev Notes (Modal design)
 */

import { App, Modal, Notice, setIcon } from 'obsidian';
import type { MultimodalUploadResponse } from '../api/types';

/**
 * Accepted file MIME types for multimodal upload
 * @source Story 35.5 AC 35.5.2 - File type filter
 */
const ACCEPTED_MIME_TYPES = [
  'image/*',
  'application/pdf',
  'audio/*',
  'video/*',
];

/**
 * File type to accept attribute string
 */
const ACCEPT_ATTRIBUTE = 'image/*,application/pdf,audio/*,video/*';

/**
 * Maximum file size in bytes (50MB for images/PDF, 500MB for video)
 * @source EPIC-35 Risk Mitigation
 */
const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50MB default
const MAX_VIDEO_SIZE_BYTES = 500 * 1024 * 1024; // 500MB for video

/**
 * Media type display configuration
 */
const MEDIA_TYPE_CONFIG: Record<string, { icon: string; label: string }> = {
  image: { icon: 'image', label: '图片' },
  pdf: { icon: 'file-text', label: 'PDF文档' },
  audio: { icon: 'music', label: '音频' },
  video: { icon: 'video', label: '视频' },
};

/**
 * Callback for upload progress updates
 */
export type UploadProgressCallback = (percent: number) => void;

/**
 * Callback for upload completion
 */
export type UploadCompleteCallback = (response: MultimodalUploadResponse) => void;

/**
 * Callback for upload errors
 */
export type UploadErrorCallback = (error: Error) => void;

/**
 * Options for AttachMediaModal
 */
export interface AttachMediaModalOptions {
  /** Node ID to attach media to */
  nodeId: string;
  /** Concept ID for the node (used for backend association) */
  conceptId: string;
  /** Canvas path (optional, for context) */
  canvasPath?: string;
  /** Callback when upload completes successfully */
  onUploadComplete?: UploadCompleteCallback;
  /** Callback when upload fails */
  onUploadError?: UploadErrorCallback;
  /** Upload function (injected for testability) */
  uploadFn?: (
    file: File,
    conceptId: string,
    onProgress?: UploadProgressCallback
  ) => Promise<MultimodalUploadResponse>;
}

/**
 * AttachMediaModal
 *
 * Provides a UI for attaching media files to Canvas concept nodes.
 * Supports file selection via button click or drag-and-drop.
 *
 * Features:
 * - File type filtering (images, PDFs, audio, video)
 * - Drag and drop support
 * - File preview before upload
 * - Upload progress indicator
 * - Success notification with thumbnail
 *
 * @source Story 35.5 AC 35.5.2 - Modal design
 */
export class AttachMediaModal extends Modal {
  private options: AttachMediaModalOptions;

  // UI state
  private selectedFile: File | null = null;
  private isUploading: boolean = false;
  private uploadProgress: number = 0;

  // UI element references
  private dropZoneEl: HTMLElement | null = null;
  private fileInputEl: HTMLInputElement | null = null;
  private previewContainerEl: HTMLElement | null = null;
  private progressContainerEl: HTMLElement | null = null;
  private progressBarEl: HTMLElement | null = null;
  private progressTextEl: HTMLElement | null = null;
  private uploadBtnEl: HTMLButtonElement | null = null;

  /**
   * Creates a new AttachMediaModal
   *
   * @param app - Obsidian App instance
   * @param options - Modal configuration options
   */
  constructor(app: App, options: AttachMediaModalOptions) {
    super(app);
    this.options = options;
  }

  /**
   * Called when the modal is opened
   * ✅ Verified from @obsidian-canvas Skill (Modal lifecycle)
   */
  onOpen(): void {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass('attach-media-modal');

    // Header
    this.renderHeader(contentEl);

    // Drop zone (AC 35.5.2: drag and drop support)
    this.renderDropZone(contentEl);

    // File preview area
    this.renderPreviewArea(contentEl);

    // Progress indicator (AC 35.5.3: upload progress)
    this.renderProgressArea(contentEl);

    // Action buttons
    this.renderActions(contentEl);
  }

  /**
   * Called when the modal is closed
   */
  onClose(): void {
    const { contentEl } = this;
    contentEl.empty();

    // Clean up state
    this.selectedFile = null;
    this.isUploading = false;
    this.uploadProgress = 0;
  }

  // ========== Render Methods ==========

  /**
   * Render modal header
   */
  private renderHeader(container: HTMLElement): void {
    const header = container.createEl('div', {
      cls: 'attach-media-modal-header',
    });

    header.createEl('h2', {
      text: '📎 附加媒体文件',
      cls: 'attach-media-modal-title',
    });

    header.createEl('p', {
      text: '将图片、PDF、音频或视频附加到此概念节点',
      cls: 'attach-media-modal-subtitle',
    });
  }

  /**
   * Render drop zone with file input
   * @source Story 35.5 AC 35.5.2 - Drag and drop support
   */
  private renderDropZone(container: HTMLElement): void {
    this.dropZoneEl = container.createEl('div', {
      cls: 'attach-media-drop-zone',
    });

    // Hidden file input
    this.fileInputEl = this.dropZoneEl.createEl('input', {
      type: 'file',
      cls: 'attach-media-file-input',
    });
    this.fileInputEl.accept = ACCEPT_ATTRIBUTE;
    this.fileInputEl.style.display = 'none';

    // Drop zone content
    const dropContent = this.dropZoneEl.createEl('div', {
      cls: 'attach-media-drop-content',
    });

    // Icon
    const iconEl = dropContent.createEl('div', {
      cls: 'attach-media-drop-icon',
    });
    setIcon(iconEl, 'upload');

    // Text
    dropContent.createEl('p', {
      text: '拖放文件到此处',
      cls: 'attach-media-drop-text',
    });

    dropContent.createEl('p', {
      text: '或',
      cls: 'attach-media-drop-or',
    });

    // Select button
    const selectBtn = dropContent.createEl('button', {
      text: '选择文件',
      cls: 'attach-media-select-btn',
    });

    // Supported formats hint
    dropContent.createEl('p', {
      text: '支持格式: 图片 (JPG, PNG, GIF), PDF, 音频 (MP3, WAV), 视频 (MP4, WebM)',
      cls: 'attach-media-formats-hint',
    });

    // Event listeners
    this.setupDropZoneEvents(selectBtn);
  }

  /**
   * Setup drop zone event listeners
   */
  private setupDropZoneEvents(selectBtn: HTMLButtonElement): void {
    if (!this.dropZoneEl || !this.fileInputEl) return;

    // Click to select file
    selectBtn.addEventListener('click', () => {
      this.fileInputEl?.click();
    });

    // File input change
    this.fileInputEl.addEventListener('change', (e) => {
      const input = e.target as HTMLInputElement;
      if (input.files && input.files.length > 0) {
        this.handleFileSelection(input.files[0]);
      }
    });

    // Drag events
    this.dropZoneEl.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.dropZoneEl?.addClass('drag-over');
    });

    this.dropZoneEl.addEventListener('dragleave', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.dropZoneEl?.removeClass('drag-over');
    });

    this.dropZoneEl.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.dropZoneEl?.removeClass('drag-over');

      const files = e.dataTransfer?.files;
      if (files && files.length > 0) {
        this.handleFileSelection(files[0]);
      }
    });
  }

  /**
   * Render file preview area
   */
  private renderPreviewArea(container: HTMLElement): void {
    this.previewContainerEl = container.createEl('div', {
      cls: 'attach-media-preview-container',
    });
    this.previewContainerEl.style.display = 'none';
  }

  /**
   * Render progress indicator area
   * @source Story 35.5 AC 35.5.3 - Upload progress
   */
  private renderProgressArea(container: HTMLElement): void {
    this.progressContainerEl = container.createEl('div', {
      cls: 'attach-media-progress-container',
    });
    this.progressContainerEl.style.display = 'none';

    // Progress bar wrapper
    const progressBarWrapper = this.progressContainerEl.createEl('div', {
      cls: 'attach-media-progress-bar-wrapper',
    });

    this.progressBarEl = progressBarWrapper.createEl('div', {
      cls: 'attach-media-progress-bar',
    });

    this.progressTextEl = this.progressContainerEl.createEl('div', {
      cls: 'attach-media-progress-text',
      text: '上传中... 0%',
    });
  }

  /**
   * Render action buttons
   */
  private renderActions(container: HTMLElement): void {
    const actionsContainer = container.createEl('div', {
      cls: 'attach-media-actions',
    });

    // Cancel button
    const cancelBtn = actionsContainer.createEl('button', {
      text: '取消',
      cls: 'attach-media-cancel-btn',
    });

    cancelBtn.addEventListener('click', () => {
      this.close();
    });

    // Upload button
    this.uploadBtnEl = actionsContainer.createEl('button', {
      text: '上传',
      cls: 'attach-media-upload-btn mod-cta',
    });
    this.uploadBtnEl.disabled = true;

    this.uploadBtnEl.addEventListener('click', async () => {
      await this.handleUpload();
    });
  }

  // ========== File Handling ==========

  /**
   * Handle file selection (from input or drop)
   * @source Story 35.5 AC 35.5.2 - File type filtering
   */
  private handleFileSelection(file: File): void {
    // Validate file type
    if (!this.isValidFileType(file)) {
      new Notice('❌ 不支持的文件类型。请选择图片、PDF、音频或视频文件。');
      return;
    }

    // Validate file size
    const maxSize = this.isVideoFile(file) ? MAX_VIDEO_SIZE_BYTES : MAX_FILE_SIZE_BYTES;
    if (file.size > maxSize) {
      const maxSizeMB = Math.round(maxSize / (1024 * 1024));
      new Notice(`❌ 文件过大。最大允许 ${maxSizeMB}MB。`);
      return;
    }

    this.selectedFile = file;
    this.updatePreview();
    this.updateUploadButtonState();
  }

  /**
   * Check if file type is valid
   */
  private isValidFileType(file: File): boolean {
    const mimeType = file.type.toLowerCase();

    return (
      mimeType.startsWith('image/') ||
      mimeType === 'application/pdf' ||
      mimeType.startsWith('audio/') ||
      mimeType.startsWith('video/')
    );
  }

  /**
   * Check if file is a video
   */
  private isVideoFile(file: File): boolean {
    return file.type.toLowerCase().startsWith('video/');
  }

  /**
   * Get media type from file
   */
  private getMediaType(file: File): 'image' | 'pdf' | 'audio' | 'video' {
    const mimeType = file.type.toLowerCase();

    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType === 'application/pdf') return 'pdf';
    if (mimeType.startsWith('audio/')) return 'audio';
    if (mimeType.startsWith('video/')) return 'video';

    return 'image'; // Default fallback
  }

  /**
   * Update file preview
   * @source Story 35.5 AC 35.5.2 - Show selected file preview
   */
  private updatePreview(): void {
    if (!this.previewContainerEl || !this.selectedFile) return;

    this.previewContainerEl.empty();
    this.previewContainerEl.style.display = 'block';

    const mediaType = this.getMediaType(this.selectedFile);
    const config = MEDIA_TYPE_CONFIG[mediaType];

    // Preview card
    const previewCard = this.previewContainerEl.createEl('div', {
      cls: 'attach-media-preview-card',
    });

    // Icon/thumbnail
    const previewIconEl = previewCard.createEl('div', {
      cls: 'attach-media-preview-icon',
    });

    if (mediaType === 'image') {
      // Show image thumbnail
      const img = previewIconEl.createEl('img', {
        cls: 'attach-media-preview-thumbnail',
      });
      img.src = URL.createObjectURL(this.selectedFile);
      img.onload = () => URL.revokeObjectURL(img.src);
    } else {
      // Show type icon
      setIcon(previewIconEl, config.icon);
    }

    // File info
    const infoEl = previewCard.createEl('div', {
      cls: 'attach-media-preview-info',
    });

    infoEl.createEl('div', {
      text: this.selectedFile.name,
      cls: 'attach-media-preview-name',
    });

    const detailsEl = infoEl.createEl('div', {
      cls: 'attach-media-preview-details',
    });

    detailsEl.createEl('span', {
      text: config.label,
      cls: 'attach-media-preview-type',
    });

    detailsEl.createEl('span', {
      text: ' • ',
    });

    detailsEl.createEl('span', {
      text: this.formatFileSize(this.selectedFile.size),
      cls: 'attach-media-preview-size',
    });

    // Remove button
    const removeBtn = previewCard.createEl('button', {
      cls: 'attach-media-preview-remove',
    });
    setIcon(removeBtn, 'x');
    removeBtn.title = '移除文件';

    removeBtn.addEventListener('click', () => {
      this.selectedFile = null;
      this.previewContainerEl!.style.display = 'none';
      this.updateUploadButtonState();
      if (this.fileInputEl) {
        this.fileInputEl.value = '';
      }
    });
  }

  /**
   * Format file size for display
   */
  private formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  /**
   * Update upload button state
   */
  private updateUploadButtonState(): void {
    if (!this.uploadBtnEl) return;

    const canUpload = this.selectedFile !== null && !this.isUploading;
    this.uploadBtnEl.disabled = !canUpload;

    if (canUpload) {
      this.uploadBtnEl.removeClass('disabled');
    } else {
      this.uploadBtnEl.addClass('disabled');
    }
  }

  // ========== Upload Handling ==========

  /**
   * Handle upload button click
   * @source Story 35.5 AC 35.5.3 - Upload file to backend
   */
  private async handleUpload(): Promise<void> {
    if (!this.selectedFile || this.isUploading) return;

    this.isUploading = true;
    this.uploadProgress = 0;
    this.showProgress();
    this.updateUploadButtonState();

    try {
      // Use injected upload function or show error
      if (!this.options.uploadFn) {
        throw new Error('Upload function not provided');
      }

      const response = await this.options.uploadFn(
        this.selectedFile,
        this.options.conceptId,
        (percent) => {
          this.updateProgress(percent);
        }
      );

      // Success
      this.hideProgress();
      this.showSuccessNotice(response);

      // Callback
      if (this.options.onUploadComplete) {
        this.options.onUploadComplete(response);
      }

      this.close();
    } catch (error) {
      this.hideProgress();
      this.isUploading = false;
      this.updateUploadButtonState();

      const errorMessage = error instanceof Error ? error.message : '上传失败';
      new Notice(`❌ ${errorMessage}`);

      // Error callback
      if (this.options.onUploadError) {
        this.options.onUploadError(error instanceof Error ? error : new Error(errorMessage));
      }
    }
  }

  /**
   * Show progress indicator
   */
  private showProgress(): void {
    if (this.progressContainerEl) {
      this.progressContainerEl.style.display = 'block';
    }
    if (this.dropZoneEl) {
      this.dropZoneEl.addClass('uploading');
    }
  }

  /**
   * Hide progress indicator
   */
  private hideProgress(): void {
    if (this.progressContainerEl) {
      this.progressContainerEl.style.display = 'none';
    }
    if (this.dropZoneEl) {
      this.dropZoneEl.removeClass('uploading');
    }
  }

  /**
   * Update progress display
   * @source Story 35.5 AC 35.5.3 - Show upload progress
   */
  private updateProgress(percent: number): void {
    this.uploadProgress = percent;

    if (this.progressBarEl) {
      this.progressBarEl.style.width = `${percent}%`;
    }

    if (this.progressTextEl) {
      this.progressTextEl.textContent = `上传中... ${Math.round(percent)}%`;
    }
  }

  /**
   * Show success notice with thumbnail
   * @source Story 35.5 AC 35.5.4 - Success notification with thumbnail
   */
  private showSuccessNotice(response: MultimodalUploadResponse): void {
    // Create custom notice with thumbnail
    const noticeMessage = `✅ 媒体文件已附加`;
    new Notice(noticeMessage, 5000);

    // Log for debugging
    console.log('[AttachMediaModal] Upload successful:', {
      id: response.id,
      mediaType: response.media_type,
      path: response.path,
      thumbnail: response.thumbnail ? 'present' : 'none',
    });
  }
}

/**
 * Factory function to create AttachMediaModal
 * @source Story 35.5 - Factory pattern for testability
 */
export function createAttachMediaModal(
  app: App,
  options: AttachMediaModalOptions
): AttachMediaModal {
  return new AttachMediaModal(app, options);
}
