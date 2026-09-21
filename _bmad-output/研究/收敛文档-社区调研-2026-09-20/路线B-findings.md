# 路线 B 探索：查漏补缺的覆盖度量化（Q2「我漏了什么」怎么量化 + 目标基准）

> 任务边界：**只收集**，不评 CLS 设计、不改任何代码/skill、不做终审。
> 本文件所有条目均带出处；社区来源（D 级）单独标注来源与日期；无法验证的内容列入「未验证清单」，不当作事实使用。
> 撰写日期：2026-09-20（America/Los_Angeles）。抓取方式：Exa 检索（via agent-reach/mcporter）+ r.jina.ai 正文抓取 + Europe PMC REST + pdftotext。

## 证据等级标尺（本文件自定）

- **A** = 一手方法学标准/手册/官方指南（PRISMA、Cochrane Handbook、JBI Manual、Campbell 官方指南、Cochrane 系统综述）
- **B** = 同行评议方法论文/系统综述/技术报告（期刊论文、CRESST 技术报告）
- **C** = 工具官方文档（Rayyan、Covidence、Obsidian、Dataview、EPPI 官方教程）
- **D** = 社区来源（插件目录、第三方统计站等）——必须带来源与日期

---

# 第一部分：覆盖度/缺口量化方法（10 条）

约定：每条按固定字段顺序 —— 方法/指标名 · 一句话定义 · 如何测量 · 适用问题 · 证据等级 · 链接+日期 · 迁移到 CLS 的具体形态（≤2 句） · 反例/失败边界。

---

## M1. PRISMA 2020 流程图计数（Flow diagram counts / 筛选漏斗计数）

- **一句话定义**：把"识别→筛选→纳入"每一阶段的记录数（含重复去除数、各阶段排除数及理由）逐一计数，画出流程漏斗。
- **如何测量**：
  - 按官方 4 套模板选择（新/更新综述 × 仅数据库与注册库/含其他来源），逐格填报；
  - 关键计数：records identified（分来源）→ duplicates removed → screened → excluded（含 full-text 排除按理由）→ studies included；
  - 中间量：duplicates removed = identified − screened；"studies awaiting classification" 等特殊类别也计入流程图（Cochrane Handbook 明确要求）。
- **适用问题**：量化"检索与筛选管线中每个阶段的丢失量"，给排除理由分布；不能直接量化"未被检索到的存在"。
- **证据等级**：A（PRISMA 官方模板；PRISMA 2020 声明）＋ A（PRISMA-ScR，用于 scoping review 的对应条目）＋ A（Cochrane Handbook 对该图的要求）。
- **链接+日期**：
  - https://www.prisma-statement.org/prisma-2020-flow-diagram （无发布日期；访问 2026-09-20）
  - https://www.bmj.com/content/372/bmj.n71 （2021-03-29，PRISMA 2020 声明）
  - https://doi.org/10.7326/M18-0850 （2018-09-03，PRISMA-ScR；item 17「Selection of sources of evidence」、item 20「Results of individual sources」、item 24「Summary of evidence 需与 review question(s) 对齐」）
- **迁移到 CLS 的形态**：把收敛文档写成漏斗表：候选材料数 → 去重后 → 可支撑条目 → 已引用/未引用，附"未引用理由"分类计数。
- **反例/失败边界**：只统计"你处理过的"记录，不能发现从未被你搜索/收集到的内容；工具侧还有两个官方警示——Covidence FAQ 指出筛选未完成时数字会变、合并 study/reference 后口径会变；Covidence DOCX 中"Studies not retrieved"默认自动为 0，需手工修正（见 M6）。

---

## M2. 相对召回率 / 敏感性（Relative recall / search sensitivity vs benchmark set）

- **一句话定义**：用一个"事先已知应当被包含"的基准条目集合（benchmark/sentinel set）做分母，计算你的检索/收集命中其中多少（=相对召回率）。
- **如何测量**（据 2025 实践指南 6 步）：
  1) 先建 benchmark set：从既往综述、个人收藏、引文追踪等多来源收集，专家复核（**不要**用待评估的检索源本身来建）；
  2) 在待评估库中按 ID（DOI 等）用 OR 拼出基准检索串 StringB；
  3) 跑目标检索串 StringA；
  4) 用 `(StringA) AND (StringB)` 取交集，得命中数；
  5) **SEN = |StringA ∩ StringB| ÷ |StringB|**（按库分别算或合并算）；
  6) 对未命中条目用 `(StringB) NOT (StringA)` 反查原因并迭代修正。
