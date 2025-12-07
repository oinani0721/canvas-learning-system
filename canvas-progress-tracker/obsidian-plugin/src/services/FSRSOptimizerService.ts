/**
 * FSRSOptimizerService - Canvas Learning System
 *
 * Story 14.12: FSRS参数优化功能（FR3.6）
 * 从真实学习行为数据中动态优化FSRS的17个参数
 *
 * @module FSRSOptimizerService
 * @version 1.0.0
 */

import { App, requestUrl } from 'obsidian';

// ============================================================================
// Types and Interfaces
// ============================================================================

/**
 * FSRS默认17参数（基于py-fsrs库）
 * These are the default weights used in FSRS-4.5 algorithm
 */
export const DEFAULT_FSRS_PARAMETERS: number[] = [
    0.4,   // w[0]: Initial stability for Again
    0.6,   // w[1]: Initial stability for Hard
    2.4,   // w[2]: Initial stability for Good
    5.8,   // w[3]: Initial stability for Easy
    4.93,  // w[4]: Difficulty weight
    0.94,  // w[5]: Stability decay
    0.86,  // w[6]: Difficulty reversion
    0.01,  // w[7]: Stability after lapse
    1.49,  // w[8]: Hard penalty factor
    0.14,  // w[9]: Easy bonus factor
    0.94,  // w[10]: Stability increase base
    2.18,  // w[11]: Difficulty stability modifier
    0.05,  // w[12]: Stability decrease
    0.34,  // w[13]: Stability growth
    1.26,  // w[14]: Interval modifier
    0.29,  // w[15]: Difficulty modifier
    2.61,  // w[16]: Stability damping
];

/**
 * 复习记录数据
 */
export interface ReviewRecord {
    conceptId: string;
    conceptName: string;
    reviewTime: Date;
    rating: 1 | 2 | 3 | 4; // Again, Hard, Good, Easy
    interval: number; // Days since last review
    stability: number;
    difficulty: number;
    retention: number; // Actual retention rate (0-1)
    success: boolean;
}

/**
 * 训练数据点
 */
export interface TrainingDataPoint {
    deltaT: number; // Review interval in days
    rating: 1 | 2 | 3 | 4;
    retention: number; // Actual retention
    conceptDifficulty: number;
    docEngagement: number;
    prerequisiteReadiness: number;
}

/**
 * 优化结果
 */
export interface OptimizationResult {
    parameters: number[];
    metrics: OptimizationMetrics;
    isOptimized: boolean;
    lastOptimizationTime: Date;
}

/**
 * 优化指标
 */
export interface OptimizationMetrics {
    sampleSize: number;
    rmse: number;
    dataQualityScore: number;
    improvementPercent: number;
    convergenceIterations: number;
}

/**
 * 优化器设置
 */
export interface FSRSOptimizerSettings {
    apiBaseUrl: string;
    timeout: number;
    minSamples: number;
    maxIterations: number;
    learningRate: number;
    convergenceThreshold: number;
    autoOptimizeInterval: number; // Reviews count for auto re-optimize
    monthlyOptimizationEnabled: boolean;
    monthlyOptimizationDay: number; // Day of month (1-28)
    monthlyOptimizationHour: number; // Hour (0-23)
}

/**
 * A/B测试配置
 */
export interface ABTestConfig {
    enabled: boolean;
    testGroupRatio: number; // Percentage using optimized params (0-1)
    trackingPeriodDays: number;
    minimumSamplesPerGroup: number;
}

/**
 * A/B测试结果
 */
export interface ABTestResult {
    controlGroup: {
        sampleSize: number;
        avgRetention: number;
        avgAccuracy: number;
    };
    testGroup: {
        sampleSize: number;
        avgRetention: number;
        avgAccuracy: number;
    };
    winner: 'control' | 'test' | 'inconclusive';
    confidence: number;
    improvementPercent: number;
}

/**
 * 默认设置
 */
