# Canvas Learning System 生产力化长期 Goal 计划书

> **Plan ID**: `PLAN-CLS-PRODUCTIVITY-2026-08-20`
> **状态**: USER-REVIEW — 总方向已获用户确认；§12 实现合同 v2、Phase 0A 的 S1–S4 与 GOV-01 方案 A 尚待用户第一级授权。授权后也只先执行 Phase 0G 的冻结 Bootstrap-0 补丁与 governance OpenSpec/manifest；在 `GOV-01-VERIFIED` 前禁止 Phase 0A scanner、A01/A02 实例化、私有 root 扫描、ChatGPT 外发和产品代码实施
> **基线时间**: 2026-08-20（HEAD `01944346`）
> **工作范围**: 当前 Obsidian Hybrid 分支；活动前端仅为 `frontend/obsidian-plugin/`，不复活已弃用 Tauri/React 产品面
> **From PRD**: §0.4 [用户核心诉求] (line 80-90)
> **From PRD**: §1.5 [BKT + FSRS + 5 信号融合] (line 599-678)
> **From PRD**: §1.8 [3 天 + 1 周主动提醒] (line 2824-2930)
> **From PRD**: §5 [Dashboard 与今日推荐] (line 4841-5185)
> **From PRD**: §6-§7 [Graphify、LanceDB、Graphiti 与 MCP 链路] (line 5815-6627)
> **From PRD**: §8 [用户旅程] (line 6936-7119)
> **From PRD**: §9-§11 [效果评估、路线、限制与回滚] (line 7120-7457)
> **From PRD**: §12 [决策点与批注区] (line 7460-7503)

## 1. 一句话 Goal

在不移动或损坏用户原始资料、不允许跨 vault 数据串写、且不依赖持续人工救火的前提下，把 Canvas Learning System 从“能力丰富的个人 alpha”提升为一个可快速接入新旧 vault、检索结果可解释、Graphiti 写读可恢复、FSRS 每日复习可信、信息收集可审计、白板可安全可视化，并经 14 天真实使用验证的个人生产力候选版本。

这不是商业 SaaS 上线目标；“生产力标准”在本计划中指：用户可以每天依赖它学习和收集信息，系统出错时会明确报错、可恢复、不会静默污染或丢数据。

## 2. 当前开发进度的明确裁定

### 2.1 总结论

当前不是“从零开始”，也不是“已经收官”。准确状态是：

> `/sync/batch` 的 P0 跨 vault 止血已经完成；第四轮审查后的 C1–C4 已提交并生成第五轮审查包，但尚无第五轮独立终裁。现有 RAG、Graphiti、FSRS 和每日 Markdown/通知链具备真实能力，但在唯一真相源、多 vault、失败可见性、用户 UAT 和恢复演练上仍有阻断项。因此当前只可称为“受控个人 alpha”，不能称为高生产力个人版本。

证据优先级按声明类型分别计算，不能用一条总排序替代：

- “代码是否存在/入口是否接通”：当前 git 与真实入口运行 > 最新独立终裁 > `CURRENT_TASK` > 旧设计文档。
- “服务当前是否工作”：带环境清单的运行证据/实时 CI > 静态代码与文档。
- “用户是否真的得到帮助”：用户真实 UAT/dogfood > 自动测试 > 实现说明；技术绿灯不能代替用户体验。

旧 `gap-analysis.md`、`annotation-tracker.md`、`s40-progress-report.md` 和 `sprint-status.yaml` 均存在时间或产品形态漂移，不能再单独用来计算当前完成率。

### 2.2 进度矩阵

| 能力面 | 当前状态 | 已有真实进展 | 未闭合门 |
|---|---|---|---|
| `/sync/batch` 跨 vault 隔离 | P0 范围已完成 | 复合 group 身份、迁移、真实 Neo4j 双 vault 写删门已落地；见 `CURRENT_TASK.md:23-30` | 读侧 Phase 2、学习关系身份和其他旁路不在这次闭环内 |
| C1–C4 第四轮返工 | 代码已落地，待裁 | `c154a7f2`、`d39983ce`、`1683328c`、`1b7485b9` 已提交；第五轮任务书在 `01944346` 入库 | 无第五轮 CLOSED/STILL-OPEN 终裁；B4、TOCTOU、P1-03/04 仍在 |
| CI 与治理 | 整体红，Agent 治理链不可复现 | 最新 C4 run 的 Python 3.11/3.12 子集通过，失败能真实传播 | Dependency Audit 仍红；CI 仅覆盖有限后端文件；无 required checks、branch protection 或 ruleset；CURRENT_TASK/规则/Plan ID 分裂，当前 Stop 链还有自动 stage/commit/push 用户工作树的写副作用风险 |
| 新 vault 部署 | 部分可用 | `/deploy-vault` 与 `install-vault.sh` 能创建新目录、复制部分系统件并激活 | 路径硬编码、manifest 漂移、会复制本机配置、无完整 preflight/rollback |
| 已有 vault 接入 | 未实现 | 有设计讨论 | 安装器直接拒绝已有目录；没有 dry-run adopt、冲突合并、回滚 |
| RAG/LanceDB | 主链可用但证据不足 | `search_notes` fast path 真实走 LanceDB；已有真实基线和部分 UAT | legacy 表 fail-open、多 vault scope 不统一、指标名实不符、真实端到端覆盖不足 |
| Graphiti 结构化写/精确读 | 部分可用 | group-aware UUID/边、精确读组过滤、C3 production caller 修复 | provenance/namespace B4、学习关系跨 vault、语义 sibling 读写不对称、DLQ 无 replay |
| FSRS v2 | 代码链存在，用户未验 | `quiz-answer → fsrs_bridge → frontmatter → daily picker` 已落地，定向测试存在 | 双真相源、真实新卡故障、并发/乱序、版本契约、多 vault 状态隔离、五项 UAT |
| 每日复习 | 单 vault 实验性可用 | launchd、Markdown/JSON、通知降级链存在 | 当天重学卡可能不刷新；Dashboard 与 picker 口径不一致；多 vault 会共享锁/缓存/通知 ID |
| 每日复习 Web UI | 未实现 | Dashboard 有静态链接和数据底账 | 活动插件无交互 Review Queue；旧 React 位于弃用目录且读错真相源 |
| 信息收集 `/board-recap` | 设计态 | 已有 v2 设计与一次原型回顾 | 仓内无 skill、四个产品决策未锁、无真实板 forward test/UAT |
| `/clear-inbox` | 设计态 | 有五步流程草案 | 无 skill；移动/复制/raw 不动之间存在未决语义与可逆性要求 |
| Canvas/Excalidraw | demo | 有三个真实 Excalidraw 快照和需求记录 | 生成器不在仓内；无格式契约、增量同步、回读、冲突与回滚 |
| 批注总账与 ChatGPT 第二段 | 未闭环 | 有旧 108 条追踪器和 8 月分批研究 | 旧追踪器仍按弃用 Tauri 组织；统计不自洽；未形成逐问证据与双审闭环 |
| Karpathy 对照 | 完成事实纠偏，未完成落地 | 已撤回“Karpathy 反对 raw RAG”的错误说法 | raw/wiki/schema 映射、wiki 中间层、lint、角色权重和采用漏斗未锁定 |

### 2.3 指定 8 月 17 日裁定的变化对账

| 8 月 17 日发现/裁决 | 后续变化 | 2026-08-20 裁定 | 证据 |
|---|---|---|---|
| P0-1 `/sync/batch` 裸 ID 跨 vault 写删 | 写侧复合 `(id, group_id)`、迁移、真实 Neo4j 双 vault 门 | **该 P0 范围 CLOSED**；不代表所有读写链都隔离 | `32e9e29c`；`CURRENT_TASK.md:23-30` |
| `/app/data` 子挂载遮蔽配置，容器走旧 fallback | 移除嵌套挂载并对齐权重 | **原 split-brain 已修**；完整部署仍有绝对路径/volume 债务 | `970cf659`、`2c5a4683` |
| mastery 离线/冷缓存不封闭 | 增加离线兜底、方法名契约和超时硬化 | **局部修复**；仍须进入稳定 CI 与真实链回归 | `05cef992`；`CURRENT_TASK.md:10-12` |
| 同步脚本可能连坐删除 sentinel 区间内用户文字 | 未见用户 UAT 证明该语义已根除 | **STILL-OPEN**，并入 raw/derived 与 mutation helper 轨 | 8/17 文档 `:28,50,54-55` |
| E-2 快照含泄题原文 | 安全投影、SnapshotV3、B3/C2 连续硬化 | **代码已落地，待第五轮终裁** | `63f3117b`、`45f91ff5`、`1683328c` |
| `_待处理/_archive` 黑名单是设计愿望，不是现实 | 索引黑名单已实现 | **索引资格闸局部 CLOSED**；raw 被 move 的产品语义仍未裁 | `fc948325`；8/17 文档 `:17,30` |
| doc_type 整族未接线、指标名实不符 | 未见封闭的当前证据 | **STILL-OPEN** | 8/17 文档 `:31,68-72`；当前 regression 脚本/基线 |
| 生产分支无服务端强制质量门 | workflow 已监听分支并传播失败 | **PARTIAL**；Dependency Audit 红、CI 仅子集、required checks/ruleset 为空 | `.github/workflows/test.yml:9-31,76-136`；最新 GitHub run |
| 批注 schema 第五代在野、总数/生命周期漂移 | 未建立统一 ledger v2 | **STILL-OPEN** | 8/17 文档 `:34,70-75`；旧 `annotation-tracker.md` |
| B-2 广度回顾先做只新增报告的薄版 | 设计稿存在，skill 不存在 | **DESIGN-ONLY** | 8/17 文档 `:103,119`；`研究/2026-08-16-广度回顾skill-设计方案.md` |
| E-5 Dashboard Web UI 缓行 | 没有活动产品实现 | **仍在缓行区**；本 Goal 只在 FSRS/Review Projection 可信后启动 | 8/17 文档 `:102,120` |

8 月 17 日正文记录的 8 个用户裁决已经 8/8 通过（`:109-120`）；文件头“待用户裁决”是过期元数据。裁决只锁方向，不自动证明实现完成。

### 2.4 当前仓库与质量门事实

