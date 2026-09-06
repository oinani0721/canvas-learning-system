> 批次: BATCH-2026-09-05-第十二批 · 车道 Y9 · CARD-G3-7 round-1（⚠️ 车道未按协议 §2.1 写首部，主 session 于 2026-09-06 集成期补记；按协议本轮不计入卡族轮次配额，正文一字未改）
> 模型: `gpt-6-astra`（车道 stderr 实测） · reasoning_effort: `ultra`（车道 stderr 实测） · codex: `codex-cli 0.153.3`（车道 stderr 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <prompt>)"`（手册规定形态；实参见车道 stderr）
> 审查绑定: `0f7ffb0d`（验收单自述；正文未写 SHA）
> 会话头自证（抄车道 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal` / `model: gpt-6-astra`

---

本轮**不能判通过**：确认 2 项 HIGH，主要是读取失败放行门锁、正文内容被误认作 frontmatter。以下均为限定读取面内的静态结论；未运行测试、未修改文件。

1. **HIGH — 读取失败被当作“无真相源”，会放行写入且遗漏降级信号。**  
   [review_service.py:198](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/app/services/review_service.py:198) 捕获 `OSError / UnicodeDecodeError` 后直接 `return out`；此时虽然 `found=True`，但 `fsrs_due=None`，`reason` 仍是初始的 `"no_node_file"`。2337 行使用 `bool(fm_truth["found"] and fm_truth["fsrs_due"])`，因此门锁被判为不适用。  
   **具体路径：**节点实际有 `fsrs_due`，文件暂时不可读，缓存及加载结果为空 → 2378 行调用保存 → 496 行推进缓存、502–503 行写盘 → 2495 行标为 `"projection-cache"`，没有读取失败信号。这直接否定作者“已有真相源时一律不推进”的自述。

2. **HIGH — reader 扫描整份 Markdown，正文示例也能成为“调度真相源”。**  
   [review_service.py:197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/app/services/review_service.py:197) 先执行 `text = path.read_text(...)`，202 行直接 `re.search(..., text, re.M)`，没有提取 frontmatter 块。  
   因此，frontmatter 没有 `fsrs_due`，但正文代码示例出现顶格 `fsrs_due: ...` 时，也会阻止投影写入，并把示例日期作为权威 due 返回。参考函数接收的是 `fm`（`fsrs_bridge.py:149–155`、`daily_review_pick.py:340–342`）。**正则表达式相同成立；由此推导解析口径相同不成立。**

3. **MEDIUM — 门锁判定跨越异步等待，不能保证写入时真相源仍不存在。**  
   [review_service.py:2336](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/app/services/review_service.py:2336) 只读取一次真相源，随后有 `await self.load_card_state(...)`，保存还可能等待 `_card_states_lock`。保存函数在493–496行拿锁后直接应用 `pending`，没有重新核验 frontmatter。  
   初次检查无真相源、等待期间 vault 写侧建立了 `fsrs_due`，仍可按旧判定推进缓存和磁盘。**读取面内没有覆盖这一并发窗口；外围是否另有协调机制无法判定。**

4. **MEDIUM — PUT 对“真相源不可解析”静默，不完整传达异常。**  
   [review_service.py:1242](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/app/services/review_service.py:1242) 仅在 `fm_truth["due"] is not None and due_date is not None` 时检查分歧。reader 已能返回 `reason="malformed_fsrs_due"`，写路径却不消费它。  
   因而非法但非空的 `fsrs_due` 可以得到 `card_state_persisted=True`、`truth_source="projection-cache"`、`degraded_reason=None`。这是**异常信号遗漏**；投影确实可能写成功，不能把它直接说成谎报 frontmatter 已更新。另一个遗漏是：计算 due 为 `None` 时，1275–1277行生成返回时间，也跳过了比较。

5. **MEDIUM — census 的范围不足以支持“没有任何在线消费方”。**  
   [decision.md:22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/_bmad-output/审查/evidence-g37/decision.md:22) 原文是“三条 HTTP 路径当前**没有任何在线消费方**”，但11–16行只登记了四个目录。用户提供的项目结构另有 `frontend/src/`、`frontend/sidecar/`，准读源码还明确引用 `canvas-vault/.claude/scripts/`，均不在该 census 中。  
   **已证实的是覆盖范围不足，不是已经找到遗漏消费者。**④“backend/app 只有定义”本次也只能看到作者登记，不能独立复算。③④保留兼容入口、留待后续收敛可以作为维护理由；注释不能证明运行时隔离，mastery 注释甚至明确承认“仍在独立推进，与 frontmatter 可以任意漂移”（291–292行）。

6. **MEDIUM — 门锁独立 reason 和降级信号的 API 透传，没有被新增测试锁住。**  
   [test_g3_7_truth_source.py:218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/tests/regression/test_g3_7_truth_source.py:218) 丢弃 GET 返回值，只断言缓存、文件不变。静态分析可见：
   - 删除生产代码2369行 `gate_blocked = True`，门仍不写，但 reason 会误报为 `auto_created_not_persisted`；**新增整套测试仍可通过**。
   - 所有 GET 测试都直接调用 service；删除 `review.py:1459–1460` 的两个透传字段，新增测试仍可通过。
   - 唯一 HTTP 测试是无分歧 PUT，315行期待 `degraded_reason is None`；把 PUT 的降级透传改成恒为 `None`，新增测试仍可通过。

   **正控本身承重：**234–238行同时检查缓存、实际 JSON 内容及 `persisted=True`，足以排除“这条路径全局本来写不动”。但这一对用例单独不能排除“仅在有 frontmatter 时错误提前返回，因此没写”。

7. **LOW — 部分断言不足以证明其描述的全部性质。**  
   [test_g3_7_truth_source.py:192](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/tests/regression/test_g3_7_truth_source.py:192) 一致分支只验 source 和无报警；删除生产代码2485行的 due 覆盖，返回带微秒的投影 due，新增测试仍可通过。  
   364–365行的“不同于旧值、接近未来”不能证明返回值绑定于实际 FSRS 计算结果；384–386行将原因转为集合后只检查包含关系，不能排除多报原因或重复原因。相对而言，178行精确 due、180行分歧原因、255–258行不可解析处理，是实际承重断言。

8. **LOW — 裁定文档与实际返回层级不符，`truth_source` 的跨端点含义也不同。**  
   [decision.md:35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/_bmad-output/审查/evidence-g37/decision.md:35) 声称“service 返回值加 `truth_source`”；实际 `review_service.py:1300–1303` 明写“不在此新增 truth_source 键……由 API 层直接给出”，端点1134行才生成字段。  
   此外，GET 的 `truth_source` 表示调度归属，PUT 的 `"projection-cache"` 表示本次写入目标。因此作者将它统一解释为“这个 concept 的调度归谁管”不准确。不过 schema 已解释区别，不能仅凭字段复用判为假成功。

正常分支的信号实现有以下核实成立之处：

| GET 状态 | `persisted` | `reason` | `truth_source` / due |
|---|---|---|---|
| 有真相源、无投影卡，门锁拦截 | `False` | `truth_source_gate_no_projection_write` | `frontmatter`，due 取源值 |
| 有真相源、命中投影卡 | 按 dirty 标记判断 | 未持久化时为 `cached_state_not_persisted` | `frontmatter`，due 取源值 |
| 真相源字段非空但不可解析 | 取决于上述投影状态 | 同上述分支 | `frontmatter`、due 为 `None`，附 `truth_source_unparsable` |
| 无真相源、自动创建 | 保存结果 | 失败时为 `auto_created_not_persisted` | `projection-cache` |

这些组合由 [review_service.py:2436](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/app/services/review_service.py:2436) 至2495行明确实现。**`frontmatter + due=null + truth_source_unparsable` 是诚实表达，不能单凭 null 判假成功。**两个端点的逗号拼接也确实保留已有原因；消费者是否正确拆分，读取面内无法确认。

写点方面，准读代码中没有发现四分类之外的第五个已证实调度入口；`_save_card_states` 是①②④的共同落点，`_load_card_states` 读取快照，`get_cached_card_states` 返回副本。但 GET 调用的 `load_card_state` 实现不在准读段，mastery 的实际更新部分也在300行之后，故不能完整认证调用链与 mastery 裁定依据。

第5项 **OpenAPI 差异无法判定**：`backend/openapi.json` 及其基准差异不在允许读取表。当前 [schemas.py:977](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/app/models/schemas.py:977)、994、1044行的三个 G3-7 字段确实都是 `Optional[str] = Field(None, ...)`；这只能证明当前模型定义为可选，不能证明生成文件没有删字段、改类型或新增必填。

总评：**核实成立**的是生产 reader 真实参与种子解析、正控真实核对落盘、正常门锁 reason、读侧有效分歧时采用 frontmatter、PUT 保留计算排期，以及整秒归一实现。**不成立**的是“已有真相源时无条件不推进”、相同正则足以证明相同解析语义、门锁诚实信号已被测试充分锁定。**读取面内无法判定**的是全仓消费者完整性、④零调用、mastery 下游依据、加载函数副作用、写侧恒为整秒的来源证明，以及 OpenAPI 是否纯加性。
