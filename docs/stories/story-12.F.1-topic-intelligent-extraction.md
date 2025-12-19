# Story 12.F.1: Topic 智能提取

**Story ID**: STORY-12.F.1
**Epic**: Epic 12.F - Agent 功能完整性修复
**优先级**: P0 BLOCKER
**状态**: Todo
**预估时间**: 4 小时
**创建日期**: 2025-12-16

---

## 用户故事

**作为** 使用 Canvas 学习系统的用户
**我希望** 当我选择一个节点并调用 Agent 解释功能时，AI 能正确理解我要解释的概念
**以便** 获得与所选节点真正相关的高质量解释内容

---

## 问题背景

### 当前问题

`_extract_topic_from_content()` 只取内容的第一行作为 topic，当第一行是元数据时，AI 收到错误的主题。

**BUG 代码位置**: `backend/app/services/agent_service.py:1089-1127`

```python
def _extract_topic_from_content(self, content: str, max_length: int = 50) -> str:
    first_line = content.strip().split('\n')[0].strip()  # BUG: 只用第一行
    return first_line if first_line else "Unknown"
```

### 问题影响

| 输入内容 | 预期 topic | 实际 topic |
|----------|------------|------------|
| `🧭 知识图谱控制中心\n# Level Set` | Level Set | 🧭 知识图谱控制中心 |
| `---\n# 概率论\n...` | 概率论 | --- |
| `<!-- meta -->\n# 线性代数` | 线性代数 | <!-- meta --> |

---

## 验收标准

- [ ] `_extract_topic_from_content()` 跳过元数据行
- [ ] 正确识别以下元数据模式:
  - Emoji 开头行 (🧭, 📊, 📋, 🔗 等)
  - Markdown 分隔符 (---)
  - HTML 注释 (<!-- -->)
  - 元数据前缀 (canvas:, note:)
- [ ] 返回第一个有效的概念名称
- [ ] 单元测试覆盖 10+ 种输入格式
- [ ] 现有测试不回归

---

## 技术方案

### 修改文件

- `backend/app/services/agent_service.py`

### 实现代码

```python
def _extract_topic_from_content(self, content: str, max_length: int = 50) -> str:
    """
    智能提取 topic，跳过元数据行

    策略:
    1. 遍历所有行，跳过元数据行
    2. 找到第一个有效的概念名称
    3. 清理 markdown 标记
    4. 截断超长内容
    """
    if not content or not content.strip():
        return "Unknown"

    lines = content.strip().split('\n')

    for line in lines:
        line = line.strip()

        # 跳过空行
        if not line:
            continue

        # 跳过元数据行
        if self._is_metadata_line(line):
            continue

        # 清理 markdown 标题标记
        if line.startswith('#'):
            line = line.lstrip('#').strip()

        # 清理其他 markdown 格式
        line = self._clean_markdown(line)

        # 找到有效 topic
        if line and len(line) >= 2:
            return line[:max_length] if len(line) > max_length else line

    return "Unknown"


def _is_metadata_line(self, line: str) -> bool:
    """
    判断是否为元数据行

    元数据行模式:
    - 导航 emoji 开头
    - Markdown 分隔符
    - HTML 注释
    - 元数据前缀
    """
    # 导航/装饰 emoji
    nav_emojis = ['🧭', '📊', '📋', '🔗', '📌', '🗂️', '📁', '🏠', '⬅️', '➡️']

    # Markdown/HTML 元素
    md_patterns = ['---', '<!--', '```', '|', '>', '*']

    # 元数据前缀
    meta_prefixes = ['canvas:', 'note:', 'created:', 'updated:', 'tags:']

    # 特殊格式
    special_patterns = ['**[', '[[', '{{']

    # 检查 emoji
    for emoji in nav_emojis:
        if line.startswith(emoji):
            return True

    # 检查 markdown 模式
    for pattern in md_patterns:
        if line.startswith(pattern):
            return True

    # 检查元数据前缀
    for prefix in meta_prefixes:
        if line.lower().startswith(prefix):
            return True

    # 检查特殊格式
    for pattern in special_patterns:
        if line.startswith(pattern):
            return True

    return False


def _clean_markdown(self, text: str) -> str:
    """清理 markdown 格式标记"""
    import re

    # 移除粗体/斜体
    text = re.sub(r'\*+([^*]+)\*+', r'\1', text)

    # 移除链接 [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # 移除内部链接 [[link]] -> link
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)

    return text.strip()
```

---

## 测试用例

```python
class TestTopicExtraction:
    """Story 12.F.1: Topic 智能提取测试"""

    def test_skip_emoji_metadata(self):
        """跳过 emoji 元数据行"""
        content = "🧭 知识图谱控制中心\n# Level Set\n定义..."
        assert extract_topic(content) == "Level Set"

    def test_skip_markdown_separator(self):
        """跳过 markdown 分隔符"""
        content = "---\n# 概率论\n内容..."
        assert extract_topic(content) == "概率论"

    def test_skip_html_comment(self):
        """跳过 HTML 注释"""
        content = "<!-- metadata -->\n# 线性代数\n内容..."
        assert extract_topic(content) == "线性代数"

    def test_clean_markdown_heading(self):
        """清理 markdown 标题标记"""
        content = "## 机器学习基础\n内容..."
        assert extract_topic(content) == "机器学习基础"

    def test_clean_bold_text(self):
        """清理粗体标记"""
        content = "**量子力学**\n内容..."
        assert extract_topic(content) == "量子力学"

    def test_skip_multiple_metadata_lines(self):
        """跳过多个元数据行"""
        content = """🧭 导航
---
📊 统计
# 真正的主题
内容..."""
        assert extract_topic(content) == "真正的主题"

    def test_truncate_long_topic(self):
        """截断超长 topic"""
        content = "这是一个非常非常非常非常非常非常非常非常非常非常长的主题名称"
        result = extract_topic(content, max_length=20)
        assert len(result) <= 20

    def test_return_unknown_for_empty(self):
        """空内容返回 Unknown"""
        assert extract_topic("") == "Unknown"
        assert extract_topic(None) == "Unknown"
        assert extract_topic("   ") == "Unknown"

    def test_skip_table_rows(self):
        """跳过表格行"""
        content = "| 列1 | 列2 |\n|---|---|\n# 实际主题"
        assert extract_topic(content) == "实际主题"

    def test_real_world_lecture_content(self):
        """真实 Lecture 内容测试"""
        content = """🧭 **[知识图谱控制中心-Lecture5.md](canvas://Lecture5)**

---

# Section 14.1 Level Set Method

Level Set 方法是一种..."""
        assert extract_topic(content) == "Section 14.1 Level Set Method"
```

---

## 依赖关系

- **被依赖**: Story 12.F.2, 12.F.3 依赖本 Story
- **无前置依赖**: 可以立即开始

---

## Definition of Done

- [ ] 代码实现完成
- [ ] 10+ 单元测试通过
- [ ] 现有测试不回归
- [ ] 代码 Review 通过
- [ ] 文档更新
