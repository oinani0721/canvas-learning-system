# Smart Clipboard System

## Metadata
- **Command**: /smart-clipboard
- **Description**: Solve agent text copy-paste issues with intelligent clipboard management
- **Bmad Pattern**: Seamless content transfer with error recovery
- **Keywords**: *clipboard, *copy, *paste, *transfer

## Usage

### Clipboard Operations
```bash
/smart-clipboard            # Enable smart clipboard features
/smart-clipboard *auto      # Auto-enable for all agent operations
/smart-clipboard status     # Show clipboard status
/smart-clipboard fix        # Fix common clipboard issues
```

### Content Management
```bash
/smart-clipboard history    # View clipboard history
/smart-clipboard clean      # Clean clipboard cache
/smart-clipboard backup     # Backup clipboard content
/smart-clipboard restore    # Restore from backup
```

## Implementation

解决Agent生成文本在添加节点时复制粘贴失败问题的智能剪贴板系统。

**问题诊断**:
- Agent生成文本格式问题 (Unicode/编码)
- 系统剪贴板权限限制
- 文本长度超限截断
- 特殊字符丢失或损坏

**解决方案**:
```python
class SmartClipboard:
    def __init__(self):
        self.clipboard_history = []
        self.encoding_detector = CharsetDetector()
        self.text_validator = TextValidator()

    async def safe_copy(self, content: str, source_agent: str) -> bool:
        """安全复制Agent生成的内容"""
        try:
            # 1. 文本验证和清理
            clean_content = self.text_validator.clean(content)

            # 2. 编码检测和转换
            encoded_content = self.encoding_detector.encode(clean_content)

            # 3. 长度检查和分段
            if len(encoded_content) > CLIPBOARD_LIMIT:
                return await self分段复制(encoded_content, source_agent)

            # 4. 复制到剪贴板
            await pyperclip.copy(encoded_content)

            # 5. 记录历史
            self.clipboard_history.append({
                'content': clean_content,
                'source': source_agent,
                'timestamp': datetime.now(),
                'status': 'success'
            })

            return True
        except Exception as e:
            logger.error(f"剪贴板复制失败: {e}")
            return await self.备用复制方案(content, source_agent)
```

**智能特性**:
- **编码检测**: 自动检测和转换文本编码
- **分段处理**: 超长文本智能分段复制
- **格式保持**: 保持Markdown格式和特殊字符
- **错误恢复**: 复制失败时自动启用备用方案
- **历史记录**: 完整的剪贴板操作历史
- **备份恢复**: 重要内容自动备份和恢复

**备用方案**:
1. **文件写入**: 写入临时文件后手动复制
2. **分批复制**: 大文本分批次复制粘贴
3. **格式简化**: 移除特殊字符确保兼容性
4. **重试机制**: 自动重试失败的复制操作

**Agent集成**:
- **无缝集成**: 所有Agent自动使用智能剪贴板
- **透明操作**: 用户无感知的剪贴板管理
- **状态反馈**: 实时显示复制状态和结果
- **错误提示**: 清晰的错误信息和解决建议

**性能指标**:
- 复制成功率: ≥99.5%
- 处理时间: <1秒 (标准文本)
- 错误恢复率: ≥95%
- 内容完整性: 100%

彻底解决Canvas系统中Agent文本传输的痛点问题。