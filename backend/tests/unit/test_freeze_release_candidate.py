# ⚠️ CARD-R-RC (BATCH-2026-09-18-第十五批) — clean RC 冻结脚本的裁判
#
# 被测物: backend/scripts/freeze_release_candidate.py
# 上游契约 (本卡零改动, 只证明冻结件与它们对得上):
#   - docs/release-evidence/manifest.schema.json: candidate.sha 正则 / dirty / worktree,
#     environment.index_sha 与 index_sha_null_reason 的「禁止省略字段冒充无关」
#   - backend/scripts/validate_release_manifest.py: _RC_NAME_RE / EVIDENCE_ROOT /
#     discover_manifests / check_rc_completeness / CLI 退出码三档
#
# 本文件**完全自足** (只用 stdlib + pytest), 可用
#   python -m pytest backend/tests/unit/test_freeze_release_candidate.py --noconftest -q
# 单独跑 —— 与 test_validate_release_manifest.py / test_check_readme_claims.py 同口径。
#
# DD-03 禁 mock 的落地形态: 每条用例在 tmp_path 里 `git init` 出**真 git 仓**, 用
# subprocess 跑**真脚本**, 脚本内部再 subprocess 真调校验器。全文件 0 处 monkeypatch、
# 0 处 mock/打桩、0 个 autouse fixture、0 处 `from app`。
#
# ⚠️ 真实耦合如实声明: `freeze` 会真调本仓校验器的 `--all`, 而 `--all` 的扫描根被校验器
# 自己钉死在**本仓** `docs/release-evidence/` (不随 --repo / --out-root 变)。因此
# `validator.all_exit_code == 0` 这条断言同时依赖「本仓既有证据树自洽」。这不是打桩能绕开
# 的耦合, 而正是本卡「骨架不得让既有证据树失自洽」这条要求的判据本身。
#
# 钉死点:
#   1. dirty 门: 未跟踪 / 已跟踪改动两态都拒, 且**零写入** (out-root 本身不得被建出来)
#   2. 没有任何跳过开关: 源码里 0 处 "allow-dirty" 字面量
#   3. candidate.sha = 冻结当刻 `rev-parse HEAD` 的完整 40 位, 与 schema 正则同形
#   4. 双树消歧: linked worktree 与主仓两态的 worktree_rel_to_main / is_linked_worktree
#   5. 依赖锁恰两项、缺一即拒 (不写 null 冒充「无锁」)
#   6. 索引 SHA 值与 null 理由互斥必给一 (镜像 schema 的「禁止省略字段冒充无关」)
#   7. 一个 SHA 一个 rc: 同落点重冻结被拒, 且原件字节不变
#   8. rc 名正则与校验器 _RC_NAME_RE 逐字同 (脚本自带字面量, 不 import 校验器)
#   9. check 逐份 journey 比对 candidate.sha, 不做「至少一份一致」
#  10. 骨架文件名 rc-manifest.json 不进校验器 rglob("manifest.json") 的扫描面
#  11. dirty 门的**已知盲区** (.gitignore 忽略面) 由用例如实钉住, 不假装覆盖

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
_REPO_ROOT = _SCRIPTS_DIR.parents[1]
_FREEZE = _SCRIPTS_DIR / "freeze_release_candidate.py"

_LOCK_RELS = ("backend/requirements.txt", "frontend/obsidian-plugin/package-lock.json")
_NULL_REASON = ("--index-sha-null-reason", "裁判用 tmp 仓, 不涉检索索引")
_SHA_RE = re.compile(r"^(?!0{40}$)[0-9a-f]{40}$")
_OFFSET_RE = re.compile(r"T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)$")
_OTHER_SHA = "b" * 40
# 退出码前缀: 只有被测脚本会打这两个标记。exit 2 这档必须靠标记认身份 ——
# 光看 returncode==2 的话, 「脚本压根不存在」也退 2, 判据会在空仓上假绿。
_ENV_MARK = "⛔ [env]"
_REJECT_MARK = "⛔ [reject]"

_EXPECTED_TOP_KEYS = {
    "rc_manifest_version",
    "rc",
    "frozen_at",
    "candidate",
    "trees",
    "dependency_locks",
    "index_sha",
    "index_sha_null_reason",
    "ci_run_id",
    "ci_run_id_null_reason",
    "validator",
    "journeys_expected",
    "environment",
    "notes",
}


# ─────────────────────────────────────────────────────────── 真 git 仓夹具


def _git(root: Path, *args: str) -> str:
    """真调 git (照 test_check_readme_claims.py 的 helper 形态), 失败即抛。"""
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _commit(root: Path, message: str) -> None:
    _git(
        root,
        "-c",
        "user.email=t@x",
        "-c",
        "user.name=t",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-q",
        "-m",
        message,
    )


def _init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q")
    # 不依赖 `git init -b` (需 git>=2.28): 建完再把当前分支改名, 老 git 也走得通。
    _git(root, "symbolic-ref", "HEAD", "refs/heads/main")


def _seed_locks(root: Path) -> None:
    bodies = {
        _LOCK_RELS[0]: "pytest==8.0.0\njsonschema==4.26.0\n",
        _LOCK_RELS[1]: '{"name": "p", "lockfileVersion": 3}\n',
    }
    for rel, body in bodies.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    _git(root, "add", "-A")
    _commit(root, "base: dependency locks")


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """tmp_path 下的真 git 仓, 两个依赖锁已提交, 工作树干净。非 autouse。"""
    root = tmp_path / "code"
    _init_repo(root)
    _seed_locks(root)
    return root


# ─────────────────────────────────────────────────────────── 跑脚本


def _run(repo_root: Path, *argv: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    run_env = dict(os.environ)
    # 宿主若正好在 CI 里跑, 继承来的 GITHUB_RUN_ID 会让「都无 ⇒ null」那条变不确定。
    run_env.pop("GITHUB_RUN_ID", None)
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, str(_FREEZE), *argv],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
        env=run_env,
    )


