> 批次: BATCH-2026-09-11-第十四批 · 车道 T5-D (card-t5-bugs) · 卡 CARD-SEC-DANGLING round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SEC-DANGLING-r3.md)"`
> 审查绑定: `9861c59598ca350ca7df10921744292b0deffb41`（= r3 代码 commit；此后仅 `_bmad-output` 文档 commit，三个代码文件与送审提交逐字一致，Codex 本轮已独立复算确认）
> 会话头自证（抄 .stderr，stderr 本身不入库 —— .gitignore:261-264 覆盖 `_bmad-output/审查/**/*.stderr*`）:
> - codex 版本行 = .stderr:2 `OpenAI Codex v0.153.3`
> - model 行 = .stderr:5 `model: gpt-6-astra`
> - reasoning 行 = .stderr:9 `reasoning effort: ultra`
>
> 备注: 本轮共发 5 次。前 4 次（23:58 ×2 / 00:03 探针 / 00:34 间隔重发）全部因账号用量上限产出 0 字节；
> 02:06 第 5 次探针得 `QUOTA_OK`（`probe_rc=0`）后原样重发成功 —— 错误里报的「Sep 19th 8:16 PM」重置时刻
> 实测约 1.5 小时即恢复，再次印证 R-05「外部服务的重置时间是一次观测不是不变量」。

---

**本轮结论：BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 3。** 另有已登记移交的 r2 LOW-2，仍未修复，不重复计入本轮发现。

代码审查绑定 `9861c59598ca350ca7df10921744292b0deffb41`；当前 HEAD 虽已前移，但这三个代码文件与送审提交一致。全程只读，未执行测试、探针、hook、项目导入或数据库连接。

**BLOCKER：0 条。HIGH：0 条。**

**MEDIUM：1 条。**

