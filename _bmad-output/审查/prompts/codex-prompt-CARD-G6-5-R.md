你是对抗性代码审查者。请对下面这次改动做独立复核，用中文回答。

工作树根目录：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b`
审查面：`git diff f78bb548..HEAD`（4 个文件，+486/-6；含测试）。基点 commit = `f78bb548`。

## 一 背景与最小读取面

这是一个本地单机学习系统的「跨库复习总览」页。数据链路是单向只读的：一个离线生产器脚本
每天把「今天该复习哪些卡」算好、落成一份 JSON 投影文件；两个只读页面（一个零 JS 的服务端
渲染页 `/overview/page`，一个带轮询的交互壳 `/overview/app`）消费它。**消费端一个数都不算**，
到期判定/计数/排序全部来自投影。

投影里早就有一个顶层 `buckets` 字段：五个桶（new / learning_queue / due_now / due_today /
future），每桶是一串节点行，每行恰好 `{node, board, why_due, fsrs_due}` 四个字段。
消费端的 `_gate_buckets()` 已经对这些行做了完整门禁（逐行验形 + 与 due_nodes 明细的成员恒等 +
以 `generated_at` 为参照时钟重算桶判据 + 与 boards rollup 逐板对账 + 三方计数硬断言），
**但验完就把行丢了**，只把五个数字（`bucket_counts`）交出去。于是两个页面上只有一行
「分层 · 新卡 1 · 学习中 1 · …」，new 和 future 两桶在节点级完全看不见（它们不在
`due_nodes` 里，板表格的节点明细里根本没有它们）。

本次改动做两件事：
1. 让 `_gate_buckets` 把**已验的那些行**一并交出来（返回值从 `dict` 变成 `(counts, rows)`），
   `_summarize` 把它作为新顶层字段 `bucket_rows` 输出；
2. 两个页面各加一个「按到期阶段分五块」的队列区块，块内逐节点点名 + `obsidian://` 深链。

请只读以下文件（**不必也不要**去读仓库其它部分）：
- `backend/app/api/v1/endpoints/review_overview.py`（聚合 + 门禁 + 零 JS 页）
- `backend/app/api/v1/endpoints/review_app.py`（交互壳；JS 以 r-string 内联在 `_PAGE_TEMPLATE`）
- `backend/tests/unit/test_review_overview.py`
- `backend/tests/unit/test_review_app.py`
- `scripts/daily_review_pick.py:998-1014`（只读参照：投影侧 `buckets` 的组装点。本卡对这个
  文件**零改动**，`git diff f78bb548 HEAD -- scripts/daily_review_pick.py` 输出为 0 字节）

## 二 作者自述（请独立核对，不要采信）

- (a) 投影侧零改动，没有新增任何与 `buckets` 语义重叠的第二套字段。
- (b) `_gate_buckets` 只改了签名与 return；原判据区（基点行号 `:429-508`，共 80 行：逐行验形
  + 成员恒等 + 桶特定时间语义 + 三方计数 + 与 rollup 对账）**逐字节未动**——作者用
  「从基点取出这 80 行原文、在改后文件里整块子串查找」验证过，命中。
- (c) 透传行来自 `buckets[name]`（与 `counts` 计数的同一个列表对象），只做四字段白名单投影，
  不排序不去重不补字段；`_summarize` 在边界上再核一次「逐桶 `len(rows[b]) == counts[b]`」，
  不等即 ValueError → 该库按既有 corrupt 语义降级。
- (d) 三方计数（到期三桶合计 == `stats.due_nodes`；`due_today+future` == `stats.future_nodes`）
  **没有重写**，既有反例用例照旧。新增的先红后绿只落在本卡新增面。
- (e) 两页队列区块在 `bucket_rows` 缺省（旧投影没有 `buckets` 键）时整块不出现，与既有
  `bucket_counts` 汇总行同一条纪律。零 CDN、零外部 URL，深链复用既有 `_node_link` / `nodeLink`。
