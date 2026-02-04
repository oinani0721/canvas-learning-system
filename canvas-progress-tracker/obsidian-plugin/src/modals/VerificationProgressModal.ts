/**
 * Verification Progress Modal - Real-time Progress Display
 *
 * Modal dialog for displaying real-time verification progress.
 * Shows current concept, color distribution, and mastery percentage.
 *
 * @module modals/VerificationProgressModal
 * @version 1.0.0
 * @story Story 24.3 - Real-time Progress Display
 *
 * UI Design:
 * ┌─────────────────────────────────┐
 * │    Verification - 离散数学       │
 * ├─────────────────────────────────┤
 * │ Current: 逆否命题               │
 * │ ████████░░░░░ 60% (6/10)        │
 * │ 🟢 4 mastered                   │
 * │ 🟡 2 partial                    │
 * │ 🟣 2 need review               │
 * │ 🔴 0 not mastered              │
 * │ Mastery: 40%                    │
 * ├─────────────────────────────────┤
 * │ [ Pause ] [ Skip ] [ End ]      │
 * └─────────────────────────────────┘
 */

import { App, Modal, Notice } from 'obsidian';

/**
 * Verification session status
 */
export type VerificationStatus = 'pending' | 'in_progress' | 'paused' | 'completed' | 'cancelled';

/**
 * Verification progress data from backend
 */
export interface VerificationProgress {
    session_id: string;
    canvas_name: string;
    total_concepts: number;
    completed_concepts: number;
    current_concept: string;
    current_concept_idx: number;
    green_count: number;
    yellow_count: number;
    purple_count: number;
    red_count: number;
    status: VerificationStatus;
    progress_percentage: number;
    mastery_percentage: number;
    hints_given: number;
    max_hints: number;
    started_at: string;
    updated_at: string;
}

/**
 * Question/Answer exchange data
 */
export interface QuestionResponse {
    quality: string;
    score: number;
    action: string;
    hint?: string;
    next_question?: string;
    current_concept: string;
    progress: VerificationProgress;
}

/**
 * Callbacks for verification modal events
 */
export interface VerificationModalCallbacks {
    onAnswer: (answer: string) => Promise<QuestionResponse>;
    onSkip: () => Promise<QuestionResponse>;
    onPause: () => Promise<void>;
    onResume: () => Promise<QuestionResponse>;
    onEnd: () => Promise<void>;
}

/**
 * Verification Progress Modal
 *
 * Displays real-time verification progress with:
 * - Current concept being verified
 * - Overall progress bar
 * - Color distribution (green/yellow/purple/red)
 * - Mastery percentage
 * - Q&A interaction area
 * - Pause/Skip/End controls
 */
export class VerificationProgressModal extends Modal {
    private sessionId: string;
    private canvasName: string;
    private apiBaseUrl: string;
    private callbacks: VerificationModalCallbacks;

    // State
    private progress: VerificationProgress;
    private currentQuestion: string;
    private isAnswering: boolean = false;
    private isPaused: boolean = false;

    // UI elements
    private progressBarFill: HTMLElement | null = null;
    private progressText: HTMLElement | null = null;
    private currentConceptEl: HTMLElement | null = null;
    private colorDistributionEl: HTMLElement | null = null;
    private masteryEl: HTMLElement | null = null;
    private questionEl: HTMLElement | null = null;
    private answerInputEl: HTMLTextAreaElement | null = null;
    private hintEl: HTMLElement | null = null;
    private feedbackEl: HTMLElement | null = null;
    private controlButtonsEl: HTMLElement | null = null;

    // Timer
    private elapsedTimer: number | null = null;
    private startTime: Date;
    private elapsedTimeEl: HTMLElement | null = null;

    // Story 31.6: Polling for real-time progress updates
    private pollingInterval: number | null = null;
    private readonly POLLING_INTERVAL_MS = 2000; // AC-31.6.1: 2-second polling

