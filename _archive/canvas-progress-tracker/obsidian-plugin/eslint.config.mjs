import obsidianmd from 'eslint-plugin-obsidianmd';
import tseslint from '@typescript-eslint/eslint-plugin';
import tsparser from '@typescript-eslint/parser';

export default [
  {
    files: ['src/**/*.ts', 'main.ts'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 2020,
        sourceType: 'module',
        project: './tsconfig.json',
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      '@typescript-eslint': tseslint,
      obsidianmd: obsidianmd,
    },
    rules: {
      // === Obsidian 反模式检测 (error = 阻止提交) ===

      // DOM 安全 — 禁止 innerHTML, <style>, <link> 等
      'obsidianmd/no-forbidden-elements': 'error',

      // 类型安全 — 禁止 as TFile / as TFolder 盲转
      'obsidianmd/no-tfile-tfolder-cast': 'error',

      // 内存泄漏 — 禁止存储 view 引用
      'obsidianmd/no-view-references-in-plugin': 'error',

      // 生命周期 — 禁止手动 detach leaves
      'obsidianmd/detach-leaves': 'error',

      // 平台检测 — 禁止 navigator，用 Platform API
      'obsidianmd/platform': 'error',

      // 正则兼容 — 禁止 lookbehind（iOS 崩溃）
      'obsidianmd/regex-lookbehind': 'error',

      // Plugin 反模式 — 禁止把 Plugin 传给 MarkdownRenderer
      'obsidianmd/no-plugin-as-component': 'error',

      // 文件操作 — 用 FileManager.trashFile 而非 Vault.trash
      'obsidianmd/prefer-file-manager-trash-file': 'error',

      // Object.assign 反模式
      'obsidianmd/object-assign': 'error',

      // 硬编码 .obsidian 路径
      'obsidianmd/hardcoded-config-path': 'error',

      // 命令规范
      'obsidianmd/commands/no-command-in-command-id': 'error',
      'obsidianmd/commands/no-command-in-command-name': 'error',
      'obsidianmd/commands/no-default-hotkeys': 'error',
      'obsidianmd/commands/no-plugin-id-in-command-id': 'error',
      'obsidianmd/commands/no-plugin-name-in-command-name': 'error',

      // Settings 规范
      'obsidianmd/settings-tab/no-manual-html-headings': 'error',
      'obsidianmd/settings-tab/no-problematic-settings-headings': 'error',

      // Vault 迭代优化
      'obsidianmd/vault/iterate': 'warn',

      // UI 文本规范
      'obsidianmd/ui/sentence-case': 'warn',
      'obsidianmd/ui/sentence-case-json': 'warn',
      'obsidianmd/ui/sentence-case-locale-module': 'warn',

      // 模板代码清理
      'obsidianmd/no-sample-code': 'warn',
      'obsidianmd/sample-names': 'warn',

      // Suggest UI
      'obsidianmd/prefer-abstract-input-suggest': 'warn',

      // === 高频违规 — 先 warn，清理后升 error ===

      // 内联样式（345处）— 先警告
      'obsidianmd/no-static-styles-assignment': 'warn',

      // 验证
      'obsidianmd/validate-manifest': 'error',
      'obsidianmd/validate-license': 'warn',
    },
  },
  {
    // 忽略构建产物和 node_modules
    ignores: ['node_modules/**', 'main.js', '*.mjs', 'scripts/**', 'src/__tests__/**'],
  },
];
