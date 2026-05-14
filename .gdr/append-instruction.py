#!/usr/bin/env python3
"""Append confirmed instruction block to the research pack XML."""
import os

XML_PATH = "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.gdr/research-pack-core-loop-feasibility.xml"

INSTRUCTION = '''  <instruction>
<![CDATA[
# Deep Research 分析请求 — 用户核心闭环可行性诊断

## 项目背景
- **技术栈**: Tauri 2 + React + TypeScript（v0 已废弃）→ 现 Obsidian Hybrid + FastAPI + Neo4j + LanceDB + Graphiti
- **架构**: BMAD R4 工作流（用户写 PRD，Claude Code 技术自决，5 Agent UAT 验收）
- **关键入口**: frontend/obsidian-plugin/src/main.ts (3606 行) + backend/app/services/* (28 服务)
- **当前状态**: Sprint 完成度 22% done / 34% done+review；Epic 4/5/7/8 全 ready-for-dev（spec 完成，代码 0%）

## 分析议题
**用户核心诉求**：批注 + 在原白板双向链接拆分与联系节点的探索过程 = 核心 →
个人记忆系统**充分理解**用户学习过程 → 检验白板**极其针对性**考察用户

Claude 5 Agent Deep Explore 已判定 **FAIL**（详见 `2026-05-13-设计可行性评估-用户核心闭环.md`）：
- 端到端 10 步中 8 步 ❌、2 步 ⚠️
- 4 处管道断在同一链
- 1 处数据层主动 strip callout（`lancedb_client.py:2249-2263`）
- Epic 4/5/7/8 全 backlog
- "用户原话/verbatim" 维度 spec 0 命中

**ChatGPT 任务**：作为独立第二意见，反驳/确认 Claude FAIL 判定。

## 分析方向（请逐项验证）

### 1. 反驳 Claude FAIL 判定
- spec 完成 80% 是否真的等于"FAIL"？
- 4 处管道断是否真致命，还是夸大？
- LanceDB strip callout 是否必修，还是可绕过（LLM 直接读 vault file）？

### 2. 验证 10 个 Gap 的真实性
- G1-G5（批注闭环）、G6-G7（探索过程 + Graphiti）、G8-G10（检验白板）
- 哪些 Gap 是真破裂，哪些是"看起来破裂但有 workaround"？
- 引用文件路径 + 行号作为证据

### 3. 评估 3 个修复路径
- **Option A**：先修 P0 数据层 bug（~10h）
- **Option B**：完整 dev Story 2.4 + 5.1 + Epic 4/5/7（~170h）
- **Option C**：fork DeepTutor + 嵌入 Canvas 5 大核心（10d MVP，见 round-21）
- 哪个 ROI 最高？工时估算是否合理？

### 4. "verbatim/用户原话"维度
- Epic 4 全 11 Story 真的 0 命中 "verbatim/原话/user_quote" 吗？
- 是否需要新增 Story 4.12 verbatim trace？
- 业界 SOTA（NotebookLM / Khanmigo / DeepTutor）怎么做"用用户原话出题"？

### 5. 业界 SOTA 对照
- Canvas 设计是否真的领先 SOTA？
- 哪些产品已经实现"批注驱动针对性考察"？
- Canvas 的"5 信号 mastery 融合"（BKT + FSRS-D/S/R + 评分 + 校准 + 自评）是否有数学校验？

## 打包内容
- 46 个文件 / 约 260K tokens
- 主体：用户批注主报告 + ChatGPT prompt + 历史调研（Round 15/21/23）+ Sprint 状态 + 22 个 Story spec + 6 个核心代码 + PRD + 项目脉络 + Graphiti core 抽取/dedupe 源码

## 分析方法
1. 通读 `<directory_structure>` 建立心智模型
2. 从入口文件追踪代码路径：
   - 批注链：main.ts (handleAnnotateCallout) → tips.py (POST endpoint) → memory_service.py (episode write) → question_generator.py (callout read)
   - 数据层：lancedb_client.py:2249-2263 (strip callout)
   - Graphiti 内容层：graphiti_core/prompts/extract_nodes.py + dedupe_nodes.py + edges.py
3. 引用 `<file path="...">` + 行号作为证据
4. 验证发现与代码实际行为一致（不要凭 spec 文本判断，要看真实代码）

## 额外上下文
- **用户是非技术背景**，Python/React 都是 AI 写的，需基础解释
- **4 MVP Story 1.16/17/18/19 已完成**（Obsidian 基础设施 100% ship）
- **当前主要阻塞**：Story 2.4（callout 入库）尚未 dev，下游全空转
- **决策时区**：用户 2026-05-06 Round-22 已确认 fork DeepTutor 嵌入 5 大核心方向（见 memory + round-21）

## 输出格式

### 表格 1 — Claude FAIL 判定逐条反驳/确认
| Gap | Claude 判定 | ChatGPT 判定 | 证据 (file:line) | 严重度修正 |
|---|---|---|---|---|

### 表格 2 — 3 Option ROI 评估
| Option | 工时 | 覆盖 Gap 数 | 风险 | ChatGPT 推荐 |
|---|---|---|---|---|

### 表格 3 — 业界 SOTA 对照（如新发现）
| 产品 | 批注捕获 | 探索路径 | 个性化出题 | 与 Canvas 对照 |
|---|---|---|---|---|

### 分章节叙述
- **章节 A**: "verbatim/用户原话"维度深度论证 + 是否需要 Story 4.12
- **章节 B**: 最终推荐（哪个 Option + 为什么）
- **章节 C**: Claude 评估未提到的盲点（如有）

## 输出风格
- 引用具体文件路径 + 行号作为论据
- 反驳时给出具体反例，不要空泛
- 对用户友好的中文表达（非技术背景）
- 如果同意 Claude，明确说"同意，理由：..."；如果不同意，明确说"反驳，证据：..."
]]>
  </instruction>
'''

with open(XML_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

if '<instruction>' in content:
    print("⚠️ Instruction already exists, skipping append.")
else:
    content = content.replace('</research_pack>', INSTRUCTION + '\n</research_pack>')
    with open(XML_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Instruction appended to {XML_PATH}")
    print(f"File size: {os.path.getsize(XML_PATH):,} bytes")
