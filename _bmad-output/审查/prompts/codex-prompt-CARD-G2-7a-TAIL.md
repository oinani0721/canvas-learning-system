# 独立复核请求 — CARD-G2-7a-TAIL（部署校验器 hotkeys 无写端 FIFO 挂起先修）

## 一 背景 + 最小读取面（请只读下面这些，不要扩大读取面）

仓库：`canvas-learning-system`，工作树 `.claude/worktrees/card-t7-skills`，分支 `card/t7-skills`。
被审提交（审 SHA）：`b3baf7d967692db0b172f5ebb4de9e4ae6357923`。前一卡末 commit（PREV）：`09567e35bf393c34d1ab185e89e6b9effede7141`。

请读：

1. `git diff 09567e35bf393c34d1ab185e89e6b9effede7141 b3baf7d967692db0b172f5ebb4de9e4ae6357923 -- . ':(exclude)_bmad-output'`
   —— 这是本卡的**全部代码改动面**（两个文件）。
2. `scripts/verify_vault_install.py`
   - `:1272-1417` — `_check_hotkeys()`（本卡主修面，形态门在 `:1311-1357`）
   - `:556-572` — `_resolved_kind()`（既有形态 helper，本卡未改）
   - `:732-760` — `_probe_regular_readable()`（既有只读探测样板，本卡未改）
   - `:53-59` — 退出码四档 docstring（本卡未改，语义不得变）
   - `:503-522` — `_entry_state()`（既有存在性判断，本卡未改）
3. `backend/tests/unit/test_vault_install_manifest.py`
   - `:3172-3267` — 本卡新增：超时常量 `HOTKEYS_FIFO_TIMEOUT_S`、`_report_section()`、
     以及回归门 `test_hotkeys_fifo_does_not_hang_and_reports_unreadable`（全文）
   - `:643-745` — 既有门 `test_verifier_write_calls_are_confined_to_write_report`（本卡在其中加了 10 条验伪锚）
   - `:758-829` — `_is_os_open()` / `_os_open_flag_names()` / `_is_readonly_open()`（本卡扩展了 `os.open` 分支）
4. `_bmad-output/验收单/UAT-CARD-G2-7a-2026-09-08.md` 的 MEDIUM-2 表行原文
   （原始缺陷描述：「hotkeys 前移后未验形态即 `read_text()` ⇒ hotkeys 是无写端 FIFO 时会阻塞在打开阶段，
   返回不了 rc=2」）。
5. 如需看本卡自己的证据：`_bmad-output/验收单/UAT-CARD-G2-7a-TAIL-2026-09-17.md` 与
   `_bmad-output/审查/evidence-g27a-tail/`。

## 二 作者自述（请独立核对，不要默认我说的是对的）

1. 缺陷：`_check_hotkeys` 在 `_entry_state`（`os.lstat`，无写端 FIFO 判 `present`）之后**直接**
   `hotkeys_path.read_text(encoding="utf-8")`。`read_text` 内部是**阻塞** open，无写端 FIFO 上
   open 一直等写者、永久停在打开阶段，外层 `except (OSError, UnicodeDecodeError)` 到不了。
2. 修法：读内容前补形态门 —— `os.open(path, os.O_RDONLY | os.O_NONBLOCK)` 拿到 fd（无写端 FIFO 上
   立即返回），再用**同一个 fd** 的 `os.fstat` 判 `stat.S_ISREG`；不是普通文件就 `os.close` 后走
   嵌套 helper `_unreadable(...)` 并 `return`（进 `report.unreadable` ⇒ 退出码 2）；是普通文件才用
   `os.fdopen(fd, "r", encoding="utf-8")` 从**同一个 fd** 读。
   自述理由：用同一 fd 的 `fstat` 而不是路径上的 `os.stat` 预判，是为了让「判形态的对象」与
   「读内容的对象」是同一个 inode。
3. 归桶：特殊文件走 `_unreadable` ⇒ 退出码 2。**刻意不照搬**同函数里 main.js 侧
   `if main_js_kind != "file":` 那条（它只置 `report.hotkeys_note`、退出码仍 0，是同一份验收单的
   MEDIUM-3 既有缺口，本卡不扩面去改它）。
