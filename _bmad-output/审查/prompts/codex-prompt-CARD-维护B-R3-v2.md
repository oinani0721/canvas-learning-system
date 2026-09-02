# 代码复核请求：一个本地笔记工具的「报告数字有出处」校验器

你是独立代码复核者。请复核一个**单机离线学习笔记工具**的一处校验逻辑，
并按末尾格式给出结论。没有网络接口、没有多用户、不处理任何凭据。

## 背景（三句话）

用户在 Obsidian 里让 AI 生成学习白板的「回顾报告」。报告里出现的计数
（「本板共有 N 个子节点」这类）必须能在扫描结果 JSON 里找到同值来源，
否则校验器报错、报告打回重写。目的是**防止 AI 在报告里编造数字**。

要复核的问题只有一个：**校验器读到的数，与用户在 Obsidian 里渲染后看到的数，
是不是同一个**。两者不一致时，校验器就会漏判或误判。

## 本轮改动（三轮，请判断是否正确且完整）

上一次复核判「需整改」，列了 4 组问题。四组都已处置，做法如下：

1. **区间表达的首端**（`_D2_RANGE_RE` / `_range_ok`）——区间端点的匹配模式
   不含符号与小数点，于是匹配可能从符号或小数点之后重新开始，把一个不完整的
   片段当成完整的区间端点。现在：首端左侧若紧邻负号或「数词+小数点」，
   判为「无法确定是不是一个完整的数」并报错（fail-closed）。
   诊断打印**完整可见串**（第一版打印的是剥掉连接字符后的形态，把「这是个区间」
   这一信息本身抹掉了）。

2. **行内代码块的豁免判据**（`_codespan_is_visible_count` / `_blank_inline_code`）——
   反引号包起来的内容按「字段值」豁免检查，但判断"是不是字段值"原先在**源码文本**
   上做，而它执行在渲染归一（`_visible_text` / `_normalize_number_seps`）**之前**。
   现在：先归一再判；判为可见计数的 span 只移除反引号、保留内容交给数值门
   （反引号不在连接字符集里，保留会让量词锚点失效）。

3. **两处「同一句话、两个文本空间」**：
   - ③段信号行的**选行**原先在源码行上做，而后续整行校验在渲染文本上做；
   - fallback ⑦「派生角色成员」的**前置 N 绑定**原先在源码行上做，
     而同一条叙述的措辞白名单已在渲染文本上做。
   现在两处都统一到渲染文本。

4. **变异脚本的崩溃识别**（`_looks_like_crash` / `_crash_text`）——用于区分
   「被测代码判错了」（正常的红）与「被测代码崩了」（无意义的红）。
   原先只看外层 pytest 的 stdout、且异常名是一张手写闭表。现在：同时看 stderr；
   判据改为 pytest 输出语法——`E   <类名>: <消息>` 是异常，
   `E     <缩进文本>` 是断言消息的续行（`assert` / `AssertionError` 属正常的红）。

## 未改动的三处（请判断这个决定是否成立）

复核意见还点名了三处「在源码文本上做匹配」的代码：台账种子行、五元组、tips。
我的判断是**它们的行为已经是 fail-closed**，因为形状一偏离就会撞上
`_verify_report` 的模板白名单这道更靠前的检查，所以本轮**没有改**。

请判断这个「不改」的决定是否成立。**不需要**构造任何输入来证明——
按代码路径推理即可：形状偏离的行会先走到哪一道检查、那道检查会不会放行。

## 请读这些文件

```
WT=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix
```

1. `WT/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py`
   —— 主实现。重点段落：
   - 连接字符与渲染归一（`_D2_NOISE_ONE` / `_INVISIBLE_ONE` / `_join_free` / `_visible_text`）
   - 取数与判值（`_NUMERAL_LIKE_CHARS` / `_NUM_RUN_PAT` / `_count_token_value` / `_cjk_single_to_int`）
   - 行内代码块豁免（`_codespan_is_visible_count` / `_blank_inline_code`）
   - 区间（`_D2_RANGE_RE` / `_RANGE_LEFT_BAD_RE` / `_range_ok`）
   - ③段信号行（`_verify_signal_lines`）与 fallback ⑦（`m7`）
   - 台账种子行（`_verify_seed_ledger_counts`）
2. `WT/backend/tests/regression/test_recap_scan_signals.py` —— 行为门。
3. `WT/backend/tests/regression/recap_domain_negverify.py` —— **只读源码**，
   看变异脚本的替换内容是否真的禁掉了它声称禁掉的那条防线。

## 请怎么验

- 只跑这一条命令：
  `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest tests/regression/test_recap_scan_signals.py -q -p no:cacheprovider`
  —— 自报 **266 passed**（开工基线 249）。以及 `git rev-parse HEAD`
  —— 应为 `7bf7dfcf831cc4622fe32830dd9fb1b59f7195cc`。
- **不要**运行 `git diff` / `git show` / `git log -p`（此前曾因此中断）。
- **不要**运行 `recap_domain_negverify.py`：它会原地改写被测源码再还原，
  上一轮你跑它时中途被打断，把变异留在了工作树里未还原，随后的 pytest
  因此测的是被改过的文件。本轮请只读它的源码。
- **不要**构造探针脚本或临时文件；不读 `fixtures/` 下的 `.md` / `.json` 正文。

车道自报的其余数字（供你核对，不必重跑）：变异脚本 46/46 全部如期变红，
被测文件运行前后逐字节一致；扩大回归 `tests/skills + 两个 regression 文件`
= 598 passed。

## 请重点判断

1. 上述四组改动**各自是否正确**？有没有引入回归、误伤合法用法、或让某条
   既有检查变成走不到的死分支？
2. 「未改动的三处」那个判断是否成立？
3. 第 4 组（崩溃识别）的二分——`E   <类名>:` 是异常、`E     <缩进文本>` 是
   断言续行——有没有**判错**的情形？
4. 新增的行为门里有没有**恒真断言**（无论实现怎么变都通过）、
   或者门的措辞比它实际验证的范围更宽？
5. 还剩哪些问题？请把「一次改动内能闭合的」与「需要重做设计的」分开列。

## 输出格式

- 第一行：`BLOCKER/HIGH 清零：是/否`
- 逐项 ✅/⚠️/❌ + `file:line` + 依据（你实际读到/跑出的观测值）。
- 存量未闭合的问题也请报，并标注是存量还是本轮引入。
- 写出你实际跑出的 pytest 结果与 `git rev-parse HEAD`。
- 末尾写明验证限制（没跑的、无法证明的）。
