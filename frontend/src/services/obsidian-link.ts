/**
 * Obsidian Link Service — Open files in Obsidian from the Tauri app.
 * Scene 9.1 / 9.2: Obsidian integration via URI protocol.
 *
 * Three-level degradation strategy:
 *   1. obsidian://adv-uri — Advanced URI plugin (supports heading navigation)
 *   2. obsidian://open — Built-in URI (vault + file level only)
 *   3. Fallback — Copy-ready file path returned to caller
 *
 * Callers:
 *   - MessageBubble.tsx — wiki-link click handler
 *   - NodeContextMenu.tsx — "Open in Obsidian" action (future)
 *
 * Wiring:
 *   - @tauri-apps/plugin-shell `open()` for URI launching in Tauri context
 *   - window.open() fallback for browser context (dev mode)
 *   - Settings vaultPath from localStorage 'canvas-learning-settings'
 */

import { open as tauriOpen } from '@tauri-apps/plugin-shell';

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export interface ObsidianLinkResult {
  success: boolean;
  method: 'adv-uri' | 'builtin-uri' | 'fallback';
  url?: string;
  copyPath?: string;
  error?: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Settings Access
// ═══════════════════════════════════════════════════════════════════════════════

const SETTINGS_KEY = 'canvas-learning-settings';

/**
 * Read the vault path from localStorage settings.
 * Returns empty string if not configured.
 */
function getVaultPath(): string {
  try {
    const stored = localStorage.getItem(SETTINGS_KEY);
    if (stored) {
      const parsed = JSON.parse(stored) as { vaultPath?: string };
      return parsed.vaultPath ?? '';
    }
  } catch {
    // ignore parse errors
  }
  return '';
}

/**
 * Extract vault name from a full vault path.
 * e.g. "C:\Users\me\Documents\MyVault" -> "MyVault"
 */
function extractVaultName(vaultPath: string): string {
  // Handle both Windows backslash and Unix forward slash
  const parts = vaultPath.replace(/\\/g, '/').split('/').filter(Boolean);
  return parts[parts.length - 1] ?? '';
}

// ═══════════════════════════════════════════════════════════════════════════════
// URI Builders
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Build an obsidian://adv-uri URL.
 * Requires the Obsidian Advanced URI community plugin to be installed.
 * Supports heading-level navigation.
 */
function buildAdvUri(vaultName: string, filePath: string, heading?: string): string {
  const params = new URLSearchParams();
  params.set('vault', vaultName);
  params.set('filepath', filePath);
  if (heading) {
    params.set('heading', heading);
  }
  return `obsidian://adv-uri?${params.toString()}`;
}

/**
 * Build an obsidian://open URL.
 * Uses Obsidian's built-in URI handler. File-level only, no heading support.
 */
function buildBuiltinUri(vaultName: string, filePath: string): string {
  const params = new URLSearchParams();
  params.set('vault', vaultName);
  params.set('file', filePath);
  return `obsidian://open?${params.toString()}`;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Tauri Environment Detection
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Check if we're running inside a Tauri webview (vs plain browser).
 */
function isTauriEnv(): boolean {
  return '__TAURI_INTERNALS__' in window;
}

/**
 * Attempt to open a URI using Tauri shell plugin, falling back to window.open.
 */
async function openUri(uri: string): Promise<boolean> {
  if (isTauriEnv()) {
    try {
      await tauriOpen(uri);
      return true;
    } catch (err) {
      console.warn('[obsidian-link] Tauri open failed, trying window.open:', err);
    }
  }
  // Fallback: browser context or Tauri open failed
  try {
    window.open(uri, '_blank');
    return true;
  } catch {
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Public API
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Open a file in Obsidian with three-level degradation:
 *   1. adv-uri (heading-level navigation)
 *   2. built-in URI (file-level only)
 *   3. fallback (returns copy-ready path)
 *
 * @param filePath - Relative file path within the vault (e.g. "Notes/Math.md")
 * @param heading  - Optional heading to navigate to (e.g. "Derivatives")
 * @param vaultPathOverride - Override vault path (defaults to settings)
 */
export async function openInObsidian(
  filePath: string,
  heading?: string,
  vaultPathOverride?: string,
): Promise<ObsidianLinkResult> {
  const vaultPath = vaultPathOverride ?? getVaultPath();

  if (!vaultPath) {
    return {
      success: false,
      method: 'fallback',
      copyPath: filePath,
      error: 'Vault path not configured in Settings. Please set the Obsidian Vault path.',
    };
  }

  const vaultName = extractVaultName(vaultPath);
  if (!vaultName) {
    return {
      success: false,
      method: 'fallback',
      copyPath: filePath,
      error: 'Could not extract vault name from path.',
    };
  }

  // Level 1: Try adv-uri (supports heading navigation)
  const advUri = buildAdvUri(vaultName, filePath, heading);
  const advOpened = await openUri(advUri);
  if (advOpened) {
    return { success: true, method: 'adv-uri', url: advUri };
  }

  // Level 2: Try built-in URI (file-level only)
  const builtinUri = buildBuiltinUri(vaultName, filePath);
  const builtinOpened = await openUri(builtinUri);
  if (builtinOpened) {
    return { success: true, method: 'builtin-uri', url: builtinUri };
  }

  // Level 3: Fallback — return copy-ready path
  const fullPath = `${vaultPath.replace(/[/\\]$/, '')}/${filePath}`;
  return {
    success: false,
    method: 'fallback',
    copyPath: fullPath,
    error: 'Could not open Obsidian. Path copied to clipboard.',
  };
}

/**
 * Parse a wiki-link string like "file#section" or just "file".
 * Returns the file path and optional heading.
 */
export function parseWikiLink(link: string): { filePath: string; heading?: string } {
  const hashIndex = link.indexOf('#');
  if (hashIndex === -1) {
    return { filePath: link };
  }
  return {
    filePath: link.substring(0, hashIndex),
    heading: link.substring(hashIndex + 1),
  };
}
