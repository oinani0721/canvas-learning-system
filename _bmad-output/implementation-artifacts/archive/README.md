# archive/ — 归档旧 spec（只读参考，不在 live 开发队列）

> **2026-05-26 ChatGPT 体系审查后建立** — BMAD spec 体系健康度 4.5/10，64 个 ready-for-dev 假繁荣。
> 本目录存放已 supersede / deprecated / merge / 与单人 Obsidian Hybrid 主线脱节的旧 spec。
> **文件保留不删除**（git 历史可追），但 status 视为 archived，不再冒充 ready-for-dev。

## 归档清单（17 个）

### 13 高确定性归档（spec 内已写 supersede/deprecated 或 sprint-status 明确砍）

| 文件 | 原 epic | 归档原因 |
|---|---|---|
| `epic-2__2-2-supplementary-material-search.md` | Epic 2 | 已被 merged rerank-evidence 路线替代（status: superseded） |
| `epic-2__2-9-rag-rerank-and-evidence.md` | Epic 2 | 已被 merged rerank-evidence 路线替代（status: superseded） |
| `epic-4__4-3-triple-fusion-question-gen.md` | Epic 4 | 已被 `LITE-4-3` supersede |
| `epic-4__4-9-calibration-vote-data-sync.md` | Epic 4 | 已并入 `LITE-5-6` |
| `epic-5__5-6-calibration-data-voting.md` | Epic 5 | spec 内已写 deprecated，`LITE-5-6` 替代 |
| `epic-5__5-7-three-layer-memory-retrieval.md` | Epic 5 | spec 内已写 deprecated，`LITE-5-7` 替代 |
| `epic-5__5-8-async-write-hot-warm-cold.md` | Epic 5 | sprint-status 明确砍（单人 <10MB，过早优化） |
| `epic-6__6-1-edge-discussion-trigger.md` | Epic 6 | 旧 Edge 讨论套件 LMS 大叙事，单人模式价值低（Edge 对话已由 ai-linked-doc.ts 实现，见 epic-6-edge-revival 计划） |
| `epic-6__6-2-ei-se-dual-strategy.md` | Epic 6 | 同上 |
| `epic-6__6-3-semantic-label-storage.md` | Epic 6 | 同上 |
| `epic-8__8-3-metacognition-calibration-matrix.md` | Epic 8 | sprint-status 明确砍元认知 2x2 矩阵（400+ 题后回头） |
| `epic-8__8-7-audit-log.md` | Epic 8 | sprint-status 明确砍操作审计日志（平台运维） |
| `epic-9__9-1-image-exam-material.md` | Epic 9 | sprint-status 明确砍多模态考察（scope 扩展） |

### 4 候选归档（3 个 infra 已 done + 1 多模态前置）

| 文件 | 原 epic | 归档原因 |
|---|---|---|
| `epic-1__1-10-health-endpoint-unification.md` | Epic 1 | ⚠️ **已 done**（commit 4e0c27b），平台 health infra，归档非因废弃而因不在当前 dev 队列（只读参考实现） |
| `epic-1__1-12-mcp-infra-tools-deployment-tier.md` | Epic 1 | ⚠️ **已 done**（commit 4e0c27b），MCP/deployment tier 运维，同上 |
| `epic-1__1-13-deployment-checklist-external-net.md` | Epic 1 | ⚠️ **已 done**（commit 4e0c27b），外网部署检查清单，同上 |
| `epic-9__9-2-phase3-enhancements.md` | Epic 9 | 多模态 Phase 3 增强，全体往后排（未开发） |

> **状态漂移警告**: 1-10/1-12/1-13 在 sprint-status.yaml 是 `done`（commit 4e0c27b），但 ChatGPT 体系审查凭 bundle 把它们当"ready-for-dev 待砍"。这是又一处 **spec 文件 status ≠ sprint-status** 漂移。归档它们是对的（运维 spec 不在 live 主干），但归档原因是"已完成 + 不在当前 dev 队列"，不是"废弃未做"。

## ⚠️ ChatGPT 误判修正

- **1-4-hotkey-binding-config.md 未归档**：ChatGPT 报告凭 bundle 推测它是"Excalidraw/Canvas 方向性遗留"，但实证文件名是 hotkey 绑定配置 — 是 Obsidian Hybrid 4 MVP 核心 onboarding（所有 hotkey 都需要它）。**保留在 epic-1/ live**。
  - 教训：ChatGPT 只看 bundle 内 102 文件，1-4 内容没打包进去，凭 spec ID 猜测出错。Claude 有 codebase 全访问，实证发现矛盾 → 不盲从。

## 如何恢复归档 spec

如果未来需要重新激活某个归档 spec（如 Sprint 5+ 做多模态）：

```bash
git mv _bmad-output/implementation-artifacts/archive/epic-9__9-1-image-exam-material.md \
       _bmad-output/implementation-artifacts/epic-9/9-1-image-exam-material.md
# 改 frontmatter status: archived → ready-for-dev
# sprint-status.yaml 加回 entry
```

## 决策追溯

- ChatGPT 体系审查报告: `_bmad-output/审查/2026-05-26-chatgpt-bmad-体系审查-报告.md` Part 3
- 体系决策固化: `_bmad-output/审查/2026-05-26-bmad-spec-体系全图诊断.md`
- Plan ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17
