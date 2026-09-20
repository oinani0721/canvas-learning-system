# 独立复核请求 — CARD-DEBT-10（BATCH-2026-09-18-第十五批）

## ① 背景与最小读取面（请只读下列内容，不要扩大读取面）

仓库树根（下文所有相对路径都相对它）：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy`

被审改动：`git diff 4cc6a78c e64fc5c5 -- . ':(exclude)_bmad-output'`（4 个文件纯新增，0 删除）。

请读：
1. `git --no-pager diff --no-color 4cc6a78c e64fc5c5 -- . ':(exclude)_bmad-output'` —— 本次改动全文
2. `scripts/verify_install_manifest.py` —— 新脚本全文（本次审查的主体）
3. `backend/tests/unit/test_verify_install_manifest.py` —— 新测试全文（它的门）
4. `scripts/vault-install-manifest.json` —— 只看新增的顶层键 `machine_items`（`items` 不在本卡范围）
5. `scripts/verify_vault_install.py` 的 `:79-112`（四档退出码与枚举）、`:274-391`（`load_manifest` 对未知顶层键的容忍）、`:916-961`（`_write_report` 的三道落盘纪律）—— 兄弟校验器，本卡**零改动**，只是被照抄口径
6. `backend/tests/unit/test_vault_install_manifest.py` 的 `:174-184` 与 `:251-270`（两条既有门：copy+skeleton 集合等价、整文件不得含 `/Users/` 且 items 不得带内容基线字段），以及 `:3533` 之后本卡追加的一段
7. `scripts/deploy-vault.sh` `:50-70`（把 `$HOME/Library` 列为禁写保护目标）
8. `scripts/launchd/daily-review-wrapper.sh` `:1-6`（「改动后需重新 cp 安装」那句注释）
9. `scripts/launchd/com.canvas.daily-review.plist` `:12-16`（`ProgramArguments`）
10. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md` `:903-907`（切片原文与完成判据方向）

**这段代码解决什么问题**：这台 Mac 上有 6 件机器级安装副本 —— `~/Library/LaunchAgents/` 下 5 个
`com.canvas.*.plist`，以及 `~/Library/Application Support/CanvasReview/bin/daily-review-wrapper.sh`。
它们当初都是人工 `cp` 进去的，仓库里没有任何东西记着「它们该长什么样」；改了仓内源却忘了重装
= 每日复习链静默停摆（2026-09-05 真的发生过一次）。本卡加一个顶层 `machine_items` 记这 6 件，
加一个只读校验器报 DRIFT，并能对其中 2 件 repo 管理的做幂等重装。

**用户裁定（2026-09-18）**：4 个仓内无 plist 源的件（memory-health / neo4j-backup / qwen-graphiti /
reranker-graphiti）全部登 `external-managed`，**不**收编进 repo，因此本次没有新建任何 `scripts/launchd/*.plist`。

## ② 作者自述 —— 请独立核对，不要采信

1. `verify()` 及其调用链零写。全文件的写调用只在 `_apply_reinstall` / `_write_report` 两个函数体内；
   测试里的 AST 门 `collect_write_call_owners` 数 `ast.Call` 节点来钉住这一点（实测 10 个写调用，
   owner 集合恰 `{_apply_reinstall, _write_report}`）。
2. `--reinstall --dry-run` 零写：除 AST 门外，行为门对 `--home` 整棵树做「相对路径 + sha256 + 权限位 +
   软链目标」全量快照，跑前跑后必须逐项相同。
3. 退出码四档：0 全对 / 1 只缺 / 2 内容漂·读不动·解析不动·程序体不对（与缺并存也取 2）/ 3 用法错。
4. `EXTERNAL-PRESENT` / `EXTERNAL-MISSING` 不计退出码，但必须出现在报告正文与摘要（4 件全丢也要看得见）。
5. `program_source` 按**内容** sha256 比，不按路径字符串比 —— 已装 plist 指向的是另一棵 worktree，
   按路径比会恒判漂移；报告里原样打出它实际指向哪棵树供人读。
6. `--apply` 指向真实 HOME 时必须显式 `--i-confirm-home-write`，且该判定在任何写入之前。
7. 报告落点不得在受管面内（从 manifest 推出来的 `<home>/Library`，加 `<harness>/scripts`），违反即用法错档
   且落点不被创建；落点判定走 `resolve()` 物理解析而非字符串前缀。
8. `source_blob` 用纯 Python 算 git blob id（不 shell out），与真 `git hash-object` 的等价性由测试钉住。

**自报的一处偏离**：卡文原话是「报告落点不得在 `--home` 树内」。字面实现会让本卡自己那条
`--report <仓内 evidence 目录>` 恒判用法错（本仓所有 evidence 落点都在 `/Users/Heishing/` 即 HOME 之下），
两条要求互斥。实现取「不得落在 manifest 声明的安装根内」= 受管面。请判断这个取舍是否让 ⑦ 的保护失效。

## ②-bis 已做过一轮内部对抗复核（5 视角 × 逐条反驳验证，38 提出 / 26 确认 / 12 被反驳）

