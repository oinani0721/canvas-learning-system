> 批次: BATCH-2026-09-18-第十五批 · 车道 P4 · 卡 CARD-CARD-STATES-ATOMIC-WRITE round-5（末轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-CARD-STATES-ATOMIC-WRITE-r5.md)"`
> 审查绑定: `28d484b91259f8172ca4ac885e2bc3188fb1ec19`（Codex 自核「已核实 HEAD=…，全量 diff 恰三文件，生产实现与 r4 逐字节相同」）
> 会话头自证（抄 `.stderr`，括注行号；stderr 本身不入库）:
> `(L4) OpenAI Codex v0.153.3` / `(L7) model: gpt-6-astra` / `(L11) reasoning effort: ultra`
> 判定: **BLOCKER=0 HIGH=0 MEDIUM=4 LOW=2** ⇒ **D-15 达标**（绑最终代码树的一轮 B/H = 0）
> 前两次尝试因鉴权失效（401 / `Not logged in`）取得 0 字节，记录见
> `codex-review-CARD-CARD-STATES-ATOMIC-WRITE-r5-auth-blocked-attempts-1-2.md`。
> 本轮 prompt 明确要求**不读**那份记录与独立 agent 的替代报告，以保独立性。

---

**可以按你指定的 `BLOCKER=0 且 HIGH=0` 标准收官。** 当前实现未发现必须在本卡内先解决的阻断项；但不能把收官记录写成“r4 全部问题关闭、16 条门已完整绑定全部保证”。

已核实 HEAD=`28d484b91259f8172ca4ac885e2bc3188fb1ec19`，全量 diff 恰三文件，生产实现与 r4 逐字节相同。全程只读、未连数据库、未读取禁止的 r5 报告。pytest 结果取自核验后的存档；补充验证使用 AST 和内存边界探针，没有重跑整套 pytest。

**BLOCKER：无。HIGH：无。以下计数包含仍成立的已登记项。**

1. **MEDIUM｜并发门消除了原来的误红，但削弱了文件操作范围的观测。**  
   位置：[test_g3_7_truth_source.py:1193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/regression/test_g3_7_truth_source.py:1193)、`:1234–1236`。

   `_TrackingLock` 的顺序正确：先取真锁再登记、先移除登记再释放，不会因这两个间隙产生重叠误判。四次调用正常收敛时，合法过期丢弃也经过锁，因此 `entered == 4` 对该问题确实具有确定性。

   但 `overlaps == []` 现在只能证明锁持有区间互斥，无法看见锁外的文件操作。**复现思路：**把 `review_service.py:734–738` 的目录 `open/fsync/close` 阶段移到锁外，保留写入、replace、记账及清理在锁内；现有断言仍可全部通过，却不再满足整段持锁。这里“16 条仍绿”是静态逐门判断。

2. **MEDIUM｜两条新门仍有未覆盖的路径，r4 MEDIUM-1 只能部分关闭。**  
   位置：[test_g3_7_truth_source.py:1330](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/regression/test_g3_7_truth_source.py:1330)、`:1363–1382`。

   | 未被拦下的输入／复现思路 | 为什么现有门仍可绿 |
   |---|---|
   | 把 `review_service.py:733` 的水位赋值移到目录 close 之后；高序号 replace 成功、目录 fsync 失败，再发布低序号 | watermark 门只让 replace 本身失败；目录 fsync 门没有随后尝试低序号，漏掉“已经发布却没有推进水位” |
   | 在 `:1060` 原有 `to_thread` 前增加同参数同步 helper 调用 | 真正写入在主线程完成；随后线程调用因相同序号而丢弃，捕获到的名称、参数、递增整数仍全部正确 |

   内存边界探针提取了真实 helper：第一条确实使新快照被低序号覆盖；第二条使用真实 `asyncio.to_thread`，新增门末尾断言全部通过，真正发布却两次都发生在 `MainThread`。**这不是整套 pytest 实测。**

   此外，`<=` 改为 `<` 也未被覆盖，因为测试没有重复使用相等序号；当前生产单调取号不会自然触发这一输入。当前生产代码没有上述问题。

3. **MEDIUM｜已登记的共享线程池饥饿仍成立。**  
   位置：[review_service.py:722](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/app/services/review_service.py:722)、`:1060`。  
   **复现思路：**让持锁者停在慢 I/O，逐个确认后续 worker 已开始等锁再取消其协程，等待线程仍可占满共享 executor。不讨论配置修法。

4. **MEDIUM｜已登记的“replace 成功必清全部 dirty”文字仍失真。**  
   位置：[spec.md:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/openspec/specs/concept-identity/spec.md:78)、`review_service.py:732–740,1063`。  
   **复现思路：**replace 成功后让目录 fsync 失败，目标已经更新，但方法返回 `False`，dirty 没有清空；现有目录 fsync 门已经展示该路径。不评价锁死文字该不该改。

