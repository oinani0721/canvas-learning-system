# Epic 21.5.1: API参数格式修复与安全检查优化

> **状态**: ✅ Epic Completed (All Stories Implemented)
> **类型**: Brownfield Enhancement (Bug Fix)
> **优先级**: P0 - Critical (所有Agent功能阻塞)
> **预计Stories**: 3个
> **创建日期**: 2025-12-14

---

## Epic Goal

修复"Path Traversal检测误报"Bug，使所有Agent端点恢复正常工作。该Bug导致用户在Obsidian中右键调用任何Agent功能时都返回HTTP 500错误。

---

## Epic Description

### Existing System Context

- **当前功能**: Canvas Learning System提供14个AI Agent，通过Obsidian插件右键菜单调用
- **技术栈**:
  - 前端: TypeScript (Obsidian Plugin)
  - 后端: Python 3.9+ / FastAPI
- **集成点**: `main.ts` → `ApiClient.ts` → HTTP POST → `agents.py` → `canvas_service.py`

### Enhancement Details

**问题根源 (双重故障)**:

| 层级 | 问题 | 文件 | 行号 |
|------|------|------|------|
| **前端** | `context.filePath`(完整路径)被当作`canvas_name`发送 | `main.ts` | 300,320,340,359,430,450,470,490,511 |
| **后端** | Path Traversal检查禁止所有含`/`的名称 | `canvas_service.py` | 49-62 |

**错误流程**:
```
用户右键点击节点 → 选择Agent
        ↓
main.ts发送: canvas_name="笔记库/子目录/test.canvas"  ❌
        ↓
后端检测到 "/" → ValidationError("Path traversal detected")
        ↓
HTTP 500 Internal Server Error
```

**修复方案**:
1. 前端: 从filePath提取文件名 `path.split('/').pop()`
2. 后端: 优化安全检查，允许合法的Canvas路径

### Success Criteria

