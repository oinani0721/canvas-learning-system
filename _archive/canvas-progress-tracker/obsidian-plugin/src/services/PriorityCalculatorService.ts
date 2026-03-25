/**
 * PriorityCalculatorService - Multi-Dimensional Priority Calculation
 *
 * Story 14.11: 多维度优先级计算
 *
 * Implements 4-dimensional priority calculation:
 * - FSRS Urgency (40%): Spaced repetition urgency based on forgetting curve
 * - Behavior Weight (30%): Learning behavior patterns from Temporal Memory
 * - Network Centrality (20%): Concept importance from Graphiti knowledge graph
 * - Interaction Weight (10%): Document interaction from Semantic Memory
 *
 * @module PriorityCalculatorService
 * @version 1.0.0
 */

import { App } from 'obsidian';
import {
    ConceptRelationship,
    TemporalEvent,
    SemanticResult,
    MemoryQueryResult,
} from './MemoryQueryService';

// =============================================================================
// Types and Interfaces
// =============================================================================

/**
 * FSRS card state for urgency calculation
 */
export interface FSRSCardState {
    /** Concept/card identifier */
    conceptId: string;
    /** Card stability (S) - days until 90% retention drops to target */
    stability: number;
    /** Card difficulty (D) - 1-10 scale */
    difficulty: number;
    /** Last review timestamp */
    lastReview: Date;
    /** Next scheduled review */
    nextReview: Date;
    /** Current repetition count */
    reps: number;
    /** Current lapses count */
    lapses: number;
    /** Current state: new, learning, review, relearning */
    state: 'new' | 'learning' | 'review' | 'relearning';
}

/**
 * Priority calculation weights configuration
 */
export interface PriorityWeights {
    /** FSRS urgency weight (default 0.4) */
    fsrsWeight: number;
    /** Behavior weight (default 0.3) */
    behaviorWeight: number;
    /** Network centrality weight (default 0.2) */
    networkWeight: number;
    /** Interaction weight (default 0.1) */
    interactionWeight: number;
}

/**
 * Individual dimension score with explanation
 */
export interface DimensionScore {
    /** Score value (0-100) */
    score: number;
    /** Explanation of how score was calculated */
    explanation: string;
    /** Raw factors used in calculation */
    factors: Record<string, number>;
}

/**
 * Complete priority calculation result
 */
export interface PriorityResult {
    /** Concept being evaluated */
    conceptId: string;
    /** Canvas name */
    canvasName?: string;
    /** Final weighted priority score (0-100) */
    priorityScore: number;
    /** Individual dimension scores */
    dimensions: {
        fsrs: DimensionScore;
        behavior: DimensionScore;
        network: DimensionScore;
        interaction: DimensionScore;
    };
    /** Weights used in calculation */
    weightsUsed: PriorityWeights;
    /** Calculation timestamp */
    calculatedAt: Date;
    /** Recommended review date based on priority */
    recommendedReviewDate: Date;
    /** Priority tier for UI display */
    priorityTier: 'critical' | 'high' | 'medium' | 'low';
    /** Story 38.3 AC-2: Whether FSRS data was unavailable for this calculation */
    fsrsUnavailable?: boolean;
    /** Story 30.17: Dimensions that used degraded/fallback values */
    degradedDimensions: string[];
}

/**
 * Priority calculator settings
 */
export interface PriorityCalculatorSettings {
    /** Custom weights (optional) */
    weights: PriorityWeights;
    /** Target retention rate for FSRS (default 0.9) */
    targetRetention: number;
    /** Days threshold for "stale" concept (default 7) */
    staleDaysThreshold: number;
    /** Minimum events for behavior analysis (default 3) */
    minEventsForBehavior: number;
    /** Whether to boost priority for prerequisite concepts */
    boostPrerequisites: boolean;
}

/**
 * Default weights (from PRD)
 */
export const DEFAULT_PRIORITY_WEIGHTS: PriorityWeights = {
    fsrsWeight: 0.4,
    behaviorWeight: 0.3,
    networkWeight: 0.2,
    interactionWeight: 0.1,
};

/**
 * Default settings
 */