export const DEFAULT_OPTIMIZER_SETTINGS: FSRSOptimizerSettings = {
    apiBaseUrl: 'http://localhost:8001/api/v1',
    timeout: 30000,
    minSamples: 100,
    maxIterations: 100,
    learningRate: 0.01,
    convergenceThreshold: 0.0001,
    autoOptimizeInterval: 50,
    monthlyOptimizationEnabled: true,
    monthlyOptimizationDay: 1,
    monthlyOptimizationHour: 3,
};

/**
 * 默认A/B测试配置
 */
export const DEFAULT_AB_TEST_CONFIG: ABTestConfig = {
    enabled: false,
    testGroupRatio: 0.5,
    trackingPeriodDays: 30,
    minimumSamplesPerGroup: 50,
};

// ============================================================================
// FSRSOptimizerService Class
// ============================================================================

/**
 * FSRS参数优化服务
 * 实现从3层记忆系统数据中优化FSRS参数
 */
export class FSRSOptimizerService {
    private app: App;
    private settings: FSRSOptimizerSettings;
    private abTestConfig: ABTestConfig;
    private currentParameters: number[];
    private optimizedParameters: number[] | null = null;
    private lastOptimization: OptimizationResult | null = null;
    private reviewsSinceOptimization: number = 0;
    private dataManager: any = null;
    private scheduledOptimizationTimer: NodeJS.Timeout | null = null;
    private abTestResults: Map<string, { group: 'control' | 'test'; reviews: ReviewRecord[] }> = new Map();

    constructor(
        app: App,
        settings: Partial<FSRSOptimizerSettings> = {},
        abTestConfig: Partial<ABTestConfig> = {}
    ) {
        this.app = app;
        this.settings = { ...DEFAULT_OPTIMIZER_SETTINGS, ...settings };
        this.abTestConfig = { ...DEFAULT_AB_TEST_CONFIG, ...abTestConfig };
        this.currentParameters = [...DEFAULT_FSRS_PARAMETERS];
    }

    // ============================================================================
    // Settings Management
    // ============================================================================

    /**
     * 获取当前设置
     */
    getSettings(): FSRSOptimizerSettings {
        return { ...this.settings };
    }

    /**
     * 更新设置
     */
    updateSettings(newSettings: Partial<FSRSOptimizerSettings>): void {
        this.settings = { ...this.settings, ...newSettings };
    }

    /**
     * 获取A/B测试配置
     */
    getABTestConfig(): ABTestConfig {
        return { ...this.abTestConfig };
    }

    /**
     * 更新A/B测试配置
     */
    updateABTestConfig(config: Partial<ABTestConfig>): void {
        this.abTestConfig = { ...this.abTestConfig, ...config };
    }

    /**
     * 设置数据管理器
     */
    setDataManager(dataManager: any): void {
        this.dataManager = dataManager;
    }

    // ============================================================================
    // Parameter Management
    // ============================================================================

    /**
     * 获取当前使用的参数
     */
    getCurrentParameters(): number[] {
        return [...this.currentParameters];
    }

    /**
     * 获取优化后的参数（如果有）
     */
    getOptimizedParameters(): number[] | null {
        return this.optimizedParameters ? [...this.optimizedParameters] : null;
    }

    /**
     * 获取上次优化结果
     */
    getLastOptimizationResult(): OptimizationResult | null {
        return this.lastOptimization;
    }

    /**
     * 是否使用优化参数
     */
    isUsingOptimizedParameters(): boolean {
        return this.optimizedParameters !== null;
    }

    // ============================================================================
    // Core Optimization Logic
    // ============================================================================

