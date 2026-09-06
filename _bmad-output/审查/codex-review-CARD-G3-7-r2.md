> 批次: BATCH-2026-09-05-第十二批 · 车道 Y9 · CARD-G3-7 round-2（⚠️ 车道未按协议 §2.1 写首部，主 session 于 2026-09-06 集成期补记；按协议本轮不计入卡族轮次配额，正文一字未改）
> 模型: `gpt-6-astra`（车道 stderr 实测） · reasoning_effort: `ultra`（车道 stderr 实测） · codex: `codex-cli 0.153.3`（车道 stderr 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <prompt>)"`（手册规定形态；实参见车道 stderr）
> 审查绑定: `ecfcc3f1`（正文首行自证；审后 08fed737 整改 5 条未复审，车道已登记）
> 会话头自证（抄车道 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal` / `model: gpt-6-astra`

---

**绑定 HEAD：`ecfcc3f1e1c6933d4c5b6016fab0957aa9d6c0b9`**  
复核结束于北京时间 2026-09-06 14:40。首尾 HEAD 一致，被审文件与 HEAD 一致。工作树另有未跟踪的 `_bmad-output/审查/codex-review-CARD-G3-7-r2.md`，所以“工作树干净”并不完全属实；本轮未读取或修改它，未运行测试。

**结论：1 HIGH、2 MEDIUM、2 LOW；未发现 BLOCKER。不支持将本轮整改认定为全部闭合。**

1. **HIGH — [review_service.py:219](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/app/services/review_service.py:219)：节点路径定位失败仍会放行投影写入，r1 HIGH-1 修复不完整。**

   `out` 在 208–214 行初始化为 `governed=False`、`reason="no_node_file"`；定位异常却仍执行：
   ```python
   except (OSError, ValueError):
       return out
   ```
   [frontmatter_signals.py:38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/app/services/frontmatter_signals.py:38) 的定位操作实际调用 `p.exists()`，涉及目录访问和文件元数据探测。

   因此，**节点实际存在且含 `fsrs_due`，但定位阶段发生权限或其他 I/O 异常**时，GET 在 2398–2399 行得到“无真相源”；若缓存、持久化加载均未命中，2440–2442 行仍调用 `_save_card_states`，后者在 534 行推进缓存、540–541 行写盘。保存成功、真实 FSRS 库可用时，还会返回 `truth_source="projection-cache"`，没有 `truth_source_unreadable`。

   225–232 行的 fail-closed 只保护**定位成功后的内容读取**。新增测试 317–341 行只对文件本身 `chmod(0o000)`，没有覆盖定位失败。这是源码可推出的故障路径，并非声称当前磁盘正在发生故障。

2. **MEDIUM — [review_service.py:2398](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/app/services/review_service.py:2398)：门锁跨等待使用旧判据，“有真相源时一律不推进”仍不成立。**

   真相源只在 2398 行读取一次；其后经过 `await self.load_card_state(...)`，保存时还要等待 `_card_states_lock`。若在此期间 frontmatter 首次出现 `fsrs_due`，当前 GET 仍按旧的 `has_truth_source=False` 写入默认卡。

   这不是推测出的新场景：2391–2397 行自己明确写着“**若这期间 vault 侧刚写出 fsrs_due，本次仍按旧判定推进投影**”。[decision.md:70](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/_bmad-output/审查/evidence-g37/decision.md:70) 也标为“登记不修”。因此，整改成立的是**承认并登记窗口**，不是关闭窗口。

   D0 文档第 66 行仍写“一律不写盘、不推进”，范围过宽；验收单 §12 第 152 行仅写“并发面未证”，没有准确转述这条已经识别的放行路径。本项只评价当前 GET，不评价后续卡的设计。

3. **MEDIUM — [验收单:199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/_bmad-output/验收单/UAT-CARD-G3-7-2026-09-06.md:199)：hook 证据不足以证明“41 条全为存量”及没有新增格式问题。**

   203–208 行的证明只有“错误行号 ∩ 本卡改动行集合 = 0”。修改类型、返回值或调用契约，可以让新增错误出现在**未修改的调用行**；零交集不能证明零新增。这里缺少基线与最终 HEAD 在相同条件下的诊断集合对照。

   格式检查也一样：193–195 行三个文件均为“基线 rc=1、工作树 rc=1”，只能证明基线已经失败，不能证明本卡没有增加格式问题。

   171、215 行明确承认违反禁止 EXCLUDE 的条款并跳过两个 hook，**披露是诚实的，免责结论未获充分支持**。我没有据此认定确实新增了 41 条错误；同样不能认证它们全部属于存量。

4. **LOW — [schemas.py:1063](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/app/models/schemas.py:1063)：公开字段说明没有完整跟上新的 degraded 语义。**

   PUT 的 `degraded_reason` 仍描述为“`Set when card_state_persisted=false`”，只列两个持久化原因；实际 1287–1309 行在投影保存成功时，也会返回分歧、不可解析或不可读原因。

   GET 的 997–1003 行遗漏 `truth_source_unreadable`；980–985 行又把 `frontmatter` 描述成已经确认节点携带 `fsrs_due`，没有涵盖“文件不可读，保守认定归 frontmatter 管”的第四态。**运行时代码有信号，字段说明不完整**，容易让消费者错误解释组合值。

5. **LOW — [decision.md:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/_bmad-output/审查/evidence-g37/decision.md:91)：扩面整改后的 census 声明和回归用例计数仍有残留漂移。**

   同文 15–24 行已经列出 `frontend/src`、sidecar、src-tauri、vault scripts 等扩面，并声称做了全仓兜底；91 行及验收单 146、148 行却仍写“四个目录”。所以用户转述的“四目录 census”已不是当前裁定文档的完整自述。

   当前测试源码共有 **18 个测试函数**；[D0 文档:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/docs/fsrs-truth-source-d0-revision.md:59) 仍写 12 用例，[known-gotchas.md:139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/docs/known-gotchas.md:139) 仍写 11 用例。这属于存档不同步，不代表测试不存在。

**其余问题的独立核对结果如下。**

**写点与 census：**指定行段内，没有发现第五个可确认的独立推进入口。PUT、GET auto-create、`save_card_state` 三处共用 `_save_card_states`；`_load_card_states` 只读取，`get_cached_card_states` 返回字典副本。但 mastery 获准正文止于第 300 行，未覆盖完整赋值过程，不能认证其全部写操作。

`save_card_state` 的“隔离”确实仍在 2336 行直接保存；mastery 注释也明确承认“仍在独立推进”。因此，**这是标注和延期处置，不是运行时阻断**。保留既有测试/spec 契约的理由可以解释选择，但相关调用方、测试、spec 不在本次读取面，不能认证“零调用方”“五处在线读方”或“唯一可落地解”。当前 census 已明确排除动态 URL、仓外客户端；四目录扫描本身也不足以证明全局零在线消费者。

**信号与返回排期：**普通分支的整改成立：

| 情形 | 已核实行为 |
|---|---|
| 有真相源、无投影卡、门锁拦截 | `persisted=False`，专用 reason 为 `truth_source_gate_no_projection_write`，没有谎报写失败 |
| 真相源不可读或不可解析 | `truth_source="frontmatter"`、`due=null`，分别报告 unreadable/unparsable；这组值本身不是假成功 |
| 投影卡已持久化、调度归 frontmatter | `persisted=True` 与 `truth_source="frontmatter"` 可以同时成立，二者描述不同事实 |
| PUT 保存成功但排期分歧 | API 标 `projection-cache`，保留本次计算值，追加分歧信号 |

PUT 的 1306–1309 行、GET 的 2556–2559 行都保留已有 degraded 原因再追加，未见当前拼接代码吞掉旧原因。[review.py:1134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/app/api/v1/endpoints/review.py:1134) 与 schema 1047–1057 行也明确限定 PUT 写的是投影。因此，**不覆盖 PUT 的 `next_review_date` 与当前公开契约一致**；不能仅因它不同于 frontmatter 再判错误。不过，“frontmatter 必然是旧值”并无时序证据，应称权威当前值与本次计算值不同。

**测试承重：**[测试文件:97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/tests/regression/test_g3_7_truth_source.py:97) 至 104 行建立真实临时 vault、写入 `.md`；143–150 行调用真实生产 reader；127–129 行使用真实 FSRS manager 创建和序列化卡。没有用替身 reader 自证。

门锁负例 219–233 行先确认缓存 miss、无文件，再检查内存、磁盘及精确 reason；正控 246–250 行检查真实 JSON 内容和 `persisted=True`。**这一对足以区分普通路径上的门锁生效与普遍写不动。**

仍需区分以下不承重或覆盖不足之处：

- 缓存命中测试 177–180 行锁住 due 和信号，未检查内存、磁盘不变，不能证明缓存命中链无副作用。
- 现有用例没有覆盖“库缺失 × frontmatter”的 GET 组合；删除 GET 拼接中的旧原因保留逻辑，真实库路径用例仍可能通过。
- 一致分支 196 行已补精确 due 断言，但种子未强制投影微秒非零；当投影恰为整秒时，删除一致分支覆盖仍可能通过该断言。
- PUT 的 507–508 行只证明不是旧日期且日期足够新，不能证明它精确等于本次 FSRS 计算结果。
- 不可读测试在 325、561 行可能 `skip`；源码存在用例不等于该环境实际执行过。

**§12 还应补充的边界：**第 149 行披露了 stability 等字段仍来自投影，但没有明确说 **`card_state` 内的排期也仍来自投影**：service 第 2496 行原样返回 `card_data`，API 第 1449 行原样转发，后续只替换外层 due。因此同一响应仍可能携带两份不同排期；本读取面不能证明有在线消费者误用它。

此外，第 2372–2379 行在 manager 未初始化时，会在读取 frontmatter 之前返回 `fsrs_not_initialized`；合法权威 due 并不能保证被返回。`load_card_state` 的实现、GET 第 2570 行之后的异常处理也不在授权范围，不能认证全部异常路径和加载副作用已经闭合。

**解析与文档/OpenAPI：**字段正则与允许读取的两个参考 reader 相同，当前代码也确实先截取 frontmatter 块再查字段，正文误识别整改成立；整秒 UTC 比较实现成立。但参考范围没有包含桥接写侧的整秒实现或 picker 的块切分实现，无法独立认证“写侧恒为整秒”和“块切分逐字同源”的全部依据。

指定基线 diff 则可明确确认：

- D0 文档仅新增勘误注和 G3-7 小节，没有修改既有句子。
- OpenAPI 仅新增三个可选、可空字符串属性：GET 的 `degraded_reason`、`truth_source`，PUT 的 `truth_source`，另更新时间戳；没有删除字段、增加必填或改变既有类型。

总评：**正文解析、普通门锁正负控、专用 reason、异常信号转发及加性文档/OpenAPI 已核实成立；完整 fail-closed、无条件不推进、hook 全属存量的证明不成立。** census 数量与在线性、隔离理由引用的外部证据、完整加载和异常链，在限定读取面内无法判定。验收单“完成、可解锁”的自报不能替代这些未闭合证据。


