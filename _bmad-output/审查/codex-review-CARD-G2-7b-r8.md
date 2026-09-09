**两步修法挡住了“祖先软链最终指向已登记保护目录”的基本情况，但没有完整保留原禁写判据。§二.5 清单仍不完整。**

以下依据限定文件的静态审查；换行差异另做了纯内存对照。未运行部署或 pytest。两份脚本的 SHA256 与 `mutation-r7-final2` 记录一致。

**BLOCKER：未发现。**

**HIGH**

1. **H-1：先 `realpath` 再判，重新丢掉了沿链 `.git` 保护。**  
   [scripts/cls_forbidden_paths.py:129](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:129)、`:132`：preflight 后出现以下拓扑时：

   ```text
   safe/sub → repo/.git → external/meta
   ```

   `parent` 只剩 `external/meta`；它不在固定保护目标中，也不再含 `.git`，因此 `hits(parent)` 放行，逐级 `O_NOFOLLOW` 随后可以正常打开并写入 Git 元数据目录。原来的 `hits(原路径)` 会通过 walker 拒绝此链。**这不是已声明的“非保护目录”残留，而是新原语丢失了一条现有保护规则。**

2. **H-2：新增 import 产生未登记、未经检查的写入面。**  
   [scripts/deploy-vault.sh:185](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:185)、`:758`、`:799`：字节码缓存缺失或过期、且未从外部禁止缓存时，普通 import 可以写入 `scripts/__pycache__/cls_forbidden_paths.*.pyc`；若 `__pycache__` 指向保护目录，这次写入发生在 `open_pinned` 检查之前。待写清单没有覆盖它。

3. **H-3：`chmod_pinned` 仍能修改保护文件的硬链接。旧洞未闭合。**  
   [scripts/cls_forbidden_paths.py:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:168)、`:170`，调用点 [scripts/deploy-vault.sh:866](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:866)：A4 读取 key 后、B5 调整权限前，若叶子被换成保护文件的硬链接，`O_NOFOLLOW` 会正常打开，随后直接 `fchmod` 修改共享 inode；helper 没有 `fstat/nlink` 拒绝。旧裸 `chmod` 同样存在此洞，不能计作新制造，但必须补入残留清单。

4. **H-4：两处裸 `os.write` 将短写当成功。**  
   [scripts/deploy-vault.sh:776](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:776)、`:829`：空间不足、文件大小限制等条件导致 `os.write` 返回小于请求长度的正数时，代码忽略返回值；文件已被截断，后续 `fsync` 成功仍不能证明全量写入，B3/B4 却可能返回成功。旧缓冲文本写入换成单次底层写入，丢掉了完整写入保障。

**MEDIUM**

1. **M-1：新增了祖先目录必须可读的要求。**  
   [scripts/cls_forbidden_paths.py:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:143)、`:168`：中间祖先为 `0111`、最终目录和文件权限正常时，普通路径访问只需祖先可搜索，新逐级 `O_RDONLY|O_DIRECTORY` 会报 `EACCES`；非 root 对既存 `0200` 文件调用 `chmod_pinned` 也打不开。后者是原语兼容性问题，不能冒称完整部署必然新增失败，因为 A4 等读取可能先拒绝它。

2. **M-2：权限 helper 未限制文件类型。**  
   [scripts/cls_forbidden_paths.py:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:168)：前置检查后，叶子若被换成无 writer 的 FIFO，`O_RDONLY` 可一直阻塞；换成可打开的目录，则会被改成 `0600`、失去搜索权限。socket 的普通 `open` 会失败，不会到达 `fchmod`。

3. **M-3：取消通用换行处理，会删除非 key 配置。**  
   [scripts/deploy-vault.sh:817](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:817)、`:820`：输入包含 `INTERNAL_API_KEY=old\rEXTRA=keep\n` 时，旧文本读取把 `\r` 识别为换行并保留 `EXTRA`；新版只按 `\n` 分割，会把两项一起替换。将这段放在正常的 A3 必填字段之后即可通过 A3。该差异已用纯内存对照确认。

