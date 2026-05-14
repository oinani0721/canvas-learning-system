# epic-5/ sprint-id vs 物理文件名 alias 表

⛔ **本目录 Epic 5 spec 命名 8/8 与 sprint-status.yaml id 完全错配**。
sprint-status 用**语义命名**（描述 UX 体验），物理目录用 **PRD 章节命名**（描述算法层）。

---

## 错位原因

- sprint id 由 SM 起草，强调用户视角行为（"dashboard"/"panel"/"tracking"）
- 物理 spec 文件名由 BMAD 实施时按 PRD 章节命名（PRD `FR-MAST-XX` "bkt-mastery-update" / "fsrs-review-interval" 等）
- 双方未同步 → 8/8 全错配

---

## sprint-id ↔ 物理文件 alias 表

| sprint-status id | 物理文件名 | Story ID | 真实内容（按物理 spec）|
|---|---|---|---|
| `5-1-bkt-fsrs-mastery-system` | `5-1-bkt-mastery-update.md` | 5.1 | BKT 掌握概率更新算法 |
| `5-2-node-color-mastery-visualization` | `5-2-fsrs-review-interval.md` | 5.2 | FSRS 复习间隔计算 |
| `5-3-learning-profile-panel` | `5-3-five-signal-fusion.md` | 5.3 | 5 信号融合（accuracy/calibration/scoring chain/error rate/recency）|
| `5-4-fsrs-review-dashboard` | `5-4-scoring-chain-integrity.md` | 5.4 | 评分链完整性 (可验真) |
| `5-5-calibration-tracking` | `5-5-error-classification-dual-write.md` | 5.5 | 错误 4 类分类双写 (Hot/Warm/Cold) |
| `5-6-multi-signal-fusion` | `5-6-calibration-data-voting.md` | 5.6 | 校准数据投票合并 |
| `5-7-eventbus-triconnect` | `5-7-three-layer-memory-retrieval.md` | 5.7 | 3 层记忆检索 (Hot/Warm/Cold) |
| `5-8-structured-extraction-manual-review` | `5-8-async-write-hot-warm-cold.md` | 5.8 | 异步写入 Hot/Warm/Cold |

---

## 语义层对应（用户视角 vs 物理实现层）

- **sprint Epic 5 (语义)**: 精通度追踪 + 学习档案 + Dashboard (用户能看见的 UI 表现)
- **物理 Epic 5 (实现)**: BKT/FSRS 算法 + 5 信号融合 + 错误分类 + 3 层记忆 (backend 算法栈)

两者是同一 Epic 的不同视角：
- sprint id 偏 "用户看到了什么"
- 物理 spec 偏 "backend 算出了什么"

dev 完成 = sprint id (UX 行为) 全部满足 AND 物理 spec (算法层) 全部 done。

---

## sprint-status.yaml 跨引用

sprint-status `epic-5:` 段 line 155-164 全 ready-for-dev (零 Story 启动)。
启动任意 Story dev 时, 协调员需:
1. 读 sprint-status 拿 sprint id (UX 期望)
2. 来本 README 查 alias 表找物理文件
3. 在物理文件读 AC + Tasks 实施

---

## 修复历史

- **2026-05-13**: 工程治理 ship 此 README + sprint-status.yaml 头部警告（不重命名物理文件以保 git 历史）

## 协调员建议

- 启动 `5-1-bkt-fsrs-mastery-system` dev → 读 `5-1-bkt-mastery-update.md` + `5-2-fsrs-review-interval.md` (BKT + FSRS 是同一 sprint Story 的两个物理子件)
- 启动 `5-2-node-color-mastery-visualization` dev → 物理 spec **不存在** (UI 层 Story, 需新建)
- 启动 `5-3-learning-profile-panel` dev → 读 `5-3-five-signal-fusion.md` (信号融合) + UI 层 spec 新建
- 启动 `5-4-fsrs-review-dashboard` dev → 读 `5-4-scoring-chain-integrity.md` (评分链) + Dashboard UI 层 spec 新建
- 启动 `5-5-calibration-tracking` dev → 读 `5-6-calibration-data-voting.md`
- 启动 `5-6-multi-signal-fusion` dev → 读 `5-3-five-signal-fusion.md` (与 5-3 共享 spec)
- 启动 `5-7-eventbus-triconnect` dev → 物理 spec **不存在** (基础设施 Story, 需新建)
- 启动 `5-8-structured-extraction-manual-review` dev → 读 `5-7-three-layer-memory-retrieval.md` + `5-8-async-write-hot-warm-cold.md`

⚠️ 物理 spec 完全覆盖率 = ~50% (4 物理文件直接命中 sprint id 5-1/5-5/5-6/5-8; 5-2/5-7 需新建)