export const DEFAULT_PRIORITY_CALCULATOR_SETTINGS: PriorityCalculatorSettings = {
    weights: DEFAULT_PRIORITY_WEIGHTS,
    targetRetention: 0.9,
    staleDaysThreshold: 7,
    minEventsForBehavior: 3,
    boostPrerequisites: true,
};

// =============================================================================
// PriorityCalculatorService Class
// =============================================================================

/**
 * Service for calculating multi-dimensional review priorities
 *
 * PRD Reference: FR3.2 聚合逻辑升级 - 多维度优先级计算
 * Formula: FSRS(40%) + 行为(30%) + 关系(20%) + 交互(10%)
 */
export class PriorityCalculatorService {
    private app: App;
    private settings: PriorityCalculatorSettings;

    constructor(app: App, settings?: Partial<PriorityCalculatorSettings>) {
        this.app = app;
        this.settings = {
            ...DEFAULT_PRIORITY_CALCULATOR_SETTINGS,
            ...settings,
            weights: {
                ...DEFAULT_PRIORITY_WEIGHTS,
                ...settings?.weights,
            },
        };
    }

    /**
     * Update service settings
     */
    updateSettings(settings: Partial<PriorityCalculatorSettings>): void {
        this.settings = {
            ...this.settings,
            ...settings,
            weights: {
                ...this.settings.weights,
                ...settings?.weights,
            },
        };
    }

    /**
     * Get current settings
     */
    getSettings(): PriorityCalculatorSettings {
        return {
            ...this.settings,
            weights: { ...this.settings.weights },
        };
    }

    /**
     * Calculate multi-dimensional priority for a concept
     *
     * @param conceptId - Concept identifier
     * @param fsrsState - FSRS card state (optional, uses defaults if not provided)
     * @param memoryResult - Memory query result from MemoryQueryService
     * @param canvasName - Canvas name (optional)
     */
    calculatePriority(
        conceptId: string,
        fsrsState: FSRSCardState | null,
        memoryResult: MemoryQueryResult | null,
        canvasName?: string
    ): PriorityResult {
        const weights = this.settings.weights;

        // Calculate each dimension
        const fsrsScore = this.calculateFSRSUrgency(fsrsState);
        const behaviorScore = this.calculateBehaviorWeight(
            memoryResult?.temporalResults || []
        );
        const networkScore = this.calculateNetworkCentrality(
            memoryResult?.graphitiResults || []
        );
        const interactionScore = this.calculateInteractionWeight(
            memoryResult?.semanticResults || []
        );

        // Story 30.17: Collect degraded dimensions
        const degradedDimensions: string[] = [];
        if (fsrsState === null) {
            degradedDimensions.push('fsrs');
        }
        if (!memoryResult || memoryResult.temporalResults.length === 0) {
            degradedDimensions.push('behavior');
        }
        if (!memoryResult || memoryResult.graphitiResults.length === 0) {
            degradedDimensions.push('network');
        }
        if (!memoryResult || memoryResult.semanticResults.length === 0) {
            degradedDimensions.push('interaction');
        }

        if (degradedDimensions.length > 0) {
            console.warn(
                `[PriorityCalculator] Concept "${conceptId}": ${degradedDimensions.length}/4 dimensions degraded [${degradedDimensions.join(', ')}]. Priority score is an estimate.`
            );
        }

        // Calculate weighted final score
        const priorityScore = Math.round(
            fsrsScore.score * weights.fsrsWeight +
            behaviorScore.score * weights.behaviorWeight +
            networkScore.score * weights.networkWeight +
            interactionScore.score * weights.interactionWeight
        );

        // Determine priority tier
        const priorityTier = this.determinePriorityTier(priorityScore);

        // Calculate recommended review date
        const recommendedReviewDate = this.calculateRecommendedReviewDate(
            priorityScore,
            fsrsState
        );

        return {
            conceptId,
            canvasName,
            priorityScore,
            dimensions: {
                fsrs: fsrsScore,
                behavior: behaviorScore,
                network: networkScore,
                interaction: interactionScore,
            },
            weightsUsed: { ...weights },
            calculatedAt: new Date(),
            recommendedReviewDate,
            priorityTier,
            // Story 38.3 AC-2: Flag when FSRS data was unavailable
            fsrsUnavailable: fsrsState === null,
            // Story 30.17: Track which dimensions used fallback values
            degradedDimensions,
        };
    }

