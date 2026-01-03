/**
 * Scoring Checkpoint Service
 * Story 2.8: 嵌入式评分检查点 - 前端实现
 *
 * 核心功能：
 * 1. 检测是否需要自动评分
 * 2. 查找关联的黄色节点
 * 3. 调用评分API
 * 4. 生成智能建议
 * 5. 更新节点颜色
 *
 * ✅ Verified from Story 2.8 PRD (嵌入式评分检查点)
 * ✅ Verified from .claude/agents/scoring-agent.md (4维度评分标准)
 */

import { App, TFile, Notice } from 'obsidian';
import { MenuContext, CanvasNodeColor } from '../types/menu';
import {
    CanvasData,
    CanvasNode,
    CanvasTextNode,
    CanvasPresetColor,
    isTextNode,
} from '../types/canvas';
import { ApiClient } from '../api/ApiClient';
import { safeJSONParse, formatCanvasJSON } from '../utils/canvas-helpers';

// ============================================================================
// Types and Interfaces
// ============================================================================

/**
 * Scoring checkpoint result
 */
export interface ScoringCheckResult {
    /** Whether scoring is needed */
    needsScoring: boolean;
    /** Yellow node ID (if found) */
    yellowNodeId?: string;
    /** Yellow node content (if found) */
    yellowContent?: string;
    /** Question node ID */
    questionNodeId?: string;
    /** Question node color */
    questionNodeColor?: CanvasNodeColor;
    /** Reason for the result */
    reason: string;
}

/**
 * Scoring result from API
 * ✅ Verified from .claude/agents/scoring-agent.md (Output Format)
 */
export interface ScoringResult {
    /** Total score (0-100) */
    totalScore: number;
    /** 4-dimension breakdown */
    breakdown: {
        accuracy: number;
        imagery: number;
        completeness: number;
        originality: number;
    };
    /** Whether passed (>= 80) */
    pass: boolean;
    /** Feedback text */
    feedback: string;
    /** Color action to take */
    colorAction: 'change_to_green' | 'change_to_purple' | 'keep_red';
    /** Node ID that was scored */
    nodeId?: string;
}

/**
 * Agent suggestion
 * ✅ Verified from Story 2.9 (评分驱动的Agent推荐)
 */
export interface AgentSuggestion {
    /** Suggested agent type */
    agentType: string;
    /** Suggested agent display name */
    agentName: string;
    /** Suggestion rationale */
    rationale: string;
}

/**
 * Intelligent suggestion based on scoring
 */
export interface SuggestionText {
    /** Summary message */
    summary: string;
    /** Dimension analysis */
    dimensionAnalysis: {
        dimension: string;
        score: number;
        status: 'good' | 'warning' | 'weak';
    }[];
    /** Weakest dimension */
    weakestDimension: string;
    /** Recommended agent */
    recommendedAgent: AgentSuggestion;
    /** Alternative agents */
    alternativeAgents: AgentSuggestion[];
}

/**
 * User choice from checkpoint modal
 */
export interface SuggestionChoice {
    /** User's choice */
    choice: 'accept_suggestion' | 'continue_original' | 'cancel';
    /** Suggested agent (if accepted) */
    suggestedAgent?: string;
}

/**
 * Checkpoint run result
 */
