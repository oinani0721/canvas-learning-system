/**
 * PreToolUse Guard v3 — DD-03 only
 *
 * v3: Removed DD-12 (file scope) and DD-13 (name-body coherence).
 * Only keeps DD-03: blocks lazy stub patterns in code edits.
 *
 * Exit code 2 = block operation
 * Exit code 0 = allow
 */
const chunks = [];
process.stdin.on('data', (chunk) => chunks.push(chunk));
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(Buffer.concat(chunks).toString());
    const tool = data.tool_name || '';
    const input = JSON.stringify(data.tool_input || {});

    if (!/^(Edit|Write)$/i.test(tool)) { process.exit(0); }

    // Anchor document protection: PRD v5 is read-only for Claude
    const filePath = (data.tool_input || {}).file_path || '';
    if (filePath.includes('14-scheme-a-implementation-prd.md')) {
      process.stderr.write('[ANCHOR] 此文件是锚定文档（PRD v5），只能由用户手动编辑。Claude 只可 READ。');
      process.exit(2);
    }

    // DD-03: block lazy stub patterns
    if (/TODO.*implement|fake.*response|hardcoded.*return/i.test(input)) {
      process.stderr.write('[DD-03] Detected stub pattern (TODO implement / fake response / hardcoded return). Write real logic.');
      process.exit(2);
    }

    process.exit(0);
  } catch (e) {
    process.exit(0);
  }
});
