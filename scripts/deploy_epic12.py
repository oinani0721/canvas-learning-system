#!/usr/bin/env python3
"""
Epic 12 部署脚本

功能:
- 环境检查
- 依赖安装
- 服务启动
- 健康验证

Usage:
    python scripts/deploy_epic12.py
    python scripts/deploy_epic12.py --skip-docker
    python scripts/deploy_epic12.py --check-only
"""

import sys
import subprocess
import os
from pathlib import Path
from typing import Tuple, Optional
import argparse


class Colors:
    """终端颜色"""
    OK = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}  {text}{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 50}{Colors.RESET}\n")


def print_step(step: int, total: int, text: str):
    """打印步骤"""
    print(f"[{step}/{total}] {text}...")


def print_ok(text: str):
    """打印成功"""
    print(f"  {Colors.OK}✓{Colors.RESET} {text}")


def print_warning(text: str):
    """打印警告"""
    print(f"  {Colors.WARNING}⚠{Colors.RESET} {text}")


def print_error(text: str):
    """打印错误"""
    print(f"  {Colors.ERROR}✗{Colors.RESET} {text}")


def run_command(cmd: str, capture: bool = True) -> Tuple[int, str, str]:
    """运行命令"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def check_python_version() -> bool:
    """检查Python版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print_ok(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python 3.9+ required, got {version.major}.{version.minor}")
        return False


def check_docker() -> bool:
    """检查Docker"""
    code, stdout, stderr = run_command("docker --version")
    if code == 0:
        version = stdout.strip()
        print_ok(f"Docker: {version}")
        return True
    else:
        print_warning("Docker not installed (optional for Neo4j)")
        return False


def check_neo4j() -> bool:
    """检查Neo4j连接"""
    try:
        from neo4j import GraphDatabase
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "password123")

        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        driver.close()
        print_ok(f"Neo4j: Connected ({uri})")
        return True
    except Exception as e:
        print_error(f"Neo4j: {e}")
        return False


def check_lancedb() -> bool:
    """检查LanceDB"""
    try:
        import lancedb
        path = os.environ.get("LANCEDB_PATH", "./data/lancedb")
        Path(path).mkdir(parents=True, exist_ok=True)
        db = lancedb.connect(path)
        print_ok(f"LanceDB: Ready ({path})")
        return True
    except Exception as e:
        print_error(f"LanceDB: {e}")
        return False


def check_agentic_rag() -> bool:
    """检查Agentic RAG"""
    try:
        # 尝试导入核心模块
        from src.agentic_rag.state_graph import canvas_agentic_rag
        if canvas_agentic_rag:
            print_ok("Agentic RAG: Compiled")
            return True
        else:
            print_error("Agentic RAG: Not compiled")
            return False
    except ImportError as e:
        print_warning(f"Agentic RAG: Import error - {e}")
        return False
    except Exception as e:
        print_error(f"Agentic RAG: {e}")
        return False


def check_langsmith() -> bool:
    """检查LangSmith配置"""
    api_key = os.environ.get("LANGSMITH_API_KEY")
    tracing = os.environ.get("LANGSMITH_TRACING", "false").lower() == "true"

    if api_key and tracing:
        print_ok("LangSmith: Configured (tracing enabled)")
        return True
    elif api_key:
        print_warning("LangSmith: API key set but tracing disabled")
        return True
    else:
        print_warning("LangSmith: Not configured (optional)")
        return True  # 可选组件


def install_dependencies() -> bool:
    """安装依赖"""
    requirements = Path(__file__).parent.parent / "requirements.txt"

    if not requirements.exists():
        print_error("requirements.txt not found")
        return False

    print("  Installing Python dependencies...")
    code, stdout, stderr = run_command(f"pip install -r {requirements} -q")

    if code == 0:
        print_ok("Dependencies installed")
        return True
    else:
        print_error(f"Failed to install dependencies: {stderr}")
        return False