- HEAD 与远端均为 `01944346`；`main` 独有 9 个提交、当前 HEAD 独有 367 个提交，合并风险不可忽略。
- 本次澄清时工作树有 10 个 tracked 变更（其中 5 个删除）和 70 个 untracked。除本计划外均先视为用户资产，长时间施工前必须动态重数并分类，禁止清理或覆盖。
- 第五轮审查包 `审查/2026-08-20-P1-05d-五轮审查包-给Codex.md` 已具备，但“送审就绪”不等于“通过”。
- 2026-08-20 核验的最新 CI run：Python 双版本成功，Dependency Audit 与 Summary 失败，整体为 failure。
- 当前 workflow 只运行选定的后端测试文件，不覆盖活动 Obsidian plugin、真实 Neo4j/LanceDB/Graphiti 集成或完整测试集。
- GitHub 分支保护返回 404，repository rulesets 为 `[]`，因此不存在强制质量门。

### 2.5 审计边界

- 本轮没有 Graphiti MCP 工具，无法执行仓库规则要求的 `search_memory_facts`，因此没有把 Graphiti live 数据状态写成已核实事实。
- RAG/Graphiti 的代码路径缺陷可由源码确认；“当前生产库是否已污染”仍是未验证项，必须在授权后的只读 census/隔离环境 canary 中确认。
- 本轮没有迁移、删除或改写 Neo4j/LanceDB/vault 数据，也没有实施业务修复；唯一写入是本计划书。

## 3. 本轮对抗审查的主要发现

### 3.1 批注问题与 ChatGPT 复审

旧批注追踪器不能直接继续打勾：其 NOT_VISIBLE 标题数与实际列举数不一致，并把大量问题归因于已经弃用的 Tauri 产品面。至少还有 BROKEN、DEAD_CODE、NOT_VISIBLE、研究问题和技术更新五类未得到当前 Obsidian 形态下的重新裁定。

风险不是“没有回答”，而是三类状态曾被混写：

1. 设计文档提出了方向；
2. 代码实现了局部；
3. 用户真实使用已经通过。

以后任何批注只允许使用以下状态：`unanswered / decision-needed / design-only / implemented-unverified / verified / rejected / superseded / duplicate / unverifiable`。`design-only` 永远不能折算为完成。

### 3.2 多 vault 快速部署

现有安装器证明“一键创建新 vault”不是空白，但尚不能可靠分发：路径和 worktree 被硬编码；已有 vault 被拒绝；插件、模板、root MCP 和配置 manifest 不完整；本机 key 与 `settings.local.json` 有被复制风险；volume、backend readiness、首次索引、Graphiti 回填和失败回滚均未成为安装事务的一部分。

更严重的是，部署表面成功不能证明数据隔离：

- `Neo4jClient.create_learning_relationship()` 仍按概念名 MERGE，再事后 SET group，同一用户跨 vault 学习同名概念会复用并搬走节点。
- LanceDB 的 legacy `vault_notes` 回退同时被读写路径使用；新 vault 专属表不存在时可能落入共享旧表。
- memory API 接受请求 vault，但 `MemoryService` 的写组仍可能读取全局 active vault，形成两个真相源。
- durable indexing pending journal 没有 vault 维度，切换 active vault 后可能在另一 vault 重放相对路径。

因此 adopt/new/activate 必须建立在统一 `VaultScope` 和双 vault canary 之后。

### 3.3 RAG 与 Graphiti 是否达到高生产力标准

没有达到。当前较准确的分层判断是：

- Lance fast path：已经有日常价值，但隔离、纯度和指标口径不足。
- Graphiti 结构化写入与精确读：局部成熟，C3 是真实进步。
- Graphiti 语义 episode 与 full RAG：仍可能写入 semantic sibling、读取只查主组；异常经常降为空列表，用户无法区分“没有记忆”和“系统坏了”。
- full RAG 请求作用域：API 没有完整 vault scope，agent 侧 subject scope 也有丢失路径。
- 数据恢复：Graphiti 死信无自动 replay，原始来源可恢复性尚未证明。
- 离线评测：现有 `recall` 实际更接近 hit@k；旧基线中的污染率和假阳性仍不足以支撑“高生产力”宣传。

当前系统可作为受控 alpha 使用，但不能在静默降级、跨 vault 或恢复方面被无条件信任。

### 3.4 FSRS 与每日白板复习

当前有两套独立 FSRS 状态：节点 frontmatter 链与后端 `fsrs_card_states.json`/MasteryStore 链。后端状态键还只有 `concept_id`，没有 `{vault_id, concept_id}`。这不是普通技术债，而是调度真相分裂。

另外存在四个会直接影响每日使用的反例：

1. 当前 py-fsrs 新卡的 `stability/difficulty` 可为 `None`，后端真实路径直接 `float()` 会失败；现有 FakeCard 测试没有证明真实路径。
2. 每日任务 09:05 生成并缓存整天，复习后 1/10 分钟到期的 Learning/Relearning 卡不会自动重新出现。
3. 节点原子替换只能防半文件，不能防两个并发复习事件的 lost update；也没有乱序事件隔离。
4. state、lock、log、notification ID 和 `board_last_recommended` 未完整带 vault ID，两个 vault 同日运行会互相影响。

实测口径还不一致：同一 vault 的 Dashboard 可把 13 个概念判为到期，而 picker 只选出 6 个。Web UI 必须消费统一 Review Projection，不能再实现第三套 due 算法。

### 3.5 信息收集 skill

现有 `/board-recap` 与 `/clear-inbox` 都是设计稿，不是可触发、可验证、可分发的 skill。对抗结论是：不要做成一个同时“回顾、移动、删除、写 YAML、重排白板”的巨型 skill。

推荐拆成两个低耦合能力：

- `board-recap`：只读原白板/材料，先新增一份增量回顾；默认不改原白板、不改节点 YAML、不移动文件。薄版通过后再输出链接回原节点的“检验白板”，用于阶段性回顾而不是复制正文。
- `clear-inbox`：显式变更型 skill；先列 preview/diff/conflict，再由用户确认 move/copy/link；全程保留 provenance、备份和撤销。

用户原始诉求不能被缩成“再写一篇 Markdown”。完整信息收集闭环必须覆盖：

`原白板/新材料 → provenance 清单 → 拆分建议 preview → 派生节点/检验白板 → 阶段回顾 → 方向偏航 lint`

其中“方向偏航”必须使用可检查的信号：用户原问题覆盖率、来源覆盖率、未答问题年龄、计划主题与实际新增材料的分布差、重复堆积、无来源结论和连续多轮没有进入学习/复习闭环；不得只让 LLM 凭感觉说“你偏题了”。原白板拆分先给稳定 ID 映射和 diff，用户确认后才创建派生产物，任何阶段都不自动删除原内容。

按 skill-creator 的约束，正式实现时必须先收集真实触发语句与三类真实板例子，使用初始化脚本创建技能骨架，保持 `SKILL.md` 精简，把确定性检查放进 `scripts/`，再以不泄露预期答案的独立 agent 做 forward test。不能用“另一个 agent 能靠上下文猜出正确答案”冒充 skill 有效。

### 3.6 Canvas / JSON Canvas / Excalidraw

现有产物是一次性展示快照，不是转换系统。Markdown/Dataview/Mermaid 白板模型缺少几何位置、尺寸、层级、z-order、group、端口和边绑定，因此不可能直接声称视觉无损 round-trip。

推荐顺序是：

1. 锁定独立的 canonical semantic model 和支持子集；
2. 先做确定性单向 exporter；
3. 保留人工布局，支持增量刷新；
4. 再做受支持子集的回读；
5. 对任何不支持元素输出 loss report，禁止静默丢弃。

JSON Canvas 适合作为开放的基础节点/边互操作层；Excalidraw 具有更丰富的自由绘制、frame、binding、files/appState 语义，不能把两者当成完全等价格式。

### 3.7 Karpathy 设计对照

Karpathy 的知识系统草案重点是三层：原始材料、LLM 维护的 wiki、中间 schema，以及 `/ingest`、`/query`、`/lint` 这类模块化操作。它没有规定 Canvas Learning System 的 FSRS、教学诊断或白板交互，也不能作为“反对 raw RAG”的依据。

建议映射如下：

| Karpathy 抽象 | CLS 对应物 | 当前缺口 |
|---|---|---|
| raw/source | 课程材料与转录通常只读；原始白板由用户控制编辑，系统只把它当受保护 source | source/derived 角色仍可能混杂；移动/复制策略矛盾 |
| wiki | 人类可编辑的节点笔记、回顾报告、解释层 | 没有被明确命名和治理的 wiki 中间层 |
| schema | frontmatter、BoardManifest、稳定 ID、关系与复习事件契约 | schema 已多处存在，但版本、provenance 和唯一真相未统一 |
| ingest | new/adopt vault、信息收集、索引与回填 | 无可靠 adopt、事务激活和 versioned manifest |
| query | Lance fast path、结构化 Graphiti、full RAG | scope、degraded 状态与指标仍不诚实 |
| lint | orphan/污染/事实支持/批注覆盖/恢复检查 | census 零散存在，没有统一生产门 |

CLS 应把 Karpathy 视为“知识层治理参考”，不是照抄产品。CLS 的差异化价值必须落在时间维度的 FSRS、可考察性、错因、白板上下文和每日行动队列。

## 4. 目标架构原则

```text
受保护 source/raw（课程材料只读；原白板仅用户可改）
  └─ ingest manifest + provenance
      └─ 可编辑 wiki（节点笔记 / board recap）
          ├─ schema（frontmatter / BoardManifest / stable IDs）
          ├─ review event ledger → FSRS current state → Review Projection
          ├─ semantic episode ledger → Graphiti projection
          └─ 可重建派生层（LanceDB / Graphiti / Dashboard / Web UI / Excalidraw export）
```

硬边界：

