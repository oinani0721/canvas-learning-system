# 代码审查请求 — CARD-Y4-D-TAIL round-4（第十四批 / 车道 T10 第 3 张）

## ① 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red`

**只读这些，不要读其它文件**：

1. `git diff 95d2d27a 9b631648 -- . ':(exclude)_bmad-output'`（本卡全部代码改动）
2. `backend/tests/unit/test_graphiti_json_dual_write.py`（改后全文）
3. `backend/tests/unit/test_story_38_6_scoring_reliability.py`（改后全文）
4. `backend/tests/unit/test_episode_worker_retry.py`（全文；本卡声称的等价覆盖基准）
5. 只读参考（不评其设计）：`backend/app/services/memory_service.py` 的
   `_enqueue_episode` / `record_learning_event` / `record_temporal_event` / `recover_failed_writes`；
   `backend/app/services/episode_worker.py` 的 `GraphitiEpisodeWorker`（`enqueue` / `is_ready` / `start`）。

**任务背景**：早前的重构（fix-rag-transform-and-episode-isolation）删掉了 `MemoryService` 上两个私有
JSON 写入助手。当时用一个**模块级 skip** + 一个**类级 skip** 把两个测试文件的相关部分整体关掉，顺带
把 4 条与那两个助手无关、本来是绿的用例也一起关掉了。本卡的任务是移除这两个 skip、恢复那 4 条，并把
真正断裂的用例改到现行管线（`_enqueue_episode` → `GraphitiEpisodeWorker`）上。

## ② 作者自述（请独立核对，不要采信）

1. 4 条恢复目标现为 PASS：`test_fire_and_forget_doesnt_block_return` / `test_timeout_protection` /
   `test_config_flag_disables_dual_write` / `TestAC3StartupRecovery::test_recover_no_file`。
   这 4 条的**断言体一字未改**，只加了 docstring 说明。
2. 移除 skip 后实测 11 条红（非既有红），已全部处置 = **7 条重写 + 4 条删除**：
   4 条重写到 worker 入队边界、3 条 recovery 重写（用真 worker）、3 条 logging 删除、
   1 条 dataclass 删除。（r2 LOW-4 更正：此前写成「4+4 重写 + 3 删除」，把
   `test_recover_no_file` 误计入重写——它完全原样未动——并把 dataclass 删除漏在删除计数外。）
3. 两个测试文件对已删私有助手的引用：`test_graphiti_json_dual_write.py` 13 → **0**；
   `test_story_38_6_scoring_reliability.py` 4 → **1**。
4. **剩余那 1 处是作者主动保留的**：它在 `@pytest.mark.xfail`（reason 含 `[CARD-RED-C1]` /
   `CARD-EPW-COVERAGE`）的 reason 文本里。卡文一边要求「引用清零」，一边把这三个 xfail 标记列为
   **禁改**。作者判定禁改边界优先，未改该行。**请独立判断这个取舍是否正确**。
5. 新断言做过负控：把 fixture 里的 `await w.start()` 去掉（worker 未就绪）后，
   重写的 6 条用例全部变红，且红在作者声称的那条断言上；`test_recover_no_file` 在同样条件下仍 PASS。
6. xfail 标记 `:37/:50/:78` 的**内容**一字未动（行号因新增一行 import 而整体 +1，变为 `:38/:51/:79`）。
7. 未触及 `backend/app/**`、未改任何 conftest、未改 `test_episode_worker_retry.py`。

### round-2 增补（r1 之后改了什么）

r1 判定 `B=0 H=0 M=1 L=1`。两条都指作者自述不准确，已按判定更正（本轮请复核更正本身）：

- r1 MEDIUM：删除说明里「比原断言更强」的措辞已删除，改为「邻近场景，非等价覆盖」，
  并逐条列出**未被接替**的观测点（success 的 debug 调用与 episode_id 关联、failure 的
  warning "failed" 文案、timeout 的慢下游输入）。`test_fire_and_forget` 注脚里
  「真实语义见 X」的归属声明已删除，改为如实声明「本仓当前无用例施加真实下游延迟」。
- r1 LOW：`test_recover_successful_replay` 的 docstring 里「旧版曾挂载已删私有助手」
  已更正为「只有 `test_recover_partial_failure` 如此」。
- r1 观察（spy 在委派前记录 ⇒ 只证明尝试入队）：`test_dual_write_called_after_neo4j_success`
  增加 `ready_worker.metrics.episodes_enqueued == 1`，由 worker 自身计数证明队列接纳；
  并在 `group_id` 断言旁标注它只是形状检查。
- r1 LOW（负控条数）：依赖 `ready_worker` 的用例共 7 条，首轮负控只跑了 6 条；已补跑第 7 条
  `test_json_write_failure_doesnt_affect_main_flow`，同样按预期变红
  （`Expected 'enqueue' to have been called once. Called 0 times.`）。

### round-3 增补（r2 之后改了什么）

r2 判定 `B=0 H=0 M=0 L=4`，四条都指陈述不一致，已逐条更正：

- r2 LOW-1：`test_record_temporal_event_dual_write` 补 `ready_worker.metrics.episodes_enqueued == 1`
  （与 4.1 同口径，由 worker 自身计数证明队列接纳）。
