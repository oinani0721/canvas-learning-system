/**
 * sync-vault.mjs - Sync manifest.json and styles.css to vault plugin directory.
 * Used by: npm run deploy:sync
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

if (!fs.existsSync(vaultDir)) {
	console.error(`🔴 Vault plugin dir not found: ${vaultDir}`);
	console.error("   Set OBSIDIAN_VAULT env or ensure default vault exists.");
	process.exit(1);
}

const assets = ["manifest.json", "styles.css"];
let synced = 0;

for (const file of assets) {
	const src = path.join(pluginRoot, file);
	const dest = path.join(vaultDir, file);
	if (fs.existsSync(src)) {
		fs.copyFileSync(src, dest);
		console.log(`✅ Synced ${file} → vault`);
		synced++;
	} else {
		console.log(`⏭️  Skipped ${file} (not found in source)`);
	}
}

console.log(`\n📦 Synced ${synced} asset(s) to: ${vaultDir}`);
