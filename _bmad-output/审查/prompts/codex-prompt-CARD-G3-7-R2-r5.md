# 独立复核请求 — CARD-G3-7-R2 round-5（r4 整改核验 · 绑定最终 HEAD · 末轮）

你是独立复核者。请**只读**，不修改任何文件，不连数据库，不运行测试或脚本。
你的 round-4 意见（0 BLOCKER / 0 HIGH / 2 MEDIUM / 3 LOW）作者已全部处置。
**这是本卡协议允许的最后一轮**（上限 5 轮）。若你确认本轮 BLOCKER=0、HIGH=0，请**明确写出这句结论**；
剩余 MEDIUM / LOW 将作为登记项进入验收单与台账，不再整改。

---

## 一 背景 + 最小读取面（写死，请只读这些）

**仓库树根**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery`

round-4 审的是 `2c18ff1d`。之后有一个整改 commit（**本轮绑定 HEAD，请自行 `git rev-parse HEAD` 核对并写进正文首句**）。

**请读**：

1. 整改 diff：`git diff 2c18ff1d HEAD -- . ':(exclude)_bmad-output'`
2. 你 round-4 原文：`_bmad-output/审查/codex-review-CARD-G3-7-R2-r4.md`
3. HEAD 版 `backend/tests/unit/test_mastery_fsrs_projection_boundary.py` **全文**（M-1/M-2/L-3 的整改都在这里）
4. HEAD 版 census：`_bmad-output/审查/evidence-g37r2/census-20260908T073936.md` 的 §0.5 第三步一段（L-5）
5. 验收单 `_bmad-output/验收单/UAT-CARD-G3-7-R2-2026-09-08.md` §10.9（L-4）

## 二 五条处置的作者自述（逐条独立核验，勿采信）

1. **MEDIUM-1（flags 判定放行未知变量，与声明的 fail-closed 相反）**：
   新增常量 `_OS_OPEN_KNOWN_FLAGS`（写 flags ∪ 只读/附加位：O_RDONLY、O_EXCL、O_NONBLOCK、O_NDELAY、O_SYNC、O_DSYNC、O_RSYNC、O_NOFOLLOW、O_CLOEXEC、O_BINARY、O_TEXT、O_INHERIT、O_NOINHERIT、O_SHORT_LIVED、O_RANDOM、O_SEQUENTIAL、O_LARGEFILE、O_ASYNC）。
   `_collect` 增加 `nonlocal unparsed` 状态：Attribute/Name 收进 names，BinOp 递归，**其他形态（调用/常量/下标）置 `unparsed = True`**。
   终判改为 `return not (not unparsed and names and names <= _OS_OPEN_KNOWN_FLAGS)` —— **只有「无未解析片段 且 收到的名字全部已知 且 无写位」才放行**。
   你给的两个反例 `flags = os.O_WRONLY; os.open(p, flags)` 与 `os.O_RDONLY | get_flags()` 应当都变成「写」。
2. **MEDIUM-2（导入表在 open 特判之后，`from shutil import copyfile as open` 漏）**：
   把「先查导入表」的分支**整体移到 `open` 特判之前**，成为 Call 循环里的第一个判定。
3. **LOW-3（`os.open(p)` 不能当「默认只读」负控）**：矩阵项标签改为「os.open 缺 flags 无效调用」并注明 flags 必填、缺省是 TypeError；`_os_open_is_write` docstring 同步改为「缺 flags 时返回 False 仅表示静态上不报写，该调用本身无效」。
4. **LOW-4（§10.9 示例与矩阵数量未同步）**：`from os import replace as r` 从「看不见的形态」移出（已由导入表覆盖，反例已进矩阵）；矩阵数量改为**29 条**（本轮又加了 3 条：os.open 未知变量 flags / os.open 混合未知调用 / `as open` 导入劫持）。
5. **LOW-5（census 「仅 3 个文件」与枚举的 4 个不一致）**：改为「命中 4 个文件（排除所有权模块 `review_service.py` 后为 3）」。

## 三 按重要性排序的问题

1. 第五轮改写的 flags 判定（`unparsed` 状态机 + 已知名单）有没有新错向？特别是：
   - `_OS_OPEN_KNOWN_FLAGS` 名单不全导致的**误报**（平台专有 flag 被当未知 ⇒ 报写）——作者声明这是刻意的从严方向，你认不认；
   - `names <= _OS_OPEN_KNOWN_FLAGS` 的子集判定与 `unparsed` 的组合，有没有仍然放行真实写入的路径。
2. 导入表移到最前之后，有没有**新的**优先级冲突（例如导入表里的名字恰好也是绑定方法名，或与 `open` 特判的顺序调换引入的别的漏）？
3. 29 条矩阵逐条静态推演是否与实现一致？
4. 综合本轮 HEAD：还有没有 BLOCKER / HIGH？若没有，请明确写「本轮 BLOCKER=0、HIGH=0」。

## 四 输出格式

- **BLOCKER / HIGH / MEDIUM / LOW**，每条 `file:line` + 一句话结论 + 证据。
- 单列 **「已核实成立的处置」**（逐条对应你 round-4 的意见编号）。
- 信息不足明说「未核实」。

## 五 边界

- 只读；不连库；不跑测试/脚本；不评 G3-5 键化（U9-C 面）；不评 pyright 存量（U1/U2 面）；不评 `test_mastery_fusion` 既有红（U11-C 面）。
- 不要求也不需要任何攻击性内容；本轮只针对读取面内整改的正确性与诚实性。
