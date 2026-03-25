/**
 * TargetedReviewWeightService - Canvas Learning System
 *
 * Story 14.14: 针对性复习问题生成算法
 *
 * Implements calculate_targeted_review_weights() algorithm:
 * - 70% weak concepts (most recent failures weighted highest)
 * - 30% mastered concepts (prevent forgetting)
 *
 * @module TargetedReviewWeightService
 * @version 1.0.0
 */

import { App, requestUrl } from 'obsidian';

/**
 * Weak concept with failure metadata
 */
export interface WeakConcept {
    conceptId: string;
    conceptName: string;
    failureCount: number;
    lastFailureDate: Date;
    averageScore: number;
    trend: 'improving' | 'stable' | 'declining';
}

/**
 * Mastered concept with review metadata
 */
export interface MasteredConcept {
    conceptId: string;
    conceptName: string;
    masteryScore: number;
    lastReviewDate: Date;
    consecutiveSuccesses: number;
}

/**
 * Concept with calculated weight
 */
export interface WeightedConcept {
    conceptName: string;
    weight: number;
    category: 'weak' | 'mastered';
    rawScore: number;
}

/**
 * Weight calculation configuration
 */
export interface WeightConfig {
    weakRatio: number;        // Default: 0.7 (70%)
    masteredRatio: number;    // Default: 0.3 (30%)
    recencyBoost: number;     // Boost for recent failures (default: 1.5)
    declineMultiplier: number; // Extra weight for declining concepts (default: 1.3)
    maxWeakConcepts: number;   // Maximum weak concepts to include
    maxMasteredConcepts: number; // Maximum mastered concepts to include
    minWeight: number;        // Minimum weight threshold
}

/**
 * Default weight configuration
 */
export const DEFAULT_WEIGHT_CONFIG: WeightConfig = {
    weakRatio: 0.7,
    masteredRatio: 0.3,
    recencyBoost: 1.5,
    declineMultiplier: 1.3,
    maxWeakConcepts: 20,
    maxMasteredConcepts: 10,
    minWeight: 0.01,
};

/**
 * Service settings
 */
export interface TargetedReviewSettings {
    apiBaseUrl: string;
    timeout: number;
    weightConfig: WeightConfig;
}

/**
 * Default service settings
 */
export const DEFAULT_TARGETED_REVIEW_SETTINGS: TargetedReviewSettings = {
    apiBaseUrl: 'http://localhost:8000/api/v1',
    timeout: 10000,
    weightConfig: { ...DEFAULT_WEIGHT_CONFIG },
};

/**
 * Weight calculation result
 */
export interface WeightCalculationResult {
    concepts: WeightedConcept[];
    weakCount: number;
    masteredCount: number;
    totalWeight: number;
    timestamp: Date;
}

/**
 * Question distribution for review
 */
export interface QuestionDistribution {
    conceptName: string;
    questionCount: number;
    category: 'weak' | 'mastered';
    weight: number;
}

/**
 * TargetedReviewWeightService
 *
 * Calculates targeted review weights based on weak and mastered concepts.
 * Implements the algorithm specified in Story 14.14.
 */
export class TargetedReviewWeightService {
    private app: App;
    private settings: TargetedReviewSettings;

    constructor(app: App, settings: Partial<TargetedReviewSettings> = {}) {
        this.app = app;
        this.settings = {
            ...DEFAULT_TARGETED_REVIEW_SETTINGS,
            ...settings,
            weightConfig: {
                ...DEFAULT_WEIGHT_CONFIG,
                ...settings.weightConfig,
            },
        };
    }

    /**
     * Get current settings
     */
    getSettings(): TargetedReviewSettings {
        return { ...this.settings };
    }

    /**
     * Update settings
     */
    updateSettings(settings: Partial<TargetedReviewSettings>): void {
        this.settings = {
            ...this.settings,
            ...settings,
            weightConfig: {
                ...this.settings.weightConfig,
                ...settings.weightConfig,
            },
        };
    }

