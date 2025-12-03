/**
 * Textbook Context Service - Canvas Learning System Cross-Canvas Associations
 *
 * Service for retrieving textbook context from associated Canvas files.
 * Implements Story 16.5: Agent引用教材上下文
 *
 * @module TextbookContextService
 * @version 1.0.0
 *
 * ✅ Verified from @graphiti Skill (search, hybrid search pattern)
 * ✅ Verified from Story 16.5 Dev Notes (1s timeout, graceful degradation)
 */

import { App, Notice } from 'obsidian';
import type { GraphitiAssociationService } from './GraphitiAssociationService';
import type { AssociationConfigService } from './AssociationConfigService';

/**
 * Textbook context result
 * ✅ Verified from Story 16.5 Dev Notes (TextbookContext interface)
 */
export interface TextbookContext {
    textbook_canvas: string;
    section_name: string;
    node_id: string;
    relevance_score: number;
    content_preview: string;
    link_format: string;  // Obsidian internal link format
}

/**
 * Prerequisite concept
 */
export interface Prerequisite {
    concept_name: string;
    source_canvas: string;
    node_id: string;
    importance: 'required' | 'recommended' | 'optional';
}

/**
 * Full context result
 */
export interface FullTextbookContext {
    contexts: TextbookContext[];
    prerequisites: Prerequisite[];
    query_time_ms: number;
    timed_out: boolean;
}

/**
 * Service configuration
 */
interface TextbookContextConfig {
    timeout: number;          // Default: 1000ms
    maxResults: number;       // Default: 3
    minRelevanceScore: number; // Default: 0.5
}

/**
 * Default configuration
 * ✅ Verified from Story 16.5 Dev Notes (1s timeout)
 */
const DEFAULT_CONFIG: TextbookContextConfig = {
    timeout: 1000,         // 1 second timeout
    maxResults: 3,
    minRelevanceScore: 0.5
};

/**
 * Textbook Context Service
 *
 * Retrieves relevant textbook content for Agent context injection.
 * Implements graceful degradation with 1-second timeout.
 *
 * ✅ Verified from Story 16.5 Dev Notes (TextbookContextService pattern)
 */
export class TextbookContextService {
    private app: App;
    private graphitiService: GraphitiAssociationService | null;
    private configService: AssociationConfigService;
    private config: TextbookContextConfig;

    /**
     * Creates a new TextbookContextService
     *
     * @param app - Obsidian App instance
     * @param graphitiService - Optional Graphiti service (null for local-only mode)
     * @param configService - Association config service
     * @param config - Optional configuration
     */
    constructor(
        app: App,
        graphitiService: GraphitiAssociationService | null,
        configService: AssociationConfigService,
        config?: Partial<TextbookContextConfig>
    ) {
        this.app = app;
        this.graphitiService = graphitiService;
        this.configService = configService;
        this.config = { ...DEFAULT_CONFIG, ...config };
    }

    /**
     * Get textbook context for a query
     *
     * ✅ Verified from Story 16.5 Dev Notes (timeout protection pattern)
     *
     * @param canvasPath - Current Canvas path
     * @param query - User query
     * @returns Promise<FullTextbookContext | null>
     */
    async getTextbookContext(
        canvasPath: string,
        query: string
    ): Promise<FullTextbookContext | null> {
        const startTime = Date.now();

        try {
            // Use Promise.race for timeout protection
            const result = await Promise.race<FullTextbookContext | null>([
                this.fetchContext(canvasPath, query),
                this.createTimeoutPromise()
            ]);

            if (result === null) {
                // Timeout occurred
                console.warn('[TextbookContextService] Query timed out for:', canvasPath);
                return {
                    contexts: [],
                    prerequisites: [],
                    query_time_ms: Date.now() - startTime,
                    timed_out: true
                };
            }

            result.query_time_ms = Date.now() - startTime;
            return result;

        } catch (error) {
            console.warn('[TextbookContextService] Error fetching context:', error);
            return null;
        }
    }

