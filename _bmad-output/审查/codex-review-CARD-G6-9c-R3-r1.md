> 批次: BATCH-2026-09-18-第十五批 · 车道 P5 · 卡 CARD-G6-9c-R3 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-R3-r1.md)"`
> 审查绑定: `967cf4cf78ef68164d64d2ab8bc87995de417d4b`（= 本卡最终 HEAD；`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 应为空）
> 会话头自证（抄 stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行，括注行号；stderr 不入库）:
> `(L4) OpenAI Codex v0.153.3` / `(L7) model: gpt-6-astra` / `(L11) reasoning effort: ultra`

---

**本轮：BLOCKER 0、HIGH 2、MEDIUM 1、LOW 2，尚未达到末轮 B/H=0 条件。**

> 批次：BATCH-2026-09-18-第十五批 / CARD-G6-9c-R3 · round-1  
> 审查绑定：`967cf4cf78ef68164d64d2ab8bc87995de417d4b`  
> 当前 HEAD：`69dbcc62…`；结束时排除 `_bmad-output` 的代码 diff 为空、rc=0。全程未修改文件、未连接数据库。

以下解析器问题在两份副本中均存在。

1. **HIGH — dst 引用名仍能退回裸名解析，造成归日错误。**  
   [scripts/local_tz.py:140](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/scripts/local_tz.py:140)、`:429`。

   **未被拦下的输入**：`TZ="A1<B>>2"`。引用分支在第一个 `>` 结束后匹配失败，裸名分支重新接受 `<B>>`，后续检查只要求名字以 `>` 结尾。

   四元组为「墙钟、偏移秒、DST、名称」：

   | UTC 时刻 | libc | 本实现 |
   |---|---|---|
   | 2026-01-15 00:30Z | `01-15 00:30, 0, 0, UTC` | `01-14 23:30, -3600, 0, A` |
   | 2026-07-15 01:30Z | `07-15 01:30, 0, 0, UTC` | `07-14 23:30, -7200, 1, B>` |

   **对照输入**：`A1<B>2`，双方结果一致。`A1<B>C>2`、`A1<B><C>2` 同样存在上述问题。独立组合对拍覆盖 3,888 个规格、23,328 个时刻，900 个规格的 5,040 点不同，均落在这三类 dst 名。

   R2 已存在此问题；原 H1 输入通过，不代表引用名这一类全部完成修复。最小修正方向是禁止 dst 裸名分支接受 `<` 开头。

2. **HIGH — 撤掉占有量词后，数字字段之间重新出现平方回溯。**  
   [scripts/local_tz.py:139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/scripts/local_tz.py:139)、`:140–141`；[计时门:2377](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/backend/tests/regression/test_g6_9c_single_tz_source.py:2377)。

   **负控输入**：`parse_posix_tz("A" + "1"*n + "+")`。Python 3.14.4、min-of-5：

   | n | 耗时 |
   |---:|---:|
   | 202 | 0.001562 s |
   | 404 | 0.006347 s |
   | 808 | 0.025023 s |
   | 1616 | 0.097640 s |
   | 3232 | 0.401579 s |

   翻倍约增长四倍；R2 在 n=3232 仅约 **0.0000156 s**。主审再次执行也得到 **0.49 s**。

   `std_off` 必填只消除了名字之间的分割；空 dst 名仍允许 `std_off` 与 `dst_off` 瓜分同一数字串。这是现有两个名字样本的**门未覆盖的路径**。需要消除数字字段之间的分割，并把此族加入计时门。

3. **MEDIUM — H4 新增入口只检查“不抛”，合法输入返回 None 仍通过。**  
   [test_g6_9c_single_tz_source.py:2430](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/backend/tests/regression/test_g6_9c_single_tz_source.py:2430)。

   **负控输入**：仅在内存中让⑤对长度超过 4300 的切换小时字段返回 `None`，然后运行原 H4 用例。

   `"AAA1,M3.2.0/" + "0"*4300 + "2,M11.1.0"` 的 libc 冬夏偏移为 `[-3600, 0]`，原件一致，内存改写版本返回 `None`，但两个副本参数的原用例均通过。

   最小加固：两个额外入口都断言返回非 None，并比较对应偏移。

4. **LOW — 三段负控说明与实际失败位置不符。**  
   [test_local_tz_negctl_r3.py:436](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/backend/tests/regression/test_local_tz_negctl_r3.py:436)、`:457`、`:464`。

   **负控输入**：执行当前 H4ZERO、KEYUTF8、HMAX。实际分别是“合法长串返回 None”“解析期编码异常”“`isoformat()` 异常”，并非说明中的 `int()`、响应序列化、`utcoffset()` 异常。oracle 本身覆盖这些实际结果，问题在说明。

5. **LOW — picker 测试说明仍残留旧状态模型。**  
   [test_g6_9c_single_tz_source.py:2600](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/backend/tests/regression/test_g6_9c_single_tz_source.py:2600)、[test_daily_review_pick.py:45](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/backend/tests/regression/test_daily_review_pick.py:45)。

   **对照输入**：检查实际 import 位置与现取函数。持有旧 picker 实例的是测试模块；runner 在函数内 import 后取得新实例，说明把方向写反了。另有夹具说明仍称时区在 import 时固化、setenv 无效。普通 import 的修复本身正确。

**对其余问题的直接回答：**

- **⓪ 接受域与 R2 等价性：**见 HIGH-1。无 `std_off` 的两条路径也不能声称对所有输入返回等价：  
  `"<A><B>1:" + "0"*4300 + "2"` 在 R2 匹配成功，但⑤先抛 `ValueError`，根本未到⑥；R3 不匹配、返回 None；libc 冬夏 UTC。这属于 R3 的改善。普通有限样本支持等价，不能推广成全域结论。

- **① 计时门：**更正四倍长度比成立。把 `std_off` 改回可选后，现有样本 n=3232 约 **0.51–0.54 s**，门确实变红；但不能覆盖 HIGH-2 的数字字段路径。

- **② AST 预检：**指纹相同就被 `:496` 拒绝，注释、docstring、冗余括号、等值数字写法等不能混过。反方向不成立：AST 不同仍可能行为相同，因此后续 oracle 必不可少。

- **③ 断言身份：**当前九段没有发现红在无关对照输入上的情况。实际失败位置如下，均属于相应性质：

  | 段 | 失败行 |
  |---|---:|
  | COLONPOSIX / H1BARE / H2COLON | 158 / 170 / 194 |
  | H3QUANT / H4ZERO | 236 / 265 |
  | ASCII / RULEA | 285 / 305 |
  | KEYUTF8 / HMAX | 331 / 375 |

  可以添加 `expect_msg` 锁定位置；H4ZERO 应锁“长串被拒”，不能锁不存在的 `ValueError`。

- **④ picker 夹具与状态：**1048 个 tracked Python 文件按指定 AST 三态扫描，`_DISPLAY_TZ=0`、`_display_tz=53`。唯一语法解析失败文件不含这两个名字。6 处 `monkeypatch.setattr` 均无 `raising=False`；5 组直接赋值都先读取旧属性，因此名字缺失也会先报错。向五组 `try` 内加入异常后，**5/5 均恢复原函数对象**。绑定版本已无真实名重复加载辅助，现取用例前后 picker 模块对象相同。仍留有两个独立辅助模块键和 `sys.path` 插入，但未发现使其他夹具失效的实际路径；本次没有重跑目录级 pytest 或 xdist 顺序扰动。

- **⑤ UTF-8：**`CANVAS_TZ`、TZ 的 ZoneInfo 分支、`/etc/localtime` 分支确实不经过解析器的严格编码检查，是**门未覆盖的路径**。本机真实测试中，带代理字符的 CANVAS_TZ 均抛包装后的 `ValueError`，没有返回非法 key；当前 localtime 返回合法的 `Asia/Hong_Kong`。没有证据将其列为实际 HIGH。

- **⑥ pyright：**生产 `backend/app` **零新增 ignore** 成立。整个代码面则新增两处测试 import ignore，其中一处来自移植，一处位于新增现取门 `:2611`；它们不影响 `pyright app` 的计数。本次 pyright 因 Node 缺少 `libllhttp.9.3.dylib` 未能启动，**没有独立重现 0 errors**。

- **⑦ 类型收窄：**保留测试辅助中的检查作为静态收窄可以成立，与生产行为校验职责不同。但当前分支不可达，不能算行为防线；“生产侧没有这个需求”的说明依据不足，两侧都把 `groupdict()` 值传给同一函数。

另外，移植的四个独有文件确与 `a8cefab4` 逐字节一致；`review_overview` 指定区域一致，其他差异位于该区域之外。两份时区副本仅模块 docstring 不同，真实 3.9.6／3.14.4 均加载成功；独立的 **299,593 串**在两解释器上匹配数均为 **40,864**，匹配分组指纹相同。原四组指定输入移植后通过属实，但 H1 尚有遗漏，H4 扩展入口也确实包含本卡新增修复。

COLONPOSIX 的冗余仅对 `display_tz()` 完整调用成立：单拆正则层，直接调用 `parse_posix_tz(":AAA-1")` 已改变结果。ASCII／RULEA 的第二层作用已独立确认。

**trap 与 SHA 的证明范围：**现有存档只证明那次 pytest 非零退出后内容恢复，不能证明 Python 脚本异常、trap 自身失败等所有退出路径。前后 SHA 相同只能证明两个采样时点内容相同，不能证明中途未修改；绑定验收单也已明确登记此限制。固定时区下 picker 计算表达式保持一致，但本次未进行完整 CLI 产出的逐字节对拍。


