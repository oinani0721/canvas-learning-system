# UAT 验收单 — CARD-G4-4 full RAG 显式 VaultScope

> ⚠️ **CARD-G4-4a 移植注（2026-09-04）**：本文件由 `card/w8-scope` 逐条
> cherry-pick 到 `card/x3-vaultscope`。按 CARD-G4-4a 完成条件 (j)，随卡
> 证据只带 `evidence-g44/g44_mutations.py` 与 `evidence-g44/mutation-run.txt`；
> 下文引用的 `final-judge1.txt` / `final-judge2.txt` / `baseline-judge*.txt`
> 与三份 `codex-review-*.stderr` **未随卡入库**（`*.stderr*` 属公共纪律禁入库项，
> judge 输出体积大且已被 4a 自身裁判输出取代）。其原文数字已逐字保留在本文
> 正文（`collected 80 items` / `3 failed, 76 passed, 1 xfailed` / API `99 passed,
> 166 deselected`），原件仍在 `card/w8-scope@6a732e1b` 可查。4a 自身的裁判
> 输出见 `UAT-CARD-G4-4a-显式VaultScope-2026-09-04.md`。

> 批次: BATCH-2026-09-01-第八批 · 车道 W8 · 分支 card/w8-scope
> 卡文: `第八批-goals/W8-2.md` · 工时 11h
> commits: ca116f51 (核心) → a3c41075 (适配) → cee863a0 (透传门+证据)
> → aaecf696 (Codex round-1 整改) → 本验收单 commit
> Codex 审查: round-1 REJECT (2B/多H) → 整改 → round-2 见
> `_bmad-output/审查/codex-review-CARD-G4-4.md` 追加段

---

## ⛔ 先读：两条显著声明（影响你判断要不要批这张卡）

1. **这是一次契约破坏（卡文裁决①，默认值非已批）**：`/rag/query` 的
   `vault_id` 从「没有这个字段」变成**必填且不能是空白**。任何在
   2026-09-01 之前写的、直接调用 `/api/v1/rag/query` 的外部脚本（如果
   存在）都会开始收到 422，必须补 `vault_id` 才能恢复。已核实本仓库内
   （canvas-vault/.claude、obsidian 插件、后端自身）**零外部调用方**，
   插件 main.ts 只调 agents/dialog、exam、tips、vault 端点——但如果你
   有仓外脚本在调它，请告诉我。
2. **agents 端点保留了「不传 vault_id 就用当前激活库」的既有行为**
   （裁决②）。⚠️ 卡文给的推理「插件 agents/dialog 依赖它」**被仓库事实
   反证**：`frontend/obsidian-plugin/src/main.ts:360-366` 明确记录该命令
   及其调用的不存在端点已删除。保留的真实理由是：双缺失推导是 G2-2
   在 2026-08-28 显式裁定的兼容层（`vault_scope.py` 契约 3），本卡一刀
   切 fail-closed 会一次改 12 个端点的对外行为，超出本卡边界。**是否
   收紧 agents 端点为缺参 fail-closed，升级为你的裁决点**（见 §6-②）。

---

## 1. 🎯 一句话目标

让 AI 检索「先选库再查书」：检索前必须明确说清用的是哪个笔记库，杜绝
A 库的问题查到 B 库的笔记。

## 2. 📖 你的视角

作为学习者，**我想让 AI 找资料时永远只在我当前学习的库里找**，以便它
不会把**别的库**的笔记混进答案、也不把我没学过的内容当成本库的记忆。
（⚠️ 范围如实声明：本卡证明的是**不跨库**；同库内跨学科的邻居扩展过滤
是已登记的已知边界，见 §未证明 #3——本卡不承诺跨学科隔离。）

## 3. 🖥️ 交互流程（你的屏幕变化）

1. 你在 Obsidian 里正常向 AI 提问（走插件对话/解释/拆解）——插件本来
   就会告诉后端「我在哪个库」，所以**你的操作完全不变**。