1. raw/source、用户手写内容和审查批注不可被自动删除或静默覆盖。
2. LanceDB、Graphiti、每日 JSON/Markdown、Dashboard 和视觉导出都是派生层，不能反过来成为相互竞争的真相源。只有在每种 Graphiti episode 都存在可重放 canonical ledger 或源指针时，才允许声明 Graphiti“可完全重建”；历史缺正文项必须明确标成不可恢复，不能用愿景覆盖事实。
3. 每次请求只解析一次 `VaultScope`；request vault、active vault、Lance table、Neo4j group、Graphiti group、journal namespace 必须一致，否则 fail closed。
4. “空结果”与“系统故障”必须分开：贯穿 `ok / empty / degraded / unavailable`。
5. 当前学习调度只允许一个 current-state 计算口径；所有界面消费同一个 Review Projection。
6. 所有跨格式写入先 preview、原子发布、备份、可撤销，并输出显式损失/冲突报告。

## 5. 长期执行路线

所有批次都遵守：先 OpenSpec/设计，用户确认，单一主题实施，真实入口测试，独立对抗复核，最后才更新状态。每轮只递交 6–8 个裁决点。Phase 0G 是为消除当前治理链循环依赖而设的一次性、规范优先的 bootstrap 例外；它经用户授权后可先于通用“OpenSpec 先于任何代码”规则精确应用冻结 safe-mode 补丁，但不得被其他任务复用。G0/G1 是既有工作流编号，不代表执行先后；实际顺序以 §12.8 为准：Phase 0G 过门后，先做 G1 对应的 Phase 0A 用户意图恢复，再做 G0 对应的 Phase 0B 技术基线。

### GOV-01 / Phase 0G — 先恢复可复现的 Agent 治理链

- [x] 三路只读对抗审计 CURRENT_TASK 分裂、Hook 运行时/分发、Stop 写副作用、DD 门与 Graphiti 治理镜像。
- [x] 冻结 Bootstrap-0 safe-mode patch 及其 base/target/patch hash，并对当前基线通过 `git apply --check`。
- [ ] 取得第一级 receipt：用户引用 handoff envelope 的精确 SHA-256，同时确认其中冻结的 HEAD/tree、§12 流程/完成门、S1–S4、GOV-01 方案 A、契约/schema 与 patch；任一 bytes 变化都重新确认。
- [ ] 第一级 receipt 生效后的第一个治理实施写入只能是冻结 Bootstrap-0；apply 前须证明该 worktree 无活动 Claude session，并只由 Codex/外部 runner 执行；safe mode 后不启动/resume Claude，磁盘配置由外部解析，fresh-session 验收延后到最终 candidate 的 network/Graphiti deny 环境。
- [ ] safe mode 验证后，只有获批 envelope 预先绑定 `runtime_readiness_state=ready/openspec_scaffold_allowed=true` 才可运行本 worktree 的 Node/OpenSpec；当前 handoff 为 `openspec-absent/false`，所以 Bootstrap 验证后必定 STOP。安装或出现新 CLI 都须新 envelope/新 receipt，不能让旧批准自动扩权。
- [ ] 取得第二级 receipt：用户批准 strict-validated OpenSpec 导出的 exact-path/action/base-hash manifest 及 digest；只在此后修改 manifest 内的治理文件、运行治理测试并作 path-scoped 本地 commit，仍禁止 push。
- [ ] 通过 GOV-T00–GOV-T12 和独立 Agent 红队，无 BLOCKER/HIGH 后才派生 `GOV-01-VERIFIED`；随后 bootstrap exception 立即失效。

退出门：两级 receipt 都与精确 revision/hash/manifest 绑定；单一 canonical task/plan、tracked rules/hooks、无写 Stop、commit trace 与 Graphiti derived-mirror 语义在 clean clone 可重放；GOV-T00–GOV-T12 全过；状态为 `GOV-01-VERIFIED`。远端未获授权时 `server_enforcement_state` 必须诚实保持 `pending`，不得宣称 server hard gate，且 OBJ-07/最终发布继续被阻断。达成前不得创建 `annotation-truth-ledger-v2`。

### G0 — 冻结事实与保护用户工作树

- [x] 三路只读对抗审计：当前进度；RAG/Graphiti/deploy；FSRS/UI/visual。
- [x] 核验 git、最新 CI、branch protection/ruleset 与第五轮审查包。
- [ ] 动态重数并分类工作树：用户资产、审查产物、应提交代码、临时物；只登记，不删除。本计划写入前的基线为 10 tracked + 70 untracked。
- [ ] 给当前分支建立可恢复基线和路径级 ownership，确认“main 独有 9 / HEAD 独有 367”的分叉策略。
- [ ] 送第五轮独立终裁；未得终裁前不宣称 P1-05/P1-01/P1-08 CLOSED。
- [ ] 修复 Dependency Audit；不能只扩大 ignore 清单。评估升级、替换或隔离 moviepy/Pillow 调用面。
- [ ] 诊断全量测试超时与 xdist 收集不确定性，逐步扩 CI；加入活动插件 build/test 和真实服务 smoke gate。
- [ ] 经用户授权后设置 required checks/ruleset；保护应在稳定绿门存在后启用。

退出门：第五轮无未处置 P0；整体 CI 绿；用户工作树分类完成；任何残余 P1 有 owner、复现和隔离措施。

### G1 — 重建全部批注总账并完成 ChatGPT × Codex 双审

- [ ] 先建立 annotation source manifest，不把“旧 108 条”当全集。S1 的候选来源边界是 PRD、repo-wide current planes、全 reachable Git refs，并把 archive/template/review pack 扫描后分类；`ROOT-ACTIVE-VAULT`、`ROOT-EXTERNAL-PRIVATE-01`、transcript 和其他私人/外部 root 只以 opaque root ID 进入本机候选清单。S1–S4 未经用户确认前不运行 final census；任何私人 root 必须逐 root 授权后才扫描，不属于默认扫描范围，原文默认不外发。
- [ ] 新建 annotation ledger v2：Local Truth Ledger 私密层才可保存用户原文、vault/path/anchor、blob/content raw digest、round/Q ID 与原子文本；public A02 只保存 opaque ID、严格枚举、public canonical SHA、keyed commitment、状态和不含私人正文的证据。两层共享随机对象 ID，但 private locator map 不提交。
- [ ] 对 manifest 发现项、旧 tracker 候选、8 月新增批注、FSRS、多 vault、RAG/Graphiti、信息收集和视觉转换做原子化与去重，但保留每条原文到新 ID 的 provenance alias。
- [ ] ChatGPT 正常批按一个主题打包 6–8 条；仅当同主题不再有其他 eligible atom 时，最后一批可为 1–5 条 `final-tail`，且必须有绑定精确 annotation revision 集合的用户 receipt，禁止 padding 或重复项凑数。包内只给用户逐批批准的最小必要材料、代码片段、测试和开放问题，不预填 Codex 结论。
- [ ] 外审前执行 secret/private-data 扫描、路径去标识化和内容最小化；默认禁止发送 `.env`、key、vault 私人正文和未获授权的外部文件。
- [ ] 交接方式固定：Codex 生成脱敏 pack，用户逐字节预览并批准后在指定 ChatGPT 会话提交（除非届时有用户批准的 connector）。完整 prompt/reply、pack bytes 与它们的 raw digest 只归档在 private layer；public A02 只保存 `CLS_EXTERNAL_PACK_v2`/`CLS_PRIVATE_CONTENT_v2` keyed commitment、`CLS_APPROVAL_RECEIPT_v2` trusted receipt commitment、ChatGPT provider/product/model 和 opaque session token。pack 就绪时仍只是 `prepared`，收到回复也只是 `reply-received`，不能写 `reviewed`。
- [ ] 要求 ChatGPT 每条给：裁定、反例、证据需求、方案比较、最小验收与不确定项。
- [ ] Codex 对 ChatGPT 的每个事实执行仓库复核，标记 `SUPPORTED / REFUTED / PARTIAL / UNVERIFIABLE`；不得用 ChatGPT 未见到的私有正文替它补写“已审”。
- [ ] 对方案分歧只提交给用户裁决，不由任一模型自行吞并。
- [ ] `verified` 必须同时有实现证据与真实 UAT；纯研究只可到 `design-only`。
- [ ] 生成覆盖报告并分开计算两个分母：`Codex 本地裁定覆盖率 = 已裁定有效原子需求 / 全部有效原子需求`；`ChatGPT 外审覆盖率 = externally-reviewed 的当前 eligible 原子 / 全部 export_eligibility=eligible 的当前原子`。只有 batch 达到 `codex-reconciled`，且精确 revision、三方 pack commitment、trusted approval/sent receipt、ChatGPT session token、reply commitment 与 Codex reconciliation commitment 全部通过 checker，才派生 `externally-reviewed`；仅有归档回复不计完成。每个无法变为 `eligible` 的有效原子需求必须由用户逐项签署当前 revision 的 `external-review-waived`，不能靠类别级默认豁免。总条目、排除项、去重映射、隐私阻断、外审证据、逐项豁免、未答、待决策、实现未验和已验必须可机械对账。

退出门：source manifest 的边界与排除项经用户确认；100% 用户原文可在 private provenance 链中追踪；Codex 本地裁定覆盖率 100%；每个有效原子需求均为 `externally-reviewed` 或用户逐项签署 `external-review-waived`；`export_eligibility=eligible` 当前原子的 ChatGPT 外审覆盖率 100%，且 reviewed 必须由完整 `codex-reconciled` 证据派生；隐私阻断项逐条显式列出；0 个无 owner 的问题；统计与实际条目一致；所有“已完成”都有代码/UAT 双证据。存在 waiver 时只能声明“除用户明确豁免项外均完成 ChatGPT 审查”，禁止声明“全部已审”。

### G2 — 统一 VaultScope，完成 new/adopt/activate/rollback