    /**
     * Fetch context from associated Canvas files
     */
    private async fetchContext(
        canvasPath: string,
        query: string
    ): Promise<FullTextbookContext> {
        const contexts: TextbookContext[] = [];
        const prerequisites: Prerequisite[] = [];

        // 1. Get local associations
        const associations = await this.configService.getAssociations(canvasPath);

        // 2. Filter for REFERENCES type (教材关联)
        const textbookAssociations = associations.filter(
            a => a.association_type === 'references'
        );

        // 3. Search in each textbook Canvas
        for (const assoc of textbookAssociations) {
            const textbookContexts = await this.searchInCanvas(
                assoc.target_canvas,
                query
            );
            contexts.push(...textbookContexts);
        }

        // 4. Get prerequisites
        const prereqAssociations = associations.filter(
            a => a.association_type === 'prerequisite'
        );

        for (const assoc of prereqAssociations) {
            prerequisites.push({
                concept_name: this.getCanvasDisplayName(assoc.target_canvas),
                source_canvas: assoc.target_canvas,
                node_id: assoc.association_id,
                importance: 'required'
            });
        }

        // 5. Try Graphiti for additional context (if available)
        if (this.graphitiService) {
            try {
                const graphitiContexts = await this.fetchFromGraphiti(canvasPath, query);
                contexts.push(...graphitiContexts);
            } catch (error) {
                console.warn('[TextbookContextService] Graphiti search failed:', error);
                // Continue with local results
            }
        }

        // 6. Sort and limit results
        const sortedContexts = contexts
            .sort((a, b) => b.relevance_score - a.relevance_score)
            .slice(0, this.config.maxResults);

        return {
            contexts: sortedContexts,
            prerequisites,
            query_time_ms: 0,
            timed_out: false
        };
    }

    /**
     * Search for relevant content in a Canvas file
     *
     * ✅ Verified from @obsidian-canvas Skill (Canvas JSON parsing)
     */
    private async searchInCanvas(
        canvasPath: string,
        query: string
    ): Promise<TextbookContext[]> {
        const contexts: TextbookContext[] = [];

        try {
            const file = this.app.vault.getAbstractFileByPath(canvasPath);
            if (!file) return [];

            // Read Canvas JSON
            const content = await this.app.vault.read(file as any);
            const canvasData = JSON.parse(content);

            if (!canvasData.nodes || !Array.isArray(canvasData.nodes)) {
                return [];
            }

            // Search nodes for query match
            const queryLower = query.toLowerCase();
            for (const node of canvasData.nodes) {
                if (node.type !== 'text') continue;

                const nodeText = node.text || '';
                const nodeLower = nodeText.toLowerCase();

                // Simple relevance scoring based on query match
                if (nodeLower.includes(queryLower)) {
                    const relevance = this.calculateRelevance(query, nodeText);

                    if (relevance >= this.config.minRelevanceScore) {
                        contexts.push({
                            textbook_canvas: canvasPath,
                            section_name: this.extractSectionName(nodeText),
                            node_id: node.id,
                            relevance_score: relevance,
                            content_preview: nodeText.slice(0, 100),
                            link_format: this.formatInternalLink(canvasPath, node.id, nodeText)
                        });
                    }
                }
            }

        } catch (error) {
            console.warn('[TextbookContextService] Failed to search canvas:', canvasPath, error);
        }

        return contexts;
    }

    /**
     * Fetch additional context from Graphiti
     */
    private async fetchFromGraphiti(
        canvasPath: string,
        query: string
    ): Promise<TextbookContext[]> {
        if (!this.graphitiService) return [];

        try {
            const searchResult = await this.graphitiService.searchCrossCanvasConcepts(query);

            return searchResult.nodes
                .filter(node => node.entity_type === 'LearningNode' || node.entity_type === 'ConceptNode')
                .map(node => ({
                    textbook_canvas: canvasPath, // Would need graph traversal for actual canvas
                    section_name: node.name,
                    node_id: node.uuid,
                    relevance_score: 0.7,
                    content_preview: node.summary || '',
                    link_format: ''
                }))
                .slice(0, 5);

        } catch {
            return [];
        }
    }

    /**
     * Calculate relevance score between query and text
     */
    private calculateRelevance(query: string, text: string): number {
        const queryLower = query.toLowerCase();
        const textLower = text.toLowerCase();

        // Exact match
        if (textLower === queryLower) return 1.0;

        // Contains full query
        if (textLower.includes(queryLower)) {
            // Higher score for shorter text (more focused)
            const lengthFactor = Math.min(1, 100 / text.length);
            return 0.7 + (0.2 * lengthFactor);
        }

        // Word overlap
        const queryWords = queryLower.split(/\s+/);
        const textWords = new Set(textLower.split(/\s+/));

        let matchCount = 0;
        for (const word of queryWords) {
            if (textWords.has(word) || [...textWords].some(w => w.includes(word))) {
                matchCount++;
            }
        }

        return matchCount / queryWords.length;
    }

