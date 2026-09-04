结论：**FAIL（0 BLOCKER / 1 HIGH / 2 MEDIUM / 2 LOW）**。126 项目标回归虽全绿，但核心排序指纹仍可被实际排序规则变更绕过。

## 发现

- [HIGH] [scripts/daily_review_pick.py:617](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/scripts/daily_review_pick.py:617)、[scripts/daily_review_pick.py:759](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/scripts/daily_review_pick.py:759)、[scripts/daily_review_pick.py:807](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/scripts/daily_review_pick.py:807) — “单源”只统一了因子名称顺序，没有统一可执行取值规则。SHA 摘要不包含取值来源、归一化精度和方向。固定输入下仅将 `priority_pick` 精度从 8 位改为 7 位，板序由 `['B板','A板']` 翻为 `['A板','B板']`，SHA 均为 `879279ff...bece`；交换 blr/min-last 的取值绑定也同样复现。以上均是排序规则变化，不是用户排除的普通数据变化。建议建立包含 name/source/default/transform/direction/params 的可执行因子描述符，并在单轮入口冻结同一 snapshot，同时供排序与 canonical SHA 使用；补近邻 pick 精度变异门。

- [MEDIUM] [scripts/daily_review_pick.py:568](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/scripts/daily_review_pick.py:568) — authoritative 缺失仍未完整闭合。实测 `{"version":1}`、`{"version":1,"authoritative":{}}`、`estimated_minutes:null` 均静默返回默认 `{3,5}`、保留 version=1，且 stderr 为空。当前只修了 estimated_minutes 已是 object 时的叶键缺失。建议区分父节缺失、子节缺失/null/错型，全部点名回落并补门。

- [MEDIUM] [test_daily_review_pick.py:1758](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/backend/tests/regression/test_daily_review_pick.py:1758) — pick 级新金样不承重：低 pick 恰好属于字典序更早的 A板。删除 `priority_pick` 后，默认与变异顺序仍都是 `['A板','B板']`。建议把低 pick 放在字典序更晚的板，并断言删除或后移首因子后顺序翻转。

- [LOW] [scripts/daily_review_pick.py:283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/scripts/daily_review_pick.py:283) — 因子键没有唯一性校验。追加重复的末级 `board` 后，排序语义对所有行不变，但 SHA 改变，构成“SHA 变而排序不变”。建议校验键已知且唯一、`board` 恰好一次并位于末级；或者把契约明确收窄为单向保证。

- [LOW] [UAT-CARD-G3-6b…md:199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md:199)、[同文件:212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md:212) — UAT 顶部已更新为 126，但两处仍写 121，证据内部不一致。建议统一为当前实测数。

## 已验证通过

- 未来推荐日：实得 `recommend_gap_days=-2`，文案为“晚于今天”，未伪装成今天。
- 原子渲染：why-only、minutes-only 均不显示解释行；双字段恢复显示。
- min-last fixture：默认 Z→Y，删除第三因子后 Y→Z，真实承重。
- 半份叶级分钟配置会点名 `per_new_node` 回落。
- 正常 tuple 下交换 blr/board，板序与 SHA 确实同变。
- 指定回归：**126 passed, 10 warnings**，pick 65 + overview 61。
- `HEAD=9af18b27`；tracked diff 仅四个允许文件，新 manifest 在允许范围；禁改文件零差异；`git diff --check` 通过。
- live 匿名聚合：14/14 条 `source_board` 均为单 wikilink，未发现多值、空值或其他形态。

限制：这是指定的 126 项目标套件，不是全量 CI；按卡文未运行 Bark runner。当前会话未暴露 Graphiti 查询接口。

**总裁决：FAIL。**


