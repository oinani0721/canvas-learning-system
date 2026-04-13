---
source: prd.md
extractedDate: '2026-04-02'
totalAnnotations: 56
---

# PRD User Annotations Archive

> 从 prd.md 提取的用户批注。原始行号为提取时的位置，PRD 正文中对应批注已清除。

## Annotations

### [Line 64] — 白板绑定笔记文件夹
**PRD Context:** Executive Summary > 成功标志："系统越来越懂你"
**User Comment:** 每个白板在使用前都是有指定相关的笔记文件夹的路径，这样agent 在节点回答用户问题的时候就可以使用我们设计的笔记检索系统，向用户返回精确的笔记片段
**Status:** Addressed (FR-KG-08 已加入：用户可以为每个白板绑定一个笔记文件夹路径)

### [Line 69] — 前端暗色主题硬编码问题
**PRD Context:** 技术架构 > 前端：Tauri 2 独立桌面应用（React + ReactFlow + Zustand + shadcn/ui + Catppuccin Mocha 暗色主题）
**User Comment:** 目前：前端说是暗色主题，但是一直是硬性编码，颜色这边还是拥有一个十分大的问题。
**Status:** For Reference (已知前端问题，CSS 变量体系在 NFR 兼容性中已规定)

### [Line 71] — FastAPI-MCP 和 Neo4j 模块调用 + Mac 部署
**PRD Context:** 技术架构 > 后端：Docker 容器（FastAPI + FastAPI-MCP + Neo4j 7691/Graphiti + LanceDB + Ollama bge-m3）
**User Comment:** FastAPI-MCP + Neo4j 7691/Graphiti ；请你明确告诉我这两个你是调用了什么模块，之前的模块我们是有遗漏，而且最终我的Canvas Learning System 我是打算在我的mac 上使用，我的mac 是M5 max 加 128G 内存
**Status:** Addressed (Graphiti 统一方案 C 已明确模块，跨平台支持已在项目类型分析中规定)

### [Line 73] — Claude Code 源码参考
**PRD Context:** 技术架构 > 对话引擎：Agent SDK Sidecar
**User Comment:** claude code 的源码进行了泄露，很多人将claude code 相关内容用ai 完善后进行了发布，我们在开发的时候也是可以进行参考的
**Status:** For Reference

### [Line 75] — Claude Code 订阅额度与模型切换
**PRD Context:** 技术架构 > 模型灵活性
**User Comment:** 本地模型我们是可以随意控制，控制调整，然后我们对话的话，我们是使用claude code 的订阅额度，但是我们在claude code 对话框内，是否可以使用claude code 的原生/命令来切换模型？
**Status:** Addressed (FR-SYS-09 已加入：用户可以在对话中通过 `/` 命令切换当前活跃 LLM 模型)

### [Line 77] — PostToolUse BEA 学习提取 Hook 解释
**PRD Context:** 技术架构 > Agent 行为保障
**User Comment:** 解释一下 PostToolUse BEA 学习提取 Hook 和 结构化输出
**Status:** For Reference (请求解释，PRD 中已保留术语)

### [Line 91] — 精通度感知设计
**PRD Context:** 用户成功 > 精通度可感知
**User Comment:** 你这里的精确度的感知你是打算怎么设计的，我怎么能感知到？难道是靠自评吗？
**Status:** Addressed (FR-MAST-03 明确：节点精通度色条+进度条+学习档案面板+FSRS复习提醒三种传达方式，精通度仅通过考察表现更新非自评)

### [Line 101] — LangGraph 管道设计
**PRD Context:** 技术成功 > LangGraph 管道零影响
**User Comment:** 你这里的LanGraph 管道是打算怎么设计的？
**Status:** Pending/Deep Research (B类调研：LangGraph 管道设计合理性)

### [Line 107] — 检索练习效应量解释
**PRD Context:** 差异化成功 > 检索练习效应量 d=1.50
**User Comment:** 请你解释一下这点是什么意思？
**Status:** For Reference (请求解释 Karpicke 2011 效应量概念)

