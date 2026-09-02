# 代码复核请求：一个本地笔记工具的「报告数字有出处」校验器（第十四次）

你是独立代码复核者。复核一个**单机离线学习笔记工具**的一处校验逻辑。
没有网络接口、没有多用户、不处理任何凭据。

## 背景（三句话）

用户在 Obsidian 里让 AI 生成学习白板的「回顾报告」。报告里出现的计数
（「本板共有 N 个子节点」这类）必须能在扫描结果 JSON 里找到同值来源，
否则校验器报错、报告打回重写。目的是**防止 AI 在报告里编造数字**。

要复核的问题只有一个：**校验器读到的数，与用户在 Obsidian 里渲染后看到的数，
是不是同一个**。

## 上一次复核的意见与本次处置

**你给的「第六形态」指出了一个结构性盲区**：只收集**认可的**小节，等于把不合口径的
种子 H3 整块排除在审计面之外；更强的形态是先放一个合规空小节让「有小节」成立、
再放第二个不合规 H3 装货，连「零 section」信号都消失。

⇒ 修法不是放宽口径，而是**给「像但不是」单独一条报告路径**：凡 `### …种子…`
却不被认可的行，直接 fail-closed。六形态实测全对（含围栏内不误报）。

| 你的其余意见 | 处置 |
|---|---|
| 损坏 `seeds=[None]` 被过滤成空 rows，再因原值仍是 list 被当合法零种子 | ✅ fail-closed |
| R23 名为 `_cli` 却只调 helper、`tmp_path` 未用 | ✅ 改名去参 |
| R26「真的没有 ledger ⇒ 仍 fail-closed」措辞过宽 | ✅ 收窄为「无 ledger **且有认可 H3**」，并注明未覆盖面 |
| 源码形状门仍在；`-k` 只确认匹配集合里有失败；崩溃二分会判错 | ⚠️ **未改**，登记 |
| ③段三套自造定位；D2 豁免段口径不同且丢 H2 标题行；tips 两数仍 raw；尾巴只拦 ASCII `批注 N 条`；`1\*5个` 被剥成 `15` | ⚠️ **未改**，如实登记（多属重做设计） |

**一条过程记录**（供你校准）：`survivor-64` 这次**未承重** —— 禁掉「损坏 seeds」
检查后，那条路径继续往下走，报出**另一条**诊断（「不在 ledger」），而我的门只写了
`assert ps`（有报错就行）⇒ 换个理由报错，门照样绿。这是变异第一次抓到「门太弱」
而不是「实现有洞」。已把六条断言全部升级为**绑定诊断关键词**。

## 请重点判断

1. 「形似种子 H3 自己 fail-closed」这条有没有**误伤**？（例如报告正文里合法出现
   `### 种子相关说明` 之类的标题。）
2. 六形态之外还有第七形态吗？
3. **继续留意范围/空间超出意图的改动** —— 你已经抓到我三次了。
4. 行为门里有没有**恒真断言**、**目标无关假绿**、或门的措辞比实测宽？
   （`survivor-64` 那次说明我这类问题仍在，请再扫一遍所有新门。）
5. 还剩哪些问题？请把「一次改动内能闭合的」与「需要重做设计的」分开列。

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
  —— 自报 **277 passed**（开工基线 249）。以及 `git rev-parse HEAD`
  —— 应为 `03b60b8617af9d18d030f09d4386b19980b47bd4`。
- **不要**运行 `git diff` / `git show` / `git log -p`（此前曾因此中断）。
- **不要**运行 `recap_domain_negverify.py`：它会原地改写被测源码再还原，
  上一轮你跑它时中途被打断，把变异留在了工作树里未还原，随后的 pytest
  因此测的是被改过的文件。本轮请只读它的源码。
- **不要**构造探针脚本或临时文件；不读 `fixtures/` 下的 `.md` / `.json` 正文。

车道自报的其余数字（供你核对，不必重跑）：变异脚本 64/64 全部如期变红，
被测文件运行前后逐字节一致；扩大回归 `tests/skills + 两个 regression 文件`
= 609 passed。

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
