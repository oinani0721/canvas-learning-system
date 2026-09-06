# 独立复核请求 — CARD-DEBT-mutation-kill-identity（变异负控的「击杀身份」判据统一）

## 一 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas`
（分支 `card/z2-cas`）。**只读**复核，请不要修改任何文件、不要连数据库。

本卡把「变异负控的击杀判据」统一到一处。要复核的东西只有两类：

1. **新模块全文**：`backend/scripts/mutation_kill_identity.py`
2. **本卡 diff**：
   ```
   git diff 3601051d <审SHA> -- . ':(exclude)_bmad-output'
   ```
   （`3601051d` 是本卡开工时的 HEAD，即上一张卡 CARD-G3-3-R1 的末 commit。
   注意 pathspec 必须写成 `':(exclude)_bmad-output'`；`':!...'` 在 zsh 下会被吃掉。）

需要时可以读的上下文（都在树内）：
- 四套 harness：`backend/scripts/g32b_mutation_gates.py`（138 条）、
  `g32cb_mutation_gates.py`（9 条）、`g32ccr1_negative_controls.py`（11 条）、
  `g33_mutation_gates.py`（18 条）；
- 它们绑的门文件：`backend/tests/regression/test_g3_2_review_ledger.py`、
  `backend/tests/regression/test_g3_3_cas.py`（**本卡一个字都没改门文件**）；
- 跑批取证：`_bmad-output/审查/evidence-mutkill/`（`.txt` / `.json`）；
- 验收单：`_bmad-output/验收单/UAT-CARD-DEBT-mutation-kill-identity-2026-09-06.md`。

### 这张卡要解决的问题（一句话）

四套 harness 原来的击杀判据都是「进程 rc 对 + 门名字样在输出里 + 有 failed 字样」。
这种判据只能回答「**有没有**红」，回答不了「红在**哪一条断言**上」。本仓已经因此
两次把不成立的结论记成 KILLED：一次是击杀由**同时施加的层**贡献，一次是**变异体
在编译期就死**（于是它声称要打红的那条断言反而通过，红落在另一条上）。

本卡的改法：抽出共用模块，加两道判据 ——
① 施加变异后、跑门**之前**先编译自检，不通过判第三种裁决 `SYNTAX-INVALID`；
② 每条变异声明 `EXPECT_MSG`（它**声称**要打红的那条断言的消息片段），判据取
pytest `-rf` 短摘要行 `FAILED <nodeid> - <reason>` 里该 nodeid 自己的 reason。

## 二 作者自述（请独立核对，不要采信）

1. **三套的 N/N**：g32b `<N>/138`、g32cb `9/9`、g32ccr1 `11/11`、g33 `18/18`，
   `ANCHOR-ERROR 0`、`SYNTAX-INVALID 0`。g33 的 verdict 列与上一张卡收官的
   `mutation-results-20260906T025116.json` 逐字相同。
2. **`EXPECT_MSG` 的来源**：g32cb 9 条、g32ccr1 11 条、以及 g32b 里
   `test_round16_fsrs_applied_across_all_branches` 那 4 条，是**先读门源码推出
   「这条变异会先撞上哪条断言」**再写的；g32b 其余条目是**先跑一次 `--probe`
   观察**（`--probe` 不做任何判定、裁决一律 `OBSERVED`、rc 恒 4）拿到实际拒因，
   再逐条对着变异意图判断「这条断言是不是它声称要打红的那条」后回填的。
   作者认为后一种绑定方式**今天证不出多少东西**（判据与被测量同源），价值在于
   **从今往后**门/代码漂移时会立刻报 SURVIVED —— 这一点已写进验收单
   「本卡未证明什么」。请判断这个自我限定是否**足够**，有没有被说宽。
3. **豁免表**：`EXPECT_MSG_EXEMPT` 逐条带理由，主要形态是「门里那条断言**没有
   消息**」（pytest 短摘要给的是 `assert 3 == 5` 这种**值**，换个 fixture 数据就变，
   不构成稳定身份）。
