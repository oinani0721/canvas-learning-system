# 代码复核请求：一个本地笔记工具的「报告数字有出处」校验器（第十三次）

你是独立代码复核者。复核一个**单机离线学习笔记工具**的一处校验逻辑。
没有网络接口、没有多用户、不处理任何凭据。

## 背景（三句话）

用户在 Obsidian 里让 AI 生成学习白板的「回顾报告」。报告里出现的计数
（「本板共有 N 个子节点」这类）必须能在扫描结果 JSON 里找到同值来源，
否则校验器报错、报告打回重写。目的是**防止 AI 在报告里编造数字**。

要复核的问题只有一个：**校验器读到的数，与用户在 Obsidian 里渲染后看到的数，
是不是同一个**。

## 上一次复核的意见与本次处置

| 你的意见 | 处置 |
|---|---|
| **#51/#55 的改名并未落实**（你连续两轮点名） | ✅ 已落实。真因是我的批量替换只断言「某处变了」——**同一个坑第三次**。本轮起改为逐条 `assert t.count(old) == 1` |
| ✅ #56 两步替换名实一致 | — |
| **新 H3 fail-closed 误伤合法零种子板**（生成侧允许 `seeds == []` / `counts.seeds == 0`） | ✅ 已修。⚠️ 中间我自己开了一个洞：第一版对 `seeds == []` **提前 return**，于是零种子板里写的任何台账行被**静默放行**（实测漏）。终版**不提前返回**，让绑定面为空自然走「不在 ledger」，五形态全对 |
| 新 H3 fail-closed 只处理「零个认可 section」，没闭合全部 H3 | ⚠️ **未改**，登记 |
| `### 种子 ###` 是合法 ATX，新门扩大了合法拒绝面 | ⚠️ 如实登记：这是「与 `_SECTION_RE` 统一口径」的代价；要放宽须改本体让两侧同动 |
| 名为 `_cli` 的 R23 实际只调 helper；仍有源码形状门而非行为门；`-k` 只确认「某项失败」不确认是目标断言 | ⚠️ **未改**，登记 |
| ③段三套自造定位；D2 豁免段口径不同且丢 H2 标题行；tips 两数仍 raw；尾巴只拦 ASCII `批注 N 条`；`1\*5个` 被剥成 `15`；崩溃二分会判错 | ⚠️ **未改**，如实登记（多属重做设计） |

**一条过程记录**（供你校准）：判据脚本的锚点预检**第一次实战兑现** —— 它秒级中止了
一次本该白跑 40 分钟的流程。触发它的是两个独立错误叠加：重锚脚本的 `old` 串写多
一截（`ruff format` 把多行串压成单行）⇒ 重锚没发生；我用 `;` 而非 `&&` 连接
⇒ 第一步失败第二步照跑。

## 请重点判断

1. 零种子板的五形态处置**各自正确**吗？有没有第六种形态我没覆盖？
2. #51/#55 改名后的描述**准确**吗？（它们各自实际禁掉的是什么。）
3. **继续留意范围/空间超出意图的改动** —— 你已经抓到我三次了。
4. 行为门里有没有**恒真断言**、**目标无关假绿**、或门的措辞比实测宽？
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
  —— 自报 **276 passed**（开工基线 249）。以及 `git rev-parse HEAD`
  —— 应为 `85d5c32c74f5e2e3268f56c0eb7c0d873566abbf`。
- **不要**运行 `git diff` / `git show` / `git log -p`（此前曾因此中断）。
- **不要**运行 `recap_domain_negverify.py`：它会原地改写被测源码再还原，
  上一轮你跑它时中途被打断，把变异留在了工作树里未还原，随后的 pytest
  因此测的是被改过的文件。本轮请只读它的源码。
- **不要**构造探针脚本或临时文件；不读 `fixtures/` 下的 `.md` / `.json` 正文。

车道自报的其余数字（供你核对，不必重跑）：变异脚本 62/62 全部如期变红，
被测文件运行前后逐字节一致；扩大回归 `tests/skills + 两个 regression 文件`
= 608 passed。

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
