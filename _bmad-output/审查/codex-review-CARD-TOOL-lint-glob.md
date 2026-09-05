**glob 改写在 Lefthook 2.1.6 下成立；`b20fe550` 可完整重现为纯格式化输出。残留扫描门存在确定的漏检和失败放行，不能按“新增行含标记必阻断”验收。**

审查绑定 `304f03ca..b20fe550`。全程只读，未运行完整 hook、变异 harness 或脚本运行时测试。以下位置均指最终提交的 [lefthook.yml](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/lefthook.yml) 和 [ruff.toml](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/ruff.toml)。

1. **MEDIUM｜`lefthook.yml:259–271,284`｜扫描失败可能报告 OK。**
   - **问题：** 两次 Git 调用及 awk 的失败没有可靠传递到最终退出码。
   - **判断依据：** Lefthook 2.1.6 使用裸 `sh -c`。只读探针让 Git 读取无效 index，Git 报错，但原结构管道返回 **0**；无扫描结果时，代码仍会走到最后的 OK。管道中的 `while` 本身没有变量丢失问题，因为结果通过文件传递。[固定版本执行源码](https://github.com/evilmartians/lefthook/blob/v2.1.6/internal/run/controller/exec/exec_unix.go#L77)
   - **建议处置：** 显式检查 Git、解析器及结果收集的失败，区分“未发现标记”和“未完成扫描”；仅加 `set -e` 不足以检查管道前段失败。

2. **MEDIUM｜`lefthook.yml:259–267`｜部分合法文件名会漏扫。**
   - **问题：** `core.quotepath=false` 不等于输出原始路径。
   - **判断依据：** 普通空格、中文可以正确处理；双引号、反斜杠、TAB、换行仍被 Git 引用和转义。`read -r` 保留这些引用文本，后续 `git diff -- "$f"` 收到错误路径，可返回空 diff 和成功状态。当前 tracked 树未发现此类特殊文件名。[Git 路径引用规则](https://git-scm.com/docs/git-config#Documentation/git-config.txt-corequotePath)
   - **建议处置：** 使用 `-z` 和 NUL 分隔解析，并按字面路径查询；`--` 只终止选项，不关闭 Git pathspec 通配和魔法语法。普通规范路径下，`_bmad-output/*` 的 `case` 能跨目录匹配；特殊路径引用会破坏这一判断。

3. **MEDIUM｜`lefthook.yml:269–270`｜以 `++` 开头的新增正文被误当成文件头。**
   - **问题：** `/^\+\+\+/ { next }` 没有区分文件头和 hunk 正文。
   - **判断依据：** 原 awk 输入 `@@ -0,0 +1 @@` 后接 `+++MUTANT`，输出为空：实际新增的 `++MUTANT` 被漏掉。再接一行普通标记时，报告第 **1** 行，实际是第 **2** 行。
   - **建议处置：** 按 hunk 状态识别文件头并维护行号。正常无逗号 hunk、多 hunk、纯删除 hunk 的探针均正确，问题集中在正文误分类。

4. **MEDIUM｜`lefthook.yml:266–270`｜diff 输出受用户配置影响，可使扫描失效。**
   - **问题：** 没有固定无颜色的机器解析格式。
   - **判断依据：** 对相同提交 diff 使用原 awk、以 `MARKER` 为探针：`color.ui=never` 命中 **2** 行，`color.ui=always` 命中 **0** 行，Git 均返回成功。颜色转义使行首匹配失效。另外，合并 hunk 后出现上下文行时，当前算法不递增这些行的行号。[Git diff 输出选项](https://git-scm.com/docs/git-diff)
   - **建议处置：** 固定 `--no-color` 等解析所需选项；明确处理上下文行，或固定不合并相邻 hunk。

5. **MEDIUM｜`lefthook.yml:259,266`｜重命名并修改的文件不在扫描保证内。**
   - **问题：** `--diff-filter=AM` 排除 `R`、`T` 等变更类型。
   - **判断依据：** 文件重命名同时新增标记，若被 Git 分类为 `R`，第一步文件枚举就不会返回它。因此“暂存新增行含标记即阻断”比实现宽。[Git 类型过滤定义](https://git-scm.com/docs/git-diff)
   - **建议处置：** 明确覆盖类型；可关闭重命名检测后扫描 A/M，或正确处理重命名目标，并补对应验收。

6. **MEDIUM｜`lefthook.yml:254`，关联 `:60,:71`｜扫描不是最终暂存区检查。**
   - **问题：** YAML 放在末尾不保证最后执行。
   - **判断依据：** 2.1.6 对未设 priority 的 commands 按名称排序，`mutant-residue-scan` 在两个 `spec-sync` **之前**，后者随后执行 `git add backend/openapi.json`。`parallel:true` 下还会出现扫描与 index 写入交错。[固定版本排序源码](https://github.com/evilmartians/lefthook/blob/v2.1.6/internal/config/command.go#L52)
   - **建议处置：** 明确安排在所有 index 写入之后；若声明检查最终暂存内容，还需确保扫描期间及之后没有其他写入。不同 hook shell 的 PID 通常不同，不能简单把并行问题归因为临时文件同名。

7. **MEDIUM，条件性安全风险｜`lefthook.yml:257–258`｜临时文件创建可能截断非预期文件。**
   - **问题：** 可预测路径配合 `: > "$TMP"`，没有排他创建或拒绝符号链接。
   - **判断依据：** 若其他主体能够在临时目录预置匹配 PID 的符号链接，且系统允许跟随，重定向会以 hook 用户权限截断目标。**当前会话 TMPDIR 实测为本人拥有的 `0700` 私有目录，不能据此声称当前机器已可跨用户利用。**
   - **建议处置：** 使用安全排他创建的临时文件，检查创建结果并设置退出清理。**需要额外证据：** 回退 `/tmp` 等部署环境的目录权限及系统符号链接保护，才能判断当地可利用性。

8. **MEDIUM｜`ruff.toml:24–30`｜提高目标版本的依据不实。**
   - **问题：** “py39 是无依据缺省”“scripts 全部由该 venv 执行”均不成立。
   - **判断依据：** Ruff 0.15.9 自述默认版本是 **py310**；旧 py39 有根 `pyproject.toml:6` 的 `requires-python = ">=3.9"` 推断依据。CI 在 `.github/workflows/api-spec-sync.yml:50,83` 明确使用 **3.11** 执行脚本，`package.json:13` 也使用 PATH 中的 `python`。[Ruff 版本推断规则](https://docs.astral.sh/ruff/configuration/#inferring-the-python-version)
   - **建议处置：** 修正文案，明确最低支持版本，必要时局部覆盖。**需要额外证据：** 放弃旧版本支持的批准要求及对应解释器验收。当前格式化没有新增 Ruff 的 py311 语法诊断，不能宣称已经破坏 CI。

9. **LOW｜`lefthook.yml:109`｜F821 示例行号过期。**
   - **问题：** 注释仍引用 `:402`。
   - **判断依据：** 最终提交中 `{technology}` 位于 `scripts/validate-source-citations.py:392`；现行配置不报，显式选择 F821 后确实报该处未定义名。
   - **建议处置：** 更新行号或引用稳定的函数／表达式。主体声明属实。

对五项自称的逐项判断如下：

| 自称 | 判断 |
|---|---|
| **1．glob 正确** | **成立，限当前 2.1.6 默认引擎。** 单 `*` 跨目录；漏一级文件实际来自额外的字面 `/`。echo 能证明 run 开始，单文件隔离探针可证明触发，但不能证明 Ruff 参数完整或检查通过。两个阴性样本不足以证明所有边界。引擎还会忽略大小写，匹配三个根下隐藏目录、vendor、fixture 等所有 staged `.py`；若这就是目标，不算过宽。`src` 当前无害，“恒空集”应改为“本 SHA 下为空”。[固定版本过滤源码](https://raw.githubusercontent.com/evilmartians/lefthook/v2.1.6/internal/run/controller/filter/filter.go) |
| **2．配置口径** | **部分成立。** 全部 **185/185** 个 backend 外 tracked Python 文件解析根配置，包含 scripts 91 和其余 94；手动 Ruff 也受影响。backend 保持自己的 **120/py39**，不会与根配置合并。120 对齐已有声明，根注释也披露了 91+94；是否超出批准范围，**需要原卡授权范围**，不能仅凭行宽变化判定越界。 |
| **3．残留门** | **部分成立。** 无 glob、标记拼接和普通新增行阻断逻辑成立；上述漏检、失败状态和执行顺序使完整保证不成立。 |
| **4．诚实性** | **部分成立。** `845 / 91 / 49 / 2 / 0`、其余94，以及两 harness 的 **153／10** 处标记、lefthook 的 **0** 处字面标记均吻合；**83→86** 也重现。无标记残留确实抓不到。SHA 比较只能证明纳入集合的文件与跑前一致，不能证明跑前已干净；历史“三裁判全绿”等事件仍需当轮日志，当前源码注释不是独立证明。 |
| **5．纯格式化** | **成立，证据强于抽查。** 86 个父提交文件经 Ruff 0.15.9 重放，**86/86 与最终 blob 逐字节一致**；包含字符串和 type comments、忽略位置的 AST **86/86 一致**，无文件增删或权限变化。全部91文件在三个提交的内存编译结果均 **90成功／1失败**，失败恒为 dashboard 第120行。运行时未验证。 |

另有一个明确验收边界：仓库 `package-lock.json:1490` 锁定 Lefthook **1.13.6**，本机验证使用 **2.1.6**；要覆盖标准依赖安装路径，仍需该版本下的同一矩阵证据。

**有条件性的数据丢失／安全风险：临时文件创建可能在上述共享目录与符号链接条件下越权截断目标；未发现已经发生的数据丢失或越权写入证据。**