    /**
     * Calculate targeted review weights
     *
     * Core algorithm:
     * - 70% of total weight goes to weak concepts
     * - 30% of total weight goes to mastered concepts
     * - Weak concepts: prioritize recent failures and declining trends
     * - Mastered concepts: prioritize those not reviewed recently
     */
    calculateTargetedReviewWeights(
        weakConcepts: WeakConcept[],
        masteredConcepts: MasteredConcept[],
        config: Partial<WeightConfig> = {}
    ): WeightedConcept[] {
        const cfg = { ...this.settings.weightConfig, ...config };
        const result: WeightedConcept[] = [];

        // Calculate weak concept weights
        const weakWeights = this.calculateWeakConceptWeights(weakConcepts, cfg);

        // Calculate mastered concept weights
        const masteredWeights = this.calculateMasteredConceptWeights(masteredConcepts, cfg);

        // Combine and normalize weights
        const totalWeakRaw = weakWeights.reduce((sum, w) => sum + w.rawScore, 0);
        const totalMasteredRaw = masteredWeights.reduce((sum, w) => sum + w.rawScore, 0);

        // Apply ratio distribution
        for (const w of weakWeights) {
            const normalizedWeight = totalWeakRaw > 0
                ? (w.rawScore / totalWeakRaw) * cfg.weakRatio
                : 0;
            if (normalizedWeight >= cfg.minWeight) {
                result.push({
                    ...w,
                    weight: normalizedWeight,
                });
            }
        }

        for (const m of masteredWeights) {
            const normalizedWeight = totalMasteredRaw > 0
                ? (m.rawScore / totalMasteredRaw) * cfg.masteredRatio
                : 0;
            if (normalizedWeight >= cfg.minWeight) {
                result.push({
                    ...m,
                    weight: normalizedWeight,
                });
            }
        }

        // Sort by weight descending
        result.sort((a, b) => b.weight - a.weight);

        return result;
    }

    /**
     * Calculate weights for weak concepts
     *
     * Factors:
     * - Recency: More recent failures get higher weight
     * - Failure count: More failures = higher weight
     * - Trend: Declining concepts get extra boost
     * - Score: Lower average score = higher weight
     */
    private calculateWeakConceptWeights(
        concepts: WeakConcept[],
        config: WeightConfig
    ): WeightedConcept[] {
        const now = Date.now();
        const dayMs = 24 * 60 * 60 * 1000;
        const results: WeightedConcept[] = [];

        // Limit to max concepts
        const limitedConcepts = concepts.slice(0, config.maxWeakConcepts);

        for (const concept of limitedConcepts) {
            // Calculate recency score (higher for more recent failures)
            const daysSinceFailure = Math.max(1,
                (now - concept.lastFailureDate.getTime()) / dayMs
            );
            const recencyScore = config.recencyBoost / Math.sqrt(daysSinceFailure);

            // Calculate failure intensity score
            const failureScore = Math.min(concept.failureCount, 10) / 10;

            // Calculate score deficit (lower score = higher weight)
            const scoreDeficit = (100 - concept.averageScore) / 100;

            // Apply trend multiplier
            const trendMultiplier = concept.trend === 'declining'
                ? config.declineMultiplier
                : concept.trend === 'stable' ? 1.0 : 0.8;

            // Combined raw score
            const rawScore = (recencyScore + failureScore + scoreDeficit) * trendMultiplier;

            results.push({
                conceptName: concept.conceptName,
                weight: 0, // Will be normalized later
                category: 'weak',
                rawScore,
            });
        }

        return results;
    }

    /**
     * Calculate weights for mastered concepts
     *
     * Factors:
     * - Time since last review: Longer = higher weight (prevent forgetting)
     * - Mastery score: Lower mastery = higher weight
     * - Consecutive successes: Balance - too many might mean overconfidence
     */
    private calculateMasteredConceptWeights(
        concepts: MasteredConcept[],
        config: WeightConfig
    ): WeightedConcept[] {
        const now = Date.now();
        const dayMs = 24 * 60 * 60 * 1000;
        const results: WeightedConcept[] = [];

        // Limit to max concepts
        const limitedConcepts = concepts.slice(0, config.maxMasteredConcepts);

        for (const concept of limitedConcepts) {
            // Time since last review (higher for older reviews)
            const daysSinceReview = Math.max(1,
                (now - concept.lastReviewDate.getTime()) / dayMs
            );
            const recencyScore = Math.log(daysSinceReview + 1);

            // Mastery deficit (even mastered concepts can be reinforced)
            const masteryDeficit = (100 - concept.masteryScore) / 100;

            // Success fatigue (too many successes might indicate need for challenge)
            const successFatigue = concept.consecutiveSuccesses > 5
                ? 0.5 + (0.5 * Math.min(concept.consecutiveSuccesses - 5, 10) / 10)
                : 0.5;

            // Combined raw score
            const rawScore = recencyScore * (1 + masteryDeficit) * successFatigue;

            results.push({
                conceptName: concept.conceptName,
                weight: 0, // Will be normalized later
                category: 'mastered',
                rawScore,
            });
        }

        return results;
    }

