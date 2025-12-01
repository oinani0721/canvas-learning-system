/**
 * GenerateReviewOutputParser - Parser for /generate-review command output
 *
 * Implements AC-3: Command output parsing for review plan generation.
 * Parses output from /generate-review command into ReviewPlan object.
 *
 * @module GenerateReviewOutputParser
 * @version 1.0.0
 *
 * Source: Story 13.4 Dev Notes - Output Parser Implementation
 */

import type {
  OutputParser,
  ReviewPlan,
  ReviewSection,
  Resource,
  ReviewPlanType,
  ReviewDifficulty,
} from '../types/ReviewTypes';

// ============================================================================
// Types
// ============================================================================

/**
 * Raw section data from API response
 */
interface RawSectionData {
  id?: string;
  title?: string;
  type?: string;
  concepts?: string[];
  duration?: number;
  order?: number;
}

/**
 * Raw resource data from API response
 */
interface RawResourceData {
  id?: string;
  title?: string;
  type?: string;
  path?: string;
  url?: string;
  required?: boolean;
}

/**
 * Raw plan data from API response
 */
interface RawPlanData {
  id?: string;
  canvas_id?: string;
  canvasId?: string;
  canvas_title?: string;
  canvasTitle?: string;
  plan_type?: string;
  planType?: string;
  difficulty?: string;
  estimated_duration?: number;
  estimatedDuration?: number;
  target_mastery?: number;
  targetMastery?: number;
  focus_areas?: string[];
  focusAreas?: string[];
  max_concepts?: number;
  maxConcepts?: number;
  sections?: RawSectionData[];
  resources?: RawResourceData[];
  generated_at?: string;
  generatedAt?: string;
  based_on_data?: string[];
  basedOnData?: string[];
}

/**
 * Raw API response structure
 */
interface RawApiResponse {
  plan?: RawPlanData;
  data?: RawPlanData;
  result?: RawPlanData;
}

// ============================================================================
// GenerateReviewOutputParser Class
// ============================================================================

/**
 * Parser for /generate-review command output
 *
 * Supports both JSON and text output formats with graceful fallback.
 * Source: Story 13.4 Dev Notes - GenerateReviewOutputParser
 */
export class GenerateReviewOutputParser implements OutputParser<ReviewPlan> {
  // ==========================================================================
  // Public Methods
  // ==========================================================================

  /**
   * Parse command output into ReviewPlan
   *
   * @param output - Raw command output
   * @returns ReviewPlan object
   * @throws Error if parsing completely fails
   */
  parse(output: string): ReviewPlan {
    if (!output || typeof output !== 'string') {
      return this.createEmptyPlan();
    }

    const trimmedOutput = output.trim();
    if (!trimmedOutput) {
      return this.createEmptyPlan();
    }

    // Try JSON parsing first
    try {
      const data = JSON.parse(trimmedOutput);
      return this.transformToReviewPlan(data);
    } catch {
      // Fallback to text parsing
      return this.parseTextOutput(trimmedOutput);
    }
  }

  // ==========================================================================
  // Private Methods - JSON Parsing
  // ==========================================================================

  /**
   * Transform JSON data to ReviewPlan
   *
   * @param data - Parsed JSON data
   * @returns ReviewPlan object
   */
  private transformToReviewPlan(data: RawApiResponse | RawPlanData): ReviewPlan {
    // Handle different response formats
    let planData: RawPlanData;

    if ('plan' in data && data.plan) {
      planData = data.plan;
    } else if ('data' in data && data.data) {
      planData = data.data;
    } else if ('result' in data && data.result) {
      planData = data.result;
    } else {
      planData = data as RawPlanData;
    }

    return {
      id: planData.id ?? this.generateId(),
      canvasId: planData.canvas_id ?? planData.canvasId ?? '',
      canvasTitle: planData.canvas_title ?? planData.canvasTitle ?? '',
      planType: this.mapPlanType(planData.plan_type ?? planData.planType),
      difficulty: this.mapDifficulty(planData.difficulty),
      estimatedDuration: planData.estimated_duration ?? planData.estimatedDuration ?? 30,
      targetMastery: this.normalizeNumber(
        planData.target_mastery ?? planData.targetMastery,
        0,
        100,
        80
      ),
      focusAreas: planData.focus_areas ?? planData.focusAreas ?? [],
      maxConcepts: planData.max_concepts ?? planData.maxConcepts ?? 10,
      sections: this.transformSections(planData.sections),
      resources: this.transformResources(planData.resources),
      generatedAt: this.parseDate(planData.generated_at ?? planData.generatedAt) ?? new Date(),
      basedOnData: planData.based_on_data ?? planData.basedOnData ?? [],
    };
  }