export interface CheckpointRunResult {
    /** Whether the checkpoint handled the flow */
    handled: boolean;
    /** Scoring result (if scoring was performed) */
    scoringResult?: ScoringResult;
    /** User's choice (if modal was shown) */
    userChoice?: SuggestionChoice;
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Learning system color constants
 * ✅ Verified from menu.ts CANVAS_COLOR_NAMES and canvas_utils.py (权威来源)
 *
 * 实际 Obsidian Canvas 渲染颜色:
 *   '1' = Gray (灰色)
 *   '2' = Green (绿色 - 完全理解, ≥80分)
 *   '3' = Purple (紫色 - 似懂非懂, 60-79分)
 *   '4' = Red (红色 - 不理解, <60分)
 *   '5' = Blue (蓝色 - AI解释)
 *   '6' = Yellow (黄色 - 个人理解) ← 关键修复
 */
const LEARNING_COLORS = {
    GRAY: '1' as CanvasPresetColor,     // 灰色 - 无特殊含义
    GREEN: '2' as CanvasPresetColor,    // 绿色 - 完全理解 (≥80分)
    PURPLE: '3' as CanvasPresetColor,   // 紫色 - 似懂非懂 (60-79分)
    RED: '4' as CanvasPresetColor,      // 红色 - 不理解 (<60分)
    BLUE: '5' as CanvasPresetColor,     // 蓝色 - AI解释
    YELLOW: '6' as CanvasPresetColor,   // 黄色 - 个人理解 ← 关键修复
} as const;

/**
 * Minimum content length for "filled" yellow node
 * ✅ Verified from Story 2.8 (定义"已填写"的标准)
 */
const MIN_CONTENT_LENGTH = 10;

/**
 * Score thresholds
 * ✅ Verified from .claude/agents/scoring-agent.md (颜色流转规则)
 */
const SCORE_THRESHOLDS = {
    PASS: 80,     // >= 80 = 绿色 (通过)
    PARTIAL: 60,  // 60-79 = 紫色 (似懂非懂)
    // < 60 = 红色 (未通过)
} as const;

/**
 * Dimension to Agent mapping
 * ✅ Verified from Story 2.9 (维度导向推荐)
 */
const DIMENSION_AGENT_MAP: Record<string, AgentSuggestion[]> = {
    accuracy: [
        { agentType: 'clarification-path', agentName: '澄清路径', rationale: '用详细解释纠正理解偏差' },
        { agentType: 'oral-explanation', agentName: '口语化解释', rationale: '用通俗语言重新解释' },
    ],
    imagery: [
        { agentType: 'memory-anchor', agentName: '记忆锚点', rationale: '通过生动类比加深记忆' },
        { agentType: 'comparison-table', agentName: '对比表', rationale: '结构化对比易混淆概念' },
    ],
    completeness: [
        { agentType: 'clarification-path', agentName: '澄清路径', rationale: '覆盖完整知识点' },
        { agentType: 'four-level-explanation', agentName: '四层次解释', rationale: '渐进式填补知识盲区' },
    ],
    originality: [
        { agentType: 'oral-explanation', agentName: '口语化解释', rationale: '引导用自己的语言表达' },
        { agentType: 'memory-anchor', agentName: '记忆锚点', rationale: '创造个性化记忆点' },
    ],
};

// ============================================================================
// ScoringCheckpointService
// ============================================================================

/**
 * Scoring Checkpoint Service
 *
 * Implements Story 2.8 - 嵌入式评分检查点
 *
 * @example
 * ```typescript
 * const service = new ScoringCheckpointService(app, apiClient);
 * const result = await service.runCheckpoint(context, 'decomposition', (choice) => {
 *   if (choice.choice === 'accept_suggestion') {
 *     // Execute suggested agent
 *   }
 * });
 * ```
 */
export class ScoringCheckpointService {
    private app: App;
    private apiClient: ApiClient;

    constructor(app: App, apiClient: ApiClient) {
        this.app = app;
        this.apiClient = apiClient;
    }

    // ========================================================================
    // Main Entry Point
    // ========================================================================

    /**
     * Run scoring checkpoint before an operation
     *
     * @param context - Menu context with node info
     * @param operationType - Type of operation being performed
     * @param onChoice - Callback when user makes a choice
     * @returns Checkpoint result
     */
    async runCheckpoint(
        context: MenuContext,
        operationType: string,
        onChoice: (choice: SuggestionChoice) => Promise<void>
    ): Promise<CheckpointRunResult> {
        // Step 1: Check if scoring is needed
        const checkResult = await this.checkNeedsScoring(context);

        if (!checkResult.needsScoring) {
            console.log(`[Story 2.8] Scoring not needed: ${checkResult.reason}`);
            return { handled: false };
        }

        // Step 2: Perform scoring
        console.log(`[Story 2.8] Auto-scoring triggered for node: ${checkResult.yellowNodeId}`);
        new Notice('正在自动评分... (预计15秒)');

        let scoringResult: ScoringResult;
        try {
            scoringResult = await this.callScoringAPI(context, checkResult.yellowContent || '');
        } catch (error) {
            console.error('[Story 2.8] Scoring failed:', error);
            new Notice('自动评分失败，继续执行原操作');
            return { handled: false };
        }

        // Step 3: Update node color
        await this.updateNodeColorAfterScoring(context, scoringResult);

        // Step 4: Check if suggestion is needed (score < 80)
        if (scoringResult.pass) {
            new Notice(`评分 ${scoringResult.totalScore} 分，理解充分！继续执行...`);
            return {
                handled: false,
                scoringResult,
            };
        }

        // Step 5: Generate suggestion and show modal
        const suggestion = this.generateSuggestion(scoringResult, operationType);

        // Import and show modal
        const { ScoringCheckpointModal } = await import('../modals/ScoringCheckpointModal');
        const modal = new ScoringCheckpointModal(
            this.app,
            scoringResult,
            suggestion,
            operationType,
            async (choice: SuggestionChoice) => {
                await onChoice(choice);
            }
        );
        modal.open();

        return {
            handled: true,
            scoringResult,
        };
    }