    /**
     * Batch calculate priorities for multiple concepts
     */
    calculateBatchPriorities(
        items: Array<{
            conceptId: string;
            fsrsState: FSRSCardState | null;
            memoryResult: MemoryQueryResult | null;
            canvasName?: string;
        }>
    ): PriorityResult[] {
        return items.map(item =>
            this.calculatePriority(
                item.conceptId,
                item.fsrsState,
                item.memoryResult,
                item.canvasName
            )
        );
    }

    /**
     * Calculate FSRS urgency score (40%)
     *
     * Based on:
     * - Days overdue vs stability
     * - Current card state
     * - Difficulty level
     */
    private calculateFSRSUrgency(state: FSRSCardState | null): DimensionScore {
        if (!state) {
            console.warn('[PriorityCalculator] FSRS data unavailable — using degraded neutral score (50). Priority accuracy reduced.');
            return {
                score: 50, // Neutral when no FSRS data
                explanation: 'No FSRS data available, using neutral score (degraded)',
                factors: {},
            };
        }

        const now = new Date();
        const daysSinceReview = Math.max(
            0,
            (now.getTime() - state.lastReview.getTime()) / (24 * 60 * 60 * 1000)
        );
        const daysUntilDue = (state.nextReview.getTime() - now.getTime()) / (24 * 60 * 60 * 1000);

        let urgencyScore = 50; // Base score
        let explanation = '';

        // Factor 1: Overdue status (most important)
        if (daysUntilDue < 0) {
            // Overdue - exponential increase in urgency
            const daysOverdue = Math.abs(daysUntilDue);
            const overdueMultiplier = Math.min(2, 1 + daysOverdue / Math.max(0.1, state.stability));
            urgencyScore = Math.min(100, 70 + daysOverdue * 3 * overdueMultiplier);
            explanation = `Overdue by ${Math.round(daysOverdue)} days`;
        } else if (daysUntilDue < 1) {
            // Due today
            urgencyScore = 80;
            explanation = 'Due today';
        } else if (daysUntilDue < 3) {
            // Due soon
            urgencyScore = 60 + (3 - daysUntilDue) * 5;
            explanation = `Due in ${Math.round(daysUntilDue)} days`;
        } else {
            // Not urgent
            urgencyScore = Math.max(20, 50 - daysUntilDue * 2);
            explanation = `Not due for ${Math.round(daysUntilDue)} days`;
        }

        // Factor 2: Card state modifier
        const stateModifiers: Record<string, number> = {
            'new': 5,
            'learning': 10,
            'relearning': 15, // Lapsed cards need more attention
            'review': 0,
        };
        urgencyScore += stateModifiers[state.state] || 0;

        // Factor 3: Difficulty modifier
        // Higher difficulty = higher urgency for same interval
        const difficultyBonus = (state.difficulty - 5) * 2; // -8 to +10
        urgencyScore += difficultyBonus;

        // Factor 4: Lapses penalty
        if (state.lapses > 0) {
            urgencyScore += Math.min(10, state.lapses * 3);
            explanation += `, ${state.lapses} lapses`;
        }

        // Clamp to 0-100
        urgencyScore = Math.max(0, Math.min(100, Math.round(urgencyScore)));

        return {
            score: urgencyScore,
            explanation,
            factors: {
                daysSinceReview,
                daysUntilDue,
                stability: state.stability,
                difficulty: state.difficulty,
                lapses: state.lapses,
                state: ['new', 'learning', 'review', 'relearning'].indexOf(state.state),
            },
        };
    }

