import esbuild from 'esbuild';
import esbuildSvelte from 'esbuild-svelte';
import sveltePreprocess from 'svelte-preprocess';
import process from 'process';
import { readFileSync } from 'fs';

const prod = process.argv.includes('--production');
const watch = process.argv.includes('--watch');

// Read manifest for banner
const manifest = JSON.parse(readFileSync('./manifest.json', 'utf-8'));

const context = await esbuild.context({
  entryPoints: ['main.ts'],
  bundle: true,
  external: [
    'obsidian',
    'electron',
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
    esbuildSvelte({
      preprocess: sveltePreprocess({ typescript: true }),
      compilerOptions: {
        css: 'injected',
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