- r2 LOW-2：三条 logging 删除说明的**段首**原写「等价覆盖逐条归属如下」，与段末「邻近场景，
  非等价覆盖」自相矛盾。段首已改为明写「邻近场景归属，不是等价覆盖」。
- r2 LOW-3：文件头 Test Coverage 原把 4.2/4.4 与其余并列。已改为只标 4.1/4.3/4.5 为
  `[verified]`，并明写 4.2/4.4 未被本文件验证、「慢下游不拖住调用方」当前全仓无覆盖。
  `test_timeout_protection` 注脚里「只证明调用方不被下游拖住」也已改为
  「只证明调用方会返回一个 episode_id」。
- r2 LOW-4：分拆自述已在本 prompt ② 段更正为「7 条重写 + 4 条删除」。

### round-4 增补（r3 之后改了什么）

r3 判定 `B=0 H=0 M=0 L=2`，两条都指措辞超出实际覆盖，已逐条收窄：

- r3 LOW-1：`test_config_flag_enables_dual_write` 的 docstring 原写
  「recording enqueues regardless of the flag」，实际只测 flag=True 一侧。已改为明写只钉
  True 侧，并补上：配对的 `test_config_flag_disables_dual_write` 断言也已与 flag 脱钩，
  ⇒ 若日后让 flag 重新生效、False 时跳过入队，**这两条都发现不了**。
- r3 LOW-2：两处 `ready_worker` fixture 的 docstring 原写「整体替换 worker 会让
  `_enqueue_episode` 的 readiness 分支与 `EpisodeTask` 创建零覆盖」。已按 r3 更正为：
  提供 `is_ready`/`enqueue` 的 stub 之下那些生产代码照样执行；stub 真正拿掉的是
  **worker 自身实现**的覆盖——队列计数、`is_ready` 的真实语义
  （`_started and _graphiti is not None`）、队列满/已关闭时 `enqueue` 返回 False 的分支。

除上述 docstring/注释外，r3 → r4 之间**没有任何可执行代码改动**。

**本轮请重点判断**：(a) 这两处收窄后的表述是否仍有过强或不实之处；
(b) 通读两个文件现存的全部覆盖声明（文件头、各 docstring、删除说明），是否还剩任何
一处「声称的覆盖 > 断言实际能发现的回归」；(c) 若已无此类问题，请明确说明。

## ③ 请按重要性排序回答

**⓪ 删除的 3 条用例是否真有等价覆盖？**
被删的是三条针对已删私有助手的 logging 用例。作者把它们归属到 `test_episode_worker_retry.py` 的
scenario 1/2/3/4（见该文件内的删除说明注释）。请逐条核对：那些 scenario 是否真的覆盖了被删用例所断言
的语义？作者自己声明「未逐断言比对、日志文案本身现无专门用例覆盖」——这个声明是否诚实、是否还有他
没说出来的覆盖损失？另有一条 `test_learning_memory_dataclass_creation` 被删，作者声明那是**真实覆盖
损失**（非等价覆盖）。请判断这个定性是否准确。

**① 重写的用例是否引用了已删私有符号，或以别的方式依赖不存在的东西？**
`test_episode_worker_retry.py` 的文件头写着「Tests MUST NOT mock deprecated retry symbols」。请检查本卡
新写/重写的代码是否违反这条，包括间接违反（例如给对象赋一个生产上并不存在的属性）。

**② 移除两个 skip 后，是否还有用例被放出来但没被正确处理？**
请核对：两个文件里现在**所有**用例的状态是否都被作者交代过。作者说除既有红外都绿了——请看是否有
被悄悄删掉、悄悄改名、或改成恒真断言而未声明的。

**③ 新断言是否存在恒真风险（门未覆盖的路径）？**
作者保留原样的 3 条目标用例，作者自己承认它们在现行管线下断言恒真（断言主体 `add_learning_episode`
已无生产调用方），并写进了 docstring。请判断：(a) 这个「保留原样 + docstring 声明」的处置是否恰当，
还是应当重写；(b) 作者**新写**的断言里是否也有恒真的（尤其 `assert isinstance(task.group_id, str)`
这类形状断言，以及 `ready_worker.metrics.episodes_enqueued == 1`）。

**④ fixture 设计是否把被测层 mock 掉了？**
作者声称 `ready_worker` 用真 `GraphitiEpisodeWorker`、只 mock 最外层 graphiti 客户端，目的是不让
`_enqueue_episode` 的 `is_ready` 分支与 `EpisodeTask` 的创建路径失去覆盖。请核对这个说法是否成立，以及
`test_recover_partial_failure` 里直接给实例赋 `ready_worker.enqueue = flaky_enqueue` 是否有副作用
（例如 fixture teardown 的 `await w.stop()`）。

## ④ 输出格式

按严重度分组：`BLOCKER` / `HIGH` / `MEDIUM` / `LOW`。每条给出：
- `file:line`
- 一句问题陈述
- 一句触发条件（什么输入或什么状态下它会出错）

若某一档为空请明写「BLOCKER: 无」。结尾给一行总计：`B=? H=? M=? L=?`。

## ⑤ 边界

- 只读审查，不要修改任何文件。
- 不要连接数据库、不要跑测试、不要执行 hook。
- 不评价 `backend/app/**` 的生产设计（那不在本卡地盘，本卡一个字都没改）。
- 不评价卡文/流程本身，只评代码与作者自述之间是否一致。
