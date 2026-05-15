---
story_id: "2.4"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 4
depends_on: ["2.1"]
blocks: []
trace:
  - "FR-CONV-05"
---

# Story 2.4: Callout 批注标记 Tips

Status: ready-for-dev

## Story

As a 学习者,
I want 在笔记中用 callout 批注标记关键知识点（Tips）,
So that 系统能识别我的 Tips 并在后续 AI 对话和考察中使用。

## Acceptance Criteria

1. **Given** 学习者在笔记中写入 `[!tip]+` callout 格式的批注
   **When** 笔记保存
   **Then** 系统解析 callout 内容并提取 tip 文本
   **And** tip 文本包含 callout 标题行和正文内容

2. **Given** Tips 已提取
   **When** 系统更新 frontmatter
   **Then** frontmatter 的 `tips[]` 数组新增条目，每条含 `text` / `added_at` / `source` 字段
   **And** 已存在的同文本 tip 不重复添加（幂等）
   **And** frontmatter 更新不破坏文件其他内容

3. **Given** 笔记中有多个 `[!tip]+` callout
   **When** 系统解析
   **Then** 所有 `[!tip]+` callout 均被识别和提取
   **And** `[!tip]-`（折叠状态）也被识别
   **And** 非 tip 类型的 callout（如 `[!warning]`、`[!note]`）不被提取

4. **Given** 学习者后续启动 AI 对话或考察
   **When** context_enrichment 组装上下文
   **Then** frontmatter 中的 `tips[]` 被注入 LLM 上下文（通过 Story 2.1 的上下文组装机制）
   **And** Tips 在上下文压缩中属于高优先级保留项（仅次于当前笔记全文）

5. **Given** 学习者删除笔记中的某个 `[!tip]+` callout
   **When** 笔记保存
   **Then** 对应 tip 从 frontmatter `tips[]` 中移除
   **And** 其他 tips 不受影响

## Tasks / Subtasks