4. **4 条锚点处置**：`M142` / `M143` / `M145` 主锚、`M157` 层锚在上一轮全量里
   命中 0 次（= 那 4 条什么都没测）。本卡逐条更锚到现址并在车道树实测 `count == 1`，
   没有退役任何一条。
5. **g32b 补了 SIGTERM/SIGINT/SIGHUP handler**，并把启动自愈从「只扫主锚」扩到
   「主锚 + 同层锚」。

## 三 请按重要性回答的问题

1. **`EXPECT_MSG` 会不会被 pytest 输出里**别的**东西喂饱？** 判据面是
   `mutation_kill_identity.failed_reasons()` 解析出的、**该 nodeid 自己的**短摘要
   reason。请找出能让「目标断言其实没红、判据却命中」的输入形态（例如：被测子进程
   在运行期把片段打到 stderr；同一门里另一条断言的消息**包含**目标片段；参数化
   用例；reason 缺失时的行为）。
2. **`syntax_check()` 对 `.md` 的块提取**用的是 `<<'PYEOF'\n(.*?)\nPYEOF`，比
   `test_g3_3_cas.py:36` 与旧 g33 用的 `python3 - <<'PYEOF'` **宽**（理由：
   `start-exam-board/SKILL.md:246` 的引导行带参数，窄正则匹配不到那一块）。
   请判断：放宽会不会把**未变异**的干净树误判成 `SYNTAX-INVALID`？会不会反过来
   漏掉某一类真正会在编译期死掉的变异体？两个 SKILL.md 之外的目标文件（`.py`）
   走的是整文件 `compile()`，够不够？
3. **豁免表的理由是否成立？** 逐条看 `EXPECT_MSG_EXEMPT`：有没有哪一条其实能绑
   （门里那条断言其实有消息、或有别的稳定身份可用），只是作者偷懒？
4. **4 条更锚是不是「同一件事」？** 逐条核对新锚指向的生产代码与该变异的意图：
   `M142`（dup 分支改用全局 W 判「已应用」）、`M143`（缺凭据不拒）、
   `M145`（dup 恢复成功后不升 true）、`M157` 层锚（序数方向校验）。
   特别请核 `M143` 与 `g32cb` 的 `M1` 锚在**同一行**这件事：两者是不是同一个变异
   的重复？（作者认为不是：`M1` 退回「只拒 None」，`M143` 是 `if False:` 整道拆掉，
   绑的门也不同。）
5. **`judge_surface_missing()` 够不够？** 它只在「rc==1 且输出里一条 `FAILED` 都没有」
   时报判据面缺失。有没有别的形态会让判据安静地退化成恒假（= 全报 SURVIVED，
   看起来像「所有门都不承重」而实际是 harness 坏了）？
6. **g32b 的 handler 覆盖到 `finally` 路径了吗？** 请核 `_install_signal_handlers()`
   抛的 `_Terminated` 会不会被沿途某个 `except Exception` 吞掉，导致还原不执行；
   以及 `--probe` / `--only` 两个新入口的 rc 语义（都恒为 4）有没有可能被误读成通过。
7. **有没有哪条判据是自指的**（拿被测对象自己的输出当期望值）、或**恒真/恒假**的？

## 四 输出格式

按严重度分组（BLOCKER / HIGH / MEDIUM / LOW），每条给：
`文件:行号` + 一句话缺陷 + **能让它发生的具体输入或场景** + 建议处置。
若某条只是「读起来可疑但证不出可达」，请明确标成 `不可达/存疑`，不要与可达缺陷并列。
最后给一段「作者自述里哪些说法比证据宽」的清单。

## 五 边界

- 只读；不要改文件、不要跑会写盘的脚本（`g32b_mutation_gates.py` 等**不带**
  `--list` 的跑法会临时改生产文件）。`--list` 是只读入口，可以跑。
- 不要连 Neo4j（7691 / 7687）、不要写 live vault。
- **门本体**（`backend/tests/**`）与**被变异的生产文件**（两个 `SKILL.md`、
  `fsrs_bridge.py`、`validate_learning_events.py`、`learning_event_log.py`）
  都不在本卡范围内 —— 它们的内容如有问题请只登记，不要当成本卡缺陷。
- `lefthook.yml` 是别的车道的地盘，本卡不改。
