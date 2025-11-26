#!/usr/bin/env python3
"""
ADR Coverage Verification Script
验证Architecture文档中的技术决策是否有对应的ADR记录

功能:
1. 扫描Architecture文档，提取技术决策点
2. 检查每个决策是否有对应的ADR文件
3. 计算ADR覆盖率并与门禁比较
4. 生成覆盖率报告

用法:
  python scripts/verify-adr-coverage.py [--report] [--threshold 80]

参数:
  --report    生成详细报告到docs/specs/adr-coverage-report.md
  --threshold 覆盖率门禁值 (默认80)

返回码:
  0 - 覆盖率达标 (≥ threshold)
  1 - 覆盖率不达标

Reference: Section 16.5.2 of planning document
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set

# Set UTF-8 encoding for Windows console
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# 已知的技术决策类别
DECISION_CATEGORIES = [
    "framework", "database", "caching", "logging", "testing",
    "authentication", "authorization", "api", "architecture",
    "persistence", "communication", "error-handling", "retry",
    "memory", "agent", "search", "integration"
]

# 决策关键词模式
DECISION_KEYWORDS = [
    r'使用\s*(\S+)\s*(?:作为|来|进行)',
    r'选择\s*(\S+)\s*(?:方案|框架|库|工具)',
    r'采用\s*(\S+)\s*(?:模式|架构|策略)',
    r'(?:Use|Using)\s+(\S+)\s+(?:for|as|to)',
    r'(?:Chose|Choosing|Selected?)\s+(\S+)',
    r'(?:Adopted?|Adopting)\s+(\S+)',
    r'决策[:：]\s*(.+)',
    r'Decision[:：]\s*(.+)',
]


class ADRCoverageVerifier:
    """ADR覆盖率验证器"""

    def __init__(self, project_root: Path, threshold: int = 80):
        self.project_root = project_root
        self.threshold = threshold
        self.arch_dir = project_root / "docs" / "architecture"
        self.adr_dir = project_root / "docs" / "architecture" / "decisions"
        self.prd_dir = project_root / "docs" / "prd"

        # 收集的技术决策
        self.tech_decisions: List[Dict] = []

        # 现有ADR
        self.existing_adrs: Dict[str, Dict] = {}

        # 覆盖率结果
        self.coverage_results: Dict = {
            'total': 0,
            'covered': 0,
            'missing': [],
            'percentage': 0.0
        }

    def scan_existing_adrs(self) -> Dict[str, Dict]:
        """扫描现有ADR文件"""
        adrs = {}

        if not self.adr_dir.exists():
            return adrs

        adr_files = list(self.adr_dir.glob("*.md"))

        for adr_file in adr_files:
            try:
                with open(adr_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 提取标题和关键词
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else adr_file.stem

                # 提取状态
                status_match = re.search(r'^##\s*Status\s*\n+\s*(\w+)', content, re.MULTILINE)
                status = status_match.group(1) if status_match else "Unknown"

                # 提取关键词 (从标题和内容)
                keywords = self._extract_keywords(title + " " + content)

                adrs[adr_file.name] = {
                    'path': str(adr_file),
                    'title': title,
                    'status': status,
                    'keywords': keywords
                }

            except Exception as e:
                print(f"Warning: Cannot parse {adr_file}: {e}")

        return adrs

    def _extract_keywords(self, text: str) -> Set[str]:
        """提取文本中的技术关键词"""
        keywords = set()

        # 技术名称模式
        tech_patterns = [
            r'(LangGraph|LangChain|Graphiti|FastAPI|Pydantic)',
            r'(Neo4j|LanceDB|Redis|PostgreSQL|SQLite)',
            r'(SSE|WebSocket|HTTP|REST|GraphQL)',
            r'(pytest|unittest|schemathesis|Gherkin|BDD)',
            r'(structlog|logging|OpenTelemetry)',
            r'(async|concurrent|parallel)',
            r'(retry|circuit.?breaker|fallback)',
            r'(cache|caching|tiered)',
            r'(FSRS|Ebbinghaus|spaced.?repetition)',
            r'(Canvas|Obsidian|Node|Edge)',
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.update(m.lower() for m in matches if isinstance(m, str))

        return keywords

    def extract_decisions_from_architecture(self) -> List[Dict]:
        """从Architecture文档中提取技术决策"""
        decisions = []

        if not self.arch_dir.exists():
            return decisions

        # 扫描所有架构文档（排除decisions目录）
        arch_files = [f for f in self.arch_dir.glob("*.md") if f.is_file()]

        for arch_file in arch_files:
            decisions.extend(self._extract_decisions_from_file(arch_file, "architecture"))

        return decisions

    def extract_decisions_from_prd(self) -> List[Dict]:
        """从PRD文档中提取技术决策"""
        decisions = []

        if not self.prd_dir.exists():
            return decisions

        # 扫描PRD目录
        prd_files = list(self.prd_dir.glob("**/*.md"))

        for prd_file in prd_files:
            decisions.extend(self._extract_decisions_from_file(prd_file, "prd"))

        return decisions

    def _extract_decisions_from_file(self, file_path: Path, source_type: str) -> List[Dict]:
        """从单个文件提取决策"""
        decisions = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"Warning: Cannot read {file_path}: {e}")
            return []

        # 查找"技术决策"或"Architecture Decision"相关章节
        in_decision_section = False
        current_decision = None

        for line_num, line in enumerate(lines, 1):
            # 检测决策章节开始
            if re.search(r'(技术决策|Architecture\s*Decision|Tech\s*Stack|Technology\s*Choice)', line, re.IGNORECASE):
                in_decision_section = True
                continue

            # 检测章节结束（遇到同级或更高级标题）
            if in_decision_section and re.match(r'^##?\s+[^#]', line):
                if not re.search(r'(决策|Decision|Choice|Stack)', line, re.IGNORECASE):
                    in_decision_section = False

            # 在决策章节或全文中查找决策模式
            for pattern in DECISION_KEYWORDS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    decision_text = match.group(1) if match.groups() else match.group(0)
                    keywords = self._extract_keywords(line)

                    if keywords:  # 只有当提取到技术关键词时才记录
                        decisions.append({
                            'text': decision_text.strip(),
                            'keywords': keywords,
                            'source_file': file_path.name,
                            'source_line': line_num,
                            'source_type': source_type,
                            'context': line.strip()[:100]
                        })

        return decisions

    def match_decision_to_adr(self, decision: Dict) -> Optional[str]:
        """将决策匹配到ADR"""
        decision_keywords = decision['keywords']

        for adr_name, adr_info in self.existing_adrs.items():
            adr_keywords = adr_info['keywords']

            # 计算关键词交集
            intersection = decision_keywords & adr_keywords

            # 如果有共同关键词，认为匹配
            if intersection:
                return adr_name

        return None

    def check_coverage(self) -> Dict:
        """检查ADR覆盖率"""
        covered = []
        missing = []

        for decision in self.tech_decisions:
            matched_adr = self.match_decision_to_adr(decision)
            if matched_adr:
                decision['matched_adr'] = matched_adr
                covered.append(decision)
            else:
                missing.append(decision)

        total = len(self.tech_decisions)
        covered_count = len(covered)
        percentage = (covered_count / total * 100) if total > 0 else 100.0

        return {
            'total': total,
            'covered': covered_count,
            'missing': missing,
            'percentage': percentage
        }

    def verify(self) -> Tuple[bool, float]:
        """
        执行覆盖率验证

        Returns:
            (passed, coverage_percentage)
        """
        print("=" * 60)
        print("[VERIFY] ADR Coverage Verification")
        print("=" * 60)
        print(f"  Threshold: {self.threshold}%")
        print()

        # 1. 扫描现有ADR
        print("[1/4] Scanning existing ADRs...")
        self.existing_adrs = self.scan_existing_adrs()
        print(f"  Found {len(self.existing_adrs)} ADR files")
        print()

        # 2. 从Architecture文档提取决策
        print("[2/4] Extracting decisions from Architecture docs...")
        arch_decisions = self.extract_decisions_from_architecture()
        print(f"  Found {len(arch_decisions)} architecture decisions")

        # 3. 从PRD文档提取决策
        print("[3/4] Extracting decisions from PRD docs...")
        prd_decisions = self.extract_decisions_from_prd()
        print(f"  Found {len(prd_decisions)} PRD decisions")

        # 合并并去重
        self.tech_decisions = self._deduplicate_decisions(arch_decisions + prd_decisions)
        print(f"  Total unique decisions: {len(self.tech_decisions)}")
        print()

        # 4. 检查覆盖率
        print("[4/4] Checking ADR coverage...")
        self.coverage_results = self.check_coverage()
        print(f"  Coverage: {self.coverage_results['covered']}/{self.coverage_results['total']} ({self.coverage_results['percentage']:.1f}%)")
        print()

        # 判断是否通过
        passed = self.coverage_results['percentage'] >= self.threshold

        # 打印结果
        print("=" * 60)
        if passed:
            print(f"[PASS] ADR Coverage {self.coverage_results['percentage']:.1f}% >= {self.threshold}% threshold")
        else:
            print(f"[FAIL] ADR Coverage {self.coverage_results['percentage']:.1f}% < {self.threshold}% threshold")

            # 列出缺失项
            if self.coverage_results['missing']:
                print("\nDecisions missing ADR documentation:")
                for decision in self.coverage_results['missing'][:5]:
                    print(f"  - {decision['text']} ({', '.join(decision['keywords'])})")
                    print(f"    Source: {decision['source_file']}:L{decision['source_line']}")
                if len(self.coverage_results['missing']) > 5:
                    print(f"  ... and {len(self.coverage_results['missing']) - 5} more")

        print("=" * 60)

        return passed, self.coverage_results['percentage']

    def _deduplicate_decisions(self, decisions: List[Dict]) -> List[Dict]:
        """去重决策列表"""
        seen_keywords = set()
        unique = []

        for decision in decisions:
            key = frozenset(decision['keywords'])
            if key not in seen_keywords and decision['keywords']:
                seen_keywords.add(key)
                unique.append(decision)

        return unique

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """生成详细覆盖率报告"""
        pct = self.coverage_results['percentage']

        report = f"""# ADR Coverage Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Threshold**: {self.threshold}%
