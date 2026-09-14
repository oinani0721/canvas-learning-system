绑定 **`b2f962d914b4a87efd0479fc54ceb98f6e142ac4`**；脚本与测试的工作区字节均与该 SHA 一致。**BLOCKER：未发现。发现 3 条 HIGH、7 条 MEDIUM、1 条 LOW。** round-1 的指定反例均已修复，但部分边界仍未闭合。

以下行号均属于 `backend/scripts/g39_three_view_reconcile.py`。

1. **HIGH — [g39_three_view_reconcile.py:310](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:310)**  
   **响应头读取失败仍被豁免。** 已通过本地 `socketpair` 和真实 urllib 路径观察：连接建立、对端收到完整 GET 后不返回响应头，`open()` 超时被归入 N3；因此分开 `open()` 与 `resp.read()` 并未真正分开连接阶段与读取阶段。

2. **HIGH — [g39_three_view_reconcile.py:606](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:606)**  
   **推荐前缀之后的板序完全漏查。** `top=[乙]`、到期数 `乙=2、甲=2、丁=1`，overview 返回 `[乙,丁,甲]` 时实得零差异，而参照 `:911` 应排 `[乙,甲,丁]`；零到期板尾序反转、`top=[]` 时全部板序反转，也能漏过。

3. **HIGH — [g39_three_view_reconcile.py:569](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:569)**  
   **overview 重复板行被字典覆盖。** 在正常 `[乙,甲]` 后追加完全相同的甲板行，实际板表变成 `[乙,甲,甲]`，脚本仍报零差异；这需要板行唯一性检查，单独补齐排序检查不能替代它。

4. **MEDIUM — [g39_three_view_reconcile.py:430](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:430)**  
   **N4 接纳了非历史形态。** 投影保留 `buckets`、删除 `boards`，overview 缺席时实得 `N4+N3`、零差异；参照 `review_overview.py:869-872` 明确规定该组合不是合法旧投影。

5. **MEDIUM — [g39_three_view_reconcile.py:586](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:586)**  
   **合法旧投影的零到期板被误报。** `boards`、`buckets` 均缺席，`upcoming` 含丙板时，overview 按参照 `:928-941` 正确追加丙板零到期行，脚本却报 `0 ↔ "(picker 明细无此板)"`，因为预期板集漏了 `upcoming`。

6. **MEDIUM — [g39_three_view_reconcile.py:212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:212)**  
   **rollup 的 `due` 值没有类型门禁。** 将合法零到期板的 `due` 改成 `false`，overview 缺席时仍零差异：Python 的 `False == 0` 使损坏计数被当成正常零值；`2.0` 与明细计数 `2` 也被视为相等。

7. **MEDIUM — [g39_three_view_reconcile.py:161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:161)**  
   **Dashboard 异常镜像仍不完整。** 基例设 `generated_at={"toString":null}`，Dashboard `:82` 的字符串插值实际抛 `TypeError`，落入 `:87` 不显示数字；脚本却返回到期数 4、无降级，并与基例 overview 对账全绿。

8. **MEDIUM — [g39_three_view_reconcile.py:737](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:737)**  
   **离线 overview 的严格解析异常逃逸。** `--overview-json` 含 `NaN` 或非法 UTF-8 时，`main()` 直接抛未捕获异常，没有差异表；HTTP overview 与 picker 路径已有的错误分类没有覆盖此入口。

9. **MEDIUM — [g39_three_view_reconcile.py:628](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:628)**  
   **不可哈希节点身份会打断对账。** 离线 overview 保持正常 `status=ok`，picker 某行改成 `node=[]`，集合构造直接抛 `TypeError`，没有生成输入损坏差异；这是离线输入处理缺口，不是现网端点排序分叉。

10. **MEDIUM — [g39_three_view_reconcile.py:643](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:643)**  
    **节点排序的独立性仍标错。** 把 overview 乙板节点逆序，产生的 `node_order` 差异仍标 `cross-source`；完整排序键已确认来自同一契约，应按新增定义标为 `reimplementation`。

11. **LOW — [g39_three_view_reconcile.py:741](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:741)**  
    **未尝试连接也能进入 N3。** 只提供 `--picker-json` 时，正常输入返回 rc=0，并写入含 `backend down` 的 N3；未知 URL 协议也会经 `:310` 落入 N3。因此豁免口并非恰好只剩连接失败。

对你点名的几个判断，补充明确结论：

- **两条 rollup 扫描形状不一致：未发现由此单独造成的假绿。** 非 object 行、非法板名、重复板名虽然被 `picker_rollup_boards()` 跳过或覆盖，但 `picker_rollup_due()` 会先产生 `structure` 差异。计数类型漏检是第 6 条。
- **`:589` 的缺省 0：未发现掩盖整体差异。** 它表示 **picker 明细派生侧的零值**，不是 rollup 的 `due`。实测“rollup 丙板 due=2、明细无丙板、overview 丙板 due=0”，overview 子项相等，但 `:446` 已报出 `2 ↔ "(明细无此板)"`，整体仍红。
- **前缀不是所有形态下都成立。** `top=[零板]`、`groups={到期板}` 时，所读参照片段会先输出到期板、再追加零板，脚本会报排序差异。授权范围未包含完整 top 前置门禁，不能进一步断言该形态能通过真实端点；该差异本身也不能证明端点违反了排序键。
- **完整节点排序键：未发现语义错位。** 已读至 `:1015`，两侧合法输入的键均为 `(fsrs_due == "", fsrs_due, node)`。同名重复节点、非字符串 `fsrs_due`、非字符串 `node`，分别被参照 `:205`、`:165`、`:201` 拒绝；真实 `corrupt` entry 会被脚本判为差异。
- **白名单：N1、N2 未发现新的豁免问题；N3、N4 不闭合**，分别见第 1、11 条和第 4 条。

round-1 逐条结论如下：

| r1 | 独立复核结论 |
|---|---|
| HIGH-1 | 零到期 rollup 板缺失已能拦截；旧投影 `upcoming` 路径仍误报，见第 5 条。 |
| HIGH-2 | 指定前缀反例已修；其余板序仍漏查，见第 2 条。 |
| HIGH-3 | picker、HTTP overview 拒绝 NaN 成立；离线入口异常逃逸，见第 8 条。 |
| HIGH-4 | 返回响应对象后的正文读取失败已修；响应头阶段仍被豁免，见第 1 条。 |
| MEDIUM-5 | 缺键与顶层/行形状损坏已分开；仍有第 4、6 条缺口。 |
| MEDIUM-6 | 板级 due 标签已修；节点排序标签残留，见第 10 条。 |
| MEDIUM-7 | `null` 行降级已修；其他 Dashboard 转换异常仍漏镜像，见第 7 条。 |
| MEDIUM-8 | HTTP 正文非法 UTF-8 正确归入读取错误；该修复未发现问题。 |
| LOW-9 | 重复 vault entry 正确生成差异；未发现问题。 |

**代理旁路修复：未发现问题**，空 `ProxyHandler({})` 与同环境默认 opener 的验伪锚均通过。

未修改文件、未运行 pytest、未连接后端或数据库；复现使用内存执行，HTTP 阶段验证仅使用本地 IPC。


