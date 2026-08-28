结论：**需整改，当前不可验收**。未发现第二套事件账或既有生产写路径净修改，但存在 1 项 BLOCKER 及多项 HIGH 契约缺陷。

审查绑定：WT `card/s3-events`，HEAD `37387a8662e9dd646fad5628841679d777cb7eae`；最终复核 SHA-256：D0 `cca271887d6c…4bed`、schema `013b7746a659…065`、validator `4c9842951095…570`、test `d0735866cbcc…678`。

### a) 文档锚点与真实代码：HIGH / PARTIAL

- **PASS**：以下锚点均准确：

  - [learning_event_log.py:31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/services/learning_event_log.py:31) 的版本、`:35-47` 九类白名单、`:52-56` 账本路径、`:59-105` 追加实现。
  - backend 五调用点：[tips.py:565](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/api/v1/endpoints/tips.py:565)、[memory.py:815](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/api/v1/endpoints/memory.py:815)、[errors.py:198/259](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/api/v1/endpoints/errors.py:198)、[conversation_distiller.py:445](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/services/conversation_distiller.py:445)。
  - vault 三写点：[quiz-answer:324](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/canvas-vault/.claude/skills/quiz-answer/SKILL.md:324)、[start-exam-board:424](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/canvas-vault/.claude/skills/start-exam-board/SKILL.md:424)、[ai-linked-doc:189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/canvas-vault/.claude/skills/ai-linked-doc/SKILL.md:189)。全仓普查确为 5+3。
  - [CLAUDE.md:135](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CLAUDE.md:135) 与 [architecture.md:79](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/architecture.md:79) 引用在位。

- **HIGH**：[schema:25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:25) 声称写失败不阻断主链，但 `append_event()` 将重复与 IO 故障都折叠为 `False`；[tips.py:572-578](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/api/v1/endpoints/tips.py:572) 对任意 `False` 立即阻断 callout 管道并误报 duplicate。真实入口复现返回 `accepted=False`。

- **HIGH**：[schema:40-41](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:40) 要求 tz-aware，但 [CalloutDirectRequest](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/api/v1/endpoints/tips.py:510) 接受 naive `added_at`，`:570` 可写出无时区 `effective_at`，随后被校验器拒绝。

- **LOW**：schema `:26` 把 skill 默认 `json.dumps` 说成紧凑分隔符；实际 skill/backend 都使用带空格的默认 separators。D0 `:3` 引用的 v2 总账也不在当前 HEAD，仅存在于后继提交 `5b9c00cf`。

### b) 校验器与 §三/§八：HIGH / FAIL

- **HIGH**：未知版本没有真正“跳过”。[schema:13/105](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:105) 要求 WARN、不判错；但 [validator:135-153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:135) 先按 v1 形状校验。v2 新形状实测同时产生 WARN 和缺字段/多字段 FAIL，最终 exit 1。

- **HIGH**：[json.loads](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:129) 默认接受非标准 JSON `NaN`；payload 含 NaN 实测零问题、判 PASS。

- **MEDIUM**：重复 JSON member 被 last-wins 吞掉；非法 UTF-8 触发未捕获 `UnicodeDecodeError` traceback；`datetime.fromisoformat` 接受非 ISO 的 `Q` 分隔符，又拒绝部分合法 ISO ordinal 日期。

- **PASS**：`Z` 与显式偏移通过；naive 时间拒绝；顶层 `event_version=true` 不会伪装成 int；解析后的重复 `event_id`、截断行、空行、非 object 均正确 FAIL。

### c) 契约测试锁漂移：HIGH / PARTIAL

- **PASS**：EVENT_VERSION、EVENT_TYPES 均有字面冻结，再与校验器复制份比较，真实锁住同步漂移。

- **PASS，间接锁**：7 键没有单独字面集合断言，但 `valid.jsonl`/`real_shapes.jsonl` 固定七键；生产与校验器同步增加第八键仍会让这些 fixture 因缺字段翻红，因此不是完全失锁。

- **HIGH**：“8 个真实写点 1:1”只是手工 fixture，[测试:180-184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:180) 没有执行真实 producer；因此未发现上述 tips naive 时间入口。

- **HIGH**：新契约文件单跑实际为 **13 passed + 1 skipped**；只有与既有 `test_learning_event_log.py` 六条合跑才是 **19 passed + 1 skipped**。[CURRENT_TASK.md:9](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:9) 与 [UAT:32-33](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:32) 把 19 归给单一新文件，证据口径失真。

### d) 生产行为与 diff：HIGH / PARTIAL

- **PASS**：八个既有生产写点及 `learning_event_log.py` 对 HEAD 的 diff 全空；后者工作树与 HEAD blob 均为 `28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`。未发现第二套账本或新增生产调用方。

- **HIGH**：当前整个 worktree 不是 G3-1 纯净 diff。审查期间并发混入 G3-4 的两个 requirements 修改、golden generator/manifest/vectors/test/evidence 等；没有独立 commit 或 patch manifest 可把 G3-1 exact bytes 单独切出。因此“git diff 只含指定 G3-1 文件”当前不能判 PASS。

- **PASS（当前现网）**：现网 22 行、恰好七键、零重复 ID、时间戳全 aware、覆盖六类事件。当前 validator exit 0；账本前后 SHA-256 均为 `2a18023e71a046db8a8c52e098cd48bd0b9898596e4ea3024e18695827796cb6`。

- **MEDIUM / PARTIAL（历史存证）**：现有存证文本未绑定 HEAD、validator/fixture SHA、Python 版本和完整命令；只能证明当前可以复现，不能独立证明存证时使用了哪些 exact bytes。

### e) §六与 G3-2：BLOCKER / FAIL

- **BLOCKER**：G3-2 v2 卡（commit `5b9c00cf`，总账 v2 `:459-463`）同时要求：

  1. 事件先落账再更新 frontmatter；
  2. 中断后“事件已在、frontmatter 未推进”可恢复；
  3. 重放相同 ID 不二次推进。

  [schema:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:91) 只规定顺序，没有 applied/pending 状态、frontmatter revision/CAS 或恢复判据。崩溃后无法区分“事件已应用”与“事件仅落账”；跳过会永久漏推进，重放会可能二次推进。再叠加 `False=重复或IO失败`，当前契约无法安全实现 G3-2。

- **HIGH**：G3-2 要求截断尾行不阻塞后续追加，但现有写点直接 `"a"` 追加；尾部无 LF 时新 JSON 会粘到坏行后，后续事件仍不可解析。

- **HIGH**：§六把 rating 定为 int，但 payload `rating: true` 当前校验器仍 PASS；历史兼容与“新行 REQUIRED”之间也没有机械可判别标记。FSRS bridge 降级时仍继续评分，却没有真实调度结果可诚实填写 library/params hash。

- **MEDIUM**：这些 hash 声称与 G3-4 manifest 同源，但 G3-2 形式依赖仍只有 G3-1，应补显式依赖或冻结降级口径。

最小整改门：先冻结 G3-2 的追加结果状态机、崩溃恢复/截断尾行规则和降级 payload；再修 validator 的未知版本早跳过、严格 JSON/时间词法/UTF-8 通道，并用真实 producer 测试替代纯手工 shapes；最后纠正测试计数和 exact-byte 存证、隔离 G3-1 patch。

审查全程未修改 workspace，也未输出现网账本正文。Graphiti MCP 本会话未暴露，因此无法写入 `[Code-Review]`；只运行了目标测试与只读机械校验，未宣称全量 CI 状态。


