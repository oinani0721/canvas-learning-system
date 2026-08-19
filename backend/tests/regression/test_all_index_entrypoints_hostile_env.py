"""所有记忆索引入口的 hostile env 契约锁 — P1-05（Codex 复核 2026-08-19）。

背景
----
上一轮把不可撤销硬底接进了 LanceDB 的两条索引路径 + orchestrator，但 Codex 复核
指出**还有一个入口完全没上锁**：

    vault_backfill.py:164-166  直接 split 原始 env 串 + 硬补 .obsidian/templates
    main.py:387-392            启动时以 execute=True 调用它

也就是说 hostile env 下，被漏过的 callout/error 会在**每次后端启动时**被写进
Graphiti 结构化图。这条比 LanceDB 更难收拾——图里的边要靠 `invalid_at` 失效，
不像 LanceDB 有 orphan sweep 自动收敛。

Codex 实测的 hostile env 结果（修复前）：

    .trash/deleted.md       allowed
    .quarantine/held.md     allowed
    .claude/private.md      allowed
    _bmad-output/audit.md   allowed
    检验白板/exam.md        blocked
    _待处理/inbox.md        blocked

本文件把**全部四个入口**放进同一张表逐一验证，确保没有第五个入口在暗处。

⛔ 不使用 mock：真实临时 vault 目录树 + 真实 monkeypatch.setenv + 真实
   pydantic Settings 解析 + 真实 backfill dry-run（execute=False）。
"""

from __future__ import annotations

import fnmatch
import shutil
import tempfile
from pathlib import Path

import pytest

from app.config import IMMUTABLE_VAULT_SKIP_DIRS, Settings

# 敌意配置：只留一项，试图撤掉全部安全边界
HOSTILE_ENV = ".git"

# 每个安全目录放一个带 callout 的 md —— callout 是 backfill 真正会回填进图的东西
SECURITY_SURFACES = [
    "检验白板/exam.md",
    "验收单/uat.md",
    "_待处理/inbox.md",
    "_archive/old.md",
    ".trash/deleted.md",
    ".quarantine/held.md",
    ".claude/private.md",
]

LEARNING_CONTENT = [
    "节点/recursion.md",
    "原白板/CS 61B.md",
]

_CALLOUT = "> [!tip]+ 测试批注\n> 这是一条会被 backfill 回填进 Graphiti 的内容\n"


@pytest.fixture
def hostile_vault(monkeypatch):
    """真实临时 vault + 敌意配置。

    ⛔ 必须 monkeypatch **单例属性**而不是只 setenv：`app.config.settings` 是
    模块级单例，`vault_backfill` 用 `from app.config import settings` 拿到的是
    已实例化对象 —— `setenv` 对它完全无效。首版只写了 setenv，导致 backfill
    读的仍是真实的 19 项默认黑名单，测试从头到尾没进入 hostile 场景（回退修复
    后行为断言依旧通过，暴露了这个空转）。
    """
    from app.config import settings as _singleton

    monkeypatch.setenv("VAULT_INDEX_SKIP_DIRS", HOSTILE_ENV)
    monkeypatch.setattr(_singleton, "VAULT_INDEX_SKIP_DIRS", HOSTILE_ENV)
    root = Path(tempfile.mkdtemp(prefix="p105-hostile-"))
    try:
        for rel in SECURITY_SURFACES + LEARNING_CONTENT:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"---\nsource_board: CS 61B\n---\n\n{_CALLOUT}", encoding="utf-8")
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _skip_dirs_under_hostile_env() -> list[str]:
    return Settings().effective_vault_skip_dirs()


def _blocked_by_dir_rule(rel_path: str, skip_dirs: list[str]) -> bool:
    return any(fnmatch.fnmatch(part, pat) for part in rel_path.split("/")[:-1] for pat in skip_dirs)


# ── 入口 1 + 2：LanceDB 全量 / 单文件（共用 skip_dirs） ────────────────────


@pytest.mark.parametrize("victim", SECURITY_SURFACES)
def test_entrypoint_lancedb_blocks_all_security_surfaces(hostile_vault, victim):
    skip_dirs = _skip_dirs_under_hostile_env()

    assert _blocked_by_dir_rule(victim, skip_dirs), f"LanceDB 入口在 hostile env 下放行了 {victim}"


