> 批次: BATCH-2026-09-05-第十二批 · 车道 Y6 · 卡 CARD-RV-D round-1 prompt-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `Codex v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-D-p1.md)"`
> 审查绑定: `514cff3c..e22ad10a`（固定审面，与 HEAD 无关）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**结论：P1 存在 HIGH 级的失败归因缺口，以及 MEDIUM 级的负控隔离性和文档措辞问题。`11/11 KILLED` 不能证明 11 个预期判据分别有效；也没有证据认定其中某条已经实际发生误归因。**

已将提供的 diff 与 `514cff3c → e22ad10a` 的三个文件改动逐字比对，完全一致。未读取 HEAD 源码、运行目标 harness、修改文件或连接数据库。以下均引用 `e22ad10a` 行号。

**1. HIGH：KILLED 绑定了测试名，没有绑定被测断言，其他原因失败也会获判 KILLED。**

依据：`e22ad10a:backend/scripts/g32ccr1_negative_controls.py:276`：

```python
killed = rc == 1 and gate in out and "failed" in out
```

其准确边界是：

| 情况 | 是否可能被判 KILLED |
|---|---|
| 指定测试内，另一条断言失败 | **会**，正常失败摘要即可满足 |
| 测试执行阶段动态编译／导入被测文件，抛出 `SyntaxError`／`ImportError`，产生 rc=1 和失败摘要 | **会** |
| 收集阶段语法／导入错误，返回 rc=2 | **不会**，不满足 `rc == 1` |
| rc=1，但输出只有 `error`，没有小写 `failed` | **不会** |
| 门名只出现在其他输出位置，另处包含 `failed`，且 rc=1 | **会**，谓词不关联这两段文本 |

这些是谓词的逻辑结果，已用内存构造的输出验证，**不是目标 pytest 的历史实测**。

`gate in out` 有有限作用：它要求输出出现名字。配合 `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:180` 的单个 `文件::测试名` 选择，可以限制普通无关测试混入。但它不识别断言、参数实例或失败阶段；门名出现在收集／摘要等任何位置都算。它不是所有运行中恒真，却几乎不能区分所选测试为什么失败。

此外，`e22ad10a:backend/scripts/g32ccr1_negative_controls.py:279` 只在未判 KILLED 时输出诊断尾行；成功汇总没有保留可回查的失败身份。

**最小可靠改动：**

- 每条负控增加预期断言身份，目标断言使用稳定、唯一的标识。
- 读取结构化 pytest 报告，要求精确 nodeid、`call` 阶段、预期断言身份匹配，失败集合符合预期，且无收集／setup／teardown 错误。
- 保存每条失败报告；语法、导入等异常另记 `ERROR/INVALID`。

**仅改成精确匹配 `FAILED …::测试名` 仍不够**，同一测试内的其他断言依然能冒充目标失败。

**2. MEDIUM：E8、E10 都包含可直接确认的附带变化，不能视为严格的单因素对照。**

- **E8 同时删除类型检查与词法检查。**  
  `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:115` 的原条件包含 `isinstance(_ts_in, str)` 和 `_TS_RE.fullmatch`，下一行整体换成 `if False`。  
  最小改动：替换为 `if not isinstance(_ts_in, str):`，只取消词法检查。

- **E10 同时引入海象重绑，并把原对象换成 bytes。**  
  `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:138` 将 `b"x"` 直接交给 `value_shape_problems`，因此存在形状检查或其他前置断言先失败的可能。  
  最小改动：使用 `shape = value_shape_problems(record := record)`，保留对象，只改变重绑语法。

这些附带变化**已证实存在**；它们是否造成了某次实际误归因，**未验证**，缺对应测试实现和失败报告。

**3. MEDIUM：schema 仍保留未限定范围的结论，措辞同步不完整。**

`e22ad10a:docs/learning-events-schema-v1.md:121` 仍称扩表后的路径“恒不触发”、真实输入拒绝面“一条都没变”。

但：

- `e22ad10a:backend/scripts/validate_learning_events.py:1624` 将结论限定在“当前业务路径”。
- `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:14` 明确 E3 只跑指定门；后续说明将另一次行为验证限定为测试套件输入。
- `e22ad10a:docs/learning-events-schema-v1.md:124` 自己承认 `append_event()` 能写入这些字段，扩表会改变拒绝面。

**最小改动：**将“恒不触发”限定为“当前已核对的落账写点与复放路径”；将“一条都没变”限定为“所运行回归套件中的行为门未变化”，并明确这不是 E3 单独提供的证据。

**E1–E11 的逐条核查如下。**“片段内单一”只说明可见替换内容，没有证明历史运行恰好死于目标断言。

