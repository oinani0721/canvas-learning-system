# 独立复核：CARD-RED-TRIAGE（第十二批 Y6-C · tests/unit 红基线 247 条分诊）

## 一 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene`

后端 `tests/unit` 有 **247 个测试一直是红的**（历史欠账）。本卡把它们逐条贴标签，
分清「测试自己过时/写错」与「实现真的回归」，据此产出下一批的修复卡草案。
**本卡零修复、一行代码未改**（用户 2026-09-05 D-10 裁定：一张定性卡）。
这些分类结论**直接决定下一批 8 张卡的走向**，所以值得独立复核一次。

**你的读取面（写死）**：

| 文件 | 用途 |
|---|---|
| `_bmad-output/审查/2026-09-05-第十二批-tests-unit-红基线分诊-247.md` | 分诊表（247 行） |
| `_bmad-output/审查/2026-09-05-第十二批-RED-第十三批卡草案.md` | 8 张卡草案 |
| `.../feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b12/unit-red-baseline-03ac8bf8.txt` | 基线文件（分母） |
| `_bmad-output/审查/evidence-red-triage/unit-run-open-20260906T104910.txt` | 开工运行日志（3.9 MB，**用 grep 取块，别整篇读**） |
| `_bmad-output/审查/evidence-red-triage/独立核实-*.md` | 作者本人对根因锚的交叉验证 |
| `backend/app/security.py:95-150` | A1-auth / A2 的根因锚 |
| `backend/app/services/memory_service.py:273-286` / `:360-380` | B 的根因锚 |
| `backend/app/config.py:274-298` / `:474-480` | C2 / C1 的根因锚 |
| `backend/app/services/supplementary_reranker.py:60-70` / `:195-202` | C2 的根因锚 |
| `backend/tests/unit/test_agent_templates_smoke.py:22-42` | E 的根因锚 |

日志里的失败块头形态是 `_+ <Class.method> _+`，**下划线数量随名字长度变，可能只有 1 个**
（这一点坑过本卡的提取器，见下）。

## 二 作者自述，请独立核对（不要默认成立）

1. **分母 247**（FAILED 209 / ERROR 38 / 63 文件）。复核报告里的「298 / 289」是
   **含 42 行日志噪音的行数**，不是分母。开工目录级与基线的 nodeid diff **为空**。
2. **卡文六类假设全部复算对上**：A1 41 / A2 9 / B 41 / C1 49 / C2 24 / E 9 / 残余 74 = 247。
3. **⛔ A1 必须拆成两张卡**（本卡最重要的结构性结论）：
   - `A1-auth` **31 条**（`test_chat_endpoint` 16 / `test_study_question_deep_mode` 8 /
     `test_enrich_context_vault_isolation` 7），失败身份 503×29 + KeyError×2，
     日志里有 `security.py:126` 的拒因原文；
   - `A1-sentinel` **10 条**（`test_startup_health_check` 6 / `test_health_detailed` 3 /
     `test_kg_health` 1），失败身份是 **W4 端口门哨兵**（`live Neo4j port connect attempted`），
     **与 auth 无关** —— `system.py:28` 的 router 没有 router 级鉴权，请求走不到 auth
     就先连了 7691。再加从残余改归的 2 条，共 **12 条**。
4. **两维度设计**：「失败身份」（技术上怎么红的）与「类别」（为什么红）是两列，
   一条的两者可以不同。实例：`test_chat_endpoint.py:274` 失败身份是 `KeyError: 'budget'`，
   但日志里紧跟 `"status": 503` ⇒ 根因是 auth。
5. **A2 的嫌疑 commit 被更正**：3 条 `assert 500 == 503` 红在**配置层**
   （`config.py:286-298 validate_security_defaults` 抛 ValidationError → 中间件兜成 500），
   嫌疑 commit 是 **`f718d040`** 而非卡文点名的 `c9bb6c9a`；
   另 6 条 `test_sync_exception_classification` **改类 A2 → A1-auth**
   （空 key 是「让 auth 放行」的手段，不是被断言的负控对象；
   真负控那三条**本次全部 PASSED、不在红基线里**）。
6. **B 类 38 条 ERROR 是有意 fail-closed 设计的副作用**，不是 bug ——
   `memory_service.py:369-373` 的注释自己写明「派生分支对污染桶抛
   `VaultScopeUnresolved` ⇒ 配置断裂会说话」。
7. **C1 的 49 条须按三子类分开**：引用已删 API（28）/ 桩值 vs 断言自相矛盾
   （`test_story_38_6` 补了本地桩 `=0.5` 却仍 `assert >= 2.0` ⇒ **恒红**）/
   锁被废弃契约（`test_story_38_4` 锁 `default is True`，而 `config.py:477` 已
   `default=False` + `[DEPRECATED]`）。
8. **失败身份的提取器被自己坑过两次**（已修，如实登记）：
   ① 块头正则写 `_{4,}` ⇒ 静默漏 61/247 条；
   ② HTTP 状态码判据用裸 `\b503\b` ⇒ 把一条时间戳断言误判成 403。
   最终版 247 条全部找到 traceback 块，14 条未提到 `test file:line`。

## 三 按重要性排序的问题

1. **每类抽 3 条**，核对表里的「测试 file:line」与「失败身份」是否**对得上日志**。
   有没有哪条的失败身份是读代码推断的、日志里其实找不到支撑？
2. **A1 拆成两类是否成立？** 那 12 条 `A1-sentinel` 的失败身份是否真的是哨兵而非 auth？
   从残余改归的那 2 条（`test_mock_degradation_transparency` /
   `test_review_mode_support`）改得对吗？
   ⚠️ 附带请判断：本卡另一处记录说 W4 哨兵的归属**随时序漂移**
   （同一批红在两轮之间发生过「一增一减」，两条正文都是该哨兵）——
   这会不会动摇「这 12 条稳定属于 sentinel 类」这个结论？
3. **「真实现回归」是否都有嫌疑 sha + 最小复现描述？**
   反过来：有没有哪条被默认成「测试过时」而其实该查回归的？
   （卡文硬约束：残余里凡被测 API 仍在生产代码里的，默认先按「真实现回归/新」写。）
4. **草案的三条硬约束是否在场**，且每张卡的裁判是 **nodeid diff** 而不是 `wc -l`？
   - RED-A1：opt-in `authed_client` fixture，**禁** autouse / `os.environ` 全局注入 key
   - RED-B：fixture 的 vault id 必须**纯虚构**，禁取 `.env` 的 ACTIVE_VAULT，禁 tests/unit 级 autouse
   - RED-C1：无替代覆盖不许删；改 `xfail(strict=True)` + reason 作跨卡交接
5. **纯分析门与收工 diff 是否成立**（本卡声称一行代码未改）？

## 四 输出格式

按严重度分级（BLOCKER / HIGH / MEDIUM / LOW），每条给：
- 一句话结论
- 具体 `文件:行` 或 nodeid
- 建议的最小改动

**只读判定不了的写「未验证」并说明缺什么** —— 不要猜。
最后给总评：这份分诊的分类结论，能不能作为下一批 8 张卡的依据。

## 五 边界

- **只读**。不改任何文件，不连任何数据库端口，不跑 pytest。
- **不评修法**、不要求给出补丁 —— 修复是下一批的事，本卡只做定性。
- 本卡零代码改动是硬边界，不要建议「顺手改一下」。