2. 变化在水面下：以前检索作用域有时「没说清」，可能落到默认桶（等于
   什么都查不到）、跨库、或从无主的老表里捞内容；现在每次检索都强制
   「报名字」，名字含糊或报错直接拒绝。
3. 如果你绕过插件直接调接口：不带库名（含空白串）→ 拒（422）；带了
   别的库的名字 → 拒（409），不会悄悄替你换库。

## 4-A. 🤖 Claude 已代验（全部代跑，✅ = 有证据）

| # | 判据 | 结果 | 证据 |
|---|------|------|------|
| 1 | 裁判1 四文件 pytest：开工基线实收 45（30+15，其中 3 条 lancedb 存量红）→ round-3 整改后 **76 passed + 1 xfailed（subject 邻居泄漏已知边界锁）+ 同样 3 条存量红**（80 collected；xfail 收紧 strict=True 后数字不变） | ✅ | `evidence-g44/final-judge1.txt`（aaecf696 后重跑归档） |
| 2 | 裁判2 `pytest tests/api -k 'rag or agents' --deselect test_agents_dedup.py`：基线 77 passed → round-3 整改后原始 99 passed（**含并发 OBS 车道 4 条**），排除 OBS 后可比口径 **95 passed 全绿**，comm 零新增失败（排除并发 OBS 车道的 test_nothrow_logging_api.py——其在本卡裁判首跑时已被并发引入，基线不存在，非本卡回归） | ✅ | 三份 -rA 输出归档 |
| 3 | 裁判3 grep 门：`DEFAULT_GROUP_ID\|get_current_vault_id` 在 rag.py / nodes.py / agents.py **0 命中**（豁免清单按卡文只含 exam_service.py / verification_service.py） | ✅ | rc=1 实测 |
| 4 | 裁判4 禁改门：chat.py / note_search_tools.py / lancedb_client.py / supplementary_search_service.py / exam_service.py / verification_service.py / rag_service.py 在本卡分支零改动（rag_service.query 签名未动） | ✅ | git log --name-only 空 |
| 5 | 裁判5 两新测试文件 `with TestClient(app` **0 命中**（无生命周期夹具，不连 7691） | ✅ | rc=1 实测 |
| 6 | 裁判6 rag.py f-string 日志门：当前 0 处 ≤ 开工基线 7（0 是并发 OBS 车道 78c9e6e7 把存量 f-string 日志 nothrow 化重写的结果；本卡新增日志全部惰性参数 + notry） | ✅ | 实测 count=0 |
| 7 | 变异 **8/8 各杀指定门**（v2 脚本，判据 = pytest exit==1 才算杀）：M1 去422 / M2 去409恢复旁路 / M3 内链改回进程级 / M4 fixture同组化 / M5 哨兵真降级 / M6 expand裸表旁路 / M7 空白validator失效 / **M8 扩展恒等失效（杀 round-2 活性门 — Codex 指出恒等函数下旧门仍绿）**；还原逐字节一致（SHA） | ✅ | `evidence-g44/mutation-run.txt`（v2, 8 变异） |
| 8 | 双 vault 真库隔离：同一 tmp LanceDB 库三表共存（A/B 前缀表 + **裸 legacy 表**）——A 检索 0 条来自 B、0 条来自裸表、正向对照、反向对称、同名不同内容只回本库版本、**wiki-link 邻居扩展不越界**（裸表 b_secret 泄漏探针 + **source_type=neighbor_expansion 活性断言**——扩展被恒等替换时门必红，M8 实证） | ✅ | 6 条隔离门全绿；裸表反例即 Codex round-1 BLOCKER-1 的生产复现，整改后转为本卡永久门 |
| 9 | 新增 35 collected = 34 passed + 1 xfailed：API 面 18（422 含空白×3 / 409 / ContextVar 注入 / 契约加性 / agents scope_source 三值）+ 单元 17（内链请求级 / current_vault_id 行为 / 哨兵 / 隔离×7 / subject 透传 / subject 泄漏边界 xfail） | ✅ | 34 passed + 1 xfailed |
| 10 | 空白 vault_id 契约（Codex round-1 HIGH-2 整改）：`""`/`"   "`/`"\t\n "`/全角空格 全部 422 且服务零调用 | ✅ | validator + 参数化用例 |