- [ ] 先解决 Cypher 规则冲突：审计并拆分 `cypher_with_group_filter()` 的读查询契约与写身份契约；在规则/测试明确支持 `MATCH/MERGE/CREATE/DELETE` 前禁止机械套 helper，新增真实 Neo4j 语法与双 vault 行为门。
- [ ] 建立唯一 `VaultScope` resolver；请求 vault 与单 active 进程不一致时返回 409，禁止静默改写作用域。
- [ ] Neo4j 概念和 LEARNED 身份加入 group；同 user、同 concept、双 vault 必须生成互不覆盖的身份。
- [ ] 删除在线 Lance legacy 表回退；旧表只能通过显式 dry-run/apply/rollback 迁移。
- [ ] pending journal、state、lock、log、notification ID 和 board 历史全部按 vault 命名空间。
- [ ] 建立 versioned install manifest，覆盖活动插件、root HTTP MCP、Claudian、skills/hooks、模板、配置 schema 和版本哈希。
- [ ] 新建 `new`、`adopt-existing`、`upgrade`、`activate`、`rollback` 五个显式动作；adopt 默认不移动用户笔记。
- [ ] 默认 dry-run，输出 create/merge/skip/conflict；重复执行幂等；禁止复制旧 key 或 `settings.local.json`。
- [ ] 激活事务：preflight → journal 隔离 → backend recreate → health → Lance 首索引 → Graphiti 回填 → UAT；失败恢复旧 ACTIVE_VAULT。D1-A 下同一进程只服务一个 active vault；双 vault canary 采用顺序切换，或启两个端口/数据卷均隔离的进程，禁止一个进程同时混跑两套 scope。

退出门：相同路径、node ID、concept、user ID 的双 vault canary 在 Lance/Neo4j/Graphiti 上写、读、删均 0 串扰。第一目标是“已有 CLS 主机上的 vault bootstrap”：标准空 vault 与 1,000-note adopt fixture 的配置/激活目标 ≤10 分钟，首次索引单独计时并显示进度；完整新机器安装另按 D7 验收。

### G3 — FSRS 唯一调度与每日 Review Projection

- [ ] 决定并写入 D0 修订：推荐“frontmatter 为 current state；per-vault append-only event ledger 为事件审计与幂等来源”，禁止后端维护第二套独立调度状态。
- [ ] 下线、隔离或改造 `/review/record`、`/fsrs-state` 和 mastery grade 的遗留写路径，使其只能调用同一调度内核。
- [ ] 修复真实 py-fsrs 新卡 `None` 序列化；测试必须使用真实库对象，不得以 FakeCard 代替验收。
- [ ] 固定 library version、algorithm version、timezone、参数 hash 与迁移版本；用 golden vectors 防依赖升级漂移。
- [ ] 增加 `{vault_id, concept_id}`、event ID、per-node CAS/lock、重复事件幂等和乱序事件隔离。
- [ ] 建立唯一 Review Projection：`due_now / due_today / learning_queue / new / suspended`，并包含 `why_due`、board/node、预计时长、freshness。
- [ ] 在节点队列之上建立每日白板推荐投影：用 `source_board`/BoardManifest 聚合节点，按最紧迫到期、遗忘风险、到期节点数、考试优先级、冷却/多样性和预计工作量排序；输出 `board_id`、rank、node IDs、due counts、estimated_minutes 与 `why_this_board`。
- [ ] 明确无归属节点、一个节点属于多板、同名板、每日白板/卡片上限和去重规则；所有系数版本化，不能让 UI 临时再算。
- [ ] Quiz 更新后立即失效 projection；重学卡到期后无需重新跑整日脚本即可出现。
- [ ] 提供旧 `next_review`/后端状态 dry-run、apply、rollback 和计数/hash 对账。

退出门：同一数据集在 picker、Markdown、Dashboard、Obsidian view 和 API 的卡片数、白板数及排序逐项相同；每张推荐板都有可核验 `why_this_board`；并发无 lost update；乱序不改变状态；FSRS mini-UAT 五项由用户真实勾选。

### G4 — RAG/Graphiti 可信写读与恢复

- [ ] 完成 P1-03/P1-04：`ok/empty/degraded/unavailable` 贯穿 MemoryService、CanvasRAGState、API、trace 和 UI。
- [ ] 所有 full RAG/agent 请求显式携带 `VaultScope` 与 subject；禁止依赖遗漏参数后的默认组。
- [ ] Graphiti semantic episode 的写入组与查询组对称；主组、semantic sibling 和允许的 subject/canvas subgroup 由同一 builder 生成。
- [ ] 为所有 Graphiti episode 类型建立 rebuild matrix：canonical source/ledger、payload 或源指针、provenance、hash、隐私/保留期、幂等 ID、重放顺序和删除语义；不能只覆盖学习事件。
- [ ] 学习 episode 改为不可变 event identity，保留每次复习；Graphiti enqueue False 必须进入 per-vault durable outbox，不能返回假成功。
- [ ] B4 增加 payload node ID admission、provenance、session namespace 和快照完整性来源证明。
- [ ] 修复 92 条历史/陈旧 DLQ 的 schema/prompt budget 后建立 replay；先按真实挂载重新 census，并逐类证明源文本或源指针与 SHA 可恢复。无正文项登记为不可恢复，不计入“全量重建成功”。
- [ ] 禁止 service 层 `group_id=None` 搜全组；所有 Cypher 经显式 group gate 和双 vault 行为测试。
- [ ] 修正指标名称和分母；建立真人标注 gold set，区分 hit@k、recall@k、precision、MRR、nDCG、污染率与 FP。

建议的个人生产门（不冒充当前承诺）：跨 vault 泄漏 0；hit@10 ≥95%；nDCG@10 ≥0.80；交付污染 ≤10%；FP ≤2%；fast path p95 ≤1 秒；新增笔记 p95 60 秒内可检索。正式成为退出门前，先冻结最少 100 条真实查询的 versioned gold set，覆盖命中/无答案/中文/跨板/跨 vault 攻击五类，由用户裁定相关性；再记录依赖、模型、索引 SHA、冷/热缓存、重复次数和 p50/p95。

### G5 — 实现信息收集与回顾 skills

- [ ] 先用四类真实例子锁定触发：原白板拆分收集、单白板当日回顾、多白板/检验白板阶段回顾、待处理材料清理；明确哪些句子不应触发。
- [ ] 决定项目分发位置；推荐仓库内 canonical source + versioned manifest 复制升级，不用绝对路径 symlink。
- [ ] 用 skill 初始化器创建 `board-recap` 与 `clear-inbox`，不手搓目录；只包含 SKILL.md、必要 scripts/references 和 UI metadata。
- [ ] `board-recap` 薄版只写新报告，记录 source revision、coverage、未答问题、证据缺口、偏航信号和下一步，不改原板/YAML。
- [ ] 薄版 UAT 后增加“拆分建议 + 检验白板”输出：稳定链接回原板/原节点，展示覆盖、未答问题和阶段主题；创建前必须 preview，不复制整段正文、不改原板。
- [ ] `clear-inbox` 只在 preview 后变更，支持 copy/link/move 方案、冲突检测、provenance、备份与撤销；默认不 delete。
- [ ] 确定性扫描、diff、ID/provenance 检查放进脚本，避免 LLM 每次重写脆弱逻辑。
- [ ] 运行技能 quick validation，并以全新 agent、最小上下文、真实原板做 blinded forward tests。
- [ ] 至少三张真实板上由用户评价“是否帮到、是否漏问题、是否发现偏航、拆分是否合理、是否误改内容”；未通过只迭代 skill，不扩功能。

退出门：触发准确；原板零静默修改；输出可追踪；失败有明确降级；三板用户 UAT 通过后才进入安装 manifest。

### G6 — 每日复习 Web UI

- [ ] 产品面优先选择活动 Obsidian plugin 的 ItemView；它是 web 技术界面但与当前产品同进程、同 vault。若用户明确需要浏览器独立访问，再选择 FastAPI-served local web app。
- [ ] UI 只消费 G3 Review Projection，不实现自己的 due 算法。
- [ ] 展示 due now、today、relearning、new、预计分钟、why due、source freshness、degraded 原因。
- [ ] 支持 refresh、snooze、完成反馈、精确打开白板/节点、空状态与离线状态。
- [ ] Quiz 后的短间隔重学卡在到期后 5 秒内出现，无需用户手动重跑脚本。
- [ ] 覆盖 Asia/Shanghai、DST 时区、午夜、睡眠唤醒、Bark 失败、D1-A 的顺序切换/双隔离进程 canary 和 10,000 节点。
- [ ] 保留 Markdown/JSON 作为可读降级面，但它们与 UI 使用相同 projection。

退出门：同一队列跨所有视图完全一致；在 versioned benchmark manifest 锁定的参考机器、10,000-node fixture、依赖/缓存协议上，验证已有 payload 首屏 <1 秒、队列重建 <2 秒；若基线证明目标不合理，必须在实现前由用户改门，不能边做边降标准。用户连续 14 天无需手工清缓存或修状态。

### G7 — Canvas / Excalidraw 安全转换

- [ ] 定义 canonical visual model：stable ID、text/file/link/group、source ref、x/y/w/h、z-order、style、edge endpoints/labels、revision。
- [ ] 书面锁定 JSON Canvas 支持子集与 Excalidraw 扩展映射；不支持元素进入 loss report。
- [ ] 产品化确定性单向 exporter；未变化输入重复导出归一化相等。
- [ ] 用 sidecar mapping 保留人工移动和布局；语义刷新不得覆盖用户布局。
- [ ] 所有写入原子替换、时间戳备份、一键撤销；导出目录必须继续被 RAG 排除。
- [ ] 第二阶段只对支持子集做回读；冲突先 preview，由用户选择，禁止 silent last-write-wins。
- [ ] 覆盖中文路径、重命名、删除、重复边、缺失 embed、1,000 节点和 A→B→A round-trip。
- [ ] 用三张真实板做视觉 UAT；“结构正确”和“视觉有用”分开打分。

退出门：支持子集 0 静默丢失；人工布局可保留；任意失败可撤销；真实板视觉 UAT 通过。

### G8 — Karpathy 对照、统一 lint 与个人生产候选验收

- [ ] 建立 raw/wiki/schema 角色清单；每种文档明确 owner、可编辑者、provenance、索引权重和生命周期。
- [ ] 建立统一 `/lint` 思路：批注覆盖、raw/derived 混淆、orphan、unsupported claim、跨 vault 身份、索引 freshness、DLQ、备份可恢复。
- [ ] 不以单一 RAG 分数替代用户价值；同时记录“找到正确材料所需时间、改正次数、每日队列完成率、人工修复次数”。
- [ ] 做一次从新/旧 vault 接入 → 信息收集 → 白板回顾 → 检索 → 出题 → FSRS → 次日 UI 的完整真实旅程。
- [ ] 执行备份/恢复演练：Lance 全删后由 canonical 内容重建；Graphiti 只对 rebuild matrix 标记 `replayable` 的 episode 宣称可重建，历史不可恢复项单独报告；复习事件与 frontmatter 不丢。
- [ ] 连续 14 天 dogfood：0 数据丢失、0 跨 vault 泄漏、0 静默假成功；所有 degraded 都可见且可恢复。
- [ ] 由 ChatGPT 做最终黑盒产品审查，Codex 做证据复核，用户做主观生产力验收。