- **适用问题**：存在"已知必含清单"时，量化"漏了哪些、漏了多少比例"；可反复迭代改进检索/搜集策略。
- **证据等级**：A（Cochrane Handbook §4.4.11 将其列为停止/自查方法之一）＋ B（2025 实践指南；2006 真实案例）。
- **链接+日期**：
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC12621535/ （2025-03-07，Research Synthesis Methods）
  - https://doi.org/10.1186/1471-2288-6-33 （2006-07-18，BMC Med Res Methodol 6:33；PMC1557524）
  - https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-04 （§4.4.11；访问 2026-09-20）
- **真实案例（2006）**：用 105 个 Cochrane 综述的**纳入研究**作参照集，测 3 种方法学检索策略对 MEDLINE 收录研究的相对召回，结果 .98–.91；并测得 72% 的纳入原始研究被 MEDLINE 收录。
- **迁移到 CLS 的形态**：让用户（或既有教材/考纲）给出"必含条目"清单，计算收敛文档对清单的覆盖率，并列出未命中清单供人工裁定。
- **反例/失败边界**：Cochrane Handbook 明确警告——"仅仅命中所知条目"反而是检索偏向已知研究的信号，可能仍在漏其他文献；benchmark 不具代表性时结果无意义；无统一合格阈值；基准过小不精确（检索过滤器研究用过 15–1347 条，最优样本量未定，2025 指南自己承认）；相对召回可能高估敏感性（若源综述本身漏检，Doustand 情况被 2006 文引用）。

---

## M3. 捕获-再捕获 / 截距交叉（Capture-recapture / capture-mark-recapture；又称 COMMA）

- **一句话定义**：用两个（或多个）独立来源之间的**重叠比例**，估计"总共有多少"，再减去已找到的，即为**漏掉的数量估计**。
- **如何测量**：
  - 最大似然估计：`N = M × n / m`（M=来源1命中，n=来源2命中，m=两者都命中）；漏检 = N − (M + n − m)；
  - 小样本改用 Chapman 估计：`N = (M+1)(n+1)/(m+1) − 1`，可算 95% CI；
  - 来源依赖性明显时用泊松回归/boosting 等模型（2011 论文的改进路线）。
- **适用问题**：多来源搜集（数据库 vs 手检、两个库、两个独立列表）后问"还有多少没被发现"；也被用于"何时停止检索"研究。
- **证据等级**：A（Cochrane Handbook §4.4.11 引用并描述）＋ B（1996 BMJ 原始案例；2011 J Clin Epidemiol 方法改进）。
- **链接+日期**：
  - https://doi.org/10.1136/bmj.313.7053.342 （1996-08-10，BMJ 313:342-343）
  - https://doi.org/10.1016/j.jclinepi.2011.03.008 （2011-06-17 电子版；J Clin Epidemiol 64(12):1364-72）
  - https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-04 （§4.4.11；访问 2026-09-20）
- **真实案例**：1996 BMJ 对《Diabetic Medicine》1984–1994 的 MEDLINE 检索 vs 手检：估计总数 160（95% CI 158–164），"漏掉"约 2 条（0–6）；2011 年两例（消化病学/血液学）用不同模型得到漏检 82（52–128）vs 127（86–186）、140（116–168）vs 188（159–223）。
- **迁移到 CLS 的形态**：用两类独立来源（如白板条目 vs 笔记/教材目录）做重叠估计，输出"估计盲区总量 + 置信区间 + 已漏清单"。
- **反例/失败边界**：**正相关 → 低估，负相关 → 高估**（1996 原文 caveat）；Cochrane Handbook 指出该方法"至少需要两次检索的结果"；2011 案例显示**模型选择会让估计大幅波动**（同为漏检，82 vs 127），报告必须带 CI 且不应当作精确值。

---

## M4. 证据缺口图矩阵覆盖率（Evidence gap map cell coverage）

- **一句话定义**：先用预声明框架（典型为"干预 × 结果"二维矩阵）定义"所有应被覆盖的格子"，再把证据逐格放入；**空白格/稀疏格 = 缺口**。
- **如何测量**：
  - 构建框架：Campbell 指南建议 4–6 个行/列头，每个头再分 4–6 个子类；3ie 用"行=干预、列=按因果链排列的结果"；
  - 系统检索与编码后，每个交叉单元格记录研究数（气泡大小=证据量；颜色区分原始研究/系统综述）；
  - 指标：**cell coverage = 有证据的格数 ÷ 总格数**；空单元格率；稀疏格率（如 <k 篇）；每格中位研究数。
