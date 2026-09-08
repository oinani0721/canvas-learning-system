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
import os
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


def _hygiene_within_root(target: Path, root: Path) -> bool | None:
    """target 是否位于 root 之内。返回 True / False / None(无法判定)。

    为什么不能只用 `is_relative_to` (Codex round-2 MEDIUM, 实测):
        它做的是**字面**路径包含判断。本机文件系统大小写不敏感, 于是
        `tests/UNIT/conftest.py` 与 `tests/unit/conftest.py` 是同一个文件
        (`samefile` 为 True), 但 `resolve()` 保留调用方给的拼写, 字面比较
        得出 False ⇒ 合法的树内文件被判成越界 = 假红。

    做法: 先试字面包含 (快, 覆盖绝大多数情况); 不成立再逐级向上用
    `samefile` 做**文件系统身份**比对 (inode 级, 不受拼写影响)。
    比对本身失败 (权限 / 竞态换链 / 目标消失) 一律返回 None ——
    「问不出来」不能压成「在根外」, 也不能压成「在根内」。
    """
    try:
        if target.is_relative_to(root):
            return True
    except (OSError, ValueError):
        return None

    try:
        current = target.parent
        while True:
            if current.samefile(root):
                return True
            parent = current.parent
            if parent == current:  # 走到文件系统根仍未命中
                return False
            current = parent
    except OSError:
        return None


