> 批次: BATCH-2026-09-11-第十四批 · 车道 T10 · 卡 CARD-RED-HYGIENE round-6
> （= **计入 D-15 配额的第 5 轮**；r5 落 0 字节、无任何产出，按协议 §2.1「牙齿」同理不计配额）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-HYGIENE.md)"`
> 审查绑定: `b55c87e78563c833882fe1932cd7b274c155d86d`（Codex 自行 `rev-parse` 实取，未照抄 prompt 里任何 SHA；
> 其报告末行自核 `git diff --stat --no-color <审SHA> HEAD -- . ':(exclude)_bmad-output'` **输出为空、rc=0**）
> 结论: **BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 3** —— 绑最终 HEAD 的一轮 B0/H0 ⇒ **D-15 达成**。
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，逐行括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）
>
> ⚠️ **本轮为什么存在**（与 r5 的关系）：r5 于 2026-09-16 23:51 落 0 字节（账户级配额在报告生成阶段耗尽），
> 当时依协议 §1 转「主 session 人审替代，不等配额」。2026-09-17 02:51 接手 session 按台账
> 「外部服务的重置时间是一次观测不是不变量」**先复测再决定**：同模型同端点最小请求 `rc=0` / 17s / stdout `OK`
> ⇒ 配额已恢复，r5 存档里 "try again at Sep 19th" 那句观测**再次被证伪**（本卡内该教训第二次应验）。
> 配额既已恢复，就不该用「人审替代」去补一件外审本可做到的事 ⇒ 补送本轮。
> 本轮 `rc=0`、跑满 8 分 27 秒、stdout **11,684 字节**（与 r5 的 0 字节对照）。
> ⇒ 本轮**消除了终审对 D-32 例外的依赖**：r4 只绑 `ef21be2c`，其后 `test_agents_health.py` 有字面 +22/-5
> 的 docstring 改动，终审绑定在**字面上**已破、只能靠 D-32 撑；本轮直接绑最终 HEAD 且 diff 为空。

---

本轮结论：**BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 3**。新增的六条替代技术声明成立；剩余发现属于文档和证据一致性问题，建议登记移交，不要求继续修改代码送审。维持撤销 r1 HIGH-1。

全程未修改文件。审查绑定实取 HEAD `b55c87e78563c833882fe1932cd7b274c155d86d`。目录级独立重跑受只读环境限制，未完成；下文明确区分实跑和存档复算。

**BLOCKER: 0**

**HIGH: 0**

未发现本卡引入的生产回归或安全缺陷。candidate422 的相同哨兵失败已存在于 `$PREV` 入库日志，不能归为本卡新增 HIGH。

**MEDIUM: 1**

1. **MEDIUM-1：验收单仍保留过期自审计数，并把未经独立确认的解释写成事实。**

   位置：[验收单 §5.0，第 495 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/验收单/UAT-CARD-RED-HYGIENE-2026-09-16.md:495)。

   独立执行 `PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -c …`，按 `SELF-REVIEW` 表格列解析：“成立”必须包含“成立”且不包含“不成立”；翻转还须工作流列明确为“不成立”。结果：

   ```text
   数据行=20
   工作流判成立=2行
   主session判成立=19行
   不成立→成立=16行
   ✅处置=15行
   含登记=3行
   ```

   验收单仍写 **17 / 14**；还声称验证 agent 正文已确认事实、只是因严重度 LOW 判不成立。然而来源文件第 125–126 行已承认：**未保留 verifier 正文，该解释未经独立确认**。

   同类残留在验收单第 411 行：R3 探针写成“通过 2／报红 17”，原档逐格实数为 **通过 3／报红 16**。

   **失败场景：**仅依据验收摘要评估自审质量，会得到与来源表、证据限制不一致的结论。  
   **建议：登记移交。**同步派生数字和证据限定，不再要求代码整改。

**LOW: 3**

1. **LOW-1：撤回与结果更正仍未同步到两份回应原件。**

   - [RESPONSE-r1，第 101–104 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-red-hygiene/RESPONSE-codex-r1-20260916.md:101) 仍正面声称“使门通过时两者必然一致”，没有针对该句的撤回指针。
   - [RESPONSE-r4，第 99 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-red-hygiene/RESPONSE-codex-r4-20260916.md:99) 仍称最终 SHA 两跑都是 `>`＝0、`blocked=0`。

   实跑 `rg -n '穷尽|必然一致' …`，并解析两份 `FINAL-R4-unit-close-run*.txt`：

   ```text
   run1: 34 failed，blocked=0
   run2: 35 failed，blocked=1
   ```

   **失败场景：**再次引用历史回应时，会复用已被反证的保证或错误运行结果。历史定位不能替代撤回标记。  
   **建议：登记移交。**保留历史正文，补明确撤回指针。这里确实找到了题述三处之外的残留。

