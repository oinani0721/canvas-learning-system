审查范围：给定 BASE → `8e3a1306db5b523493d46e9bbeb4c8420d9a52f3`。确认 **4 项 MEDIUM、1 项 LOW**。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM**

1. **交互页重新判定活跃性，会推翻服务端结果。**  
   [review_app.py:364](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_app.py:364) 用 `Date.parse` 和浏览器 `Date.now()` 再筛一次已经由服务端筛好的 snooze。
   
   **失败场景：**服务端 19:59，浏览器快两分钟；截至 20:00 的板仍被服务端判为活跃，交互页却提前恢复待做并隐藏“取回”。另有无需钟差的复现：既有显示时区支持秒级 offset，生成 `2026-09-09T20:00:00+08:00:30` 后，Python 判活跃，JS 解析为 `NaN`，导致 POST 成功后交互页仍不显示“已推迟”。

2. **损坏 snooze 板名可使整个总览 GET 返回 500。**  
   [review_overview.py:2484](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:2484) 只检查键值是 `str`；新增 `entry.snoozed` 未经过既有 projection 的 UTF-8 可编码检查。
   
   **失败场景：**state 包含 `{"snoozed":{"\ud800":"2026-09-09T20:00:00+08:00"}}`，当前为当天 10:00。孤立代理字符键通过活跃筛选，最终 JSON 响应编码抛 `UnicodeEncodeError`。异常发生在 `_collect` 返回之后，单库异常兜底捕获不到，整个聚合请求失败。

3. **极值 until 在生成唤醒时间时溢出，终止 runner 本轮执行。**  
   [daily_review_run.py:627](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:627) 未保护 `u.astimezone(timezone.utc)`。
   
   **失败场景：**state 中 `snoozed={"A":"9999-12-31T23:59:59-01:00"}`。生产器解析成功且判为活跃，但转 UTC 越到 10000 年，抛 `OverflowError`。此时 payload 已写出，state 尚未保存；runner 记录生成失败并退出，本轮推送也不执行。

4. **错误类型的唤醒缓存字段会阻断本应发生的重扫。**  
   [daily_review_run.py:580](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:580) 直接比较 `snooze_wake_utc <= now_z`，没有类型验证。
   
   **失败场景：**同日 payload、SHA、两个账签名均正常，但 state 中 `snooze_wake_utc=1`。比较抛 `TypeError`，现有缓存分支异常处理不接它。即使 `due_crossed=True`，也会先在计算 `wake_crossed` 时失败，runner 本轮退出而非重扫。

**LOW**

1. **冷启动 GET 的惰性导入突破只读契约。**  
   [daily_review_run.py:500](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:500) 的 picker 导入发生在 `_load_runner` 禁止字节码写入的窗口之外。
   
   **失败场景：**后端首次读取非空 snooze，picker 尚未导入且没有有效字节码缓存。GET → `_snoozed_active` → runner 包装函数会尝试创建 `scripts/__pycache__/daily_review_pick*.pyc`。已拦截到真实 loader 写请求，未实际执行写盘。既有冷加载门只调用 `_load_runner`，因此漏掉此路径。

其余指定核对结果：

- 两档换算使用 `_display_now()` 提供的时区；DST 切换前时刻的探针确认次日午夜采用次日 offset。未发现新增 `_DISPLAY_TZ*` 常量。
- pick 对 naive、普通错格式、非字符串值、非字符串键、过期值均丢弃；两条未改动的金样门能抓住 payload 顶层新键。
- 正常 state 下，旧 v2 不因缺 snooze 签名白重扫；wake、due 单独或同时到点均触发重扫，没有短路失效。
- FSRS 三项写面允许集未放宽；新增负控明确检查 `_FSRS_GATE_MSG`。
- 新 POST 仅由点击触发；没有节点级、自定义时长或静默改档入口。两个页面直接消费 `tonight_available`。**GET 与 POST 各自读一次时钟，并非两个请求共用一次读数**；正常跨 20:00 的 422 竞态不列缺陷。
- 新增 `<details>` 条件渲染，两条既有计数断言未改；同板完成且推迟只渲染一次。
- `_SNOOZE_NOTE` 共享注入；两张 AST 表各加一项，检查器及探针矩阵未改；四条枚举门仍是精确登记。
- 改为版本常量的断言均检查升版结果；输入夹具 v1/v2 字面量保留，另有实值 `3` 的独立门。

全程未修改文件、未连接数据库或网络服务。完成了 diff 核对及纯内存复现；未运行会写临时文件的完整 pytest。


