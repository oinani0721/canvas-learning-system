> ⚠️ 本文件是 CARD-W4-FINAL-ACCOUNTING 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十四批手册 §三 T9-A 块。
> 批次标记 `[BATCH-2026-09-11-第十四批 / CARD-W4-FINAL-ACCOUNTING]`。车道：`card-t9-w4`（分支 `card/t9-w4`，NEW @ `08100483`，venv symlink 已建、`backend/.env` 在），本车道第 **1/4** 张，前提：**无（T9 首卡，HEAD 必须 = `B14_BASE` `08100483` 且 `git status --porcelain` 空）**，之后串 T9-B CARD-W4-4b7-TAIL → T9-C CARD-W4-SENTINEL-REBIND → T9-D CARD-RUNTIME-SHA-SURFACE。用户已裁：**R-11**（U7-A 外审 HIGH-1「`_final_accounting` 落盘失败 print 在退出保护块外、rc=0 假绿」登记 TAIL 高优先 = 第十四批、人判合入；方法学 HEAD−try/except 对照追认）/ D-15 多轮 / D-32 纯注释尾巴不重置。勘探 2026-09-11 于主干 `286178d8`（recon C §5 / §0.3），写卡已在 `08100483` 复测（本文件 `286178d8`↔`08100483` 零 diff）。协议（⛔ 必须读 **feature 主干树 `--add-dir` 那份**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md` —— §1 合并门 + D-15 轮次 / §2.1 存档首部 / §2.2 裁判落盘 + `--no-color` / §3 W4 哨兵）；手册同理只读主干树那份：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-11-第十四批开跑手册-10车道43卡.md`（§零 / §一 / §四）。⚠️ **车道树自己的 `.claude/rules/card-batch-protocol.md` 与手册是 `08100483` 版、不含本批回写**，别读那份；本批资产（卡文/协议/手册/64 基线）都在 feature 主干树，车道只读引用一律写绝对路径。

# CARD-W4-FINAL-ACCOUNTING — W4 守卫最终结账：落盘失败 print 移入退出保护块（stderr 同坏时 print 异常不再逸出 atexit 回调 → 消除「有未结账拦截却 rc=0」假绿）+ AST 判据「`_final_accounting` 内每个 print 都被 `except BaseException` 护住」先红后绿 + 三跑 A/B/C 全 rc=3

