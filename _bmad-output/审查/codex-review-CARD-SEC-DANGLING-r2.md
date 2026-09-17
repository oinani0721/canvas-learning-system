> 批次: BATCH-2026-09-11-第十四批 · 车道 T5-D (card-t5-bugs) · 卡 CARD-SEC-DANGLING round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SEC-DANGLING-r2.md)"`
> 审查绑定: `76a602c436e25e55c44c690098a4b55ed1f99cfd`（该轮送审时的 HEAD = r2 commit）
> 会话头自证（抄 .stderr，stderr 本身不入库 —— .gitignore:261-264 覆盖 `_bmad-output/审查/**/*.stderr*`）:
> - codex 版本行 = .stderr:2 `OpenAI Codex v0.153.3`
> - model 行 = .stderr:5 `model: gpt-6-astra`
> - reasoning 行 = .stderr:9 `reasoning effort: ultra`
>
> 备注: 本轮 prompt 发过两次。首版写于 `_as_dict` 加固前、自述与引用存档均已过时，由车道用 TaskStop 主动中止，**未产出任何存档文件**，不计轮次；本档是改写 prompt 后重发的那一次。

---

**本轮结论：BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 4。** MEDIUM-1 部分关闭；MEDIUM-2 的核心问题已关闭，但仍有一处证据措辞需要收窄。

审查绑定 `76a602c436e25e55c44c690098a4b55ed1f99cfd`。独立计算的三个提交文件 SHA 与最终红绿档一致；r1→r2 确实只改测试文件。全程未运行测试、hook、应用或数据库连接，未写文件。

**BLOCKER：0 条。HIGH：0 条。**

**MEDIUM：2 条。**