退出门：所有硬门通过，剩余风险有书面接受；才可标记 `personal-production-candidate`。

## 6. 并行 Agent Workflow

每个批次最多四个并发槽，建议固定角色：

| 角色 | 职责 | 禁止事项 |
|---|---|---|
| Root/协调 | 锁范围、合并证据、维护 plan/CURRENT_TASK、提交用户决策 | 不把外审结论直接当事实 |
| Evidence agent | 只读追踪真实入口、数据流、旧决策和 UAT | 不实施、不预设结论 |
| Red-team agent | 构造反例、跨 vault/故障/回滚场景 | 不只检查 helper 或源码字符串 |
| Scoped implementer/verifier | frontend 或 backend 单域实施；随后换独立 verifier 跑真实门 | 不跨 DD-12 范围，不用 mock/fake 冒充验收 |

实施纪律：

1. 每个新能力先通过 OpenSpec CLI 建 change，分别获取 proposal/design/specs/tasks 模板并 strict validate。
2. 一个批次只处理一个根因族；前端和后端如需联动，拆为有明确契约的独立提交。
3. commit 必须含 `PLAN-CLS-PRODUCTIVITY-2026-08-20` 或具体 FR/@spec，并有 `Story:` trailer。
4. 每批保留 before/after 反例、真实入口测试、回滚验证、CI 链接和 UAT 清单。
5. 每批结束更新本计划勾选与 `CURRENT_TASK`；不在恢复锚点写会随 push 过期的 run 号和累计计数。
6. 任何删除、移动 raw、改 secrets、启用 GitHub ruleset、迁移 live Neo4j/Lance 数据，都要另行取得用户授权。

### 每批验证矩阵

命令从仓库根运行；某项确实不适用时必须在证据包写明原因，不能静默跳过：

| 变更面 | 每批最低门 |
|---|---|
| Backend | 受影响测试 + `cd backend && .venv/bin/pytest tests/ -x -q`；在全量超时债修复前，临时只允许“定向门 + 明确超时证据 + 独立豁免”，G0 退出前必须恢复全量门 |
| 活动前端 | `npm --prefix frontend/obsidian-plugin run build` + `npm --prefix frontend/obsidian-plugin test` |
| OpenSpec/API | `npx openspec validate <change> --strict` + `npm run verify:spec` |
| Repo gate | `npx lefthook run pre-commit` + 编辑后 LSP diagnostics |
| 数据边界 | 真实 Neo4j/LanceDB/Graphiti 隔离环境的同 ID 双 vault 行为测试；mock/fake 不计验收 |
| 迁移/写盘 | dry-run → fixture apply → hash/count 对账 → rollback → 再 apply；live 执行另行授权 |

### 基准协议

所有时间/质量门先生成 versioned benchmark manifest，至少记录：参考机器、OS、依赖与模型版本、vault/节点/查询规模、数据 SHA、冷/热缓存、并发度、时区、随机种子、重复次数、统计量和裁决人。没有 manifest 的“10 分钟”“1 秒”“95%”只能是建议目标，不能用来宣布通过。

## 7. 用户需要先裁定的七个设计门

### D1 — 多 vault 运行模式

- **A（推荐）**：先保持单 active backend，但 new/adopt/activate 是事务式且 fail closed；需要时快速切换。双 vault 同时性测试用两个完全隔离的进程，不让一个进程同时服务两个 vault。
- B：一个 backend 同时服务多个 vault；能力更强，但作用域、并发、资源与 UI 复杂度显著提高。

### D2 — FSRS 当前状态

- **A（推荐）**：frontmatter 是唯一 current state；per-vault append-only ledger 只负责事件审计、幂等与重放，所有视图读统一 projection。
- B：后端数据库为 current state，frontmatter 只做投影；事务较强，但削弱本地可读/可迁移性，并推翻现有 D0。

### D3 — “Web UI”的含义

- **A（推荐）**：Obsidian plugin ItemView，使用 React/DOM 的嵌入式 Web UI。
- B：FastAPI 提供的本地浏览器 Web app，可脱离 Obsidian打开。
- C：继续只用 Dataview/Markdown；成本最低，但达不到本计划的交互验收。

### D4 — 视觉转换范围

- **A（推荐）**：先单向、确定性、保布局 exporter，再做受支持子集回读。
- B：第一版就做完整双向 Canvas↔Excalidraw；周期和数据损失风险最高，不建议。

### D5 — 信息收集 skill 形态

- **A（推荐）**：`board-recap` 与 `clear-inbox` 两个窄 skill，review 与 mutation 分离。
- B：一个总 skill 自动判断并执行所有动作；触发和安全边界更难验证。

### D6 — 已有 vault 的 raw 处理

- **A（推荐）**：原地保留，以 manifest/角色标记接入；生成 derived 输出，不移动 raw。
- B：复制到统一目录；更整齐但产生双份和同步问题。
- C：移动到统一目录；破坏链接和用户习惯风险最高。

### D7 — “快速部署”的范围

- **A（推荐）**：本 Goal 先完成“已经安装 CLS 服务的同一台机器，为 new/existing vault 做 bootstrap、激活与回滚”；Docker/Neo4j/Lance/Graphiti/模型服务只做 readiness 校验。
- B：同时交付全新机器安装器，包含 Docker/volume、Neo4j、Graphiti、LanceDB、embedding/LLM、secrets、launchd/Bark；应拆成独立 OpenSpec 与安装 UAT，不能藏在“依赖已安装”一句里。

若用户回复“批准 Goal，采用七项推荐”，即可按 A/A/A/A/A/A/A 启动；任何单项也可单独改选。

## 8. 统一生产力验收门

| 维度 | 必过标准 |
|---|---|
| 数据安全 | 0 静默删除/覆盖；raw 不自动移动；每次变更可回滚 |
| 多 vault | 同 ID/同名/同用户双 vault 在 Lance/Neo4j/Graphiti/FSRS/通知上 0 串扰；D1-A 用顺序切换或双隔离进程验证 |
| 故障诚实 | empty 与 degraded/unavailable 分离；不得把异常转成成功空结果 |
| 部署 | new/adopt 幂等、dry-run、无绝对路径/旧 secret、失败自动回滚 |
| FSRS | 唯一 current state；并发/重复/乱序安全；真实库 golden vectors；用户 UAT 全勾 |
| 每日 UI | 卡片与推荐白板的数量/排序在各视图一致；`why_this_board` 可解释；短间隔重学可见；精准打开板/节点；14 天无手工救火 |
| RAG | 指标名实一致；跨 vault 0；质量/延迟/freshness 达到 G4 建议门或经用户调整后的门 |
| Graphiti | 写入 ACK 真实、outbox/DLQ 可 replay、provenance 可核验；仅对 rebuild matrix 标为 replayable 的类型宣称可重建 |
| Skills | 原板拆分/检验白板/阶段回顾/清理触发准确，最小权限，真实板 blinded forward test，原板零静默修改 |
| Visual | 支持子集 0 静默丢失、布局保留、冲突 preview、备份/撤销 |
| 治理 | CI 全绿、required checks 生效、OpenSpec strict、plan/commit/UAT 可追踪 |
| 用户价值 | 完整真实旅程通过；用户确认系统确实减少查找、整理与决定复习内容的时间 |

## 9. 明确不做

- 不在第五轮终裁与 P0 数据边界之前铺 Web UI 或视觉大功能。
- 不复活 `frontend/src/` 的旧 React/Tauri 产品面来“快速交差”。
- 不以 mock、fake、源码字符串断言或 synthetic surrogate 作为真实入口验收。
- 不把 Graphiti/LanceDB 索引当 canonical 数据，也不让其失败时静默返回空。
- 不直接把全部批注塞进一个超长 ChatGPT prompt；按主题小批交叉审查。
- 不承诺第一版完整 Excalidraw fidelity。
- 不把 Karpathy 草案当作唯一产品路线或权威背书。
- 不碰未分类的用户工作树改动，不执行删除、重置或批量移动。

## 10. 外部一手参考