| 输入 | 隔离性判定 | 依据 |
|---|---|---|
| E1 | 追加 `self_confidence_raw` 重复行；没有限定条目 A。是否影响其他条目／检查，未验证。 | `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:59–63` |
| E2 | 将该字段移到键序末尾；片段内是重排，也没有限定 A。实际影响范围未验证。 | `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:69–73` |
| E3 | 新增严格表字段。**如果 (f) 的固定表等值断言成立，扩表也会违反它**，因此 KILLED 可能只证明表变了，不能独自证明“死条目”检查有效。 | `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:79–82` |
| E4 | 同时取消 dict 判定和值相等判定；但声明目标是整个往返自证，不能据此认定拆了两道独立防线。若只测等值判据，应保留 dict 判定。 | `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:88–90` |
| E5 | 普通赋值重绑并复制 dict；保持 dict 类型，**并未证明非 dict 分支变得可达**。若只测 Store，可改为 `record = record`。 | `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:153–155` |
| E6 | 在尾部追加同值重复行；除了结束边界，也可能触发重复次数等检查。实际失败身份未验证。 | `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:96–100` |
| E7 | 在成功出口插入 `SystemExit`；片段本身没有 F1 专属条件。是否先破坏测试中其他阶段，未验证。 | `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:106–109` |
| E8 | **不隔离：类型检查、词法检查一起删除。** | `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:115–117` |
| E9 | 清空整表，符合“空表”负控目标；由固定表等值断言拦下也符合该目标，但不能证明其他业务一致性判据有效。 | `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:123–131` |
| E10 | **不隔离：NamedExpr 重绑之外，还改变对象类型和值。** | `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:137–139` |
| E11 | 可见片段只去掉 tuple 遍历，保留 list；未见第二项独立改动。tuple 样本和实际失败身份未验证。 | `e22ad10a:backend/scripts/g32ccr1_negative_controls.py:145–147` |

需要优先复查失败身份的是 **E8、E10**；其次是 **E3** 的“死条目”归因，以及共用 emitter 测试的 **E1／E2／E6／E7**。全部 11 条都受宽判条件影响，但**严格条件下究竟哪条不再算 KILLED，目前均未验证**。

E5／E10 覆盖的是**同一个“不重绑 record”前提的 `Assign` 与 `NamedExpr` 两种语法形式**。它们有不同的 AST 语法覆盖价值，尤其后者针对漏扫海象的问题；不能计作两道独立防线。

**validator 的新增实数是：31 行注释＋6 行 docstring＋0 行可执行语句。**

| 分类 | 新增行位置 | 数量 |
|---|---|---:|
| 注释 | `e22ad10a:backend/scripts/validate_learning_events.py:1612–1613` | 2 |
| 注释，包括单独的 `#:` 行 | `e22ad10a:backend/scripts/validate_learning_events.py:1617–1645` | 29 |
| docstring，替换旧措辞形成的新增行 | `e22ad10a:backend/scripts/validate_learning_events.py:1678` | 1 |
| docstring，纯插入 | `e22ad10a:backend/scripts/validate_learning_events.py:1680–1684` | 5 |
| 可执行语句 | 无 | **0** |

“非注释新增只有 5 行”漏算了 `:1678`。本次改变了说明文字及 `__doc__`，没有改变校验逻辑或严格字段表。

schema 五行中，`e22ad10a:docs/learning-events-schema-v1.md:120` 的收窄判据与代码说明一致；`:121` 存在上述过度概括；`:122` 的分工说明与注释无直接矛盾，但实际路径未验证；`:123` 是已移交缺口记录，本卡不提出修复；`:124` 的结构可写入例外已同步，其中“门锁死三者”的实现未验证。

**(c)、(f) 的实现核验存在明确的审面边界。**

| 自述 | 本次能确认什么 |
|---|---|
| 扫描任何 Store 上下文的 `record` | 看得到 E5／E10 输入，**看不到扫描实现，未验证**。 |
| 守卫和调用同为顶层，且守卫在前 | **P1 未包含对应实现，未验证**。 |
| 守卫必须比较 dict 并立即 return | **P1 未包含对应实现，未验证**。 |
| 一致性提取器改 AST | **P1 未包含提取器，未验证**。 |
| 严格表期望逐项写死 | E9 的替换锚点写死了五个 tuple，**但锚点不是测试期望值**，无法判断期望是否从实现读取。 |
| 容器门增加 tuple 样本 | 只看到 E11 删除 tuple 支持的输入，**样本本身未验证**。 |

所缺证据是 **`e22ad10a` 时刻对应回归测试门的实现**；实际失败归因还缺每条负控的结构化报告。不能把“P1 没有包含实现”说成“整改没有实现”。

**总评：**(a) **部分成立**：三处确实加入限定、枚举表零改动，但 schema 仍有绝对化残句；14 键差集和写点／复放事实未独立验证。(c) **实现未验证**：仅确认两种重绑输入存在，且 E10 不够隔离。(f) **实现未验证**：E9／E11 输入存在，不足以证明 AST 提取、独立固定期望或 tuple 样本已经落实。当前证据足以要求修正 harness 的归因判据，尚不足以接受作者对各道防线的完整证明。


