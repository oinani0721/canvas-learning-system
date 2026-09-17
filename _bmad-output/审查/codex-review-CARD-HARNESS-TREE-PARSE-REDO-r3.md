> 批次: BATCH-2026-09-11-第十四批 · 车道 T7 · 卡 CARD-HARNESS-TREE-PARSE-REDO round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HARNESS-TREE-PARSE-REDO-r3.md)"`
> 审查绑定: `08100483..e844d6a1`（该轮 HEAD = `e844d6a1`；本轮之后按其 MEDIUM 改代码 ⇒ HEAD 已前进到 `34451227`，故本轮**不绑最终 HEAD**，见 r4）
> ⚠️ prompt 缺陷如实记: 写该 prompt 时 `\u005f` 被中间工具层展开成 `_`，使 §二.5 与 Q6 变成「`"harness__tree"` 展开后是 `harness__tree`」这种自相矛盾的表述 ⇒ **Q6 这一问在该轮实际上没测到东西**（Codex 仍据代码实测答了「单下划线」）。
> 会话头自证（抄 .stderr 前 12 行中的三条，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）

---

审查绑定确认：HEAD 为 `e844d6a1`，三个代码文件与该提交一致。**整改仍不完整：4 条 MEDIUM、1 条 LOW。** 以下行为缺口均在缺库降级分支。

**BLOCKER：无。**

**HIGH：无。** 本次证明到解析与选树层，未证明真实缺库环境最终完成错误写入。

**MEDIUM：**

1. **Unicode 空白仍会绕过续行检查，截短合法 YAML 的路径。**  
   位置：[SKILL.md:474](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:474)，涉及 `:475–487`。  
   规范路径后接缩进的 NBSP-only 行，或 NBSP 后紧接 `#` 的行时，`.strip()` 将真实标量内容误判为空行／注释；PyYAML 将其折叠进路径，降级却采用前一行的树。

2. **首个文档标记整行早退，会吞掉同行配置，也漏掉连续空文档。**  
   位置：[SKILL.md:477](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:477)，涉及 `:478–480`。  
   开头 `---` 后同行放流式映射时，PyYAML 能读到显式键，降级却跳过整行而回退；连续起始标记或开头出现结束标记时，因未更新文档状态，降级还可能采用 PyYAML 整份拒绝的配置。

3. **整行引号计数不能确定引号是否闭合，仍会把标量内容认成键。**  
   位置：[SKILL.md:494](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:494)。  
   普通键中的字面引号、跨行标量的定界引号及尾注释中的引号恰好配成偶数时，检查全部放行；降级采用标量内部的规范形状行，而 PyYAML 实际没有该键，应该回退。单、双引号均已验证。

4. **非换行类 YAML 禁用字符仍未被拒绝，且不只会导致“无键回退”。**  
   位置：[SKILL.md:451](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:451)，涉及 `:470、496–504`。  
   其他字段含 U+0001 等禁用字符，同时目标键指向存在的规范路径时，PyYAML 报 `ReaderError`，降级却返回该树；这超出了 docstring 仅承认的“坏在别处、判为无键而回退”。

**LOW：**

1. **49 参数门对新增三组判据失效不敏感。**  
   位置：[test_g3_2_review_ledger.py:7576](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7576)，相关参数在 `:7578、7581、7583`，允许条件在 `:7618`。  
   别名、块标量和跨行引号参数仍被既有“非规范目标行”判据拒绝，指令参数则被文档标记拒绝；**仅在内存中同时删除指令、八个符号和奇数引号判据，49 条仍全部通过。**

其余问题逐项核对：

- **Q0，来源完备性：**尚未成立。需要单独考虑**非换行 Unicode 空白的词法身份**，由空行／注释识别及续行判据负责；**非换行非法字符**应由整份字符合法性检查负责。文档同行内容、空文档状态及引号角色混用，则属于已经列出的类别内部仍有缺口，不能靠扩大关键词清单证明完整。
- **Q1，过度拒绝：**在给定“缺库罕见、下游同样需要 PyYAML”的前提下，取舍成立，未发现值得单独放宽的一条。例子需纠正：**整行注释里的单个引号会被跳过**；内容行的尾注释才会参与奇偶计数。
- **Q2，顺序：**文档标记检查在整行注释检查**之前**。普通内容行上，续行检查先于 `_seen_content` 更新，没有发现该顺序本身漏检；问题是空行／注释早退，以及文档标记的 `continue` 跳过状态更新和同行检查。
- **Q3，字符集：**`chr()` 仍生成预期的八个字符。CR/LF 经文本读取归一化，NEL/LS/PS 由集合拦截，实际换行覆盖未发现遗漏；VT/FF/FS/GS/RS 在 PyYAML 中是**非法字符，并非换行**。八个字符均有拒绝依据，但集合不涵盖全部非法字符，尚缺其他 C0/C1 控制字符及 U+FFFE/U+FFFF 等。
- **Q4，既有 16 nodeid：**四个提交中的参数、断言和去除 docstring 后的函数体逐项相同；内存解析符合下表，端到端写入行为未复跑。

| 既有门类 | 数量 | 核对结果 |
|---|---:|---|
| 无键、显式树、引号尾注释、空值注释 | 4 | 回退、采用指定树、保留引号值、回退 |
| 井号分隔 | 5 | 无分隔保留；SP 剥注释；TAB 拒绝；U+3000/NBSP 保留 |
| 值首 Unicode 空白 | 2 | 原样保留，按完整相对路径拒绝 |
| 坏路径 | 4 | 绝对、`~`、引号、相对路径均拒绝 |
| 清空值 | 1 | 裸空值及空串均回退 |

TAB 拒绝层上移，但既有断言只要求非零码与零写。

- **Q5，49 参数是否假同值：**未发现共同上游早退造成的假同值。实测为 **8 条完整路径拒因相同、2 条预期无键回退、39 条降级专属拒绝**；问题是上述 LOW 的守卫覆盖盲区。以 `4d21bc9b` 函数在内存重放，新增九条中确有五条不满足判据。
- **Q6，两处自查修正：**当前状态属实。`:451` 赋值行全部为 ASCII，当前函数中没有那八种字面不可见字符；测试 `:7574` 构造的转义键经 PyYAML 解析确为 **`harness_tree`，单下划线**。

本次使用源码、AST 和内存配置对照，PyYAML 为 **6.0.3**；未修改文件、未联网或连接数据库，未运行写盘测试。作者的 **83／232／546 passed** 未独立复跑。