### [Line 109] — Edge 理解纠正
**PRD Context:** 差异化成功 > 双重学习策略叠加
**User Comment:** 你对edge 理解有误，edge 是用来在原白板中关联两个节点的，我们在使用原白板的时候是剖析知识点和题目，而不是进行验证
**Status:** Addressed (PRD 已修正：Edge 对话属于原白板的知识剖析功能，不属于验证/考察。Active Recall 归属检验白板)

### [Line 111] — 白箱 Inspectable OLM 解释
**PRD Context:** 差异化成功 > 白箱学生模型
**User Comment:** 请你解释一下这点是什么意思？
**Status:** For Reference (请求解释 Bull & Kay OLM 白箱模型概念)

### [Line 131] — 可衡量指标可靠性核验
**PRD Context:** 可衡量指标表格末尾
**User Comment:** 这些标准是真实可靠吗？我觉得需要 /gemini-deep-research 的code 分析来真实核验
**Status:** Pending/Deep Research (B类调研：全部可衡量指标的可靠性验证)

### [Line 148] — Hybrid Search 分词机制核验
**PRD Context:** Layer 1 > Hybrid Search（bge-m3 + jieba 中文分词）
**User Comment:** 这一点分词，分的是我的笔记路径的词是吧， 请你使用/gemini-deep-research的code 分析来检验一下是否是可靠的
**Status:** Pending/Deep Research (B类调研：jieba 分词在笔记检索场景的可靠性)

### [Line 158] — 信号融合信号数量
**PRD Context:** Layer 2 > 多信号融合（5-6 核心信号）
**User Comment:** 你这里的信号融合到底融合了几个信号，请你给我列出来，请你使用 /gemini-deep-research 的code 分析
**Status:** Addressed (FR-MAST-06 已列出 5 个核心信号：BKT 掌握概率 + FSRS 记忆稳定性 + 考察评分 + 校准偏差 + 自信度自评)

### [Line 161] — Agentic RAG 检索算法可靠性
**PRD Context:** Layer 2 > Agentic RAG Level 1+2 + 四路搜索
**User Comment:** 请你告诉我你这里的算法设计检索 可靠吗？请你使用 /gemini-deep-research 的code 分析
**Status:** Pending/Deep Research (B类调研：Agentic RAG 四路搜索算法设计可靠性)

### [Line 163] — 白箱 OLM 呈现方式
**PRD Context:** Layer 2 > 白箱 Inspectable OLM
**User Comment:** 你这里的白箱是打算怎么呈现？
**Status:** Addressed (FR-MAST-03 明确三种传达方式，Phase 2 独立 OLM 三层面板)

### [Line 170] — Edge 对话 EI+SE 策略解释
**PRD Context:** Layer 3 > Edge 对话（双重学习策略叠加）
**User Comment:** Elaborative Interrogation + Self-Explanation 请你告诉我，你这一点到底是在干嘛
**Status:** For Reference (请求解释精细化追问和自我解释学习策略)

### [Line 220] — 检验白板三角协作设计 + Graphiti 历史记录检索
**PRD Context:** 工作流 2 > 系统基于 FSRS+BKT+KG 三角协作选择薄弱节点
**User Comment:** 你这里打算怎么设计3角协作，请你使用 /gemini-deep-research 来code 分析，而且我的tips edge ，以及我在和ai 对话所犯下的错误以及混淆点，是记录到Graphiti 的，首先你在你记录到Graphiti 后，上面就是我的学习个人历史，那么你是要怎么记录我的历史和检索我的历史，才能精确在检验白板中精准命中我的问题，达到真正考察的目的，提示词又是怎么设计这又很关键了。
**Status:** Pending/Deep Research (B类调研：FSRS+BKT+KG 三角协作 + Graphiti 学习历史记录/检索精度 + 出题 prompt 设计)

### [Line 222] — ACP 内容与 4 维评分角度
**PRD Context:** 工作流 2 > AI 基于 ACP 考察数据包 + 4 维 Rubric 出题考察
**User Comment:** ACP 又是包含了什么，4维这里又是什么角度，这些是可靠的吗？使用 /gemini-deep-research 来code 分析
**Status:** Addressed (出题 Prompt 5 层结构已详述 ACP 内容；FR-EXAM-04 明确 4 维：概念准确/推理质量/知识覆盖/知识整合)

