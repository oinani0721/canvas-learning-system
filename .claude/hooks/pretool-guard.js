/**
 * PreToolUse Guard v2 — 确定性阻止违规代码编辑
 *
 * v2 新增：文件范围检查（DD-12）— agent_type 与 file_path 不匹配时阻止
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

    const filePath = (data.tool_input && data.tool_input.file_path) || '';
    const agentType = data.agent_type || '';

    // ===== DD-03: Mock 检测 =====
    const mockPatterns = /return\s*\[\s*\]|return\s*\{\s*\}|TODO.*implement|mock.*data|fake.*response|hardcoded.*return/i;
    if (mockPatterns.test(input)) {
      process.stderr.write('[DD-03] 检测到疑似 mock/模拟实现（return []、TODO implement等）。禁止写入假数据。请实现真实逻辑。');
      process.exit(2);
    }

    // ===== DD-13: 名实一致 — 函数名必须匹配实际行为 =====
    // Write: 检查 content（完整文件）
    // Edit: 读磁盘完整文件 + 合并 new_string 后检查（防止片段误判）
    if (filePath.endsWith('.py')) {
      let content = '';
      if (/^Write$/i.test(tool)) {
        content = (data.tool_input && data.tool_input.content) || '';
      } else if (/^Edit$/i.test(tool)) {
        try {
          const fs = require('fs');
          const diskContent = fs.readFileSync(filePath, 'utf-8');
          const newStr = (data.tool_input && data.tool_input.new_string) || '';
          const oldStr = (data.tool_input && data.tool_input.old_string) || '';
          content = oldStr ? diskContent.replace(oldStr, newStr) : diskContent + '\n' + newStr;
        } catch (_) { content = ''; }
      }
      if (content.length >= 20) {
        const libraryKeywords = {
          graphiti: ['graphiti_core', 'add_episode', 'search_memory', 'GraphitiBridge', 'graphiti_client'],
          fsrs: ['fsrs', 'FSRS', 'Card', 'Rating', 'review_card'],
          neo4j: ['neo4j', 'GraphDatabase', 'AsyncDriver', 'AsyncSession'],
          chromadb: ['chromadb', 'collection.add', 'collection.query'],
          openai: ['openai', 'OpenAI', 'ChatCompletion'],
          gemini: ['genai', 'GenerativeModel', 'gemini'],
          lancedb: ['lancedb', 'LanceDB', 'lance'],
        };
        const funcPattern = /(?:def|class)\s+(\w+)/g;
        let m;
        while ((m = funcPattern.exec(content)) !== null) {
          const fn = m[1].toLowerCase();
          for (const [kw, markers] of Object.entries(libraryKeywords)) {
            if (fn.includes(kw)) {
              const hasMarker = markers.some(mk => content.toLowerCase().includes(mk.toLowerCase()));
              const hasImport = new RegExp('(?:import|from)\\s+.*' + kw, 'i').test(content);
              if (!hasMarker && !hasImport) {
                process.stderr.write('[DD-13] 函数 "' + m[1] + '" 名称含 "' + kw + '" 但未 import/调用 ' + kw + '。重命名函数或实现真正的集成。');
                process.exit(2);
              }
            }
          }
        }
      }
    }

    // ===== DD-12: 文件范围检查 =====

    // frontend agent 只能改前端文件
    if (/frontend/i.test(agentType) && filePath) {
      const isFrontend = /frontend|obsidian-plugin|canvas-progress-tracker|src[\/\\](components|views|styles|ui)/i.test(filePath);
      const isConfig = /package\.json|tsconfig|eslint|styles\.css|\.svelte|\.tsx?$|\.css$/i.test(filePath);
      if (!isFrontend && !isConfig) {
        process.stderr.write('[DD-12] frontend agent 不能修改 ' + filePath + '。只允许改前端文件（frontend/、obsidian-plugin/、src/components/ 等）。');
        process.exit(2);
      }
    }

    // backend agent 只能改后端文件
    if (/backend/i.test(agentType) && filePath) {
      const isBackend = /backend|src[\/\\](agentic_rag|api|canvas|services|memory|verification|optimization|migration|command_handlers)/i.test(filePath);
      const isConfig = /requirements\.txt|pyproject\.toml|pytest\.ini|\.env/i.test(filePath);
      if (!isBackend && !isConfig) {
        process.stderr.write('[DD-12] backend agent 不能修改 ' + filePath + '。只允许改后端文件（backend/、src/agentic_rag/ 等）。');
        process.exit(2);
      }
    }

    process.exit(0);
  } catch (e) {
    process.exit(0); // 解析失败时放行
  }
});
