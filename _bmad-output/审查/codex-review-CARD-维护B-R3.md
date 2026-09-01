BLOCKER/HIGH 清零：否（就 C 取值口径而言）。

### 终裁正文

- ❌ HIGH｜存量未闭合：fallback 的 ASCII 仍按碎片入池。D2 ASCII 会跨连接字符取数，但 fallback 仍使用 `re.findall(r"\d+")`；`1 000`、`9**5` 会分别成为 `[1,0]`、`[9,5]`，碎片均碰池即可放行。[recap_scan.py:1668](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1668>)、[recap_scan.py:1918](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1918>)。因此“CJK 与 ASCII、D2 与 fallback 同一口径”不成立。

- ❌ HIGH｜表外字符导致尾片重锚，仍是 round-5 同型碰撞：

  - `九十八万5个`：CJK run 不命中整体，ASCII 只取 `5`。
  - `廿五个`：`廿`在表外，CJK 从 `五`重锚，按 5 入池；读者读 25。
  - `980,005个`：逗号切断后只取 `005→5`；逗号虽可见，却是正常千分位，不能归入“读者不会读成连续数”。

  证据见 [recap_scan.py:1383](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1383>)、[recap_scan.py:1499](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1499>)、[recap_scan.py:1653](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1653>)。`:1526-1528` 的“集合外字符一律 None/fail-closed”比真实调用链宽。

- ❌ HIGH｜连接表内也不全是“不可见排版噪声”。`[*_~\\\`]`允许未配对、渲染可见的 Markdown 字符；`[多余来几约近超]`会改变数量语义；任意短 `<...>`也可能包含 `<br>` 等可见布局。[recap_scan.py:1352](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1352>)、[recap_scan.py:1368](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1368>)。例如 `1*0个`会按 10 入池；`五来个`会按精确 5 入池。因此 `_join_free`“还原读者看到的那个数”的措辞过宽。

- ❌ HIGH｜`_D2_QUANT` 还有词法歧义。表内含 `点`；`五点五个`或 `5点5个`会被拆成两个 5 分别碰池，而读者看到的是 5.5。[recap_scan.py:1383](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1383>)。

三张表的登记结论：

- `_D2_JOIN_ONE`：承认“封闭表”属实，但“表外可见断点不会被读成连续数”被逗号反例推翻；表内可见/语义连接也未登记充分。
- `_D2_QUANT`：封闭性有注明，但残余说明低估了有限量词检查面及 `点`的歧义。
- `_CJK_NUM_CHARS`：17 字边界、`:1308/:1316` 当前手抄集合一致均属实；但“表外只是不进提取面”低估了尾片重锚碰撞。
- ✅ possessive `*+`：在当前定义下不改变匹配语言。连接字符集与后继 ASCII/CJK 数字字符集不相交，回退不可能产生新的成功匹配；当前作用只是限制回溯。若以后两集合出现交集，结论需重审。[recap_scan.py:1386](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1386>)、[recap_scan.py:1503](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1503>)。

### 测试复核

- ✅ 未见现存“实现不改也恒真”的核心门。映射期望已独立写死；两道合成门用窄池证明单字确实携自身值入池。[test_recap_scan_signals.py:3138](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3138>)、[test_recap_scan_signals.py:3197](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3197>)、[test_recap_scan_signals.py:3376](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3376>)。
- ❌ `:3296-3298` 宣称 CJK/ASCII × D2/fallback 全覆盖，但矩阵的 fallback 只测 CJK，未测 ASCII；与实现缺口一致。[test_recap_scan_signals.py:3296](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3296>)、[test_recap_scan_signals.py:3345](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3345>)。
- ⚠️ `:3088-3096` 的名称/首句仍称“中文数词入池”，实际契约是多字直接 fail-closed；`:3217`、`:3252` 的“一律”也应限定为表内字符、命中允许式或紧邻登记量词。
- ⚠️ `assert "九十八万五" in r.stdout`足以区分本次原始碎片 bug，因为原输入仍含连接符；但不足以冻结诊断契约——子串没有与同一条“无法解析”problem 绑定。`:3388-3392` 的两个独立 `any`也可理论上由两条不同问题分别满足。应要求同一 problem 同时包含诊断类别和完整 token。

### Survivor 承重

- ⚠️ survivor-13：若真的全局禁掉“跨连接提取”，`:3170-3181` 的正则契约、`:3288` CLI 矩阵和`:3388-3392` D2 合成门都应受影响。只杀矩阵一条，说明 mutant 只切了某一消费路径或负验证只选跑一门；不能据此宣称该门独自承载整项性质。CJK 路径有纵深，fallback ASCII 则根本未建立该防线。
- ⚠️ survivor-14：若其正是题面所述“恢复拼接前行级剥零”，指定测试中只有`:3337-3344`的 `1 000→1000`区分新旧顺序；`:3356`连续 `016`不能区分。该性质目前确为单点承重，没有独立纵深。

### 实际命令结果与过程

- pytest：收集 255；实际 `240 passed, 15 failed`，退出码 1，不是预期 255。失败分布为`:1031` 1 条、`:1055` 4 条、`:1190` 3 条、`:1650` 1 条、`:2807` 6 条。
- `recap_domain_negverify.py`：退出码 2；执行变异前发现已有串行锁，因此本轮没有得到“14 条全部变红”的结果，也不能把 survivor 实测写成通过。
- `git rev-parse HEAD`：`61d84d7523b0d3a9be7244beb0b696845118665d`
- pytest 首次在只读环境因无可写临时目录而未收集；随后以完全相同命令重跑，以上为真实测试结果。未运行 diff/show/log，未读 fixture 正文，未构造探针或临时脚本。
