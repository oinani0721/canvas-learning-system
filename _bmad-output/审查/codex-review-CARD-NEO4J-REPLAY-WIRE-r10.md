> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-WIRE round-10
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-WIRE-r10.md)"`
> 审查绑定: `8e3c3fa2a8a4d2063eb9fa8bc65725d4ce2941e4`（= 代码最终 SHA；**终审**：可作为接线卡止血版本交付，未确认还有必须留在本卡内修完的 HIGH）
> 会话头自证（抄 .stderr 第 2/5/9 行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**以本卡“接线卡”的范围论，`8e3c3fa2` 已达到可交付的止血状态：本卡新增／遗漏 HIGH 仍为 0。但 `pending` 尚未处处自洽，r9 MEDIUM-3 不能关闭。**

结论绑定 `8e3c3fa2a8a4d2063eb9fa8bc65725d4ce2941e4`。审查始末实际 HEAD 均为 `881c4941`，仅多文档变更，工作树干净。完成两路独立源码复核与 AST 条件核验；未改文件、未连接数据库、未运行实库门。按指定最小读取面，承接 r9 全卡审查基线，本轮没有重新读取 `310eef31..8e3c3fa2` 的全部历史差分。

1. **HIGH〔既有算法，应归独立重写卡〕— 缺 timestamp 的旧评分仍能覆盖新评分。**  
   [fallback_sync_service.py:609](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:609)，关联 `:636–639、:746、:770–774`。  
   **负控输入：**旧 `score=10` 缺 timestamp，图上已有较新的 `score=90`；重放取得当前时间，通过更新条件覆盖 90。携带真实旧 timestamp 的**对照输入**受到保护。当前机制已复核；“基线已有”的分类依据 r9 存档。

2. **HIGH〔既知 G2-2 移交〕— 暂存记录仍采用当前 vault 归属。**  
   [fallback_sync_service.py:1006](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:1006)，关联 `:1009–1012、:616、:702、:751`。  
   **负控输入：**A 的暂存记录在切到 B 后回灌；归属取当前 ContextVar／active vault，未核对记录来源，仍可能写入 B。

3. **MEDIUM〔既知移交，r9 MEDIUM-3 未闭环〕— 剩余量仍有双向失真。**  
   [fallback_sync_service.py:924](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:924)，关联 `:421–427、:509–520`。  
   **负控输入：**全部重放成功、没有追加，轮转连续三次 `PermissionError`；第三次仍只记 warning、正常返回，原文件完整保留，两链却返回 **`pending=0` 且无 `error`**。新增外层兜底接不到被吞掉的异常。

   **反向负控输入：**轮转已经成功，随后清理旧归档在 `:936` 或 `:952` 抛 `OSError`；外层 `:135/:142` 返回 **`recovered=0,pending=-1,error`**，但活跃暂存文件已经不存在。这是本轮统一改 `-1` 后的过度保守分支。两种情况合并计同一条状态失真，不能据此认定数据删除 HIGH。

4. **MEDIUM〔既知移交〕— 模块锁仍存在跨事件循环复用问题。**  
   [fallback_sync_service.py:84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:84)，关联 `:110`。  
   **负控输入：**同进程 loop A 先通过竞争绑定模块锁，再在 loop B 竞争；保留 r9 的跨循环失败结论。本轮确认锁结构未变，未重复运行锁实验。

5. **MEDIUM〔既知移交〕— 错误非默认 vault 的归属门仍按 r9 保留。**  
   `backend/tests/integration/test_neo4j_replay_wire_t6b.py:429`，证据见 [r9 存档:27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-WIRE-r9.md:27)。  
   **未被拦下的输入：**Concept 与 LEARNED 同属错误组 `vault__other__wrong`，其余数量和字段正确，门没有独立比较预期来源组。本轮测试源码不在允许读取面，**该项及行号沿用 r9，未独立重验**。

对问题⓪，逐个统计返回路径核验如下。行号均指目标版本的 `fallback_sync_service.py`：

| 返回位置 | 条件与结论 |
|---|---|
| failed `281、292` | 文件不存在／空内容 → `0/0`。 |
| failed `289、386` | 初读／finalize 重读失败 → `-1 + error`。 |
| failed `409–413` | 清 checkpoint 失败 → `-1 + error`，旧假零关闭；重读成功时数量可能可知，取值仍偏保守。 |
| failed `427` | 返回 `len(merged)`；轮转吞异常时失真，见第 3 项。 |
| canvas `436、441、448` | 不存在／空内容／解析结果为假值 → `0/0`；最后一项**并非严格限定空列表**。 |
| canvas `445、499` | 捕获到的初读／解析／重读失败 → `-1 + error`。 |
| canvas `520` | 返回 `len(merged)`；同样受轮转吞异常影响。 |
| learning `539、544、552` | 不存在／空内容／`memories` 为假值 → `0/0`。 |
| learning `549、593` | 捕获的初读失败 → `-1 + error`；正常结束 → `pending=failed`。 |
| 外层 `135、142、149–153` | 捕获异常 → `0/-1/error`；成功轮转后的清理失败会过度保守。 |
| 外层 `117、123、126` | 返回 `skipped/reason`，不声称零积压。 |

`learning_memories` 刻意保留源文件，`pending` 表示本轮失败数；全部成功后文件非空而 `pending=0` 属于既定行为。离线计数器则仍采用坏文件计零并 warning 的旧口径，不能当作精确剩余量。

作者“三链初读／解析失败均已变为 `-1`”的说法也过宽：`UnicodeDecodeError` 等普通 `ValueError` 未被全部捕获，会直接抛出，不形成逐链统计；这不是静默零待回灌，也不新增 HIGH。

**r9 LOW-6 已关闭。** [traces.py:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:95) 与 handler docstring 均说明 UNKNOWN、伴随 `error` 及跳过负值。所有显式 `pending=-1` 返回均带 `error`；服务与 `main.py` 汇总的负控 `[-1,2,0]` 均保留“≥2＋未知链”，空字符串 `error` 也能被启动汇总识别。

**计数汇总：BLOCKER 0 / HIGH 2 / MEDIUM 3 / LOW 0。**

| 分类（互斥计数） | 剩余 |
|---|---:|
| 本卡引入或遗漏，扣除以下既知项 | **0；HIGH 0** |
| 既有算法，应归独立重写卡 | **1：HIGH 1** |
| 既知移交，含状态失真残项及同根分支 | **4：HIGH 1、MEDIUM 3** |

**对③的明确回答：可以作为接线卡止血版本交付；未确认还有必须留在本卡内修完的 HIGH。** 这不代表 `pending` 整改全部闭环或全系统 HIGH 清零。实走 **10 轮，超过 5 轮上限**；两次 D-15 停车后继续整改的事实按本轮交接记录保留，主 session 可裁定止于此版。


