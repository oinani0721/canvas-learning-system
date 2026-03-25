/**
 * Canvas Learning System - MCP Configuration Generator
 * Story 3.1: Task 5 (MCP Config Preload)
 *
 * Generates the `canvas-mcp.json` configuration file that tells Claude Code
 * how to connect to the backend MCP server. The config is injected via
 * `--mcp-config` when spawning the CLI process.
 *
 * The specific MCP tools exposed are implemented in Story 3.2; this module
 * only generates the transport configuration.
 *
 * [Source: _bmad-output/implementation-artifacts/3-1-claude-code-cli-per-node-session.md#Task 5]
 *
 * Callers:
 *   - Plugin main.ts onload — calls writeMcpConfig() to generate the config
 *     file, then passes the path to ClaudeCodeEngine constructor
 *
 * Wiring:
 *   - Plugin onload: const mcpPath = writeMcpConfig(pluginDataDir, backendUrl)
 *   - Plugin onload: new ClaudeCodeEngine(pluginDataDir, mcpPath)
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
