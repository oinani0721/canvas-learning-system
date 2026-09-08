> 批次: BATCH-2026-09-07-第十三批 · 车道 U2 · 卡 CARD-PYRIGHT-DEBT-rest round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-DEBT-rest-r1.md)"`
> 审查绑定: `41cc849c`（= 阶段 1 末 HEAD；按 D-15 阶段 1 这一轮**不绑合并态**，阶段 2 末轮必绑最终 HEAD）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

本轮在限定读取面内确认 **1 项 MEDIUM**，不能将阶段 0＋1 判为“运行期行为不变”。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM**

- [backend/app/clients/neo4j_client.py:599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u2-pyright-rest/backend/app/clients/neo4j_client.py:599)：把 `driver` 固定在重试循环之外，改变了原先每次重试读取 `self._driver` 的行为。请求 A 等待重试期间，若 `cleanup()` 关闭旧连接、请求 B 随后初始化新连接，A 在 `:609` 仍向已关闭的旧实例开启 session，无法采用已经恢复的新连接；这不是纯类型改动。

**LOW：无。**

九问的核对结果如下：

| 问题 | 判断 |
|---|---|
| **1．25 条 ignore** | 独立计数确为 **25 条行级 ignore**，未发现已证实的“真错误误标假阳”。`edges.py:112`、`infra_tools.py:63/64` 等已有明确缺陷登记。但 `metadata.py:574` 的 SDK 签名、`health.py:1169` 的实际返回类型不在允许读取面，清单里的“实测”不能算本轮独立验证。 |
| **2．四处 assert/绑定** | 实际是 **三个 assert＋一个 driver 绑定**。`metadata.py:570` 遇 None 时仍被同一 `except Exception` 捕获并继续，但异常从 `AttributeError` 变成无消息的 `AssertionError`，日志内容有变化。`:681` 的 None 情况被空列表分支挡住；`intelligent_parallel.py:129` 位于成功构造或复用之后，未发现新截断路径。driver 问题见 MEDIUM。 |
| **3．四维必填化调用点** | **不能确认全仓无遗漏**：未修改的 services、其他测试及 MCP 调用点不在读取面。新增测试覆盖显式构造和 `**kwargs`；另隔离核对 `model_validate`，缺四维时前后都失败，只改变错误位置。未发现正常验证构造的成功输入集合收缩。 |
| **4．OpenAPI 证明强度** | **不足以证明全键不变。** 独立核对还确认 `exam_models.py:150–153` 给四个属性新增了 `description`，模型 JSON Schema 除 required 外确有变化；是否进入实际 OpenAPI，本轮无法确认。纯机械改写部分则有下面的独立 AST 证据支持。 |
| **5．循环 import／单例** | 未发现新增问题。`TYPE_CHECKING` 导入运行期不执行，返回注解是字符串，原有单例创建和初始化逻辑保留。 |
| **6．litellm 缺席降级** | **仍在。** `llm_call_logger.py:43–51` 运行期仍捕获 `ImportError`、采用 `object` 基类，构造函数仍跳过相应 `super()` 调用。 |
| **7．位置默认机械改写** | **核对通过：352 处／26 文件**，默认表达式及原关键字逐字保留；570 个原有必填 `Field(...)`、108 个其他 `default_factory` 调用未被误动。与扫描的 **366→14** 一致，剩余 14 处属于共享文件。 |
| **8．ContentBlockParam 收紧** | 未发现新增合法输入拒绝。`images` 入口仍含 `Any`，局部注解不会校验或转换 MIME；`img.get(...)` 缺键仍默认 PNG，显式 `None` 仍原样传递。另外，“只有 TextBlock **声明** text”不足以证明实例不可能带额外属性，故不能独立背书 `hasattr` 与 `isinstance` 的无条件等价。 |
| **9．api 延后是否放宽** | **当前只能认定仍有 21 条未完成，不能认定豁免已经成立。** 原卡 §三不在读取面；若明确允许延后 `exam.py`，属于阶段安排；若只允许延后两个共享文件，额外剔除 `exam.py` 就是放宽。验收单自述不能替代原始授权依据。 |

两份 multiset 的实际末行仅为 `rc=1`、`rc=0`，因此未将验收单转述的 NEW/GONE 数字标为独立验证。全程未修改文件、未连接数据库、未运行 integration/e2e；本轮不作最终 HEAD 放行结论。