  /**
   * Transform raw sections to ReviewSection array
   *
   * @param sections - Raw section data array
   * @returns Array of ReviewSection objects
   */
  private transformSections(sections?: RawSectionData[]): ReviewSection[] {
    if (!sections || !Array.isArray(sections)) {
      return [];
    }

    return sections.map((section, index) => ({
      id: section.id ?? `section-${index + 1}`,
      title: section.title ?? `Section ${index + 1}`,
      type: section.type ?? 'concept',
      concepts: section.concepts ?? [],
      duration: section.duration ?? 10,
      order: section.order ?? index + 1,
    }));
  }

  /**
   * Transform raw resources to Resource array
   *
   * @param resources - Raw resource data array
   * @returns Array of Resource objects
   */
  private transformResources(resources?: RawResourceData[]): Resource[] {
    if (!resources || !Array.isArray(resources)) {
      return [];
    }

    return resources.map((resource, index) => ({
      id: resource.id ?? `resource-${index + 1}`,
      title: resource.title ?? `Resource ${index + 1}`,
      type: resource.type ?? 'note',
      path: resource.path ?? resource.url ?? '',
      required: resource.required ?? false,
    }));
  }

  // ==========================================================================
  // Private Methods - Text Parsing (Fallback)
  // ==========================================================================

