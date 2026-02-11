#!/usr/bin/env node
/**
 * verify.mjs - 验证 vault 中的 main.js 是否与源码同步
 *
 * 检查项:
 * 1. vault main.js 是否存在
 * 2. vault main.js 的修改时间是否比源码 main.ts 更新
 * 3. vault main.js 的文件大小是否合理
 *
 * 用法: npm run verify
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pluginRoot = path.join(__dirname, '..');
const vaultPluginDir = path.join(pluginRoot, '..', '..', '笔记库', '.obsidian', 'plugins', 'canvas-review-system');
const vaultMainJs = path.join(vaultPluginDir, 'main.js');
const sourceMainTs = path.join(pluginRoot, 'main.ts');
const sourceSrcDir = path.join(pluginRoot, 'src');

// ANSI colors
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const RESET = '\x1b[0m';
const BOLD = '\x1b[1m';

function getNewestSourceTime(dir) {
    let newest = 0;
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            const sub = getNewestSourceTime(fullPath);
            if (sub > newest) newest = sub;
        } else if (entry.name.endsWith('.ts') || entry.name.endsWith('.css')) {
            const stat = fs.statSync(fullPath);
            if (stat.mtimeMs > newest) newest = stat.mtimeMs;
        }
    }
    return newest;
}

console.log(`${BOLD}=== Canvas Plugin Deployment Verify ===${RESET}\n`);

// Check 1: vault directory exists
if (!fs.existsSync(vaultPluginDir)) {
    console.log(`${RED}[FAIL]${RESET} vault 插件目录不存在: ${vaultPluginDir}`);
    process.exit(1);
}

// Check 2: vault main.js exists
if (!fs.existsSync(vaultMainJs)) {
    console.log(`${RED}[FAIL]${RESET} vault main.js 不存在: ${vaultMainJs}`);
    console.log(`  运行: npm run build`);
    process.exit(1);
}

const vaultStat = fs.statSync(vaultMainJs);
const vaultMtime = vaultStat.mtimeMs;
const vaultSize = vaultStat.size;

// Check 3: source files
const mainTsStat = fs.statSync(sourceMainTs);
const newestSrcTime = getNewestSourceTime(sourceSrcDir);
const newestSourceTime = Math.max(mainTsStat.mtimeMs, newestSrcTime);

const vaultDate = new Date(vaultMtime);
const sourceDate = new Date(newestSourceTime);
const ageSec = Math.round((Date.now() - vaultMtime) / 1000);
const ageMin = Math.round(ageSec / 60);

console.log(`  vault main.js: ${(vaultSize / 1024).toFixed(0)} KB`);
console.log(`  vault 修改时间: ${vaultDate.toLocaleString()}`);
console.log(`  源码最新修改: ${sourceDate.toLocaleString()}`);
console.log(`  vault 年龄: ${ageMin < 60 ? ageMin + ' 分钟' : Math.round(ageMin / 60) + ' 小时'}`);
console.log('');

if (vaultMtime >= newestSourceTime) {
    console.log(`${GREEN}${BOLD}  ✅ FRESH${RESET} — vault main.js 比源码更新`);
    process.exit(0);
} else {
    const lagSec = Math.round((newestSourceTime - vaultMtime) / 1000);
    const lagMin = Math.round(lagSec / 60);
    console.log(`${RED}${BOLD}  🔴 STALE${RESET} — vault main.js 落后源码 ${lagMin < 60 ? lagMin + ' 分钟' : Math.round(lagMin / 60) + ' 小时'}`);
    console.log(`  ${YELLOW}运行: npm run deploy${RESET}`);
    process.exit(1);
}