def start_neo4j_docker() -> bool:
    """启动Neo4j Docker容器"""
    # 检查是否已运行
    code, stdout, _ = run_command("docker ps --filter name=neo4j-canvas --format '{{.Names}}'")
    if "neo4j-canvas" in stdout:
        print_ok("Neo4j: Already running")
        return True

    # 检查是否存在但停止
    code, stdout, _ = run_command("docker ps -a --filter name=neo4j-canvas --format '{{.Names}}'")
    if "neo4j-canvas" in stdout:
        print("  Starting existing Neo4j container...")
        code, _, stderr = run_command("docker start neo4j-canvas")
        if code == 0:
            print_ok("Neo4j: Started")
            return True
        else:
            print_error(f"Failed to start Neo4j: {stderr}")
            return False

    # 创建新容器
    print("  Creating Neo4j container...")
    cmd = """docker run -d \
        --name neo4j-canvas \
        --restart unless-stopped \
        -p 7474:7474 -p 7687:7687 \
        -e NEO4J_AUTH=neo4j/password123 \
        -v neo4j_data:/data \
        neo4j:5.15"""

    code, _, stderr = run_command(cmd)
    if code == 0:
        print_ok("Neo4j: Created and started")
        print("  Waiting for Neo4j to initialize (10s)...")
        import time
        time.sleep(10)
        return True
    else:
        print_error(f"Failed to create Neo4j: {stderr}")
        return False


def create_data_directories() -> bool:
    """创建数据目录"""
    directories = [
        "./data/lancedb",
        "./logs",
        "./backups"
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    print_ok("Data directories created")
    return True


def run_health_check() -> bool:
    """运行健康检查"""
    health_script = Path(__file__).parent / "health_check_epic12.py"

    if health_script.exists():
        code, stdout, stderr = run_command(f"python {health_script}")
        print(stdout)
        return code == 0
    else:
        print_warning("Health check script not found, running inline checks...")

        checks = [
            ("Neo4j", check_neo4j),
            ("LanceDB", check_lancedb),
            ("Agentic RAG", check_agentic_rag),
            ("LangSmith", check_langsmith),
        ]

        all_passed = True
        for name, check_fn in checks:
            try:
                if not check_fn():
                    all_passed = False
            except Exception as e:
                print_error(f"{name}: {e}")
                all_passed = False

        return all_passed


def main():
    parser = argparse.ArgumentParser(description="Epic 12 Deployment Script")
    parser.add_argument("--skip-docker", action="store_true",
                        help="Skip Docker/Neo4j setup")
    parser.add_argument("--check-only", action="store_true",
                        help="Only run checks, no installation")
    args = parser.parse_args()

    print_header("Epic 12 Deployment Script")

    total_steps = 5 if not args.skip_docker else 4
    step = 0

    # Step 1: 环境检查
    step += 1
    print_step(step, total_steps, "Checking environment")

    if not check_python_version():
        print_error("Environment check failed")
        return 1

    has_docker = check_docker()

    if args.check_only:
        print("\n[Check-only mode] Skipping installation steps\n")
        return 0 if run_health_check() else 1

    # Step 2: 安装依赖
    step += 1
    print_step(step, total_steps, "Installing dependencies")

    if not install_dependencies():
        print_error("Dependency installation failed")
        return 1

    # Step 3: 创建目录
    step += 1
    print_step(step, total_steps, "Creating data directories")

    if not create_data_directories():
        print_error("Failed to create directories")
        return 1

    # Step 4: 启动Neo4j (可选)
    if not args.skip_docker and has_docker:
        step += 1
        print_step(step, total_steps, "Starting Neo4j")

        if not start_neo4j_docker():
            print_warning("Neo4j setup failed - you may need to start it manually")

    # Step 5: 健康验证
    step += 1
    print_step(step, total_steps, "Verifying deployment")

    if not run_health_check():
        print_warning("Some health checks failed - review above")

    # 完成
    print_header("Deployment Complete!")

    print("Next steps:")
    print("  1. Review .env configuration")
    print("  2. Start the API server:")
    print("     python -m src.api.main")
    print("  3. Access the API at:")
    print("     http://localhost:8000")
    print("  4. View API docs at:")
    print("     http://localhost:8000/docs")
    print("")

    return 0


if __name__ == "__main__":
    sys.exit(main())
