# Codex 对抗性审查 — CARD-DEBT-openapi-sync [BATCH-2026-09-01-第八批]

你是独立对抗审查者。车道工作树: <repo> (下称 LANE)。
完整卡文: <repo>/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W4-3.md (必读)。
验收单: LANE/_bmad-output/审查/CARD-DEBT-openapi-sync-验收单.md

## 审查对象（本卡全部改动面）

1. `scripts/spec-tools/check-openapi-drift.py` (新增) — OpenAPI 快照漂移门 + --write 重生成
2. `backend/scripts/openapi_drift_negative_control.py` (新增) — 负控 4 变异
3. `backend/tests/contract/test_openapi_snapshot_drift.py` (新增) — 进程内门测试
4. `.github/workflows/api-spec-sync.yml` (修改) — 路径修正 + 漂移门翻红 + 删 update-spec + 停 Dredd
5. `lefthook.yml` (修改) — spec-sync 段重写
6. `backend/openapi.json` (重生成, 只经 --write)

背景: 原 CI 三处检查仓库根 openapi.json(该文件全历史不存在)→恒走 else; update-spec job
`git push || true` 恒绿却从未推上; GitHub 24/24 runs failure(Dredd, 日志 410 不可证因);
lefthook spec-sync 裸 python + 2>/dev/null + 查错路径 = 死了 4 个月。

## 重点审（卡文点名的方向，逐条给结论）

A. **归一化是否把真实漂移也归掉了** — 五条规则(删 info 易变键/dict key 排序/required
   字符串数组 sorted/其余数组保序/标量 JSON 类型标签)逐一攻击。特别审:
   - required 集合语义 vs enum 有序语义的边界判定是否有第三种情况被漏掉;
   - int 与 float 归并为 number 是否吞了真实契约差异(bool 与数字已用类型标签分开);
   - DETAIL_LINE_CAP 截断是否会掩盖负控/CI 依赖的「点名」行。
B. **app.openapi() 是否跨机器确定** — operationId/路由注册顺序/schema 缓存。本机实测
   3 次连 key 序逐字节相同; CI 是 3.11 本机是 3.14, 跨版本未实测——这个证据缺口
   验收单已声明, 评估该声明是否充分、是否还有未声明的确定性风险。
C. **删除 update-spec 是否让快照更易再陈旧** — 现在保鲜靠 lefthook(改 API 即重生成
   并 stage, 失败出声 exit 1) + CI 漂移红门 + 批次收官主干重生成。逐个失效条件审:
   --no-verify 绕过 / lefthook 未 install / 无 pre-merge-commit hook(合并序协议兜底)。
D. **Dredd 停用依据是否充分** — 24/24 红 + 日志 410 不可证因 + schemathesis
   in-process(test_openapi_contract.py, from_asgi)覆盖面 vs Dredd HTTP 回放面。
   已登记独立候选卡。评估「停用而非修复」是否正确、注释交代是否充分。
E. **CI 改动是否引入新假门** — 新漂移门什么情况下红得不真实(CI 3.11 导出≠快照)?
   detect-breaking-changes 的 `git show origin/<base>:backend/openapi.json` fallback
   `{}` 是否又造出一个静默退化? contract-test if:false 后 summary 的 needs 行为。
F. **负控与门测试的假绿** — 4 变异是否真的承重(改了会红、不改不红)? 前置门
   (正本无漂移检查)设计是否合理? 已实证: bool→int 真漂移曾被吞、已修(类型标签),
   审修复是否有残留同类问题。
G. **禁改边界** — backend/app/** 零改动、exam_service/verification_service、
   test.yml/plugin-ci.yml/readme-claims.yml/release-evidence.yml、
   test_openapi_contract.py、.gitignore 是否被本卡碰到(git 核对)。
H. **验收单诚实性** — 「待你裁决」三项(update-spec 删除/Dredd 停用/lefthook 出声化)
   是否以「建议默认、待裁决」措辞呈现; 「未经 GitHub 实跑验证」缺口是否显著;
   每道门的「不证明什么」是否如实。

## 纪律

- 只读审查: 不改任何文件。所有断言给 file:line 或可复现命令。
- LANE/backend/.venv/bin/python 可用于复现(只读命令; 禁连 7691; 禁跑 TestClient)。
- 严重度: BLOCKER(功能假门/契约错误/越界改动) / HIGH(证据缺口或假绿路径) /
  MEDIUM(健壮性) / LOW(措辞)。
- 末行必须给: `BLOCKER/HIGH 清零: 是|否`。
