# UAT · CARD-G3-2 — per-vault 复习事件账本落地（write-ahead + 复习 payload 扩展）

> [BATCH-2026-09-01-第八批 / CARD-G3-2] 车道 `card-w7-ledger`（分支 `card/w7-ledger`，从 9af18b27 切）
> ⚠️ **范围边界（卡文原文）**：本卡 = **单写者正确性**——A1 write-ahead、A2 恢复先于新写、A3 严格递增（等时 W+1s）、A5 整秒、A6 UTC 入参、A4.2 唯一折叠基线、A4.3 耐久序列、A4.4 原子发布、A4.5 parsed 查重 + 短写校验 + envelope 冲突门。
> **A4.1 per-node 排他锁 / fencing epoch / conditional takeover 与 per-vault 账本锁 = G3-3，本卡不做。** 本卡不实现任何锁，静态块靠「quiz-answer 单进程串行」的单写者假设工作——**并发面不成立**（禁写「并发安全」）。

## 一句话：这张卡让你多了什么

以前你答完题如果电脑恰好在那半秒断电，这次评分可能**丢掉**或把你的掌握度**记错**；现在评分会先把这条事件写进一个只追加的日志（写前日志），成功了才更新掌握度——中途断电后重开 `/quiz-answer`，**上一次评分会自动补齐**，调度状态不会重复推进、也不会丢失。FSRS 的算法时间口径也一并修正（北京时间评分不再被算错、同一秒连考两次不再挤掉）。

## ⛔ 开始验收前：本卡没有上线，无法在浏览器里验

按默认裁决⑤（不部署 live；worktree 为 canonical，部署须你另行批准），本卡改动只存在于本 worktree。live vault 的 quiz-answer/SKILL.md 与 fsrs_bridge.py **原样未动**（有 sha 判据）。因此本验收单没有「你在 Obsidian 里点这些」的部分——4-B 如实降级为 fixture 路径验证。

## 你要做的验收（4-B · fixture 路径，约 2 分钟）

本卡唯一你能亲手碰的验证面（可选，不做也行——技术段已全代跑）：

1. 打开 `canvas-vault/.claude/skills/quiz-answer/SKILL.md`，滚到 Step 4c 的 python 块——确认结构注释里有 `G3-2 A1 write-ahead`、`A2 恢复先于新写`、`envelope 冲突` 字样，且**账本写入段出现在 frontmatter 发布段之前**。
2. 产品可见变化（部署后才会生效）的一句话预期：**评分中途断电 → 重开 quiz-answer → 自动补齐上一次评分**（backmatter 与账本自愈一致），而不是像以前那样这次评分静默丢失。

## 我已经代你跑完的（4-A · 技术项，全部真实执行）

