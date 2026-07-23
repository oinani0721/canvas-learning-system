# Canvas Learning System — Vault

## 目录结构

| 路径 | 用途 |
|------|------|
| `原白板/` | 学习白板（单 md 一板） |
| `节点/` | 概念节点扁平池（一 vault 一学科） |
| `检验白板/` | 信息隔离考察板（由 /start-exam-board 生成） |
| `raw/` | 原始学习资料 |
| `.canvas-config.yaml` | vault 级配置（vault_id / subject / active_board） |

## ⛔ 弃用路径

严禁写入 `wiki/canvases/`、`wiki/concepts/`、`outputs/exam_boards/`。

## ⛔ 图谱记忆触发（批次2' 线2，MEM-FLYWHEEL）

用户提问含回忆意图（「我之前/上次/学过/错过/考过/记得/哪里薄弱」类，指向用户自己的学习历史）→ 必须先调 `mcp__canvas-learning-mcp__search_memories` 再作答；查不到就明说，禁止编造学习历史。

## Skill 索引

| Skill | 用途 |
|---|---|
| `/configure-whiteboard` | 建板（推荐用插件命令） |
| `/ai-linked-doc` | 派生节点（Cmd+Shift+D 注入） |
| `/chat-with-context` | RAG 对话 |
| `/node-chat` | 节点对话（Cmd+Shift+C 注入） |
| `/study-question` | 解题深度 |
| `/exam-quick` | 零留档口头抽查（不写文件不评分） |
| `/start-exam-board` | 生成检验白板（`node <节点>` = 单节点定向考察，M4 吸收 QuickExam） |
| `/quiz-answer` | 检验白板评分 |

## 核心学习闭环

建白板 → Cmd+Shift+D 派生节点 → Cmd+Shift+A 批注 → /start-exam-board 考察 → 手写答 → /quiz-answer 静默评分 → Dashboard 看掌握度

## 掌握度

掌握度字段 = frontmatter `mastery_score`（0-1）：<0.4 薄弱 / 0.4-0.7 学习中 / ≥0.7 掌握。
