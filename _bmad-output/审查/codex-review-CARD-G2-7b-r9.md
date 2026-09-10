**四条 HIGH 修复中，未发现 r8 新引入的 HIGH；但 0200 回退没有修成，另发现一条旧的禁写面遗漏。** 本次未运行部署、变异或文件测试；仅做了只读检查和纯内存验证。

**BLOCKER：未发现。**

**HIGH**

- **H-1｜旧遗漏：shell 临时写入早于禁写检查。** [deploy-vault.sh:268](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:268)：**由 Bash 3.2 执行、`TMPDIR` 指向可写保护目录时**，`<<< "$HOSTS"` 会创建并写入临时文件，发生在 preflight 之前，dry-run 同样经过这里；随后删除文件不能撤销这次写入。`:933` 的 TMPDIR 检查来得太晚，而且只覆盖非 8011 的镜像分支。这是版本条件明确的静态反例，本轮没有运行写入探针；不能外推为所有 Bash 版本都如此。

**MEDIUM**

- **M-1｜r8 修复未生效。** [cls_forbidden_paths.py:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:184)：非 root 打开普通 `0200` 文件产生的 `EACCES` 本身就是 `PermissionError`，先被这里重新抛出，因此 `:189` 的 `O_WRONLY` 回退不可达。纯内存验证了异常类型；这是旧兼容性问题仍在，不是新增运行回归。
- **M-2｜新增原语的行为门不足。** [test_deploy_vault_sh.py:1231](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1231)：若把 `write_all` 的推进改成 `view = view[len(view):]`，短写会再次被当成功，而这里仍满足字符串断言；[mutate_r6.py:170](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-g27b/mutate_r6.py:170) 只验证“调用退回裸 `os.write`”会被抓住。此外，`:129` 的**叶子** `O_NOFOLLOW` 变异不能证明**祖先逐级打开**承重。18/18 的记录成立，但不能承担这些额外结论。
- **M-3｜r5 存量仍在。** [deploy-vault.sh:212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:212)：链接数命令输出数字后非零退出，或输出 `0`／超出 shell 整数范围的值时，现有检查仍未完整处理。
- **M-4｜r5 存量仍在。** [deploy-vault.sh:681](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:681)：合法父路径含 `O'Brien` 时，删除值内全部引号会改变路径，导致 A3 误拒。
- **M-5｜既存证据边界仍在。** [dir-red-close-r8fix.txt:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-g27b/dir-red-close-r8fix.txt:5)：不同失败原因可以产生相同 nodeid 集合，mtime 非零项也不能仅凭代码没有引用就确定写者；允许文件只有对账摘要，无法独立重算原始红集或事件归属。

**LOW：未发现新的确定问题。**

其余重点逐项判断：

| 维度 | 判断 |
|---|---|
| `hits(path) or hits(parent)` | **未发现回归。** `hits(path)` 抛异常时，尚未到首次 `os.open`，异常传播为失败，不会转成放行。 |
| 叶子自身是 `.env` | **未发现回归。** `skip_env_name=True` 会跳过叶名规则，符合 outputs 口径；CLI 的 strict 参数检查仍保留。叶子软链另由 `O_NOFOLLOW` 拒绝。 |
| `write_all` 的 EINTR／EAGAIN | **未发现假成功。** Python 通常自动重试未被异常信号处理器打断的 EINTR；实际异常继续上抛。两处内容写入使用 `O_RDWR`，没有 `O_NONBLOCK`，后者只用于 chmod。失败可能留下部分内容，仍属非事务边界。 |
| 去掉 `O_CREAT` | **未发现首次部署必然 ENOENT。** env 在 `:596` seed，`:720` 再保底；data.json 在 `:652` 通过存在性检查后才到 `:769`。文件随后被移走而失败，符合整改目标。 |
| `O_WRONLY` 与第二次检查 | **未发现截断或新增保护面绕过。** 没有 `O_TRUNC`；修正异常分支后，第二次调用仍重新执行完整判据。目前该回退尚不可达。 |
| 通用换行 | **未发现有效 UTF-8 输入反例。** 在相同后处理、macOS/POSIX 写回口径下，先合并字节再 CRLF→LF、CR→LF，等价于文本读取的 `newline=None`。3,280 组纯内存组合对照全部相等；这不是对历史整段实现的穷尽回归证明。 |
| 五处 `container_name` | **未发现本轮相关回归。** |
| 指定证据中的明文密钥 | **未发现。** |

`PYTHONDONTWRITEBYTECODE=1` **足以关闭所展示 Python 调用的普通 import 字节码写入，但不足以证明所有子工具零缓存写入**。它位于这些调用之前，双向证据支持该 `.pyc` 路径的修复；它不约束显式编译、导入代码自身的其它写入或 npm。

因此，§二.5 还应补上以下边界：

- [deploy-vault.sh:494](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:494) 的构建分支没有约束 npm 日志／缓存目录。日志开启且相关配置指向保护目录时存在额外写入路径；本轮未读取 npm 实现及构建配置，**完整写入集合未证明**。
- `chmod_pinned` 的非普通文件限制没有覆盖 B3/B4 内容写入：前置检查后若叶子被换成 FIFO，仍可能阻塞；这是旧路径边界。
- 错误后的部分写入、三文件不一致与整脚本重跑不能自动恢复，仍需登记到 adopt／恢复卡。
- `NFC + lower` 与 APFS 完整 Unicode 等价规则未证明，源码也已承认这一点。

**本卡必须处理：** Bash 临时写入遗漏、无效的 EACCES 回退，以及短写推进的行为验证；npm 构建分支也应补证或明确限制受支持配置，才能继续承诺禁写面零写。性能、完整 namei／Unicode 等价、目录并发稳定性和事务恢复可以登记下一卡，无需再次重塑判据。

**结论：本轮 BLOCKER 0 条、HIGH 1 条；该 HIGH 属于旧遗漏，r8 新引入 HIGH 0 条。**
