> 批次: BATCH-2026-09-05-第十二批 · 车道 Y2 · 卡 CARD-G6-5-R round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-5-R.md)"`
> 审查绑定: `f78bb548..af5fd97e`（审后按本报告 MEDIUM/LOW 整改 → 失绑，整改面已在 UAT-CARD-G6-5-R-2026-09-05.md §4-A(h) 登记）
> 会话头自证（抄 .stderr 含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

结论：**指定四文件中，未发现新增 BLOCKER / HIGH；发现 1 项 MEDIUM 测试假绿，以及 3 项 LOW 说明问题。当前透传与 pending 修复的实现成立，但作者对部分测试、守卫能力的表述过宽。**

审查锚定 `af5fd97e500037a3daf2ca73ed473ecb706cd369`。四文件实际 diff 为 `+499/-19`；完整提交区间有 **11 个变更文件**，其余内容未打开，本结论仅覆盖指定读取面。全程未修改文件；执行了纯内存验证，未复跑会落盘的 pytest、生产器或 pyright。

## BLOCKER

**查过，未发现。**

## HIGH

**查过，未发现。** 未发现透传绕过原门禁、旧投影兼容回归、新增自动 POST，或正常单次刷新被修坏。

## MEDIUM

**[MEDIUM] 双刷新成功对照允许“第二次永远不结算”仍然通过**

位置：[test_review_app.py:2356](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:2356)、[review_app.py:363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_app.py:363)。

- **为什么是缺陷：** 对照②最后只检查“累计 6 次”、不含“累计 5 次”。第二次 POST 返回的“正在同步最新数字…”已经包含累计 6，所以这不能证明 GET 完成了结算。
- **触发条件：** 第二轮 pending 结算发生回归。纯内存执行原测试体的结果如下：

| 内存变异 | 失败覆盖反例 | 单次对照① | 双次对照② |
|---|---|---|---|
| 当前实现 | PASS | PASS | PASS |
| 删除入口作废旧 pending 的语句 | FAIL | PASS | PASS |
| 完全禁用结算 | PASS | FAIL | PASS |
| 仅跳过累计 6 的 pending 结算 | PASS | PASS | PASS |

- **建议改法：** GET2 返回后断言仍在等待；GET3 返回后同时断言“数字已更新”和累计 6，并检查最终重绘内容。

因此，两条对照合起来能识别“结算全部坏掉”，**不能识别“仅第二次结算坏掉”**。这是测试缺陷，不是当前生产代码第二次刷新失效的证据。

## LOW

**[LOW] “new 不在 due_nodes、此前节点级不可见”的说明错误，测试使用了不自洽的夹具**

位置：[review_overview.py:1045](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_overview.py:1045)、[review_app.py:246](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_app.py:246)、[test_review_app.py:2189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:2189)。

- **为什么是缺陷：** `_DUE_BUCKETS` 明确包含 `new`；成员恒等门禁要求新卡同时出现在 `due_nodes`，随后进入 `boards[].nodes`。真正不在到期明细里的两桶是 **`due_today/future`**，生产器指定参照段也明确如此。
- **触发条件：** 任意合法含新卡投影。纯内存调用实际 `_summarize` 后，新卡同时出现在板明细和队列。JS 测试仅拼入 `bucket_rows`，没有同步板明细与计数；“并查集不在板里”只是夹具自身造成的。休息日测试还给 `due_count=0` 拼入了非空到期桶。
- **建议改法：** 更正说明；使用成员、计数一致的夹具，验证新卡在两种视图中均可见，`due_today/future` 由队列补全节点明细。

**[LOW] 行数守卫被描述成了来源／身份守卫**

位置：[review_overview.py:368](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_overview.py:368)、[review_overview.py:739](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_overview.py:739)。

- **为什么是缺陷：** `len(rows[b]) == counts[b]` 在当前实现中恒真。它只能检测逐桶长度漂移，不能保证身份、字段值、顺序或来源未改变。“换来源就当场 corrupt”说得过满。
- **触发条件：** 未来实现用等长数据替换返回行。纯内存包装真实 gate，仅替换返回的 future 节点名，保持长度不变，`_summarize` 照常通过。
- **建议改法：** 将注释限定为“逐桶行数漂移守卫”。**当前真实投影输入没有上述包装路径，不构成现行门禁绕过；无需因此改动冻结判据。**

