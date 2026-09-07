**BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 4。**

未发现本卡通过自证断言翻绿、波及 skip、改动其他卡用例或修改生产代码。发现的问题集中在交接追踪与证据表述；(e) 的源码证据足以支持移交，不能据此裁定数据面回归。

[LOW] 配置项这条 xfail 没有提供可定位的接收卡标识。  
[test_cache_configuration.py:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_cache_configuration.py:53)  
一句说明：后续清理配置或解除 xfail 时，reason 和依据表都只有“配置清理卡（登记）”，而 `[CARD-RED-C1]` 是来源卡，无法从这些记录定位接收卡。

[LOW] 收工 skip 快照漏采一处，不能支持“五处标记原文均已留存”的声明。  
[y4d-skip-marks-close.txt:24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/_bmad-output/审查/evidence-red-c1/y4d-skip-marks-close.txt:24)  
一句说明：插入 27 行后仍按旧位置 `135–138` 抽取，快照只剩空标题，下一行已进入第五个文件；实际类级 skip 在收工文件第 162 行，最终 diff 和原始摘要仍能证明它未变。

[LOW] “11 处生产调用方”没有说明直接调用与上游入口的统计口径。  
[c1-verdicts.md:102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/_bmad-output/审查/evidence-red-c1/c1-verdicts.md:102)  
一句说明：按直接调用 `AgentService._trigger_memory_write` 计是 **10 处**，加上 batch 的两处包装方法调用是 **12 处**，排除中间转发、按上游入口才是 **11 处**；这不影响写侧仍可达的结论。

[LOW] 未限定路径的 `59586af1 --stat` 被误记为只有两个文件。  
[c1-verdicts.md:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/_bmad-output/审查/evidence-red-c1/c1-verdicts.md:211)  
一句说明：复执行该命令会看到第三个文件 `graphiti_bridge_service.py`；`config.py` 确实不在其中，因此另取 `daa9fd37` 的分叉仍然成立。

逐项复核结果如下。

**1. 自证断言：该项未发现本卡新增问题。**

| 用例（省略类名前缀） | 收工被断言物与处置 |
|---|---|
| `test_settings_field_default_is_false` | `app.config.Settings.model_fields[…].default`，生产字段元数据 |
| `test_lowercase_alias_returns_false_by_default` | 生产 `Settings` 实例及 property；property 直接返回大写字段 |
| `test_missing_env_var_defaults_to_false` | 清除环境覆盖后的生产 `Settings(_env_file=None)` 实例 |
| `test_retry_delay_reads_settings` | 生产 `MemoryService` 实例属性；配置输入虽被替换，被测服务没有替换，现加严格 xfail |
| `test_inner_per_attempt_timeout_increased` | 仍是本地 `0.5` 常量；断言未改，保留失败并严格 xfail |
| `test_retry_backoff_base_is_1_second` | 仍是本地 `0.1` 常量；断言未改，保留失败并严格 xfail |
| `test_backoff_progression` | 仍从本地常量推导；断言未改，保留失败并严格 xfail |
| `test_memory_service_getattr_fallback_is_false` | 读取生产 `Settings`，但 `getattr` 表达式写在测试内，未执行 memory_service 防御点；本卡没有靠翻断言使其通过 |
| `test_main_imports_fallback_sync` | 读取 `app.main` 源文件，保持原断言、移交 |
| `test_fallback_sync_called_in_lifespan` | 读取 `app.main` 源文件，保持原断言、移交 |

三条翻绿断言见 [test_story_38_4_dual_write_default.py:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_story_38_4_dual_write_default.py:46)、`:64`、`:261`，均能捕捉生产默认值变回 True。

历史删除行也逐项吻合：`59586af1` 删除两个 retry 属性、两个旧常量及其消费路径、memory_service 的开关防御点、main 的 fallback import/call；`daa9fd37` 才修改配置默认值并加入 DEPRECATED。这里的 **7＋3 分组成立**，其中 QA 那条 reason 同时引用两个提交也是准确的。

