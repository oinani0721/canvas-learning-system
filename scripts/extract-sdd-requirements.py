"""
SDD Requirements Extraction Script
从PRD和Architecture文档中提取所有API端点和数据模型，生成SDD需求索引。

使用方法:
    python scripts/extract-sdd-requirements.py

输出:
    docs/specs/sdd-requirements-index.md
"""

import re
import os
import sys
import io
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# Force UTF-8 encoding for Windows console output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


class SDDRequirementsExtractor:
    """SDD需求提取器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.prd_dir = self.project_root / "docs" / "prd"
        self.arch_dir = self.project_root / "docs" / "architecture"
        self.specs_dir = self.project_root / "specs"

        # API端点清单
        self.api_endpoints: List[Dict] = []
        # 数据模型清单
        self.data_models: List[Dict] = []

    def extract_api_endpoints_from_epic(self, epic_file: Path) -> List[Dict]:
        """从Epic文件中提取API端点定义"""
        endpoints = []

        with open(epic_file, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

            # 查找API Endpoints章节
            in_api_section = False
            current_category = None
            line_number = 0

            for line_num, line in enumerate(lines, 1):
                # 检测API章节开始
                if re.search(r"## API Endpoints", line, re.IGNORECASE):
                    in_api_section = True
                    continue

                # 检测章节结束 (只检测二级标题 ##，不包括 ### 三级标题)
                if in_api_section and line.startswith("## ") and "API" not in line:
                    break

                if in_api_section:
                    # 检测分类（如 ### Canvas操作）
                    category_match = re.search(r"###\s+(.+)\s+\((\d+)\s+endpoints?\)", line)
                    if category_match:
                        current_category = category_match.group(1).strip()
                        continue

                    # 提取端点定义
                    # 格式: - `METHOD /path` - 描述
                    endpoint_match = re.search(r"-\s+`(GET|POST|PUT|DELETE|PATCH)\s+([^`]+)`\s*-\s*(.+)", line)
                    if endpoint_match and current_category:
                        method = endpoint_match.group(1)
                        path = endpoint_match.group(2)
                        description = endpoint_match.group(3).strip()

                        endpoints.append(
                            {
                                "method": method,
                                "path": path,
                                "description": description,
                                "category": current_category,
                                "prd_file": epic_file.name,
                                "prd_line": line_num,
                                "openapi_status": "⏳待检查",
                                "coverage": 0,
                            }
                        )

        return endpoints

    def extract_data_models_from_epic(self, epic_file: Path) -> List[Dict]:
        """从Epic文件中提取数据模型定义"""
        models = []

        with open(epic_file, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

            # 查找数据模型章节
            in_model_section = False
            current_category = None

            for line_num, line in enumerate(lines, 1):
                # 检测数据模型章节开始
                if re.search(r"## 数据模型", line, re.IGNORECASE) or re.search(r"## Data Models", line, re.IGNORECASE):
                    in_model_section = True
                    continue

                # 检测章节结束 (只检测二级标题 ##，不包括 ### 三级标题)
                if in_model_section and line.startswith("## ") and "模型" not in line and "Model" not in line:
                    break

                if in_model_section:
                    # 检测分类
                    category_match = re.search(r"\d+\.\s+\*\*(.+模型)\*\*\s+\((\d+)个\)", line)
                    if category_match:
                        current_category = category_match.group(1).strip()
                        # 不要continue，继续检查同一行是否有模型名称

                    # 提取模型名称
                    # 格式: `ModelName`, `ModelBase`, `ModelCreate`
                    # 注意：模型名称和分类可能在同一行
                    if current_category and "`" in line:
                        model_names = re.findall(r"`([A-Z][a-zA-Z]+)`", line)
                        for model_name in model_names:
                            models.append(
                                {
                                    "name": model_name,
                                    "category": current_category,
                                    "prd_file": epic_file.name,
                                    "prd_line": line_num,
                                    "schema_status": "⏳待检查",
                                    "coverage": 0,
                                }
                            )

        return models

    def check_openapi_coverage(self):
        """检查OpenAPI规范覆盖率"""
        openapi_file = self.specs_dir / "api" / "fastapi-backend-api.openapi.yml"

        if not openapi_file.exists():
            print(f"⚠️ OpenAPI文件不存在: {openapi_file}")
            return

        with open(openapi_file, "r", encoding="utf-8") as f:
            openapi_content = f.read()

        for endpoint in self.api_endpoints:
            path = endpoint["path"]
            method = endpoint["method"].lower()

            # 检查路径是否存在
            if path in openapi_content:
                # 检查方法是否定义
                # 简单检查：在路径定义后查找方法
                path_index = openapi_content.find(path)
                if path_index != -1:
                    section = openapi_content[path_index : path_index + 1000]
                    if f"  {method}:" in section or f"    {method}:" in section:
                        endpoint["openapi_status"] = "✅已定义"
                        endpoint["coverage"] = 100
                    else:
                        endpoint["openapi_status"] = "⚠️路径存在，方法缺失"
                        endpoint["coverage"] = 50
            else:
                endpoint["openapi_status"] = "❌未定义"
                endpoint["coverage"] = 0

    def check_schema_coverage(self):
        """检查JSON Schema覆盖率"""
        schema_dir = self.specs_dir / "data"

        if not schema_dir.exists():
            print(f"⚠️ Schema目录不存在: {schema_dir}")
            return

        # 读取所有schema文件
        schema_files = list(schema_dir.glob("*.schema.json"))

        for model in self.data_models:
            model_name = model["name"]

            # 检查是否有对应的schema文件
            # 转换驼峰到kebab-case
            # 例如: NodeCreate → node-create.schema.json
            kebab_name = re.sub(r"(?<!^)(?=[A-Z])", "-", model_name).lower()

            matched = False
            for schema_file in schema_files:
                if kebab_name in schema_file.stem:
                    model["schema_status"] = f"✅{schema_file.name}"
                    model["coverage"] = 100
                    matched = True
                    break

            if not matched:
                model["schema_status"] = "❌未定义"
                model["coverage"] = 0

    def generate_index_markdown(self) -> str:
        """生成Markdown格式的SDD需求索引"""

        # 统计覆盖率
        total_endpoints = len(self.api_endpoints)
        covered_endpoints = sum(1 for e in self.api_endpoints if e["coverage"] == 100)
        endpoint_coverage_pct = (covered_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0

        total_models = len(self.data_models)
        covered_models = sum(1 for m in self.data_models if m["coverage"] == 100)
        model_coverage_pct = (covered_models / total_models * 100) if total_models > 0 else 0

        overall_coverage = (
            (covered_endpoints + covered_models) / (total_endpoints + total_models) * 100
            if (total_endpoints + total_models) > 0
            else 0
        )

        md = f"""# SDD需求索引 (SDD Requirements Index)

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**生成脚本**: scripts/extract-sdd-requirements.py