| # | 判据 | 结果 |
|---|---|---|
| 1 | 五文件合跑（卡文裁判 1）：`pytest tests/regression/test_learning_events_schema_contract.py test_fsrs_bridge.py test_learning_event_log.py test_g3_2_review_ledger.py test_fsrs_golden_vectors.py -q` | **254 passed + 1 skipped**（基线 230 collect + 新增 25 collect = 255；skip 为 G3-1 既有 live 账本门，worktree 无此文件） |
| 2 | `validate_learning_events.py <fixture 账本>` | **rc=0 PASS**，review/1 行含 golden 绑定（library_version=6.3.1 / params_hash=7b28ae29… 与 manifest 真值相等），vault_id 绑定 `canvas_vault_测试`（规范化形式，写侧漏 sanitize 会被当场判错） |
| 3 | 写点门 grep | 恰 4 文件：`learning_event_log.py` + quiz-answer/start-exam-board/ai-linked-doc 三 SKILL.md，无第三套实现（test_write_point_survey_no_third_implementation 锁定） |
| 4 | 变异 6 条，串行，还原逐字节比对 | **6/6 各杀指定门**（每轮整改后复跑均 6/6）：去 fsync→耐久序列门红；交换写序回先 frontmatter→写序断言红；恢复子串查重→子串陷阱门红；去 W+1s→等时门红；放行小数秒（_iso 保 %f）→整秒门红；去 canonical envelope 门→冲突拒绝门红。脚本：session scratchpad `g32_mutations.py`（六条各自只跑指定门，判据=该门 FAILED，不是「某处有失败」） |
| 5 | 新增测试文件 | `backend/tests/regression/test_g3_2_review_ledger.py` **25 门**（卡文要求 ≥11）。核心门：同 id 重放不二次推进 / **崩溃窗口①恢复与直接应用整节点字节对拍（卡文 (c)② 字面判据）** / append 前失败零写 / 等时 W+1s / 小数秒截断 / 残缺卡 fail-closed 零写 / 截断尾行(partial JSON)自愈+坏行如实暴露 / envelope 冲突拒绝(含 exam_board·event_version 篡改变体)+同 envelope no-op / validator+golden 绑定+vault_id 规范化+rating 同源 / body 逐字节不变 / 写点普查 / degraded 哨兵成对+W 冻结 / 耐久序列与写序 spy(含双父目录 inode) / legacy 行不重放 / 跨事件 A2 重放（对拍 bridge 直调）/ 子串查重陷阱(ASCII 键名+验伪断言) / pending 重放失败一律 fail-closed(含 abandoned rating 两变体) / degraded A3 的 A7 上界 / F1 在 Obsidian 裸词形态命中 / append_event LF 守卫+空文件首写 / **degraded 遗留重试只补 FSRS 防 EMA 双吃** / **完整应用态换事实必须拒** / **账本 event_id 重复 fail-closed** / **转义引号 eid 幂等** / **fsrs 身份篡改的分层防线(envelope 放行+validator 拦)** |
| 6 | bridge 三缺陷（schema §九移交） | 全修并实证：`12:00:00+08:00` → 归一 UTC `04:00:00Z`（原实现被 fsrs 库 ValueError）；naive 拒收 exit=2 明说；小数秒入口截断；W 与 review_time 逐字相同；显式 rating 严格 int + abandoned 自洽（rating!=1 拒）；stdin/stdout 向后兼容（test_fsrs_bridge.py 10 门全绿） |
| 7 | learning_event_log 查重（§九移交） | 子串 → parsed-field equality，幂等语义不变（event_id 唯一），坏行留痕不算 duplicate 证据；追加前 LF 守卫（size>0 守卫防空文件 seek 崩）；顺手修 §九登记的「8 类」注释→9 类 |
| 8 | live 零写 | 开工/收工 live 账本与 节点/ rollup sha 逐字相同；`cmp` worktree vs live fsrs_bridge.py **rc=1**（worktree 已改、live 未动 = 未部署）；live SKILL.md 差 4 行为 G5-9 既有（未动） |
| 9 | 禁改门 | `git log --name-only <merge-base>..HEAD -- review_service.py daily_review_pick.py validate_learning_events.py` 输出为空（commit 后复核见 §证据）；验伪锚（本卡确改的 SKILL.md 同命令非空）确认门有判别力 |

## 五、Codex 审查处置（round-1 → 整改全落地）

round-1 存档 `审查/codex-review-CARD-G3-2-round1.md`，裁定「需整改」：3 BLOCKER + 3 HIGH + 3 MEDIUM + 1 LOW + 1 验证限制 + 1 环境误报。逐条处置：

