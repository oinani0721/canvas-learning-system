# ADR-011: 文件路径处理 - pathlib 标准化

## 状态

**已接受** | 2025-12-16

## 背景

Canvas Learning System 需要处理多种文件路径场景：

1. **Obsidian Vault 路径** - 用户笔记库根目录
2. **Canvas 文件路径** - `.canvas` 文件位置
3. **图片引用路径** - Markdown 中的 `![[image.png]]` 或 `![](path.png)`
4. **FILE 类型节点** - 引用外部 `.md` 文件的节点

### 跨平台挑战

| 平台 | 路径分隔符 | 示例 |
|------|-----------|------|
| Windows | `\` | `C:\Users\ROG\托福\Canvas\笔记库` |
| macOS/Linux | `/` | `/home/user/vault` |

### 常见问题

1. **字符串拼接** - `folder + "/" + file` 在 Windows 上可能失败
2. **路径规范化** - `./images/../assets/img.png` 需要解析
3. **相对路径解析** - 相对于 vault 或 canvas 文件目录
4. **路径存在性检查** - 需要跨平台一致的 API

## 决策

**统一使用 Python `pathlib.Path` 进行所有文件路径操作**

### 核心原则

```python
# ✅ 正确做法 - 使用 pathlib
from pathlib import Path

vault_path = Path("/path/to/vault")
image_path = vault_path / "images" / "formula.png"
resolved = image_path.resolve()
exists = resolved.exists()

# ❌ 错误做法 - 字符串拼接
vault_path = "/path/to/vault"
image_path = vault_path + "/" + "images" + "/" + "formula.png"  # Windows 兼容问题
```

### 使用规范

| 操作 | pathlib 方法 | 说明 |
|------|-------------|------|
| 路径拼接 | `path / "subdir" / "file"` | 使用 `/` 运算符 |
| 获取文件名 | `path.name` | 不含目录 |
| 获取文件名(无扩展) | `path.stem` | 如 `KP01-Level-Set定义` |
| 获取扩展名 | `path.suffix` | 如 `.md` |
| 获取父目录 | `path.parent` | |
| 路径规范化 | `path.resolve()` | 解析 `..` 和符号链接 |
| 检查存在 | `path.exists()` | |
| 检查是文件 | `path.is_file()` | |
| 相对路径 | `path.relative_to(base)` | |

### 应用场景

#### 1. Markdown 图片路径解析 (Story 12.E.4)

```python
from pathlib import Path
from typing import List, Optional

async def resolve_image_paths(
    refs: List[ImageReference],
    vault_path: Path,
    canvas_dir: Optional[Path] = None
) -> List[dict]:
    """
    解析图片引用的相对路径为绝对路径

    ✅ Verified from ADR-011: pathlib 标准化
    """
    resolved = []

    for ref in refs:
        candidates = [
            vault_path / ref.path,  # 相对于 vault
        ]
        if canvas_dir:
            candidates.append(canvas_dir / ref.path)  # 相对于 canvas

        for candidate in candidates:
            try:
                abs_path = candidate.resolve()
                if abs_path.exists() and abs_path.is_file():
                    resolved.append({
                        "reference": ref,
                        "absolute_path": str(abs_path),
                        "exists": True
                    })
                    break
            except Exception:
                continue

    return resolved
```

#### 2. FILE 类型节点路径处理 (Epic 12.D)

```python
def get_file_content(node: dict, vault_path: Path) -> Optional[str]:
    """
    读取 FILE 类型节点引用的文件内容

    ✅ Verified from ADR-011: pathlib 标准化
    """
    file_ref = node.get("file", "")
    if not file_ref:
        return None

    file_path = vault_path / file_ref
    resolved = file_path.resolve()

    if resolved.exists() and resolved.is_file():
        return resolved.read_text(encoding="utf-8")

    return None
```

#### 3. 文件名 Topic 提取 (Story 12.E.2)

```python
def extract_topic_from_filepath(file_path: str) -> str:
    """
    从文件路径提取主题名

    Example: "KP01-Level-Set定义.md" -> "Level Set定义"

    ✅ Verified from ADR-011: pathlib 标准化
    """
    path = Path(file_path)
    stem = path.stem  # 不含扩展名

    # 去掉前缀编号
    import re
    topic = re.sub(r'^KP\d+[-_]?', '', stem)
    topic = topic.replace('-', ' ').replace('_', ' ')

    return ' '.join(topic.split())
```

## 影响

### 正面影响

1. **跨平台兼容** - Windows/macOS/Linux 无需特殊处理
2. **代码清晰** - `path / "subdir"` 比 `os.path.join()` 更直观
3. **类型安全** - IDE 自动补全和类型检查
4. **错误减少** - 避免字符串拼接导致的路径错误
5. **一致性** - 整个项目统一的路径处理风格

### 负面影响

1. **轻微学习曲线** - 需要熟悉 pathlib API
2. **字符串转换** - 某些 API 需要 `str(path)` 转换

### 缓解措施

- 在代码注释中标注 `✅ Verified from ADR-011`
- 在 Story Dev Notes 中引用本 ADR

## 关联

### 受影响的 Stories

| Story | 影响 |
|-------|------|
| Story 12.E.4 | Markdown 图片路径解析使用 pathlib |
| Story 12.E.5 | Agent 多模态集成中的路径处理 |
| Epic 12.D | FILE 类型节点路径读取 |

### 相关 ADR

- **ADR-005**: LangGraph Checkpointer (SQLite 路径也使用 pathlib)
- **ADR-008**: 测试框架 (测试 fixtures 中的路径处理)

## 参考

- [Python pathlib 官方文档](https://docs.python.org/3/library/pathlib.html)
- [PEP 428 – The pathlib module](https://peps.python.org/pep-0428/)
