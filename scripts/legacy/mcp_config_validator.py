"""
MCP配置验证器
Canvas Learning System - Story 8.8

提供严格的配置文件验证和错误报告功能。
"""

import yaml
import os
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path

from mcp_exceptions import MCPConfigurationError, create_config_error

# 设置日志
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """验证结果数据类"""
    is_valid: bool
    field_name: str
    message: str
    suggestion: Optional[str]
    severity: str  # "error", "warning", "info"


@dataclass
class ConfigField:
    """配置字段定义"""
    name: str
    field_path: List[str]
    field_type: type
    required: bool
    default_value: Any
    validation_rules: List[str]
    description: str


class MCPConfigValidator:
    """MCP配置验证器"""

    def __init__(self):
        """初始化配置验证器"""
        # 定义配置字段结构
        self.config_schema = {
            "mcp_service": {
                "fields": [
                    ConfigField(
                        name="vector_database",
                        field_path=["mcp_service", "vector_database"],
                        field_type=dict,
                        required=True,
                        default_value={"type": "chromadb"},
                        validation_rules=["has_subfield_type", "type", "subfield_exists"],
                        description="向量数据库配置"
                    ),
                    ConfigField(
                        name="embedding_model",
                        field_path=["mcp_service", "embedding_model"],
                        field_type=dict,
                        required=True,
                        default_value={"model_name": "sentence-transformers/all-MiniLM-L6-v2", "device": "auto"},
                        validation_rules=["has_subfield_type", "type", "required_subfields"],
                        description="嵌入模型配置"
                    ),
                    ConfigField(
                        name="semantic_processing",
                        field_path=["mcp_service", "semantic_processing"],
                        field_type=dict,
                        required=False,
                        default_value={"chunk_size": 512, "extract_concepts": True, "generate_tags": True},
                        validation_rules=["has_subfield_type", "type", "numeric_validation"],
                        description="语义处理配置"
                    ),
                    ConfigField(
                        name="memory_management",
                        field_path=["mcp_service", "memory_management"],
                        field_type=dict,
                        required=False,
                        default_value={"max_memories_per_collection": 10000, "auto_compress_threshold": 5000},
                        validation_rules=["has_subfield_type", "type", "numeric_validation"],
                        description="记忆管理配置"
                    ),
                    ConfigField(
                        name="creative_association",
                        field_path=["mcp_service", "creative_association"],
                        field_type=dict,
                        required=False,
                        default_value={"enable": True, "creativity_levels": {}},
                        validation_rules=["has_subfield_type", "type", "creative_levels_validation"],
                        description="创意联想配置"
                    ),
                    ConfigField(
                        name="hardware_detection",
                        field_path=["mcp_service", "hardware_detection"],
                        field_type=dict,
                        required=False,
                        default_value={"auto_detect_gpu": True, "fallback_to_cpu": True},
                        validation_rules=["has_subfield_type", "type", "boolean_validation"],
                        description="硬件检测配置"
                    )
                ]
            }
        }

    def validate_config_file(self, config_path: str) -> List[ValidationResult]:
        """验证配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            List[ValidationResult]: 验证结果列表
        """
        results = []

        # 检查文件存在性
        if not os.path.exists(config_path):
            results.append(ValidationResult(
                is_valid=False,
                field_name="file_existence",
                message=f"配置文件不存在: {config_path}",
                suggestion="请检查文件路径或创建配置文件",
                severity="error"
            ))
            return results

        # 检查文件可读性
        if not os.access(config_path, os.R_OK):
            results.append(ValidationResult(
                is_valid=False,
                field_name="file_readable",
                message=f"配置文件不可读: {config_path}",
                suggestion="请检查文件权限",
                severity="error"
            ))

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                try:
                    config_data = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    results.append(ValidationResult(
                        is_valid=False,
                        field_name="yaml_parsing",
                        message=f"YAML解析错误: {str(e)}",
                        suggestion="请检查YAML语法，确保正确的缩进和引号",
                        severity="error"
                    ))
                    return results

                # 验证配置结构
                structure_results = self._validate_config_structure(config_data)
                results.extend(structure_results)

                # 验证字段值
                value_results = self._validate_config_values(config_data)
                results.extend(value_results)

        except Exception as e:
            results.append(ValidationResult(
                is_valid=False,
                field_name="file_processing",
                message=f"处理配置文件时发生错误: {str(e)}",
                suggestion="请检查文件格式和内容",
                severity="error"
            ))

        return results

    def _validate_config_structure(self, config: Dict) -> List[ValidationResult]:
        """验证配置结构"""
        results = []

        if not isinstance(config, dict):
            results.append(ValidationResult(
                is_valid=False,
                field_name="root_structure",
                message="配置文件根节点必须是字典类型",
                suggestion="确保配置文件格式为: 'mcp_service: {...}'",
                severity="error"
            ))
            return results

        if "mcp_service" not in config:
            results.append(ValidationResult(
                is_valid=False,
                field_name="missing_root_section",
                message="缺少必要根节点: 'mcp_service'",
                suggestion="在配置文件中添加 'mcp_service' 部分",
                severity="error"
            ))
            return results

        mcp_service = config["mcp_service"]
        if not isinstance(mcp_service, dict):
            results.append(ValidationResult(
                is_valid=False,
                field_name="mcp_service_type",
                message="'mcp_service' 节点必须是字典类型",
                suggestion="确保 'mcp_service' 部分格式正确",
                severity="error"
            ))

        # 验证已知字段
        known_fields = set()
        for field in self.config_schema["mcp_service"]["fields"]:
            known_fields.add(field.name)

        config_fields = set(mcp_service.keys())
        unknown_fields = config_fields - known_fields

        if unknown_fields:
            for field in unknown_fields:
                results.append(ValidationResult(
                    is_valid=True,
                    field_name="unknown_field",
                    message=f"发现未知字段: '{field}'",
                    suggestion=f"如果这是自定义字段，请确认其正确性；否则检查拼写",
                    severity="warning"
                ))

        return results

    def _validate_config_values(self, config: Dict) -> List[ValidationResult]:
        """验证配置字段值"""
        results = []

        # 递归验证配置结构
        def validate_section(section_config: Dict, schema_fields: List[ConfigField], section_path: List[str]) -> None:
            for field in schema_fields:
                field_value = self._get_nested_value(section_config, field.field_path)
                field_results = self._validate_field_value(field, field_value, section_path)
                results.extend(field_results)

        validate_section(config.get("mcp_service", {}),
                        self.config_schema["mcp_service"]["fields"],
                        ["mcp_service"])

        return results

    def _get_nested_value(self, config: Dict, path: List[str]) -> Any:
        """获取嵌套配置值"""
        value = config
        for key in path:
            if isinstance(value, dict) and key in value:
                value = value[key]
            elif isinstance(value, (list, tuple)) and isinstance(key, int) and 0 <= key < len(value):
                value = value[key]
            else:
                return None
        return value

    def _validate_field_value(self, field: ConfigField, value: Any, field_path: List[str]) -> List[ValidationResult]:
        """验证单个字段值"""
        results = []

        # 检查必填字段
        if field.required and value is None:
            results.append(ValidationResult(
                is_valid=False,
                field_name=f"{'->'.join(field.field_path)}",
                message=f"必填字段 '{field.name}' 不能为空",
                suggestion=f"请在配置中设置 '{field.name}' 的值",
                severity="error"
            ))

        # 检查字段类型
        if value is not None and not isinstance(value, field.field_type):
            results.append(ValidationResult(
                is_valid=False,
                field_name=f"{'->'.join(field.field_path)}",
                message=f"字段 '{field.name}' 类型错误，期望 {field.field_type.__name__}，实际 {type(value).__name__}",
                suggestion=f"请确保 '{field.name}' 的值类型为 {field.field_type.__name__}",
                severity="error"
            ))

        # 执行自定义验证规则
        if value is not None:
            for rule in field.validation_rules:
                rule_results = self._execute_validation_rule(rule, field, value, field_path)
                results.extend(rule_results)

        return results

    def _execute_validation_rule(self, rule: str, field: ConfigField, value: Any, field_path: List[str]) -> List[ValidationResult]:
        """执行验证规则"""
        results = []

        if rule == "has_subfield_type":
            if isinstance(value, dict):
                required_subfields = ["type", "model_name", "device"]
                missing_subfields = [sf for sf in required_subfields if sf not in value]
                for subfield in missing_subfields:
                    results.append(ValidationResult(
                        is_valid=False,
                        field_name=f"{'->'.join(field.field_path)}->{subfield}",
                        message=f"缺少必需子字段: '{subfield}'",
                        suggestion=f"请在 '{field.name}' 中添加 '{subfield}' 字段",
                        severity="error"
                    ))

        elif rule == "type":
            if field.name == "device":
                valid_devices = ["auto", "cpu", "cuda"]
                if isinstance(value, str) and value not in valid_devices:
                    results.append(ValidationResult(
                        is_valid=False,
                        field_name=f"{'->'.join(field.field_path)}",
                        message=f"设备值无效: '{value}'，有效值: {valid_devices}",
                        suggestion=f"请使用有效设备: {valid_devices}",
                        severity="error"
                    ))

        elif field.name == "model_name":
            if isinstance(value, str):
                if not value or "/" not in value:
                    results.append(ValidationResult(
                        is_valid=False,
                        field_name=f"{'->'.join(field.path)}",
                        message=f"模型名称格式错误，应为 'organization/model_name' 格式",
                        suggestion=f"请使用标准的transformer模型名称格式",
                        severity="error"
                    ))

        elif rule == "required_subfields":
            if field.name == "embedding_model":
                required = ["model_name", "device"]
                if isinstance(value, dict):
                    for subfield in required:
                        if subfield not in value:
                            results.append(ValidationResult(
                                is_valid=False,
                                field_name=f"{'->'.join(field.field_path)}->{subfield}",
                                message=f"嵌入模型缺少必需字段: '{subfield}'",
                                suggestion=f"请在 '{field.name}' 中添加 '{subfield}' 字段",
                                severity="error"
                            ))

        elif rule == "numeric_validation":
            numeric_fields = {
                "chunk_size": {"min": 1, "max": 4096},
                "max_memories_per_collection": {"min": 100, "max": 100000},
                "auto_compress_threshold": {"min": 100, "max": 100000},
                "compression_ratio": {"min": 0.1, "max": 1.0}
            }

            if field.name in numeric_fields and value is not None:
                field_range = numeric_fields[field.name]
                if isinstance(value, (int, float)):
                    if value < field_range["min"] or value > field_range["max"]:
                        results.append(ValidationResult(
                            is_valid=False,
                            field_name=f"{'->'.join(field.field_path)}",
                            message=f"数值超出有效范围: {field_range['min']}-{field_range['max']}，当前值: {value}",
                            suggestion=f"请设置 {field.name} 在有效范围内",
                            severity="error"
                        ))

        elif rule == "boolean_validation":
            if field.name == "hardware_detection":
                boolean_fields = ["auto_detect_gpu", "fallback_to_cpu"]
                if isinstance(value, dict):
                    for subfield in boolean_fields:
                        if subfield in value and not isinstance(value[subfield], bool):
                            results.append(ValidationResult(
                                is_valid=False,
                                field_name=f"{'->'.join(field.field_path)}->{subfield}",
                                message=f"布尔字段 '{subfield}' 必须为 true/false",
                                suggestion=f"请设置 {subfield} 为布尔值",
                                severity="error"
                            ))

        elif rule == "creative_levels_validation":
            if field.name == "creative_association" and isinstance(value, dict):
                if "creativity_levels" in value:
                    levels = value["creativity_levels"]
                    valid_keys = ["conservative", "moderate", "creative"]
                    for level in levels:
                        if level not in valid_keys:
                            results.append(ValidationResult(
                                is_valid=False,
                                field_name=f"{'->'.join(field.field_path)}->creativity_levels->{level}",
                                message=f"无效的创意级别: '{level}'",
                                suggestion=f"有效级别: {valid_keys}",
                                severity="error"
                            ))

        return results

    def generate_config_template(self, output_path: str) -> None:
        """生成配置文件模板"""
        template = {
            "mcp_service": {
                "vector_database": {
                    "type": "chromadb",  # chromadb, faiss, pinecone
                    "persist_directory": "./data/memory_db",
                    "collection_name": "canvas_memories"
                },
                "embedding_model": {
                    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                    "device": "auto",  # auto, cpu, cuda
                    "batch_size": 32,
                    "max_sequence_length": 512
                },
                "semantic_processing": {
                    "chunk_size": 512,
                    "chunk_overlap": 50,
                    "min_chunk_size": 100,
                    "extract_concepts": True,
                    "generate_tags": True
                },
                "memory_management": {
                    "max_memories_per_collection": 10000,
                    "auto_compress_threshold": 5000,
                    "compression_ratio": 0.3,
                    "retention_days": 365
                },
                "creative_association": {
                    "enable": True,
                    "creativity_levels": {
                        "conservative": {
                            "temperature": 0.7,
                            "max_associations": 5
                        },
                        "moderate": {
                            "temperature": 0.9,
                            "max_associations": 8
                        },
                        "creative": {
                            "temperature": 1.2,
                            "max_associations": 12
                        }
                    },
                    "cross_domain_threshold": 0.6,
                    "analogy_generation": True,
                    "practical_applications": True
                },
                "hardware_detection": {
                    "auto_detect_gpu": True,
                    "fallback_to_cpu": True,
                    "memory_threshold_mb": 4096,
                    "cuda_memory_fraction": 0.8
                }
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(template, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"配置模板已生成: {output_path}")

    def validate_and_report(self, config_path: str, output_format: str = "console") -> Tuple[bool, List[ValidationResult]]:
        """验证并报告结果

        Args:
            config_path: 配置文件路径
            output_format: 输出格式 ("console", "json", "markdown")

        Returns:
            Tuple[bool, List[ValidationResult]]: (是否有效, 验证结果列表)
        """
        results = self.validate_config_file(config_path)

        # 按严重程度排序
        error_results = [r for r in results if r.severity == "error"]
        warning_results = [r for r in results if r.severity == "warning"]
        info_results = [r for r in results if r.severity == "info"]

        is_valid = len(error_results) == 0

        # 输出结果
        if output_format == "console":
            self._print_console_report(error_results, warning_results, info_results)
        elif output_format == "json":
            self._print_json_report(error_results, warning_results, info_results)
        elif output_format == "markdown":
            self._print_markdown_report(error_results, warning_results, info_results)

        return is_valid, results

    def _print_console_report(self, errors: List[ValidationResult], warnings: List[ValidationResult], info: List[ValidationResult]):
        """打印控制台报告"""
        if errors:
            print("❌ 配置验证失败:")
            for error in errors:
                print(f"  • {error.message}")
                if error.suggestion:
                    print(f"    💡 建议: {error.suggestion}")

        if warnings:
            print("⚠️ 配置警告:")
            for warning in warnings:
                print(f"  • {warning.message}")
                if warning.suggestion:
                    print(f"    💡 建议: {warning.suggestion}")

        if info:
            print("ℹ️ 配置信息:")
            for info_item in info:
                print(f"  • {info_item.message}")

        if not errors and not warnings:
            print("✅ 配置验证通过")

    def _print_json_report(self, errors: List[ValidationResult], warnings: List[ValidationResult], info: List[ValidationResult]):
        """打印JSON格式报告"""
        report_data = {
            "valid": len(errors) == 0,
            "summary": {
                "total_issues": len(errors) + len(warnings) + len(info),
                "error_count": len(errors),
                "warning_count": len(warnings),
                "info_count": len(info)
            },
            "issues": {
                "errors": [{"field": error.field_name, "message": error.message, "suggestion": error.suggestion} for error in errors],
                "warnings": [{"field": warning.field_name, "message": warning.message, "suggestion": warning.suggestion} for warning in warnings],
                "info": [{"field": info.field_name, "message": info.message} for info in info]
            }
        }

        print(json.dumps(report_data, ensure_ascii=False, indent=2))

    def _print_markdown_report(self, errors: List[ValidationResult], warnings: List[ValidationResult], info: List[ValidationResult]):
        """打印Markdown格式报告"""
        print("# 配置验证报告")
        print()

        if errors:
            print("## ❌ 错误")
            for error in errors:
                print(f"- **{error.field_name}**: {error.message}")
                if error.suggestion:
                    print(f"  💡 建议: {error.suggestion}")

        if warnings:
            print("## ⚠️ 警告")
            for warning in warnings:
                print(f"- **{warning.field_name}**: {warning.message}")
                if warning.suggestion:
                    print(f"  💡 建议: {warning.suggestion}")

        if info:
            print("## ℹ️ 信息")
            for info_item in info:
                print(f"- **{info_item.field_name}**: {info_item.message}")

        print()
        print(f"**总结**: {'✅ 通过' if len(errors) == 0 else '❌ 失败'} ({len(errors)} 个错误, {len(warnings)} 个警告)")


def main():
    """主函数示例"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="MCP配置验证器")
    parser.add_argument("config", help="配置文件路径")
    parser.add_argument("--format", choices=["console", "json", "markdown"], default="console", help="输出格式")
    parser.add_argument("--generate-template", help="生成配置模板", metavar="OUTPUT_PATH")
    parser.add_argument("--validate", help="验证配置文件", metavar="CONFIG_PATH")

    args = parser.parse_args()

    if args.generate_template:
        validator = MCPConfigValidator()
        validator.generate_config_template(args.generate_template)
        print(f"配置模板已生成: {args.generate_template}")
        return

    if args.validate:
        validator = MCPConfigValidator()
        is_valid, results = validator.validate_and_report(args.validate, args.format)

        sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()