# Shared fixtures for EPIC-32 FSRS unit tests
# Extracted from test_review_service_fsrs.py, test_fsrs_state_query.py
# to eliminate fixture duplication across 4 files.
"""
Shared pytest fixtures for FSRS unit tests.

Provides mock dependencies (CanvasService, BackgroundTaskManager) and
ReviewService factory/instance fixtures used by:
- test_review_service_fsrs.py
- test_fsrs_state_query.py
- test_card_state_concurrent_write.py (indirectly)
"""

import ast
import hashlib
import warnings
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ═══════════════════════════════════════════════════════════════════════════════
# CARD-TEST-hygiene-vaultinit [BATCH-2026-09-05-第十二批]
# Session-level invariant: running tests/unit must not leave a vault skeleton
# behind in the repository.
#
# 背景（实测 2026-09-05，本卡 (a) 定位）: `VaultInitService.initialize_vault()`
# 唯一的生产调用点是 `system.py::setup_wizard`, 那里 `Path(vault_path).resolve()`
# 会把**相对路径 / 空串静默拼到 cwd 上** —— pytest 从 backend/ 起跑时,
# cwd 就是 backend/, 于是骨架 (raw/ wiki/ outputs/ CLAUDE.md) 落进代码目录。
# 一个冻结的污染证据树 (card-z4-redbase @ c8611a89) 正是这个形态。
#
# 这道门不修复任何写入路径, 它只保证**下次再发生时会立刻变红**, 而不是像
# 之前那样靠人在几天后 `git status` 时偶然发现、并且归错文件。
#
# ⚠️ 覆盖面（别把它当成全覆盖）: 本 fixture 在 tests/unit/conftest.py,
# 只在 **tests/unit 被收集时**生效。本卡实测到的那个真凶其实在 tests/contract
# —— `test_openapi_contract.py::test_api_contract[POST /api/v1/system/setup-wizard]`,
# schemathesis 对全端点做属性输入且无 exclude, 生成的空串/相对路径打进
# setup-wizard 就地建骨架。**那条链不在这道门的覆盖范围内**, 它由
# `system.py::SetupWizardRequest` 的绝对路径 field_validator 堵住 (同批同卡)。
# 想让这道门覆盖全部套件, 需要把它放到 backend/tests/conftest.py —— 那个文件
# 当前是另一张卡 (Y7-A) 的地盘, 本卡硬边界禁改。
# ═══════════════════════════════════════════════════════════════════════════════

# 与 app/services/vault_init_service.py::VAULT_DIRECTORIES 的顶层项对应
# （raw / wiki/... / outputs/... → 顶层 raw, wiki, outputs）加上 CLAUDE.md。
_HYGIENE_SKELETON_PATHS = ("raw", "wiki", "outputs", "CLAUDE.md")

# 已入库、会被属性输入类测试写坏的文件（sha 变化即污染）。
_HYGIENE_TRACKED_FILES = (".gitignore", "config/subject_mapping.yaml")

_HYGIENE_TMP_GLOB = "test-vault*"

# CARD-HYGIENE-conftest [BATCH-2026-09-07-第十三批]
# ⛔ 拼接而不是整段字面量。本文件会被下面 `_hygiene_scan_tmp_literals()` 自身排除,
# 但只要整段路径还以任何形式留在本文件里 (字符串、docstring、**注释**都算),
# 验收单 §二.7a 那条 `grep -c` 验伪锚就恒 >= 1 ——「门写对了」与「门漏了
# 自身排除」两种情况再也分不开。所以本文件全篇不写整段路径, 只写拼接。
# ⚠️ 必须用 `+`: 相邻字面量 ("/tmp/" "test-vault") 在词法期就被折叠成一个
# ast.Constant, 拆了等于没拆 (实测)。
_TMP_LITERAL = "/tmp/" + "test-vault"