## 〇 事实
| 事实 | 位置 / 实测命令 |
|---|---|
| **文件**：`backend/tests/support/live_port_guard.py`（**1575** 行，blob `d0f12093…` @ `08100483`；与 U7 车道树 sha `e1988410c382a827cc412f28cc7f839e689b4a06` **完全相同**；`286178d8` / `08100483` / 波 0 文档 commit `e58d5c5c` 对本文件**零 diff**，波 0 只动文档） | `shasum backend/tests/support/live_port_guard.py`；`git diff --stat --no-color 286178d8 08100483 -- backend/tests/support/live_port_guard.py`（空） |
| `_final_accounting` 实测 **1487–1535**（AST），`os._exit(FINAL_EXIT_CODE)` 是函数最后一句 **:1535** | `python3 -c "import ast;t=ast.parse(open('backend/tests/support/live_port_guard.py').read());print([(n.name,n.lineno,n.end_lineno) for n in ast.walk(t) if getattr(n,'name','')=='_final_accounting'])"` → `[('_final_accounting', 1487, 1535)]` |
| **⛔ 缺陷行 :1512**（落盘失败 print）：`:1511 except Exception as exc:  # noqa: BLE001 —— 落盘失败要说话，但不能盖掉结账` → **`:1512 print(f"*** W4 guard: 账本落盘失败 {path}: {exc!r} ***", file=sys.stderr)`**；该 `except Exception` 体**不是** `except BaseException` 保护块 ⇒ :1512 的 print 自身抛出时无人接 | `grep -nF '账本落盘失败' backend/tests/support/live_port_guard.py` → `1512`（恰 1 行） |
| 落盘路径与发布：`:1504 ledger = STATE.finalize_and_snapshot()` / `:1505 path = os.environ.get(ENV_LEDGER)` / `:1506 if path:` / `:1507 try:` / `:1510 _publish_ledger(path, ledger)`（这三行本卡**不改**） | `sed -n 1504,1512p backend/tests/support/live_port_guard.py` |
| 退出保护块（正例对照，本卡不改，照此同型修 :1512）：裁定分支 `:1519 if unaccounted > 0 or (blocked > 0 and effective_status == 0):` / 保护块注释 `:1520-1521`（「报告整块包住（Codex round-1 HIGH-3 同型）：stderr 已关闭时 print 会抛，原来那个只裹 flush 的 try 挡不住它」）/ **`:1522 try:`** / 报告 print `:1523`、迭代 print `:1530` / **`:1533 except BaseException:  # noqa: BLE001` / `:1534 pass`** / **`:1535 os._exit(FINAL_EXIT_CODE)`** | `sed -n 1519,1535p backend/tests/support/live_port_guard.py` |
| **口径更正 1（recon C §5.3）**：U7 验收单写 `:1291-1303` 保护块与其后 `os._exit`（整体较本主干 **−231 行**，取自更早审 SHA）；卡文一律用主干实测行号或 `grep -nF` 锚，⛔ 禁照抄旧行号（长度门 ⑪） | recon C §5.3 |
| **口径更正 2（本次写卡补，recon C §5.4 脚本注释只列 1512/1523 两行）**：`_final_accounting` 内 `print(...)` Call 实测 **3 个**（`:1512` / `:1523` / `:1530`），不是两个。`B14_BASE` 上 AST = `1512 UNPROTECTED / 1523 protected / 1530 protected`（恰 1 个未护）；**修后必须 0 个 UNPROTECTED**（三个全 protected）。⇒ 设计稿 §4「修后两行 protected」为笔误，实义是「修后三个 print 全 protected / 0 UNPROTECTED」 | AST 脚本（§二.2，本次写卡实测输出三行） |
| **缺陷机理（recon C §5.1）**：`ENV_LEDGER = "W4_GUARD_LEDGER"`（`:222`）指向一个**目录** ⇒ `_publish_ledger`→`write_ledger` 的 `open(path,"w")` 抛 `IsADirectoryError`（`OSError` 子类，被 `:1511 except Exception` 接住）⇒ 执行 :1512 print。若此时 stderr 已关闭（atexit LIFO：先注册的「弄坏 stderr」回调**先**跑，`_final_accounting` 跑时 stderr 已坏），:1512 的 print **抛异常逸出** `_final_accounting`（它是 atexit 回调）⇒ :1535 的 `os._exit(3)` 永不执行 ⇒ 进程 **rc=0**，而账本 `blocked=1 / unaccounted=1`（未结账拦截却 0 收场 = 假绿） | recon C §5.1 |
| **三跑对照基线（U7 验收单 CONFIRMED 6/6，recon C §5.2）**：A（ledger=目录 + stderr 坏）**rc=0**（缺陷恰落此格）/ B（只落盘失败：ledger=目录 + stderr 正常）**rc=3** / C（只 stderr 坏：ledger 正常 + stderr 坏）**rc=3**。只有 A 红而 B/C 绿，才说明缺陷**恰在两条件同时成立**那一格，不是「随便坏一个就退不出去」 | recon C §5.2；U7 `UAT-CARD-RV-W4-4`「HIGH-1 CONFIRMED」 |
| **R-11**（`_bmad-output/审查/evidence-b13-integ/RULINGS-2026-09-10.md` 条目「R-11 U7 车道 → 人判合入」）：U7-A 外审 HIGH-1（`_final_accounting` 落盘失败 print 在退出保护块外、rc=0 假绿形态）→ 登记 TAIL 高优先（第十四批）；W4 门是测试基建**非产品数据面**；U7-C 5 轮已尽；复核员独立复现确认；方法学替代（HEAD−try/except 对照）追认 | RULINGS-2026-09-10.md 条目 R-11 |
| **guard 可用 API（搭建三跑 harness 用）**：`install()`（`:893`，内部先 `_install_audit_hook()` 后 `register_final_accounting()`，**预检 `assert_neo4j_target_blocked()` 仅当 `W4_GUARD_REQUIRE_BLOCKED_TARGET == "1"` 才跑 → 默认不连任何库**）/ `register_final_accounting()`（`:1361`，atexit LIFO：先注册→后跑）/ `STATE.late_snapshot()`（`:379`，取 `blocked/unaccounted/total`）/ `_audit_hook`（`:772`，`sys.addaudithook(_audit_hook)` `:857`）/ `FINAL_EXIT_CODE = 3`（`:225`）/ `BLOCK_REASON`（`:205`）。受拦事件由 `sys.audit("socket.connect", None, ("127.0.0.1", 7691))` **合成，不建真实连接** | `sed -n 893,960p`；`grep -n 'def install\|def register_final_accounting\|def late_snapshot\|ENV_REQUIRE_BLOCKED_TARGET\|FINAL_EXIT_CODE ='` |
| **U7 参考 harness（只读参考，在别的车道树，本卡不引用其路径做判据）**：`card-u7-w4guard/_bmad-output/审查/evidence-rv-w44/verify-codex-high1.py`（子进程 CHILD + 三跑 run(A/B/C)，该脚本只放 `_bmad-output`、不进代码树）。本卡在**自己车道树**重建等价 harness 落 `evidence-w4final/`，⛔ **行号全改主干实测**（U7 脚本 docstring 含旧行号，不得复制） | — |
| **非 app 卡**：`lefthook.yml` `python-typecheck` glob = `backend/app/*.py`（`:206`）；本卡只改 `backend/tests/support/**` ⇒ **不触发 typecheck、非 app 卡、无「pyright 保持 0」义务**（不在手册长度门 ⑩ 的 14 张 app 卡清单内）。`python-lint`（ruff）glob 覆盖 `backend/**/*.py`：`live_port_guard.py` 在 `B14_BASE` 上 `ruff format --check` = 已格式化、`ruff check` = All checks passed（本次写卡实测）⇒ 本卡改动须保持绿、**本文件无 462 既有漂移**（协议 §2.3 过渡条款对本文件不应触发） | `grep -n 'python-typecheck\|glob:' lefthook.yml`；`<venv>/ruff format --check <file>` / `ruff check <file>`（本次写卡实测 rc=0） |
| **guard 契约套件**：`backend/tests/unit/test_live_port_guard_contract.py`（含 `test_final_accounting_*` 族 `:1363` / `:1542` / `:1583` 等）——本卡**禁改**（非本卡地盘），作绿判据跑；它**不覆盖** A 格（ledger=目录 + stderr 坏 → rc），所以本卡的先红后绿锁只在 evidence 脚本、committed 套件无回归锁（见 §四「本卡未证明」④、「台账待登记」④） | `grep -n 'def test.*final_accounting\|def test.*ledger' backend/tests/unit/test_live_port_guard_contract.py` |
| tests/unit 红基线 **64** 条（`_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`，nodeid 口径，跑法带 `--ignore tests/unit/test_deploy_vault_sh.py`），**不含任何 `live_port_guard` nodeid** | `grep -vc '^#' <BASE>` → 64；`grep -c live_port_guard <BASE>` → 0（本次写卡实测；BASE 在 feature 主干树绝对路径） |
| **本批纪律**：非 app 卡（`python-typecheck` 不触发，但禁越界碰 `backend/app`）/ 判据 grep git 输出一律 `--no-color` + 同次验伪锚 / evidence 后缀 `.txt` 不 `.log`（仓根 `.gitignore` 吞 `*.log`）/ 末行 `rc=$pipestatus[1]`（zsh）/ ruff 判据 zsh 数组写法 / **批中禁装工具**（不往共享 venv 装/升包）/ `canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py` ⛔ 零写者 / live vault · 7691/7687 · 现网 LanceDB 只读 / 临时换文件负控走 EXIT trap 无条件还原 + 全文件 `shasum -a 256` 前后逐字同、⛔ 禁 `git stash` / 禁 `git checkout` 还原 | 手册 §零 / 协议 §2.2/§2.3 |