- **适用问题**："这块主题哪里已经有证据、哪里几乎没有"——研究优先级与补漏清单。
- **证据等级**：A（3ie 官方方法与平台页；Campbell 官方指南）＋ B（2023 方法学评论；Saran & White 2018）。
- **链接+日期**：
  - https://www.3ieimpact.org/evidence-hub/evidence-gap-maps （访问 2026-09-20；页面原文："graphically highlighting the gaps, where few or no impact evaluations or systematic reviews exist"）
  - https://www.3ieimpact.org/sites/default/files/2019-01/wp28-egm.pdf （2017-02，3ie Working Paper 28；doi 10.23846/wp0028）
  - https://doi.org/10.1002/cl2.1125 （2020-11-19，Campbell EGM 生产指南）
  - https://doi.org/10.1186/s13643-023-02178-5 （2023-03-15，Systematic Reviews："Big Picture" review family）
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC8428058/ （Saran & White，Campbell Syst Rev 2018;14(1):1-38）
- **迁移到 CLS 的形态**：把"研究问题/概念"作行、"材料来源/证据类型"作列，逐格填数量与强度；空/稀疏格直接生成"待补主题清单"。
- **反例/失败边界**：2023 评论明确指出 EGM"只图绘已知、不允许探索性发现"（"only charts what is known and does not allow a more exploratory approach"）；框架本身若不系统，缺口就是"作者视角推断出来的"（原文："Without such a structure, the gaps are not identified in a systematic way, but rather inferred... influenced by their own perspectives and bias"）；Saran & White 强调"EGM 总结有什么证据，不总结证据说了什么"；3ie 页面要求图需定期更新。

---

## M5. 系统地图 / 证据映射计数（Systematic map / evidence map / descriptive map）

- **一句话定义**：用明确分类框架对某一宽领域的研究做**系统盘点与计数**，描述证据的规模、分布与空白（不做效应量综合）。
- **如何测量**：
  - 显式研究问题驱动检索与纳入，把每篇研究按维度编码成类别 → 交叉表计数 → 报告分布（规模/年份/地区/类型）与空白；
  - 工具链示例（EPPI-Centre 官方教程）：EPPI-Reviewer 导出编码 JSON → EPPI-Mapper 选择 Column/Row/Segment 属性 → 自动填充单元格 → 输出可交互地图。
- **适用问题**："这个领域一共做了多少、都是什么类型、哪里分布稀疏"。
- **证据等级**：B（2016 系统综述：39 篇证据地图出版物；2010 真实案例论文）＋ C（EPPI 官方工具文档）。
- **链接+日期**：
  - https://doi.org/10.1186/s13643-016-0204-x （2016-02-10，"What is an evidence map?"：31 个定义中 67% 以"identification of gaps"为目的；结论：无权威标准、方法异质）
  - https://doi.org/10.1111/j.1365-2753.2008.01112.x （2010；Hetrick 等，"evidence mapping… 理解 extent and distribution of evidence… highlighting both what is known and where gaps exist"，youth mental health 案例）
  - https://eppi.ioe.ac.uk/CMS/Portals/35/Creating%20an%20EGM.pdf （EPPI-Centre 工具文档，无日期；访问 2026-09-20）
- **迁移到 CLS 的形态**：把笔记/白板条目按主题与类型做交叉计数，输出"分布表 + 空白分布区"，作为收敛文档的附录。
- **反例/失败边界**：2016 综述明确"没有权威建议规定证据地图应由什么构成"，定义与产物高度异质；2010 案例论文自己指出做地图需要"人员、时间、预算"规划；与其近亲 EGM 一样，只做盘点不做质量/效应判断。

---

## M6. 筛查工具过程指标（Rayyan / Covidence 的进度与决策计数）

- **一句话定义**：用文献筛查工具自动产生的过程统计（去重数、已筛/未筛、Maybe、冲突、排除理由分布）量化"处理覆盖率与未决存量"。
- **如何测量**（按官方文档操作）：
  - Rayyan：检测重复（Possible Duplicates → Resolved/Unresolved）；筛选台决策计数（Include / Maybe / Exclude + reason）；"删除重复数"是 PRISMA 识别阶段的必需数据点；
  - Covidence：Review Summary 实时看 PRISMA 流程图（重复检测+人工标记合计；full-text 排除按理由计数）；`Download DOCX` 导出对齐 PRISMA 2020 的图。
