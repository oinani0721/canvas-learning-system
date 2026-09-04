# 对抗性代码审查任务 — CARD-W4-3b（门债补门）

你是独立审查者。工作树只读：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4`

**审查面 = 本卡未提交改动**，取法：

```
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4
git diff
```

涉及 4 个文件：
- `backend/scripts/lifespan_isolation_guard_probes.py`
- `backend/scripts/lifespan_isolation_negative_control.py`
- `backend/scripts/lifespan_isolation_runtime_sha.sh`
- `backend/tests/conftest.py`（仅一段 docstring 措辞更正）

## 一、这三个脚本是什么

一套「跑测试没碰生产数据 / 没连生产库」的门：

- `lifespan_isolation_runtime_sha.sh` —— 把一条命令包起来，比较命令前后若干**运行时
  数据文件**的 sha256。判 `RUNTIME-FILES: unchanged`（rc=被包裹命令的 rc）或
  `RUNTIME-FILES: CHANGED`（rc=1）或 `GATE-BROKEN`（门自认不可信，rc=1/2）。
- `lifespan_isolation_guard_probes.py` —— 上面那道门 + 一个 socket 门的**探针集**：
  每条探针把某一层防线拆掉或污染，断言门给出**指定的**那个结论。末行
  `GUARD-PROBES: PASS — N/N`。
- `lifespan_isolation_negative_control.py` —— 负控：在隔离副本里摘掉测试隔离夹具，
  断言防线让用例变红；外加一个静态 AST 门（扫 `backend/tests/` 里「未被隔离夹具
  覆盖的 TestClient 进 with 语句」）和它自己的反例/正例清单。

## 二、本卡改了什么（作者自述，**请独立核对，不要采信**）

上一张卡（X4）人判合入时，作者自认两条「修了但没有门能证明修对了」：

1. **M15**：`runtime_sha.sh` 修过一个真·假绿（被监视的 journal 从固定文件名改成
   `vault_index_pending__<key>.jsonl` 之后，固定锚点落空，`absent == absent` 让门恒判
   unchanged）。但 22 条注册探针里唯一碰运行时文件的那条走的是**固定项**分支，
   glob 分支无人覆盖 —— 删掉 glob 那几行，探针照样全绿。
2. **LOW#18**：AST 门修过一个「同名函数重定义时，安全的那个定义让整个名字被判安全」
   的缺陷，修法是失格名单；但没把对应反例加进常设清单 —— 删掉修复，负控照样全绿。

顺带处理四条：

3. **M14**：两侧的 glob `vault_index_pending*.jsonl` 比写侧实际能产出的形态宽
   （会收 `vault_index_pending_backup.jsonl` 这类人手放的旁文件 ⇒ 假红）。收窄成
   「旧固定名精确项 + `vault_index_pending__*.jsonl`」。
4. **M16**：失格名单跨迭代累积，把「知识还没补齐」的中间状态钉成永久结论，
   误拒 `def outer(): return inner()` 写在 `inner` 定义之前的合法工厂。改成每轮重算。
5. **M13**：脚本注释断言「`compgen -G` 展开本身已排序、不必外部 sort」——作者称在
   `/bin/bash` 3.2.57 上实测该断言为假（compgen 给 readdir 顺序），已改为显式
   `LC_ALL=C sort` 并 fail-closed。
6. `tests/conftest.py` 一段「atexit LIFO 最后执行」的措辞更正。

作者自称新增/改动 7 条 shell 探针族 + 1 个 Python 侧自证函数 + 2 条 AST 反例 + 2 条
AST 正例，并做了 9 条「拆掉修复后指定的那条门必须翻红」的实测，全部 KILLED。

## 三、请你回答的问题（按重要性排序）

1. **新加的门是否真的承重？** 对每一条新门，判断「把它保护的那段实现改坏，这条门
   会不会红」。作者的 9 条拆门实测在
   `_bmad-output/审查/CARD-W4-3b-拆门实测.txt`（若存在）。你不必复跑，但请从代码
   逻辑判断：判据是否可能被**别的**原因满足（即红得不是因为它该管的那件事）？
   期望「变绿」的对照探针（`runtime-glob-cached-expansion` /
   `runtime-glob-pattern-neutralized` / `runtime-glob-sidecar-excluded`）尤其值得看：
   它们判 `rc==0 且 stdout 含 unchanged 且不含 GATE-BROKEN`，这个判据够不够？
2. **M14 的收窄是放松方向** —— 现在有没有一种**生产写侧真的会产出**的 journal 文件名
   逃出新监视面？请看 `backend/app/core/vault_state_paths.py` 的
   `namespaced_state_path` / `legacy_state_path` / `fs_safe_key` 与
   `backend/app/services/vault_index_orchestrator.py` 的写点。
3. **M16 的修复是放宽方向** —— 「失格名单每轮重算」会不会让某类真正不安全的形态在
   AST 门下被判为「安全」？特别是：同名工厂 + 转调 + 迭代次数（`range(2)` 内层 / `range(4)`
   外层）三者组合下，有没有收敛不到、或收敛到错误不动点的输入？
4. **M13 的改动引入了新的外部依赖**（`/usr/bin/sort`）。它的 fail-closed 处理、
   与 `|| true` 的交互（作者刻意把排序拆出管道，理由写在注释里）是否正确？
   `LC_ALL=C` 是否足以钉死顺序？
5. `runtime_files()` 的 Python 侧自证函数（`run_runtime_files_selftest`）放在
   `main()` 最前、在 `--ast-only` / `--ast-negative-control` 短路**之前**。这个位置
   合适吗？它的四条判据有没有一条是恒真的（即无论实现对错都会通过）？
6. **声明与实现是否一致**：注释/docstring 里有没有比代码实际做到的更宽的说法？
   本仓的历史教训是「门说的比证明的宽」，请逐条比对新写的注释。

## 四、输出格式

按级别（BLOCKER / HIGH / MEDIUM / LOW）列出发现，每条给：位置（`文件:行`）、
一句话结论、**你据以判断的依据**（读到的具体代码，不要只说"可能"）、建议修法。
若某条你无法在只读环境下判定，请明说「未验证」并写清需要什么才能判定 —— 不要把
推测写成结论。最后给一句整体裁定：本卡的阻断级问题数量。

## 五、边界

- 只读，不要修改任何文件，不要运行会写盘的命令。
- 不要连接 7691 / 7687 / 7692 任何数据库端口。
- `backend/tests/support/live_port_guard.py` 的既有缺陷**不在本卡范围**（已另立卡），
  除非本卡的改动让它变得更糟。