    /**
     * Get full calculation result with metadata
     */
    calculateWithMetadata(
        weakConcepts: WeakConcept[],
        masteredConcepts: MasteredConcept[],
        config: Partial<WeightConfig> = {}
    ): WeightCalculationResult {
        const concepts = this.calculateTargetedReviewWeights(
            weakConcepts,
            masteredConcepts,
            config
        );

        const weakCount = concepts.filter(c => c.category === 'weak').length;
        const masteredCount = concepts.filter(c => c.category === 'mastered').length;
        const totalWeight = concepts.reduce((sum, c) => sum + c.weight, 0);

        return {
            concepts,
            weakCount,
            masteredCount,
            totalWeight,
            timestamp: new Date(),
        };
    }

    /**
     * Generate question distribution for a specific number of questions
     *
     * Distributes questions among concepts based on their weights.
     * Ensures at least 1 question per included concept if possible.
     */
    generateQuestionDistribution(
        weightedConcepts: WeightedConcept[],
        totalQuestions: number
    ): QuestionDistribution[] {
        if (weightedConcepts.length === 0 || totalQuestions <= 0) {
            return [];
        }

        const result: QuestionDistribution[] = [];
        let remainingQuestions = totalQuestions;
        const totalWeight = weightedConcepts.reduce((sum, c) => sum + c.weight, 0);

        // First pass: assign based on proportional weights
        const assignments: Map<string, number> = new Map();

        for (const concept of weightedConcepts) {
            const proportion = totalWeight > 0 ? concept.weight / totalWeight : 0;
            const questions = Math.floor(proportion * totalQuestions);
            assignments.set(concept.conceptName, questions);
            remainingQuestions -= questions;
        }

        // Second pass: distribute remaining questions to highest-weight concepts
        const sortedConcepts = [...weightedConcepts].sort((a, b) => b.weight - a.weight);
        let i = 0;
        while (remainingQuestions > 0 && i < sortedConcepts.length) {
            const name = sortedConcepts[i].conceptName;
            assignments.set(name, (assignments.get(name) || 0) + 1);
            remainingQuestions--;
            i++;
        }

        // Build result
        for (const concept of weightedConcepts) {
            const questionCount = assignments.get(concept.conceptName) || 0;
            if (questionCount > 0) {
                result.push({
                    conceptName: concept.conceptName,
                    questionCount,
                    category: concept.category,
                    weight: concept.weight,
                });
            }
        }

        // Sort by question count descending
        result.sort((a, b) => b.questionCount - a.questionCount);

        return result;
    }

    /**
     * Validate distribution against PRD requirements
     *
     * PRD requires: 针对性问题分布符合配置比例（误差≤1）
     */
    validateDistribution(
        distribution: QuestionDistribution[],
        config: Partial<WeightConfig> = {}
    ): { valid: boolean; weakRatio: number; masteredRatio: number; error: number } {
        const cfg = { ...this.settings.weightConfig, ...config };

        const totalQuestions = distribution.reduce((sum, d) => sum + d.questionCount, 0);
        const weakQuestions = distribution
            .filter(d => d.category === 'weak')
            .reduce((sum, d) => sum + d.questionCount, 0);
        const masteredQuestions = distribution
            .filter(d => d.category === 'mastered')
            .reduce((sum, d) => sum + d.questionCount, 0);

        const actualWeakRatio = totalQuestions > 0 ? weakQuestions / totalQuestions : 0;
        const actualMasteredRatio = totalQuestions > 0 ? masteredQuestions / totalQuestions : 0;

        // Calculate error as absolute difference in question counts
        const expectedWeakQuestions = Math.round(cfg.weakRatio * totalQuestions);
        const expectedMasteredQuestions = Math.round(cfg.masteredRatio * totalQuestions);

        const weakError = Math.abs(weakQuestions - expectedWeakQuestions);
        const masteredError = Math.abs(masteredQuestions - expectedMasteredQuestions);
        const maxError = Math.max(weakError, masteredError);

        return {
            valid: maxError <= 1,
            weakRatio: actualWeakRatio,
            masteredRatio: actualMasteredRatio,
            error: maxError,
        };
    }

