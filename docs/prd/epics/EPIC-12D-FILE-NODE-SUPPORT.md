# Epic 12.D: FILE 类型节点内容读取支持 - Brownfield Enhancement

**版本**: 1.0
**创建日期**: 2025-12-15
**状态**: 待实施
**类型**: Brownfield Enhancement (Epic 12 扩展补丁 - P0 CRITICAL)
**来源**: UltraThink 深度调研报告

---

## 1. Epic 概述

### 1.1 Epic 目标

修复 FILE 类型 Canvas 节点内容从未被读取的致命 Bug，实现：
- 前端支持读取 FILE 类型节点链接的 MD 文件内容
- 后端支持解析 FILE 类型节点并读取对应文件
- 完整的日志追踪链路，便于未来调试

### 1.2 问题背景

**UltraThink 深度调研发现**:

用户选择 Canvas 节点后调用 Agent 解释功能，生成的内容与所选节点**完全无关**：

| 测试 | 选择节点 | 预期输出 | 实际输出 |
|------|----------|----------|----------|
| 测试1 | Level Set定义 (kp01) | Level Set / 水平集解释 | 特征值和特征向量 |
| 测试2 | Level Set定义 (kp01) | Level Set / 水平集解释 | Transformer 模型 |

**根因确认**: kp01 节点是 **FILE 类型**，内容存储在外部 MD 文件中，但前后端均只处理 TEXT 类型。

### 1.3 历史错误假设

| Epic | 假设 | 验证结果 |
|------|------|---------|
| 12.B | node_content 参数没传递 | **错误** - 参数确实为空，但原因是 FILE 类型不支持 |
| 12.C | 上下文污染覆盖节点内容 | **错误** - 禁用后问题依然存在 |
| **12.D** | FILE 类型节点内容从未被读取 | **正确** - 根因确认 |

### 1.4 成功标准

| 指标 | 当前值 | 目标值 | 验证方法 |
|------|--------|--------|---------|
| FILE 节点内容读取成功率 | 0% | 100% | kp01 测试通过 |
| TEXT 节点功能完整性 | 100% | 100% | 回归测试 |
| AI 生成主题准确率 | 0% | 100% | Level Set 测试用例 |
| 日志可追踪性 | 0% | 100% | 节点类型+内容来源可见 |

---

## 2. 现有系统上下文

### 2.1 技术栈

- **后端**: FastAPI + Python 3.11
- **前端插件**: TypeScript + Obsidian API
- **Canvas 格式**: Obsidian Canvas JSON (.canvas)

### 2.2 关键集成点

```
canvas-progress-tracker/obsidian-plugin/
├── src/managers/ContextMenuManager.ts  # 右键菜单 - BUG位置
├── src/api/ApiClient.ts                # API 客户端
└── src/types/canvas.ts                 # Canvas 类型定义

backend/app/
├── api/v1/endpoints/agents.py          # Agent API 端点
├── services/agent_service.py           # Agent 服务层
├── services/context_enrichment_service.py  # 上下文增强 - BUG位置
└── services/canvas_service.py          # Canvas 文件服务
```

### 2.3 Obsidian Canvas 节点类型

| 类型 | JSON 字段 | 内容位置 | 当前支持 |
|------|-----------|----------|----------|
| `text` | `text: "内容..."` | JSON 内嵌 | ✅ 已支持 |
| `file` | `file: "path/to.md"` | 外部 MD 文件 | ❌ **未支持** |
| `link` | `url: "https://..."` | 外部 URL | ❌ 不需要 |
| `group` | - | 分组容器 | ❌ 不需要 |

### 2.4 BUG 链路图

```
用户点击 kp01 节点 (type=file)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  前端 BUG: ContextMenuManager.ts 第 871-874 行                    │
│                                                                   │
│  const nodeContent =                                              │
│    nodeInfo.nodeData?.type === 'text' && nodeInfo.nodeData?.text  │
│      ? nodeInfo.nodeData.text                                     │
│      : undefined;  // ← FILE 类型返回 undefined!                  │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
API 请求: POST /api/v1/agents/explain/four-level
         { canvas_name: "Lecture5", node_id: "kp01", node_content: null }
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  后端 BUG: context_enrichment_service.py 第 202 行                │
│                                                                   │
│  target_content = target_node.get("text", "")                    │
│                                                                   │
│  → FILE 节点没有 text 字段，返回空字符串 ""!                       │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
AI 收到空内容 → 完全幻觉 → 生成 Transformer/特征值等随机主题
```

---

## 3. Stories 列表

### Story 12.D.1: 前端支持 FILE 类型节点 (P0 BLOCKER)

**问题**: 前端只处理 TEXT 类型，FILE 类型节点返回 undefined

**BUG 代码** (ContextMenuManager.ts:871-874):
```typescript
const nodeContent: string | undefined =
  nodeInfo.nodeData?.type === 'text' && nodeInfo.nodeData?.text
    ? nodeInfo.nodeData.text
    : undefined;  // FILE 类型被忽略！
```