## 4-B. 👤 你来验（产品体验，3-5 分钟）

⚠️ **诚实边界（Codex round-2 指出）**：插件目前**没有**接 full-RAG 提问
路径（agents/dialog 已删、chat-with-context skill 未走 /rag/query），所以
本卡在 Obsidian 里**没有可直接操作的可感变化**——你日常用插件不会有任何
不同（这本身就是验收点：隔离收紧零误伤）。可感验证只有一条：

- [ ] （仅当你有仓外脚本直接调检索接口）我跑一下我的脚本 → 我看到它
      提示需要补一个库名参数 → 我感觉系统在逼我把话说清楚，而不是乱猜。
      没有脚本就跳过这条，勾「不适用」。

未来插件接入 full-RAG 时，本卡的「先选库再查书」约束会自动生效。

## 5. 🚦 验收结果

- Claude 侧技术验收：**全绿**（判据 1-10 + 变异 8/8）。
- Codex round-1 REJECT 的 2 BLOCKER + HIGH 已整改（见 §「与卡文偏差及
  round-1 整改记录」）；round-2 复审结论见审查存档。
- 等你勾完 4-B + 对 §6 裁决点表态后，本卡才算通过。

## 5.5 ⛔ Codex 三轮到顶声明（卡文停轮规则，必须显著）

- round-1 REJECT（2 BLOCKER + 多 HIGH）→ round-2 REJECT（1 残留 HIGH +
  1 新发现 HIGH + 声明类）→ round-3 REJECT（剩余项全为**声明宽于证据**
  类 + 登记完整性，**无新的生产代码缺陷**；3 项 PASS 含 BLOCKER-1 活性
  门与 8/8 变异独立复跑）。
- **三轮上限已到，未清零。按卡文规则：本卡不合并、留台账。**
- round-3 剩余项（全部已整改或登记，本轮 commit 收口）：
  1. subject 邻居泄漏登记不完整 → xfail 收紧 strict=True + physics 行补
     subject 列 + 请求作用域带二级（更贴生产形态）；台账 G4-4-R1 登记。
  2. UAT §2 跨学科承诺与 §未证明 #3 自相矛盾 → §2 已加范围声明。
  3. 收官裁判数字：80 collected（非 79）已更正；裁判 2 双口径（99 原始
     含 OBS 4 条 / 95 排除）已注明。
  4. 「邻居扩展与主链同源同表」过宽 → 收窄为「无 course_id 分支」；
     course_id 分支脱节登记台账 G4-4-R1。
- **决策建议**：剩余项均属「已知边界登记 + 声明精确化」，不是新的跨
  vault 生产缺陷；BLOCKER 级（裸表旁路/空白 vault_id）已修并有变异门。
  是否接受「带台账合并」由你裁决（§6-⑦）。

## 6. 📝 批注区

[!question]+ 待你裁决（卡文默认裁决①-⑤ + round-1 新增，均为默认值非已批）

- **① `/rag/query` 的 vault_id 必填（本卡最大契约变化）**：缺/空白 →
  422，显式不一致 → 409。仓内零调用方已核实；若你有仓外脚本调它需补
  参数。若不同意必填，退路是改回 Optional + 缺省 409 拒绝（更狠）或缺
  省推导 active vault（更松）——请表态。
- **② agents 端点保留「双缺失推导 active vault」**。⚠️ 卡文原推理
  「插件 agents/dialog 依赖」已被 main.ts:360-366 反证（该命令已删）；
  保留的真实依据是 G2-2 既有裁定 + 避免本卡一次性改 12 个端点对外行为。
  加性响应头 X-Vault-Scope-Source 透出来源。**新裁决子项**：要不要在
  后续卡把 agents 端点也收紧为缺参 fail-closed？（插件既不依赖，收紧
  的破坏面比卡文撰写时预想的小。）
