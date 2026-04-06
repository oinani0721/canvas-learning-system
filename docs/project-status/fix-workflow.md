# Bug 修复工作流

> 每个新 session 修 bug 前先读这个文件。
> 批注追踪清单: `docs/project-status/annotation-tracker.md`

---

## 修复前 Checklist

- [ ] 读 `annotation-tracker.md` 选下一个 bug
- [ ] 判断复杂度：简单（1-2 文件）vs 复杂（多文件/不确定根因）
- [ ] 创建分支：`git checkout -b fix/FR-XXX-NN`

## 简单 Bug 流程

```
git checkout -b fix/FR-XXX-NN
  → 读相关代码确认根因
  → 修复
  → 在修复函数加注释 # @spec: domain-nnn
  → 测试：.venv/bin/pytest tests/ -x -q
  → git commit -m "fix(FR-XXX-NN): 描述 @spec: domain-nnn"
  → git checkout main && git merge fix/FR-XXX-NN
  → 更新 annotation-tracker.md 打 [x]
```

## 复杂 Bug 流程（OpenSpec 全流程）

```
git checkout -b fix/FR-XXX-NN

阶段 1 — 探索（不改代码）:
  /opsx:explore "分析 FR-XXX-NN 根因"
  → Claude 读代码、分析、报告根因
  → 你确认方向

阶段 2 — 提案:
  /opsx:propose "修复 FR-XXX-NN: [确认的根因和方案]"
  → 生成: openspec/changes/fix-xxx/
    ├── proposal.md  (修复方案)
    ├── design.md    (设计决策)
    ├── specs/       (验收标准 Given/When/Then)
    └── tasks.md     (拆分任务)
  → 你审查 proposal.md

阶段 3 — 实现:
  /opsx:apply
  → 按 tasks.md 逐步实现
  → 每个修复函数加 # @spec: domain-nnn
  → PostToolUse 自动跑 ruff format + pytest

阶段 4 — 归档:
  /opsx:archive
  → delta spec 同步到 openspec/specs/
  → git commit -m "fix(FR-XXX-NN): 描述 @spec: domain-nnn"
  → git checkout main && git merge fix/FR-XXX-NN
  → 更新 annotation-tracker.md 打 [x]
```

## Commit Message 格式

```
fix(FR-EXAM-01): 修复检验白板考察功能卡死 @spec: algo-scoring-001

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

**必须包含**: `FR-XXX-NN` 或 `@spec: domain-nnn`（lefthook 会检查）

## 分支命名

```
fix/FR-EXAM-01        # bug 修复
fix/FR-RET-09         # bug 修复
feat/new-feature      # 新功能（走 /opsx:propose）
```

## 三阶段合并顺序

Phase 1（基础，可并行）:
- fix/FR-EXAM-01 → exam_service.py
- fix/FR-RET-09 → rag_service.py
- fix/FR-MAST-01 → mastery_engine.py

Phase 2（构建，依赖 Phase 1）:
- fix/FR-EXAM-02 → 依赖 MAST-01
- fix/FR-RET-05 → 依赖 RET-09
- fix/FR-MAST-06 → 依赖 MAST-01

Phase 3（前端集成）:
- App.tsx 路由
- Store 同步
- UI 组件

## 硬性门槛（自动执行）

| 门槛 | 触发时机 | 效果 |
|------|---------|------|
| mock 阻断 (DD-03) | 编辑时 PreToolUse | exit 2 阻断 |
| 范围约束 (DD-12) | 编辑时 PreToolUse | exit 2 阻断 |
| 名实一致 (DD-13) | 编辑时 PreToolUse | exit 2 阻断 |
| ruff auto-format | 编辑后 PostToolUse | 自动格式化 |
| pytest | 编辑后 PostToolUse | 失败则 exit 1 |
| ruff lint + format check | git commit 时 | 拒绝不合格代码 |
| spec reference | git commit 时 | 拒绝无 @spec/FR- 的代码提交 |
| --no-verify 禁止 | Claude Code deny | 无法绕过 hooks |
| commitlint | git commit 时 | 必须 conventional commit |
| backup push | git commit 后 | 自动 push 到 backup 远程 |

## Spec↔Code 追踪

**写入时**: 修复代码加 `# @spec: domain-nnn` 注释
**提交时**: commit message 含 `@spec:` 或 `FR-` 引用
**验证时**: 定期跑 `npx @fission-ai/openspec trace`
**查询**: `git log --grep="FR-EXAM-01"` 找所有相关修复