    /**
     * Fetch weak concepts from backend (Story 14.13 integration)
     */
    async fetchWeakConcepts(canvasPath: string, lookbackDays: number = 30): Promise<WeakConcept[]> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/graphiti/weak-concepts`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    canvas_path: canvasPath,
                    lookback_days: lookbackDays,
                }),
                throw: false,
            });

            if (response.status === 200 && response.json?.concepts) {
                return response.json.concepts.map((c: any) => ({
                    conceptId: c.concept_id,
                    conceptName: c.concept_name,
                    failureCount: c.failure_count,
                    lastFailureDate: new Date(c.last_failure_date),
                    averageScore: c.average_score,
                    trend: c.trend,
                }));
            }

            return [];
        } catch (error) {
            console.error('Error fetching weak concepts:', error);
            return [];
        }
    }

    /**
     * Fetch mastered concepts from backend
     */
    async fetchMasteredConcepts(canvasPath: string): Promise<MasteredConcept[]> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/graphiti/mastered-concepts`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    canvas_path: canvasPath,
                }),
                throw: false,
            });

            if (response.status === 200 && response.json?.concepts) {
                return response.json.concepts.map((c: any) => ({
                    conceptId: c.concept_id,
                    conceptName: c.concept_name,
                    masteryScore: c.mastery_score,
                    lastReviewDate: new Date(c.last_review_date),
                    consecutiveSuccesses: c.consecutive_successes,
                }));
            }

            return [];
        } catch (error) {
            console.error('Error fetching mastered concepts:', error);
            return [];
        }
    }

    /**
     * Calculate weights for a canvas (convenience method)
     */
    async calculateForCanvas(
        canvasPath: string,
        config: Partial<WeightConfig> = {}
    ): Promise<WeightCalculationResult> {
        const [weakConcepts, masteredConcepts] = await Promise.all([
            this.fetchWeakConcepts(canvasPath),
            this.fetchMasteredConcepts(canvasPath),
        ]);

        return this.calculateWithMetadata(weakConcepts, masteredConcepts, config);
    }

    /**
     * Generate optimized question set for a canvas
     */
    async generateQuestionSetForCanvas(
        canvasPath: string,
        questionCount: number,
        config: Partial<WeightConfig> = {}
    ): Promise<{
        distribution: QuestionDistribution[];
        validation: { valid: boolean; weakRatio: number; masteredRatio: number; error: number };
        metadata: WeightCalculationResult;
    }> {
        const metadata = await this.calculateForCanvas(canvasPath, config);
        const distribution = this.generateQuestionDistribution(
            metadata.concepts,
            questionCount
        );
        const validation = this.validateDistribution(distribution, config);

        return {
            distribution,
            validation,
            metadata,
        };
    }

    /**
     * Get statistics for weight calculation
     */
    getWeightStatistics(concepts: WeightedConcept[]): {
        weakTotal: number;
        masteredTotal: number;
        avgWeakWeight: number;
        avgMasteredWeight: number;
        maxWeight: number;
        minWeight: number;
    } {
        const weakConcepts = concepts.filter(c => c.category === 'weak');
        const masteredConcepts = concepts.filter(c => c.category === 'mastered');

        const weakTotal = weakConcepts.reduce((sum, c) => sum + c.weight, 0);
        const masteredTotal = masteredConcepts.reduce((sum, c) => sum + c.weight, 0);

        const avgWeakWeight = weakConcepts.length > 0
            ? weakTotal / weakConcepts.length
            : 0;
        const avgMasteredWeight = masteredConcepts.length > 0
            ? masteredTotal / masteredConcepts.length
            : 0;

        const weights = concepts.map(c => c.weight);
        const maxWeight = weights.length > 0 ? Math.max(...weights) : 0;
        const minWeight = weights.length > 0 ? Math.min(...weights) : 0;

        return {
            weakTotal,
            masteredTotal,
            avgWeakWeight,
            avgMasteredWeight,
            maxWeight,
            minWeight,
        };
    }
}

/**
 * Factory function
 */
export function createTargetedReviewWeightService(
    app: App,
    settings?: Partial<TargetedReviewSettings>
): TargetedReviewWeightService {
    return new TargetedReviewWeightService(app, settings);
}