**Status**: {'PASS' if pct >= self.threshold else 'FAIL'}

---

## Coverage Summary

| Metric | Value |
|--------|-------|
| Total Decisions | {self.coverage_results['total']} |
| Covered by ADR | {self.coverage_results['covered']} |
| Missing ADR | {len(self.coverage_results['missing'])} |
| Coverage | {pct:.1f}% |
| Status | {'PASS' if pct >= self.threshold else 'FAIL'} |

---

## Existing ADRs ({len(self.existing_adrs)})

| ADR | Title | Status | Keywords |
|-----|-------|--------|----------|
"""
        for adr_name, adr_info in sorted(self.existing_adrs.items()):
            keywords = ', '.join(list(adr_info['keywords'])[:3])
            report += f"| {adr_name} | {adr_info['title'][:40]}... | {adr_info['status']} | {keywords} |\n"

        report += f"""
---

## Decisions Missing ADR ({len(self.coverage_results['missing'])})

"""
        if self.coverage_results['missing']:
            report += "| Decision | Keywords | Source | Line |\n"
            report += "|----------|----------|--------|------|\n"
            for decision in self.coverage_results['missing']:
                keywords = ', '.join(list(decision['keywords'])[:3])
                report += f"| {decision['text'][:40]}... | {keywords} | {decision['source_file']} | L{decision['source_line']} |\n"
        else:
            report += "_All decisions have corresponding ADR documentation._\n"

        report += """
