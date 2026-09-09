"""Story 1.7: Root .env + Docker Compose variable-ization validation tests.

Tests verify that:
- Root .env.example exists with required variable groups
- docker-compose.yml has no hardcoded user paths
- validate-env.sh exists and is syntactically valid
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_ROOT_ENV_VARS = [
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "CANVAS_BASE_PATH",
    "OLLAMA_HOST",
    "CORS_ORIGINS",
    "API_PORT",
]


class TestRootEnvExample:
    """Task 1: Root .env.example must exist with required variables."""

    def test_env_example_exists(self):
        env_example = PROJECT_ROOT / ".env.example"
        assert env_example.exists(), "Root .env.example must exist"

    @pytest.mark.parametrize("var_name", REQUIRED_ROOT_ENV_VARS)
    def test_required_variable_present(self, var_name: str):
        env_example = PROJECT_ROOT / ".env.example"
        if not env_example.exists():
            pytest.skip(".env.example not yet created")
        content = env_example.read_text()
        assert var_name in content, f"{var_name} must be in root .env.example"

    def test_env_in_gitignore(self):
        gitignore = PROJECT_ROOT / ".gitignore"
        content = gitignore.read_text()
        assert ".env" in content, ".env must be in .gitignore"


class TestDockerComposeVariableization:
    """Task 2: docker-compose.yml must not have hardcoded user paths."""

    def test_no_hardcoded_user_paths(self):
        dc = PROJECT_ROOT / "docker-compose.yml"
        content = dc.read_text()
        # 契约演进 8a80595f (2026-07-12 "neo4j 挂载迁主仓")：Story 1.7 的「compose 里
        # 不得有硬编码用户路径」被该 commit 就 neo4j 三条 bind-mount **有意推翻**——
        # 相对路径 ./docker/neo4j/* 随启动目录漂移，519MB 学习记忆图谱（唯一不可再生
        # 数据）因此寄居在一个随时会被清理的 worktree 里；commit body 原文「worktree
        # 清理 = 记忆蒸发」，并留了 backend/data/backups/ 的全量导出。⇒ 有据演进。
        # 处置：三条做成**显式豁免名单**，其余任何硬编码用户路径照旧红。
        # ⛔ 不改 docker-compose.yml（本卡零生产改动）、不放宽正则。
        # ⛔ 用「子集」而不是「相等」：若日后真把这三条改回变量化，本用例应当继续绿，
        #    而不是被这份名单钉死在今天这个中间状态。[CARD-RED-C2]
        GRANDFATHERED_ABS_MOUNTS = {
            "- /Users/Heishing/Desktop/canvas/canvas-learning-system/docker/neo4j/data:/data",
            "- /Users/Heishing/Desktop/canvas/canvas-learning-system/docker/neo4j/logs:/logs",
            "- /Users/Heishing/Desktop/canvas/canvas-learning-system/docker/neo4j/plugins:/plugins",
        }
        offending = [
            line.strip()
            for line in content.splitlines()
            if re.search(r"/Users/\w+/", line)
        ]
        unexpected = [line for line in offending if line not in GRANDFATHERED_ABS_MOUNTS]
        assert not unexpected, (
            f"Hardcoded user paths found outside the 8a80595f neo4j exemption: {unexpected}"
        )

    def test_neo4j_ports_use_variables(self):
        dc = PROJECT_ROOT / "docker-compose.yml"
        content = dc.read_text()
        assert "${NEO4J_HTTP_PORT" in content or "${NEO4J_BOLT_PORT" in content, (
            "Neo4j ports should use environment variables"
        )

    def test_vault_mount_not_readonly(self):
        dc = PROJECT_ROOT / "docker-compose.yml"
        content = dc.read_text()
        ro_vault_mounts = re.findall(r"vault.*:ro", content)
        assert not ro_vault_mounts, (
            f"Vault mounts should not be :ro by default: {ro_vault_mounts}"
        )


class TestValidateEnvScript:
    """Task 4: validate-env.sh must exist."""

    def test_script_exists(self):
        script = PROJECT_ROOT / "scripts" / "validate-env.sh"
        assert script.exists(), "scripts/validate-env.sh must exist"

    def test_script_is_executable(self):
        script = PROJECT_ROOT / "scripts" / "validate-env.sh"
        if not script.exists():
            pytest.skip("Script not yet created")
        assert script.stat().st_mode & 0o111, "validate-env.sh must be executable"
