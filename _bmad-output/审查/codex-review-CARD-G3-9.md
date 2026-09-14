**本轮不通过。**绑定 `30b23c4d`，发现以下漏检与分类问题；未发现 BLOCKER。反例在内存中验证，以下 `rc=0` 按脚本实际返回条件判断。

1. **HIGH — [g39_three_view_reconcile.py:489](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:489)：零到期板未参与完整板集对账。**  
   picker 含合法的 `丙板：due=0, future=1`，overview 漏掉丙板，仍得到 `semantic_diff=[]`，报告“三面逐项相同”。总览会少显示一板；N1 的 Dashboard 全板口径不能解释 picker↔overview 的这个差异。

2. **HIGH — [g39_three_view_reconcile.py:504](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:504)：板序检查比较的是子序列，未检查前缀。**  
   `top_boards=[乙板]`、overview 顺序为 `[甲板,乙板]` 时，过滤后仍等于 `[乙板]`，对账全绿；实际总览首板已与推荐首板不同。

3. **HIGH — [g39_three_view_reconcile.py:637](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:637)：JSON 解析与 Dashboard 分叉，可造成两面假绿。**  
   正常投影仅加入 `"extra": NaN`，Python 默认 `json.loads` 接受，overview 未连接时仍报告两面相同、`rc=0`；真实 Dashboard 在 `Dashboard.md:59` 的 `JSON.parse` 失败，进入 `:87`，显示“投影损坏”而不出数字。

4. **HIGH — [g39_three_view_reconcile.py:239](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:239)：已连接后的读取失败也被豁免为 N3。**  
   HTTP 已返回 200，但 `resp.read()` 超时或连接重置，会被记录为 `not-fetched/backend down`；自洽 picker 因而得到零差异、`rc=0`。这超出了“仅连不上可以降级”的边界。

5. **MEDIUM — [g39_three_view_reconcile.py:179](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:179)：N4 混淆缺键与类型损坏。**  
   `boards` 明明存在，但为 `null`、`{}` 或字符串，仍被记成“无 boards 顶层键”；overview 缺席时三例均零差异。在线端点返回 `corrupt` 能兜住，但两面降级路径会放过已经读到的损坏。

6. **MEDIUM — [g39_three_view_reconcile.py:494](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:494)：板级计数独立性标错。**  
   overview 和脚本都对同份 `due_nodes` 做 group-by 计数；按脚本自己的定义，这项应是 `structurally-guaranteed`。将 overview 某板 `due` 改为 3、picker 保持 2，可观察到差异行错误标为 `cross-source`。它能检测实现漂移，但不能充当第三个独立派生源；picker rollup↔明细的 `cross-source` 标注未发现问题。

7. **MEDIUM — [g39_three_view_reconcile.py:140](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:140)：Dashboard 镜像遗漏逐行计算的异常。**  
   `due_nodes=[null]、stats.due_nodes=1` 时，镜像报告 `due_count=1、degraded_reason=None`；实际 `Dashboard.md:70–72` 访问 `null.due_reason` 后进入 `:87`，显示损坏、不出数字。此例另有非法板名差异，整体不会假绿，但 Dashboard 面的记录错误。

8. **MEDIUM — [g39_three_view_reconcile.py:236](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:236)：非法 UTF-8 响应逃出错误分类。**  
   HTTP 200 正文含 `0xff` 时，`decode()` 抛出未捕获的 `UnicodeDecodeError`，CLI 中断、没有对账报告，没有按声明计入 `semantic_diff`。

9. **LOW — [g39_three_view_reconcile.py:270](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:270)：重复目标 vault ID 时静默取首个匹配项。**  
   响应含同一目标 ID 的 `[ok, corrupt]` 两条 entry，可以只选第一条而全绿。当前端点每目录一条，未发现它会产生此形态；这是异常响应的防御缺口，**不是跨 vault 合并**。

其余问题的结论：

- **N2 豁免边界：未发现直接吞掉正常节点行序差异。**同时间、不同节点名的第三键能够排序；重复 `node` 和非字符串 `fsrs_due` 分别被端点 `:205–206`、`:165–166` 拒绝，进入 `corrupt`，不会进入成功排序路径。
- **实际排序键逐位一致性尚未核验。**授权片段到 `review_overview.py:1000` 截断，未包含完整排序键；补充读取请求尚未获答复，因此不能宣称已核实实现。
- **降级提示本身未发现问题。**`compared_views`、终端“未覆盖总览页”和报告 `vaults_without_overview` 均明确；问题是第 4 条的降级分类过宽。
- **正常响应的甲支取数未发现问题。**另一个 vault 排第一仍选择目标 ID，缺目标明确报差异，没有跨库求和。
- **Dashboard 的 bool 排除与 `|| stats.ineligible` 回退未发现分叉。**

未修改文件、未连接数据库或启动后端；未运行会落盘的 pytest，也未读取范围外的变异证据，因此不确认作者所述“6/6”。


