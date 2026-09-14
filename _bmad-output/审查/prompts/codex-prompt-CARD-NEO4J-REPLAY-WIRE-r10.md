# Codex 复核 — CARD-NEO4J-REPLAY-WIRE（BATCH-2026-09-11-第十四批 / 车道 T6 / **round-10**）

## ① 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
分支 `card/t6-neo4j`。**本轮审查 SHA = `8e3c3fa2`（当前 HEAD）**。

r9 审 `97bf3672` 的结论：**「本卡新增／遗漏 HIGH 已降为 0」**，分类计数为
**本卡引入或遗漏 1（LOW 1，HIGH 0）/ 既有算法应归独立重写卡 1（HIGH）/ 既知移交 4（HIGH 1 + MEDIUM 3）**。
本轮绑整改后的 `8e3c3fa2`。审查期间车道**不改任何代码**。

⚠️ 已远超卡文 5 轮上限（实走 10 轮），如实登记。车道两次按 D-15 停车并交主 session，均因流程判定「(n) 未闭环」而继续整改。**主 session 仍可裁定止于任一版本。**

**最小读取面（只读这些）**：

1. **本轮整改 diff**：`git diff 97bf3672 8e3c3fa2 -- . ':(exclude)_bmad-output'`（2 文件、34 增 14 删）
2. `backend/app/services/fallback_sync_service.py` 的**全部 `return` 路径**与汇总段
3. `backend/app/api/v1/endpoints/traces.py` 的端点 `description` 与 docstring
4. `backend/app/main.py:378-470`
5. r9 存档：`_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-WIRE-r9.md`

## ② 作者自述（请独立核对，不要采信）

- **r9 LOW-6（端点未解释 `pending=-1`）** → 已改：端点 `description`（对外 OpenAPI 文案）与 handler docstring 都写明「`-1` = UNKNOWN，不是负一条；该链必带 `error`；聚合方必须**跳过负值**而不是求和」。
- **r9 MEDIUM-3（剩余量与失败状态失真）** → 按你列的分支逐条改：
  - 清 checkpoint 失败 ⇒ 文件**未被动过**，剩余是原快照全部而非 `merged` ⇒ 改 `pending=-1` + `error`（这条分支是车道上一轮新写的）。
  - 三链**初读/解析失败**原返回 `{0,0}` 无 `error` ⇒ 改 `-1` + `error`。
  - 外层 `except` 兜底 stats 同改 `pending=-1`（含 `_rotate_file` 抛 `PermissionError` 那条）。
  - finalize 重读失败与清游标失败的**局部日志**不再打 `len(still_pending)`（与 `unknown` 汇总矛盾）。
  - 保留 `pending=0` 的只剩「文件不存在 / 内容为空 / 解析出空列表」——那是真的没有待回灌。
- `_sync_learning_memories` 返回标注改 `Dict[str, Any]`，pyright 回 `0 errors`。

**未改、继续移交**：缺 timestamp 覆盖新评分（你归为既有算法应归重写卡）、G2-2 跨 vault、模块锁跨事件循环、错误 vault 归属门可假绿。

## ③ 问题（按重要性排序）

⓪ **`pending` 口径现在是否处处自洽？** 请逐个 `return` 路径核：是否还有「文件里实际还有条目、却报 `pending=0` 且无 `error`」的分支；以及反过来，是否有「文件确实空了、却报 `-1`」的过度保守分支。

① **本卡全量改动面（`310eef31..8e3c3fa2`）是否还有剩余的数据丢失 / 跨 vault 污染 / 门假绿 HIGH？** 请严格限定在这三类。

② 若 HIGH 仍非 0，请在计数汇总中**继续按三类分项**（本卡引入或遗漏 / 既有算法应归重写卡 / 既知移交），这是主 session 裁定止血边界的唯一依据。

③ 请直接回答：**以本卡「接线卡」的范围论，`8e3c3fa2` 是否已达到可以交付的止血状态？** 若否，请指出还差哪一条**必须**在本卡内修完。

## ④ 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句复现思路。
措辞请用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。
末尾给计数汇总 + 三类分项 + 对问题③的明确回答。

## ⑤ 边界

- 只读审查，不要改任何文件，不要连任何数据库。
- 不评 T6-C 的面；不评 `security.py` / `live_port_guard.py` 本身设计；`openapi.json` 未再生是刻意的。
