# 独立复核请求 — CARD-RED-C1（tests/unit 既有红「JSON dual-write 退役族」10 条对齐现行契约）

## 一 背景与最小读取面（只读这些，不要扩大扫描面）

仓库根（本车道 worktree）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c`
分支 `card/u11-red-c`，开工基线 `da690bf8`。

这张卡的任务：`backend/tests/unit` 有一条长期存在的红基线（202 个 nodeid）。其中 **10 条**同属一个根因族——2026-03-26 的 `59586af1` 删除了 fake bridge / JSON dual-write 生产代码，而这些测试仍在断言被删掉的契约。本卡要求对这 10 条**逐条自取「契约演进依据」**，然后三选一处置：改断言对齐现行契约 / `xfail(strict=True)` 做跨卡交接 / 给不出依据就移交另一张定性卡（U5-C RED-R）。硬约束：无替代覆盖不许删用例；禁 `xfail(strict=False)`；禁把断言改成只锁测试文件内本地常量的自证；禁改 `backend/app/**`；另有 33+4 条同族被 `pytest.mark.skip` 掩盖的用例，本卡一律不去 skip。

**最小读取面（请只读下列，逐项）**：

1. 本卡代码改动：`git diff da690bf8 <审SHA> -- . ':(exclude)_bmad-output'`
2. `_bmad-output/审查/evidence-red-c1/c1-verdicts.md`（作者的 10 条依据表 + (e) 移交论证 + 事实更正）
3. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b13/red-align-da690bf8.md` 的 `:114-129`（本卡 10 条 nodeid 与失败身份分型）
4. `backend/app/config.py:470-482`（现行 DEPRECATED 字段定义）
5. `backend/tests/unit/test_story_38_6_scoring_reliability.py:20-95`（本地桩常量与 TestAC1TimeoutRetryAlignment 全类）
6. `_bmad-output/审查/evidence-red-c1/red-diff-<收工ts>.txt`（收工 nodeid 差集）+ 同目录 `tmp-window-attribution.txt`（一条被跨车道环境噪音污染的轮次的归属说明）

## 二 作者自述，请独立核对（不要采信下列任何一句，请自己去证）

1. **10 条依据各自成立，不是一个 sha 抄十遍**：作者声称 7 条依据是 `59586af1`，另 **3 条**（`config.py` 的 `ENABLE_GRAPHITI_JSON_DUAL_WRITE` 默认值族）依据是 **`daa9fd37`**，理由是 `git show 59586af1 --stat` 的文件列表里根本没有 `config.py`。请核对这个分叉是否成立，以及每条依据引用的删除行是否真在该 commit 里。
2. **子类②（3 条桩值矛盾）选 B（xfail 交接）而不是 A（把桩值改回 2.0/1.0）的理由**：作者声称 `GRAPHITI_JSON_WRITE_TIMEOUT` / `GRAPHITI_RETRY_BACKOFF_BASE` 在 `backend/app` 下 0 命中，所以无论桩值取哪个方向，断言的被断言物都只是同文件上方的本地常量 = 自证。请核对这个「无可重锚生产符号」的判断。
3. **(d)(e)(f) 三个分叉的判断证据**：分别是 memory_service 侧 getattr 防御点是否还在、main.py 的 fallback sync 调用是否还在、`MEMORY_RETRY_*` 配置项有没有消费方。请核对这三处的 census 是否有遗漏面。
4. **SKIPPED 集开工/收工**：作者声称原始 `diff` 非空但差异**只是行号标签位移 27 行**（等于其在该文件插入的行数，且插入点全在 skip 标记之前），归一化行号后集合逐条相同。请核对这个说法，特别是「归一化」有没有把真实变化一起抹掉。
5. **`>` 行为零**：收工 nodeid 差集应只有 `<` 行。作者声称第一次收工轮出现的唯一 `>` 行（一条 teardown ERROR）来自另一车道在全机共享 `/tmp` 下创建的目录，并已重跑取干净轮。请核对该归属论证是否成立、以及重跑轮是否真的干净。

## 三 请按重要性排序回答下列问题

1. **有没有把断言改成只锁本地桩 / 只锁测试文件内常量的自证？** 逐条看改动后的断言，判断其被断言物是否来自 `app.` 生产模块。特别看 `test_story_38_4_dual_write_default.py` 里被翻成 `is False` 的 3 条。
2. **每条 `xfail(strict=True)` 的 reason 是否写明归属卡，且其中的事实声明是否比证据宽？** 尤其：作者在 `test_qa_38_4_dual_write_extra.py` 的 reason 里主动收窄了措辞，声明「同形 getattr 防御在 `canvas_service.py` 仍有 6 处且 fallback 默认值是 True」。请核对这 6 处是否真实存在、以及收窄后的措辞有没有仍然过宽的残留。另请评估被交接到的等价覆盖（`backend/tests/unit/test_episode_worker_retry.py`，5 个用例）实际覆盖了什么、是否足以支撑「退役」这一判断。
3. **(e) 两条判「移交」而不是「挂 xfail 当演进」是否正确？** 作者的论证是：`failed_writes.jsonl` 的写侧（经 `_trigger_memory_write`，11 处生产调用）仍活，而两条回收路径（`FallbackSyncService.sync_all_fallbacks` / `MemoryService.recover_failed_writes`）双双零生产调用方，替代者 `episode_worker.py` 未接管，`main.py:216` 启动期恢复的是另一机制（EventBus 的 `data/outbox`）。请独立核对每一环；若你认为该判断有误（无论方向），请说明是哪一环不成立。
4. **33+4 条被 skip 掩盖的同族用例，是否被本卡任何改动波及？** 本卡在 `test_story_38_6_scoring_reliability.py` 里加了装饰器，该文件同时含一处类级 skip。
5. **同文件里不属于本卡的用例（归 U11-B 的 7 条 C2、归 U5-C 的 2 条 R）是否被顺手改动？** 本卡明令禁碰它们，也禁改任何类名。另：作者声明未改 `test_story_38_4_dual_write_default.py` 的模块级 docstring（其 `:8/:10` 仍称默认为 True，与翻转后的断言不一致），理由是该文件头同时描述 U11-B 地盘的 AC-2。请评估这个「不改并登记」的取舍。

## 四 输出格式

每条发现写成：

```
[BLOCKER|HIGH|MEDIUM|LOW] <一句话结论>
file:line
一句说明：该问题在什么输入或什么时序下会显现
```

没有发现就明说「该项未发现问题」，不要为凑数编造。请在开头给出四个等级各自的计数。

## 五 边界

- **只读**。不要修改任何文件，不要运行会写盘的命令。
- **不要连数据库**（本仓有 Neo4j 7691/7687，本卡完全不涉及；`tests/integration` / `tests/e2e` 也不在范围）。
- **不要评价 U5-C 的回归定性结论本身**——本卡只负责提供证据并移交，是否真的是数据面回归由那张卡裁定。你可以评价「本卡提供的证据是否支撑得起移交这个动作」。
- **不要评价第十四批的去 skip 方案**（33+4 条如何恢复不在本卡范围）。
- 不要给出修复补丁，只指出问题与位置。
