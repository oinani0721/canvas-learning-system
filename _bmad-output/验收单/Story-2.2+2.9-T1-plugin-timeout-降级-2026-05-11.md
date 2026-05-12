---
story_id: "2.2+2.9"
task_id: "T1"
title: "Plugin Timeout + 错误降级"
ship_date: "2026-05-11"
status: "review"
phase: "B (功能可用)"
trace:
  - "Story-2.2+2.9 AC #2"
  - "Story 2.9 Task 6 (原)"
  - "ChatGPT Review 2026-05-11 P0-A 间接关联"
deploy:
  plugin_main_js: "canvas-vault/.obsidian/plugins/canvas-learning-system/main.js (147,159 bytes)"
  tests: "156/156 pass (含新增 8 chat-fallback tests)"
---

# Story 2.2+2.9 T1 — Plugin 超时降级验收单

## 1. 🎯 一句话目标（非技术）

当 Canvas 后端没启动、网络断了、或反应慢时，你按 Cmd+Shift+E 不再看到一个让人慌的红色错误，而是看到一个清楚的"backend 没连上，已经用本地数据降级"提示，对话照常能进行。

## 2. 📖 你的视角

**作为** 一个用 Canvas 学习的人,
**我想** 在 backend 偶尔出问题（机器刚开机、docker 没起、网络断、backend 卡了）时，Cmd+Shift+E 不要把我整个工作流卡住,
**以便** 我能继续聊节点、做笔记、推进学习，不被基础设施问题打断。

## 3. 🖥️ 交互流程（你的屏幕变化）

**正常路径**（backend 在跑，绝大多数情况）:
```
你做: 打开 节点/admissibility.md → 按 Cmd+Shift+E
↓
屏幕右上角弹: "已组装 backend RAG 上下文 5.2KB / 8 邻居 + 3 补充材料 ⭐ / 2100/4096 tokens（780ms）..."
↓
Claudian 侧栏打开 → 你 Cmd+V 粘贴 → 对话继续
```

**降级路径**（backend 没启 / 卡了 > 3 秒）:
```
你做: 打开 节点/admissibility.md → 按 Cmd+Shift+E
↓
等 3 秒（你能感觉到一个短暂的"嗯?"）
↓
屏幕右上角弹: "⚠️ backend 未连接，已降级到本地 1-hop（5 邻居 / 2.8KB / 3050ms）切到 Claudian 粘贴"
↓
Claudian 侧栏打开 → 你 Cmd+V 粘贴 → 对话继续（用本地邻居数据，质量稍逊但能用）
```

## 🤖 Claude 已代验（技术 assert，你不用管）

| Check | 命令 / 证据 | 结果 |
|---|---|---|
| Plugin 测试套件 | `npm test` (含 8 个新增 chat-fallback test) | ✅ 156/156 pass, 0 fail, 49ms |
| Build 产物 | `npm run build` → main.js | ✅ 147,159 bytes, 无 error |
| 部署 main.js | `cp main.js canvas-vault/.obsidian/plugins/canvas-learning-system/` | ✅ 文件已就位 (mtime 2026-05-11 20:33) |
| AbortController 集成 | code review main.ts:614-643 | ✅ controller + setTimeout(3000) + signal: controller.signal + clearTimeout |
| 降级路径 prompt 格式 | test "marker 是 HTML 注释格式" | ✅ `<!-- Degradations: ... -->` 是 Obsidian-safe（渲染时不可见） |
| 双 reason 区分 | test "backend_timeout vs backend_unreachable" | ✅ 两种 reason 产生不同 prompt，不会被吞 |
| 保留 skill 前缀 | test "保留 /chat-with-context skill 前缀" | ✅ 降级 prompt 仍以 `/chat-with-context` 开头（不混淆为 `/node-chat`）|
| 邻居 fallback | code review main.ts:fallbackToLocalNeighbors | ✅ 调用现有 `collectNodeNeighbors(activeFile.path, 5)` → 1-hop local |
| Notice 文案差异化 | code review main.ts:fallbackToLocalNeighbors | ✅ "backend 超时" vs "backend 未连接" 两种文案 |
| Claudian 切换保留 | code review main.ts:fallbackToLocalNeighbors | ✅ 降级路径仍触发 `claudian:open-view` |
| 剪贴板兜底 | code review showRetryNotice 调用 | ✅ 剪贴板失败时给 retry Notice，不静默 |

**Claude 模拟测试场景**（你不用做，仅记录）:
- 场景 A: backend docker 没启 → 期望 catch TypeError → fallbackToLocalNeighbors(reason="backend_unreachable") → Notice "⚠️ backend 未连接..."
- 场景 B: backend 卡了 > 3000ms → 期望 AbortError → fallbackToLocalNeighbors(reason="backend_timeout") → Notice "⚠️ backend 超时..."
- 场景 C: backend 正常 → 走主路径 → Notice "已组装 backend RAG 上下文..." (不变)