    /**
     * Extract section name from node text
     */
    private extractSectionName(text: string): string {
        // Try to find a header pattern
        const headerMatch = text.match(/^#+\s*(.+)$/m);
        if (headerMatch) {
            return headerMatch[1].trim();
        }

        // Use first line as section name
        const firstLine = text.split('\n')[0];
        if (firstLine.length > 50) {
            return firstLine.slice(0, 47) + '...';
        }

        return firstLine || 'Unknown Section';
    }

    /**
     * Format Obsidian internal link
     *
     * ✅ Verified from @obsidian-canvas Skill (Internal link syntax)
     */
    private formatInternalLink(canvasPath: string, nodeId: string, text: string): string {
        const displayName = this.extractSectionName(text);
        const canvasName = this.getCanvasDisplayName(canvasPath);

        // Format: [[Canvas#节点ID|显示名]]
        return `[[${canvasPath}#${nodeId}|${canvasName} > ${displayName}]]`;
    }

    /**
     * Get display name from Canvas path
     */
    private getCanvasDisplayName(path: string): string {
        const name = path.split('/').pop() || path;
        return name.replace('.canvas', '');
    }

    /**
     * Create timeout promise
     */
    private createTimeoutPromise(): Promise<null> {
        return new Promise(resolve => {
            setTimeout(() => resolve(null), this.config.timeout);
        });
    }

    /**
     * Build Agent prompt with textbook context
     *
     * ✅ Verified from Story 16.5 Dev Notes (build_agent_prompt pattern)
     *
     * @param basePrompt - Original Agent prompt
     * @param context - Textbook context
     * @returns Enhanced prompt with context
     */
    buildAgentPrompt(
        basePrompt: string,
        context: FullTextbookContext | null
    ): string {
        if (!context || (context.contexts.length === 0 && context.prerequisites.length === 0)) {
            return basePrompt;
        }

        let contextSection = '\n\n## 相关教材参考\n';

        // Add textbook contexts
        for (const ctx of context.contexts) {
            contextSection += `- ${this.getCanvasDisplayName(ctx.textbook_canvas)} > ${ctx.section_name}\n`;
            contextSection += `  内容预览: ${ctx.content_preview}...\n`;
        }

        // Add prerequisites
        if (context.prerequisites.length > 0) {
            contextSection += '\n## 建议先复习\n';
            for (const prereq of context.prerequisites) {
                contextSection += `- ${prereq.concept_name} (${this.getCanvasDisplayName(prereq.source_canvas)})\n`;
            }
        }

        // Add instruction for Agent
        contextSection += `
请在回答中适当引用上述教材内容，格式为"参见教材: {教材名} > {章节名}"。
如果识别到需要前置知识，请提示"建议先复习: {概念名}({来源Canvas})"。
`;

        return basePrompt + contextSection;
    }

    /**
     * Format textbook reference for node metadata
     *
     * @param context - Textbook context
     * @returns Formatted reference string
     */
    formatTextbookRef(context: TextbookContext): string {
        return `参见教材: ${this.getCanvasDisplayName(context.textbook_canvas)} > ${context.section_name}`;
    }

    /**
     * Create clickable links for contexts
     *
     * @param contexts - Array of textbook contexts
     * @returns Markdown formatted links
     */
    createClickableLinks(contexts: TextbookContext[]): string {
        return contexts
            .map(ctx => ctx.link_format)
            .filter(link => link)
            .join('\n');
    }
}

/**
 * Prerequisite Detector
 *
 * Detects and retrieves prerequisite concepts for a given concept.
 * Implements Story 16.5 Task 2.
 *
 * ✅ Verified from Story 16.5 Dev Notes (PrerequisiteDetector pattern)
 */
export class PrerequisiteDetector {
    private app: App;
    private graphitiService: GraphitiAssociationService | null;
    private configService: AssociationConfigService;
    private maxDepth: number = 3;

    /**
     * Creates a new PrerequisiteDetector
     */
    constructor(
        app: App,
        graphitiService: GraphitiAssociationService | null,
        configService: AssociationConfigService
    ) {
        this.app = app;
        this.graphitiService = graphitiService;
        this.configService = configService;
    }