def _hygiene_scan_tmp_literals() -> tuple[list[str], list[str]]:
    """扫 tests/unit/**/*.py 里硬编码的 `/tmp/` + `test-vault` 字符串常量。

    **只读**: 只 scandir + read_bytes + ast.parse。不创建 / 不删除 / 不写入任何
    文件, 不 import 被扫文件, 不依赖 cwd (扫描根走 __file__, 与门盯 backend/ 同理)。

    为什么必须走 AST 而不是 grep 全文:
    - `test_startup_health_check.py:56-66` 有三条 `#` 注释记录 Y6-A 改前的旧
      硬编码值 —— grep 会把这些注释判成回归 (假红);
    - 本文件自己的告警文案也含同一段路径 —— grep 形态的门必然自指。
    AST 只看 `ast.Constant` 字符串, 两个假红面同时消失。

    为什么用 `os.walk(onerror=...)` 而不是 `Path.rglob`
    (Codex round-1 HIGH #1, 实测):
        `Path.rglob` 在**遍历期**抑制 `PermissionError` —— 目录枚举被拒时它
        安静地少产出文件, 于是本函数返回 `([], [])` = 「无命中、无检查失败」,
        正是这道门自己声称要杜绝的假绿。外层再包 `try` 也够不着, 因为异常
        在 `rglob` 内部就被吞了。`os.walk` 的 `onerror` 回调是唯一能把这类
        失败报出来的钩子; `followlinks=False` (默认) 同时挡住目录符号链接
        把扫描面拐出树外。

    ⚠️ **本门证明的是「源码里没有这种硬编码常量」, 不是「本树没有 /tmp 写者」。**
    判据只是「某个 `str` 类型的 `ast.Constant` 含连续子串 `_TMP_LITERAL`」,
    以下形态**一律漏检** (Codex round-1 HIGH #2 逐条实测, 不是穷举):
      - 路径运算分段:      `Path("/tmp") / ("test-vault-" + x)`
      - 运行期拼接:        `"/tmp/" + name`、`os.path.join("/tmp", "test-vault…")`
      - 前缀被**拆开**的 f-string (⚠️ 前缀完整的 f-string 反而**会**命中, 不是漏检)
      - 等价但不同写法的路径: `"/tmp//test-vault-x"`、`"/tmp/./test-vault-x"`
        (`/tmp/` 后面不紧跟 `t`, 连续子串就不成立)
      - `bytes` 字面量 (同一段路径但带 `b` 前缀): 被 `isinstance(..., str)` 排除
      - API 分参数:        `tempfile.mkdtemp(prefix="test-vault-", dir="/tmp")`
      - cwd 恰为 `/tmp` 时的相对路径 `"test-vault-x"`
      - 值来自环境变量 / 配置 / 扫描面之外的模块
    另: 本文件**整体**被排除 (见下), 故本文件其他 fixture 里将来出现的完整
    硬编码路径同样漏检。要覆盖这些需要数据流分析, 明确不在本卡范围。

    返回 (hits, unchecked):
      hits      —— "<file>:<lineno>", 源码里可归属到**本 worktree** 的硬编码常量;
      unchecked —— 目录枚举失败 / 读不了 / 解析不了 / 符号链接越界的条目。
                   **不算通过**:「没命中」与「没检查」必须分开, 否则一个权限
                   坏掉的子目录就能让门静默放行。
    """
    self_path = Path(__file__).resolve()
    scan_root = self_path.parent

    hits: list[str] = []
    unchecked: list[str] = []

    def _on_walk_error(exc: OSError) -> None:
        target = getattr(exc, "filename", None) or "<未知路径>"
        unchecked.append(f"{target} (目录枚举失败: {type(exc).__name__}: {exc})")

    for dirpath, dirnames, filenames in os.walk(scan_root, onerror=_on_walk_error):
        dirnames.sort()
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            py = Path(dirpath) / name

            try:
                resolved = py.resolve()
            except OSError as exc:
                unchecked.append(f"{py} (路径解析失败: {type(exc).__name__}: {exc})")
                continue

            if resolved == self_path:
                continue

            # 符号链接越界 (Codex round-1 MEDIUM): 树内的 *.py 若链到扫描根之外,
            # read_bytes() 会读到扫描根外的内容,「信号都在本 worktree 内」这句
            # 声明就不成立了。报边界不符, 不当普通树内源码读, 也不静默跳过。
            within = _hygiene_within_root(resolved, scan_root)
            if within is False:
                unchecked.append(f"{py} (链接目标在扫描根之外: {resolved}; 扫描根 = {scan_root})")
                continue
            if within is None:
                unchecked.append(f"{py} (无法判定链接目标是否在扫描根内: {resolved})")
                continue

            try:
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

    ⚠️ 降级只发生在**不可归属**这一侧, 不是「放松要求」: 本树源码里
    **硬编码**的 test-vault* 路径常量仍然硬红 —— 那是新增源码字面量门的职责。
    ⚠️ 但它是**源码规则门**, 不是写入归属证明: 它只看字符串常量, 对路径运算 /
    bytes / tempfile 参数 / 相对路径等形态看不见 (Codex round-1 HIGH #2)。
    所以告警文案只说「归属未知, 请核查或重跑」, **不**说「不是本次新增的回归」。
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

    # 三类信号分开收集 (Codex round-2 HIGH #1)。它们的**语义不同**, 不能共用
    # 一句「运行污染了工作树」和同一份写者推定:
    #   pollution   —— 首尾快照真的变了, 本次运行确实写了东西;
    #   source_rule —— 源码里有硬编码常量, 是**静态**规则, 不表示本次跑写了什么
    #                  (P1 正控用的就是一个从不执行的常量);
    #   cannot_check—— 既没通过也没违规, 门拒绝把「没检查」当「没问题」。
    pollution: list[str] = []
    source_rule: list[str] = []
    cannot_check: list[str] = []

    for rel in _HYGIENE_SKELETON_PATHS:
        if after["exists"][rel] and not before["exists"][rel]:
            pollution.append(f"  新出现 vault 骨架: {root / rel}")

    for rel in _HYGIENE_TRACKED_FILES:
        if after["sha"][rel] != before["sha"][rel]:
            pollution.append(
                f"  已入库文件被改写: {root / rel}\n"
                f"    before sha256={before['sha'][rel]}\n"
                f"    after  sha256={after['sha'][rel]}"
            )

    if literal_hits:
        source_rule.extend(f"  {h}" for h in literal_hits)

    if literal_unchecked:
        cannot_check.extend(f"  {u}" for u in literal_unchecked)

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
                    "\n    /tmp 全机共享 ⇒ **归属未知**: 可能来自本 session, 也可能来自任何"
                    "\n    别的进程 (Codex Y6-A HIGH #1: mtime / ps / lsof 都不能单独证明历史"
                    "\n    写入归属)。⇒ 本 session **不判红**, 但**请核查或重跑**, 不要直接"
                    "\n    当成「别人弄的」。"
                    "\n    本树源码里的硬编码写者另有源码字面量门守 (硬 fail), 但那道门只看"
                    "\n    字符串常量 —— 路径运算 / bytes / tempfile 参数 / 相对路径 等形态它"
                    "\n    看不见, 所以它不能证明本树没有写者。盲区清单见 _hygiene_scan_tmp_literals 的 docstring。"
                ),
                stacklevel=1,
            )

    sections: list[str] = []

    if pollution:
        sections.append(
            "【工作树被写坏】以下变化发生在本次 session 首尾两次快照之间, "
            "即本次运行确实写了东西:\n"
            + "\n".join(pollution)
            + "\n  最可能的写者: 某个用例往 setup-wizard 端点传了**相对路径或空串**的"
            "\n  vault_path (system.py 会 resolve() 成 cwd), 或直接给 VaultInitService"
            "\n  传了非 tmp_path 的路径。修法: 测试一律用 tmp_path fixture。"
        )

    if source_rule:
        sections.append(
            "【源码规则命中】tests/unit 源码里有硬编码的 "
            + _TMP_LITERAL
            + " 路径常量:\n"
            + "\n".join(source_rule)
            + "\n  ⚠️ 这是**静态**规则, **不表示本次运行写了任何东西** —— 它拦的是"
            "\n  「将来会往全机共享 /tmp 写」。Y6-A 已把这类路径改成 tmp_path,"
            "\n  重新出现即回归。修法: 用 tmp_path fixture。"
        )

    if cannot_check:
        sections.append(
            "【检查无法完成】以下目标既没通过也没违规 —— 门拒绝把「没检查」"
            "当成「没问题」:\n"
            + "\n".join(cannot_check)
            + "\n  ⚠️ 这**不是**已经发生写入的证据, 只是这道门这次没能看全。"
            "\n  多半是权限 / 符号链接 / 语法错误。恢复可见性后重跑。"
        )

    if sections:
        pytest.fail(
            "tests/unit 卫生门未通过 "
            "(CARD-TEST-hygiene-vaultinit + CARD-HYGIENE-conftest):\n\n" + "\n\n".join(sections),
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
