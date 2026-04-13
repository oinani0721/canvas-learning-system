---
story_id: "2.8"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P2"
estimate_hours: 6
depends_on: ["2.1"]
blocks: ["9.1"]
trace:
  - "FR-MM-01"
  - "FR-MM-02"
---

# Story 2.8: 图片识别对话

Status: ready-for-dev

## Story

As a 学习者,
I want 贴入图片后 AI 能识别并讨论图片内容,
So that 我可以用图片（如板书照片、示意图、代码截图）辅助学习讨论。

## Acceptance Criteria

1. **Given** 学习者的笔记中嵌入了图片（`![[img.png]]` Obsidian 图片语法）
   **When** 启动 AI 对话（`/chat_with_context`）
   **Then** 系统检测笔记中的图片嵌入引用
   **And** 解析图片文件路径（相对于 vault 根目录）

2. **Given** 图片文件路径已解析
   **When** 系统加载图片
   **Then** 图片通过 Claudian 原生图像识别（Claude 3.5 multimodal）分析内容
   **And** 分析结果包含：图片类型描述（diagram / code_screenshot / handwriting / photo）+ 内容文本提取 + 关键概念标注
   **And** 单张图片分析耗时 < 3s

3. **Given** 图片分析结果已获取
   **When** 系统组装 LLM 对话上下文
   **Then** 图片分析结果作为额外上下文注入 system prompt
   **And** 注入格式：`"笔记中嵌入的图片:\n  图片: {filename}\n  类型: {type}\n  内容: {extracted_text}\n  关键概念: {concepts}"`

4. **Given** 图片内容已纳入对话上下文
   **When** 学习者提问关于图片的问题（如"这张图里的数据结构是什么？"）
   **Then** AI 回答能准确引用图片内容
   **And** AI 能将图片内容与笔记文本内容关联分析

5. **Given** 图片识别功能正常运行
   **When** 考虑数据持久化
   **Then** 图片分析结果不自动写入知识图谱索引（降级策略）
   **And** 分析结果仅在当前 session 有效，不跨 session 缓存
   **And** 降级原因记录在日志中（`image_kg_persistence_disabled`）

6. **Given** 笔记中的图片文件不存在或格式不支持
   **When** 系统尝试加载图片
   **Then** 跳过该图片，继续处理其他内容
   **And** 在 structlog 中记录 warning：`image_not_found` 或 `unsupported_format`
   **And** 对话正常进行，仅缺少该图片的上下文

7. **Given** 笔记中嵌入多张图片（> 3 张）
   **When** 系统处理图片
   **Then** 最多分析前 3 张图片（按出现顺序）
   **And** 后续图片跳过并在日志中记录 `image_limit_reached`

## Tasks / Subtasks