## 一 完成条件（AND）
- (a) **第 0 分钟**：`pwd` = `…/worktrees/card-t9-w4`、`git branch --show-current` = `card/t9-w4`、`git rev-parse --short=8 HEAD` = `08100483`、`git status --porcelain` 空；`test -e backend/.venv/bin/pytest && test -e backend/.env`；`PYTEST=$(pwd)/backend/.venv/bin/pytest`。开工先 `sed -n` / `grep -nF` / AST 核 §〇 每条 file:line（行号漂移则在验收单写「卡文 :X → 实测 :Y」，并以实测为准）。**开工基线自证**（必跑并落档）：`BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`；`test -f "$BASE" && grep -vc '^#' "$BASE"` → **64**（不是 64 或文件不在 ⇒ 停下报主 session，不得继续）；`grep -c live_port_guard "$BASE"` → 0。**手册地盘对齐核**（只读主干树那份）：`grep -n 'live_port_guard\|CARD-W4-FINAL-ACCOUNTING\|T9-A' <手册绝对路径>` 应命中 §一「只 T9」地盘行与车道表；命中则验收单写「已对齐」并抄该行，⛔ 不命中也**不得改手册**（手册非本卡地盘），按本卡 §三 执行并在验收单首段如实写。
- (b) **先红**（在 HEAD **未改代码**时先跑两个判据并落 `evidence-w4final/*-before-*.txt`）：
  ① **AST 判据**（§二.2 脚本）：输出**恰 1 行** `1512 ... UNPROTECTED`，另两行 `1523 protected` / `1530 protected`（即 `_final_accounting` 内 3 个 print 中 1 个未护）。
  ② **三跑 harness**（§二.3）：**A rc=0**（缺陷复现）/ **B rc=3** / **C rc=3**；且三跑进程内账本都 `blocked == 1 and unaccounted == 1`（前提成立，否则后面全无意义）；A 的 rc **≠** B、C 的 rc（缺陷落在两条件同时成立那一格，不是随便坏一个就退不出去）。
  （⛔ 若改前 AST 0 行 UNPROTECTED 或三跑 A 已 rc=3 = 夹具/锚写反了，停下重写，不得靠 (c) 去「修」一个已绿的判据。）
