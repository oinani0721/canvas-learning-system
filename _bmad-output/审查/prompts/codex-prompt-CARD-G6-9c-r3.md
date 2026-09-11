# 代码审查请求 — CARD-G6-9c round-3（对 round-2 整改的复核）

## 一 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime`

round-2 你审 `0e8dc06e → d858c357`，判定**两条 HIGH 都没真正解决**：
HIGH-1 的「回落进程本地」拿的是此刻的固定偏移、丢了 DST 规则；
HIGH-2 的「用 generated_at 自带偏移当参照系」是缺陷位移，DST 边界误拒合法投影、
反过来还放行错误归桶的投影。两条我都复现确认，本轮请复核整改。

审查绑定：`d858c357 → b1e58489`

**请读这些**：

1. `git diff d858c357 b1e58489` —— 本轮全部整改
2. `scripts/local_tz.py` 与 `backend/app/core/display_tz.py` 全文（新增了 `_SystemLocalTZ`）
3. `backend/tests/regression/test_g6_9c_single_tz_source.py` 全文（门 ⑦ 重写、新增门 ⑨）
4. `backend/app/api/v1/endpoints/review_overview.py` 的 `_gate_buckets` 参照系那段
5. `backend/tests/unit/test_vault_lint.py` 的 `host_tz` fixture 与新增的接线证明门
6. `_bmad-output/审查/codex-review-CARD-G6-9c-r2.md` —— 你 round-2 的原文

## 二 整改自述（请独立核对，不要采信）

**HIGH-1**：新增 `_SystemLocalTZ(tzinfo)`，每次按**被换算的那个时刻**现问 C 库
（`time.mktime(...)` → `time.localtime(...).tm_isdst`），`utcoffset` / `dst` / `tzname` 都逐时刻算，
**不缓存** `time.timezone` / `time.altzone`（`tzset()` 之后它们会变，缓存等于把时区固化在 import 时刻）。
两份副本各有一份逐字相同的该类。复验 7 个 TZ 写法 × 3 个跨 DST 时刻，与 C 库无参 `astimezone()` 全部一致。

**HIGH-2**：参照系按**证据**择一 ——
此刻显示时区在 `generated_at` 那一刻的偏移与它自带的偏移**相同** ⇒ 用该时区的完整规则；
**不同** ⇒ 退回 `generated_at` 自带的固定偏移。
四个场景实测通过：春季前跳（NY 生成 NY 显示）、秋季回拨（同）、切时区（上海生成 UTC 显示）、同区当日。

**门的修补**：
- 门 ⑦ 的 oracle 从 `datetime.now().astimezone().tzinfo` 换成**无参** `instant.astimezone()`（C 库逐时刻），
  探针加了带 DST 规则的 `EST5EDT,M3.2.0,M11.1.0` 与三个跨 DST 时刻；
  另加**前提断言**用例：宿主 `/etc/localtime` 与全部探针 TZ 在所有时刻同解时如实红（不恒真）。
- 门 ⑨ 改为**走真实** `_gate_buckets`（初版在测试里复刻了参照系逻辑，是一道假门 —— 变异 M5/M7 首跑 SURVIVED 才暴露）。
- 新增 `test_vault_lint_today_actually_reads_the_shared_tz_source`：不替换任何东西、只动 `CANVAS_TZ`，
  东京与基里巴斯必须给出不同的「今天」。
- `host_tz` fixture：teardown 无条件重新 `tzset()`（此前只还原环境变量，`time` 模块的 C 层缓存不刷新）。

**变异从 5 扩到 8**：M4（POSIX 串读 `/etc/localtime`）、M6（POSIX 串落此刻固定偏移）、
M5（参照系恒用自带偏移）、M7（参照系恒用此刻时区）、M8（vault_lint 内部硬编码）——
八条全部 KILLED，各绑不同的失败身份，还原后逐文件核 sha。

**登记不修**：切时区不保证缓存失效（属 `ensure_payload` 面）、JS 在 `display_tz=null` 时用浏览器本地、
配置项四进程无统一入口、门 ⑥ 的宿主依赖。均在验收单「本卡未证明什么」。

## 三 请回答的问题（按重要性排序）

1. `_SystemLocalTZ` 的实现是否正确？`utcoffset` / `dst` / `fromutc` 的协议有没有踩坑
   （尤其 DST 转换当刻的折叠/空缺时段、`tm_isdst=-1` 的歧义解析、`mktime` 在不存在的本地时刻上的行为）？
2. 参照系「按证据择一」是否有新的失效面？举例：投影由**第三个**时区生成、而此刻显示时区在那一刻恰好同偏移
   （比如同为 +08:00 的 `Asia/Shanghai` 与 `Asia/Singapore`），门会用错规则吗？后果多严重？
3. 门 ⑦ / ⑨ / lint 接线门是否承重？把对应修复退回去，它们是否**只**因自己那条断言而红？
   有没有哪条门在某类宿主上会恒真或恒假？
4. 两份副本现在各有一个类 + 一个函数，源码对照门只比 `display_tz` 函数 —— `_SystemLocalTZ` 漂移了它发现得了吗？
5. `_SystemLocalTZ` 返回的 tzinfo 没有 `.key`，于是默认部署下 GET 的 `display_tz` 在 POSIX TZ 形态下仍是 `null`。
   这条链路的语义是否自洽？
6. 整改整体上有没有引入新的 BLOCKER / HIGH？特别是：有没有哪个原本能被抓住的坏投影现在会被放行？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 四级，每条给出 `file:line` 与一句话说明为什么它是那个级别。
没有问题的级别写「无」。请不要复述我的自述，只写你独立查证后的结论。
若某条 round-2 的问题在你看来仍未真正解决，请明确指出并保持原级别。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接数据库或任何网络服务。
- `recap_exam_build.py` / `inbox_preview.py` / `scripts/launchd/*` 本卡零改动，不在审查范围。
