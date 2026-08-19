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

本文件把**全部文件扫描入口**放进同一张表逐一验证，确保没有下一个入口在暗处：

    1+2  LanceDB 全量 / 单文件         5  canvas_projection_sync（CANVAS_EDGE）
    3    orchestrator should_index     6  relationship_sync vault 全量
    4    Graphiti backfill             7  relationship_sync by-node（含四类路径反例）
                                       8  error_rebuild _scan_vault_md_files

P1-05b（2026-08-19）：5-8 是 Codex 二轮复核点名的四条漏网活链，全部收口到
app.core.vault_admission.check_vault_path（唯一准入函数）。

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

# P1-05b: 每个文件带一条 relationships — 让 projection sync / relationship sync
# 两条边写入链也有真实原料 (检验白板的 relationship 变成 CANVAS_EDGE.label 就是
# 出题链泄漏)。backfill 的 callouts 计数不受影响。
_FRONTMATTER = (
    "---\n"
    "source_board: CS 61B\n"
    "relationships:\n"
    "  - type: prerequisite\n"
    '    target: "[[other-node]]"\n'
    "    description: 准入契约测试关系\n"
    "---\n\n"
)

#: vault 根级直下的杂项 md — 不属任何黑名单模式, 专门验证 root_level 规则
ROOT_NOISE = "根级杂项.md"


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
        for rel in SECURITY_SURFACES + LEARNING_CONTENT + [ROOT_NOISE]:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"{_FRONTMATTER}{_CALLOUT}", encoding="utf-8")
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
    fn_src = inspect.getsource(vault_backfill.is_blacklisted_for_backfill)

    # P1-05c: 唯一策略源升级为 check_vault_path (其内部消费
    # effective_vault_skip_dirs + 文件名黑名单 + 归一 + containment)
    assert "is_blacklisted_for_backfill" in src, "backfill 未走统一判定函数"
    assert "check_vault_path" in fn_src, (
        "is_blacklisted_for_backfill 未委托 check_vault_path —— 私有规则复活 (Codex 三轮 F-01b)"
    )
    assert "VAULT_INDEX_SKIP_DIRS" not in src or "split" not in src, (
        "vault_backfill 仍在自行 split 原始 env 串，绕过硬底"
    )


@pytest.mark.asyncio
async def test_backfill_blocks_blacklisted_filenames_in_subdirs(hostile_vault):
    """P1-05c (Codex 三轮 F-01b 实锤): backfill 旧判定缺文件名黑名单 —
    raw/CLAUDE.md 的 callout 曾被计入待写 (dry-run callouts 含它)。"""
    from app.services.vault_backfill import backfill_vault

    (hostile_vault / "raw").mkdir(exist_ok=True)
    (hostile_vault / "raw" / "CLAUDE.md").write_text(f"{_FRONTMATTER}{_CALLOUT}", encoding="utf-8")

    stats = await backfill_vault(str(hostile_vault), driver=None, embedder=None, group_id="vault__test", execute=False)

    assert stats["callouts"] == len(LEARNING_CONTENT), f"backfill 仍放行子目录黑名单文件名的 callout: stats={stats}"


def test_orchestrator_rejects_dotdot_traversal(hostile_vault):
    """P1-05c (F-01b): orchestrator 此前对 '../outside.md' 返回 (True,'ok')。"""
    from app.services.vault_index_orchestrator import VaultIndexOrchestrator

    orch = VaultIndexOrchestrator.__new__(VaultIndexOrchestrator)
    orch._skip_dirs = _skip_dirs_under_hostile_env()

    assert orch.should_index("../outside.md") == (False, "outside_vault")
    assert orch.should_index("节点/../../escape.md") == (False, "outside_vault")
    # root_level 是检索面与图写入面的 by-design 分歧: orchestrator 放行根级
    # 用户笔记 (由根级文件名黑名单管), check_vault_path 拒 — 显式锁住该分歧
    assert orch.should_index("根级笔记.md")[0] is True


def test_lancedb_single_file_judges_before_read():
    """P1-05c (F-01b): index_single_file 黑名单判定必须在读正文之前 (源码序锁)。"""
    import inspect

    from agentic_rag.clients.lancedb_client import LanceDBClient

    src = inspect.getsource(LanceDBClient.index_single_file)
    assert src.index("_is_skipped_vault_file(rel_path") < src.index('open(file_path, "r"'), (
        "单文件路径仍先读正文后判黑名单 — 禁区文件正文不该被读进进程"
    )