- **适用问题**：单人/团队筛查的"完成度与一致性"；未决清单即待补漏清单。
- **证据等级**：C（两工具官方帮助中心文档）。
- **链接+日期**：
  - https://help.rayyan.ai/hc/en-us/articles/45703234075281-How-to-Screen-References-in-Rayyan （Exa 元数据日期 2026-06-29；访问 2026-09-20）
  - https://help.rayyan.ai/hc/en-us/articles/46779581890961-How-to-Detect-and-Manage-Duplicates-in-Rayyan （Exa 元数据日期 2026-05-17）
  - https://support.covidence.org/help/export-prisma （页面日期 2025-10-22）
  - https://support.covidence.org/help/faq-why-don-t-the-numbers-in-my-prisma-flowchart-add-up （页面日期 2025-10-22）
- **迁移到 CLS 的形态**：在收敛文档里维护"导入→去重→已判定→未决（Maybe/冲突）→引用/未引用"计数表，未决列表驱动补漏动作。
- **反例/失败边界**：Rayyan 官方明示 Maybe **不是最终决定**、不计入 Include/Exclude 统计、不触发冲突、不出现在 PRISMA；重复检测必须**在筛查开始前完成**，否则决策计数与 PRISMA 会失真；Covidence FAQ 说明数字会因未完成筛选/合并而变化，必须等全部完成再导出；Covidence DOCX 中"Studies not retrieved"默认为 0 需手工修正。

---

## M7. Obsidian 未链接提及 + 孤儿率（Unlinked mentions & orphan notes）

- **一句话定义**：未链接提及 = 笔记正文提到了某笔记名但未建立链接；孤儿 = 没有任何链接的笔记；二者给出"知识库连接覆盖度"的两个可计数指标。
- **如何测量**：
  - 未链接提及：每个笔记的 Backlinks 面板 → "Unlinked mentions" 段落计数（官方定义："backlinks to any unlinked occurrence of the name of the active note"）；
  - 孤儿率 = 无链接笔记数 ÷ 总笔记数；Graph view 设置里的 "Orphans" 开关可显示/隐藏无链接笔记；
  - Dataview 量化（基于官方字段文档构造）：`file.inlinks`（入链列表）与 `file.outlinks`（出链列表）；孤儿查询可写为 `LIST WHERE length(file.inlinks) = 0 AND length(file.outlinks) = 0`（**本条目为文档化字段的构造式，非官方配方**）；
  - 链接覆盖率 = 1 − 孤儿率；或"入链 ≥ 1 的笔记占比"。
- **适用问题**：知识库里"哪些内容孤立、哪些名字被提到却没被连接"。
- **证据等级**：C（Obsidian 官方帮助与 Dataview 官方文档）＋ D（社区插件：见下）。
- **链接+日期**：
  - https://obsidian.md/help/plugins/backlinks （官方；无发布日期；源文件 https://raw.githubusercontent.com/obsidianmd/obsidian-help/master/en/Plugins/Backlinks.md ；访问 2026-09-20）
  - https://obsidian.md/help/plugins/graph （官方："Orphans toggles whether to show notes without any links"）
  - https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-pages/ （官方文档；无发布日期；访问 2026-09-20）
  - 社区插件 Link Unlinked Mentions：https://community.obsidian.md/plugins/link-unlinked-mentions ＋ 第三方说明页 https://www.obsidianstats.com/plugins/link-unlinked-mentions （**社区来源，均无发布日期；访问 2026-09-20**；功能：把纯文本提及批量转为 `[[wikilink]]`，应用前预览，直接修改当前笔记、**不可逆（需备份）**，同名笔记/别名冲突时会跳过并提示）
- **迁移到 CLS 的形态**：在收敛文档统计"每主题的未链接提及数、入链数、孤儿清单"；孤儿笔记即未被收敛进任何结论的条目候选。
- **反例/失败边界**：未链接提及只匹配"笔记名/别名"的文本出现，不做语义相似判断；**别名缺失会漏报**；被 Excluded files 规则排除的文件不参与未链接提及；"无链接"不等于"无价值"（日记/模板等天然孤儿）；社区的批量链接插件会直接改笔记且不可逆，重名条目会被跳过（社区自述）。