def _freeze(
    repo_root: Path,
    out_root: Path,
    *extra: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return _run(
        repo_root,
        "freeze",
        "--repo",
        str(repo_root),
        "--out-root",
        str(out_root),
        *extra,
        env=env,
    )


def _only_rc_dir(out_root: Path) -> Path:
    children = sorted(p for p in out_root.iterdir() if p.is_dir())
    assert len(children) == 1, f"期望 out-root 下恰一个 rc 目录, 实得 {children}"
    return children[0]


def _manifest(rc_dir: Path) -> dict:
    return json.loads((rc_dir / "rc-manifest.json").read_text(encoding="utf-8"))


def _both(proc: subprocess.CompletedProcess[str]) -> str:
    return proc.stdout + proc.stderr


# ─────────────────────────────────────────────────────────── 1-2 dirty 门


def test_dirty_untracked_refused_exit_1_zero_write(repo: Path, tmp_path: Path) -> None:
    """未跟踪文件也算脏 (--untracked-files=all), 且拒绝路径上 out-root 根本不该被建出来。"""
    out_root = tmp_path / "out"
    (repo / "stray-note.txt").write_text("未提交的草稿\n", encoding="utf-8")

    proc = _freeze(repo, out_root, *_NULL_REASON)

    assert proc.returncode == 1, _both(proc)
    assert _REJECT_MARK in _both(proc), _both(proc)
    # ⚠️ 锚必须是 `dirty tree` 这个**只有主门会说的短语**, 不能是裸 "dirty" ——
    # 脚本通过主门之后会打印四条 `ℹ️ dirty 门覆盖面: …` caveat, 裸 "dirty" 会被那些
    # 说明文字满足(负控 N10 实测: 主门被变异掉后本条仍因此少红一半)。
    assert "dirty tree" in _both(proc), _both(proc)
    assert "stray-note.txt" in _both(proc), "应打印脏条目, 否则人不知道该提交什么"
    # 零写入: 不是「目录存在但空」, 是**目录不存在**。
    assert not out_root.exists(), f"拒绝路径留下了写入痕迹: {sorted(out_root.rglob('*'))}"


def test_dirty_modified_tracked_refused(repo: Path, tmp_path: Path) -> None:
    """已跟踪文件改了没提交同样拒 —— 与未跟踪面各拆一层。"""
    out_root = tmp_path / "out"
    (repo / _LOCK_RELS[0]).write_text("pytest==9.9.9\n", encoding="utf-8")

    proc = _freeze(repo, out_root, *_NULL_REASON)

    assert proc.returncode == 1, _both(proc)
    assert _REJECT_MARK in _both(proc), _both(proc)
    assert "dirty tree" in _both(proc), _both(proc)  # 同上: 不用裸 "dirty"
    assert "requirements.txt" in _both(proc), "应列出是哪个已跟踪文件脏了"
    assert not out_root.exists()


# ─────────────────────────────────────────────────────────── 3 干净态冻结


def test_clean_freeze_writes_manifest_and_skeleton(repo: Path, tmp_path: Path) -> None:
    out_root = tmp_path / "out"
    proc = _freeze(repo, out_root, *_NULL_REASON)
    assert proc.returncode == 0, _both(proc)

    rc_dir = _only_rc_dir(out_root)
    doc = _manifest(rc_dir)

    # —— 骨架
    assert (rc_dir / "journeys" / ".gitkeep").is_file(), "空 journeys/ 进不了 git, 需 .gitkeep"
    assert list(rc_dir.rglob("manifest.json")) == [], (
        "骨架不得落下任何 manifest.json —— 校验器 discover_manifests 只 rglob 这个名字, "
        "冻结件叫 rc-manifest.json 正是为了不改变 --all 的结果"
    )

    # —— 键集固定
    assert set(doc) == _EXPECTED_TOP_KEYS
    assert doc["rc_manifest_version"] == "1.0.0"

    # —— candidate
    head = _git(repo, "rev-parse", "HEAD")
    cand = doc["candidate"]
    assert cand["sha"] == head
    assert _SHA_RE.fullmatch(cand["sha"]), "须是 schema 认的完整 40 位小写 hex 且非全零"
    assert cand["branch"] == _git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert cand["detached"] is False
    assert cand["dirty"] is False
    assert Path(cand["worktree"]) == repo.resolve()

    # —— rc 名
    assert doc["rc"] == rc_dir.name
    assert re.fullmatch(r"^[A-Za-z0-9._-]{1,64}$", doc["rc"])
    assert head[:8] in doc["rc"], "默认 rc 名须带 sha 前缀, 否则同日两次冻结会撞名"

    # —— frozen_at 带时区偏移 (身份判据: 只认时间段之后的偏移, 不被日期里的 '-' 蒙混)
    assert _OFFSET_RE.search(doc["frozen_at"]), doc["frozen_at"]

    # —— 依赖锁恰两项且 sha256 逐字同
    locks = doc["dependency_locks"]
    assert [item["path"] for item in locks] == list(_LOCK_RELS)
    for item in locks:
        raw = (repo / item["path"]).read_bytes()
        assert item["sha256"] == hashlib.sha256(raw).hexdigest()
        assert item["bytes"] == len(raw)

    # —— 索引 / CI
    assert doc["index_sha"] is None
    assert doc["index_sha_null_reason"] == _NULL_REASON[1]
    assert doc["ci_run_id"] is None
    assert doc["ci_run_id_null_reason"]

    # —— 校验器真调
    assert doc["validator"]["all_exit_code"] == 0, _both(proc)
    assert doc["validator"]["require_complete"] is None, (
        "out-root 在校验器证据根之外时 --require-complete 看不见本 rc, 须记 null + 理由"
    )
    assert doc["validator"]["require_complete_skip_reason"]
    assert doc["journeys_expected"] == [f"J{i:02d}" for i in range(1, 11)]

    # —— 校验器 stdout 原样透传给裁判
    assert "PASS" in proc.stdout


# ─────────────────────────────────────────────────────────── 4 重冻结


def test_rerun_same_rc_refused(repo: Path, tmp_path: Path) -> None:
    out_root = tmp_path / "out"
    first = _freeze(repo, out_root, *_NULL_REASON, "--rc-name", "rc-fixed")
    assert first.returncode == 0, _both(first)
    before = (out_root / "rc-fixed" / "rc-manifest.json").read_bytes()

    second = _freeze(repo, out_root, *_NULL_REASON, "--rc-name", "rc-fixed")

    assert second.returncode == 1, _both(second)
    assert _REJECT_MARK in _both(second), _both(second)
    assert "落点已存在" in _both(second), (
        "须红在「落点已存在」这道守卫上 —— 删掉它之后未捕获的 FileExistsError 同样退 1、"
        "同样发生在写文件之前, 光看 rc 与字节不变区分不出来(独立审查变异实测)"
    )
    assert (out_root / "rc-fixed" / "rc-manifest.json").read_bytes() == before, "被拒的第二次冻结不得覆盖第一次的冻结件"


# ─────────────────────────────────────────────────────────── 5-6 索引 / CI


def test_index_sha_xor_reason(repo: Path, tmp_path: Path) -> None:
    """镜像 schema「禁止省略字段冒充无关」: 值与理由必须恰给一个。"""
    neither = _freeze(repo, tmp_path / "o1")
    assert neither.returncode == 1, _both(neither)
    assert _REJECT_MARK in _both(neither), _both(neither)
    assert not (tmp_path / "o1").exists()

    both = _freeze(repo, tmp_path / "o2", "--index-sha", "abc", *_NULL_REASON)
    assert both.returncode == 1, _both(both)
    assert not (tmp_path / "o2").exists()

    only_value = _freeze(repo, tmp_path / "o3", "--index-sha", "abc")
    assert only_value.returncode == 0, _both(only_value)
    doc = _manifest(_only_rc_dir(tmp_path / "o3"))
    assert doc["index_sha"] == "abc"
    assert doc["index_sha_null_reason"] is None


def test_ci_run_id_precedence(repo: Path, tmp_path: Path) -> None:
    explicit = _freeze(repo, tmp_path / "o1", *_NULL_REASON, "--ci-run-id", "7", env={"GITHUB_RUN_ID": "9"})
    assert explicit.returncode == 0, _both(explicit)
    assert _manifest(_only_rc_dir(tmp_path / "o1"))["ci_run_id"] == "7"

    from_env = _freeze(repo, tmp_path / "o2", *_NULL_REASON, env={"GITHUB_RUN_ID": "9"})
    assert from_env.returncode == 0, _both(from_env)
    doc_env = _manifest(_only_rc_dir(tmp_path / "o2"))
    assert doc_env["ci_run_id"] == "9"
    assert doc_env["ci_run_id_null_reason"] is None

    neither = _freeze(repo, tmp_path / "o3", *_NULL_REASON)
    assert neither.returncode == 0, _both(neither)
    doc_none = _manifest(_only_rc_dir(tmp_path / "o3"))
    assert doc_none["ci_run_id"] is None
    assert doc_none["ci_run_id_null_reason"], "null 必须带理由, 与索引 SHA 同口径"


# ─────────────────────────────────────────────────────────── 7-8 双树


def test_detached_head_recorded(repo: Path, tmp_path: Path) -> None:
    """tmp 仓内的 detach (与 §三「禁 checkout-HEAD 还原形态」无关, 那条约束的是本仓)。"""
    _git(repo, "checkout", "-q", "--detach")
    proc = _freeze(repo, tmp_path / "out", *_NULL_REASON)

    assert proc.returncode == 0, _both(proc)
    cand = _manifest(_only_rc_dir(tmp_path / "out"))["candidate"]
    assert cand["branch"] == "HEAD"
    assert cand["detached"] is True
    assert cand["sha"] == _git(repo, "rev-parse", "HEAD")


def test_linked_worktree_dual_tree_fields(repo: Path, tmp_path: Path) -> None:
    """双树消歧: 先在主仓冻结 ('.', False), 再在 linked worktree 冻结 ('wt', True)。

    顺序不能反 —— `git worktree add <repo>/wt` 之后主仓会多出一个未跟踪的 wt/,
    那时再在主仓冻结会被 dirty 门 (正确地) 拒掉。
    """
    main_out = tmp_path / "out-main"
    main_proc = _freeze(repo, main_out, *_NULL_REASON, "--rc-name", "rc-main")
    assert main_proc.returncode == 0, _both(main_proc)
    main_cand = _manifest(main_out / "rc-main")["candidate"]
    assert main_cand["worktree_rel_to_main"] == "."
    assert main_cand["is_linked_worktree"] is False
    assert _manifest(main_out / "rc-main")["trees"]["code"]["kind"] == "main"

    wt = repo / "wt"
    _git(repo, "worktree", "add", "-q", str(wt))

    wt_out = tmp_path / "out-wt"
    wt_proc = _freeze(wt, wt_out, *_NULL_REASON, "--rc-name", "rc-wt")
    assert wt_proc.returncode == 0, _both(wt_proc)
    doc = _manifest(wt_out / "rc-wt")
    cand = doc["candidate"]
    assert cand["is_linked_worktree"] is True
    assert cand["worktree_rel_to_main"] == "wt"
    assert Path(cand["git_common_dir"]) == (repo / ".git").resolve()
    assert Path(cand["worktree"]) == wt.resolve()
    assert doc["trees"]["code"]["kind"] == "linked-worktree"


def test_vault_root_recorded_readonly(repo: Path, tmp_path: Path) -> None:
    """第二棵树 (vault) 只读记账: 记 HEAD 与脏条目数, 不动它一个字节。"""
    vault = tmp_path / "vault"
    _init_repo(vault)
    (vault / "note.md").write_text("# 已提交\n", encoding="utf-8")
    _git(vault, "add", "-A")
    _commit(vault, "vault base")
    (vault / "untracked.md").write_text("# 未提交\n", encoding="utf-8")

    before = sorted(
        (p.relative_to(vault).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
        for p in vault.rglob("*")
        if p.is_file() and ".git/" not in p.relative_to(vault).as_posix()
    )

    proc = _freeze(repo, tmp_path / "out", *_NULL_REASON, "--vault-root", str(vault))
    assert proc.returncode == 0, _both(proc)

    trees = _manifest(_only_rc_dir(tmp_path / "out"))["trees"]
    assert Path(trees["vault"]["path"]) == vault.resolve()
    assert _SHA_RE.fullmatch(trees["vault"]["git_head"])
    assert trees["vault"]["git_head"] == _git(vault, "rev-parse", "HEAD")
    assert trees["vault"]["dirty_entries"] == 1
    assert trees["vault_null_reason"] is None

    after = sorted(
        (p.relative_to(vault).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
        for p in vault.rglob("*")
        if p.is_file() and ".git/" not in p.relative_to(vault).as_posix()
    )
    assert after == before, "vault 树必须逐字节不变 (只读)"


def test_vault_absent_records_null_reason(repo: Path, tmp_path: Path) -> None:
    """不传 --vault-root 时不许省略字段, 要 null + 理由 (与索引 SHA 同口径)。"""
    proc = _freeze(repo, tmp_path / "out", *_NULL_REASON)
    assert proc.returncode == 0, _both(proc)
    trees = _manifest(_only_rc_dir(tmp_path / "out"))["trees"]
    assert trees["vault"] is None
    assert trees["vault_null_reason"]


# ─────────────────────────────────────────────────────────── 10-11 拒绝面


@pytest.mark.parametrize("victim_index", [0, 1])
def test_missing_lockfile_refused(repo: Path, tmp_path: Path, victim_index: int) -> None:
    """锁文件缺一即拒 —— 不写 null 冒充「本项目无锁」。

    ⚠️ 两份锁各测一次: 原先只删第二份, 「第一份缺席」是未覆盖的输入(独立审查 r2)。
    """
    victim = _LOCK_RELS[victim_index]
    _git(repo, "rm", "-q", victim)
    _commit(repo, f"drop {victim}")

    proc = _freeze(repo, tmp_path / "out", *_NULL_REASON)

    assert proc.returncode == 1, _both(proc)
    assert _REJECT_MARK in _both(proc), _both(proc)
    assert victim in _both(proc), f"拒绝信息要指出缺的是哪一份: {_both(proc)}"
    assert not (tmp_path / "out").exists()


def test_validator_missing_exit_2(repo: Path, tmp_path: Path) -> None:
    """校验器缺席 = 环境错 (2), 不是内容不合格 (1), 且零写入。

    ⚠️ 这里不能只断言 `returncode == 2`: 被测脚本**自己不存在**时
    `python <缺席脚本>` 同样退 2 (先红实测), 只看数字这条会在空仓上假绿。
    所以判据锚在只有本脚本才打得出的 _ENV_MARK 上 —— 身份判据, 不是数量判据。
    """
    proc = _freeze(repo, tmp_path / "out", *_NULL_REASON, "--validator", str(tmp_path / "nope.py"))

    assert proc.returncode == 2, _both(proc)
    assert _ENV_MARK in _both(proc), _both(proc)
    assert "nope.py" in _both(proc)
    assert not (tmp_path / "out").exists()


def test_not_a_git_repo_exit_2(tmp_path: Path) -> None:
    """--repo 指向非 git 目录 = 环境错 (2)。"""
    plain = tmp_path / "plain"
    plain.mkdir()
    proc = _run(
        plain,
        "freeze",
        "--repo",
        str(plain),
        "--out-root",
        str(tmp_path / "out"),
        *_NULL_REASON,
    )

    assert proc.returncode == 2, _both(proc)
    assert _ENV_MARK in _both(proc), _both(proc)
    assert not (tmp_path / "out").exists()


# ─────────────────────────────────────────────────────────── 12 check


def _write_journey(rc_dir: Path, jid: str, sha: str) -> None:
    jdir = rc_dir / "journeys" / jid
    jdir.mkdir(parents=True, exist_ok=True)
    (jdir / "manifest.json").write_text(
        json.dumps({"rc": rc_dir.name, "journey_id": jid, "candidate": {"sha": sha}}, indent=2) + "\n",
        encoding="utf-8",
    )


def test_check_detects_journey_sha_mismatch(repo: Path, tmp_path: Path) -> None:
    out_root = tmp_path / "out"
    assert _freeze(repo, out_root, *_NULL_REASON).returncode == 0
    rc_dir = _only_rc_dir(out_root)
    rc_sha = _manifest(rc_dir)["candidate"]["sha"]

    # ⚠️ 只放一份 journey 时,「逐份比对」与「至少一份一致」在该输入下**不可区分**
    # (独立审查变异实测: 改成后者同样全绿)。所以必须放两份 —— 一份对、一份错。
    _write_journey(rc_dir, "J02", rc_sha)
    _write_journey(rc_dir, "J01", _OTHER_SHA)
    bad = _run(repo, "check", str(rc_dir))
    assert bad.returncode == 1, _both(bad)
    assert "J01" in bad.stdout
    assert "sha 不一致" in bad.stdout

    _write_journey(rc_dir, "J01", rc_sha)
    good = _run(repo, "check", str(rc_dir))
    assert good.returncode == 0, _both(good)

    # ⚠️ 第四处「取名面小于主张」(独立审查 r2 抓到, 且是**上一轮修复自己造出来的**):
    # 为区分「逐份」与「至少一份」补的那份 J02 现在在场, 它的**成功行**里也有 "J02",
    # 于是「J02 应出现在缺失清单里」这条断言被成功行满足 —— 搜整个 stdout 是错的口径。
    # 正解: 把缺失清单那一行单独摘出来, 只在它里面判。
    missing_lines = [ln for ln in good.stdout.splitlines() if "尚缺" in ln]
    assert len(missing_lines) == 1, good.stdout
    missing_line = missing_lines[0]
    for jid in (f"J{i:02d}" for i in range(3, 11)):
        assert jid in missing_line, f"缺失清单应含 {jid}: {missing_line}"
    for present_jid in ("J01", "J02"):
        assert present_jid not in missing_line, f"{present_jid} 在场, 不该进缺失清单: {missing_line}"
    assert "尚缺 8 条" in missing_line, missing_line


def test_check_zero_journeys_does_not_claim_verification(repo: Path, tmp_path: Path) -> None:
    """零 journey 时 check 仍退 0, 但**不得**说成「全部绑同一个 sha」。

    空集上「全部 X 满足 P」恒真。刚冻结出来的骨架一条 journey 都没有, 若照「全部一致」
    那句话打, rc=0 会被读成「这个 RC 验过了」—— 而它什么都没比对。本条钉住的是报告
    必须区分「验过且通过」与「没什么可验」。
    """
    out_root = tmp_path / "out"
    assert _freeze(repo, out_root, *_NULL_REASON).returncode == 0
    rc_dir = _only_rc_dir(out_root)

    proc = _run(repo, "check", str(rc_dir))

    assert proc.returncode == 0, _both(proc)
    assert "全部绑同一个" not in proc.stdout, proc.stdout
    assert "未比对任何" in proc.stdout, proc.stdout
    assert "尚缺 10 条" in proc.stdout, proc.stdout


def test_check_rejects_tampered_rc_manifest(repo: Path, tmp_path: Path) -> None:
    """check 也守 rc-manifest 自身: dirty 被改成 true / rc 与目录名不符都要红。"""
    out_root = tmp_path / "out"
    assert _freeze(repo, out_root, *_NULL_REASON).returncode == 0
    rc_dir = _only_rc_dir(out_root)
    path = rc_dir / "rc-manifest.json"

    doc = _manifest(rc_dir)
    doc["candidate"]["dirty"] = True
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dirty_proc = _run(repo, "check", str(rc_dir))
    assert dirty_proc.returncode == 1, _both(dirty_proc)
    assert "dirty" in dirty_proc.stdout

    doc["candidate"]["dirty"] = False
    doc["rc"] = "another-name"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rc_proc = _run(repo, "check", str(rc_dir))
    assert rc_proc.returncode == 1, _both(rc_proc)
    assert "another-name" in rc_proc.stdout


def test_check_missing_rc_manifest_exit_1(repo: Path, tmp_path: Path) -> None:
    empty = tmp_path / "empty-rc"
    empty.mkdir()
    proc = _run(repo, "check", str(empty))
    assert proc.returncode == 1, _both(proc)
    assert "rc-manifest.json" in _both(proc)


# ─────────────────────────────────────────────────────────── 13 正则共享


def test_rc_name_regex_shared_with_validator() -> None:
    """rc 名正则必须与校验器 _RC_NAME_RE 逐字同 —— 否则冻结出来的目录名校验器不认。

    脚本本体**不** import 校验器 (走 subprocess 保证校验器零改动), 两处各持一份字面量;
    这条裁判就是那两份字面量之间唯一的机械纽带。
    """
    sys.path.insert(0, str(_SCRIPTS_DIR))
    import freeze_release_candidate as frc
    import validate_release_manifest as vrm

    assert frc._RC_NAME_RE.pattern == vrm._RC_NAME_RE.pattern
    assert frc.JOURNEYS_EXPECTED == list(vrm.ALL_JOURNEYS)


def test_rc_name_rejects_path_like(repo: Path, tmp_path: Path) -> None:
    """rc 名只许目录名, 不许路径 —— 与校验器 check_rc_completeness 的红队整改同口径。"""
    proc = _freeze(repo, tmp_path / "out", *_NULL_REASON, "--rc-name", "../escape")
    assert proc.returncode == 1, _both(proc)
    assert _REJECT_MARK in _both(proc), _both(proc)
    assert not (tmp_path / "out").exists()
    assert not (tmp_path / "escape").exists()


# ─────────────────────────────────────────────────────────── 边界如实钉住


# freeze 子命令允许存在的**全部**选项名。封闭集合: 加任何新 flag 都必须先改这里, 于是
# 「有没有偷偷多一个 dirty 旁路」变成一道机械门, 而不是靠记得去 grep 某个具体名字。
_FREEZE_OPTIONS = {
    "-h",
    "--help",
    "--repo",
    "--out-root",
    "--rc-name",
    "--index-sha",
    "--index-sha-null-reason",
    "--ci-run-id",
    "--vault-root",
    "--validator",
}


def _freeze_subparser_options() -> set:
    sys.path.insert(0, str(_SCRIPTS_DIR))
    import freeze_release_candidate as frc

    parser = frc._build_parser()
    sub_action = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)][0]
    opts = set()
    for action in sub_action.choices["freeze"]._actions:
        opts.update(action.option_strings)
    return opts


def test_no_dirty_bypass_switch(repo: Path, tmp_path: Path) -> None:
    """dirty 门没有跳过开关 —— 判据锚在 freeze 子命令的**选项名全集**上。

    ⚠️ 这条判据被独立审查用变异打穿过两次, 两次都是**判据的取名面小于它的主张**:
      1. 最初写成 `assert "allow-dirty" not in source` —— 被脚本 docstring 里
         「没有 --allow-dirty」这句**诚实声明**打红。文本缺席 ≠ 行为拒绝。
      2. 改成「AST 字面量 0 处 allow-dirty」+「CLI 拒 --allow-dirty」两面后, 变异实测:
         给 freeze 加一个叫 --force 的 flag 让它跳过 dirty 判定, 全文不出现 allow-dirty
         字样 —— **22 条裁判全绿**, 而脏树能冻出 dirty=false 的失实回执。那两面合起来
         证明的只是「不存在一个叫 --allow-dirty 的 flag」, 不是它声称的「没有跳过开关」。
    现在锚在封闭集合上: 任何**新增**选项(不管叫什么)都会让这条红。
    """
    assert _freeze_subparser_options() == _FREEZE_OPTIONS

    # 验伪锚: 集合确实是从真 parser 取的, 不是把常量抄了两遍 —— 少一个已知在场的选项必须不等。
    assert _freeze_subparser_options() != (_FREEZE_OPTIONS - {"--vault-root"})

    proc = _freeze(repo, tmp_path / "out", *_NULL_REASON, "--allow-dirty")
    assert proc.returncode != 0, _both(proc)
    assert "unrecognized arguments" in proc.stderr, proc.stderr
    assert not (tmp_path / "out").exists()


def test_gitignored_file_does_not_block_freeze(repo: Path, tmp_path: Path) -> None:
    """**已知盲区如实钉住**: `.gitignore` 忽略的文件不进 porcelain, 冻结照过。

    这不是 bug 而是 dirty 门的覆盖面边界 (git 的 porcelain 语义)。脚本必须把这条边界
    打印出来, 让读冻结件的人知道「dirty=false」到底保证了什么、没保证什么 —— 本条断言
    钉的就是「边界被声明」, 而不是「边界不存在」。
    """
    (repo / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _commit(repo, "add gitignore")
    (repo / "ignored").mkdir()
    (repo / "ignored" / "blob.bin").write_text("x", encoding="utf-8")

    proc = _freeze(repo, tmp_path / "out", *_NULL_REASON)

    assert proc.returncode == 0, _both(proc)
    assert "gitignore" in proc.stdout, "dirty 门的盲区必须在冻结当刻被打印声明"
    doc = _manifest(_only_rc_dir(tmp_path / "out"))
    assert doc["candidate"]["dirty"] is False
    assert "gitignore" in " ".join(doc["candidate"]["dirty_scope_caveats"])


def test_environment_recorded(repo: Path, tmp_path: Path) -> None:
    proc = _freeze(repo, tmp_path / "out", *_NULL_REASON)
    assert proc.returncode == 0, _both(proc)
    env = _manifest(_only_rc_dir(tmp_path / "out"))["environment"]
    assert env["git_version"].startswith("git version")
    assert env["python_version"] == ".".join(str(n) for n in sys.version_info[:3])
    assert env["host_os"]


# ─────────────────────────────────────── 独立审查（Codex r1 + 内部 8 维对抗）整改回归
#
# 下面这一组全部来自 2026-09-18/19 的两份独立复核。每条都先在真仓/真 tmp 仓上复现过
# 缺陷、再写门 —— 不是"看起来该测一下"。


def test_blank_string_args_refused(repo: Path, tmp_path: Path) -> None:
    """空串/纯空白不是「没给」也不是「给了」——一律拒。

    ⚠️ 复现过的缺陷: 原实现用 `bool(args.index_sha)` 判「给没给」, 于是
    `--index-sha "" --index-sha-null-reason 理由` 两个都给了却通过 XOR 门, 并写出
    `index_sha: ""` —— 恰好违反 schema 对该字段的 minLength: 1, 正是这道门声称要挡的那格。
    """
    both_given = _freeze(repo, tmp_path / "o1", "--index-sha", "", "--index-sha-null-reason", "理由")
    assert both_given.returncode == 1, _both(both_given)
    assert _REJECT_MARK in _both(both_given)
    assert "空串" in _both(both_given) or "空白" in _both(both_given)
    assert not (tmp_path / "o1").exists()

    blank_reason = _freeze(repo, tmp_path / "o2", "--index-sha-null-reason", "   ")
    assert blank_reason.returncode == 1, _both(blank_reason)
    assert not (tmp_path / "o2").exists()

    # 对照输入: 同一条链路上, 真正合法的取值必须照常通过 —— 否则这道门是"一律拒"而不是"拒空"。
    ok = _freeze(repo, tmp_path / "o3", "--index-sha", "abc")
    assert ok.returncode == 0, _both(ok)


def test_rc_name_dot_and_dotdot_refused_no_escape(repo: Path, tmp_path: Path) -> None:
    """rc 名 `.` / `..` 必须拒 —— 它们能 fullmatch 与校验器共享的那条正则。

    ⚠️ 复现过的缺陷: `--rc-name ..` 且 --out-root 尚不存在时, 原实现 **退 0 并打印
    「✅ 已冻结」**, 而骨架与 rc-manifest 落在了 --out-root 的**父目录**里(实测)。
    共享正则不能单方面收紧(收紧了冻出来的目录名校验器就不认了), 所以另加一道包含性判据。
    """
    import re as _re

    shared = _re.compile(r"^[A-Za-z0-9._-]{1,64}$")
    assert shared.fullmatch("..") and shared.fullmatch("."), "前提: 共享正则确实放过它们"

    box = tmp_path / "box"
    box.mkdir()
    escaped = _freeze(repo, box / "not-yet", *_NULL_REASON, "--rc-name", "..")
    assert escaped.returncode == 1, _both(escaped)
    assert _REJECT_MARK in _both(escaped)
    assert not (box / "journeys").exists(), "骨架逃到了 out-root 之外"
    assert not (box / "rc-manifest.json").exists()

    dot = _freeze(repo, tmp_path / "dotout", *_NULL_REASON, "--rc-name", ".")
    assert dot.returncode == 1, _both(dot)
    assert not (tmp_path / "dotout" / "rc-manifest.json").exists()


def test_same_sha_different_rc_name_refused(repo: Path, tmp_path: Path) -> None:
    """「一个 SHA 一个 rc」必须按 SHA 判, 不能只按目录名。

    ⚠️ 复现过的缺陷: 同一个干净 SHA 换个 --rc-name 就能再冻一个, 两次都退 0(实测
    rc-a / rc-b 并存), README 那条硬规则形同虚设。默认名里还含日期, 跨日同样能重冻。
    """
    out_root = tmp_path / "out"
    first = _freeze(repo, out_root, *_NULL_REASON, "--rc-name", "rc-a")
    assert first.returncode == 0, _both(first)

    second = _freeze(repo, out_root, *_NULL_REASON, "--rc-name", "rc-b")
    assert second.returncode == 1, _both(second)
    assert _REJECT_MARK in _both(second)
    assert "rc-a" in _both(second), "拒绝信息要指出是哪个 rc 已经占了这个 SHA"
    assert not (out_root / "rc-b").exists()

    # 对照输入: 换一个 SHA 就该放行 —— 否则这道门挡的是"第二次冻结"而不是"同 SHA 重冻"。
    (repo / "note.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _commit(repo, "second commit")
    third = _freeze(repo, out_root, *_NULL_REASON, "--rc-name", "rc-c")
    assert third.returncode == 0, _both(third)


def _real_validator_on(tmp_root: Path, *, with_schema: bool, bad_manifest: bool) -> Path:
    """在 tmp 下搭一棵**合成证据树**, 把**真校验器原样拷进去**, 返回那份校验器的路径。

    ⚠️ 这不是替身 (独立审查 r2 判定上一版的 `_write_validator_stub` 属 mock, 违反禁 mock,
    该判定成立): 跑的是 `validate_release_manifest.py` 的**真实实现**, 只是喂给它一棵
    合成的输入树 —— 与既有裁判 `test_validate_release_manifest.py` 的做法同口径
    (真实现 + 合成 fixture)。退出码由真实校验逻辑自己算出来, 不是我们预设的。

    - `with_schema=False` ⇒ 校验器找不到 schema, 按它自己的规则报**环境错 (2)**
    - `bad_manifest=True`  ⇒ 证据树里有一份结构不合法的 manifest, `--all` 判**内容不合格 (1)**
    """
    scripts = tmp_root / "backend" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_SCRIPTS_DIR / "validate_release_manifest.py", scripts / "validate_release_manifest.py")
    evidence = tmp_root / "docs" / "release-evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    if with_schema:
        shutil.copy2(
            _REPO_ROOT / "docs" / "release-evidence" / "manifest.schema.json",
            evidence / "manifest.schema.json",
        )
    if bad_manifest:
        jdir = evidence / "rc-synthetic" / "journeys" / "J01"
        jdir.mkdir(parents=True, exist_ok=True)
        # 顶层空对象: 必需字段全缺, 真校验器的结构层会判它不合格。
        (jdir / "manifest.json").write_text("{}\n", encoding="utf-8")
    return scripts / "validate_release_manifest.py"


def test_validator_nonzero_blocks_all_writes(repo: Path, tmp_path: Path) -> None:
    """校验器 --all 不通过 ⇒ 整体拒且**零写入**（这道门此前零测试覆盖）。

    用真校验器跑在一棵含畸形 manifest 的合成证据树上 —— rc=1 是它自己判出来的。
    """
    validator = _real_validator_on(tmp_path / "vrepo1", with_schema=True, bad_manifest=True)

    proc = _freeze(repo, tmp_path / "out", *_NULL_REASON, "--validator", str(validator))

    assert proc.returncode == 1, _both(proc)
    assert _REJECT_MARK in _both(proc)
    assert "FAIL" in proc.stdout, "校验器 stdout 必须原样透传"
    assert not (tmp_path / "out").exists(), "校验器没过就不该留下任何骨架"


def test_validator_exit_2_is_passed_through(repo: Path, tmp_path: Path) -> None:
    """校验器报环境错(2) ⇒ 原样透传 2, 不降级成 1。

    这条此前被登记为「未证明」(以为要卸 jsonschema 才能测)。把真校验器放进一棵**没有
    schema** 的合成证据树即可 —— 它按自己的规则退 2, 无需动任何依赖。
    """
    validator = _real_validator_on(tmp_path / "vrepo2", with_schema=False, bad_manifest=False)

    proc = _freeze(repo, tmp_path / "out", *_NULL_REASON, "--validator", str(validator))

    assert proc.returncode == 2, _both(proc)
    assert _ENV_MARK in _both(proc)
    assert not (tmp_path / "out").exists()


def test_check_handles_non_dict_candidate(repo: Path, tmp_path: Path) -> None:
    """journey 的 candidate 是非 dict 真值时, check 必须记一条问题而不是崩掉。

    ⚠️ 复现过的缺陷: 手填成 `"candidate": "<sha>"` 时原实现抛 AttributeError,
    已攒下的问题全丢、后面的 journey 一份都不再比对。
    """
    out_root = tmp_path / "out"
    assert _freeze(repo, out_root, *_NULL_REASON).returncode == 0
    rc_dir = _only_rc_dir(out_root)
    rc_sha = _manifest(rc_dir)["candidate"]["sha"]

    jdir = rc_dir / "journeys" / "J01"
    jdir.mkdir(parents=True)
    (jdir / "manifest.json").write_text(
        json.dumps({"rc": rc_dir.name, "journey_id": "J01", "candidate": rc_sha}) + "\n",
        encoding="utf-8",
    )
    # 同时放一份**正常但不一致**的 J02: 若 J01 让程序崩掉, J02 的问题就永远报不出来。
    _write_journey(rc_dir, "J02", _OTHER_SHA)

    proc = _run(repo, "check", str(rc_dir))

    assert proc.returncode == 1, _both(proc)
    assert "Traceback" not in _both(proc), "不得以未捕获异常收场"
    assert "J01" in proc.stdout and "不是对象" in proc.stdout
    assert "J02" in proc.stdout, "J01 的畸形不得吞掉 J02 的不一致"


def test_check_name_resolved_via_out_root_not_cwd(repo: Path, tmp_path: Path) -> None:
    """传 rc **名字**时只按 --out-root 解析, 不看 cwd。

    ⚠️ 复现过的缺陷: 原实现先试 cwd 相对路径, cwd 下恰有同名目录时会静默压过显式
    --out-root —— 你以为在验候选树的 rc, 实际验的是手边那个同名目录。
    """
    out_root = tmp_path / "out"
    assert _freeze(repo, out_root, *_NULL_REASON, "--rc-name", "rc-x").returncode == 0

    # 在 cwd(= repo) 下造一个同名诱饵目录, 里面放一份 sha 完全对不上的回执
    decoy = repo / "rc-x"
    (decoy / "journeys").mkdir(parents=True)
    (decoy / "rc-manifest.json").write_text(json.dumps({"rc": "rc-x"}) + "\n", encoding="utf-8")

    proc = _run(repo, "check", "rc-x", "--repo", str(repo), "--out-root", str(out_root))

    assert proc.returncode == 0, _both(proc)
    assert str(out_root) in proc.stdout or "rc-x" in proc.stdout
    # 决定性判据: 真去验了诱饵的话, 它缺一堆必需键, 必然退 1。
    assert _REJECT_MARK not in _both(proc), "被 cwd 下的同名诱饵目录劫持了"


def test_check_declares_what_it_did_not_verify(repo: Path, tmp_path: Path) -> None:
    """check 通过时必须自陈边界 —— 它只核绑定, 不核 schema / symlink / RC 完整性。"""
    out_root = tmp_path / "out"
    assert _freeze(repo, out_root, *_NULL_REASON).returncode == 0
    proc = _run(repo, "check", str(_only_rc_dir(out_root)))

    assert proc.returncode == 0, _both(proc)
    # 三项各锁一个词 —— 只认「未验」+「schema」的话, 删掉 symlink 与完整性两项仍绿
    # (独立审查 r2 的负控输入)。
    assert "未验" in proc.stdout
    assert "schema" in proc.stdout
    assert "symlink" in proc.stdout
    assert "完整性" in proc.stdout


def test_candidate_key_set_pinned(repo: Path, tmp_path: Path) -> None:
    """candidate 的键集是封闭的 —— 与顶层键集同口径, 加字段必须先改这条。"""
    assert _freeze(repo, tmp_path / "out", *_NULL_REASON).returncode == 0
    cand = _manifest(_only_rc_dir(tmp_path / "out"))["candidate"]
    assert set(cand) == {
        "sha",
        "branch",
        "detached",
        "dirty",
        "worktree",
        "worktree_rel_to_main",
        "git_common_dir",
        "git_dir",
        "main_root",
        "main_root_source",
        "is_linked_worktree",
        "dirty_scope_caveats",
        "rechecked_before_write",
    }
    assert cand["rechecked_before_write"] is True


def test_main_root_comes_from_worktree_list(repo: Path, tmp_path: Path) -> None:
    """main_root 走 `git worktree list --porcelain` 首条, 不靠 `<git-common-dir>/..` 推。

    ⚠️ 后者只在 common dir 恰好是 `<主工作树>/.git` 时成立; --separate-git-dir、
    submodule(`.git/modules/<name>`)、bare 三种拓扑下会给出「看起来合理但错」的目录,
    连带 is_linked_worktree / worktree_rel_to_main / trees.code.kind 一起错。
    """
    assert _freeze(repo, tmp_path / "m1", *_NULL_REASON, "--rc-name", "rc-main").returncode == 0
    main_cand = _manifest(tmp_path / "m1" / "rc-main")["candidate"]
    # 主树情形不做任何推算: --git-dir == --git-common-dir 即证, main_root 就是 --show-toplevel
    assert main_cand["main_root_source"] == "self(main-worktree)"
    assert Path(main_cand["main_root"]) == repo.resolve()
    assert main_cand["is_linked_worktree"] is False
    assert Path(main_cand["git_dir"]) == Path(main_cand["git_common_dir"])

    wt = repo / "wt"
    _git(repo, "worktree", "add", "-q", str(wt))
    assert _freeze(wt, tmp_path / "m2", *_NULL_REASON, "--rc-name", "rc-wt").returncode == 0
    wt_cand = _manifest(tmp_path / "m2" / "rc-wt")["candidate"]
    assert wt_cand["main_root_source"] == "worktree-list"
    assert Path(wt_cand["main_root"]) == repo.resolve(), "linked worktree 里也要指回主工作树"
    assert wt_cand["is_linked_worktree"] is True
    assert wt_cand["worktree_rel_to_main"] == "wt"
    assert Path(wt_cand["git_dir"]) != Path(wt_cand["git_common_dir"]), "linked 树的两者必不同"


# ─────────────────────────────── Codex round-2 整改回归（独立审查 1 HIGH + 7 MEDIUM + 5 LOW）


def test_duplicate_scan_fails_closed_on_unreadable_manifest(repo: Path, tmp_path: Path) -> None:
    """同 SHA 判重遇到读不出来的旧件必须**拒绝**, 不能 continue 跳过。

    ⚠️ 原实现 `except … continue`, 于是把旧回执弄成截断 JSON 再换个 rc 名就能重冻,
    而注释所说「由 check 去报」没有任何调用链保证 —— 校验器 `--all` 压根不扫
    rc-manifest.json(独立审查 r2)。
    """
    out_root = tmp_path / "out"
    assert _freeze(repo, out_root, *_NULL_REASON, "--rc-name", "rc-a").returncode == 0
    (out_root / "rc-a" / "rc-manifest.json").write_text("{ 截断的 json", encoding="utf-8")

    proc = _freeze(repo, out_root, *_NULL_REASON, "--rc-name", "rc-b")

    assert proc.returncode == 1, _both(proc)
    assert _REJECT_MARK in _both(proc)
    assert "fail-closed" in _both(proc) or "读不出来" in _both(proc), _both(proc)
    assert not (out_root / "rc-b").exists()


def test_duplicate_scan_fails_closed_on_non_dict_candidate(repo: Path, tmp_path: Path) -> None:
    """旧件的 candidate 是非 dict 真值时, 判重扫描也要拒而不是崩。"""
    out_root = tmp_path / "out"
    assert _freeze(repo, out_root, *_NULL_REASON, "--rc-name", "rc-a").returncode == 0
    doc = _manifest(out_root / "rc-a")
    doc["candidate"] = "只是个字符串"
    (out_root / "rc-a" / "rc-manifest.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    proc = _freeze(repo, out_root, *_NULL_REASON, "--rc-name", "rc-b")

    assert proc.returncode == 1, _both(proc)
    assert "Traceback" not in _both(proc), "不得以未捕获异常收场"
    assert "candidate 不是对象" in _both(proc), _both(proc)
    assert not (out_root / "rc-b").exists()


def test_rc_name_leading_dot_refused(repo: Path, tmp_path: Path) -> None:
    """rc 名不得以 `.` 开头 —— 否则 freeze 认名字、check 认路径, 两边取值域不一致。

    ⚠️ 独立审查 r2: `freeze --rc-name .rc` 合法, 但 `check .rc --out-root X` 会把它
    当 cwd 相对路径, 于是验的是手边那份而不是 X 下那份, 而成功行只打名字看不出来。
    """
    import re as _re

    assert _re.compile(r"^[A-Za-z0-9._-]{1,64}$").fullmatch(".rc"), "前提: 共享正则放过它"

    proc = _freeze(repo, tmp_path / "out", *_NULL_REASON, "--rc-name", ".rc")

    assert proc.returncode == 1, _both(proc)
    assert _REJECT_MARK in _both(proc)
    assert not (tmp_path / "out").exists()


def test_check_rejects_non_dict_candidate_in_rc_manifest(repo: Path, tmp_path: Path) -> None:
    """rc-manifest 自身的 candidate 非 dict 时 check 要拒而不是崩(与 journey 侧同型)。"""
    out_root = tmp_path / "out"
    assert _freeze(repo, out_root, *_NULL_REASON).returncode == 0
    rc_dir = _only_rc_dir(out_root)
    doc = _manifest(rc_dir)
    doc["candidate"] = ["不是对象"]
    (rc_dir / "rc-manifest.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    proc = _run(repo, "check", str(rc_dir))

    assert proc.returncode == 1, _both(proc)
    assert "Traceback" not in _both(proc)
    assert "candidate 不是对象" in _both(proc), _both(proc)


def test_check_survives_invalid_utf8(repo: Path, tmp_path: Path) -> None:
    """含非法 UTF-8 字节的 manifest 只能让 check 判红, 不能让它以 UnicodeDecodeError 收场。"""
    out_root = tmp_path / "out"
    assert _freeze(repo, out_root, *_NULL_REASON).returncode == 0
    rc_dir = _only_rc_dir(out_root)
    rc_sha = _manifest(rc_dir)["candidate"]["sha"]

    jdir = rc_dir / "journeys" / "J01"
    jdir.mkdir(parents=True)
    (jdir / "manifest.json").write_bytes(b'{"candidate": {"sha": "\xff\xfe non-utf8"}}')
    _write_journey(rc_dir, "J02", _OTHER_SHA)

    proc = _run(repo, "check", str(rc_dir))

    assert proc.returncode == 1, _both(proc)
    assert "Traceback" not in _both(proc), _both(proc)
    assert "J01" in proc.stdout
    assert "J02" in proc.stdout, "J01 的编码问题不得吞掉 J02 的不一致"


def test_separate_git_dir_topology(tmp_path: Path) -> None:
    """`--separate-git-dir`(git 目录在树外)下双树字段仍正确。

    ⚠️ 这条是独立审查 r2 的 LOW「没覆盖它声称修复的特殊拓扑」促成的, 一覆盖就抓到真错:
    本机 git 2.50.1 实测, 该拓扑下 `git worktree list --porcelain` 把**git 目录**报成
    worktree 路径(`worktree <…>/sepgit`), 而 `--git-common-dir` 也指向它 —— 于是
    「worktree-list 首条」与「common-dir 的父目录」**两种推算法都给出错值**。
    正解是不推算: `--git-dir == --git-common-dir` ⟺ 当前就是主工作树。
    """
    work = tmp_path / "sepwt"
    gitdir = tmp_path / "sepgit"
    work.mkdir()
    _git(work, "init", "-q", "--separate-git-dir", str(gitdir))
    _git(work, "symbolic-ref", "HEAD", "refs/heads/main")
    _seed_locks(work)

    # 前提自证: git 在这个拓扑下确实把 git 目录报成了 worktree 路径。
    listed = _git(work, "worktree", "list", "--porcelain").splitlines()[0]
    assert listed == f"worktree {gitdir.resolve()}", f"前提变了, 本条的意义要重估: {listed}"

    proc = _freeze(work, tmp_path / "out", *_NULL_REASON, "--rc-name", "rc-sep")
    assert proc.returncode == 0, _both(proc)

    cand = _manifest(tmp_path / "out" / "rc-sep")["candidate"]
    assert cand["main_root_source"] == "self(main-worktree)"
    assert Path(cand["main_root"]) == work.resolve(), "main_root 必须是工作树, 不是 git 目录"
    assert Path(cand["main_root"]) != gitdir.resolve()
    assert cand["is_linked_worktree"] is False
    assert cand["worktree_rel_to_main"] == "."


def test_rc_dir_preexisting_symlink_refused(repo: Path, tmp_path: Path) -> None:
    """落点是一条指向 out-root 之外的软链时必须拒, 且外部目标一个字节都不能动。

    ⚠️ 独立审查 r2 判 HIGH 的是**竞态**版本(校验器 subprocess 跑的那几秒里软链才被建出来)。
    竞态本身没法在单测里确定性复现, 本条覆盖的是**静态**版本: 软链在冻结开始前就在那儿。
    竞态那一半靠 `os.mkdir` 的原子语义兜(已存在的任何东西——含软链——都让它抛
    FileExistsError), 该路径**未被本套裁判覆盖**, 已在验收单「本卡未证明什么」登记。
    """
    out_root = tmp_path / "out"
    out_root.mkdir()
    outside = tmp_path / "outside"
    (outside / "journeys").mkdir(parents=True)
    victim = outside / "rc-manifest.json"
    victim.write_text('{"pre-existing": true}\n', encoding="utf-8")
    before = victim.read_bytes()
    (out_root / "rc-evil").symlink_to(outside, target_is_directory=True)

    proc = _freeze(repo, out_root, *_NULL_REASON, "--rc-name", "rc-evil")

    assert proc.returncode == 1, _both(proc)
    assert _REJECT_MARK in _both(proc)
    assert victim.read_bytes() == before, "外部目标被写/截断了"
    assert not (outside / "journeys" / ".gitkeep").exists(), "骨架落到了 out-root 之外"
