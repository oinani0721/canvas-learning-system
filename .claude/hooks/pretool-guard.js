/**
 * PreToolUse Guard — 确定性阻止违规代码编辑
 *
 * Exit code 2 = 阻止操作（Claude 必须调整后重试）
 * Exit code 0 = 允许操作
 */
const chunks = [];
process.stdin.on('data', (chunk) => chunks.push(chunk));
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(Buffer.concat(chunks).toString());
    const tool = data.tool_name || '';
    const input = JSON.stringify(data.tool_input || {});

    // 只检查 Edit/Write 工具
    if (!/^(Edit|Write)$/i.test(tool)) { process.exit(0); }

    // 检查是否在写 mock/模拟实现
    const mockPatterns = /return\s*\[\s*\]|return\s*\{\s*\}|TODO.*implement|mock.*data|fake.*response|hardcoded.*return/i;
    if (mockPatterns.test(input)) {
      process.stderr.write('[DD-03] 检测到疑似 mock/模拟实现（return []、TODO implement等）。禁止写入假数据。请实现真实逻辑。');
      process.exit(2);
    }

    process.exit(0);
  } catch (e) {
    process.exit(0); // 解析失败时放行
  }
});
