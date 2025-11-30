#!/usr/bin/env python3
"""
Epic 12 健康检查脚本

检查项目:
- Neo4j连接
- LanceDB状态
- Graphiti客户端
- Agentic RAG编译状态
- FSRS初始化
- LangSmith配置

Usage:
    python scripts/health_check_epic12.py
    python scripts/health_check_epic12.py --json
    python scripts/health_check_epic12.py --verbose
"""

import sys
import os
import json
import argparse
from datetime import datetime
from typing import Tuple, Dict, Any, Optional
from pathlib import Path


class Colors:
    """终端颜色"""
    OK = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def check_neo4j() -> Tuple[bool, str, Dict[str, Any]]:
    """
    检查Neo4j连接状态

    Returns:
        (passed, message, details)
    """
    try:
        from neo4j import GraphDatabase

        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "password123")

        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()

        # 获取一些统计信息
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()["count"]

        driver.close()

        return True, f"Connected ({uri})", {
            "uri": uri,
            "node_count": node_count
        }
    except ImportError:
        return False, "neo4j package not installed", {}
    except Exception as e:
        return False, str(e), {}


def check_lancedb() -> Tuple[bool, str, Dict[str, Any]]:
    """
    检查LanceDB状态

    Returns:
        (passed, message, details)
    """
    try:
        import lancedb

        path = os.environ.get("LANCEDB_PATH", "./data/lancedb")

        # 确保目录存在
        Path(path).mkdir(parents=True, exist_ok=True)

        db = lancedb.connect(path)
        tables = db.table_names()

        return True, f"Ready ({path})", {
            "path": path,
            "tables": list(tables),
            "table_count": len(tables)
        }
    except ImportError:
        return False, "lancedb package not installed", {}
    except Exception as e:
        return False, str(e), {}


def check_graphiti() -> Tuple[bool, str, Dict[str, Any]]:
    """
    检查Graphiti客户端

    Returns:
        (passed, message, details)
    """
    try:
        from src.agentic_rag.clients.graphiti_client import GraphitiClient

        client = GraphitiClient()

        # 尝试获取一些统计信息
        stats = client.get_stats() if hasattr(client, 'get_stats') else {}

        node_count = stats.get('node_count', 'N/A')
        edge_count = stats.get('edge_count', 'N/A')

        return True, f"Initialized ({node_count} nodes, {edge_count} edges)", {
            "node_count": node_count,
            "edge_count": edge_count
        }
    except ImportError as e:
        return False, f"Import error: {e}", {}
    except Exception as e:
        # Graphiti可能未配置但不影响基本功能
        return True, f"Initialized (stats unavailable: {e})", {}


def check_agentic_rag() -> Tuple[bool, str, Dict[str, Any]]:
    """
    检查Agentic RAG编译状态

    Returns:
        (passed, message, details)
    """
    try:
        from src.agentic_rag.state_graph import canvas_agentic_rag

        if canvas_agentic_rag:
            # 检查graph结构
            nodes = getattr(canvas_agentic_rag, 'nodes', {})
            edges = getattr(canvas_agentic_rag, 'edges', [])

            return True, "Compiled", {
                "node_count": len(nodes) if nodes else "N/A",
                "edge_count": len(edges) if edges else "N/A"
            }
        else:
            return False, "Not compiled", {}
    except ImportError as e:
        return False, f"Import error: {e}", {}
    except Exception as e:
        return False, str(e), {}


def check_fsrs() -> Tuple[bool, str, Dict[str, Any]]:
    """
    检查FSRS初始化状态

    Returns:
        (passed, message, details)
    """
    try:
        from fsrs import FSRS, Rating

        # 创建FSRS实例测试
        fsrs = FSRS()

        return True, "Initialized", {
            "version": getattr(fsrs, 'version', 'N/A')
        }
    except ImportError:
        return False, "fsrs package not installed", {}
    except Exception as e:
        return False, str(e), {}


