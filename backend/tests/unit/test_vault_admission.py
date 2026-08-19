"""P1-05b: check_vault_path 统一准入函数的行为契约。

reason 枚举穷举 + 边界: 每个 slug 至少一个正/反例, 且判定必须作用于
vault **相对** parts (祖先目录免疫 — 本仓 worktree 位于 .claude/worktrees/ 下)。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.vault_admission import ADMISSION_REASONS, check_vault_path


@pytest.fixture
def vault(tmp_path) -> Path:
    root = tmp_path / "vault"
    (root / "节点").mkdir(parents=True)
    (root / "节点" / "a.md").write_text("x", encoding="utf-8")
    return root


def test_ok_relative_and_absolute_agree(vault):
    assert check_vault_path("节点/a.md", vault) == (True, "ok")
    assert check_vault_path(vault / "节点" / "a.md", vault) == (True, "ok")


def test_not_markdown(vault):
    (vault / "节点" / "a.txt").write_text("x", encoding="utf-8")
    assert check_vault_path("节点/a.txt", vault) == (False, "not_markdown")


def test_suffix_case_insensitive(vault):
    # .MD 是合法 markdown (后缀白名单 casefold)
    assert check_vault_path("节点/b.MD", vault) == (True, "ok")


def test_outside_vault_absolute(vault):
    assert check_vault_path("/etc/hosts.md", vault) == (False, "outside_vault")


def test_outside_vault_dotdot_escape(vault):
    assert check_vault_path("../escape.md", vault) == (False, "outside_vault")
    # 深层 ../ 链条同样折叠后判定
    assert check_vault_path("节点/../../escape.md", vault) == (False, "outside_vault")


def test_dotdot_that_stays_inside_is_ok(vault):
    # 词法折叠后仍在 vault 内 → 合法 (canonical 化后按真实位置判)
    assert check_vault_path("节点/../节点/a.md", vault) == (True, "ok")


def test_symlink_escape(vault, tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    link = vault / "节点" / "link.md"
    link.symlink_to(outside)

    assert check_vault_path("节点/link.md", vault) == (False, "symlink_escape")


def test_root_level_rejected(vault):
    (vault / "杂项.md").write_text("x", encoding="utf-8")
    assert check_vault_path("杂项.md", vault) == (False, "root_level")


def test_blacklisted_dir_hard_floor(vault, monkeypatch):
    """hostile env (只留 .git) 下检验白板仍被拦 — 硬底不可被 env 撤销。"""
    from app.config import settings as _singleton

    monkeypatch.setenv("VAULT_INDEX_SKIP_DIRS", ".git")
    monkeypatch.setattr(_singleton, "VAULT_INDEX_SKIP_DIRS", ".git")

    for bad in ["检验白板/exam.md", "验收单/uat.md", ".trash/x.md", ".claude/skills/s.md"]:
        ok, reason = check_vault_path(bad, vault)
        assert (ok, reason) == (False, "blacklisted_dir"), f"{bad} → {reason}"


def test_blacklisted_file(vault):
    for bad in ["节点/CLAUDE.md", "节点/图.excalidraw.md", "节点/UAT-测试.md"]:
        ok, reason = check_vault_path(bad, vault)
        assert (ok, reason) == (False, "blacklisted_file"), f"{bad} → {reason}"


def test_ancestor_dotdir_immunity(tmp_path):
    """vault 位于 .dotdir/ 下, 内部合法节点必须放行 — 判定只看相对 parts。"""
    root = tmp_path / ".claude" / "worktrees" / "wt" / "vault"
    (root / "节点").mkdir(parents=True)
    (root / "节点" / "a.md").write_text("x", encoding="utf-8")

    assert check_vault_path("节点/a.md", root) == (True, "ok")
    assert check_vault_path(root / "节点" / "a.md", root) == (True, "ok")


def test_all_reasons_are_declared():
    """本测试文件覆盖到的 reason 必须都在 ADMISSION_REASONS 枚举里 (拼写锁)。"""
    covered = {
        "ok",
        "not_markdown",
        "outside_vault",
        "symlink_escape",
        "root_level",
        "blacklisted_dir",
        "blacklisted_file",
    }
    assert covered == ADMISSION_REASONS