### [Line 227] — 检验白板拉出节点数量限制 + 噪音累积 + Graphiti 帮助
**PRD Context:** 工作流 2 > 发现新盲区 → 用户从对话中拉出新节点
**User Comment:** 什么叫最多3个，在检验白板对话中我发现值得讨论的新疑问，我就会拉出来，这时候我点击这个节点就是原白板的剖析模式，你是要限定死我在检验白板中拉出新节点的数量吗，然后这个新节点的属性是否也是同步归类于这个检验白板所对应的原白板，然后随着检验白板的次数使用的越来越多，那么你还能精确的考察我的个人情况吗？是否会因为噪音过多而无法判断，然后Graphiti 本身自带的模块以及功能是否可以在这点上提供帮助，使用 /gemini-deep-research 来code 分析，找到有相关的优质源码解决方案。
**Status:** Addressed (FR-EXAM-05 已修改为不限数量；新节点自动继承原白板分类属性；Graphiti 90 天图清理控制噪音)

### [Line 254] — 精通度更新通知是否刚需
**PRD Context:** 后端架构 > 新建 8 个模块 > 精通度更新通知
**User Comment:** 精确度更新通知是什么？我感觉完全不像相关的刚需功能吧
**Status:** For Reference (用户质疑此功能的刚需性)

### [Line 258] — API 端点适配解释
**PRD Context:** 后端架构 > 局部调整 — API 端点适配新前端数据格式、节点 CRUD 接口对接
**User Comment:** API 端点适配新前端数据格式、节点 CRUD 接口对接；那么我请问这些又是什么？
**Status:** For Reference (请求解释后端适配含义)

### [Line 263] — Graphiti 统一设置质量核验
**PRD Context:** 后端架构 > Graphiti 统一（方案 C + GraphitiEpisodeWorker）
**User Comment:** 使用 /gemini-deep-research 来code 分析，看一下Graphiti 这样设置是否优质
**Status:** Pending/Deep Research (B类调研：Graphiti 方案 C + GraphitiEpisodeWorker 架构质量)

### [Line 283] — LangGraph 原生功能利用率
**PRD Context:** 后端架构 > LangGraph 保留
**User Comment:** 我记得我们LangGraph 这里有很多的原生板块功能都没有用到吧，我想知道我们这里是怎么设计的，然后请你使用一下/gemini-deep-research 来code 分析 看一下设计得是否合理。
**Status:** Pending/Deep Research (B类调研：LangGraph 原生功能利用率和设计合理性)

### [Line 293] — 6 阶段增量算法设计合理性
**PRD Context:** 后端架构 > 6 阶段增量算法集成
**User Comment:** 这些算法的设计是否合理，请你使用一下/gemini-deep-research 来code 分析，确保成熟有效
**Status:** Pending/Deep Research (B类调研：6 阶段增量算法集成设计合理性)

### [Line 307] — 节点图片粘贴 + Obsidian Canvas 对标
**PRD Context:** 前端架构 > 节点数据格式 > 5 种节点来源验证
**User Comment:** 节点内是否支持粘贴图片，白板上又是否可以粘贴图片，请你对标 obsidian 中的 Canvas 插件所支持的类型，请你使用一下/gemini-deep-research 来code 分析，确保成熟有效
**Status:** Addressed (FR-KG-09 已加入：节点内容区域支持行内图片混排 + 独立图片节点。支持文本、图片、文件嵌入、链接)

### [Line 321] — Neo4j 学习历史节点/Edge 定义 + 检索设计
**PRD Context:** 数据架构 > Neo4j（Graphiti）— 知识图谱、节点关系、学习轨迹
**User Comment:** 关于你把我的个人学习历史写入到Neo4j 后，里面的节点和edge 你打算是怎么定义的，那么最终你要怎么设计才能，让agent 能成熟有效的检索到我的个人历史，请你使用一下/gemini-deep-research 来code 分析，确保成熟有效
**Status:** Pending/Deep Research (B类调研：Neo4j/Graphiti 学习历史数据模型设计 + 检索精度)