---

## 📊 覆盖率总览

| 类别 | 总数 | 已覆盖 | 覆盖率 | 状态 |
|------|------|--------|--------|------|
| API端点 | {total_endpoints} | {covered_endpoints} | {endpoint_coverage_pct:.1f}% | {"✅" if endpoint_coverage_pct >= 80 else "⚠️" if endpoint_coverage_pct >= 50 else "❌"} |
| 数据模型 | {total_models} | {covered_models} | {model_coverage_pct:.1f}% | {"✅" if model_coverage_pct >= 80 else "⚠️" if model_coverage_pct >= 50 else "❌"} |
| **总体** | {total_endpoints + total_models} | {covered_endpoints + covered_models} | {overall_coverage:.1f}% | {"✅" if overall_coverage >= 80 else "⚠️" if overall_coverage >= 50 else "❌"} |

**质量门禁**: 覆盖率需达到 ≥80% 才能通过Planning Finalize

---

## 🔗 API端点清单 (来自PRD Epic 15)

| 端点 | 方法 | 描述 | PRD位置 | OpenAPI状态 | 覆盖率 |
|------|------|------|---------|-------------|--------|
"""

        # 按分类组织端点
        categories = {}
        for endpoint in self.api_endpoints:
            cat = endpoint["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(endpoint)

        for category, eps in categories.items():
            md += f"\n### {category}\n\n"
            for ep in eps:
                md += f"| {ep['path']} | `{ep['method']}` | {ep['description']} | {ep['prd_file']}:L{ep['prd_line']} | {ep['openapi_status']} | {ep['coverage']}% |\n"

        md += f"""
---

## 📦 数据模型清单 (来自PRD Epic 15)

| 模型名称 | 分类 | PRD位置 | Schema状态 | 覆盖率 |
|----------|------|---------|------------|--------|
"""

        # 按分类组织模型
        model_categories = {}
        for model in self.data_models:
            cat = model["category"]
            if cat not in model_categories:
                model_categories[cat] = []
            model_categories[cat].append(model)

        for category, models in model_categories.items():
            md += f"\n### {category}\n\n"
            for model in models:
                md += f"| `{model['name']}` | {model['category']} | {model['prd_file']}:L{model['prd_line']} | {model['schema_status']} | {model['coverage']}% |\n"

        md += """
---

## 🔍 追溯矩阵

### PRD需求 → OpenAPI端点 → JSON Schema → Story

| PRD需求 | OpenAPI路径 | 相关Schema | Story引用 |
|---------|-------------|-----------|----------|
"""

        # 简单追溯矩阵（需要后续完善）
        for endpoint in self.api_endpoints[:5]:  # 示例前5个
            path = endpoint["path"]
            method = endpoint["method"]
            # 猜测相关Schema（实际需要更智能的映射）
            related_schemas = []
            for model in self.data_models:
                if "Request" in model["name"] or "Response" in model["name"]:
                    if any(keyword in path for keyword in ["node", "edge", "canvas", "agent", "review"]):
                        related_schemas.append(f"`{model['name']}`")

            schemas_str = ", ".join(related_schemas[:2]) if related_schemas else "_TBD_"
            md += f"| {endpoint['description']} | `{method} {path}` | {schemas_str} | _待关联_ |\n"

        md += """