    /**
     * Creates a new VerificationProgressModal
     *
     * @param app - Obsidian App instance
     * @param sessionId - Verification session ID
     * @param canvasName - Name of the canvas being verified
     * @param firstQuestion - First question to display
     * @param initialProgress - Initial progress data
     * @param apiBaseUrl - Base URL for REST API
     * @param callbacks - Callbacks for verification events
     */
    constructor(
        app: App,
        sessionId: string,
        canvasName: string,
        firstQuestion: string,
        initialProgress: VerificationProgress,
        apiBaseUrl: string,
        callbacks: VerificationModalCallbacks
    ) {
        super(app);
        this.sessionId = sessionId;
        this.canvasName = canvasName;
        this.currentQuestion = firstQuestion;
        this.progress = initialProgress;
        this.apiBaseUrl = apiBaseUrl;
        this.callbacks = callbacks;
        this.startTime = new Date();
    }

    /**
     * Called when the modal is opened
     */
    async onOpen(): Promise<void> {
        const { contentEl } = this;
        contentEl.empty();
        contentEl.addClass('verification-progress-modal');

        this.renderContent();
        this.startElapsedTimer();
        this.startPolling(); // Story 31.6: Start real-time progress polling
    }

    /**
     * Called when the modal is closed
     */
    onClose(): void {
        this.cleanup();
        const { contentEl } = this;
        contentEl.empty();
    }

    /**
     * Cleanup resources
     */
    private cleanup(): void {
        if (this.elapsedTimer) {
            window.clearInterval(this.elapsedTimer);
            this.elapsedTimer = null;
        }
        this.stopPolling();
    }

    // ===========================================================================
    // Story 31.6: Real-time Progress Polling
    // ===========================================================================

    /**
     * Start polling for progress updates
     * AC-31.6.1: Frontend polls every 2 seconds
     */
    private startPolling(): void {
        if (this.pollingInterval) {
            return; // Already polling
        }

        this.pollingInterval = window.setInterval(async () => {
            await this.fetchAndUpdateProgress();
        }, this.POLLING_INTERVAL_MS);

        console.log(`[VerificationProgressModal] Started polling for session ${this.sessionId}`);
    }

    /**
     * Stop polling for progress updates
     */
    private stopPolling(): void {
        if (this.pollingInterval) {
            window.clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            console.log(`[VerificationProgressModal] Stopped polling for session ${this.sessionId}`);
        }
    }

    /**
     * Fetch progress from API and update display
     * AC-31.6.2: Color distribution real-time updates
     */
    private async fetchAndUpdateProgress(): Promise<void> {
        // Don't poll if session is completed or cancelled
        if (this.progress.status === 'completed' || this.progress.status === 'cancelled') {
            this.stopPolling();
            return;
        }

        try {
            const response = await fetch(
                `${this.apiBaseUrl}/review/session/${encodeURIComponent(this.sessionId)}/progress`,
                {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                }
            );

            if (!response.ok) {
                if (response.status === 404) {
                    // Session no longer exists
                    this.stopPolling();
                    return;
                }
                console.warn(`[VerificationProgressModal] Failed to fetch progress: ${response.status}`);
                return;
            }

            const progress: VerificationProgress = await response.json();
            this.updateProgress(progress);

            // Stop polling if session completed
            if (progress.status === 'completed' || progress.status === 'cancelled') {
                this.stopPolling();
            }
        } catch (error) {
            console.warn(`[VerificationProgressModal] Error fetching progress:`, error);
            // Don't stop polling on temporary network errors
        }
    }

