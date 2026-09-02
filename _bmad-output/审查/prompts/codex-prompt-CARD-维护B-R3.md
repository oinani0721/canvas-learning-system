# 代码复核请求：一个本地笔记工具的「报告数字有出处」校验器（第八次）

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
| **四空格围栏限制实际失效**：前缀剥离先吃掉任意前导空白，`open_re` 的 ` {0,3}` 形同虚设 | ✅ 只剥**容器前缀**（引用 `>` / 列表 marker，各自 ≤3 格），无 marker 时不动缩进。实测四空格伪围栏已拦，顶层/三格真围栏与列表项内围栏三条对照不受伤 |
| 种子尾巴「覆盖扩大**且**接受集放松」，我只说了扩大那一半 | ✅ 措辞已改成两者兼有；并补 `_tail_conflict()`：尾巴里再写**同名字段** `批注 N 条` 即 fail-closed。其它字段（`理解度未闭环 N 条`/`已派生 N 点`）在 scan JSON 无逐节点对应，**不绑定**，如实登记 |
| 「逐个处理全部小节」范围超出意图（未限父级 `## 台账`、未排围栏） | ✅ 收窄。这是你**第三次**抓到我「改动范围超出意图」 |
| `preflight()` 只检查 `old != new`，docstring 说「不证明替换非空」而成功消息宣布「替换非空」，自相矛盾 | ✅ 选择把**检查改强**：按真实顺序模拟整组替换、要求最终源码确实变化。**改完当场抓到 `survivor-7`**（锚点因同轮围栏修复而失效） |
| 拒绝门只断言 `returncode != 0`，未绑定诊断原因 | ⚠️ 新门已用诊断绑定；**存量门未逐条改**，如实登记 |
| tips 两数仍 raw；③段小节仍从 raw 标题提取；D2 丢掉 H2 标题行本身；`_visible_text` 非完整 renderer；变异归因过宽（`-k` 用 OR 时只证明至少撞上一道门） | ⚠️ **未改**，如实登记（多属重做设计） |

## 请重点判断

1. 本轮改动**各自是否正确**？特别是围栏前缀剥离的新正则 —— 它同时要满足
   「剥掉引用/列表容器前缀」与「无 marker 时保留缩进」，有没有漏掉的容器形态
   （例如 `>` 后直接跟内容、多层嵌套、有序 marker 的变体）？
2. `_tail_conflict()` 只堵「同名字段第二次出现」这一种矛盾，边界写准了吗？
3. **继续留意范围/空间超出意图的改动** —— 你已经抓到我三次了。
4. 行为门里有没有**恒真断言**、或门的措辞比它实际验证的范围更宽？
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
  —— 自报 **272 passed**（开工基线 249）。以及 `git rev-parse HEAD`
  —— 应为 `8fa72b2fd4ab8e4cf534a8aa7c0aef335873b2dd`。
- **不要**运行 `git diff` / `git show` / `git log -p`（此前曾因此中断）。
- **不要**运行 `recap_domain_negverify.py`：它会原地改写被测源码再还原，
  上一轮你跑它时中途被打断，把变异留在了工作树里未还原，随后的 pytest
  因此测的是被改过的文件。本轮请只读它的源码。
- **不要**构造探针脚本或临时文件；不读 `fixtures/` 下的 `.md` / `.json` 正文。

车道自报的其余数字（供你核对，不必重跑）：变异脚本 54/54 全部如期变红，
被测文件运行前后逐字节一致；扩大回归 `tests/skills + 两个 regression 文件`
= 604 passed。

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