# ── 硬底完整性 ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("required", [".trash", ".quarantine", ".claude"])
def test_hard_floor_covers_p105_additions(required):
    """P1-05 复核补入的三项必须在硬底里。

    .claude 的理由（P1-05b 勘误 2026-08-19）：它含 hooks（可执行）/ settings
    （可能含 key）/ SKILL.md（是 .md，会被 Markdown 扫描器实际扫到）。首版写的
    "快照 JSON 会被索引"是错的 —— 扫描器只收 .md，JSON 本就不在扫描面。
    """
    assert required in IMMUTABLE_VAULT_SKIP_DIRS, f"{required} 不在不可撤销硬底，仍可被一行 env 撤销"


def test_all_entrypoints_agree_under_hostile_env(hostile_vault):
    """多入口判定一致性 —— 任何一个放行而其它拦截，都是新的旁路。

    P1-05b: 统一准入函数 check_vault_path 也纳入同一致性面（对子目录路径，
    它与 LanceDB 目录规则 / orchestrator 必须同判）。
    """
    from app.core.vault_admission import check_vault_path
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
        adm_ok, adm_reason = check_vault_path(hostile_vault / rel, hostile_vault)
        assert lance == (not adm_ok), (
            f"入口判定分歧: {rel} —— LanceDB blocked={lance}, "
            f"check_vault_path blocked={not adm_ok} (reason={adm_reason})"
        )


# ── 入口 5：canvas_projection_sync（CANVAS_EDGE 原因边 — label 直通出题链） ──


@pytest.mark.asyncio
async def test_entrypoint_projection_sync_blocks_all_security_surfaces(hostile_vault):
    """rglob 链此前**完全无过滤** —— 检验白板的 relationships 会 MERGE 成
    CANVAS_EDGE.label，经 question_generator._get_edge_reasons 直通出题上下文。
    dry-run（execute=False）不碰 Neo4j，行为断言全部来自真实文件扫描。"""
    from app.services.canvas_projection_sync import CanvasProjectionSync

    svc = CanvasProjectionSync()
    result = await svc.sync(str(hostile_vault), group_id="vault:test", execute=False)

    assert result["edges_synced"] == len(LEARNING_CONTENT), (
        f"projection sync 在 hostile env 下多写了 "
        f"{result['edges_synced'] - len(LEARNING_CONTENT)} 条边 —— "
        f"安全面的 relationship 漏进 CANVAS_EDGE。result={result}"
    )
    assert result["nodes_with_relationships"] == len(LEARNING_CONTENT)
    # 7 个安全面 + 1 个根级杂项, 全部被准入拒绝
    assert result["files_skipped_admission"] == len(SECURITY_SURFACES) + 1


@pytest.mark.asyncio
async def test_projection_sync_dry_run_never_touches_neo4j(hostile_vault):
    from app.services.canvas_projection_sync import CanvasProjectionSync

    svc = CanvasProjectionSync()
    await svc.sync(str(hostile_vault), group_id="vault:test", execute=False)

    assert svc._neo4j is None, "dry-run（execute=False）不得创建 Neo4j client"


def test_main_startup_projection_sync_declares_execute_true():
    """源码级锁：sync() 默认已改 dry-run，启动链必须显式 execute=True 才真写。"""
    import inspect

    from app import main

    src = inspect.getsource(main)
    segments = src.split("rel_svc.sync(")
    assert len(segments) == 2, "main.py 启动链应恰好调用一次 rel_svc.sync"
    assert "execute=True" in segments[1][:300], "启动链未显式声明写意图 execute=True"


# ── 入口 6：relationship_sync vault 全量 ────────────────────────────────────


@pytest.mark.asyncio
async def test_entrypoint_relationship_vault_scan_blocks(hostile_vault):
    """此前用模块私有 SKIP_DIRS（缺检验白板/验收单/_待处理/_archive 四个铁律目录）。"""
    from app.services.relationship_sync_service import sync_relationships_in_vault

    result = await sync_relationships_in_vault(hostile_vault, dry_run=True)

    assert result["files_scanned"] == len(LEARNING_CONTENT), (
        f"relationship vault 扫描在 hostile env 下扫了 {result['files_scanned']} 个文件 "
        f"（应只剩学习内容 {len(LEARNING_CONTENT)} 个）"
    )
    assert result["total_synced"] == len(LEARNING_CONTENT)


# ── 入口 7：relationship_sync by-node（唯一接受任意字符串路径的写入口） ──────


class _CaptureEdgeClient:
    def __init__(self):
        self.calls = []

    async def add_edge_relationship(self, edge):
        self.calls.append(edge)
        return True


