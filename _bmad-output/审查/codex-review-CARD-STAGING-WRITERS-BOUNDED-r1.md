> 批次: BATCH-2026-09-18-第十五批 · 车道 P2 · 卡 CARD-STAGING-WRITERS-BOUNDED round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-STAGING-WRITERS-BOUNDED.md)"`
> 审查绑定: `2a921e771cb5621520cc0251d8651df01739ce56`（正文首句已自证同 SHA）
> 会话头自证（抄 .stderr 三行，括注行号；stderr 本身不入库）:
> `(L4) OpenAI Codex v0.153.3` / `(L7) model: gpt-6-astra` / `(L11) reasoning effort: ultra`

---

**不能按 HIGH=0 收口。** 已绑定 `2a921e771cb5621520cc0251d8651df01739ce56`，所审代码与该提交一致。以下结论来自限定源码及纯内存对照；未修改文件、启动服务或连接数据库。

[HIGH] `backend/app/core/failed_writes_constants.py:133` — **⓪ 超时风险确已登记给 REPLAY-REWRITE，但新守卫仍重新打开了原先封住的丢记录窗口。**  
  复现思路：**未被拦下的输入**：回灌取得 5 行快照且仍在缓慢运行，超时后新写触发轮转，活动文件剩 1 行；finalize 的 `1 > 5` 为假，新条目被覆盖或误标为已回灌；**对照输入**为旧守卫，相同时序不会轮转。

登记本身属实：docstring `:104–109`、本卡验收单 `:306–309` 和 `:333–336` 均明确移交 P2-C，后者要求下一卡引用。新超时门仅断言发生轮转，**门未覆盖的路径**是原回灌随后继续 finalize。因此这不是把旧回灌算法单独列为发现，而是本卡放行轮转造成的安全退化。

[MEDIUM] `backend/app/core/failed_writes_constants.py:278` — **⓪ “越限不再无限期”“至多失效指定秒数”仍然过强。**  
  复现思路：**对照输入**为现有直接持锁且时间戳为 `None` 的真锁门，无论持续多久仍禁止轮转；**未被拦下的输入**还包括持续轮转失败但追加成功。

同类过强表述包括：

- 本文件 `:102` 的“上限至多失效”，以及 `:69–79` 未加条件的“不丢数据／任一竞态都安全”。
- `fallback_sync_service.py:92` 的“区分正在回灌与挂住”：时间戳只能判断耗时。
- 本卡验收单 `:308` 的绝对时间上限，以及 `:370` 的“不会撑爆／强退不会整批不见”。

[HIGH] `backend/app/services/memory_service.py:1437` — **① 即时刷盘提前触发既有的失败后无条件清空逻辑，使短暂 IO 故障变成无法补刷的记录丢失。**  
  复现思路：**未被拦下的输入**：请求期间 `mkdir/open/write/close` 抛 `OSError`，磁盘随后恢复；`:2899–2900` 已清空 pending，`cleanup()` 无记录可补写。

纯内存提取真实刷盘方法验证：`mkdir` 抛 `PermissionError` 后，pending 和已写记录均为空，恢复后再次刷盘仍无记录。部分写入后失败也会清掉未写尾部。清空逻辑虽是旧代码，本卡新增了“请求期短暂故障、退出前已恢复仍丢失”的时序；现有即时刷盘门只覆盖成功落盘。

[MEDIUM] `backend/app/services/memory_service.py:1437` — **① 新调用确实增加事件循环中的同步 IO 和同步锁等待。**  
  复现思路：**未被拦下的输入**：活动文件读取缓慢，或另一线程持有 `failed_writes_lock`；批次协程同步执行核行数、轮转、追加，期间其他协程无法获得调度。

没有 `await` 能避免协程插入 append/clear 之间，但不能证明 IO 不阻塞。正常及已捕获刷盘异常路径的 `errors / failed / episode_ids` 赋值未变；刷盘失败只记日志。正常单事件循环下，成功刷盘后 cleanup 不会重复落盘。现有门未验证调度延迟或三个返回字段。

[HIGH] `backend/app/services/event_bus.py:378` — **新增轮转会令正在恢复的读取句柄留在旧文件，最终改写覆盖新活动文件中的未恢复条目。**  
  复现思路：**未被拦下的输入**：上限为 1、活动文件只有 A；恢复读出 A，在 `await publish(A)` 期间写入 B，轮转后读取器看不到新文件中的 B，`:429` 最终以 A 覆盖 B；**对照输入**为旧裸追加，相同时序读取器会继续读到 B。

抽取真实写入、恢复及轮转函数，使用保留文件身份的内存 IO 模型得到：

```text
禁用轮转：恢复 A、B；活动文件 A、B
启用轮转：只恢复 A；overflow 为 A；活动文件为 A；B 消失
```

这是本卡轮转对既有恢复流程的新增恶化。现有 outbox 门没有覆盖恢复期间轮转。

[LOW] `backend/tests/unit/test_staging_writers_bounded.py:499` — **③ `"-00" in name` 会误匹配 UTC 零点的时间戳，导致正确实现误红。**  
  复现思路：**未被拦下的输入**为 UTC `00:12:34`：全部 100 个候选都被错误注入权限异常，随机兜底名也无法通过 `:504`；**对照输入**为 UTC 11 点，此时仅拦序号 `-00`，返回 `-01` 后门绿。

[MEDIUM] `backend/tests/unit/test_staging_writers_bounded.py:575` — **新增 AST 隔离门验证的是名字出现，不能保证路径实际隔离。**  
  复现思路：**未被拦下的输入**为 `test_x(tmp_path)` 内调用未传路径的 `DeadLetterStore().store(...)`，或只放入两个路径常量字符串再调用写者，扫描结果均为空；**门未覆盖的路径**还包括 `Test*` 类方法。

上述漏判已对真实扫描函数做纯内存验证。现有直接违规的**负控输入**能被抓住、合规 fixture 的**对照输入**仍绿，但不足以支持“忘了隔离就当场红”；这不表示当前测试已实际写入现网文件。

其余问题核对结果：

- **② 锁顺序：限定读取面内未发现新增反序。** 两个新增临界区调用的轮转原语不自行取锁，也未传回调；没有发现 `_dead_letter_io_lock → failed_writes_lock` 的反向获取。守卫只读 `_sync_all_lock.locked()`。这不能扩大为全仓调用链的无死锁证明。
- **③ 三条吞异常门有效。** 本地 Python 3.14.4 内存负控得到：旧 `overflow_siblings` 返回 `[]`、旧候选选择返回 `-00`、旧 `count` 返回 `0`；现实现分别抛权限异常、返回 `-01`、抛权限异常。**门未覆盖的路径**包括 100 个候选全部探测失败后返回未经探测的随机名，以及缺失文件的同族对照；随机兜底是既有代码，不另算新增丢数。
- **④ 配置通过。** 新增三个常量均走 `bound_from_env`，非整数及低于下限的值退回默认并告警；`OUTBOX_MAX_ROTATIONS=0` 合法。未发现新增裸 `int()` 导入崩溃面。
- **⑤ 新增 `# pyright: ignore` 为 0 条，新增 `type: ignore` 也为 0。** 本轮未复跑 `pyright app`，因此不能把验收单的“0 errors”当成本轮实测。

证据限制：指定旧裁定书在此 checkout 只有 **111 行**，无法核对所指第 158、186 行；本卡验收单引用已按审查 SHA 读取。未运行 pytest 或磁盘集成测试。