**修复方案**:
```typescript
// ✅ Verified from Obsidian API Docs (vault.cachedRead)
let nodeContent: string | undefined;

if (nodeInfo.nodeData?.type === 'text' && nodeInfo.nodeData?.text) {
  // TEXT 类型：直接从 JSON 读取
  nodeContent = nodeInfo.nodeData.text;
} else if (nodeInfo.nodeData?.type === 'file' && nodeInfo.nodeData?.file) {
  // FILE 类型：读取链接的 MD 文件内容
  const filePath = nodeInfo.nodeData.file;
  const abstractFile = this.app.vault.getAbstractFileByPath(filePath);
  if (abstractFile instanceof TFile) {
    // cachedRead 比 read 更快，使用缓存版本
    nodeContent = await this.app.vault.cachedRead(abstractFile);
    console.log(`[Story 12.D.1] Read FILE node content: ${filePath}, length: ${nodeContent.length}`);
  } else {
    console.warn(`[Story 12.D.1] File not found: ${filePath}`);
  }
}
```

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts` (第 871-880 行)

**验收标准**:
- [ ] FILE 类型节点的右键菜单能获取链接文件内容
- [ ] TEXT 类型节点仍然正常工作 (回归测试)
- [ ] console.log 显示 `[Story 12.D.1] Read FILE node content: ...`

**预估**: 1h

---

### Story 12.D.2: 后端支持 FILE 类型节点 (P0 BLOCKER)

**问题**: 后端只读取 .text 字段，FILE 节点返回空字符串

**BUG 代码** (context_enrichment_service.py:202):
```python
target_content = target_node.get("text", "")  # FILE 节点返回空字符串！
```

**修复方案**:
```python
# ✅ Verified from project config (VAULT_PATH in backend/.env)
def _get_node_content(self, node: dict) -> str:
    """
    获取节点内容，支持 text 和 file 类型

    Args:
        node: Canvas 节点数据

    Returns:
        节点文本内容
    """
    node_type = node.get("type", "")
    node_id = node.get("id", "unknown")

    if node_type == "text":
        # TEXT 类型：直接从 JSON 读取
        content = node.get("text", "")
        logger.debug(f"[Story 12.D.2] TEXT node {node_id}: {len(content)} chars")
        return content

    elif node_type == "file":
        # FILE 类型：读取链接的 MD 文件
        file_path = node.get("file", "")
        if file_path:
            try:
                # VAULT_PATH 来自 backend/.env 配置
                full_path = self._vault_path / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding="utf-8")
                    logger.info(f"[Story 12.D.2] FILE node {node_id}: read {file_path}, {len(content)} chars")
                    return content
                else:
                    logger.warning(f"[Story 12.D.2] FILE node {node_id}: file not found: {full_path}")
            except Exception as e:
                logger.error(f"[Story 12.D.2] Failed to read FILE node {node_id}: {e}")
        return ""

    else:
        logger.debug(f"[Story 12.D.2] Unknown node type: {node_type}")
        return ""

# 使用
target_content = self._get_node_content(target_node)
```

**修改文件**:
- `backend/app/services/context_enrichment_service.py` (第 195-230 行)

**验收标准**:
- [ ] FILE 类型节点能正确读取链接 MD 文件内容
- [ ] TEXT 类型节点仍然正常工作
- [ ] 日志显示 `[Story 12.D.2] FILE node kp01: read KP01-Level-Set定义.md, 2847 chars`

**预估**: 1h

---

### Story 12.D.3: 添加节点类型完整日志链 (P1)

**目标**: 在关键位置添加日志，追踪节点类型和内容来源，便于未来调试

**任务**:
1. 前端 `handleCanvasNodeContextMenu()` 记录节点类型和内容来源
2. 后端 `enrich_with_adjacent_nodes()` 记录节点类型和读取方式
3. 后端 `agents.py` 记录收到的 node_content 和 effective_content

**日志格式**:
```
[Story 12.D.3] Node content trace:
  - node_id: kp01
  - node_type: file
  - file_path: KP01-Level-Set定义.md
  - content_source: file_read | json_text | empty
  - content_length: 2847 chars
  - content_preview: # Level Set的定义...
```

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts`
- `backend/app/services/context_enrichment_service.py`
- `backend/app/api/v1/endpoints/agents.py`

**验收标准**:
- [ ] 日志清楚显示节点类型和内容来源
- [ ] 可追踪内容从前端到 AI 的完整流程
- [ ] 便于快速定位类似问题

**预估**: 30min

---

## 4. 实施优先级

| 优先级 | Story | 依赖 | 预估 | 风险 |
|--------|-------|------|------|------|
| **P0** | 12.D.1 前端 FILE 支持 | 无 | 1h | 低 |
| **P0** | 12.D.2 后端 FILE 支持 | 无 | 1h | 低 |
| **P1** | 12.D.3 日志追踪链 | 12.D.1, 12.D.2 | 30min | 低 |