2. **LOW-2：当前测试 docstring 仍引用已经删除的旧 helper。**

   位置：[test_agents_health.py，第 660–661 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/api/v1/endpoints/test_agents_health.py:660)，符号 `test_mock_expected_templates_match_production_truth_source`。

   `rg -n '_assert_not_mutated_after_binding'` 核实当前文件只有该引用，没有定义。实际执行路径已是 `_collect_writes()` → `_production_expected_templates()`。

   **失败场景：**维护者按现行说明定位写入检查，会追到已不存在的实现。  
   **建议：登记移交。**这是文档遗留，不影响当前检查实际报红。

3. **LOW-3：W4 协议引用未说明来自另一工作树。**

   位置：[验收单第 120 行附近](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/验收单/UAT-CARD-RED-HYGIENE-2026-09-16.md:120)，以及第 367–377 行。

   检查当前车道及 `git show f294878b:.claude/rules/card-batch-protocol.md`，均没有所引“第 79 行”的 W4 条款。独立读取 `feature-obsidian-hybrid-dev` 工作树，则其第 79 行确有该条款。

   **失败场景：**仅检出被审 SHA，无法按文内相对路径复核所引用的规则。  
   **建议：登记移交。**补来源工作树和版本。规则确实存在，不判为伪造；其中 `grep -c "blocked="` 的既有缺陷仍不能作为次数证明。

**九个反面问题的逐项回答**

1. **退役是否漏消费方：未发现仓内遗漏。**

   独立 `git grep`、生产代码动态 `getattr` AST 扫描及 Settings 序列化调用检查，未发现这两个键的消费路径；相关动态配置键是 `AI_PROVIDER_{i}_*`。被排除目录的命中属于文档、研究包和历史记录。

   `Settings.model_config` 为 `extra="ignore"`。真实 Settings 的内存探针分别经构造参数、进程环境和 `DotEnvSettingsSource` 注入旧键，均被忽略，属性与 `model_dump()` 都不含它们；dotenv 正控键确实生效。旧部署 `.env` 留着这两个键不会继续控制重试参数。仓外消费者不在本次证明范围内。

2. **鉴权断言是否恒真：单独零调用不足，现有对照有效。**

   拒绝组单独看，错误 patch、错误端点或 body 校验失败都可能造成零调用。但对照组使用相同 payload、端点、配置和 spy，仅移除鉴权依赖，并要求 **200 且 spy 被 await**，能排除这些共同错误。

   patch 对应真实 handler 的 `litellm.acompletion` 调用点。对照结束时先 pop 鉴权覆盖，fixture teardown 再 `clear()` 全部 overrides，不遗留 `get_settings`。零 await 的直接证明范围仍仅是“未到该次 LLM 调用”。

3. **guard 是否还有漏面：有，且本轮已直接证实。**

   它只钉绑定处字面量，不能保证运行时名单一致。两个最终断言都非恒真：等长改名会击中相等断言；长度变化会击中长度约束或相等比较。

   从常量或文件读取会因非字面量形态报红；非字面量元素会使 `ast.literal_eval` 抛异常，测试失败，不会静默通过。空字面量也不能通过完整 guard。

4. **目录级是否没有 `>`：不能这样声称。**

   本轮确实执行了指定命令：

   ```sh
   cd backend
   PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest tests/unit \
     --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider
   ```

   在收集前退出，`rc=1`，错误为 `FileNotFoundError: No usable temporary directory found`。因此**没有独立目录运行结果**。

   对原始存档独立复算：

   ```text
   BASE：64个唯一nodeid＝35 FAILED＋29 ERROR
   R5存档：35个红nodeid
   BASE-only：30
   R5-only：1，candidate422
   ```

   `$PREV` 入库的 integ5 第 601 行已有同一 candidate422 指纹，第 1143 行已有 `blocked=1`。EPW 34 条与本卡 R3 的 34 条逐项相同；integ5 则是 65 条，不能混成同一红集。维持撤销 HIGH 的依据是这些历史原始证据。

5. **pyright 是否被跳过：提交历史仍 PARTIAL，当前实跑通过。**

   成功 commit1 的原始 hook 输出没有保留，不能追认“那次必然实跑通过”。后续仅改测试或文档的提交不命中 `backend/app/*.py`，属于 glob skip；这与工具缺席不同。

   本轮默认 Node 缺动态库，随后仅为该进程指定现成 Node v24.16.0，执行绝对路径 `pyright app`，结果：

   ```text
   0 errors, 81 warnings, 0 informations
   rc=0
   ```

   未安装工具、未修改共享环境。

