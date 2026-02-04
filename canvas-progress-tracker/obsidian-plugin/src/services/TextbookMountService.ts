/**
 * Textbook Mount Service - Canvas Learning System
 *
 * Service for managing multi-format textbook mounting.
 * Implements Epic 21: 多格式教材挂载系统
 *
 * Supported formats:
 * - Markdown (.md) - Parsed locally in Obsidian
 * - PDF (.pdf) - Parsed via backend API
 * - Canvas (.canvas) - Existing support via CrossCanvasService
 *
 * @module TextbookMountService
 * @version 1.0.0
 */

import { Notice, type App, type TFile } from 'obsidian';
import type {
    MountedTextbook,
    TextbookSection,
    TextbookType,
} from '../types/UITypes';

/**
 * Storage key for mounted textbooks
 */
const TEXTBOOKS_STORAGE_KEY = 'canvas-mounted-textbooks';

/**
 * Backend API endpoint for PDF parsing
 */
const PDF_PARSE_ENDPOINT = '/api/v1/textbook/parse-pdf';

/**
 * Backend API endpoint for textbook sync
 * @source Epic 28 - 方案A: 前端同步到后端
 */
const TEXTBOOK_SYNC_ENDPOINT = '/api/v1/textbook/sync-mount';
const TEXTBOOK_UNMOUNT_ENDPOINT = '/api/v1/textbook/unmount';

/**
 * Service for managing textbook mounting and parsing
 * [Source: Epic 21 - 多格式教材挂载系统]
 * [Enhanced: Epic 28 - 方案A: 前端同步到后端]
 */
export class TextbookMountService {
    private app: App;
    private mountedTextbooks: MountedTextbook[] = [];
    private backendUrl: string;
    /**
     * Current active canvas path for textbook mounting context
     * @source Epic 28 - 方案A: 前端同步到后端
     */
    private currentCanvasPath: string | null = null;

    constructor(app: App, backendUrl: string = 'http://127.0.0.1:8000') {
        this.app = app;
        this.backendUrl = backendUrl;
        this.loadMountedTextbooks();
    }

    // ============================================================================
    // Canvas Context (Epic 28 - Backend Sync)
    // ============================================================================

    /**
     * Set the current canvas path for mounting context
     * Must be called before mounting textbooks so sync knows which canvas to associate
     *
     * @param canvasPath - Active canvas file path
     * @source Epic 28 - 方案A: 前端同步到后端
     */
    setCurrentCanvasPath(canvasPath: string): void {
        this.currentCanvasPath = canvasPath;
        console.log('[TextbookMountService] Set current canvas:', canvasPath);
    }

    /**
     * Get the current canvas path
     */
    getCurrentCanvasPath(): string | null {
        return this.currentCanvasPath;
    }

    // ============================================================================
    // Persistence
    // ============================================================================

    /**
     * Load mounted textbooks from localStorage
     */
    private loadMountedTextbooks(): void {
        try {
            const stored = localStorage.getItem(TEXTBOOKS_STORAGE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                this.mountedTextbooks = parsed.map((tb: any) => ({
                    ...tb,
                    mountedDate: new Date(tb.mountedDate),
                    lastAccessedDate: tb.lastAccessedDate ? new Date(tb.lastAccessedDate) : undefined,
                }));
            }
        } catch (error) {
            console.error('[TextbookMountService] Failed to load textbooks:', error);
            this.mountedTextbooks = [];
        }
    }

    /**
     * Save mounted textbooks to localStorage
     */
    private saveMountedTextbooks(): void {
        try {
            localStorage.setItem(TEXTBOOKS_STORAGE_KEY, JSON.stringify(this.mountedTextbooks));
        } catch (error) {
            console.error('[TextbookMountService] Failed to save textbooks:', error);
        }
    }

    // ============================================================================
    // Mount/Unmount Operations
    // ============================================================================

    /**
     * Get all mounted textbooks
     */
    getMountedTextbooks(): MountedTextbook[] {
        return [...this.mountedTextbooks];
    }