    // ========================================================================
    // Detection Logic
    // ========================================================================

    /**
     * Check if scoring is needed for the given context
     *
     * 修复后的逻辑 (基于用户反馈 2025-12-23):
     * 触发条件: 用户操作"个人理解"节点(黄色节点)时触发评分
     *
     * 检测标准:
     * 1. 点击的节点是黄色节点 (color === '6') 或ID以 "understand-" 开头
     * 2. 黄色节点是文本节点
     * 3. 黄色节点内容 >= 10 字符
     *
     * @param context - Menu context
     * @returns Check result
     */
    async checkNeedsScoring(context: MenuContext): Promise<ScoringCheckResult> {
        console.log(`[Story 2.8 DEBUG] checkNeedsScoring called with:`, {
            filePath: context.filePath,
            nodeId: context.nodeId,
        });

        if (!context.filePath || !context.nodeId) {
            return {
                needsScoring: false,
                reason: '缺少文件路径或节点ID',
            };
        }

        // Read canvas data
        const canvasData = await this.readCanvasData(context.filePath);
        if (!canvasData) {
            console.log(`[Story 2.8 DEBUG] Failed to read canvas data from: ${context.filePath}`);
            return {
                needsScoring: false,
                reason: '无法读取Canvas数据',
            };
        }
        console.log(`[Story 2.8 DEBUG] Canvas loaded: ${canvasData.nodes.length} nodes, ${canvasData.edges.length} edges`);

        // Find the target node (user clicked node)
        const targetNode = canvasData.nodes.find(n => n.id === context.nodeId);
        if (!targetNode) {
            console.log(`[Story 2.8 DEBUG] Target node not found: ${context.nodeId}`);
            return {
                needsScoring: false,
                reason: '未找到目标节点',
            };
        }
        console.log(`[Story 2.8 DEBUG] Target node found:`, {
            id: targetNode.id,
            color: targetNode.color,
            type: targetNode.type,
        });

        // ===== 修复后的核心逻辑 =====
        // 检测用户点击的节点是否是"个人理解"节点（黄色节点）
        const isPersonalUnderstandingNode =
            targetNode.color === LEARNING_COLORS.YELLOW ||  // 颜色是黄色 ('6')
            context.nodeId.startsWith('understand-');        // 或ID以 understand- 开头

        console.log(`[Story 2.8 DEBUG] Is personal understanding node:`, {
            isYellow: targetNode.color === LEARNING_COLORS.YELLOW,
            YELLOW_CODE: LEARNING_COLORS.YELLOW,
            nodeColor: targetNode.color,
            hasUnderstandPrefix: context.nodeId.startsWith('understand-'),
            result: isPersonalUnderstandingNode,
        });

        if (!isPersonalUnderstandingNode) {
            // 如果点击的不是黄色节点，则不触发评分
            console.log(`[Story 2.8 DEBUG] Node is not a personal understanding node, skipping scoring`);
            return {
                needsScoring: false,
                questionNodeId: context.nodeId,
                questionNodeColor: targetNode.color as CanvasNodeColor,
                reason: '只有操作个人理解节点(黄色)时才触发评分',
            };
        }

        // 用户点击的是黄色节点，检查是否是文本节点
        if (!isTextNode(targetNode)) {
            return {
                needsScoring: false,
                questionNodeId: context.nodeId,
                yellowNodeId: targetNode.id,
                reason: '个人理解节点不是文本节点',
            };
        }

        // 获取黄色节点内容
        const content = (targetNode as CanvasTextNode).text?.trim() || '';
        console.log(`[Story 2.8 DEBUG] Yellow node content length: ${content.length}, preview: ${content.substring(0, 50)}...`);

        if (content.length < MIN_CONTENT_LENGTH) {
            return {
                needsScoring: false,
                questionNodeId: context.nodeId,
                yellowNodeId: targetNode.id,
                yellowContent: content,
                reason: `个人理解内容太短(${content.length}字符，需要至少${MIN_CONTENT_LENGTH}字符)`,
            };
        }

        // 查找连接的原材料/问题节点 (用于参考对比)
        const sourceNode = this.findSourceMaterialNode(canvasData, context.nodeId);
        console.log(`[Story 2.8 DEBUG] Source material node:`, sourceNode ? {
            id: sourceNode.id,
            type: sourceNode.type,
            color: sourceNode.color,
        } : 'not found');

        // 所有检查通过 - 需要评分
        return {
            needsScoring: true,
            questionNodeId: sourceNode?.id || context.nodeId,  // 原材料/问题节点ID
            questionNodeColor: sourceNode?.color as CanvasNodeColor,
            yellowNodeId: targetNode.id,  // 黄色节点ID (即用户点击的节点)
            yellowContent: content,       // 黄色节点内容 (用户的理解)
            reason: '检测到已填写的个人理解，需要评分',
        };
    }