**[LOW] “本函数一个数都不算”与实际展示代码不符**

位置：[review_overview.py:1049](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_overview.py:1049)、[review_app.py:248](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_app.py:248)。

- **为什么是缺陷：** SSR 在 `:1062/:1081` 使用 `len/sum`，JS 在 `:256/:258` 使用列表长度计算桶数和总数。没有重判到期，但确实计算了展示数量。
- **触发条件：** 任意带 `bucket_rows` 的页面。
- **建议改法：** 准确说明为“只统计已验行数，不重判到期、不重新排序”。若“展示层也禁止计数”是字面硬要求，则桶数字应消费既有 `bucket_counts`，总数文案可省略，无需新增投影字段。

## §三 我不同意作者的地方 / 作者说对了的地方

- **(a) 说对了。** 指定生产器文件 diff 实测 **0 字节**；新增 `bucket_rows` 属于消费端摘要，没有新增第二套落盘投影字段。

- **(b) 核心说对了。** 基点 `429–508` 共 **80 行、5526 字节**，在当前 `444–523` 唯一、逐字节命中。原三方计数及对账判据没有被重写。

- **(c) 当前确实同源，但守卫能力需收窄。** [review_overview.py:445](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_overview.py:445) 取得 `buckets[name]`，`:480` 计数，`:505–514` 用这些计数做断言，`:560` 从同一列表复制四字段。输出是新建列表／字典，但内容来自同一批已验行；没有排序、去重或补字段。边界长度断言是未来长度回归守卫，不是独立真实性证明。

- **(d) 现存判据与测试断言保留，历史“先红后绿”未独立认证。** 新增真生产器测试包含逐行等值和顺序检查，具备有效约束；长度反例则只证明删行会被拒绝。源码测试定义数为 overview `61→63`、app `40→42`，不能据此认证 `153/74/268 passed`。

- **(e) 旧投影路径成立，查过未发现回归。** [review_overview.py:728](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_overview.py:728) 将两值初始化为 `None`；缺少 `buckets` 时原样输出。有 buckets 无 boards 仍在 `:735` 抛 `ValueError`，由 `:899–902` 降级 corrupt。SSR `:1055`、JS `:252` 整块省略。没有 None 被转成 `{}` 的路径；合法全空投影是五个空数组。深链复用及转义、零新增 CDN／外部 HTTP URL，查过未发现问题。

- **(f) 修法确实对上时序，正常单刷没有被修过头。** [review_app.py:530](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_app.py:530) 先拦截同库在飞操作，`:536` 删除旧 pending；本次 POST 成功后，`:553` 才新建本次 pending，随后 GET 结算。删除修复语句后原反例立即失败。轮询、排程、`visibilitychange` 未改；唯一 POST 仍在手动 handler `:543`，自动轮询不发 POST。对照②的证明缺口见 MEDIUM。

- **(g) 未发现静态修正掩盖真缺陷，但数量自述不准确。** 实际 **13 处＝7 条 ignore＋6 处改名**：
  - app 测试 `:418/:441/:443`：三处运行时类型条件充分，属于静态收窄限制。
  - overview 测试 `:2111/:2128/:2129`：故意错型输入；其中 `why_due=None` 在 `:2138–2141` 明确验证旧路径放行，并非漏掉 corrupt 断言。
  - overview 测试 `:1053`：另有一处漏报的 `reportMissingImports`，前两行已动态加入 `scripts` 路径。
  - overview 测试 `:1375/:1447/:2106/:2435/:2549/:2576`：六处未使用绑定改名，右侧求值保持。
  
  “四文件 0 error”和后文“测试仍有 40 个既有 error”应标明各自验证 SHA／时点；本次未复跑 pyright，不能同时认定为当前结果。

- **参照系声明已经落入 docstring，原则正确。** [review_overview.py:370](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_overview.py:370) 明写 `generated_at`，`:431–433` 实际使用它。换成读取时刻后，原合法 `due_today` 到点会被 `:467–468` 拒绝，跨日还可能触发日期检查。注释将后果具体归到“到期侧逆检查”不够准确：不搬行、只换时钟时，首先触发的是**非到期侧检查**。仅对显示时间做人话化，不会改变桶或三方等式。


