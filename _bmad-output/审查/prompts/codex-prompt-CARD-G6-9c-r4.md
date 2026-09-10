# 代码审查请求 — CARD-G6-9c round-4（对 round-3 整改的复核）

## 一 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime`

round-3 你审 `d858c357 → b1e58489`，判定两条 HIGH 仍未解决：
HIGH-1 的 `_SystemLocalTZ` 未实现 `fromutc()`（南半球 DST 错日、时刻不守恒）；
HIGH-2 是缺陷位移（放行了 round-2 原本能拦住的错误投影）。
两条我都复现确认，本轮请复核重做后的形态。

审查绑定：`b1e58489 → 96d3013e`

**请读这些**：

1. `git diff b1e58489 96d3013e -- . ':(exclude)_bmad-output'` —— 本轮全部整改
2. `scripts/local_tz.py` 与 `backend/app/core/display_tz.py` 全文（`_SystemLocalTZ` 重写过）
3. `backend/tests/regression/test_g6_9c_single_tz_source.py` 全文（门 ⑦ 重写 + 新门 + 负控）
4. `backend/app/api/v1/endpoints/review_overview.py` 的 `_gate_buckets`（搜 "参照系 = 生产器"）
5. `scripts/daily_review_pick.py` 的 `build_payload` 顶层键区（搜 "display_tz"）
6. `_bmad-output/审查/codex-review-CARD-G6-9c-r3.md` —— 你 round-3 的原文

## 二 整改自述（请独立核对，不要采信）

**HIGH-1**：`_SystemLocalTZ` 现在自实现
- `fromutc(dt)`：`calendar.timegm(dt.timetuple())` 得 epoch 秒 → `time.localtime(ts)`
  （C 库 UTC→本地正解，DST 与历史规则一并带上）；折叠时段检测「往前推一个
  `_dst_gap()` 还得到相同墙钟」⇒ 标 `fold=1`。
- `utcoffset(dt)`：`time.mktime(墙钟)` 反推偏移；`dt.fold=1` 且「往后推一个 gap
  仍是同一墙钟」时 `stamp += gap`（`mktime` 对折叠墙钟只返回较早那个）。
- 不缓存 `time.timezone`/`time.altzone`。
复验：10 个时区（含 Lord_Howe 30 分钟 DST、Chatham、Santiago 南半球、上海历史夏令时）
× 11 个时刻（含南北半球折叠两侧、空缺边缘）= 110 组，墙钟与 C 库全一致、
时刻守恒全通过。

**HIGH-2**：改为**生产器自报**。
- `build_payload` 加性顶层键 `display_tz`：`getattr(_DISPLAY_TZ, "key", None)`
  （它归日用的时区 IANA 名；末档无名时区为 null）。
- `_gate_buckets(..., producer_tz=payload.get("display_tz"))`：自报值必须是可解析的
  时区名，且与 `generated_at` 的偏移**自洽**（否则 payload 自相矛盾，拒收）；
  缺席（旧投影）退回此刻显示时区（那会误判 corrupt 但不会放行错误归桶）。
- 该校验放在外层 try **之外**，拒因不被重包。
四正例（春季前跳 / 秋季回拨 / Bogota→NY 同偏移不同规则 / 切时区）+
四负控（错误桶必拒、伪造 display_tz 两种必拒、旧投影必放行）全对。

**送审前的自查（这是本轮的额外内容）**：我先用 5 个独立视角的 workflow 做了对抗性
预审（如实登记：12 个 agent 里 11 个因会话限额失败，只有 test-strength 跑完）。
对它指出的问题我**逐条自验**，发现 **4 个存活变异** —— round-3 写的门没有一条
锁住 round-3 的整改：
- 删掉整个 `_SystemLocalTZ` 类：对照门只比 `display_tz` 函数体，且 scripts 副本的
  POSIX 分支从未被任何测试执行 ⇒ 存活；
- 删掉自定义 `fromutc`：探针时刻全在 DST 折叠窗口之外 ⇒ 存活；
- 删掉 fold 处理：判据只比墙钟而 `datetime.__eq__` 忽略 fold ⇒ 存活；
- 断开生产接线 `producer_tz=payload.get(...)`：门 ⑧/⑨/负控三处自己复刻了那行 ⇒ 存活。

补门后全部击杀：
- 对照门扩到比 `_SystemLocalTZ` **类体** + 先查**存在性**（`getsource` 抛
  `AttributeError` 时 traceback 不带可辨认身份）；
- 门 ⑦ 参数化到**两份副本**（backend + scripts），探针时刻加到 8 个（含折叠两侧、
  空缺边缘、南半球），判据加**时刻守恒**（换算结果转回 UTC 必须等于原时刻）；
- 门 ⑧/⑨/负控改走 **`_summarize`**（`_gate_buckets` 的唯一生产调用方，接线在它内部）。

变异负控从 9 条扩到 **16 条**（M1-M16），全部 KILLED、各绑不同失败身份、还原逐字节相同。
其中 M8 一度**假杀**（变异体用 `timezone(timedelta(...))`，而本卡已删掉未使用的
`timedelta` import ⇒ 变异体自己 NameError），改用文件里恒在的 `datetime` 后才是真击杀。

## 三 请回答的问题（按重要性排序）

1. `_SystemLocalTZ` 的 `fromutc`/`utcoffset`/`dst`/`_dst_gap` 是否正确？
   重点：`_dst_gap()` 用 `time.timezone - time.altzone`（该时区**当前**的 DST 跨度）——
   对历史 DST 跨度不同的年代（或 DST 跨度非整小时的时区），fold 判定会怎样错？
   后果落在哪条判据上？
2. `producer_tz` 自洽校验「只比偏移相等」还有什么伪造能通过？比如真实生产时区是
   同偏移**同规则**的另一个时区（Asia/Shanghai vs Asia/Macau），门用了哪个规则、
   有实际差异吗？
3. payload 顶层新增 `display_tz` 的**所有消费方**都安全吗（daily_review_run /
   send_bark / review_overview / review_app 的 JS / vault_lint）？旧消费方读到陌生键
   会怎样？
4. 16 条变异的门是否真的各自承重？特别是 M10-M16（本轮新补的）——有没有哪条
   变异的红其实来自「别的断言先失败」而不是它指定的那条身份？
5. 门 ⑦ 的 10 个参数格（5 TZ × 2 副本）× 8 时刻里，有没有恒真格？
   `test_posix_probe_actually_differs_from_etc_localtime` 的前提断言是聚合口径
   （至少一个 TZ 有区分力），部分参数在某些宿主上会静默退化吗？
6. 门 ⑧/⑨/负控改走 `_summarize` 之后，有没有把 `_summarize` 自身的其他检查
   （schema_version、容器形状等）意外卷进来，让「桶位参照系」的失败与其他失败
   混在一棵树里？
7. 整改整体上有没有引入新的 BLOCKER / HIGH？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 四级，每条给出 `file:line` 与一句话说明为什么它是那个级别。
没有问题的级别写「无」。请不要复述我的自述，只写你独立查证后的结论。
若某条 round-3 的问题在你看来仍未真正解决，请明确指出并保持原级别。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接数据库或任何网络服务。
- `recap_exam_build.py` / `inbox_preview.py` / `scripts/launchd/*` 本卡零改动，不在审查范围。