    /**
     * Calculate behavior weight score (30%)
     *
     * Based on Temporal Memory events:
     * - Recency of learning events
     * - Frequency of engagement
     * - Event types (decomposition, explanation, scoring)
     */
    private calculateBehaviorWeight(events: TemporalEvent[]): DimensionScore {
        if (events.length === 0) {
            console.warn('[PriorityCalculator] Behavior data unavailable — no temporal events. Using degraded neutral score (50).');
            return {
                score: 50,
                explanation: 'No learning events recorded (degraded)',
                factors: {},
            };
        }

        const now = new Date();
        const oneDay = 24 * 60 * 60 * 1000;

        // Sort events by timestamp (newest first)
        const sortedEvents = [...events].sort(
            (a, b) => b.timestamp.getTime() - a.timestamp.getTime()
        );

        // Factor 1: Recency (most recent event)
        const mostRecentEvent = sortedEvents[0];
        const daysSinceLastEvent = (now.getTime() - mostRecentEvent.timestamp.getTime()) / oneDay;

        let recencyScore = 50;
        if (daysSinceLastEvent > this.settings.staleDaysThreshold) {
            // Stale - needs attention
            recencyScore = 70 + Math.min(30, (daysSinceLastEvent - this.settings.staleDaysThreshold) * 3);
        } else if (daysSinceLastEvent < 1) {
            // Very recent - less urgent
            recencyScore = 20;
        } else {
            // Normal range
            recencyScore = 30 + daysSinceLastEvent * 5;
        }

        // Factor 2: Event frequency (more events = more engaged, maybe struggling)
        const recentEvents = events.filter(
            e => (now.getTime() - e.timestamp.getTime()) / oneDay < 7
        );
        const frequencyScore = Math.min(30, recentEvents.length * 5);

        // Factor 3: Event type weighting
        const typeWeights: Record<string, number> = {
            'decomposition': 15, // Needed help breaking down
            'explanation': 10,
            'scoring': 5,
            'learning': 5,
            'review': 0,
        };

        let typeBonus = 0;
        for (const event of sortedEvents.slice(0, 5)) {
            typeBonus += typeWeights[event.eventType] || 0;
        }
        typeBonus = Math.min(20, typeBonus);

        // Combine factors
        const behaviorScore = Math.round(
            recencyScore * 0.5 + frequencyScore + typeBonus
        );

        return {
            score: Math.max(0, Math.min(100, behaviorScore)),
            explanation: `Last activity ${Math.round(daysSinceLastEvent)} days ago, ${recentEvents.length} events in past week`,
            factors: {
                daysSinceLastEvent,
                totalEvents: events.length,
                recentEventCount: recentEvents.length,
                mostRecentType: mostRecentEvent.eventType as unknown as number,
            },
        };
    }

    /**
     * Calculate network centrality score (20%)
     *
     * Based on Graphiti knowledge graph:
     * - Number of relationships
     * - Relationship strength
     * - Prerequisite status (is this a foundation concept?)
     */
    private calculateNetworkCentrality(relationships: ConceptRelationship[]): DimensionScore {
        if (relationships.length === 0) {
            console.warn('[PriorityCalculator] Network data unavailable — no concept relationships. Using degraded neutral score (50).');
            return {
                score: 50,
                explanation: 'No concept relationships found (degraded)',
                factors: {},
            };
        }

        // Factor 1: Connection count (more connections = more important)
        const connectionScore = Math.min(40, relationships.length * 8);

        // Factor 2: Average relationship strength
        const avgStrength = relationships.reduce((sum, r) => sum + r.strength, 0) / relationships.length;
        const strengthScore = avgStrength * 30;

        // Factor 3: Prerequisite boost (if this concept is a prerequisite for others)
        const isPrerequisite = relationships.some(r => r.relationType === 'prerequisite');
        let prerequisiteBonus = 0;
        if (this.settings.boostPrerequisites && isPrerequisite) {
            // Count how many concepts depend on this
            const dependentCount = relationships.filter(
                r => r.relationType === 'prerequisite'
            ).length;
            prerequisiteBonus = Math.min(20, dependentCount * 5);
        }

        // Factor 4: Relationship type diversity
        const uniqueTypes = new Set(relationships.map(r => r.relationType));
        const diversityBonus = Math.min(10, (uniqueTypes.size - 1) * 3);

        const networkScore = Math.round(
            connectionScore + strengthScore + prerequisiteBonus + diversityBonus
        );

        return {
            score: Math.max(0, Math.min(100, networkScore)),
            explanation: `${relationships.length} connections, avg strength ${(avgStrength * 100).toFixed(0)}%` +
                (isPrerequisite ? ', prerequisite concept' : ''),
            factors: {
                connectionCount: relationships.length,
                avgStrength,
                isPrerequisite: isPrerequisite ? 1 : 0,
                uniqueRelationTypes: uniqueTypes.size,
            },
        };
    }

