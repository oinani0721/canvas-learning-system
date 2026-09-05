> ⚠️ 本文件是 CARD-G6-3 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z1-B 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-G6-3]`。车道：复用 `card-x2-g62b`，**前提 Z1-A 已独立 commit 且工作树干净**。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-G6-3 — 重学卡 5 秒可见闭环（端到端时序取证，零产品代码改动）

## 〇 事实
| 事实 | 位置 |
|---|---|
| 依赖全在主干：G6-1 投影按需重建 API + G6-4 节点级明细 = `866778a5`；G6-2 交互复习壳 = `626f3c21`；G6-2b 收口 = `ced0e215` | `git log --grep=CARD-G6-` |
| 自动轮询节奏 `review_app.py:11-14` `clamp(next_due − now, 5s, 60s)`；重学卡 learning step 60s/600s 早已实证；但「答错 → 到期 → UI 5 秒内可见」这条链**从未端到端量过一次** | review_app.py 头部 |
| UI 只有两个 GET 页 + 一个 POST（`/overview/refresh`，review_overview.py:1849）；自动轮询绝不 POST | review_overview.py:938 / :1152 / :1849 |
| A3 launchd 链（skip-done 门 + plist）在主干，本卡不得触碰 | `scripts/daily_review_run.py` + plist |
| 本卡是**取证卡**：不改产品代码，与 Z1-C/D 的渲染面零冲突；放在 Z1-C/D 之前跑 = 拿到改动前的基线 | — |

## 一 完成条件（AND）
- (a) 端到端脚本（真实 py-fsrs 对象、tmp vault fixture、**禁 FakeCard**）：模拟答错 → 等到期 → 断言 UI 数据源 JSON 在 due+5s 内含该卡；连跑 3 次全过，每次实测时延写进 `_bmad-output/审查/evidence-g63/`。
- (b) 轮询节奏契约固化为测试（对现有 JS 沙箱 harness 加测，**不改 JS**）：clamp 下界 5s / 上界 60s / visibilitychange 暂停并回前台立即拉一轮 / 自动轮询绝不 POST refresh——四条各一断言。
- (c) 轮询开销量化：60 分钟窗口的请求次数与 CPU 占用实测记录（不达标只登记，不静默调参）。
- (d) A3 launchd 链回归：skip-done 门不受影响，plist 逐字节未改（sha 前后同）。
- (e) 若实测 due+5s 不可达：如实写进验收单并给「改门（放宽到 N 秒）/ 改实现（缩 clamp 下界）」两案交用户裁，**禁止边做边降标准**。
- (f) 零产品代码：`git diff --stat <Z1-A commit> HEAD -- backend/app/api/v1/endpoints/ canvas-vault/.claude/scripts/` 为空。

## 二 裁判命令
1. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_review_app.py` → 含新增轮询契约断言全绿；node 不可用时 fail-closed 不得 skip。
2. `… $PYTEST -q -p no:cacheprovider tests/regression/test_daily_review_run.py` → 绿，验收单记 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS` 摘要行。
3. E2E 脚本连跑 3 次 rc=0；三次时延与请求计数落 evidence-g63/。
4. (f) 的 `git diff --stat` 为空。

## 三 禁改与隔离
禁改 `review_app.py` / `review_overview.py` 任何产品代码（Z1-C/D 面；需要改轮询参数 → 走 (e) 交裁）；禁改 `fsrs_bridge.py` 评分语义（Z2 面）；禁改 A3 plist 与 `daily_review_run.py` 主流程；禁 FakeCard；live vault 只读；不连 7691/7687；`*.stderr*` 不入库；不改台账；不 push。

## 四 Codex / 验收单
默认**不送 Codex**（取证卡，无产品代码）；若 (e) 触发需改实现则由 Z1-C 一并送审。验收单 `…/验收单/UAT-CARD-G6-3-<日期>.md`：DoD-3 双段；4-B「答错的卡几秒后会自己出现在复习页上，不用刷新」+ felt-sense；「本卡未证明什么」必填：未测万节点规模、未测真实 Obsidian 客户端；「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100；不 push。**commit 后同车道继续 Z1-C。**
