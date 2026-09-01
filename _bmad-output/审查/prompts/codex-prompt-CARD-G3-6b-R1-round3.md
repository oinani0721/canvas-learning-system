# 复核轮 R1 round-3（终轮）: CARD-G3-6b-R1 [BATCH-2026-09-01-第九批]

你是独立对抗审查方。本轮是 R1 的**第 3 轮，也是卡文预算的最后一轮**。

- 车道: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard
- **待审最终 commit: `ae7f67a4288729ad1bed2c611e2c0a7f364aacb9`**（分支 card/w6-whyboard，worktree clean）
- 你的前两轮报告: `_bmad-output/审查/codex-review-CARD-G3-6b-R1.md`（round-1，FAIL 1H/3M/2L）、
  `codex-review-CARD-G3-6b-R1-round2.md`（round-2，FAIL 0B/**0H**/5M/3L）
- 卡文: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第九批-goals/W6.md
- 验收单: `_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md`

## 本轮范围（同前两轮）

卡文 §4(c)：`.pyc` / `__pycache__` 与运行时篡改**排除在威胁模型外**，本卡不宣称
运行时完整性。**请不要构造 `.pyc` 篡改、mtime 伪造或运行时字节码替换的验证代码。**
你 round-1/2 对该边界措辞提的 LOW 均已采纳。

## round-2 → round-3 逐条整改（请验真伪）

- **[M1] 探针没绑「实际分钟」与「同组分钟的最终 rank SHA」** → 新增断言：独立复算
  「用 11/13 的 `effective_rank_config`」的 sha，要求 **(a) 等于** payload 落盘的
  rank sha、**(b) 不等于** 用 `DEFAULT_MINUTES` 复算的 sha。
  **你的那个单变异（摘要喂默认分钟、实际用 11/13）已加入负控**，现判 CAUGHT。
- **[M2] 「recorded 以实际为准」只查中间对象** → 新增断言：**仅 `recorded` 不同**的
  两份 manifest 各走一次**四板生产入口** `build_payload`，要求整份 payload 逐字相同、
  `len(top_boards)` 精确为 3、ranked 总数为 4。**你的 recorded-控制-截断变异已加入负控**。
- **[M3] 负控自己是假的（任意非零退出都算被抓）** → 改三态 `CAUGHT/MISSED/INVALID`：
  必须 (a) 探针跑完有 `复核结果:` summary、(b) stderr 无 `Traceback`、(c) **指定的
  那条**断言出现在 `[FAIL]` 行（按关键词精确匹配）。**加了验伪锚**：空源码必须判
  `INVALID`，若判 CAUGHT 则负控本身失效。结论收窄为「**这 6 种已知破坏**被抓」，
  并在输出末尾显式打印「未枚举形态仍可能漏网」。
- **[M4] 收窄没做全** → `TIE_FACTOR_KEYS` 注释、`TIE_PICK_ROUND_DIGITS` 注释、
  `test_g36b_tie_keys_are_single_source` docstring 三处改为单向表述（「改它必变 sha；
  **排序变不变取决于数据**」）；`effective_rank_config` 里「三条声明」改「四条」。
  **卡文 §5-2 的冲突未自行改卡文**（它是只读权威），改为**待裁决 ⑨** 交给卡文 owner：
  A) 把裁判限定为「本文件字节或明列生效值」/ B) 显式 waiver。
- **[M5] sha 归因混杂** → 改为 **commit / pick.py sha / rank sha 三元组表**，逐跳写明
  原因，并加归因纪律（`pick.py` 任何字节改动都换 sha；读旧证据先看其头部记的源码 sha）。
  已更正「新断言纳入」这个错误归因（新断言在测试文件，不进实现摘要）。
- **[L1] clean clone 阶段 0 rc=4 依赖未跟踪 `.env`** → 脚本头部**显式声明**该环境依赖
  与 clean clone 下的表现；**红时也归档 pytest tail**；删掉「rc=1 是唯一能证明断言
  失败的退出码」的过强措辞。
- **[L2] 「launchd 无自然触发路径」仍残留一处** → 已收回；并把「grep 要按语义找、
  不能只 grep 自己写过的那句」记在该处。
- **[L3] W4 锚点漂移** → 已刷新为实测 `d3fba4e0`（比你报的 `6518e5af` 还新）；
  runner 门**结论不变**（仍 BLOCKED），但理由改为「W4 未清零 + 集成树不存在」。

## 本轮复跑数据（请独立复核）

- 裁判 1：`130 passed`（pick 69 + overview 61）。
- 探针：A（`c2d2e590` 原样字节 `ad1a38a5…`）**22/22**；B（当前字节 `1f5eb882…`）**22/22**。
- 负控：**6 种已知破坏**各被其指定断言抓住；**验伪锚生效**（空源码判 INVALID）。
- 变异：**8/8** 各杀其指定门（全 `rc=1`，精确 nodeid，红时归档 tail），还原逐字节一致。
- live 只读探针：前后 sha 逐字相同零写入，rank sha `bc3aa142…`。
- **(e) runner 门仍 BLOCKED**（`batch9/integration` 分支与 `batch9-integration` worktree 均不存在）。

## 请重点审查

1. M1/M2 的新断言是否真的关闭了你构造的那两个假绿；能否再构造**别的**单变异，
   让 22 项探针 + 130 项测试同时全绿而生产入口行为已错。
2. M3 的三态判定与验伪锚是否真的成立；负控的结论收窄是否够诚实。
3. M4 收窄是否**这次做全了**（源码、测试、验收单全文还有无过宽表述）；
   把卡文冲突转为待裁决项、而不自行改只读卡文，这个处置是否恰当。
4. M5 的三元组表与实际字节是否处处对得上。
5. runner 门 BLOCKED 的登记是否仍然诚实（W4 锚点已再次前移，请自行核实当前值）。
6. 本卡是否还有任何「声明宽于证明」的残余。

前两轮已核实为真的项不重审，除非本轮改动波及。

## 输出格式

`[BLOCKER|HIGH|MEDIUM|LOW]` + 文件:行号 + 问题 + 建议修法；**末尾必须给出总裁决
PASS 或 FAIL**。没有发现也要明说查了什么、怎么查的。不要复述代码。
