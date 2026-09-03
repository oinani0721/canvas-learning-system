# 复核轮 R1 round-2: CARD-G3-6b-R1 [BATCH-2026-09-01-第九批]

你是独立对抗审查方，本轮是 R1 的第 2 轮（卡文预算最多 3 轮）。

- 车道: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard
- **待审最终 commit: `66346bce74410ed8996277c55c9b4c4d763103f9`**（分支 card/w6-whyboard，worktree clean）
- 上一轮 R1 commit: `9e158d82`；实现 commit: `c2d2e590`；功能基线: `9af18b27`
- 你的 round-1 报告: `_bmad-output/审查/codex-review-CARD-G3-6b-R1.md`（FAIL，1H/3M/2L）
- 卡文: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第九批-goals/W6.md
- 验收单: `_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md`

## 本轮范围（同 round-1，先读）

卡文 §4(c)：**`.pyc` / `__pycache__` 与运行时篡改明确排除在本卡威胁模型外，
本卡不宣称运行时完整性。** 该边界已写进源码 docstring、测试 docstring 与验收单。
**请不要构造 `.pyc` 篡改、mtime 伪造或运行时字节码替换的验证代码。**

你 round-1 的 LOW 已被采纳：验收单不再宣称「launchd 不存在自然触发路径」，
改为「本卡未评估该路径，按威胁模型排除」。若你认为这个排除本身仍不正当，
请用文字论证提出，不需要 PoC。

## round-1 → round-2 逐条整改（请验真伪）

- **[HIGH] decay_beta 函数体不在指纹内** → **你的发现已被 R1 独立复现并确认成立**
  （`_bmad-output/审查/evidence-g36b-r1/g36b_r1_verify_high_decay.py` +
  `verify-high-decay-output.txt`：六常量逐字相同、板序 `[B板,A板]`→`[A板,B板]`、
  rank sha 两边 `503fd4b6…`）。
  整改取你两个建议中的**前者（收窄保证）**而非后者（把 decay_beta 字节纳入摘要）——
  理由：后者改变 sha 语义 = 扩功能，与卡文「本卡不扩功能、只做证据复核」定位冲突，
  且 `decay_beta.py` 是卡文明令禁改的文件。
  具体：`_implementation_sha` docstring 收窄为「**本文件字节 + 明列生效值**」，
  并新增**第 2 条**如实登记该缺口；验收单「本卡未证明什么」新增**第 9 条**同款登记。
  **请核查这个取舍是否可接受，以及收窄后的措辞是否仍有过宽处。**

- **[MEDIUM] 探针实证假绿（四处）** → 全改，项数 17→20：
  ① authoritative 六案例改为断言**精确回落值**（含半份配置的 `{7, 5}`）+ 告警**点名词**；
  ② 取值绑定改为比较**最终 rank SHA**，并核对 `cfg["implementation_sha256"]` 与裸值一致；
  ③「分钟真生效」改为走 **`build_payload` 生产入口**，断言落盘 `estimated_minutes`
     等于 `due_new×13 + 其余×11`；
  ④「recorded 以实际为准」改为断言**生效值**（`cfg["limits"]` / `cfg["ranking_factors"]`）
     未被登记的谎称值污染。
  另新增**负控** `g36b_r1_negctl_probe.py`：复现你的三重破坏，**逐项单独 + 三处叠加**
  四种形态，全部变红（输出见 `negctl-output.txt`）。
  **请再试一次**：能否构造别的破坏使强化后的 20 项探针仍报全 PASS。

- **[MEDIUM] R1-F1 仍漏多处过宽声明** → 三处 docstring 改为「本 fixture 上的单向观察」，
  显式否认逆命题与全空间覆盖。精度门**补上真实排序断言**（原版从未调用 `rank_boards`）：
  近邻 pick 差 1e-8，8 位 `[B板,A板]` / 7 位同分退 blr 级 `[A板,B板]`。
  该新断言的承重已验证（变异精度常量接入点 → 门红，还原逐字节一致）。
  验收单第 5 条标题也改了（原标题与正文自相矛盾）。

- **[MEDIUM] 变异脚本防假绿部分成立** → 仅 `rc=1` 判红，`2/3/4/5` 一律 INVALID；
  改用精确 nodeid `file::testname`；保留 stderr 尾部；加 SIGINT/SIGTERM 还原 handler
  并**如实声明它不等价于 EXIT trap**（SIGKILL 仍留字节，真判据是逐字节比对）。

- **[LOW] launchd 自然触发路径** → 两处措辞收回（见上）。
- **[LOW] batch9 目录 vs 分支** → 补齐两条检查并注明分支 ref 与 worktree 目录名。

## 本轮复跑数据（请独立复核）

- 裁判 1：`130 passed`（pick 69 + overview 61）。
- 探针：A（`c2d2e590` 原样字节 `ad1a38a5…`）**20/20**；B（当前字节 `2c8186a1…`）**20/20**。
- 变异：**8/8** 各杀其指定门（全 `rc=1`），还原逐字节一致。
- live 只读探针：前后 sha 逐字相同（零写入），rank sha `503fd4b6…`→`eb6b6710…`。
- **(e) runner 门仍 BLOCKED**（`card/w4-safety-r2` HEAD 仍 `2cacbb0c`，batch9 集成树不存在）。

## 请重点审查

1. HIGH 的**取舍**是否可接受（收窄声明 vs 扩指纹），收窄后措辞是否还有过宽处。
2. 强化后的 20 项探针**是否还能被构造出假绿**；负控本身是否有效（四种形态够不够）。
3. 新补的排序断言是否真承重，还是又一处空转。
4. 变异脚本的 rc 判定与 nodeid 改动是否真的关闭了 round-1 指出的缺口。
5. 是否还有**别处**在宣称超出实际证明面的保证（源码、测试、验收单全文）。
6. 证据数字与其绑定的字节状态是否处处对得上（含本轮新增的 sha 演进一跳）。

round-1 已核实为真的项不重审，除非本轮改动波及。

## 输出格式

`[BLOCKER|HIGH|MEDIUM|LOW]` + 文件:行号 + 问题 + 建议修法；**末尾必须给出总裁决
PASS 或 FAIL**。没有发现也要明说查了什么、怎么查的。不要复述代码。