### [Line 326] — SQLite + aiosqlite 用途解释
**PRD Context:** 数据架构 > SQLite + aiosqlite — 对话消息持久化
**User Comment:** 请你告诉我**SQLite + aiosqlite** 是什么东西，是节点的对话历史以及session 的对话历史管理吗？
**Status:** For Reference (请求确认 SQLite 用途)

### [Line 332] — Hot-Warm-Cold 归档长期未复习可靠性
**PRD Context:** 数据架构 > 三层对话归档（Hot-Warm-Cold）> Warm（30 天-6 个月）
**User Comment:** 你这样是怎么操作的，那么如果我长时间没有回来复习的话，那么我们复习的时候还能精确的考察到我的需求点吗？请你使用一下/gemini-deep-research 来code 分析，确保成熟有效
**Status:** Pending/Deep Research (B类调研：Hot-Warm-Cold 归档下长期不用后精度保障)

### [Line 344] — 对话上下文窗口三层管理解释 + 可靠性
**PRD Context:** 数据架构 > 对话上下文窗口三层管理
**User Comment:** 请你解释一下这3层管理，并且使用/gemini-deep-research 来code 分析，证明成熟有效。
**Status:** Pending/Deep Research (B类调研：Tier 1/2/3 上下文管理成熟度)

### [Line 351] — 核心算法 + K-RAG 设计有效性
**PRD Context:** 算法架构 > 核心算法管道
**User Comment:** 之前 Gemini 的deep research 深度调研报告，还提供了让Graphiti 增加K-RAG的设计，请问这些核心算法的设计是否真的真实有效，使用一下/gemini-deep-research 来code 分析，确保成熟有效
**Status:** Pending/Deep Research (B类调研：核心算法管道 + K-RAG 增强有效性)

### [Line 370] — 推理谬误出题策略理解确认
**PRD Context:** 算法架构 > 错误类型 → 出题策略映射 > 推理谬误
**User Comment:** 这里推理谬误，指的是我一开始在原白板解这道题目的时候，犯了推理上的错误，那么在这次检验白板中，那么你再次尝试使用题目来考察我，诱导我陷入同样的错误，那么你看我这时还会不会犯下这错误。
**Status:** For Reference (用户确认了对推理谬误出题策略的理解)

### [Line 373] — 错题类型与错题策略合理性
**PRD Context:** 算法架构 > 错误类型 → 出题策略映射 > 似懂非懂
**User Comment:** 使用一下/gemini-deep-research 来code 分析 看一下这里的错题类型是否足够，以及针对这种错题类型所做出的错题策略是否合理。
**Status:** Pending/Deep Research (B类调研：错题分类 4 主类 + 2 子类的完备性 + 策略合理性)

### [Line 379] — Calibration Tracking 用户参与环节
**PRD Context:** 算法架构 > Calibration Tracking > AI 评分可靠性三层保险
**User Comment:** 这个指标是你自动运行吗？还是我要在什么环节下要参与进去。
**Status:** Addressed (已明确：答前显式自评"你觉得自己会吗？"是用户参与环节，评分三层保险自动运行)

### [Line 399] — 性能保障策略解释 + 可靠性
**PRD Context:** 可扩展性 > 性能保障策略
**User Comment:** 请你解释一下这些性能保障策略，使用一下/gemini-deep-research 来code 分析，确保成熟有效
**Status:** Pending/Deep Research (B类调研：ACP token budget、Metadata pre-filtering、Hot-Warm-Cold、Graph Temporal Compaction 成熟度)

### [Line 415] — 用户旅程与算法映射缺失
**PRD Context:** 旅程 1 揭示的需求
**User Comment:** 但是我没有看到你这里所描述的用户旅程上的功能都和前面所提到的算法相对应
**Status:** Addressed (已新增"旅程 → 算法映射"表格)

