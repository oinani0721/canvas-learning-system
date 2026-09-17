# Codex 复核 — CARD-NEO4J-REPLAY-WIRE（BATCH-2026-09-11-第十四批 / 车道 T6 / **round-9**）

## ① 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
分支 `card/t6-neo4j`。**本轮审查 SHA = `97bf3672`（当前 HEAD）**。

轮次：r1..r7 略（见 r8 存档），r8 审 `a66316df` 得 **B0/H3/M3**，其中你自行分类为：
**本卡修复遗漏 1（HIGH）/ 既有算法应归独立重写卡 1（HIGH）/ 既知移交项 4（HIGH 1 + MEDIUM 3）**。
本轮绑整改后的 `97bf3672`。审查期间车道**不改任何代码**。

⚠️ 已远超卡文 5 轮上限，如实说明：车道两次按 D-15 停车并交主 session，均因流程判定「(n) 未闭环」而继续整改至 `HIGH = 0`。**主 session 仍可裁定止于任一版本。**

**最小读取面（只读这些）**：

1. **本轮整改 diff**：`git diff a66316df 97bf3672 -- . ':(exclude)_bmad-output'`（2 文件、61 增 19 删）
2. `backend/app/services/fallback_sync_service.py` 全文（重点：文件头 `_PROGRESS_VERSION` 注释、`_sync_all_fallbacks_locked` 的汇总段、三个 `_sync_*` 的全部 `return` 路径）
3. `backend/app/main.py:378-470`（启动汇总段）
4. r8 存档：`_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-WIRE-r8.md`

## ② 作者自述（请独立核对，不要采信）

- **r8 HIGH-1（本卡修复遗漏：成功条件变了但旧游标仍被接受）** → 已改：`_PROGRESS_VERSION` 由 `"split-lf+contiguous"` 升为 `"split-lf+contiguous+history"`，旧标记一律回退 0。常量注释补上「变更条件有**三类**：切行方式 / 游标推进规则 / **成功判定**」——第三类正是这次漏掉的。实测：带旧标记 `index=50` ⇒ 实际尝试 51 条、`c0` 在内。
- **r8 MEDIUM-4（finalize 保留了条目却报 pending=0）** → 已改：两条链统一为 `pending = len(merged)`（文件里实际剩余，含期间新追加的）；提前返回路径补 `error` 键 + `pending = -1` 表「数不出来」。
- **上一条引入的连锁（作者自查）**：`-1` 哨兵会被 `sum()` 吃进汇总，把「未知」变成负数，比原来报 0 更糟。两处消费点（本服务自身汇总 + `main.py` 启动汇总）同步改为跳过负值并打 `"≥N (+链名 unknown)"`。`grep` 确认无第三处消费点。
- 两个子方法返回标注由 `Dict[str, int]` 改为 `Dict[str, Any]`（`error` 是 `str`），pyright 回 `0 errors`。

**未改、继续移交**：r8 的「缺 timestamp 覆盖新评分」（你已归为**既有算法应归独立重写卡**）、G2-2 跨 vault、模块锁跨事件循环、错误 vault 归属门可假绿。

## ③ 问题（按重要性排序）

⓪ **本轮两条修复是否各自关上了那条路径，有没有引入新问题？** 具体：(a) `-1` 哨兵是否还有未被处理的消费点（含 `main.py`、日志、以及任何把 stats 直接序列化给外部的地方，例如 `traces.py` 的管理端点响应）；(b) `pending = len(merged)` 的新口径在「全部成功且无追加」时是否仍为 0；(c) 版本号升级后，`canvas_events` / `learning_memories` 的历史 checkpoint 一并回退是否有副作用。

① **管理端点 `POST /api/v1/traces/replay-fallbacks` 现在会把 `pending: -1` 与 `error: str` 原样返回给调用方** —— 这是否构成新的契约/信息暴露问题？

② **本卡全量改动面（`310eef31..97bf3672`）是否还有剩余的数据丢失 / 跨 vault 污染 / 门假绿路径？** 请把 HIGH 严格限定在这三类。

③ 请继续在计数汇总中**单独标出**：本卡引入或遗漏的条数 vs 既有算法应归重写卡的条数 vs 既知移交项条数。这是主 session 裁定止血边界的依据。

## ④ 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句复现思路。
措辞请用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。
末尾给计数汇总 + 上述三类分项。

## ⑤ 边界

- 只读审查，不要改任何文件，不要连任何数据库。
- 不评 T6-C 的面；不评 `security.py` / `live_port_guard.py` 本身设计；`openapi.json` 未再生是刻意的。