def _hygiene_backend_root() -> Path:
    """backend/ 的绝对路径。

    走 __file__ 而不是 cwd: 这道门必须在任何起跑目录下都盯同一个 backend/,
    而 pytest 的 cwd 取决于调用方 (repo 根 / backend/ / IDE)。
    conftest 位于 backend/tests/unit/ → parents[2] == backend/。
    """
    return Path(__file__).resolve().parents[2]


def _hygiene_snapshot() -> dict:
    """只读快照。**不创建、不删除、不写入任何文件。**

    setup 与 teardown 共用本函数 —— 若两侧各写一份逻辑, 环境差异
    (例如 /tmp 一时不可读) 会让前后口径不一致, 门就成了假红。
    读不到的目标一律记 None, 前后同为 None 即视为未变化。
    """
    root = _hygiene_backend_root()
    exists = {rel: (root / rel).exists() for rel in _HYGIENE_SKELETON_PATHS}

    sha: dict[str, str | None] = {}
    for rel in _HYGIENE_TRACKED_FILES:
        try:
            sha[rel] = hashlib.sha256((root / rel).read_bytes()).hexdigest()
        except OSError:
            sha[rel] = None

    try:
        tmp: frozenset[str] | None = frozenset(p.name for p in Path("/tmp").glob(_HYGIENE_TMP_GLOB))
    except OSError:
        tmp = None

    return {"exists": exists, "sha": sha, "tmp": tmp}


def _hygiene_scan_tmp_literals() -> tuple[list[str], list[str]]:
    """扫 tests/unit/**/*.py 里硬编码的 `/tmp/` + `test-vault` 字符串常量。

    **只读**: 只 read_bytes + ast.parse。不创建 / 不删除 / 不写入任何文件,
    不 import 被扫文件, 不依赖 cwd (扫描根走 __file__, 与门盯 backend/ 同理)。

    为什么必须走 AST 而不是 grep 全文:
    - `test_startup_health_check.py:56-66` 有三条 `#` 注释记录 Y6-A 改前的旧
      硬编码值 —— grep 会把这些注释判成回归 (假红);
    - 本文件自己的告警文案也含同一段路径 —— grep 形态的门必然自指。
    AST 只看 `ast.Constant` 字符串, 两个假红面同时消失。

    已知盲区 (如实登记, 见验收单「本卡未证明什么」②): 运行期拼接出来的路径
    (`"/tmp/" + name`、f-string 变量段、`os.path.join` 分段) 不是单个 Constant,
    本门看不见。

    返回 (hits, unchecked):
      hits      —— "<file>:<lineno>", 可归属到**本 worktree** 的写者嫌疑;
      unchecked —— 读不了 / 解析不了的文件。**不算通过**:「没命中」与「没检查」
                   必须分开, 否则一个语法坏掉的文件就能让门静默放行。
    """
    self_path = Path(__file__).resolve()
    scan_root = self_path.parent

    hits: list[str] = []
    unchecked: list[str] = []

    for py in sorted(scan_root.rglob("*.py")):
        try:
            if py.resolve() == self_path:
                continue
            source = py.read_bytes()
        except OSError as exc:
            unchecked.append(f"{py} (读取失败: {type(exc).__name__}: {exc})")
            continue

        try:
            tree = ast.parse(source, filename=str(py))
        except (SyntaxError, ValueError) as exc:
            unchecked.append(f"{py} (解析失败: {type(exc).__name__}: {exc})")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and _TMP_LITERAL in node.value:
                hits.append(f"{py}:{node.lineno}")

    return hits, unchecked