---

## M8. 课程地图 / 试卷蓝图覆盖率（Curriculum mapping / Table of specifications）

- **一句话定义**：以学习目标（或课程标准）为基线行，把"教学机会/评估题项"映射为列，计算每条目标被覆盖的条目数与权重偏差。
- **如何测量**：
  - 建矩阵：行=目标/内容域（或目标 × 认知层级两维），列=教学或评估机会；每格填条目数/题数；
  - **覆盖率 = 至少被覆盖 1 次的目标数 ÷ 目标总数**；权重偏差 = 实际条目占比 − 计划占比；
  - Harden（AMEE Guide 21）给出 10 个可查看"窗口"（预期学习成果、内容、评估、学习机会、地点、资源、时间表、师资、管理、学生）与 9 步开发流程；
  - 2024 案例（CELT）：对现成选择题库做"反向工程"五步分析，借助 Anderson & Krathwohl 两维 Taxonomy Table 选择题目，输出对齐的可视化。
- **适用问题**："目标清单 vs 实际材料/题目"的对齐审计；考试/内容覆盖是否均衡。
- **证据等级**：B（Harden 2001；CELT 2024 实践论文）＋ D/C（ANSI 博客 2023-02-21 作为行业说明，可选）。
- **链接+日期**：
  - https://pubmed.ncbi.nlm.nih.gov/11371288/ ；https://doi.org/10.1080/01421590120036547 （2001-03，Med Teach）
  - https://doi.org/10.22329/celt.v15i1.7856 （2024-03-28，CELT/Collected Essays on Learning and Teaching）
  - https://blog.ansi.org/anab/creating-table-specifications-test-blueprint/ （2023-02-21，ANSI 博客）
- **迁移到 CLS 的形态**：让"目标段/大纲"作行、白板/笔记条目作列，统计每条目标的材料数与题量权重，空行=未覆盖目标。
- **反例/失败边界**：覆盖计数不评估材料/题目质量；蓝图权重是人为判断（CELT 摘要自称设计蓝图是耗时的专家工作）；矩阵是快照，需要随目标更新维护。

---

## M9. 对照标准的稽核与反馈（Audit & feedback / compliance gap）

- **一句话定义**：用明确"标准/目标"对照实际表现，量化 `差距 = 1 − 合规率`，并把差距反馈给执行者。
- **如何测量**：
  - 合规率 = 符合标准的条目数 ÷ 应合规条目数；gap = 1 − 合规率；
  - Cochrane 综述（Ivers 2012）用"相对基线的合规率绝对差（adjusted RD）"汇总效果：中位 4.3%（IQR 0.5%–16%）；反馈在"基线表现低、来自上级/同事、多次、书面+口头、含明确目标与行动计划"时更有效。
- **适用问题**：有明确外部标准（指南、规范、大纲）时的"差多少、差在哪"。
- **证据等级**：A（Cochrane 系统综述 CD000259.pub3）。
- **链接+日期**：
  - https://doi.org/10.1002/14651858.CD000259.pub3 （2012；Cochrane Database Syst Rev 2012, Issue 6）
  - https://europepmc.org/article/MED/22696318 （摘要页；访问 2026-09-20）
- **迁移到 CLS 的形态**：对"考纲/学习目标"逐条打掌握/覆盖标记，输出合规率与逐条差距清单，作为收敛文档的"离标准还差什么"页。
- **反例/失败边界**：审计只是测量，不是修复；效果取决于基线与反馈方式（Ivers 结论）；标准本身过期/错误会让差距指标误导；本条目在 CLS 的映射仅是方法类比，非设计建议。

---

## M10. 概念图基准覆盖（Criterion-map scoring / proposition coverage）

- **一句话定义**：以"专家/基准概念图"为对照，统计你的知识图覆盖了基准图中多少命题（及其关系结构），缺失项即漏点。
- **如何测量**（CRESST 技术报告归纳的 3 类评分策略）：
  - 组件评分：数命题（两个节点+一条带标签连线=一个命题，是"最小意义单位"）、层级、示例等；
  - **criterion map 对比**：把学习者图与专家图逐命题比对；
  - 混合：组件分 + 对照分；
  - 覆盖率 = 匹配命题数 ÷ 基准图命题总数（可细分到层级/分支）。