- **③ rag_service.query 签名不变**，作用域经 ContextVar 注入、内链读
  vault_scope——技术路线确认。
- **④ G4-3b（状态词汇对齐）不吸收**，登记「G4-4 合并后开」为独立卡。
- **⑤ 过渡期判据**：test_agents_dedup.py（真连 7691）deselect，待
  CARD-TEST-isolate-lifespan 合入主干后由主 session 补跑。
- **⑥（round-1 新增）邻居扩展表源统一**：expand_neighbors 原查裸
  vault_notes 表、与主链检索表（canvas_nodes 系）脱节，本卡在**无
  course_id 分支**统一为主链同表；⚠️ 有 course_id 的分支主链查
  vault_notes、扩展仍查 canvas_nodes 系（round-3 指出），该分支的
  统一与 subject 过滤一并移交（台账 G4-4-R1）——若你观察到「AI 引用
  的关联笔记」行为变化，回报这里。
- **⑦（round-3 新增）三轮到顶带台账合并与否**：Codex 三轮终态
  REJECT，剩余项为登记类（见 §5.5）。接受「带台账 G4-4-R1 合并」
  还是要求 R1 收口后再合并？

[!error]+ 历史追溯

- [!error]+ v1 → v2（Codex round-1 REJECT 整改, commit aaecf696）
  - BLOCKER-1 邻居扩展裸表旁路 → nodes 侧同源解析 + 表源统一 + 泄漏
    探针门（M6 杀）。
  - HIGH-2 空白 vault_id 绕 422 → 模型层 validator + 3 形态用例（M7 杀）。
  - HIGH-4 本卡回归 test_recommend_action.py **9 处**（裁判 2 的 -k 选择面
    没覆盖该文件名）→ 补适配；第 10 处（mock 裸 Exception）经 Codex 独立
    复核实证**开工前已红**（ca116f51^ 即 1 failed），属存量红非本卡引入，
    一并适配并修正 mock 类型
    （handler 只优雅降级预期依赖故障是设计行为，测试意图不变）。
  - HIGH-5 验收单声明不实（理由/数字/覆盖面）→ 本 v2 全文重写。
  - HIGH-7 变异证据缺陷 → 脚本 v2（exit==1 判据 + M5 真降级）+ 归因
    更正：v1 的 M5 exit=4 是**脚本 gate 路由 bug**，此前归因「并发抖动」
    有误。

- [!error]+ v2 → v3（Codex round-2 REJECT 整改）
  - round-1 BLOCKER-1 残留：活性对照是假绿（a_neighbor 本在主检索表,
    扩展结果被去重, 恒等函数下门仍绿）→ 活性判据改为 source_type=
    neighbor_expansion 断言 + fixture 加干扰行把 a_neighbor 挤出主检索
    top + **M8 恒等变异实证杀门**。
  - 新发现 HIGH 同 vault 跨 subject 邻居泄漏 → expand_neighbors 不传
    subject 属 client 禁改面, xfail 锁边界 + 移交登记 + 撤回跨学科
    级别声明（见 §未证明 #3）。
  - 数字/归属更正：recommend_action 本卡回归 9 条非 10（第 10 处开工前
    已红, Codex ca116f51^ 独立复跑实证）；新测试 35 collected = 34
    passed + 1 xfailed；4-B 重写（插件无 full-RAG 提问路径, 可感验证
    受限如实声明）；§6.5 d/a 行更正（rag.py 属独占面/响应头客户端
    可读但不受影响）。
  - 交付完整性：收官裁判输出（aaecf696 后）已归档 final-judge1/2.txt；
    数字与 Codex 独立复跑对齐（76+1x+3 存量红 / API 99 passed）。

## 6.5 与卡文偏差及 round-1 整改记录（逐条，防「声明比证据宽」）

