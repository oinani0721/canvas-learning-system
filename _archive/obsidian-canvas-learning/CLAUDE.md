# Canvas Learning Plugin

## Project
- Obsidian plugin (pure TypeScript, no UI framework)
- Entry: src/main.ts, src/settings.ts
- Build: `npm run dev` (esbuild watch) or `npm run build` (production)
- Deploy: copy main.js + manifest.json + styles.css to vault plugin dir
- Progress tracking: PROGRESS.md (update checkboxes when done)

## Obsidian API Rules (DD-06)
- Use `containerEl.createEl()` / `createDiv()` — never `document.createElement()`
- Use `setText()` / `createEl()` — never `innerHTML`
- Use CSS classes in styles.css — never `element.style.X = Y`
- Use `this.registerDomEvent()` — never raw `addEventListener()`
- Use `this.registerEvent()` for workspace events
- Use `this.registerInterval(window.setInterval(...))` — never raw `setInterval()`
- Use Obsidian's `requestUrl()` — never `fetch()`
- Colors: use CSS variables (`var(--text-normal)`) — never hardcoded hex
- CSS selectors: prefix with `.canvas-learning-*`

## Hard Constraints
- All code must have real implementations — no stubs, no fake data, no empty functions
- No UI framework (no Svelte, no React, no Preact)
- Every code change must be verified in Obsidian before proceeding
- Max 80 lines per step

## Files
- `_v1-ref/` — old code for reference (api-client.ts reusable)
- `_reference/obsidian-sample-plugin/` — official template reference