    /**
     * Find the source material node connected to a yellow node
     * 查找连接到黄色节点的原材料/问题节点
     *
     * 节点关系: 原材料 --> 问题 --> 黄色节点
     * 或: 原材料 --> 黄色节点 (直接连接)
     *
     * @param canvasData - Canvas data
     * @param yellowNodeId - Yellow node ID
     * @returns Source material node or null
     */
    findSourceMaterialNode(canvasData: CanvasData, yellowNodeId: string): CanvasNode | null {
        console.log(`[Story 2.8 DEBUG] Looking for source material from yellow node: ${yellowNodeId}`);

        // 查找指向黄色节点的边 (incoming edges)
        const incomingEdges = canvasData.edges.filter(e => e.toNode === yellowNodeId);
        console.log(`[Story 2.8 DEBUG] Found ${incomingEdges.length} incoming edges to yellow node`);

        for (const edge of incomingEdges) {
            const sourceNode = canvasData.nodes.find(n => n.id === edge.fromNode);
            if (!sourceNode) continue;

            console.log(`[Story 2.8 DEBUG] Checking source: ${sourceNode.id}, type: ${sourceNode.type}, color: ${sourceNode.color}`);

            // 返回第一个找到的来源节点 (通常是解释节点或原材料节点)
            return sourceNode;
        }

        // 如果没找到incoming，检查outgoing (以防边方向反了)
        const outgoingEdges = canvasData.edges.filter(e => e.fromNode === yellowNodeId);
        console.log(`[Story 2.8 DEBUG] Found ${outgoingEdges.length} outgoing edges from yellow node`);

        for (const edge of outgoingEdges) {
            const targetNode = canvasData.nodes.find(n => n.id === edge.toNode);
            if (!targetNode) continue;

            // 只考虑非黄色节点作为来源
            if (targetNode.color !== LEARNING_COLORS.YELLOW) {
                console.log(`[Story 2.8 DEBUG] Found source via outgoing: ${targetNode.id}`);
                return targetNode;
            }
        }

        console.log(`[Story 2.8 DEBUG] No source material node found`);
        return null;
    }

