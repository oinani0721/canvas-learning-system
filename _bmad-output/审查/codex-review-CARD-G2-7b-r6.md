**仍有两处禁写面漏拦，以及写前 `chmod` 引入的一处回归。**以下区分新增问题与未闭合的旧问题。验证限于允许文件、纯内存模型和 shell 片段；没有运行部署或重跑 pytest。

**BLOCKER**

1. **B-3 未闭合：第一跳可读仍不代表整条目标链可解析。**  
   [scripts/cls_forbidden_paths.py:120](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:120)：当 `.claude-cache → /opaque/hop → /external/protected`，HOME 正常但 `/opaque` 不可搜索时，第一跳 `readlink` 成功，`:130` 的非严格 realpath 却只登记 `/opaque/hop`，且 `enumerate_failed=False`；直接指定 `/external/protected/x` 被放行。当前源码的内存模型结果为 `rc=0 / OK`。这是整改遗漏，**不是职责拆分新增的回归**。

2. **保护目标为根目录时，两条轴共同漏拦。**  
   [scripts/cls_forbidden_paths.py:331](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:331)：当现有 `.claude-cache → /`，`tk + os.sep` 变成 `"//"`，普通 `/safe/out` 不满足后代比较；`:231` 同样如此，walker 又没有记录初始根。内存模型同样返回 `rc=0 / OK`。这是**既有但未列出的漏洞**。

**HIGH**

1. **写前 `chmod` 在链接检查之前修改保护对象。**  
   [scripts/deploy-vault.sh:777](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:777)：如果 `.env.<vault>` 在 A3 校验结束后、B4 开始前被替换成保护文件的有效软链或硬链接，`chmod 600` 会先改变保护对象权限，随后 `:795` 的 `O_NOFOLLOW`／`:797` 的链接数检查才拒绝。旧版会在这些检查拒绝后退出；**这是新增的元数据越界写**，不能归入已披露的 `fstat↔ftruncate` 窗口。内容 SHA 和 `find -newermt` 也检测不到这类权限修改。

**MEDIUM**

1. **256 限制会误拒合法浅路径。**  
   [scripts/cls_forbidden_paths.py:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:186)：计数发生在忽略空段、`.` 之前，相对软链还会重新消耗祖先路径预算；例如 `"/" + "./"*256 + "safe/out"` 实际只是 `/safe/out`、没有软链，当前 CLI 模型仍返回超限 HIT。它限制的是处理段数，**不是软链跳数**。这是本轮新增误拦。

2. **H-2 的变异制造了语法错误，现有用例仍被另一分支兜底。**  
   [mutate_r5.py:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-g27b/mutate_r5.py:63)：替换产生 `*) : ;`，缺少 `;;`，内存语法检查得到 rc 2。即使改成合法回退，[test_deploy_vault_sh.py:1893](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1893) 只测的 `relcourse` 仍被 `deploy-vault.sh:314` 拦成 rc 64，消息也含“绝对路径”；多段相对输入 `parent/course` 才能揭示入口检查被删除。**这条 KILLED 不能证明入口门承重。**

3. **H-3 没有核定声称的断言失败。**  
   [mutate_r5.py:81](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-g27b/mutate_r5.py:81)：失败片段为空，`:114` 因而直接取 True；该变异先让测试 `:1534` 的 `.index()` 抛出 `ValueError`，到不了顺序断言。因此“七条都核定指定断言变红”不成立。

4. **镜像源码门仍允许整个检查块不可达。**  
   [test_deploy_vault_sh.py:1512](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1512)：把 `deploy-vault.sh:911` 的外层条件改成 `if false; then`，内层直接条件保持原样，判据与复查全部跳过、后续 sed 照常执行，但该节点的源码断言仍全部成立。把数组元素替换成镜像根也未被绑定。因此原 M-2 的第三处只能算**局部加强**。

5. **`ancestor_symlink_hits` 独立承重尚未证明。**  
   [scripts/cls_forbidden_paths.py:251](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:251)：允许证据里的七条变异没有删除或失效这个函数，只有删除 `hits()` 对 `chain_hits` 的调用；不能据此认定“两轴各自承重”。这不等于已证明该函数冗余或拆分漏拦。

你已登记的旧 MEDIUM 不重复编号；**§二.3 清单不完整**，至少需要补入上述遗漏与证据缺口。

**LOW：未发现独立问题。**

其余问题逐项结论：

- **逐段核心顺序：未发现问题。**相对目标以链所在目录为基准、绝对目标从根重启、解链之后处理 `..` 都正确；根处 `dirname` 不会越过 `/`。
- **拆分导致的新漏拦：未发现。**在稳定、可解析且未超限的普通路径上，未找到原并集因拆分而丢失的反例；上述两个 BLOCKER 来自共享目标构建／比较。
- **B-1 双前缀：未发现新误拦。**多跳 HOME、词法与物理 HOME 互为前缀、HOME 自身以 `.claude` 结尾，都保留了拼接目录边界。
- **H-2 当前实现、H-3 普通不可写文件、B-4 数组：未发现额外回归。**绝对路径 gate 与父目录不变量一致；chmod 失败会返回 73；本机 bash 3.2.57 的空数组计数保护实测正常。
- **完整 namei 等价仍未证明。**`:192` 忽略 `.`、空段及尾斜杠，`:202–212` 不区分部分解析错误，因此 `普通文件/.`、`普通文件/..`、`普通文件/` 的成败语义与内核不同；未找到这些差异造成的静态越界写。连续斜杠在 CLI 层会被消去；跨挂载入口的对象等价、完整 APFS Unicode 折叠仍未证明。异常空 `readlink` 返回值也没有 fail-closed 分支，但未建立普通有效软链下的可达输入。

存档确实记录了 311 passed、九条负控及镜像控制组，两脚本当前 SHA 也与变异还原记录一致；这些不弥补上述变异缺陷。允许证据中未发现疑似真实明文密钥。

**本轮 BLOCKER 2 条，HIGH 1 条。**
