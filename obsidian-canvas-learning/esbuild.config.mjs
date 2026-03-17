import esbuild from 'esbuild';
import esbuildSvelte from 'esbuild-svelte';
import sveltePreprocess from 'svelte-preprocess';
import process from 'process';
import { readFileSync } from 'fs';
import { compileModule } from 'svelte/compiler';

const prod = process.argv.includes('--production');
const watch = process.argv.includes('--watch');

// Read manifest for banner
const manifest = JSON.parse(readFileSync('./manifest.json', 'utf-8'));

/**
 * Custom esbuild plugin for .svelte.ts/.svelte.js files.
 *
 * Svelte 5 "runes mode" files (.svelte.ts) use $state/$derived/$effect
 * outside of .svelte components. The standard esbuild-svelte plugin only
 * handles .svelte files via compile(). These module-scope rune files
 * must be processed via compileModule() instead.
 *
 * Pipeline: .svelte.ts -> esbuild (strip TS types) -> compileModule() -> JS
 */
function svelteModulePlugin() {
  return {
    name: 'esbuild-svelte-modules',
    setup(build) {
      // Intercept .svelte.ts and .svelte.js files
      build.onLoad({ filter: /\.svelte\.(ts|js)$/ }, async (args) => {
        const source = readFileSync(args.path, 'utf-8');

        // Step 1: Strip TypeScript types using esbuild's transform
        const stripped = await esbuild.transform(source, {
          loader: args.path.endsWith('.ts') ? 'ts' : 'js',
          target: 'es2022',
          // Preserve class fields to avoid issues with $state transform
          keepNames: true,
        });

        // Step 2: Compile with Svelte 5 compileModule()
        const result = compileModule(stripped.code, {
          filename: args.path,
          generate: 'client',
        });

        // Report warnings
        if (result.warnings?.length) {
          for (const w of result.warnings) {
            console.warn(`[svelte-module] ${args.path}: ${w.message}`);
          }
        }

        return {
          contents: result.js.code,
          loader: 'js',
        };
      });
    },
  };
}

const context = await esbuild.context({
  entryPoints: ['main.ts'],
  bundle: true,
  // Svelte 5 组件库解析必需
  mainFields: ['svelte', 'browser', 'module', 'main'],
  conditions: ['svelte', 'browser'],
  external: [
    'obsidian',
    'electron',
    'child_process',
    'util',
    'path',
    'fs',
    '@codemirror/autocomplete',
    '@codemirror/collab',
    '@codemirror/commands',
    '@codemirror/language',
    '@codemirror/lint',
    '@codemirror/search',
    '@codemirror/state',
    '@codemirror/view',
    '@lezer/common',
    '@lezer/highlight',
    '@lezer/lr',
  ],
  format: 'cjs',
  target: 'es2022',
  logLevel: 'info',
  sourcemap: prod ? false : 'inline',
  treeShaking: true,
  outfile: 'main.js',
  minify: prod,
  plugins: [
    // Must come BEFORE esbuild-svelte so .svelte.ts files are handled
    // before esbuild's default TS loader processes them
    svelteModulePlugin(),
    esbuildSvelte({
      preprocess: sveltePreprocess({ typescript: true }),
      compilerOptions: {
        css: 'injected',
        runes: true,  // Svelte 5 runes mode
      },
    }),
  ],
  banner: {
    js: `/* ${manifest.name} v${manifest.version} */`,
  },
});

if (watch) {
  await context.watch();
  console.log('Watching for changes...');
} else {
  await context.rebuild();
  await context.dispose();
}