_(追溯矩阵持续更新中...)_

---

## 📋 待创建SDD清单

### 缺失的OpenAPI端点
"""

        missing_endpoints = [e for e in self.api_endpoints if e["coverage"] < 100]
        if missing_endpoints:
            for ep in missing_endpoints:
                md += f"- [ ] `{ep['method']} {ep['path']}` - {ep['description']} ({ep['openapi_status']})\n"
        else:
            md += "_✅ 所有API端点已定义_\n"

        md += """
### 缺失的JSON Schema
"""

        missing_models = [m for m in self.data_models if m["coverage"] < 100]
        if missing_models:
            for model in missing_models:
                kebab_name = re.sub(r"(?<!^)(?=[A-Z])", "-", model["name"]).lower()
                md += f"- [ ] `{model['name']}` → `specs/data/{kebab_name}.schema.json`\n"
        else:
            md += "_✅ 所有数据模型已定义Schema_\n"

        md += """
---

## 🛠️ 使用指南

### Architect创建OpenAPI端点

```bash
# 1. 读取本Index，确认待创建端点
# 2. 执行创建命令（含Context7验证）
@architect *create-openapi "/api/v1/canvas/{canvas_name}"

# 3. Index会自动更新覆盖率
```

### Architect创建JSON Schema

```bash
# 1. 读取本Index，确认待创建Schema
# 2. 执行创建命令（含Context7验证）
@architect *create-schemas "NodeCreate"

# 3. Index会自动更新覆盖率
```

### SM创建Story时检查

```bash
# SM Agent自动执行：
# 1. 读取SDD Index
# 2. 检查Story涉及的端点/模型是否已有SDD
# 3. 缺失则HALT，通知Architect补充
```

---

## 📌 注意事项

1. **本文件自动生成** - 请勿手动编辑统计数据
2. **更新频率** - 每次运行`scripts/extract-sdd-requirements.py`自动更新
3. **质量门禁** - Planning Finalize时检查覆盖率 ≥80%
4. **追溯完整性** - 确保每个SDD都能追溯到PRD需求

---

**文档版本**: 1.0
**最后更新**: {datetime.now().strftime('%Y-%m-%d')}
"""

        return md

    def save_index(self, output_file: Path):
        """保存索引到文件"""
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)

        md_content = self.generate_index_markdown()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"✅ SDD需求索引已生成: {output_file}")
        print(f"📊 API端点: {len(self.api_endpoints)} 个")
        print(f"📦 数据模型: {len(self.data_models)} 个")

    def run(self):
        """执行提取流程"""
        print("🔍 开始提取SDD需求...")

        # 1. 提取API端点
        print("\n📡 提取API端点...")
        epic15_file = self.prd_dir / "epics" / "EPIC-15-FastAPI.md"
        if epic15_file.exists():
            self.api_endpoints = self.extract_api_endpoints_from_epic(epic15_file)
            print(f"   ✅ 从{epic15_file.name}提取 {len(self.api_endpoints)} 个API端点")
        else:
            print(f"   ⚠️ {epic15_file} 不存在")

        # 2. 提取数据模型
        print("\n📦 提取数据模型...")
        if epic15_file.exists():
            self.data_models = self.extract_data_models_from_epic(epic15_file)
            print(f"   ✅ 从{epic15_file.name}提取 {len(self.data_models)} 个数据模型")

        # 3. 检查OpenAPI覆盖率
        print("\n🔍 检查OpenAPI覆盖率...")
        if self.api_endpoints:
            self.check_openapi_coverage()
            covered = sum(1 for e in self.api_endpoints if e["coverage"] == 100)
            print(
                f"   ✅ OpenAPI覆盖: {covered}/{len(self.api_endpoints)} ({covered / len(self.api_endpoints) * 100:.1f}%)"
            )
        else:
            print("   ⚠️ 没有找到API端点")

        # 4. 检查Schema覆盖率
        print("\n🔍 检查Schema覆盖率...")
        if self.data_models:
            self.check_schema_coverage()
            covered_models = sum(1 for m in self.data_models if m["coverage"] == 100)
            print(
                f"   ✅ Schema覆盖: {covered_models}/{len(self.data_models)} ({covered_models / len(self.data_models) * 100:.1f}%)"
            )
        else:
            print("   ⚠️ 没有找到数据模型")

        # 5. 生成索引
        print("\n📝 生成SDD需求索引...")
        output_file = self.project_root / "docs" / "specs" / "sdd-requirements-index.md"
        self.save_index(output_file)

        print("\n✨ 提取完成！")


def main():
    # 项目根目录
    project_root = Path(__file__).parent.parent

    extractor = SDDRequirementsExtractor(str(project_root))
    extractor.run()


if __name__ == "__main__":
    main()