4. 回归测试走 `subprocess` + `timeout=`，不在 pytest 进程内调 `main()`/`verify()` —— 进程内那条路
   在缺陷回归时会把整套 pytest 一起挂住，既不会红也拿不到失败信息。超时取 60 秒，依据是同一条命令
   正常路径本机连跑 5 次最慢 0.052 秒。
5. 负控输入两段（都实测变红）：(1) 去掉整个形态门、还原为裸 `read_text` ⇒ 回归门红在
   `subprocess.TimeoutExpired`；(2) 把形态门判据改成恒放行（`if False:`）⇒ 回归门红在
   「明细必须说清是形态问题」那条身份断言。第二段里退出码**仍是 2**、hotkeys **仍在** unreadable 桶里
   （FIFO 读到 EOF ⇒ 空串 ⇒ 落到既有的「不是合法 JSON」分支），所以只断言退出码或只断言
   「在 unreadable 里」的门在该输入下会给出通过。
6. 既有门 `test_verifier_write_calls_are_confined_to_write_report` 因新增的 `os.open` 变红：
   其豁免 helper `_is_readonly_open` 按 `isinstance(node.func, ast.Attribute)` 判「绑定方法」，
   于是把 `os.open(path, flags)` 当成 `path.open(mode)`、把 path 当模式读。我给它加了 `os.open` 分支：
   旗标必须是纯 `os.O_*` 字面（可用 `|` 连）且全部落在只读白名单
   `{O_RDONLY, O_NONBLOCK, O_CLOEXEC, O_NOFOLLOW, O_DIRECTORY, O_NOCTTY}`；缺旗标、算出来的旗标、
   混进任一写旗标一律仍判违规，并补了 10 条正反验伪锚。
7. 未碰 `backend/app/**`、未碰 `scripts/vault-install-manifest.json`、未改退出码四档语义。

## 三 请按重要性排序回答的问题

① `O_NONBLOCK` 打开之后、若目标确实是普通文件，从该 fd 用
   `os.fdopen(fd, "r", encoding="utf-8").read()` 读到的字符串，与原先
   `Path.read_text(encoding="utf-8")` 是否**逐字等价**？请特别看：文本换行处理（`newline=None`
   通用换行是否两边一致）、编码错误行为（`UnicodeDecodeError` 是否仍从同一个 `except` 出去）、
   空文件、以及大文件是否会被截断（`.read()` 在 `O_NONBLOCK` 的普通文件上是否可能短读）。

② 形态门是否覆盖了 FIFO 之外的其它非普通文件（字符/块设备、目录、Unix socket、软链指向上述之一）？
   这些输入分别会走到哪一条分支、最终是否都归 `unreadable` 且退出码为 2？有没有哪一类会
   落到「不计退出码」的说明档里？

③ 新测试的 `timeout=60` 取值是否合适：慢机 / 冷启动下会不会误红，缺陷回归时会不会太晚变红？
   另外，回归门在超时那条路上是否可能让 FIFO 残留在临时目录里，进而影响后续测试？

④ **是否存在门未覆盖的路径**，让 FIFO 仍从别的读点进入阻塞 open？请具体看：
   同函数里 main.js 侧的 `main_js_path.read_text(...)`（其前有 `if main_js_kind != "file":` 先 return，
   请判断这道先行形态门是否真的让那一行不可达）、`--source` 侧的读取路径、以及
   `_collect_extra` / `_walk` / `_digest` 这些在 `_check_hotkeys` 之前跑的环节。

⑤ `unreadable` 归桶与 note 文案是否**如实**？也就是「看不见」有没有在任何一条分支上被说成「一致」
   或「查过没问题」？以及 fd 所有权：三条早退路径与 `os.fdopen` 接管之间，有没有漏关或双关 fd 的情形？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
- 一句话结论
- `file:line`
- 一句话说明「在什么输入下会看到这个问题」

没有问题的级别请明确写「无」。结尾给一行 `BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

## 五 边界

- **只读**：不要运行 hook、不要暂存或提交文件、不要连任何数据库或网络服务、不要改动工作树。
- FIFO 相关行为请用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这类说法来描述。
- 不需要评审 `_bmad-output/` 下的文档写作质量，只在它与代码事实矛盾时指出。
