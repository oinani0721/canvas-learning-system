# 代码复核请求：一个本地笔记工具的「报告数字有出处」校验器（第十一次）

你是独立代码复核者。复核一个**单机离线学习笔记工具**的一处校验逻辑。
没有网络接口、没有多用户、不处理任何凭据。

## 背景（三句话）

用户在 Obsidian 里让 AI 生成学习白板的「回顾报告」。报告里出现的计数
（「本板共有 N 个子节点」这类）必须能在扫描结果 JSON 里找到同值来源，
否则校验器报错、报告打回重写。目的是**防止 AI 在报告里编造数字**。

要复核的问题只有一个：**校验器读到的数，与用户在 Obsidian 里渲染后看到的数，
是不是同一个**。

## 上一次复核的意见与本次处置

**你抓到的根因**：`_SECTION_RE` 的 docstring 里明写着「存在性检查与下游定位必须
共用本函数」，而我上一轮为了让 ATX 支持缩进与闭合井号，**在种子扫描里自己写了
两式** —— 正好犯了那句话警告的事。你给的 `## 台账（x` 反例成立：必需段门认在场、
我的式子拒收 ⇒ 种子校验器拿到零个 section 直接返回，`999` 完全不绑定。

⇒ **改回共用 `_SECTION_RE`**。代价是缩进标题与 ATX 闭合井号**两侧一致地不接受**；
我补了**端到端验证**：那样写的报告会被必需段门判 FAIL，所以「不接受」不是漏网。
要放宽得改 `_SECTION_RE` 本体让两侧同时动 —— 不在本轮范围。

| 你的其余意见 | 处置 |
|---|---|
| 「小节内跳过围栏」只保护消费行、没保护**小节终点**（围栏内 `## 假标题` 提前截断） | ✅ 终点扫描也判围栏 |
| R24 文案宽于实测（六处） | ⚠️ 新 R25 门补了「围栏内标题截断」与「端到端 fail-closed」两条；其余**如实收窄措辞**，未逐条补 |
| 我 round-27/28 的两条门编码了旧的分叉决定 | ✅ 随统一口径改判 |
| 围栏容器区分仅修对窄例；`(?<!未)批注` 数字域仍漏；ATX 只在普通 ASCII 行基本正确 | ⚠️ **未改**，登记 |
| 列表 continuation 未建模；tips 两数仍 raw；③段 raw 多处定位且边界口径不一致；D2 丢 H2 标题行；fallback ⑦ 对 inline-code 反引号失配；缩进代码未纳入 fence map；「60/60」不能逐条证明按名称承重 | ⚠️ **未改**，如实登记（多属重做设计） |

## 请重点判断

1. 改回共用 `_SECTION_RE` 之后，种子绑定的入口与全局必需段门**端到端一致**了吗？
   还有没有别的消费方在用自造口径？
2. 小节终点判围栏之后，还有没有能让小节提前/延后终止的形态？
3. **继续留意范围/空间超出意图的改动** —— 你已经抓到我三次了。
4. 行为门里有没有**恒真断言**、或门的措辞比它实际验证的范围更宽？
   （你连续两轮抓到我文案宽于实测，请再查新加的 R25 门。）
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
  —— 自报 **275 passed**（开工基线 249）。以及 `git rev-parse HEAD`
  —— 应为 `11a95fdcd87e38b2c0a992bd1969ba9321808219`。
- **不要**运行 `git diff` / `git show` / `git log -p`（此前曾因此中断）。
- **不要**运行 `recap_domain_negverify.py`：它会原地改写被测源码再还原，
  上一轮你跑它时中途被打断，把变异留在了工作树里未还原，随后的 pytest
  因此测的是被改过的文件。本轮请只读它的源码。
- **不要**构造探针脚本或临时文件；不读 `fixtures/` 下的 `.md` / `.json` 正文。

车道自报的其余数字（供你核对，不必重跑）：变异脚本 60/60 全部如期变红，
被测文件运行前后逐字节一致；扩大回归 `tests/skills + 两个 regression 文件`
= 607 passed。

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
