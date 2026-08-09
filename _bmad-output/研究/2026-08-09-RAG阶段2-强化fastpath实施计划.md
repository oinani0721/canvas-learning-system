# RAG 阶段 2：强化 fast path 实施计划（PLAN `RAG-S2-2026-08-09`）

> 方案基准 = ChatGPT P0-B（已批准）: metadata scope → dense+FTS → RRF → dedup → 18012 reranker → elbow → 诚实遥测 + 60 条 golden query 门禁。
> 四路侦察已完成（读侧管线/18012 服务/chunk 策略/golden 素材），全部 file:line 实证 + bge-m3 实测 A/B 数据。

## 侦察核心结论（开工前提）

1. **真实主链（enrich-hook）零 rerank**——有启发式 rerank 的是插件热键链 enrich-context；18012 适配器已存在（`graphiti/rerank_client.py`）但只接 Graphiti
2. **权重方向反转**：路径权重 `videos/lectures 1.5 > 节点/ 0.9`、类型权重 `video_transcript 0.9 > note 0.7`——视频转录被系统性加权高于手写笔记，与目标相反（93% 淹没的第三重成因）
3. **18012 实测**：bge-reranker-v2-m3，N=40→125ms；⛔ 单文档 512 token 上限且超限**整请求 500**（中文 ~640 字爆）；elbow 0.25 阈值对 sigmoid(logit) 分布量纲失配（沿用会砍到只剩 top1）；接入点 `supplementary_search_service.py` 归一化循环后/elbow 前
4. **chunk 组合方案实测**（bge-m3 A/B）：#1 段落级语义边界切分（咖啡 0.4227→0.668）+ #2 callout 分级剥离（堵**检验白板题面泄漏**——Fundamentals chunk 内联完整题面已可被检索=信息隔离旁路激活）+ #3 面包屑条件化（短块 +0.091）；一次 force_rebuild；#4 per-doc_type chunk size 留金集评测后微调；#5 diff-based 否决（破坏纯函数性）
5. **三个前置 bug**：①句子切分器在 `!` 后断句把 `[!question]` 切成 `[!\nquestion]`（所有含批注 chunk 的噪音源+剥离正则前提）②line_start 偏移 128 行+section 级粒度（引用全错）③frontmatter `---` 非行锚定截断风险
6. **golden 基建**：fork `run_memory_retrieval_regression.py`（基线版本化/容差门禁/shadow/judge/exit2 全有）；nDCG 全仓零实现需新写且金集必须带 grade 分级；素材 48 条真实（19 个 session transcript 16 条真提问+检验白板弃答+question 批注+UAT 实测判定样本）+12 合成；直调 `search_supplementary` 评测（无 episode_worker 约束）但**必须手动设 vault ContextVar**
7. 真实手写内容仅 ~46 chunks（2.1%，比之前估的 133 更少）；派生节点 40%+ chunks 是零信息模板样板（`## 核心概念` 占位符等）

## 任务分解（每个 T 完成即 commit）

| T | 内容 | 关键文件 |
|---|---|---|
| T1 **金集先行** | vault_gold_set.yaml（60 条，grade 分级+污染三档：硬禁/配额/零容忍）+ run_vault_retrieval_regression.py（Tier R 排序全表/Tier D 交付/Tier H hook 冒烟 5 条；nDCG 新写；judge 二段可后补）+ **跑开工基线封版** | 新 `backend/tests/regression/vault_gold_set.yaml`, 新 `backend/scripts/run_vault_retrieval_regression.py` |
| T2 **快速修正批** | ①权重方向翻转（reference_priority.json: 节点/ 提权、videos 降权；TYPE_WEIGHTS note>video_transcript）②convert 白名单补 `_rrf_score`/`_fts_only` + `_raw_score` 透传（confidence 地基）③链 A 补 exam_board 排除（隔离缺口）④bug①③②修复 | `reference_priority.json`, `supplementary_reranker.py`, `lancedb_client.py`, `note_search_tools.py` |
| T3 **chunk 改造** | #1 段落级优先边界+话题转折句强制分块+overlap 段落化；#2 `_strip_boilerplate` 泛化分级（检验白板题面剥离/模板样板剥离/用户疑问 callout 独立成块/quote 保留）；#3 面包屑条件化（短块只留文件名）；force_rebuild；金集前后对比 | `lancedb_client.py` `_chunk_text`/`_split_md_by_heading`/`_strip_*` |
| T4 **dedup + rerank 接入** | 源文件级 dedup（resolve_chunks 后同源合并取最高分）；RetrievalReranker（连接池+400 字符截断+1.5s 超时+失败回落原分）插 :225-231；elbow 迁 rerank 分并金集重校准；融合 `sigmoid(ce)×type_weight−hub_penalty`（先修 doc_type 字段传递）；env `RETRIEVAL_RERANKER_BASE_URL`（回落 GRAPHITI_*） | 新 `backend/app/services/retrieval_reranker.py`, `supplementary_search_service.py`, `_normalize_material` |
| T5 **链统一 + 诚实遥测** | 链 A 接共享后处理（hybrid+dedup+rerank+taint+exam_board）profile 化；retrieval_confidence（FTS 参与/双通道确认/score 分布/degraded 细分）；M6 incremental 收编 | 新共享层 + `note_search_tools.py` |
| T6 **验证收尾** | 金集门禁对比（特征向量 query 污染 10/10→0 目标；咖啡 query 交付 miss→hit；handwritten_share@10 显著上升）+ live 实测 + 独立对抗审查 + commit + 用户 UAT 卡 | — |

## 明确不做（防蔓延）
- raw/ 整体排除（用户可能要检索转录——用权重+rerank 治理而非排除）
- 启动脚本 -ub 2048 提批（独立变更，先客户端截断）
- LLM 查询改写/意图路由（2.6 意图导航协议范畴）
- Board Manifest/稳定身份（1.5/2.5）

## 验收标准
- 金集门禁：`contamination@10` 显著下降、同形歧义 query `raw/** in top10 = 0`、`handwritten_share@10` ≥ 30%（基线 ~6%）、咖啡 appended_content query 交付层 hit、`nDCG@10` 不低于开工基线
- live：「我笔记里关于特征值与特征向量讲了什么」注入清单以 节点/ 为主
- 用户 UAT：同一批实测问题，体感「引用的是我写的笔记而不是视频转录」
