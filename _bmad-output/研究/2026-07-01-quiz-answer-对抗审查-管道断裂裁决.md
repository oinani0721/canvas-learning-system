# `/quiz-answer` 对抗审查 — 熟练度/校准管道断裂裁决

> 你让我对 `/quiz-answer` 设计的成熟度做对抗性审查。我起了 3 个并行 agent(后端接口现实 / Skill 工程韧性 / 学习科学闭环),**指令是"找它站不住的地方"**,三方独立证据相互印证,我又亲手核验了最要命的几条(file:line 附后)。
> **一句话裁决:`/quiz-answer` 设计不成熟。不是"补几个健壮性"能救——它宣称的"熟练度驱动 + 校准闭环 + 真正有效",在当前代码里从源头就是断的,而且断在至少 4 个相互独立的点。这正是我们反复栽的 G-FAKE 模式(schema/命名像、实际没接线)。你对路A的怀疑完全命中。**

---

## 零、⛔ 先诚实纠正我自己的三处错判(上一份裁决文档的)

对抗审查把我上一份 `...出题设计-ChatGPT核实与裁决.md` 里的三个判断打穿了。我先认错,再往下:

| 我之前写的 | 真相 | 证据 |
|---|---|---|
| "先走**路A**、MVP 够用"(把 4 信号写回 frontmatter) | ❌ **路A 依赖路B**。`query_mastery` 返回体里 `calibration_bias`/`false_mastery_risk`/`fluent_count`/`mastery_level` **一个都没有**,连 `next_review` 都不返回。写回 frontmatter 根本没有数据源。 | `mastery_tools.py` QueryMasteryOutput(39-81):只有 p_mastery/fsrs_stability/fsrs_difficulty/effective_proficiency/interaction_count |
| "`calibration_bias` **信号现成、不用从零造**" | ❌ 值现成 = **死值**。它唯一输入是"作答前信心自评",而两个 Skill + 后端 exam 流程**从不采集 confidence**,`CALIBRATION_RECORDED` 事件在 exam 流程**无 emitter**。它永远拿不到新数据。 | `calibration_tracker.py:217-234` 需 self_confidence;`event_handlers.py:210` handler 存在但 exam 侧无人 publish |
| (记忆里)"5 信号融合是**活的、完整的**" | ❌ live 路径上**实为 2 信号**。`preload_from_calibration_records` **全仓零调用方**(只有 3 处定义),exam_score/calibration/自评三信号永远 inactive,`effective_proficiency` 只由 BKT(0.30)+FSRS(0.25) 归一化。 | `signal_registry.py:180/218/255` 仅定义无调用;`mastery_engine.py:140-142` 只 preload 有 preload() 的 2 个信号 |

**这三条我亲手 grep/read 核实过,不是 agent 转述。**

---

## 一、⛔ BLOCKER — 4 个独立断点(任一不修,功能即空转)

### B1 · pipeline_token 死锁 —— 熟练度更新在 `/quiz-answer` 物理断裂(全案最致命)

三个 agent **各自独立**撞到同一堵墙,我亲验:

- `PIPELINE_STEPS = {"generate_question": ["score_answer"], "score_answer": ["update_fsrs","update_bkt"]}`(`pipeline_token.py:25-28`)
- `update_bkt`(238)和 `update_fsrs`(325)**都强制** `validate_token(pipeline_token, expected_previous_step="score_answer")`,且 `pipeline_token` 是必填 Field(95/121)
- token 的**唯一签发者是 `score_answer`**(`exam_tools.py:567-568`),而 `score_answer` 走 Gemini AutoScorer——正是 Mode D 要绕开的东西

→ `/quiz-answer` 用订阅评分、绕过 `score_answer` 直调 `update_bkt/update_fsrs` → **每次必抛 `PIPELINE_TOKEN_INVALID`**。BKT/FSRS 引擎**永远不会被更新**。叠加 HARD-SILENT(用户看不到失败)= 最坏组合:**用户以为在长期训练,后端熟练度纹丝不动。**

### B2 · 信心自评从不采集 —— 校准闭环没有燃料(你点名的怀疑)

