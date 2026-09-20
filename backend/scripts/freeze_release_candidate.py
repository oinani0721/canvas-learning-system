#!/usr/bin/env python3
"""CARD-R-RC — clean release candidate 冻结脚本（RC 证据的生成端）。

产出: <out-root>/<rc>/rc-manifest.json + <out-root>/<rc>/journeys/.gitkeep

**它补的是哪一半**: `docs/release-evidence/` 的校验器 (`validate_release_manifest.py`)
把 `candidate.sha` 必须是完整 40 位、`candidate.dirty` 必须是 `false` 定成了硬门, 却
只"验格式不验存在"(README 已知边界)——也就是说, 这两个字段此前**没有生成端**, 全靠
人手填, 而 README 自己就记着"事后把归档提交填进来是最常见的错误"。本脚本让这两个字段
由机器在冻结当刻取: SHA 来自 `git rev-parse HEAD`(必然存在), dirty=false 来自一道
**拒绝脏树、且拒绝路径零写入**的硬门。R-J01…R-J10 与 G8-6 dogfood 的 `rc_sha` 从此
有唯一来源 = `<rc>/rc-manifest.json` 的 `candidate.sha`。

两个子命令:
  freeze  — 冻结当前 HEAD, 生成 rc 骨架, 并真调校验器 `--all`(+ 同树时 `--require-complete`)
  check   — 核 rc-manifest 自身自洽, 且各 journey manifest 的 candidate.sha 与它逐份一致

退出码三档 (与校验器同口径):
  0 通过 / 1 内容不合格或被拒绝 / 2 环境错(不是 git 仓、git 不可用、校验器缺席、
  校验器自己报环境错)

设计约束 (卡文 CARD-R-RC):
  * **stdlib only** —— `jsonschema` 不在 backend/requirements.txt(现为传递依赖), 冻结
    脚本不能依赖它; schema 校验一律交给校验器 subprocess, 缺依赖时由校验器 rc=2 说话。
  * **不 import 校验器** —— 走 subprocess, 保证校验器本体零改动、零被本脚本的导入副作用
    影响。代价是 `_RC_NAME_RE` 与 `JOURNEYS_EXPECTED` 两处各持一份字面量; 裁判
    `test_rc_name_regex_shared_with_validator` 是这两份之间唯一的机械纽带。
  * **不设任何跳过 dirty 门的开关** —— 脏树上的证据不成立(README/S17)。回填件允许
    `dirty=true` 是 journey manifest 的事, RC 冻结件恒 false。这条由裁判
    test_no_dirty_bypass_switch 两面钉住: AST 层证「源码里没有这类 flag 的字面量」,
    行为层证「真把这种 flag 喂进来 CLI 会拒」—— 字面量缺席不等于行为拒绝。

⚠️ dirty 门的覆盖面 (如实声明, 不假装覆盖):
  `git status --porcelain --untracked-files=all` 看得见"已跟踪文件的改动"与"未跟踪
  文件", 看不见下面这些 ——
    1. `.gitignore` / `.git/info/exclude` 忽略掉的文件(构建产物、本地配置、venv);
    2. 被 `git update-index --assume-unchanged` / `--skip-worktree` 标记的文件;
    3. 仓外依赖(容器镜像、named volume 里的索引、宿主环境变量)。
  因此 `dirty=false` 的准确含义是"**git 跟踪面**上没有未提交改动", 不是"这台机器上
  没有任何未保存的东西"。这句话会被原样写进 rc-manifest 的
  `candidate.dirty_scope_caveats`, 免得下游把它读成更强的保证。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

RC_MANIFEST_VERSION = "1.0.0"
RC_MANIFEST_NAME = "rc-manifest.json"

# ⚠️ 与 validate_release_manifest._RC_NAME_RE 逐字同 —— rc 名只许是目录名, 不许是路径
# (否则 `--require-complete ../../tmp/x` 能用仓外伪造件满足发布门, 校验器红队整改原文)。
# 本脚本不 import 校验器, 这份是第二份字面量; 两份的一致性由裁判
# test_rc_name_regex_shared_with_validator 机械钉住。
_RC_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

JOURNEYS_EXPECTED = [f"J{i:02d}" for i in range(1, 11)]

# 与 schema 的 candidate.sha 同形: 完整 40 位小写 hex, 且拒绝全零 null SHA。
_SHA_RE = re.compile(r"^(?!0{40}$)[0-9a-f]{40}$")

# 依赖锁清单 (相对仓根)。恰两项 —— 本仓无 uv.lock / poetry.lock / pyproject.toml。
DEPENDENCY_LOCKS = (
    "backend/requirements.txt",
    "frontend/obsidian-plugin/package-lock.json",
)

DIRTY_SCOPE_CAVEATS = (
    "dirty 取自 git status --porcelain --untracked-files=all, 覆盖面 = git 跟踪面。",
    "不覆盖 .gitignore / .git/info/exclude 忽略掉的文件(构建产物、本地配置、venv)。",
    "不覆盖 assume-unchanged / skip-worktree 标记过的文件。",
    "不覆盖仓外状态(容器镜像、named volume 内的索引、宿主环境变量)。",
    # 独立审查实测: index 里是 gitlink(mode 160000)但工作树该目录为空(未 checkout)时,
    # 往该路径下放任何文件, porcelain 恒 0 条 —— 且 git 没有任何 flag 能把它们列出来
    # (--ignored=matching 也命中 0)。本仓 _reference/obsidian-sample-plugin 正是此态。
    # 这类文件 `git add` 会被 fatal 拒绝、进不了 commit, 但确实躺在盘上。
    "不覆盖未 checkout 的 gitlink 路径下的内容(git 拒绝跟踪, 也无法枚举)。",
    # 操作进行中(rebase/merge/cherry-pick paused)的工作树可以是干净的, 此刻的 HEAD
    # 在 abort 后可能从所有 ref 不可达 —— dirty=false 不保证 SHA 事后仍可达。
    "不保证 HEAD 事后可达: rebase/merge 进行中时工作树可以干净, abort 后该 SHA 可能失联。",
    # `--ignore-submodules=none` 只关掉子模块那一类忽略。别的 git config 仍能让 status
    # 少报: 典型是 `core.fileMode=false` 下已跟踪文件的可执行位变化(独立审查 r2 指出)。
    "不覆盖被 git config 抑制的元数据变化(如 core.fileMode=false 下的可执行位)。",
)

NOTES = (
    "candidate.sha 是被冻结的代码 SHA, 不是归档本目录的那个提交 —— 归档提交必然晚于它"
    "(见 docs/release-evidence/README.md「RC 冻结与重跑规则」)。"
)

# 退出码标记: 让"脚本自己判出来的环境错"与"脚本压根没跑起来"可区分。
# python 执行一个不存在的文件同样退 2, 裁判只看数字会假绿。
_ENV_MARK = "⛔ [env]"
_REJECT_MARK = "⛔ [reject]"

EXIT_OK = 0
EXIT_REJECT = 1
EXIT_ENV = 2


class _Env(Exception):
    """环境错 (退 2)。"""


class _Reject(Exception):
    """内容不合格 / 被拒绝 (退 1)。"""


# ───────────────────────────────────────────────────────────────── git 真调


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            # `--no-optional-locks`: 普通 `git status` 会顺手刷新 index(写 .git/index),
            # 对「只读记账」的 vault 树来说那是写入。全局加上, 所有 git 读都不动磁盘状态。
            ["git", "--no-optional-locks", "-C", str(repo), *args],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:  # git 本身不可执行
        raise _Env(f"git 不可执行: {exc}") from exc


def _git_out(repo: Path, *args: str) -> str:
    proc = _git(repo, *args)
    if proc.returncode != 0:
        raise _Env(f"git {' '.join(args)} 失败 (rc={proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout.strip()


def _porcelain_entries(repo: Path, *pathspec: str) -> list[str]:
    """`--porcelain --untracked-files=all -z` 的条目表。

    用 `-z` 而不是按行切: `-z` 不对路径做 quoting, 中文/空格路径不会被转义成
    另一个字符串(按行 + quotepath 的组合是本仓踩过的坑)。

    ⚠️ rename 条目在 `-z` 下占**两段**(新名 NUL 旧名 NUL), 所以本函数的条目数对
    rename 会偏大一。判定只用"是否非空"(不受影响), 条目数仅用于打印与 vault 树的
    粗粒度记账 —— 如实写在这里, 免得下游把它当精确计数。
    """
    args = [
        "status",
        "--porcelain",
        "--untracked-files=all",
        # ⚠️ 不加这个 flag, `submodule.<name>.ignore` 配成 dirty/all 时子模块内部的改动
        # 与 HEAD 漂移都会被 status 静默吞掉 —— 那是仓内状态, 不属于任何一条 caveat。
        "--ignore-submodules=none",
        "-z",
    ]
    if pathspec:
        args.extend(["--", *pathspec])
    raw = _git_out(repo, *args)
    return [seg for seg in raw.split("\0") if seg]


def _resolve_repo(explicit: str | None) -> Path:
    start = Path(explicit).expanduser() if explicit else Path.cwd()
    if not start.is_dir():
        raise _Env(f"--repo 不是目录: {start}")
    proc = _git(start, "rev-parse", "--show-toplevel")
    if proc.returncode != 0:
        raise _Env(f"不是 git 仓 (或 git 拒绝访问): {start} — {proc.stderr.strip()}")
    return Path(proc.stdout.strip()).resolve()


def _main_worktree(repo: Path, worktree: Path, git_dir: Path, git_common_dir: Path) -> tuple[Path | None, str]:
    """主工作树路径 + 它是怎么得出来的(写进产物, 好让读的人知道这个值有多可信)。

    **不靠路径推算判「主树还是 linked 树」** —— 靠 git 的结构事实:
    `--git-dir == --git-common-dir` ⟺ 当前就是主工作树(linked 树的 git-dir 恒是
    `<common>/worktrees/<name>`)。这条不受 `--separate-git-dir` / bare 影响。

    ⚠️ 两条推算法都实测错过(独立审查 r2 的 LOW 促成本次覆盖):
      - `git_common_dir.parent`: separate-git-dir 下 common dir 在树外, parent 不是工作树;
      - `git worktree list --porcelain` 首条: separate-git-dir 仓里 git 把**git 目录**
        报成 worktree 路径(本机 git 2.50.1 实测 `worktree <…>/sepgit`)。
    所以主树情形直接用 `--show-toplevel`; linked 情形才去问 worktree list, 且对它的答案
    做**合理性校验**(不能等于 common dir、必须是真目录), 都不成立就如实记 null。
    """
    if git_dir == git_common_dir:
        return worktree, "self(main-worktree)"

    proc = _git(repo, "worktree", "list", "--porcelain")
    if proc.returncode == 0:
        for line in proc.stdout.splitlines():
            if line.startswith("worktree "):
                candidate = Path(line[len("worktree ") :]).resolve()
                if candidate != git_common_dir and candidate.is_dir():
                    return candidate, "worktree-list"
                break
    parent = git_common_dir.parent
    if parent.is_dir() and (parent / ".git").exists():
        return parent, "git-common-dir-parent(fallback)"
    return None, "unresolved"


def _git_identity(repo: Path) -> dict:
    """冻结当刻的代码身份 + 双树拓扑消歧字段。"""
    sha = _git_out(repo, "rev-parse", "HEAD")
    if not _SHA_RE.fullmatch(sha):
        raise _Env(f"rev-parse HEAD 给出的不是合法 40 位 SHA: {sha!r}")

    head_ref = _git(repo, "symbolic-ref", "--short", "-q", "HEAD")
    detached = head_ref.returncode != 0
    branch = "HEAD" if detached else head_ref.stdout.strip()

    worktree = Path(_git_out(repo, "rev-parse", "--show-toplevel")).resolve()
    # ⚠️ `--git-common-dir` 在主仓里返回相对值 `.git`, 在 linked worktree 里返回绝对
    # 路径 —— 不绝对化的话 main_root 会算成 worktree 自己, 双树消歧字段全错。
    common_raw = Path(_git_out(repo, "rev-parse", "--git-common-dir"))
    git_common_dir = (common_raw if common_raw.is_absolute() else repo / common_raw).resolve()

    # ⚠️ main_root **不能**用 git_common_dir.parent 推 —— 那只在 common dir 恰好是
    # `<主工作树>/.git` 时成立。`--separate-git-dir`、submodule(`.git/modules/<name>`)、
    # bare 仓三种拓扑下它都会给出一个「看起来合理但错」的目录, 连带 is_linked_worktree /
    # worktree_rel_to_main / trees.code.kind 一起错。`git worktree list --porcelain` 的
    # **首条恒为主工作树**, 与 git 目录怎么摆无关。
    git_dir_raw = Path(_git_out(repo, "rev-parse", "--git-dir"))
    git_dir = (git_dir_raw if git_dir_raw.is_absolute() else repo / git_dir_raw).resolve()
    # is_linked 取自 git 的结构事实, 不再依赖路径比较是否相等。
    is_linked = git_dir != git_common_dir
    main_root, main_root_source = _main_worktree(repo, worktree, git_dir, git_common_dir)

    return {
        "sha": sha,
        "branch": branch,
        "detached": detached,
        "dirty": False,
        "worktree": str(worktree),
        "worktree_rel_to_main": (os.path.relpath(worktree, main_root) if main_root else None),
        "git_common_dir": str(git_common_dir),
        "git_dir": str(git_dir),
        "main_root": (str(main_root) if main_root else None),
        "main_root_source": main_root_source,
        "is_linked_worktree": is_linked,
        "dirty_scope_caveats": list(DIRTY_SCOPE_CAVEATS),
    }


# ───────────────────────────────────────────────────────────────── 采集


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_locks_present(repo: Path) -> None:
    """依赖锁恰两项, 缺一即拒 —— 不写 null 冒充「本项目无锁」。只查在场, 不算摘要。

    与 `_hash_locks` 拆开是为了让**摘要**与末次 HEAD/status 复核落在同一个时间窗里:
    早早算好的摘要可能属于另一个快照(独立审查 r2 指出的残留时间窗)。
    """
    missing = [rel for rel in DEPENDENCY_LOCKS if not (repo / rel).is_file()]
    if missing:
        raise _Reject("依赖锁缺失: " + ", ".join(missing) + " — 锁文件缺席时不写 null 冒充「无锁」, 先补齐再冻结。")


def _hash_locks(repo: Path) -> list[dict]:
    """算两份锁的 sha256 与字节数。读不动 = 环境错(rc=2), 不是内容不合格。"""
    items: list[dict] = []
    for rel in DEPENDENCY_LOCKS:
        path = repo / rel
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise _Env(f"读依赖锁失败: {path} — {exc}") from exc
        items.append({"path": rel, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    return items


def _collect_vault(vault_root: str | None) -> tuple[dict | None, str | None]:
    """第二棵树 (vault) 的只读记账。只跑 git 读命令, 不写它一个字节。"""
    if vault_root is None:
        return None, (
            "本次冻结未声明 vault 树 (--vault-root 未给)。线上拓扑是「worktree 代码 + "
            "主仓 vault」缝合体, 涉及 vault 数据的旅程须显式声明, 见 README 双树声明。"
        )
    path = Path(vault_root).expanduser()
    if not path.is_dir():
        raise _Env(f"--vault-root 不是目录: {path}")
    proc = _git(path, "rev-parse", "--show-toplevel")
    if proc.returncode != 0:
        raise _Env(f"--vault-root 不在 git 仓内: {path} — {proc.stderr.strip()}")
    resolved = path.resolve()
    return (
        {
            "path": str(resolved),
            "git_head": _git_out(path, "rev-parse", "HEAD"),
            "dirty_entries": len(_porcelain_entries(path, str(resolved))),
        },
        None,
    )


# ───────────────────────────────────────────────────────────────── 校验器


def _validator_evidence_root(validator: Path) -> Path:
    """复算校验器自己的 EVIDENCE_ROOT。

    校验器把它钉死成 `Path(__file__).resolve().parents[2] / "docs" / "release-evidence"`
    —— 不随 cwd 与任何参数变。所以 `--require-complete` 只看得见**校验器所在仓**的证据
    树; `--out-root` 指到树外时这道门根本看不到本次冻结的 rc, 此时记 null + 理由, 而不是
    记一个"跑过且通过"的假象。
    """
    return validator.resolve().parents[2] / "docs" / "release-evidence"


def _run_validator(validator: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(validator), *args],
        capture_output=True,
        text=True,
        cwd=str(validator.resolve().parents[2]),
    )


def _echo_validator(proc: subprocess.CompletedProcess[str], label: str) -> None:
    print(f"── 校验器 {label} (rc={proc.returncode}) ──")
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n")


# ───────────────────────────────────────────────────────────────── freeze


def _existing_rc_for_sha(out_root: Path, sha: str) -> Path | None:
    """out_root 下是否已有一个绑同一个 candidate.sha 的 rc 目录。

    ⚠️ **fail-closed**: 读不出来 / 顶层非对象 / candidate 非对象的旧件一律**拒绝冻结**,
    不 `continue` 跳过。跳过的话, 把旧件弄成不可读或截断就能让判重失效, 而
    「由 check 去报」并没有任何调用链保证(校验器 `--all` 压根不扫 rc-manifest.json)
    —— 独立审查 r2 指出的洞。
    """
    if not out_root.is_dir():
        return None
    for manifest in sorted(out_root.glob(f"*/{RC_MANIFEST_NAME}")):
        try:
            # ValueError 覆盖 json.JSONDecodeError 与 UnicodeDecodeError 两种
            doc = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise _Reject(
                f"out-root 下有一份读不出来的回执: {manifest} — {exc}。"
                " 无法证明本次不是同 SHA 重冻, 故拒绝(fail-closed)。先修好或移走它。"
            ) from exc
        if not isinstance(doc, dict):
            raise _Reject(f"out-root 下的回执顶层不是对象: {manifest} — 同上, fail-closed 拒绝。")
        cand = doc.get("candidate")
        if cand is not None and not isinstance(cand, dict):
            raise _Reject(f"out-root 下的回执 candidate 不是对象: {manifest} — 同上, fail-closed 拒绝。")
        if (cand or {}).get("sha") == sha:
            return manifest.parent
    return None


def _default_rc_name(sha: str) -> str:
    return f"rc-{_dt.datetime.now().strftime('%Y%m%d')}-{sha[:8]}"


def _reject_blank_args(args: argparse.Namespace, *names: str) -> None:
    """空串/纯空白**不是**「没传」, 也**不是**「传了」—— 一律拒, 让调用方明确表态。

    ⚠️ 独立审查实测的反例: 原实现用 `bool(args.index_sha)` 判「给没给」, 于是
    `--index-sha "" --index-sha-null-reason 理由` 两个都给了却照样通过 XOR 门, 并写出
    `index_sha: ""` —— 恰好违反 schema 对该字段的 minLength: 1, 也正是这道门声称要挡的那一格。
    """
    for name in names:
        value = getattr(args, name.lstrip("-").replace("-", "_"), None)
        if value is not None and not value.strip():
            raise _Reject(
                f"{name} 收到空串/纯空白 —— 空值既不是「没给」也不是「给了」。 要么别传这个参数, 要么传一个非空值。"
            )


def _cmd_freeze(args: argparse.Namespace) -> int:
    # ① 纯参数校验 (零 git 调用, fail fast)。镜像 schema 的「禁止省略字段冒充无关」:
    #    index_sha 与 index_sha_null_reason 必须恰给一个。
    _reject_blank_args(args, "--index-sha", "--index-sha-null-reason", "--ci-run-id", "--rc-name", "--vault-root")
    # 判「给没给」看的是 is not None(argparse 未出现即 None), 不是真值 —— 见 _reject_blank_args。
    if (args.index_sha is not None) == (args.index_sha_null_reason is not None):
        raise _Reject(
            "--index-sha 与 --index-sha-null-reason 必须恰给一个 "
            f"(当前: index_sha={args.index_sha!r}, reason={args.index_sha_null_reason!r})。"
            " 索引快照取不到是常态, 但要显式说明理由, 不能省略字段冒充「不涉索引」。"
        )

    # ② git 身份
    repo = _resolve_repo(args.repo)
    candidate = _git_identity(repo)

    # ③ dirty 硬门 —— 必须在任何 mkdir 之前, 拒绝路径零写入
    porcelain_entries = _porcelain_entries(repo)
    dirty = bool(porcelain_entries)
    if dirty:
        shown = porcelain_entries[:20]
        for entry in shown:
            print(f"    {entry}")
        if len(porcelain_entries) > len(shown):
            print(f"    … 另有 {len(porcelain_entries) - len(shown)} 条未列出")
        raise _Reject(
            f"dirty tree ({len(porcelain_entries)} 条未提交条目), 拒绝冻结。"
            " 脏树上跑出来的证据不成立(README/S17), 本脚本没有跳过开关: 先提交或清理, 再冻结。"
        )
    for caveat in DIRTY_SCOPE_CAVEATS:
        print(f"ℹ️  dirty 门覆盖面: {caveat}")

    # ④ 依赖锁(只查在场, 摘要留到末次复核之后算) / vault 树 / 校验器可用性 —— 仍在写入之前
    _assert_locks_present(repo)
    vault, vault_null_reason = _collect_vault(args.vault_root)

    validator = (
        Path(args.validator).expanduser()
        if args.validator
        else Path(__file__).with_name("validate_release_manifest.py")
    )
    if not validator.is_file():
        raise _Env(f"校验器不存在: {validator}")
    # 校验器靠 `parents[2]` 定位自己的仓根。放在浅路径(如 /tmp/v.py)时会 IndexError,
    # 以裸 traceback + rc=1 逃出去 —— 那是环境错, 不是内容不合格(独立审查 r2)。
    if len(validator.resolve().parents) < 3:
        raise _Env(
            f"校验器路径太浅, 无法定位它的仓根: {validator.resolve()} — "
            "它必须位于 <repo>/backend/scripts/ 这样的层级下。"
        )

    # ⑤ rc 名与落点
    rc = args.rc_name or _default_rc_name(candidate["sha"])
    if not _RC_NAME_RE.fullmatch(rc):
        raise _Reject(f"rc 名 {rc!r} 不合法 (须匹配 {_RC_NAME_RE.pattern}) — 只接受目录名, 不接受路径。")
    out_root = Path(args.out_root).expanduser() if args.out_root else repo / "docs" / "release-evidence"
    rc_dir = out_root / rc
    # ⚠️ 上面那条正则**不足以**保证 rc 是个目录名: `.` 与 `..` 都能 fullmatch 它
    # (独立审查实测)。而这条正则是与校验器共享的字面量, 不能单方面收紧, 否则冻出来的
    # 目录名校验器不认。所以在它之外再加一道**包含性**判据: rc_dir 物理解析后必须恰好
    # 是 out_root 的直接子目录。实测原实现下 `--rc-name ..` + 尚不存在的 out-root
    # 会退 0 并把骨架写到 out-root **之外**, 还打印「✅ 已冻结」。
    # 共享正则**不足以**保证 rc 是个可用的目录名, 再加一道「必须是 out-root 的直接子目录」:
    #   - `.` 与 `..` 都能 fullmatch 共享正则(独立审查 r1 实测), 且 out-root 尚不存在时
    #     原实现会退 0 并把骨架写到 out-root **之外**;
    #   - `.rc` 这类前导点名字虽然落点没问题, 但 check 的名字/路径分流把以 `.` 开头的一律
    #     当路径, 两边取值域不一致会让 `check .rc --out-root X` 去验 cwd 下那份(r2 实测)。
    # 这条正则是与校验器共享的字面量, 不能单方面收紧, 所以约束加在它外面。
    # ⚠️ 两条判据合成**一道**门: 分开写时「包含性」那半没有任何独占输入(能逃出 out-root 的
    # 只有 `.`/`..`, 而它们都以 `.` 开头), 于是变异掉它不会让任何裁判变红 —— 一道没有裁判
    # 看管的门迟早会烂。合并后它有唯一且可测的行为(负控 N2 实测)。
    if rc.startswith(".") or rc_dir.resolve().parent != out_root.resolve():
        raise _Reject(
            f"rc 名 {rc!r} 不是一个可用的落点名: 不得以 '.' 开头(与 check 的名字/路径分流口径统一), "
            f"且解析后必须是 --out-root 的直接子目录(本次会落到 {rc_dir.resolve()}, "
            f"而 out-root 是 {out_root.resolve()})。"
        )
    if rc_dir.exists():
        raise _Reject(
            f"落点已存在: {rc_dir} — 同名 rc 不覆盖。要重冻结先按 README「RC 冻结与重跑规则」"
            "处理(代码变了就是新 SHA 新 rc; 没变就复用已有 rc)。"
        )
    # 「一个 SHA 一个 rc」必须按 **SHA** 判, 不能只按目录名 —— 否则同一个干净 SHA 换个
    # --rc-name(或跨日让默认名里的日期变一下)就能再冻一个, README 那条硬规则形同虚设。
    duplicate = _existing_rc_for_sha(out_root, candidate["sha"])
    if duplicate is not None:
        raise _Reject(
            f"同一个 SHA 已经冻结过: {duplicate.name} (candidate.sha = {candidate['sha']})。"
            " 一个 SHA 一个 RC —— 要新 rc 就先产生新 SHA; 想往旧 rc 补 journey 证据无需再冻结。"
        )

    # ⑥ 校验器 --all: 骨架不得让既有证据树失自洽 —— 先跑, 不过就不写
    all_proc = _run_validator(validator, "--all")
    _echo_validator(all_proc, "--all")
    if all_proc.returncode == EXIT_ENV:
        raise _Env("校验器 --all 报环境错 (rc=2), 原样透传。冻结中止, 未写入任何文件。")
    if all_proc.returncode != EXIT_OK:
        raise _Reject(
            f"校验器 --all 不通过 (rc={all_proc.returncode}) — 既有证据树已经不自洽, "
            "在它上面冻结 RC 只会把问题固化。先修既有 manifest。"
        )

    # ⑦ 写入前复核身份 —— ⑥ 那个 subprocess 是整条链路最长的一段, 它跑的时候工作树
    #    可能被人改了、HEAD 可能被切走。不复核的话, 旧 SHA + 后读的锁 + dirty=false
    #    会一起出现在同一份回执里(独立审查指出的时间窗)。
    sha_now = _git_out(repo, "rev-parse", "HEAD")
    if sha_now != candidate["sha"]:
        raise _Reject(
            f"冻结期间 HEAD 变了 ({candidate['sha'][:12]}… → {sha_now[:12]}…) — 拒绝写入。"
            " 回执必须是某一个时刻的快照, 不能是跨越多个状态的拼盘。"
        )
    if _porcelain_entries(repo):
        raise _Reject("冻结期间工作树变脏 — 拒绝写入(同上: 回执必须是单一时刻的快照)。")
    candidate["rechecked_before_write"] = True

    # 锁摘要在这里才算 —— 与上面这次 HEAD/status 复核同窗。早早算好的摘要可能属于
    # 另一个快照(独立审查 r2: 首次 status 之后改锁、末次 status 之前改回即可)。
    locks = _hash_locks(repo)

    # ⑧ 到这里才第一次写入。
    # ⚠️ 软链竞态(独立审查 r2 判 HIGH): 包含性检查发生在校验器 subprocess **之前**,
    #    那几秒里 rc_dir 可能被做成指向外部目录的软链, 于是 `mkdir(parents=True)` 会跟着
    #    软链把骨架建到 out-root 外, `write_text` 还能截断那边已有的回执。
    #    对策是**用创建动作本身做判据**: `os.mkdir` 对已存在的任何东西(含软链)都抛
    #    FileExistsError, 是原子的; 建成之后再复核一次「它确实是 out-root 下的真目录」。
    try:
        out_root.mkdir(parents=True, exist_ok=True)
        os.mkdir(rc_dir)  # 不用 parents=True: 要的就是「已存在即失败」这个原子语义
    except FileExistsError as exc:
        raise _Reject(f"落点在校验期间被创建了: {rc_dir} — 拒绝写入(疑似竞态)。") from exc
    except OSError as exc:
        raise _Env(f"建 rc 目录失败: {rc_dir} — {exc}") from exc
    if rc_dir.is_symlink() or rc_dir.resolve().parent != out_root.resolve():
        raise _Env(f"建出来的 rc 目录不在 out-root 下: {rc_dir.resolve()} — 中止(疑似竞态)。")
    try:
        (rc_dir / "journeys").mkdir()
        (rc_dir / "journeys" / ".gitkeep").write_text("", encoding="utf-8")
    except OSError as exc:
        raise _Env(f"建 rc 骨架失败: {rc_dir} — {exc}") from exc

    # ⑨ --require-complete 只在 out_root 就是校验器的证据根时才有意义
    evidence_root = _validator_evidence_root(validator)
    require_complete: dict | None = None
    require_complete_skip_reason: str | None = None
    if out_root.resolve() == evidence_root.resolve():
        rq_proc = _run_validator(validator, "--require-complete", rc)
        _echo_validator(rq_proc, f"--require-complete {rc}")
        missing = [line.strip() for line in rq_proc.stdout.splitlines() if "[RC] 缺 " in line]
        require_complete = {"exit_code": rq_proc.returncode, "missing": missing}
    else:
        require_complete_skip_reason = (
            f"--out-root ({out_root.resolve()}) 不是校验器钉死的证据根 ({evidence_root}), "
            "--require-complete 看不见本 rc, 故未跑。冻结当刻本就缺 J01–J10, "
            f"预期清单见 journeys_expected ({len(JOURNEYS_EXPECTED)} 条)。"
        )

    doc = {
        "rc_manifest_version": RC_MANIFEST_VERSION,
        "rc": rc,
        "frozen_at": _dt.datetime.now().astimezone().isoformat(),
        "candidate": candidate,
        "trees": {
            "code": {
                "path": candidate["worktree"],
                "kind": "linked-worktree" if candidate["is_linked_worktree"] else "main",
            },
            "vault": vault,
            "vault_null_reason": vault_null_reason,
        },
        "dependency_locks": locks,
        "index_sha": args.index_sha,
        "index_sha_null_reason": args.index_sha_null_reason,
        "ci_run_id": args.ci_run_id or os.environ.get("GITHUB_RUN_ID") or None,
        "ci_run_id_null_reason": None,
        "validator": {
            "script": _rel_to_repo(validator, validator.resolve().parents[2]),
            "schema_sha256": _schema_sha256(evidence_root),
            "all_exit_code": all_proc.returncode,
            "require_complete": require_complete,
            "require_complete_skip_reason": require_complete_skip_reason,
        },
        "journeys_expected": list(JOURNEYS_EXPECTED),
        "environment": {
            "host_os": platform.platform(),
            "git_version": _git_out(repo, "--version"),
            "python_version": platform.python_version(),
        },
        "notes": NOTES,
    }
    if doc["ci_run_id"] is None:
        doc["ci_run_id_null_reason"] = "本地冻结, 无 CI 运行 (未给 --ci-run-id, 环境亦无 GITHUB_RUN_ID)。"

    try:
        _write_json(rc_dir / RC_MANIFEST_NAME, doc)
    except OSError as exc:
        raise _Env(f"写 {RC_MANIFEST_NAME} 失败: {rc_dir} — {exc}") from exc
    print(f"✅ 已冻结 {rc}")
    print(f"    落点   {rc_dir}")
    print(f"    sha    {candidate['sha']}")
    print(f"    树     {doc['trees']['code']['kind']} @ {candidate['worktree_rel_to_main']}")
    return EXIT_OK


def _rel_to_repo(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def _schema_sha256(evidence_root: Path) -> str | None:
    schema = evidence_root / "manifest.schema.json"
    if not schema.is_file():
        return None
    try:
        return _sha256_file(schema)
    except OSError as exc:
        raise _Env(f"读 schema 指纹失败: {schema} — {exc}") from exc


def _write_json(path: Path, doc: dict) -> None:
    path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


# ───────────────────────────────────────────────────────────────── check

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


def _resolve_rc_dir(args: argparse.Namespace) -> Path:
    """把位置参数解析成一个 rc 目录。**名字优先按 --repo/--out-root 解析, 不看 cwd。**

    ⚠️ 原实现先试 `Path(rc_dir).is_dir()`(相对 cwd), 于是在 cwd 下恰好有个同名目录时,
    它会静默压过显式给的 `--repo` / `--out-root` —— 你以为在验候选树的 rc, 实际验的是
    手边那个同名目录, 而成功行只打 rc 名不打路径, 看不出验错了树(独立审查实测)。
    """
    raw = args.rc_dir
    looks_like_path = ("/" in raw) or raw.startswith((".", "~")) or Path(raw).is_absolute()

    if not looks_like_path and _RC_NAME_RE.fullmatch(raw):
        # 是个**名字** —— 只按显式作用域解析, 绝不回落到 cwd。
        repo = _resolve_repo(args.repo)
        out_root = Path(args.out_root).expanduser() if args.out_root else repo / "docs" / "release-evidence"
        named = out_root / raw
        if named.is_dir():
            return named.resolve()
        raise _Reject(f"rc 目录不存在: {named} (按 rc 名在 --out-root 下解析; 要指路径请写成路径)")

    path = Path(raw).expanduser()
    if path.is_dir():
        return path.resolve()
    raise _Reject(f"rc 目录不存在: {path.resolve()}")


def _cmd_check(args: argparse.Namespace) -> int:
    rc_dir = _resolve_rc_dir(args)
    manifest_path = rc_dir / RC_MANIFEST_NAME

    problems: list[str] = []
    if not manifest_path.is_file():
        raise _Reject(f"{rc_dir} 下没有 {RC_MANIFEST_NAME} — 这不是一个冻结出来的 rc 目录。")
    try:
        # ValueError 同时覆盖 json.JSONDecodeError 与 UnicodeDecodeError —— 后者在
        # 文件含非法 UTF-8 字节时抛出, 原先不在捕获范围内, 会以裸 traceback 收场。
        doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise _Reject(f"{RC_MANIFEST_NAME} 读不出来: {exc}") from exc
    if not isinstance(doc, dict):
        raise _Reject(f"{RC_MANIFEST_NAME} 顶层不是对象。")

    keys = set(doc)
    if keys != _EXPECTED_TOP_KEYS:
        if keys - _EXPECTED_TOP_KEYS:
            problems.append(f"rc-manifest 多出字段: {sorted(keys - _EXPECTED_TOP_KEYS)}")
        if _EXPECTED_TOP_KEYS - keys:
            problems.append(f"rc-manifest 缺字段: {sorted(_EXPECTED_TOP_KEYS - keys)}")

    candidate = doc.get("candidate")
    if candidate is not None and not isinstance(candidate, dict):
        # 与 journey 侧同型: 非 dict 真值会让 .get 抛 AttributeError 崩掉整轮。
        raise _Reject(f"{RC_MANIFEST_NAME} 的 candidate 不是对象 (实得 {type(candidate).__name__})。")
    candidate = candidate or {}
    rc_sha = candidate.get("sha")
    if not (isinstance(rc_sha, str) and _SHA_RE.fullmatch(rc_sha)):
        problems.append(f"candidate.sha 不是合法 40 位 SHA: {rc_sha!r}")
    if candidate.get("dirty") is not False:
        problems.append(f"candidate.dirty={candidate.get('dirty')!r} — RC 冻结件恒 false, 脏树证据不成立。")
    if doc.get("rc") != rc_dir.name:
        problems.append(f"rc 字段 {doc.get('rc')!r} 与目录名 {rc_dir.name!r} 不符 — 校验器 S6 要求两者一致。")

    # 逐份 journey 比对, 不做「至少一份一致」
    journeys_dir = rc_dir / "journeys"
    present: list[str] = []
    for jid in JOURNEYS_EXPECTED:
        jpath = journeys_dir / jid / "manifest.json"
        if not jpath.is_file():
            continue
        present.append(jid)
        try:
            jdoc = json.loads(jpath.read_text(encoding="utf-8"))  # ValueError 含非法编码
        except (OSError, ValueError) as exc:
            problems.append(f"{jid} manifest 读不出来: {exc}")
            continue
        if not isinstance(jdoc, dict):
            problems.append(f"{jid} manifest 顶层不是对象")
            continue
        jcand = jdoc.get("candidate")
        if jcand is not None and not isinstance(jcand, dict):
            # 手填成 "candidate": "<sha>" 这类真值非 dict 时, 原实现 .get 抛 AttributeError
            # 直接崩掉 —— 已攒下的问题全丢, 后面的 journey 一份都不再比对(独立审查实测)。
            problems.append(f"{jid} 的 candidate 不是对象 (实得 {type(jcand).__name__}), 无法取 sha")
            continue
        jsha = (jcand or {}).get("sha")
        if jsha != rc_sha:
            problems.append(f"{jid} sha 不一致: journey={jsha!r} rc-manifest={rc_sha!r}")
        else:
            print(f"✅ {jid} candidate.sha 与 rc-manifest 一致")

    if problems:
        print(f"{_REJECT_MARK} check 不通过 ({rc_dir.name} @ {rc_dir}):")
        for problem in problems:
            print(f"    {problem}")
        return EXIT_REJECT

    if present:
        print(f"✅ check 通过 ({rc_dir.name}): 在场的 {len(present)} 条 journey 全部绑同一个 candidate.sha")
    else:
        # ⚠️ 空集上「全部 X 满足 P」恒真 —— 照上面那句打, rc=0 会被读成「这个 RC 验过了」,
        # 而实际上一条 candidate.sha 都没比对过。零 journey 必须换一句话说清楚。
        print(f"✅ check 通过 ({rc_dir.name}): rc-manifest 自洽; 在场 0 条 journey, 本次未比对任何 candidate.sha")
    print(f"    sha {rc_sha}")
    # 诚实边界: 这条命令只证明「绑定一致」。结构合法性归校验器 --all, RC 完整性归
    # --require-complete, symlink 冒充多条旅程归 check_rc_completeness —— 都不在这里。
    print(
        "ℹ️  本命令只核 candidate.sha 绑定一致, **未验** journey manifest 的 schema 结构、"
        "未验 symlink 冒充、未判 RC 完整性(那是校验器 --all / --require-complete 的事)。"
    )
    absent = [jid for jid in JOURNEYS_EXPECTED if jid not in present]
    if absent:
        # 只打印不判红 —— 判红归校验器 --require-complete, 那才是 RC 发布门。
        print(f"ℹ️  尚缺 {len(absent)} 条 journey: {' '.join(absent)}")
    return EXIT_OK


# ───────────────────────────────────────────────────────────────── CLI


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="clean release candidate 冻结脚本 (CARD-R-RC)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    fr = sub.add_parser("freeze", help="冻结当前 HEAD, 生成 <out-root>/<rc>/ 骨架")
    fr.add_argument("--repo", help="代码仓路径 (默认 cwd 所在仓)")
    fr.add_argument("--out-root", help="rc 目录的落点根 (默认 <repo>/docs/release-evidence)")
    fr.add_argument("--rc-name", help="rc 目录名 (默认 rc-<YYYYMMDD>-<sha[:8]>)")
    fr.add_argument("--index-sha", help="检索索引快照标识; 与 --index-sha-null-reason 二选一")
    fr.add_argument(
        "--index-sha-null-reason",
        help="取不到索引 SHA 时的理由 (禁止省略字段冒充「不涉索引」)",
    )
    fr.add_argument("--ci-run-id", help="CI 运行标识 (默认读环境变量 GITHUB_RUN_ID)")
    fr.add_argument("--vault-root", help="vault 树路径 (只读记账; 不给则记 null + 理由)")
    fr.add_argument("--validator", help="校验器路径 (默认本脚本同目录的 validate_release_manifest.py)")
    fr.set_defaults(func=_cmd_freeze)

    ck = sub.add_parser("check", help="核 rc-manifest 自洽, 且各 journey 的 candidate.sha 与它一致")
    ck.add_argument("rc_dir", help="rc 目录路径, 或 rc 名 (配合 --repo / --out-root 解析)")
    ck.add_argument("--repo", help="代码仓路径 (rc_dir 给的是名字时用来定位)")
    ck.add_argument("--out-root", help="rc 目录的落点根 (同上)")
    ck.set_defaults(func=_cmd_check)

    return parser


def _run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return args.func(args)
    except _Reject as exc:
        print(f"{_REJECT_MARK} {exc}")
        return EXIT_REJECT
    except _Env as exc:
        print(f"{_ENV_MARK} {exc}", file=sys.stderr)
        return EXIT_ENV


def main() -> int:  # pragma: no cover - 薄封装
    return _run()


if __name__ == "__main__":
    raise SystemExit(main())