1. **`x-*` 过滤被推广到命名 Map，新增了合法内联引用漏检；B4、B6 又把这种漏检判为 PASS。**

   位置：[test_openapi_contract.py:275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/contract/test_openapi_contract.py:275)，受影响调用为 `:297`、`:339`、`:342`、`:344`。

   `Paths Object` 和 Callback Object 的表达式层可以有规范扩展；但 `webhooks`、`components.pathItems`、`components.callbacks`、operation 的 `callbacks` 是**命名映射**，其中 `x-event`、`x-tmpl` 可以是正常名称。Components Object 自身允许扩展，不代表其子映射中所有 `x-*` 名称都是扩展。[OpenAPI 3.1 对象定义](https://spec.openapis.org/oas/v3.1.0.html#components-object)、[operation callbacks](https://spec.openapis.org/oas/v3.1.0.html#operation-object)

   静态反例：保留一个引用已声明 `Known` 的正常 operation，再增加 `webhooks["x-event"].post.security=[{"Missing":[]}]`。三个前置断言仍成立，但 r3 会在进入 webhook 前跳过它，漏掉 `Missing`；r2 会枚举它。因此，`:308` 的“全部内联位置”仍过强。

   同一根因也出现在探针：[B4 :238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-sec-dangling/enum-coverage-probe-r3-20260916T232823.txt:238) 的期望遗漏 `DataOnly`；B6 `:248` 的期望遗漏 `DataOnly`、`DataOnly2`。**这里确实存在“期望集合写错却仍 PASS”。**

   **复核思路：**分别区分可扩展对象与命名映射，将合法 webhook／callback／组件名称设为 `x-event`，逐层比较 r2、r3 应产出的引用集合。

**LOW：3 条。**

1. **“15 条能区分加固”不成立，计数自洽没有验证标签正确。**

   位置：[探针 :229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-sec-dangling/enum-coverage-probe-r3-20260916T232823.txt:229)、`:265`、`:302`。

   - B2 的 `summary="s"`、`parameters=[]` 在 r1 已被 `isinstance(operation, dict)` 跳过，前后结果相同。
   - C4 的旧实现 `continue` 与新实现空迭代均产出空集合，其 `True` 标注同样不成立。
   - `:302–305` 仅统计手填标签。若明确比较 r2 提交与 r3，只有 B3–B6 四条行为改变；跨轮加固应逐条绑定对应旧版本。
   - 另有措辞例外：**19 条合成用例**比较完整集合；E1 `:292` 是数量、声明集及悬空集检查，并非完整引用集合比较。

   没发现“实际结果反过来生成期望”的恒真断言；B2、C4 是**缺乏鉴别力**，不能称为逻辑上恒真。

   **复核思路：**固定每条用例的旧版本源码，分别推导输出或异常，再核对 `discriminates`，不以标签总数替代前后比较。

2. **`$ref` 的精细分类主张超出了指定普查档的直接证据。**

   位置：[test_openapi_contract.py:322](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/contract/test_openapi_contract.py:322)、[普查档 :2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-sec-dangling/ref-distribution-census-20260916T204712.txt:2)。

   存档支持所列 **736／212／524、Path Item 级 0、无 webhooks、组件类别及 callbacks 子树 `$ref` 为 0**。但没有脚本或细分路径，不能单凭这九行独立确认“524 处全部在 operation 请求／响应 schema 中”。

   此外，`:2` 仍写“`$ref` 只出现在 components.schemas 侧”，与 `:4` 的 `paths: 524` 自相矛盾。应更正旧目的行，并让正文分类精度与证据一致；这不等于认定本仓实际存在未发现的 `$ref` 缺口。

   **复核思路：**核对每个计数的路径分类依据，区分“排除了这些入口”和“已确认所有剩余引用的具体位置”。

3. **“最终 SHA 上重跑”字面不准确，但最终逻辑版本的绑定能够成立。**

   位置：[验收单 :389](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/验收单/UAT-CARD-SEC-DANGLING-2026-09-16.md:389)、`:390`，以及两份长跑日志各自 `:1`。

   日志绑定测试文件 `ae32c3c7…`，送审文件实际为 `85e3dd22…`。我独立逆转验收单 `:394` 披露的唯一 docstring 尾改，所得 SHA **精确等于日志中的完整 SHA**；去掉该 docstring 后，两版 AST 相同。

   因此 r2 LOW-3 的实质争点可以关闭，但应写成“尾改前版本重跑，最终版本经文案等价关系绑定”，无需仅因此要求再跑。

   **复核思路：**逆转已披露的唯一文案修改，重算文件 SHA，并比较移除该 docstring 后的 AST。

对 **⓪ 关闭状态**，我的判断是：

| r2 项目 | 本轮判断 |
|---|---|
| MEDIUM-1 | `$ref` 边界已明确；这是**收窄主张，解析能力未变**。“全部内联”又被本轮 MEDIUM 动摇。 |
| MEDIUM-2 | **可独立复核性已关闭**；期望正确性和鉴别标签仍有上述问题。 |
| LOW-1 | 原 Paths／Callback 扩展误计已修；推广过滤引入新漏检，不能无条件判关闭。 |
| LOW-3 | 实质关闭；保留上述 SHA 措辞问题。 |
| LOW-4 | 已关闭。[红绿档 :11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-sec-dangling/r3-red-green-negctl-20260916T232904.txt:11)、`:24`、`:31` 分别记录三个阶段 W4 为零。 |
| LOW-2 | 理由已更正，耦合仍在；作为已登记移交项保留。 |

对 **①、④ 的其余边界**：

- 非字符串名称不会在 `_named_entries` 的 `startswith` 处报错，而是被保留；Path Item 内部的非字符串方法键仍可能在 `.lower()` 报错。声明的 JSON 往返输入保证键为字符串。
- `X-` 不被过滤符合前缀大小写规则。Paths 下既不以 `/`、也不以小写 `x-` 开头的键，并不是题述暗示的合法标准字段；当前实现可能误计这种无效输入。`summary` 等合法 Path Item 固定字段则由方法白名单排除。[规范格式](https://spec.openapis.org/oas/v3.1.0.html#format)、[Paths Object](https://spec.openapis.org/oas/v3.1.0.html#paths-object)
- 在声明的 JSON 树、不解析 `$ref` 的前提下，未发现新增循环递归或生成器消费问题。`_as_dict` 仍只是容器保护，不能保证任意畸形 `security` 或整个 schema 都安全跳过；这是既有边界。

对 **③**，存档脚本全文的 SHA 已独立复算为 `caf15d04…`，与档头一致；`list()` 消费及集合比较均可确认。因此现在能审出具体错误，但 **20/20 不能证明期望本身正确**。

对 **⑤**，主张成立。我独立计算了 r1、r2、送审提交、当前 HEAD 和工作树的文件 SHA，全部一致，且 r1→送审提交这两文件的 diff 为空：

```text
backend/app/security.py
925443dce1f90b35391898dc7cfa45c436107b7d015ed9f24e30c90e0e361904

backend/openapi.json
9df9f7df7fdb9a8f4d5ae22aa0886fe8e36d0e66f4e106a1579801c9824bab79
```