- [Karpathy：A few random notes on building a general knowledge agent](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [FSRS 官方实现与版本说明](https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler)
- [Graphiti group namespacing](https://help.getzep.com/graphiti/core-concepts/graph-namespacing)
- [Graphiti adding episodes](https://help.getzep.com/graphiti/core-concepts/adding-episodes)
- [JSON Canvas 1.0 specification](https://jsoncanvas.org/spec/1.0/)
- [Excalidraw official types](https://github.com/excalidraw/excalidraw/blob/master/packages/excalidraw/types.ts)

## 11. 激活条件

本 Goal 当前只完成了只读审计与计划编写。GOV-01 是 Phase 0A 之前的 **Phase 0G 规范优先门**：它仅用于先隔离当前有写副作用且不可复现的 Agent 治理链。若本 Goal 的通用“OpenSpec 先于代码”顺序与 Phase 0G 冲突，经用户锁定的 GOV-01 决策稿、本节和 §12.8 的一次性 safe-mode 例外优先；它不放宽私有数据、产品代码、外部写入或后续 change 的授权边界。

Phase 0G 的规范与可执行输入固定为；下列路径一律以 Git repo root 为 base：

- 决策稿：`_bmad-output/审查/phase0a-annotation-truth/2026-08-20-GOV-01-追踪真相源修复决策稿.md`；
- 冻结补丁：`_bmad-output/审查/phase0a-annotation-truth/2026-08-20-GOV-01-Bootstrap-0-safe-mode.patch`；
- 补丁 SHA-256：`d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa`。
- 第一级 receipt envelope：`_bmad-output/审查/phase0a-annotation-truth/GOV-01-first-receipt-envelope-v1.json` 及同目录 strict schema；其 domain-separated receipt SHA-256 由最终 handoff 给出并必须出现在用户回复中。该 envelope 冻结 HEAD/tree、上述文档/契约/schema、project config/package/lock、resolved toolchain 与 patch；任一变化使旧批准失效。

任一 base/patch/target hash 不匹配都必须停止并生成新 revision，禁止 fuzzy apply。两级授权是两张不可合并的 receipt：

1. **第一级授权（design lock + safe mode）**：用户以精确 envelope SHA 确认其中冻结的 §12 流程/完成门、S1–S4、GOV-01 方案 A、patch、project config/package/lock 和 resolved toolchain state；preflight 重算 envelope 内所有 hash。它先允许在证明该 worktree 无活动 Claude session 后由 Codex/外部 runner 应用冻结 Bootstrap-0 并验证 safe mode。只有同一获批 envelope 已写 `ready/true` 时，才继续在三项 telemetry/update opt-out、`npx --no-install` 与 network-deny 下创建/strict validate `repair-agent-governance-v2`，并生成 GOV 决策稿逐名列出的 control schema/checker/inner manifest/target/rollback/containment/second-receipt envelope 七个文件。当前 handoff 为 `openspec-absent/false`，故只授权 Bootstrap 后 STOP；不授权安装、OpenSpec、governance apply、本地 commit 或 push。
2. **第二级授权（exact apply）**：OpenSpec strict 通过后，用户引用 second-receipt outer-envelope SHA 与 challenge，批准其绑定的 inner exact-path/action manifest、target/rollback bundles、containment 与 control-artifact hashes；inner manifest 只列治理目标，outer envelope 绑定 control evidence，双方都不自哈希。每项分别绑定 B0 `authorization_baseline_identity` 与 B2 `live_apply_preimage`、两者之间仅允许的 transition class、对象类型、mode 与 target hash。Bootstrap 已触及的路径和 first-stage-created 路径不得错误地继续按 B0 preimage/`ABSENT` 做 live CAS。这才允许修改 manifest 内的治理文件、运行 GOV-T00–GOV-T12，并在 receipt 明确包含时在隔离临时 clone/index 创建本地 candidate commit；仍不授权移动用户 index/ref、push、Graphiti 网络写或 manifest 外动作。用户 message ID/时间不回写冻结 target；需要提交 receipt projection 时另开证据 revision。

在 `GOV-01-VERIFIED` 前，除本 Goal/GOV 决策文档的计划收敛外，repo 的执行性写入只允许上述 Phase 0G 链：第一级 receipt 下的冻结 Bootstrap-0 补丁 + governance OpenSpec/manifest，以及第二级 receipt 逐项授权的 exact governance apply/测试/本地 commit。不得创建 `annotation-truth-ledger-v2`、运行 final census、实例化 A01/A02、读取私有 root 或修改产品代码。只有 GOV-T00–GOV-T12 全过且独立 Agent 红队无 BLOCKER/HIGH，才可派生 `GOV-01-VERIFIED` 并进入 Phase 0A；Phase 0A 完成后才进入 Phase 0B，不能跳到 UI、skill 或 Excalidraw 实施。

1. **S1**：repo-wide current tree + 全 reachable refs + 锚定 PRD；archive/template/review pack 扫描后分类，不按目录静默排除。
2. **S2**：private truth layer 默认放 repo 外；仓库只提交 strict public projection。repo 内 gitignored 只能作为用户明确批准的降级方案。
3. **S3**：`ROOT-ACTIVE-VAULT`、外部私人 root 与 transcript 逐 root 授权；无授权或无来源保持 pending，禁止报 complete。
4. **S4**：先用 OpenSpec 建立 A01/A02 schema、invariant checker、scanner 与 reconciler；schema + content-addressed checker 联合门通过后，才运行无上限 final census 和首批 ChatGPT pack。
5. **GOV-01**：按两级授权消除 CURRENT_TASK/规则真相源/Plan ID 的追踪 split-brain，使 DD-14 可复现；`GOV-01-VERIFIED` 是 Phase 0A 的必要先决条件。

对 **§12 流程/完成门** 的确认只锁定 Goal 工作流：它不构成 D7-A/B 的选择，也不构成 A01 boundary receipt、任何私有/外部 root 的读取或扫描授权、ChatGPT 外发批准、A03 锁版、产品代码修改或覆盖 root `README.md` 的授权。这些均须按各自契约另行获得绑定精确范围/revision/bytes 的 receipt。

**User：我需要让 codex 审查明确知道我之前的所有批注（最重要的是 User：），从而明确知道当前我聚焦的 Canvas learning systeam 是要实现什么，我们 Canvas learning systeam 在部署到不同 vault 快速使用，并且最终我需要你 goal 再进行大规模改进后，我要你给我一个 完整的产品 readme。我才能得知是否目前的 Canvas learning systeam 是否符合我的需求，这个 readme 不能编造，是要明确在真正的使用场景跑通 E2E 测试才可写明**

## 12. User 批注吸收：Goal 实现合同 v2

> 本节直接响应上方 User 批注。若与前文的阶段顺序、批注总数或 README 发布条件冲突，以本节为准。上方 User 原文保持不改。

### 12.1 唯一终局

Canvas Learning System 的终局不是“仓库里有很多功能”。当前推荐范围采用 D7-A：用户能在一台已安装 CLS 服务的个人电脑上完成下列闭环；这不是对 D7 的静默代选。用户须在 A03 锁版前确认 D7-A 或 D7-B；若选择 D7-B，必须增加 clean-machine installer 的独立目标、旅程和发布门后再实施：

1. 对一个新 vault 或已有 vault 做可预览、可回滚的快速接入，且不移动/覆盖原资料；
2. 从原始材料和原白板收集信息，保留来源，拆成可学习节点与检验白板，并能发现方向偏航；
3. 用可信 RAG 找回相关笔记，用 Graphiti 保存并读取带 vault 身份、来源和恢复路径的个人学习记忆；
4. 从真实白板完成出题、回答、错误/批注回写和 FSRS 状态更新；
5. 第二天在活动 Obsidian UI 中看到“今天复习哪些白板、为什么、复习哪些节点”，并完成短间隔重学；
6. 在需要时把受支持的白板结构安全导出为 JSON Canvas/Excalidraw，保留布局并明确报告损失；
7. 切换到第二个 vault 时，同名路径、节点、概念、用户、FSRS 和通知全部不串；故障时明确 degraded/unavailable，备份可恢复；
8. 以上真实旅程全部在同一个 clean release-candidate SHA 上通过后，才生成完整、可复现、不夸大的产品 README。

Goal 的完成条件是“用户每天能依赖的完整闭环”，不是代码量、测试文件名、模型自评、旧 UAT 或单个离线指标。

### 12.2 八个编号化实现目标

| ID | 用户最终得到什么 | 必须交付 | 权威完成证据 |
|---|---|---|---|
| **OBJ-01 批注意图真相** | Codex 能解释所有历史 `User` 批注如何收敛到当前产品目标 | source manifest、annotation ledger v2、supersedes/duplicate/隐私链、Product Intent Contract | 用户批准边界的 A01 revision 与对该边界完整重放的 A02 revision 均 complete；100% 当前有效 canonical atom 映射到 A03/OBJ-01–08 并有证据化 disposition；每项对当前 revision 恰好二选一（XOR）为 `externally-reviewed` 或获用户逐项 `external-review-waived`；批准 scope 内无活动 `unanswered/decision-needed/deferred`；A03 绑定精确 A01/A02 revision 并由用户锁版 |
| **OBJ-02 Vault 快速接入** | 同机对 new/existing vault 执行 dry-run、bootstrap/adopt、activate、upgrade、rollback | versioned manifest、单一 VaultScope、无 secret 复制、进度/冲突报告 | J01/J02/J10 黑盒 E2E；原文 hash 不变；跨 vault 串扰为 0 |
| **OBJ-03 信息收集与白板收敛** | 原材料/原白板可被回顾、拆分、形成检验白板并发现偏航 | `board-recap`、`clear-inbox`、拆分 preview、provenance、undo、偏航 lint | J03/J08；至少三张用户授权真实板的盲测和用户 UAT |
| **OBJ-04 RAG/Graphiti 可信记忆** | 搜索与记忆命中可解释；empty 与故障可区分；写入可确认、可重放 | 统一 scope、诚实四态、episode ledger/outbox/DLQ、rebuild matrix、真实 gold set | J04/J05/J10；真实 Lance/Neo4j/Graphiti，无核心 mock/skip |
| **OBJ-05 FSRS 每日学习闭环** | 出题后产生唯一调度状态；每日按白板推荐，并解释 `why_this_board` | review event ledger、FSRS current state、Review Projection、Obsidian Review UI | J06/J07/J10；并发/重复/乱序安全；跨视图数量和排序一致；用户跨日 UAT |
| **OBJ-06 白板视觉互操作** | 受支持结构可稳定导出、保留人工布局、回读不静默丢失 | canonical visual model、JSON Canvas/Excalidraw exporter、受支持子集 controlled importer + conflict preview、loss report、backup/undo | J09；三张真实板视觉 UAT；支持子集 A→B→A 归一化相等 |
| **OBJ-07 运行、恢复与质量门** | 故障可见，索引可按矩阵重建，升级/回滚可复现 | CI/required checks、observability、backup/restore drill、benchmark/SLO manifest、dogfood protocol | J10、恢复演练、整体 CI 绿、满足最低活动量的 14 天 dogfood 0 丢失/串 vault/静默假成功 |
| **OBJ-08 证据化产品 README** | 用户能准确知道产品能做什么、怎么装、怎么用、哪些还不能用 | capability evidence ledger、README draft/frozen candidate、用户批准后的 root `README.md` | candidate 逐声明审计通过并获用户覆盖批准；执行覆盖且复核后才关闭 OBJ-08，避免用“OBJ-08 已完成”作为覆盖前提 |

Karpathy 的 raw/wiki/schema 与 ingest/query/lint 只作为 OBJ-01/03/04 的知识治理约束，不单列成产品功能，也不能覆盖 CLS 的学习闭环目标。

### 12.3 “所有批注”到底意味着什么

2026-08-20 的只读初始 census 已证明旧“108 条”不可用：

- 当前仓库四个范围加外部只读 PRD 共扫描 1,425 个 Markdown；185 个文件出现 797 个严格候选 marker。
- 797 只落在 781 行，归一后为 623 种行文本；包含镜像、派生引用、模板、空槽、误报和多轮修正，绝不等于 797 个独立问题。
- 旧 `annotation-tracker.md` 自称 108，分类标题相加为 110，实际列举 106；`gap-analysis.md` 当前严格 marker 为 109。
- 当前 Git 历史还出现 353 个已删除 Markdown 路径；必须做 blob 级历史扫描，不能只扫工作树。
- `ROOT-ACTIVE-VAULT` 的本地只读粗盘点中，21 个内容 Markdown 没有足够真实学习批注，合法学习 callout 为 0，`active_board` 为 null；这是未获逐 root 扫描授权前保存的 provisional aggregate，不公开真实 root 名或 locator，也不能拿它冒充信息收集 skill 的生产样本。
- 私有 `ROOT-EXTERNAL-PRIVATE-01` 的本地只读粗盘点发现 129 个文件、329 个显式 User 候选，但含空槽、重复引用与敏感身份/教育/移民/财务等信息；该数字只是 provisional candidate baseline，默认禁止整库外发。

“所有批注”的全集不靠口头声称，而由用户批准的 versioned Source Manifest 冻结。每个 revision 必须记录：授权 root、互斥 source plane、current-tree public VCS identity、扫描截止时间、全部 reachable Git refs/blobs、授权的外部根、解析器/规则版本、逐 SourceObject/SourceBinding/ScanAttempt 结果和排除 receipt。refs/history、index、dirty 与 untracked inventory 的 raw digest 只留 private layer；public projection 统一保存 `CLS_PRIVATE_CONTENT_v2` domain-separated HMAC。后来新增或新发现的批注进入下一 revision delta；旧 revision 不回写改数。只有该边界经用户确认，才允许报告覆盖率。

因此 OBJ-01 使用两层总账：

1. **Local Truth Ledger**：只在本机保存原文、路径、blob SHA、段落锚点、内容哈希、round/Q ID、supersedes 链和隐私等级。
2. **External Review Ledger**：只包含用户逐批批准的 allowlist；使用最小化改写、父目标、已有答复摘要和公开证据，不含原始私人正文。

“全部给 ChatGPT 审查”按两个边界诚实执行：100% 有效原子需求进入本地裁定链；只有当前 revision 的 `export_eligibility=eligible` 需求才进入用户批准的 ChatGPT pack。隐私阻断项只有在用户批准最小化改写并通过 privacy scan 后才可转为 `eligible`；若仍不能外发，必须由用户对该原子需求当前 revision 逐项签署 `external-review-waived`。收到回复不等于完成；只有 `codex-reconciled` 且 pack/approval/sent/session/reply/reconciliation 证据通过 checker 才派生 `externally-reviewed`。没有该外审证据或逐项 waiver 的有效需求会阻断 OBJ-01；存在 waiver 时只能声明“除用户明确豁免项外均完成 ChatGPT 审查”，不得声称“全部已审”。

A01/A02 的私密层、原始 prompt/reply、路径映射、raw digest 和私人正文默认必须放在 repo 外的本机最小权限目录；repo 内 gitignored 只可作为用户明确批准且记录 receipt 的降级方案。仓库只能提交脱敏 opaque ID、public canonical SHA、domain-separated keyed commitment、统计、裁定和不含私人正文的证据，禁止提交 private bytes 的裸 hash。每批外发都须在发送前预览并单独批准；撤回只影响尚未发送的批次，已发送事实必须留在审计记录中，不能声称已从外部模型删除。

每条记录至少包含：

Local Truth Ledger 私密层保存 `vault/path/line_or_anchor/raw digest/atomic text`；public projection 只保存 `annotation_id / source_object_id / source_binding_id / source_kind / parent_goal / validity_state / disposition / local_review_state / implementation_state / evidence_level / supersedes / aliases / privacy_class / export_eligibility / external_review_outcome / external_review_batch_id / external_review_waiver_id / owner / next_action / keyed commitments`。

来源分类固定为：`primary / derived / requote / mirror / template-example / placeholder / false-positive / external-private`。综合 disposition 固定为：`unanswered / decision-needed / deferred / design-only / implemented-unverified / verified / rejected / superseded / duplicate / unverifiable`；`deferred` 在执行中必须绑定用户批准和复查日期，不能成为无期限隐藏队列；长期 Goal 完成前，它必须被实现/拒绝/取代，或由用户明确映射为不在批准 scope 内的 non-goal/known limitation，因而批准 scope 内的活动 `deferred` 必须为 0。候选有效性、本地事实复核、实现证据和外审状态必须使用正交字段，不能继续塞进同一个 status。

优先级固定为：`最新明确 User 修正/裁决 > PRD 锚定决策 > 直接 User 原文 > 派生回复/审查摘要 > 已弃用 Tauri 假设`。去重不删除来源；重复项必须保留 alias 与修正链。

### 12.4 强制产物

| 产物 ID | 产物 | 作用 | 允许生成时间 |
|---|---|---|---|
| A01 | Annotation Source Manifest | 用 revision 冻结扫描根/排除根、SHA/time、reachable refs/blobs、授权外部根、规则版本与统计；私密路径层不提交 | Phase 0A |
| A02 | Annotation Ledger v2 | public projection 保存候选分类、原子需求、状态、隐私与不含私人正文的证据；私密原文层默认留在 repo 外，repo 内 gitignored 仅限用户明确批准的降级方案 | Phase 0A，持续更新 |
| A03 | Product Intent Contract | 把有效批注收敛到 OBJ-01–08 和明确非目标，并绑定其依据的精确 A01/A02 revision/digest | Phase 0A；A01/A02 complete 后由用户确认并锁版 |
| A04 | Capability Evidence Ledger | 每项能力的入口、证据等级、SHA、环境、失败行为与限制 | G0 起持续更新 |
| A05 | OpenSpec changes | 每个根因族的 proposal/design/spec/tasks 与 PRD 锚点 | 具体实施前逐个创建 |
| A06 | Release E2E Evidence | J01–J10 的 manifest、日志、checksum、截图/UAT、回滚结果 | clean RC 阶段 |
| A07 | README Draft / Frozen Candidate | J01–J10 E3 后可生成 draft；E4/E5 与 14 天 dogfood 后才冻结 candidate，全程不覆盖 root README | Phase 4 draft；Phase 5 freeze |
| A08 | 最终 root README | 用户最终查看的真实产品说明 | E5 与用户明确覆盖批准后 |

Phase 0G 已有两件冻结设计产物：`审查/phase0a-annotation-truth/2026-08-20-GOV-01-追踪真相源修复决策稿.md` 与 `审查/phase0a-annotation-truth/2026-08-20-GOV-01-Bootstrap-0-safe-mode.patch`（SHA-256 `d2f9a1ff45006cf19bd5295b751e2b620dc6043d6ec1ff26494c1d2d722aa8aa`）。它们仍为未授权实施的决策/补丁输入，不是 `GOV-01-VERIFIED` 证据。

Phase 0A 的公开初稿已落在 `审查/phase0a-annotation-truth/`：实施契约、来源边界 draft、A01 public schema 与 A02 strict public schema。它们当前均为 `DRAFT-BOUNDARY-REVIEW/incomplete`，只证明 schema 与边界设计已开始，不构成激活许可；在 S1–S4 获用户确认、`GOV-01-VERIFIED`、`annotation-truth-ledger-v2` OpenSpec 建立、schema + content-addressed checker 联合门通过、A01 boundary receipt 获批和无上限重扫完成前，不得把它们计为 A01/A02 已完成。A01 只有在用户批准的 boundary revision 完整扫描、对账并过门后才可 complete；A02 只有对该精确 A01 revision 的当前有效 canonical atoms 完整重放且 checker 过门后才可 complete。

不先写“完整 README”再想办法证明；顺序必须是 `需求真相 → 实现 → E2E 证据 → capability ledger → README candidate → 用户批准覆盖`。

### 12.5 证据等级

| 等级 | 名称 | 能证明什么 | README 规则 |
|---|---|---|---|
| E0 | Planned | 只有 PRD/OpenSpec/Goal | 只能出现在 Roadmap/Not available |
| E1 | Experimental | 代码入口 + 单元/契约测试 | 不得写“可用” |
| E2 | Integration-tested | 真实入口和隔离服务；核心依赖无 mock | 可标 Experimental，必须列限制 |
| E3 | Verified on reference environment | clean RC SHA、真实 Obsidian/backend/stores、无 skip 黑盒 E2E | 才可写“已在参考环境验证” |
| E4 | User-verified | E3 + 用户按真实场景完成 UAT | 才可写“用户可用/有帮助” |
| E5 | Personal production candidate | 全部硬门 + 14 天 dogfood + 恢复演练 | 才可写“可每天依赖的个人候选版本” |

文件名含 `e2e`、模型代验、历史 UAT、fixture、CI 绿或“代码存在”都不会自动提升等级。相关入口、依赖、模型、schema 或 UI 实质变化后，旧 E3/E4 自动降为 `implemented-unverified`，必须在新 RC SHA 重跑。

E3 之前必须在 A03/A04 锁定用户批准的生产力 SLO，且不能看完结果再降低门槛。初始候选包括：new/adopt 配置与激活时间（首次索引单列）、RAG gold-set 质量/污染/FP 与 cold/warm p95、索引 freshness、Review UI 首屏/重建 p95、Graphiti ACK/replay 和恢复时间。可从 G2/G4/G6 的建议值起草，最终阈值、参考环境、数据规模和降级规则都写入 versioned benchmark/SLO manifest；J manifest 必须记录阈值与实测。未达标只能判失败，或经用户事前/书面接受后在 README 降级为限制，不能用“已经测过”替代“达到生产力标准”。

### 12.6 十条真实用户旅程 E2E

统一证据目录建议为 `docs/release-evidence/<rc>/journeys/Jxx/`。每个 `manifest.json` 必含 candidate SHA、`dirty=false`、环境/模型/index SHA、真实命令、skip/mock 声明、起止时间、断言、回滚、脱敏 artifact checksum 和用户签字。

| ID | 真实旅程 | 关键硬断言 |
|---|---|---|
| J01 | 新 vault bootstrap | preflight→安装→activate→backend ready→首次索引→搜到新笔记→rollback；无旧 secret/绝对路径 |
| J02 | 用户授权的已有 vault adopt | 记录真实规模/content hash；dry-run、冲突选择、原文 hash 不变、激活/回滚；默认不移动 raw。另用 versioned benchmark 验证规模上限，不虚构固定笔记数冒充真实场景 |
| J03 | 原始材料到学习白板 | 建原白板→派生节点→批注→检验白板；provenance 完整，原内容零静默改写 |
| J04 | RAG 检索 | 正命中、无答案、考题隔离、跨 vault 同名攻击；empty 与 degraded/unavailable 可区分 |
| J05 | Graphiti 记忆 | 批注/对话写入→精确/语义读取→重启→provider 故障入 outbox/DLQ→replay；无重复/串 vault |
| J06 | 出题与 FSRS | 正常回答和“不会”→不泄题→不可变 review event→FSRS due；重复/乱序/并发安全 |
| J07 | 次日白板复习 UI | due/learning/relearning/new、10 分钟回炉、snooze、完成、精准开板/节点；UI/Markdown/API 排序一致 |
| J08 | 信息收集 skills | recap→拆分 preview→派生板/节点→clear-inbox preview/copy/link/move→undo；默认 raw hash 不变 |
| J09 | Canvas/Excalidraw | 三张真实板导出、增量保布局、unsupported loss report、controlled import conflict preview、rollback、支持子集 A→B→A |
| J10 | 双 vault 与恢复 | A/B 同路径/node/concept/user；Lance/Neo/Graphiti/FSRS/通知全写读删隔离；备份恢复后继续学习闭环 |

J01–J10 是一次 clean RC 的完整门；自动门之外，至少一个用户授权的真实 existing vault 必须完成 E4：对原库只做 preflight/dry-run/hash 基线，在可恢复隔离副本上跑 `adopt → 信息收集 → 白板学习 → RAG/Graphiti → 出题/FSRS → 次日 UI → vault 切换 → 备份恢复`。任何 live 原库写入仍须另行授权，且前后原库 hash 必须不变；合成 fixture/canary 不能代替这条真实旅程。

之后执行 versioned 14-day dogfood protocol；一次长 E2E 或闲置 14 天都不算。初始最低活动量为：同一 RC SHA 连续 14 个日历日每日启动并核对 Review Projection，有到期项时至少完成一张板；窗口内至少 10 次学习 session、5 次 ingest→board、3 次两类信息 skill、2 次 vault 激活切换，并各完成 1 次 provider 故障/replay、备份恢复和 visual export/import。漏日或漏覆盖则窗口未完成；任何影响产品行为的修改都须重跑受影响 J，并从新 SHA 重新开始 14 天。具体数值可在运行前由用户调整并锁入协议，开始后不得为迁就结果下调。

### 12.7 最终产品 README 发布合同

当前根 `README.md` 是历史介绍，不是可信产品说明：它仍宣称 12–14 个 Agent、自动复习 Canvas、旧插件目录、旧 Quick Start 和已经漂移的 backend/vault 配置。Goal 执行早期应先添加“alpha/待重新验证”诚实提示；不得在证据不足时把旧文案润色成新承诺。

最终 README 至少包含：

1. 产品定位、目标用户、明确非目标与当前发布等级；
2. 已验证旅程总表和 Feature maturity matrix；
3. raw/wiki/schema/event/derived 的真相源边界；
4. Obsidian/Claudian、FastAPI、Lance、Neo4j、Graphiti、FSRS 的真实调用链；
5. 参考环境、支持平台、模型、端口和版本矩阵；
6. new vault 安装与 existing vault adopt/冲突/activate/rollback；
7. 第一次使用、信息收集、白板学习、出题、每日复习的完整操作；
8. RAG/Graphiti/FSRS 的口径、degraded/unavailable 与恢复语义；
9. 隐私、secrets、vault 写权限、备份、恢复、卸载与迁移；
10. 质量/性能指标、已知限制、明确未实现功能、故障排查；
11. 开发/测试命令，以及如何从 committed evidence 重放发布证明。

在相应证据达到 E3/E4/E5 前，最终 README 禁止声明：`production-ready`、任意 vault 一键可用、完整 multi-vault safe、Graphiti 永久且全量可重建、full multi-source RAG 是默认主链、把 hit@k 写成 recall、FSRS/UI 已完全一致、Canvas↔Excalidraw 无损双向、14 个 Agent 协同、移动端可用、skipped/degraded 等同成功。

只有同时满足以下条件才允许覆盖 root README：

1. OBJ-01–07 全部达到退出门，OBJ-08 的 frozen candidate 已完成逐声明证据审计；P0 全 CLOSED，残余 P1 有隔离、owner、用户书面接受并进入 Known limitations；
2. 冻结 clean RC SHA，整体 CI、活动插件、完整 backend、OpenSpec strict、spec sync、pre-commit 与 required checks 全绿；
3. J01–J10 全部达到 E3，涉及用户价值/视觉的旅程达到 E4；
4. 14 天 dogfood、Lance 重建、Graphiti replayable matrix 重放、FSRS/ledger 恢复和 activate rollback 达到 E5；
5. README 每条“可用”声明能反查 committed manifest，安装命令从 release artifact 在 clean 环境重跑；
6. ChatGPT 完成脱敏黑盒产品审查，Codex 完成逐声明证据复核；
7. 用户查看旧 README→candidate diff 后，明确批准覆盖 root `README.md`；覆盖、链接/命令复核和证据反查完成后才关闭 OBJ-08。

### 12.8 不可变执行顺序

1. **Phase 0G — Agent 治理 bootstrap**：用户引用精确 envelope SHA 给出第一级 receipt（冻结 HEAD/tree、§12 流程/完成门、S1–S4、GOV-01 方案 A、契约/schema/patch、project config/package/lock 与 resolved toolchain）→ 只读重算 envelope、ownership 与 Claude session census → 仅在该 worktree 无活动 Claude session 时，由 Codex/外部 runner 作为该 receipt 生效后的第一个治理实施写入精确应用冻结 Bootstrap-0 → 验证 target hash、`hooks={}`、无 post-commit push、其余 worktree/refs 不变，不启动/resume Claude → 若获批 envelope 是 `openspec-absent/false`（当前 handoff）则 STOP，工具链变化后先新 envelope/新 receipt；仅 `ready/true` 才在三项 opt-out + `npx --no-install` + network-deny 下创建/strict validate `repair-agent-governance-v2` 并产出 control artifacts → first-stage containment receipt → 用户引用 second outer-envelope SHA/challenge给第二级 receipt → 只按获批 bundles 修复治理链、在 namespaced persistent candidate ref 固化并运行 GOV-T00–GOV-T12；到 candidate clean worktree 才在 network/Graphiti deny 下做 fresh Claude/Codex session 验收 → 独立红队无 BLOCKER/HIGH → `GOV-01-VERIFIED`，Phase 0A 从该 candidate 的 clean execution worktree开始。任一 hash/manifest 漂移都回到用户重批；全程不 push、不读私有 Vault、不写 Graphiti、不修产品代码。
2. **Phase 0A — 用户意图恢复与双审**：仅在 `GOV-01-VERIFIED` 后创建 `annotation-truth-ledger-v2` OpenSpec → schema+checker 联合门 → 用户另行批准 A01 boundary revision → scanner 无上限 census/A01 revision → A02 seed 与原子问题/修正链 → 用户逐批批准全部脱敏标准批或 `final-tail` → ChatGPT 逐题审查 → Codex 对全部回复逐事实复核并完成 reconciliation → 无法外发项由用户对当前 revision 逐项 waiver 或继续脱敏、分歧交用户裁定 → A02 回写并完成 → 最后生成绑定精确 A01/A02 revision 的 A03 Product Intent Contract，由用户确认并锁版。禁止在首批 pack 前锁定 A03。
3. **Phase 0B — 技术真相与安全**：dirty worktree ownership → 第五轮终裁 → CI/Dependency Audit → P0/P1 封闭清单。
4. **Phase 1 — 数据与部署地基**：VaultScope、跨存储身份、new/adopt/rollback、canonical ledgers。
5. **Phase 2 — 核心学习闭环**：信息收集、RAG/Graphiti、出题/FSRS、白板级 Review Projection。
6. **Phase 3 — 产品面与视觉**：Obsidian Review UI、Canvas/Excalidraw、可观察性与恢复 UX。
7. **Phase 4 — Release candidate**：J01–J10、性能/质量基准、恢复演练、用户 UAT。
8. **Phase 5 — Dogfood 与文档**：按冻结协议完成 14 天真实使用 → 冻结 A07 README candidate → 双审 → 用户批准并发布 A08。

任何阶段都不能用后续 UI 掩盖前一阶段的治理或数据不可信。Phase 0G 未过门时，Phase 0A 的 OpenSpec/scanner/ledger 与所有产品实施都被阻断；Phase 0A 未过门时，后续功能设计和大规模修改被阻断。两者都不阻断不产生 repo/外部写入的只读安全审查；私人 vault 原文默认不进入外部模型。

### 12.9 Goal 的最终完成公式

只有下式全部为真，Codex 才可把长期 Goal 标记 complete：

```text
GOV-01-VERIFIED
AND A01 = complete（绑定用户批准的精确 boundary revision/receipt，且边界内来源已完整扫描与对账）
AND A02 = complete（对该精确 A01 revision 完整重放，checker 过门）
AND 全部有效 User 批注在 A01→A02 provenance 链中可追踪
AND 对 CurrentValidCanonicalAtoms(A01.revision, A02.revision) 的每个 atom：
    externally-reviewed XOR external-review-waived(bound_to_same_current_revision, user_signed)
AND 批准 scope 内 active disposition 为 unanswered / decision-needed / deferred 的 atom 数 = 0
AND A03 绑定上述精确 A01/A02 revision/digest，且已由用户确认并锁版
AND OBJ-01–08 全部过门
AND J01–J10 同一 clean RC 无核心 mock/skip 通过
AND 14 天 dogfood 与恢复演练通过
AND 最终 README 每条声明都有 committed evidence
AND 用户批准覆盖并确认产品符合其真实需求
```

否则只能报告当前等级与未闭合项，不得通过缩小 Goal、只写 README 或只跑局部测试宣布完成。
