> 批次: BATCH-2026-09-11-第十四批 · 车道 T5-D (card-t5-bugs) · 卡 CARD-SEC-DANGLING round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SEC-DANGLING-r4.md)"`
> 审查绑定: `0726057e846d4c28f8202ce0ee73f46b486d7ae5`（= r4 代码 commit = 送审时的 HEAD；Codex 本轮自述「当前 HEAD 与工作树测试文件一致」）
> 会话头自证（抄 .stderr，stderr 本身不入库 —— .gitignore:261-264 覆盖 `_bmad-output/审查/**/*.stderr*`）:
> - codex 版本行 = .stderr:2 `OpenAI Codex v0.153.3`
> - model 行 = .stderr:5 `model: gpt-6-astra`
> - reasoning 行 = .stderr:9 `reasoning effort: ultra`
>
> 本轮结论: **BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 3** —— 卡文 (k)「绑最终 HEAD 的一轮 BLOCKER/HIGH = 0」在本轮达成。
> 三条 LOW 全为文案不准（无代码缺陷），按 D-32 以纯文案尾巴修复，见验收单 §七 round-4 收尾。

---

**结论：BLOCKER 0 条 / HIGH 0 条 / MEDIUM 0 条 / LOW 3 条。r3 MEDIUM-1 已关闭，未发现本轮新增的代码缺陷。**

审查绑定 `0726057e846d4c28f8202ce0ee73f46b486d7ae5`，当前 HEAD 与工作树测试文件一致。全程只读，未运行测试、探针、hook、项目导入或数据库连接。已登记移交的 `importorskip` 耦合不重复计入。

**LOW：3 条。**

1. **验收单把 r3 的文案等价证明用于 r2，原来的不准确措辞也仍有残留。**

   位置：[UAT:343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/验收单/UAT-CARD-SEC-DANGLING-2026-09-16.md:343)、`:344、:372、:383、:390、:391、:455`。

   `:343` 明确说两条 **r2** 长跑绑定 `9765a69a…`，随后还有 `_as_dict` 真代码加固；`:344` 却用 **r3** 的 docstring 等价证明绑定它们。该证明的两端实际是 `ae32c3c7… → 85e3dd22…`。另外，`:390–391` 等处仍称“最终 sha 上重跑”，与 `:455` 的“已更正”不一致。

   r4 新日志直接绑定当前测试文件 SHA，因此此项影响历史证据说明。

   **复核思路：**逐一对应日志输入 SHA、等价证明两端 SHA 和修改性质，再检查正文是否引用同一组版本。

2. **普查已补齐 operation 子结构分类，但源码“全部在 schema 里”的措辞仍比证据更细。**

   位置：[test_openapi_contract.py:335](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/contract/test_openapi_contract.py:335)、[普查档:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-sec-dangling/ref-distribution-census-20260916T204712.txt:21)。

   新增细分为 `responses 430 + requestBody 91 + parameters 3 = 524`，支持“全部位于这三类 operation 子结构”。但通配路径止于 `responses…` 等，没有展示引用是否进一步落入 `schema`，也未收录分类实现或完整路径。

   因此，**r3 LOW-2 的矛盾部分已关闭，精确分类措辞仅部分关闭**。将源码表述收窄到“三类 operation 子结构”即可与当前证据一致。

   **复核思路：**对照每项分类实际保留的结构层级，分别核实“位于 operation 子结构”和“位于 schema 内”两种主张。

3. **探针期望已改对，但 B5、B6 的说明文字仍有错误。**

   位置：[探针:256](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-sec-dangling/enum-coverage-probe-r4-20260917T021352.txt:256)、`:264`；输出区对应 `:86、:91`。

   B5 的“同上”现在承接 B4 的“名层过滤被修复”，但 B5 测的是两版均保留的表达式过滤。B6 写“r3 漏三条”，实际只漏 `NamedXPi`、`NamedXCb2` **两条**，`RealScheme` 始终存在。

   **复核思路：**固定输入，按两版调用层次列出全部产出，再核对旁注中的改变层级和遗漏数量。