6. **两条 flaky 和契约红是否应在本卡处理：登记移交正确。**

   相关文件对 `$PREV` 无改动，且明确超出六文件地盘。契约测试在打开已删除 schema 时就失败，尚未进入 pattern 比较。现有材料不能把它们归为本卡新引入缺陷；也不能用少量全绿跑次证明 flaky 根因已解决。

7. **六条替代声明是否成立：成立；原探针逐行等价仍不可追认。**

   本轮直接加载当前测试文件，内存替换 `inspect.getsource`，调用真实 `_production_expected_templates()`，进一步调用**完整 guard 测试**，没有复刻取值算法。以当前 13 项名单为初值：

   | 输入 | 完整 guard | 执行输入函数的结果 |
   |---|---|---|
   | `match` 星号捕获 | 通过 | 名单被替换 |
   | 类体调用 `.pop()` | 通过 | 少一项 |
   | 已触发的 `except … as expected_templates` | 通过 | 异常块后名字被删除 |
   | `import math as expected_templates` | 通过 | 变为模块 |
   | `def expected_templates(): …` | 通过 | 变为函数 |
   | 推导式局部同名变量 | 报红：绑定数 2 | 外层名单不变 |
   | 赋值后追加无右值注解 | 报红：绑定数 2 | 名单不变 |
   | 切片副本写下标 | 报红：其它写入 | 名单不变 |

   `.append()` 正控确实报红；仅有纯注解时，当前实现确为 `binds=1`，红在无法取得普通赋值字面量。

   原 R5 存档没有保存探针源码和精确输入，只留下临时脚本占位路径，因此不能声称逐字审过原脚本、证明其复刻完全等价。**本轮直接运行真实完整调用点，已独立确认这些技术结论，排除了结论只能由复刻偏差产生的疑虑。**

8. **还有撤回遗漏吗：有，见 LOW-1。**

   R1 回应仍留“必然一致”。当前代码、R4 存档新增撤回批注、验收单 §六.11 的主要整改成立；R4 存档原有 26 格正文未被改写。

9. **旧实现证据是否仍被当作当前依据：主体版本对应已修正。**

   Git 对象确认 R3 是枚举语句实现，R4 是 `ctx` 实现；早期 `guard-ast-shapes` 已明确降为逻辑副本过程记录。验收单 §五的 R3 引用处于历史轮次小结，不应误报为当前证据。当前遗留是 LOW-2 的旧符号引用，以及 MEDIUM-1 的格数错误。

**其余验收核对**

- r4 至当前仅两个 docstring 块改变。独立 AST 复算：保留 docstring 时不同；去除后逐字相同，长度均为 **43367**。
- 累计代码面恰好为允许的 **6 文件**；六文件 HEAD blob 与工作树逐字相同。OpenAPI 与 `$PREV` 相同，且本轮只读生成比对得到 `DRIFT: none (paths=197 schemas=357)`。
- `ruff check --no-cache` 五个 Python 文件通过。格式检查仅 cache configuration 文件失败；独立计算实际改行是 `$PREV` **284–286**、`8bfcdfce` **247–249**、当前 **250–252**，三版文本相同，与本卡实际改行交集为空。
- health 红绿、等长改名负控及 auth 三段负控存档的失败身份与主张吻合；负控前后哈希相同。它们属于**存档核对，不是本轮 pytest 独立重跑**。
- cache 测试数从 **15／5 xfail** 到 **13／4 xfail**。RED 的 `3 failed, 7 passed, 5 xfailed`，删除其中一条失败及一条 xfail、修好两条失败后，成为 `9 passed, 4 xfailed`；没有把删除记作转绿。
- 第 0 分钟干净状态及成功 commit1 的 hook 历史保持 **PARTIAL、不追认**；现有 Git 对象不能恢复当时未记录的工作树状态。
- 两份 `SUPERSEDED` 的作废理由和替代证据相符。r5 无结论的存档不能计为通过或失败；本轮按第 5 个有结论轮次处理。

**绑定声明：本次审查 SHA＝`b55c87e78563c833882fe1932cd7b274c155d86d`；实跑 `git --no-pager diff --stat --no-color b55c87e78563c833882fe1932cd7b274c155d86d HEAD -- . ':(exclude)_bmad-output'` 输出为空、rc＝0；不带 `--stat` 的绑定自核同样为空、rc＝0。**


