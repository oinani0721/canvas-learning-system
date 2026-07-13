# 开发路线图 v2 — Claude Code 原生 + 本地模型激活（2026-07-13 定稿）

> **触发**: 用户 R5-Q1 批注拍板「改为 claude code 然后重新进行规划开发路径」+ ChatGPT Deep Research 报告交叉验证完成。
> **取代**: R3-Q1 路线图 v1（Phase 0-4）。v1 的架构决策全部保留，运行时选型按交叉验证修正。

## 一 · 已锁定决策台账（全部有批注/报告出处）

| # | 决策 | 出处 |
|---|---|---|
| D-1 | 产品形态 = **Obsidian + Claude Code 原生**；Claudian 降级为可选侧栏，不再是关键链路单点 | R5-Q1 批注拍板 |
| D-2 | Graphiti 挂本地模型（M5 Max），**写入+检索记忆完全启动** | R3 批注拍板 |
| D-3 | 语义通道走**双图隔离**（影子图 `vault:canvas_vault:semantic`），批注事件不二次灌入 | R3-Q1 对抗审查 |
| D-4 | 对话记忆 = **SessionEnd 归档钩子 + 后端确定性管道**（不挂 Graphiti MCP） | R4-Q2 |
| D-5 | QuickExam 被检验白板**吸收**（/start-exam-board 加 node 参数），后端 Gemini 管道退役 | R3-Q1 方案 A' |
| D-6 | 部署**弃 Ollama 单体**；多服务分工 + schema canary 门控 + fail-closed | R4 批注 + ChatGPT DR 交叉验证 |
| D-7 | 评分主轨 = quiz-answer 本地 EMA（订阅），backend 评分链封存 | R1-Q3 / Q3 拍板 |

## 二 · 部署拓扑定稿（内部调研 × ChatGPT DR 交叉验证合并）

```
macOS 宿主（M5 Max 128G，launchd 三个 LaunchAgent 自启）
├─ :12341  llama-server · LLM 约束底座（确定性锚点）
│    模型: Qwen3.5-35B-A3B GGUF Q4_K_S（~21.5GB，KV cache 留余量）
│    ⛔ 启用前必过 nested-schema canary（llama.cpp #21228 $ref/$defs fail-open 风险）
├─ :1234   LM Studio headless · LLM 性能升级线（可选，canary 通过后才转主）
│    ⛔ Qwen3.5 reasoning 模型有 #1773 blocker（json_schema 输出跑进 reasoning_content）
│    候选: 非 reasoning 中文 instruct 模型 / 等 issue 修复
├─ :18012  llama-server · reranker（bge-reranker-v2-m3 GGUF, --pooling rank --rerank）
├─ :11434  Ollama · embedding 现状保留（bge-m3 生产正常，最后迁移且不达标不迁）
└─ Docker backend → host.docker.internal:{12341,18012,11434}
```

**交叉验证的关键修正**（记入设计约束）：
1. canary 验收 6 条硬标准：content 非空 / 无 think 残片 / json.loads 过 / pydantic 过 / **nested $ref/$defs 严格约束** / 不落 reasoning_content；连续 50-100 次零失败
2. canary 失败 = **fail-closed**：不启动语义抽取 worker，结构化直写主链不受影响
3. GGUF 档位：Q4_K_S 首选（Q4_K_M 文件 22.3GB + KV cache 会破 24GB 软线）
4. embedding 迁移验收：同文本新旧 cosine > 0.999 或 top-10 overlap ≥ 80-90%，不达标保留 Ollama（同名 bge-m3 ≠ 同向量空间）
5. SEMAPHORE_LIMIT / max_coroutines 先降 1（且修复 SEMAPHORE 赋值时机 bug——import 前设置才生效）

## 三 · 里程碑（总 ~6-8 人天，M0 已完成）

| 里程碑 | 内容 | 工作量 | 状态 |
|---|---|---|---|
| **M0 · Claude Code 切换** | ✅ .mcp.json 双副本落位（终端 `cd canvas-vault && claude` 即用）；SKILL 文案双宿主化 + Notice 措辞（后置化妆项） | 0.1d | **✅ 2026-07-13** |
| **M1 · Schema Canary 工具 + 模型验证** | canary 脚本（6 条硬标准 + Graphiti 真实嵌套 schema probe + 50 次压测）；llama-server 基线 **50/50 零失败, avg 1.42s/p95 1.57s**（关思考 `--reasoning off/budget 0` 是通过前提，开思考 5 跑 2 挂 avg 107s）；中文白板名 punycode 段编码修复 + E2E 全链验证（add_episode 6.9s，影子分组 1 Episodic + 3 Entity）；**GRAPHITI_LLM_PROVIDER=local 已启用** | 1d | **✅ 2026-07-13** |
| **M2 · llm/reranker 工厂 + 双图隔离** | llm_factory + reranker_factory ✅；semantic_group_id + 双图检索（读侧）✅；写侧 `_process_episode` 单点影子重定向 ✅；SEMAPHORE bug 修复 ✅ | 2.5d | **✅ 2026-07-13** |
| **M3 · SessionEnd 归档管道** | vault settings.json 加 SessionEnd 钩子（原生环境，D-1 前置已满足）→ POST /archive/conversation 端点 → 蒸馏 → 影子图；修 C 类工具 group 硬编码 | 1d | 待 M2 |
| **M4 · QuickExam 吸收** | start-exam-board 加 node 参数（~20 行）；插件命令引导化；exam-quick 文案改定位；后端管道 UAT 后摘除 | 0.5-1d | **独立可先行** |
| **M5 · reranker 上线 + embedding 迁移** | llama-server rerank + 30 行适配器 + 后台链 cross_encoder；embedding 兼容验证（不达标保留 Ollama） | 1-2d | 最后 |

**执行顺序**: M0 ✅ → M1 ✅ → M4 ✅ → M2 ✅ → M3（进行中）→ M5。

## 四 · 风险与回退（承 ChatGPT DR）

- LM Studio + Qwen3.5 reasoning 空 content → 切 llama-server / 换非 reasoning 模型
- llama-server nested schema fail-open → canary 拦截 → schema flatten 或禁用语义 worker（主链不受影响）
- KV cache 破 24GB → Q4_K_S / MLX 4bit / 限上下文
- embedding 向量漂移 → 保留 Ollama 或全量重嵌新表
- Docker 起早于宿主模型服务 → worker 启动 canary healthcheck，失败走 outbox 不 enqueue

- **User：**
