# epic-6/ 实际内容说明

⛔ **本目录物理内容 = 3 个 Edge 对话 spec** (= epics.md 真相源 Epic 6 "Edge 对话与深度剖析")。

**不是** sprint-status.yaml 名义上的 "Epic 6 检验白板与递归考察 (10 stories)"。

真正的 **sprint Epic 6 (检验白板, 10 stories)** 物理 spec 位于 `../epic-4/` (11 stories, epics.md 真相源 Epic 4)。详见 `../epic-4/README.md`。

---

## 编号错位根因

| 编号体系 | Epic 6 含义 | 物理目录位置 |
|---|---|---|
| sprint-status.yaml (旧 Tauri sprint 计划) | 检验白板与递归考察, 10 stories | `../epic-4/` ⚠️ |
| epics.md (Obsidian 真相源, BMAD 重写 2026-04-12) | Edge 对话与深度剖析, 3 stories | `epic-6/` ✅ 本目录 |

物理文件名采用 epics.md 编号 → 本目录 = Edge 对话内容。

---

## 本目录文件清单 (3 个 Edge 对话 spec)

```
6-1-edge-discussion-trigger.md             (Edge 对话 Story 6.1 触发器)
6-2-ei-se-dual-strategy.md                 (Story 6.2 EI/SE 双策略)
6-3-semantic-label-storage.md              (Story 6.3 语义标签存储)
```

---

## sprint-status.yaml 跨引用

sprint-status.yaml `epic-4:` 段 (line 144-149) 列 4 个 Story id (`4-1-edge-dialog-trigger` 等) 是 sprint **语义命名**。
本目录 3 个物理文件使用 epics.md 编号 (sprint 4 ↔ 物理 3, 部分合并)。

**逻辑 Story 对应关系（推断）**:
- sprint `4-1-edge-dialog-trigger` ↔ 物理 `6-1-edge-discussion-trigger.md` ✅
- sprint `4-3-ei-se-dual-strategy` ↔ 物理 `6-2-ei-se-dual-strategy.md` ✅
- sprint `4-2-edge-dialog-agent-reasoning` + `4-4-edge-dialog-fallback` ↔ 缺独立物理 spec（实施时需融入 6-1/6-2 或新建）
- 物理 `6-3-semantic-label-storage.md` 为 backend 持久化层 spec, sprint id 未单列

---

## 修复历史

- **2026-05-13**: 工程治理 ship 此 README + sprint-status.yaml 头部警告

## 协调员建议

- BMAD dev-story 跑 sprint Epic 4 (Edge 对话) Story 时, 物理 spec 路径 = `epic-6/6-X-*.md`
- 不要在本目录新增 "检验白板" 内容（用 ../epic-4/）
- `4-2-edge-dialog-agent-reasoning` / `4-4-edge-dialog-fallback` 需要时再新建物理 spec