5. **LOW｜全局水位没有绑定目标文件，r4 条件性边界仍成立。**  
   位置：[review_service.py:678](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/app/services/review_service.py:678)、`:723`。  
   **复现思路：**目标 A 的低序号 worker 延迟，切换目标 B 并先发布高序号，再恢复 A；A 被误丢。需要目标切换这一额外前提，固定生产目标下不升级 HIGH。

6. **LOW｜Scenario 7 仍有未限定的“无 tmp 残留”承诺。**  
   位置：[spec.md:165](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/openspec/specs/concept-identity/spec.md:165)、`review_service.py:723–726`。  
   **复现思路：**n 已发布；n+1 写入失败且清理自身失败，留下 tmp；旧 worker 随后以 m<n 进入 helper，直接过期返回，既存残留仍在。这是静态确认的门未覆盖路径。Requirement 与 Scenario 6 新增的清理例外本身已经正确。

十段**负控输入**均只拆一个机制，存档结果如下：

| 编号 | 拆除的机制 | 红门数 |
|---|---|---:|
| 1 | finally 清理 | 4 |
| 2 | 文件 fsync | 3 |
| 4 | 文件线程锁 | 1 |
| 5 | flush | 1 |
| 6 | 对父目录同步 | 1 |
| 7 | 过期守卫 | 1 |
| 8 | 发布记账 | 1 |
| 9 | 派发前取号 | 1 |
| 10 | 线程派发 | 1 |
| 11 | replace 成功后记账 | 1 |

各组恢复后的 SHA 与当前 service 一致。1 的四条红中确实没有并发门；9、10 各只使 `before_dispatch` 红，11 只使 `watermark` 红。因此这些具体整改有效，但没有排除第 1、2 项的其他输入。

**对照输入**准确分类为 **5 绿＋8 条断言红＋3 条接口错误**，见 [redbind-r5:112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/_bmad-output/审查/evidence-card-states-atomic/redbind-r5-20260918T201215.txt:112)：

| 分类 | 门 |
|---|---|
| 5 绿 | S1、S2、S3 恢复旧值、S4、S5 |
| 7 条文件行为红 | 编码无 tmp、replace 失败清理、fsync 顺序、文件 fsync 失败、目录 fsync 失败、write 失败、cleanup 失败归一 |
| 1 条派发断言红 | `before_dispatch`：捕获四次派发，预期两次 |
| 3 条接口错误 | 并发门缺 `_card_states_file_lock`；stale、watermark 缺 `_card_states_seq`，均为 `AttributeError` |

三个接口错误不能计作对照输入的行为证据；但保留接口的负控输入 4、7/8、11 分别提供了行为红，不能因此断言这三门完全没有绑住行为。

r4 关闭状态为：

| r4 项 | 本轮判断 |
|---|---|
| MEDIUM-1 | 三个指定负控输入已覆盖；更广的行为保证仍部分开放，见第 2 项 |
| MEDIUM-2 | 合法过期丢弃造成误红已关闭；换观测点引入第 1 项覆盖退化 |
| LOW-5 | 原报告点名的 Requirement、Scenario 6 两处已关闭；Scenario 7 另有第 6 项残余 |
| LOW-7 | 已关闭，AST、Ruff、Pyright 均保存字面 argv |
| MEDIUM-3/4、LOW-6 | 仍成立，分别对应上文第 3、4、5 项 |

存档绑定还有一个需要准确表述的细节：运行首部实际记录的是 `d317b2ee…`，并非送审 SHA；但该提交到 `28d484b…` 排除 `_bmad-output` 后 diff 为空，三份业务文件完全一致，两个源码的跑前／收工 SHA 均匹配。因此可以建立内容等价绑定，前后 SHA 相等仍不能证明运行期间绝无短暂改动。

unit 新红的正文确为 [5 秒超时](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/_bmad-output/审查/evidence-card-states-atomic/unit-r5-20260918T201307.txt:392)。复测从 33 红恢复为 [32 红](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/_bmad-output/审查/evidence-card-states-atomic/unit-r5b-20260918T211849.txt:931)，唯一消失项就是 `leading_zero`，相对红基线没有新增。耗时增长支持负载解释，但没有 CPU/load 记录，“单跑 2 passed”也只有首部自述。**可确认复测未再出现该超时；高负载是合理推断，尚非独立证实的唯一根因。** 现有证据不足以将它归成本卡新增缺陷。

**本卡可按既定门槛收官，并保留以上四项 MEDIUM、两项 LOW。**

BLOCKER=0 HIGH=0 MEDIUM=4 LOW=2


