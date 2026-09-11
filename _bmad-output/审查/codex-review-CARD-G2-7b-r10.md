本轮发现 **1 项新增 HIGH、1 项旧遗漏 HIGH**，暂不能维持“新引入 = 0”的判断。以下依据限定文件静态核对及纯内存解析片段对照，未运行部署或测试套件。

**BLOCKER：未发现。**

**HIGH：两项，必须本卡处理。**

1. **新增：npm 的实际写入路径没有完整过判据。** [scripts/deploy-vault.sh:511](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:511)：当 `--apply` 触发 build，合法 evidence 下若预置 `npm-$TS → 保护目录`，第 512 行的 `mkdir -p` 就会向保护目录创建 `cache/logs`，**无需竞争窗口，也无需推断 npm 实现**；这些新增子路径不在第 392 行的待写清单中。

   同一入口还有相对路径问题：`--evidence-dir evidence` 获准，但第 512 行按调用目录创建，第 514–516 行进入插件目录后再把相同的相对字符串交给 npm，检查、创建与使用的落点分裂。此项修复必须同时覆盖**新增子路径检查和路径基准固定**；不能归入“npm 完整写入集合尚未证明”转卡。

2. **旧遗漏：here-document 仍会先于 TMPDIR 检查写临时文件。** [scripts/deploy-vault.sh:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:186)：在题定 Bash 3.2 下，`TMPDIR` 指向保护目录时，步骤 2 经第 605 行调用 `pinned_chmod600` 的 `<< 'PYCHMOD'` 就会产生临时写入；步骤 3 第 783、829 行同类。

   唯一 TMPDIR 检查在第 958 行，已经太晚，默认端口 8011 还完全跳过。删掉 `<<<` 修好了 preflight 前的那条路径，但没有闭合这一条；它也不属于已登记的六处显式重定向竞争窗口。

**MEDIUM：未发现本轮新增。**

**LOW：可转卡。**

- **混合空白兼容回归。** [scripts/deploy-vault.sh:278](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:278)：分四轮剥空格、tab，遇到 `$'\t claude \t'` 时，删除 tab 后留下的空格不会再处理，旧版接受、新版拒绝。
- **长空白输入明显变慢。** 同处逐字符删除反复复制字符串，具有二次复杂度；仅解析片段中，10,000 个前缀空格旧约 0.007 秒、新约 2.64 秒。长逗号列表反复截取 `_rest` 也有累计复制成本。
- **零进度行为门缺少超时兜底。** [test_deploy_vault_sh.py:1798](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1798)：若以后删除 `write_all` 的 `n <= 0` 拒绝分支，该测试会无限循环；这是门的健壮性问题，当前实现正常。

`--hosts` 的对照结果如下；**rc 只代表解析片段**：

| 输入 | 旧 → 新 |
|---|---|
| `,`、`,,`、`claude,,claude,` | 0 → 0 |
| 仅空格、仅 tab | 0 → 0 |
| `$'\t \t'`、`$'\t claude \t'` | 0 → 64 |
| `cla ude`、`$'claude\r'` | 0 → 64 |
| `$'claude\ncodex'` | 0 → 64 |
| 空字符串 | 1 → 0 |
| `%`、`#`、`*` | 64 → 64 |

旧版 `tr` 删除字段内全部空白，`read` 只读取第一行；新版保留这些字符，所以不完全等价。空字符串旧版在 Bash 3.2 空数组展开时触发 `set -u`。展开元字符只是变量值，**未发现二次展开、glob 注入或宿主校验绕过**。

其余重点核对：

- **ForbiddenPath：未发现新问题。** [cls_forbidden_paths.py:194](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:194) 正确区分判据拒绝与内核 EACCES。允许读取的生产代码中，没有仍执行的 `except PermissionError` 调用点；测试第 1726 行按父类接收异常，仍兼容子类。
- **`os.write` 顺序依赖：未发现。** [test_deploy_vault_sh.py:1777](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1777) 确实替换进程共享的 `os.write`，但两条测试均在 `finally` 恢复，之后才关闭文件、执行断言。补丁期间其他线程可能受影响，当前读取面未见该并发条件。假推进会被完整字节断言抓住。

npm 配置层之外，第 519 行启动的构建进程仍有这些边界：

- `build` 及启用的 `prebuild/postbuild` 可以自行写文件；`npm run build` **不意味着自动执行依赖的 `postinstall`**，但构建脚本若再调用安装命令则另当别论。
- Node 的覆盖率输出，以及版本支持且开启的编译缓存，例如 `NODE_V8_COVERAGE`、`NODE_COMPILE_CACHE`，有独立路径设置。
- 构建脚本或 esbuild 若使用临时文件，其临时目录、构建输出目录不会因 npm cache/logs 配置而自动受检。未读取对应实现，不能断言本次具体触发了哪些路径。

§二.8 已列项目，未发现新的证据要求本轮提前处理；漏列的必修项是上述 here-document 临时写入。证据摘要无法独立重算失败正文、红集和事件归属，继续按已登记 M-5 处理，未重复计为新问题；允许读取的证据中**未发现疑似明文密钥**。

结论：本轮 **BLOCKER 0、HIGH 2（新增 1、旧遗漏 1）**；本卡尚不可收敛，必须处理上述两项 HIGH。