- (c) **最小修法**（只碰 `backend/tests/support/live_port_guard.py`，只动 `:1511-1512` 的 `except Exception` 体）：把 :1512 的落盘失败 print **包进嵌套保护块**，与退出保护块 `:1522-1534` 同型：
  ```python
          except Exception as exc:  # noqa: BLE001 —— 落盘失败要说话，但不能盖掉结账
              try:
                  print(f"*** W4 guard: 账本落盘失败 {path}: {exc!r} ***", file=sys.stderr)
              except BaseException:  # noqa: BLE001 —— 可观测性不得挡在强制退出前面
                  pass
  ```
  使落盘失败 print 自身抛出的异常（stderr 同坏时）**不再逸出** `_final_accounting`，流程照常走到 :1519 裁定分支 → :1522-1534 退出保护块 → :1535 `os._exit(3)`。⛔ **不动**：取快照 `:1504`、`_publish_ledger` 调用 `:1510`、裁定分支 `:1519`、退出保护块 `:1522-1534`、`os._exit(FINAL_EXIT_CODE)` `:1535`、函数签名；不改任何结账/发布/退出语义（落盘失败仍「说话」，只是 print 异常被就地吞掉，与 :1534 同语义）。
- (d) **后绿**（改后同两判据重跑，落 `evidence-w4final/*-after-*.txt`）：① AST **0 行 UNPROTECTED**（`:1512` / `:1523` / `:1530` 三行全 protected）；② 三跑 **A rc=3 / B rc=3 / C rc=3**（三跑进程内账本仍 `blocked == 1, unaccounted == 1`）。
- (e) **负控输入**（承重，临时改代码后无条件还原 + sha 前后逐字同）：把 (c) 新加的嵌套 `try: … except BaseException: pass` 删掉（还原到 UNPROTECTED 形态）→ 重跑 ① AST 必回到**恰 1 行** `1512 UNPROTECTED`、② 三跑 **A 必回 rc=0**（验伪锚：证明两判据真能翻转，不是恒绿）；每段走 EXIT trap **无条件还原**（`git show HEAD:backend/tests/support/live_port_guard.py > <tmp>` 比对还原，⛔ 禁 `git stash` / 禁 `git checkout`），`shasum -a 256 backend/tests/support/live_port_guard.py` 跑前/跑后两行逐字同（都贴进验收单）。
- (f) **guard 契约不回退**：`cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_live_port_guard_contract.py` → 0 failed（开工 / 收工各一次，passed 数写实测并对比）；`tests/unit -k live_port_guard` 绿（本卡只把 print 护起来，不改结账/发布/退出语义 ⇒ 契约套件应原样通过）。
- (g) **目录级**：`tests/unit`（带 `--ignore tests/unit/test_deploy_vault_sh.py`）收工一次，nodeid 口径与 `$BASE`（64）diff **只允许 `<` 行**（本卡不修红，预期仍为空；任何 `>` = 阻断；rc 与汇总行都在）；⛔ 承重那跑的文件名**先固定成变量**（禁 glob，见 §二.6）；⛔ 禁 `wc -l` 当判据。
- (h) **地盘核**：`git diff --stat --no-color 08100483 HEAD -- . ':(exclude)_bmad-output'` 的代码文件 ⊆ {`backend/tests/support/live_port_guard.py`}（**仅此一个**；验伪锚：同命令去掉 `':(exclude)_bmad-output'` 应多出 `_bmad-output/` 路径）。
- (i) **现网只读**：三跑 harness 的 ledger 路径全部 `tempfile.TemporaryDirectory` 派生；harness **不设** `W4_GUARD_REQUIRE_BLOCKED_TARGET=1`、不设 `NEO4J_URI` / LanceDB 路径类环境变量指向现网；受拦事件用 `sys.audit` 合成、**不建真实连接**；禁连 7691/7687。开工 `touch $EV/sentinel`，收工对现网 LanceDB 目录（路径以 `backend/app/config.py` lancedb 字段 + `backend/.env` 实测为准，只 `ls -la`）`find <dir> -type f -newer $EV/sentinel | wc -l` = 0。
- (j) **Codex**：顺序固定「代码与两判据全部定稿 → 跑全部裁判 → 送 Codex → 之后只改 `_bmad-output`」；Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本卡有代码改动 ⇒ 多轮，上限 5；见 §四）；prompt 五分节 + 最小读取面写死；prompt 与存档不得出现协议 §2 的四个禁用措辞。
- (k) **提交**：单独 commit（T9-B 开工前工作树必须干净）；header ≤100 含 `[BATCH-2026-09-11-第十四批 / CARD-W4-FINAL-ACCOUNTING]` 且含卡号，body 行 ≤100（`wc -m`）；`*.stderr*` 不入库；不 push；`ruff check` / `ruff format --check`（zsh 数组写法，对本卡 diff 文件跑）绿（`B14_BASE` 上本文件已格式化，本卡改动须保持；本文件实测无 462 漂移，不应触发 §2.3 过渡）；本卡不触及 `backend/app`（`python-typecheck` 不触发；若 diff 出现 `backend/app` 文件 = 越界，停下报主 session，⛔ 不自作主张扩面）。
- (l) **「本卡未证明什么」必填**（≥4，见 §四）+ **「台账待登记条目」必填**（≥4，见 §四）。

