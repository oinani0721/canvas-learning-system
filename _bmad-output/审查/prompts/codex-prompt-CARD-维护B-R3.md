# 代码复核请求：一个本地笔记工具的「报告数字有出处」校验器（第五次）

你是独立代码复核者。复核一个**单机离线学习笔记工具**的一处校验逻辑。
没有网络接口、没有多用户、不处理任何凭据。

## 背景（三句话）

用户在 Obsidian 里让 AI 生成学习白板的「回顾报告」。报告里出现的计数
（「本板共有 N 个子节点」这类）必须能在扫描结果 JSON 里找到同值来源，
否则校验器报错、报告打回重写。目的是**防止 AI 在报告里编造数字**。

要复核的问题只有一个：**校验器读到的数，与用户在 Obsidian 里渲染后看到的数，
是不是同一个**。

## 上一次复核的意见与本次处置

**你上一轮最有价值的一条**：我请你留意「有没有别处也做了范围超出意图的改动」，
你找到的那个我完全没想到 —— 我防的是**变量作用域**泄漏，你找到的是**语义空间**
泄漏：小节整体归一后，行里取到的节点名已是 `SeedA`，却仍拿去对 raw `node_id`
`Seed_A`。而且第二个后果比第一个坏得多：不只误拒，**值绑定被整条跳过**，
写错的批注数反而不报数字错。这条已修（先精确匹配 raw id，不中再退归一空间，
归一撞车 fail-closed 不猜，诊断报 raw 名）。

其余处置：

| 你的意见 | 处置 |
|---|---|
| 区间正则手抄了第二份分隔表，我声称的「同源」不成立 | ✅ 改为从同一常量机械生成；门逐字符双向锁 11/11（此前只枚举 5 个） |
| ③段信号行未走共用 helper，「四处消费方同源」不成立 | ✅ 生产已统一；门改为按**调用点计数**锁漂移 |
| docstring 仍称「缩进上界 + 紧跟冒号」，冒号条件早已删除 | ✅ 文案更正 |
| r19 只验「是某个 CompletedProcess」，未证明是**返回的那个** | ✅ 改 `is` 断言 |
| r16 的 case 名仍写「段外」，措辞只收窄一半 | ✅ 改为「③段内伪信号行」 |
| 变异脚本写入在 `try/finally` 之前 | ✅ 挪进 try；SIGKILL/断电兜底不到的部分**如实声明**，不吹 |
| tips / ③标题仍是 raw 绑定；manifest seed 行允许任意 tail；`_visible_text` 不是完整 renderer | ⚠️ **未改**，如实登记（后两条属重做设计） |

**两处我自己在同一小时里又踩的坑**（供你校准对我自证内容的信任度）：
① 写门的判据用 `replace("def X","")` 想排除函数定义 —— **删名字不删函数体**，
门当场变红；② 给新修复写的第一版变异是 `else:` → `elif True:` —— **语义相同 =
空变异**，我在写「小心空变异」的同一小时里又写了一个。两条都已改正。

## 请重点判断

1. 上述改动**各自是否正确**？有没有引入回归、误伤合法用法、
   或让某条既有检查变成走不到的死分支？**继续留意范围/空间超出意图的改动。**
2. 节点身份的「先 raw 精确、不中退归一、撞车 fail-closed」这个三段式是否成立？
   有没有它**判错**的情形？
3. 「tips」「③段标题」两处我**未能复现**的观察是否成立？
   请按代码路径推理，**不需要**构造输入。
4. 新增/修改的行为门里有没有**恒真断言**、或者门的措辞比它实际验证的范围更宽？
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
  —— 自报 **271 passed**（开工基线 249）。以及 `git rev-parse HEAD`
  —— 应为 `514d5bfa2ef0a1a091128160c33d52b56ef41c4e`。
- **不要**运行 `git diff` / `git show` / `git log -p`（此前曾因此中断）。
- **不要**运行 `recap_domain_negverify.py`：它会原地改写被测源码再还原，
  上一轮你跑它时中途被打断，把变异留在了工作树里未还原，随后的 pytest
  因此测的是被改过的文件。本轮请只读它的源码。
- **不要**构造探针脚本或临时文件；不读 `fixtures/` 下的 `.md` / `.json` 正文。

车道自报的其余数字（供你核对，不必重跑）：变异脚本 52/52 全部如期变红，
被测文件运行前后逐字节一致；扩大回归 `tests/skills + 两个 regression 文件`
= 603 passed。

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
