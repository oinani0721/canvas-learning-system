/**
 * DD-03 Hard Hook: Production Code Import Guard
 *
 * Blocks unittest.mock imports in PRODUCTION code (backend/app/).
 * Test files (backend/tests/) are free to use mocking libraries.
 *
 * This is the deterministic enforcement of DD-03.
 * The existing pretool-guard.js catches "return []" patterns;
 * this hook catches the root cause: test library imports in production code.
 *
 * Exit code 2 = block operation
 * Exit code 0 = allow
 */
const chunks = [];
process.stdin.on('data', (chunk) => chunks.push(chunk));
process.stdin.on('end', () => {
  try {
    const input = JSON.parse(Buffer.concat(chunks).toString());
    const tool = input.tool_name || '';

    if (!/^(Edit|Write)$/i.test(tool)) { process.exit(0); }

    const filePath = (input.tool_input && input.tool_input.file_path) || '';

    // Only check production Python files (backend/app/)
    const isProductionPy = /backend[/\]app[/\].*\.py$/i.test(filePath);
    if (!isProductionPy) { process.exit(0); }

    // Get the content being written
    let content = '';
    if (/^Write$/i.test(tool)) {
      content = (input.tool_input && input.tool_input.content) || '';
    } else if (/^Edit$/i.test(tool)) {
      content = (input.tool_input && input.tool_input.new_string) || '';
    }

    if (!content) { process.exit(0); }

    // Detect test library imports and usage in production code
    const forbidden = [
      /from\s+unittest\.mock\s+import/,
      /from\s+unittest\s+import\s+mock/,
      /import\s+unittest\.mock/,
      /\bMagicMock\s*\(/,
      /\bAsyncMock\s*\(/,
      /\bpatch\s*\(/,
      /\b@patch\b/,
    ];

    for (const pattern of forbidden) {
      if (pattern.test(content)) {
        process.stderr.write(
          '[DD-03] Production code (' + filePath + ') contains test library imports. ' +
          'These belong in tests/ only. Use dependency injection to provide real implementations. ' +
          'Matched: ' + pattern.source
        );
        process.exit(2);
      }
    }

    process.exit(0);
  } catch (e) {
    process.exit(0);
  }
});
