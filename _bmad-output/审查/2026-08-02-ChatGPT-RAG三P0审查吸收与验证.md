# ChatGPT RAG 三 P0 审查 — 吸收与实机验证

> **Date**: 2026-08-02
> **输入**: ChatGPT 对 `rag-p0_pack_2026-08-02.md`（60 文件）+ GitHub 分支交叉核验的对抗性审查
> **验证**: 7 个代码级反证逐条实机核查 —— **7/7 CONFIRMED，0 驳回**
> **总裁决**: ChatGPT 否决我方原清单式修补，裁决成立。采纳其重构方案（细节见 §三）

---

## 一、7 个反证的实机验证（全部实锤）

| # | ChatGPT 反证 | 实机验证 | 证据 |
|---|-------------|---------|------|
| 1 | debounce 是「只留最后一个文件」不是「合并」；索引中新事件被静默丢弃 | ✅ CONFIRMED | `lancedb_index_service.py:139` coalesce key 默认 `vault:{vault_root}`（整 vault 一个 key，异 path 互相 cancel）；`:174` 索引中直接 return 无重放 |
| 2 | refresh-changed 返回 `scheduled=len(req.paths)` 假成功 | ✅ CONFIRMED | `index.py:153` 无条件返回循环计数 |
| 3 | 单文件与全量索引双套漂移实现 | ✅ CONFIRMED（我方审查已证） | 文件名黑名单缺失/CPU-only vectorizer/`return 0` 六义 |
| 4 | 「6 源」实为 5 个 Send，cross-canvas 从未实现 | ✅ CONFIRMED | `state_graph.py:145-149` 恰 5 个 Send；`cross_canvas_retriever.py:40` `_warned_unimplemented` 占位哨兵 |
| 5 | path_map 不是修法；根因是同步 wrapper 返回 coroutine | ✅ CONFIRMED（打脸我方原方案） | `state_graph.py:520` 同步 `def rewrite_loop_routing` return `async fan_out_retrieval(state)` = coroutine；`:713` 注释自书「No path_map needed」 |
| 6 | `configurable` 也是错的；该传 `context=` | ✅ CONFIRMED（再打脸） | `state_graph.py:567` `context_schema=CanvasRAGConfig` + `rag_service.py:234-237` `config=config`；**容器实测 langgraph 1.1.10**（支持 `context=`）；requirements 仅 `langgraph>=0.3.10` 无锁版本（漂移风险坐实） |
| 7 | 旧 daemon NEO4J_URI 指 7689，生产在 7691 | ✅ CONFIRMED | `~/bin/graphiti-canvas-daemon.sh:33` `bolt://localhost:7689`；实测 7689 **0 监听**（恢复=崩溃循环；排除了写错库的最坏情形） |

## 二、结构性诊断采纳（原文 §二，逐条认账）

七条全部与我方两轮审查发现互相印证，核心一句：**系统没有「可执行能力契约」，长期用 fallback/空数组/scheduled=N 把接线故障伪装成低质量或成功**。特别认账：
- 「fallback 必须让系统状态变红」——quality 假信号让四轮修复都能自我宣告成功，这是复发的第一因
- 「异常转空数组导致 RetryPolicy 永远看不到故障」——graphiti/lancedb 节点 catch-all 返回 []，retry 形同虚设
- 「channel health = len(results)>0 只是 non_empty_count」——把健康空结果和连错库混为一谈

## 三、三 P0 最终方案（ChatGPT 裁决 + 我方采纳）

**P0-A 重写（否决原「补一行」）**：
- 结构：事件加速（保存钩子/FSEvents）+ fingerprint anti-entropy 扫描兜底（启动 reconciliation 非阻塞 + 周期 10-15min）
- durable per-path pending map（同 path 覆盖、异 path 绝不互相取消、索引中标 dirty 重放）
- 全量/单文件/删除/rename 合并为同一套索引原语（plan/embed/publish/remove/should_index）
- API 返回结构化状态（accepted/coalesced/completed/excluded/failed…），废除 scheduled=N
- SLO：保存后 60s 可检索（watcher 正常 10s）、删除后 60s 不可检索、freshness lag>5min 即 stale 状态

**P0-B 退役默认主链（否决「修活后上线」）**：
- 生产默认 = fast path：metadata scope → dense+FTS → RRF → dedup → **18012 reranker** → elbow → 诚实遥测
- search_notes 不再陪跑 31 秒；扩展通道按意图触发（temporal→Graphiti、图像→multimodal）；cross-canvas 保持 disabled
- LangGraph 旧管道进 shadow 模式（夜间固定 query 集对比），达量化门槛（nDCG@10 +0.05 等九项）才复活，连续两轮不达标物理删除
- 顺带修正确修法：async router（不是 path_map）、`context=`（不是 configurable）、env 名单一化+不一致启动失败、模型 registry+启动探测、锁 langgraph 版本
- quality 拆三层：execution health（ok_nonempty/ok_empty/timeout/error/disabled/misconfigured）/ retrieval_confidence（对实际交付结果计算）/ offline quality（60 条 golden query 集：Recall/MRR/nDCG/污染率）

**P0-C 正式退役 8765（否决重建）**：
- 删 ~/.claude.json graphiti-canvas 定义 + 修正 known-gotchas 的「已修复」谎言 + 归档 daemon 脚本
- backend 成唯一 Graphiti 写权威；SessionEnd 走鉴权端点 + 幂等键（session_id+summary_version）
- 产品能力如实表述：批注=近实时；session=结束时归档（不再宣称「session 内实时记忆」）

**防再犯**：契约测试四组 41 条（原文 §九清单直接转 pytest）+ launchd 三层探针（registration/process/functional canary）+ heartbeat dead-man 模式 + ops/launchd/ 版本化。

## 四、实施顺序（原文 §十二，五阶段）

0. **止血**：extended pipeline 默认关、去 31s 陪跑、废 quality 假信号、结构化 source 状态、锁 langgraph 版本
1. **索引正确性**：pending queue/统一原语/删除改名/generation publish/reconciliation/freshness canary
2. **强化 fast path**：去重、course metadata、接 reranker、60 条 golden query、回归门禁
3. **退役 8765**：backend 单写 + SessionEnd 鉴权幂等 + launchd 版本化三层探针
4. **shadow 评估旧管道**：达门槛复活，两轮不达标删除

## 五、ChatGPT 标注的待实机验证项（我方补测结果）

| 项 | 结果 |
|----|------|
| 容器 langgraph 版本 | **1.1.10**（context= 可用；锁版本必要性坐实） |
| 7689 是否有另一套 Neo4j | **0 监听**（恢复旧 daemon=崩溃循环而非写错库） |
| 其余 7 项（Graphiti P95/模型 ID 现役/18012 增益/multimodal 表/8765 delete 工具清单/指纹差集） | 随阶段 0-2 实施时逐项补测 |