下列问题已被确认并已在本次提交里整改，每条都配了一个「改之前会绿、改之后才红」的对照输入
（负控存档 `_bmad-output/审查/evidence-debt-10/negctl-{1..6}-*.txt`）。**请不要把篇幅花在
复述它们上面**，但欢迎指出整改本身是否引入了新问题、或者是否只修了一半：

1. 真实 HOME 判定原先是路径字符串比较 → 改 `(st_dev, st_ino)` inode 身份（`/users/x`、
   `/USERS/X`、`/System/Volumes/Data/Users/x` 四种拼法原先全部写穿）。
2. 写入落点原先只查叶子是不是软链 → 增加**物理**包含判定（`<home>/Library` 整个是软链时，
   临时文件与 `os.replace` 都会落在链目标里）。注意：禁止性判定（报告落点）反向取
   「字面 ∪ 物理」的并集，两个方向相反，刻意不共用谓词 —— 请核这个不对称是否写反了。
3. `install` 余段未要求相对 → `~//Library/x` 的余段是绝对路径，`home / "/Library/x"` 在
   pathlib 里丢掉左操作数。现在 load 期拒绝，`expand_install` 再做一次包含断言。
4. AST 零写门：绑定形态 `p.open("w")` 的 mode 在 `args[0]` 而不是 `args[1]`（原写法让
   `Path.open` 整族漏报）；`*args` / `**kwargs` 判不出 mode 时保守判为写；认 import 改名；
   owner 改**限定名**（防内层同名函数顶替白名单）；补 `kw_defaults` 等非 body 子树。
5. apply 复制方向原先没有任何断言锁住（`MATCH` 是对称相等，方向写反时状态字符串一样）→
   增加「harness 整树零改动」+「安装副本等于事先取下的源字节」。
6. 读之前先问是不是普通文件（无写端 FIFO 会让 `read_bytes()` 在内核里永久阻塞）。
7. `ProgramArguments` 解析改按 launchd 真实规则（`Program` 优先），相对路径归
   `PROGRAM-DANGLING` 而不拿进程 cwd 补全；写路径上的 `OSError` 归 `EXIT_MISMATCH`。
8. 重复 `install` 按规范化后的路径去重；NUL / 不可编码值归 manifest 错档。

## ②-ter 第一轮（绑定 `390f25cf`）的 4 HIGH + 6 MEDIUM —— 全部采纳并已整改

本轮请**重点核这些整改本身**：是否修对了、是否只修了一半、是否引入了新问题。

| r1 | 整改 | 对照输入 |
|---|---|---|
| H1 零写门是**调用点**判据，对「`verify()` 里加一行 `_write_report(...)`」无感 | 新增**调用图可达性**门 `writers_reachable_from()`：从 `verify` / `_verify_one` / `_verify_program` / `plan_reinstall` 四个只读入口出发，沿调用图不许走到两个写者。owner 改带 kind 前缀的限定名（`def:` / `class:`），堵住「模块级 `class _write_report:`」与「内层同名 def」两个洞。词表补 `io.FileIO` / `builtins.open` 别名 / 变量别名 | 负控⑨：植入后**调用点门 `owners - allowed = []`（看不见）**，调用图门报 `['_write_report']` |
| H2 报告落点门对大小写别名未拦下，会覆盖仓内 plist 源 | 包含判定补 inode 身份，且必须**逐级**祖先比对 —— 别名路径自身 `lexists` 为真，只比第一个存在的祖先等于拿文件比目录，恒不相等 | 负控⑧ + `test_report_guard_is_not_fooled_by_a_case_alias`（断言仓内 plist 字节未变） |
| H3 确认门只问「`--home` 是不是家目录」，`--home /` 配 `~/Users/<user>/…` 可写真机 | 改问「**这次要写的地方**在不在真实 HOME 里」：apply 前逐条把 `expand_install` 的结果与 `Path.home()` 做物理包含判定 | 负控⑦ + `test_confirmation_is_keyed_on_the_write_target_not_on_home_spelling`（用真机安装路径，断言在写之前被拦下且真机 sha 未变） |
| H4 报告原样回显 `ProgramArguments` 泄漏凭据 | `NAME=VALUE` 一律脱敏；出错只描述**形状**（元素个数 + 类型）不回显内容；`env` 形态跳过环境赋值再取程序路径 | `test_report_never_echoes_credentials_from_a_plist` |
| M5 `lexists` 把 EACCES/ENOTDIR 吞成 False，把「读不动=2」降成「缺失=1」 | 改 `os.lstat` 分档：`FileNotFoundError` → 不在；其它 `OSError`/`ValueError` → UNREADABLE（阻断）。external 件同样按此处理（豁免只覆盖「仓库不保管它的内容」，不覆盖「整块目录读不动」） | `test_untraversable_install_dir_is_unreadable_not_missing` |
| M6 包含检查与写入之间的软链竞态 | 父目录 `open(O_DIRECTORY)` 后核对 `(st_dev, st_ino)` 与刚检查过的那个目录一致，之后全部走 `dir_fd=` / `os.fchmod(fd)`，**不再有任何一次按路径的解析**。残余窗口在 docstring 如实声明（macOS 无 `openat2(RESOLVE_BENEATH)`） | 见 `_apply_reinstall` docstring |
| M7 解释器不存在仍判 PROGRAM-MATCH | `_resolve_program_target` 额外返回解释器路径，`_verify_program` 先查它在不在 | `test_missing_interpreter_is_dangling_not_match` |
| M8 binary plist 里带 NUL 的路径让 `os.stat` 抛 `ValueError` 裸穿 | `_presence` / `_regular_file_problem` / `_read_bytes` / `_apply_reinstall` 一并捕 `ValueError` | `test_nul_in_a_plist_program_path_stays_inside_the_four_exit_codes` |
| M9 程序体状态比**值集合**，少三条 label 照样绿 | 改比整个字典（5 条 label 逐条钉死） | 生产代码限制成只查两件时该断言必红 |
| M10 快照漏掉目录软链的指向 | `dirnames` 里的软链记 `dirlink -> target` | `test_tree_snapshot_notices_a_retargeted_directory_symlink` |

