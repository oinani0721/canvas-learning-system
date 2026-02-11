#!/usr/bin/env node
/**
 * deploy.mjs - 一键编译 + 部署 + 同步 + 验证
 *
 * 执行步骤:
 * 1. TypeScript 类型检查
 * 2. esbuild 编译到 vault
 * 3. 同步 manifest.json 和 styles.css 到 vault
 * 4. 验证部署状态
 *
 * 用法: npm run deploy
 */
import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pluginRoot = path.join(__dirname, '..');
const vaultPluginDir = path.join(pluginRoot, '..', '..', '笔记库', '.obsidian', 'plugins', 'canvas-review-system');

// ANSI colors
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const RESET = '\x1b[0m';
const BOLD = '\x1b[1m';

console.log(`${BOLD}=== Canvas Plugin Deploy ===${RESET}\n`);

// Step 0: Verify vault directory exists
if (!fs.existsSync(vaultPluginDir)) {
    console.log(`${RED}[FAIL]${RESET} vault 插件目录不存在: ${vaultPluginDir}`);
    process.exit(1);
}

// Step 1: TypeScript check + esbuild (build script handles both)
console.log(`${YELLOW}[1/3]${RESET} 编译 TypeScript → vault main.js ...`);
try {
    execSync('npm run build', { cwd: pluginRoot, stdio: 'inherit' });
} catch (e) {
    console.log(`\n${RED}[FAIL]${RESET} 编译失败`);
    process.exit(1);
}

// Step 2: Sync manifest.json and styles.css
console.log(`\n${YELLOW}[2/3]${RESET} 同步 manifest.json + styles.css → vault ...`);
const filesToSync = ['manifest.json', 'styles.css'];
for (const file of filesToSync) {
    const src = path.join(pluginRoot, file);
    const dest = path.join(vaultPluginDir, file);
    if (fs.existsSync(src)) {
        fs.copyFileSync(src, dest);
        console.log(`  ✅ ${file}`);
    } else {
        console.log(`  ⚠️ ${file} 不存在，跳过`);
    }
}

// Step 3: Verify
console.log(`\n${YELLOW}[3/3]${RESET} 验证部署 ...`);
const vaultMainJs = path.join(vaultPluginDir, 'main.js');
if (fs.existsSync(vaultMainJs)) {
    const stat = fs.statSync(vaultMainJs);
    const size = (stat.size / 1024).toFixed(0);
    const mtime = new Date(stat.mtimeMs).toLocaleString();
    console.log(`  vault main.js: ${size} KB @ ${mtime}`);
    console.log(`\n${GREEN}${BOLD}✅ 部署完成！${RESET} Obsidian 将通过 hot-reload 自动加载。`);
} else {
    console.log(`${RED}[FAIL]${RESET} vault main.js 不存在`);
    process.exit(1);
}