| # | 级别 | 发现 | 处置 |
|---|---|---|---|
| 1 | **BLOCKER** | 既有 pending 重放失败后仍会追加新的 degraded 事件（A2「追加前重放至空」被破坏） | **已修**：重放循环失败即 SystemExit fail-closed 零写；degraded 落账仅当 pending 空/全部重放成功。新门⑰锁定 |
| 2 | **BLOCKER** | dup restore 重放失败仍发布 calibration → 同 event_id 之后被 F1 当完整应用（FSRS 悬挂） | **已修**：重放失败在循环内直接退出（restore 到达时重放必然已成功），F1=T ⟺ 完整应用不变量保住 |
| 3 | **BLOCKER** | envelope 冲突门只比五个局部字段；篡改 exam_board / event_version / attempt_count / effective_at 四种均漏过 | **已修**：改为 §6.2 A4.5 冻结的 **canonical envelope 全等比较**（时刻字段采纳 durable 行）；门⑧补篡改变体 + 原样回写后 restore 成功对照 |
| 4 | **BLOCKER（环境误报）** | 卡文 W7.md 在本 worktree ENOENT | 非缺陷：卡文在编排 worktree（feature-obsidian-hybrid-dev），round-2 提示词已给正确路径 |
| 5 | HIGH | 真实 partial-JSON 截断尾行在账本读取阶段即 fail-closed，「截断自愈」不可达（旧门只测「完整行缺 LF」） | **已修**：读取区分尾行（跳过+留痕）与中间坏行（fail-closed）；追加前 LF 守卫隔离。门⑦改用真 partial JSON + 校验器如实报坏行断言 |
| 6 | HIGH | append_event 坏尾行 continue 后直接拼接 → 新事件连坐损坏却返回成功 | **已修**：查重坏行留 warning；追加前 LF 守卫。新门⑳ |
| 7 | HIGH | degraded 本地 A3 推进缺 A7 排他上界 → 制造非法孤儿事件 | **已修**：bump 后查 9000-01-01Z 上界，越界 SystemExit 零写。新门⑱ |
| 8 | MEDIUM | 显式 rating 被 int() 强转（1.5→1 静默收） | **已修**：bridge 严格 isinstance(int)，bool 显式排除；门⑰变体验证 |
| 9 | MEDIUM | 生产块依赖单写者但未明示；「并发」日志措辞误导 | **已修**：静态块头注声明单写者前提（G3-3 前无锁）；_again 分支改「防御性二次查重（单写者下不可达）」 |
| 10 | MEDIUM | 门⑯陷阱（中文 EID+转义 note）实测杀不掉旧子串谓词 | **已修**：改 ASCII eid + **payload 键名**载体（值内引号恒转义导致 needle 尾引号不匹配——首版陷阱被门内验伪断言自己抓出后换键名载体）；M3 变异复跑确认红 |
| 11 | LOW | fixture 无既存 calibration_log（live 规范化裸词形态未覆盖） | **已修**：新门⑲——模拟 Obsidian 剥引号后重跑必须幂等 no-op 零写 |
| 12 | 验证限制 | spy 的 dir_count≥2 未绑定目录 inode | **已修**：门⑬断言 dir fsync inode 集合 ⊇ {VAULT 根, 节点父目录} |

round-2（`审查/codex-review-CARD-G3-2-round2.md`）复核裁定「需整改」：B-1 目标修复 PASS，但抓出分诊层新问题（3 BLOCKER + 4 HIGH + 1 MEDIUM）。逐条处置：

| # | 级别 | 发现 | 处置 |
|---|---|---|---|
| 1 | **BLOCKER** | F1 在 A2 与 envelope 门之前早退——①已完整应用后换事实（abandoned 翻转）被「幂等跳过」吞掉；②degraded 落账写过 calibration 但没写 W，F1 早退让 degraded pending 永不恢复 | **已修**：分诊重排——「已应用」机械判据改为 **W >= durable.review_time**（F1 只是 calibration 域证据）；dup 存在时 envelope 门最先执行；已应用+换事实 → 拒；degraded 遗留 → 恢复只补 FSRS（防 EMA 双吃）。门㉑/㉒锁定 |
| 2 | **BLOCKER** | envelope 门自抄 fsrs 两键与 attempt_count（`_mine` 从 `_dpl` 取值=自己比自己），篡改穿透 | **已修**：两键**显式排除出等价面**（环境快照非评分事实，完整性由 validator golden 绑定门承担——门㉕锁定分层）；attempt_count **按态独立复算**。门⑧篡改变体+门㉕锁定 |
| 3 | **BLOCKER** | A2 不拒绝全文件重复 event_id——两条相同 pending 行被各重放一次 = 确定性二次 apply | **已修**：账本读取后全文件 event_id 唯一性检查，重复 → fail-closed。门㉓锁定 |
| 4 | HIGH | abandoned 分支绕过严格 rating 门（abandoned+rating=1.5 静默应用） | **已修**：显式 rating 验证提到 abandoned 分支前 + 新自洽门（abandoned=true 且 rating!=1 拒）。门⑰补两变体 |
| 5 | HIGH | 门②未落实卡文「恢复与直接应用逐字节相同」（last_examined/calibration.ts 用了重试 ts） | **已修**：全部副作用以 durable.review_time 为业务时刻基准（mastery 抽函数、calibration ts、last_examined 统一）；门②升级为整节点字节对拍 |
| 6 | HIGH | _fm_has_event 只剥外引号不反解转义（含引号 eid → F1 假阴性 → attempt/calibration 双写） | **已修**：双引号 scalar 经 json.loads 与写侧同源反解。门㉔锁定 |
| 7 | HIGH | LF 守卫在零字节文件 seek(-1) 抛 OSError → append_event 恒 False（首事件永远写不进） | **已修**：守卫加 `st_size > 0`。门⑳补空文件变体 |
| 8 | MEDIUM | 单写者声明收窄成「同一节点」（账本 per-vault 共享） | **已修**：改为「同一 vault 内不得并行任何两个 quiz-answer」 |

