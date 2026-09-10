**`fchmod(fd)` 只关闭了 HIGH-1 的一部分；目前不能判定安全边界闭合。** 当前三份 r6 文件的 Git blob 与指定差异目标一致。以下结论来自只读审查及纯内存源码验证，未运行部署或 pytest。

**BLOCKER：未发现。**

**HIGH-1：祖先路径与实际写入对象仍未绑定，属于遗留问题。**  
[scripts/deploy-vault.sh:795](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:795)：在 A3 后将独立的 `ENV_DIR=/safe/env` 换成指向保护目录的软链，只要保护区里的同名 `.env.course` 是普通、单链接文件，`open` 就会跟随祖先，随后 `fchmod → ftruncate → write` 全部作用于保护对象；在第 783 行读取之后替换，还会把安全文件的旧内容写进保护文件。

这里要区分两件事：B4 对**末段软链、打开时已有多个硬链接**的权限越界确实修掉了；祖先替换导致的内容越界在 r5 的同一写入链中已经存在，不能说是 r6 新引入。

正确方向是从**可信且稳定的目录 fd** 开始，逐级用 `O_DIRECTORY | O_NOFOLLOW` 获取目录句柄，再将叶文件的打开、读取和发布绑定到同一父目录 fd。仅仅先按完整路径打开父目录，再用 `openat`，仍留下取得父 fd 时的祖先问题。合法祖先软链需要明确处理策略；`fstat` 后新增硬链接、目录被改名也需要稳定性前提或权限隔离。若本卡不承担这些，应明确登记为未闭合 HIGH。

同类遗漏还包括 `scripts/deploy-vault.sh:564`、`:841` 的路径式 `chmod`：在对应位置前替换末段，仍可修改保护对象权限。这里合并计入同一 HIGH。

**MEDIUM**

- **新增权限门没有锁住真正的拒绝顺序。** [backend/tests/unit/test_deploy_vault_sh.py:1546](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1546)：把 `fchmod` 移到 `fstat` 后、`if st.st_nlink > 1` 前，既存硬链接会先被改权限再拒写，但整个新门仍通过。已用纯内存变异验证。当前生产代码顺序正确，缺的是防回归能力。

- **根路径本身绕过判据入口。** [scripts/cls_forbidden_paths.py:434](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:434)：输入 `label:/`、`label:////`、`label:/./` 时，`mkdir_p_segments()` 返回空列表，直接走到 `OK`，即使保护目标已经解析成 `/`。这是旧入口漏洞未被本轮根修复覆盖；部署 preflight 的其他非根产出仍会命中根保护，因此这里不升级为部署 BLOCKER。

- **镜像门仍未证明控制流可达。** [backend/tests/unit/test_deploy_vault_sh.py:1515](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1515)：保留现有守卫，再将整个检查块包进 `if false; then … fi`，源码门仍通过，后面的 `sed` 仍可执行。已在内存中验证，变换后的 bash 语法也通过；指定的那条替换变异被杀，不等于这个边界已关闭。

- **全目标扩面的承重性仍未证明。** [scripts/cls_forbidden_paths.py:167](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:167)：若删除这里的全目标检查，第 156 行仍检查 `.claude*`，新增的第二跳用例因此不能隔离这项职责。应补正常可搜索 HOME 下，`.codex → 不可搜索的中间跳 → 外部目标` 这一类行为门。这里没有声称删除后整套测试已实测全绿。

你列出的旧 MEDIUM 也仍需保留：`scripts/deploy-vault.sh:196` 的 nlink 查询退出码及数值边界、`:665` 对 `O'Brien` 等合法值的误处理，以及禁写面对账没有覆盖元数据和写入来源。§二.6 因而**不完整**，至少需要补入上述四项和 HIGH 的完整边界。

**LOW：未发现需要单列的新增缺陷。** 对问题 2—4，边界如下：

- **大目录、FIFO/socket：未发现问题。** `scripts/cls_forbidden_paths.py:117` 的 `stat` 获取元数据，不遍历 `~/Library` 内容，也不打开 FIFO/socket 等待对端。不过 `.claude*` 实际在第 156、167 行各查一次，并非所有目标都只查一次。
- **错误分类：未发现新的安全放行问题。** 第 120 行会把 `ENOTDIR` 也全局拒绝，例如 `$HOME/.config` 是普通文件时，无关的安全输出也被拦。这是明确的保守误拦边界；不能据此把 EACCES、ELOOP、EIO 等直接改为放行。
- **其他目标退化：真实调用链中未发现。** `k()` 会绝对化并规范化目标，空串、`.`、尾斜杠不会原样进入 `under()`；第 101 行的分隔符边界也避免了兄弟目录仅因字符串前缀相同而命中。APFS 完整折叠仍维持原有未证明项。
- **无限循环或指数展开：未发现，前提是系统调用能够返回。** 第 249—262 行保证每次扩展队列都消耗跳数，最多展开 64 次；普通段和大量 `..` 只消耗队列。但第 227 行的 `pop(0)`、保存完整路径及第 434 行起对前缀重复检查，仍可能造成高额时间和内存开销。网络卷调用的耗时也没有上界，旧版 `realpath/lstat` 同样存在这个边界。

指定变异中未发现 r5 那种语法损坏或空期望片段；日志记录的 10/10、探针全绿及还原 SHA 相互吻合。正负控和增量数字也内部一致。但允许读取的材料不含目录级原始输出及完整 nodeid 集，因此不能独立确认并发时序或逐 nodeid 相等；H-3 仍是终态证据。证据中未发现疑似明文真实密钥。

**结论：本轮 BLOCKER 0 条，HIGH 1 条（遗留未闭合，同类越界合并计数）。**