- [ ] Task 1: Callout 解析器 (AC: #1, #3)
  - [ ] 1.1: 在 `backend/app/services/` 下创建 `callout_parser.py`
  - [ ] 1.2: 实现 `parse_tips(markdown_content: str) -> List[TipEntry]` 函数
  - [ ] 1.3: 使用正则匹配 Obsidian callout 语法：`> \[!tip\][+-]?\s*(.*)\n(> .*\n)*` 提取标题和正文
  - [ ] 1.4: 同时识别 `[!tip]+`（展开）和 `[!tip]-`（折叠）两种状态
  - [ ] 1.5: 忽略非 tip 类型 callout（`[!warning]` / `[!note]` / `[!fail]` 等）

- [ ] Task 2: Frontmatter tips[] 更新 (AC: #2, #5)
  - [ ] 2.1: 在 `callout_parser.py` 中实现 `sync_tips_to_frontmatter(file_path: str, parsed_tips: List[TipEntry]) -> bool`
  - [ ] 2.2: 读取现有 frontmatter，对比 parsed_tips 与已有 `tips[]`
  - [ ] 2.3: 新增不存在的 tip（`text` 匹配判断去重），设置 `added_at` 为当前时间，`source` 为 `callout_parse`
  - [ ] 2.4: 移除 frontmatter 中存在但 markdown 中已删除的 tip
  - [ ] 2.5: 使用原子写入（写临时文件 → rename）确保 frontmatter 安全（NFR 数据完整性：零损坏）

- [ ] Task 3: 文件保存事件监听 (AC: #1, #5)
  - [ ] 3.1: 在后端文件监听服务（`backend/app/services/` 中的 watcher 或 event_bus）中注册 `.md` 文件保存事件
  - [ ] 3.2: 文件保存时触发 `parse_tips` + `sync_tips_to_frontmatter` 流程
  - [ ] 3.3: 仅处理 `wiki/concepts/` 目录下的文件（排除 raw/ / outputs/ 等）
  - [ ] 3.4: 防抖处理：同一文件 500ms 内多次保存只触发一次解析

- [ ] Task 4: Tips 注入上下文验证 (AC: #4)
  - [ ] 4.1: 确认 Story 2.1 的 `ChatContextAssembler` 在读取 frontmatter 时包含 `tips[]` 字段
  - [ ] 4.2: 确认 Tips 在压缩优先级中属于高优先级（与 errors[] 同级，仅次于当前笔记全文）

- [ ] Task 5: 测试 (AC: #1~#5)
  - [ ] 5.1: 单元测试 `parse_tips`：单个 tip、多个 tip、折叠 tip、非 tip callout 过滤
  - [ ] 5.2: 单元测试 `sync_tips_to_frontmatter`：新增、去重、删除、幂等
  - [ ] 5.3: 集成测试：写入带 `[!tip]+` 的 .md 文件 → 验证 frontmatter 更新 → 启动对话 → 验证 tip 在 LLM 上下文中

## Dev Notes

- **Obsidian callout 语法**: `> [!tip]+ 标题` 表示展开状态，`> [!tip]- 标题` 表示折叠状态。正文在后续以 `> ` 开头的行中
- **Frontmatter tips[] schema**: 参考 Anchor PRD §3.2 (line 3380-3385)，格式为 `{text: str, added_at: datetime, source: str}`
- **已有代码**: `backend/app/services/error_classifier.py` 中已有类似的 frontmatter 读写模式可参考
- **原子写入**: 使用 `tempfile.NamedTemporaryFile` + `os.replace()` 模式确保不产生半截文件

### Project Structure Notes

```
backend/app/services/
  callout_parser.py               # 新增：callout 解析 + frontmatter 同步
backend/tests/unit/
  test_callout_parser.py          # 新增
```

### References

- Anchor PRD §3.2 frontmatter tips[] schema: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 3370-3395)
- Obsidian callout 文档: https://help.obsidian.md/callouts
- BMAD PRD FR-CONV-05: `_bmad-output/planning-artifacts/prd.md` (line 357)

## UAT Script

> 1. 打开 `wiki/concepts/admissibility.md`
> 2. 在笔记末尾添加一个 callout：`> [!tip]+ 关键：h(n) 必须小于等于真实代价`
> 3. 保存文件
> 4. 打开文件的 frontmatter（YAML 区域），验证 `tips:` 数组中新增了对应条目
> 5. 启动 AI 对话，验证 AI 的上下文中包含这条 tip
> 6. 删除该 callout 并保存，验证 frontmatter 中对应 tip 已移除

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| callout 解析 | unit | `pytest tests/unit/test_callout_parser.py -x` | 全部通过 |
| frontmatter 同步 | unit | `pytest tests/unit/test_callout_parser.py::test_sync_tips -x` | 增删幂等 |
| 非 tip 过滤 | unit | `pytest tests/unit/test_callout_parser.py::test_ignore_non_tip -x` | 不提取 warning/note |
| 端到端注入 | integration | `pytest tests/integration/test_tips_in_context.py -x` | LLM 上下文含 tip |

## User Feedback & Changes

### Feedback Log

(empty)

### Deviation Notes

(empty)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — 2026-05-14

### Implementation Path

**Plan A 实施** (4 路对抗审查共识后, 从 Plan B 回退):
- 1st attempt Plan B (plugin debounce + Graphiti append-only): 实施完发现 ChatGPT-2 找的 ghost field bug + 7 个盲点, 不满足 AC#5 删除追踪
- 2nd attempt Plan A (frontmatter 真相源): 完美对齐 spec + 5 AC 全通
- 决策文档: `_bmad-output/research/2026-05-14-plan-b-postmortem.md` (212 行)
- Plan B 代码保留 git history (commit 3d10a02) 作 Plan C 未来参考

### Architecture Highlights

1. **Plugin 端真相源**: `FrontmatterTipsSync` 监听 `metadataCache.on('changed')` 用 Obsidian 官方 `app.fileManager.processFrontMatter` API 原子写入
2. **完全覆盖语义**: `buildNewTips` 每次重写 tips[] 而非 append, 天然支持 AC#5 删除追踪
3. **防无限循环**: `tipsEqual` 比对新旧内容相同则跳过, 不重复 trigger metadataCache
4. **保留 added_at**: 旧 tip 匹配 (text+tag+understanding) 沿用 added_at, 新 tip 写当前时间
5. **严格协议**: regex `/^>\s*\[!(tips|error|question|keypoint)\][+-]\s*(.*)$/i` 双 telltale 排除模板 hint
6. **Backend 第 3 source**: `learning_context_service._fetch_tips_and_errors` 加 yaml.safe_load 路径读 .md frontmatter, 跟 MemoryService + LearningMemoryClient 三路 fallback

### Debug Log References

(to be filled by Dev agent)

### Completion Notes List

(to be filled by Dev agent)

### File List

**Plan A v3.0 新建 (1 个)**:
- `frontend/obsidian-plugin/src/frontmatter-tips-sync.ts` (115 行)

**Plan A v3.0 修改 (4 个)**:
- `frontend/obsidian-plugin/src/callout.ts` (parser 协议修复 + parseCalloutsFromContent + SHA256)
- `frontend/obsidian-plugin/src/main.ts` (集成 FrontmatterTipsSync + onload 注册 metadataCache.on('changed'))
- `backend/app/services/learning_context_service.py` (加第 3 source frontmatter reader, +51 行)
- `backend/app/api/v1/endpoints/tips.py` (/batch endpoint 加 410 deprecated marker)

**Plan A 验收单** (覆盖 v2.0 → v3.0):
- `_bmad-output/验收单/Story-P0-callout-backend-sync.md` (v3.0 含 v1→v3 历史追溯)

**Postmortem 决策文档**:
- `_bmad-output/research/2026-05-14-plan-b-postmortem.md` (212 行)

**Plan B 代码 (保留 git history 作 Plan C 参考)**:
- commit 3d10a02 含 backend/app/graphiti/group_id_compat.py 等 11 个文件
- 入口已 disable (saveCalloutToBackend 调用注释 + /tips/batch 返回 410 Gone)

### Change Log

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-05-14 早 | v1.0 (Plan B) | plugin debounce + Graphiti append-only, 实测端到端 8 sync + 3 EpisodicNode |
| 2026-05-14 中 | v2.0 (Plan B 升级) | 加 4 agent 对抗审查 + ChatGPT 第二意见 |
| 2026-05-14 晚 | v3.0 (Plan A) | 回退 Plan A frontmatter 真相源 + 5 AC 全通 |
| 2026-05-14 晚 | v3.1 (regex fix) | 严格协议 regex (4 复数 tag + 必带 +/-) 排除模板 hint 误识别 |
