# 独立复核请求 — CARD-G6-9a 时区 / 午夜 / 唤醒补跑边界矩阵

## 一 背景与最小读取面

本仓是一个本地学习系统。每日复习清单由两条路径生成：
- **launchd 定时任务**（宿主 macOS，12 个档位）跑 `scripts/daily_review_run.py`
- **Web refresh 端点**（后端容器）跑同一个生产器 `scripts/daily_review_pick.py`

本卡是一张**零产品代码的取证卡**：只新增一个测试文件，把此前只存在于注释与口头
预期里的边界写成可执行的门。发现真缺陷的处置是「如实红 + 登记不修」。

请只读以下文件/行段，不必通读全仓：

| 路径 | 读什么 |
|---|---|
| `backend/tests/regression/test_g6_9_boundary_matrix.py` | **全文**（本卡唯一新增，497 行，主要审查对象） |
| `scripts/daily_review_run.py` | `:40`（PUSH_WINDOW）、`:124-183`（ensure_payload）、`:202-262`（main）、`:262-276`（失败落账） |
| `scripts/daily_review_pick.py` | `:236-243`（_TZ_SHANGHAI）、`:1020-1024`（date / generated_at 落盘） |
| `backend/app/api/v1/endpoints/review_overview.py` | `:80-88`（_DISPLAY_TZ_NAME）、`:340-346`（_sh_day）、`:348-160 内的 :65-71`（_gate_buckets 参照时钟）、`:1273`、`:1291-1305`（TZ 强制的说明与实测）、`:1317`（env["TZ"] 赋值） |
| `scripts/launchd/daily-review-wrapper.sh` / `com.canvas.daily-review.plist` | 环境变量设置面 |
| `_bmad-output/审查/evidence-g69/` | 本卡全部裁判输出 |

## 二 作者自述（请独立核对，不要采信）

1. **两套时钟**：`daily_review_run.py:215-216` 的 `local = now.astimezone(); today =
   local.date().isoformat()` 走**机器本地时区**，它驱动 `last_generate_date` /
   `last_push_accepted_date` / `board_last_recommended` 的值；而显示侧恒按
   `Asia/Shanghai` 归日。测试用 `TZ` 环境变量 + `time.tzset()` 真的改变了 runner 看到的
   本地时区（有独立用例 `test_tz_fixture_actually_moves_the_local_clock` 证明这一点，
   断言四个时区给出四个不同 UTC 偏移，且夏令时时区在 7 月落在夏令时那一档）。

2. **矩阵结果**：4 时区 × 4 瞬间 = 16 组合，实测 **8 组分叉**，用
   `xfail(strict=True)` 逐条登记，`KNOWN_DIVERGENT` 是**硬编码字面量**（不是由被测公式
   现算的），且用例内额外断言"登记表的值与实测逐字相符"。

3. **本卡的核心发现**（`test_launchd_path_does_not_force_display_tz`）：两条写路径对
   时区的处置是**非对称**的——web refresh 路径在 `review_overview.py:1317` 强制
   `env["TZ"] = _DISPLAY_TZ_NAME`（注释 `:1291-1305` 写明"不接受透传"并附实测），
   而 launchd 路径的 wrapper 只 export PATH/HOME/LANG、plist 的 `EnvironmentVariables`
   只有 PATH，**没有任何一处钉住 TZ**。宿主时区一旦变，runner 会静默产出错日期。

4. **午夜跨界**：用真实 `picker.build_payload` 在上海 23:59 与次日 00:01 各生成一次，
   跑 `_gate_buckets` 的完整调用链（`_gate_due_groups` / `_gate_upcoming` /
   `_gate_boards_rollup` 三个 helper 都只 import 调用），断言那颗"上海 8/1 00:30 到期"的
   节点从 `future` 桶翻到 `due_today` 桶。两次门禁都放行。

