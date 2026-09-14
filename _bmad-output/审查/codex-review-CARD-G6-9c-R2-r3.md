> 批次: BATCH-2026-09-11-第十四批 · 车道 T3（`card-t3-review`）· 卡 CARD-G6-9c-R2 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`--version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-R2-r3.md)"`
> 审查绑定: `08100483 → 130e2dd2 → 25933d55 → 5a9d835e`（送审时 HEAD = `5a9d835e`；本轮审后按其意见又改了代码 ⇒ **不绑最终 HEAD**，另送 round-4 绑 `75f5102b`）
> 会话头自证（抄 `.stderr` 中含版本 / model / reasoning 的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（L2） / `model: gpt-6-astra`（L5） / `reasoning effort: ultra`（L9）

---

复核未通过：**1 HIGH、1 MEDIUM、3 LOW**。接受原 **HIGH-1 的驳回**，不再把它计为本卡新增问题。

绑定 `5a9d835e6fe26958edfc27ec7700c0e2cba7feba`；以下 C 库结果限定本机 macOS，未联网、未连接数据库、未修改文件。

**BLOCKER：无。**

**HIGH-1：省略规则仍新增接受 C 库拒收的串，原 HIGH-2 未完全关闭。**

位置：[local_tz.py:197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:197)、[display_tz.py:196](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/core/display_tz.py:196)。

两类独立反例：

- `"AAA0<BBB>\n"`，末尾为真实 LF：既有正则的 `$` 配合 `.match()` 允许留下末尾换行。
- `"A" * 508 + "0BBB"`：没有限制名称长度，宿主 C 库拒收；相邻的 507 个 `A` 正控被双方接受。

**复现：**两串在 `2026-07-01T23:30Z` 上，BASE 返回 `None`、C 库退 UTC，均为 **7月1日23:30**；HEAD 接受并换算为 **7月2日00:30+01:00**。

正则宽松性虽是既有代码，但本卡补默认规则后才让这些串参与换算，属于**本卡新增错误接受面，r2→HEAD 尚未修掉**。

**MEDIUM-1：拒绝表没有守住负向 DST 差值边界。**

位置：[test_g6_9c_single_tz_source.py:600](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:600)。

当前实际是 **13 条拒绝＋3 条正控**，不是 11 条。三种指定退化确实都有承重：

| 删除检查 | 能抓住的输入 |
|---|---|
| std 侧 | `AAA24BBB23` |
| dst 侧 | `AAA23BBB24` |
| 差值 | `AAA12BBB-12` |

但两张表仍不构成完整验证。

**复现：**仅在内存把 `abs(dst_off - std_off) >= 86400` 改成 `(dst_off - std_off) >= 86400`，13 拒＋3 正全部通过；`AAA-12BBB12` 却被接受，夏季调用 `.dst()` 抛出 `ValueError`，因为差值为 **−24h**。

**当前 HEAD 正确拒绝此串；问题是新增测试缺少防退化覆盖。**

**LOW-1：三条偏移检查通过，仍可能因候选年份越界抛异常。**

位置：[local_tz.py:286](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:286)、[display_tz.py:285](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/core/display_tz.py:285)。

**复现：**用 `AAA0BBB` 转换 `0002-07-01T12:00Z`，偏移只有 `0/+1h`，三检查全通过，但候选 `y−2=0` 导致 `ValueError: year must be in 1..9999, not 0`。

显式串 `AAA0BBB,M3.2.0,M11.1.0` 在同一时刻 **BASE 成功、HEAD 失败**，证明年份 2 是本卡扩大候选窗带来的新增边界；这不是差值检查漏洞，且在声明的 C 库对齐年份范围之外。

**LOW-2：LOW-3 的新解释仍然不准确。**

位置：[test_g6_9c_single_tz_source.py:493](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:493)。

2024 是闰年，`+365.17 天` **尚未滚入下一年**。

**复现：**计算 `AAA1BBB0,365/3,365/2` 的窗口，实际季度为：

`start(2024)=2024-12-31 04:00Z → end(2025)=2026-01-01 02:00Z`

它的 start 没有滚出名义年，却仍需 `y−2` 才能覆盖 2026 元旦。因此，“start 有没有滚年决定是否需要 y−2”这个区分点不成立；这里关键是采用的 **end(2025) 延伸到了 2026**。前三个替代串的新日期描述则与实测一致。

**LOW-3：固定偏移／±2h 的旧说明仍有遗漏。**

位置：[test_review_overview.py:898](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/unit/test_review_overview.py:898)。

**复现：**对照该注释与 `_gate_buckets` 的缺失分支：注释仍说缺键进入固定偏移回退、按 ±2h 翻转判断，实际已经统一拒收。这段属于 **BASE→HEAD 累计 diff 新增内容**，只是没有出现在本次五文件整改 diff 中。

另外几个问题的明确结论：

- **接受域不能称为逐条相等。** 单个正负号、重复符号拒收、所测缺省字段和秒 `60` 的算术进位均对齐。引用名中的冒号、空格、下划线、逗号、中文及长度 1/2，本机 C 库也接受，不能按严格字符表误判。反向差异仍有 `AAA0000BBB`、`<>0BBB`、`<A<B>0BBB`：C 库接受而 BASE/HEAD 都拒，属于**既有范围缺口**。归一化到 ±24h 或 DST 差达到 ±24h 的拒收，则是明确的 Python 可表示性取舍。
- **差值检查对 `dst()` 返回值可表示性充分。** 返回值只能是 `0` 或 `dst_off−std_off`。587 个获准规格在 2007..2037 的 **218,364 个墙钟／偏移对照点零分歧**；额外 **21,132 点**调用 `dst/timetuple/isoformat` 和转回 UTC，零异常。不能由此推出全部年份都安全，见 LOW-1。
- **42／448.70／365／730 天均为安全界。** 最大显式字段为 `41.6948958333` 天，隐式 DST 偏移最大 `41.7365625` 天；最大转移时刻相对元旦为 `448.3897916667` 天。两个排除距离分别至少 365、730 天。
- **仍有既有注释错误，不计新增：** [local_tz.py:288](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:288) 把 `s≤e` 解释为“窗口落在同一年内”；WART 的 2024 窗口实际延至 `2025-01-01 04:00Z`。BASE 已有同义表述。
- **原 HIGH-1 驳回成立。** [review_overview.py:544](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/api/v1/endpoints/review_overview.py:544) 的生成瞬间偏移自洽检查在 BASE 已存在。BASE、r2、HEAD 的参照时区探针结果一致；未发现本卡引入或加重 Bogota 换名面。维持“既有自洽核验上限”的判断，撤销其作为本卡 HIGH 的计数。

两份共享定义源码逐字一致；测试函数名集合为 `19→23→25→25`，相对 BASE 无丢失。验证采用源码对照和内存探针，未运行会创建临时文件的整套 pytest；六个累计改动文件的前后 SHA-256 均一致。