    /**
     * Find connected yellow node from a question node (保留旧方法作为备用)
     *
     * @param canvasData - Canvas data
     * @param nodeId - Source node ID
     * @returns Yellow node or null
     */
    findConnectedYellowNode(canvasData: CanvasData, nodeId: string): CanvasNode | null {
        // Find edges from this node
        const outgoingEdges = canvasData.edges.filter(e => e.fromNode === nodeId);
        console.log(`[Story 2.8 DEBUG] Looking for personal understanding nodes from: ${nodeId}`);
        console.log(`[Story 2.8 DEBUG] Found ${outgoingEdges.length} outgoing edges`);

        // Strategy 1: Find nodes connected via "个人理解" labeled edges
        for (const edge of outgoingEdges) {
            const targetNode = canvasData.nodes.find(n => n.id === edge.toNode);
            console.log(`[Story 2.8 DEBUG] Edge to: ${edge.toNode}, label: "${edge.label}", targetNode color: ${targetNode?.color}`);

            // Match by edge label "个人理解" - this is the most reliable way
            if (edge.label === '个人理解' && targetNode) {
                console.log(`[Story 2.8 DEBUG] MATCH via label: Found personal understanding node ${targetNode.id}`);
                return targetNode;
            }

            // Also match by node ID prefix "understand-"
            if (targetNode && targetNode.id.startsWith('understand-')) {
                console.log(`[Story 2.8 DEBUG] MATCH via ID prefix: Found understand node ${targetNode.id}`);
                return targetNode;
            }

            // Also match by yellow color (color='3') for completeness
            if (targetNode && targetNode.color === LEARNING_COLORS.YELLOW) {
                console.log(`[Story 2.8 DEBUG] MATCH via color: Found yellow node ${targetNode.id}`);
                return targetNode;
            }
        }

        // Strategy 2: Check incoming edges (in case edge direction is reversed)
        const incomingEdges = canvasData.edges.filter(e => e.toNode === nodeId);
        console.log(`[Story 2.8 DEBUG] Found ${incomingEdges.length} incoming edges`);
        for (const edge of incomingEdges) {
            const sourceNode = canvasData.nodes.find(n => n.id === edge.fromNode);
            console.log(`[Story 2.8 DEBUG] Edge from: ${edge.fromNode}, label: "${edge.label}", sourceNode color: ${sourceNode?.color}`);

            if (edge.label === '个人理解' && sourceNode) {
                console.log(`[Story 2.8 DEBUG] MATCH via label (incoming): Found personal understanding node ${sourceNode.id}`);
                return sourceNode;
            }

            if (sourceNode && sourceNode.id.startsWith('understand-')) {
                console.log(`[Story 2.8 DEBUG] MATCH via ID prefix (incoming): Found understand node ${sourceNode.id}`);
                return sourceNode;
            }

            if (sourceNode && sourceNode.color === LEARNING_COLORS.YELLOW) {
                console.log(`[Story 2.8 DEBUG] MATCH via color (incoming): Found yellow node ${sourceNode.id}`);
                return sourceNode;
            }
        }

        console.log(`[Story 2.8 DEBUG] No personal understanding node found`);
        return null;
    }

    // ========================================================================
    // Scoring API
    // ========================================================================

    /**
     * Call scoring API
     *
     * @param context - Menu context
     * @param yellowContent - Yellow node content to score
     * @returns Scoring result
     */
    async callScoringAPI(context: MenuContext, yellowContent: string): Promise<ScoringResult> {
        const canvasName = this.extractCanvasFileName(context.filePath);

        console.log(`[Story 2.8] Calling scoring API with content (${yellowContent.length} chars)`);

        // ✅ Verified from ApiClient.scoreUnderstanding (Story 13.3)
        // ✅ Story 2.8: Pass yellowContent as node_content for real-time scoring
        // API returns 0-10 per dimension, 0-40 total. We scale to 0-25 per dimension, 0-100 total.
        const response = await this.apiClient.scoreUnderstanding({
            canvas_name: canvasName,
            node_ids: context.nodeId ? [context.nodeId] : [],
            node_content: yellowContent,  // Story 2.8: Pass actual yellow node content
        });

        // Parse response
        const scoreData = response.scores?.[0];
        if (!scoreData) {
            throw new Error('No scoring data returned from API');
        }

        // Scale from 0-40 to 0-100 (multiply by 2.5)
        const scaleFactor = 2.5;
        const totalScore = Math.round((scoreData.total || 0) * scaleFactor);
        const pass = totalScore >= SCORE_THRESHOLDS.PASS;

        let colorAction: 'change_to_green' | 'change_to_purple' | 'keep_red';
        if (totalScore >= SCORE_THRESHOLDS.PASS) {
            colorAction = 'change_to_green';
        } else if (totalScore >= SCORE_THRESHOLDS.PARTIAL) {
            colorAction = 'change_to_purple';
        } else {
            colorAction = 'keep_red';
        }

        return {
            totalScore,
            breakdown: {
                // Scale from 0-10 to 0-25 (multiply by 2.5)
                accuracy: Math.round((scoreData.accuracy || 0) * scaleFactor),
                imagery: Math.round((scoreData.imagery || 0) * scaleFactor),
                completeness: Math.round((scoreData.completeness || 0) * scaleFactor),
                originality: Math.round((scoreData.originality || 0) * scaleFactor),
            },
            pass,
            // Story 2.8: Use feedback from backend Agent (100-200 chars specific suggestions)
            feedback: scoreData.feedback || '评分完成',
            colorAction,
            nodeId: scoreData.node_id,
        };
    }

