> 批次: BATCH-2026-09-11-第十四批 · 车道 T3（`card-t3-review`）· 卡 CARD-G6-9c-R2 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`/opt/homebrew/bin/codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-R2-r1.md)"`
> 审查绑定: `08100483 → 130e2dd2`（送审时 HEAD = `130e2dd2`；本轮审后按其意见改了代码 ⇒ **不绑最终 HEAD**，另送 round-2 绑 `25933d55`）
> 会话头自证（抄 `.stderr` 中含版本 / model / reasoning 的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（L2） / `model: gpt-6-astra`（L5） / `reasoning effort: ultra`（L9）

---

**本轮不能关闭全部 HIGH：确认 2 条 HIGH、1 条 MEDIUM。候选年窗口本身未发现继续漏格。**

审查绑定 `08100483 → 130e2dd2`。复现使用本机 Darwin/Python 3.14 的纯内存执行；未修改文件、联网或连接数据库。

**BLOCKER：无。**

**HIGH**

1. **±2 小时带宽仍会放行错误桶，HIGH-2 未关闭。**  
   位置：[review_overview.py:628](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/api/v1/endpoints/review_overview.py:628)、常量 `:141`。

   复现：真实时区 `ABC-1DEF-5`，`generated_at=2026-03-08T00:30:00+01:00`，`fsrs_due=2026-03-08T20:30:00Z`；保持单行的计数、板汇总和 upcoming 一致，只交换桶名及是否提供时区。

   | `producer_tz` | 合法 `future` | 伪造 `due_today` |
   |---|---|---|
   | `ABC-1DEF-5` | 放行 | 拒绝 |
   | `None` | 拒绝 | **放行** |

   libc 与解析器都确认到期时刻为 **03-09 01:30 +05:00**。固定 `+01:00` 的 ±2 小时端点却分别为 **03-08 19:30、23:30**，漏掉真实的 +4 小时变化。负向 −4 小时也已复现反向误放行。因此，即使现实常见 DST 都落在两小时内，也不能据此覆盖本项目实际接受的输入域。

2. **省略规则的新分支接受非法偏移，新增静默错日及异常。**  
   位置：[scripts/local_tz.py:149](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:149)、[backend/app/core/display_tz.py:148](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/core/display_tz.py:148)。

   复现：设置 `TZ=AAA0:60BBB`，转换 `2026-01-20T00:30Z`：

   - BASE 与本机 libc：`2026-01-20 00:30+00:00`。
   - HEAD 两副本：**`2026-01-19 23:30−01:00`**。

   分钟 `60` 未经范围校验，被补规则分支接成有效时区；旧版本该串退 UTC。同类 `AAA999BBB` 现在会在输出 `.isoformat()` 时抛出偏移超过 ±24 小时的 `ValueError`。这是新增接受面的回归，并非候选年窗口遗漏。

**MEDIUM**

1. **合法固定时区投影也会被整份拒绝，可用性损失并不限于真实 DST 边界。**  
   位置：[review_overview.py:618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/api/v1/endpoints/review_overview.py:618)。

   复现：真实固定 UTC，`generated_at=2026-09-14T12:00:00Z`，合法 `due_today` 行到期于 `2026-09-14T23:30:00Z`；提供 `"UTC"` 时通过，`producer_tz=None` 时因虚拟 +2 小时探针跨日而拒绝。这里没有 DST，也没有错误归桶。

   这是明确的保守拒绝取舍；若按作者所述，现役末档宿主正常产出 `display_tz:null`，它们也承受该损失。本次仅确认 gate 拒绝，未推断范围外的页面或重建行为。

**LOW**

- **候选窗证明写错上界，且没有覆盖新增规则的实际取值域。**  
  [local_tz.py:223](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:223)，backend 对应 `:222`。注释上界多写一个 `365 天`，该松界不能推出 `y−2`；解析 `AAA999:99:99BBB-999:99:99` 还会生成约 **83.43 天**的 end `secs`，不满足“切换时刻均小于 42 天”。默认规则应单独用 `e=日期零点+3600−std_off` 证明；修正证明后窗口仍足够。

- **负 `secs` 的阈值写反。**  
  [local_tz.py:167](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:167)，backend `:166`。`3600+Δ<0` 要求 **`Δ<−1h`**，不是 `<+1h`；代入 `Δ=0` 即可反证。

- **“既有 11 串规则都落在名义年内”仍不实。**  
  [test_g6_9c_single_tz_source.py:487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:487)。既有 `WART4WARST,J1/0,J365/25` 的 end(2024) 是当地 **2025-01-01 01:00**；它没有暴露漏窗，不能解释为它不滚年。

- **固定偏移投影“必须放行”的旧注释未同步。**  
  [同测试:1016](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:1016) 仍如此声明，但 `:1036` 正在断言同一 Bogota 23:30 样本被拒；生产函数 `:562–563` 也保留了对应表述。

- **“每年 603 小时错日”应限定年份。**  
  [local_tz.py:129](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:129)，backend `:128`。逐小时复算 `CET-1CEST` 与 UTC 的日期差异：2026 为 603 小时，2024 为 **604 小时**。此外，两副本原有的默认 `02:02:00` 注释仍残留，属于 BASE 已有问题。

其余问题的核对结果：

- **Q1：窗口通过，原界表述需修正。** 显式 `999:99:99` 为 `41.6948958` 天；省略 DST 偏移时还会自动加一小时，最大达 `41.7365625` 天，所以严格的 `≤41.7` 不成立，`<42` 成立。独立扩大候选窗至 `y−5…y+4` 未发现增量；显式规则和默认规则分别证明后，`y−2…y+1` 足够。
- **Q2：公式在“秋季切换钉于当地标准时 01:00”的前提下正确，负秒算术也正确。** 代码明确声明 2007..2037，未把区间外写成已对齐；本机 2038 年失去 DST 的差异也已复现。但该分支不读取宿主 `posixrules`、不检测平台：文件缺席或宿主默认规则不同，仍使用这套美式规则。跨平台一致性本次未实测，不能背书。
- **Q3：端点充分性成立。** 日期随偏移递增，按 `<参照日／同日／>参照日` 三态依次变化；两端同态而内部异态的反例不存在。漏洞在区间宽度。
- **Q4：同源核验通过。** docstring 后字节 SHA256 相同，为 `510d44c6814793e3c278a6c401caa54cc52deaa648a5c48ff97355d4c76e5383`。本卡没有新增七名单之外的解析器定义；修改均被源码门覆盖。
- **Q5：新样本有效。** 两副本门⑦共 **308 个对照点**全部通过；删 `y−2` 能击中跨年样本，两个区分性闰年变异分别只击中对应探针。四个非 +1h 秋季扫描能击杀固定 7200 的变异，正控保持通过。年份约束明确写在测试 `:365–369`。

历史七段负控的 trap、前后 hash、原始失败消息，以及 pyright／ruff／64 条基线差异，**本次未核验**。新增错误桶测试 `:1126` 接受任意 `ValueError`，其通过本身不能证明具体拒因；上述内存复算也不等同于完整 pytest 或端到端验收。