**请特别核这两处不对称，它们是我刻意写成相反方向的**：
- 禁止性判定（报告落点）取「字面 ∪ 物理 ∪ inode」的**并集**（保守多禁）；
  允许性判定（写入落点）只取**物理**包含（保守少放）。共用一个谓词会让其中一侧反过来。
- `EXTERNAL-*` 不计退出码，但「external 件所在目录读不动」归 UNREADABLE（计退出码）——
  豁免的是「仓库不保管它的内容」，不是「它的任何问题都不报」。

## ③ 请按重要性回答的问题

0. **零写是否真被锁住**：AST 门的检测清单（`WRITE_DOTTED` / `WRITE_METHODS` / `open()` 的 mode 判定）
   是否够宽？一个现实的实现能不能一边写文件一边让门保持绿（别名导入、间接调用、`tempfile`、
   `io.open`、把写委托给两个允许函数之外定义的被调方）？`collect_write_call_owners` 的 owner 归属遍历
   会不会把调用记到错误的外层函数上（嵌套函数、推导式、lambda、类体、try/except/with 体）？
1. **DRIFT 判定能否被 MISSING / UNREADABLE 混成 MATCH**：「读不到」是否确实计阻断？
   `ItemResult` 的默认 status、external 分支里读失败但仍报 `EXTERNAL-PRESENT` 的路径，是否会让
   两种不同处境在报告里长得一样？
2. **`--apply` 的写路径**：`O_EXCL` + `os.replace` 是否防半写？安装副本是软链时会不会沿链写到别处
   （注意 `is_symlink()` 检查与 `os.replace` 之间的时间差）？`--i-confirm-home-write` 是否真拦得住真实 HOME
   （`--home` 能否写成解析后等于真实 home 但比较不相等的形式：尾斜杠、软链、`~`、相对路径、
   大小写不敏感文件系统、`/tmp` 与 `/private/tmp`）？多件计划中途失败会不会留下半更新的树而无信号？
3. **原地执行的程序体按内容比**：会不会让「plist 指向一棵陈旧的树里的旧版本」漏报？
   `harness` 侧源缺失与已装程序体缺失，在报告里是否可区分？`ProgramArguments[1]` 是相对路径 /
   含 `~` / 软链 / 目录 / 设备文件时各走哪条分支？
4. **external 条目不计退出码**是否会让「4 个 plist 全丢」在实际使用中静默？摘要里那行警示够不够？
5. **报告是否泄漏凭据**：plist 里含绝对路径可接受，但不得含任何密钥内容。
6. **门是否名实相符**：`test_verify_install_manifest.py` 里有没有哪条测试，在它声称覆盖的代码发生
   现实的回归之后仍然会保持绿？特别注意 `_statuses()` / `_program_statuses()` 这两个解析器
   —— 若它们静默返回空字典，某些字典相等断言会变成空对空。

## ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` 和一句复现思路（具体输入或文件系统状态
→ 错误的输出 / 退出码 / 写入）。不要报风格偏好、命名口味、缺类型标注、「建议加注释」这类。
描述测试覆盖问题时请用这些说法：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。

## ⑤ 边界（这些不在本次审查范围，请不要在它们上面花篇幅）

- 本卡只读真实 `~/Library/**`，不写；真机 `--apply` 未执行（需用户当次授权）。
- 不连任何数据库。
- 不评这 4 份 plist 的语义（`KeepAlive` / 触发时刻 / `PATH` 是否合理）。
- 不评 `launchctl` 重载步骤（本脚本刻意不调用它，重载是人的动作，已登记移交）。
- 不评 `scripts/verify_vault_install.py` 自身的逻辑（本卡零改动）与它的零写门重设计（另一张卡）。
- 不评 `scripts/vault-install-manifest.json` 的 `items`（G2-6 的面，本卡一字未动）。