    // ========================================================================
    // Suggestion Generation
    // ========================================================================

    /**
     * Generate intelligent suggestion based on scoring result
     *
     * @param scoringResult - Scoring result
     * @param operationType - Original operation type
     * @returns Suggestion text
     */
    generateSuggestion(scoringResult: ScoringResult, operationType: string): SuggestionText {
        const { totalScore, breakdown } = scoringResult;

        // Analyze dimensions
        const dimensionAnalysis = [
            { dimension: '准确性', key: 'accuracy', score: breakdown.accuracy },
            { dimension: '形象性', key: 'imagery', score: breakdown.imagery },
            { dimension: '完整性', key: 'completeness', score: breakdown.completeness },
            { dimension: '原创性', key: 'originality', score: breakdown.originality },
        ].map(d => ({
            dimension: d.dimension,
            score: d.score,
            status: this.getDimensionStatus(d.score),
            key: d.key,
        }));

        // Find weakest dimension
        const weakest = dimensionAnalysis.reduce((min, curr) =>
            curr.score < min.score ? curr : min
        );

        // Get recommended agents for weakest dimension
        const recommendedAgents = DIMENSION_AGENT_MAP[weakest.key] || DIMENSION_AGENT_MAP.accuracy;

        // Generate summary
        let summary: string;
        if (totalScore >= SCORE_THRESHOLDS.PARTIAL) {
            summary = `您的理解得分 ${totalScore} 分，基本正确但存在盲区。`;
        } else {
            summary = `您的理解得分 ${totalScore} 分，需要进一步深化学习。`;
        }

        return {
            summary,
            dimensionAnalysis: dimensionAnalysis.map(d => ({
                dimension: d.dimension,
                score: d.score,
                status: d.status,
            })),
            weakestDimension: weakest.dimension,
            recommendedAgent: recommendedAgents[0],
            alternativeAgents: recommendedAgents.slice(1),
        };
    }

    /**
     * Get dimension status based on score
     */
    private getDimensionStatus(score: number): 'good' | 'warning' | 'weak' {
        if (score >= 20) return 'good';
        if (score >= 15) return 'warning';
        return 'weak';
    }

    // ========================================================================
    // Color Update
    // ========================================================================

    /**
     * Update node color after scoring
     *
     * PRD规定：
     * - 黄色节点 (color="6") = 个人理解 → 颜色不变
     * - 蓝色节点 (color="5") = AI解释节点 → 根据评分变色
     * - 教材节点 → 颜色不变
     *
     * @param context - Menu context
     * @param scoringResult - Scoring result
     */
    async updateNodeColorAfterScoring(
        context: MenuContext,
        scoringResult: ScoringResult
    ): Promise<void> {
        if (!context.filePath || !context.nodeId) return;

        // Read canvas data
        const canvasData = await this.readCanvasData(context.filePath);
        if (!canvasData) return;

        // Find the scored node
        const nodeIndex = canvasData.nodes.findIndex(n => n.id === context.nodeId);
        if (nodeIndex === -1) return;

        const scoredNode = canvasData.nodes[nodeIndex];
        const currentColor = scoredNode.color || '1';

        // PRD规定：黄色节点(color="6")颜色不变
        if (currentColor === LEARNING_COLORS.YELLOW) {
            console.log(`[Story 2.8] Yellow node ${context.nodeId} - color preserved (PRD规定)`);

            // 查找并更新关联的AI解释节点（蓝色 color="5"）
            const linkedAINodeId = this.findLinkedAIExplanationNode(canvasData, context.nodeId);
            if (linkedAINodeId) {
                const aiNodeIndex = canvasData.nodes.findIndex(n => n.id === linkedAINodeId);
                if (aiNodeIndex !== -1) {
                    const newColor = this.determineNewColor(scoringResult.colorAction);
                    canvasData.nodes[aiNodeIndex].color = newColor;

                    // Write back and refresh
                    await this.writeCanvasData(context.filePath, canvasData);
                    await this.refreshCanvasView(context.filePath);

                    console.log(`[Story 2.8] Updated linked AI node ${linkedAINodeId} color to ${newColor}`);
                }
            }
            return; // 不更新黄色节点本身的颜色
        }

        // 非黄色节点：正常更新颜色
        const newColor = this.determineNewColor(scoringResult.colorAction);
        canvasData.nodes[nodeIndex].color = newColor;

        // Write back to file
        await this.writeCanvasData(context.filePath, canvasData);

        // Trigger view refresh
        await this.refreshCanvasView(context.filePath);

        console.log(`[Story 2.8] Updated node ${context.nodeId} color to ${newColor}`);
    }

