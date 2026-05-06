# Canvas Learning System — Vault

## 目录结构

| 目录 | 用途 |
|------|------|
| `raw/` | 原始导入笔记（未处理） |
| `wiki/concepts/` | 概念笔记（Templater 模板生成） |
| `wiki/canvases/` | Obsidian Canvas 画布文件 |
| `outputs/exam_boards/` | 考察板（exam-board 模板生成） |

## Templater 模板

- `concept.md` — 新建概念笔记时自动填充 frontmatter（掌握度、复习时间、关系等）
- `exam-board.md` — 新建考察板时自动填充题目和评分结构

## Claudian 使用指南

通过 Claudian（Claude MCP sidecar）与后端交互：
- "帮我检查系统状态" — 运行启动验证（Neo4j/Ollama/FastAPI/MCP）
- "帮我复习" — 查看待复习概念（基于 FSRS 算法）
- "拆解这个概念" — 将复杂概念分解为子问题