**对 ⓪、④：层级区分正确，MEDIUM-1 可以关闭。**

四个命名映射在测试文件 `:307、:354、:357、:359` 都恢复普通遍历，合法的 `x-*` 名称能够进入枚举。对应 [OpenAPI 根对象](https://spec.openapis.org/oas/v3.1.0.html#openapi-object)、[Components](https://spec.openapis.org/oas/v3.1.0.html#components-object) 和 [Operation](https://spec.openapis.org/oas/v3.1.0.html#operation-object) 的定义，没有发现 `_as_dict` 与 `_extensible_entries` 错配。

“只用两处”准确说是**两类对象、三个调用点**：Paths 一处，Callback 表达式层两处。其扩展过滤符合 [Paths](https://spec.openapis.org/oas/v3.1.0.html#paths-object) 与 [Callback](https://spec.openapis.org/oas/v3.1.0.html#callback-object) 的定义。

**对 ①：它过滤扩展，不验证键的完整语法。**

- 非 `/`、非 `x-` 的 Paths 键，以及非 `x-*` 的非法 Callback 表达式键，都会继续遍历其值，可能计入无效输入中的 `security`。
- 外层非字符串键同样保留；但 **Path Item 内部方法键**若非字符串，会在 `:299` 的 `.lower()` 报错。
- 这些是既有边界。对既定 JSON 往返输入、仅检查引用完整性的范围可以接受；PASS 不证明结构合法。规范要求对象键为字符串，Callback 合法键也可能包含固定 URL 前缀，不能简单要求以 `{$` 开头。[规范格式](https://spec.openapis.org/oas/v3.1.0.html#format)、[Callback 示例](https://spec.openapis.org/oas/v3.1.0.html#callback-object-examples)

**对 ②：四条 r4 期望集合均正确，只有三条区分 r3 与 r4。**

下表简写方案名；对应位置串也已逐对核对。

| 用例 | r3 产出 | r4 产出 |
|---|---|---|
| B4 | `RealScheme` | `RealScheme、NamedXCb` |
| B6 | `RealScheme` | `RealScheme、NamedXPi、NamedXCb2` |
| B7 | `Known` | `Known、Missing` |
| B8 | `RealScheme` | `RealScheme` |

B8 是防止表达式过滤退化的覆盖，不能证明 r3→r4 行为改变。按脚本明确的“**本卡某项加固**”跨轮口径，它与 B5 的 `True` 可以成立；**15 / 6 / 1 分类成立，但不代表 15 条都能区分 r3/r4**。未发现新的错误期望或必须改为 `False` 的标签。B2、C4 与 E1 的口径已更正。

末尾脚本 SHA 已独立复算，与档头 `2297b96f…` 一致；21 条合成用例确实消费生成器并比较完整集合，E1 仅核数量、声明集和悬空集。

**对 ③：更正留痕有效，分类口径本身可用。**

普查 `:11–16` 明确撤回了第 2 行的测前猜测，保留原行可以接受。按真实 JSON 层级取 operation 后第一个结构段，是可靠的分类口径；当前档没有分类实现，故其实现正确性仍未独立核实。剩余证据精度问题见 LOW-2。

**对 ⑤：仍成立。**

独立复算 r1、r3、r4／当前 HEAD 和工作树，两个文件 SHA 全部一致：

```text
backend/app/security.py
925443dce1f90b35391898dc7cfa45c436107b7d015ed9f24e30c90e0e361904

backend/openapi.json
9df9f7df7fdb9a8f4d5ae22aa0886fe8e36d0e66f4e106a1579801c9824bab79
```

r4 红绿、ruff、contract 与 unit 日志也均绑定当前测试文件的完整 SHA `85ef982bc36fec9702155cdf47f460e74d598d3aa36413519a1a9b4bf47f649c`。
