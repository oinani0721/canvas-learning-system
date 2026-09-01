BLOCKER/HIGH 清零：否（就 A/B/C 三缝隙及其整改而言）

- ✅ **A — PASS。** [`recap_scan.py:962-991`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:962) 将引用前导空白和剩余缩进统一换算为绝对内容列；`:1053` 的 `fence_list_col` 与 `:1070` 的比较同属绝对列。目标形态中开栏前缀列与内容列均为 5，不会误判容器终止。`:1049` 能识别本案列表 marker。定向门 [`test_recap_scan_signals.py:3050-3068`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3050) 与实现一致；三分类单元契约 [`test_recap_scan_signals.py:2444-2512`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:2444) 未被推翻。

- ✅ **B — PASS。** [`recap_scan.py:1808-1818`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1808) 先执行③段外检查，之后才进行 `data_mode != fallback_local` 早退；manifest 因而受检。HIGH-5b/6 的 fallback 专属边界从 `:1819` 开始。定向门 [`test_recap_scan_signals.py:3071-3085`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3071) 明确锁定 manifest、附录和专属诊断。

- ⚠️ **C — PARTIAL / HIGH。** 标准样例“九十八万”会在 [`recap_scan.py:1858-1872`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1858) 正确得到 `980000` 并因池外而拦截；但整改宣称的“解析失败 fail-closed”并未成立。

新增问题（仅计整改直接暴露/引入）：

- **HIGH — C 的失败关闭分支静态不可达，并可能按错误值查池。** `:1859` 的提取字符集与 [`recap_scan.py:1450-1465`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1450) 的映射集合完全相同；任何非空匹配都会在 `:1477-1495` 返回整数，因此 `:1861-1865` 的 `v is None / 无法验证` 分支不可达，集合外写法则根本不会进入解析器。与此同时，`:1478-1480` 对连续数字字仅反复覆盖 `digit`，不验证中文数词文法，可能只保留末位并在 `:1868-1872` 对错误的小值查池；若发生池碰撞，同类允许式仍可通过。该解析器虽非本 commit 新建，但 `ff946d8c` 新增的 C 路径直接依赖并宣称了这一保证，故属于本轮整改问题。

- **测试缺口伴随上述 HIGH。** [`test_recap_scan_signals.py:3088-3100`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/regression/test_recap_scan_signals.py:3088) 只覆盖一个可解析且池外的标准数词，并接受“无出处”或“无法验证”任一诊断；没有锁定解析值、解析失败分支或错误值与池碰撞路径。

- **LOW — A 注释口径滞后。** [`recap_scan.py:1041-1047`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1041) 仍称使用“剥引用后的相对口径”，与 `:1050-1053`、`:1070` 的绝对列实现矛盾；不影响当前行为。

过程与边界：

- 指定套件结果：`249 passed, 14 warnings in 33.67s`，exit code `0`。
- 首次受限沙箱运行在收集前因无可用临时目录退出；随后仅以相同命令在获准环境重跑并成功。
- 未构造或执行额外探针，未读取 `fixtures/` 下 `.md/.json` 正文，未编辑文件。
- `:1049` 的 marker 检测是整行搜索而非仅检查剥除前缀，但该条件在 `ff946d8c` 前已存在，按本轮“仅直接引入”规则不登记为新 finding。
- 结果仅代表该定向套件，不代表全量 CI。当前工具集没有 Graphiti 查询能力，未伪称完成该协议步骤。