    /**
     * Detect prerequisites for a concept
     *
     * ✅ Verified from Story 16.5 Dev Notes (detectPrerequisites pattern)
     *
     * @param concept - Concept name to find prerequisites for
     * @param canvasPath - Current Canvas path
     * @returns Promise<Prerequisite[]>
     */
    async detectPrerequisites(
        concept: string,
        canvasPath: string
    ): Promise<Prerequisite[]> {
        const prerequisites: Prerequisite[] = [];
        const visited = new Set<string>();

        await this.traversePrerequisites(
            canvasPath,
            prerequisites,
            visited,
            0,
            'required'
        );

        return prerequisites;
    }

    /**
     * Traverse prerequisite chain
     */
    private async traversePrerequisites(
        canvasPath: string,
        prerequisites: Prerequisite[],
        visited: Set<string>,
        depth: number,
        importance: 'required' | 'recommended' | 'optional'
    ): Promise<void> {
        if (depth >= this.maxDepth || visited.has(canvasPath)) {
            return;
        }

        visited.add(canvasPath);

        // Get local prerequisites
        const associations = await this.configService.getAssociations(canvasPath);
        const prereqAssocs = associations.filter(a => a.association_type === 'prerequisite');

        for (const assoc of prereqAssocs) {
            if (visited.has(assoc.target_canvas)) continue;

            prerequisites.push({
                concept_name: this.getCanvasDisplayName(assoc.target_canvas),
                source_canvas: assoc.target_canvas,
                node_id: assoc.association_id,
                importance: this.determineImportance(depth)
            });

            // Recurse for transitive prerequisites
            await this.traversePrerequisites(
                assoc.target_canvas,
                prerequisites,
                visited,
                depth + 1,
                this.determineImportance(depth + 1)
            );
        }

        // Also check Graphiti if available
        if (this.graphitiService && depth === 0) {
            try {
                const graphitiPrereqs = await this.fetchGraphitiPrerequisites(canvasPath);
                for (const prereq of graphitiPrereqs) {
                    if (!visited.has(prereq.source_canvas)) {
                        prerequisites.push(prereq);
                    }
                }
            } catch {
                // Continue without Graphiti
            }
        }
    }

    /**
     * Fetch prerequisites from Graphiti
     */
    private async fetchGraphitiPrerequisites(canvasPath: string): Promise<Prerequisite[]> {
        if (!this.graphitiService) return [];

        // Search for REQUIRES relationships
        const results = await this.graphitiService.searchCrossCanvasConcepts(
            `Prerequisites for ${canvasPath}`
        );

        return results.edges
            .filter(edge => edge.name === 'REQUIRES')
            .map(edge => ({
                concept_name: edge.fact.split(' ')[0] || 'Unknown',
                source_canvas: '', // Would need additional lookup
                node_id: edge.uuid,
                importance: 'recommended' as const
            }));
    }

    /**
     * Determine importance based on depth
     */
    private determineImportance(depth: number): 'required' | 'recommended' | 'optional' {
        if (depth === 0) return 'required';
        if (depth === 1) return 'recommended';
        return 'optional';
    }

    /**
     * Get display name from Canvas path
     */
    private getCanvasDisplayName(path: string): string {
        const name = path.split('/').pop() || path;
        return name.replace('.canvas', '');
    }

    /**
     * Format prerequisites for display
     *
     * @param prerequisites - Array of prerequisites
     * @returns Formatted markdown string
     */
    formatPrerequisites(prerequisites: Prerequisite[]): string {
        if (prerequisites.length === 0) return '';

        let result = '## 建议先复习\n\n';

        // Group by importance
        const required = prerequisites.filter(p => p.importance === 'required');
        const recommended = prerequisites.filter(p => p.importance === 'recommended');
        const optional = prerequisites.filter(p => p.importance === 'optional');

        if (required.length > 0) {
            result += '**必修**:\n';
            for (const prereq of required) {
                result += `- ${prereq.concept_name} (${this.getCanvasDisplayName(prereq.source_canvas)})\n`;
            }
        }

        if (recommended.length > 0) {
            result += '\n**推荐**:\n';
            for (const prereq of recommended) {
                result += `- ${prereq.concept_name} (${this.getCanvasDisplayName(prereq.source_canvas)})\n`;
            }
        }

        if (optional.length > 0) {
            result += '\n**可选**:\n';
            for (const prereq of optional) {
                result += `- ${prereq.concept_name} (${this.getCanvasDisplayName(prereq.source_canvas)})\n`;
            }
        }

        return result;
    }
}
