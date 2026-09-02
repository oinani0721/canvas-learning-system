# 代码复核请求：一个本地笔记工具的「报告数字有出处」校验器（第九次）

你是独立代码复核者。复核一个**单机离线学习笔记工具**的一处校验逻辑。
没有网络接口、没有多用户、不处理任何凭据。

## 背景（三句话）

用户在 Obsidian 里让 AI 生成学习白板的「回顾报告」。报告里出现的计数
（「本板共有 N 个子节点」这类）必须能在扫描结果 JSON 里找到同值来源，
否则校验器报错、报告打回重写。目的是**防止 AI 在报告里编造数字**。

要复核的问题只有一个：**校验器读到的数，与用户在 Obsidian 里渲染后看到的数，
是不是同一个**。

## 上一次复核的意见与本次处置

**你抓到的根因**：我在种子小节扫描里**手抄了第二份围栏状态机**（遇任意三反引号
就布尔翻转），而同一个文件里 `_strip_code_blocks` 早有语义完整的实现。你给的
反例（四反引号开栏 → 块内三反引号伪闭栏 → 四反引号真闭栏，状态 True→False→True）
完全成立。⇒ 已改为**复用本体**：剥完行数不变，「原行非空而剥后为空」= 在围栏内。

| 你的其余意见 | 处置 |
|---|---|
| 父级 H2 用 `"台账" in heading` ⇒ `## 非台账示例` 也算 | ✅ 改整行匹配 |
| `### 种子 ###`（合法 ATX 闭合）不识别、`###种子`（非法）反而命中 | ✅ 两侧改正 |
| 绑定索引摊平全部角色 ⇒ 派生节点混进种子小节即通过 | ✅ 收窄到 `seeds`（扁平 list 形态无角色信息，维持并登记） |
| `_tail_conflict` 只在 raw 尾巴上找；`未批注` 子串误判 | ✅ 先归一再判 + 词边界 |
| 围栏容器前缀 marker 后吞任意空白（`>` 后 5 格 + ``` 被剥成顶层 fence） | ✅ 引用 padding ≤1 格、列表 marker 后 1-4 格 |
| `run_suite` 注解写四元组、实际五元组 | ✅ 更正 |
| preflight docstring 前后矛盾（先说证明「替换非空」，后说不证明） | ✅ 后者改为「不证明**行为**非空/目标防线确被禁掉」 |
| **我把 survivor-7 的功劳记给了新增的「最终变化」门** | ✅ 更正：它是被 `hits != 1` 抓到的 |
| **R22 门文案声称证明「不在围栏内才生效」，实际只测了 `## 附录`** | ✅ 已补 fenced-seed 用例 |
| **列表 continuation 未建模**（`- item` 之后的相对内容列） | ⚠️ **未改**，你说继续补单条 regex 无法闭合这一面，我同意，属重做设计 |
| tips 两数仍 raw；③段标题仍 raw 定位；D2 丢掉 H2 标题行；`_visible_text` 非完整 renderer；变异归因过宽（`-k` OR 只证明至少一道门承重） | ⚠️ **未改**，如实登记 |

## 请重点判断

1. 本轮改动**各自是否正确**？特别是「复用 `_strip_code_blocks` 判在不在围栏内」
   这个做法 —— 它依赖「剥后行数与原文一致」，这个前提在所有分支上都成立吗？
2. 围栏容器前缀的新正则（引用 ≤1 格 padding、列表 marker 后 1-4 格）
   有没有新的漏识别或误识别？
3. **继续留意范围/空间超出意图的改动** —— 你已经抓到我三次了。
4. 行为门里有没有**恒真断言**、或门的措辞比它实际验证的范围更宽？
   （我这轮刚因此被你抓到一次，请再查一遍新加的 R23 门。）
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
  —— 自报 **273 passed**（开工基线 249）。以及 `git rev-parse HEAD`
  —— 应为 `636b09a421fbe13ae7551e8ba10d376cdec32fbb`。
- **不要**运行 `git diff` / `git show` / `git log -p`（此前曾因此中断）。
- **不要**运行 `recap_domain_negverify.py`：它会原地改写被测源码再还原，
  上一轮你跑它时中途被打断，把变异留在了工作树里未还原，随后的 pytest
  因此测的是被改过的文件。本轮请只读它的源码。
- **不要**构造探针脚本或临时文件；不读 `fixtures/` 下的 `.md` / `.json` 正文。

车道自报的其余数字（供你核对，不必重跑）：变异脚本 56/56 全部如期变红，
被测文件运行前后逐字节一致；扩大回归 `tests/skills + 两个 regression 文件`
= 605 passed。

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
