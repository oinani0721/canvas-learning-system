@epic-12 @three-layer-memory @agentic-rag
Feature: 三层记忆系统 + Agentic RAG
  As a 学习新知识的学生
  I want 基于三层记忆架构的智能检索系统，融合Graphiti时序图谱、LanceDB语义记忆和Temporal行为监控
  So that 获得更精准、上下文相关的学习内容，生成高质量检验白板辅助学习

  Background:
    Given Canvas Learning System 已正确配置
    And FastAPI 后端运行在 localhost:8000
    And Neo4j (Graphiti) 服务可用
    And LanceDB 数据库已初始化
    And Temporal Memory (PostgreSQL) 已连接

  # ============================================================
  # 检索与融合场景 (1-6)
  # ============================================================

  @priority-high @retrieval
  Scenario: 成功融合三层记忆生成检验白板
    Given 学生在Canvas "离散数学.canvas" 上有学习历史
    And Graphiti 知识图谱包含 "命题逻辑" 相关概念节点和关系
    And LanceDB 语义记忆库包含相关解释文档向量
    And Temporal Memory 记录了学习行为:
      | 操作类型 | 概念         | 得分 | 时间   |
      | 评分     | 逆否命题     | 65   | 2天前  |
      | 评分     | 充分必要条件 | 45   | 3天前  |
    When 学生请求生成 "命题逻辑" 的检验白板
    Then Agentic RAG 分析查询意图
    And 系统使用 Send 模式并行检索三层记忆:
      | 检索层   | 返回内容                              |
      | Graphiti | 概念关系网络                          |
      | LanceDB  | 相关解释文档                          |
      | Temporal | 薄弱概念列表 ["充分必要条件", "逆否命题"] |
    And RRF 融合算法整合检索结果 (k=60)
    And Cohere rerank-multilingual-v3.0 重排序
    And 生成的检验白板优先覆盖薄弱概念 (70%权重)
    And 检索质量评分 >= high (Top-3 avg >= 0.7)

  @priority-high @routing
  Scenario: Agentic RAG 正确选择检索和融合策略
    Given Agentic RAG StateGraph 已初始化
    And 配置支持以下融合策略:
      | 策略     | 场景         | 参数                    |
      | RRF      | 默认检索     | k=60                    |
      | Weighted | 检验白板生成 | alpha=0.7 (薄弱点权重)  |
      | Cascade  | 成本优化     | Tier1不足才调Tier2      |
    When 收到 "生成检验白板" 类型的请求
    Then 系统自动选择 Weighted 融合策略
    And 系统自动选择 Cohere reranking (hybrid_auto模式)
    And 薄弱概念权重设置为 70%
    And 已掌握概念权重设置为 30%

  @priority-high @routing
  Scenario: 普通检索使用默认 RRF 策略
    Given Agentic RAG StateGraph 已初始化
    When 收到 "查询概念解释" 类型的请求
    Then 系统自动选择 RRF 融合策略 (k=60)
    And 系统自动选择 Local reranking (bge-reranker-base)
    And 三层记忆权重平均分配

  @priority-high @fusion
  Scenario: 三层记忆并行检索成功融合
    Given 学生查询 "逆否命题的证明方法"
    And Graphiti 包含以下概念关系:
      | 概念     | 关系       | 目标概念 |
      | 逆否命题 | PROVES_BY  | 反证法   |
      | 逆否命题 | RELATED_TO | 原命题   |
    And LanceDB 包含以下文档向量:
      | doc_id  | content            | similarity |
      | doc-001 | 口语化解释-逆否命题 | 0.89       |
      | doc-002 | 澄清路径-命题逻辑   | 0.76       |
    And Temporal Memory 记录薄弱概念 ["反证法"]
    When Agentic RAG 执行 fan_out_retrieval
    Then 三层检索并行执行 (Send模式)
    And 总延迟 < 150ms (不含网络)
    And RRF融合结果包含:
      | rank | source   | content              |
      | 1    | Temporal | 反证法 (薄弱概念加权) |
      | 2    | LanceDB  | 口语化解释-逆否命题   |
      | 3    | Graphiti | 逆否命题-反证法关系   |

  @priority-medium @quality-control
  Scenario: 低质量检索结果触发Query重写
    Given 学生查询 "什么是数理逻辑" (模糊查询)
    And 初次检索质量评分为 low (Top-3 avg = 0.42)
    When 质量控制器评估结果
    Then 系统触发 Query Rewriter
    And 重写查询为 "数理逻辑基础概念 命题演算 谓词逻辑"
    And 执行第二次检索
    And 新检索质量评分为 medium (Top-3 avg = 0.65)
    And 重写次数 = 1, 未超过最大限制 (max=2)

  @priority-medium @fallback
  Scenario: Graphiti数据为空时降级到双层检索
    Given 学生查询新Canvas "线性代数.canvas" 的概念
    And Graphiti 知识图谱中无该Canvas相关数据
    And LanceDB 包含通用线性代数文档
    And Temporal Memory 无学习历史
    When Agentic RAG 执行并行检索
    Then Graphiti 检索返回空结果
    And 系统降级到 LanceDB 单层检索
    And 融合算法跳过空层 (graceful degradation)
    And 返回结果仅来自 LanceDB
    And 日志记录降级事件: "Graphiti empty, fallback to LanceDB-only"

  @priority-medium @fallback
  Scenario: 新用户无学习历史时的处理
    Given 新用户首次使用系统
    And Temporal Memory 无任何学习行为记录
    And Graphiti 和 LanceDB 包含通用学习资料
    When 用户请求生成检验白板
    Then Temporal Memory 返回空薄弱概念列表
    And Weighted 融合策略降级为 RRF (无法计算薄弱点权重)
    And 检验白板使用均匀分布覆盖所有概念
    And 系统提示: "检测到新用户，建议先完成基础学习建立记忆"

  @priority-medium @timeout
  Scenario: 单层检索超时不阻塞整体流程
    Given 学生查询 "命题逻辑"
    And Graphiti 服务响应正常
    And LanceDB 服务响应正常
    And Neo4j 网络延迟导致 Temporal Memory 超时
    When Agentic RAG 执行并行检索
    And Temporal Memory 检索超过 200ms 超时阈值
    Then 系统取消 Temporal Memory 请求
    And 使用 Graphiti + LanceDB 双层结果融合
    And 日志记录: "Temporal retrieval timeout, proceeding with 2-layer fusion"
    And 总延迟 < 400ms (P95目标)
    And 结果质量评分仍可达 medium 或以上

  @priority-medium @fallback
  Scenario: Cohere API 限流自动降级到本地Reranker
    Given 检验白板生成请求
    And Cohere API 返回 429 Rate Limited
    When 系统调用 reranking 服务
    Then 自动降级到 Local Reranker (bge-reranker-base)
    And 日志记录: "Cohere rate limited, fallback to local reranker"
    And 检索流程继续完成
    And 用户无感知 (透明降级)

  # ============================================================
  # 记忆写入触发场景 (7-9)
  # ============================================================

  @priority-high @memory-write
  Scenario: 评分操作同步写入Graphiti和Temporal Memory
    Given 学生在 "离散数学.canvas" 完成黄色节点回答
    And 节点ID为 "yellow-001", 概念为 "逆否命题"
    When scoring-agent 评分为 72分
    Then 系统更新Canvas节点颜色为紫色
    And 同步写入 Graphiti:
      | 操作        | 数据                              |
      | add_episode | 概念: 逆否命题, 得分: 72, 时间戳  |
      | 创建关系    | (Student)-[:SCORED]->(逆否命题)   |
    And 同步写入 Temporal Memory:
      | 操作         | 数据                            |
      | 更新FSRS卡片 | difficulty调整, next_review计算 |
      | 记录行为     | score_event, timestamp          |
    And LanceDB 不写入 (评分不产生文档)
    And 写入顺序: Canvas先完成 -> 记忆后写入 (非阻塞)

  @priority-high @memory-write
  Scenario: 生成口语化解释同时写入三层记忆
    Given 学生请求为 "充分必要条件" 生成口语化解释
    When oral-explanation agent 生成1200字解释文档
    Then 系统创建MD文件并链接到Canvas
    And 同步写入 Graphiti:
      | 操作        | 数据                                      |
      | add_episode | 类型: oral-explanation, 概念: 充分必要条件 |
      | 创建关系    | (解释文档)-[:EXPLAINS]->(充分必要条件)     |
    And 同步写入 LanceDB:
      | 操作       | 数据                                           |
      | 向量化存储 | doc_id, content, embedding[1536], type, concept |
    And 同步写入 Temporal Memory:
      | 操作     | 数据                             |
      | 记录行为 | explanation_generated, timestamp |
    And 三层写入并行执行，总延迟 < 500ms

  @priority-high @memory-write
  Scenario: 基础拆解操作构建知识图谱
    Given 学生对红色节点 "命题逻辑" 执行问题拆解
    When basic-decomposition agent 生成5个子问题
    Then Canvas创建5个新的问题节点和边
    And Graphiti 写入:
      | 实体     | 关系          | 目标       |
      | 命题逻辑 | DECOMPOSES_TO | 什么是命题 |
      | 命题逻辑 | DECOMPOSES_TO | 命题的真值 |
      | 命题逻辑 | DECOMPOSES_TO | 复合命题   |
      | 命题逻辑 | DECOMPOSES_TO | 逻辑联结词 |
      | 命题逻辑 | DECOMPOSES_TO | 命题公式   |
    And Temporal Memory 记录拆解事件
    And LanceDB 不写入 (拆解不产生长文档)

  # ============================================================
  # 记忆查询触发场景 (10-12)
  # ============================================================

  @priority-high @memory-query @ebbinghaus
  Scenario: 艾宾浩斯复习系统查询到期复习内容
    Given 今天是2025-01-20
    And Temporal Memory 中有以下FSRS卡片到期:
      | 概念     | next_review | difficulty |
      | 逆否命题 | 2025-01-20  | 0.6        |
      | 充分条件 | 2025-01-19  | 0.8        |
    When 艾宾浩斯复习系统执行每日检查
    Then 系统查询 Temporal Memory 获取到期卡片
    And 系统查询 Graphiti 获取概念关联关系
    And 系统查询 LanceDB 获取相关解释文档
    And 生成复习清单:
      | 优先级 | 概念     | 复习材料来源                |
      | 1      | 充分条件 | Graphiti关系 + LanceDB解释 |
      | 2      | 逆否命题 | Graphiti关系 + LanceDB解释 |
    And 通知用户有2个概念需要复习

  @priority-high @memory-query
  Scenario: 生成检验白板时查询并优先覆盖历史薄弱点
    Given 学生请求为 "离散数学.canvas" 生成检验白板
    And 用户选择 "针对性复习" 模式
    When Agentic RAG 执行检索
    Then 系统查询 Graphiti 获取:
      | 查询         | 结果                       |
      | 历史检验记录 | 3次检验历史                |
      | 薄弱概念关系 | ["反证法", "充分必要条件"] |
    And 系统查询 Temporal Memory 获取:
      | 查询             | 结果                    |
      | FSRS低掌握度卡片 | difficulty > 0.7 的概念 |
    And Weighted融合策略设置:
      | 概念类型   | 权重 |
      | 薄弱概念   | 70%  |
      | 已掌握概念 | 30%  |
    And 检验白板问题分布符合权重设置

  @priority-high @memory-query @cross-canvas
  Scenario: 基于Graphiti图遍历发现跨Canvas相关题目
    Given 学生在 "离散数学.canvas" 学习 "逆否命题"
    And Graphiti 知识图谱包含以下结构:
      | 源实体          | 关系       | 目标实体          |
      | 离散数学.canvas | CONTAINS   | 逆否命题          |
      | 逆否命题        | RELATED_TO | 反证法            |
      | 反证法          | RELATED_TO | 间接证明          |
      | 数理逻辑.canvas | CONTAINS   | 反证法            |
      | 高等数学.canvas | CONTAINS   | 间接证明          |
      | 数理逻辑.canvas | CONTAINS   | 逆否命题应用题-Q1 |
      | 高等数学.canvas | CONTAINS   | 反证法练习题-Q2   |
    When 学生请求查询 "逆否命题" 的跨Canvas相关题目
    Then 系统执行 Graphiti Cypher 查询
    And 返回结果:
      | Canvas          | 题目              | 关联概念 | 关联深度 |
      | 数理逻辑.canvas | 逆否命题应用题-Q1 | 逆否命题 | 1        |
      | 数理逻辑.canvas | 反证法基础题      | 反证法   | 1        |
      | 高等数学.canvas | 反证法练习题-Q2   | 间接证明 | 2        |
    And 不查询 LanceDB (无Canvas归属元数据)
    And 不查询 Temporal Memory (无题目关系结构)

  # ============================================================
  # 数据隔离与可扩展性场景 (13-17)
  # ============================================================

  @priority-high @isolation
  Scenario: 单Canvas检索使用group_ids隔离
    Given 系统中存在以下Canvas数据:
      | Canvas          | 概念数 | group_id                  |
      | 离散数学.canvas | 150    | canvas-discrete-math      |
      | 数理逻辑.canvas | 200    | canvas-mathematical-logic |
      | 高等数学.canvas | 300    | canvas-advanced-math      |
    And 总图谱规模: 650概念, 3000+关系
    When 学生在 "离散数学.canvas" 查询 "逆否命题"
    Then Graphiti 查询包含 group_ids 过滤
    And 检索范围限制在 150 概念内 (而非 650)
    And 检索延迟 < 100ms (Story 12.3 目标)
    And 结果不包含其他Canvas的 "逆否命题" 相关概念

  @priority-high @cross-canvas @ui
  Scenario: 用户通过Obsidian Plugin请求跨Canvas题目关联
    Given 学生在 Obsidian 中打开 "离散数学.canvas"
    And 学生选中节点 "逆否命题" (node-id: yellow-001)
    When 学生通过以下方式之一发起请求:
      | 方式     | 操作                              |
      | 右键菜单 | 右键节点 -> "查找跨Canvas相关题目" |
      | 命令面板 | Ctrl+P -> 输入 "Canvas: 跨Canvas关联" |
      | 侧边栏   | 点击插件面板 -> "关联查询" 按钮    |
    Then Obsidian Plugin 构造 HTTP 请求到 FastAPI
    And FastAPI 路由请求到 Agentic RAG StateGraph
    And StateGraph 执行 Graphiti 跨Canvas查询 (不使用group_ids限制)
    And 返回结果到 Obsidian Plugin
    And 侧边栏显示结果列表
    And 用户可点击结果跳转到目标Canvas

  @priority-medium @performance
  Scenario: 大规模图谱性能保护机制
    Given Neo4j 图谱规模:
      | 指标     | 当前值 | 阈值   |
      | 概念节点 | 12,000 | 10,000 |
      | 关系边   | 65,000 | 50,000 |
    And 当前检索未使用 group_ids 过滤
    When 执行 Graphiti hybrid_search
    Then 系统检测到超过规模阈值
    And 自动降级策略:
      | 措施           | 说明                     |
      | 强制 group_ids | 必须指定Canvas范围       |
      | 限制遍历深度   | max_hops = 2 (默认3)     |
      | 减少返回数量   | num_results = 5 (默认10) |
    And 日志警告: "Graph scale exceeded threshold, applying performance protection"
    And 建议用户: "考虑归档旧Canvas数据或分库"

  @priority-medium @isolation
  Scenario: LanceDB语义检索按Canvas分区过滤
    Given LanceDB 存储以下文档:
      | doc_id  | content               | canvas_file     | concept  |
      | doc-001 | 离散数学-逆否命题解释 | 离散数学.canvas | 逆否命题 |
      | doc-002 | 数理逻辑-逆否命题解释 | 数理逻辑.canvas | 逆否命题 |
      | doc-003 | 高数-极限定义         | 高等数学.canvas | 极限     |
    And 向量空间中 doc-001 和 doc-002 相似度 = 0.92
    When 学生在 "离散数学.canvas" 查询 "逆否命题"
    Then LanceDB 查询包含 canvas_file 过滤
    And 返回 doc-001 (相似度0.89)
    And 不返回 doc-002 (属于不同Canvas)
    And 避免跨Canvas内容混淆

  @priority-medium @cross-canvas
  Scenario: 检验白板生成允许跨Canvas语义扩展
    Given 学生请求生成 "离散数学.canvas" 检验白板
    And 用户勾选 "包含相关Canvas资料"
    When Agentic RAG 执行 LanceDB 检索
    Then 移除 canvas_file 严格过滤
    And 使用 concept 相关性过滤
    And 结果包含多个Canvas的相关文档
    And 融合时标注文档来源Canvas

  # ============================================================
  # POC验证和迁移场景 (19-23) - Story 12.2, 12.3
  # ============================================================

  @priority-high @poc @story-12.2
  Scenario: LanceDB POC性能验证 - 10K向量
    Given LanceDB 测试数据库已初始化
    And 已导入 10,000 个测试向量 (维度: 1536)
    When 执行语义相似度搜索 (top-10)
    Then P95 延迟 < 20ms
    And 查询结果准确率 >= 95%
    And 内存占用 < 500MB

  @priority-high @poc @story-12.2
  Scenario: LanceDB POC性能验证 - 100K向量
    Given LanceDB 测试数据库已初始化
    And 已导入 100,000 个测试向量 (维度: 1536)
    When 执行语义相似度搜索 (top-10)
    Then P95 延迟 < 50ms
    And 查询结果准确率 >= 95%
    And 支持并发查询 (10 QPS)

  @priority-high @poc @story-12.2
  Scenario: LanceDB 支持 OpenAI Embedding
    Given LanceDB 已初始化
    And OpenAI API 可用
    When 插入文档时使用 text-embedding-3-small 生成向量
    Then 向量维度为 1536
    And 向量成功存储到 LanceDB
    And 语义搜索结果与 OpenAI embedding 一致

  @priority-medium @migration @story-12.3
  Scenario: ChromaDB 到 LanceDB 数据迁移
    Given ChromaDB 包含以下数据:
      | 集合名称           | 文档数 | 向量维度 |
      | canvas_explanations | 500    | 1536     |
      | canvas_concepts      | 200    | 1536     |
    When 执行迁移工具 migrate_chromadb_to_lancedb
    Then LanceDB 成功导入所有文档
    And 数据一致性校验通过:
      | 检查项     | 结果 |
      | 文档数量   | 一致 |
      | 向量内容   | 一致 |
      | 元数据完整 | 一致 |
    And 迁移日志记录完整

  @priority-medium @migration @story-12.3
  Scenario: ChromaDB 到 LanceDB 双写模式
    Given 系统配置为双写模式
    And ChromaDB 和 LanceDB 同时运行
    When 插入新文档到语义记忆层
    Then 文档同时写入 ChromaDB 和 LanceDB
    And 两个数据库内容一致
    And 读取操作优先使用 LanceDB
    And 双写延迟增加 < 50%

  @priority-medium @migration @story-12.3
  Scenario: LanceDB 迁移回滚计划
    Given 已完成 ChromaDB 到 LanceDB 迁移
    And LanceDB 运行正常
    When 检测到 LanceDB 严重故障
    Then 自动触发回滚:
      | 步骤 | 操作                        |
      | 1    | 切换读取到 ChromaDB         |
      | 2    | 停止 LanceDB 写入           |
      | 3    | 通知管理员                  |
    And 服务可用性 >= 99.9%
    And 数据不丢失

  # ============================================================
  # LangGraph StateGraph 场景 (24-26) - Story 12.5
  # ============================================================

  @priority-high @stategraph @story-12.5
  Scenario: CanvasRAGState Schema 定义
    Given Agentic RAG StateGraph 初始化
    When 检查 CanvasRAGState 类型定义
    Then 包含以下字段:
      | 字段名            | 类型                | 用途               |
      | query             | str                 | 原始查询           |
      | rewritten_query   | Optional[str]       | 重写后的查询       |
      | canvas_file       | str                 | 当前Canvas文件     |
      | graphiti_results  | List[SearchResult]  | Graphiti检索结果   |
      | lancedb_results   | List[SearchResult]  | LanceDB检索结果    |
      | temporal_results  | List[WeakConcept]   | Temporal检索结果   |
      | fused_results     | List[SearchResult]  | 融合后结果         |
      | quality_score     | QualityLevel        | 质量评分           |
      | rewrite_count     | int                 | 重写次数           |
      | final_output      | Any                 | 最终输出           |
    And 所有字段类型检查通过

  @priority-high @stategraph @story-12.5
  Scenario: CanvasRAGConfig Context 配置
    Given Agentic RAG StateGraph 初始化
    When 检查 CanvasRAGConfig 配置
    Then 包含以下配置项:
      | 配置项            | 默认值          | 说明                |
      | fusion_strategy   | rrf             | 默认融合策略        |
      | rerank_mode       | hybrid_auto     | 重排序模式          |
      | max_rewrite       | 2               | 最大重写次数        |
      | timeout_ms        | 200             | 单层检索超时        |
      | quality_threshold | 0.6             | 质量阈值            |
    And 配置可通过 RunnableConfig 传递

  @priority-high @stategraph @story-12.5
  Scenario: StateGraph 编译和执行
    Given CanvasRAGState 和 CanvasRAGConfig 已定义
    And 以下节点已实现:
      | 节点名             | 功能                   |
      | analyze_query      | 查询分析               |
      | fan_out_retrieval  | 并行检索 (Send模式)    |
      | fuse_results       | 结果融合               |
      | evaluate_quality   | 质量评估               |
      | generate_output    | 输出生成               |
    When 执行 StateGraph.compile()
    Then 编译成功，返回 CompiledGraph
    And 图结构包含条件边 (质量不足时重写)
    And 端到端执行测试通过

  # ============================================================
  # UI交互场景 (27)
  # ============================================================

  @priority-medium @ui @epic-13
  Scenario: 完整的跨Canvas关联UI交互流程
    Given 学生在 Obsidian 中使用 Canvas Learning System 插件
    And 插件已连接到本地 FastAPI 后端 (localhost:8000)
    When 学生在 "离散数学.canvas" 右键点击 "逆否命题" 节点
    Then 显示上下文菜单:
      | 菜单项           | 快捷键 |
      | 生成解释         | Ctrl+E |
      | 评分             | Ctrl+S |
      | 查找跨Canvas关联 | Ctrl+R |
      | 生成检验白板     | Ctrl+V |
    When 学生点击 "查找跨Canvas关联"
    Then 弹出配置对话框:
      | 选项     | 默认值     | 说明             |
      | 搜索范围 | 所有Canvas | 可选择特定Canvas |
      | 关联深度 | 2跳        | 1-3跳            |
      | 结果数量 | 10         | 5-20             |
    When 学生点击 "搜索" 按钮
    Then 侧边栏显示加载动画
    And 状态文字: "正在搜索跨Canvas关联..."
    When 后端返回结果 (延迟 < 500ms)
    Then 侧边栏显示结果卡片列表:
      | Canvas          | 题目           | 关联概念 | 操作   |
      | 数理逻辑.canvas | 逆否命题应用题 | 逆否命题 | [打开] |
      | 高等数学.canvas | 反证法练习     | 反证法   | [打开] |
    And 每个卡片显示关联路径图示
    When 学生点击 [打开] 按钮
    Then Obsidian 打开目标Canvas文件
    And 自动定位到目标节点
    And 高亮显示目标节点 (3秒)
