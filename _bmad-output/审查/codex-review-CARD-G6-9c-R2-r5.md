> 批次: BATCH-2026-09-11-第十四批 · 车道 T3（`card-t3-review`）· 卡 CARD-G6-9c-R2 round-5（轮次上限）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`--version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-R2-r5.md)"`
> 审查绑定: `08100483 → ebe0db58`（送审时 HEAD = `ebe0db58`；⚠️ 本轮审后按其意见又改了代码至 `a7e11469` ⇒ **不绑最终 HEAD**，且轮次已达上限 5，按 D-15 车道不能自判通过，整改交主 session 裁定是否再送一轮）
> 会话头自证（抄 `.stderr` 中含版本 / model / reasoning 的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（L2） / `model: gpt-6-astra`（L5） / `reasoning effort: ultra`（L9）

---

**结论：本卡新增 1 HIGH、1 MEDIUM、3 LOW。本轮不通过；已达第 5 轮上限，应停下车道，交主 session 人审。**

绑定 `08100483 → ebe0db585a47b2bad6c37dad67d833cbd8bc3107`。审查结束时六个范围内文件仍与该 HEAD 一致，全程只读、无网络或数据库连接。

**BLOCKER：无。**

**HIGH：1 条。**

- **H1【本卡新增】UTF-8 长度检查引入未捕获的编码异常。**  
  位置：[display_tz.py:189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/core/display_tz.py:189)、[local_tz.py:190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:190)。  
  复现：清除 `CANVAS_TZ`，设置 `os.environb[b"TZ"] = b"AAA0<\xff>"`，调用真实 `display_tz()`。Python 将该字节读为 `\udcff`，严格 `.encode("utf-8")` 抛 `UnicodeEncodeError`；**BASE 正常返回 UTC，HEAD 两副本均抛异常**。标准侧 `b"<\xff>0BBB"` 同样。本机 libc 接受这些字节并正常换算。  
  [review_overview.py:122](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/api/v1/endpoints/review_overview.py:122) 的模块启动校验直接调用该函数，因此具有启动失败影响；这是实际环境变量可达的新增异常。

**MEDIUM：1 条。**

- **M1【本卡新增】省略规则分支接受引用名中的 NUL。**  
  位置：[display_tz.py:181](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/core/display_tz.py:181)、[local_tz.py:182](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:182)。  
  复现：JSON 自报 `display_tz="AAA0<B\u0000BB>"`，搭配五个空桶、零统计及 `generated_at="2026-07-01T23:30:00+01:00"`；内存执行实际 `_gate_buckets`，**BASE 拒绝不可解析时区，HEAD 完整通过**。  
  NUL 无法作为完整 POSIX 环境字符串传递，所以这是新增的语法接受缺口，**不能称作“同一完整串被 libc 拒收”**；与既有换名搬桶重合的影响不重复计 HIGH。

**LOW：3 条。**

- **L1【本卡新增】候选年测试没有守住新增的南半球上界检查。**  
  位置：[test_g6_9c_single_tz_source.py:598](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:598)。  
  复现：仅在内存把 `elif year < 9999:` 改成 `else:`，整条候选年测试仍通过，因为唯一规格走北半球分支。当前生产守卫有效，但这条回归门不能发现南支守卫被删除。

- **L2【本卡新增】LOW-2 的机制说明仍不准确。**  
  位置：[test_g6_9c_single_tz_source.py:500](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:500)。  
  复现：`AAA1BBB0,365/3,365/2`、`Y=2024` 的季度为 `2024-12-31T04Z → 2026-01-01T02Z`。两个端点的位移没有相加，季度也没有“整体推到 Y+2”。准确机制是：**南支终点取 `e(Y+1)`，该端点可滚入 `Y+2`，因此覆盖 y 年初的季度可能来自名义年 y−2。**

- **L3【本卡新增】测试注释仍有与行为不符的总括。**  
  位置：[test_g6_9c_single_tz_source.py:594](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:594)、[同文件:625](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:625)。  
  “本门只保证不抛”已与新增的 `+01:00` 断言矛盾；十八拒例总括中的“退 UTC，与 C 库一致”也不成立。复现 `AAA12BBB-12`、`2026-07-01T23:30Z`：libc 给 `07-02 11:30 +12h`，BASE／HEAD 都退 UTC、归 `07-01`。**这里新增的是错误说明，运行支持缺口属于既有。**

其余问题的核对结果：

- **关于 C 库拒收而 HEAD 接受：**本轮对 13,035 个有效 UTF-8 候选串抽样，5,688 个被 HEAD 接受，每个比较六个时刻，未发现此方向的反例。这不是全输入空间证明。H1 属于“libc 接受、HEAD 抛异常”；M1 属于无法完整传入 C 环境的输入。
- **关于候选年边界：**两个守卫把 `_dst_window` 参数限制在 `1..9999`，两副本各 9,216 次边界探针无异常；北支 `9999-07-01T23:30Z` 恢复为 `+01:00`。但不能宣称所有边界换算正确：南支在公元 1 年初、9999 年末仍可能漏季度；**BASE 同点原本抛 year 0／10000，属既有范围支持缺口，不计新增**。
- **关于用例独立性：**所列防线都有独立承重用例，但不是严格“一层恰好一条”，存在合理冗余：

| 防线 | 独立用例 |
|---|---|
| std／dst 单侧 | `AAA24BBB23`／`AAA23BBB24` |
| 差值／差值 abs | `AAA12BBB-12`／`AAA-12BBB12` |
| 标准偏移必填 | `<AAA><BBB>` |
| 换行 | `AAA0<BBB>\n` |
| ASCII／分钟／秒 | `AAA１BBB`／`AAA0:60BBB`／`AAA0:0:61BBB` |
| 字节长度 | 两条 176 字符、516 字节引用名串 |

十八拒例、三正例及上述独立变异均已在内存复验。完整十七段负控未重跑；最新日志的完成标记与三份生产文件 SHA256 均吻合。

**你的既有清单归因仍成立，但需补两类：**南半球极值年份的范围支持缺口；以及 libc 接受、但受 Python 单侧偏移或 DST 差值必须小于 24 小时限制而被拒的省略规则串。第 4 项中的“退 UTC”仍可能导致错日，只是 BASE 同样如此。


