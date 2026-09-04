# 对抗性审查请求: CARD-G3-6b 板级 why_this_board 与系数版本化 [BATCH-2026-09-01-第八批]

你是独立对抗审查方。车道 (git worktree, 分支 card/w6-whyboard):
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard
下称 LANE。基线 commit = 9af18b27 (主干 HEAD, 分叉点)。

## 必读 (按序)

1. 卡文 (规格真源, 一切以它为准):
   /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W6.md
2. LANE/scripts/daily_review_pick.py — 模块 docstring 的 S4/S5/S6 书面裁定段
   (本卡规格; 审查按它判), 及全部 diff。
3. LANE/scripts/review_rank_manifest.json (新文件)。
4. LANE/backend/app/api/v1/endpoints/review_overview.py — _summarize 的
   top_boards 门禁段 / board_rows 构造 / _board_table_html 渲染段。
5. LANE/backend/tests/regression/test_daily_review_pick.py 的 CARD-G3-6b 段。
6. LANE/backend/tests/unit/test_review_overview.py 的 CARD-G3-6b 段。

改动范围 (工作区 vs 9af18b27): 上述 4 个文件 + 新 manifest, 应无其他。
用 `git -C LANE diff 9af18b27 -- <path>` 看 diff。

## 审查重点 (卡文指定, 逐项给结论)

A. why_this_board 是否真由投影内因子复算 — 非 LLM、非 UI 再算:
   - why_this_board(factors) 是否纯函数; 落盘 factors 代回能否逐字复现落盘句子。
   - factors 是否全部是投影内已有数据的确定性派生, 有无虚构/估算/第二口径
     (对照 boards rollup 的 due 三分与 due_nodes 行既有字段)。
   - 渲染层 review_overview 是否零计算 (只 escape + 拼接)。
B. 系数是否全部进 manifest:
   - sha256 摘的是「运行时生效值」而非 manifest 文件字节 — 验证这一声明的
     真伪 (若实现只是对文件取 hash, 这是 BLOCKER)。
   - decay 六常量 / 因子序 / 上限 / 分钟常量, 任何一处改动是否必然改 sha。
   - authoritative vs recorded 的边界是否名实一致 (改 recorded 不得改变行为)。
C. 加性纯度与排序金样锁:
   - schema_version 仍 3; 既有键 byte 级不动 (两个累积冻结金样是否真在守)。
   - top_boards 排序与基线逐字相同的门是否真能抓改序 (fixture 的 tie-break
     覆盖是否足够)。
   - runner 消费面 (daily_review_run.py:159-165 等) 零变化。
D. 裁定完整性: S6 五条 (无归属/一节点多板/同名板/上限/去重) 是否各有独立
   测试; 多板裁定的实测声明是否与 _fm_str/_board_name 实际行为一致
   (可自行构造节点验证 YAML 数组 vs 逗号串两种写法)。

## 已知边界 (如实声明, 不算缺陷)

- decay_beta.py 本体禁改 (归 CARD-G6-1b); daily_review_run.py / send_bark.py
  / fsrs_bridge.py / router.py / .gitignore 禁改 — 禁改门已验。
- scripts/daily_review_pick.py 的 ruff 格式漂移是存量 (HEAD --check 即红),
  按 G3-6a 先例不动。
- estimated_minutes 常量 (3/5 分钟) 是拍脑袋值, 卡文明示待用户改 — 非缺陷。
- truncated 只透出布尔, 不解截断 (裁决⑤: 上限只登记不截断改)。

## 输出格式

对每条发现: [BLOCKER|HIGH|MEDIUM|LOW] + 文件:行号 + 问题 + 建议修法。
末尾给总裁决: PASS / FAIL (存在任一 BLOCKER 或 HIGH 即 FAIL)。
没有发现也要明说哪几项查了什么、为什么干净。不要复述代码, 给判断。
