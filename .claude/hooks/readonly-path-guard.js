#!/usr/bin/env node
/**
 * readonly-path-guard — PreToolUse hook (Edit / Write / MultiEdit / NotebookEdit / Bash)
 *
 * D-H (2026-09-14): CLAUDE.md promised "PRD 只读，pretool-guard.js 强制阻断" but
 * pretool-guard.js only checks DD-03 stub patterns and never looks at paths, and the
 * worktree quarantined project hooks (GOV-01). This hook is the real, path-level guard.
 *
 * Rules
 *   R1  PRD anchor file is read-only for every tool, in every session.
 *   R2  Live vault is read-only for sessions whose cwd is OUTSIDE the vault
 *       (dev sessions). Sessions running inside the vault (runtime skills) are exempt.
 *   R3  Obsidian CLI write / exec subcommands (eval, create, delete, move, ...) are
 *       blocked in every session; read subcommands (backlinks, links, search, ...) pass.
 *   R4  Human bypass: the user (not Claude) runs  `touch ~/.claude/readonly-guard.allow`
 *       in their own terminal; the guard then allows writes for bypass_window_min minutes.
 *
 * Bash detection is per command segment (split on && || ; | ` newline) and looks at the
 * *write target* of each segment: redirection targets, copy-like destinations (cp/mv/ditto/
 * rsync/install/ln last argument), tee arguments, and in-place/destructive tokens (sed -i,
 * perl -i, rm, touch, mkdir, git checkout/restore, ...) that mention a protected path.
 * A protected path used only as a *source* (cp <vault>/x /tmp/y, cat, grep, shasum) passes.
 * Heredoc / quoted text that merely *mentions* a protected path is not a write.
 *
 * Exit 2 = block (stderr shown to Claude) · Exit 0 = allow · parse failure = allow (fail-open,
 * same convention as pretool-guard.js).
 *
 * Installed copy: ~/.claude/readonly-path-guard.js (wired in ~/.claude/settings.json).
 * Source of truth: <repo>/.claude/hooks/readonly-path-guard.js · tests: .claude/hooks/tests/
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const HOME = os.homedir();
const DEFAULT_CONFIG = {
  prd_files: [
    '/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md',
  ],
  live_vaults: [
    '/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault',
  ],
  bypass_file: path.join(HOME, '.claude', 'readonly-guard.allow'),
  bypass_window_min: 20,
};

function loadConfig() {
  const override = process.env.CLS_READONLY_GUARD_CONFIG || path.join(HOME, '.claude', 'readonly-paths.json');
  try {
    if (fs.existsSync(override)) {
      const user = JSON.parse(fs.readFileSync(override, 'utf8'));
      return Object.assign({}, DEFAULT_CONFIG, user);
    }
  } catch (_) { /* fall through to defaults */ }
  return DEFAULT_CONFIG;
}

function norm(p) {
  if (!p) return '';
  let s = String(p);
  if (s.startsWith('~/')) s = path.join(HOME, s.slice(2));
  s = path.normalize(s);
  try { s = fs.realpathSync(s); } catch (_) { /* not existing yet: keep normalized */ }
  return s;
}

function isInside(file, dir) {
  const f = norm(file), d = norm(dir);
  return f === d || f.startsWith(d + path.sep);
}

function bypassActive(cfg) {
  try {
    const st = fs.statSync(cfg.bypass_file);
    const ageMin = (Date.now() - st.mtimeMs) / 60000;
    // allow ~1 min of negative skew: fs mtime (ns) can be marginally ahead of Date.now() (ms)
    return ageMin >= -1 && ageMin <= cfg.bypass_window_min;
  } catch (_) { return false; }
}

