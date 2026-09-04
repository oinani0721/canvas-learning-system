# 复核轮 R1: CARD-G3-6b-R1 [BATCH-2026-09-01-第九批]

你是独立对抗审查方。本轮审查对象是一个**复核轮**，不是功能开发轮。

- 车道: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard
- **待审最终 commit: `9e158d8222da4d422f640ecf504088ee98649a6e`**（分支 card/w6-whyboard，worktree clean）
- 上一轮实现 commit: `c2d2e590`；功能基线: `9af18b27`
- 卡文: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第九批-goals/W6.md
- 验收单: `_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md`

## 背景：为什么有这一轮

第八批 round-3 两次运行都在完成验证后、输出最终报告时被内容过滤器拦截，
stdout 为 0 bytes（`_bmad-output/审查/codex-review-CARD-G3-6b-round3.md` 是空文件）。
因此「round-2 的 5 项发现已整改」这个判断**至今没有任何第三方签名结论**。

本轮卡文的任务因此是**证据真实性复核**，不是再扩功能。

## 本轮范围（明确的 out-of-scope，请先读）

卡文 §4(c) 明令：**Python bytecode 缓存（`.pyc` / `__pycache__`）与运行时篡改
明确排除在本卡威胁模型之外，本卡不宣称运行时完整性。**

- 这不是隐瞒：该边界已如实写进源码 docstring（`scripts/daily_review_pick.py`
  的 `_implementation_sha`，三条声明中的第 3 条）、测试 docstring、以及验收单
  「本卡未证明什么」第 4 条与「(c) pyc 面」小节。
- 上一轮 round-3 的 prompt 曾要求「探查排序规则变了而 sha 不变的残余面」，
  这直接导致审查方去构造绕过完整性校验的运行时篡改 PoC。本轮**不请求**该类工作。
- **请不要构造 `.pyc` 篡改、mtime 伪造或其他运行时字节码替换的验证代码。**
  该面的存在是已知的、已书面登记的设计边界。

**但**：如果你判断「把这一面排除出去」这个决定本身不正当（例如它其实有自然
触发路径、或声明文本仍然过宽、或这个收窄实质上是在回避审查），请直接把该判断
作为发现写出来 —— 用文字论证即可，不需要可执行 PoC。这一条是我明确请你评价的。

## R1 这一轮实际做了什么（请逐条验真伪）

1. **(a) 基线重收**：开工 `--collect-only` 实收 130 collected = 130 passed
   （pick 69 + overview 61），未照抄历史数字。
2. **(b) 独立复核**：`_bmad-output/审查/evidence-g36b-r1/g36b_r1_recheck.py`
   自构输入重测 round-2 五项整改，17/17 PASS。输出**分两份**归档，各自绑定字节：
   - `recheck-A-on-c2d2e590-bytes.txt`（对 c2d2e590 原样字节，sha `ad1a38a5…`）
   - `recheck-B-on-r1-narrowed-bytes.txt`（对 R1 收窄后字节，sha `2c8da36c…`）
3. **(c) 边界收窄（R1-F1）**：R1 自查发现三处「声明比证据宽」并整改 ——
   `_implementation_sha` / `effective_rank_config` / 测试 docstring 原写
   「任何排序规则改动**必然**变 sha」「兜住…的**整类**攻击」，而 round-3 已存在
   反例。现收窄为源文件字节层 + 三条声明（摘 .py 字节 / **单向**保证 / 不覆盖
   运行时）。验收单 H2 整改栏同步收窄。
4. **(d) 变异**：`g36b_r1_mutations.py` 8 条串行各杀其指定门，还原逐字节一致。
   脚本含三道防假绿：阶段 0 先证 8 门未变异时全绿（红可归因）/ 锚点唯一性断言
   （防死变异）/ `rc=5` 判 INVALID 不判红。
5. **(e) runner 门**：结构性 BLOCKED 并如实登记（`card/w4-safety-r2` HEAD 仍在
   开工基线 `2cacbb0c`，`batch9/integration` 不存在）。**本轮没有跑 runner。**
6. **(R1-F2) 证据一致性**：修「复现命令」段残留的 `126 passed` / `6 条全红`
   （正文为 130 / 8 条）；历史轨迹 `121→126→130` 与 round-2 报告里的「126 回归」
   属历史证据，原样保留未改。
7. **(g)** `estimated_minutes` 3/5 保持建议默认待用户校准，并注明未做真实跨日校准。

## 请重点审查

1. **上述每条的真伪**（鼓励自行运行测试、读探针脚本、复算 sha 实测）。
2. **收窄后的措辞是否仍有过宽处**：R1 声称修了三处「声明比证据宽」，请检查
   `scripts/daily_review_pick.py`、`backend/tests/regression/test_daily_review_pick.py`
   与验收单全文，是否还有别的地方在宣称超出实际证明面的保证。这是本轮的核心问题。
3. **独立复核探针本身是否是有效证据**：`g36b_r1_recheck.py` 的 17 项断言里，
   有没有「门空转」（无论被测对象怎样都会 PASS）的项？有没有 fixture 设计使某项
   实际上没测到它声称要测的性质？
4. **变异脚本的三道防假绿是否真的成立**，还是仅是措辞。
5. **BLOCKED 登记是否诚实**：(e) 未做这件事，验收单是否有任何地方把它写成
   「做了」或用别的证据冒充。
6. **证据一致性**：验收单里的数字/sha 与其绑定的字节状态是否处处对得上。

round-1/2 已 PASS 的项不重审，除非 R1 的改动波及。

## 输出格式

`[BLOCKER|HIGH|MEDIUM|LOW]` + 文件:行号 + 问题 + 建议修法；**末尾必须给出总裁决
PASS 或 FAIL**。没有发现也要明说查了什么、怎么查的。不要复述代码。
