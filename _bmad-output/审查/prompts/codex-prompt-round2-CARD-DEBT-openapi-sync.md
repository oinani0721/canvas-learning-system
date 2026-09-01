# Codex 对抗性审查 Round-2 — CARD-DEBT-openapi-sync 整改验证 [BATCH-2026-09-01-第八批]

你是独立对抗审查者, 本轮**只做一件事**: 验证 Round-1 的 4 BLOCKER + 2 HIGH 是否被
真实修复, 以及修复是否引入新缺陷。车道: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro
Round-1 报告: _bmad-output/审查/codex-review-CARD-DEBT-openapi-sync.md
整改 commit: 6c81ebc9 (`git show 6c81ebc9` 看全 diff; 基线 2fb779b3)

## 逐项验证清单(每项给 PASS/FAIL + 你实际跑的证据)

1. **B1 required 宿主守卫**: scripts/spec-tools/check-openapi-drift.py 的 _normalize
   现要求宿主 dict 含 properties/type 才排序 required。复验:
   a) enum 内嵌 required 反例必须报漂移(你可重跑构造反例);
   b) 守卫不回归: 正常 schema required 顺序仍被吸收;
   c) 宿主守卫前提 281/281 是我在当前快照实测的 —— 请独立重测这个数字。
2. **B2 CI 环境**: api-spec-sync.yml 的 export 与 drift gate 步骤是否都注入了
   DEBUG/CORS_ORIGINS/INTERNAL_API_KEY, 配方是否与 test.yml:119-121 语义一致;
   用同样的 env -i 复现法验证配方是否足以让 import app.config 成功。
3. **B3 触发面**: workflow paths(PR+push)与 lefthook 三命令的并集是否覆盖
   main.py/config.py/mcp/**/api/models/schemas; lefthook glob 引擎边界(数组失效/
   ** 需跨一级/花括号备选须真实路径)的三个实测结论是否与你对本机 lefthook 的
   理解一致; 三命令并行命中同一 commit 时 --write 的 tmp+rename 原子写是否
   足以消除交错损坏。
4. **B4 fail-closed**: 基线 git show 失败现在是否让 job 红(无 {} 降级); oasdiff
   解析失败是否让步骤红; summary 对 skipped/failure 是否不再显示绿色 None。
5. **H5/H6 声明**: 验收单 §三.2(依赖未锁)与 §三.3(schemathesis 未接 CI 白名单)
   的表述是否与事实相符; workflow 注释里是否还有夸大。
6. **新缺陷扫描**: 整改 diff 里有没有引入新的假门/吞漂移/越界(禁改面与 2fb779b3
   相同: backend/app/**、test.yml、plugin-ci.yml、readme-claims.yml、
   release-evidence.yml、test_openapi_contract.py、.gitignore、requirements.txt)。

## 纪律

- 只读。LANE/backend/.venv/bin/python 可复现(禁连 7691/7687, 禁 TestClient)。
- 每条结论给 file:line 或命令输出。MEDIUM/LOW 直接列出不必续轮。
- 末行必须给: `BLOCKER/HIGH 清零: 是|否`。
