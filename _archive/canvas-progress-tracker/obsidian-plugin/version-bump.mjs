/**
 * Canvas Review System - Version Bump Script
 *
 * ✅ Verified from Context7: /obsidianmd/obsidian-sample-plugin (version bumping)
 *
 * Automatically updates version numbers in manifest.json and versions.json
 * when running `npm version patch/minor/major`
 */

import { readFileSync, writeFileSync } from "fs";

const targetVersion = process.env.npm_package_version;

// Read manifest.json and update version
let manifest = JSON.parse(readFileSync("manifest.json", "utf8"));
const { minAppVersion } = manifest;
manifest.version = targetVersion;
writeFileSync("manifest.json", JSON.stringify(manifest, null, "\t"));

// Update versions.json
let versions = JSON.parse(readFileSync("versions.json", "utf8"));
versions[targetVersion] = minAppVersion;
writeFileSync("versions.json", JSON.stringify(versions, null, "\t"));

console.log(`Canvas Review System: Version bumped to ${targetVersion}`);
