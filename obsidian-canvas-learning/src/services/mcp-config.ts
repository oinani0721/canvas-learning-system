/**
 * Canvas Learning System - MCP Configuration Generator
 * Story 3.1: Task 5 (MCP Config Preload)
 * Story 3.2: Task 5 (MCP Config Dynamic Injection)
 *
 * Generates the `canvas-mcp.json` configuration file that tells Claude Code
 * how to connect to the backend MCP server. The config is injected via
 * `--mcp-config` when spawning the CLI process.
 *
 * [Source: _bmad-output/implementation-artifacts/3-2-mcp-tool-exposure-backend-api.md#Task 5]
 * [Source: _bmad-output/implementation-artifacts/3-1-claude-code-cli-per-node-session.md#Task 5]
 */

import { existsSync, mkdirSync, writeFileSync } from 'fs';
import { dirname, join } from 'path';

// ═══════════════════════════════════════════════════════════════════════════════
// MCP Config Types
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * MCP server configuration entry.
 * Follows the Claude Code `--mcp-config` JSON format.
 */
interface McpServerEntry {
  type: 'sse';
  url: string;
  description: string;
}

/**
 * Root MCP configuration object.
 */
interface McpConfig {
  mcpServers: Record<string, McpServerEntry>;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Config Generation
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Generate the MCP configuration JSON content.
 *
 * Story 3.2 AC-5: Config format follows Claude Code `--mcp-config` spec.
 *
 * @param backendUrl - The FastAPI backend base URL (default: http://localhost:8001)
 * @returns The MCP configuration as a formatted JSON string.
 */
export function generateMcpConfig(
  backendUrl = 'http://localhost:8001',
): string {
  // Ensure URL doesn't have trailing slash
  const baseUrl = backendUrl.replace(/\/+$/, '');

  const config: McpConfig = {
    mcpServers: {
      'canvas-learning': {
        type: 'sse',
        url: `${baseUrl}/mcp`,
        description:
          'Canvas Learning System backend tools: mastery tracking, ' +
          'exam generation, scoring, memory search, and canvas operations.',
      },
    },
  };

  return JSON.stringify(config, null, 2);
}

/**
 * Write the MCP configuration file to the plugin data directory.
 *
 * Story 3.2 AC-5: Config file is written to the plugin's data directory
 * so it can be referenced via `--mcp-config` when spawning Claude Code.
 *
 * @param pluginDataDir - Absolute path to the plugin data directory.
 *   Typically: `${vault}/.obsidian/plugins/canvas-learning-system/`
 * @param backendUrl - The FastAPI backend base URL.
 * @returns The absolute path to the generated config file.
 */
export function writeMcpConfig(
  pluginDataDir: string,
  backendUrl = 'http://localhost:8001',
): string {
  const configPath = join(pluginDataDir, 'canvas-mcp.json');

  // Ensure directory exists
  const dir = dirname(configPath);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  const content = generateMcpConfig(backendUrl);
  writeFileSync(configPath, content, 'utf-8');

  console.log(
    `[Canvas Learning] MCP config written to ${configPath}`,
  );

  return configPath;
}

/**
 * Get the expected MCP config file path (without writing).
 *
 * @param pluginDataDir - Plugin data directory path.
 * @returns The expected config file path.
 */
export function getMcpConfigPath(pluginDataDir: string): string {
  return join(pluginDataDir, 'canvas-mcp.json');
}