- **适用问题**："概念/关系层面我漏了哪些"；概念网络完整性检查。
- **证据等级**：B（CRESST CSE Technical Report 436，1997-08；其相关的 JRST 1996 论文指出概念图评估的多重问题）。
- **链接+日期**：
  - https://cresst.org/wp-content/uploads/TECH436.pdf （1997-08，Ruiz-Primo, Schultz, Shavelson）
  - https://eric.ed.gov/?id=EJ528405 （1996，Journal of Research in Science Teaching："Problems and Issues in the Use of Concept Maps in Science Assessment"）
- **迁移到 CLS 的形态**：以课程/考纲概念图（或用户"目标段"生成的概念清单）为 criterion map，对笔记网络算命题覆盖率并列出缺失命题。
- **反例/失败边界**：基准图的质量与粒度直接决定结论；命题比对需要人工或明确规则（评分者一致性是原研究关注点）；1996 论文标题即提示概念图用于评估存在成体系的问题（"Problems and Issues"），原报告为小样本探索性研究。

---

# 第二部分：「目标基准」的 3 种可行来源（各附真实案例/工具出处）

> 说明：以下只收集"基准从哪来、怎么被已验证地使用"，不评 CLS 应采用哪一种。

## B1. 用户自己的研究问题清单（research_questions / 目标问题集）

- **基准形态**：事先写定的问题列表（含 Population/Concept/Context 或 PICO 要素），后续所有覆盖统计以"每条问题是否被材料/证据触达"为单位。
- **一手依据（真实案例/工具出处）**：
  - JBI Manual（scoping reviews 章）：要求 **a priori 协议**，协议是"所有评审者已同意的研究目标与方法"的文档；10.2.2 页面明确 PROSPERO 目前不接受 scoping review，可用 OSF（标准化模板）或 FigShare 挂协议。链接：https://jbi-global.atlassian.net/wiki/spaces/MANUAL/pages/355862667 （访问 2026-09-20）；章 DOI 10.46658/JBIMES-24-09。
  - PRISMA-ScR（Tricco 2018）：item 4（Objectives）、item 5（Protocol and registration）、item 24（Summary of evidence **须与 review question(s) 及 objectives 关联**）。链接：https://doi.org/10.7326/M18-0850 （2018-09-03）。
- **量化接口**：问题覆盖率 = 有材料支撑的问题数 ÷ 问题总数；每问题挂接的证据/条目计数；未触达问题清单。
- **失败边界**：问题写得太粗/太细都会让覆盖率失去意义；协议改动需透明记录（JBI 页面：若偏离协议需在最终综述中说明并给理由）。

## B2. 板的目标段 / 预声明框架（pre-specified framework，例如"干预×结果""概念×来源""目标×评估"）

- **基准形态**：在开始收集之前先写定的框架（矩阵的维度与格子），它是"哪些格子算应有内容"的判定标准。
- **一手依据（真实案例/工具出处）**：
  - 3ie EGM 方法：framework（矩阵）"sets out the substantive parameters of the EGM"；行=干预、列=结果；气泡=研究。链接：https://www.3ieimpact.org/sites/default/files/2019-01/wp28-egm.pdf （2017-02）。
  - Campbell 官方指南：framework 是 EGM 的基础（"The framework and PICOS are closely related…the framework is the basis…"）；建议 4–6 个行列头、各 4–6 子类。链接：https://doi.org/10.1002/cl2.1125 （2020-11-19）。
  - 方法学警句（2023）：没有结构化框架，"缺口不是被系统识别，而是被作者视角推断"（原文见 M4）。链接：https://doi.org/10.1186/s13643-023-02178-5 （2023-03-15）。
  - 真实 EGM 案例：Campbell 交通领域 EGM（Malhotra et al. 2021, Campbell Syst Rev 17(4):e1203，被 2023 评论引述）；3ie 平台在列的 "Food Systems and Nutrition Evidence and Gap map"（https://www.3ieimpact.org/evidence-hub/evidence-gap-maps ，访问 2026-09-20）。
  - 教育版真实案例：试卷蓝图（CELT 2024）用两维 Taxonomy Table 作为"目标段"，把题库逐题映射成对齐矩阵。链接：https://doi.org/10.22329/celt.v15i1.7856 （2024-03-28）。
- **量化接口**：空单元格率、稀疏格率（<k）、每格条目数——直接对应"目标段里哪些格子没被填上"。
- **失败边界**：框架是人为选定的（Campbell 指南承认需咨询与迭代）；框架过宽/过窄会制造或掩盖缺口；需随主题更新（3ie 页面强调定期更新）。

