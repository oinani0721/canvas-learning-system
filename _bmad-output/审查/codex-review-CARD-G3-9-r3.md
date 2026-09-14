> 批次: BATCH-2026-09-11-第十四批 · 车道 T4-A · 卡 CARD-G3-9 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G3-9-r3.md)"`
> 审查绑定: `0596386b`（该轮送审时的 HEAD；本轮十一条采纳后代码前进，故本轮**不绑**最终 HEAD，另送 round-4）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）

---

**仍有 HIGH，round-3 尚不能收口。BLOCKER 未发现。** 当前 HEAD 为 `0596386b6b9f6ce89ee1ad38a926367b64b6fee7`，脚本和测试的工作区内容均与绑定 SHA 一致。以下问题均属于对账器；未评价参照端点本体。

定位均在 [backend/scripts/g39_three_view_reconcile.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py)。

1. **HIGH — `g39_three_view_reconcile.py:406、437`：重定向后的连接失败仍被 N3 豁免。**  
   用真实重定向处理器、内存响应复现：首跳收到 `302`，下一跳连接被拒，最终返回 `not-fetched`，自洽 picker 得到 `semantic_diff=[]`；首跳后端已经响应，却被报告成 `backend down`。

2. **MEDIUM — `g39_three_view_reconcile.py:93、391`：跨平台 errno 整数混用，既误收也漏收。**  
   macOS 的 `ETIME=101` 被判为连接失败，`ENETDOWN=50` 却不被接纳；Linux 的 `EHOSTDOWN=112`、`ENETDOWN=100` 也不在白名单。应使用当前平台的 `errno` 名称，不能合并两平台的数字。Linux 部分验证了分类函数，未运行 Linux 网络探针。

3. **MEDIUM — `g39_three_view_reconcile.py:422、432`：协议及 URL 异常仍会逃逸，不能形成差异报告。**  
   内存解析非法状态行、超长响应头分别产生未捕获的 `BadStatusLine`、`LineTooLong`；输入 `localhost`、`http://[broken` 或非法端口也分别逃出 `ValueError`／`InvalidURL`，没有进入声明的 `__open_error__`。

4. **MEDIUM — `g39_three_view_reconcile.py:125`：数组会传播元素字符串化异常，当前判定漏查。**  
   将 `stats.unassigned` 设为 `[{"toString":null}]`，真实 Dashboard JS 进入“投影损坏”，复算却仍给出正常数字，与正常 overview 对账得到 `semantic_diff=[]`；嵌套数组同样漏查，`generated_at` 也受影响。

5. **MEDIUM — `g39_three_view_reconcile.py:193、209`：遗漏 `backlogCnt` 的插值异常。**  
   设置 `ineligible.placeholder=[]`、`stats.ineligible={"toString":null}`，Dashboard 在 `:78` 抛错，N5 两面对账却仍为零差异；正常 overview 在场时会因 backlog 不等报红，因此这是明确的**两面假绿**。

6. **MEDIUM — `g39_three_view_reconcile.py:703`：计数比较仍允许 `false` 与 `0` 相等。**  
   将 placeholder 清空、相应板级 placeholder 清零，令 `stats.ineligible=false`、overview backlog 为 `0`，对账仍为零差异；Dashboard 实际显示“待剖析积压 false 张”，与 overview 的 `0` 不同。

7. **MEDIUM — `g39_three_view_reconcile.py:783、786`：picker 的节点自检依赖 overview 在场。**  
   对原绿夹具仅设置 `due_nodes[0].node=[]`，正常 overview 在场会报损坏，但走 N3 或 N5 时检查完全不执行，得到 `semantic_diff=[]`。这是 r2 MEDIUM-9 修复仍存在的旁路。

8. **MEDIUM — `g39_three_view_reconcile.py:728、766、798`：损坏的 overview 行被过滤后隐形。**  
   在正常 overview 的板表追加 `null`，或在已有板的节点列表追加 `{"node":[]}`，两种输入均仍为零差异；重复板检查没有覆盖非法板行，节点身份检查也先丢掉了非法节点。

9. **MEDIUM — `g39_three_view_reconcile.py:783`：零到期板的节点列表完全不查。**  
   在合法 picker 中加入一块未来板，并给对应 overview 零到期板塞入 `nodes=[{"node":"phantom"}]`，仍得到零差异；循环只遍历与 `groups` 的交集，而零到期板不在其中。

10. **MEDIUM — `g39_three_view_reconcile.py:328`：新增排序路径可被损坏时间值打断。**  
    两个 rollup 零到期板的 `next_due` 分别为 `{"x":1}` 和合法时间字符串，配合 `ok` overview，`reconcile()` 抛出 `TypeError: '<' not supported between instances of 'str' and 'dict'`，整次报告中断。

11. **MEDIUM — `g39_three_view_reconcile.py:281、331`：旧分支会覆盖重复 upcoming，并归一非法排序值。**  
    删除 `boards`，加入两条同名 upcoming，而 overview 只保留一条对应零板，仍得到零差异和 N4；非字符串 `next_due` 也被改成空排序键。此项是**离线损坏响应／未来门禁漂移漏检**：当前参照端点会拒绝这种投影，实际返回 `corrupt` 时对账器仍能报红。

其余重点结论：

- **完整板序：合法输入下未发现偏差。** 两支共比较 1,152 组组合，`next_due or None`、upcoming 原字符串、排序键及排除已到期板均一致。
- **`_strict_count()` 返回 None：未发现因此全绿。** 下游已经保留 `picker.boards(self)/structure` 差异；合法来源下的 `zero_source` 缺省也未发现问题。
- **`continue` 整板：未发现因此全绿。** 它会少报该板后续节点差异，但此前已追加损坏差异；真正的假绿是第 7 条中检查根本没执行。
- **插值误报：未发现。** 正常 JSON 原始值、普通对象不抛；自身带 `toString` 键的对象会抛，数组递归传播元素异常，普通对象的普通属性不会被递归转换。转换顺序是 `toString → valueOf`。其余插值字段中，除遗漏的 `backlogCnt` 外，未发现额外异常入口。
- **N1–N5 尚未闭合。** N3 有第 1 条直接假豁免；N3/N5 还有第 7 条自检旁路。N4 的“缺 boards 且缺 buckets”判断本身未发现错误，第 11 条属于后续漏验。
- r2 的重复板检查、`buckets` 无 `boards` 拦截、合法旧投影、rollup `due` 类型检查、普通离线读取/解析异常分类、独立性标签及 N3/N5 区分，**指定修复路径未发现回退**。

全程只读，复现仅在内存运行；未执行会写盘的 pytest、未启动后端、未连接数据库。