5. **唤醒补跑**三条串成一个叙事：08:00（窗口外）只落盘不推 → 同日 10:00 走缓存且
   `generated_at` 与文件 mtime 都不变、补上那次推送 → 次日 10:00 重新生成。
   **不 monkeypatch PUSH_WINDOW**（窗口判定正是被测物）。

6. **Bark 失败**：替身 `send` 返回 1，在**替身内部当场检查**投影文件是否已存在
   （那一刻就是"推送发生时"），断言 `last_error == "bark-send"` /
   `last_result == "generated_push_failed"` / 不落 accepted 日期。

7. **登记（不修）**：推送失败在 Web UI 与 `/overview` JSON 均不可见——`backend/app`
   对 runner 的四个 state 专属键零引用。该断言的匹配面**收窄过两次**：初版用裸
   `last_error` 命中了三个同名局部变量；二版用 `daily-review.` 命中了一句说"**不碰**
   state 文件"的注释。现在只认 runner 专属键，并配一条"这些键在 runner 里必须存在"的
   验伪锚 + 一条正面佐证断言。

8. **零产品代码**：`git diff --stat BASE HEAD -- backend/app backend/lib scripts
   canvas-vault` = 0 行；live vault 两个产物 sha 跑测试前后逐字节相同；live vault 内
   近 2 小时零新增 `__pycache__`。**未触发任何 launchd 档位**（只 `launchctl list` 与读日志）。

## 三 请按重要性排序回答的问题

1. **TZ 用例是否真改变了 runner 看到的本地时区**，还是只改了传进去的参数？
   `machine_tz` 夹具的 teardown 是否在任何失败路径下都能还原（它会污染同进程后续用例）？
2. **补跑用例②是否证明了「只补推送不重生成」**，还是只证明了「没崩」？
   `generated_at` 不变 + mtime 不变这两条，合起来是否足以排除"重新生成出了字节相同的
   文件"？`ensure_payload` 的三道缓存门（sha / next_due_utc / 节点池 mtime）里，
   有没有哪一道其实是本用例走绿的真正原因，而不是我以为的那道？
3. **Bark 注入是否真绑定 `:258-259` 那两条落账**，落盘顺序断言是否承重？
   在替身内部检查文件存在性，会不会因为 `ensure_payload` 总是先跑而**恒真**——
   即这条断言有没有可能永远不会红？
4. **零产品代码断言是否覆盖 `backend/lib` 与 `scripts`**？有没有哪条路径能让测试
   写到这两处而判据看不见？
5. **8 条 xfail 的定性是否与断言消息一致**？`KNOWN_DIVERGENT` 的字面值与实测是否
   真的逐条相符？`strict=True` 在这里是否用对了（它应当在有人统一两套时钟后报红）？
6. `test_launchd_path_does_not_force_display_tz` 与
   `test_push_failure_is_invisible_to_backend_app` 这两条"断言缺失"型的门，
   会不会因为**读错文件 / 关键词过期**而恒绿？它们各自的验伪锚够不够？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级列出发现，每条给出：一句话结论、文件与行号、
你据以判断的事实（读到的哪一行代码或哪一行证据）、建议处置。
若某条无法从给定读取面判断，请明说「读取面不足」，不要推测。最后给一句整体结论。

## 五 边界与已裁决事项

以下**不在**本次审查范围（已裁决，不必提出）：
- 不改任何产品代码：发现的时钟分叉一律登记移交，本卡不修
- 不做「推送失败」的 UI 徽标（移交 CARD-G6-9b，本批不排）
- 不触发真实 launchd 档位（只读 `launchctl list` 与日志文件）
- 不覆盖非 macOS 平台；不做万节点规模
- TZ 矩阵全绿也只证明「本机 tzdata 下这 4 个时区、这 4 个瞬间」

请**不要**在回答中给出任何用于绕开时区校验或触发定时任务的具体操作步骤；
本次需要的是「判据是否承重、结论是否被证据支撑」的评估。