- [x] 所有9个Agent端点调用成功 (decompose, explain/*, score, etc.)
- [x] 子目录下的Canvas文件也能正常工作
- [x] 无HTTP 500错误
- [x] 保持真正的Path Traversal攻击防护 (`..`仍被阻止)

---

## Stories

### Story 21.5.1.1: 修复前端canvas_name参数构建 (P0)

**目标**: 修改main.ts中所有API调用，从完整路径提取Canvas文件名

**验收标准**:
- [x] AC-1: 创建辅助函数`extractCanvasFileName(filePath: string): string`
- [x] AC-2: 修改9处API调用使用该函数
- [x] AC-3: 单元测试覆盖边界情况 (无路径、Windows路径、深层路径)

**修改文件**:
- `canvas-progress-tracker/obsidian-plugin/main.ts`

**代码示例**:
```typescript
// 辅助函数
private extractCanvasFileName(filePath: string | undefined): string {
    if (!filePath) return '';
    // 支持 / 和 \ 路径分隔符
    return filePath.split(/[/\\]/).pop() || '';
}

// 调用示例
canvas_name: this.extractCanvasFileName(context.filePath)
```

---

### Story 21.5.1.2: 优化后端Path Traversal安全检查 (P1)

**目标**: 修改`_validate_canvas_name()`，允许合法路径但阻止真正的攻击

**验收标准**:
- [x] AC-1: 允许Canvas路径中的`/`字符
- [x] AC-2: 仍然阻止`..`(目录遍历)、`\0`(空字节注入)
- [x] AC-3: 添加路径规范化，防止`/./`、`//`等变种攻击
- [x] AC-4: 单元测试覆盖安全边界

**修改文件**:
- `backend/app/services/canvas_service.py`

**代码示例**:
```python
def _validate_canvas_name(self, canvas_name: str) -> None:
    """
    Validate canvas name to prevent path traversal attacks.

    Allowed: Forward slashes for subdirectory paths
    Blocked: .., \0, consecutive slashes, backslashes
    """
    dangerous_patterns = [
        '..', '\0', '\\', '//', '/./',
    ]
    for pattern in dangerous_patterns:
        if pattern in canvas_name:
            raise ValidationError(f"Invalid canvas path: {canvas_name}")

    # 确保路径不以/开头(绝对路径)
    if canvas_name.startswith('/'):
        raise ValidationError(f"Absolute path not allowed: {canvas_name}")
```

---

### Story 21.5.1.3: 添加集成测试与回归验证 (P2)

**目标**: 确保修复不引入新问题，并防止回归

**验收标准**:
- [x] AC-1: 添加前端单元测试 `extractCanvasFileName()`
- [x] AC-2: 添加后端单元测试 `_validate_canvas_name()`
- [x] AC-3: 添加端到端测试 (插件调用 → 后端响应)
- [x] AC-4: 运行现有测试套件，确保无回归

**测试文件**:
- `canvas-progress-tracker/obsidian-plugin/tests/` (新建)
- `backend/tests/unit/test_canvas_service.py`

---

## Compatibility Requirements

- [x] 现有APIs接口签名不变
- [x] 无数据库Schema变更
- [x] UI变更遵循现有模式
- [x] 性能影响最小

---

## Risk Mitigation

| 风险 | 缓解措施 | 回滚计划 |
|------|----------|----------|
| 安全检查放宽可能引入漏洞 | 保留`..`检查，仅允许`/` | 恢复原有严格检查 |
| 前端修改影响其他功能 | 提取独立辅助函数，不修改核心逻辑 | Git revert main.ts |
| 测试不充分 | Story 3专门做测试 | 增量部署，监控bug_log |

---

## Definition of Done

- [x] 所有Stories完成且验收标准通过
- [x] 现有功能通过回归测试
- [x] 集成点工作正常
- [ ] 文档已更新 (CHANGELOG.md) - 待更新
- [x] 无功能回归

---

## 实现记录

> **Epic 21.5.1 已于 2025-12-14 完成实现**
>
> **实现摘要**:
> - 前端: `extractCanvasFileName()` 辅助函数 @ `main.ts:1512`
> - 后端: `_validate_canvas_name()` 安全检查优化 @ `canvas_service.py:49-69`
> - 测试: `extractCanvasFileName.test.ts` + `test_canvas_validation.py`
>
> **关键修改**:
> - 9处API调用现在使用文件名提取
> - 安全检查允许 `/` 但仍阻止 `..`, `\0`, `\\`, `//`, `/./`
> - 阻止绝对路径 (以 `/` 开头)

---

## 技术分析记录

### 错误信息
```
HTTP 500: Path traversal detected in canvas name:
2025_lecture_53_05_corrected_hold.pdf-3820ad9e-e32b-4f96-87da-83918ade5c6c/2025_lecture_53_05_corrected_hold.md
```

### 双重根源分析

#### 根源A：前端参数构建错误 (main.ts)
- **问题**: 9处API调用都使用`context.filePath`(完整路径)作为`canvas_name`
- **期望**: `canvas_name`应该是文件名，如`"离散数学.canvas"`
- **实际**: 发送了完整路径，如`"笔记库/离散数学.canvas"`
- **受影响行号**: 300, 320, 340, 359, 430, 450, 470, 490, 511

#### 根源B：后端安全检查过于严格 (canvas_service.py:49-62)
```python
def _validate_canvas_name(self, canvas_name: str) -> None:
    dangerous_patterns = ['..', '/', '\\', '\0']
    for pattern in dangerous_patterns:
        if pattern in canvas_name:
            raise ValidationError(f"Path traversal detected...")
```
- **问题**: 完全禁止`/`字符，但正常路径也包含`/`
- **影响**: 即使修复前端，任何子目录下的Canvas也会失败

### 错误流程图
```
用户右键点击节点 → 选择Agent操作
        ↓
ContextMenuManager提取 filePath = "笔记库/子目录/test.canvas"
        ↓
main.ts: canvas_name = context.filePath  ❌ 错误！应该提取文件名
        ↓
API请求发送: {"canvas_name": "笔记库/子目录/test.canvas", "node_id": "xxx"}
        ↓
后端 _validate_canvas_name() 检测到 "/" → 抛出异常
        ↓
HTTP 500: "Path traversal detected in canvas name"
```