    /**
     * Render main content
     */
    private renderContent(): void {
        const { contentEl } = this;

        // Header
        const header = contentEl.createEl('div', { cls: 'verification-header' });
        header.createEl('h2', {
            text: `Verification - ${this.canvasName}`,
            cls: 'modal-title',
        });

        // Elapsed time
        this.elapsedTimeEl = header.createEl('span', {
            text: '00:00',
            cls: 'elapsed-time',
        });

        // Current concept section
        const conceptSection = contentEl.createEl('div', { cls: 'current-concept-section' });
        conceptSection.createEl('span', { text: 'Current: ', cls: 'concept-label' });
        this.currentConceptEl = conceptSection.createEl('span', {
            text: this.progress.current_concept,
            cls: 'concept-name',
        });

        // Progress bar section
        const progressSection = contentEl.createEl('div', { cls: 'verification-progress-section' });
        const progressBarContainer = progressSection.createEl('div', { cls: 'progress-bar-container' });
        this.progressBarFill = progressBarContainer.createEl('div', { cls: 'progress-bar-fill' });
        this.updateProgressBar();

        this.progressText = progressSection.createEl('p', { cls: 'progress-text' });
        this.updateProgressText();

        // Color distribution section
        this.colorDistributionEl = contentEl.createEl('div', { cls: 'color-distribution' });
        this.updateColorDistribution();

        // Mastery percentage
        this.masteryEl = contentEl.createEl('div', { cls: 'mastery-section' });
        this.updateMastery();

        // Divider
        contentEl.createEl('hr', { cls: 'section-divider' });

        // Q&A Section
        const qaSection = contentEl.createEl('div', { cls: 'qa-section' });

        // Question display
        this.questionEl = qaSection.createEl('div', { cls: 'question-display' });
        this.questionEl.createEl('p', { text: this.currentQuestion, cls: 'question-text' });

        // Hint display (initially hidden)
        this.hintEl = qaSection.createEl('div', { cls: 'hint-display hidden' });

        // Answer input
        const answerSection = qaSection.createEl('div', { cls: 'answer-section' });
        this.answerInputEl = answerSection.createEl('textarea', {
            cls: 'answer-input',
            placeholder: 'Enter your answer here...',
        });
        this.answerInputEl.rows = 4;

        // Submit button
        const submitBtn = answerSection.createEl('button', {
            text: 'Submit Answer',
            cls: 'submit-button primary',
        });
        submitBtn.addEventListener('click', () => this.handleSubmitAnswer());

        // Feedback display (initially hidden)
        this.feedbackEl = qaSection.createEl('div', { cls: 'feedback-display hidden' });

        // Divider
        contentEl.createEl('hr', { cls: 'section-divider' });

        // Control buttons
        this.controlButtonsEl = contentEl.createEl('div', { cls: 'control-buttons' });
        this.renderControlButtons();
    }

    /**
     * Render control buttons based on current state
     */
    private renderControlButtons(): void {
        if (!this.controlButtonsEl) return;
        this.controlButtonsEl.empty();

        if (this.isPaused) {
            // Resume button
            const resumeBtn = this.controlButtonsEl.createEl('button', {
                text: 'Resume',
                cls: 'control-button primary',
            });
            resumeBtn.addEventListener('click', () => this.handleResume());
        } else {
            // Pause button
            const pauseBtn = this.controlButtonsEl.createEl('button', {
                text: 'Pause',
                cls: 'control-button',
            });
            pauseBtn.addEventListener('click', () => this.handlePause());
        }

        // Skip button
        const skipBtn = this.controlButtonsEl.createEl('button', {
            text: 'Skip',
            cls: 'control-button warning',
        });
        skipBtn.addEventListener('click', () => this.handleSkip());

        // End button
        const endBtn = this.controlButtonsEl.createEl('button', {
            text: 'End Session',
            cls: 'control-button danger',
        });
        endBtn.addEventListener('click', () => this.handleEnd());
    }

    /**
     * Update progress bar
     */
    private updateProgressBar(): void {
        if (this.progressBarFill) {
            this.progressBarFill.style.width = `${this.progress.progress_percentage}%`;
        }
    }

    /**
     * Update progress text
     */
    private updateProgressText(): void {
        if (this.progressText) {
            this.progressText.textContent = `${this.progress.progress_percentage}% (${this.progress.completed_concepts}/${this.progress.total_concepts})`;
        }
    }

    /**
     * Update color distribution display
     */
    private updateColorDistribution(): void {
        if (!this.colorDistributionEl) return;
        this.colorDistributionEl.empty();

        const colors = [
            { color: 'green', count: this.progress.green_count, label: 'mastered', emoji: '' },
            { color: 'yellow', count: this.progress.yellow_count, label: 'partial', emoji: '' },
            { color: 'purple', count: this.progress.purple_count, label: 'need review', emoji: '' },
            { color: 'red', count: this.progress.red_count, label: 'not mastered', emoji: '' },
        ];

        for (const { color, count, label, emoji } of colors) {
            const item = this.colorDistributionEl.createEl('div', { cls: `color-item color-${color}` });
            item.createEl('span', { text: `${emoji} ${count} ${label}`, cls: 'color-text' });
        }
    }

    /**
     * Update mastery percentage
     */
    private updateMastery(): void {
        if (this.masteryEl) {
            this.masteryEl.empty();
            this.masteryEl.createEl('span', { text: 'Mastery: ', cls: 'mastery-label' });
            this.masteryEl.createEl('span', {
                text: `${this.progress.mastery_percentage}%`,
                cls: `mastery-value ${this.getMasteryClass()}`,
            });
        }
    }