## 二 裁判命令
> 树根先 `PYTEST=$(pwd)/backend/.venv/bin/pytest`；**`EV=$(pwd)/_bmad-output/审查/evidence-w4final`（必须绝对路径 —— 承重裁判带 `cd backend`，相对 `EV` 会解析成不存在的 `backend/_bmad-output/…`，`tee` 报 No such file、存档落不下来）**；**基线不在本树** —— `BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`（feature 主干树绝对路径，⛔ 不是 `$(pwd)/_bmad-output/…`）。**开工自证**：`test -f "$BASE" && grep -vc '^#' "$BASE"` → 64（否则停下报主 session）。`mkdir -p "$EV"`；承重裁判 `2>&1 | tee "$EV"/<name>-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]`（zsh；`.txt` 不 `.log`）。
1. **事实核**：`git rev-parse --short=8 HEAD` → `08100483`；`git status --porcelain | wc -l` → 0；`python3 -c "import ast;t=ast.parse(open('backend/tests/support/live_port_guard.py').read());print([(n.name,n.lineno,n.end_lineno) for n in ast.walk(t) if getattr(n,'name','')=='_final_accounting'])"` → `[('_final_accounting', 1487, 1535)]`；`grep -nF '账本落盘失败' backend/tests/support/live_port_guard.py` → `1512`（恰 1 行）；`sed -n '1504,1535p' backend/tests/support/live_port_guard.py` 与 §〇 原文逐字同；`shasum backend/tests/support/live_port_guard.py` 记录开工 sha。
2. **AST 判据脚本**（落 `$EV/ast-protected.py`，改前/改后各跑一次 tee）：
   ```python
   import ast
   src = open('backend/tests/support/live_port_guard.py', encoding='utf-8').read()
   fn = [n for n in ast.walk(ast.parse(src)) if getattr(n, 'name', '') == '_final_accounting'][0]
   for n in ast.walk(fn):
       if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'print':
           prot = any(
               isinstance(a, ast.Try) and a.lineno < n.lineno <= a.end_lineno
               and any(isinstance(h.type, ast.Name) and h.type.id == 'BaseException' for h in a.handlers)
               for a in ast.walk(fn) if isinstance(a, ast.Try)
           )
           print(n.lineno, 'protected' if prot else 'UNPROTECTED')
   ```
   跑（⛔ **从车道树根跑** —— 脚本按相对路径 `backend/tests/support/live_port_guard.py` 打开，不是 `cd backend`）：`backend/.venv/bin/python "$EV"/ast-protected.py 2>&1 | tee "$EV"/ast-<before|after>-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]`。**改前期望**三行：`1512 UNPROTECTED` / `1523 protected` / `1530 protected`（`grep -c UNPROTECTED` = 1）；**改后期望**三行全 `protected`（`grep -c UNPROTECTED` = 0）。⛔ 判据是**逐行 protected/UNPROTECTED 名单**，不是只数个数（等长替换混淆）。