- [ ] Task 1: Obsidian 图片嵌入检测与路径解析 (AC: #1)
  - [ ] 1.1: 在 `backend/app/services/` 下创建 `image_context_service.py`
  - [ ] 1.2: 实现 `detect_embedded_images(markdown_content: str, vault_path: str) -> List[ImageRef]`
  - [ ] 1.3: 正则匹配 Obsidian 图片语法：`!\[\[(.*?\.(png|jpg|jpeg|gif|webp|svg))\]\]` 和标准 markdown 图片 `!\[.*\]\((.*?)\)`
  - [ ] 1.4: 解析为绝对路径：`vault_path / image_ref`（处理子目录引用如 `![[attachments/img.png]]`）

- [ ] Task 2: Claude multimodal 图片分析 (AC: #2)
  - [ ] 2.1: 实现 `analyze_image(image_path: str) -> ImageAnalysis` — 调用 Claude 3.5 的 vision 能力
  - [ ] 2.2: 构造 multimodal 请求：将图片 base64 编码发送给 LLM，prompt 要求返回结构化分析（type / extracted_text / key_concepts）
  - [ ] 2.3: 支持的图片格式：PNG / JPEG / GIF / WebP（SVG 降级为跳过）
  - [ ] 2.4: 设置 3s 超时，超时返回空分析结果
  - [ ] 2.5: 限制最多处理 3 张图片，超出部分跳过

- [ ] Task 3: 图片上下文注入 (AC: #3, #4)
  - [ ] 3.1: 在 `chat_context_assembler.py`（Story 2.1）中新增 `inject_image_context(image_analyses: List[ImageAnalysis]) -> str`
  - [ ] 3.2: 将分析结果格式化为 LLM 可理解的上下文片段
  - [ ] 3.3: 图片上下文在 token 预算中的优先级低于 Tips/errors（压缩时先移除图片上下文）
  - [ ] 3.4: 在 skill workflow Step 3（context_enrichment 后）插入图片分析步骤

- [ ] Task 4: 降级策略实现 (AC: #5, #6, #7)
  - [ ] 4.1: 图片分析结果不写入 Graphiti 或 LanceDB（显式禁用，日志记录 `image_kg_persistence_disabled`）
  - [ ] 4.2: 分析结果仅存在于当前 session 的内存中，session 结束后丢弃
  - [ ] 4.3: 图片文件不存在时返回 `ImageRef(status="not_found")`，不中断流程
  - [ ] 4.4: 不支持的格式（SVG）返回 `ImageRef(status="unsupported")`

- [ ] Task 5: 复用已有 multimodal_service (AC: #2)
  - [ ] 5.1: 检查 `backend/app/services/multimodal_service.py`（Story 35.1）是否有可复用的图片处理逻辑
  - [ ] 5.2: 如有 base64 编码 / 文件读取 / 格式验证等功能，直接复用
  - [ ] 5.3: 如需新增 vision API 调用，在 `image_context_service.py` 中实现（不修改 multimodal_service.py）

- [ ] Task 6: 测试 (AC: #1~#7)
  - [ ] 6.1: 单元测试 `detect_embedded_images`：Obsidian 语法、标准 markdown、子目录路径
  - [ ] 6.2: 单元测试 `analyze_image`：正常分析、超时、不支持格式
  - [ ] 6.3: 单元测试图片上下文注入：格式化、token 预算优先级
  - [ ] 6.4: 单元测试降级：文件不存在、超过 3 张限制
  - [ ] 6.5: 集成测试：含图片的笔记 → 启动对话 → 提问图片内容 → AI 正确引用

## Dev Notes

- **已有 multimodal_service.py**: `backend/app/services/multimodal_service.py`（Story 35.1）已有文件上传、管理、base64 编码等逻辑，可复用部分功能
- **已有 markdown_image_extractor.py**: `backend/app/services/markdown_image_extractor.py` 可能已有图片路径解析逻辑，需检查
- **Claude 3.5 Vision**: 使用 LiteLLM 调用 Claude multimodal API，传入 base64 图片和分析 prompt
- **图片不持久化原因**: PRD FR-MM-01/02 明确标注"降级：图片不自动持久化到知识图谱索引"。这是有意设计，避免图片 OCR 错误污染索引
- **Anchor PRD 引用**: §8.5 旅程 5 图片学习 (line 7046-7069)

### Project Structure Notes

```
backend/app/services/
  image_context_service.py        # 新增：图片检测 + 分析 + 上下文注入
  chat_context_assembler.py       # Story 2.1 创建，扩展 inject_image_context()
  multimodal_service.py           # 已有：可能复用 base64 / 文件处理
  markdown_image_extractor.py     # 已有：可能复用路径解析
backend/tests/unit/
  test_image_context_service.py   # 新增
```

### References

- BMAD PRD FR-MM-01/02: `_bmad-output/planning-artifacts/prd.md` (line 512-513)
- 已有 multimodal_service.py: `backend/app/services/multimodal_service.py`
- 已有 markdown_image_extractor.py: `backend/app/services/markdown_image_extractor.py`
- Claude Vision API: https://docs.anthropic.com/en/docs/build-with-claude/vision

## UAT Script

> 1. 在 `wiki/concepts/` 下创建一个含图片的笔记，例如 `binary-tree.md`，嵌入一张二叉树示意图 `![[attachments/binary-tree-diagram.png]]`
> 2. 启动 AI 对话
> 3. 提问："这张图里的数据结构是什么类型？"
> 4. 验证 AI 能正确识别二叉树并给出解释
> 5. 验证 AI 的回答能将图片内容与笔记文本关联
> 6. 检查后端日志，确认图片分析完成且未写入知识图谱（`image_kg_persistence_disabled`）
> 7. 嵌入一张不存在的图片 `![[missing.png]]`，重新启动对话，验证对话正常、日志有 warning

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 图片检测 | unit | `pytest tests/unit/test_image_context_service.py::test_detect_images -x` | Obsidian + md 语法 |
| 路径解析 | unit | `pytest tests/unit/test_image_context_service.py::test_path_resolution -x` | 绝对路径正确 |
| 格式过滤 | unit | `pytest tests/unit/test_image_context_service.py::test_unsupported_format -x` | SVG 跳过 |
| 数量限制 | unit | `pytest tests/unit/test_image_context_service.py::test_max_3_images -x` | 第 4 张跳过 |
| 降级不持久化 | unit | `pytest tests/unit/test_image_context_service.py::test_no_kg_persistence -x` | 无写入调用 |

## User Feedback & Changes

### Feedback Log

(empty)

### Deviation Notes

(empty)

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

(to be filled by Dev agent)

### Completion Notes List

(to be filled by Dev agent)

### File List

(to be filled by Dev agent)
