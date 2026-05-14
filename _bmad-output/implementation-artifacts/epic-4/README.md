# epic-4/ 实际内容说明

⛔ **本目录物理内容 = 11 个检验白板 spec** (= epics.md 真相源 Epic 4 "检验白板灵魂")。

**不是** sprint-status.yaml 名义上的 "Epic 4 Edge 连线对话与关系学习 (4 stories)"。

真正的 **sprint Epic 4 (Edge 对话, 4 stories)** 物理 spec 位于 `../epic-6/`（见 `../epic-6/README.md`）。

---

## 编号错位根因

| 编号体系 | Epic 4 含义 | 物理目录位置 |
|---|---|---|
| sprint-status.yaml (旧 Tauri sprint 计划) | Edge 对话, 4 stories | `../epic-6/` ⚠️ |
| epics.md (Obsidian 真相源, BMAD 重写 2026-04-12) | 检验白板灵魂, 11 stories | `epic-4/` ✅ 本目录 |

物理文件名采用 epics.md 编号 → 本目录 = 检验白板内容。

---

## 本目录文件清单 (11 个检验白板 spec)

```
4-1-exam-isolation-anti-nesting.md         (检验白板 Story 4.1 隔离 + 防嵌套)
4-2-weak-node-selection.md                 (Story 4.2 弱节点选择)
4-3-triple-fusion-question-gen.md          (Story 4.3 三路融合出题)
4-4-exam-mode-selection.md                 (Story 4.4 考试模式选择)
4-5-md-editor-answer-submit.md             (Story 4.5 MD editor 答题提交)
4-6-silent-scoring-autoscore.md            (Story 4.6 静默评分 autoscore)
4-7-progressive-hints-skip.md              (Story 4.7 渐进提示 skip)
4-8-bookmark-concept-extraction.md         (Story 4.8 bookmark 概念抽取)
4-9-calibration-vote-data-sync.md          (Story 4.9 校准投票数据同步)
4-10-exam-record-persistence.md            (Story 4.10 检验记录持久化)
4-11-irt-difficulty-callout-exam.md        (Story 4.11 IRT 难度 callout)
```

---

## sprint-status.yaml 跨引用

sprint-status.yaml `epic-6:` 段 (line 170-181) 列的 10 个 Story id (`6-1-exam-board-generation` 等) 是 sprint **语义命名**。
本目录 11 个物理文件使用 **PRD 章节命名**，无法逐一对应（sprint 10 ↔ 物理 11，story 划分不同）。

**dev-story Skill 解析提示**:
- sprint id `6-X-...` (检验白板) → 看本目录 `4-Y-*.md` 找对应行为
- 推荐 BMAD 协调员先读 `_bmad-output/planning-artifacts/epics.md` Epic 4 段获取真实 BDD/AC

---

## 修复历史

- **2026-05-13**: 工程治理 ship 此 README + sprint-status.yaml 头部警告（不重命名物理文件以保 git 历史）

## 协调员建议

- BMAD dev-story 跑 sprint Epic 6 (检验白板) Story 时, 物理 spec 路径 = `epic-4/4-X-*.md`
- 不要在本目录新增 "Edge 对话" 内容（用 ../epic-6/）
