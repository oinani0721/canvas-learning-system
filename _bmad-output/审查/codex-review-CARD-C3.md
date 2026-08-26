结论：`FAIL / NOT READY`。当前 CARD-C3 修复了最小 `state:0` 枚举异常，但存在 1 个可复现 BLOCKER；绿色测试不足以证明 legacy 卡可正常复习。

### BLOCKER

1. Legacy New 只迁移了状态，未迁移其参数哨兵，真实复习仍会崩溃。

   [fsrs_manager.py:323–338](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/lib/memory/temporal/fsrs_manager.py:323) 将 `state=0` 改为 `Learning`，却原样保留 `stability/difficulty=0.0`。[同文件:147–153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/lib/memory/temporal/fsrs_manager.py:147) 的仓库 fallback 和官方 [py-fsrs v3 Card 默认值](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/v3.0.0/src/fsrs/models.py) 都会生成这种旧格式。

   实测：

   ```text
   {"state":0,"stability":0.0,"difficulty":0.0,"reps":0,"lapses":0}
   -> deserialize: Learning(1), stability=0.0, difficulty=0.0
   -> real fsrs 6.3.1 review_card(Good)
   -> ZeroDivisionError: zero to a negative power
   ```

   原因是 [v6 Learning 分支](https://github.com/open-spaced-repetition/py-fsrs/blob/v6.3.1/fsrs/scheduler.py) 仅在参数为 `None` 时初始化新卡；`0.0` 会进入后续稳定度计算。真实 [review_service.py:975–1057](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:975) 会吞掉该异常并静默返回 `algorithm="ebbinghaus-fallback"`。读写后还会形成 `state=1 + zero parameters`，丢失 legacy 标记但保留毒化参数。

   修复建议：对符合旧 New 形状的 `state=0` 同步归一化 `stability/difficulty: 0.0→None`、`step→0`；为矛盾的正 `reps/stability/last_review` 制定显式告警或拒绝策略，不要猜成 Review。验收必须走 `deserialize → real Scheduler.review_card → serialize` 全链。

### HIGH

1. 完整 legacy frontmatter 仍会在 bridge 真实路径崩溃。

   [fsrs_bridge.py:73–80](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/canvas-vault/.claude/scripts/fsrs_bridge.py:73) 将 YAML `null` 保留为字符串；[同文件:89–105](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/canvas-vault/.claude/scripts/fsrs_bridge.py:89) 只映射 state 后直接 `int()`/`float()`。

   - companion 字段为 `null`：`ValueError: invalid literal for int()`
   - companion 字段为 `0`：真实调度器出现上述 `ZeroDivisionError`

   [test_fsrs_bridge.py:90–100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/tests/regression/test_fsrs_bridge.py:90) 只提供 `due + state`，绕开了这些字段；未跟踪测试的 bridge 用例又直接传 dict。

   修复建议：建立完整 state0 迁移分支，归一化 `null`/zero 字段，并增加完整 frontmatter 和 stdin CLI 回归。

2. `FSRS_AVAILABLE=False` 分支仍持续制造和写出 state0。

   [fsrs_manager.py:38–42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/lib/memory/temporal/fsrs_manager.py:38)、[145–153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/lib/memory/temporal/fsrs_manager.py:145)、[294–297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/lib/memory/temporal/fsrs_manager.py:294)、[347–351](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/lib/memory/temporal/fsrs_manager.py:347)、[382–394](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/lib/memory/temporal/fsrs_manager.py:382) 均保留 0。

   系统 Python 无 fsrs 时实测：create、读写 roundtrip、`card_to_state` 内外层全部输出 0。该分支并非死码：[review_service.py:81–101](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:81) 会把 wrapper 导入成功误认为库可用，[工厂:227–235](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:227) 随后实例化 fallback manager。

   修复建议：缺库时最好 fail closed 并返回 `None`，直接走 Ebbinghaus；若保留 fallback，则所有持久化边界必须共享同一迁移规则并增加隔离缺库测试。

### MEDIUM

1. `CardState` 公共序列器仍自产 0。

   [fsrs_manager.py:55–90](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/lib/memory/temporal/fsrs_manager.py:55) 默认 state0，`to_dict()` 原样写出，`from_dict()` 缠失或输入0也不迁移。当前无热生产调用者，所以不是现时崩溃入口；但它违反测试所宣称的“任何新写入不得再产出0”。

   修复建议：默认/legacy 归一为1，或用 `Optional[int]=None` 明确表示“无卡”。

2. 服务/API 的输出契约仍允许非法 0。

   [review_service.py:872–874](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:872)、[1021–1027](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:1021)、[2195–2202](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/services/review_service.py:2195) 均以0兜底；[schemas.py:923–927](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/app/models/schemas.py:923) 仍公开描述 `0=New`，且不限制1–3。

   修复建议：实际卡缺失/非法 state 应拒绝或统一规范化；schema 限制 `ge=1, le=3`，同步更新 OpenAPI 与旧测试。

3. 回归夹具没有覆盖真实 legacy/fallback 故障。

   [test_fsrs_legacy_state_zero.py:59–80](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/tests/regression/test_fsrs_legacy_state_zero.py:59) 使用 `state0 + stability3.5 + reps2 + last_review` 的矛盾组合，并停在反序列化；[105–116](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/tests/regression/test_fsrs_legacy_state_zero.py:105) 用 `_HeadlessCard`，不是实际 `FSRS_AVAILABLE=False` 分支。

   修复建议：加入官方 v3/仓库 fallback 的 canonical payload、一次真实 review、真实缺库隔离进程，以及完整 frontmatter CLI 用例。

### LOW

1. “fsrs v6 删除 New”版本归因不准确。

   [fsrs_manager.py:303–307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/backend/lib/memory/temporal/fsrs_manager.py:303)、[fsrs_bridge.py:91–92](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l2-fsrs-debt/canvas-vault/.claude/scripts/fsrs_bridge.py:91) 及新测试均如此表述。官方 v3 尚有 New(0)，但 [v4 文档](https://raw.githubusercontent.com/open-spaced-repetition/py-fsrs/v4.0.0/README.md) 和 [v5.1.3 源码](https://github.com/open-spaced-repetition/py-fsrs/blob/v5.1.3/fsrs/fsrs.py) 已只有三态。

   修复建议：改成“legacy py-fsrs v3/其他实现可能保存 New(0)；当前 py-fsrs 6.x 不接受0”。

### 五个审查维度

| 维度 | 判定 | 结论 |
|---|---|---|
| 1. 0→1 语义 | PARTIAL | 基础映射无问题：New 应映射 Learning；合法1/2/3未改变。仅凭 reps/stability 推断 Review 不可靠。字段级迁移存在 BLOCKER。 |
| 2. A1 None/null | PASS | 无问题：manager docstring、bridge 注释和测试模块均显式标注 state 例外；A1 契约测试通过。若新增 `0.0→None`，必须补充说明这一字段级例外。 |
| 3. 入口 census | FAIL | 真实 v6 JSON 读入口均汇聚到 `deserialize_card`，无额外遗漏；但 fallback、CardState、服务/API 写侧仍可产出0。`ConceptState.fsrs_state=0` 是“无 card_data”的独立 sentinel，不宜在 C3 中盲改为1，应另卡迁为 `None`。 |
| 4. 测试真实性 | PARTIAL | 真实 fsrs 6.3.1、真实 bridge parser 和最小红绿链均无问题；canonical legacy、完整 frontmatter、真实缺库分支未覆盖。 |
| 5. stdlib 入口 | PASS | 无问题：没有模块级 fsrs import；类导入仍位于 `review()`，原有 `_ensure_fsrs()` 仅运行时探测。系统 Python 导入模块后 `fsrs` 未加载。 |

验证：当前目标测试 `25 passed`；扩展 FSRSManager 套件 `55 passed`；`git diff --check` 通过。HEAD 重构的旧入口对最小 state0 确实红，当前最小用例转绿，但上述 hostile payload 仍失败。未运行全套 CI；本会话无 Graphiti/LSP 工具。未修改工作区，也未依赖 `_bmad-output` 下的未跟踪审查/验收文档作为证据。



---

## 处置记录（Claude Code, 2026-08-25）

> 审查结论 FAIL / NOT READY 后按 BLOCKER/HIGH 清零纪律全部处置，裁判套件复跑 68 passed。

| 级别 | 发现 | 处置 |
|---|---|---|
| BLOCKER-1 | 只迁 state 不迁参数哨兵，`{"state":0,"stability":0.0}` 真实复习 ZeroDivisionError | ✅ FIXED — deserialize_card state:0 分支升级为字段级迁移：stability/difficulty 0.0→None（v6 只认 None 为未初始化）；矛盾形状（正 stability/reps/last_review）保留参数 + logger.warning，不猜 Review。新增 canonical legacy 全链测试（deserialize→真实 Scheduler.review_card→serialize）+ 矛盾形状告警测试，均实测走通（review 后 stability 2.3065） |
| HIGH-1 | bridge 完整 legacy frontmatter：伴生字段 null→ValueError / 0→ZeroDivisionError | ✅ FIXED — fsrs_bridge review() state:0 分支新增 `_legacy_param` 哨兵归一（空/null/none/~/0/0.0/不可解析→None），step 兜底 0（Learning 首步）；非 legacy 路径逐字节不变。新增完整 frontmatter（null+0.0 伴生）、矛盾形状（正参数保留）、stdin CLI（re-exec 链）3 个回归用例 |
| HIGH-2 | FSRS_AVAILABLE=False fallback 分支持续制造/写出 state0 | ✅ FIXED（卡内范围）— fallback create_card State.New→State.Learning；serialize/deserialize/card_to_state fallback 路径全部 0→1 映射与兜底；新增屏蔽 fsrs import 的隔离子进程实测用例。fallback 数值参数（0.0）保留：_fallback_review 算术依赖数值而非 None 哨兵，跨界毒性由真实分支读侧迁移拆除。fail-closed（缺库直接 None 走 Ebbinghaus）需动 review_service 工厂 — 档案明令 C3 不碰 review_service，移交未来"静默降级根治"卡 |
| MEDIUM-1 | CardState 默认 state=0 / from_dict 不迁移 | ✅ FIXED — 默认 1；from_dict 0/缺失→1；测试锁定 |
| MEDIUM-2 | review_service/schemas API 层 0 兜底 + "0=New" 描述 | ⏳ 移交 — 超 C3 白名单（review_service 其他区段档案明令不动；schemas 契约改动需 OpenAPI 同步），已列入验收单"已知不修"与后续卡候选。Codex 维度 3 亦确认 ConceptState.fsrs_state=0 是独立哨兵不宜本卡盲改 |
| MEDIUM-3 | 回归夹具缺 canonical legacy / 真实缺库 / 完整 frontmatter | ✅ FIXED — 上述新增用例全覆盖（canonical 全链、隔离子进程、完整 frontmatter、stdin CLI） |
| LOW-1 | "fsrs v6 删除 New" 版本归因不准（v4 起已三态） | ✅ FIXED — 全部措辞改为 "legacy 实现（官方 py-fsrs v3 及本仓库 fallback）会存出 New(0)；py-fsrs 4+/6.x 只有三态" |

附注：处置中发现 fallback serialize_card 不支持 datetime due 的既有缺陷（与 state 无关，fallback create 直出的卡 json.dumps 即崩），超 C3 范围，测试中注明绕过，随 MEDIUM-2 一并列入后续卡候选。