**总预估**: 2.5h (单 Sprint 完成)

**实施顺序**:
```
Story 12.D.1 (前端 FILE 支持)  ←── 最高优先级
        ↓ (可并行)
Story 12.D.2 (后端 FILE 支持)
        ↓
Story 12.D.3 (日志追踪)
        ↓
验证测试
```

---

## 5. 兼容性要求

- [x] 现有 TEXT 类型节点处理逻辑不变
- [x] API 端点参数结构不变
- [x] 数据库 schema 无变更
- [x] UI 右键菜单无变更
- [x] 性能影响可忽略 (MD 文件读取 < 10ms)

---

## 6. 风险缓解

### 主要风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| MD 文件路径错误 | 读取失败返回空 | 添加详细日志，优雅降级 |
| 编码问题 | 中文乱码 | 强制 UTF-8 编码 |
| 文件不存在 | 读取失败 | 返回空字符串，记录警告日志 |

### 回滚计划

1. **代码级回滚**: 恢复原条件判断逻辑
2. **分步发布**: 先发布前端 12.D.1，验证后再发布后端 12.D.2
3. **无数据变更**: 纯代码修改，回滚无副作用

---

## 7. 快速验证测试

### 测试用例

```
Canvas: Math53/Lecture5.canvas
节点: kp01 (type=file, file=KP01-Level-Set定义.md)
操作: 四层次解释

预期结果:
✅ 生成内容包含 "Level Set" / "水平集" / "等高线"
❌ 不包含 "Transformer" / "特征值" / "特征向量"
```

### 测试步骤

1. **构建并部署插件**:
   ```powershell
   cd canvas-progress-tracker/obsidian-plugin && npm run build
   Copy-Item main.js "C:\Users\ROG\托福\Canvas\笔记库\.obsidian\plugins\canvas-review-system\" -Force
   ```

2. **重启后端**:
   ```powershell
   cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. **重启 Obsidian** (加载新插件)

4. **执行测试**:
   - 打开 `Canvas/Math53/Lecture5.canvas`
   - 右键点击 kp01 节点
   - 选择 "四层次解释"
   - 验证生成内容主题是否正确

---

## 8. 关键文件清单

### 需要修改的文件

| 文件 | 修改内容 | Story | 行号 |
|------|---------|-------|------|
| `ContextMenuManager.ts` | FILE 类型节点读取 | 12.D.1 | 871-880 |
| `context_enrichment_service.py` | _get_node_content() | 12.D.2 | 195-230 |
| `agents.py` | 日志增强 | 12.D.3 | 640-650 |

### 不需要新增文件

本 Epic 为纯修复性质，不需要创建新文件。

---

## 9. Definition of Done

- [ ] Story 12.D.1 完成：前端能读取 FILE 类型节点内容
- [ ] Story 12.D.2 完成：后端能读取 FILE 类型节点内容
- [ ] Story 12.D.3 完成：完整日志追踪链
- [ ] kp01 (Level Set) 测试用例通过
- [ ] TEXT 类型节点回归测试通过
- [ ] 插件重新构建并部署到正确 vault
- [ ] 后端重启并验证

---

## 10. Story Manager 交接

**请为此 Brownfield Epic 开发详细用户故事。关键考虑点**:

- 这是对现有系统的紧急修复，运行 FastAPI + TypeScript 技术栈
- 集成点: ContextMenuManager → API → context_enrichment_service
- 现有模式: 异步文件读取 (前端 vault.cachedRead，后端 pathlib)
- 关键兼容性要求: TEXT 类型节点功能不变

Epic 目标是在保持系统完整性的同时，修复 FILE 类型节点内容读取失败导致的 AI 幻觉问题。

---

## 附录 A: kp01 节点原始数据

```json
{
  "id": "kp01",
  "type": "file",
  "file": "2025_lecture_53_05_corrected_hold.pdf-3820ad9e-e32b-4f96-87da-83918ade5c6c/KP01-Level-Set定义.md",
  "color": "1",
  "height": 510,
  "width": 760,
  "x": -4880,
  "y": -440
}
```

**注意**: 没有 `text` 字段，内容在外部 MD 文件中。

---

## 附录 B: 证据汇总

| 证据编号 | 来源 | 内容 |
|----------|------|------|
| E1 | Lecture5.canvas:332-335 | `kp01.type = "file"` |
| E2 | Lecture5.canvas:330 | `kp01.file = "...KP01-Level-Set定义.md"` |
| E3 | ContextMenuManager.ts:871-874 | 只处理 `type === 'text'` |
| E4 | context_enrichment_service.py:202 | 只读取 `.text` 字段 |
| E5 | 用户测试 (Story 12.C.1) | 禁用上下文增强后问题依然存在 |

---

*Epic 12.D 创建完成 - 2025-12-15*
*基于 UltraThink 深度调研报告*
*修复 FILE 类型节点支持 - P0 CRITICAL*