// ---------- protected-path classification ----------
/** {kind:'prd'|'vault', target} when `candidate` (a path string, maybe relative/quoted) hits a protected path */
function classify(candidate, cwd, cfg) {
  if (!candidate) return null;
  const raw = String(candidate).replace(/^["']|["']$/g, '');
  const abs = path.isAbsolute(raw) || raw.startsWith('~/') ? norm(raw) : norm(path.join(cwd || '', raw));
  for (const f of cfg.prd_files) {
    if (abs === norm(f) || raw === f || raw.endsWith(path.basename(f))) return { kind: 'prd', target: f };
  }
  for (const v of cfg.live_vaults) {
    if (isInside(abs, v) || raw === v || raw.startsWith(v + '/')) return { kind: 'vault', target: v };
  }
  return null;
}

function mentionsProtected(cmd, cwd, cfg) {
  const hits = [];
  for (const f of cfg.prd_files) {
    if (cmd.includes(f) || cmd.includes(path.basename(f))) hits.push({ kind: 'prd', target: f });
  }
  for (const v of cfg.live_vaults) {
    if (cmd.includes(v)) { hits.push({ kind: 'vault', target: v }); continue; }
    const rel = path.basename(v);
    const cwdN = norm(cwd || '');
    if (cwdN && isInside(path.join(cwdN, rel), v) && new RegExp('(^|[\\s"\'=])' + rel + '/').test(cmd)) {
      hits.push({ kind: 'vault', target: v });
    }
  }
  return hits;
}

// ---------- Obsidian CLI ----------
const OBSIDIAN_WRITE_SUBCMDS = [
  'eval', 'create', 'delete', 'move', 'rename', 'append', 'prepend', 'unique',
  'property:set', 'property:remove', 'daily:append', 'daily:prepend',
  'plugin:install', 'plugin:uninstall', 'plugin:enable', 'plugin:disable', 'plugin:reload', 'plugins:restrict',
  'theme:set', 'theme:install', 'theme:uninstall', 'snippet:enable', 'snippet:disable',
  'sync:restore', 'sync:on', 'sync:off', 'publish:add', 'publish:remove', 'history:restore',
  'restart', 'reload', 'command', 'bookmark', 'base:create', 'template:insert',
  'workspace:save', 'workspace:load', 'workspace:delete', 'web', 'devtools', 'dev:cdp', 'dev:debug', 'dev:mobile',
];

function obsidianWriteHit(cmd) {
  const re = /(^|[\s;&|`(])(?:[^\s;&|`]*\/)?(?:obsidian-cli|obsidian)(\s+(?:vault=\S+\s+)?)([a-z][a-z:-]*)/g;
  let m;
  while ((m = re.exec(cmd)) !== null) {
    const sub = m[3];
    if (OBSIDIAN_WRITE_SUBCMDS.includes(sub)) return sub;
  }
  return null;
}

// ---------- Bash write-target extraction (per segment) ----------
const ARG_RE = /"[^"]*"|'[^']*'|\S+/g;
const SEG_SPLIT_RE = /(?:&&|\|\||[;|`\n])/;
// redirection target: `> file`, `>> file`, `2> file` — not `2>&1`, `>&2`, `<`
const REDIRECT_TARGET_RE = /(?:^|[^<])(?:>>?|\d>)(?!&)\s*("[^"]*"|'[^']*'|[^\s;&|]+)/g;
const COPY_LIKE_RE = /(?:^|\s)(cp|mv|ditto|rsync|install|ln)\s+(.*)$/;
const TEE_RE = /(?:^|\s)tee\s+(.*)$/;
// commands that write in place / destructively to the paths they mention (first word of the segment only)
const INPLACE_RE = /^(?:sudo\s+)?(sed\s+(?:-[a-zA-Z]*i|--in-place)|perl\s+-[a-zA-Z]*i|truncate|shred|rm|rmdir|touch|mkdir|chmod|chown|xattr\s+-[wd]|python3?\s+-c|git\s+(?:checkout|restore|stash|clean|mv|rm|apply|am|rebase|merge|reset|cherry-pick|revert|pull))(?:\s|$)/;

function writeTargetsOfSegment(seg) {
  const out = [];
  let m;
  REDIRECT_TARGET_RE.lastIndex = 0;
  while ((m = REDIRECT_TARGET_RE.exec(seg)) !== null) {
    const t = m[1].replace(/^["']|["']$/g, '');
    if (t !== '/dev/null') out.push(t);
  }
  const c = COPY_LIKE_RE.exec(seg);
  if (c) {
    const args = (c[2].match(ARG_RE) || []).filter(a => !/^-/.test(a));
    if (args.length) out.push(args[args.length - 1]);
  }
  const t = TEE_RE.exec(seg);
  if (t) for (const a of (t[1].match(ARG_RE) || [])) if (!/^-/.test(a)) out.push(a);
  return out;
}

/** {kind,target} of the first protected path this segment would write, or null */
function segmentWrites(seg, cwd, cfg) {
  for (const tgt of writeTargetsOfSegment(seg)) {
    const c = classify(tgt, cwd, cfg);
    if (c) return c;
  }
  if (INPLACE_RE.test(seg)) {
    const hits = mentionsProtected(seg, cwd, cfg);
    if (hits.length) return hits[0];
  }
  return null;
}

function decide(data, cfg) {
  const tool = data.tool_name || '';
  const input = data.tool_input || {};
  const cwd = data.cwd || process.cwd();

  if (bypassActive(cfg)) return { allow: true, reason: 'bypass-file' };

  // ---- file-editing tools ----
  if (/^(Edit|Write|MultiEdit|NotebookEdit)$/i.test(tool)) {
    const raw = input.file_path || input.notebook_path || '';
    if (!raw) return { allow: true };
    const fp = path.isAbsolute(raw) ? norm(raw) : norm(path.join(cwd, raw));
    for (const f of cfg.prd_files) {
      if (norm(f) === fp) return { allow: false, rule: 'R1', msg: `PRD 锚定文档只读：${f}` };
    }
    for (const v of cfg.live_vaults) {
      if (isInside(fp, v) && !isInside(cwd, v)) {
        return { allow: false, rule: 'R2', msg: `线上 vault 只读（会话 cwd 在 vault 之外）：${fp}` };
      }
    }
    return { allow: true };
  }

  // ---- Bash ----
  if (/^Bash$/i.test(tool)) {
    const cmd = String(input.command || '');
    if (!cmd) return { allow: true };
    const ob = obsidianWriteHit(cmd);
    if (ob) return { allow: false, rule: 'R3', msg: `Obsidian CLI 写/执行子命令被拦：${ob}` };
    if (mentionsProtected(cmd, cwd, cfg).length === 0) return { allow: true };   // cheap pre-filter
    for (const rawSeg of cmd.split(SEG_SPLIT_RE)) {
      const seg = rawSeg.trim();
      if (!seg) continue;
      const w = segmentWrites(seg, cwd, cfg);
      if (!w) continue;
      if (w.kind === 'prd') return { allow: false, rule: 'R1', msg: `PRD 锚定文档只读，命令段会写入它：${w.target}` };
      if (w.kind === 'vault' && !isInside(cwd, w.target)) {
        return { allow: false, rule: 'R2', msg: `线上 vault 只读（会话 cwd 在 vault 之外），命令段会写入它：${w.target}` };
      }
    }
    return { allow: true };
  }
  return { allow: true };
}

function main() {
  const chunks = [];
  process.stdin.on('data', (c) => chunks.push(c));
  process.stdin.on('end', () => {
    let data;
    try { data = JSON.parse(Buffer.concat(chunks).toString() || '{}'); } catch (_) { process.exit(0); }
    const cfg = loadConfig();
    const d = decide(data, cfg);
    if (d.allow) process.exit(0);
    process.stderr.write(
      `[readonly-path-guard ${d.rule}] ${d.msg}\n` +
      `这是 CLAUDE.md「只读锚定」的真实执行层。若确需写入：由用户本人在 Claude 之外的终端执行 ` +
      `\`touch ${cfg.bypass_file}\`（${cfg.bypass_window_min} 分钟窗口），Claude 不得自行创建该文件。\n`
    );
    process.exit(2);
  });
}

if (require.main === module) main();
module.exports = { decide, DEFAULT_CONFIG, obsidianWriteHit, mentionsProtected, classify, writeTargetsOfSegment, segmentWrites };
