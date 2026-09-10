> 批次: BATCH-2026-09-07-第十三批 · 车道 card-u6-reviewtime · 卡 CARD-G6-9c round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（/opt/homebrew/bin/codex）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-r5.md)"`
> 审查绑定: `96d3013e → 129c14fa`（送审时 HEAD = 129c14fa；审后代码树零改动，`git diff --stat 129c14fa HEAD -- . ':(exclude)_bmad-output'` 为空 ⇒ **仍绑最终 HEAD**）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

已核实 `96d3013e → 129c14fa`，五个受审文件与目标提交逐字节一致。**两条 HIGH 仍未关闭，另发现一条新增 HIGH。** round-4 的纽约折叠、Lord Howe 1985、上海 1991 三个具体反例已修复。

**BLOCKER：无。**

**HIGH**

1. **HIGH-1 未关闭：跨年季度仍会漏格，直接算错日期。** [local_tz.py:176](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/local_tz.py:176)、[display_tz.py:175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/core/display_tz.py:175)：只检查名义年份 `y−1/y/y+1`，遗漏结束规则已经滚入当前年的更早季度，保持 **HIGH**。

   两份副本均独立复现：

   ```text
   TZ：AAA1BBB0,365/3,365/2
   UTC：2024-01-01T00:30:00Z
   实际：2023-12-31T23:30:00−01:00，fold=1
   正确：2024-01-01T00:30:00+00:00
   ```

   非闰年的裸 `365` 落到次年元旦；正确窗口是 `start(2022)=2023-01-01T04:00Z → end(2023)=2024-01-01T02:00Z`，当前循环漏掉了名义 2022 年。**此例转回 UTC 仍然守恒。** `/167` 滚年也能触发同类错日。

2. **HIGH-2 未关闭：固定偏移回退仍然放行错误桶。** [review_overview.py:541](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:541)：已登记的误拒存在完全对称的错误放行，不能降级为只有兼容性损失，保持 **HIGH**。

   真实 `_summarize` 复现：纽约生产，`generated_at=2026-03-08T00:30:00−05:00`，到期 `2026-03-09T04:30:00Z`，正确桶是 `future`。

   | `display_tz` | 正确 `future` | 错误 `due_today` |
   |---|---|---|
   | `America/New_York` | 放行 | 拒绝 |
   | 缺失 | **拒绝** | **放行** |
   | `null` | **拒绝** | **放行** |

   `12`、`{}`、空串现在确实拒收，Bogota 正例也已修复，但整条 HIGH 未关闭。`:540` 的“不会放行错误归桶”不成立。

   此外，[review_overview.py:1037](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:1037) 只返回 `corrupt`；[review_app.py:629](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_app.py:629) 的重建由手动按钮触发。**未发现页面自动重生成自愈的实现。**

3. **新增 HIGH：合法的省略切换规则写法被静默改成 UTC。** [local_tz.py:133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/local_tz.py:133)、[display_tz.py:132](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/core/display_tz.py:132)：`dst` 存在而规则省略并非语法非法，本机 libc 使用默认规则，代码却整体退回 UTC，常见配置可以直接错日，判 **HIGH**。

   ```text
   TZ=CET-1CEST
   UTC=2026-07-31T22:30Z
   两副本：2026-07-31 22:30+00:00
   libc：  2026-08-01 00:30+02:00
   ```

   [本机 tzset(3)](/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/share/man/man3/tzset.3:273) 明确说明省略规则时使用 `posixrules`；“更早的 ZoneInfo 档已经覆盖”并不成立。

**MEDIUM**

- **解析器仍未实现声称的合法域。** [local_tz.py:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/local_tz.py:46)、[display_tz.py:45](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/core/display_tz.py:45)：偏移和时刻只做数字累加、引用名过宽、匹配允许尾换行，会接受非法规格甚至返回 Python 无法使用的时区，判 **MEDIUM**。

  | 输入 | 已验证问题 |
  |---|---|
  | `ABC5:60` | 接受为 UTC−6；libc 退 UTC，能够错日 |
  | `ABC3DEF,M3.2.0/2:60,M11.1.0` | 非法分钟被接受 |
  | `ABC3DEF,M3.2.0/168,M11.1.0` | 超出所采用大时刻范围仍接受 |
  | `ABC`、`ABC3,M3.2.0,M11.1.0` | 分别接受缺必需标准偏移、无 DST 名却附规则 |
  | `<A>3`、`<A:B>3`、`<A B>3` | 引用名长度／字符域不符合严格 POSIX |
  | `ABC3\n`、`ABC٣` | 接受尾换行／非 ASCII 数字 |
  | `ABC+24:00` | 返回对象，但日期格式化会抛 `ValueError` |

  **`+24:00` 要区分两层限制：POSIX 小时字段允许 24，Python `tzinfo` 要求偏移严格小于 24 小时。** 默认 DST 偏移也需检查，例如 `ABC-23DEF,…` 会推导出不可表示的 `+24:00`。`/167:30` 本身已正确接受。

  拒绝 `AB3` 符合严格 POSIX 简名要求，可以作为明确的兼容性边界；但目前仍接受 `<A>` 和含冒号的 `<+10:30>`，并没有一致地执行这个取舍。