## 👤 你来验（产品体验，2-3 分钟，全在 Obsidian 里）

> 这一段全程在 Obsidian 主界面操作。
> Cmd+Shift+E 在日常使用中绝大多数走正常路径——只在偶尔出问题时
> 才会出现降级 Notice，你只需要"留意 Notice 颜色和措辞"即可。

### Step 1 — 正常路径不变（最重要的回归测试）

- [ ] 我做：在 Obsidian 里打开任意一个 `节点/<concept>.md` 节点页（比如 `节点/admissibility.md` 或你常用的任意节点）
- [ ] 我做：按 Cmd+Shift+E
- [ ] 我看到：右上角弹 Notice "已组装 backend RAG 上下文 X KB / N 邻居 ..."（**不是**黄色 ⚠️ 提示，**不是**红色 error 弹窗）
- [ ] 我感觉：和以前一样顺畅，没变慢、没怪提示——证明改动没把好东西改坏

### Step 2 — 切到 Claudian 验对话正常

- [ ] 我做：Step 1 之后切到 Claudian 侧栏，Cmd+V 粘贴
- [ ] 我看到：Claudian 输入框里出现的内容开头是 `/chat-with-context`，下面跟着节点正文 + 邻居 + 补充材料
- [ ] 我感觉：Claude 给我的回答有节点上下文，跟以前一致——主路径没坏

### Step 3 — 留意未来某天会见到的"降级 Notice"（被动观察）

> 这一步**不用主动做什么**。在以下场景"自然遇到"降级时，留意 Notice 颜色和措辞：
>   - 早上刚开 Obsidian、Canvas 后端还在启动中
>   - 突然断网、Wi-Fi 切换中
>   - 后端响应慢于 3 秒（罕见）

- [ ] 我看到（某天遇到时）：右上角弹**黄色** ⚠️ Notice "backend 未连接，已降级到本地 1-hop（N 邻居 / X KB / XXXX ms）"（**不是**红色 error 把整个工作流卡住）
- [ ] 我感觉：知道发生了什么、不慌；继续粘到 Claudian 后对话依然能进行，邻居更少但回答不会答非所问

### Step 4 — 等问题自己恢复（无需手动重启 Obsidian）

> 同样**不用主动做什么**。后端恢复在线后再按 Cmd+Shift+E 即可。

- [ ] 我看到（后端恢复后再按 Cmd+Shift+E 时）：Notice 又回到 "已组装 backend RAG 上下文..." 正常文案
- [ ] 我感觉：系统**自动恢复**，不用重启 Obsidian、不用重新加载插件

## 5. 🚦 验收结果

### 通过（全部勾完）
- [ ] Step 1 ✅
- [ ] Step 2 ✅ (或跳过)
- [ ] Step 3 ✅ (或跳过)
- [ ] Step 4 ✅ (或跳过)

通过 → 在文末写"通过，启 T2"

### 不通过
- 用 Cmd+Shift+A 在下面的批注区加 `[!error]+` callout 写发生了什么
- 我读批注后 correct-course 调整

## 6. 📝 批注区

### 用户批注（你写，用 Cmd+Shift+A）

> [!question]+ 我有一个问题
> （在这写）

> [!error]+ 我看到了 error
> （在这写）

> [!tip]+ 我建议
> （在这写）

### 已知的已批注问题（历史追溯）

无（T1 首次 ship）

## 7. 🔗 技术 spec 引用（给 Claude 读的，你不用看）

- **合并 Story spec**: `_bmad-output/implementation-artifacts/epic-2/2-2-and-2-9-merged-rerank-evidence.md` (T1 段)
- **修改源文件**:
  - `frontend/obsidian-plugin/src/main.ts` — handleChatWithContext 加 timeout (line 614-643) + fallbackToLocalNeighbors 新增 (line 967+)
  - `frontend/obsidian-plugin/src/node-chat-context.ts` — 新增 buildChatWithContextFallbackPrompt 纯函数 (line 310+) + 新增 type ChatFallbackReason
  - `frontend/obsidian-plugin/package.json` — test 命令加 chat-fallback.test.ts
- **新增测试**: `frontend/obsidian-plugin/tests/chat-fallback.test.ts` (8 tests)
- **部署位置**: `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` (147,159 bytes)
- **关键常量**: `CHAT_ENRICH_TIMEOUT_MS = 3000` (main.ts:78, study-question deep mode 走独立路径不受影响)
- **ChatGPT 审查响应**: `_bmad-output/chatgpt-review-response-2026-05-11.md`

---

**Ship 时间**: 2026-05-11 20:33
**下一步**: T1 通过 → 启 T2 (合并 Wikilink Service, 4h) → ship T2 验收单