### [Line 440] — 考察难度权衡设计
**PRD Context:** 旅程 3 > 一周后检验白板考察
**User Comment:** 切记考察的时候，不能太深也不能太浅，这一点的设计权衡很重要要适合用户回答，请你/gemini-deep-research 来看一下如何改善设计。
**Status:** Addressed (FR-EXAM-22 已加入：难度采用连续 IRT difficulty 参数，校准依据 BKT 掌握概率和同类主题历史表现)

### [Line 459] — 图片索引状态设计 + 算法覆盖
**PRD Context:** 旅程 5 > 图片密集型学习 > 搜索索引建立中
**User Comment:** 这一点的功能我们前面也是没有任何算法提到的，你这里的搜索索引建立中的提示是打算怎么来设计？如何设计索引让用户有明确的感知到是否索引成功。
**Status:** Addressed (FR-KG-07 已加入：四种状态指示 — 处理中/已完成/部分失败/失败 + 详情可查看)

### [Line 511] — 递归考察信心打击 + 误差累积解释
**PRD Context:** 创新聚焦 > 检验白板递归考察 > 最大风险
**User Comment:** 递归越深越打击信心 + 误差累积 | 认知负荷控制（15/25/35/45 分钟提醒）+ 多题验证（3 题多数投票 85%→95%） | 你这里的这些内容是什么意思，然后请你 /gemini-deep-research 调研一下看一点这样是否靠谱
**Status:** Pending/Deep Research (B类调研：递归考察信心风险缓解策略靠谱性)

### [Line 514] — Edge 对话精细化追问用途
**PRD Context:** 创新聚焦 > Edge 对话（双重策略叠加）
**User Comment:** /gemini-deep-research code 分析  我这里是表达了我对这两个节点的关系理解，你这里的精细化追问 是用来做什么的。
**Status:** Pending/Deep Research (B类调研：Edge 对话 Elaborative Interrogation 设计合理性)

### [Line 516] — 信号融合设计合理性
**PRD Context:** 创新聚焦 > 多信号融合（5-6 核心信号）
**User Comment:** /gemini-deep-research  code 分析 你这里的信号融合怎么设计才是合理的，是经过事实验证成熟有效的
**Status:** Pending/Deep Research (B类调研：信号融合设计事实验证)

### [Line 518] — 三层评分保险解释 + 可靠性
**PRD Context:** 创新聚焦 > Calibration Tracking（Area9 模式）
**User Comment:** 三层评分保险（自一致性+Rubric 分解+可选双模型） 是什么意思？这样设计是否可靠 /gemini-deep-research  code 分析 来对抗性审查
**Status:** Pending/Deep Research (B类调研：三层评分保险可靠性)

### [Line 561] — 多学科隔离设计
**PRD Context:** 多学科与扩展性 > 同时学多门课
**User Comment:** 同时学多门学科这里你是怎么设计的，虽然我的优先级不高
**Status:** For Reference (用户了解设计但不急)

### [Line 580] — 笔记片段精确返回 + 跳转 Obsidian
**PRD Context:** 项目类型深度分析 > 跨平台策略
**User Comment:** 关于精确返回笔记片段以及ARAG 这点你还没有提到，点击笔记片段实现直接跳转到obsidian 的原笔记的位置可靠吗？请你使用/gemini-deep-research 看一下这样的设计是否可靠。
**Status:** Addressed (FR-RET-13 已加入：双向链接支持文件级/章节级/块级跳转)

### [Line 614] — Claude Code 订阅切换 + /resume + 上下文压缩
**PRD Context:** 模型灵活性 > API Key 安全
**User Comment:** claude code 的订阅服务也不要绑死，可以更换账号，可能我们在对话框内也可以用/命令来进行切换，然后还有一点如果在对话框内使用/resume 的话，那么是切换到session的对话历史，那么我怎么知道哪一个节点，用到哪一个session，以及如果出现像claude code 一样的上下文压缩后面又怎么处理，请你使用/gemini-deep-research 来进行code 分析。
**Status:** Addressed (FR-SYS-08 账号切换 + FR-CONV-12 /resume session 映射 + FR-CONV-13 上下文压缩保留关键数据)