| # | 偏差 | 理由 | 测试/证据 |
|---|------|------|----------|
| a | scope_source 透出形态 = **HTTP 响应头** `X-Vault-Scope-Source`，非卡文含糊的「加性透出」（未指明形态） | schemas.py 不在本卡独占面；响应模型加字段会进 openapi 契约面（W4③ 债未清）。**该响应头未进 openapi/响应 schema**——HTTP 客户端技术上可读取该头，但旧客户端不解析未知头，行为不受影响 | test_rag_vault_scope_api.py::TestAgentScopeSourceHeader |
| b | 卡文写的三值名 explicit/legacy_group_id/derived_active 与 VaultScope.source 实际值域**不同名**。逐对映射：explicit→`request-vault`；legacy_group_id→`legacy-group`；derived_active→`active-vault`（hook-cwd 值域 rag/agents 端点不产生） | 值域以 vault_scope.py:84-86 实际为准，不造第二套词汇 | 同上三值用例 |
| c | 卡文预写「vault:default 污染桶抛 VaultScopeUnresolved 属预期」与代码不符：`current_vault_id()` **无形状校验不抛**（fail-closed 属 require_read_group 读侧职责） | 不为凑卡文造校验层（会改 vault_scope 本体或造第二真相源，均禁改） | test_pollution_bucket_returns_default_segment_without_raising |
| d | 最小适配 3 个**既有测试文件**（均不在独占清单也不在禁改清单）：test_rag_four_state_api（vault_id 必填后 26 用例必 422）、test_agents_learning_event（11 用例 handler 直调 TypeError）、test_recommend_action（**9 条**本卡回归 + 1 条开工前已红的存量红，Codex round-1 抓出漏网）；另 rag.py 新日志补 notry——**rag.py 本身在本卡独占面内**，该项是独占面内的实现修正而非跨面适配。断言语义零改动（机械适配）；仅 recommend_action 1 处 mock 异常类型改 RuntimeError（理由见 §6 error 区） | 跨面范围以卡文独占/禁改清单为准 | 各文件 commit a3c41075 / aaecf696 diff |
| e | agents 作用域解析调用点实为 **7 处**（卡文语境的「8 个」不准；含 _call_explanation 覆盖 6 个 explain 端点），响应头覆盖 = **12 个带作用域解析的 POST handler**；/agents/health 无该机制（它不做作用域解析），409 失败响应无头 | 数字以代码为准 | agents.py 7 处 `response.headers[...]` |
| f | 邻居扩展表源从裸 vault_notes 统一为主链表（canvas_nodes 系）| 卡文未预见；Codex round-1 BLOCKER-1 整改 | 裁决点⑥ |

## 7. 🔗 技术 spec 引用（给 Claude 读）

- 卡文: `feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W8-2.md`
- 总账 v2: §二 G4-4 + §四 L1↔L10 改组决议 (b)（exam/verification 豁免=G5-12）
- 范式: chat.py:284-296（resolve_vault_scope 每请求一次 + 409）
- 改动: rag.py（vault_id 必填+空白 validator+resolve+删旁路+notry 日志）/
  nodes.py（compress_context 读 current_vault_id+三节点哨兵+expand 表源统一）/
  agents.py（7 调用点+X-Vault-Scope-Source+12 handler response 注入）
- 测试: test_rag_vault_scope_api.py (18) + test_agentic_rag_vault_scope.py (17, 含 1 xfail)
  + 适配 test_rag_four_state_api / test_agents_learning_event / test_recommend_action
- 证据: `_bmad-output/审查/evidence-g44/`（裁判基线/收官 + 变异 v2 脚本与运行输出）
- Codex: `_bmad-output/审查/codex-review-CARD-G4-4.md`（round-1 REJECT 存档 +
  round-2 追加段）+ prompts/codex-prompt-CARD-G4-4.md

---

## ⛔ 本卡未证明什么（必填段，防止「声明比证据宽」）

1. **test_agents_dedup.py 未跑**（真连 7691，卡文裁决⑤）——待
   CARD-TEST-isolate-lifespan 合入主干后由主 session 补跑。
