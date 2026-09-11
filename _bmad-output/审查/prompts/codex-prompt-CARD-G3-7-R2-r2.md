# 独立复核请求 — CARD-G3-7-R2 round-2（整改核验 · 绑定最终 HEAD）

你是独立复核者。请**只读**，不修改任何文件，不连数据库，不运行测试或脚本。
你的 round-1 意见（1 HIGH / 3 MEDIUM / 1 LOW）作者已全部采信并整改；本轮请**独立核验整改本身是否成立**，
不要因为「上一轮已指出」而放过，也不要因为「作者说已修」而放行。

---

## 一 背景 + 最小读取面（写死，请只读这些）

**仓库树根**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery`

round-1 审的是 `c480de1d`。之后有两个整改 commit：
- `136c6809`（代码：门加固 + 锁加计数 + 退役自动门 + docstring 修正）
- `65e18d04`（docs：检索范围措辞）
**本轮绑定 HEAD = `65e18d04`**（请自行 `git rev-parse HEAD` 核对并写进正文首句）。

**请读**：

1. 整改 diff：`git diff c480de1d 65e18d04 -- . ':(exclude)_bmad-output'`
2. 你 round-1 的原文：`_bmad-output/审查/codex-review-CARD-G3-7-R2-r1.md`
3. HEAD 版 `backend/tests/unit/test_mastery_fsrs_projection_boundary.py` **全文**（门加固的主战场）
4. HEAD 版 `backend/tests/unit/test_review_service_fsrs.py` `:585-:700`（锁 + 新退役门）
5. HEAD 版 `backend/app/services/mastery_engine.py` `:276-:310`（docstring 行号改函数名锚）
6. HEAD 版 `docs/fsrs-truth-source-d0-revision.md` `:65-:70`（四写点表 ④ 行）
7. HEAD 版 census：`_bmad-output/审查/evidence-g37r2/census-20260908T073936.md` **全文**（HIGH-1 整改主战场，重点 §0.3 / §0.4 / §0.5 / §一 / §六 / §七）
8. 负控存档（你上轮「未核实-2」说缺 pytest 原始正文；本轮重跑已附）：`_bmad-output/审查/evidence-g37r2/negctl-N1N2-20260908T114151.txt`（16.8KB，末尾附录 A/B 是两个变异体下门文件的完整 pytest 输出，含 `^E` 行）
9. 验收单「本卡未证明什么」更新：`_bmad-output/验收单/UAT-CARD-G3-7-R2-2026-09-08.md` §10

## 二 五条整改的作者自述（逐条独立核验，勿采信）

1. **HIGH-1（census 取数面）**：新增 §0.5「面④ 经公开 API 的消费」——第一步用 AST 枚举 `review_service.py` 全部函数体触碰 `self._card_states` / `_CARD_STATES_FILE` 的方法（9 个、公开 6 个，含初版漏掉的 `get_history` 与 `schedule_review`）；第二步逐方法在 `backend/app` 找外部调用点，并逐行排除 `rollback` 上 `OperationTracker` 的同名假阳性。补上 `review.py:681`（初版漏掉的第三个调用点）。§0.3 的「去掉间接规则 ⇒ N 恒 = 0」论证已更正为「系统性漏掉」；§六 结论加「N 的正确读法」限定；§七 补第 7/8 条盲区。
   **请核**：AST 方法清单是否真的完整（你会不会用别的方法枚举出第 10 个）？§0.5 表里的行号与 HEAD 是否相符（作者声明该节实测基点是 `c480de1d` 而非表头的 `8f7440ef`，此差别已注明——这个注明够不够）？
2. **MEDIUM-2（写边界门）**：名单拆两档（`UNAMBIGUOUS_FS_WRITES` 见名即判 / `AMBIGUOUS_FS_WRITES` 需 `_receiver_is_filesystem` 判接收者）；`_open_is_write` 按调用形态取 mode 下标（绑定方法 args[0]、内建 args[1]）；`_find_write_calls` 补扫「未被调用的 Attribute 节点」以捕获回调式引用（`asyncio.to_thread(p.write_text, d)`）；验伪锚改为 16 条判据矩阵（含你 round-1 的全部反例）。
   **请核**：16 条矩阵是否每条都与实现一致？两档划分还有没有你 round-1 没提、本轮仍存在的误拦/漏报形态（例如 import 别名、`getattr` 动态取方法——作者已在验收单 §10.9 声明这是固有盲区，你认不认这个声明的边界画得对）？
3. **MEDIUM-3（锁加计数）**：替身 `touched.append(...)`，用例末尾 `assert touched == []`。
   **请核**：这条是否真的不依赖异常冒泡？有没有它仍抓不住的复活形态？
4. **MEDIUM-4（范围措辞）**：`docs/fsrs-truth-source-d0-revision.md` ④ 行改为写明实际命令与范围；验收单同步。
   **请核**：新措辞是否仍比证据宽？
5. **LOW-5（行号→函数名锚）**：`mastery_engine.py` 读方清单改用函数名；门文件模块 docstring 同步现状。
   **请核**：被点名的函数现在还是不是读方（读一遍 `_get_retrievability` 与 `concept_to_response`）？docstring 与代码是否一致？

另有一条**作者自加**（非你 round-1 意见）：`test_retired_public_card_state_writer_is_gone`（`assert not hasattr(svc, "save_card_state")`）。作者自评：挡得住同名复活、挡不住改名复活（已在验收单 §10.10 声明）。请评这个自评是否诚实。

## 三 按重要性排序的问题

1. 整改有没有只是「换个说法」而没解决实质的？（特别是 HIGH-1：census 的 N=1 现在的支撑是否够）
2. 整改是在压力下重写的——最容易引入新缺陷却最没人看过。门的两档名单、回调式扫描、计数锁，有没有新引入的误报/漏报/逻辑错？
3. 你 round-1 的四条「未核实」（动态调用链 / 负控正文 / 行为门前提 / OpenSpec 移交）里，负控正文这条本轮已附完整输出——请据附录 A/B 实际核验 N1/N2 是否真打在点名断言上；其余三条作者维持原声明（验收单 §10），边界画得是否仍然诚实？
4. 综合本轮 HEAD：还有没有 BLOCKER / HIGH 级的新发现？

## 四 输出格式

- **BLOCKER / HIGH / MEDIUM / LOW**，每条 `file:line` + 一句话结论 + 你读到的证据。
- 单列 **「已核实成立的整改」**（逐条：你 round-1 的哪条意见、被哪段整改解决、你核到了什么）。
- 信息不足的明说「未核实」。

## 五 边界

- 只读；不连库；不跑测试/脚本；不评 G3-5 键化（U9-C 面）；不评 pyright 存量（U1/U2 面）；不评 `test_mastery_fusion` 那条主干既有红（U11-C 面）。
- 不要求也不需要任何攻击性内容；本轮只针对上述读取面内整改的正确性与诚实性。
