> 批次: BATCH-2026-09-05-第十二批 · 车道 Y5 · 卡 CARD-RV-A round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-A.md)"`
> 审查绑定: 三个只读 diff 区间 `d9f7b544..8e8fd737` / `304f03ca..7283a8df` / `a5e0ce79..c8611a89`（车道 HEAD `03ac8bf8`，三面文件与各右端 SHA 逐字节相同）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/…/.claude/worktrees/card-y5-review` / `model: gpt-6-astra`

---

**四条轮询断言对给出的四种变异确有针对性，但不能据此认定完整契约都已覆盖。** 另外，计数整改仍能接受没有注册业务用例的 Node 输出；装饰器整改的“完整路径比对”自述也不准确。

本轮**实测得出**：三段 diff 的文件数、增删行数和 hunk 数与题述一致。仓库只读取了指定 diff；另做了不导入仓库的内存实验和 Node 空文件实验。题述 pytest、变异和生成器结果均未复跑。

以下行号取 diff 右端。“已见且成立”仅评价所列意见的具体回应，不表示旧审查覆盖了最终补丁。三态无法表达的“覆盖未知／整改尚未完全证明”，会明确另述，不强行判成“未见”。

**Z1**

| 位置(file:line) | 本卡判定 | 依据 |
|---|---|---|
| [test_review_app.py:268](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/tests/unit/test_review_app.py:268)：保护 `Request` | **已见且成立** | **阅读推断**：向禁止重绑定集合增加名字是单调加严；新增 `Request = str` 探针对准原问题。没有因此扩大接受范围。 |
| [test_review_app.py:518](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/tests/unit/test_review_app.py:518)：注解豁免说明 | **已见且成立** | **阅读推断**：诚实纠正“只认裸 Name”的旧说明，并明确承认 `Request.__class__`、`Request[0]` 的根名豁免没有修复。声明成立不等于缺口关闭。 |
| [test_review_app.py:470](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/tests/unit/test_review_app.py:470)：装饰器接收者 | **已见但回应引入新问题** | **实测得出**：新表达式会在第一个 `(` 截断，调用后的路径仍被丢弃；所以“完整路径比对”不成立。这里确认的是比较方式的缺陷；**完整门是否出现旧拒新允，未验证**，见下文。 |
| [test_review_app.py:862](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/tests/unit/test_review_app.py:862)：计数不变量 | **已见且成立** | **阅读推断＋实测得出**：三项算术约束确实加严，但不能证明业务用例已注册。属于整改不充分，没有新增“原拒现允”的输出集合。 |
| [test_review_app.py:2107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/tests/unit/test_review_app.py:2107)：①② clamp | **未见** | **阅读推断**：新增于存档 A 的右端之后。检查的是传给沙箱定时器的延迟，越过了纯函数层；两种常量变异直接改变该测量值。 |
| [test_review_app.py:2123](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/tests/unit/test_review_app.py:2123)：③可见性 | **未见** | **阅读推断**：检查初始隐藏时不排程，以及恢复可见后监听器回调再次 GET；没有检查已有定时器在转入后台时被取消。 |
| [test_review_app.py:2137](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/tests/unit/test_review_app.py:2137)：④零 POST | **未见** | **阅读推断**：检查固定成功响应下的首轮、五次定时器回调和可见性切换。注入 POST 正好违反被测计数，但覆盖范围小于“自动轮询整条路径”。 |

**问题①结论：支持“四个具体变异各自被对应断言检出”，不支持完整性证明。**

**阅读推断，依据题述实验结果：**

- ①变异确实破坏下限；②变异确实破坏精确的 60 秒上限。②的失败文字“一小时不问后端”与该变异不符：改成 30 秒实际是更早轮询，断言有效但诊断文字不准确。
- ③的变异只证明“恢复前台再 GET”这一半承重。删除转入后台时的取消操作，是否会被这四条检出，现有断言没有提供保证。
- ④的变异确实测到沙箱收到 POST；但没有覆盖网络失败、非 200、JSON／渲染失败、不同数据和竞态分支。切换后也没有要求 GET 达到 7，因此它在 `pollNow=false` 下仍绿是合理的。
- “真实事件”应限定为**调用沙箱保存的生产监听器回调**；这里没有浏览器原生事件分发或真实等待五个轮询周期。
- 旧实现全绿只说明旧实现也满足这些性质，不削弱回归测试价值，也不能证明本卡修过生产代码。
- 第一种变异的“其余三条”标为“未记录”，因此表格本身只完整支持后三次单杀；第一次的独立性依赖后面的文字陈述。

**阅读推断，LOW**：①使用真实时钟并截去毫秒，输入实际只有约 1–2 秒的新鲜窗口。若执行暂停足够久，会变成已过期数据并回落 60 秒，可能使正确实现偶发红。

**未验证**：harness 如何识别 POST、维护计数及模拟定时器不在读取面内，不能独立认证其捕获能力；需要授权提供相关 helper 全文。

**问题②结论：Request 整改成立；装饰器整改存在截断问题；计数整改不能完全关闭“空门假绿”。**

装饰器的最小候选是：

```python
@_PAGE_TEMPLATE.replace("x", "y").replace
def _probe():
    pass
```

**实测得出**：新表达式得到的接收者是 `_PAGE_TEMPLATE.replace`，丢掉了调用结构。独立执行此片段会在定义期因装饰器调用参数不合要求而抛出 `TypeError`。

**阅读推断**：嵌入生产代码本身已有多次 `.replace()` 链，因此同口径的 Call 检查需要处理这个接收者。这构成值得复核的新增放行候选。但 `_root_name`、允许集合和完整检查器不在读取面，**尚不能确认旧门拒绝、新门整体放行，更不能把它报成已实测 HIGH**。

计数门有确定的格式反例：

```text
$ node --test /dev/null
rc=0
ℹ tests 1
ℹ pass 1
ℹ fail 0
ℹ skipped 0
```

**实测得出，Node v24.16.0**：空文件本身被计为一个成功 test，没有注册任何 `node:test` 用例，三条不变量仍全部满足。此外，新增正则分别取各字段第一次匹配；内存实验中，前置 `tests=1/pass=1/fail=0`、后置 `tests=0/pass=0/fail=0`，仍取前组通过。

这证明通用判据存在边界，**不证明当前 `_run_node` 完整路径可被同样掏空**。新增 assert 只会收紧旧门，所以应记为原 MEDIUM 问题未充分关闭，而非新增接受路径。

**Z4-A**

存档 B 明确审过未提交的五文件 diff。**阅读推断**：哈希不匹配不能确定具体哪些 hunk 审过、哪些后来改过，不能把本面全部判为“那轮不可能看到”。

| 位置(file:line) | 本卡判定 | 依据 |
|---|---|---|
| [test_lancedb_vault_isolation.py:70](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/tests/unit/test_lancedb_vault_isolation.py:70)：M1 同一 client 两次解析 | **已见且成立** | **阅读推断**：复用同一 client，要求两个不同 accessor 值产生不同表名，恢复了对“构造时冻结 vault”这类回归的鉴别力。 |
| [test_write_side_group_guard.py:110](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/tests/regression/test_write_side_group_guard.py:110)：M2 输入隔离 | **已见且成立** | **阅读推断**：同时固定 accessor、`ACTIVE_VAULT` 和路径 basename，结构上回应了已知环境别名污染。实际实现是否只依赖这些输入，未验证。 |
| [test_metadata_subject_mapping.py:317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/tests/api/v1/endpoints/test_metadata_subject_mapping.py:317)：L1 格式出处 | **已见且成立** | **阅读推断**：文字明确区分 D16 前缀与 resolver 再拼 canvas 的组合形态，回应方向一致；历史出处和实现引用未独立核实。 |
| [test_write_side_group_guard.py:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/tests/regression/test_write_side_group_guard.py:77)：LOW 鉴别边界披露 | **已见且成立** | **阅读推断**：明确承认丢弃两个参数、走同值 fallback 仍会绿。这项披露诚实，但周围仍保留过强的路径证明措辞。 |

**问题③结论：未发现能够坐实“掩盖了真实实现回归”的证据；也不能据此认证“零实现回归”。**

**阅读推断**：把 `reload_settings` 换成 patch，确实将相应用例的覆盖缩至 accessor 下游，不再检验真实配置／YAML／accessor 的联动。但 `test_vault_switch.py:247` 仍保留真实 reload 和 accessor，只隔离到无 YAML 的输入。这说明覆盖有所分工，不能直接推出某个真实缺陷已被掩盖。

需要保留两项限制：

- **LOW，阅读推断**：`test_write_side_group_guard.py:82` 仍说 legacy 值不同“保证显式优先”，`:95` 仍说“证明别名归一化确实发生”。输出相同不能证明执行路径；409 用例能够排除无条件丢弃显式参数，却不能证明成功分支一定消费了它。新增披露诚实，整体措辞尚未完全收敛。
- **未验证**：`test_subject_resolver.py:121` 将“subject/category 必须同时提供”反转为“仅 subject 即生效”，是实质行为期望变化。新增 docstring 引用 Story 1.9，不能自行证明旧失败是假红。需要对应契约、实现片段和历史失败证据。同理，其余旧期望“已经过时”的历史归因也未独立证实。

本面其他 hunk 的旧审覆盖归属同样**未验证**；三态缺少这一选项，因此不伪造“未见”判定。

**Z4-B**

| 位置(file:line) | 本卡判定 | 依据 |
|---|---|---|
| [intelligent_parallel_models.py:286](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/app/models/intelligent_parallel_models.py:286)：补漏公开字段 | **已见且成立** | **阅读推断**：回应存档 C 的公开契约漏项，字段说明和示例确实去掉旧裸格式。实际 ContextVar／fallback 行为未验证。 |
| [metadata.py:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/app/api/v1/endpoints/metadata.py:125)、[metadata_models.py:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/app/models/metadata_models.py:53)：措辞对齐 | **未见** | **阅读推断**：在存档 C 绑定右端之后；内容与 Z4-A 的“D16 前缀＋resolver 组合形态”澄清一致。 |
| [openapi.json:1876](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/openapi.json:1876)：五对替换 | **未见** | **实测得出**：该增量为 +5/-5，共十行；四对内容能对应源码，另一次替换是生成时间戳。历史生成方式未验证。 |

**问题④结论：核心措辞一致；内容可对应，不足以证明历史上由机器生成。**

**实测得出，依据 diff 对照**：

| OpenAPI 位置 | 对应来源 |
|---|---|
| `1876` description | `metadata_models.py:53` 的字段说明 |
| `5880` description | `intelligent_parallel_models.py:286` 的字段说明 |
| `5882` example | `intelligent_parallel_models.py:291` 的示例 |
| `17905` description | `metadata.py:125` 的端点文档字符串 |
| `15682` `x-generated-at` | 时间戳元数据，不对应三份源码的文本改动 |

**阅读推断，依据用户提供的实测结果**：`DRIFT: none` 支持“按生成器当前比对规则没有漂移”，无法区分机器生成、手工写成相同内容或生成后编辑。生成器是否忽略时间戳也未核实。证明历史生成方式需要当次执行记录及输出绑定。

**LOW，阅读推断**：智能并行字段文字列举有作用域的二／四段和无作用域的 `vault:default:<subject>`，示例却是三段 `vault:cs_61b:数学`。这是示例解释不足，不能据此认定实际值非法，也不构成与 Z4-A 核心措辞的冲突。

本轮没有确认新增 BLOCKER/HIGH；但装饰器候选尚未完成全门验证，存档 A 的既有 HIGH 也没有逐项关闭证据。下述“否”表示**清零尚未获证**，不把未验证事项冒充已确认 HIGH。

BLOCKER/HIGH 清零：否


