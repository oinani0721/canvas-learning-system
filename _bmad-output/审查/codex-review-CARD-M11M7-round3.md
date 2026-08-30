# Codex 独立复核存档 — CARD-M11M7 round-3

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-31
> **卡**: BATCH-2026-08-31-第七批 / CARD-M11M7
> **审阅范围**: 只审 round-2 的四条整改（MEDIUM 板级数字抹除 + 组合态 / LOW-1 exit 码 /
> LOW-2 零写承重 / LOW-3 docstring）
>
> ## 裁决与处置
>
> **PARTIAL · BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 2 ·「需再一轮，仍只需短定向复核」**
>
> 三条全部**已修**（下表），按第六批停轮规则（BLOCKER/HIGH → 再一轮；MEDIUM/LOW →
> 登记结案）本轮无 BLOCKER/HIGH ⇒ **本卡在此收口**，整改后未再跑 round-4。
> ⚠ 这意味着**下表三项整改本身没有经过独立复核**——如实声明，不宣称"已终裁清零"。
>
> | 条 | 复核者的实证 | 我的处置 |
> |---|---|---|
> | **MEDIUM** 冲突态仍发布顺序相关的**结构**数字 | 240 块同构板实测：`seeds/derived` 有 **125/240** 块随板序交换（节点被改时 `derived-from` 同时变，role 判定翻转） | ✅ 修：抹除面从「三个 tips 字段」扩到**全部取自本次扫描的数字**，改用**正向白名单** `_TRUSTED_BOARD_KEYS`（新增字段默认被抹掉而非默认泄漏） |
> | **LOW** 非法 SHA 的「一律 exit 2」仍依赖状态 | 「缺板/目标已存在 + 非法 SHA」实测 exit 0（零写，但退出码契约失真） | ✅ 修：形状校验提到 `cmd_create` 最前（参数合法性与 vault 状态无关）；测试扩为 3 种非法 SHA × 5 种状态组合 |
> | **LOW** LOW-2 的零写因果仍假承重 | `good_sha` 取自无竞态内容；竞态那份真 SHA 是 `085eb2e1…944b9`，禁掉冲突门 + 传它 ⇒ `created:true`，写出 1273 bytes | ✅ 修：测试改为先**禁掉冲突门**撞出竞态那份真 SHA 并证明它确实能写出产物，再恢复冲突门用同一份 SHA 重跑 |
>
> ### 复核者确认已通过的部分（摘）
>
> - preview 组合态控制流正确（target+conflict / missing+conflict / 三者同时都含冲突且不渲染）；
> - missing-only / target-only / normal 与整改前 functional predecessor 的 stdout **逐字节相同**；
> - 一致态、单板、空板、幽灵、板内重复、部分重叠：preview stdout 与 create 产物**逐字节相同**；
> - 整改前回放：六个新增/改写实例 **5 FAIL / 1 PASS**（唯一仍绿的正是它点名的 LOW-2）。
>
> ### 诚实声明的证据缺口
>
> 复核者自陈：整改前的生产 blob 未进 Git 对象库，基线按 round-2 源码行重建，
> 功能/hunk 一致但**原 blob 身份严格标为 UNVERIFIABLE**。

---

## 裁决

**PARTIAL — BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 2。需要再一轮：是，仍只需短定向复核。**

复核锚点：`card/v2-recapfix`，HEAD `9cf0fb85ed839bb7035d023534fca222a24d6968`。工作树状态与开始时一致。

### 【MEDIUM】冲突态仍发布顺序相关的结构数字

[recap_exam_build.py:157–175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:157) 发布 `members/seeds/derived/listed_in_concepts/ghost_count`；但 [整改函数 :314–333](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:314) 只删除三个 tips 字段。节点修改还可通过 [recap_scan.py:553–604](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:553) 同时改变 role。

实测：

- 真实 CLI、240 块同构板、并发原子切换共享节点的 `tips + derived-from`。
- 正序与逆序都进入冲突拒绝，三个 tips 字段全部消失。
- 但同一板的 `seeds/derived` 有 **125/240** 块发生交换。
- 两板确定性复现：`A,B` 为 A=`1/0`、B=`0/1`；`B,A` 后同一板反转。
- 固定 anchor、按板名规范化完整 JSON 后仍不相等，故不是单纯数组顺序差异。
- 增删尾板、只改 anchor 本身未产生额外差异；反转扫描顺序即可复现泄漏。

现有竞态只增加 tip（[测试 :2386–2414](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/skills/test_g5_9_recap_exam.py:2386)），所谓逐字节锁实际只比较按板名投影后的 `boards + reason`（[测试 :2448–2465](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/skills/test_g5_9_recap_exam.py:2448)），因此是假绿门；本项未闭合。

### 【LOW】非法 SHA 的“一律 exit 2”仍依赖状态

[cmd_create :900–928](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:900) 仍先处理 missing/target；SHA 形状校验到 [937–941](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:937) 才执行。

空串、`NOTHEX`、64 位大写三种输入：

- fresh normal、纯 conflict：全部 `exit 2`、lstat/字节快照全等。
- target、missing、target+conflict、missing+conflict、三者同时：全部 `exit 0`，但零写。

因此纯冲突修好了，但既有“非法形状一律 exit 2”契约仍未成立。新增测试 [2526–2539](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/skills/test_g5_9_recap_exam.py:2526) 只锁 fresh-target 的纯冲突态。

### 【LOW】LOW-2 的零写因果仍是假承重

[测试 :2506–2523](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/backend/tests/skills/test_g5_9_recap_exam.py:2506) 的 `good_sha` 来自无竞态内容，不是竞态下将被渲染的内容：

- control SHA：`8931d5bd…3b716`，对照创建成功。
- 禁用 [冲突门 :942–952](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:942) 后，同一 SHA 仍由 [SHA mismatch :953–972](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:953) 拒绝，零写。
- 真正的 raced SHA 为 `085eb2e1…944b9`；禁用冲突门并传该 SHA，实测 `created:true`，写出 1273 bytes。

整条测试会因拒绝文案断言而红，但“零写只由冲突门保证”的子结论仍未承重。

## 已通过

- Preview 组合态控制流 [823–890](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:823) 正确：target+conflict、missing+conflict、三者同时都包含冲突且不渲染。
- missing-only、target-only、normal 与整改前 functional predecessor 的原始 stdout 逐字节相同。
- `_cross_board_totals` 正确跳过缺板（[205–208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:205)）；docstring [193–199](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:193) 已改正。
- 整改前回放：六个新增/改写实例为 **5 FAIL / 1 PASS**；唯一仍绿的是 LOW-2 零写测试。
- 一致态、单板、空板、幽灵、板内重复、部分重叠：preview stdout 与 create 产物均逐字节相同。
- 两个目标测试文件：**249 passed**；`git diff --check` 通过。

限制：整改前生产 blob 未进入 Git；基线按 round-2 精确源码行及 numstat 重建，功能/hunk 一致，但原 blob 身份严格标为 **UNVERIFIABLE**。


