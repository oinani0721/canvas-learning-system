# Deep Research 分析请求 — 检验白板 v1(诚实版)对抗性审查

## 项目背景

- **系统**:Canvas Learning System(Obsidian Hybrid 路径)。学习数据全部是 Obsidian vault 里的 markdown 文件(`原白板/` 学习白板、`节点/` 概念节点扁平池、`检验白板/` 考察板、`Dashboard.md` Dataview 反馈面板)。
- **被审对象的形态**:两个 Claude Code Skill(`SKILL.md` = 给 LLM 的提示词程序,由 Claude Code 逐 Step 执行,工具受 allowed-tools 白名单约束)+ 一处 TypeScript Obsidian 插件改动(`frontend/obsidian-plugin/src/`,esbuild 打包)。
- **检验白板是什么**:系统灵魂功能 = Karpicke 检索练习(retrieval practice, d=1.50)的**信息隔离主动回忆板**——从原白板挑最薄弱节点,只用用户自己的批注/派生原因出题(绝不读/回显节点定义正文),用户在 md 里手写答,答完静默评分(HARD-SILENT:不当场显分,延迟反馈走 Dashboard)。
- **为什么是"诚实 v1"**:后端 BKT/FSRS 熟练度管道在 4 个独立点断裂(B1 pipeline_token 死锁 / B2 信心从不采集 / B3 节点未注册 mastery store / B4 group_id 跨 vault 污染,详见打包内的裁决文档)。故 v1 刻意**不碰后端 MCP 熟练度链**,用本地 EMA(α=0.5)写节点 frontmatter `mastery_score` + 本地攒 `calibration_log`,并在回执里声明"本地估计、不宣称熟练度驱动有效"。
- **疑问回流双路径**(用户确认"两者都要"):路径① 在检验白板里选中文字 Cmd+Shift+D 派生独立疑问节点(前端从检验白板 frontmatter `selected_node` 重定向,疑问节点的 source_note/derived-from/relationships.target 指向被考原节点而非瞬态检验白板文件);路径② `/quiz-answer` 把答题区的疑问批注(callout)归纳 append 回被考原节点正文(含 AI 判断的原因)。

## 分析议题

检验白板 v1(诚实版)对抗性审查 — 2 个 Skill(start-exam-board / quiz-answer)+ 前端交付3(检验白板派生疑问节点回链被考原节点)+ 真机生成样本 + 三方质量评估。审查:
1. **信息隔离(d=1.50)是否真守住** — SKILL 的 Grep-only 机制(HARD-ISO-1~4)有没有漏洞会把节点定义正文带进出题上下文或回显给用户?
2. **本地 EMA / calibration_log 攒数据方案是否合理** — α=0.5 EMA 作为 BKT/FSRS 占位是否可辩护?calibration_log 结构攒的数据 v2 真能回灌校准闭环吗?
3. **fallback 出题策略(A1 修订后)是否符合学习科学** — 薄弱档(<0.4/占位)单概念 cued recall + 锚点;"辨析邻居"上移 0.4-0.7 档;辨析避开 up/derived-from 父子节点。这套难度门控站得住吗?
4. **疑问回流双路径设计是否成立** — 路径①(前端重定向)+ 路径②(callout 归纳)的分工、数据流、边界(selected_node 缺失回退等)有没有断点?
5. **诚实边界取舍是否正确** — "不碰断裂后端管道、本地占位、明示不宣称有效"这个降级决策,相比"先修管道再上功能",是不是对的工程/产品取舍?

## 打包内容

20 个文件:①被审 Skills(start-exam-board 含 A1 修订/quiz-answer/exam-quick 参照)②前端交付3(ai-linked-doc.ts/main.ts/node-derivation.ts/测试)③真机样本+vault schema 真相(检验白板样本/原白板/节点/Dashboard/config)④设计依据(v1 诚实版设计/管道断裂裁决/熟练度 PRD/开发任务书/三方评估报告)。

## 分析方法

1. 通读 <directory_structure> 建立心智模型;SKILL.md 当"提示词程序"读——它的执行者是 LLM,评估时要考虑 LLM 会不会偏离指令(指令歧义 = 缺陷)。
2. 从真机样本(检验白板/特征值与特征向量-2026-07-05-1815.md)反推执行路径,对照 SKILL 逐 Step 验证。
3. 前端从 main.ts 的 handleAILinkedDoc → runHybridDerivation 追数据流(sourceNoteStem 重定向是关键)。
4. 引用 <file path="..."> + 行号作为证据;每个发现先试图证伪再报。

## 请分析(对抗性框架)

a. **逐项试图证伪我们的核心声明**:(i) 信息隔离守住(检验白板 md 零定义泄漏、出题只用 Grep 定向抽取);(ii) start↔quiz 两 Skill 契约闭合(frontmatter 字段/sentinel/→ 分隔符);(iii) quiz-answer Step 4 的 python 原子写在真实节点变体(mastery/mastery_level/无字段/blockquote 结尾无换行)上无 bug;(iv) 前端重定向让疑问节点正确指向被考原节点且原有 原白板//节点/ 派生零回归。
b. **问题列表**:| 编号 | 严重度(CRITICAL/HIGH/MEDIUM/LOW) | 文件:行号 | 问题 | 建议 |。
c. **学习科学文献对照**:A1 修订(cued recall 降档/辨析门控/父子回避)与 retrieval practice、desirable difficulty、cognitive load、contrasting cases 文献是否一致?有没有更优方案?
d. **盲点猎杀**:我们的三方评估(打包内 2026-07-05-检验白板v1-真机质量评估.md)漏看了什么?特别欢迎:提示词程序的执行漂移风险、多题扩展时的结构隐患、calibration_log 长期膨胀、Obsidian 渲染边界、并发/时序问题。
e. **改善建议**(附具体修法,最好给 SKILL 指令原文级别的替换建议)。

## 额外上下文(已知项,请勿重复报,聚焦新盲点)

- 已知三伤及处置:难度超档(已修 A1)/父子辨析别扭(已修 A1)/`节点/Fundamentals.md:9` 把 eigenvalue 写成 vector 的数据错误(**未修**,用户学习内容待确认;它会污染 quiz-answer 的评分基准——这条的**系统性解法**欢迎建议)。
- B1-B4 后端断点 + v2 待办清单已在设计文档 §五,不必重复。
- 首轮对抗审查已修的 7 缺陷(board_stem/quoted hook/Grep-only/selected_node 重定向/python 原子写/mastery 变体兼容/静默回执)详见评估报告——可验证修复质量,但别当新发现报。
- 检验白板 v1 = 单题闭环;多题/白板级调度/FSRS 到期是 v2。

## 输出格式

问题表格(b 格式)置顶 + 按 5 个议题分章节叙述;每章末给"证伪结论:成立/被推翻 + 证据"。中文回复。
