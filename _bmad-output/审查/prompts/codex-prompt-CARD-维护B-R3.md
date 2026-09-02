# 代码复核请求：一个本地笔记工具的「报告数字有出处」校验器（第四次）

你是独立代码复核者。复核一个**单机离线学习笔记工具**的一处校验逻辑。
没有网络接口、没有多用户、不处理任何凭据。

## 背景（三句话）

用户在 Obsidian 里让 AI 生成学习白板的「回顾报告」。报告里出现的计数
（「本板共有 N 个子节点」这类）必须能在扫描结果 JSON 里找到同值来源，
否则校验器报错、报告打回重写。目的是**防止 AI 在报告里编造数字**。

要复核的问题只有一个：**校验器读到的数，与用户在 Obsidian 里渲染后看到的数，
是不是同一个**。

## 上一次复核的意见与本次处置

| 你上次的意见 | 处置 |
|---|---|
| **恒真断言**：测试读自身源码找一个就在断言行里的字符串 | ✅ **你判对了**。实测验伪：删掉真正的调用点，门仍 2 passed。已改 monkeypatch 哨兵，再验 → 1 failed。这是本卡**第三次**同款恒真断言 |
| 崩溃识别不是可靠二分（内层无 traceback 崩溃假阴 / 正文偶含 traceback 假阳 / 缩进只是当前 formatter 启发式） | ✅ **说法已收回**。结构调整：**确定性的一半**改由测试侧在源头打 `[[CHILD-CRASH]]` 标记（子进程 stderr 出现 traceback 即标记，不依赖任何渲染格式）；解析 pytest 渲染**降级为补充启发式**，能力边界写进 docstring |
| 注释称绑定「`-q` 默认 tb」，实际 pytest.ini 强制 `--tb=short` | ✅ **事实错误已更正**；并补了 1/2 格缩进的门证据（无实测样本，判为异常是保守方向，显式锁住） |
| ③段「段外伪信号」门的注入锚仍在③段内，措辞过宽 | ✅ 措辞已收窄，真正的段外路径如实登记为本门不覆盖 |
| 变异 #48 名称比范围宽 | ✅ 变异已扩到全部分隔面 |
| ③标题 / seed / tips 的 raw/visible 夹缝（你指出 manifest 模式没有形状门） | ✅ **你又判对了**。manifest 模式下 seed 台账双行逃逸**两条实测放行**，已修；tips 与③标题在两种模式下都**未能复现**，如实登记为「未复现 ≠ 安全」 |

**两处方法论更正**（供你判断我这次是否还犯同样的错）：

1. 我上一轮说「三处 raw 绑定实测不成立」，错在**两层**：攻击形态选错
   （只测「改坏那条唯一正确行」，没测「留一条好的 + 加一条渲染等价的冲突行」）；
   以及**只在一个数据模式下验证就下全局结论**。
2. 修 seed 时我写的 `text = _visible_block(text)` 落在了 `_verify_report` 的
   **函数体作用域**，重绑了局部 `text` ⇒ **其后所有检查**都吃到归一文本。
   症状是一条既有变异变成空变异；已收窄为局部变量。
   **请留意我这次有没有别处也做了范围超出意图的改动。**

## 请重点判断

1. 上述改动**各自是否正确**？有没有引入回归、误伤合法用法、
   或让某条既有检查变成走不到的死分支？**特别是有没有别处的作用域/范围泄漏。**
2. 崩溃识别现在是「确定性标记 + 补充启发式」两层。这个结构是否成立？
   标记那一半有没有漏（什么样的子进程崩溃不会产生 traceback）？
3. 「tips」「③段标题」两处我**未能复现**的观察是否成立？
   请按代码路径推理，**不需要**构造输入。
4. 新增的行为门里有没有**恒真断言**、或者门的措辞比它实际验证的范围更宽？
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
  —— 自报 **270 passed**（开工基线 249）。以及 `git rev-parse HEAD`
  —— 应为 `f7d25f5800d551170679cba766e002e6c0872deb`。
- **不要**运行 `git diff` / `git show` / `git log -p`（此前曾因此中断）。
- **不要**运行 `recap_domain_negverify.py`：它会原地改写被测源码再还原，
  上一轮你跑它时中途被打断，把变异留在了工作树里未还原，随后的 pytest
  因此测的是被改过的文件。本轮请只读它的源码。
- **不要**构造探针脚本或临时文件；不读 `fixtures/` 下的 `.md` / `.json` 正文。

车道自报的其余数字（供你核对，不必重跑）：变异脚本 51/51 全部如期变红，
被测文件运行前后逐字节一致；扩大回归 `tests/skills + 两个 regression 文件`
= 602 passed。

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