### [Line 629] — 更新策略与 Obsidian 无关确认
**PRD Context:** 更新策略 > 独立桌面应用 > Tauri 2 自动更新
**User Comment:** 这里和obsidian 无关了吧
**Status:** Addressed (PRD 已改为"独立桌面应用"，无 Obsidian 引用)

### [Line 714] — 答前自评解释
**PRD Context:** Phase 1 MVP 核心 > 校准追踪
**User Comment:** 这里的答前自评是什么意思？
**Status:** Addressed (已在 FR-MAST-05 补充说明：考察前 AI 询问"你觉得自己会吗？"收集自信度)

### [Line 719] — Prompt 管理和比较方式
**PRD Context:** Phase 1 MVP 核心 > 质量保证
**User Comment:** 你这里打算怎么进行Prompt 的管理和比较？
**Status:** Addressed (FR-QA-02 已明确：版本管理 + diff 对比 + 输出比较 + 变更自动触发回归测试)

### [Line 747] — SOLO 量表和实验算法解释
**PRD Context:** Phase 3 长期愿景 > 高级分析
**User Comment:** SOLO 量表、FIRe 等实验算法 这些是什么东西，适合我吗？请你使用 /gemini-deep-research 来进行code 分析。
**Status:** Pending/Deep Research (B类调研：SOLO 量表和高级分析算法适用性)

### [Line 799] — 多节点互连 Edge 对话上下文
**PRD Context:** 能力域 2 > FR-CONV-03 > AI 对话时自动注入 1-hop 邻居节点学习上下文
**User Comment:** 如果出现多个节点互相用edge 连接的情况下会怎么样
**Status:** Addressed (FR-CONV-11 已加入：超过 5 个 1-hop 邻居时按相关性/时间/精通度缺口优先排序，总量受 ACP token 预算约束)

### [Line 836] — FR-EXAM-13 出题策略合理性
**PRD Context:** 能力域 4 > FR-EXAM-13 系统按白板类型定制出题策略
**User Comment:** FR-EXAM-13 ，请你使用/gemini-deep-research 来进行code 分析 看看是否合理，看看还有什么需要补充的
**Status:** Pending/Deep Research (B类调研：白板类型定制出题策略合理性)

### [Line 857] — FR-MAST-06 信号融合合理性
**PRD Context:** 能力域 5 > FR-MAST-06 系统将 5 个核心信号融合为单维掌握度
**User Comment:** FR-MAST-06；请你使用/gemini-deep-research 来进行code 分析 看看是否合理
**Status:** Pending/Deep Research (B类调研：5 信号融合为单维掌握度合理性)

### [Line 865] — FR-RET-02 检索有效性
**PRD Context:** 能力域 6 > FR-RET-02 AI 对话时自动检索相关上下文
**User Comment:** FR-RET-02 请你使用/gemini-deep-research 来进行code 分析 看看是否合理，怎样设置才是真正有价值，有效的？
**Status:** Pending/Deep Research (B类调研：对话时自动检索上下文的有效性设计)

### [Line 883] — Agent SDK 原生 /命令系统开关
**PRD Context:** 能力域 7 > FR-SKILL-01 `/` 命令系统基于 Agent SDK 原生技能注册机制
**User Comment:** 等价于claude code 原生的/命令系统，我们调用 Agent SDK 是有这个开关来进行启动的。
**Status:** For Reference (用户确认 Agent SDK 技能注册开关机制)

### [Line 958] — 图片 OCR 存储为记忆
**PRD Context:** 性能 > 图片 OCR < 10s
**User Comment:** 这里的图片OCR 之后是打算当成记忆来储存吗？
**Status:** Addressed (FR-KG-06 已明确：检索层提取文字/公式/概念进入搜索索引和知识图谱，作为结构化学习记忆持久化)

### [Line 1007] — 已脱离 Obsidian 确认
**PRD Context:** 兼容性 > Tauri 2 v2.x
**User Comment:** 我们已经不是obsidian 了
**Status:** Addressed (PRD 全文已迁移到 Tauri 2 独立桌面应用架构)
