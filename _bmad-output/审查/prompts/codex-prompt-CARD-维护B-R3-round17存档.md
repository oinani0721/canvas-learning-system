# 代码复核请求：一个本地笔记工具的「报告数字有出处」校验器（第十七次）

你是独立代码复核者。复核一个**单机离线学习笔记工具**的一处校验逻辑。
没有网络接口、没有多用户、不处理任何凭据。

## 背景（三句话）

用户在 Obsidian 里让 AI 生成学习白板的「回顾报告」。报告里出现的计数
（「本板共有 N 个子节点」这类）必须能在扫描结果 JSON 里找到同值来源，
否则校验器报错、报告打回重写。目的是**防止 AI 在报告里编造数字**。

要复核的问题只有一个：**校验器读到的数，与用户在 Obsidian 里渲染后看到的数，
是不是同一个**。

## 上一轮你判 B/H 清零＝否，逐条处置如下（请复核每一条）

| 你的判词 | 处置 |
|---|---|
| **BLOCKER** `%%…%%` 隐藏硬断点 | ✅ 修：按 **HTML 注释逐字同款**口径 —— 原始文本上一次判死 + 校验前剥掉。配 `r30` 门（5 报 1 放，含「单个 `%` 不误伤」对照）|
| **HIGH** 第八形态（`_h3_wellformed` 标题体收 `[^\n]*`）| ✅ 修：按它自己 docstring 声称的「与 `_SECTION_RE` 同精神」收紧 —— 恰好一个空格、标题不含 Markdown 标记、无尾随闭合井号 |
| **HIGH** inline-code/highlight 两条靠尾随 ` ###` 才红 | ✅ 你说得对。已补**不带 closer** 的独立条目，`r27` 扩到 15 形态（9 报 6 放）|
| **HIGH** 首个 H3 之前无人看管 | ✅ 修：`_cur_bad` 初值改 `True` |
| **HIGH** `tips_open`/`derived_children_count` 有字段却没绑 | ✅ 修：已补逐节点绑定 + `r31` 门（篡改必红、无字段不误报）。**那句「没有对应逐节点字段可绑」是假声明，已删** |
| **HIGH** 变异证据：73 未独立冻结 / 只比计数不比身份 / collect-only rc 未查 / 列表内未查重 | ✅ 四条全修：`DESIGNATED_COUNT_EXPECTED=78` 独立冻结、`-rf` 解析真实失败 nodeid 集要求与指名集**完全相等**、rc 检查、列表内查重 |
| ⚠️ round-35 语义扩张 `1, 2个`→`12个` | ✅ 修：改回本域既有的「**定界要宽、赋值要窄**」—— 分隔符进定界集（不再制造硬断点）但不参与赋值 ⇒ 含糊分隔 fail-closed。⚠️ 我第一版把合法分组**首段**也限成 1-3 位，当场打红 `r7`（收窄判据时把一条既有契约一起收掉了）|
| ⚠️ `r29` 只断言 `rc != 0`（目标无关假绿）| ✅ 绑定诊断关键词；机制断言改为**安全性质**断言 |
| ⚠️ `survivor-14/29` 只算「性质相关」 | ⚠️ **未改**，登记 |
| ⚠️ 锁的窄窗口（`LOCK.mkdir()` 后、进 try 前）| ⚠️ **未改**，登记；根治是改副本不改原件 |
| ❌ **A1 软换行绕过 D2** | ❌ **未修**：D2 按**源码行**判句式而 Obsidian 渲染是**段落**，修法是把判定单位从行改到渲染段 —— 属重做设计，你也确认它本身足以维持 BLOCKER |

新增变异 `survivor-67~71` 分别锁住上述五条新防线；`survivor-12/13/20` 三条**存量**
锚点被本轮改动打歪，已由预检当场抓出并重锚。

## 请重点判断

1. **上表每一条处置是否真的成立** —— 尤其 `%%` 的「原始文本上一次判死」有没有
   误伤面（我只测了单个 `%`），以及 `_h3_wellformed` 收紧后有没有**第九形态**。
2. **「定界宽/赋值窄」这个改法**：分隔符进 `_NUM_RUN_CHARS` 之后，有没有别处
   因此变宽或变窄（我跑了全套 281 门 + 613 扩大回归，但门只覆盖已写断言）。
3. `survivor-67~71` 的**指名**对不对？判据 `collected == failed == len(指名)`
   且 `failed_ids == set(指名)` 还有没有绕过？
4. **继续留意范围/空间超出意图的改动** —— 你已经抓到我三次了。
5. 行为门里有没有**恒真断言**、**目标无关假绿**、或门的措辞比实测宽？
6. 还剩哪些问题？请把「一次改动内能闭合的」与「需要重做设计的」分开列。

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
  —— 自报 **281 passed**（开工基线 249）。以及 `git rev-parse HEAD`
  —— 应为 `e3ee51d7` 开头的那个 commit。
- **不要**运行 `git diff` / `git show` / `git log -p`（此前曾因此中断）。
- **不要**运行 `recap_domain_negverify.py`：它会原地改写被测源码再还原，
  上一轮你跑它时中途被打断，把变异留在了工作树里未还原，随后的 pytest
  因此测的是被改过的文件。本轮请只读它的源码。
- **不要**构造探针脚本或临时文件；不读 `fixtures/` 下的 `.md` / `.json` 正文。

车道自报的其余数字（供你核对，不必重跑）：变异脚本 **71/71 指定门全数杀死**（nodeid 绑定 + 失败身份比对），
被测文件运行前后逐字节一致；扩大回归 `tests/skills + 两个 regression 文件`
= 613 passed。

## 输出格式

- 第一行：`BLOCKER/HIGH 清零：是/否`
- 逐项 ✅/⚠️/❌ + `file:line` + 依据（你实际读到/跑出的观测值）。
- 存量未闭合的问题也请报，并标注是存量还是本轮引入。
- 写出你实际跑出的 pytest 结果与 `git rev-parse HEAD`。
- 末尾写明验证限制（没跑的、无法证明的）。