@pytest.fixture(scope="session", autouse=True)
def _no_vault_skeleton_left_behind():
    """CARD-TEST-hygiene-vaultinit (c): 跑完 tests/unit 不得往仓库里撒 vault 骨架。

    失败发生在 session teardown, 表现为末尾一条 ERROR 且 pytest rc != 0。

    CARD-HYGIENE-conftest [BATCH-2026-09-07-第十三批] 按**能不能归属**分流
    (手册 §四.5 D-27 裁定 (乙)):
    - **可归属**信号 → 硬 fail 不变: 树内 vault 骨架路径、树内 tracked 文件
      sha、以及新增的树内源码字面量门 —— 三者都在本 worktree 内, 天然唯一;
    - **不可归属**信号 → 降为「环境受干扰」告警: `/tmp` 是**全机共享**的,
      任何别的 worktree 在本 session 首尾两次快照之间建出匹配目录, 都会让
      本车道 teardown 变红。Codex Y6-A HIGH #1 实证 mtime / ps / lsof 都不能
      单独证明历史写入归属 ⇒ 把它判成「本卡新增回归」是错误归因。

    ⚠️ 降级只发生在**不可归属**这一侧, 不是「放松要求」: 本树自己往
    /tmp 根写 test-vault* 目录仍然硬红 —— 那正是新增源码字面量门的职责。
    (这段说明刻意不写成整段路径: docstring 也是 ast.Constant, 写全了
     就成了门自己要抓的形态 —— 本卡打补丁时被自校验当场拦下过一次。)
    ⚠️ 也不是静默吞掉: 告警文案里的固定串「环境受干扰」是可 grep 的判据,
    pytest.ini 无 filterwarnings ⇒ 它会进 warnings summary 与汇总行。
    """
    # setup 段扫源码: 扫的是 session 开跑那一刻的树内状态, 不受运行期改动影响。
    literal_hits, literal_unchecked = _hygiene_scan_tmp_literals()

    before = _hygiene_snapshot()
    yield
    after = _hygiene_snapshot()

    root = _hygiene_backend_root()
    violations: list[str] = []

    for rel in _HYGIENE_SKELETON_PATHS:
        if after["exists"][rel] and not before["exists"][rel]:
            violations.append(f"  新出现 vault 骨架: {root / rel}")

    for rel in _HYGIENE_TRACKED_FILES:
        if after["sha"][rel] != before["sha"][rel]:
            violations.append(
                f"  已入库文件被改写: {root / rel}\n"
                f"    before sha256={before['sha'][rel]}\n"
                f"    after  sha256={after['sha'][rel]}"
            )

    if literal_hits:
        violations.append(
            "  tests/unit 源码含硬编码 " + _TMP_LITERAL + " 路径 (本树写者会污染"
            "全机共享 /tmp;\n"
            "    Y6-A 已把它们改成 tmp_path, 重现 = 回归): " + ", ".join(literal_hits) + "\n"
            "    修法: 用 tmp_path fixture。"
        )

    if literal_unchecked:
        violations.append(
            "  源码字面量门**无法检查**以下文件 (「没命中」≠「没检查」, 不算通过):\n    "
            + "\n    ".join(literal_unchecked)
        )

    # /tmp 是全机共享的 ⇒ 不可归属 ⇒ 告警而不是 fail (手册 §四.5 D-27 (乙))。
    # ⛔ 禁再降成静默: 固定串「环境受干扰」是本卡的判据锚点。
    if before["tmp"] is not None and after["tmp"] is not None:
        new_tmp = sorted(after["tmp"] - before["tmp"])
        if new_tmp:
            warnings.warn(
                pytest.PytestWarning(
                    "[hygiene] 环境受干扰: 新出现 "
                    + _TMP_LITERAL
                    + "* 目录: "
                    + ", ".join(f"/tmp/{n}" for n in new_tmp)
                    + "\n    ⚠️ /tmp 是全机共享的: 本仓多 worktree 并行跑测试时, 别的车道"
                    "\n       跑 tests/unit 同样会产出这些目录 (本卡 2026-09-06 01:55 实测"
                    "\n       card-y9-maingoal 车道即如此)。判定归属请核对 `stat -f '%Sm' <路径>`"
                    "\n       与 `ps -ww -p <pid>` / `lsof -a -p <pid> -d cwd`, 而不是只看存在性。"
                    "\n    /tmp 全机共享、归属不可判 ⇒ 本 session **不判红** (Codex Y6-A HIGH #1);"
                    "\n    本树自身的写者由源码字面量门守, 那道门是硬 fail。"
                    "\n    这条告警 = 环境受干扰、需要重跑, **不是**本次运行新增的回归。"
                ),
                stacklevel=1,
            )

    if violations:
        pytest.fail(
            "tests/unit 运行污染了工作树 (CARD-TEST-hygiene-vaultinit 不变量门):\n"
            + "\n".join(violations)
            + "\n\n最可能的写者: 某个用例往 setup-wizard 端点传了**相对路径或空串**的"
            "\nvault_path (system.py 会 resolve() 成 cwd), 或直接给 VaultInitService"
            "\n传了非 tmp_path 的路径。修法: 测试一律用 tmp_path fixture。",
            pytrace=False,
        )


