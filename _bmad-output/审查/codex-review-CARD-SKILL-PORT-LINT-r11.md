**仍有新回归，残余风险尚未完整声明。** 复核绑定 `8386e41f05f4027a40fa8f494e4f070bc986043e`；测试文件工作区 blob 与提交一致，为 `88590b9d3d2d3045f9a6a050189c0f76da50eec8`。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库。

下列反例均经纯函数内存验证；比较的是正式门使用的计数、normpath 多重集和行号，包含新增的 URL 覆盖判据。

**BLOCKER：未发现。**

**HIGH：9 条。前三条包含本轮新回归。**

1. **HIGH — [test_skill_portability_lint.py:605](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:605)：新的续接扫描跳过嵌套 `elif`，提前截断合法复合语句。**

   将下面代码放进 shell fence 的 Python heredoc：

   ```python
   if True:
       if False:
           pass
       elif (P := "/tmp/cls-exam/" "." "./x"):
           pass
   ```

   当前把前三行认走，孤立的 `elif` 转交 shlex，拼接关系丢失。安全对照只把 `"."` 改成 `"a"`：九计数相同，五集合全空，但坏形态的 P 规范化为 `/tmp/x`。

   **仅在内存恢复旧版“紧邻下一行”检查，越界和动态判据立即报红，证明是新回归。** 同根还漏同级注释隔开的 `elif`，以及嵌套 `case`。

2. **HIGH — [test_skill_portability_lint.py:455](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:455)、`:506`：容器前缀整改使合法嵌套引用解析失败，列表缩进也仍会被删。**

   ````text
   >  > ```python
   >  > P = "/tmp/cls-exam/" + "." * 2 + "/x"
   >  > ```
   ````

   这是合法的双层引用 fence；当前剥除后留下 ` > P = ...`，五集合全空。安全对照只改 `"."` 为 `"a"`，九计数不变。**恢复整改前的前缀正则后立即抓到，证明是新回归。**

   同根既存缺口：列表 fence 中的 `def f(p=动态路径):` 和缩进函数体，经开头 `[ \t]*` 处理后都变成顶格，默认参数表达式因此漏检。

3. **HIGH — [test_skill_portability_lint.py:1554](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1554)、`:1168`：新增误报基线只绑定行号，使登记行可以替换成真实债。**

   从允许读取的 diff 取出 start-exam-board 第 577 行，仅将其中的：

   ```text
   `/tmp/cls-exam/`
   ```

   替换为：

   ```text
   P="/tmp/cls-exam/"`printf .`"./x"
   ```

   其余文字不动。实测九计数不变；越界、动态、父目录、URL 均为空；可疑行与 opaque 均保持 `[577]`。命令替换后的路径却是 `/tmp/x`。

   **因此，这次登记的代价不只是三条误报：它新开放了无需修改基线即可引入真实债的原行号。** “零余量不变”不成立。

