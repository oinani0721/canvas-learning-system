'use strict';
// node --test .claude/hooks/tests/readonly-path-guard.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const os = require('os');
const fs = require('fs');
const path = require('path');
const { decide, DEFAULT_CONFIG } = require('../readonly-path-guard.js');

const PRD = DEFAULT_CONFIG.prd_files[0];
const VAULT = DEFAULT_CONFIG.live_vaults[0];
const DEV = '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output';
// point the bypass file at a path that never exists so tests are deterministic
const cfg = Object.assign({}, DEFAULT_CONFIG, { bypass_file: path.join(os.tmpdir(), 'no-such-bypass-' + process.pid) });

const edit = (file_path, cwd = DEV) => ({ tool_name: 'Edit', tool_input: { file_path }, cwd });
const write = (file_path, cwd = DEV) => ({ tool_name: 'Write', tool_input: { file_path }, cwd });
const bash = (command, cwd = DEV) => ({ tool_name: 'Bash', tool_input: { command }, cwd });

test('R1: Edit/Write on PRD is blocked in any cwd', () => {
  assert.equal(decide(edit(PRD), cfg).allow, false);
  assert.equal(decide(write(PRD, VAULT), cfg).allow, false);
  assert.equal(decide(edit(PRD), cfg).rule, 'R1');
});

test('R1: Bash write indicators on PRD are blocked, reads pass', () => {
  assert.equal(decide(bash(`echo x >> "${PRD}"`), cfg).allow, false);
  assert.equal(decide(bash(`sed -i '' 's/a/b/' "${PRD}"`), cfg).allow, false);
  assert.equal(decide(bash(`cp /tmp/x "${PRD}"`), cfg).allow, false);
  assert.equal(decide(bash(`cat "${PRD}" | head`), cfg).allow, true);
  assert.equal(decide(bash(`grep -n foo "${PRD}" 2>&1`), cfg).allow, true);
  assert.equal(decide(bash(`sed -n '1,10p' "${PRD}"`), cfg).allow, true);
  assert.equal(decide(bash(`wc -l "${PRD}" > /dev/null`), cfg).allow, true);
  // basename alone is enough to trigger the PRD rule
  assert.equal(decide(bash(`printf 'x' > 14-scheme-a-implementation-prd.md`), cfg).allow, false);
});

test('R2: live vault writes blocked from dev cwd, allowed from inside the vault', () => {
  const f = path.join(VAULT, '节点', 'Fundamentals.md');
  assert.equal(decide(write(f, DEV), cfg).allow, false);
  assert.equal(decide(write(f, DEV), cfg).rule, 'R2');
  assert.equal(decide(write(f, VAULT), cfg).allow, true);
  assert.equal(decide(write(f, path.join(VAULT, '节点')), cfg).allow, true);
  assert.equal(decide(bash(`cp /tmp/a.py "${VAULT}/.claude/scripts/fsrs_bridge.py"`, DEV), cfg).allow, false);
  assert.equal(decide(bash(`cp /tmp/a.py "${VAULT}/.claude/scripts/fsrs_bridge.py"`, VAULT), cfg).allow, true);
  assert.equal(decide(bash(`tee "${VAULT}/x.md" < /tmp/y`, DEV), cfg).allow, false);
  assert.equal(decide(bash(`echo hi > "${VAULT}/x.md"`, DEV), cfg).allow, false);
});

test('R2: relative mention from main repo root counts; reads never block', () => {
  const MAIN = '/Users/Heishing/Desktop/canvas/canvas-learning-system';
  assert.equal(decide(bash(`cp x.md canvas-vault/节点/y.md`, MAIN), cfg).allow, false);
  assert.equal(decide(bash(`grep -rn foo canvas-vault/ | head`, MAIN), cfg).allow, true);
  assert.equal(decide(bash(`git status --porcelain canvas-vault/`, MAIN), cfg).allow, true);
  assert.equal(decide(bash(`shasum -a 256 "${VAULT}/节点/Fundamentals.md"`, DEV), cfg).allow, true);
  assert.equal(decide(bash(`ls -la "${VAULT}/原白板"`, DEV), cfg).allow, true);
  // a file with the same folder name elsewhere is not the live vault
  assert.equal(decide(write('/tmp/canvas-vault/x.md', DEV), cfg).allow, true);
  assert.equal(decide(bash(`cp a /tmp/canvas-vault/x.md`, DEV), cfg).allow, true);
});