    /**
     * 从3层记忆系统数据优化FSRS参数
     * 核心优化函数 - FR3.6
     */
    async optimizeParameters(): Promise<OptimizationResult> {
        // Step 1: 获取历史复习数据
        const reviewHistory = await this.fetchReviewHistory();

        if (reviewHistory.length < this.settings.minSamples) {
            console.warn(`⚠️ 复习样本不足(${reviewHistory.length}<${this.settings.minSamples}),使用默认FSRS参数`);
            return {
                parameters: [...DEFAULT_FSRS_PARAMETERS],
                metrics: {
                    sampleSize: reviewHistory.length,
                    rmse: 0,
                    dataQualityScore: 0,
                    improvementPercent: 0,
                    convergenceIterations: 0,
                },
                isOptimized: false,
                lastOptimizationTime: new Date(),
            };
        }

        // Step 2: 获取概念网络影响
        const conceptInfluence = await this.fetchConceptNetworkInfluence(reviewHistory);

        // Step 3: 获取文档交互模式
        const docInteractions = await this.fetchDocumentInteractions(reviewHistory);

        // Step 4: 准备训练数据
        const trainingData = this.prepareTrainingData(
            reviewHistory,
            conceptInfluence,
            docInteractions
        );

        // Step 5: 执行梯度下降优化
        const optimizationResult = this.runGradientDescentOptimization(trainingData);

        // Step 6: 评估优化效果
        const evaluationMetrics = this.evaluateOptimization(
            trainingData,
            DEFAULT_FSRS_PARAMETERS,
            optimizationResult.parameters
        );

        // Step 7: 计算数据质量评分
        const dataQualityScore = this.calculateDataQuality(trainingData);

        const result: OptimizationResult = {
            parameters: optimizationResult.parameters,
            metrics: {
                sampleSize: trainingData.length,
                rmse: evaluationMetrics.newRmse,
                dataQualityScore,
                improvementPercent: evaluationMetrics.improvementPercent,
                convergenceIterations: optimizationResult.iterations,
            },
            isOptimized: true,
            lastOptimizationTime: new Date(),
        };

        // 保存结果
        this.lastOptimization = result;
        this.optimizedParameters = result.parameters;
        this.reviewsSinceOptimization = 0;

        console.log(`✅ FSRS参数优化完成: RMSE=${result.metrics.rmse.toFixed(4)}, ` +
            `样本数=${result.metrics.sampleSize}, 质量评分=${result.metrics.dataQualityScore.toFixed(2)}`);

        return result;
    }

    /**
     * 应用优化后的参数
     */
    applyOptimizedParameters(): boolean {
        if (!this.optimizedParameters) {
            return false;
        }
        this.currentParameters = [...this.optimizedParameters];
        return true;
    }

    /**
     * 重置为默认参数
     */
    resetToDefaultParameters(): void {
        this.currentParameters = [...DEFAULT_FSRS_PARAMETERS];
        this.optimizedParameters = null;
    }

    // ============================================================================
    // Data Fetching
    // ============================================================================

    /**
     * 从Temporal Memory获取历史复习数据
     */
    async fetchReviewHistory(): Promise<ReviewRecord[]> {
        if (!this.dataManager) {
            return this.fetchReviewHistoryFromAPI();
        }

        try {
            const dao = this.dataManager.getReviewRecordDAO();
            const allRecords = await dao.getAllReviewRecords();

            return allRecords.map((record: any) => ({
                conceptId: record.conceptId || record.id,
                conceptName: record.conceptName,
                reviewTime: new Date(record.reviewTime || record.timestamp),
                rating: record.rating || 3,
                interval: record.interval || 1,
                stability: record.stability || 1,
                difficulty: record.difficulty || 5,
                retention: record.retention || 0.9,
                success: record.success !== false,
            }));
        } catch (error) {
            console.error('Error fetching review history from data manager:', error);
            return this.fetchReviewHistoryFromAPI();
        }
    }

