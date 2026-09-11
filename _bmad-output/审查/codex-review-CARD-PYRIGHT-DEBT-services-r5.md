> 批次: BATCH-2026-09-07-第十三批 · 车道 U1（card-u1-pyright-svc）· 卡 CARD-PYRIGHT-DEBT-services round-5（阶段 2 末轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-DEBT-services-r5.md)"`
> 审查绑定: `d7790f4b`（代码最终 HEAD = `ccd2a4d1`；`d7790f4b` 仅多一个 `_bmad-output` 文档 commit，
> `git diff --stat ccd2a4d1 d7790f4b -- . ':(exclude)_bmad-output'` 为空。Codex 正文首句已自证「其 services 树与 ccd2a4d1 完全相同」）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**本轮：B0 / H0 / M3 / L4。** 复核绑定当前 HEAD `d7790f4b48f2ab91cf933f54147d1afb5c244454`；其 services 树与 `ccd2a4d1` 完全相同，工作区 services 无修改。全程只读，未连接数据库或运行测试。

**BLOCKER**

（无）

**HIGH**

（无）

**MEDIUM**

1. **[difficulty_matcher.py:234](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/difficulty_matcher.py:234)：`cast(str, …)` 确实隐藏了可空内容的类型债，不能称为已证明安全的窄化。** LiteLLM 的 `Message.content` 允许 `None`，此处没有内容守卫，仍会在 `.strip()` 抛出 `AttributeError`，随后记录错误并回退到 `0.5`；非流式返回 `ModelResponse` 并不保证其中的内容是字符串。[官方定义](https://github.com/BerriAI/litellm/blob/main/litellm/types/utils.py)

2. **[review_service.py:1239](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/review_service.py:1239)、`:2135`：“生产零调用方／传递性零曝光”超出了证据能支持的结论。** 搜索 `.generate_verification_canvas(` 会漏掉方法取出后通过别名调用、回调注册、字符串反射等方式，而允许读取的材料不足以排除这些入口；可靠表述应是“未发现直接生产调用，动态可达性未证”。

3. **[lefthook-blocked-raw-phase2-20260911T084608.txt:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/_bmad-output/审查/evidence-pyright-svc/lefthook-blocked-raw-phase2-20260911T084608.txt:47)：hook 存档不支持“完整原始输出、报错全部 PEND0”的说明。** 文件明确包含已登记为真缺陷的 `agentic_rag.embedding.embedding_service`，且可见诊断只有 **15 errors／11 warnings**，汇总却是 **19／20**；第二份也缺少汇总所称的两条 warning，因此遗漏项无法独立归属。

**LOW**

1. **[canvas_service.py:341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/canvas_service.py:341)：“同被 except 捕获，所以逐字不变”不成立。** 若 `None` 到达，`:358` 的日志原因会从原 `AttributeError` 文本变成空字符串；正常入口确有非空守卫，当前未证实存在生产重新置空路径，因此这是注释错误和条件性差异，尚不能判为生产回归。

2. **[review_service.py:87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/review_service.py:87)：删除 `CardState` 包含运行期模块接口变化。** 删除导入及兜底赋值会移除该模块属性，也移除了导入成功对该符号的要求；即使没有消费者，也不能据此称为纯注解变化，而“全仓无人导入或 patch”在本轮读取面内未获独立验证。

3. **[multimodal_service.py:310](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/backend/app/services/multimodal_service.py:310)：替换常量合理，但“遵循仍有效的弃用信号”解释不准确。** Pillow **9.4 已撤销 `Image.LANCZOS` 的弃用**，12.0 源码仍从枚举生成值为 `1` 的模块级常量，因此这里属于兼容类型声明的等值替换。[官方撤销说明](https://pillow.readthedocs.io/en/stable/releasenotes/9.4.0.html#constants)、[12.0 源码](https://github.com/python-pillow/Pillow/blob/12.0.0/src/PIL/Image.py#L173)

4. **[验收单:735](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc/_bmad-output/验收单/UAT-CARD-PYRIGHT-DEBT-services-2026-09-08.md:735)、`:964`、`:1135`：数量混用了编辑位置、缺陷类别和不同版本。** 表内数字相加是 **34 而非 24**，“8 条中 6 条真缺陷”实际是 **7 条对应 4 类缺陷**，而 `GONE=220` 对应旧的 `420→200`；若最终确为 `420→198、NEW=0`，则应为 **222**。

8 条 ignore 的逐条核对如下：

| 位置 | 结论与依据 |
|---|---|
| `review_service.py:1243` | 保留既有缺陷的理由成立：允许点读的 `CanvasService` 没有 `get_canvas`，改成 `read_canvas` 会改变行为；死路径结论仍未证实。 |
| `review_service.py:1613` | 防御转换理由成立：`TypeError/ValueError` 被紧邻 handler 捕获并回落到 3，ignore 比声称输入一定可转换的 cast 更诚实。 |
| `review_service.py:2141` | `canvas_name` 确非 dataclass 字段，修正会改变运行行为。 |
| `review_service.py:2142` | `from_node` 确非字段，同上。 |
| `review_service.py:2143` | `to_node` 确非字段，同上。 |
| `review_service.py:2144` | `label` 确非字段，同上。 |
| `multimodal_service.py:1427` | 承重记录成立，但“运行期永久不存在”尚未独立验证：允许读取面不含包树与安装解析环境。 |
| `learning_context_service.py:205` | 缺参理由成立：允许点读的定义明确要求 `query`，本处未传且捕获 `TypeError`；所称生产端点不在读取面，入口可达性未独立确认。 |

这些具体 rule 没有发现可进一步细分到单条消息的写法；也未发现能在**严格保持行为**的同时真正修复上述缺陷的替代方案。承重 **8/8** 只能证明抑制有效，不能证明抑制理由正确。

`EdgeRelationship` 调用行删除 ignore 的依据成立：Pyright **1.1.411 和 1.1.414** 都遍历诊断 range 覆盖的各行寻找匹配 rule，因此四个参数行确实还会压住“缺三个必填参数”这一条**已登记的附带诊断**。未找到现存配置／版本反例；未来若诊断范围收窄到调用首行或 rule 改名，可能重新出现，升级时需要复验。[1.1.411 实现](https://github.com/microsoft/pyright/blob/1.1.411/packages/pyright-internal/src/analyzer/sourceFile.ts#L1014)、[1.1.414 实现](https://github.com/microsoft/pyright/blob/1.1.414/packages/pyright-internal/src/analyzer/sourceFile.ts#L1062)

其余源码核对：7 处重命名涉及的 6 个函数中，未发现旧名或新名被同作用域、闭包、f-string、`locals()`／`eval` 读取；归一化重命名、注解和 cast 后，相关函数 AST 一致。`review_service` 三处 `Any` 沿用了既有属性守卫，未找到具体错类型反例；`Sequence` cast 有 `fetchall()` 返回列表的实现依据。未发现既有业务判定行被修改，但新增 assert、删除模块属性和更换常量引用意味着严格的“全是类型层编辑”说法不成立。

总评：**未发现已证实的新生产回归，但不能无保留确认“类型债真实清零、所有验收门已独立复算”。** 指定多重集仅提供绑定 `0188c4e5` 的三行摘要，最终 `NEW=0` 无法独立重算；指定 tests 差集仍使用作废基线，虽然干净基线的 64 个失败 nodeid 可重算，最终干净差集不在读取清单。预期的 35 条残余没有计入发现；当前源码 HEAD 绑定成立，上述证据与表述问题仍需闭合。


