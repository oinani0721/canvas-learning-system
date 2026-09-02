BLOCKER/HIGH 清零：否

### 机器事实

- ✅ WT `card-v2-recapfix` 的 `git rev-parse HEAD`：`f7d25f5800d551170679cba766e002e6c0872deb`，与预期一致。
- ✅ 指定命令最终结果：`270 passed, 14 warnings in 44.57s`，exit 0。
- 首次在只读沙箱内因无可用临时目录、尚未收集测试便失败；获准后原样重跑得到上述结果。

### 核心问题

- ❌ HIGH，存量：tips 仍在 raw 文本绑定。[recap_scan.py:2191–2222](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2191) 的段抓取、`in_sec`、`all_hits` 都使用 raw `text`。后续 D2 虽做 visible 归一，但非“全板规模”句会在 1937、1981 跳过；fallback 全文门又只检查含“派生”的行。因此两种模式仍存在“保留正确行，再加入渲染等价但两个固定短语均被排版切开的冲突行”路径。

- ❌ HIGH，存量：③标题仍按 raw `^### ③` 选段，见 [recap_scan.py:1113–1115](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1113)、2243–2248、2437–2443。styled ③标题下的冲突信号可落在信号绑定之外；2248 只挡 exact-raw「无来源结论」，其他三个信号没有同类段外门。

- ❌ HIGH，本轮引入的语义范围泄漏：seed 修复虽没有变量作用域外泄，但把整个小节交给 `_visible_block` 后，再拿归一后的节点名对 raw `node_id`，见 [recap_scan.py:2059–2099](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/board-recap/scripts/recap_scan.py:2059)。实际路径位于同文件；其中 `_visible_text` 无条件删 `_`/`*`（1734–1765），而节点名规则并不禁 `_`（121–149）。`Seed_A` 会变成 `SeedA`：单独存在时误拒；若两者并存，还可能绑定到错误节点的 `tips_count`。这是“局部变量正确、归一范围错误”。

- ❌ HIGH，存量：manifest seed 行允许任意 tail。[recap_scan.py:1262–1265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1262) 的 `rest` 是 `.*`，而 2084–2099 只绑定第一个批注数。fallback 才有整行形状门（2473–2485）；manifest 下在正确数字后再陈述另一计数仍无绑定。

- ❌ HIGH，存量、设计级：`_visible_text` 仍不能代表 Obsidian 渲染。源码自己已确认 escaped/unpaired `* _ ~` 可把读者看到的 `1*5` 按 `15` 入池并放行，[recap_scan.py:1441–1454](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1441)，并承认不是完整 renderer（1693–1694）。highlight、合法多反引号 code span、embed、`%%…%%`、表外 Unicode 数字等仍不闭合。所以全局命题“校验器读数恒等于 Obsidian 可见数”目前不能成立。

### 本轮处置判断

- ✅ ③段内信号行改为 visible 选行（1124–1131）、五元组局部 `_visible_block`（2155–2165）、fallback ⑦的 visible `m7`（2257–2268）均正确，未发现静态死分支。
- ✅ fallback 形状门使用局部 `seed_vis`（2458–2465），其后的全文“派生”门仍遍历原 `text`（2491–2499）；上一版的函数体级重绑已消除。
- ⚠️ seed 值绑定能正确关闭此次 manifest 双行逃逸，但因上述节点身份归一，整体只能判 PARTIAL。
- “tips、③标题未复现”作为所选探针的观察可以解释，但不能推导安全：
  - tips：只切开一侧时，同一行另一计数短语会形成第二个 raw 命中，触发重复门。
  - ③标题：复制完整四信号块时，raw「无来源结论」会撞 2248 的段外门。
  更窄的代码路径仍开放。

### 崩溃识别