---

## Recommendations

"""
        if pct < self.threshold:
            report += f"ADR coverage is below the {self.threshold}% threshold. To improve:\n\n"
            report += "1. Create ADRs for the missing decisions listed above\n"
            report += "2. Use the command: `@architect *create-adr {decision-title}`\n"
            report += "3. Ensure ADRs contain Context7技术验证 section for source verification\n\n"

            # 推荐创建的ADR
            if self.coverage_results['missing']:
                report += "### Suggested ADRs to Create\n\n"
                seen = set()
                for decision in self.coverage_results['missing'][:5]:
                    keywords = list(decision['keywords'])
                    if keywords:
                        primary_keyword = keywords[0]
                        if primary_keyword not in seen:
                            seen.add(primary_keyword)
                            report += f"- ADR: {primary_keyword.upper()} Selection/Integration\n"
                            report += f"  Context: {decision['context'][:60]}...\n\n"
        else:
            report += "Coverage meets the threshold. No action required.\n"

        report += f"""
---

**Report generated by**: scripts/verify-adr-coverage.py
**Reference**: Section 16.5.2 of planning document
"""

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\nReport saved to: {output_path}")

        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Verify ADR coverage against architecture decisions')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--threshold', type=int, default=80, help='Coverage threshold percentage (default: 80)')
    parser.add_argument('--output', type=str, help='Report output path (default: docs/specs/adr-coverage-report.md)')

    args = parser.parse_args()

    # 项目根目录
    project_root = Path(__file__).parent.parent

    # 创建验证器并执行
    verifier = ADRCoverageVerifier(project_root, args.threshold)
    passed, coverage = verifier.verify()

    # 生成报告
    if args.report:
        output_path = Path(args.output) if args.output else project_root / "docs" / "specs" / "adr-coverage-report.md"
        verifier.generate_report(output_path)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