    /**
     * Mount a new textbook file
     * @param filePath - Path to the file in vault
     * @returns Promise<MountedTextbook>
     */
    async mountTextbook(filePath: string): Promise<MountedTextbook> {
        // Check if already mounted
        const existing = this.mountedTextbooks.find(tb => tb.path === filePath);
        if (existing) {
            console.log('[TextbookMountService] Textbook already mounted:', filePath);
            return existing;
        }

        // Determine file type
        const type = this.getTextbookType(filePath);
        const file = this.app.vault.getAbstractFileByPath(filePath);

        if (!file || !(file instanceof this.app.vault.adapter.constructor) && !file) {
            throw new Error(`File not found: ${filePath}`);
        }

        const tFile = file as TFile;
        const name = tFile.basename;

        // Parse sections based on type
        let sections: TextbookSection[] = [];

        if (type === 'markdown') {
            sections = await this.parseMarkdownSections(filePath);
        } else if (type === 'pdf') {
            sections = await this.parsePdfSections(filePath);
        }
        // Canvas files don't need section parsing - they use CrossCanvasService

        const textbook: MountedTextbook = {
            id: `tb-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            path: filePath,
            name,
            type,
            mountedDate: new Date(),
            sections,
            referenceCount: 0,
        };

        this.mountedTextbooks.push(textbook);
        this.saveMountedTextbooks();

        // Epic 28: Sync to backend if we have a current canvas context
        if (this.currentCanvasPath) {
            await this.syncToBackend(textbook, this.currentCanvasPath);
        } else {
            console.warn('[TextbookMountService] No canvas context set, skipping backend sync');
        }

        console.log('[TextbookMountService] Mounted textbook:', textbook.name, 'sections:', sections.length);
        return textbook;
    }

    /**
     * Mount a textbook and associate it with a specific canvas
     *
     * @param filePath - Path to the textbook file
     * @param canvasPath - Canvas path to associate with
     * @returns Mounted textbook
     *
     * @source Epic 28 - 方案A: 前端同步到后端
     */
    async mountTextbookForCanvas(filePath: string, canvasPath: string): Promise<MountedTextbook> {
        this.setCurrentCanvasPath(canvasPath);
        return this.mountTextbook(filePath);
    }

    /**
     * Sync mounted textbook to backend .canvas-links.json
     *
     * @param textbook - Textbook to sync
     * @param canvasPath - Canvas path to associate with
     * @source Epic 28 - 方案A: 前端同步到后端
     */
    private async syncToBackend(textbook: MountedTextbook, canvasPath: string): Promise<void> {
        try {
            const response = await fetch(`${this.backendUrl}${TEXTBOOK_SYNC_ENDPOINT}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                },
                body: JSON.stringify({
                    canvas_path: canvasPath,
                    textbook: {
                        id: textbook.id,
                        path: textbook.path,
                        name: textbook.name,
                        type: textbook.type,
                        sections: (textbook.sections || []).map(s => ({
                            id: s.id,
                            title: s.title,
                            level: s.level,
                            preview: s.preview,
                            start_offset: s.startOffset,
                            end_offset: s.endOffset,
                            page_number: s.pageNumber,
                        })),
                    },
                }),
            });

            if (response.ok) {
                const data = await response.json();
                console.log('[TextbookMountService] Synced to backend:', data.config_path);
            } else {
                const errorText = await response.text();
                console.warn('[TextbookMountService] Backend sync failed:', response.status, errorText);
                // Story 34.3 Task 6.2: Show notice for backend sync failure
                new Notice(`⚠️ 教材关联同步失败 (${response.status}): 本地挂载成功，但后端同步未完成`);
            }
        } catch (error) {
            console.error('[TextbookMountService] Backend sync error:', error);
            // Story 34.3 Task 6.2: Show notice for backend sync error
            new Notice('⚠️ 教材关联同步错误: 本地挂载成功，但后端同步未完成');
            // Don't fail the mount operation if sync fails
        }
    }

    /**
     * Unmount a textbook
     * @param textbookId - Textbook ID to unmount
     * @param canvasPath - Optional canvas path for backend sync
     * @source Enhanced: Epic 28 - 方案A: 前端同步到后端
     */
    async unmountTextbook(textbookId: string, canvasPath?: string): Promise<void> {
        const index = this.mountedTextbooks.findIndex(tb => tb.id === textbookId);
        if (index !== -1) {
            const removed = this.mountedTextbooks.splice(index, 1)[0];
            this.saveMountedTextbooks();

            // Epic 28: Sync unmount to backend
            const effectiveCanvasPath = canvasPath || this.currentCanvasPath;
            if (effectiveCanvasPath) {
                await this.syncUnmountToBackend(textbookId, effectiveCanvasPath);
            }

            console.log('[TextbookMountService] Unmounted textbook:', removed.name);
        }
    }

    /**
     * Sync textbook unmount to backend
     *
     * @param textbookId - Textbook ID to unmount
     * @param canvasPath - Canvas path
     * @source Epic 28 - 方案A: 前端同步到后端
     */
    private async syncUnmountToBackend(textbookId: string, canvasPath: string): Promise<void> {
        try {
            const response = await fetch(`${this.backendUrl}${TEXTBOOK_UNMOUNT_ENDPOINT}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                },
                body: JSON.stringify({
                    canvas_path: canvasPath,
                    textbook_id: textbookId,
                }),
            });

            if (response.ok) {
                console.log('[TextbookMountService] Unmount synced to backend');
            } else {
                console.warn('[TextbookMountService] Backend unmount sync failed:', response.status);
            }
        } catch (error) {
            console.error('[TextbookMountService] Backend unmount sync error:', error);
        }
    }

    /**
     * Get textbook type from file extension
     */
    private getTextbookType(filePath: string): TextbookType {
        const ext = filePath.toLowerCase().split('.').pop();
        switch (ext) {
            case 'md':
            case 'markdown':
                return 'markdown';
            case 'pdf':
                return 'pdf';
            case 'canvas':
                return 'canvas';
            default:
                return 'markdown'; // Default to markdown
        }
    }

    // ============================================================================
    // Markdown Parsing
    // ============================================================================

    /**
     * Parse Markdown file to extract sections (headings)
     * @param filePath - Path to markdown file
     * @returns Promise<TextbookSection[]>
     */
    private async parseMarkdownSections(filePath: string): Promise<TextbookSection[]> {
        try {
            const file = this.app.vault.getAbstractFileByPath(filePath);
            if (!file) return [];

            const content = await this.app.vault.read(file as TFile);
            return this.extractMarkdownHeadings(content);
        } catch (error) {
            console.error('[TextbookMountService] Failed to parse markdown:', error);
            return [];
        }
    }

    /**
     * Extract headings from markdown content
     * @param content - Markdown content
     * @returns TextbookSection[]
     */
    private extractMarkdownHeadings(content: string): TextbookSection[] {
        const sections: TextbookSection[] = [];
        const lines = content.split('\n');
        let currentOffset = 0;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);

            if (headingMatch) {
                const level = headingMatch[1].length;
                const title = headingMatch[2].trim();

                // Get content preview (next few lines)
                let preview = '';
                let previewLines = 0;
                for (let j = i + 1; j < lines.length && previewLines < 5; j++) {
                    const nextLine = lines[j].trim();
                    if (nextLine && !nextLine.startsWith('#')) {
                        preview += nextLine + ' ';
                        previewLines++;
                    }
                    if (nextLine.startsWith('#')) break;
                }
                preview = preview.substring(0, 200).trim();

                // Calculate end offset (until next heading or end of file)
                let endOffset = content.length;
                for (let j = i + 1; j < lines.length; j++) {
                    if (lines[j].match(/^#{1,6}\s+/)) {
                        endOffset = currentOffset + lines.slice(i, j).join('\n').length;
                        break;
                    }
                }

                sections.push({
                    id: `section-${i}-${Date.now()}`,
                    title,
                    level,
                    preview,
                    startOffset: currentOffset,
                    endOffset,
                });
            }

            currentOffset += line.length + 1; // +1 for newline
        }

        return sections;
    }

    // ============================================================================
    // PDF Parsing (via Backend)
    // ============================================================================

    /**
     * Parse PDF file sections via backend API
     * @param filePath - Path to PDF file
     * @returns Promise<TextbookSection[]>
     */
    private async parsePdfSections(filePath: string): Promise<TextbookSection[]> {
        try {
            // Read file as binary
            const file = this.app.vault.getAbstractFileByPath(filePath);
            if (!file) return [];

            const arrayBuffer = await this.app.vault.readBinary(file as TFile);
            const base64 = this.arrayBufferToBase64(arrayBuffer);

            // Send to backend for parsing
            const response = await fetch(`${this.backendUrl}${PDF_PARSE_ENDPOINT}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_content: base64,
                    file_name: (file as TFile).basename,
                }),
            });

            if (!response.ok) {
                console.warn('[TextbookMountService] PDF parsing not available (backend may not support it yet)');
                return [{
                    id: `section-pdf-${Date.now()}`,
                    title: 'PDF Document',
                    level: 1,
                    preview: 'PDF parsing requires backend support. Please ensure backend is running with PDF parsing enabled.',
                    startOffset: 0,
                    endOffset: 0,
                }];
            }

            const data = await response.json();
            return data.sections || [];
        } catch (error) {
            console.error('[TextbookMountService] Failed to parse PDF:', error);
            return [{
                id: `section-pdf-error-${Date.now()}`,
                title: 'PDF Document (Unparsed)',
                level: 1,
                preview: 'PDF could not be parsed. Backend service may be unavailable.',
                startOffset: 0,
                endOffset: 0,
            }];
        }
    }

    /**
     * Convert ArrayBuffer to Base64 string
     */
    private arrayBufferToBase64(buffer: ArrayBuffer): string {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    // ============================================================================
    // Content Retrieval
    // ============================================================================

    /**
     * Get section content from a textbook
     * @param textbookId - Textbook ID
     * @param sectionId - Section ID
     * @returns Promise<string>
     */
    async getSectionContent(textbookId: string, sectionId: string): Promise<string> {
        const textbook = this.mountedTextbooks.find(tb => tb.id === textbookId);
        if (!textbook) return '';

        const section = textbook.sections?.find((s: TextbookSection) => s.id === sectionId);
        if (!section) return '';

        if (textbook.type === 'markdown') {
            try {
                const file = this.app.vault.getAbstractFileByPath(textbook.path);
                if (!file) return '';

                const content = await this.app.vault.read(file as TFile);
                return content.substring(section.startOffset, section.endOffset);
            } catch (error) {
                console.error('[TextbookMountService] Failed to get section content:', error);
                return '';
            }
        }

        // For PDF, return preview (full content requires backend)
        return section.preview;
    }

    /**
     * Search across all mounted textbooks
     * @param query - Search query
     * @returns Promise<SearchResult[]>
     */
    async searchTextbooks(query: string): Promise<Array<{
        textbook: MountedTextbook;
        section: TextbookSection;
        matchContext: string;
    }>> {
        const results: Array<{
            textbook: MountedTextbook;
            section: TextbookSection;
            matchContext: string;
        }> = [];

        const queryLower = query.toLowerCase();

        for (const textbook of this.mountedTextbooks) {
            if (textbook.type === 'markdown') {
                // Search in markdown content
                try {
                    const file = this.app.vault.getAbstractFileByPath(textbook.path);
                    if (!file) continue;

                    const content = await this.app.vault.read(file as TFile);
                    const contentLower = content.toLowerCase();

                    if (contentLower.includes(queryLower)) {
                        // Find which section contains the match
                        for (const section of textbook.sections || []) {
                            const sectionContent = content.substring(section.startOffset, section.endOffset);
                            if (sectionContent.toLowerCase().includes(queryLower)) {
                                // Extract match context
                                const matchIndex = sectionContent.toLowerCase().indexOf(queryLower);
                                const start = Math.max(0, matchIndex - 50);
                                const end = Math.min(sectionContent.length, matchIndex + query.length + 50);
                                const matchContext = '...' + sectionContent.substring(start, end) + '...';

                                results.push({
                                    textbook,
                                    section,
                                    matchContext,
                                });
                            }
                        }
                    }
                } catch (error) {
                    console.error('[TextbookMountService] Search error:', error);
                }
            } else if (textbook.type === 'canvas') {
                // Canvas search is handled by CrossCanvasService
                continue;
            } else {
                // Search in section titles/previews for PDF
                for (const section of textbook.sections || []) {
                    if (
                        section.title.toLowerCase().includes(queryLower) ||
                        section.preview.toLowerCase().includes(queryLower)
                    ) {
                        results.push({
                            textbook,
                            section,
                            matchContext: section.preview,
                        });
                    }
                }
            }
        }

        return results;
    }

    /**
     * Get available textbook files in vault (MD, PDF, Canvas)
     */
    async getAvailableTextbookFiles(): Promise<Array<{ path: string; basename: string; type: TextbookType }>> {
        const files = this.app.vault.getFiles();
        const textbookFiles: Array<{ path: string; basename: string; type: TextbookType }> = [];

        for (const file of files) {
            const ext = file.extension.toLowerCase();
            if (ext === 'md' || ext === 'markdown') {
                textbookFiles.push({
                    path: file.path,
                    basename: file.basename,
                    type: 'markdown',
                });
            } else if (ext === 'pdf') {
                textbookFiles.push({
                    path: file.path,
                    basename: file.basename,
                    type: 'pdf',
                });
            } else if (ext === 'canvas') {
                textbookFiles.push({
                    path: file.path,
                    basename: file.basename,
                    type: 'canvas',
                });
            }
        }

        return textbookFiles.sort((a, b) => a.basename.localeCompare(b.basename));
    }

    /**
     * Increment reference count for a textbook
     */
    incrementReferenceCount(textbookId: string): void {
        const textbook = this.mountedTextbooks.find(tb => tb.id === textbookId);
        if (textbook) {
            textbook.referenceCount++;
            textbook.lastAccessedDate = new Date();
            this.saveMountedTextbooks();
        }
    }
}

/**
 * Factory function
 */
export function createTextbookMountService(app: App, backendUrl?: string): TextbookMountService {
    return new TextbookMountService(app, backendUrl);
}