    /**
     * Calculate interaction weight score (10%)
     *
     * Based on Semantic Memory results:
     * - Relevance scores of related documents
     * - Document access patterns
     */
    private calculateInteractionWeight(results: SemanticResult[]): DimensionScore {
        if (results.length === 0) {
            console.warn('[PriorityCalculator] Interaction data unavailable — no semantic results. Using degraded neutral score (50).');
            return {
                score: 50,
                explanation: 'No document interactions found (degraded)',
                factors: {},
            };
        }

        // Factor 1: Average relevance
        const avgRelevance = results.reduce((sum, r) => sum + r.relevanceScore, 0) / results.length;
        const relevanceScore = avgRelevance * 50;

        // Factor 2: Document count (more related docs = more important concept)
        const docCountScore = Math.min(30, results.length * 6);

        // Factor 3: Document type bonus
        const typeBonus: Record<string, number> = {
            'explanation': 10,
            'example': 8,
            'note': 5,
            'canvas': 3,
        };

        let typeBonusTotal = 0;
        for (const result of results.slice(0, 5)) {
            typeBonusTotal += typeBonus[result.documentType] || 0;
        }
        typeBonusTotal = Math.min(20, typeBonusTotal);

        const interactionScore = Math.round(relevanceScore + docCountScore + typeBonusTotal);

        return {
            score: Math.max(0, Math.min(100, interactionScore)),
            explanation: `${results.length} related documents, avg relevance ${(avgRelevance * 100).toFixed(0)}%`,
            factors: {
                documentCount: results.length,
                avgRelevance,
                topRelevance: results[0]?.relevanceScore || 0,
            },
        };
    }

    /**
     * Determine priority tier for UI display
     */
    private determinePriorityTier(score: number): 'critical' | 'high' | 'medium' | 'low' {
        if (score >= 80) return 'critical';
        if (score >= 60) return 'high';
        if (score >= 40) return 'medium';
        return 'low';
    }

    /**
     * Calculate recommended review date based on priority
     */
    private calculateRecommendedReviewDate(
        priorityScore: number,
        fsrsState: FSRSCardState | null
    ): Date {
        const now = new Date();

        // If FSRS has a next review date and it's in the future, use it as base
        if (fsrsState && fsrsState.nextReview > now) {
            // Adjust based on priority score
            if (priorityScore >= 80) {
                // Critical - review ASAP
                return now;
            } else if (priorityScore >= 60) {
                // High - review within a day
                const tomorrow = new Date(now);
                tomorrow.setDate(tomorrow.getDate() + 1);
                return tomorrow;
            } else {
                // Use FSRS scheduled date
                return fsrsState.nextReview;
            }
        }

        // No FSRS data or overdue - base on priority score
        const daysToAdd = Math.max(0, Math.floor((100 - priorityScore) / 10));
        const reviewDate = new Date(now);
        reviewDate.setDate(reviewDate.getDate() + daysToAdd);
        return reviewDate;
    }

    /**
     * Sort concepts by priority (highest first)
     */
    sortByPriority(results: PriorityResult[]): PriorityResult[] {
        return [...results].sort((a, b) => b.priorityScore - a.priorityScore);
    }

    /**
     * Filter concepts by priority tier
     */
    filterByTier(
        results: PriorityResult[],
        tier: 'critical' | 'high' | 'medium' | 'low'
    ): PriorityResult[] {
        return results.filter(r => r.priorityTier === tier);
    }

    /**
     * Get concepts needing review today
     */
    getConceptsNeedingReviewToday(results: PriorityResult[]): PriorityResult[] {
        const today = new Date();
        today.setHours(23, 59, 59, 999);

        return results.filter(r => r.recommendedReviewDate <= today);
    }
}

// =============================================================================
// Factory Function
// =============================================================================

/**
 * Create a new PriorityCalculatorService instance
 */
export function createPriorityCalculatorService(
    app: App,
    settings?: Partial<PriorityCalculatorSettings>
): PriorityCalculatorService {
    return new PriorityCalculatorService(app, settings);
}
