> 批次: BATCH-2026-09-07-第十三批 · 车道 U2 · 卡 CARD-PYRIGHT-DEBT-rest round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-DEBT-rest-r2.md)"`
> 审查绑定: `acbc79be`（= 阶段 1 末 HEAD；按 D-15 阶段 1 这一轮**不绑合并态**，阶段 2 末轮必绑最终 HEAD）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

复核代码 HEAD：`acbc79be059c085c945148401236d5c2a46a9433`，仅覆盖阶段 0＋1。**round-1 的 MEDIUM 已修复，未发现新的可达运行故障；尚有证据表述需要收窄。**

- **BLOCKER：无。**
- **HIGH：无。**
- **MEDIUM：无。**
- **LOW：1 条。** [negctl-p1r2-20260908T075609.txt:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u2-pyright-rest/_bmad-output/审查/evidence-pyright-rest/negctl-p1r2-20260908T075609.txt:15)：所谓“负控 4”实际只检查当前赋值位置，末行明确“未改动 OK”，未执行标题所称的移出闭包变异。将其用于证明“错误变异已被判据拒绝”时，会把未执行的验证记成通过；这不影响本轮独立确认 driver 整改成立。

**1．Neo4j 重试整改成立。**

`backend/app/clients/neo4j_client.py:610` 每次进入 `_execute_with_retry` 都重新读取 `self._driver`，因此下一次尝试可以使用重建后的连接。

`:611` 遇到 None 时，原来抛 `AttributeError`，现在抛带消息的 `AssertionError`。二者都不属于 `RETRYABLE_EXCEPTIONS` 中的三个 Neo4j 异常，均不会转成 `RetryError`，均跳过 JSON fallback 并向外抛出。**没有新增原来可恢复、现在失败的路径；但异常类型和正文确实改变，不能称逐字等价。**

**2．Claude 三处可执行逻辑恢复基线。**

`backend/app/clients/claude_client.py:290`、`:435`、`:507` 的判断和累加表达式与 `da690bf8` 相同，三个循环的 AST 也相同。可执行代码中 `TextBlock` 导入、引用均为 0；`isinstance` 改写只留下解释性注释。

整份文件并非字节相同，因为增加了注释和类型声明。负控 3 存档的恢复 SHA 与当前代码独立计算的 SHA 相同，`0→11→0` 证据成立。

**3．ignore 是 28 条，不是 25 条。**

共有 **28 个行级 ignore、29 个规则项**，因为 `suggestions.py:207` 一行指定两个规则。

未发现确定的“真错冒充假阳”新增案例：`edges.py:112`、`infra_tools.py:63/:64` 明确标为真缺陷；`suggestions.py:207` 也明示保留 `content=None` 的存量错误。`metadata.py:576` 的假阳结论仍有具体对象绑定缺口，见第 5 项。

**4．四条 assert 不能统一表述为“原位置遇 None 都会崩”。**

| 位置 | 独立判断 |
|---|---|
| `neo4j_client.py:611` | 原来直接调用 None 的 `.session()`，同样失败；异常分流不变。 |
| `metadata.py:572` | 原来 `.drop_table()` 同样失败；两种异常均被同一个 `except Exception` 捕获后继续。 |
| `metadata.py:683` | 正常 None 对应空列表，进不了该分支；若读取列表后连接被清空，原 `.open_table()` 同样失败。 |
| `intelligent_parallel.py:129` | 正常同步控制流保证单例已存在或刚构造完成；基线此处只是 `return _service`，并非属性解引用。成立的是“不变式保证非 None”。 |

四条均已有消息；未发现新增失败路径，但不能据此宣称异常行为完全不变。

**5．补充证据的效力如下。**

| 项目 | 判定 |
|---|---|
| **(a) 授权** | **足够。** 卡文明确授权 `exam.py` 延后；独立 diff 为空。 |
| **(b) 调用点** | **足以支持现有显式构造路径不受影响。** 按所贴全仓检索，两处生产构造均传四维。不能扩大成所有 schema 消费行为均不变。 |
| **(c) schema** | **五处差异成立；“对外契约零影响”尚不足。** 静态 OpenAPI 文件不含两个名称，只能证明该制品中的情况。还缺基线与当前树通过实际应用入口重新生成 OpenAPI、逐键比较的证据；孤立的 `DRIFT: none` 未交代这些绑定。 |
| **(d) SDK** | **health 足够，metadata 尚差一步。** 本地 `connect→table_names` 与实测 list 支持 `len`。两个 `drop_table` 签名证明具体类支持参数，但还需证明包装器运行时的 `_db` 确实绑定 `LanceDBConnection`；当前不能将缺口反过来认定为真错误。 |
| **(e) multiset** | **算术成立。** `356−124=232`、`232−0+0=232`、`421−190+1=232`；唯一 NEW 落在 services。它们支持诊断集合结论，不能证明运行期“零副作用”。其中阶段 0 的数字来自本轮贴文，另外两组与允许存档一致。 |

**6．位置默认机械改写未发现漏改、误改。**

独立核算 **352 处、26 个文件**，默认值及其他参数保持一致，多行形态未改坏。除 `backend/app/models/exam_models.py:150` 起四个明确的维度调整外，未发现必填 `Field(...)` 或 `default_factory` 被误动。

四维调整确实改变 schema 和缺字段时的错误内容；新增测试正是在验证这一变化。原来和现在均拒绝缺维度输入，不能把它归为严格的运行期逐字等价。存档剩余 14 处位置默认均在阶段 2 的 `system.py`。

**7．API 剩余 21 条属于阶段安排。**

`exam.py` 的 10 条有卡文直接授权；`review.py` 的 7 条、`system.py` 的 4 条由本轮明确留待阶段 2。`21＝10＋7＋4` 与存档一致，属于阶段安排，**目前不能称整个非 services 范围已经清零**。

本轮未修改文件、未连接数据库、未运行测试；测试和 pyright 结果按限定存档审阅，不代表独立复跑或最终合并态验收。