    /**
     * Get CSS class based on mastery level
     */
    private getMasteryClass(): string {
        if (this.progress.mastery_percentage >= 80) return 'mastery-high';
        if (this.progress.mastery_percentage >= 60) return 'mastery-medium';
        return 'mastery-low';
    }

    /**
     * Start elapsed time timer
     */
    private startElapsedTimer(): void {
        this.elapsedTimer = window.setInterval(() => {
            this.updateElapsedTime();
        }, 1000);
    }

    /**
     * Update elapsed time display
     */
    private updateElapsedTime(): void {
        if (!this.elapsedTimeEl) return;

        const elapsed = Math.floor((Date.now() - this.startTime.getTime()) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        this.elapsedTimeEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }

    /**
     * Handle submit answer
     */
    private async handleSubmitAnswer(): Promise<void> {
        if (this.isAnswering || !this.answerInputEl) return;

        const answer = this.answerInputEl.value.trim();
        if (!answer) {
            new Notice('Please enter an answer', 3000);
            return;
        }

        this.isAnswering = true;
        this.showLoading(true);

        try {
            const response = await this.callbacks.onAnswer(answer);
            this.handleResponse(response);
        } catch (err) {
            console.error('Failed to submit answer:', err);
            new Notice('Failed to submit answer. Please try again.', 5000);
        } finally {
            this.isAnswering = false;
            this.showLoading(false);
        }
    }

    /**
     * Handle response from backend
     */
    private handleResponse(response: QuestionResponse): void {
        // Update progress
        this.progress = response.progress;
        this.updateProgressBar();
        this.updateProgressText();
        this.updateColorDistribution();
        this.updateMastery();

        // Update current concept
        if (this.currentConceptEl) {
            this.currentConceptEl.textContent = response.current_concept;
        }

        // Show feedback
        this.showFeedback(response.quality, response.score);

        // Handle action
        switch (response.action) {
            case 'hint':
                this.showHint(response.hint || '');
                break;
            case 'next':
                this.showNextQuestion(response.next_question || '');
                break;
            case 'complete':
                this.handleComplete();
                break;
        }
    }

    /**
     * Show feedback for answer quality
     */
    private showFeedback(quality: string, score: number): void {
        if (!this.feedbackEl) return;

        this.feedbackEl.empty();
        this.feedbackEl.removeClass('hidden');

        const qualityEmoji = this.getQualityEmoji(quality);
        const qualityText = this.getQualityText(quality);

        this.feedbackEl.createEl('span', {
            text: `${qualityEmoji} ${qualityText} (Score: ${score.toFixed(1)})`,
            cls: `feedback-text quality-${quality}`,
        });

        // Auto-hide after 3 seconds
        setTimeout(() => {
            if (this.feedbackEl) {
                this.feedbackEl.addClass('hidden');
            }
        }, 3000);
    }

    /**
     * Get emoji for quality level
     */
    private getQualityEmoji(quality: string): string {
        switch (quality) {
            case 'excellent': return '';
            case 'good': return '';
            case 'partial': return '';
            case 'wrong': return '';
            default: return '';
        }
    }

    /**
     * Get text for quality level
     */
    private getQualityText(quality: string): string {
        switch (quality) {
            case 'excellent': return 'Excellent!';
            case 'good': return 'Good!';
            case 'partial': return 'Partial understanding';
            case 'wrong': return 'Not quite right';
            default: return quality;
        }
    }

    /**
     * Show hint
     */
    private showHint(hint: string): void {
        if (!this.hintEl) return;

        this.hintEl.empty();
        this.hintEl.removeClass('hidden');
        this.hintEl.createEl('p', { text: hint, cls: 'hint-text' });
        this.hintEl.createEl('p', {
            text: `(Hint ${this.progress.hints_given}/${this.progress.max_hints})`,
            cls: 'hint-count',
        });

        // Clear answer input for retry
        if (this.answerInputEl) {
            this.answerInputEl.value = '';
            this.answerInputEl.focus();
        }
    }

    /**
     * Show next question
     */
    private showNextQuestion(question: string): void {
        this.currentQuestion = question;

        if (this.questionEl) {
            this.questionEl.empty();
            this.questionEl.createEl('p', { text: question, cls: 'question-text' });
        }

        // Hide hint
        if (this.hintEl) {
            this.hintEl.addClass('hidden');
        }

        // Clear answer input
        if (this.answerInputEl) {
            this.answerInputEl.value = '';
            this.answerInputEl.focus();
        }
    }

    /**
     * Handle verification complete
     */
    private handleComplete(): void {
        new Notice(`Verification completed! Mastery: ${this.progress.mastery_percentage}%`, 5000);

        // Show completion summary
        if (this.questionEl) {
            this.questionEl.empty();
            this.questionEl.createEl('h3', { text: 'Verification Complete!', cls: 'complete-title' });
            this.questionEl.createEl('p', {
                text: `You have completed all ${this.progress.total_concepts} concepts.`,
                cls: 'complete-text',
            });
        }

        // Hide answer section
        if (this.answerInputEl) {
            this.answerInputEl.parentElement?.addClass('hidden');
        }

        // Update control buttons
        if (this.controlButtonsEl) {
            this.controlButtonsEl.empty();
            const closeBtn = this.controlButtonsEl.createEl('button', {
                text: 'Close',
                cls: 'control-button primary',
            });
            closeBtn.addEventListener('click', () => this.close());
        }
    }

    /**
     * Handle skip button
     */
    private async handleSkip(): Promise<void> {
        if (this.isAnswering) return;

        this.isAnswering = true;
        this.showLoading(true);

        try {
            const response = await this.callbacks.onSkip();
            this.handleResponse(response);
        } catch (err) {
            console.error('Failed to skip:', err);
            new Notice('Failed to skip. Please try again.', 5000);
        } finally {
            this.isAnswering = false;
            this.showLoading(false);
        }
    }

    /**
     * Handle pause button
     * Story 31.6 AC-31.6.4: Support pause/resume session
     */
    private async handlePause(): Promise<void> {
        try {
            await this.callbacks.onPause();
            this.isPaused = true;
            this.stopPolling(); // Story 31.6: Stop polling when paused
            this.renderControlButtons();
            new Notice('Session paused', 3000);

            // Disable answer input
            if (this.answerInputEl) {
                this.answerInputEl.disabled = true;
            }
        } catch (err) {
            console.error('Failed to pause:', err);
            new Notice('Failed to pause session', 5000);
        }
    }

    /**
     * Handle resume button
     * Story 31.6 AC-31.6.4: Support pause/resume session
     */
    private async handleResume(): Promise<void> {
        try {
            const response = await this.callbacks.onResume();
            this.isPaused = false;
            this.startPolling(); // Story 31.6: Resume polling when session resumes
            this.renderControlButtons();
            this.handleResponse(response);
            new Notice('Session resumed', 3000);

            // Enable answer input
            if (this.answerInputEl) {
                this.answerInputEl.disabled = false;
                this.answerInputEl.focus();
            }
        } catch (err) {
            console.error('Failed to resume:', err);
            new Notice('Failed to resume session', 5000);
        }
    }

    /**
     * Handle end button
     */
    private async handleEnd(): Promise<void> {
        try {
            await this.callbacks.onEnd();
            new Notice(`Session ended. Mastery: ${this.progress.mastery_percentage}%`, 5000);
            this.close();
        } catch (err) {
            console.error('Failed to end session:', err);
            new Notice('Failed to end session', 5000);
        }
    }

    /**
     * Show/hide loading state
     */
    private showLoading(show: boolean): void {
        const submitBtn = this.contentEl.querySelector('.submit-button');
        if (submitBtn) {
            if (show) {
                submitBtn.textContent = 'Submitting...';
                (submitBtn as HTMLButtonElement).disabled = true;
            } else {
                submitBtn.textContent = 'Submit Answer';
                (submitBtn as HTMLButtonElement).disabled = false;
            }
        }
    }

    /**
     * Update progress from external source
     */
    public updateProgress(progress: VerificationProgress): void {
        this.progress = progress;
        this.updateProgressBar();
        this.updateProgressText();
        this.updateColorDistribution();
        this.updateMastery();

        if (this.currentConceptEl) {
            this.currentConceptEl.textContent = progress.current_concept;
        }
    }
}
