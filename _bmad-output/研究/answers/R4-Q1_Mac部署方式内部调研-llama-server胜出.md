---
title: "R4-Q1 · Mac 部署方式内部调研（替代 Ollama）— llama-server 胜出，待 ChatGPT DR 交叉验证"
date: 2026-07-13
round: R4
question: Q1
source_file: _bmad-output/研究/answers/R3-Q1_本地模型激活Graphiti与QuickExam切订阅-对抗审查与落地设计.md
source_line: 33
category: research
parent: "[[批注总索引表-2026-07-12]]"
---

# R4-Q1 · Mac 部署方式内部调研

> 状态: **内部意见**（2 路 agent deep explore，全结论带 URL/file:line）。research-pack 已按你指令打包（`.gdr/research-pack-graphiti-local-model-deploy.xml`，90K tokens）交 ChatGPT Deep Research——**两边交叉验证后再定终版**。

## 批注原文

> **User：关于模型的选择我建议你使用 xml skill 打包好相关的文件给 Chat GPT 来 deep reasearch ，然后模型的部署不建议使用 ollma，使用更加成熟稳定适合 mac 的方式**

## 一句话核心结论

你否决 Ollama 是**有实锤依据的**（4 个官方 issue 确证它正处引擎切换期的不稳定阶段）；内部调研全景对比 8 个候选后，**llama-server（llama.cpp）胜出**——它是唯一能用一个运行时统一服务 LLM+embedding+reranker 三件套的方案，而且「结构化输出强制」恰好是它的看家本领（Graphiti 的生死线）。LM Studio 是强备选（性能最高、运维最友好，但缺 reranker 接口且新守护进程有内存泄漏前科）。

## 一 · 你的否决被确证：Ollama 的四个实锤不稳定点

1. MLX 新后端只对少数模型生效，不支持的**静默回退**到慢一倍的旧路径（无任何告警）
2. macOS 上 MLX 动态库加载失败是高频故障（3 个独立 issue）
3. 官方文档自己标注 OpenAI 兼容层是 **experimental**（"可能变更或移除"），且有 issue 实证结构化输出约束被静默忽略——与我们实测症状吻合
4. reranker 接口社区求了两年没落地（PR 停滞超半年）

结论：不是"为换而换"，Ollama 当前确实不满足"成熟稳定"。

## 二 · 八候选全景对比

| 运行时 | 结构化输出(生死线) | 三模型统一 | Metal 性能 | 长期稳定 | 运维体验 | 判定 |
|---|---|---|---|---|---|---|
| **llama-server** ⭐ | ✅ GBNF 语法强制（看家本领，历史 bug 已修） | ✅ 唯一全能（chat+embed+**rerank**，router mode 每模型独立进程互不连坐） | ~71 tok/s（够用） | ✅ 单 C++ 二进制，Metal 一等公民 3 年 | ⚠️ 无 GUI，需一次性脚本化 | **主推** |
| LM Studio | ✅ MLX 引擎 Outlines 真强制 | ⚠️ 缺 rerank（会错误映射到 embeddings） | ~90-108 tok/s（最快） | ⚠️ llmster 守护进程 2026-01 才出，已有 headless 内存泄漏 issue | ✅ 最好（GUI+登录自启+按需加载） | 强备选 |
| Ollama | ❌ /v1 疑似忽略 schema | ❌ 无 rerank | ~43 tok/s（最慢） | ❌ 引擎切换期 | ✅ 好 | 排除（你已否决+实锤） |
| mlx_lm.server | ❌ 无 json_schema | ❌ 仅 chat | 快 | — | — | 排除（**官方自认不适合生产**） |
| vLLM/SGLang | — | — | ❌ Apple 支持缺失/太新 | — | — | 排除 |
| Jan/GPT4All/Msty | — | ❌ API 面不足/付费壳 | — | — | — | 排除（无黑马） |

## 三 · 推荐部署拓扑（内部版，待 ChatGPT 交叉验证后定稿）

```
宿主 Mac（brew install llama.cpp → llama-server router mode，launchd 开机自启）
 ├─ qwen3.5:35b-a3b Q4（LLM 抽取，~20GB 峰值——比预估还省，128G 毫无压力）
 ├─ bge-m3 GGUF（embedding，1024 维与存量兼容免重嵌）
 └─ bge-reranker-v2-m3 GGUF（精排，/v1/rerank 原生支持）
      ↑ 每模型独立进程（一个崩不连坐）+ LRU 按需换入换出
Docker 后端 → host.docker.internal:8080/v1 统一访问
```

**附带红利**：对话蒸馏器现在单独养着一个 qwen3:8b——迁移后与 Graphiti 抽取共用同一个 35B 端点，砍掉一个模型。

**迁移改动**（全部定位到 file:line，5 处代码 + 配置）：episode_worker 换 OpenAIGenericClient、embedder_factory 改 base_url（近零改动）、蒸馏器/推荐服务换前缀、健康检查从 Ollama 专有接口改标准接口。核心工程已在 R3-Q1 Phase 1 计划内，只是运行时目标从 Ollama 换成 llama-server。

## 四 · 与 ChatGPT DR 报告的比对方法

拿到报告后重点核对三点：① 它对各运行时 json_schema 支持现状的判断是否与我们的 issue 实证一致；② 它推荐的量化档位与 20GB 实测峰值是否吻合；③ 它是否发现了我们没扫到的黑马运行时。矛盾之处以**可复现实验**为准（Phase 0 半天实验本来就在计划内）。

- **User：**

## 关联

- [[R3-Q1_本地模型激活Graphiti与QuickExam切订阅-对抗审查与落地设计|📚 R3-Q1]]
- [[R4-Q2_对话记忆写入实现设计-不挂MCP用归档钩子|📚 R4-Q2]]（同轮批注）
- [[批注总索引表-2026-07-12]]