## B3. 外部对照语料（external comparator corpus / 外部标准）

- **基准形态**：外部已存在的"必含清单/标准"，例如既往综述的纳入研究集合、国家标准文件、经典教材目录等。
- **一手依据（真实案例/工具出处）**：
  - 真实案例1（基准=既往综述纳入研究）：Sampson et al. 2006 用 105 个 Cochrane 综述的纳入研究作参照集验证检索策略（72% 被 MEDLINE 收录；相对召回 .91–.98）。链接：https://doi.org/10.1186/1471-2288-6-33 （2006-07-18）。
  - 工具/流程出处（2025）：基准集应从多来源构建、专家复核、避免用被评估库自建；给出 6 步工作流与 5 个数据库操作示例。链接：https://pmc.ncbi.nlm.nih.gov/articles/PMC12621535/ （2025-03-07）。
  - 真实案例2（基准=国家标准）：Kesidou & Roseman 2002（ERIC 记录证实：研究"middle school programs 支持 national science standards 关键科学概念"的程度并识别典型强弱点）；AAAS Project 2061 还发布了以 Benchmarks 为基准的教材评估报告系列（Algebra / High School Biology / Middle Grades Math & Science）。链接：https://eric.ed.gov/?q=%22How+well+do+middle+school+science+programs+measure+up%22 （论文：J Res Sci Teach 2002，doi 10.1002/tea.10035）；https://www.aaas.org/programs/project-2061/publications （访问 2026-09-20）。
- **量化接口**：覆盖率 = 命中外部清单条目数 ÷ 清单条目总数；未命中清单；或配合 M3 估计清单外的未知量。
- **失败边界**：外部清单本身若有偏移（只覆盖部分期刊/年份/语言），会把它的偏差带入结论（2006 文即讨论"相对召回可能高估"，若源综述自身漏检）；Project 2061 的报告正文本次未取得（403），只使用了 ERIC 摘要与 AAAS 报告目录页（详见未验证清单）。

---

# 第三部分：关键词 → 命中对照

| 关键词 | 本文件中的落点 |
|---|---|
| coverage matrix / 覆盖矩阵 | M4（EGM 矩阵）、M8（课程地图/蓝图矩阵） |
| gap map / evidence gap map | M4（3ie/Campbell）；另见 M5 与 B2 |
| knowledge gap analysis | 未获独立一手方法；该语义出现在 PRISMA-ScR（"identify…knowledge gaps"）与 EGM 文献（"identifying gaps"）中，故未单列条目（避免无出处内容） |
| unlinked mentions / 未链接提及 | M7（Obsidian 官方 Backlinks 面板） |
| orphan notes / 孤儿笔记 | M7（Graph view 的 Orphans 开关；Dataview 字段构造式） |
| PRISMA flow diagram | M1（官方模板；Covidence/Rayyan 的对应计数） |
| PRISMA-ScR / JBI / Cochrane（一手） | M1（PRISMA-ScR）、B1（JBI）、M2/M3/M9（Cochrane Handbook 与 CD000259） |
| Rayyan / Covidence（工具） | M6 |

---

# 第四部分：检索日志（可复核）

工具：agent-reach（Exa via mcporter）检索；r.jina.ai 抓正文；Europe PMC REST 取摘要；pdftotext/textutil 转文档。执行日期：2026-09-20。

1. Exa 检索（20 条固定查询，逐条落盘 /tmp/convB/）：PRISMA 2020 flow diagram（Page BMJ 2021）；Cochrane Handbook ch.4；relative recall；capture-recapture；3ie EGM；Campbell EGM guidance；EPPI systematic map；Rayyan help；Covidence support；Obsidian unlinked mentions / orphan；Dataview；Harden AMEE 21；Ivers audit & feedback；concept map（Ruiz-Primo/Shavelson）；Project 2061（Kesidou & Roseman）；JBI Manual scoping reviews；table of specifications；evidence mapping（Hetrick 2010）；Obsidian orphan 社区插件。
2. 正文核验（Jina 抓取，共 30+ 页）：prisma-statement.org、bmj.com、cochrane.org（ch.4 全文 30 万字节）、PMC12621535、PMC1557524、PMC8428058、PMC2655834（被 reCAPTCHA 拦截）、3ie 官网与 WP28 PDF、Campbell 指南 PDF、systematicreviewsjournal、Rayyan 帮助 2 篇、Covidence 2 篇、obsidian.md help（Graph 页 + Backlinks 源文件）、blacksmithgu.github.io、PubMed(Harden)、Europe PMC(Ivers/Hetrick/2011)、JBI Confluence（10.2.2 成功、10.3 未渲染）、EPPI-Reviewer PDF、CRESST TECH436 PDF、AAAS、ERIC、CELT、White Rose（capture docx）。
3. 补充说明：Exa 免费额度在最后 2 条查询（ToS PDF、knowledge gap）触发限流；以其他已获取来源替代或按"未获独立来源"处理。

