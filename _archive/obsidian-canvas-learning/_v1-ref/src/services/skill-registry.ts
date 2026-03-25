/**
 * Canvas Learning System - Skill Registry
 * Story 3.5: /Command Skill Integration (AC-1, AC-3, AC-4, Task 2)
 *
 * Scans the `.claude/commands/` directory to discover skill prompt templates.
 * Parses each `.md` file's frontmatter for name, description, and icon.
 * Provides a reactive skill list for the SkillSelector UI to consume.
 *
 * Key behaviors:
 * - Scans `.claude/commands/` in the project root (not Obsidian vault)
 * - Supports user-added custom skills (AC-4: add .md file, no restart needed)
 * - Re-scans on every '/' trigger (lightweight, directory listing only)
 *
 * [Source: _bmad-output/implementation-artifacts/3-5-skill-command-integration.md#Task 2]
 */

import { existsSync, readdirSync, readFileSync } from 'fs';
import { join, basename } from 'path';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export interface Skill {
  /** The command name (file stem without .md). Used as `/command-name`. */
  commandName: string;

  /** Display name from frontmatter or derived from filename. */
  name: string;

  /** Short description from frontmatter. */
  description: string;

  /** Emoji icon from frontmatter (default: tool icon). */
  icon: string;

  /** Absolute path to the .md file. */
  filePath: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Default skill metadata (for existing commands without full frontmatter)
// ═══════════════════════════════════════════════════════════════════════════════

const DEFAULT_SKILL_META: Record<string, { name: string; description: string; icon: string }> = {
  'basic-decompose': {
    name: '基础拆解',
    description: '将复杂概念分解为可理解的子概念',
    icon: '🧩',
  },
  'deep-decompose': {
    name: '深度拆解',
    description: '递归分解到原子级知识点，暴露理解盲点',
    icon: '🔬',
  },
  'four-level': {
    name: '四级解释',
    description: '新手/进阶/专家/创新四个层次解释',
    icon: '📊',
  },
  compare: {
    name: '概念对比',
    description: '对比两个容易混淆的概念',
    icon: '⚖️',
  },
  'memory-anchor': {
    name: '记忆锚点',
    description: '为概念创建记忆术/类比/助记',
    icon: '⚓',
  },
  'deep-explain': {
    name: '深度解释',
    description: '深入浅出解释概念的本质原理',
    icon: '💡',
  },
  'example-teach': {
    name: '举例教学',
    description: '通过具体实例理解抽象概念',
    icon: '📝',
  },
  'oral-explain': {
    name: '口语化解释',
    description: '用最通俗的语言解释专业概念',
    icon: '🗣️',
  },
  'question-decompose': {
    name: '问题拆解',
    description: '将大问题分解为可回答的小问题',
    icon: '❓',
  },
  score: {
    name: '知识检验',
    description: '快速检测对概念的理解程度',
    icon: '✅',
  },
  'verify-question': {
    name: '验证追问',
    description: '通过追问验证理解的深度',
    icon: '🔍',
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// SkillRegistry
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Manages the registry of available skills.
 *
 * Skills are discovered from `.claude/commands/` directory.
 * The list is refreshed on each '/' trigger to pick up newly added skills
 * without requiring a plugin restart (AC-4).
 */
class SkillRegistry {
  /** Skill list. */
  skills: Skill[] = [];

  /** Cached commands directory path. */
  private commandsDir: string | null = null;

  /**
   * Scan and load all skills from the commands directory.
   *
   * @param projectRoot - The project root directory containing `.claude/commands/`.
   *   For this project, the vault base path is used to navigate to the project root.
   */
  loadSkills(projectRoot: string): void {
    // The commands directory is at the project root level
    // Navigate from vault path to find the .claude/commands directory
    const candidates = [
      join(projectRoot, '.claude', 'commands'),
      // Also check parent directories in case vault is nested
      join(projectRoot, '..', 'canvas-learning-system', '.claude', 'commands'),
      join(projectRoot, '..', '..', 'canvas-learning-system', '.claude', 'commands'),
    ];

    let commandsDir: string | null = null;
    for (const candidate of candidates) {
      if (existsSync(candidate)) {
        commandsDir = candidate;
        break;
      }
    }

    if (!commandsDir) {
      console.warn(
        '[Canvas Learning] SkillRegistry: .claude/commands/ directory not found',
      );
      this.skills = [];
      return;
    }

    this.commandsDir = commandsDir;
    this.scanDirectory();
  }

  /**
   * Rescan the commands directory for skill files.
   * Called on every '/' trigger to pick up new files (AC-4).
   */
  refresh(): void {
    if (this.commandsDir) {
      this.scanDirectory();
    }
  }

  /**
   * Scan the directory and parse each .md file.
   */
  private scanDirectory(): void {
    if (!this.commandsDir || !existsSync(this.commandsDir)) {
      this.skills = [];
      return;
    }

    const files = readdirSync(this.commandsDir).filter((f) =>
      f.endsWith('.md'),
    );

    const skills: Skill[] = [];

    for (const file of files) {
      const filePath = join(this.commandsDir, file);
      const commandName = basename(file, '.md');
      const skill = this.parseSkillFile(filePath, commandName);
      if (skill) {
        skills.push(skill);
      }
    }

    // Sort alphabetically by name
    skills.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
    this.skills = skills;
  }

  /**
   * Parse a single skill .md file.
   *
   * Extracts frontmatter fields: name, description, icon.
   * Falls back to DEFAULT_SKILL_META or derived values.
   */
  private parseSkillFile(filePath: string, commandName: string): Skill | null {
    try {
      const content = readFileSync(filePath, 'utf-8');
      const frontmatter = this.parseFrontmatter(content);
      const defaults = DEFAULT_SKILL_META[commandName];

      return {
        commandName,
        name:
          frontmatter.name ??
          defaults?.name ??
          commandName.replace(/-/g, ' '),
        description:
          frontmatter.description ??
          defaults?.description ??
          '',
        icon:
          frontmatter.icon ??
          defaults?.icon ??
          '🔧',
        filePath,
      };
    } catch (err) {
      console.warn(
        `[Canvas Learning] SkillRegistry: failed to parse ${filePath}:`,
        err,
      );
      return null;
    }
  }

  /**
   * Parse YAML-like frontmatter from a Markdown file.
   * Simple parser for key: value pairs between --- delimiters.
   */
  private parseFrontmatter(content: string): Record<string, string> {
    const result: Record<string, string> = {};
    const match = content.match(/^---\s*\n([\s\S]*?)\n---/);
    if (!match) return result;

    const lines = match[1].split('\n');
    for (const line of lines) {
      const colonIdx = line.indexOf(':');
      if (colonIdx < 0) continue;

      const key = line.slice(0, colonIdx).trim();
      let value = line.slice(colonIdx + 1).trim();

      // Skip array values (like allowed-tools)
      if (value.startsWith('[') || value === '') continue;

      // Remove quotes
      if (
        (value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))
      ) {
        value = value.slice(1, -1);
      }

      result[key] = value;
    }

    return result;
  }
}

/** Singleton skill registry instance. */
export const skillRegistry = new SkillRegistry();
