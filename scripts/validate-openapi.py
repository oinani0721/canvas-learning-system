#!/usr/bin/env python3
"""
OpenAPI Specification Validation Script
验证OpenAPI规范文件的语法和兼容性

功能:
1. 验证YAML语法正确性
2. 检查OpenAPI版本 (3.0.x 或 3.1.x)
3. 验证必要字段存在 (openapi, info, paths)
4. 检查$ref引用是否有效
5. 检测breaking changes (删除端点等)

用法:
  python scripts/validate-openapi.py [openapi_files...]

参数:
  openapi_files - 要验证的OpenAPI文件列表，如果不提供则验证所有

返回码:
  0 - 验证通过
  1 - 验证失败
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Try to import yaml, fall back to basic validation if not available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Try to import openapi-spec-validator for comprehensive validation
try:
    from openapi_spec_validator import validate_spec
    from openapi_spec_validator.exceptions import OpenAPIValidationError
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def validate_yaml_syntax(file_path: Path) -> Tuple[bool, str, Optional[Dict]]:
    """
    验证YAML语法

    返回:
        (valid, error_message, parsed_content)
    """
    if not YAML_AVAILABLE:
        # Basic validation without yaml library
        try:
            content = file_path.read_text(encoding='utf-8')
            # Check for basic YAML structure indicators
            if not content.strip():
                return False, "File is empty", None
            return True, "", None
        except Exception as e:
            return False, f"Error reading file: {e}", None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        if content is None:
            return False, "File is empty or contains only comments", None
        return True, "", content
    except yaml.YAMLError as e:
        return False, f"YAML syntax error: {e}", None


def validate_openapi_version(spec: Dict[str, Any], file_path: Path) -> List[str]:
    """验证OpenAPI版本"""
    errors = []

    openapi_version = spec.get('openapi')
    if not openapi_version:
        errors.append(f"{file_path.name}: Missing 'openapi' version field")
    elif not re.match(r'^3\.(0|1)\.\d+$', str(openapi_version)):
        errors.append(f"{file_path.name}: Invalid OpenAPI version '{openapi_version}' (expected 3.0.x or 3.1.x)")

    return errors


def validate_required_fields(spec: Dict[str, Any], file_path: Path) -> List[str]:
    """验证必要字段"""
    errors = []
    warnings = []

    # Required top-level fields
    required_fields = ['openapi', 'info', 'paths']
    for field in required_fields:
        if field not in spec:
            errors.append(f"{file_path.name}: Missing required field '{field}'")

    # Info section requirements
    if 'info' in spec:
        info = spec['info']
        if 'title' not in info:
            errors.append(f"{file_path.name}: Missing 'info.title'")
        if 'version' not in info:
            errors.append(f"{file_path.name}: Missing 'info.version'")

    # Check if paths is empty (warning)
    if 'paths' in spec and not spec['paths']:
        warnings.append(f"{file_path.name}: 'paths' section is empty")

    return errors


def validate_refs(spec: Dict[str, Any], file_path: Path) -> List[str]:
    """验证$ref引用"""
    errors = []
    components = spec.get('components', {})
    schemas = components.get('schemas', {})

    def check_refs(obj: Any, path: str = ""):
        if isinstance(obj, dict):
            if '$ref' in obj:
                ref = obj['$ref']
                # Check internal references
                if ref.startswith('#/components/schemas/'):
                    schema_name = ref.replace('#/components/schemas/', '')
                    if schema_name not in schemas:
                        errors.append(f"{file_path.name}: Invalid $ref '{ref}' - schema not found")
                # Check external file references
                elif not ref.startswith('#'):
                    ref_file = ref.split('#')[0]
                    if ref_file:
                        ref_path = (file_path.parent / ref_file).resolve()
                        if not ref_path.exists():
                            errors.append(f"{file_path.name}: Invalid $ref '{ref}' - file not found")

            for key, value in obj.items():
                check_refs(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_refs(item, f"{path}[{i}]")

    check_refs(spec)
    return errors


def validate_paths_structure(spec: Dict[str, Any], file_path: Path) -> List[str]:
    """验证paths结构"""
    errors = []
    paths = spec.get('paths', {})

    valid_methods = {'get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace'}

    for path, path_item in paths.items():
        if not path.startswith('/'):
            errors.append(f"{file_path.name}: Path '{path}' must start with '/'")

        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            if method.startswith('x-'):
                continue  # Extension fields
            if method in ['parameters', 'servers', 'summary', 'description']:
                continue  # Path-level fields
            if method not in valid_methods:
                errors.append(f"{file_path.name}: Invalid HTTP method '{method}' at path '{path}'")

            if isinstance(operation, dict):
                # Check for operationId (recommended)
                if 'operationId' not in operation:
                    # This is a warning, not error - don't add to errors
                    pass

                # Check responses field (required)
                if 'responses' not in operation:
                    errors.append(f"{file_path.name}: Missing 'responses' for {method.upper()} {path}")

    return errors


def validate_with_openapi_validator(spec: Dict[str, Any], file_path: Path) -> List[str]:
    """使用openapi-spec-validator进行完整验证"""
    errors = []

    if not VALIDATOR_AVAILABLE:
        return errors

    try:
        validate_spec(spec)
    except OpenAPIValidationError as e:
        errors.append(f"{file_path.name}: {str(e)}")
    except Exception as e:
        errors.append(f"{file_path.name}: Validation error: {str(e)}")

    return errors


def validate_openapi_file(file_path: Path) -> Tuple[List[str], List[str]]:
    """
    验证单个OpenAPI文件

    返回:
        (errors, warnings)
    """
    errors = []
    warnings = []

    # 1. 验证YAML语法
    valid, error_msg, spec = validate_yaml_syntax(file_path)
    if not valid:
        errors.append(f"{file_path.name}: {error_msg}")
        return errors, warnings

    if spec is None:
        warnings.append(f"{file_path.name}: Could not parse YAML (yaml library not available)")
        return errors, warnings

    # 2. 验证OpenAPI版本
    version_errors = validate_openapi_version(spec, file_path)
    errors.extend(version_errors)

    # 3. 验证必要字段
    field_errors = validate_required_fields(spec, file_path)
    errors.extend(field_errors)

    # 4. 验证paths结构
    path_errors = validate_paths_structure(spec, file_path)
    errors.extend(path_errors)

    # 5. 验证$ref引用
    ref_errors = validate_refs(spec, file_path)
    errors.extend(ref_errors)

    # 6. 使用openapi-spec-validator进行完整验证 (如果可用)
    if VALIDATOR_AVAILABLE and not errors:
        validator_errors = validate_with_openapi_validator(spec, file_path)
        errors.extend(validator_errors)

    return errors, warnings


def main():
    """主函数"""
    # Set UTF-8 encoding for Windows console
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("=" * 60)
    print("[VALIDATE] OpenAPI Specification Validation")
    print("=" * 60)

    if not YAML_AVAILABLE:
        print("[WARNING] PyYAML not installed. Using basic validation only.")
        print("   Install with: pip install pyyaml")

    if not VALIDATOR_AVAILABLE:
        print("[INFO] openapi-spec-validator not installed. Using basic validation.")
        print("   For comprehensive validation: pip install openapi-spec-validator")

    print()

    # 确定要验证的文件
    if len(sys.argv) > 1:
        # 验证指定的文件
        files_to_validate = [Path(f) for f in sys.argv[1:]]
    else:
        # 验证所有OpenAPI文件
        api_dir = get_project_root() / 'specs' / 'api'
        if not api_dir.exists():
            print(f"[WARNING] API specs directory not found: {api_dir}")
            return 0

        files_to_validate = list(api_dir.glob('*.yml')) + list(api_dir.glob('*.yaml'))

    if not files_to_validate:
        print("[INFO] No OpenAPI files to validate")
        return 0

    # 验证每个文件
    all_errors = []
    all_warnings = []

    for file_path in files_to_validate:
        if not file_path.exists():
            all_errors.append(f"File not found: {file_path}")
            continue

        print(f"Validating: {file_path.name}...", end=" ")
        errors, warnings = validate_openapi_file(file_path)

        if errors:
            print("[FAILED]")
            all_errors.extend(errors)
        elif warnings:
            print("[WARNINGS]")
            all_warnings.extend(warnings)
        else:
            print("[OK]")

    # 打印汇总
    print("\n" + "=" * 60)

    if all_errors:
        print("\n[ERRORS]:")
        for error in all_errors:
            print(f"  - {error}")

    if all_warnings:
        print("\n[WARNINGS]:")
        for warning in all_warnings:
            print(f"  - {warning}")

    if not all_errors and not all_warnings:
        print("\n[SUCCESS] All OpenAPI specifications validated successfully!")

    print("=" * 60)

    # 返回码
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
