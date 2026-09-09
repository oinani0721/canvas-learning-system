# 独立审查请求 — CARD-RED-NEW（BATCH-2026-09-07-第十三批 / 车道 U11-C）

## 一 背景 + 最小读取面（请只读下列内容，不要扩大读取面）

本卡处理 `backend/tests/unit` 既有红基线（202 nodeid @ `da690bf8`）里被分诊为「新」类的 **8 条**。任务不是「把红改绿」，而是**逐条给出「回归 / 契约演进 / 测试写错」三选一裁定 + 依据（须含一条运行期或 git 证据）**，再据裁定分派处置。

硬约束（卡文原文）：**不得默认「测试写错」就改断言**；其中 `test_multimodal_path_security.py::TestValidateSafePath::test_path_traversal_windows_style`（失败身份 `DID NOT RAISE`）是**安全面**，其断言一个字都不许改，实现只能更严、不能更松。

请读（仓库根 = 本工作树根）：

1. 本卡代码 diff：`git diff --no-color b17b710d HEAD -- . ':(exclude)_bmad-output'`
2. 裁定表：`_bmad-output/审查/evidence-red-new/new-verdicts.md`
3. RED 分派中本卡 8 条的出处：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b13/red-align-da690bf8.md` 的 `:204-215`
4. 生产判定行（只读这些区间）：
   - `backend/app/services/calibration_tracker.py:36-92,185-195`
   - `backend/app/services/difficulty_matcher.py:36-44,370-384`
   - `backend/app/services/event_bus.py:50-56,244-305`
   - `backend/app/services/canvas_service.py:282-296,888-902`
   - `backend/app/services/mastery_fusion.py:145-170`
   - `backend/app/services/multimodal_service.py:490-530`，含两个调用方 `:560-580` 与 `:715-725`
5. 证据存档（全在 `_bmad-output/审查/evidence-red-new/`）：
   - `identity-open-*.txt`（开工 8 条失败身份原文）
   - `line-history.txt` / `line-history-detail.txt`（判定行与断言行的 `git log -L` 变更史）
   - `canvas-callargs-*.txt`（#3 的 `call_args_list` 取证）
   - `canvas-pre14f0412d-*.txt`（#3 的反证：还原旧等待写法后 5/5 PASSED）
   - `posix-path-semantics.txt`（#8 的 POSIX 路径语义实测）
   - `sec-before-RED-*.txt` / `sec-after-GREEN-*.txt` / `sec-samefile-*.txt` / `sec-consumers-*.txt`（#8 先红后绿 + 未误拒）
   - `negctl-eventbus-*.txt`（#5/#6 负控 + 还原 shasum）
   - `empty-window-consumers.txt`（#4 消费方证据）
   - `red-diff-*.txt`（目录级 nodeid diff）
   - `format-gate-bypass-evidence.txt`（format 门的带存档跳过依据）

## 二 作者自述，请独立核对（不要采信，请自行验证）

1. **8 条裁定 = 测试写错 7 / 防御深度不足 1 / 回归 0 / 契约演进 0。**
2. 作者认为卡文给的「生产与测试同 commit 诞生 ⇒ 不是回归」这条推理**不充分**，已升级为「判定行与断言行的语义自引入后从未变过（`git log -L` 追史）」。请核对：这条升级后的推理在**每一条**上是否真的成立，特别是 #1/#2（断言行另有 `836d0986`）与 #3（生产另有 `14f2d5a5`/`836d0986`）——作者称这些都是纯格式化、语义未变。
3. **#3 是作者主动推翻卡文推定的一条**：卡文说它「诞生即矛盾」，作者实测 `14f0412d`（2026-02-07）把 `await asyncio.sleep(0.1)` 换成 `await wait_for_call(...)` 是实质变更，还原旧写法后 5/5 PASSED ⇒ 它曾经绿过。请核对这个反证的设计是否真的只改了测试等待写法而生产保持不变（单变量），以及结论是否被证据支持。
4. **#8 的断言、`match=` 串、返回值、warning/raise 文案均未改**，只改了判定行使其更严。
5. **#5/#6 的负控**确实让指定判据变红，且同轮 #5 与 `test_tier2_success` 仍绿（作者称这证明负控特异性）。
6. 生产改动**只有一个文件**（`multimodal_service.py`，+10/−1），逐处对得上裁定行，**无任何类型注解改动**。
7. 目录级 nodeid diff 的 `>` 行为零。
8. `ruff format --check` 对 5 个文件报失败，作者称是**存量**（`ruff.toml line-length=120` vs 文件的 black-88 存量排版），并以多重集对照声称本卡**新增 format 债 = 0**。请核对该判据的口径是否成立。

## 三 按重要性排序的问题

1. **#8（安全面，最重要）**：处置是否在**不放宽任何防御**的前提下完成？新判定 `not A or not B` 相比原 `not A` 是否严格只扩大拒绝面？归一化 `str(file_path).replace("\\", "/")` 会不会把**合法**路径误拒——特别是 POSIX 下文件名合法含反斜杠的情形，以及 storage base 自身含反斜杠的情形？返回值仍为 `file_path.resolve()`（未归一化），两个生产调用方 `:565`/`:709`（行号已因本卡改动位移）的落盘行为是否确实不变？作者承认「当前两个调用方上这条路径不可达、收益是前瞻性的」——这个自我限定是否诚实且完整？
2. **#5/#6**：新写法是否**真的**让重试链跑到了断言，而不是换了一种方式的假绿？负控证据指向的是**那一条**判据还是别的失败？`assert call_count >= 2` / `assert bus._stats["outbox_written"] >= 1` 有没有被悄悄放宽？用 `monkeypatch.setattr("app.services.event_bus.TIER2_BASE_DELAY_S", 0.0)` 是否等于改了生产常量（作者称生产源码 `:54 = 2.0` 一字未动）？负控的失败形态是 `wait_condition` 的 `TimeoutError` 而非 `AssertionError`——这是否削弱了负控的说服力？
3. **#3**：`call_args_list` 证据能否分辨「竞态」与「生产根本没发 edge_created」？新断言（`call_args_list` 中存在且**仅一次** `edge_created` 且 `edge_id` 匹配）是否仍能发现「edge_created 从未发出」这一失效？`assert len(edge_calls) == 1` 用 `== 1` 而非 `>= 1`，会不会引入新的脆性？
4. **#4**：改测试而不改生产的选择，消费方证据是否充分？作者称唯一告警面 `health_monitor._check_difficulty_match_rate` 先判 `total_in_window == 0` 因而根本不读 `is_healthy`，内部消费方位于 `_window.append` 之后因而空窗不可达——请独立核对这两条。
5. **#1/#2**：阈值来源是否**既参与计算又被单独断言**（防「期望值与被测量同源」的自证）？有没有把实现的 `<` 改成 `<=` 这类产品语义改动（作者称生产 `calibration_tracker.py` 未改）？内侧正控 `threshold - 0.001` 是否真能证明边界落在阈值上而非整体平移？浮点上 `0.15 - 0.001` 是否稳定落在 WELL 侧？
6. **#7**：新数据 `a=[1,0,1,0]` / `b=[1,1,0,0]` 的 r 是否真的接近 0（请自行算一遍）？`abs(r) < 0.5` 的判据强度有没有被放宽？`test_perfect_negative_correlation`（`:307-312`）是否仍绿？公式是否未动？
7. **越界检查**：有没有顺手改到 U11-A/U11-B 的用例、别的车道地盘（`tests/conftest.py`、`tests/unit/conftest.py`、`tests/support/`）、或任何类型注解？有没有用 `skip`/`xfail` 把红换成静默绿、删用例、或把断言降级为「仅有调用」？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：`file:line` + 一句话复现思路。若某级为空请显式写「无」。不需要给出补丁。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接任何数据库（本卡无真库面）。
- 不评价第十四批的 MOCKFIX / ENVDEP 卡。
- 不需要提供修复补丁，只需指出问题。