3. **三跑 harness**（落 `$EV/three-run-abc.py`，改前/改后各跑一次 tee；子进程合成拦截事件、不建真实连接）：
   ```python
   import hashlib, json, os, subprocess, sys, tempfile
   from pathlib import Path
   BACKEND = Path.cwd()                      # 从 backend/ 目录跑
   GUARD = BACKEND / "tests/support/live_port_guard.py"
   CHILD = r'''
   import atexit, io, json, os, sys
   backend, ledger_path, break_stderr = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
   os.environ["W4_GUARD_LEDGER"] = ledger_path
   os.environ.pop("W4_GUARD_REQUIRE_BLOCKED_TARGET", None)   # 默认不连库
   sys.path.insert(0, backend)
   from tests.support import live_port_guard as guard
   guard.install()                           # 内部先注册 _final_accounting
   if break_stderr:                          # atexit LIFO：后注册→先跑→结账时 stderr 已坏
       def _break():
           b = io.StringIO(); b.close(); sys.stderr = b
       atexit.register(_break)
   try:                                      # 合成一条到受拦端口的审计事件（不建真实连接）
       sys.audit("socket.connect", None, ("127.0.0.1", 7691))
   except BaseException:
       pass
   snap = guard.STATE.late_snapshot()
   print("CHILD-JSON: " + json.dumps({"blocked": snap["blocked"], "unaccounted": snap["unaccounted"]}), flush=True)
   # 正常返回 —— rc 完全交给 atexit 的 _final_accounting 决定
   '''
   def run(label, ledger_is_dir, break_stderr):
       with tempfile.TemporaryDirectory(prefix="w4final-") as td:
           tdp = Path(td); child = tdp / "child.py"; child.write_text(CHILD, encoding="utf-8")
           ledger = tdp / "ledger_as_dir"; ledger.mkdir() if ledger_is_dir else None
           if not ledger_is_dir:
               ledger = tdp / "ledger.json"
           env = dict(os.environ); env["PYTHONDONTWRITEBYTECODE"] = "1"
           p = subprocess.run([sys.executable, str(child), str(BACKEND), str(ledger), "1" if break_stderr else "0"],
                              capture_output=True, text=True, env=env, timeout=120)
           payload = {}
           for line in p.stdout.splitlines():
               if line.startswith("CHILD-JSON: "):
                   payload = json.loads(line[len("CHILD-JSON: "):])
           return {"label": label, "rc": p.returncode, "acct": payload}
   sha0 = hashlib.sha256(GUARD.read_bytes()).hexdigest()
   a = run("A ledger=目录 + stderr 坏", True, True)
   b = run("B 只落盘失败（ledger=目录 + stderr 正常）", True, False)
   c = run("C 只 stderr 坏（ledger 正常 + stderr 坏）", False, True)
   for r in (a, b, c):
       print(f"{r['label']}: rc={r['rc']} acct={r['acct']}")
   print("sha-unchanged:", hashlib.sha256(GUARD.read_bytes()).hexdigest() == sha0)
   print("PRECOND blocked/unaccounted all 1:", all(r["acct"].get("blocked") == 1 and r["acct"].get("unaccounted") == 1 for r in (a, b, c)))
   print("A!=B,C:", a["rc"] != b["rc"] and a["rc"] != c["rc"])
   ```
   跑（⛔ **从 `backend/` 目录跑** —— harness 内 `BACKEND = Path.cwd()` 且子进程按 `tests.support.live_port_guard` 导入，必须 cwd=backend）：`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python "$EV"/three-run-abc.py 2>&1 | tee "$EV"/three-run-<before|after>-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]`。**改前期望**：`A rc=0` / `B rc=3` / `C rc=3` / `PRECOND … True` / `A!=B,C: True`；**改后期望**：`A rc=3` / `B rc=3` / `C rc=3` / `PRECOND … True`。
4. **负控 (e)**：删 (c) 的嵌套保护 try（还原 UNPROTECTED）后重跑裁判 2、3 → AST 回到 1 行 `1512 UNPROTECTED` **且**三跑 A 回 rc=0（两判据都翻转才算承重）；EXIT trap 无条件还原（`git show HEAD:backend/tests/support/live_port_guard.py > /tmp/w4final-orig.py` 后 `cp` 还原，禁 git stash/checkout）；`shasum -a 256 backend/tests/support/live_port_guard.py` 负控段跑前/跑后两行逐字同（都贴）。
5. **guard 契约**：`cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_live_port_guard_contract.py 2>&1 | tee "$EV"/contract-<open|close>-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]` → 0 failed（开/收各一，passed 数写实测对比）。
6. **目录级**：**承重文件名先固定成变量**（⛔ 禁 glob）：`TS=$(date +%Y%m%dT%H%M%S); RUN="$EV"/unit-close-$TS.txt`（开工同法 `unit-open-$TS.txt`）；`cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider 2>&1 | tee "$RUN"; echo rc=$pipestatus[1] | tee -a "$RUN"`；`grep -E '^(FAILED|ERROR) tests/' "$RUN" | sed 's/ - .*//' | sort -u > "$EV"/close.nodeids; grep -v '^#' "$BASE" | sort -u > "$EV"/base.nodeids; diff "$EV"/base.nodeids "$EV"/close.nodeids` → 开工为空；收工只允许 `<`（本卡不修红，预期仍空）。⛔ 判据里只出现 `$RUN` 与 `$BASE` 两个变量（`grep … unit-close-*.txt` 会因多份文件前缀污染 nodeids → 假阻断）。
7. **地盘门 + 现网只读**：`git diff --stat --no-color 08100483 HEAD -- . ':(exclude)_bmad-output'` 的代码文件 ⊆ {`backend/tests/support/live_port_guard.py`}（验伪锚：去掉 exclude 多出 `_bmad-output/`）；`grep -n 'fsrs_bridge\|decay_beta' backend/tests/support/live_port_guard.py` → 0 命中；`find <现网 lancedb 目录> -type f -newer "$EV"/sentinel | wc -l` → 0（开工 `touch "$EV"/sentinel`）。
8. **Codex 后**：`git diff --stat --no-color <审SHA> HEAD -- . ':(exclude)_bmad-output'` → 空（仍绑定）；存档首部 `模型 / reasoning_effort / codex` 三字段齐；`grep -c` 旧模型名 → 0。

