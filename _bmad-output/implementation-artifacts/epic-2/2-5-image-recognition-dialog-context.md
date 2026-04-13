---
doc_type: story
story_id: "2.5"
aliases: ["2.5"]
epic_id: "EPIC-2"
prd_id: "PRD14"
status: ready-for-dev
priority: "P2"
estimate_hours: 4
depends_on: ["2.1"]
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 2.5: 图片识别纳入 AI 对话上下文

## Story

As a 学习者,
I want 系统识别笔记中嵌入的图片并纳入 AI 对话上下文,
so that 我可以就图片内容（图表、公式截图等）向 AI 提问。

## Acceptance Criteria

1. **Given** 当前笔记中嵌入了图片（`![[image.png]]` 或 `![](path)` 格式）
   **When** 学习者启动 AI 对话
   **Then** 系统提取图片并通过多模态 LLM 获取描述
   **And** 图片描述作为额外上下文注入对话
   **And** 只传筛选后的图片，不传整个 vault 的图片（NFR-INT-3）

## Tasks / Subtasks

- [ ] Task 1: 实现图片提取与路径解析 (AC: #1)
  - [ ] 1.1 在 `backend/app/services/` 新建 `image_context_service.py`，定义 `ImageContextService` 类
  - [ ] 1.2 实现 `extract_images(note_path: str, vault_path: str) -> List[ImageRef]`：解析 `.md` 文件中的 `![[image.png]]`（wikilink 格式）和 `![alt](relative/path)` 格式图片引用
  - [ ] 1.3 `ImageRef` dataclass：`filename: str`、`absolute_path: str`、`alt_text: str`、`embed_syntax: str`
  - [ ] 1.4 wikilink 格式图片路径解析：从 vault 根目录递归搜索匹配文件名，找到第一个匹配文件返回绝对路径
  - [ ] 1.5 过滤策略（NFR-INT-3）：只提取当前笔记正文中直接引用的图片，不递归提取邻居笔记的图片；支持的格式 `.png`、`.jpg`、`.jpeg`、`.gif`、`.webp`；单笔记最多处理 3 张图片（避免超出多模态 LLM 限制）

- [ ] Task 2: 多模态 LLM 图片描述生成 (AC: #1)
  - [ ] 2.1 实现 `describe_image(image_path: str) -> str`：读取图片文件，Base64 编码，发送到多模态 LLM 获取描述
  - [ ] 2.2 多模态 LLM 调用：通过 Ollama API（`/api/generate`）使用 `llava` 或 `moondream` 模型（项目配置中的多模态模型）
  - [ ] 2.3 prompt 模板：`"请简洁描述这张图片的内容，重点关注图中的数学公式、图表结构、标注文字。不超过 150 字。"`
  - [ ] 2.4 图片描述超时设为 10s；超时或模型不可用时返回 `f"[图片: {filename}，描述获取失败]"` 占位字符串，不抛异常
  - [ ] 2.5 图片描述结果缓存：以图片文件路径 + mtime 为 key，内存 LRU 缓存（maxsize=50），避免同一图片重复调用多模态 LLM

- [ ] Task 3: 图片描述注入对话上下文 (AC: #1)
  - [ ] 3.1 修改 `DialogContextService.build_context()`（Story 2.1 实现），在上下文组装阶段调用 `ImageContextService.extract_images()` + `describe_image()`
  - [ ] 3.2 图片描述以结构化方式追加到系统 prompt：`## 笔记中的图片\n- 图片 image.png：{描述}\n- 图片 chart.png：{描述}`
  - [ ] 3.3 图片描述的 token 预算：在 3K token 总限制内，为图片区域预留最多 400 tokens（每张约 130 tokens）；超出时截断最后一张图片描述
  - [ ] 3.4 图片区域在上下文中的优先级：高于邻居摘要，低于当前笔记正文（即：当前笔记 > 图片描述 > 邻居摘要）

- [ ] Task 4: 编写测试 (AC: #1)
  - [ ] 4.1 单元测试 `backend/tests/unit/test_image_context_service.py`：
    - `extract_images()` 正确解析 `![[image.png]]` 和 `![alt](path)` 两种格式
    - 超过 3 张图片时只返回前 3 张
    - vault 中找不到图片文件时返回空列表（不抛异常）
    - `describe_image()` 超时时返回占位字符串
  - [ ] 4.2 单元测试缓存：同一图片路径（mtime 不变）第二次调用时命中缓存，不再调用多模态 LLM
  - [ ] 4.3 集成测试 `backend/tests/integration/test_image_context_injection.py`：
    - 含图片的笔记启动对话时，`build_context()` 返回的 system prompt 包含图片描述段落
    - 图片描述 token 数 ≤ 400
  - [ ] 4.4 前端测试：无需新增（图片上下文对前端透明，通过 Story 2.1 的 `ChatPanel.test.tsx` 覆盖）

## Dev Notes

- **wikilink 图片格式**：Obsidian 的 `![[image.png]]` 是 wikilink embed 语法，需要在 vault 全局搜索文件名匹配（不是相对路径）。obsidiantools 库支持 attachment 解析，可以复用 Story 1.2 的 `WikilinkGraph` 实例
- **多模态模型选择**：优先使用 `llava:7b`（Ollama 官方支持，图文理解能力强），若 Ollama 未拉取 llava 则降级到纯文本占位字符串。通过 `settings.MULTIMODAL_MODEL`（配置项）读取，不硬编码模型名
- **Base64 大小限制**：单张图片 Base64 后不超过 2MB（约 1.5MB 原图），超出则压缩（使用 Pillow 缩放到 800px 宽）再编码。Pillow 是项目已有依赖
- **NFR-INT-3 图片过滤**：只传当前笔记的图片，明确不传：邻居笔记的图片、vault 其他笔记的图片。`extract_images()` 的 `note_path` 参数必须是当前活跃笔记路径，不能是邻居路径
- **LRU 缓存**：使用 `functools.lru_cache` 不够（需要 mtime 参数），改用 `cachetools.LRUCache`（已在 backend 依赖中）或自己实现简单的 `{(path, mtime): description}` 字典缓存

### Project Structure Notes

- 新建文件：`backend/app/services/image_context_service.py`
- 修改文件：`backend/app/services/dialog_context_service.py`（注入图片描述，Story 2.1 实现）
- 测试文件：
  - `backend/tests/unit/test_image_context_service.py`
  - `backend/tests/integration/test_image_context_injection.py`
- 样式参考：`backend/app/services/rag_service.py`（service 结构，LLM 调用模式）

### References

- [Source: backend/app/services/wikilink_graph.py] — Story 1.2 WikilinkGraph，wikilink attachment 解析可复用
- [Source: backend/app/services/dialog_context_service.py] — Story 2.1 实现，本 story 修改的核心文件
- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.5] — AC 原文和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR46] — FR46 原文：图片识别纳入 AI 对话上下文
- [Source: docker-compose.yml#ollama] — Ollama 服务配置，多模态模型需从此服务拉取

## UAT Script

> 非技术用户验收脚本：只描述用户操作和预期看到的内容，不含代码术语。

1. **验证 AI 能理解笔记中的图片** (AC: #1)
   - 打开一篇包含图片的笔记（例如：笔记中有一张贴入的数学图表截图）
   - 启动 AI 对话，提问："请解释这张图的含义"或"图中显示了什么？"
   - AI 的回复中应该包含对图片内容的描述（不应回答"我无法查看图片"）
   - 如果 AI 表示看不到图片，请记录 Story 2.5 和图片格式（是 ![[图片名]] 还是 ![](路径)）

2. **验证不会处理其他笔记的图片** (AC: #1)
   - 打开一篇本身没有图片的笔记，但该笔记链接到了含图片的笔记
   - 启动 AI 对话
   - AI 回复中不应该出现对链接笔记图片的描述
   - 如果 AI 描述了当前笔记没有的图片内容，请记录 Story 2.5

3. **验证图片加载失败时对话仍可用** (AC: #1)
   - 打开一篇引用了不存在图片文件的笔记（图片已被删除但 ![[]] 语法还在）
   - 启动 AI 对话，发送任意问题
   - 对话应正常进行，AI 应能正常回复（不因图片加载失败而崩溃）
   - 如果对话崩溃或报错，请记录 Story 2.5 和错误内容

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-2.5.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_image_context_service.py -x -q` | 0 failed |
| CP-2.5.2 | pytest | `.venv/bin/pytest backend/tests/integration/test_image_context_injection.py -x -q` | 0 failed |
| CP-2.5.3 | ruff | `ruff check backend/app/services/image_context_service.py` | exit 0 |

## User Feedback & Changes

### Feedback Log

<!-- Users write BMAD-ANNO callouts below. Claude scans and dispatches by intent. -->

### Deviation Notes

<!-- Claude auto-fills: summary of historically processed feedback -->

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List

## Relations

- EPIC: [[EPIC-2]]
- PRD: [[PRD14]]
- Depends on: [[2.1]]