`calibration_bias` 唯一来源 = `record_calibration(node_id, self_confidence, actual_performance)`(`calibration_tracker.py:217-234`)。通读两个 Skill:`/start-exam-board`(草稿 52-97)+ `/quiz-answer`(125-150)**零处采集 confidence**,allowed-tools 也不含 `record_calibration`(该工具其实存在于 `memory_tools.py:249`,是 Skill 没接)。→ 没有信心输入 → 没有新 calibration record → **"过度自信→出反例题"的闭环从源头没燃料**。路A 搬运的是一个**永不更新的死值**。

### B3 · node 身份断裂 —— 即便 token 修好也 not_found

MCP 工具 `get_concept(node_id)` 查的是 Neo4j `EntityNode.mastery_concept_id`(`mastery_store.py:85` MERGE);检验白板 frontmatter 存的是**节点名**(selected_nodes),草稿**没写名→id 解析**。更糟:上游 `ai-linked-doc` 明写"不调后端 API"(SKILL.md:309)→ **vault 节点从未注册进 mastery store** → `get_concept` 返回 None → `not_found, updated=False`(静默 no-op)。**token 修好了照样 not_found。**

### B4 · group_id 落 `DEFAULT_GROUP_ID`(=cs188) —— 违反 C-3 隔离契约,跨 vault 污染

三个 MCP 工具调 `get_concept/save_concept` **全不传 group_id**(`mastery_tools.py:166/254/341`)→ 一律落 `DEFAULT_GROUP_ID`(=`cs188`,`config.py:989`)。项目 CLAUDE.md 的 **C-3 契约明文禁止** writer/reader 拿 DEFAULT_GROUP_ID 走生产路径。→ 所有 vault 熟练度全塌进 cs188,cs61b 的 `recursion` 和数学的 `recursion` 撞进同一 concept_id。**工具连 group_id 参数都不收。**

---

## 二、🔴 HIGH — 会坏但非阻断

| # | 缺陷 | 证据 |
|---|---|---|
| H1 | `update_bkt` 收 `is_correct: bool` **不是 grade**,内部 `grade = 3 if is_correct else 1`(`mastery_tools.py:301/351`)→ **4 档评分坍缩成对/错二值**,Grade-4 的 `fluent_count++` 永不触发 → Level-4 "Mastered"(硬门槛 fluent_count≥2)**永远升不到**。且同一次作答 BKT 拿二值、FSRS 拿真 grade,自相矛盾。 | 已亲验 |
| H2 | **HARD-SILENT = 零反馈,不是延迟反馈**。而 ChatGPT 引的强证据(Smith&Kimball / arXiv 2505.13381)是"**延迟给**解释性反馈"而非"不给"。把 desirable-difficulty 的 delay 误做成 zero,会**削弱**检验白板效果。 | 草稿 122-123/145-149 |
| H3 | HARD-SILENT **名不副实**:答完开 Dashboard 看 mastery 从 0.30 跳到 0.55,等价于"我答对了"——表现照样泄漏。要么延迟掌握度可见,要么显式裁决"防的是考中偷看,不是即时反馈"。 | 逻辑 + 白板 dataviewjs 读 `mastery_score` |
| H4 | frontmatter 字段名读写全错:真实节点是 `mastery_score`,Dashboard dataviewjs 读 `n.mastery_score`;草稿写回 `mastery_level`(新造字段)→ **Dashboard 永远看不到**。 | 实测 `canvas-vault/节点/*.md` + 白板模板 |
| H5 | 无幂等守卫:同一张白板跑两次 `/quiz-answer` → 重复评分、重复更新(BKT/FSRS 双写)。`status: in_progress` 全程没被置 `done`。今天因 B1/B3 侥幸 no-op,**B1/B3 一修好双写立刻成真**(定时炸弹)。 | 草稿无 status 守卫 |

---

## 三、🟡 MEDIUM

