# epic-3/ 实际归属说明

⛔ **本目录混合两套编号体系，共 6 个物理文件 + 12 个 sprint id 占位无物理 spec**。

---

## 双轨编号现状

### 1) sprint Epic 3 真实归属 (1 个 spec, 12 个未写)

sprint-status.yaml `epic-3:` (line 124-138) = "节点 AI 对话与交互, 13 stories"。

| sprint id | 物理 spec | 状态 |
|---|---|---|
| `3-1-claude-code-cli-per-node-session` | ✅ `3-1-claude-code-cli-per-node-session.md` | review (2026-05-02 ship) |
| `3-2-mcp-tool-exposure-backend-api` | ❌ 物理未写 | ready-for-dev (占位) |
| `3-3-chat-panel-ui-streaming` | ❌ 物理未写 | ready-for-dev (占位) |
| `3-4-learning-context-auto-injection` | ❌ 物理未写 | ready-for-dev (占位) |
| `3-5-skill-command-integration` | ❌ 物理未写 | ready-for-dev (占位) |
| `3-6-tips-annotation-error-archiving` | ❌ 物理未写 | ready-for-dev (占位) |
| `3-7-dialog-pullout-node` | ❌ 物理未写 | ready-for-dev (占位) |
| `3-8-dialog-archive-async-generation` | ❌ 物理未写 | ready-for-dev (占位) |
| `3-9-engine-fallback` | ❌ 物理未写 | ready-for-dev (占位) |
| `3-10-quota-management-degradation` | ❌ 物理未写 | ready-for-dev (占位) |
| `3-11-crash-recovery` | ❌ 物理未写 | ready-for-dev (占位) |
| `3-12-token-tracking-cost-statistics` | ❌ 物理未写 | ready-for-dev (占位) |
| `3-13-prompt-injection-output-safety` | ❌ 物理未写 | ready-for-dev (占位) |

**覆盖率**: 1/13 = 7.7% (只有 3-1 节点对话原型有 spec)

### 2) 历史遗留 epics.md 编号 KG 构建 spec (5 个待归档)

epics.md 真相源 Epic 3 = "知识图谱构建" (Graphify 流程)。这 5 个 spec 与 sprint Epic 3 完全无关:

```
3-1-concept-extraction-wikilink.md      ⚠️ 与 sprint 3-1 同名冲突 (文件层防覆盖看大小或 mtime)
3-2-graphify-relation-extraction.md
3-3-edge-relationship-files.md
3-4-bookmark-exam-extraction.md
3-5-kg-health-image.md
```

**建议**: 归档到 `_bmad-archive/epic-3-legacy-kg-build/` (单独保留 commit 历史可追溯)，或更名为 `kg-3-X-...md` 加 `kg-` 前缀消歧。

---

## 文件名冲突警告

`epic-3/3-1-*.md` 存在 **两个文件**：

```bash
$ ls epic-3/ | grep "^3-1"
3-1-claude-code-cli-per-node-session.md   # sprint Epic 3 真实 spec ✅
3-1-concept-extraction-wikilink.md        # 历史遗留 KG 构建 spec ⚠️
```

**dev-story Skill 解析 sprint id `3-1-claude-code-cli-per-node-session` 时**, 必须用**完整 kebab-name** 匹配，**不要**用 prefix `3-1-*` 模糊匹配（会撞 KG spec）。

---

## 修复历史

- **2026-05-13**: 工程治理 ship 此 README + sprint-status.yaml 头部警告
- **未来**: 12 个未写 spec 待 dev 启动时逐个新建（按 sprint id kebab-name 落盘）

## 协调员建议

- 启动任意 `3-2`~`3-13` Story 前，先**新建物理 spec**（用 BMAD `bmad-bmm-create-story` Skill）
- 5 个历史 KG 构建 spec 不参与 sprint Epic 3 的 dev-story 流程
- 优先归档 5 个旧 spec 避免冲突: `git mv epic-3/3-{2,3,4,5}-*.md _bmad-archive/epic-3-legacy-kg-build/` (需用户授权, 涉及 git 历史)