- ⚠️ PARTIAL：结构只能称“traceback 子集的确定性标记 + formatter 启发式补充”，不能称可靠二分。[test_recap_scan_signals.py:109–139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:109) 只在 `run_verify` 子进程 stderr 含精确 traceback 头时打标；`run_collect` 没有该接线。
- 不产生该 traceback 头的典型漏项包括：顶层 `SyntaxError`/`IndentationError`、显式 `SystemExit`、捕获异常后非零退出、`os._exit`、SIGKILL/SIGSEGV/SIGABRT、OOM/native fatal crash。反之，成功进程若向 stderr 打印该字面也会误标。
- producer 与 consumer 各自手写 `[[CHILD-CRASH]]`，见测试 104–126 与 [negverify.py:662–664](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:662)，没有把真实 producer 输出直接送入 classifier 的端到端同步门。
- `E {1,3}<名称>` 与 4+ 格续行的规则是当前 `--tb=short` 启发式；[pytest.ini:19–21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/pytest.ini:19) 确实固定了 `--tb=short`。1/2 格测试诚实注明“无实测、保守锁定”，不能算真实 formatter 证据。
- ❌ 文档仍有事实错误：测试 docstring 称“缩进上界 + 紧跟冒号”共同判异常（[test:4587–4588](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4587)），实现已明确删除冒号条件（negverify 673–680）。

### 行为门与变异

- ✅ r19 monkeypatch 哨兵不再恒真；删除真实调用会让 `called` 为空。
- ⚠️ 其措辞仍略宽：测试丢弃 `run_verify()` 返回值，只验证哨兵参数是某个 `CompletedProcess`，没有证明它就是返回的那个对象，见 [test:4660–4668](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4660)。
- ⚠️ r20 的“四处消费方都走 `_visible_block`，漂移即被抓”不成立。[test:4744–4747](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:4744) 只测 helper 存在及自身输出；生产实际只有三个 helper 调用，③信号仍直接逐行 `_visible_text`。
- ⚠️ r16 虽在注释承认真正段外路径未覆盖，但随后的 case 名和断言仍写“段外”，见 4485–4493；措辞只收窄了一半。
- ✅ #48 的替换静态上确实移除了当前全部 11 个区间分隔符，见 [negverify.py:568–577](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:568)。
- ⚠️ 但行为门只枚举 `~～〜到至`，漏六种横线（test 4566–4569）；且真正区间正则仍手抄另一份分隔表（recap_scan 1652–1655），并非“同源”。全删 mutant 被第一个 `~` 杀死，不能证明每个字符面独立承重。
- ⚠️ 静态复核未发现 51 个 old anchor 命中注释、旧位置或 textual no-op；但 `run_suite` 只要求所选 OR 用例中至少一个失败（[negverify.py:776–797](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:776)）。所以“51/51”只证明 51 个组合 mutant 各至少撞上一道门。
- ❌ 变异脚本仍原地写 TARGET，且写入发生在还原 `try/finally` 之前（[negverify.py:769–773](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/recap_domain_negverify.py:769）。写入异常、SIGKILL、解释器崩溃或断电仍可留下变异；前后 hash 自检覆盖不了这些情况。

### 闭合建议

一次改动内可闭合：

- tips 使用局部 visible 视图统一抓段、选行和全局重复检查。
- ③标题、重复段、段外四个 label 共用一个“剥代码块后 visible”的 section helper。
- seed 仅归一固定结构词与数字，保留 raw 节点身份并增加归一碰撞检查；manifest tail 改正向语法并绑定全部计数。
- marker producer/consumer共享常量或把真实输出直接送 classifier；哨兵增加对象 identity；修正文档。
- #48 对全部 11 个字符逐项正反锁，并让 `_D2_RANGE_RE` 从同一常量派生。

需要重做设计：

- 用 Obsidian/CommonMark 兼容 AST/renderer，或对未支持的 Markdown/Obsidian 语法 fail-closed；继续扩正则表无法证明渲染等价。
- 变异在隔离副本/临时 checkout 中运行，停止原地改生产文件。
- 若要可靠识别无 traceback 崩溃，需要结构化记录子进程退出原因，而不是解析 pytest 文本。

验证限制：未运行变异脚本、602 项扩大回归或任何探针；未读 fixtures 正文；未运行 `git diff/show/log -p`；未修改工作区。51/51、602 passed 与字节一致性仅作车道自报，未独立重跑。