- **M1 · 答案提取正则太脆**:多行答案 / 答案含 `>`(如"h(n) > h*(n)")/ callout 格式漂移(去 `+`、加空格)/ "最后一个 callout" 多题时不可靠 / 占位符防不住半成品答。建议靠 `questions[q1].id` + sentinel 注释定位,别靠 `> 答:` 行前缀。allowed-tools 还缺 Glob/Grep(连"哪张检验白板/哪个节点文件"都定位不了)。
- **M2 · 单题即停 vs 检索练习剂量**:calibration 需 ≥10 条脱离 INSUFFICIENT、≥3 条信号才非 None;BKT 按 interactions/10 算 reliability。**单题首版既喂不出收敛、也测不出真实检索练习效果**——作为工程边界 OK,但**不能用它"验证检验白板有效"**,只能验"管道跑通"。
- **M3 · 单次运行职责过载**:提取答案→读正文→4维评分→算grade→调3个MCP→写回两文件frontmatter,路A 再加 5+ 字段。建议拆:`/quiz-answer` 只管"提取+评分+写score+置done"(纯 vault,确定能成);熟练度更新拆成独立步骤走完整管道 + 显式处理 not_found/token 失败。

---

## 四、重新裁决 + 必补清单(按阻断性排序)

**ChatGPT 那张漂亮的"熟练度→Bloom→题型决策表"先别接——它的输入(calibration_bias / mastery 演化)在当前代码里全是断的。** 要么先修这 4 条管道,要么诚实降级首版。

**若要打通"熟练度驱动"(必补,排序):**
1. **【阻断·架构】拆 pipeline_token 死锁(B1)**:给 Skill 开一条**免 token 的静默更新入口**(新 MCP 工具 `submit_silent_grade(node_id, grade, group_id)` 直接喂 `update_on_interaction` 一次,内建 faithfulness/退化校验),或让 token 校验接受"订阅评分"来源。
2. **【阻断·隔离】mastery MCP 工具加 group_id 并贯穿 store(B4)**,用 `build_vault_group_id()` 构造。
3. **【阻断·身份】node 名→mastery_concept_id 解析 + 保证 vault 节点注册进 mastery store(B3)**。
4. **【燃料】采集信心自评(B2)**:`/start-exam-board` 出题前采集 confidence,`/quiz-answer` 评分后调 `record_calibration`(该 MCP 工具已存在,只需接)。
5. **【路A 前提】扩 `query_mastery` 返回体**:加 calibration_bias/false_mastery_risk/fluent_count + 补 mastery_level/next_review(这几个后端都已算好,见 `mastery_engine.py:638-689` 的完整档案函数,子集回填即可)。
6. **【完整性】收口 grade 坍缩 + 双工具重复计数(H1/H5)**:方案 1 的单一静默入口可一并解决。
7. **【接线】把后端 `/mcp` 注册进客户端 MCP config**(当前 `.mcp.json` 无 canvas-learning-mcp,`mcp__canvas-learning-mcp__*` 现在根本解析不了)。

**若诚实降级首版(honest MVP):**
- v1 = **纯信息隔离主动回忆 + 手写答**(HARD-ISO 是真的、d=1.50 命脉成立)+ 本地写 `mastery_score`,**不碰 MCP 熟练度链**。
- **明确标注"熟练度驱动 + 校准闭环 = 管道未通,暂不宣称有效"**,不做 G-FAKE 式过度承诺。
- 顺手在 v1 就**采集信心自评**(即便还不接后端),为 v2 攒 calibration 数据。

---

## 五、验证过的关键证据(file:line)

- `pipeline_token.py:25-28`(PIPELINE_STEPS)· `mastery_tools.py:238/325`(强制 token 校验)· `exam_tools.py:567-568`(token 唯一签发者)—— **B1 亲验**
- `signal_registry.py:180/218/255`(preload_from_calibration_records 仅定义)· grep 全仓**零调用方** —— **"2 not 5 信号" 亲验**
- `calibration_tracker.py:217-234`(需 self_confidence)· `event_handlers.py:210`(handler 有、exam 侧无 emitter)· `memory_tools.py:249`(record_calibration 工具存在但 Skill 没接)—— **B2 亲验**
- `mastery_tools.py:301/351`(is_correct→grade 3/1 坍缩)· QueryMasteryOutput 无 4 字段 —— **H1 + 路A 亲验**
- `mastery_store.py:85`(MERGE on mastery_concept_id)· `ai-linked-doc/SKILL.md:309`(不调后端 → 节点未注册)—— **B3**