@pytest.mark.asyncio
async def test_entrypoint_by_node_rejects_hostile_paths(hostile_vault, tmp_path):
    """四类路径反例：绝对路径 / `../` 上跳 / vault 外真实文件 / symlink 逃逸。

    此前这些全部放行 —— relative_to 的 fallback 只是换显示格式，不拒绝。
    """
    from app.services.relationship_sync_service import sync_relationships_for_note

    real_outside = tmp_path / "real.md"
    real_outside.write_text(
        '---\nrelationships:\n  - type: uses\n    target: "[[x]]"\n---\n',
        encoding="utf-8",
    )
    link = hostile_vault / "节点" / "link-escape.md"
    link.symlink_to(real_outside)

    attacks = {
        "绝对路径": "/etc/hosts.md",
        "../上跳": "../outside/real.md",
        "vault外真实文件": str(real_outside),
        "symlink逃逸": "节点/link-escape.md",
    }
    for label, attack in attacks.items():
        cap = _CaptureEdgeClient()
        result = await sync_relationships_for_note(attack, hostile_vault, group_id="vault:test", edge_client=cap)
        assert result["synced"] == 0, f"{label} 未被拒绝: {attack}"
        assert result["errors"] and result["errors"][0].startswith("path_rejected:"), (
            f"{label} 应返回 path_rejected:* — got {result}"
        )
        assert cap.calls == [], f"{label} 竟然写入了 edge!"


@pytest.mark.asyncio
async def test_entrypoint_by_node_admits_legit_note(hostile_vault):
    """正向对照：合法节点路径必须照常同步（防御不能顺手把正门也焊死）。"""
    from app.services.relationship_sync_service import sync_relationships_for_note

    cap = _CaptureEdgeClient()
    result = await sync_relationships_for_note(
        "节点/recursion.md", hostile_vault, group_id="vault:test", edge_client=cap
    )
    assert result["synced"] == 1
    assert len(cap.calls) == 1


# ── 入口 8：error_rebuild _scan_vault_md_files ──────────────────────────────


def test_entrypoint_error_rebuild_scan_respects_admission(hostile_vault):
    """主分支（节点/*.md）也过准入：节点/CLAUDE.md 属文件名黑名单必须被拒。"""
    from app.services.error_rebuild_service import _scan_vault_md_files

    (hostile_vault / "节点" / "CLAUDE.md").write_text("---\nerrors: []\n---\n", encoding="utf-8")

    files = _scan_vault_md_files(hostile_vault)
    rels = sorted(str(f.relative_to(hostile_vault)) for f in files)
    assert rels == ["节点/recursion.md"], f"error_rebuild 扫描面异常: {rels}"


def test_entrypoint_error_rebuild_root_fallback_rejected(tmp_path):
    """fallback 扫根级是 Codex 复核点名的旁路 —— 根级 md 一律 root_level 拒绝。"""
    from app.services.error_rebuild_service import _scan_vault_md_files

    (tmp_path / "x.md").write_text("x", encoding="utf-8")

    assert _scan_vault_md_files(tmp_path) == []


# ── 祖先目录免疫（三处既有 bug 的反例：vault 位于 .dotdir/ 下） ─────────────


@pytest.mark.asyncio
async def test_ancestor_dotdir_vault_not_zeroed_out(tmp_path):
    """vault 位于 .dotdir/ 下时扫描结果必须非零。

    修复前 relationship_sync / error_reader 对**绝对** parts 判 startswith('.')，
    祖先目录命中 → 整个 vault 静默零扫描。这不是假想场景：本仓 worktree 的
    vault 就位于 `.claude/worktrees/feature-obsidian-hybrid-dev/` 下。
    """
    vault = tmp_path / ".dotdir" / "vault"
    (vault / "节点").mkdir(parents=True)
    (vault / "节点" / "n1.md").write_text(
        "---\n"
        "relationships:\n"
        '  - type: prerequisite\n    target: "[[n2]]"\n'
        "errors:\n"
        "  - id: e1\n    type: concept_confusion\n    last_seen_at: '2026-08-19T00:00:00'\n"
        "---\n",
        encoding="utf-8",
    )

    from app.services.relationship_sync_service import sync_relationships_in_vault

    result = await sync_relationships_in_vault(vault, dry_run=True)
    assert result["files_scanned"] == 1, "祖先 .dotdir 让 relationship_sync 零扫描"

    from app.services.error_reader import query_errors_by_type

    matched = await query_errors_by_type(vault, "concept_confusion")
    assert len(matched) == 1, "祖先 .dotdir 让 error_reader 零扫描"