2. **rag_service 全图未真跑**：检索作用域链按「端点 resolve 注入
   ContextVar → 节点读 ContextVar → 表名（含邻居扩展同源）」分段真链
   证明（各段全绿 + 泄漏探针门），但没有起真 LangGraph 全图——防多查询
   重写节点触发真实 LLM 外发调用。
3. **同 vault 跨 subject 的邻居扩展过滤未做**（Codex round-2 新发现
   HIGH）：expand_neighbors 不传 subject，wiki-link 邻居按 canvas LIKE
   匹配整张 vault 表——math 请求可能经邻居扩展带入同 vault 内 physics
   板内容（Codex 真库反例实证）。收口需改 expand_neighbors 签名
   （lancedb_client，V5 未合禁改面），**登记移交（台账 G4-4-R1）**；
   本卡以 `test_neighbor_expansion_respects_subject_boundary` xfail
   （**strict=True**）锁住该已知缺陷（收口后转正为门），并撤回任何
   「不混入别的学科笔记」级别的声明——本卡证明的是**不跨 vault**，
   不是不跨学科。另：有 course_id 的检索分支主链查 vault_notes、邻居
   扩展查 canvas_nodes 系（round-3 指出的表源脱节残留），与 subject
   过滤同批移交。
4. **bge-m3 真实向量语义质量未测**：embed 打桩固定向量，隔离不依赖向量
   （B 笔记物理上不在 A 的候选集/表）。
5. **LanceDB 读侧裸表回退（B0.7）仍在**（lancedb_client.py:732-759，
   V5 未合禁改面）：前缀表缺失时 resolve 会回退读裸表——「A 库从未索引
   过」的边界下仍可能触达裸表内容。本卡已把**触发面**收窄（主链与邻居
   扩展同源解析、泄漏探针门护住 A 表在位场景），但回退语义本身的收敛
   属 lancedb_client owner（V5 或另立卡），**本卡未修**。
6. **Graphiti 侧二级组错桶**（Codex round-1 HIGH 子项）：检索节点传
   legacy subject/canvas 值、graphiti_client 内部又从进程级 vault 重建
   物理组（graphiti_client.py:381-420）——组一致性归 G4-5「语义 episode
   写读组对称」（owner 卡）；Codex 实证其为二级组错桶、非 /rag/query
   跨 vault 泄漏，本卡不扩大声称、未修。
7. **裁判面之外的既有 rag 调用方适配**：tests/integration/
   test_rag_multimodal_api.py（10 处 POST）与 tests/regression/
   test_production_bugs.py（1 处空 body POST）不在裁判面，必填后会
   422——登记遗留，待统一适配；openapi.json 快照滞后（W4③ 债，
   spec-sync hook 在 commit 时自动重导出）。
8. **test_lancedb_vault_isolation.py 的 3 条存量红**：yaml 稳定 ID 压过
   reload_settings 的环境耦合，开工即红，非本卡引入，未修（超范围）。
9. **表名行为变更未做现网验证**：ContextVar 注入形态从「裸 subject_id
   或不注入」变为「group_id 恒注入」，LanceDB 表解析统一到 vault 稳定
   ID 命名空间。带 subject_id 的旧请求原解析路径不再可达——生产数据若
   散落在 subject 前缀表中，检索面会变化。本卡仅以测试证明新链正确，
   未验证现网 LanceDB 表分布（属部署面）。
10. **并发车道交错**：本 worktree 期间有 DEBT-8 收尾 session 与 OBS
   nothrow-logging 车道并行作业。OBS 的 rag.py nothrow 改写已在其
   commit 78c9e6e7 落地（先于本卡 round-1 整改 commit），两车道 rag.py
   改动已共存验证（本卡裁判在 78c9e6e7 之上全绿）；d6a5e697 /
   ec62828e 归 DEBT-8 车道。四卡在分支上的交错历史待主 session 合并时
   按 commit 标记辨识。
