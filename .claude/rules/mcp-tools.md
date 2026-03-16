# MCP 工具调度规则

## Sequential Thinking（结构化思维）⚠️ 高优先级
- **何时使用**：复杂问题、多步骤推理、需要分解的任务 → 必须调用 `sequential-thinking`
- **强制调用场景**：
  - 判断启发函数 admissibility → 逐步检验所有 edge case
  - "两人争论谁对谁错" → 分别验证双方每一步
  - "是否 always/never 成立" → 系统性寻找反例
  - **原则：宁可多调用一次，也不要因为跳过而给出错误答案**

## Context7（实时文档查询）
- 需要查询库/框架/API 最新文档时 → 调用 `context7`
- 涉及外部库的具体 API 细节时，先查文档，避免依赖过时记忆

## 组合使用
涉及外部依赖的复杂任务：context7 查文档 → sequential thinking 制定方案 → 执行

## LSP（语言服务器）— ✅ 已修复
- **积极使用 LSP**：编辑 Python 文件后查 diagnostics、重构时查 references、修改签名后查调用处
- **后备方案**：如 LSP 不可用，使用 `pyright --outputjson` 或 Python AST 解析器

## ⛔ 编辑后代码质量检查 — 每次编辑 Python 文件后执行
- **编辑 .py 文件后**，主动执行以下检查（至少一项）：
  1. 查看 LSP diagnostics（被动获取，编辑后自动出现）
  2. `ruff check {file}` — lint 检查
  3. `ruff format --check {file}` — 格式检查
- **重构多文件时**：先 `LSP findReferences` 确认影响范围，改完后逐文件查 diagnostics
- **提交前**：`ruff check backend/app/ src/` 全量 lint