1. **⓪ MEDIUM-1 尚未完全关闭：未解析的 `$ref` 仍会漏掉合法引用。**  
   [test_openapi_contract.py:294](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/contract/test_openapi_contract.py:294)、`:302`。

   标准的**内联**入口已经补齐，未发现另一类遗漏的内联 Security Requirement 承载位置。但 Path Item／Callback 的引用目标可以位于外部文档，也不限于已遍历的组件位置。[OpenAPI 引用规则](https://spec.openapis.org/oas/v3.1.0.html#relative-references-in-uris)

   例如，`paths["/hidden"]` 引用根扩展中的 `#/x-shared-pathitems/Hidden`，目标是包含未声明方案 `Missing` 的 Path Item。另保留正常直接 operation 后，三个前置条件均可通过，而 `Missing` 完全不会进入枚举结果。因此“全部合法位置”仍过强。

   **复核思路：**保留正常直接 operation，把唯一悬空方案放入遍历清单之外的 `$ref` 目标，逐层推导最终引用集合。

2. **② 16/16 验伪锚缺少输入和断言原文，无法独立确认有效性。**  
   [enum-coverage-probe-r2c-20260916T202622.txt:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-sec-dangling/enum-coverage-probe-r2c-20260916T202622.txt:3)、`:12–22`。

   该档只有脚本 SHA、PASS 标签和产出摘要，没有合成 schema、B 组断言或 `run_no_raise` 实现。因此，**无法判断 B1/B2 比较了完整结果，还是仅检查某个名字未出现；也不能指认哪条断言恒真。**

   可以明确区分：

   - 若 `run_no_raise` 实际消费生成器，“不抛异常”有测试意义；若只创建生成器，则没有执行遍历主体。现档无法核对。
   - D6 的 `None` 在旧式 `(value or {})` 下也会通过：它检查容错，但不能区分本次加固。
   - D7 的“不抛异常”不能证明大写方法被识别；D7b 才声称检查了引用。两条属于同一输入场景。
   - D1/D2 若使用空字符串／空列表，旧代码也可能通过；档内没有具体值。

   **复核思路：**核对脚本原文中的实际输入、生成器消费、完整期望结果和断言，再将原文绑定到记录的 SHA；仅凭摘要不能完成这一步。

**LOW：4 条。**

1. **① `x-*` 误计只修了 Path Item 层，外层仍有缺口。**  
   [test_openapi_contract.py:284](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/contract/test_openapi_contract.py:284)、`:314`、`:322`。

   Callback Object 和 Paths Object 也允许扩展。若 Callback Object 中存在：

   ```json
   {"x-audit-data": {"get": {"security": [{"DataOnly": []}]}}}
   ```

   当前代码会把扩展值当作 Path Item，计入 `DataOnly`；`paths["x-audit-data"]` 同理。这会造成误红，也可能冒充 `per_op_refs` 满足非空条件。原来 Path Item 同级的误计已修，但新增递归仍存在同类问题。[Callback Object](https://spec.openapis.org/oas/v3.1.0.html#callback-object)、[Paths Object](https://spec.openapis.org/oas/v3.1.0.html#paths-object)

   **复核思路：**把扩展分别置于这两个对象层级，赋予 `get.security` 形状，沿循环追踪是否到达 `yield`。

2. **④ LOW-2 可以登记为未解决限制，但“必须留在同文件所以不能修”不充分。**  
   [UAT-CARD-SEC-DANGLING-2026-09-16.md:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/验收单/UAT-CARD-SEC-DANGLING-2026-09-16.md:307)。

   模块级 `importorskip` 的耦合仍在。保留原文件也可以调整：将 schemathesis 的可选导入、schema 初始化和相关装饰器定义限制在依赖可用的分支，静态门独立定义。是否接受这项调整另属范围决策，但并非技术上只能迁移文件。

   **复核思路：**分别展开依赖存在／缺失的模块执行路径，检查静态门是否仍被定义和收集。

3. **⑥ 两条长跑的复用理由把“未收集”推成了“任何内容都不进运行”。**  
   [UAT-CARD-SEC-DANGLING-2026-09-16.md:336](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/验收单/UAT-CARD-SEC-DANGLING-2026-09-16.md:336)。

   日志支持所述收集范围，但没有实际 argv 或导入轨迹。`conftest`、`pytest_plugins`、`-p`、自动加载插件及显式导入，都可能加载未被收集的模块；普通 pytest 缓存本身不会凭空执行未选模块。[pytest 插件加载规则](https://docs.pytest.org/en/stable/how-to/writing_plugins.html#plugin-discovery-order-at-tool-startup)

   **不能据此断言必须重跑，也不能认定“绝对不受影响”已被证明。** 单纯被导入同样不代表修改后的 helper 被调用。

   **复核思路：**核对实际参数与变更 helper 的调用依赖，再决定旧结果能否复用；本轮限定读取面不足以完成该排除。

4. **③ MEDIUM-2 核心已关闭，但“每次定向跑均为零”超出当前承重档可直接确认的范围。**  
   [test_openapi_contract.py:228](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/contract/test_openapi_contract.py:228)。

   禁闭外导入、ASGI 请求、缓存以及单一 socket 入口的边界已经写清。剩余问题是最终红绿档仅在[对照阶段 :11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-sec-dangling/r2-final-red-green-negctl-20260916T203537.txt:11)保留 W4 零记账；红阶段和负控阶段没有对应行。宜限定为已保存记录的运行，不能由缺失记录推出全部阶段为零。

   **复核思路：**逐阶段对应 W4 输出，区分“已记录为零”和“摘要未记录”。

其余判断：

- **① 递归与重复计数：**在声明的 JSON 树输入下，递归持续向下，不解析 `$ref`，没有发现无限递归路径。普通组件引用也不会自动计两遍：引用处被跳过，仅组件定义处产出；`:303` 的重复计数解释不准确，但不影响悬空布尔判断。
- **① 大小写与 `_as_dict`：**`.lower()` 接受 `GET`／`Get` 属宽松容错；OpenAPI 固定字段区分大小写，大写用例不能证明标准 operation 覆盖。[规范格式规则](https://spec.openapis.org/oas/v3.1.0.html#format) `_as_dict` 确实防住所列容器的非 dict `.items()` 错误，但不等于验证整个畸形 schema，尤其不保护所有 `security` 值或完整断言中的 `components` 访问。
- **⑤ 本轮无需重新生成生产源或快照，推断成立。** 精确 diff 没有改变 schema 生成输入，提交内容 SHA 与最终证据一致；也没有必要仅因测试 helper 加固，重做 r1 已成立的生产语义论证。需要复核的是变更后的测试门及其证据，上述问题集中于此。
