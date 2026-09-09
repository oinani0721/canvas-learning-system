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
        #
        # 豁免面 = 「**恰好 services.neo4j.volumes 里的这三条，各至多一次**」。
        # 判据分两轴，缺一不可：
        #   轴一（内容，逐行文本）：任何含硬编码用户路径的**行**，其内容必须在豁免名单里。
        #       用原始文本扫描而非 YAML 值，是为了不放过写在**注释**里的路径——
        #       原断言的正则是对全文跑的，换成只看 YAML 值会在这一面变弱。
        #   轴二（位置，YAML 结构）：任何含硬编码用户路径的**值**，其结构路径必须恰为
        #       services → neo4j → volumes → <序号>，且每条至多出现一次。
        #
        # ⚠️ 轴二为什么不能用「按缩进认 service」的行扫描（Codex round-1 HIGH + round-2
        #    HIGH 连续两轮打回本条）：`other: # comment` / `"other":` 都是合法 YAML 但
        #    不匹配 `^  name:$`，于是那一行会**沿用上一个**被认出的名字；实测把一条挪到
        #    `other: # comment` 的 volumes 下，行扫描把它算成了 `neo4j-test-data`
        #    （顶层 volumes 段的一个卷名，根本不是 service）而三段判据全过。
        #    结构问题要用结构化解析回答，不能用缩进启发式。
        # ⛔ 三条判据都用「子集/上界」而不是「相等」：日后真把这三条改回变量化时，
        #    本用例应当继续绿，而不是被这份名单钉死在今天这个中间状态。
        # ⛔ 不改 docker-compose.yml（本卡零生产改动）、不放宽正则。[CARD-RED-C2]
        GRANDFATHERED_MOUNT_VALUES = {
            "/Users/Heishing/Desktop/canvas/canvas-learning-system/docker/neo4j/data:/data",
            "/Users/Heishing/Desktop/canvas/canvas-learning-system/docker/neo4j/logs:/logs",
            "/Users/Heishing/Desktop/canvas/canvas-learning-system/docker/neo4j/plugins:/plugins",
        }
        EXEMPT_VOLUMES_PATH = ("services", "neo4j", "volumes")
        HARDCODED = re.compile(r"/Users/\w+/")

        # ── 轴一：内容（含注释行）────────────────────────────────────────────
        offending_lines = [
            line.strip() for line in content.splitlines() if HARDCODED.search(line)
        ]
        wrong_content = [
            line
            for line in offending_lines
            if line.lstrip("- ").strip() not in GRANDFATHERED_MOUNT_VALUES
        ]
        assert not wrong_content, (
            f"Hardcoded user paths outside the 8a80595f neo4j exemption: {wrong_content}"
        )

        # 轴一.b（数量，也走原始文本）：每条豁免值在**全文**至多出现一次。
        # ⚠️ 数量判据必须在文本层做，不能只数 YAML 解析后的值（Codex round-3 MEDIUM）：
        # `<<:` 合并键 + 显式覆盖会让原文里出现两次的路径在解析结果里只剩一次甚至归零，
        # 只数解析值时重复就被 safe_load 悄悄吃掉了。
        duplicated_in_text = [
            value
            for value in GRANDFATHERED_MOUNT_VALUES
            if sum(1 for line in offending_lines if line.lstrip("- ").strip() == value) > 1
        ]
        assert not duplicated_in_text, (
            f"Exempted mount values appear more than once in the file text: {duplicated_in_text}"
        )

        # ── 轴二：位置（YAML 结构）──────────────────────────────────────────
        import yaml

        compose = yaml.safe_load(content)
        located: list[tuple[tuple, str]] = []

        def _walk(node, path: tuple):
            if isinstance(node, dict):
                for k, v in node.items():
                    if isinstance(k, str) and HARDCODED.search(k):
                        located.append((path + (k,), k))
                    _walk(v, path + (str(k),))
            elif isinstance(node, list):
                for idx, v in enumerate(node):
                    _walk(v, path + (str(idx),))
            elif isinstance(node, str) and HARDCODED.search(node):
                located.append((path, node))

        _walk(compose, ())

        # ⚠️ 深度必须**精确**是 4（services / neo4j / volumes / <序号>），不能只比前三段
        # （Codex round-3 HIGH）：`path[:3]` 会把 volumes 元素的**后代字段**一并豁免，
        # 于是长格式挂载 `- {type: bind, source: <获准串>, target: /other}` 的 source
        # 落在 (services, neo4j, volumes, 0, "source")，前三段相同就放行了——
        # 而它实际挂到了另一个 target，是一条**新的**主机路径挂载。
        misplaced = [
            (path, value)
            for path, value in located
            if len(path) != 4
            or path[:3] != EXEMPT_VOLUMES_PATH
            or value not in GRANDFATHERED_MOUNT_VALUES
        ]
        assert not misplaced, (
            f"Hardcoded user paths outside services.neo4j.volumes[<i>]: {misplaced}"
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