- **“全部共享定义”对照仍有缺口。** [test_g6_9c_single_tz_source.py:116](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:116)：遗漏 `_POSIX_TZ_RE` 和 `_POSIX_DEFAULT_TRANSITION`，单份副本可以发生真实语义漂移而相关门全绿，判 **MEDIUM**。仅把 scripts 缺省时刻减一秒，源码两门及全部 54 个纯参数格仍通过；`06:59:59Z` 已出现两副本相差一小时。仅缩短 scripts 正则的时刻小时长度，也能让 `/167:30` 一份接受、一份拒绝而全部通过。

- **round-4 回归覆盖不足仍在。** [测试文件:340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:340)：门⑦实际是 **11×2×8＝176 次换算**，没有自述的 `05:45Z/06:45Z`；全部时刻位于 2026 年，范围表又只验解析成功与否，无法锁住上述闰年／年界 HIGH，保持 **MEDIUM**。半小时规格也没有探入实际折叠窗口。

- **round-4 失败身份混杂仍在。** [测试文件:614](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:614)、同文件 `:715`：任意 `_summarize` 的 `ValueError` 仍被包装成参照系错误，单凭外层文案不能认证击杀身份，保持 **MEDIUM**；这不代表本次实际复放的 M5／M7／M16 是假杀。

- **原浏览器归日分歧未关闭。** [review_app.py:209](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_app.py:209)：`Intl.DateTimeFormat` 不接受 POSIX 规格串，随后退回浏览器时区，新 `.key` 没有解决原 null 分歧，保持 **MEDIUM**。实际 JS 验证中，纽约应显示“现在”的条目，在上海浏览器显示“明天”。

- **生产／消费偏移格式仍不一致，属于既存缺口。** [review_overview.py:134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:134)：合法 `ABC5:30:30`／`ABC15` 会产出 `−05:30:30`／`−15:00`，却被 `generated_at` 门拒绝，判 **MEDIUM**；已对照旧提交，不能称为本轮新增。

- **原“切区必 stale”问题仍在。** [review_overview.py:1052](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:1052)：仍只比较日期，同日切区不会触发 stale，保持 **MEDIUM**。

- **原跨进程配置差异仍在。** [app/__init__.py:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/__init__.py:16)、[vault_lint.py:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/scripts/vault_lint.py:95)：后端加载 `.env`、独立 CLI 不加载，同源函数不保证收到相同配置，保持 **MEDIUM**。

**LOW**

- **零 DST 偏移差时名称错误。** [local_tz.py:222](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/local_tz.py:222)、[display_tz.py:221](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/core/display_tz.py:221)：`AAA0BBB0,M3.2.0,M11.1.0` 在一月也返回 `BBB`，应为 `AAA`；不影响归日，判 **LOW**。
- **原门⑦单格承重限制仍在。** [测试文件:526](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:526)：整体有区分力不代表每格都能击杀某项缺陷，保持 **LOW**；M4 有 6 格存活，M6 有 14 格存活，**整个门并非恒真**。
- **原门⑥宿主依赖仍在。** [测试文件:847](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:847)：允许的无名固定偏移兜底仍会被“必须有 `.key`”拒绝，保持 **LOW**。

三项自查整改本身正确：默认 `02:00`、J/n 分开范围、fold 按偏移大小选侧。对相同墙钟 `W`，UTC 为 `W−offset`，所以较大偏移必然对应较早时刻；负 DST 和半小时跨度不会推翻这个结论。双候选算法未发现独立反例，本次错误来自其依赖的窗口判定。

同源重建仍只能证明自洽，不能认证真实来源。实测把自报规格从 `EST5EDT,M3.2.0,M11.1.0` 改成 `EST5EDT,M3.3.0,M11.1.0`，生成时偏移仍一致，同时改成错误 `due_today` 可以通过；这是 round-4 已说明的核验上限，不另重复计 HIGH。

按描述重建的变异结果如下，测试行号均指上述回归文件，M8 除外：

| 变异 | 独立确认的实际承重 |
|---|---|
| M1／M2 | `:93` 源码漂移／`:291` 求值固化 |
| M3 | 已验证产生 `.key=None`；**未复放原子进程测试** |
| M4／M6 | `:388` 墙钟断言，分别 16／8 格失败 |
| M5 | 纽约春秋两格，真实桶日期检查 |
| M7 | Bogota→纽约、上海→UTC，真实桶日期检查 |
| M8 | `test_vault_lint.py:700`，实际归日错误，无 NameError |
| M9 | `:786`，Tokyo 伪造实际放行 |
| M10／M11／M12 | `:127` 存在性／`:133` 源码一致性 |
| M13／M14／M15 | `:388` 墙钟／`:393` 时刻守恒 |
| M16 | **本轮为纽约春秋两格**，不能沿用 r4 的 Bogota／上海身份 |
| M17／M18 | `:423` 缺省切换点 |
| M19／M20／M21／M22 | `:467` 折叠／`:483` 空缺方向 |
| M23／M24 | `:430` 时刻守恒，各两格 |
| M25／M26 | `:523`，错误接受 J0 |

除 M3 上述限制外，重建变异均确认实际真杀；但仓内没有原始 harness 和完整 traceback，不能认证历史每条变异的逐字内容及匹配器。

本次未修改文件、未连接网络或数据库。动态验证使用原函数的内存执行；未运行需要落盘夹具的完整 pytest。


