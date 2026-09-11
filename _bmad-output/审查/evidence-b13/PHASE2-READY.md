# PHASE2-READY：第十三批阶段 2 开工通告（2026-09-10）

> 队列 1~3 全部 squash 进候选树并 ff 主干后本文件生效。**生效候选树 sha = 主干 HEAD（见下）**。

## 阶段 2 开工：候选树 `<本文件提交时的主干 HEAD，见 git log>`

### U1（card-u1-pyright-svc）与 U2（card-u2-pyright-rest）都照此执行
1. `git merge --no-edit <主干 HEAD>`（主干 ff 后候选树 sha = 主干 HEAD；禁 rebase；冲突停下报主 session）。
2. 阶段 2 面不变：U1 清 10 个共享文件（60 条）；U2 清 `api/v1/endpoints/review.py`(7→现状以重测为准) 与 `api/v1/system.py`。
3. **D-29 已裁（手册 §四.5）：U2 额外带入 U1 分支的 `backend/app/services/exam_service.py` 单文件**（`git show card/u1-pyright-svc:backend/app/services/exam_service.py > backend/app/services/exam_service.py`）；带入后 U2 不再改它一个字，台账声明单文件 crossover；集成以 U1 版本为准（squash 零冲突）。
4. U1 基线（开工基准，⛔ 禁用「已清零」存档当基准）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b13/u1a-base/pyright-services-base-da690bf8.json`。
5. 判据不变：U1 阶段 2 末 `pyright app/services` = `0 errors`；U2 阶段 2 末非 services 面 = `0`（services 残余逐条交主 session 对账）；全量 `pyright app` = 0 是主 session 集成候选树的合入门（U1-A→U2-A squash 之后）。
6. 各自末轮 Codex 绑最终 HEAD BLOCKER/HIGH = 0（U2-A 已用 2/5 轮，剩 3 轮预算；超限停轮交主 session）。
7. 完成后各自 commit + 验收单 v2；主 session 随后 squash U1-A → U2-A → U2-B（GATE，全批最后）→ openapi 再生第二次。

### 批中已定事项（复核裁定书 `_bmad-output/审查/evidence-b13-integ/RULINGS-2026-09-10.md`）
- U6-C 已退回车道补审（snooze 时间炸弹裁判红 + 失绑），不随本波次；U8-C 未实施 → 第十四批。
- U3 `test_deploy_vault_sh.py` 在复核环境有挂起记录 → 候选树裁判观察项，复现 = 集成修复后合。
- flaky 两处（candidate_service / mock_degradation_transparency）按噪声登记。