test('copy-like commands: protected path as SOURCE is a read, as DESTINATION is a write', () => {
  const f = path.join(VAULT, '节点', 'Fundamentals.md');
  assert.equal(decide(bash(`cp "${f}" /tmp/copy.md`, DEV), cfg).allow, true);
  assert.equal(decide(bash(`cp "${PRD}" /dev/null`, DEV), cfg).allow, true);
  assert.equal(decide(bash(`rsync -a "${VAULT}/" /tmp/vault-snapshot/`, DEV), cfg).allow, true);
  assert.equal(decide(bash(`cp /tmp/copy.md "${f}"`, DEV), cfg).allow, false);
  assert.equal(decide(bash(`mv /tmp/x.md "${VAULT}/节点/"`, DEV), cfg).allow, false);
  assert.equal(decide(bash(`cp -r /tmp/dir "${VAULT}"`, DEV), cfg).allow, false);
  assert.equal(decide(bash(`ditto /tmp/a "${VAULT}/b"`, DEV), cfg).allow, false);
  assert.equal(decide(bash(`cat "${f}" && cp /tmp/z "${PRD}"`, DEV), cfg).allow, false);
  // reading the vault then writing elsewhere in the same chain stays a read
  assert.equal(decide(bash(`cp "${f}" /tmp/a.md && echo done > /tmp/b.txt`, DEV), cfg).allow, true);
});

test('R3: Obsidian CLI write/exec subcommands blocked, read subcommands pass', () => {
  const BIN = '/Applications/Obsidian.app/Contents/MacOS/obsidian-cli';
  assert.equal(decide(bash(`${BIN} vault=0a302bd176301457 backlinks file=Fundamentals format=json`), cfg).allow, true);
  assert.equal(decide(bash(`obsidian search:context query=foo`), cfg).allow, true);
  assert.equal(decide(bash(`obsidian vault=abc outline file=x format=json`), cfg).allow, true);
  assert.equal(decide(bash(`obsidian eval code="app.vault.getFiles().length"`), cfg).allow, false);
  assert.equal(decide(bash(`${BIN} vault=0a302bd176301457 create name=x content=y`), cfg).allow, false);
  assert.equal(decide(bash(`perl -e 'alarm 25; exec @ARGV' -- ${BIN} vault=abc delete file=x`), cfg).allow, false);
  assert.equal(decide(bash(`obsidian property:set name=a value=b`), cfg).allow, false);
  assert.equal(decide(bash(`obsidian command id=editor:rename-heading`), cfg).allow, false);
  assert.equal(decide(bash(`obsidian vault=abc append file=x content=y`), cfg).allow, false);
  // blocked even when cwd is inside the vault (CLI targets vaults by id, not cwd)
  assert.equal(decide(bash(`obsidian eval code=1`, VAULT), cfg).allow, false);
  // unrelated words are not the CLI
  assert.equal(decide(bash(`echo "obsidian is great" && cat notes.md`), cfg).allow, true);
});

test('R4: bypass file within window allows everything', () => {
  const bp = path.join(os.tmpdir(), 'readonly-guard-bypass-test-' + process.pid);
  fs.writeFileSync(bp, '');
  const c2 = Object.assign({}, cfg, { bypass_file: bp });
  try {
    assert.equal(decide(edit(PRD), c2).allow, true);
    assert.equal(decide(bash(`obsidian eval code=1`), c2).allow, true);
  } finally { fs.unlinkSync(bp); }
});

test('other tools and malformed input are allowed (fail-open)', () => {
  assert.equal(decide({ tool_name: 'Read', tool_input: { file_path: PRD }, cwd: DEV }, cfg).allow, true);
  assert.equal(decide({ tool_name: 'Grep', tool_input: { pattern: 'x', path: VAULT }, cwd: DEV }, cfg).allow, true);
  assert.equal(decide({}, cfg).allow, true);
  assert.equal(decide({ tool_name: 'Bash', tool_input: {}, cwd: DEV }, cfg).allow, true);
});