@pytest.fixture(autouse=True)
def _stub_vault_identity_registry(monkeypatch):
    """R10 P0-01 注册表引入后的单测隔离 (autouse).

    endpoint 型单测 (TestClient) 会走到 get_vault_identity_registry() —
    真实 registry 连真 Neo4j, 会把测试 vault 名认领进生产注册表 (实测
    污染过一次: test_vault_id_reaches_cypher_as_physical_group 把生产桶
    vault__canvas_vault 认领成了 'canvas_vault', 真插件发 'canvas-vault'
    将来必 409)。unit 层一律 stub 模块级 accessor 为 no-op。

    ⚠️ 只 patch get_vault_identity_registry() 函数, 不动
    VaultIdentityRegistry 类 — test_vault_identity_registry.py 直接
    实例化类 + fake driver, 不受影响; tests/integration/ 有独立
    conftest, 真注册表路径在那里验收。
    """

    class _NoopRegistry:
        async def assert_identity(self, *, raw_vault_id: str, physical_gid: str) -> None:
            return None

    import app.services.vault_identity_registry as vir

    monkeypatch.setattr(vir, "get_vault_identity_registry", lambda: _NoopRegistry())
    yield


@pytest.fixture
def mock_canvas_service():
    """Shared mock CanvasService for FSRS unit tests."""
    mock = MagicMock()
    mock.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})
    return mock


@pytest.fixture
def mock_task_manager():
    """Shared mock BackgroundTaskManager for FSRS unit tests."""
    mock = MagicMock()
    mock.submit_task = MagicMock(return_value="task_123")
    return mock


@pytest.fixture
def review_service_factory(mock_canvas_service, mock_task_manager):
    """Factory to create ReviewService with mocked dependencies."""

    def _create():
        from app.services.review_service import ReviewService

        return ReviewService(
            canvas_service=mock_canvas_service,
            task_manager=mock_task_manager,
        )

    return _create


@pytest.fixture
def review_service(review_service_factory):
    """Create ReviewService instance for testing."""
    return review_service_factory()


@pytest.fixture
def fallback_service(mock_canvas_service, mock_task_manager):
    """ReviewService with FSRS disabled (Ebbinghaus fallback mode).

    CARD-D3 Codex LOW-2: 构造会把模块全局 FSRS_RUNTIME_OK 置 False,
    yield 后恢复原值, 防止污染同 worker 随后的 health 类测试。
    """
    from app.services import review_service as rs_module
    from app.services.review_service import ReviewService

    prev_runtime_ok = rs_module.FSRS_RUNTIME_OK
    with patch("app.services.review_service.create_fsrs_manager", return_value=None):
        svc = ReviewService(
            canvas_service=mock_canvas_service,
            task_manager=mock_task_manager,
            fsrs_manager=None,
        )
    yield svc
    rs_module.FSRS_RUNTIME_OK = prev_runtime_ok
