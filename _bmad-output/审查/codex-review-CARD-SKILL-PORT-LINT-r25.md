复核绑定 **`cb4fa9f8`**；被测文件 blob 与提交一致。旧版由许可 diff 在内存重建。未修改文件、运行 pytest 或访问网络／数据库。

**确认 4 条“`e22c6d27` 能抓、`cb4fa9f8` 漏掉”的新回归，另有两类整改未闭合。**

**BLOCKER：未发现。**

**HIGH：6 条。**

1. **新回归——[test_skill_portability_lint.py:1597](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1597)：重定向扫描没有使用引号掩码，普通参数可以让真实 Python 执行区消失。**

   ```sh
   python3 - <<'A' '<not-a-file'
   P = "/t" + "mp/cls-exam/x"
   P = "/etc/passwd"
   A
   ```

   `'<not-a-file'` 是普通 argv，stdin 仍来自 A；新版却将其记成 `<file`，覆盖 fd 0。公开动态判据：**旧版命中第 4 行，新版 `[]`**。

2. **新回归——[test_skill_portability_lint.py:1529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1529)：只检查 `body.startswith("c")`，丢掉合法组合选项 `-Bc` 中的脚本。**

   ```sh
   python3 -Bc 'P = "/t" + "mp/cls-exam/x"; P = "/etc/passwd"'
   ```

   新版把脚本内容误认成文件名。**旧版动态判据命中，新版 `[]`**；树内解释器也实测接受 `-Bc`。

3. **新回归——[test_skill_portability_lint.py:1574](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1574)、[`:1614`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1614)：合法 Python 左移被误认成 heredoc，进而取消整块重赋值检查。**

   ```python
   P = "/t" + "mp/cls-exam/x"
   N = 1 << 2
   P = "/etc/passwd"
   ```

   `<< 2` 使 `saw_heredoc=True`，三条独立语句又不能通过单元检查建立重赋值关系。**旧版命中，新版 `[]`**。

   **以上三项均有安全对照**：将末句目标 `P` 改为 `Q`，旧、新均不报；危险形态只有新版漏报。

4. **新回归——[test_skill_portability_lint.py:2550](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2550)：只看邻接字符，不看邻接字符是否被转义，能漏切真正的后台分隔符。**

   ```sh
   true \>& printf -v CLS_BACKEND_URL %s ""; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"
   ```

   `\>` 是普通参数，随后 `&` 应分隔命令；新版却当作 `>&`，把 `printf` 拼进前段，使段首检测失效。**旧版 URL 判据命中，新版 `[]`**；实际配置变量被清空。

5. **整改未闭合——[test_skill_portability_lint.py:1339](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1339)：`parent.values()` 看不到没有子节点的裸提前离开语句。**

   ```python
   readers = []
   def f():
       P = "/etc/passwd"
       readers.append(lambda: P)
       return
       P = "/t" + "mp/cls-exam/x"
   f()
   result = readers[0]()
   ```

   裸 `return` 不进入被扫描集合，后面的赋值仍被认作最终覆盖。实测 `result="/etc/passwd"`，动态判据却为 `[]`；将 `return` 换成 `pass`，结果才是合规路径。

   裸 `raise` 同样漏检；`break`、`continue` 也不会进入该集合。现有测试的 `return P` 恰因拥有 `Name` 子节点才被发现。**这是旧缺口未修完，不是本轮新增回归。**

6. **整改未闭合——[test_skill_portability_lint.py:1143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1143)：反射检查没有遍历完整赋值目标，名单也遗漏直接可见的命名空间写入机制。**

   ```python
   P = "/t" + "mp/cls-exam/x"
   (globals()["P"],) = ("/etc/passwd",)
   ```

   确定会覆盖模块 `P`，但顶层目标是 `Tuple`，检查直接跳过；**旧、新动态判据均为 `[]`**。

   同样漏报的机制包括：

   - `for globals()["P"] in [...]`
   - `dict.update(globals(), P=...)`
   - `setattr(sys.modules[__name__], "P", ...)`
   - `sys.modules[__name__].__dict__["P"] = ...` 及 `.update(...)`
   - `importlib.reload(sys.modules[__name__])`
   - `from x import *`：目前被登记成名字 `"*"`，没有表示未知名字覆盖。

   后两项的实际覆盖结果取决于模块内容，但**机制直接可见**，按当前契约应登记未知，不能静默。

这些 `/tmp` 反例使用拆分字面量，实测九项计数与其他路径判据无法区分，**`tmp_block_fingerprints()` 也为空**，因此不是仅丢失诊断分类、仍被第十条拦住。

**MEDIUM：2 条。**

1. **新误报——[test_skill_portability_lint.py:1396](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1396)：`_bound_names()` 遗漏仅注解及 `del` 形成的局部绑定。**

   当 `outer` 持有合规 `P`，`middle` 仅声明 `P: str`，而 `inner` 用 `nonlocal P` 写入越界值时，真正目的地是 `middle`；新版却越过它，误报 `outer.P` 被覆盖。**旧版 `[]`，新版命中**；实际执行验证 `outer.P` 仍合规。死分支里的 `del P` 同样复现。

2. **既存、分界过宽——[test_skill_portability_lint.py:2725](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2725)：`unset C'LS'_BACKEND_URL` 仍静默，不应归入需要另卡才能解决的数据流问题。**

   ```sh
   unset C'LS'_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"
   ```

   变量名完全由字面词确定，只需正确去引号；实测 URL 判据为空，计数与指纹也不兜底。`:2407`／`:2711` 虽已登记不修，仍属于本卡正在维护的词法判据。

**LOW：未发现独立问题。**

对你指定的五种分隔形态，实测如下：

| 形态 | 当前处理 | 结论 |
|---|---|---|
| `2>&1` | `&` 不切段 | 未发现问题 |
| `>&2` | `&` 不切段 | 未发现问题 |
| `a \|& b` | 两字符分别切，空段丢弃 | 非空命令边界正确 |
| `a&&b` | 两个 `&` 分别切，空段丢弃 | 非空命令边界正确 |
| `a & b` | 单个 `&` 切段 | 未发现问题 |

这只说明**命令边界**正确；共用判定的实际错误是 HIGH-4 的转义邻接情况。

`_provably_last()` 的“整段最早退出”近似还有两个明确的**误报方向**：`return P` 在 `if False` 中，或前面的 `raise ValueError` 已被对应 `except` 捕获时，最终合规赋值本来能够执行，新版仍登记。这可以保留为明确声明的保守面；与 HIGH-5 的漏报应分开处理。

其余复核维度：

- `_own_nodes()` 按字段排除、正常形参识别及不动点搬运：**未发现旧抓新漏的已证实回归**；绑定集合问题见 MEDIUM-1。
- 直接 `globals()["P"]=...` 已能触发，`globals().get(...)` 仍保持不触发：**未发现整改失效**。
- 删除四个控制流 helper：**未发现独立回归**。
- 交接常量纯函数返回 `[]`：**未发现问题**。

本卡与另卡的分界应是：**本轮回归、直接可见的写入／词法遗漏，以及已有判据承诺覆盖却静默的形态，应在本卡闭合；完整跨文件数据流、别名传播、运行期路径和真实宿主行为可以另卡。** 对后者，即使不求精确结果，直接出现的未知写入机制仍可在本卡登记。

**本轮 BLOCKER 0 条，HIGH 6 条。**
