/**
 * verify-vault.mjs - Verify vault main.js is fresh (updated recently).
 * Used by: npm run verify
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pluginRoot = path.resolve(__dirname, "..");
const PLUGIN_ID = "canvas-review-system";

function getVaultDir() {
	if (process.env.OBSIDIAN_VAULT) {
		return path.join(process.env.OBSIDIAN_VAULT, ".obsidian", "plugins", PLUGIN_ID);
	}
	return path.resolve(pluginRoot, "../../笔记库/.obsidian/plugins", PLUGIN_ID);
}

const vaultDir = getVaultDir();
const mainJs = path.join(vaultDir, "main.js");

if (!fs.existsSync(mainJs)) {
	console.error(`🔴 NOT FOUND: ${mainJs}`);
	console.error("   Run 'npm run build' first to compile and deploy.");
	process.exit(1);
}

const stat = fs.statSync(mainJs);
const ageMs = Date.now() - stat.mtimeMs;
const ageSec = Math.round(ageMs / 1000);
const ageMin = Math.round(ageMs / 60000);
const size = (stat.size / 1024).toFixed(1);

// 5 minutes = 300000ms
const FRESH_THRESHOLD = 300000;

if (ageMs < FRESH_THRESHOLD) {
	console.log(`✅ FRESH — vault main.js updated ${ageSec}s ago (${size} KB)`);
	console.log(`   Path: ${mainJs}`);
} else {
	console.log(`🔴 STALE — vault main.js updated ${ageMin} min ago (${size} KB)`);
	console.log(`   Path: ${mainJs}`);
	console.log(`   Run 'npm run build' to refresh.`);
	process.exit(1);
}

// Also check manifest.json sync
const srcManifest = path.join(pluginRoot, "manifest.json");
const vaultManifest = path.join(vaultDir, "manifest.json");
if (fs.existsSync(srcManifest) && fs.existsSync(vaultManifest)) {
	const srcVersion = JSON.parse(fs.readFileSync(srcManifest, "utf-8")).version;
	const vaultVersion = JSON.parse(fs.readFileSync(vaultManifest, "utf-8")).version;
	if (srcVersion === vaultVersion) {
		console.log(`✅ manifest.json version synced: ${srcVersion}`);
	} else {
		console.log(`🔴 manifest.json version mismatch! source=${srcVersion} vault=${vaultVersion}`);
		console.log(`   Run 'npm run deploy:sync' to fix.`);
		process.exit(1);
	}
}