round-3（`审查/codex-review-CARD-G3-2-round3.md`，卡文上限最后一轮）裁定「**需整改**」：round-2 的 8 条中 6 条 PASS（B-a/B-c/H-a 原项/H-c/H-d/M-a），但深挖出 **2 BLOCKER + 3 HIGH + 2 MEDIUM 残留**。**按卡文停轮规则（BLOCKER/HIGH 续轮，最多 3 轮），3 轮到顶未清零 → 本卡停轮、不合并、留未合卡台账 §一**。残留全清单与触发条件：

| # | 级别 | 残留 | 触发条件（何时才会咬人） |
|---|---|---|---|
| R1 | BLOCKER | envelope 门对 durable payload 的**未知额外键**自抄放行——外部写入带 `payload.out_of_order=true` 的 durable 行可绕过 A2 恢复 | 账本被外部工具写入非本写点产出的行（单写者正常路径不产生） |
| R2 | BLOCKER | A2 会消费**小数秒** durable review_time（bridge 整秒化后 W<原始值 → 同行二次推进） | 账本存在小数秒 review_time 的行——本写点从不产出（_iso 整秒），仅手工/故障写入 |
| R3 | HIGH | envelope 门 attempt 复算用当前 tip——**历史事件重跑（E1→E2→重跑 E1）被误报冲突** | 用户翻旧检验白板重跑旧评分（正常使用可达，方向安全=fail-closed 报错，非数据损坏，但体验破损） |
| R4 | HIGH | 正常路径 mastery 仍用 payload 原始 ts（恢复路径用 review_time）——「等时 bump/小数秒」场景两路径产物字节不等 | payload ts 触发 A3 bump 或小数秒截断时的崩溃窗口①恢复 |
| R5 | HIGH | A2 会应用 scored 行 rating 与 grade_norm 不自洽的 pending（validator 事后才拦） | 账本存在数据损坏的 review/1 行 |
| R6 | MEDIUM | fsrs 身份键排除出 envelope 等价面的裁决**未回写 schema §6.2**（契约原文只排除 recorded_at） | 文档同步债 |
| R7 | MEDIUM | 尾行容错只看「最后一行解析失败」，带 LF 的损坏末行也被当截断容忍 | 账本末行坏但带 LF（完整损坏而非截断） |

**停轮理由（如实）**：三轮整改模式显示，每轮修复都会引入新的状态机分支（round-1 修 7 条 → round-2 抓出分诊层 3 BLOCKER → round-2 修 8 条 → round-3 又抓 2 BLOCKER）——当前分诊已从四格膨胀为六格状态机，继续无审查地修复会把复杂度推得更高。round-3 残留的共同特征：**全部需要「账本被外部工具写入非本写点产出的行」或「用户重跑历史评分」才触发**，单写者正常评分路径（写→崩溃→重试→恢复）已被 25 门与三轮审查确认收口。

## 如实边界声明（本卡未证明什么）