@pytest.mark.parametrize("ok_path", LEARNING_CONTENT)
def test_entrypoint_lancedb_still_admits_learning_content(hostile_vault, ok_path):
    skip_dirs = _skip_dirs_under_hostile_env()

    assert not _blocked_by_dir_rule(ok_path, skip_dirs), f"硬底误伤学习内容 {ok_path}"


# ── 入口 3：orchestrator 准入门 ───────────────────────────────────────────


@pytest.mark.parametrize("victim", SECURITY_SURFACES)
def test_entrypoint_orchestrator_should_index_blocks(hostile_vault, victim):
    from app.services.vault_index_orchestrator import VaultIndexOrchestrator

    orch = VaultIndexOrchestrator.__new__(VaultIndexOrchestrator)
    orch._skip_dirs = _skip_dirs_under_hostile_env()

    ok, reason = orch.should_index(victim)

    assert ok is False, f"orchestrator 在 hostile env 下放行了 {victim} (reason={reason})"
    assert reason == "blacklisted_dir"


# ── 入口 4：Graphiti backfill（Codex 指出的漏网入口，启动时 execute=True） ──


@pytest.mark.asyncio
async def test_entrypoint_graphiti_backfill_blocks_all_security_surfaces(hostile_vault):
    """⛔ 本轮核心：backfill 此前直接 split 原始 env 串，绕过硬底。

    用真实 dry-run（execute=False，不碰图）验证：hostile env 下所有安全面的
    callout 都不被计入回填。
    """
    from app.services.vault_backfill import backfill_vault

    stats = await backfill_vault(
        str(hostile_vault),
        driver=None,  # execute=False 时不触碰
        embedder=None,
        group_id="vault__test",
        execute=False,
    )

    # 7 个安全面各有 1 条 callout；2 个学习内容各有 1 条。
    # 根级 md 本就被 len(rel_parts)==1 规则挡掉，这里全部放在子目录。
    assert stats["callouts"] == len(LEARNING_CONTENT), (
        f"backfill 在 hostile env 下多回填了 {stats['callouts'] - len(LEARNING_CONTENT)} 条 —— "
        f"安全面的 callout 漏进了 Graphiti 图层。stats={stats}"
    )


@pytest.mark.asyncio
async def test_backfill_uses_the_single_policy_source(hostile_vault, monkeypatch):
    """backfill 必须读 effective_vault_skip_dirs()，而非自己 split env 串。

    源码级锁：防止后来者"图省事"改回 split，重新打开这个入口。
    """
    import inspect

    from app.services import vault_backfill

    src = inspect.getsource(vault_backfill.backfill_vault)

    assert "effective_vault_skip_dirs" in src, "vault_backfill 未使用唯一策略源 —— 硬底对 Graphiti 写入口失效"
    assert "VAULT_INDEX_SKIP_DIRS" not in src or "split" not in src, (
        "vault_backfill 仍在自行 split 原始 env 串，绕过硬底"
    )


# ── 硬底完整性 ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("required", [".trash", ".quarantine", ".claude"])
def test_hard_floor_covers_p105_additions(required):
    """P1-05 复核补入的三项必须在硬底里。

    .claude 的理由值得单独记：它含 cache/board-manifest/ —— **E-2 脱敏过的快照
    本身就存在那里**。若 .claude 可被 env 撤销，E-2 的防护会从另一端失效。
    """
    assert required in IMMUTABLE_VAULT_SKIP_DIRS, f"{required} 不在不可撤销硬底，仍可被一行 env 撤销"


def test_all_entrypoints_agree_under_hostile_env(hostile_vault):
    """四入口判定一致性 —— 任何一个放行而其它拦截，都是新的旁路。"""
    from app.services.vault_index_orchestrator import VaultIndexOrchestrator

    skip_dirs = _skip_dirs_under_hostile_env()
    orch = VaultIndexOrchestrator.__new__(VaultIndexOrchestrator)
    orch._skip_dirs = skip_dirs

    for rel in SECURITY_SURFACES + LEARNING_CONTENT:
        lance = _blocked_by_dir_rule(rel, skip_dirs)
        orch_ok, _ = orch.should_index(rel)
        assert lance == (not orch_ok), (
            f"入口判定分歧: {rel} —— LanceDB blocked={lance}, orchestrator blocked={not orch_ok}"
        )