- (f) 顺带修了一条移交缺陷（交互壳 JS）：同一个库连点两次刷新时，第一次重建挂下的 pending
  会在第二次刷新失败后由那轮补发的 GET 结算，把第二次的失败提示改写成第一次的「数字已更新」。
  修法是在刷新入口作废同库旧 pending（`delete state.pendingSync[vid]`）。

- (g) 顺带清了两个测试文件里 **10 处既有类型检查报错**（3 处 `# pyright: ignore[...]`
  给静态收窄丢失的行、3 处给故意传错类型的敌意 fixture、4 处未使用绑定加下划线前缀）。
  这些是零行为改动的静态检查噪声，之所以在本卡清是因为 pre-commit 的类型检查门对
  **暂存文件**逐个跑，而本卡的硬边界禁止跳过该门；清完后这 4 个文件 0 error。
  请一并核对：这 10 处有没有哪一处实际上掩盖了真缺陷，而不只是静态分析的收窄限制？

裁判实测结果（可复跑）：两个单测文件 153 passed（用例数 40+61 → 42+63）；
`tests/regression/test_daily_review_pick.py` 74 passed；`tests/api` 268 passed；
pyright 对两个 `backend/app/**` 文件 0 error（40 个既有 error 全在两个测试文件里，
与基点的错误身份集逐条相同）。

## 三 请按重要性排序回答这些问题

1. **透传行与计数是否真同源**：交出去的行有没有可能与 `:490-499` 那两条计数断言所依据的
   数据不是同一批？边界上那条 `len(rows[b]) == counts[b]` 是不是恒真的空断言？如果是空的，
   它还挡得住什么、挡不住什么？请给出你的判断依据（指出具体行号）。
2. **旧投影路径是否仍然成立**：没有 `buckets` 键的旧投影是否仍走 `bucket_counts = None`、
   `bucket_rows = None`，两页整块不渲染？「有 buckets 无 boards」是否仍抛 ValueError？
   新字段有没有在任何一条路径上从 None 变成空 dict（那会让页面显示一个假的空队列）。
3. **JS 改动的影响面**：`queueLayersHtml` 与那条 pending 修复，有没有触及轮询节奏、
   visibilitychange 处理、或 POST 路径？自动轮询是否仍然一次 POST 都不发？
   pending 修复有没有可能让**正常的单次刷新**结算不了（即修过头）？
4. **移交缺陷的处置是否如实**：(f) 的修法是否真的对上了所描述的时序？测试里的两条「对照」
   是否足以区分「修好了」与「把结算整个弄坏了」？
5. **参照系声明是否落在代码里**：三方计数的参照系是 `generated_at` 而不是 `now`
   这句话，是否确实写进了 `_gate_buckets` 的 docstring？改成 `now` 会有什么后果，
   作者在注释里的说法是否正确？
6. 其余你认为重要的问题（含测试是否有假绿、注释是否比证据说得宽）。

## 四 输出格式

按严重度分组（BLOCKER / HIGH / MEDIUM / LOW），每条写：
`[级别] 标题` + `文件:行号` + 「为什么是缺陷」+ 「触发条件」+ 「建议改法」。
末尾给一节「§三 我不同意作者的地方 / 作者说对了的地方」，逐条点名。
如果某一类你查过但没发现问题，请明确写「查过，未发现」，不要沉默。

## 五 边界与已裁决（不要在这些方向上提建议）

- **已裁决，不重开**：不新增 `queue_layers` 或任何与 `buckets` 语义重叠的第二套投影字段；
  `scripts/daily_review_pick.py` 本卡零改动；不做万节点规模的渲染性能（另一张卡 G6-11）；
  三方计数的参照系就是 `generated_at`；不做「答题后立刻触发投影重建」（用户已裁定维持
  「下一次定时重算后可见」）。
- 本卡不改 `review_overview.py:429-508` 的判据本体、不改投影文件格式、不新增任何写侧动作
  或 POST 端点。
- 请只做**只读**分析：不要修改仓库任何文件，不要运行会写盘的命令。
- 本次审查只需要你的分析结论与行号指认，不需要任何示例代码。
