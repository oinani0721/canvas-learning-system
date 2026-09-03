# 代码复核请求：一个本地笔记工具的「报告数字有出处」校验器（第十八次·末轮）

你是独立代码复核者。复核一个**单机离线学习笔记工具**的一处校验逻辑。
没有网络接口、没有多用户、不处理任何凭据。

## 背景（三句话）

用户在 Obsidian 里让 AI 生成学习白板的「回顾报告」。报告里出现的计数
（「本板共有 N 个子节点」这类）必须能在扫描结果 JSON 里找到同值来源，
否则校验器报错、报告打回重写。目的是**防止 AI 在报告里编造数字**。

要复核的问题只有一个：**校验器读到的数，与用户在 Obsidian 里渲染后看到的数，
是不是同一个**。

## 上一轮处置（请逐条复核）

| 你的判词 | 处置 |
|---|---|
| ❌ **第九形态**（`### 其他` / `### 种子 (说明)` ASCII 括号 / `### 种子 ^id` 块 id / 缩进 H3 不更新状态）| ✅ 修：安全态收窄为「统一口径 `_SECTION_RE` 认得出的台账小节」（`种子`/`派生` 两项），并认 1-3 空格缩进。⚠️ 这张表**封闭**（模板自己的段名），与 round-33 要避开的「伪装面开放集闭表」不同 —— 那边枚举的是**攻击形态** |
| ⚠️ 我引入的误伤：`_NUM_RUN_PAT` 让分隔符**单独**成 token ⇒ `#### 派生，说明` 报「无法验证的数字」| ✅ 修：run 首尾都必须是数字字符 |
| ⚠️ 合法分组吞 `_D2_JOIN_ONE`（含空白与「约」等可见字）⇒ `1, 002`/`1,约002` 归成 `1002` | ✅ 修：分组内不再容连接字符（标签/零宽此前已由 `_visible_text` 剥掉）|
| ❌ `survivor-71` 目标无关先红 | ✅ 重写为「分组内重新容连接字符」，精确对应上面那条 |
| ❌ 测试侧残留假声明（与 `r31` 自相矛盾）| ✅ 删 |
| ⚠️ `r27` 宣称「十五形态九报六放」，实数十报五放 | ✅ 改为**按实际表算并断言**，不再手写汇总数 |
| ⚠️ `r29` 文案仍说「分隔符一律删除」| ✅ 更正为「定界宽/赋值窄」|
| ⚠️ `r29/r30` 只判 `rc != 0`（把崩溃算成拦截）| ✅ 统一助手 `_assert_rejected`：`rc==1` + 拒 traceback + 绑关键词 |
| ⚠️ `DESIGNATED` 只冻结总数、身份未独立冻结；dict 重复 key 在 preflight 前被 Python 覆盖 | ⚠️ **未改**，登记 |
| ⚠️ `survivor-14` 只算性质相关；锁窄窗；hash 检查用 `assert`（`python -O` 可移除）| ⚠️ **未改**，登记 |
| ❌ A1 软换行 + 本轮新报三条存量 BLOCKER（H2 标题不进 D2 / `数据来源与新鲜度` 段无条件豁免 / inline-code 豁免不是白名单）+ 开放集 HIGH | ❌ **未修**：均属「先渲染再核数」重做设计的同一根因 |

⛔ **一条值得你知道的发现**：`survivor-68`（打 `_h3_wellformed` 标题体）本轮
**未承重** —— 因为上一轮改用 `_SECTION_RE` 判定后，那个函数已**定义了但无人调用**。
281 门全绿、613 回归全绿、ruff 全过、你读源码也没提，**没有任何东西会因为一个函数
没人调用而变红**；只有「改它不影响任何行为」把它照了出来。已删死代码，
`survivor-68` 按「被取代的死纵深」退役，`survivor-73` 改为自包含（原文本引用已删函数
会变成 `NameError` ＝ 崩溃伪红）。

## 请重点判断

1. **第九形态是否真的闭合** —— 安全态改成「只认 `### 种子` / `### 派生`」之后，
   还有没有**第十形态**？以及这个收窄有没有新的**误伤**面？
2. 上表每条 ✅ 是否成立；两条自伤修法有没有再开新口。
3. `survivor-71/72/73` 的**指名**对不对？有没有「目标无关先红」？
4. **继续留意范围/空间超出意图的改动** —— 你已经抓到我三次了。
5. 行为门里有没有**恒真断言**、**目标无关假绿**、或门的措辞比实测宽？
6. 这是本卡的**末轮**（卡文上限 3 轮）。请给一句总判：
   在**不做「先渲染再核数」重做设计**的前提下，本域还剩多少可闭合面？

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
  —— 应为 `1bfb51b1` 开头的那个 commit。
- **不要**运行 `git diff` / `git show` / `git log -p`（此前曾因此中断）。
- **不要**运行 `recap_domain_negverify.py`：它会原地改写被测源码再还原，
  上一轮你跑它时中途被打断，把变异留在了工作树里未还原，随后的 pytest
  因此测的是被改过的文件。本轮请只读它的源码。
- **不要**构造探针脚本或临时文件；不读 `fixtures/` 下的 `.md` / `.json` 正文。

车道自报的其余数字（供你核对，不必重跑）：变异脚本 **72/72 指定门全数杀死**（nodeid 绑定 + 失败身份比对），
被测文件运行前后逐字节一致；扩大回归 `tests/skills + 两个 regression 文件`
= 613 passed。

## 输出格式

- 第一行：`BLOCKER/HIGH 清零：是/否`
- 逐项 ✅/⚠️/❌ + `file:line` + 依据（你实际读到/跑出的观测值）。
- 存量未闭合的问题也请报，并标注是存量还是本轮引入。
- 写出你实际跑出的 pytest 结果与 `git rev-parse HEAD`。
- 末尾写明验证限制（没跑的、无法证明的）。
