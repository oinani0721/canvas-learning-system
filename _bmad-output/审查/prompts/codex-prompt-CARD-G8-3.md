你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树（下称 <Lane>）；你可以在只读沙箱里运行 `git --no-pager …` 读命令与 `sed -n` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-3（BATCH-2026-09-18-第十五批）：给 `backend/scripts/vault_lint.py` 加第二批四检查 ——
annotation_coverage（`验收单`/`审查` 下 `**User：**` 批注未答数与最老年龄，轻量 grep 口径）/
dlq_backlog（复制 traces.py:80-93 八条路径做**文件级**计数，⛔ 不 import app.*、不调端点）/
backup_freshness（`backups/neo4j/backup.log` 最近一条 `OK:` 的新鲜度，小时）/
recap_unsourced（子进程复用 recap_scan.py 收集模式的 `signals.unsourced_conclusions`）；
输入面不可用一律 degraded（warn + `details.degraded=true`，不伪装）。
前卡语境：G8-2 骨架 `4e489c10` 三检查 + X5-C G8-2b `79fd8bf8` 六 M 一 L 收口；本卡**不改**三旧检查 /
`exit_code` / `report_to_json` / `render_text`。

被审改动面：`git --no-pager diff --no-color fd9c7382 2b298383 -- . ':(exclude)_bmad-output'`（= 2 个文件；也可直接读改后整文件）。行号为改后现值（已实测）：

1. `backend/scripts/vault_lint.py`（+675/−5）
   - `:65-109` import 块（「import 零重依赖」不变量；`:108/:109` cvr / local_tz；`import subprocess` 是本次新增 stdlib）
   - `:211/:217/:235/:243/:253/:278` Finding / CheckResult / LintReport / exit_code / report_to_json / render_text（**本卡未动**）
   - `:924` `DLQ_BACKLOG_FILES`（恰 8 键；`:914-920` 注释声明复制口径与同源锁）
   - `:1042` `check_annotation_coverage`（含 `_annotation_hits`）
   - `:1143` `check_dlq_backlog`（含 `_count_jsonl_lines`）
   - `:1255` `check_backup_freshness`（含 `_BACKUP_OK_RE`）
   - `:1370` `check_recap_unsourced`
   - `:1495` CHECKS（7 项）/ `:1506` run_checks（新只读参数）/ `:1578` _EPILOG / `:1635` main（五新参）
2. `backend/tests/unit/test_vault_lint.py`（+483/−20）
   - `:1619` `_REAL_RECAP_SCAN`；`:1624` `_bmad_root`（以及 `_backend_dir` / `_backups_dir` / `_new_faces_args` / `_new_faces_kwargs`）
   - 新增 21 个 test 函数（75 → 96；112 collected）：四反例 `:1687` 起、四干净、四 degraded、同源锁 `:1854`、`--help`、`--only`、边界（size_capped / 盲区 / 无 OK / 无 dump / 超时 / no-signals + json-decode）

口径来源（只读参考，⛔ 不改）：`backend/app/api/v1/endpoints/traces.py:80-93`（BACKLOG_FILES 八条）与 `:270-357`（`_backlog_entry` 口径）· `backend/app/core/failure_counters.py:81-113`（count_lines / overflow_siblings）· `scripts/backup-neo4j.sh` 全文（53 行；:12 / :16 / :53）· `canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:637-660`（`_has_provenance`）/ `:715-730`（`sig_unsourced`）/ `:3448-3470`（main 参数）/ `:3690-3700`（signals 装配）· 新增测试全段 · `_bmad-output/审查/codex-review-CARD-G8-2-round12.md`（前卡终审语境）· 台账 §一.b「X5-C G8-2b」一行（`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:38`）· 卡文 §〇（`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P6-C.md`）

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. 四检查全走真文件零 mock：反例 / 干净 / degraded 全部 `tmp_path` 派生；recap 真起 `recap_scan.py` 子进程（不 patch subprocess）；DLQ 同源锁真起 `app` 包路由子进程（cwd=backend）。
2. `vault_lint.py` 仍零 `app.*` import（`grep -c '^from app\|^import app'` → 0），DLQ 只复制口径。
3. DLQ 八条与 traces.py 逐路径相等，且由**两层**同源锁绑定（AST 键集 + 子进程解析后 resolve 逐条相等）。
4. degraded 从不伪装 ok：warn + `details.degraded=true` + summary `"degraded:"` 前缀；不加第四种 status。
5. live 三处只读 digest 前后逐字同（live vault 全树 / 主干树 `_bmad-output` 的 `验收单`+`审查` / 现网 `backups/neo4j`）；三旧检查结论逐字未变。
6. 现网 recap 6/6 板 degraded（no-signals）系 live 副本为旧版脚本（输出无 `signals` 键）——如实降级非缺陷；换成兼容脚本时 6 板 value 全 0/无据。

# ③ 请按重要性回答（先看分诊表高 urgency 面）

Jev 分诊（jev-1.13.0；ref `2b298383`，全卡 diff；按 urgency 降序）：

| file | +/− | urgency | risk | review | test | flag |
|---|---|---|---|---|---|---|
| `backend/scripts/vault_lint.py` | +675/−5 | **2.92** | logic (conf 0.76) | 0.87 | 0.70 | True |
| `backend/tests/unit/test_vault_lint.py` | +483/−20 | **2.18** | test_or_docs (conf 0.94) | 0.74 | 0.92 | True |

（工具对超大 diff `truncated=True`，分诊仅供排序。）

⓪ 「已答」三形态判定是否会把**未答**批注判成已答（假阴性方向）——尤其 30 行窗口跨过下一条批注或 `## ` 的边界？
① DLQ 计数在 `size_capped` / PermissionError 下是否被压成 0 而不是 degraded？
② 备份检查取「最后一条 OK」是否会被后来的 SKIP 行遮住真实新鲜度（应取最后 OK 的时间而不是最后一行）？
③ recap 子进程超时 / rc≠0 是否会让整个检查报 ok（应 degraded 且其余板照报）？
④ 同源锁 (B) 的包路由子进程是否有出站 / 落盘副作用（cwd=backend、`PYTHONDONTWRITEBYTECODE=1`、`git status` 前后空）？
⑤ 负控是否红在指定断言且每段只拆一层？
⑥ `_EPILOG` 分级文案与代码分支是否一致？

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**负控输入**」「**对照输入**」「**未被拦下的输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`** —— 该行会被用作轮次闭合的依据。

# ⑤ 边界

只读；不连任何库（7691 / 7692 / 7687 不适用）；不评 G8-2c 变异复跑（X5-C 21 条旧变异已登记随 G8-2c）；不评 traces.py 自身改法；不评 D-41 / D-42 备份对账；不评 G5-4 信号定义；`_bmad-output/` 下验收单与存档不在审查面内（上方点名的前卡存档除外）。
