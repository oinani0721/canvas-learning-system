# 代码审查请求 — CARD-G6-9c round-2（对 round-1 整改的复核）

## 一 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime`

round-1 你审的是 `da690bf8 → 0e8dc06e`，给出 BLOCKER 0 / HIGH 2 / MEDIUM 6 / LOW 4。
我逐条复现后做了整改，本轮请复核**整改本身**。

审查绑定：`0e8dc06e → d858c357`（整改 commit）

**请读这些**：

1. `git diff 0e8dc06e d858c357` —— 本轮全部整改
2. `git diff da690bf8 d858c357 -- . ':(exclude)_bmad-output'` —— 整张卡的最终代码面
3. `scripts/local_tz.py` 与 `backend/app/core/display_tz.py` 全文
4. `backend/tests/regression/test_g6_9c_single_tz_source.py` 全文（新增了门 ⑦ 与门 ⑧）
5. `_bmad-output/审查/codex-review-CARD-G6-9c.md` —— 你 round-1 的原文（供对照）

## 二 整改自述（请独立核对，不要采信）

**HIGH-1（POSIX TZ 串被忽略）**：我复现确认成立——上海宿主 + `TZ=UTC0` 时
`2026-07-31T16:30Z` 被算成 08-01，而 C 库本地是 07-31。
改法：`TZ` 存在但 `ZoneInfo` 拒绝时，回落到**进程本地**（`datetime.now().astimezone().tzinfo`），
不再往下读 `/etc/localtime`。补了门 ⑦（`test_posix_tz_string_resolves_to_process_local_not_etc_localtime`，
三个参数化值 + 一条正控 `test_valid_tz_names_still_win_over_process_local`）。

**HIGH-2（切时区后合法投影被判 corrupt）**：复现确认成立。
改法：`_gate_buckets` 的参照日改用 `generated_at` **自带的偏移**（`ref_tz = ref.tzinfo` / `ref_day = ref.date()`），
桶内每行也用同一个 `ref_tz` 换算（`_display_day(ts, ref_tz)`）。
理由：门的职责是校验「这份产出自不自洽」；「投影是不是今天的」由 `_vault_entry` 的 stale 判定负责，
那里仍用此刻的显示时区（切时区后投影变 stale ⇒ 触发重新生成，是正确行为）。
补了门 ⑧（`test_bucket_gate_uses_projection_own_tz_not_current_display_tz`）。

**MEDIUM（3 条已改）**：
- 源码对照门从 `ln.strip()` 改 `textwrap.dedent()` + `rstrip()`（保留相对缩进），
  docstring 也改了——它此前声称「只比函数体」，实际比的是 `inspect.getsource` 的整段。
- 矩阵的 `machine_tz` 与 `_real_runner_today` 都清掉 `CANVAS_TZ`，teardown 还原。
- lint 判别门的冻结时刻从 UTC `08-31 23:00` 换成 UTC `09-01 02:00`（NY 是前一天 22:00，
  UTC 日与 NY 日不同），并 `setenv TZ=Asia/Shanghai` + `tzset()` 钉住宿主。

**LOW（3 条已改）**：偏移显示支持半小时（`+05:30` 不再显示成 `UTC+5`，整小时输出与改前逐字相同）；
`vault_lint` 的无效时区转 `LintConfigError`（退出码 3 而非 1）；`_sh_local` 旧名改掉（实际 4 处）。

**登记不修**：JS 在服务端下发 `null` 时用浏览器本地（MEDIUM）；配置项在四个进程里没有统一入口（MEDIUM）；
门 ⑥「默认必须有名」依赖宿主能力（LOW）。三条都写进了验收单的「本卡未证明什么」。

我另做了 5 个变异负控，其中 M4 / M5 是把上面两条 HIGH 的修复**退回缺陷形态**，
用来验证新补的门是否承重；harness 判据是「指定的那道门 FAILED 且失败正文含指定断言串」，
变异后先 `ast.parse` 自检语法（不合法记 SYNTAX-INVALID，不算击杀），还原后逐文件核 sha。

## 三 请回答的问题（按重要性排序）

1. HIGH-1 的改法是否**真的**解决了问题，还是把缺陷挪了个位置？回落到进程本地之后，
   有没有新的形态会让「设了 TZ 却按别的时区算」重新出现？
2. HIGH-2 的改法是否让门变弱了？用 `generated_at` 自带偏移当参照系之后，
   哪些原本能被门抓住的坏投影现在会被放行？（尤其：生产器若把 `generated_at` 写成一个与它实际
   分桶所用时区不一致的值，门还能发现吗？）
3. 门 ⑦ 与门 ⑧ 是否承重？把对应的修复退回去（M4 / M5），它们是否**只**因为自己那条断言而红，
   而不是因为别的原因（导入失败、别的断言先红）？
4. `_display_day(ts, tz)` 新增的可选参数是否有被误用的面？它的默认分支仍走此刻的显示时区，
   而显示层与门层现在用的是两套参照系 —— 这个分工在代码里是否清晰、有没有哪个调用点站错了边？
5. 源码对照门改用 `dedent` 之后，还有哪些能改变语义但比较仍通过的写法？
6. 矩阵清掉 `CANVAS_TZ` 之后，`_real_runner_today` 启动的 runner 子进程会不会仍从别处继承到它？
7. lint 判别门换时刻并钉住宿主之后，它 docstring 里声称的三条变异是否**全部**可杀？
8. 偏移格式化的改动是否对整小时时区逐字节保持原样？有没有哪个既有断言依赖旧的取整行为？
9. `vault_lint` 把 `ValueError` 转成 `LintConfigError` 之后，是否吞掉了别的本该以退出码 1 结束的错误？
10. 整改整体上有没有引入新的 BLOCKER / HIGH？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 四级，每条给出 `file:line` 与一句话说明为什么它是那个级别。
没有问题的级别写「无」。请不要复述我的自述，只写你独立查证后的结论。
若 round-1 的某条问题在你看来**没有真正解决**，请明确指出并保持原级别。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接数据库或任何网络服务。
- `recap_exam_build.py` / `inbox_preview.py` / `scripts/launchd/*` 本卡零改动，不在审查范围。