---

# 第五部分：未验证 / 未获取清单（不得当作已核实事实使用）

1. **Project 2061 报告正文**：project2061.org 报告页 403、web.archive.org 匿名访问被临时封禁（返回 AbuseAlleviationError，2026-09-20）。仅使用 ERIC 摘要与 AAAS 报告目录页；报告内的具体覆盖率数字未核实。
2. **PARE《Classroom Test Construction: The Power of a Table of Specifications》**：scholarworks.umass.edu 403。改用 CELT 2024 与 ANSI 博客作为 ToS 出处。
3. **《Estimating the horizon of articles…》PMC2655834**：Jina 抓取被 reCAPTCHA 拦截，未核实，未引用其结论。
4. **3ie 早期 WP23（Snilstveit 2013）**：未抓取；本文件使用 2017 年 WP28。
5. **知识缺口分析（knowledge gap analysis）作为独立方法**：本轮未找到可引用的独立一手方法学出处，作"无独立来源"处理。
6. **Rayyan/Covidence 条目日期**：Rayyan 两篇日期来自 Exa 元数据（2026-05-17 / 2026-06-29），Covidence 两篇为页面标注（2025-10-22）；均标注为"元数据日期/页面日期"而非发布日考证。
7. **社区来源**：Obsidian 社区插件页与第三方统计站（M7）为社区自述，均无发布日期，已在原处标注。

---

# 附：来源清单（按方法编号）

- M1：prisma-statement.org/prisma-2020-flow-diagram；bmj.com/372/bmj.n71（2021-03-29）；doi 10.7326/M18-0850（2018-09-03）
- M2：PMC12621535（2025-03-07）；doi 10.1186/1471-2288-6-33（2006-07-18）；Cochrane Handbook ch.4 §4.4.11
- M3：doi 10.1136/bmj.313.7053.342（1996-08-10）；doi 10.1016/j.jclinepi.2011.03.008（2011）
- M4：3ie 官网 EGM 页；3ie WP28（2017-02）；doi 10.1002/cl2.1125（2020-11-19）；doi 10.1186/s13643-023-02178-5（2023-03-15）；PMC8428058（2018）
- M5：doi 10.1186/s13643-016-0204-x（2016-02-10）；doi 10.1111/j.1365-2753.2008.01112.x（2010）；EPPI-Centre 教程 PDF（无日期）
- M6：Rayyan 帮助 2 篇（Exa 元数据 2026-06-29 / 2026-05-17）；Covidence 帮助 2 篇（页面 2025-10-22）
- M7：obsidian.md/help/plugins/backlinks；obsidian.md/help/plugins/graph；blacksmithgu.github.io/obsidian-dataview（均官方，无日期）；社区插件页 2 个（社区，无日期）
- M8：PubMed 11371288 / doi 10.1080/01421590120036547（2001-03）；doi 10.22329/celt.v15i1.7856（2024-03-28）；blog.ansi.org（2023-02-21）
- M9：doi 10.1002/14651858.CD000259.pub3（2012）；europepmc.org/article/MED/22696318
- M10：cresst.org TECH436 PDF（1997-08）；eric.ed.gov/EJ528405（1996）
- B1：JBI Confluence 10.2.2（访问 2026-09-20）；doi 10.46658/JBIMES-24-09；PRISMA-ScR（2018-09-03）
- B2：3ie WP28（2017-02）；doi 10.1002/cl2.1125（2020-11-19）；doi 10.1186/s13643-023-02178-5（2023-03-15）；doi 10.22329/celt.v15i1.7856（2024-03-28）
- B3：doi 10.1186/1471-2288-6-33（2006-07-18）；PMC12621535（2025-03-07）；ERIC（Kesidou & Roseman 2002）；aaas.org 报告目录页