    /**
     * Determine new color based on scoring action
     */
    private determineNewColor(colorAction: 'change_to_green' | 'change_to_purple' | 'keep_red'): CanvasPresetColor {
        switch (colorAction) {
            case 'change_to_green':
                return LEARNING_COLORS.GREEN;
            case 'change_to_purple':
                return LEARNING_COLORS.PURPLE;
            default:
                return LEARNING_COLORS.RED;
        }
    }

    /**
     * 查找与黄色节点关联的AI解释节点
     * PRD: 评分结果只更新蓝色AI解释节点颜色，不更新黄色个人理解节点
     *
     * @param canvasData - Canvas data
     * @param yellowNodeId - Yellow node ID
     * @returns Linked AI explanation node ID or null
     */
    private findLinkedAIExplanationNode(canvasData: CanvasData, yellowNodeId: string): string | null {
        if (!canvasData.edges) return null;

        // 查找从黄色节点出发的边
        for (const edge of canvasData.edges) {
            // 找到以黄色节点为起点的边
            if (edge.fromNode === yellowNodeId) {
                const targetNodeId = edge.toNode;
                const targetNode = canvasData.nodes.find(n => n.id === targetNodeId);
                // 检查目标是否为AI解释节点（蓝色 color="5"）
                if (targetNode && targetNode.color === LEARNING_COLORS.BLUE) {
                    return targetNodeId;
                }
            }
            // 也检查以黄色节点为终点的边（双向关联）
            if (edge.toNode === yellowNodeId) {
                const sourceNodeId = edge.fromNode;
                const sourceNode = canvasData.nodes.find(n => n.id === sourceNodeId);
                // 检查源节点是否为AI解释节点（蓝色 color="5"）
                if (sourceNode && sourceNode.color === LEARNING_COLORS.BLUE) {
                    return sourceNodeId;
                }
            }
        }
        return null;
    }

    // ========================================================================
    // Canvas File Operations
    // ========================================================================

    /**
     * Read canvas data from file
     */
    private async readCanvasData(filePath: string): Promise<CanvasData | null> {
        const file = this.app.vault.getAbstractFileByPath(filePath);
        if (!(file instanceof TFile)) return null;

        try {
            const content = await this.app.vault.read(file);
            return safeJSONParse<CanvasData>(content);
        } catch (error) {
            console.error('[Story 2.8] Failed to read canvas:', error);
            return null;
        }
    }

    /**
     * Write canvas data to file
     */
    private async writeCanvasData(filePath: string, data: CanvasData): Promise<void> {
        const file = this.app.vault.getAbstractFileByPath(filePath);
        if (!(file instanceof TFile)) return;

        try {
            await this.app.vault.modify(file, formatCanvasJSON(data));
        } catch (error) {
            console.error('[Story 2.8] Failed to write canvas:', error);
        }
    }

    /**
     * Refresh canvas view after modification
     * ✅ Verified from Epic 12.M (Canvas View Refresh)
     */
    private async refreshCanvasView(filePath: string): Promise<void> {
        // Trigger Obsidian to refresh the canvas view
        const file = this.app.vault.getAbstractFileByPath(filePath);
        if (!(file instanceof TFile)) return;

        // Use workspace trigger to refresh
        this.app.workspace.trigger('file-modified', file);
    }

    /**
     * Extract canvas file name from path
     */
    private extractCanvasFileName(filePath?: string): string {
        if (!filePath) return '';
        const parts = filePath.split('/');
        return parts[parts.length - 1] || '';
    }
}