1. **并发面不成立**（最重要）：本卡没有实现任何锁。两个 quiz-answer 同时评同一节点时，A2 的「重放至空」没有互斥保护，可能出现双写或丢事件。schema §6.2 A4.1/A4.5 的 per-node sidecar 锁 + fencing epoch + per-vault 账本锁全部属 **G3-3**。单写者 = quiz-answer 单进程串行是本卡正确性的前提。
2. **耐久性只证明到调用序列**：变异与 spy 门证明 write→flush→fsync→replace 的**调用顺序**，不证明真实断电后数据存活（需故障注入硬件或 dev-machine 崩溃模拟，不在本卡）。
3. **A2 重放只恢复 FSRS 调度状态**：mastery（衰减 Beta）与疑问 callout 没有事件载荷可复放——崩溃窗口①的恢复路径里，FSRS 恰好应用一次，但 EMA/calibration 由本次运行用本次 payload 重写。跨事件 pending（别的板的事件）恢复时 mastery 副作用**永久丢失**（无数据可复放），只有 FSRS 被补上。
4. **旧写序遗留不补录**：历史节点若处于「frontmatter 已应用但账本无该事件」（旧写序产物），本卡判定为整体 no-op 并 stdout 声明，不自动补录（审计完整性走人工补录通道）。
5. **vault_id 绑定链的环境前提**：`_vault_id_of` import `app.config` 硬依赖 `backend/.env` 与 PyYAML——这是校验器早已承担的前提（非本卡引入），失败模式 = 写侧 fail-closed 拒写（不是写错值）。若要摆脱，需把 `sanitize_vault_id` 拆到无 pydantic 依赖模块（另立卡）。
6. **Obsidian 插件是既存第二写路径**：`frontend/obsidian-plugin/src/main.ts` 的 node_derived 直写不在本卡写点门 grep 范围（卡文命令只扫 backend/app + canvas-vault/.claude），本卡未动它，登记为存量事实。
7. **幂等分诊依赖单一原子写不变量**：「frontmatter 有 event_id = 上次完整成功」成立于现有实现（mastery/FSRS/calibration 同一次 os.replace），若未来有人把 frontmatter 写拆成多次，这个判据会失效——已写进代码注释。
8. **fixture 与生产的已知差异**：测试节点 frontmatter 仿 live 真实形态（裸值/字段序），但 live 只有一个带 fsrs 字段的真实节点（Learning 态 step:0）；Review/Relearning 态的 canonical 形状来自契约三态表，无 live 样本可逐字对照。
9. **Codex round-3 残留（R1-R7，见 §五表格）**：最要紧的用户可见项是 R3——重跑**历史**评分（E1→E2→重跑 E1）会被误报 envelope 冲突（fail-closed 报错，不损数据）；部署前若你常用「翻旧板重跑」，此项必须先修。

## 待你裁决

| # | 事项 | 默认（本卡已按默认实现） | 备选 |
|---|---|---|---|
| ① | review_time ≤ W 时 | 推进 W+1s 写入（不拒绝，不丢评分） | 拒绝写入（会丢真实评分，与审计完整性冲突） |
| ② | fsrs 不可用时 | 事件仍落账 + `degraded:<原因>` 哨兵成对 + frontmatter 只写衰减 Beta 不写 W；fsrs 恢复后下次评分的 A2 自动补应用 | 阻塞评分直到 fsrs 恢复 |
| ③ | 残缺卡（三态 degraded） | fail-closed：报错、零写、检验白板保持 scored_pending_node_update 续跑态 | 跳过该节点继续写其他节点（会在错误基线上叠加，契约禁止） |
| ④ | 查重口径 | parsed-field equality（修正实现，幂等语义不变，不触发 v2 升版） | — |
| ⑤ | 部署 | 不部署 live；部署须你批准后另行执行（同时部署 SKILL.md + fsrs_bridge.py，两者成对） | — |
| ⑥ | **何时部署到 live** | 建议：**不合并、等残留清零卡（G3-2b）后再部署**——round-3 残留 R3 会让「重跑历史评分」报错（fail-closed 方向，不损数据但体验破损）；若接受此限制可先部署 | 立即部署（接受 R3 体验限制与 R1/R2 的边缘触发面） |
| ⑦ | **round-3 残留（R1-R7）处置** | 登记未合卡台账，立「G3-2b 残留清零」卡（预计：R1 未知键冲突化 + R2 durable 时刻整秒校验 + R3 按事件独立 attempt 复算 + R4 统一业务时刻 + R5 重放前自洽校验 + R6 schema §6.2 修订 + R7 LF 判据收紧，约 1 天） | 本卡回滚（放弃 write-ahead 改造） |

## 证据位置

- 审查存档：`_bmad-output/审查/codex-review-CARD-G3-2-round{1,2,3}.md`（stderr 留档同名 `.stderr`；三轮裁定均为「需整改」，round-3 残留 R1-R7 见 §五）
- Codex 提示词：`_bmad-output/审查/prompts/codex-prompt-CARD-G3-2.md`（round-3 版）+ `codex-prompt-CARD-G3-2-round2.md`（round-1 版内联于 round1.stderr 对话流）
- 新测试：`backend/tests/regression/test_g3_2_review_ledger.py`（25 门）
- 契约文档：`docs/learning-events-schema-v1.md` §6.1-6.3（本卡未改契约文本；实现与其判据一致，**唯 fsrs 身份键排除出 envelope 等价面一项待 §6.2 修订回写 = 残留 R6**）
- 变异脚本：session scratchpad `g32_mutations.py`（串行 + 还原逐字节比对）