  /**
   * Parse text output format (fallback)
   *
   * @param output - Text output to parse
   * @returns ReviewPlan object
   */
  private parseTextOutput(output: string): ReviewPlan {
    const plan = this.createEmptyPlan();
    const lines = output.split('\n').filter(line => line.trim());

    let currentSection: 'plan' | 'sections' | 'resources' = 'plan';
    let sectionIndex = 0;

    for (const line of lines) {
      // Detect section headers
      if (line.match(/^#+\s*sections?/i) || line.match(/^sections?:/i)) {
        currentSection = 'sections';
        continue;
      }
      if (line.match(/^#+\s*resources?/i) || line.match(/^resources?:/i)) {
        currentSection = 'resources';
        continue;
      }

      // Parse based on current section
      switch (currentSection) {
        case 'plan':
          this.parsePlanLine(line, plan);
          break;
        case 'sections':
          const section = this.parseSectionLine(line, sectionIndex);
          if (section) {
            plan.sections.push(section);
            sectionIndex++;
          }
          break;
        case 'resources':
          const resource = this.parseResourceLine(line);
          if (resource) {
            plan.resources.push(resource);
          }
          break;
      }
    }

    return plan;
  }

  /**
   * Parse a plan property line
   *
   * @param line - Line to parse
   * @param plan - Plan object to update
   */
  private parsePlanLine(line: string, plan: ReviewPlan): void {
    const keyValueMatch = line.match(/^\s*[-*]?\s*([\w\s]+):\s*(.+)$/);
    if (!keyValueMatch) return;

    const [, key, value] = keyValueMatch;
    const normalizedKey = key.toLowerCase().trim().replace(/\s+/g, '_');

    switch (normalizedKey) {
      case 'canvas':
      case 'canvas_id':
        plan.canvasId = value.trim();
        break;
      case 'canvas_title':
      case 'title':
        plan.canvasTitle = value.trim();
        break;
      case 'plan_type':
      case 'type':
        plan.planType = this.mapPlanType(value.trim());
        break;
      case 'difficulty':
        plan.difficulty = this.mapDifficulty(value.trim());
        break;
      case 'duration':
      case 'estimated_duration':
        plan.estimatedDuration = parseInt(value.trim(), 10) || 30;
        break;
      case 'target_mastery':
      case 'mastery':
        plan.targetMastery = parseInt(value.trim(), 10) || 80;
        break;
      case 'focus_areas':
      case 'focus':
        plan.focusAreas = value.split(',').map(s => s.trim()).filter(Boolean);
        break;
      case 'max_concepts':
        plan.maxConcepts = parseInt(value.trim(), 10) || 10;
        break;
    }
  }

  /**
   * Parse a section line
   *
   * @param line - Line to parse
   * @param index - Section index
   * @returns ReviewSection or null
   */
  private parseSectionLine(line: string, index: number): ReviewSection | null {
    // Pattern: "1. Title (concepts: A, B, C; duration: 10min)"
    const match = line.match(
      /^\s*[-*\d.]+\s*([^(]+)(?:\(.*concepts?:\s*([^;)]+))?(?:.*duration:\s*(\d+))?\)?/i
    );

    if (match && match[1]) {
      const [, title, concepts, duration] = match;
      return {
        id: `section-${index + 1}`,
        title: title.trim(),
        type: 'concept',
        concepts: concepts ? concepts.split(',').map(s => s.trim()) : [],
        duration: parseInt(duration, 10) || 10,
        order: index + 1,
      };
    }

    return null;
  }

  /**
   * Parse a resource line
   *
   * @param line - Line to parse
   * @returns Resource or null
   */
  private parseResourceLine(line: string): Resource | null {
    // Pattern: "- Title (path/to/file.md, required)"
    const match = line.match(
      /^\s*[-*]+\s*([^(]+)(?:\(([^,)]+)(?:,\s*(required))?\))?/i
    );

    if (match && match[1]) {
      const [, title, path, required] = match;
      return {
        id: this.generateId(),
        title: title.trim(),
        type: this.inferResourceType(path),
        path: path?.trim() ?? '',
        required: required !== undefined,
      };
    }

    return null;
  }

  // ==========================================================================
  // Private Methods - Utilities
  // ==========================================================================

  /**
   * Create an empty plan with defaults
   *
   * @returns Empty ReviewPlan
   */
  private createEmptyPlan(): ReviewPlan {
    return {
      id: this.generateId(),
      canvasId: '',
      canvasTitle: '',
      planType: 'comprehensive',
      difficulty: 'adaptive',
      estimatedDuration: 30,
      targetMastery: 80,
      focusAreas: [],
      maxConcepts: 10,
      sections: [],
      resources: [],
      generatedAt: new Date(),
      basedOnData: [],
    };
  }

  /**
   * Map plan type string to ReviewPlanType
   *
   * @param planType - Plan type string
   * @returns ReviewPlanType value
   */
  private mapPlanType(planType?: string): ReviewPlanType {
    if (!planType) return 'comprehensive';

    const normalized = planType.toLowerCase().trim();
    switch (normalized) {
      case 'weakness-focused':
      case 'weakness':
      case 'focused':
        return 'weakness-focused';
      case 'comprehensive':
      case 'full':
      case 'complete':
        return 'comprehensive';
      case 'targeted':
      case 'specific':
        return 'targeted';
      default:
        return 'comprehensive';
    }
  }

  /**
   * Map difficulty string to ReviewDifficulty
   *
   * @param difficulty - Difficulty string
   * @returns ReviewDifficulty value
   */
  private mapDifficulty(difficulty?: string): ReviewDifficulty {
    if (!difficulty) return 'adaptive';

    const normalized = difficulty.toLowerCase().trim();
    switch (normalized) {
      case 'easy':
      case 'simple':
      case 'beginner':
        return 'easy';
      case 'medium':
      case 'moderate':
      case 'intermediate':
        return 'medium';
      case 'hard':
      case 'difficult':
      case 'advanced':
        return 'hard';
      case 'adaptive':
      case 'auto':
      case 'dynamic':
        return 'adaptive';
      default:
        return 'adaptive';
    }
  }

  /**
   * Infer resource type from path
   *
   * @param path - Resource path
   * @returns Resource type string
   */
  private inferResourceType(path?: string): string {
    if (!path) return 'note';

    const lowerPath = path.toLowerCase();
    if (lowerPath.endsWith('.canvas')) return 'canvas';
    if (lowerPath.endsWith('.md')) return 'note';
    if (lowerPath.startsWith('http')) return 'external';
    return 'note';
  }

  /**
   * Normalize a number to a range
   *
   * @param value - Value to normalize
   * @param min - Minimum allowed value
   * @param max - Maximum allowed value
   * @param defaultValue - Default if value is invalid
   * @returns Normalized number
   */
  private normalizeNumber(
    value: number | undefined,
    min: number,
    max: number,
    defaultValue: number
  ): number {
    if (value === undefined || value === null || isNaN(value)) {
      return defaultValue;
    }
    return Math.max(min, Math.min(max, value));
  }

  /**
   * Parse date string to Date object
   *
   * @param dateStr - Date string to parse
   * @returns Date object or undefined
   */
  private parseDate(dateStr?: string): Date | undefined {
    if (!dateStr) return undefined;

    const date = new Date(dateStr);
    return isNaN(date.getTime()) ? undefined : date;
  }

  /**
   * Generate a unique ID
   *
   * @returns Unique identifier string
   */
  private generateId(): string {
    return `plan-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}