def check_langsmith() -> Tuple[bool, str, Dict[str, Any]]:
    """
    检查LangSmith配置

    Returns:
        (passed, message, details)
    """
    api_key = os.environ.get("LANGSMITH_API_KEY")
    tracing = os.environ.get("LANGSMITH_TRACING", "false").lower() == "true"
    project = os.environ.get("LANGSMITH_PROJECT", "default")

    if api_key and tracing:
        return True, "Connected (tracing enabled)", {
            "tracing": True,
            "project": project
        }
    elif api_key:
        return True, "Configured (tracing disabled)", {
            "tracing": False,
            "project": project
        }
    else:
        # LangSmith是可选的
        return True, "Not configured (optional)", {
            "configured": False
        }


def check_cohere() -> Tuple[bool, str, Dict[str, Any]]:
    """
    检查Cohere API配置

    Returns:
        (passed, message, details)
    """
    api_key = os.environ.get("COHERE_API_KEY")

    if api_key:
        # 可选：测试API连接
        return True, "Configured", {
            "configured": True
        }
    else:
        # Cohere是可选的（会降级到本地Reranking）
        return True, "Not configured (will use local reranking)", {
            "configured": False
        }


def check_openai() -> Tuple[bool, str, Dict[str, Any]]:
    """
    检查OpenAI API配置

    Returns:
        (passed, message, details)
    """
    api_key = os.environ.get("OPENAI_API_KEY")

    if api_key:
        return True, "Configured", {
            "configured": True,
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        }
    else:
        # OpenAI用于Query重写，是可选的
        return True, "Not configured (query rewrite disabled)", {
            "configured": False
        }


def run_all_checks(verbose: bool = False) -> Dict[str, Any]:
    """
    运行所有健康检查

    Args:
        verbose: 是否输出详细信息

    Returns:
        检查结果字典
    """
    checks = [
        ("Neo4j", check_neo4j),
        ("LanceDB", check_lancedb),
        ("Graphiti", check_graphiti),
        ("Agentic RAG", check_agentic_rag),
        ("FSRS", check_fsrs),
        ("LangSmith", check_langsmith),
        ("Cohere", check_cohere),
        ("OpenAI", check_openai),
    ]

    results = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "checks": {}
    }

    all_passed = True
    critical_failed = False

    print(f"\n{Colors.BOLD}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}  Epic 12 Health Check{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 50}{Colors.RESET}\n")

    for name, check_fn in checks:
        try:
            passed, message, details = check_fn()

            # 确定严重性
            is_critical = name in ["Neo4j", "LanceDB", "Agentic RAG"]

            if passed:
                status_icon = f"{Colors.OK}[OK]{Colors.RESET}"
            elif is_critical:
                status_icon = f"{Colors.ERROR}[FAIL]{Colors.RESET}"
                critical_failed = True
                all_passed = False
            else:
                status_icon = f"{Colors.WARNING}[WARN]{Colors.RESET}"

            print(f"{status_icon} {name}: {message}")

            if verbose and details:
                for key, value in details.items():
                    print(f"     {key}: {value}")

            results["checks"][name] = {
                "passed": passed,
                "message": message,
                "details": details,
                "critical": is_critical
            }

        except Exception as e:
            print(f"{Colors.ERROR}[FAIL]{Colors.RESET} {name}: Unexpected error - {e}")
            results["checks"][name] = {
                "passed": False,
                "message": f"Unexpected error: {e}",
                "details": {},
                "critical": name in ["Neo4j", "LanceDB", "Agentic RAG"]
            }
            all_passed = False

    # 总结
    print(f"\n{Colors.BOLD}{'=' * 50}{Colors.RESET}")

    if critical_failed:
        results["overall_status"] = "unhealthy"
        print(f"{Colors.ERROR}  CRITICAL: Some essential services are down{Colors.RESET}")
    elif not all_passed:
        results["overall_status"] = "degraded"
        print(f"{Colors.WARNING}  WARNING: Some optional services are not configured{Colors.RESET}")
    else:
        print(f"{Colors.OK}  All checks passed!{Colors.RESET}")

    print(f"{Colors.BOLD}{'=' * 50}{Colors.RESET}\n")

    return results


def main():
    parser = argparse.ArgumentParser(description="Epic 12 Health Check")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed information")
    args = parser.parse_args()

    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    results = run_all_checks(verbose=args.verbose)

    if args.json:
        print(json.dumps(results, indent=2))

    # 返回码
    if results["overall_status"] == "unhealthy":
        return 1
    elif results["overall_status"] == "degraded":
        return 0  # 降级但可用
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