4. **M-4：读取成功之前，已经创建文件或改变权限。**  
   [scripts/deploy-vault.sh:804](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:804)、`:810`：`.env` 在 A3/B1 后被移走时，旧版先读会因 `ENOENT` 失败；新版 `O_CREAT` 创建空文件，最后只写入 key，B4 仍成功，却丢失此前检查过的实例字段。另外，非 UTF-8 输入现在会先改权限、再解码失败；`data.json` 的空文件或解析失败同样存在读取前副作用。

5. **M-5：两个新端到端门可能写回真实源码树。**  
   [backend/tests/unit/test_deploy_vault_sh.py:1597](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1597)、`:1648`：测试把 `frontend` 软链回真实仓库，却没有旧 apply 门的 `main.js` 缺失检查；干净 checkout 缺少该构建产物时，会通过 `deploy-vault.sh:490` 在真实前端目录执行构建，越出测试声称的 `tmp_path` 写入范围，并可能在镜像判据之前失败。

**LOW / 证明边界**

- [scripts/cls_forbidden_paths.py:129](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:129)：直接调用 `open_pinned("file")` 时父目录取 `/`，不是 cwd；现有四个调用点均带目录，因此尚未构成部署入口回归。
- [backend/tests/unit/test_deploy_vault_sh.py:1699](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1699)：现有原语门只测试调用前固定的软链，没有验证①与②之间换链；`:1637` 的镜像“零写”断言只看 mtime，也检测不到单独的权限变化。

你特别问的几项边界，结论如下：

| 维度 | 核对结果 |
|---|---|
| ①与②之间的窗口 | 对已校验的物理路径，尚未打开的段被换成软链，逐级打开会拒绝；已经打开的段随后被换链，后续仍沿旧 fd。没有发现这一机制本身新增的跟链漏洞，但不能覆盖已声明的改名、真目录替换，以及上述 H-1。 |
| 父目录不存在 | ①可能允许尚不存在的安全路径串；②在第一个**仍不存在**的段报 `ENOENT`，不会执行叶子 `O_CREAT`。但 `missing/..` 可能已被 `realpath` 消掉，不能笼统说“原输入缺父目录必然失败”。 |
| 既存叶子为软链 | 当前 `O_CREAT|O_NOFOLLOW`、不带 `O_EXCL` 的调用报 `ELOOP`。外层只判 Python 非零，映射为对应步骤失败；traceback 可见原因，脚本没有按 errno 分类。 |
| 循环依赖 | **未发现**。同模块函数调用与定义顺序没有形成循环依赖。 |
| HOME 枚举与 fail-closed | 每次原语调用重新排序枚举 HOME、stat/解析保护目标，增加重复开销与后半程失败机会；未发现由此新增的确定 fail-open。没有性能实测，也没有保护目标集合稳定性的证明。 |
| 空文件、无尾换行、非 UTF-8 | 内容转换层面，空输入和普通 LF 的无尾换行行为**未发现新差异**；非 UTF-8 两版都会失败，但新版读取前副作用见 M-4。空 `.env` 在正常部署流程中还会先被 A3 拒绝。 |
| 根输入修复、B4 的 nlink 拒绝顺序 | **未发现本轮新增问题**。 |
| Compose 本轮回归、证据中疑似明文密钥 | **未发现**。 |

因此，§二.5 除保留原有项目外，应补上上述缺口，以及“完整输出叶子没有在 `open_pinned` 内重新过判据”的边界：它目前只判父目录，保护目标若在 preflight 后变成输出文件本身，不能据此推导该文件也已复查。

证据确实记录了 14 条 KILLED、探针全绿、八条负控及 H-3 结果；新增五个测试、删除零个也与 diff 一致。不过限定读取面没有提供足以独立重算 `134 passed`、202 个红集 nodeid 同集的原始日志，不能把摘要升级为本次独立复验。

**结论：本轮 BLOCKER 0 条，HIGH 4 条，其中 3 条为本轮新增，1 条为旧洞未闭合。**
