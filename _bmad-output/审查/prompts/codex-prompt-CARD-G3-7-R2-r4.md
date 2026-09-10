# 独立复核请求 — CARD-G3-7-R2 round-4（r3 整改核验 · 绑定最终 HEAD）

你是独立复核者。请**只读**，不修改任何文件，不连数据库，不运行测试或脚本。
你的 round-3 意见（0 BLOCKER / 0 HIGH / 4 MEDIUM / 2 LOW）作者已全部处置；本轮请**独立核验处置是否成立**。
这轮的重点是收敛确认：若你确认本轮 BLOCKER=0、HIGH=0，请**明确写出这句结论**。

---

## 一 背景 + 最小读取面（写死，请只读这些）

**仓库树根**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery`

round-3 审的是 `975af19c`。之后有一个整改 commit（**本轮绑定 HEAD，请自行 `git rev-parse HEAD` 核对并写进正文首句**）。

**请读**：

1. 整改 diff：`git diff 975af19c HEAD -- . ':(exclude)_bmad-output'`
2. 你 round-3 原文：`_bmad-output/审查/codex-review-CARD-G3-7-R2-r3.md`
3. HEAD 版 `backend/tests/unit/test_mastery_fsrs_projection_boundary.py` **全文**（MEDIUM-1/2 与 LOW-5 的整改：`_os_open_is_write`、导入表先查、`called_name_nodes`、矩阵 21→26 条含常量路径反例）
4. HEAD 版 census：`_bmad-output/审查/evidence-g37r2/census-20260908T073936.md`（MEDIUM-3 第三步升级全仓 tracked 口径 / MEDIUM-4 三处「从未」收窄 / LOW-6 两步法→三步法）
5. 验收单 `_bmad-output/验收单/UAT-CARD-G3-7-R2-2026-09-08.md` §10.6 与 §10.9（「未见实现证据」收窄 + 「门会红一次」改为「枚举面内守门」的如实表述）

## 二 六条处置的作者自述（逐条独立核验，勿采信）

1. **MEDIUM-1（os.open flags）**：`_open_is_write` 四分——内建 Name→args[1]；`io.open`/`builtins.open`（接收者是模块名）→args[1]；`os.open`（接收者是 os）→转 `_os_open_is_write` 按**整数位掩码 flags** 判（O_WRONLY/O_RDWR/O_APPEND/O_CREAT/O_TRUNC/O_TEMPORARY 任一命中即写；flags 缺省=O_RDONLY 放行；flags 非名字形态解析不出→fail-closed 按写）；其余 Attribute（绑定方法）→args[0]。
2. **MEDIUM-2（导入衔接）**：三处——① 调用判定改为**先查导入表**再查原名单（修「别名 r 记录了却查不到」与第一档导入别名 cp 的漏）；② 回调扫描补 `Name` 分支（`from os import replace; asyncio.to_thread(replace, a, b)` 用 `called_name_nodes` 排除被调用者后命中）；③ 你 r3 指出的 `node.module.split(".")[0]` 对 `from os.path import ...` 的处理保留（你已说明拿不存在的标准库导入当反例无效，作者未再改这一点，理由照抄你的原话）。
3. **MEDIUM-3（目录全集）**：第三步从「补扫四个目录」升级为**全仓 tracked 文件一次扫**（`git grep -- . ':(exclude)_bmad-output' ':(exclude)_bmad-archive'`）——git 只搜 tracked 文件，目录全集问题消解。结果按文件归类：生产面命中仅 `review.py`（3，N 的来源）+ rollback 两处已排除假阳性 + 所有权模块自身；tests/docs/.gdr 不计；`backend/scripts`、backend 根 .py、仓库根、`tools/`、顶层 `tests/` 零命中（不在列表即证明）+ 正控。
4. **MEDIUM-4（三处未同步）**：census `:258`（节标题）`:261`（单文件限定注明）`:264`（结论句）与验收单 §10.6 全部改为「未见一致的证据 / 未见反证」口径。
5. **LOW-5（矩阵反例）**：io.open/builtins.open 两条改用**字符串常量路径**（`'notes.md'`）——并按你的分析如实注明「变量路径 p 在 r2 版会 fail-closed 报写，r2 的洞只在常量路径上」；注释改为如实分轮。矩阵 21→**26 条**（加 os.open 位掩码写/默认只读/O_RDONLY 只读、导入别名、第一档导入别名、裸名回调）。
6. **LOW-6（步骤引用）**：census 全文「两步法」→「三步法」清零（含 §0.5 标题、§六 N 限定句、§七.7）。

另：验收单 §10.9 的「新增写法时门会红一次」按你 r3 的批评改为「对**已枚举形态**（矩阵 26 条 + 三轮反例）会红；对未枚举形态静默放行，不是 fail-closed 的入口保证」。

## 三 按重要性排序的问题

1. 第四轮改写的 `_os_open_is_write` 与导入先查逻辑有没有新错向？（`_collect` 对 BinOp 的递归、`not names` 的 fail-closed 分支、`called_name_nodes` 与被调用 Name 的区分）
2. 26 条矩阵逐条静态推演是否与实现一致？
3. census 全仓口径下还有没有你没看到的新消费方或新问题？
4. 综合本轮 HEAD：还有没有 BLOCKER / HIGH？若没有，请明确写「本轮 BLOCKER=0、HIGH=0」。

## 四 输出格式

- **BLOCKER / HIGH / MEDIUM / LOW**，每条 `file:line` + 一句话结论 + 证据。
- 单列 **「已核实成立的处置」**（逐条对应你 round-3 的意见编号）。
- 信息不足明说「未核实」。

## 五 边界

- 只读；不连库；不跑测试/脚本；不评 G3-5 键化（U9-C 面）；不评 pyright 存量（U1/U2 面）；不评 `test_mastery_fusion` 既有红（U11-C 面）。
- 不要求也不需要任何攻击性内容；本轮只针对读取面内整改的正确性与诚实性。
