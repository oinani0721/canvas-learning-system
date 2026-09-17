# 独立复核请求 round-3 — CARD-AILINKED-4TH-WRITER

## 一 背景与最小读取面

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
分支 `card/t7-skills`。**本轮审查绑定 `HEAD = 12f85104`**。
round-1 审 `41629ec3`（B0/H0/M2/L1），round-2 审 `65e3f333`（B0/H0/M1/L0）。两轮四条全部整改。

请读：

1. `git diff 65e3f333 12f85104 -- . ':(exclude)_bmad-output'`（**本轮整改的全部改动**）
2. `git diff d5ad6fca 12f85104 -- . ':(exclude)_bmad-output'`（本卡全部代码改动，5 文件）
3. `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` 的 Step 5.5 写点块（`:214-354`）
4. `backend/tests/skills/test_ai_linked_doc_writer.py` 全文（现为 5 个门 + 2 个伴随/验伪锚）
5. `backend/app/services/learning_event_log.py:188-343`（backend 侧参照实现，只读）

## 二 round-2 一条的整改内容（请独立核对）

### MEDIUM → 有损 UTF-8 解码使无法解码的坏行成为查重证据

采纳你的定位与修法。现在查重段的形态是：

- 按**物理 LF** 切 **bytes**（`raw.split(b'\n')`，末尾 LF 之后的空串不算一行）；
- 逐行在 `try` 内**严格**解码后再解析（`json.loads(_bl.decode('utf-8'))`）；
- 捕获 `(ValueError, RecursionError)`——`UnicodeDecodeError` 是 `ValueError` 的子类，一并接住；
- **没有**改成整本严格解码（那会让一条坏行中止整次追加，方向更坏）。

新增门 `test_undecodable_line_is_not_dedup_evidence`：预置一条 `event_id` 恰等于目标 evid、
但 `payload` 里含原始字节 `0xff` 的历史行，断言新事件仍落账恰 1 条。
先红实测（两个不同的历史版本，两种失败形态）：

- 对 `d5ad6fca`（原始 `python3 -c` 单行写点）：红在 `rc=1` —— 写点**直接崩溃**于
  `UnicodeDecodeError`（原写点对 `open(ev, encoding='utf-8')` 的迭代没有任何 try 保护）；
- 对 `65e3f333`（round-1 版，整本有损解码）：红在承重断言 —— **静默零落账**。

请核对：现在这条路径上还有没有别的输入能让「坏行的代价超出它自己那一行」？
`_bl.strip()` 对纯空白 bytes 行的处理、`raw` 为空时的分支，有没有边界问题？

### 自查补漏（不是你提的，是本轮自己发现的）

本卡此前在 SKILL.md 的一行注释里引入了 **2 个裸 U+2028 / U+2029 码点**（全仓其余 8 个
`SKILL.md` 该计数均为 0，故确认是本卡引入）。已改为转义写法 ` ` / ` `。
讽刺之处：那行注释正是在说「不要用 `splitlines()`，因为这些字符会被切开」。
请核对：改后全文该计数是否为 0？还有没有别的不可见字符残留？

## 三 你在 round-2 指出的两条限制，我**未**改代码，只登记，请确认这样处理合适

1. **计时不是无条件保证**：`t_held` 是父进程收到 `held` 的时刻、`t0` 在 gate 放行后记录，
   `HOLD_S * 0.25` 留出的余量不能覆盖任意调度停顿。
2. **「必红」不是跨机器保证**：固定 backlog 与 busy-spin 屏障放大了竞态窗口，但门② ① 那条
   的必红性依赖「解析耗时 > 取锁轮询间隔」这个时间常数关系。

我的处理：两条都如实写进验收单的「本卡未证明什么」，不改代码——理由是更强的形态
（你建议的 `sys.settrace` + pipe 握手把写者暂停在「读完快照、尚未追加」处）需要在提取到的
逐字模板外再套一层执行控制，复杂度与本卡收益不成比例，且会引入新的「trace 改变被测行为」风险。
请判断：这个取舍是否合适？如果你认为必须改，请说明理由与最小形态。

## 四 仍需复核的原有问题（结论若不变可简短确认）

⓪ parsed-field 相等是否覆盖「历史行中非 event_id 字段的值恰等于新 evid」。
① fd 生命周期：锁内全程同一 fd、`close` 在锁内、无隐式重开账本的路径。
② LF 守卫在锁内、`raw` 为空时不补 LF。
③ 形态门：首尾空白拒写不 strip、码点集与校验器 `validate_learning_events.py:426` 同集、
   门④ 三类反例在 `derive:` 前缀下都可达。
④ 外形与提取：门⑪ 集合仍 4 份、块正文无行首 `PYEOF`、两处 `<>` 占位逐字保留、
   producer 门只动了 ai-linked-doc 那一个函数。
⑤ backend `learning_event_log.py` 仅改注释（去 docstring 后 AST 与 `d5ad6fca` 相同）。

作者侧本轮实测：`tests/skills` **555 passed**（基线 546 + 本卡 9）、四个 regression 文件
**569 passed / 1 skipped**（与开工同数）、`tests/unit` 红集与 64 条基线**逐条相同**、
`pyright app`（cwd=`backend/`）**0 errors, 81 warnings**、`ruff check` 与 `ruff format --check` 均通过、
五段负控各红在指定断言且两份被监视文件跑前/跑后 `shasum -a 256` 逐字相同。

## 五 输出格式与边界

- 按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句定位思路；没有的分级写「无」。
- **只读**，不修改任何文件；不连任何数据库（7691 / 7687 不碰）。
- `pyright` 若在你的环境仍启动失败（前两轮报缺 `libllhttp.9.3.dylib`），如实写「未复证」即可。
- 不评 `start-exam-board/SKILL.md:477` 的同类子串残留（已登记移交，非本卡面）。
- 不评「完整 vault 里真实跑一次 ai-linked-doc skill」——本卡只逐字提取写点模板用 subprocess 跑。
