"""
Canvas学习系统 - 本地化支持模块

提供多语言支持和本地化功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class LocalizationManager:
    """本地化管理器"""

    def __init__(self, default_language: str = "zh-CN"):
        self.default_language = default_language
        self.current_language = default_language
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()

    def load_translations(self):
        """加载翻译文件"""
        translations_dir = Path("translations")

        # 内置翻译（避免文件依赖）
        self.translations = {
            "zh-CN": {
                # 系统消息
                "command_not_found": "命令未找到: {command}",
                "invalid_parameters": "参数错误: {error}",
                "execution_failed": "命令执行失败: {error}",
                "timeout": "命令执行超时",
                "success": "执行成功",
                "error": "执行失败",

                # 帮助信息
                "help_title": "Canvas学习系统帮助",
                "usage": "用法",
                "examples": "示例",
                "parameters": "参数",
                "description": "描述",
                "aliases": "别名",
                "category": "类别",

                # 参数类型
                "string": "字符串",
                "integer": "整数",
                "boolean": "布尔值",
                "flag": "标志",
                "path": "路径",
                "choice": "选择",

                # 类别名称
                "system": "系统命令",
                "canvas": "Canvas操作",
                "memory": "记忆系统",
                "analytics": "数据分析",
                "utilities": "实用工具",

                # 常用词汇
                "required": "必需",
                "optional": "可选",
                "default": "默认",
                "yes": "是",
                "no": "否",
                "true": "真",
                "false": "假",
                "cancel": "取消",
                "confirm": "确认",
                "back": "返回",
                "next": "下一步",
                "previous": "上一步",
                "finish": "完成",
                "save": "保存",
                "load": "加载",
                "delete": "删除",
                "edit": "编辑",
                "view": "查看",
                "search": "搜索",
                "export": "导出",
                "import": "导入",
                "settings": "设置",
                "about": "关于",
                "help": "帮助",
                "exit": "退出",

                # 错误消息
                "file_not_found": "文件未找到: {file}",
                "permission_denied": "权限不足",
                "invalid_format": "格式无效",
                "network_error": "网络错误",
                "server_error": "服务器错误",
                "unknown_error": "未知错误",

                # 成功消息
                "operation_completed": "操作完成",
                "file_saved": "文件已保存",
                "data_exported": "数据已导出",
                "settings_updated": "设置已更新",

                # 命令特定消息
                "canvas_status_ok": "Canvas系统状态正常",
                "memory_search_results": "找到 {count} 条相关记忆",
                "analysis_completed": "分析完成",
                "validation_passed": "验证通过",
                "validation_failed": "验证失败",
            },

            "en-US": {
                # System messages
                "command_not_found": "Command not found: {command}",
                "invalid_parameters": "Invalid parameters: {error}",
                "execution_failed": "Command execution failed: {error}",
                "timeout": "Command execution timeout",
                "success": "Success",
                "error": "Error",

                # Help information
                "help_title": "Canvas Learning System Help",
                "usage": "Usage",
                "examples": "Examples",
                "parameters": "Parameters",
                "description": "Description",
                "aliases": "Aliases",
                "category": "Category",

                # Parameter types
                "string": "String",
                "integer": "Integer",
                "boolean": "Boolean",
                "flag": "Flag",
                "path": "Path",
                "choice": "Choice",

                # Category names
                "system": "System Commands",
                "canvas": "Canvas Operations",
                "memory": "Memory System",
                "analytics": "Data Analytics",
                "utilities": "Utilities",

                # Common words
                "required": "Required",
                "optional": "Optional",
                "default": "Default",
                "yes": "Yes",
                "no": "No",
                "true": "True",
                "false": "False",
                "cancel": "Cancel",
                "confirm": "Confirm",
                "back": "Back",
                "next": "Next",
                "previous": "Previous",
                "finish": "Finish",
                "save": "Save",
                "load": "Load",
                "delete": "Delete",
                "edit": "Edit",
                "view": "View",
                "search": "Search",
                "export": "Export",
                "import": "Import",
                "settings": "Settings",
                "about": "About",
                "help": "Help",
                "exit": "Exit",

                # Error messages
                "file_not_found": "File not found: {file}",
                "permission_denied": "Permission denied",
                "invalid_format": "Invalid format",
                "network_error": "Network error",
                "server_error": "Server error",
                "unknown_error": "Unknown error",

                # Success messages
                "operation_completed": "Operation completed",
                "file_saved": "File saved",
                "data_exported": "Data exported",
                "settings_updated": "Settings updated",

                # Command specific messages
                "canvas_status_ok": "Canvas system status is OK",
                "memory_search_results": "Found {count} related memories",
                "analysis_completed": "Analysis completed",
                "validation_passed": "Validation passed",
                "validation_failed": "Validation failed",
            }
        }

        # 尝试从文件加载额外的翻译
        if translations_dir.exists():
            for lang_file in translations_dir.glob("*.json"):
                lang_code = lang_file.stem
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        file_translations = json.load(f)
                        if lang_code in self.translations:
                            self.translations[lang_code].update(file_translations)
                        else:
                            self.translations[lang_code] = file_translations
                except Exception as e:
                    print(f"加载翻译文件失败 {lang_file}: {e}")

    def set_language(self, language: str):
        """设置当前语言"""
        if language in self.translations:
            self.current_language = language
        else:
            print(f"语言 {language} 不支持，使用默认语言 {self.default_language}")
            self.current_language = self.default_language

    def get_text(self, key: str, **kwargs) -> str:
        """获取本地化文本"""
        # 尝试获取当前语言的翻译
        if self.current_language in self.translations:
            text = self.translations[self.current_language].get(key)
            if text:
                return text.format(**kwargs) if kwargs else text

        # 尝试获取默认语言的翻译
        if self.default_language in self.translations:
            text = self.translations[self.default_language].get(key)
            if text:
                return text.format(**kwargs) if kwargs else text

        # 如果都没有找到，返回key本身
        return key.format(**kwargs) if kwargs else key

    def get_available_languages(self) -> list:
        """获取可用语言列表"""
        return list(self.translations.keys())

    def add_translation(self, language: str, key: str, text: str):
        """添加翻译"""
        if language not in self.translations:
            self.translations[language] = {}
        self.translations[language][key] = text

    def translate_parameter_type(self, param_type: str) -> str:
        """翻译参数类型"""
        return self.get_text(param_type)

    def translate_category(self, category: str) -> str:
        """翻译类别名称"""
        return self.get_text(category)

    def format_help_text(self, command_info: Dict[str, Any]) -> str:
        """格式化帮助文本"""
        # 根据当前语言选择格式
        if self.current_language.startswith("zh"):
            return self._format_help_chinese(command_info)
        else:
            return self._format_help_english(command_info)

    def _format_help_chinese(self, command_info: Dict[str, Any]) -> str:
        """格式化中文帮助"""
        lines = []
        lines.append(f"# {command_info['name']}")

        if command_info.get('aliases'):
            aliases = ", ".join(command_info['aliases'])
            lines.append(f"**别名**: {aliases}")

        lines.append(f"**描述**: {command_info['description']}")
        lines.append(f"**用法**: {command_info['usage']}")

        if command_info.get('parameters'):
            lines.append("**参数**:")
            for param in command_info['parameters']:
                required_str = "必需" if param['required'] else f"可选 (默认: {param.get('default', '无')})"
                param_type = self.translate_parameter_type(param['type'])
                lines.append(f"  --{param['name']} ({param_type}): {param['description']} - {required_str}")

        if command_info.get('examples'):
            lines.append("**示例**:")
            for example in command_info['examples']:
                lines.append(f"  {example}")

        return "\n".join(lines)

    def _format_help_english(self, command_info: Dict[str, Any]) -> str:
        """格式化英文帮助"""
        lines = []
        lines.append(f"# {command_info['name']}")

        if command_info.get('aliases'):
            aliases = ", ".join(command_info['aliases'])
            lines.append(f"**Aliases**: {aliases}")

        lines.append(f"**Description**: {command_info['description']}")
        lines.append(f"**Usage**: {command_info['usage']}")

        if command_info.get('parameters'):
            lines.append("**Parameters**:")
            for param in command_info['parameters']:
                required_str = "Required" if param['required'] else f"Optional (default: {param.get('default', 'none')})"
                param_type = self.translate_parameter_type(param['type'])
                lines.append(f"  --{param['name']} ({param_type}): {param['description']} - {required_str}")

        if command_info.get('examples'):
            lines.append("**Examples**:")
            for example in command_info['examples']:
                lines.append(f"  {example}")

        return "\n".join(lines)

# 全局本地化管理器实例
_localization_manager: Optional[LocalizationManager] = None

def get_localization_manager() -> LocalizationManager:
    """获取全局本地化管理器实例"""
    global _localization_manager
    if _localization_manager is None:
        _localization_manager = LocalizationManager()
    return _localization_manager

def set_language(language: str):
    """设置系统语言"""
    manager = get_localization_manager()
    manager.set_language(language)

def get_text(key: str, **kwargs) -> str:
    """获取本地化文本（便捷函数）"""
    manager = get_localization_manager()
    return manager.get_text(key, **kwargs)

def t(key: str, **kwargs) -> str:
    """获取本地化文本（简写函数）"""
    return get_text(key, **kwargs)

# 初始化默认语言
def init_localization(language: str = "zh-CN"):
    """初始化本地化系统"""
    global _localization_manager
    _localization_manager = LocalizationManager(language)
    return _localization_manager