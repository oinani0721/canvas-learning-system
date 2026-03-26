# GDA S27 — 打通管道全景审计报告

> **日期**: 2026-03-25 | **方法**: 16 Agent 并行深度探索 | **目标**: 路径 A 实施依据

---

## 总览

| 维度 | 结果 |
|------|------|
| 扫描文件 | 325+ 文件 / 165K+ 行 |
| MCP Tools | 15/15 **全部真实实现**（无 mock） |
| 管道状态 | 7 条通信管道，4 条健康，3 条需验证 |
| 假命名 | graphiti-core **零 import**，42+ 处假命名确认 |
| 考试管道 | AutoSCORE 4D + pipeline_token 完整，**prompt 文件缺失** |
| RAG 管道 | 6 路检索仅 2 路真正可用，学科隔离仅 2/6 通道 |
| Dashboard | 三选项卡完整，但节点 Profile 缺 4 项功能 |
| Docker | 就绪，**Neo4j 端口不匹配**（.env=7688, docker=7691） |
| Sidecar | Windows 可用性约 70-75%，路径转义+上下文压缩风险 |

---

## Phase 1: 启动验证 — 关键发现

### Docker 服务
- 3 服务：Neo4j(7691) + Ollama(11434) + FastAPI(8001)
- **端口不匹配**：docker-compose 暴露 7691，但 .env 连接 7688（外部实例）
User: canvas-learning-system 这个docker 容器是不是才是匹配的？
- Ollama 模型需手动 pull：`docker exec ... ollama pull bge-m3`
- Gemini API Key **已配置** 在 .env 中

### 前端
- 30 组件 / 4 Store / 12 Service / sidecar
- HintButton/SkipButton 的 API 端点**已确认存在**（exam.py）
- CognitiveLoadTimer 需移除（用户已抛弃）

---

## Phase 2: Graphiti 迁移 — 关键发现

### 6Phase 迁移计划
- Phase 0: 环境配置（15 min）
- Phase 1: 删除死代码（30 min）
- Phase 2: GraphitiEpisodeWorker（2-3h，**最复杂**）
- Phase 3: 替换 Bridge 层（3-4h，**临界交换**）
- Phase 4+5: 假命名清理 + Layered Search（可并行，3-5h）
- **总计 9-13h**

### graphiti-core 状态
- 零 import，零调用
- 唯一出现：dependencies.py 的错误消息文本
- 当前实际存储：Neo4j Cypher + JSON 双写 + 内存缓存

### Gemini API
- .env 已有 API Key：`AI_API_KEY=AIzaSyC...`
- Provider: google, Model: gemini-3.1-flash-lite-preview
- **用户说"照搬 Claude Code 的配置"** — 配置已就绪

---

## Phase 3: 管道修复 — 关键发现

### MCP Tools（15 个全部真实实现）
- pipeline_token HMAC-SHA256 机制完整
- generate_question → score_answer → update_fsrs/bkt 链式验证
- PreToolUse hook **未实现**（所有工具立即执行）

### 考试管道
- AutoSCORE 4 维 4 分制：完整实现
- 5 层 prompt 结构：完整，但 **layer*.md 文件不存在**（使用硬编码默认值）
- HintButton 4 级渐进提示 + 精通度衰减：完整
- SkipButton 无惩罚跳过：完整

### RAG 管道
- 6 路检索实际状态：
  - ✅ LanceDB（有 CPU fallback）
  - ✅ Vault Notes（有 CPU fallback）
  - ⚠️ Graphiti（需 Neo4j 运行）
  - ⚠️ Multimodal（需 Gemini Vision）
User：Multimodal 是什么？然后 - ❌ 教材（Canvas 映射 TODO）
  - ❌ 跨 Canvas（关联逻辑 TODO） 这两个功能先取消
  - ❌ 教材（Canvas 映射 TODO）
  - ❌ 跨 Canvas（关联逻辑 TODO）
- 学科隔离：仅 graphiti + lancedb 2 个通道实现

### Tips/Edge 写入检索
- InlineAnnotation 双写（localStorage + 后端）完整
- ConversationDistiller 4 类提取真正工作
- record_learning_memory entity_type 格式不规范（需修复）

### Dashboard + Profile
- 三选项卡（白板/考试历史/复习）完整
- LearningProfile 4 端点完整
- **缺失 4 项功能**：考察记录列表、错误历史、疑惑→新节点、点击跳转

---

## 决策依赖图（关键路径）

```
Gemini 额度 (已解除: .env 有 API Key)
  → Phase 0 环境配置 (15min)
  → Phase 1 死代码清理 (30min)
  → Phase 2 GraphitiEpisodeWorker (2-3h)
  → Phase 3 Bridge 切换 (3-4h)
  → Phase 4+5 并行 (3-5h)
  → MVP #5/#10 解锁
  → Node Profile 完整

并行可做：MVP #1/#2/#3/#4/#7/#13 验证（不依赖 Graphiti）
```
  Q4：CognitiveLoadTimer（计时器）移除 — 你之前说过已经抛弃计时功能。确认移除？

  Q5：Node Profile 4 项缺失功能的优先级 — 目前节点 Profile 缺少：
  - a. 考察记录列表（哪次考试考过这个节点）
  - b. 错误历史（时间线）
  - c. 疑惑→新节点手动创建
  - d. 点击跳转到当时的对话/白板
User：CognitiveLoadTimer 我觉得先进行移除，然后疑惑→新节点手动创建 是你检测出来然后问我是否需要单独讨论，这时候我是可以和原白板一样选择相关的文本来创建节点；然后我觉得最优先级创建的是点击跳转到当时的对话/白板

---

## 需要用户确认的问题队列

### P0 — 立即确认
1. Neo4j 端口：7688（外部 CS188）vs 7691（Docker 内）用哪个？
2. group_id：单一 `canvas-learning` vs 按学科 `canvas-cs188`？
我记得前端我可以给白板命名以及索引学科的笔记路径吧，请你按照我的命名来

### P1 — Phase 实施前确认
3. 考试 prompt 文件缺失：创建 layer*.md 还是继续用硬编码默认值？
User：你这里考试指的是检验白板吗？关于提示词层面的东西绝对不能硬编码，你要学习高质量成熟的提示词案例，然后我需要尝试了，才知道适不合适合我
4. CognitiveLoadTimer 移除确认
5. Node Profile 4 项缺失功能的优先级

### P2 — 延后确认
6. Edge 蒸馏范围（edge-level vs node context-level）
7. SDK session 上下文管理策略