## 三 禁改与隔离
- 本卡地盘 = **`backend/tests/support/live_port_guard.py`（独占，只改 `:1511-1512` 的 `except Exception` 体，加一层嵌套 `try/except BaseException: pass`）** + `_bmad-output/审查/evidence-w4final/**`（harness / AST 脚本 / 裁判存档）、`_bmad-output/验收单/UAT-CARD-W4-FINAL-ACCOUNTING-<日期>.md`、`_bmad-output/审查/prompts/codex-prompt-CARD-W4-FINAL-ACCOUNTING*.md` 与 Codex 存档（随卡 commit）。
- `live_port_guard.py` 内**禁改**：取快照 `:1504`、`_publish_ledger` 调用 `:1510`、裁定分支 `:1519`、退出保护块 `:1522-1534`、`os._exit(FINAL_EXIT_CODE)` `:1535`、`finalize_and_snapshot`（`:365`）、`_audit_hook`（`:772`）、`record`（`:308`）、`_publish_ledger` 本体（`:1408`）、`write_ledger`、`register_final_accounting`（`:1361`）、`install`（`:893`）、`late_snapshot`（`:379`）——本卡**只把「落盘失败 print」护起来**，不改任何结账/发布/退出/装门语义。
- **禁改 T9 后续卡地盘**（本卡不碰）：`backend/tests/support/guard_plugin.py`、`backend/tests/conftest.py`、`backend/tests/unit/conftest.py`（T9-C）、`scripts/runtime_sha.sh`（T9-D）。
- **禁改 `backend/tests/unit/test_live_port_guard_contract.py`**（非本卡地盘，作绿判据跑，不新增/不修改其用例）；禁改任何 `backend/app/**`（零文件；`python-typecheck` 不触发，若 diff 出现 app 文件 = 越界，停下）。
- **硬边界**：⛔ 禁写 live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/**`；⛔ 禁连 7691/7687（harness 用 `sys.audit` 合成，不设 `W4_GUARD_REQUIRE_BLOCKED_TARGET=1`/`NEO4J_URI`）；⛔ 禁碰 `canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py`（本卡零关联，grep 0 命中）；⛔ 现网 LanceDB 只读；⛔ 禁 `git stash`（栈跨全部 worktree 共享）；不改台账；不 push；`*.stderr*` 不入库；`.log` 后缀不用；批中禁装包。
- **禁放宽判据**：三跑不得改成「没报错就算过」——必须 A 的 rc 真从 0 翻到 3、且 B/C 恒 3、`PRECOND` 三跑 `blocked=unaccounted=1` 成立；AST 判据必须逐 print 报 protected/UNPROTECTED；负控两判据都要翻转（AST 回 1 UNPROTECTED **且**三跑 A 回 rc=0），只翻一个 = 判据没锁住缺陷，停下。

## 四 Codex / 验收单
命令（协议 §2 固定）：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-FINAL-ACCOUNTING[-rN].md)" > _bmad-output/审查/codex-review-CARD-W4-FINAL-ACCOUNTING[-rN].md 2> _bmad-output/审查/codex-review-CARD-W4-FINAL-ACCOUNTING[-rN].stderr </dev/null`。
**轮次**：Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本卡有代码改动 ⇒ **多轮，上限 5**；第 5 轮仍有 HIGH 停下交主 session；审后再改代码必再送一轮；纯注释/docstring 尾巴按 D-32 不占轮次不重置，主 session 逐行等价核；车道对 HIGH 的驳回写理由但不能自判通过；0 字节存档重发一次，再 0 字节 → 主 session 人审）。存档首部六行 blockquote（协议 §2.1：会话头自证 = 抄 `.stderr` 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行并**括注行号**；缺 `模型 / reasoning_effort / codex` 任一 = 该轮不计配额）。
**prompt 五分节**：一 背景 + **最小读取面写死** = `git diff 08100483 <审SHA> -- . ':(exclude)_bmad-output'` + `live_port_guard.py :1485-1540`（改后实测范围）+ `$EV/ast-protected.py` 全文 + `$EV/three-run-abc.py` 全文 + recon C §5 摘要 + R-11 原文；二 作者自述请独立核对：`:1512` 落盘失败 print 现被嵌套 `except BaseException` 护住、三跑 A 由 rc=0 翻 rc=3、B/C 恒 rc=3、三跑 `blocked=unaccounted=1`、未改结账/发布/退出语义、负控两判据能翻转；三 按重要性排序的问题：⓪ :1512 的嵌套保护是否真吞掉**所有**逸出路径（含 `BrokenPipeError` / `ValueError: I/O operation on closed file` 等 stderr 坏态），是否引入新的「吞掉真实结账失败信号」的风险；① A 格改后 rc=3 是否靠 `os._exit(FINAL_EXIT_CODE)` 真执行、而非别处早退或被别的兜底路径掩盖；② 三跑用 `sys.audit` 合成的拦截事件与真实 `socket.connect` 拦截是否在记账路径上等价（`blocked/unaccounted` 计数一致）；③ 保护 print 吞异常后「落盘失败要说话」是否仍成立 / 可观测性降级是否可接受（对照 :1534 同款注释）；④ committed 套件无回归锁（先红后绿只在 evidence 脚本）是否遗漏面、是否该把契约套件纳入本卡；⑤ `_rewrite_ledger_after_late_record` 等迟到路径是否有同型未护 print；四 输出格式（BLOCKER/HIGH/MEDIUM/LOW + file:line + 一句复现思路，措辞用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」）；五 边界（只读、不连库、不跑完整 7692 真库门与真实 atexit 迟到线程竞态、不评 W4 哨兵判据改绑 = T9-C 面）。
**验收单** `_bmad-output/验收单/UAT-CARD-W4-FINAL-ACCOUNTING-<日期>.md`（DoD-3 双段）：4-A Claude 已代验贴证据（AST 改前 1 UNPROTECTED / 改后 0；三跑改前 A0·B3·C3 / 改后 A3·B3·C3；契约套件 0 failed；负控两判据翻转 + sha 逐字同；目录级 diff 空；地盘门 ⊆ 一文件）；4-B 零技术词一句 + felt-sense，例：「以前测试在一种少见的组合下会'假装通过'、其实出过问题也不声张；现在就算连报错的出口都坏了，系统也一定会以'失败'收场、绝不蒙混——我感觉这道最后的安全网终于真的兜得住了，心里踏实」。
**「本卡未证明什么」**（≥4）：① 未证明真实 Neo4j 拦截（用 `sys.audit` 合成，不建真实连接）；② 未跑完整 7692 真库门、未证真实 atexit 迟到线程与 `_publish_ledger` 锁竞态下的行为；③ 三跑只覆盖 `IsADirectoryError`（落盘失败）+ stderr closed 两类故障，未覆盖磁盘满 / 权限 / 路径消失等其它落盘失败与 stderr 半坏态；④ **committed 测试套件未新增回归锁**——先红后绿只在 `evidence-w4final/` 脚本、不在 CI 跑的 pytest 里；若要 committed 锁须把 `test_live_port_guard_contract.py` 纳入本卡地盘（交主 session 裁）；⑤ 未排查 `_rewrite_ledger_after_late_record` / 迟到路径的 print 是否也有同型未护（本卡只改 `_final_accounting`）；⑥ 未评 W4 哨兵判据改绑（T9-C 面）。
**「台账待登记条目」**（≥4）：① R-11 U7-A HIGH-1「rc=0 假绿」→ 本卡修复 sha + AST / 三跑 evidence 路径；② 口径更正「U7 验收单旧行号（−231 行）→ 主干 `:1512/:1522-1534/:1535`」落档；③ 口径更正「`_final_accounting` 内 print 实测 3 个（`:1512/:1523/:1530`），设计稿『两行 protected』为笔误」落档；④ **committed 回归锁缺口**（evidence-only 先红后绿）→ 建议把 `test_live_port_guard_contract.py` 纳入 T9-A 地盘补一条 A 格回归用例，交主 session 裁；⑤ 迟到路径 / `_rewrite_ledger_after_late_record` 同型未护排查移交（若 Codex 发现）；⑥ Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数；⑦ tests/unit 目录级 diff 结果。
commit header ≤100 含批次标记且含卡号；不 push；**独立 commit 且工作树干净后同车道继续 T9-B**；跑完说「复核第十四批 T9」。