    /**
     * 从API获取复习历史
     */
    private async fetchReviewHistoryFromAPI(): Promise<ReviewRecord[]> {
        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/temporal/query`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filter_type: 'all_reviews',
                    min_samples: this.settings.minSamples,
                    fields: ['review_time', 'rating', 'interval', 'stability', 'difficulty', 'retention'],
                }),
            });

            if (response.status !== 200) {
                return [];
            }

            const data = response.json;
            return (data.reviews || []).map((r: any) => ({
                conceptId: r.concept_id,
                conceptName: r.concept_name,
                reviewTime: new Date(r.review_time),
                rating: r.rating,
                interval: r.interval,
                stability: r.stability,
                difficulty: r.difficulty,
                retention: r.retention,
                success: r.success,
            }));
        } catch (error) {
            console.error('Error fetching review history from API:', error);
            return [];
        }
    }

    /**
     * 从Graphiti获取概念网络影响
     */
    private async fetchConceptNetworkInfluence(
        reviews: ReviewRecord[]
    ): Promise<Map<string, { difficulty: number; prerequisites: number }>> {
        const result = new Map<string, { difficulty: number; prerequisites: number }>();
        const concepts = [...new Set(reviews.map(r => r.conceptName))];

        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/graphiti/query`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    analysis_type: 'learning_difficulty_distribution',
                    concepts,
                }),
            });

            if (response.status === 200) {
                const data = response.json;
                for (const [concept, info] of Object.entries(data.distribution || {})) {
                    result.set(concept, {
                        difficulty: (info as any).difficulty || 0.5,
                        prerequisites: (info as any).prerequisite_count || 0,
                    });
                }
            }
        } catch (error) {
            console.error('Error fetching concept network influence:', error);
        }

        // Fill defaults for missing concepts
        for (const concept of concepts) {
            if (!result.has(concept)) {
                result.set(concept, { difficulty: 0.5, prerequisites: 0 });
            }
        }

        return result;
    }

    /**
     * 从Semantic Memory获取文档交互模式
     */
    private async fetchDocumentInteractions(
        reviews: ReviewRecord[]
    ): Promise<Map<string, { engagement: number; documentCount: number }>> {
        const result = new Map<string, { engagement: number; documentCount: number }>();
        const concepts = [...new Set(reviews.map(r => r.conceptName))];

        try {
            const response = await requestUrl({
                url: `${this.settings.apiBaseUrl}/memory/semantic/query`,
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pattern: 'review_engagement_correlation',
                    concepts,
                }),
            });

            if (response.status === 200) {
                const data = response.json;
                for (const [concept, info] of Object.entries(data.correlations || {})) {
                    result.set(concept, {
                        engagement: (info as any).engagement || 0.5,
                        documentCount: (info as any).document_count || 0,
                    });
                }
            }
        } catch (error) {
            console.error('Error fetching document interactions:', error);
        }

        // Fill defaults
        for (const concept of concepts) {
            if (!result.has(concept)) {
                result.set(concept, { engagement: 0.5, documentCount: 0 });
            }
        }

        return result;
    }

    // ============================================================================
    // Training Data Preparation
    // ============================================================================

    /**
     * 准备训练数据
     */
    private prepareTrainingData(
        reviews: ReviewRecord[],
        conceptInfluence: Map<string, { difficulty: number; prerequisites: number }>,
        docInteractions: Map<string, { engagement: number; documentCount: number }>
    ): TrainingDataPoint[] {
        return reviews.map(review => {
            const influence = conceptInfluence.get(review.conceptName) || { difficulty: 0.5, prerequisites: 0 };
            const interaction = docInteractions.get(review.conceptName) || { engagement: 0.5, documentCount: 0 };

            // Calculate prerequisite readiness (0-1)
            const prerequisiteReadiness = influence.prerequisites > 0
                ? Math.min(1, review.stability / (influence.prerequisites * 2))
                : 1;

            return {
                deltaT: Math.max(0.1, review.interval),
                rating: review.rating,
                retention: review.retention,
                conceptDifficulty: influence.difficulty,
                docEngagement: interaction.engagement,
                prerequisiteReadiness,
            };
        });
    }

    // ============================================================================
    // Gradient Descent Optimization
    // ============================================================================

    /**
     * 执行梯度下降优化
     */
    private runGradientDescentOptimization(
        trainingData: TrainingDataPoint[]
    ): { parameters: number[]; iterations: number } {
        let params = [...DEFAULT_FSRS_PARAMETERS];
        let prevLoss = Infinity;
        let iterations = 0;

        for (let i = 0; i < this.settings.maxIterations; i++) {
            iterations++;

            // Calculate gradients
            const gradients = this.calculateGradients(trainingData, params);

            // Update parameters
            params = params.map((p, idx) => {
                const newVal = p - this.settings.learningRate * gradients[idx];
                // Clamp to reasonable bounds
                return Math.max(0.001, Math.min(10, newVal));
            });

            // Calculate loss
            const loss = this.calculateLoss(trainingData, params);

            // Check convergence
            if (Math.abs(prevLoss - loss) < this.settings.convergenceThreshold) {
                break;
            }
            prevLoss = loss;
        }

        return { parameters: params, iterations };
    }

    /**
     * 计算梯度
     */
    private calculateGradients(
        trainingData: TrainingDataPoint[],
        params: number[]
    ): number[] {
        const epsilon = 0.0001;
        const gradients: number[] = [];

        for (let i = 0; i < params.length; i++) {
            // Numerical gradient approximation
            const paramsPlus = [...params];
            const paramsMinus = [...params];
            paramsPlus[i] += epsilon;
            paramsMinus[i] -= epsilon;

            const lossPlus = this.calculateLoss(trainingData, paramsPlus);
            const lossMinus = this.calculateLoss(trainingData, paramsMinus);

            gradients.push((lossPlus - lossMinus) / (2 * epsilon));
        }

        return gradients;
    }

    /**
     * 计算损失（RMSE）
     */
    private calculateLoss(
        trainingData: TrainingDataPoint[],
        params: number[]
    ): number {
        if (trainingData.length === 0) return 0;

        let sumSquaredError = 0;

        for (const data of trainingData) {
            const predicted = this.predictRetention(data, params);
            const error = predicted - data.retention;
            sumSquaredError += error * error;
        }

        return Math.sqrt(sumSquaredError / trainingData.length);
    }

    /**
     * 预测记忆保持率
     * 使用FSRS公式的简化版本
     */
    private predictRetention(
        data: TrainingDataPoint,
        params: number[]
    ): number {
        // Simplified FSRS retention formula
        // R(t) = (1 + t/S)^(-1/decay)
        // where S = initial_stability * rating_factor * difficulty_factor

        const initialStability = params[data.rating - 1]; // w[0-3] based on rating
        const difficultyWeight = params[4];
        const decayFactor = params[5];

        // Calculate effective stability
        const difficultyModifier = 1 + difficultyWeight * (data.conceptDifficulty - 0.5);
        const engagementBonus = 1 + 0.1 * data.docEngagement;
        const prerequisiteBonus = 1 + 0.1 * data.prerequisiteReadiness;

        const effectiveStability = initialStability * difficultyModifier * engagementBonus * prerequisiteBonus;

        // Calculate retention
        const retention = Math.pow(1 + data.deltaT / effectiveStability, -1 / decayFactor);

        // Clamp to [0, 1]
        return Math.max(0, Math.min(1, retention));
    }

    // ============================================================================
    // Evaluation and Quality
    // ============================================================================

    /**
     * 评估优化效果
     */
    private evaluateOptimization(
        trainingData: TrainingDataPoint[],
        defaultParams: number[],
        optimizedParams: number[]
    ): { oldRmse: number; newRmse: number; improvementPercent: number } {
        const oldRmse = this.calculateLoss(trainingData, defaultParams);
        const newRmse = this.calculateLoss(trainingData, optimizedParams);
        const improvementPercent = oldRmse > 0
            ? ((oldRmse - newRmse) / oldRmse) * 100
            : 0;

        return { oldRmse, newRmse, improvementPercent };
    }

    /**
     * 计算数据质量评分
     */
    private calculateDataQuality(trainingData: TrainingDataPoint[]): number {
        if (trainingData.length === 0) return 0;

        // Factor 1: Sample size (0-1)
        const sampleScore = Math.min(1, trainingData.length / 500);

        // Factor 2: Rating distribution (0-1)
        const ratingCounts = [0, 0, 0, 0];
        trainingData.forEach(d => ratingCounts[d.rating - 1]++);
        const minRatio = Math.min(...ratingCounts) / trainingData.length;
        const distributionScore = minRatio * 4; // Perfect distribution = 1

        // Factor 3: Time span diversity (0-1)
        const intervals = trainingData.map(d => d.deltaT);
        const minInterval = Math.min(...intervals);
        const maxInterval = Math.max(...intervals);
        const spanScore = maxInterval > minInterval
            ? Math.min(1, (maxInterval - minInterval) / 30)
            : 0.5;

        // Factor 4: Retention variance (0-1)
        const retentions = trainingData.map(d => d.retention);
        const avgRetention = retentions.reduce((a, b) => a + b, 0) / retentions.length;
        const variance = retentions.reduce((sum, r) => sum + Math.pow(r - avgRetention, 2), 0) / retentions.length;
        const varianceScore = Math.min(1, variance * 10); // Good variance = 1

        // Weighted average
        return (
            sampleScore * 0.4 +
            distributionScore * 0.2 +
            spanScore * 0.2 +
            varianceScore * 0.2
        );
    }

    // ============================================================================
    // Auto-Optimization and Scheduling
    // ============================================================================

    /**
     * 记录新的复习并检查是否需要自动优化
     */
    async recordReview(review: ReviewRecord): Promise<boolean> {
        this.reviewsSinceOptimization++;

        if (this.reviewsSinceOptimization >= this.settings.autoOptimizeInterval) {
            const result = await this.optimizeParameters();
            return result.isOptimized;
        }

        return false;
    }

    /**
     * 启动月度定时优化
     */
    startScheduledOptimization(): void {
        if (!this.settings.monthlyOptimizationEnabled) return;

        // Clear existing timer
        this.stopScheduledOptimization();

        const checkAndOptimize = async () => {
            const now = new Date();
            if (
                now.getDate() === this.settings.monthlyOptimizationDay &&
                now.getHours() === this.settings.monthlyOptimizationHour
            ) {
                console.log('🔄 执行月度FSRS参数优化...');
                await this.optimizeParameters();
            }
        };

        // Check every hour
        this.scheduledOptimizationTimer = setInterval(checkAndOptimize, 60 * 60 * 1000);

        // Also check immediately
        checkAndOptimize();
    }

    /**
     * 停止定时优化
     */
    stopScheduledOptimization(): void {
        if (this.scheduledOptimizationTimer) {
            clearInterval(this.scheduledOptimizationTimer);
            this.scheduledOptimizationTimer = null;
        }
    }

    // ============================================================================
    // A/B Testing
    // ============================================================================

    /**
     * 获取概念的测试组分配
     */
    getTestGroupAssignment(conceptId: string): 'control' | 'test' {
        if (!this.abTestConfig.enabled) {
            return 'control';
        }

        // Deterministic assignment based on concept ID hash
        let hash = 0;
        for (let i = 0; i < conceptId.length; i++) {
            hash = ((hash << 5) - hash) + conceptId.charCodeAt(i);
            hash |= 0;
        }
        const ratio = Math.abs(hash % 100) / 100;

        return ratio < this.abTestConfig.testGroupRatio ? 'test' : 'control';
    }

    /**
     * 获取概念应使用的参数
     */
    getParametersForConcept(conceptId: string): number[] {
        if (!this.abTestConfig.enabled || !this.optimizedParameters) {
            return this.currentParameters;
        }

        const group = this.getTestGroupAssignment(conceptId);
        return group === 'test' ? this.optimizedParameters : DEFAULT_FSRS_PARAMETERS;
    }

    /**
     * 记录A/B测试结果
     */
    recordABTestReview(conceptId: string, review: ReviewRecord): void {
        if (!this.abTestConfig.enabled) return;

        const group = this.getTestGroupAssignment(conceptId);
        const existing = this.abTestResults.get(conceptId) || { group, reviews: [] };
        existing.reviews.push(review);
        this.abTestResults.set(conceptId, existing);
    }

    /**
     * 分析A/B测试结果
     */
    analyzeABTestResults(): ABTestResult {
        const controlReviews: ReviewRecord[] = [];
        const testReviews: ReviewRecord[] = [];

        for (const [_, data] of this.abTestResults) {
            if (data.group === 'control') {
                controlReviews.push(...data.reviews);
            } else {
                testReviews.push(...data.reviews);
            }
        }

        const controlStats = this.calculateGroupStats(controlReviews);
        const testStats = this.calculateGroupStats(testReviews);

        // Determine winner
        let winner: 'control' | 'test' | 'inconclusive' = 'inconclusive';
        let improvementPercent = 0;
        let confidence = 0;

        if (
            controlReviews.length >= this.abTestConfig.minimumSamplesPerGroup &&
            testReviews.length >= this.abTestConfig.minimumSamplesPerGroup
        ) {
            improvementPercent = controlStats.avgRetention > 0
                ? ((testStats.avgRetention - controlStats.avgRetention) / controlStats.avgRetention) * 100
                : 0;

            // Simple confidence based on sample size and effect size
            const effectSize = Math.abs(improvementPercent) / 100;
            const sampleFactor = Math.min(1, (controlReviews.length + testReviews.length) / 200);
            confidence = Math.min(0.99, effectSize * sampleFactor * 2);

            if (confidence >= 0.8) {
                winner = improvementPercent > 0 ? 'test' : 'control';
            }
        }

        return {
            controlGroup: controlStats,
            testGroup: testStats,
            winner,
            confidence,
            improvementPercent,
        };
    }

    /**
     * 计算组统计
     */
    private calculateGroupStats(reviews: ReviewRecord[]): {
        sampleSize: number;
        avgRetention: number;
        avgAccuracy: number;
    } {
        if (reviews.length === 0) {
            return { sampleSize: 0, avgRetention: 0, avgAccuracy: 0 };
        }

        const avgRetention = reviews.reduce((sum, r) => sum + r.retention, 0) / reviews.length;
        const avgAccuracy = reviews.filter(r => r.success).length / reviews.length;

        return {
            sampleSize: reviews.length,
            avgRetention,
            avgAccuracy,
        };
    }

    /**
     * 清除A/B测试数据
     */
    clearABTestData(): void {
        this.abTestResults.clear();
    }

    // ============================================================================
    // Persistence
    // ============================================================================

    /**
     * 导出优化状态
     */
    exportState(): {
        currentParameters: number[];
        optimizedParameters: number[] | null;
        lastOptimization: OptimizationResult | null;
        reviewsSinceOptimization: number;
    } {
        return {
            currentParameters: [...this.currentParameters],
            optimizedParameters: this.optimizedParameters ? [...this.optimizedParameters] : null,
            lastOptimization: this.lastOptimization,
            reviewsSinceOptimization: this.reviewsSinceOptimization,
        };
    }

    /**
     * 导入优化状态
     */
    importState(state: {
        currentParameters?: number[];
        optimizedParameters?: number[] | null;
        lastOptimization?: OptimizationResult | null;
        reviewsSinceOptimization?: number;
    }): void {
        if (state.currentParameters) {
            this.currentParameters = [...state.currentParameters];
        }
        if (state.optimizedParameters !== undefined) {
            this.optimizedParameters = state.optimizedParameters ? [...state.optimizedParameters] : null;
        }
        if (state.lastOptimization !== undefined) {
            this.lastOptimization = state.lastOptimization;
        }
        if (state.reviewsSinceOptimization !== undefined) {
            this.reviewsSinceOptimization = state.reviewsSinceOptimization;
        }
    }
}

// ============================================================================
// Factory Function
// ============================================================================

/**
 * 创建FSRSOptimizerService实例
 */
export function createFSRSOptimizerService(
    app: App,
    settings?: Partial<FSRSOptimizerSettings>,
    abTestConfig?: Partial<ABTestConfig>
): FSRSOptimizerService {
    return new FSRSOptimizerService(app, settings, abTestConfig);
}