4. **HIGH — [test_skill_portability_lint.py:479](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:479)、`:487`：散文拼段仍跨越实际 Markdown 块边界。**

   ````text
   段尾 `未闭合
   # 标题
   执行 `/var/cache(
   /tmp/cls-exam/x`
   ````

   最后两行实际形成合法 code span；当前把标题两侧合并，让前段反引号抢走后段 opening，五集合全空。相邻列表项、引用内空行 `>`、HTML 注释块也复现相同漏检。

   表格还有反方向问题：启用 GFM 表格语义后，本不相邻的单元格／行会被拼出假 span，产生误报。新增的原始空行判断尚未覆盖这些边界。

5. **HIGH — [test_skill_portability_lint.py:522](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:522)、`:282`：fence 开闭条件仍能把真实代码误归为散文。**

   ````text
   ``` text `label`
   说明
   ```
   P = "/tmp/cls-exam/" + "." * 2 + "/x"
   ```
   ````

   反引号 fence 的 info string 不允许出现任何反引号；第一行实际不是 fence。当前只拒绝长度至少等于 opening 的 run，因而错误开闭，漏掉真实代码中的动态路径。

   另一个同类输入是在普通 fence 内放四空格缩进的 `` ``` ``：它应是内容，`:282` 的 `^\s*` 却允许其提前闭合。两种输入都能做到九计数不变、五集合全空。

6. **HIGH — [test_skill_portability_lint.py:418](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:418)、`:422`：剩余中文句读和 Unicode 空白仍能作为 shell 词的一部分。**

   ```text
   执行 P="/var/cache""/tmp/cls-exam/"，`printf a`，
   ```

   相比安全赋值 `P="/tmp/cls-exam/x"`，九计数相同、五集合全空；实际路径为 `/var/cache/tmp/cls-exam/，a，`。

   `，。；：！？…—·`、NBSP、全角空格均复现。删除 `*` 和中文引号的方向成立，但**保留这些字符仍在放行同根漏检**。

7. **HIGH — [test_skill_portability_lint.py:857](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:857)：新预筛仍漏解析后的 bytes 常量。**

   ```python
   P = b"/t" b"mp/cls-exam/" + b"." * 2 + b"/x"
   ```

   `_py_strings()` 返回 `[]`；直接调用 `_has_dynamic_tmp_join()` 返回 `True`，但正式入口的预筛将它挡掉，全部附加判据为空。安全对照只改 `b"."` 为 `b"a"`，九计数相同。

8. **HIGH — [test_skill_portability_lint.py:824](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:824)：AST 判据只检查叶常量，漏掉显式常量拼接后才出现的 `/tmp`。**

   ```python
   P = ("/t" + "mp/cls-exam/") + "." * 2 + "/x"
   ```

   `_py_strings()` 已返回 `/tmp/cls-exam/`，因此预筛通过；但两个叶常量分别不含 `/tmp`，父链检查根本没有启动。安全对照只改 `"."` 为 `"a"`，九计数相同、全部附加判据为空，坏值规范化为 `/tmp/x`。

   这与上一条分别发生在**入口预筛**和**AST 起点选择**，需要分别处理。

9. **HIGH — [test_skill_portability_lint.py:831](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:831)：保留 `Assign` 安全停止点仍允许静态确定的赋值覆盖。**

   ```python
   P = "/tmp/cls-exam/x"; P = "/var/cache/x"
   ```

   相比单次安全赋值，九计数和全部附加判据均不变，最终 P 却确定为 `/var/cache/x`。将合规赋值放在 `if False` 分支中也一样。

   这是**既存、未声明的缺口**。既然前轮已把“合规常量与实际赋值脱钩”纳入判据目标，就不能把这个版本归为运行期未知；删除 `Expr` 只封住了其中一种形态。

**MEDIUM：1 条。**

- **MEDIUM — [test_skill_portability_lint.py:1499](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1499)：`unset` 补丁仍漏合法选项和引用写法。**

  ```sh
  unset -v CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/api/v1/ping"
  ```

  相比单独 curl，九计数和全部附加判据不变，但外部配置被确定性清空。`unset -- CLS_BACKEND_URL`、`unset "CLS_BACKEND_URL"` 也漏。

**LOW：1 条。**

- **LOW — [test_skill_portability_lint.py:1810](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1810)：400 行断言只量返回单元，没有约束失败后废弃的解析窗口。**

  ```python
  body = ["P = ("] + ["    # c"] * k
  ```

  Python 窗口持续尝试到块尾，然后回退成单行单元，返回的最长单元始终为 1。`k=500/1000/2000` 实测约 `0.035/0.123/0.464s`；二次增长已经发生，长度断言仍绿。因此它没有钉住所声明的成本前提。

其余维度逐项结论：

| 维度 | 复核结果 |
|---|---|
| 不完整 Python 一直尝试到块尾，是否吞掉其余候选 | **未发现永久吞块漏检。** 已复现尝试到块尾，但失败后仍会进入 shell／单行回退；成本问题见 LOW。 |
| `_backtick_spans()` 的 opening／closing run 与转义 | **未发现新的提取缺陷。** 对 87,380 个短字符串与本地 CommonMark 解析作有限对照，内容归一化后全部一致。 |
| 掩码处理非 ASCII 标点是否丢 span | **未发现。** 范围虽宽于规范，已测输入中没有改变反引号的转义奇偶。 |
| span 空白归一化 | 实现保留原始换行和两侧空格，仍可能产生保守误报；上述对照不证明原始候选值完全一致。 |
| `With/withitem/comprehension/keyword/Starred/NamedExpr/装饰器/默认参数` | **未发现完整 AST 父链误放。** 测试形态均触发动态判据；合规默认参数的保守误报与声明一致。前置切分仍有 HIGH-1／2。 |
| `codeop` 对普通反斜杠续行、装饰器及异步语句 | **未发现额外提前终止。** 已确认的复合语句回归来自外加续接检查。 |
| body 引用深度多／少于 opening | 会发生内容失真：多出的 `>` 被误剥，少一层时没有正确结束容器；已验证样本为保守误报方向，未另计 HIGH。 |
| 来源前缀与 U5-B／U6 | 确会随格式翻转：相同代码从 fenced 改为四空格缩进，结果可由 `fence:/tmp/x ×2` 变成 `prose:/tmp/x ×1`。`:1429` 已提示来源含义，**未发现新增诊断缺陷**；U5-B 仍须同步多重集和行号基线。U6 独立 scripts 不经过这条逻辑，**未发现新问题**。 |
| 形态表第 15 行 | 32 行表的第 15 行是 `unset`，指名 URL 判据正确；三判据表实际为 16 行，其第 15 行指名越界也正确。**未发现错选。** |
| 两处内存变异 | 删除 fence 同字符条件、恢复分号截断，均使对应断言失败，**未发现残留不承重**。新版 `elif` 对照也能杀死旧逻辑变异。 |
| 其他断言承重性 | 32 行指名检查均通过。`:2778`“至少有人红”仍由前一断言直接蕴含，无额外承重，属于前轮已指出项。 |

默认参数的保守误报取舍可以成立；三条 opaque 误报仅登记行号则存在 HIGH-3 的新增缺口。未重读真实技能正文，因此没有把“122 个测试通过”或“最长单元 278 行”当作本轮独立验证结果。

**本轮 BLOCKER 0 条，HIGH 9 条。**