选择 B 有依据，但“两个旧名字零命中”只能证明**旧符号消失**。现存 worker 仍有 `can_retry`、`backoff_seconds`，只是采用随机退避，并不实现原来固定的 2 秒／1、2、4 秒契约。

**2. xfail reason 与替代覆盖：除上述接收卡定位问题，该项未发现问题。**

五条全部为 `strict=True`；另外四条明确归 `CARD-EPW-COVERAGE`。memory_service 的开关代码已消失，仅留下历史 docstring；canvas_service 的 `267/360/440/457/986/995` 六处真实存在，第三参数全部为 **True**。收窄后的 reason 没有继续声称整个防御模式消失。两个 `MEMORY_RETRY_*` 在 `backend/app` 下只有配置定义，无消费引用。

`test_episode_worker_retry.py` 五条实际覆盖：入队处理成功、失败三次后第四次成功与退避范围、耗尽重试写死信、指标、显式 request_id 进入死信。它们执行生产 worker，但没有覆盖旧单次超时、固定退避、MemoryService 配置读取、getattr 防御或旧失败文件恢复；退避范围断言甚至允许恒零延迟通过。因此它们支持“已有替代机制和部分覆盖”，**不足以证明完整等价覆盖或完成退役**。本卡已明确交接覆盖缺口，没有把这些测试当成完整验收。

**3. (e) 移交动作：该项未发现问题。**

各环节源码均支持移交：

- `_trigger_memory_write` 的超时、异常分支仍调用 `_record_failed_write`，实际追加同一个 `FAILED_WRITES_FILE`。
- `_record_structured_outbox` 也仍有生产调用，并写入该文件。
- 两条回收 API 在 `backend/app` 下均没有生产调用；fallback sync 函数体确实处理三类存储。
- worker 使用自己的 `dead_letter_episodes.jsonl`，没有接管 `failed_writes.jsonl`。
- `main.py:216` 恢复的是 EventBus 的 `data/outbox/events.jsonl`。
- memory_service 另有读取旧失败文件的合并视图，但只加载分数，不构成第三条重放路径。

这足以支持保留两条红项并交给 U5-C 定性。受读取边界限制，我确认的是 `backend/app` 的静态调用关系，没有扩大扫描以背书“全仓只有测试”，也没有验证现网 pending 数据。

**4. 33＋4 条 skip：实际影响该项未发现问题。**

最终提交确实仅在 AC1 三个方法前各新增 9 行，类级 skip 与被遮蔽用例均未改。48 条开工／收工摘要只有四个位置变化：

`154/165/190/236 → 181/192/217/263`。

除行号外逐字相同；按**保留重复次数的多重集**重新归一化比较也一致，没有靠去重抹掉真实变化。上面的快照漏采属于归档缺口，不是 skip 被改动。

**5. 其他卡用例与模块 docstring：该项未发现越界改动。**

逐个比较函数及装饰器后，变化只有三组改名和五个新增 xfail；其他用例、所有类名和类级装饰器保持不变，移交文件也完全未改。因此没有顺手修改 U11-B 的 7 条 C2 或 U5-C 的 2 条 R。

模块头 `:8/:10` 确实仍写 True。结合本卡限定范围及已登记说明，“不改并登记”可以接受；它仍是文档残留，不应被当成现行默认值依据。

**收工差集：该项未发现新增红项，但归属证据只能部分确认。**

从原始日志重算得到 **202 → 194，移除恰好 8 条、新增 0 条**；两条移交测试仍红。两次弃轮均只多同一个 wikilink teardown ERROR，分别报告两个 treeB 目录；终审轮没有该污染消息，恢复为 29 errors。

不过，具体由 U10-A 创建的通告、stat、ps 输出只有作者转述，不能独立确认写者身份。原始日志也没有 SHA 或输入文件摘要，因此可以确认“存档终审轮干净、结果符合最终 diff”，不能单凭“终审绑定轮”名称证明其输入精确绑定 `343fce8e`。

本次未运行测试、修改文件或连接数据库；运行结果结论来自存档日志复算。
