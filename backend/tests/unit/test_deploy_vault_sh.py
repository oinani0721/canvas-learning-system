# CARD-G2-7b (BATCH-2026-09-07-第十三批) — scripts/deploy-vault.sh 的裁判
#
# 被测物: scripts/deploy-vault.sh（六步 + rc 表 + 禁写面 realpath 判据）
#         + docker-compose.yml 的 5 处 container_name 参数化（缺省等价门）
# 真相源: 脚本头注的参数全表与 rc 表; docker compose config 的渲染结果。
#
# 全部 subprocess 调脚本, 只 dry-run 或写 tmp_path。禁写面用例把 CLS_LIVE_VAULT
# 覆盖成 tmp 下的假 live —— 判据逻辑同真 live, 但测试不依赖本机真 live 存在、
# 也绝不去碰它（如实声明: 真 live 路径的那一条由车道负控存档覆盖, 见
# evidence-g27b/neg-live-vault-*.txt）。
#
# 钉死点:
#   1. rc 表: 0 / 64 用法错 / 7N 第 N 步。每条断言**同时**核 rc 数字与消息片段 ——
#      光看「非零」会把「脚本因 set -u 崩了(rc=1)」读成「判据拦住了(rc=71)」。
#      这不是假想: 本卡实测过三次 —— `"$abs）"` 里全角括号紧跟变量被 bash 吃进
#      变量名, set -u 报 unbound, rc=1 而不是 71, 消息里也没有「禁写面」。
#   2. 非 ASCII 紧跟变量门(test_no_var_ref_followed_by_non_ascii): 上面那个坑在本卡
#      **总共踩了 6 次** —— 存量 8 处 + 我自己在 step4/step5/HIGH-1 整改/MEDIUM-2 整改里
#      又新引入 4 次, 每次都是「写中文消息时顺手用了全角括号」。靠记性无效, 只能靠门。
#      Codex r1 LOW-1 又指出它对 bash 续行是瞎的 ⇒ 现在按**逻辑行**扫(见 _logical_lines)。
#   3. 禁写面判据必须覆盖 --vault / --evidence-dir / --env-dir **三个**路径参数;
#      只测 --vault 会让另两个零覆盖。
#   4. compose 缺省等价: 不传 CLS_*_CONTAINER 时, config 渲染与**参数化之前**的
#      版本逐字节相同; 且单独覆盖任一变量只改它自己那一行。
#      ⚠️ 取名面必须含全部 5 处 ⇒ 必须带 --profile test/windows/dev,
#      否则 config 只渲染 neo4j + backend 两个服务, 另 3 处改动零覆盖。
#   5. 端口模板化清单单一来源: 步 3 与步 4(源镜像) 共用 $PORT_TEMPLATED_FILES,
#      两份清单各自漂移会让「目标已特化 vs 基准未特化」重新变成假 drift。

from __future__ import annotations

import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
DEPLOY_SH = REPO_ROOT / "scripts" / "deploy-vault.sh"
COMPOSE = REPO_ROOT / "docker-compose.yml"

CONTAINER_VARS = {
    "CLS_NEO4J_CONTAINER": "canvas-learning-system-neo4j",
    "CLS_NEO4J_TEST_CONTAINER": "canvas-learning-system-neo4j-test",
    "CLS_OLLAMA_CONTAINER": "canvas-learning-system-ollama",
    "CLS_BACKEND_CONTAINER": "canvas-learning-system-backend",
    "CLS_DEV_CONTAINER": "claude-dev",
}
ALL_PROFILES = ["--profile", "test", "--profile", "windows", "--profile", "dev"]

#: 本文件**每一处** subprocess.run 的墙钟兜底（CARD-DEPLOY-TIMEOUT，集成期裁定 R-15）。
#: 原来 16 处裸跑一个上限都没有 —— 候选树跑 tests/unit 时，真跑 DEPLOY_SH 的用例
#: 在步 1 的 `npm run build` 上逐个**无限挂起**，整份文件永远跑不完（挂起的那一跑
#: 连报错都没有，只是不返回）。
#: 取 600 的依据：① 与集成期单点补丁 `3966ddad` 给 `:1874` 打的 `timeout=600` 同值，
#: 不在同一份文件里立两套口径；② 它是**兜底**，不是主防线 —— 主防线是脚本自己的
#: `CLS_NPM_BUILD_TIMEOUT`（缺省 300s）。取其 2 倍 ⇒ 正常情况下先看到脚本的超时文案
#: （能指出哪一步超时），只有脚本上限本身失效时才由这里兜住。
#: ⚠️ 未逐跑实测最坏耗时（见验收单「本卡未证明什么」④）：这是保守上限，不是紧界。
_SUBPROCESS_TIMEOUT = 600


#: 必须从继承环境里剥掉的开关（Codex r2 HIGH-1）。
#: `_run` 继承整个 os.environ；宿主若设了 CLS_DEPLOY_ALLOW_DOCKER_UP=1，
#: 「缺省不 up」那条用例会**先真起容器**再断言 SKIP —— 断言发生在脚本跑完之后，
#: 拦不住启动。这是 r1 把闸门反转成 opt-in 之后留下的新回归。
_STRIP_ENV = ("CLS_DEPLOY_ALLOW_DOCKER_UP", "CLS_MIN_SKILLS", "CLS_LIVE_VAULT")


def _run(
    *args: str,
    env: dict[str, str] | None = None,
    timeout: int = 120,
    script: Path | None = None,
):
    """跑 deploy-vault.sh，返回 CompletedProcess（不 check）。"""
    full_env = dict(os.environ)
    for _k in _STRIP_ENV:
        full_env.pop(_k, None)
    if env:
        full_env.update(env)
    return subprocess.run(
        [str(script or DEPLOY_SH), *args],
        capture_output=True,
        text=True,
        env=full_env,
        cwd=str(REPO_ROOT),
        timeout=timeout,
    )


def _fake_live(tmp_path: Path) -> Path:
    """建一个 tmp 下的假 live vault，用 CLS_LIVE_VAULT 指向它。"""
    lv = tmp_path / "fake-live-vault"
    lv.mkdir(parents=True, exist_ok=True)
    return lv


# ═══ ① bash -n ══════════════════════════════════════════════════════════════
def test_deploy_vault_sh_parses():
    r = subprocess.run(["bash", "-n", str(DEPLOY_SH)], capture_output=True, text=True, timeout=_SUBPROCESS_TIMEOUT)
    assert r.returncode == 0, f"bash -n rc={r.returncode}: {r.stderr}"


def test_deploy_vault_sh_is_executable():
    assert os.access(DEPLOY_SH, os.X_OK), f"{DEPLOY_SH} 不可执行"


# ═══ ② --help ═══════════════════════════════════════════════════════════════
HELP_FLAGS = [
    "--vault",
    "--harness",
    "--port",
    "--hosts",
    "--subject",
    "--apply",
    "--activate",
    "--also-push",
    "--evidence-dir",
    "--env-dir",
]


def test_help_lists_six_steps_and_rc_table():
    r = _run("--help")
    assert r.returncode == 0, f"--help rc={r.returncode}"
    out = r.stdout
    for n, name in enumerate(["preflight", "install", "postprocess", "verify", "activate", "evidence"], start=1):
        assert f"[{n}/6]" in out, f"--help 缺 [{n}/6]"
        assert name in out, f"--help 缺步名 {name}"
    for rc in ["64", "71", "72", "73", "74", "75", "76"]:
        assert rc in out, f"--help 的 rc 表缺 {rc}"


@pytest.mark.parametrize("flag", HELP_FLAGS)
def test_help_lists_every_flag(flag: str):
    """每个参数逐条断言 —— 漏一个就是「测试调了一个 --help 里没定义的开关」。"""
    r = _run("--help")
    assert r.returncode == 0
    assert flag in r.stdout, f"--help 未列出 {flag}"


def test_help_documents_env_dir_default_is_harness():
    """--env-dir 的缺省必须写明是 <harness>/ —— 它决定 .env.<vault> 落哪。"""
    r = _run("--help")
    line = next((ln for ln in r.stdout.splitlines() if "--env-dir" in ln), "")
    assert line, "--help 没有 --env-dir 那一行"
    assert "<harness>" in line, f"--env-dir 行未写明缺省 <harness>/: {line!r}"


# ═══ ③④⑦ 用法错与端口 ═══════════════════════════════════════════════════════
def test_missing_vault_is_usage_error():
    r = _run("--harness", str(REPO_ROOT))
    assert r.returncode == 64, f"rc={r.returncode}"
    assert "--vault" in r.stderr


def test_no_args_is_usage_error():
    r = _run()
    assert r.returncode == 64, f"rc={r.returncode}"


def test_unknown_flag_is_usage_error():
    r = _run("--vault", "/tmp/x", "--harness", str(REPO_ROOT), "--no-such-flag")
    assert r.returncode == 64, f"rc={r.returncode}"
    assert "未知参数" in r.stderr


@pytest.mark.parametrize("host", ["codex", "opencode", "dsh", "claude,codex"])
def test_second_tier_hosts_rejected_with_e1(tmp_path: Path, host: str):
    """E-1: 本版只 claude。消息必须点名 E-1，否则读者不知道这是「等实测表」而非 bug。"""
    r = _run(
        "--vault",
        str(tmp_path / "v"),
        "--harness",
        str(REPO_ROOT),
        "--hosts",
        host,
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
    )
    assert r.returncode == 64, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    assert "E-1" in r.stderr, f"消息未点名 E-1: {r.stderr!r}"


def test_activate_without_apply_is_usage_error(tmp_path: Path):
    r = _run(
        "--vault",
        str(tmp_path / "v"),
        "--harness",
        str(REPO_ROOT),
        "--activate",
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
    )
    assert r.returncode == 64, f"rc={r.returncode}"
    assert "--activate" in r.stderr


@pytest.mark.parametrize("port", ["7691", "7692", "7478", "11434"])
def test_reserved_ports_rejected_in_preflight(tmp_path: Path, port: str):
    r = _run(
        "--vault",
        str(tmp_path / "v"),
        "--harness",
        str(REPO_ROOT),
        "--port",
        port,
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
    )
    assert r.returncode == 71, f"port {port} rc={r.returncode}: {r.stdout}"
    assert "端口" in r.stdout


def test_non_numeric_port_is_usage_error(tmp_path: Path):
    r = _run("--vault", str(tmp_path / "v"), "--harness", str(REPO_ROOT), "--port", "80a1")
    assert r.returncode == 64, f"rc={r.returncode}"


# ═══ ⑤ 禁写面：三个路径参数 × 多种命中形态 ═══════════════════════════════════
def test_forbidden_surface_covers_vault_param(tmp_path: Path):
    lv = _fake_live(tmp_path)
    r = _run(
        "--vault",
        str(lv),
        "--harness",
        str(REPO_ROOT),
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(lv)},
    )
    assert r.returncode == 71, f"rc={r.returncode}: {r.stdout}"
    assert "禁写面" in r.stdout
    assert "--vault" in r.stdout, f"消息未点名被拦的参数: {r.stdout!r}"


def test_forbidden_surface_covers_vault_inside_live(tmp_path: Path):
    """位于 live vault **之下**（不只等于）也必须拦。"""
    lv = _fake_live(tmp_path)
    r = _run(
        "--vault",
        str(lv / "nested" / "deep"),
        "--harness",
        str(REPO_ROOT),
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(lv)},
    )
    assert r.returncode == 71, f"rc={r.returncode}: {r.stdout}"
    assert "禁写面" in r.stdout


def test_forbidden_surface_covers_dot_git_segment(tmp_path: Path):
    """路径中任何一段名为 .git ⇒ 拦（不限 <harness>/.git）。"""
    g = tmp_path / "somerepo" / ".git"
    g.mkdir(parents=True)
    r = _run(
        "--vault",
        str(g / "v"),
        "--harness",
        str(REPO_ROOT),
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
    )
    assert r.returncode == 71, f"rc={r.returncode}: {r.stdout}"
    assert "禁写面" in r.stdout
    assert ".git" in r.stdout


@pytest.mark.parametrize("name", ["a.env", ".env", ".env.probe"])
def test_forbidden_surface_covers_env_files(tmp_path: Path, name: str):
    r = _run(
        "--vault",
        str(tmp_path / name),
        "--harness",
        str(REPO_ROOT),
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
    )
    assert r.returncode == 71, f"{name} rc={r.returncode}: {r.stdout}"
    assert "禁写面" in r.stdout


def test_forbidden_surface_covers_evidence_dir_param(tmp_path: Path):
    """⛔ 只查 --vault 会让 --evidence-dir 零覆盖 —— evidence 会真写进禁写目录。"""
    lv = _fake_live(tmp_path)
    r = _run(
        "--vault",
        str(tmp_path / "vaults" / "ok_name"),
        "--harness",
        str(REPO_ROOT),
        "--evidence-dir",
        str(lv / "evidence"),
        "--env-dir",
        str(tmp_path / "env"),
        env={"CLS_LIVE_VAULT": str(lv)},
    )
    assert r.returncode == 71, f"rc={r.returncode}: {r.stdout}"
    assert "--evidence-dir" in r.stdout, f"消息未点名 --evidence-dir: {r.stdout!r}"
    assert not (lv / "evidence").exists(), "被拦之前就已经写了 = 拦晚了"


def test_forbidden_surface_covers_env_dir_param(tmp_path: Path):
    """⛔ 同上：--env-dir 决定 .env.<vault> 落哪，零覆盖 = 密钥可能落进禁写目录。"""
    lv = _fake_live(tmp_path)
    r = _run(
        "--vault",
        str(tmp_path / "vaults" / "ok_name"),
        "--harness",
        str(REPO_ROOT),
        "--env-dir",
        str(lv / "envs"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(lv)},
    )
    assert r.returncode == 71, f"rc={r.returncode}: {r.stdout}"
    assert "--env-dir" in r.stdout, f"消息未点名 --env-dir: {r.stdout!r}"
    assert not (lv / "envs").exists(), "被拦之前就已经写了 = 拦晚了"


def test_forbidden_surface_resolves_relative_and_dotdot(tmp_path: Path):
    """判据必须解 realpath：`<live>/../<live 名>` 这类别名不能绕过。"""
    lv = _fake_live(tmp_path)
    alias = str(lv / ".." / lv.name)
    r = _run(
        "--vault",
        alias,
        "--harness",
        str(REPO_ROOT),
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(lv)},
    )
    assert r.returncode == 71, f"别名绕过了判据: rc={r.returncode} {r.stdout}"
    assert "禁写面" in r.stdout


def test_forbidden_surface_resolves_symlink(tmp_path: Path):
    """软链指向 live ⇒ 解开后仍须拦。"""
    lv = _fake_live(tmp_path)
    link = tmp_path / "link-to-live"
    link.symlink_to(lv, target_is_directory=True)
    r = _run(
        "--vault",
        str(link),
        "--harness",
        str(REPO_ROOT),
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(lv)},
    )
    assert r.returncode == 71, f"软链绕过了判据: rc={r.returncode} {r.stdout}"
    assert "禁写面" in r.stdout


# ═══ vault 名不动点（两套命名口径不得分裂）═══════════════════════════════════
@pytest.mark.parametrize("bad", ["probe-b13", "Probe", "probe b13"])
def test_vault_name_must_be_fixpoint_of_both_naming_functions(tmp_path: Path, bad: str):
    """sanitize_vault_id（后端）与 vault_key（推送链）必须给出同一个名字。

    `probe-b13` 这类含 `-` 的名字: sanitize 变 `probe_b13`、vault_key 原样 ⇒ 后端与
    推送链指向不同 key（决策页 §二 G4 的分裂本体）。preflight 必须拒。
    """
    r = _run(
        "--vault",
        str(tmp_path / "vaults" / bad),
        "--harness",
        str(REPO_ROOT),
        "--port",
        "8199",
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
    )
    assert r.returncode == 71, f"{bad!r} rc={r.returncode}: {r.stdout}"
    assert "不动点" in r.stdout, f"消息未说明不动点: {r.stdout!r}"


# ═══ ⑥ dry-run 正控：零写 ═══════════════════════════════════════════════════
def test_dry_run_prints_six_lines_and_writes_nothing(tmp_path: Path):
    target = tmp_path / "vaults" / "probe_dry"
    evd = tmp_path / "ev"
    envd = tmp_path / "env"
    r = _run(
        "--vault",
        str(target),
        "--harness",
        str(REPO_ROOT),
        "--port",
        "8198",
        "--hosts",
        "claude",
        "--env-dir",
        str(envd),
        "--evidence-dir",
        str(evd),
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
    )
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    lines = re.findall(r"^\[(\d)/6\] (\w+): (OK|SKIP|FAIL)", r.stdout, re.M)
    assert len(lines) == 6, f"六行不全: {lines}"
    assert [n for n, _, _ in lines] == list("123456"), f"步序不对: {lines}"
    assert not any(st == "FAIL" for _, _, st in lines), f"dry-run 有 FAIL: {lines}"
    # 零写：三个落点目录都不该被创建
    assert not target.exists(), "dry-run 建了目标 vault"
    assert not evd.exists(), "dry-run 写了 evidence（『不传 --apply = 零写』被破）"
    assert not (envd / "probe_dry").exists() and not list(envd.glob(".env.*")) if envd.exists() else True


def test_dry_run_step6_is_skip_not_ok(tmp_path: Path):
    """步 6 在 dry-run 下必须 SKIP —— OK 意味着它真落盘了。"""
    r = _run(
        "--vault",
        str(tmp_path / "vaults" / "probe_dry2"),
        "--harness",
        str(REPO_ROOT),
        "--port",
        "8197",
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
    )
    assert r.returncode == 0
    assert re.search(r"^\[6/6\] evidence: SKIP", r.stdout, re.M), r.stdout


# ═══ ⑧ compose 缺省等价 ═════════════════════════════════════════════════════
def _compose_config(compose_path: Path, project_dir: Path, env: dict[str, str] | None = None):
    """渲染 compose config。

    Codex r1 LOW-2：必须先从继承的环境里**清掉** CLS_*_CONTAINER —— 否则「不传变量」
    这个前提不成立（测试继承整个 os.environ，宿主若设过其中任一个，缺省等价门比的
    就不是默认环境）。要覆盖某个变量的用例通过 env 参数显式传入。
    """
    full_env = dict(os.environ)
    for _k in CONTAINER_VARS:
        full_env.pop(_k, None)
    if env:
        full_env.update(env)
    return subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(compose_path),
            "--project-directory",
            str(project_dir),
            *ALL_PROFILES,
            "config",
        ],
        capture_output=True,
        text=True,
        env=full_env,
        timeout=120,
    )


def _pre_parameterization_compose() -> str | None:
    """取参数化**之前**那一版 docker-compose.yml 的内容。

    按内容找（不写死 SHA —— 写死会过期, 见 memory「引用的历史数字会过期」）:
    沿着 docker-compose.yml 的提交史往回, 第一个不含 CLS_BACKEND_CONTAINER 的版本。
    """
    log = subprocess.run(
        ["git", "log", "--format=%H", "--", "docker-compose.yml"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=_SUBPROCESS_TIMEOUT,
    )
    if log.returncode != 0:
        return None
    for sha in log.stdout.split():
        show = subprocess.run(
            ["git", "show", f"{sha}:docker-compose.yml"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=_SUBPROCESS_TIMEOUT,
        )
        if show.returncode == 0 and "CLS_BACKEND_CONTAINER" not in show.stdout:
            return show.stdout
    return None


@pytest.mark.skipif(
    shutil.which("docker") is None, reason="本机没有 docker CLI —— compose 缺省等价门无法渲染（不静默跳过, 理由在此）"
)
def test_compose_defaults_render_byte_identical_to_pre_parameterization(tmp_path: Path):
    """不传任何 CLS_*_CONTAINER 时, config 渲染必须与参数化前逐字节相同。

    ⚠️ 必须带 --profile test/windows/dev: 缺省只渲染 neo4j + backend 两个服务,
    另 3 处 container_name 改动会完全落在门外（判据取名面 < 它的主张）。
    """
    old = _pre_parameterization_compose()
    if old is None:
        pytest.skip("找不到参数化前的 docker-compose.yml 版本（浅克隆或历史被改写）")
    empty = tmp_path / "empty"
    empty.mkdir()
    old_path = tmp_path / "docker-compose.old.yml"
    old_path.write_text(old, encoding="utf-8")

    r_old = _compose_config(old_path, empty)
    r_new = _compose_config(COMPOSE, empty)
    assert r_old.returncode == 0, f"旧版 config rc={r_old.returncode}: {r_old.stderr[-400:]}"
    assert r_new.returncode == 0, f"新版 config rc={r_new.returncode}: {r_new.stderr[-400:]}"
    assert r_new.stdout == r_old.stdout, (
        "参数化改变了缺省渲染结果（应逐字节相同）:\n"
        + "\n".join(
            f"  {ln}"
            for ln in __import__("difflib").unified_diff(
                r_old.stdout.splitlines(),
                r_new.stdout.splitlines(),
                fromfile="pre-parameterization",
                tofile="HEAD",
                lineterm="",
                n=1,
            )
        )[:2000]
    )


@pytest.mark.skipif(shutil.which("docker") is None, reason="本机没有 docker CLI")
def test_all_five_container_names_are_in_the_gate_scope(tmp_path: Path):
    """验伪锚: 门的取名面必须真含 5 处 —— 否则上一条「逐字节同」是空集比空集。"""
    empty = tmp_path / "empty"
    empty.mkdir()
    r = _compose_config(COMPOSE, empty)
    assert r.returncode == 0, r.stderr[-400:]
    rendered = re.findall(r"^\s*container_name:\s*(\S+)", r.stdout, re.M)
    assert sorted(rendered) == sorted(CONTAINER_VARS.values()), (
        f"渲染出的 container_name 集合与 5 个现网常量不符: {sorted(rendered)}"
    )


@pytest.mark.skipif(shutil.which("docker") is None, reason="本机没有 docker CLI")
@pytest.mark.parametrize("var", sorted(CONTAINER_VARS))
def test_each_container_var_changes_exactly_its_own_line(tmp_path: Path, var: str):
    """单独覆盖任一变量 ⇒ 只改它自己那一行（其余 4 个常量不动）。"""
    empty = tmp_path / "empty"
    empty.mkdir()
    base = _compose_config(COMPOSE, empty)
    assert base.returncode == 0, base.stderr[-400:]
    probe = f"probe-{var.lower().replace('_', '-')}"
    got = _compose_config(COMPOSE, empty, env={var: probe})
    assert got.returncode == 0, got.stderr[-400:]

    rendered = re.findall(r"^\s*container_name:\s*(\S+)", got.stdout, re.M)
    assert rendered.count(probe) == 1, f"{var}={probe} 命中 {rendered.count(probe)} 处（期望 1）"
    others = {v for k, v in CONTAINER_VARS.items() if k != var}
    assert others <= set(rendered), f"覆盖 {var} 时动了别的容器名: {sorted(rendered)}"

    changed = [
        ln
        for ln in __import__("difflib").unified_diff(
            base.stdout.splitlines(), got.stdout.splitlines(), lineterm="", n=0
        )
        if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))
    ]
    assert len(changed) == 2, f"{var} 改了 {len(changed) // 2} 行（期望 1）: {changed}"


# ═══ ⑨⑩ apply / 步 5 / 幂等 ═════════════════════════════════════════════════
def _apply(tmp_path: Path, name: str, port: str, *extra: str, timeout: int = 120):
    env_d = tmp_path / "env"
    ev_d = tmp_path / "ev"
    return _run(
        "--vault",
        str(tmp_path / "vaults" / name),
        "--harness",
        str(REPO_ROOT),
        "--port",
        port,
        "--hosts",
        "claude",
        "--env-dir",
        str(env_d),
        "--evidence-dir",
        str(ev_d),
        "--apply",
        *extra,
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
        timeout=timeout,
    )


@pytest.mark.skipif(
    not (REPO_ROOT / "canvas-vault" / ".obsidian" / "plugins" / "canvas-learning-system" / "main.js").exists(),
    reason="树上没有 gitignored main.js —— apply 会触发 npm run build（联网+耗时），"
    "本用例只验部署逻辑, 不在单测里 build（build 真跑由车道 (e) 存档覆盖）",
)
def test_apply_writes_key_0600_and_syncs_three_places(tmp_path: Path):
    t0 = time.monotonic()
    r = _apply(tmp_path, "probe_ap", "8196")
    elapsed = time.monotonic() - t0
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    assert elapsed < 60, f"apply 耗时 {elapsed:.1f}s 超 60s 门"

    v = tmp_path / "vaults" / "probe_ap"
    keyfile = v / ".obsidian" / "cls-internal-key.txt"
    assert keyfile.is_file(), "key 文件未生成"
    assert oct(keyfile.stat().st_mode)[-3:] == "600", oct(keyfile.stat().st_mode)
    key = keyfile.read_text().strip()
    assert len(key) == 64, f"openssl rand -hex 32 应为 64 字符, 实为 {len(key)}"

    import json

    dj = json.loads((v / ".obsidian" / "plugins" / "canvas-learning-system" / "data.json").read_text())
    assert dj["internalApiKey"] == key, "data.json 的 key 与 key 文件不同"

    envf = tmp_path / "env" / ".env.probe_ap"
    assert envf.is_file(), f".env.probe_ap 未落在 --env-dir: {envf}"
    assert oct(envf.stat().st_mode)[-3:] == "600", oct(envf.stat().st_mode)
    assert f"INTERNAL_API_KEY={key}" in envf.read_text(), ".env 的 key 与 key 文件不同"


@pytest.mark.skipif(
    not (REPO_ROOT / "canvas-vault" / ".obsidian" / "plugins" / "canvas-learning-system" / "main.js").exists(),
    reason="见上：树上无 main.js 时 apply 会 build",
)
def test_apply_templates_port_in_all_four_files(tmp_path: Path):
    r = _apply(tmp_path, "probe_pt", "8195")
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}"
    v = tmp_path / "vaults" / "probe_pt"
    for rel in [
        ".mcp.json",
        ".claude/settings.json",
        ".claude/hooks/session-end-archive.py",
        ".obsidian/plugins/canvas-learning-system/data.json",
    ]:
        txt = (v / rel).read_text(encoding="utf-8")
        assert ":8011" not in txt, f"{rel} 仍有 :8011 残留"
        assert ":8195" in txt, f"{rel} 没有 :8195"


@pytest.mark.skipif(
    not (REPO_ROOT / "canvas-vault" / ".obsidian" / "plugins" / "canvas-learning-system" / "main.js").exists(),
    reason="见上：树上无 main.js 时 apply 会 build",
)
def test_step5_skips_up_when_no_docker_up_flag_set(tmp_path: Path):
    """缺省（不设 CLS_DEPLOY_ALLOW_DOCKER_UP）⇒ 步 5 跑完 config 断言就 SKIP，绝不 up -d。

    Codex r1 HIGH-2: 旧实现的闸门是 CLS_DEPLOY_NO_DOCKER_UP 缺省 0，即「不设开关就真起
    容器」。现在反转成 opt-in —— 本用例**故意不设任何开关**，验证缺省就是不 up。
    """
    if shutil.which("docker") is None:
        pytest.skip("本机没有 docker CLI —— 步 5 的 config 断言无法渲染")
    r = _apply(tmp_path, "probe_a5", "8194", "--activate")
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    m = re.search(r"^\[5/6\] activate: (OK|SKIP|FAIL) (.*)$", r.stdout, re.M)
    assert m, f"没有 [5/6] 行: {r.stdout}"
    assert m.group(1) == "SKIP", f"步 5 应 SKIP, 实为 {m.group(1)}: {m.group(2)}"
    assert "config 断言过" in m.group(2), f"步 5 未做 config 断言: {m.group(2)}"
    # 零容器 —— 三态，不把「问不出来」压成「没有」
    ps = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=_SUBPROCESS_TIMEOUT
    )
    # Codex r1 LOW-1：不能只看 stdout —— docker 查询失败时它是空的，
    # 「空输出里没有那个名字」会被读成「容器没起来」= 假绿。
    # 但 rc≠0 也不该判 FAIL：那是**问不出来**，不是「起来了」。本机实测 daemon 未运行时
    # `docker ps` rc=1，而 `docker compose config` 不需要 daemon，所以别的门照样能跑。
    if ps.returncode == 0:
        assert "cls-probe_a5" not in ps.stdout, "步 5 真起了容器"
    else:
        # 降级证据：步 5 打的是 SKIP（上面已断言过）。如实记：这一支**没有**用
        # docker 侧证据交叉验证「零容器」，只证明脚本自己走的是不 up 的分支。
        assert m.group(1) == "SKIP", (
            f"docker ps 问不出来(rc={ps.returncode})，此时只剩脚本输出这一条证据，而它不是 SKIP: {m.group(0)}"
        )


@pytest.mark.skipif(
    not (REPO_ROOT / "canvas-vault" / ".obsidian" / "plugins" / "canvas-learning-system" / "main.js").exists(),
    reason="见上：树上无 main.js 时 apply 会 build",
)
def test_second_apply_is_blocked_and_changes_nothing(tmp_path: Path):
    """幂等（如实口径）：install 的防覆盖闸门在第二次就拦住 ⇒ 目标零变化。

    ⚠️ 这**不是**「六步重跑一遍结果相同」。install-vault.sh 对已存在目标 exit 66
    ⇒ 步 2 FAIL 72，到不了步 3。所以「key 已存在则不重生」那条分支在端到端层面
    不可达（要它可达需要 adopt 语义, 归 G2-7c）。这里锁住的是更强的性质:
    第二次跑不会动已有 vault 一个字节。
    """
    r1 = _apply(tmp_path, "probe_id", "8193")
    assert r1.returncode == 0, f"首次 rc={r1.returncode}: {r1.stdout}"
    v = tmp_path / "vaults" / "probe_id"
    envf = tmp_path / "env" / ".env.probe_id"

    snap = {p.relative_to(v): p.read_bytes() for p in v.rglob("*") if p.is_file()}
    env_before = envf.read_bytes()

    r2 = _apply(tmp_path, "probe_id", "8193")
    assert r2.returncode == 72, f"第二次应被 install 防覆盖闸门拦成 72, 实为 {r2.returncode}"

    after = {p.relative_to(v): p.read_bytes() for p in v.rglob("*") if p.is_file()}
    assert after == snap, (
        "第二次跑改动了目标 vault: "
        f"新增={sorted(set(after) - set(snap))} 删除={sorted(set(snap) - set(after))} "
        f"改内容={sorted(k for k in set(after) & set(snap) if after[k] != snap[k])}"
    )
    assert envf.read_bytes() == env_before, ".env 被第二次跑改了"


def test_env_file_mismatch_fails_closed_before_any_write(tmp_path: Path):
    """已有 .env.<vault> 与本次参数矛盾 ⇒ 73，且**任何写之前**就拦。

    这条锁的是 Phase A/B 拆分：修复前版本先写 key、后校验 .env，失败时留下
    「key 已写、另两处未同步」的半成品（Codex 问题 ③ 正是问这个）。
    """
    if not (REPO_ROOT / "canvas-vault" / ".obsidian" / "plugins" / "canvas-learning-system" / "main.js").exists():
        pytest.skip("树上无 main.js 时 apply 会 build")
    env_d = tmp_path / "env"
    env_d.mkdir()
    (env_d / ".env.probe_mm").write_text(
        "API_PORT=9999\nACTIVE_VAULT=probe_mm\nCLS_BACKEND_CONTAINER=cls-probe_mm-backend\nINTERNAL_API_KEY=\n",
        encoding="utf-8",
    )
    r = _apply(tmp_path, "probe_mm", "8192")
    assert r.returncode == 73, f"rc={r.returncode}: {r.stdout}"
    assert "矛盾" in r.stdout, r.stdout
    v = tmp_path / "vaults" / "probe_mm"
    assert not (v / ".obsidian" / "cls-internal-key.txt").exists(), (
        "步 3 在校验失败前就写了 key 文件 = 半成品（Phase A/B 拆分被破）"
    )
    txt = (v / ".mcp.json").read_text(encoding="utf-8")
    assert ":8011" in txt, "端口模板化在校验失败前就跑了 = 半成品"


# ═══ 源码级门（把踩过三次的坑锁住）═════════════════════════════════════════
_VAR_THEN_NON_ASCII = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*[^\x00-\x7f]")


def _logical_lines(text: str):
    """把 bash 的反斜杠续行折叠成逻辑行，并保留起始物理行号。

    Codex r1 LOW-1：逐**物理行**扫描可以被续行躲开 —— 变量在上一行行尾、非 ASCII 字符
    在下一行行首，物理行上看不到「紧跟」，而 bash 看到的是折叠后的逻辑行。
    """
    out, buf, start = [], "", None
    for i, raw in enumerate(text.splitlines(), 1):
        if start is None:
            start = i
        if raw.endswith("\\"):
            buf += raw[:-1]
            continue
        out.append((start, buf + raw))
        buf, start = "", None
    if buf:
        out.append((start or 1, buf))
    return out


@pytest.mark.parametrize("script", ["deploy-vault.sh", "install-vault.sh"])
def test_no_var_ref_followed_by_non_ascii(script: str):
    """`"...（$abs）"` 这种写法会让 bash 把全角括号的首字节吃进变量名。

    后果不是语法错（bash -n 过、--help 过、正控过），而是**只在那条分支被走到时**
    `set -u` 报 unbound variable、脚本 rc=1 —— 而不是本该的 rc 71。调用方若只判
    「非零就算拦住了」就会以为没事，但 rc 语义已错、消息里也没有「禁写面」。
    本卡实测：修了 8 处之后，我自己新写的两行又引入同一个坑 ⇒ 做成门。
    修法：一律 `${var}` 显式界定。
    """
    path = REPO_ROOT / "scripts" / script
    bad = []
    for i, line in _logical_lines(path.read_text(encoding="utf-8")):
        if line.lstrip().startswith("#"):
            continue
        for m in _VAR_THEN_NON_ASCII.finditer(line):
            bad.append(f"{script}:{i} {m.group(0)!r} | {line.strip()[:90]}")
    assert not bad, "变量引用后紧跟非 ASCII 字符（改用 ${var}）:\n  " + "\n  ".join(bad)


def test_var_then_non_ascii_gate_has_a_falsifier():
    """验伪锚：上一条门若正则写坏了就会永远绿。喂一个已知坏样本必须被抓到。"""
    sample = 'FORBIDDEN_HIT="*.env 文件（$abs）"'
    assert _VAR_THEN_NON_ASCII.search(sample), "门的正则抓不到已知坏样本"
    fixed = 'FORBIDDEN_HIT="*.env 文件（${abs}）"'
    assert not _VAR_THEN_NON_ASCII.search(fixed), "门把正确写法也当成坏样本"
    # Codex r1 LOW-1：续行样本 —— 逐物理行看不见，折叠成逻辑行才看得见
    split_sample = 'MSG="x $abs\\\n）"'
    assert not any(_VAR_THEN_NON_ASCII.search(ln) for ln in split_sample.splitlines()), (
        "样本构造错了：它在物理行上就应该看不见"
    )
    assert any(_VAR_THEN_NON_ASCII.search(ln) for _n, ln in _logical_lines(split_sample)), (
        "折叠续行后仍抓不到 —— 门对续行是瞎的"
    )


def test_port_templated_files_is_single_source_shared_by_step3_and_step4():
    """端口模板化清单必须只有一份定义, 且步 3 与步 4（源镜像）都引用它。

    两份清单各自漂移 ⇒ 目标被特化、基准没被特化 ⇒ 步 4 重新报假 content-drift。
    """
    src = DEPLOY_SH.read_text(encoding="utf-8")
    assert src.count("PORT_TEMPLATED_FILES=") == 1, "PORT_TEMPLATED_FILES 有多处定义"
    refs = src.count("$PORT_TEMPLATED_FILES")
    assert refs >= 3, f"引用数 {refs} < 3（步 3 两处 + 步 4 源镜像一处）"

    body = src[src.index("PORT_TEMPLATED_FILES=") :]
    decl = body.splitlines()[0]
    for rel in [".mcp.json", ".claude/settings.json", ".claude/hooks/session-end-archive.py"]:
        assert rel in decl, f"清单缺 {rel}: {decl}"


def test_step4_uses_mirrored_source_when_port_differs():
    """步 4 在 --port ≠ 8011 时必须用「同端口口径的源镜像」当基准。

    两个错解都要挡住：① 不传 --source（丢掉 content-drift 整个轴，门却还绿）；
    ② 放宽步 4 的 rc 判据。
    """
    src = DEPLOY_SH.read_text(encoding="utf-8")
    step4 = src[src.index("step4_verify()") : src.index("# ═══ 步 5")]
    assert "--source" in step4, "步 4 不传 --source = 丢掉 content-drift 轴"
    assert "SRC_MIRROR" in step4, "步 4 未用源镜像做基准"
    assert re.search(r'rc"?\s*!=\s*0|"\$rc" != 0', step4), "步 4 未对校验器 rc 做严格判定"


def test_rc_table_in_header_matches_actual_exit_codes():
    """头注 rc 表与 run_step 的实际算法（70+N）必须一致。"""
    src = DEPLOY_SH.read_text(encoding="typing" if False else "utf-8")
    assert "exit $((70 + n))" in src, "run_step 的 rc 算法变了, 头注 rc 表需同步"
    for n in range(1, 7):
        assert f"7{n} 步 {n}" in src, f"头注 rc 表缺 7{n} 步 {n}"


def test_dry_run_is_the_default_not_apply():
    """缺省必须是 dry-run —— 反过来（缺省就写）是不可逆的默认值。"""
    src = DEPLOY_SH.read_text(encoding="utf-8")
    assert re.search(r"^APPLY=0$", src, re.M), "APPLY 缺省不是 0"
    assert "--apply) APPLY=1" in src


def test_second_tier_hosts_not_implemented_anywhere():
    """E-1：不得偷偷生成二线宿主的配置件。"""
    src = DEPLOY_SH.read_text(encoding="utf-8")
    for artifact in ["AGENTS.md", ".codex/config.toml", "opencode.json", ".dsh/"]:
        # 只允许出现在「不生成」的说明里, 不允许出现在写操作附近
        for i, line in enumerate(src.splitlines(), 1):
            if artifact in line and not line.lstrip().startswith("#"):
                pytest.fail(f"deploy-vault.sh:{i} 在非注释行提到二线件 {artifact}: {line.strip()}")


def test_run_helper_strips_host_authorization_switch(monkeypatch, tmp_path: Path):
    """`_run` 必须剥掉宿主的 CLS_DEPLOY_ALLOW_DOCKER_UP（Codex r2 HIGH-1）。

    宿主设了 1 而测试继承它时，「缺省不 up」那条用例会先真起容器再断言 SKIP ——
    断言在脚本跑完之后，拦不住启动。这条门直接验剥离行为，不依赖 docker 状态。
    """
    monkeypatch.setenv("CLS_DEPLOY_ALLOW_DOCKER_UP", "1")
    # --help 不走部署路径，只用来观察脚本看到的环境：改用一个会打印环境的探针
    probe = tmp_path / "probe.sh"
    probe.write_text(
        '#!/usr/bin/env bash\nprintf "ALLOW=%s\\n" "${CLS_DEPLOY_ALLOW_DOCKER_UP:-<unset>}"\n',
        encoding="utf-8",
    )
    probe.chmod(0o755)
    # ⛔ 必须**真的走 _run**（Codex r3 MEDIUM-4）：原版自己重新构造并剥离环境再执行探针，
    #    于是删掉 _run 里的剥离两行、这条门的结果完全不变 —— 它锁不住被测行为。
    #    现在把探针脚本交给 _run 去跑（script= 参数），剥离逻辑由 _run 自己执行。
    r = _run(script=probe)
    assert r.returncode == 0, r.stderr
    assert "ALLOW=<unset>" in r.stdout, f"_run 没有剥掉 CLS_DEPLOY_ALLOW_DOCKER_UP: {r.stdout!r}"
    # 反向锚：不经 _run 时宿主值确实可见 —— 证明上面那条不是因为环境里本来就没有
    raw = subprocess.run(
        [str(probe)], capture_output=True, text=True, env=dict(os.environ), timeout=_SUBPROCESS_TIMEOUT
    )
    assert "ALLOW=1" in raw.stdout, f"控制组不成立：宿主环境里本来就没有该变量，上面那条断言不承重: {raw.stdout!r}"


def test_yaml_module_is_available_for_step5_assertion():
    """步 5 的结构化断言依赖 harness venv 的 pyyaml —— 缺了会让断言恒 FAIL。"""
    assert yaml is not None


# ═══ 脱敏：evidence 是要入库的，明文凭据不许落盘 ═════════════════════════════
_SECRET_LINE = re.compile(
    r"^[ \t]*-?[ \t]*[A-Za-z0-9_]*"
    r"(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|AUTH|CREDENTIAL)[A-Za-z0-9_]*[:=][ \t]*(.+)$",
    re.M,
)


def test_step5_pipes_compose_config_through_redaction():
    """步 5 落盘 config **之前**必须过 redact_secrets。

    `docker compose config` 会把 --env-file 与**宿主 env** 里的凭据展开成明文
    （INTERNAL_API_KEY / GOOGLE_API_KEY / NEO4J_PASSWORD / NEO4J_AUTH …）。
    本卡实测: 未脱敏那版把真实 GOOGLE_API_KEY 写进了 evidence 目录。
    必须是「明文从不落盘」而不是「落了再擦」—— 落了再擦意味着它曾在磁盘上存在过。
    """
    src = DEPLOY_SH.read_text(encoding="utf-8")
    assert "redact_secrets()" in src, "缺 redact_secrets 过滤器"
    step5 = src[src.index("step5_activate()") : src.index("# ═══ 步 6")]
    assert "redact_secrets" in step5, "步 5 落盘 config 时未过脱敏"
    # 必须是管道进脱敏后再重定向，而不是先 > 文件、事后再改
    assert re.search(r"config[^\n]*\|\s*\n?\s*redact_secrets\s*>", step5) or re.search(
        r"\|\s*redact_secrets\s*>\s*\"\$cfg\"", step5
    ), f"步 5 的落盘不是「config | redact_secrets > 文件」形态:\n{step5[:600]}"


def test_redaction_filter_masks_secrets_but_keeps_assertion_fields(tmp_path: Path):
    """脱敏必须盖住凭据、且**不能**盖住步 5 断言要用的字段。

    盖过头（把 container_name / published / target / host_ip 也换掉）会让步 5 的
    结构化断言恒 FAIL —— 那是另一种坏：门从「能拦」变成「永远拦」。
    """
    fn = tmp_path / "redact.sh"
    src = DEPLOY_SH.read_text(encoding="utf-8")
    body = src[src.index("redact_secrets()") :]
    body = body[: body.index("\n}\n") + 3]
    fn.write_text(body, encoding="utf-8")

    sample = (
        "      GEMINI_API_KEY: AIzaSyDUMMY1234567890\n"
        "      INTERNAL_API_KEY: DUMMYKEYDUMMYKEYDUMMYKEYDUMMYKEY\n"
        "      NEO4J_PASSWORD: DUMMYPASSWORD\n"
        "      NEO4J_AUTH: neo4j/DUMMYPASSWORD\n"
        "      - ANTHROPIC_API_KEY=sk-ant-dummy\n"
        "      container_name: cls-probe-backend\n"
        '      published: "8124"\n'
        "      target: 8001\n"
        "      host_ip: 127.0.0.1\n"
    )
    r = subprocess.run(
        ["bash", "-c", f". '{fn}'; redact_secrets"],
        input=sample,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
    )
    assert r.returncode == 0, r.stderr
    out = r.stdout

    # 凭据全没了
    for leaked in ["AIzaSyDUMMY1234567890", "DUMMYKEYDUMMYKEYDUMMYKEYDUMMYKEY", "sk-ant-dummy", "neo4j/DUMMYPASSWORD"]:
        assert leaked not in out, f"脱敏漏了 {leaked!r}:\n{out}"
    # 每一条含敏感键名的行, 值都必须是 <redacted>
    for m in _SECRET_LINE.finditer(out):
        assert m.group(1).strip() == "<redacted>", f"未脱敏的行: {m.group(0)!r}"
    # 断言字段一个不少
    for keep in ["container_name: cls-probe-backend", 'published: "8124"', "target: 8001", "host_ip: 127.0.0.1"]:
        assert keep in out, f"脱敏盖过头, 弄丢了断言字段 {keep!r}:\n{out}"


#: 本文件这条卡族自己的 evidence 目录。CARD-G2-8 补上 `evidence-g2-8`：
#: 原来两条门只钉 `evidence-g27b` 一个目录名，G2-8 的存档落在另一个目录 ⇒
#: **完全不在门的取名面内**（门绿证明不了新目录里没有凭据）。新开 evidence
#: 目录的卡必须同步加进这份清单，否则它的存档是无人看管的。
_EVIDENCE_DIRS = ("evidence-g27b", "evidence-g2-8")


def _existing_evidence_dirs() -> list[Path]:
    return [d for n in _EVIDENCE_DIRS if (d := REPO_ROOT / "_bmad-output" / "审查" / n).is_dir()]


def test_no_plaintext_credentials_in_committed_evidence():
    """本卡族的 evidence 目录里不许有明文凭据（它们是要入库的）。

    ⚠️ 这条门看的是**当前工作区**的 evidence 目录, 不是历史 —— 它防的是
    「下一次跑完忘了脱敏就 commit」。
    """
    evs = _existing_evidence_dirs()
    if not evs:
        pytest.skip(f"{_EVIDENCE_DIRS} 都不存在（首次跑或已归档）")
    pats = {
        "Google API key": re.compile(r"AIzaSy[A-Za-z0-9_\-]{10,}"),
        "INTERNAL_API_KEY 明文": re.compile(r"INTERNAL_API_KEY[:=]\s*[0-9a-f]{16,}"),
        "NEO4J 明文密码": re.compile(r"NEO4J_(?:PASSWORD|AUTH)[:=]\s*(?!<redacted>)\S"),
        "sk-/ghp_/xox token": re.compile(r"\b(?:sk-[A-Za-z0-9]{8,}|ghp_[A-Za-z0-9]{8,}|xox[baprs]-)"),
    }
    bad = []
    for ev in evs:
        for p in ev.rglob("*"):
            if not p.is_file():
                continue
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for label, pat in pats.items():
                if pat.search(txt):
                    bad.append(f"{ev.name}/{p.name}: {label}")
    assert not bad, "evidence 里有明文凭据:\n  " + "\n  ".join(bad)


def test_credential_gate_actually_matches_something():
    """验伪锚：上面那组正则得真能命中 —— 否则「0 命中」证明不了任何事。

    （记忆教训：判据恒 0 的假阴性，本仓栽过不止一次。）
    """
    probe = "INTERNAL_API_KEY=0123456789abcdef0123456789abcdef"
    assert re.search(r"INTERNAL_API_KEY[:=]\s*[0-9a-f]{16,}", probe), "凭据正则连正例都不命中"


def test_evidence_dir_has_no_stderr_archives():
    """协议 §2.2: *.stderr* 永不入库。"""
    evs = _existing_evidence_dirs()
    if not evs:
        pytest.skip(f"{_EVIDENCE_DIRS} 都不存在")
    stray = [f"{ev.name}/{p.name}" for ev in evs for p in ev.rglob("*stderr*")]
    assert not stray, f"evidence 里有 stderr 存档: {stray}"


# ═══ 禁写面判据本体的门（Codex r2 BLOCKER-1~4 整改后新增）══════════════════════
# ⚠️ 为什么这些门是**直接调判据脚本**而不是看 deploy-vault.sh 的源码：
#    Codex r2 MEDIUM 指出源码门「检查字符串数量或存在性」，对功能退化不敏感 ——
#    把 `src="$SRC_MIRROR"` 改回源树、把失败判断改成 `if false && …`，源码门照样绿。
#    判据本体的正确性只能由**喂输入看判定**来锁。
FORBID_PY = REPO_ROOT / "scripts" / "cls_forbidden_paths.py"


def _forbid(live: str, *items: str, outputs: tuple[str, ...] = ()):
    argv = [sys.executable, str(FORBID_PY), live, *items]
    if outputs:
        argv += ["--outputs", *outputs]
    return subprocess.run(argv, capture_output=True, text=True, timeout=_SUBPROCESS_TIMEOUT)


@pytest.fixture
def alias_tree(tmp_path: Path):
    """建一棵含各种别名形态的树：prot 是保护目录，safe 是合法区。"""
    prot = tmp_path / "prot"
    (prot / "sub").mkdir(parents=True)
    safe = tmp_path / "safe"
    safe.mkdir()
    (safe / "link").symlink_to(prot / "sub", target_is_directory=True)
    (safe / "alias").symlink_to(prot, target_is_directory=True)
    (safe / "link2").symlink_to(safe / "link", target_is_directory=True)
    return prot, safe


def test_forbidden_judge_catches_symlink_dotdot_physical_target(alias_tree):
    """`link/..` 的物理落点在保护目录内 —— r1 的三种词法解释**全部**漏拦这一条。

    `/safe/link/../probe`（`link → prot/sub`）：`..` 是 link **目标**的父目录，
    所以真实落点是 `prot/probe`。`cd -L` 与字符串折叠都得出 `/safe/probe`。
    这是把判据从 bash 搬到 `os.path.realpath` 的唯一理由，必须锁住。
    """
    prot, safe = alias_tree
    r = _forbid(str(prot), f"p:{safe}/link/../probe")
    assert r.returncode == 1, f"漏拦: {r.stdout}{r.stderr}"
    assert r.stdout.startswith("HIT"), r.stdout


@pytest.mark.parametrize(
    "form",
    [
        "missing/../alias/probe",  # 缺失段之后接软链：折叠后必须再解链
        "link2/../probe",  # 多重软链
        "alias/probe",  # 普通软链
        "alias/deep/nested/probe",  # 软链下的深层路径
    ],
)
def test_forbidden_judge_catches_alias_forms(alias_tree, form: str):
    prot, safe = alias_tree
    r = _forbid(str(prot), f"p:{safe}/{form}")
    assert r.returncode == 1, f"{form} 漏拦: {r.stdout}"


def test_forbidden_judge_is_case_insensitive_for_protected_dir(alias_tree):
    """APFS 缺省大小写不敏感 ⇒ 大写别名指向同一目录，必须拦。"""
    prot, safe = alias_tree
    upper = str(prot.parent / prot.name.upper() / "probe")
    r = _forbid(str(prot), f"p:{upper}")
    assert r.returncode == 1, f"大小写别名漏拦: {r.stdout}"


@pytest.mark.parametrize("seg", [".git", ".GIT", ".Git"])
def test_forbidden_judge_catches_dotgit_any_case(alias_tree, seg: str):
    """Codex r2 BLOCKER-2：原实现算了 lc 却用原串比 `.git` ⇒ `.GIT` 漏拦。"""
    prot, safe = alias_tree
    r = _forbid(str(prot), f"p:{safe}/{seg}/probe")
    assert r.returncode == 1, f"{seg} 漏拦: {r.stdout}"
    assert ".git" in r.stdout.lower(), r.stdout


@pytest.mark.parametrize("name", [".env", "a.env", ".env.local", ".ENV.local", "A.ENV"])
def test_forbidden_judge_catches_env_names_any_case_in_strict_mode(alias_tree, name: str):
    prot, safe = alias_tree
    r = _forbid(str(prot), f"p:{safe}/{name}")
    assert r.returncode == 1, f"{name} 在 strict 模式漏拦: {r.stdout}"


@pytest.mark.parametrize("name", [".env.probe_x", ".env.probe_x.tmp"])
def test_outputs_mode_allows_the_scripts_own_env_files(alias_tree, name: str):
    """⛔ 反向门：脚本自己产出的 `.env.<vault>` 必须**放行**。

    本卡实测过这个坑：把 env 文件名规则也套在产出对象上，脚本会永远拦下自己的
    正常产出 —— 整改后所有正控一度 rc 71。门必须两个方向都测。
    """
    prot, safe = alias_tree
    r = _forbid(str(prot), outputs=(f"p:{safe}/{name}",))
    assert r.returncode == 0, f"outputs 模式误拦自己的产出: {r.stdout}"
    assert r.stdout.startswith("OK"), r.stdout


def test_outputs_mode_still_blocks_protected_dirs(alias_tree):
    """outputs 模式只放宽**文件名**规则，保护目录规则一分不放。"""
    prot, _safe = alias_tree
    r = _forbid(str(prot), outputs=(f"p:{prot}/.env.sneaky",))
    assert r.returncode == 1, f"outputs 模式把保护目录也放过了: {r.stdout}"


def test_forbidden_judge_rejects_literal_tilde(alias_tree):
    """字面 `~` 开头：判据会展开、shell 不会 ⇒ 落点必然分歧，直接拒。"""
    prot, _safe = alias_tree
    r = _forbid(str(prot), "p:~/probe")
    assert r.returncode == 1, r.stdout
    assert "~" in r.stdout, r.stdout


def test_forbidden_judge_does_not_glob_expand(alias_tree):
    """含 `*` 的路径按**字面**处理 —— bash 的 `set -- $p` 会做通配符展开（r1 的缺陷）。"""
    prot, safe = alias_tree
    r = _forbid(str(prot), f"p:{safe}/*/../probe")
    # 不论判定结果，都不应崩、也不应因展开出多个名字而行为不定
    assert r.returncode in (0, 1), f"rc={r.returncode}: {r.stderr}"
    assert r.stdout.count("\n") == 1, f"一个输入应只有一行输出: {r.stdout!r}"


def test_forbidden_judge_control_group_allows_legit_paths(alias_tree):
    """⛔ 控制组：合法路径必须放行 —— 否则判据从「能拦」退化成「永远拦」。"""
    prot, safe = alias_tree
    r = _forbid(
        str(prot),
        f"vault:{safe}/vaults/ok_name",
        f"ev:{safe}/evidence",
        f"envdir:{safe}/envs",
    )
    assert r.returncode == 0, f"误拦合法路径: {r.stdout}"
    assert r.stdout.count("OK") == 3, r.stdout


def test_forbidden_judge_usage_error_is_64(alias_tree):
    prot, _ = alias_tree
    r = _forbid(str(prot), "no-colon-here")
    assert r.returncode == 64, f"rc={r.returncode}: {r.stdout}{r.stderr}"


def test_deploy_script_delegates_forbidden_judge_to_python_helper():
    """deploy-vault.sh 不得自己用 bash 判物理路径（r1 的三种词法解释已被证伪）。"""
    src = DEPLOY_SH.read_text(encoding="utf-8")
    assert "cls_forbidden_paths.py" in src, "未委派给 python 判据脚本"
    body = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
    for gone in ("norm_path()", "_hits_one()", "build_forbidden()"):
        assert gone not in body, f"bash 侧的旧判据 {gone} 还在（应已删除）"
    assert FORBID_PY.is_file(), f"{FORBID_PY} 不存在"


def test_forbidden_judge_covers_actual_output_objects_not_just_params():
    """Codex r2 BLOCKER-4：三个参数过检 ≠ 实际写入对象过检。

    断言 preflight 把脚本真正会写的对象也送进判据（按标签名核，不数字符串个数）。
    """
    src = DEPLOY_SH.read_text(encoding="utf-8")
    seg = src[src.index("local -a PENDING_WRITES=(") : src.index('STEP_MSG="禁写面')]
    # ⛔ 不能只验标签（Codex r3 MEDIUM-5）：保留 `plugin-data:` 标签却传一个安全父目录，
    #    只验标签的门照样绿。这里把**实际传的路径表达式**一起钉。
    expected = {
        "--vault:": '"--vault:$VAULT"',
        "--evidence-dir:": '"--evidence-dir:$EVIDENCE_DIR"',
        "--env-dir:": '"--env-dir:$ENV_DIR"',
        "env-file:": '"env-file:$ENV_FILE"',
        "env-file-tmp:": '"env-file-tmp:$ENV_FILE.tmp"',
        "key-file:": '"key-file:$VAULT/.obsidian/cls-internal-key.txt"',
        "plugin-data:": '"plugin-data:$VAULT/.obsidian/plugins/canvas-learning-system/data.json"',
    }
    for label, expr in expected.items():
        assert label in seg, f"判据调用缺对象 {label}"
        assert expr in seg, f"{label} 传的不是预期路径表达式，应为 {expr}"
    for expr in (
        '"ev-install-log:$EVIDENCE_DIR/install-$TS.txt"',
        '"ev-deploy-report-tmp:$EVIDENCE_DIR/deploy-$TS.txt.tmp"',
    ):
        assert expr in seg, f"缺 evidence 对象 {expr}（r3 BLOCKER-2）"
    # ⛔ 两个**构建产物**（Codex r4 HIGH-1）：它们原本只在判据列表里、不在 -L 列表里。
    for expr in (
        '"harness-mainjs:$HARNESS/canvas-vault/.obsidian/plugins/canvas-learning-system/main.js"',
        '"harness-build-out:$HARNESS/frontend/obsidian-plugin/main.js"',
    ):
        assert expr in seg, f"缺构建产物 {expr}（r4 HIGH-1）"
    # 判据必须**逐字消费那个数组**，而不是再手抄一遍（手抄就会重新漂移）。
    assert '--outputs "${PENDING_WRITES[@]}"' in seg, (
        "判据没有直接消费 PENDING_WRITES —— 只要重新手抄一份列表，两份清单就会再次漂移"
    )


def test_pending_writes_is_the_single_source_for_link_and_hardlink_checks():
    """⛔ Codex r4 HIGH-1 的**结构性**修法：一个数组两个消费方。

    r4 抓到的事实是：`--outputs` 判据列表有 12 项，紧跟着的 `-L` 列表只有 10 项 ——
    `harness-mainjs` / `harness-build-out` 两个构建产物是软链时**没有任何一层会拦**。
    两份手抄清单必然漂移，所以门要钉的不是「第 11、12 项也抄上了」，而是
    「**只有一份清单**」：判据与 -L/硬链接检查都遍历同一个数组。

    反向锚：旧的手抄形态（`for lnk in "$ENV_FILE" ...`）必须**不再存在**——
    否则有人「顺手加回来」时这道门仍会绿。
    """
    src = DEPLOY_SH.read_text(encoding="utf-8")
    assert src.count("local -a PENDING_WRITES=(") == 1, "待写清单不止一份"
    assert 'for lnk in "$ENV_FILE" "$ENV_FILE.tmp"' not in src, (
        "又出现了第二份手抄的 -L 列表 —— 这正是 r4 HIGH-1 漂移的成因"
    )
    loop = src[src.index('for item in "${PENDING_WRITES[@]}"') :]
    loop = loop[: loop.index("done")]
    assert '[ -L "$lnk" ]' in loop, "-L 检查没有消费 PENDING_WRITES"
    assert 'assert_writable_now "$lnk"' in loop, (
        "硬链接检查没有覆盖每个待写对象（r4 BLOCKER-4：路径判据保护不了 inode）"
    )


def test_every_bash_write_site_has_a_prewrite_recheck():
    """⛔ Codex r4 HIGH-1：只有 install 日志一处做了写前复查。

    脚本里所有**bash 重定向**写入点都要在紧邻处再查一次（软链 + 硬链接）；
    两处 python 写入改用 `O_NOFOLLOW`，那是真原子的，不靠复查。
    """
    src = DEPLOY_SH.read_text(encoding="utf-8")
    for obj in (
        'assert_writable_now "$ENV_FILE.tmp"',
        'assert_writable_now "$ilog"',
        'assert_writable_now "$keyfile.tmp"',
        'assert_writable_now "$rep"',
        'assert_writable_now "$cfg"',
        'assert_writable_now "$out.tmp"',
        # CARD-G2-8 新增的第三处写入点：`--also-push` 改 harness 自己的 `.env`
        'assert_writable_now "$henv"',
    ):
        assert obj in src, f"写入点缺紧邻复查: {obj}"
    # ⛔ 架构已变（Codex r7 HIGH-1）：`O_NOFOLLOW` 的字面量不再在本脚本里 ——
    #    两处 python 写入统一走 `cls_forbidden_paths.open_pinned()`（解析后当场过判据 +
    #    逐级 `O_DIRECTORY|O_NOFOLLOW` + `openat` 叶子）。门跟着改，不是删。
    # ⚠️ CARD-G2-8 把这四个计数从 2 改到 3，因为**真的多了第三处 python 写入**：
    #    `also_push_daily_review()` 改 harness 自己的 `.env`（追加 DAILY_REVIEW_VAULTS）。
    #    门的意图是「**每一处** python 写入都走硬化原语」，跟着写入点数走才叫钉住；
    #    把新写入点改成 bash 重定向来保住「2」才是放宽（那处会失去 O_NOFOLLOW 与防短写）。
    #    ⇒ 再加写入点仍要同步改这几个数，且新写入点必须也走 open_pinned + write_all。
    assert src.count("open_pinned(") == 3, "三处 python 写入必须都走 open_pinned"
    # ⛔ 裸 `os.write` 会**短写**（Codex r8 HIGH-4）：返回值小于长度时文件已被截断，
    #    忽略返回值 = 把「只写了一半」当成功。每处写入必须走循环写。
    assert src.count("write_all(fd, ") == 3, "三处写入必须走 write_all（防短写）"
    # 原语本体在判据模块里（与 open_pinned 同理：两个 heredoc 各抄一份必然漂移，本卡栽过）
    _f = FORBID_PY.read_text(encoding="utf-8")
    assert "def write_all(" in _f and "n = os.write(fd, view)" in _f, "write_all 必须真的调 os.write 并按返回值推进"
    bare = [ln for ln in src.splitlines() if "os.write(" in ln and "write_all" not in ln]
    assert not bare, f"脚本内仍有裸 os.write（短写会被当成功）: {bare}"
    assert src.count("os.ftruncate(fd, 0)") == 3, "必须先 fstat 查链接数再 ftruncate"
    assert src.count("st.st_nlink > 1") == 3, "O_NOFOLLOW 之后还要挡硬链接（共享 inode）"
    # 原语本体的形状（在判据模块里）：逐级 O_NOFOLLOW + 叶子也带 O_NOFOLLOW
    fsrc = FORBID_PY.read_text(encoding="utf-8")
    assert "os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW" in fsrc, "逐级打开必须带 O_NOFOLLOW"
    assert "flags | os.O_NOFOLLOW" in fsrc, "叶子打开必须强制带 O_NOFOLLOW"
    # ⚠️ 锚点必须**抗格式化**：ruff format 会把长调用折成多行，钉连续字面量的门
    #    会被自己的 formatter 打红（本门第一版就是这么红的 —— 记忆里「门锚点失效」同型）。
    #    先把空白折叠成单空格再断言。
    flat = " ".join(fsrc.split())
    assert "hits(path, targets, claude_prefixes" in flat, (
        "**原路径**必须过判据 —— 只判解析后的 parent 会丢掉 walker 的沿链 `.git` 保护"
        "（Codex r8 HIGH-1：本卡第 6 次「改判据形状 = 删掉一条已有规则」）"
    )
    assert "hits( parent, targets, claude_prefixes" in flat, (
        "解析后的父目录也必须过判据 —— 只 realpath 等于替攻击者把链走完（本卡实测证伪过）"
    )
    # ⛔ 路径式 chmod 必须绝迹：它每次重新解析路径，末段/祖先被换掉就改到别人的权限
    bare = [
        ln
        for ln in src.splitlines()
        if "chmod " in ln and not ln.lstrip().startswith("#") and "pinned_chmod600" not in ln
    ]
    assert not bare, f"仍有路径式 chmod: {bare}"
    # `stat -f '%l'` 在 GNU 下是文件系统信息、会回一个看似合理的数字 —— 不许再用
    assert "stat -f '%l'" not in src, "不要用 stat 取链接数（BSD/GNU 口径不同且都不报错）"


# ═══ Codex r4 BLOCKER-1：`.claude*` 词法前缀不得被 realpath 物理化 ═══════════════
def _forbid_home(home: Path, live: str, *items: str, outputs: tuple[str, ...] = ()):
    """在**假 HOME** 下跑判据（判据用 expanduser("~") 读 HOME）。"""
    argv = [sys.executable, str(FORBID_PY), live, *items]
    if outputs:
        argv += ["--outputs", *outputs]
    env = dict(os.environ)
    env["HOME"] = str(home)
    return subprocess.run(argv, capture_output=True, text=True, env=env, timeout=_SUBPROCESS_TIMEOUT)


@pytest.fixture
def home_with_claude_symlink(tmp_path: Path):
    """假 HOME：`.claude -> <tmp>/claude-base`，另有仅名字相近的 `claude-baseball`。

    这两个名字是刻意选的：`claude-base` 是 `claude-baseball` 的**字符串前缀**。
    """
    home = tmp_path / "home"
    home.mkdir()
    base = tmp_path / "claude-base"
    base.mkdir()
    ball = tmp_path / "claude-baseball"
    ball.mkdir()
    (home / ".claude").symlink_to(base, target_is_directory=True)
    live = tmp_path / "fake-live"
    live.mkdir()
    return home, base, ball, live


def test_forbidden_judge_keeps_claude_prefix_lexical(home_with_claude_symlink):
    """⛔ r4 BLOCKER-1：`$HOME/.claude-new/probe`（尚不存在）必须仍被拦。

    我 r3 统一 NFC 时把 `claude_prefix` 从 `.lower()` 换成了 `k()`，而 `k()` **内含
    realpath** —— 于是这条**刻意保持词法**的规则被物理化成 `<tmp>/claude-base`，
    尚不存在的 `.claude-new` 既不在枚举名单里、又不再匹配前缀，**保护整条失效**。
    这条规则存在的唯一理由就是覆盖 realpath 看不到的东西。
    """
    home, _base, _ball, live = home_with_claude_symlink
    probe = str(home / ".claude-new" / "probe")
    r = _forbid_home(home, str(live), f"--env-dir:{probe}")
    assert r.returncode != 0, f"未拦住尚不存在的 .claude-new: {r.stdout}{r.stderr}"
    assert "HIT" in r.stdout


def test_forbidden_judge_does_not_falsely_block_prefix_sibling(home_with_claude_symlink):
    """控制组（另一个方向）：`<tmp>/claude-baseball/probe` 必须**放行**。

    把前缀物理化成 `<tmp>/claude-base` 之后，裸 `startswith` 会把只是名字相近的
    `claude-baseball` 一起拦掉 —— 判据退化成「永远拦」是另一种坏，且更难发现。
    """
    home, _base, ball, live = home_with_claude_symlink
    probe = str(ball / "probe")
    r = _forbid_home(home, str(live), f"--env-dir:{probe}")
    assert r.returncode == 0, f"误拦了仅名字相近的兄弟目录: {r.stdout}{r.stderr}"


def test_forbidden_judge_still_blocks_the_claude_symlink_target(home_with_claude_symlink):
    """同时保住另一轴：`.claude` 的**解链目标**里的路径仍要拦（规则 4① 枚举登记）。

    前缀改回词法之后, 「解链目标」这一轴必须仍由枚举覆盖 —— 否则就是
    「收紧一处丢掉一整个轴」。
    """
    home, base, _ball, live = home_with_claude_symlink
    r = _forbid_home(home, str(live), f"--env-dir:{base / 'probe'}")
    assert r.returncode != 0, f"未拦住 .claude 的解链目标: {r.stdout}{r.stderr}"


# ═══ Codex r4 BLOCKER-2：两层软链把 `.git` 藏在解链途中 ═══════════════════════
@pytest.fixture
def two_hop_git(tmp_path: Path):
    """`safe/alias -> repo/.git -> external/meta`：`.git` 只出现在**中间那一跳**。"""
    ext = tmp_path / "external" / "meta"
    ext.mkdir(parents=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").symlink_to(ext, target_is_directory=True)
    safe = tmp_path / "safe"
    safe.mkdir()
    (safe / "alias").symlink_to(repo / ".git", target_is_directory=True)
    live = tmp_path / "fake-live"
    live.mkdir()
    return safe, live


def test_forbidden_judge_catches_git_hidden_mid_chain(two_hop_git):
    """⛔ r4 BLOCKER-2：原始串里只有 `alias`、realpath 结果里只有 `meta`。

    `.git` 那一跳**两边都看不见** —— 只比首尾（我 r3 的做法）必漏。
    """
    safe, live = two_hop_git
    for probe in (str(safe / "alias"), str(safe / "alias" / "x")):
        r = _forbid_home(Path.home(), str(live), f"--env-dir:{probe}")
        assert r.returncode != 0, f"未拦住解链途中的 .git（{probe}）: {r.stdout}{r.stderr}"
        assert ".git" in r.stdout


def test_forbidden_judge_allows_two_hop_chain_that_stays_safe(tmp_path: Path):
    """控制组：同样两跳、但途中不经过任何保护目标 —— 必须放行。"""
    safe = tmp_path / "safe"
    (safe / "final").mkdir(parents=True)
    (safe / "mid").symlink_to(safe / "final", target_is_directory=True)
    (safe / "ok").symlink_to(safe / "mid", target_is_directory=True)
    live = tmp_path / "fake-live"
    live.mkdir()
    r = _forbid_home(Path.home(), str(live), f"--env-dir:{safe / 'ok' / 'x'}")
    assert r.returncode == 0, f"误拦了全程安全的两跳链: {r.stdout}{r.stderr}"


# ═══ Codex r5 BLOCKER-2：把「路径」当原子对象解 ⇒ 逐段遍历面漏两类 ════════════
@pytest.fixture
def nested_hop_git(tmp_path: Path):
    """`alias -> hop/sub`，`hop -> repo/.git`，`.git -> external/meta`。

    与 r4 的 `two_hop_git` **不同**：`.git` 不在链的**目标本身**，而在目标的
    **祖先段**里。旧实现 `islink("<safe>/hop/sub")` 会先解掉 `hop` 落到
    `external/meta/sub`，`sub` 自身不是链 ⇒ False ⇒ 链停在第一跳，`.git` 全程不出现。
    """
    ext = tmp_path / "external" / "meta"
    (ext / "sub").mkdir(parents=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").symlink_to(ext, target_is_directory=True)
    safe = tmp_path / "safe"
    safe.mkdir()
    (safe / "hop").symlink_to(repo / ".git", target_is_directory=True)
    (safe / "alias").symlink_to(safe / "hop" / "sub", target_is_directory=True)
    live = tmp_path / "fake-live"
    live.mkdir()
    return safe, live


def test_forbidden_judge_catches_git_in_ancestor_of_link_target(nested_hop_git):
    """⛔ r5 BLOCKER-2(a)：`.git` 藏在**链目标的祖先段**里，首尾两侧都看不见。"""
    safe, live = nested_hop_git
    for probe in (str(safe / "alias"), str(safe / "alias" / "x")):
        r = _forbid_home(Path.home(), str(live), f"--env-dir:{probe}")
        assert r.returncode != 0, f"未拦住链目标祖先里的 .git（{probe}）: {r.stdout}{r.stderr}"
        assert ".git" in r.stdout


def test_forbidden_judge_does_not_fold_dotdot_before_resolving(tmp_path: Path):
    """⛔ r5 BLOCKER-2(b)：`..` 必须在**解完软链之后**才处理，不能词法先折。

    `alias -> <repo>/.git/../sub`：旧实现 `normpath` 把 `.git/..` 折成 `<repo>/`，
    `.git` 这一段当场消失；而内核是先解 `.git`（→ external/meta）再退一级。
    """
    ext = tmp_path / "external" / "meta"
    ext.mkdir(parents=True)
    (tmp_path / "external" / "sub").mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").symlink_to(ext, target_is_directory=True)
    safe = tmp_path / "safe"
    safe.mkdir()
    (safe / "alias").symlink_to(f"{repo}/.git/../sub")
    live = tmp_path / "fake-live"
    live.mkdir()
    r = _forbid_home(Path.home(), str(live), f"--env-dir:{safe / 'alias' / 'x'}")
    assert r.returncode != 0, f"`..` 被提前折叠，漏掉途中的 .git: {r.stdout}{r.stderr}"
    assert ".git" in r.stdout


def test_forbidden_judge_allows_dotdot_chain_that_stays_safe(tmp_path: Path):
    """控制组：同样带 `..` 的链、但途中不经过保护目标 —— 必须放行。"""
    base = tmp_path / "base"
    (base / "inner").mkdir(parents=True)
    (base / "sub").mkdir()
    safe = tmp_path / "safe"
    safe.mkdir()
    (safe / "alias").symlink_to(f"{base}/inner/../sub")
    live = tmp_path / "fake-live"
    live.mkdir()
    r = _forbid_home(Path.home(), str(live), f"--env-dir:{safe / 'alias' / 'x'}")
    assert r.returncode == 0, f"误拦了全程安全的 `..` 链: {r.stdout}{r.stderr}"


# ═══ Codex r5 BLOCKER-1：HOME 自身是软链时物理别名轴丢失 ══════════════════════
@pytest.fixture
def symlinked_home(tmp_path: Path):
    """HOME 自身是软链：`homealias -> homephys`。"""
    phys = tmp_path / "homephys"
    phys.mkdir()
    alias = tmp_path / "homealias"
    alias.symlink_to(phys, target_is_directory=True)
    live = tmp_path / "fake-live"
    live.mkdir()
    return alias, phys, live


def test_forbidden_judge_covers_physical_home_claude_prefix(symlinked_home):
    """⛔ r5 BLOCKER-1：用**物理** HOME 写出的 `.claude-new`（尚不存在）必须仍被拦。

    r4 为修「前缀被 realpath 掉」把 `claude_prefix` 改成纯词法 `join($HOME, ".claude")`，
    于是 `HOME=/homealias -> /homephys` 时，`/homephys/.claude-new/probe` 既不在枚举
    名单里（尚不存在）、也不匹配 `/homealias/.claude` ⇒ **放行**。
    两条需求是正交的：不 realpath `.claude` 那一段，但要 realpath **HOME 那一段**。
    """
    alias, phys, live = symlinked_home
    probe = str(phys / ".claude-new" / "probe")
    r = _forbid_home(alias, str(live), f"--env-dir:{probe}")
    assert r.returncode != 0, f"物理 HOME 下的 .claude-new 未被拦: {r.stdout}{r.stderr}"
    assert "HIT" in r.stdout


def test_forbidden_judge_still_covers_lexical_home_claude_prefix(symlinked_home):
    """另一轴不能丢：用**词法** HOME 写的同一目标也必须拦（两条前缀并存）。"""
    alias, _phys, live = symlinked_home
    r = _forbid_home(alias, str(live), f"--env-dir:{alias / '.claude-new' / 'probe'}")
    assert r.returncode != 0, f"词法 HOME 下的 .claude-new 未被拦: {r.stdout}{r.stderr}"


def test_forbidden_judge_physical_home_axis_does_not_overblock(symlinked_home):
    """控制组：物理 HOME 下**不叫 .claude\\*** 的目录必须放行。

    加物理轴的代价必须是零误拦 —— 否则就是把判据推向「永远拦」。
    """
    alias, phys, live = symlinked_home
    r = _forbid_home(alias, str(live), f"--env-dir:{phys / 'notclaude' / 'probe'}")
    assert r.returncode == 0, f"物理轴误拦了非 .claude 目录: {r.stdout}{r.stderr}"


# ═══ Codex r5 BLOCKER-3：HOME 可读但不可搜索 ⇒ 枚举结果不可信 ═════════════════
def test_forbidden_judge_fail_closed_when_home_not_searchable(tmp_path: Path):
    """⛔ r5 BLOCKER-3：`listdir` 成功 ≠ 解链成功。

    HOME 有读权限（r）无搜索权限（x）时，名字照常列得出来，而解析子项需要搜索权限，
    `realpath(strict=False)` 会把 EACCES 吞掉 ⇒ 外部保护目标整批漏登记，
    旧实现的 `enumerate_failed` 仍是 False，判据却照常宣称「全部 OK」。
    """
    if os.geteuid() == 0:
        pytest.skip("以 root 运行时权限位不生效，本条无从制造前提（r4 LOW-1 同型）")
    home = tmp_path / "home"
    home.mkdir()
    ext = tmp_path / "ext"
    ext.mkdir()
    (home / ".claude-cache").symlink_to(ext, target_is_directory=True)
    live = tmp_path / "fake-live"
    live.mkdir()
    safe = tmp_path / "safe"
    safe.mkdir()
    os.chmod(home, 0o444)  # r 但无 x
    try:
        # ⛔ 先断言**前提真的成立**（记忆：补了控制组 ≠ 控制组成立）：
        #    若本机/文件系统让 X_OK 仍为真，这条门就没在测它自称的东西。
        assert not os.access(home, os.X_OK), "前提不成立：HOME 仍可搜索，本条门测不到 B-3"
        r = _forbid_home(home, str(live), f"--env-dir:{safe / 'x'}")
    finally:
        os.chmod(home, 0o755)
    assert r.returncode != 0, f"HOME 不可搜索时未 fail-closed: {r.stdout}{r.stderr}"
    assert "fail-closed" in r.stdout, f"未走 fail-closed 分支: {r.stdout!r}"


def _sh_src() -> str:
    return DEPLOY_SH.read_text(encoding="utf-8")


def test_step4_mirror_files_pass_the_same_judge_before_sed(tmp_path: Path):
    """⛔ r5 BLOCKER-4：镜像**根**合法 ≠ 镜像**里**要写的对象合法。

    `cp -R` 保留源树软链；源树若有 `.claude/hooks -> <保护目录>`，`sed -i` 会沿链
    写过去，而 r4 只把 `TMPDIR` 这个根交给了判据。

    ⚠️ **这条门自己证不到端到端**（Codex r4 MEDIUM-4/M-2 的教训：源码门不等于恒真）：
    它只证明「判据调用存在且未被就地失效、对象取自 `$PORT_TEMPLATED_FILES` 这个单一
    来源、位置在 `sed -i` **之前**」。

    端到端由**车道负控**承担，不在 pytest 里（要造一个能过 preflight 的 harness 副本，
    单条用例跑十几秒）：`evidence-g27b/neg-positive-r5fix-*.txt` 记录了
      · 把 harness 副本的 `canvas-vault/.claude/hooks` 换成指向保护目录的软链
        → `rc=74`，消息点名 `mirror-.claude/hooks/session-end-archive.py` 与命中的目标，
        且保护目录 `find -newermt` 计数为 **0**（拦在写之前，不是写完才发现）；
      · 同一副本把 hooks 还原为真目录 → `rc=0`（控制组：判据不是「永远拦」）。
    """
    src = _sh_src()
    call = 'check_forbidden_paths --outputs "${MIRROR_WRITES[@]}"'
    judge = src.index(call)
    sed_at = src.index('sed -i \'\' "s|:8011|:$PORT|g" "$SRC_MIRROR/$t"')
    assert judge < sed_at, "镜像判据必须在 sed -i 之前，否则拦截发生时已经写过了"
    # ⛔ 「文本存在」挡不住**就地失效**（本卡实测：把它改成 `false && check_forbidden_paths …`
    #    这条门原样绿 —— 正是 Codex r4 MEDIUM-4 说的「留在注释或不可达代码中仍能满足断言」）。
    #    故钉住整条语句的**形状**：它必须是 `if` 的直接条件，前面不许挂任何短路。
    line = next(ln for ln in src.splitlines() if call in ln)
    assert line.strip() == f"if {call}; then", f"镜像判据被就地失效或改写: {line.strip()!r}"
    # ⛔ 内层形状对了，**外层**仍可被 `if false; then` 整块架空（Codex r6 MEDIUM-4）：
    #    判据与写前复查一起跳过、sed 照跑，而上面那条断言毫无察觉。故把外层守卫也钉住。
    guard = 'if [ "${#MIRROR_WRITES[@]}" -gt 0 ]; then'
    assert guard in src, "镜像判据的外层守卫被改写或删除（整块可被架空）"
    assert src.index(guard) < judge, "外层守卫必须包住判据调用"
    # 对象身份：清单必须从 $PORT_TEMPLATED_FILES 构建（与 sed 循环同一来源），
    # 而不是另抄一份 —— 两份手抄清单必然漂移（r4 HIGH-1 的原话）。
    build = src.index("MIRROR_WRITES+=(")
    loop_hdr = src.rfind("for t in $PORT_TEMPLATED_FILES", 0, build)
    assert loop_hdr != -1, "镜像待写清单未取自 $PORT_TEMPLATED_FILES 单一来源"
    # 写前复查也要覆盖到镜像文件（软链/硬链接两条）。
    assert 'assert_writable_now "${mt#*:}"' in src, "镜像文件缺写前复查"


def test_env_key_write_chmods_only_after_nofollow_and_nlink(tmp_path: Path):
    """⛔ r6 HIGH-1（我 r5 修 HIGH-3 时引入的第 5 次自伤）：收紧权限**不能用路径式 chmod**。

    r5 我在 bash 里写了 `[ -e "$ENV_FILE" ] && chmod 600 "$ENV_FILE"` 放在 python 块之前。
    若目标在 A3 校验之后、B4 之前被换成指向保护文件的软链或硬链接，那次 chmod 会
    **先改掉保护对象的权限**，之后才轮到 `O_NOFOLLOW` / nlink 把写拒掉 —— 旧版反而
    没有这个越界写，而且它改的是元数据，内容 sha 与 `find -newermt` 都看不见。

    ⇒ 正解是 `os.fchmod(fd)`：fd 由 `O_NOFOLLOW` 取得（末段是软链就根本打不开）、
    且已过 nlink 检查，此时改权限只会落在那个已确认安全的 inode 上。

    本门钉三件事：① 存在 `os.fchmod(fd, 0o600)`；② 它在 `fstat`/nlink 之后、
    `ftruncate` 之前；③ 步 3 里**不再有任何路径式 `chmod ... "$ENV_FILE"`**。
    """
    src = _sh_src()
    blk_start = src.index('if ! python3 - "$ENV_FILE" "$key"')
    blk = src[blk_start : src.index("\nPY", blk_start)]
    for anchor in ("os.fstat(fd)", "st.st_nlink > 1", "os.fchmod(fd, 0o600)", "os.ftruncate(fd, 0)"):
        assert anchor in blk, f"B4 写入块缺锚点 {anchor!r}"
    # ⛔ 光钉「在 fstat 之后」不够（Codex r7 MEDIUM-1）：把 fchmod 塞进 fstat 与
    #    `if st.st_nlink > 1` **之间**，既存硬链接仍会先被改权限再拒写，而门照样绿。
    #    真正要锁的是「在**拒绝分支**之后」。
    reject = blk.index('raise SystemExit(f".env 有 {st.st_nlink}')
    assert blk.index("os.fstat(fd)") < reject < blk.index("os.fchmod(fd, 0o600)"), (
        "fchmod 必须在 nlink **拒绝分支之后** —— 否则硬链接会先被改权限再拒写"
    )
    assert blk.index("os.fchmod(fd, 0o600)") < blk.index("os.ftruncate(fd, 0)"), "fchmod 必须在 ftruncate 之前"
    # ③ 路径式 chmod 在步 3 里必须绝迹（seed_env_file 里的那次不在此范围）。
    #    ⚠️ 必须先剥注释：说明为什么删掉它的那段注释里就写着这个字面量，
    #    不剥的话这条门会被自己的文档打红（本门第一版就是这么红的）。
    step3 = src[src.index("# B4 .env.<vault> 的 INTERNAL_API_KEY 同值") : src.index("# B5 key **文件**落盘")]
    step3_code = "\n".join(ln for ln in step3.splitlines() if not ln.lstrip().startswith("#"))
    assert 'chmod 600 "$ENV_FILE"' not in step3_code, (
        "步 3 仍有路径式 chmod —— 目标被换掉时会改到保护对象的权限（r6 HIGH-1）"
    )
    # seed 出来的那份从诞生就是 0600，走不到这个窗口。
    assert '(umask 077 && : > "$ENV_FILE.tmp")' in src, "seed 的临时文件缺 umask 077"


def test_step4_mirror_symlink_is_blocked_end_to_end(tmp_path: Path):
    """⛔ r7 MEDIUM-3：源码门证不了控制流可达 —— 把整块包进 `if false; then … fi`，
    守卫与内层形状都还在、bash 语法也过，门照样绿而 `sed` 照跑。

    ⇒ 这条改用**端到端**：造一份 harness 副本，把 `canvas-vault/.claude/hooks` 换成
    指向「保护目录」的软链（`CLS_LIVE_VAULT` 指向它），`--port != 8011` 触发源镜像。
    `cp -R` 保留软链 ⇒ 若判据没真的跑，`sed -i` 会沿链写进保护目录。
    判据：rc **74** + 消息点名那个镜像文件 + 保护目录**零写入**。
    控制组在下一条（hooks 还原为真目录 → rc 0），证明不是「永远拦」。
    """
    # ⛔ 干净 checkout 上缺 gitignored main.js 时，preflight 会在**真实**前端目录跑
    #    `npm run build`（deploy-vault.sh 的 E-4 分支）—— 越出本用例声称的 tmp_path
    #    写入范围，还可能在镜像判据之前就失败（Codex r8 MEDIUM-5）。
    if not (REPO_ROOT / "canvas-vault" / ".obsidian" / "plugins" / "canvas-learning-system" / "main.js").exists():
        pytest.skip("树上无 gitignored main.js 时 apply 会在真实前端目录触发 npm run build")
    src_cv = REPO_ROOT / "canvas-vault"
    if not (src_cv / ".claude" / "hooks" / "session-end-archive.py").is_file():
        pytest.skip("源树缺 .claude/hooks/session-end-archive.py，无从造该拓扑")
    h = tmp_path / "harness"
    h.mkdir()
    for name in ("scripts", "docker-compose.yml", "backend", "frontend"):
        os.symlink(REPO_ROOT / name, h / name)
    shutil.copytree(src_cv, h / "canvas-vault", symlinks=True)
    live = tmp_path / "protected"
    (live / "hooks").mkdir(parents=True)
    hooks = h / "canvas-vault" / ".claude" / "hooks"
    for f in hooks.iterdir():
        shutil.copy2(f, live / "hooks" / f.name)
    shutil.rmtree(hooks)
    os.symlink(live / "hooks", hooks)

    env = dict(os.environ)
    for _k in _STRIP_ENV:
        env.pop(_k, None)
    env["CLS_LIVE_VAULT"] = str(live)
    env["CLS_DEPLOY_NO_DOCKER_UP"] = "1"
    before = time.time()
    r = subprocess.run(
        [
            str(DEPLOY_SH),
            "--vault",
            str(tmp_path / "vaults" / "mirrorprobe"),
            "--harness",
            str(h),
            "--port",
            "8231",
            "--hosts",
            "claude",
            "--env-dir",
            str(tmp_path / "env"),
            "--evidence-dir",
            str(tmp_path / "ev"),
            "--apply",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=_SUBPROCESS_TIMEOUT,
    )
    assert r.returncode == 74, f"镜像内软链未被步 4 拦下: rc={r.returncode}\n{r.stdout}{r.stderr}"
    assert "禁写面" in r.stdout and "mirror-" in r.stdout, f"消息未点名镜像对象: {r.stdout!r}"
    touched = [f for f in live.rglob("*") if f.stat().st_mtime > before]
    assert not touched, f"拦下前已经写了保护目录: {touched}"


def test_step4_mirror_control_group_passes_without_symlink(tmp_path: Path):
    """控制组：同样的 harness 副本、hooks 是真目录 → 必须 rc 0（判据不是「永远拦」）。"""
    # ⛔ 干净 checkout 上缺 gitignored main.js 时，preflight 会在**真实**前端目录跑
    #    `npm run build`（deploy-vault.sh 的 E-4 分支）—— 越出本用例声称的 tmp_path
    #    写入范围，还可能在镜像判据之前就失败（Codex r8 MEDIUM-5）。
    if not (REPO_ROOT / "canvas-vault" / ".obsidian" / "plugins" / "canvas-learning-system" / "main.js").exists():
        pytest.skip("树上无 gitignored main.js 时 apply 会在真实前端目录触发 npm run build")
    src_cv = REPO_ROOT / "canvas-vault"
    if not (src_cv / ".claude" / "hooks").is_dir():
        pytest.skip("源树缺 .claude/hooks")
    h = tmp_path / "harness"
    h.mkdir()
    for name in ("scripts", "docker-compose.yml", "backend", "frontend"):
        os.symlink(REPO_ROOT / name, h / name)
    shutil.copytree(src_cv, h / "canvas-vault", symlinks=True)
    live = tmp_path / "protected"
    live.mkdir()
    env = dict(os.environ)
    for _k in _STRIP_ENV:
        env.pop(_k, None)
    env["CLS_LIVE_VAULT"] = str(live)
    env["CLS_DEPLOY_NO_DOCKER_UP"] = "1"
    r = subprocess.run(
        [
            str(DEPLOY_SH),
            "--vault",
            str(tmp_path / "vaults" / "mirrorctrl"),
            "--harness",
            str(h),
            "--port",
            "8232",
            "--hosts",
            "claude",
            "--env-dir",
            str(tmp_path / "env"),
            "--evidence-dir",
            str(tmp_path / "ev"),
            "--apply",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=_SUBPROCESS_TIMEOUT,
    )
    assert r.returncode == 0, f"无软链的正常镜像被误拦: rc={r.returncode}\n{r.stdout}{r.stderr}"


def test_open_pinned_rejects_ancestor_symlink_into_protected(tmp_path: Path):
    """⛔ r7 HIGH-1：祖先目录被换成指向保护区的软链 ⇒ 写入必须被拒。

    `O_NOFOLLOW` 只挡末段；祖先照样被跟随。这是本卡最后一条 HIGH。
    ⚠️ 我的**第一版修法被自己的冒烟当场证伪**：只做「写入时 realpath 父目录 + 逐级
    O_NOFOLLOW」等于**跟着攻击者当下的链走** —— realpath 把要检测的那条软链解成了
    目标真路径，遍历一路畅通。现在是两步：解析后**当场过判据**，再逐级 O_NOFOLLOW。
    """
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from cls_forbidden_paths import open_pinned

    prot = tmp_path / "protected"
    (prot / "sub").mkdir(parents=True)
    victim = prot / "sub" / "b.txt"
    victim.write_text("secret", encoding="utf-8")
    safe = tmp_path / "safe"
    safe.mkdir()
    os.symlink(prot / "sub", safe / "sub")  # 祖先被换成指向保护区的软链
    with pytest.raises((PermissionError, OSError)):
        open_pinned(str(safe / "sub" / "b.txt"), os.O_WRONLY, live_vault=str(prot))
    assert victim.read_text(encoding="utf-8") == "secret", "保护区内容被改动了"


def test_open_pinned_allows_legitimate_symlinked_ancestor(tmp_path: Path):
    """控制组：**合法**的祖先软链必须放行 —— 否则判据退化成「永远拦」。

    macOS 的 `/tmp -> /private/tmp`、`/var -> private/var` 都是这种；tmp_path 本身
    就在 `/private/var/folders/...` 下。直接对**原串**逐级 O_NOFOLLOW 会把它们全拒掉，
    这也是「解析后再判」而不是「不解析」的理由。
    """
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from cls_forbidden_paths import open_pinned

    prot = tmp_path / "protected"
    prot.mkdir()
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    os.symlink(real, alias)  # 合法软链：目标不在保护区
    fd = open_pinned(str(alias / "ok.txt"), os.O_WRONLY | os.O_CREAT, 0o600, live_vault=str(prot))
    try:
        os.write(fd, b"ok")
    finally:
        os.close(fd)
    assert (real / "ok.txt").read_bytes() == b"ok", "合法软链下的正常写入被误拦或写错地方"


def test_write_all_actually_completes_short_writes(tmp_path: Path, monkeypatch):
    """⛔ r9 MEDIUM-2：字符串门抓不到「假推进」。

    把 `write_all` 的推进改成 `view = view[len(view):]`，短写仍会被当成功，
    而「存在 `n = os.write(fd, view)`」这种源码断言照样满足。
    ⇒ 换成**行为门**：注入一个每次只写 1 字节的 `os.write`，断言全量落盘且调用次数
    等于字节数（后者能抓住「一次跳完」的假推进）。
    """
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import cls_forbidden_paths as cfp

    payload = b"0123456789abcdef"
    real_write = os.write
    calls = {"n": 0}

    def one_byte_write(fd, data):
        calls["n"] += 1
        return real_write(fd, bytes(data)[:1])

    target = tmp_path / "out.bin"
    fd = os.open(target, os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        monkeypatch.setattr(cfp.os, "write", one_byte_write)
        cfp.write_all(fd, payload)
    finally:
        monkeypatch.undo()
        os.close(fd)
    assert target.read_bytes() == payload, "短写下没有写全 —— write_all 的推进有问题"
    assert calls["n"] == len(payload), (
        f"os.write 只被调用 {calls['n']} 次而数据 {len(payload)} 字节 —— 推进量与实际写入量脱节（假推进）"
    )


def test_write_all_raises_when_write_makes_no_progress(tmp_path: Path, monkeypatch):
    """控制组：`os.write` 恒返回 0 时必须抛错，而不是死循环或静默成功。"""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import cls_forbidden_paths as cfp

    target = tmp_path / "stuck.bin"
    fd = os.open(target, os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        monkeypatch.setattr(cfp.os, "write", lambda _fd, _d: 0)
        with pytest.raises(OSError, match="短写"):
            cfp.write_all(fd, b"abc")
    finally:
        monkeypatch.undo()
        os.close(fd)


def test_chmod_pinned_allows_write_only_file(tmp_path: Path):
    """⛔ r9 MEDIUM-1：0200（只写不可读）的既存文件必须能被收紧，而不是打不开就失败。

    我 r8 写的 `except PermissionError: raise` 把**内核**的 EACCES 一并吞了 ——
    `PermissionError` 本身就是 `OSError(EACCES)` 的子类，于是 `O_WRONLY` 回退
    **永远不可达**。修法是给判据自己的拒绝一个专属类型 `ForbiddenPath`，两者才分得开。
    """
    if os.geteuid() == 0:
        pytest.skip("root 无视权限位，0200 也能 O_RDONLY 打开，本条无从制造前提")
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from cls_forbidden_paths import chmod_pinned

    prot = tmp_path / "protected"
    prot.mkdir()
    f = tmp_path / "writeonly.txt"
    f.write_text("x", encoding="utf-8")
    f.chmod(0o200)
    chmod_pinned(str(f), 0o600, live_vault=str(prot))
    assert f.stat().st_mode & 0o777 == 0o600, "0200 文件未被收紧（EACCES 回退不可达）"


def test_tmpdir_and_npm_dirs_are_in_pending_writes():
    """⛔ r10 HIGH-1 + HIGH-2：两处**我自己新开的写入面**必须进同一份待写清单。

    · HIGH-1：我 r9 为「约束 npm 写入面」加的 `mkdir -p "$EVIDENCE_DIR/npm-$TS/{cache,logs}"`
      **本身就是未过判据的写入面** —— evidence 下预置 `npm-<TS> -> 保护目录` 时那个
      mkdir 直接写进去。**为堵写入面而新开的写入面。**
    · HIGH-2：Bash 3.2 对 **here-document** 同样在 `$TMPDIR` 建临时文件（步 2 的
      `pinned_chmod600`、步 3 两处 python 块都会触发）。r9 删掉 `<<<` 只修好了
      preflight **之前**那一条；原唯一的 TMPDIR 检查在步 4，太晚且缺省端口完全跳过。
    """
    src = _sh_src()
    i = src.index("local -a PENDING_WRITES=(")
    block = src[i : src.index("\n    )", i)]
    for key in ("ev-npm-cache:", "ev-npm-logs:"):
        assert key in block, f"待写清单缺 {key}（该写入面未过判据）"
    # ⚠️ `tmpdir` 自 r11 MEDIUM-1 起**不在** PENDING_WRITES 里 —— 那份清单的语义是
    #    「本脚本创建/截断的**叶子文件**」，其消费方会做 `-L` 软链拒绝，而 TMPDIR 是
    #    「**写入其中**的目录」，`/tmp -> /private/tmp` 这种合法软链会被误拒。
    #    它改走 DIR_WRITES：**只过判据、不过叶子规则**。主张不变，位置变了。
    assert 'DIR_WRITES=("tmpdir:${TMPDIR:-/tmp}")' in src, "TMPDIR 未进 DIR_WRITES"
    assert '--outputs "${PENDING_WRITES[@]}" "${DIR_WRITES[@]}"' in src, "DIR_WRITES 必须与 PENDING_WRITES 一起交给判据"
    # 基准固定：相对 --evidence-dir/--env-dir 必须在解析期就绝对化
    assert 'EVIDENCE_DIR="$PWD/$EVIDENCE_DIR"' in src, "相对 --evidence-dir 未做词法绝对化"
    assert 'ENV_DIR="$PWD/$ENV_DIR"' in src, "相对 --env-dir 未做词法绝对化"


def test_hosts_whitespace_stripping_reaches_fixpoint():
    """⛔ r10 LOW-1：混合空白必须剥到不动点。

    我 r9 写的是「空格轮 → tab 轮」四段串行，`\t claude \t` 剥完 tab 后留下的空格
    不会再处理 ⇒ 旧版接受、新版拒绝，是一条行为回归。
    """
    src = _sh_src()
    seg = src[src.index('_rest="$HOSTS"') : src.index("done", src.index('_rest="$HOSTS"'))]
    # ⚠️ 自 r11 LOW-1 起不再用「剥首尾」的不动点循环 —— 旧 `tr -d '[:space:]'` 删的是
    #    **全部位置**的**所有** ASCII 空白（含 \v \f \r 与中间空白）。
    #    bash 模式替换一次删净，零 fork、线性时间（顺带消掉 r10 LOW-2 的二次复杂度）。
    assert "_h=\"${_h//[$' \\t\\n\\r\\v\\f']/}\"" in seg, "去空白必须用模式替换删净全部位置的 ASCII 空白，不能只剥首尾"
    assert "while :; do" not in seg, "剥首尾的不动点循环已被取代，不应再出现"


def test_relative_harness_still_yields_absolute_default_dirs(tmp_path: Path):
    """⛔ r11 HIGH-1：绝对化必须在**默认值赋好之后**。

    我 r10 把词法绝对化放在了默认值赋值**之前** ⇒ `--harness .` + 省略 `--evidence-dir`
    时，默认值 `$HARNESS/_bmad-output/…` 是之后才填的，整条仍是相对串、绝对化白做。
    随后 npm 段先按调用 cwd `mkdir -p`、再 `cd` 进插件目录把同一相对串交给 npm ⇒ 落点分裂。
    """
    r = subprocess.run(
        [
            str(DEPLOY_SH),
            "--vault",
            str(tmp_path / "vaults" / "course"),
            "--harness",
            ".",
            "--port",
            "8291",
            "--hosts",
            "claude",
            "--env-dir",
            str(tmp_path / "env"),
        ],
        capture_output=True,
        timeout=600,
        text=True,
        cwd=REPO_ROOT,
        env={
            **{k: v for k, v in os.environ.items() if k not in _STRIP_ENV},
            "CLS_LIVE_VAULT": str(_fake_live(tmp_path)),
        },
    )
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    m = re.search(r"^\[6/6\] evidence: SKIP will write: (\S+)", r.stdout, re.M)
    assert m, f"没拿到 evidence 路径: {r.stdout!r}"
    assert m.group(1).startswith("/"), f"默认 evidence-dir 仍是相对路径: {m.group(1)!r}"


def test_legitimate_tmpdir_symlink_is_not_rejected(tmp_path: Path):
    """⛔ r11 MEDIUM-1：`TMPDIR=/tmp` 必须放行 —— macOS 的 `/tmp -> /private/tmp` 是**合法**软链。

    我 r10 把 `tmpdir` 塞进 `PENDING_WRITES`，于是它过了**叶子文件**的 `-L` 软链规则，
    `TMPDIR=/tmp`（极常见，未设时也回退到它）当场 rc 71，dry-run 同样中招。
    TMPDIR 是「**写入其中**的目录」而非「本脚本创建/截断的叶子」⇒ 只走判据、不走叶子规则。
    """
    env = {k: v for k, v in os.environ.items() if k not in _STRIP_ENV}
    env["CLS_LIVE_VAULT"] = str(_fake_live(tmp_path))
    base = [
        str(DEPLOY_SH),
        "--vault",
        str(tmp_path / "vaults" / "course"),
        "--harness",
        str(REPO_ROOT),
        "--port",
        "8292",
        "--hosts",
        "claude",
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
    ]
    for tmpdir in ("/tmp", ""):
        r = subprocess.run(
            base, capture_output=True, text=True, env={**env, "TMPDIR": tmpdir}, timeout=_SUBPROCESS_TIMEOUT
        )
        assert r.returncode == 0, f"TMPDIR={tmpdir!r} 被误拒: rc={r.returncode} {r.stdout}"
    # 控制组：指向保护目录仍必须拦
    r = subprocess.run(
        base,
        capture_output=True,
        text=True,
        env={**env, "TMPDIR": str(tmp_path / "protected")},
        timeout=_SUBPROCESS_TIMEOUT,
    )
    (tmp_path / "protected").mkdir(exist_ok=True)
    r = subprocess.run(
        base,
        capture_output=True,
        text=True,
        env={**env, "CLS_LIVE_VAULT": str(tmp_path / "protected"), "TMPDIR": str(tmp_path / "protected")},
        timeout=_SUBPROCESS_TIMEOUT,
    )
    assert r.returncode == 71, f"TMPDIR 指向保护目录未被拦: rc={r.returncode} {r.stdout}"
    assert "tmpdir" in r.stdout, f"消息未点名 tmpdir: {r.stdout!r}"


def test_hosts_strips_all_whitespace_like_tr(tmp_path: Path):
    """⛔ r11 LOW-1：旧 `tr -d '[:space:]'` 删的是**全部位置**的**所有** ASCII 空白。

    含 `\v` `\f` `\r` 与**中间**空白（`cl au\tde` → `claude`）。
    我 r9 只剥首尾空格、r10 改不动点循环仍只剥首尾 —— 两版都不等价。
    """
    env = {k: v for k, v in os.environ.items() if k not in _STRIP_ENV}
    env["CLS_LIVE_VAULT"] = str(_fake_live(tmp_path))
    base = [
        str(DEPLOY_SH),
        "--vault",
        str(tmp_path / "vaults" / "course"),
        "--harness",
        str(REPO_ROOT),
        "--port",
        "8293",
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
    ]
    for hosts in ("cl au\tde", "\vclaude\f", "\rclaude\r", "\t claude \t"):
        real = hosts.encode().decode("unicode_escape")
        r = subprocess.run(
            base + ["--hosts", real], capture_output=True, text=True, env=env, timeout=_SUBPROCESS_TIMEOUT
        )
        assert r.returncode == 0, f"--hosts {real!r} 被误拒: rc={r.returncode} {r.stderr}"
    r = subprocess.run(
        base + ["--hosts", "claude,codex"], capture_output=True, text=True, env=env, timeout=_SUBPROCESS_TIMEOUT
    )
    assert r.returncode == 64, "二线宿主必须仍被拒（判据不能因放宽空白而放宽宿主）"


def test_no_here_string_before_preflight():
    """⛔ r9 HIGH-1：`<<<` 在 Bash 3.2 下会在 `$TMPDIR` **建临时文件**。

    `--hosts` 的解析在 preflight **之前**、dry-run 也会走到 —— `TMPDIR` 指向保护目录时
    就是一次先于任何判据的写入，事后删除撤不回。步 4 的 TMPDIR 检查来得太晚，
    且只覆盖非 8011 的镜像分支。
    ⇒ 改成纯参数展开切分（零子进程、零临时文件）。本门钉住它不许回退。
    """
    src = _sh_src()
    code = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
    assert "<<<" not in code, "非注释行仍有 here-string（Bash 3.2 会写临时文件）"
    assert '_rest="$HOSTS"' in code, "--hosts 必须用纯参数展开切分"


def test_chmod_pinned_rejects_hardlink_and_nonregular(tmp_path: Path):
    """⛔ r8 HIGH-3 / MEDIUM-2：`chmod_pinned` 必须挡硬链接、且只对普通文件生效。

    叶子被换成**保护文件的硬链接**时 `O_NOFOLLOW` 照常打开，直接 `fchmod` 就改了共享 inode
    ——这个洞旧的裸 `chmod` 也有，不是本轮新造，但必须补上。
    目录若被 `chmod 0600` 会丢搜索权限；FIFO 会让 `open` 阻塞（故原语带 `O_NONBLOCK`）。
    """
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from cls_forbidden_paths import chmod_pinned

    prot = tmp_path / "protected"
    prot.mkdir()
    victim = tmp_path / "victim.txt"
    victim.write_text("x", encoding="utf-8")
    victim.chmod(0o644)
    hard = tmp_path / "hardlink.txt"
    os.link(victim, hard)
    with pytest.raises(OSError, match="硬链接"):
        chmod_pinned(str(hard), 0o600, live_vault=str(prot))
    assert victim.stat().st_mode & 0o777 == 0o644, "共享 inode 的权限被改了"

    d = tmp_path / "adir"
    d.mkdir(mode=0o755)
    with pytest.raises(OSError):
        chmod_pinned(str(d), 0o600, live_vault=str(prot))
    assert d.stat().st_mode & 0o777 == 0o755, "目录被 chmod 成 0600 会丢搜索权限"

    # 控制组：普通单链接文件必须正常收紧（判据不是「永远拒」）
    ok = tmp_path / "ok.txt"
    ok.write_text("y", encoding="utf-8")
    ok.chmod(0o644)
    chmod_pinned(str(ok), 0o600, live_vault=str(prot))
    assert ok.stat().st_mode & 0o777 == 0o600


def test_script_disables_bytecode_cache_before_importing_primitives():
    """⛔ r8 HIGH-2：`import cls_forbidden_paths` 本身会写 `scripts/__pycache__/*.pyc`。

    那次写入发生在 `open_pinned` 检查**之前**，也不在 preflight 的待写清单里 ——
    `__pycache__` 若指向保护目录就是一次**未受检写入**。
    把判据搬进模块换来了单一来源，同时新造了一个写入面：每个架构改动都要重新问
    「它新增了哪些写入」。
    """
    # ⚠️ 用 find 而不是 index：`index` 找不到会抛 ValueError，红的就不是这条断言了
    #    —— 本卡第 3 次踩这个形状（r6 MEDIUM-3 首次由 Codex 指出）。
    src = _sh_src()
    export_at = src.find("export PYTHONDONTWRITEBYTECODE=1")
    first_import = src.find("from cls_forbidden_paths import")
    assert export_at != -1, "禁字节码缓存必须在任何 import 之前（export 整行缺失）"
    assert first_import == -1 or export_at < first_import, "禁字节码缓存必须在任何 import 之前"


def test_multi_segment_relative_vault_is_rejected_at_entry(tmp_path: Path):
    """⛔ r6 MEDIUM-2：`relcourse` 那条 KILLED **证不了入口门承重**。

    单段相对路径即使入口检查被删，也仍会被后面的 `case */*` 不变量断言拦成 rc 64、
    消息同样含「绝对路径」——两条分支给出同样的结果，变异因此杀不掉。
    **多段**相对输入 `parent/course` 才只有入口那一条能拦。
    """
    (tmp_path / "parent" / "course").mkdir(parents=True)
    r = _preview(tmp_path, "parent/course", "8197", cwd=tmp_path)
    assert r.returncode == 64, f"多段相对 --vault 未被入口拒: rc={r.returncode} {r.stdout}{r.stderr}"
    assert "绝对路径" in r.stderr, f"消息未点明原因: {r.stderr!r}"


# ═══ Codex r6 BLOCKER-2：保护目标解析成根时，`tk + os.sep` = "//" ⇒ 三处比较一起漏 ═══
def test_forbidden_judge_handles_protected_target_at_root(tmp_path: Path):
    """⛔ r6 BLOCKER-2：`.claude-cache -> /` 这类退化配置下，一切路径都该被拦。

    原来三处各手写 `key == tk or key.startswith(tk + os.sep)`，`tk` 为 `/` 时后半段
    变成 `"//"`，`/safe/out` 两边都不满足 ⇒ **全部漏拦**。三份手抄的比较必然一起错。
    """
    home = tmp_path / "home"
    home.mkdir()
    (home / ".claude-cache").symlink_to("/", target_is_directory=True)
    live = tmp_path / "fake-live"
    live.mkdir()
    safe = tmp_path / "safe"
    safe.mkdir()
    r = _forbid_home(home, str(live), f"--env-dir:{safe / 'out'}")
    assert r.returncode != 0, f"保护目标为根时漏拦: {r.stdout}{r.stderr}"


def test_forbidden_judge_checks_root_path_input(tmp_path: Path):
    """⛔ r7 MEDIUM-2：输入**本身就是根**（`/`、`////`、`/./`）时判据一条都不跑。

    `mkdir_p_segments("/")` 返回**空列表**，逐段循环于是零次迭代、直接落到 `OK`。
    空列表不代表「没有写入面」，而代表「写入面就是根本身」。

    ⚠️ 本条与上一条测的是**两件事**：上一条是「保护**目标**解析成根」，
    这一条是「**输入路径**是根」。r7 首轮变异 SURVIVED 正是因为我只有上一条 ——
    门没测到它自称测的那件事（`segs = [os.sep]` 那行删掉，上一条照样绿）。
    """
    home = tmp_path / "home"
    home.mkdir()
    (home / ".claude-cache").symlink_to("/", target_is_directory=True)
    live = tmp_path / "fake-live"
    live.mkdir()
    for probe in ("/", "////", "/./"):
        r = _forbid_home(home, str(live), f"--env-dir:{probe}")
        assert r.returncode != 0, f"根路径输入 {probe!r} 未被判据检查: {r.stdout}{r.stderr}"


# ═══ Codex r6 BLOCKER-1：第一跳可读 ≠ 整条链可解析 ════════════════════════════
def test_forbidden_judge_fail_closed_when_second_hop_unsearchable(tmp_path: Path):
    """⛔ r6 BLOCKER-1：`.claude-cache -> /opaque/hop -> /external/protected`。

    `/opaque` 不可搜索时，**第一跳** `readlink` 成功（r5 只验到这里），
    而 `realpath(strict=False)` 把 EACCES 吞掉、只登记到 `/opaque/hop`，
    `enumerate_failed` 仍是 False ⇒ 直接写 `/external/protected/x` 被放行。
    """
    if os.geteuid() == 0:
        pytest.skip("以 root 运行时权限位不生效，本条无从制造前提")
    home = tmp_path / "home"
    home.mkdir()
    opaque = tmp_path / "opaque"
    opaque.mkdir()
    protected = tmp_path / "external" / "protected"
    protected.mkdir(parents=True)
    (opaque / "hop").symlink_to(protected, target_is_directory=True)
    (home / ".claude-cache").symlink_to(opaque / "hop", target_is_directory=True)
    live = tmp_path / "fake-live"
    live.mkdir()
    safe = tmp_path / "safe"
    safe.mkdir()
    os.chmod(opaque, 0o644)  # 可读不可搜索
    try:
        assert not os.access(opaque / "hop", os.F_OK), "前提不成立：中间跳仍可解析"
        r = _forbid_home(home, str(live), f"--env-dir:{safe / 'x'}")
    finally:
        os.chmod(opaque, 0o755)
    assert r.returncode != 0, f"第二跳不可搜索时未 fail-closed: {r.stdout}{r.stderr}"
    assert "fail-closed" in r.stdout, f"未走 fail-closed 分支: {r.stdout!r}"


# ═══ Codex r6 MEDIUM-1：上限计的应是软链跳数，不是处理过的段数 ════════════════
def test_forbidden_judge_does_not_block_deep_but_linkless_path(tmp_path: Path):
    """⛔ r6 MEDIUM-1：`"/" + "./"*300 + "safe/out"` 实际只是 `/safe/out`，没有任何软链。

    r5 我把计数放在循环顶端（数的是**段**），于是这种合法浅路径也撞上限 ⇒ 误拦。
    只有解链才可能不收敛（环），普通段只会让待处理队列变短、必然终止。
    """
    live = tmp_path / "fake-live"
    live.mkdir()
    safe = tmp_path / "safe"
    safe.mkdir()
    home = tmp_path / "home"
    home.mkdir()  # 必须是**真实存在**的目录，否则 os.access 失败会走 _enumerate fail-closed
    deep = "/" + "./" * 300 + str(safe).lstrip("/") + "/out"
    r = _forbid_home(home, str(live), f"--env-dir:{deep}")
    assert r.returncode == 0, f"无软链的深段路径被误拦: {r.stdout}{r.stderr}"


def test_forbidden_judge_fail_closed_on_symlink_loop(tmp_path: Path):
    """控制组（另一个方向）：真正的软链环必须仍然 fail-closed。

    上限从「段数」改成「跳数」之后，它守住的是环 —— 这条证明那道保护还在。
    """
    live = tmp_path / "fake-live"
    live.mkdir()
    loop = tmp_path / "loop"
    other = tmp_path / "other"
    loop.symlink_to(other)
    other.symlink_to(loop)
    home = tmp_path / "home"
    home.mkdir()  # 同上：HOME 必须真实存在，否则红的会是 _enumerate 而不是环
    r = _forbid_home(home, str(live), f"--env-dir:{loop / 'x'}")
    assert r.returncode != 0, f"软链环未 fail-closed: {r.stdout}{r.stderr}"
    assert "fail-closed" in r.stdout, f"应因跳数超限 fail-closed，实际: {r.stdout!r}"


def test_forbidden_judge_does_not_fail_closed_on_normal_home(tmp_path: Path):
    """控制组：正常可读可搜索的 HOME 必须**不**报 fail-closed。

    否则这条整改会把判据变成「永远拦」——比漏拦更难发现。
    """
    home = tmp_path / "home"
    home.mkdir()
    live = tmp_path / "fake-live"
    live.mkdir()
    safe = tmp_path / "safe"
    safe.mkdir()
    r = _forbid_home(home, str(live), f"--env-dir:{safe / 'x'}")
    assert r.returncode == 0, f"正常 HOME 下误报: {r.stdout}{r.stderr}"
    assert "fail-closed" not in r.stdout


# ═══ 行为门：替代不承重的源码门（Codex r2 MEDIUM）══════════════════════════════
@pytest.mark.skipif(
    not (REPO_ROOT / "canvas-vault" / ".obsidian" / "plugins" / "canvas-learning-system" / "main.js").exists(),
    reason="树上无 gitignored main.js 时 apply 会触发 npm run build",
)
def test_step4_actually_evaluates_content_drift_when_port_differs(tmp_path: Path):
    """步 4 在 `--port != 8011` 时必须**真的评了 content-drift**，而不是跳过它。

    Codex r2 MEDIUM 指出源码门不承重：把 `src="$SRC_MIRROR"` 改回源树、或把步 4 的
    模板化清单砍成一项，`assert "--source" in step4` / `assert "SRC_MIRROR" in step4`
    照样绿。所以这里改成**看报告内容**：

      · `content-drift : 0`  ⇒ 传了 --source 且没有漂移（若不传 --source，
        校验器会打 `not evaluated`，这条断言直接红）
      · `match` > 0          ⇒ 真比过内容，不是空集比空集
    """
    r = _apply(tmp_path, "probe_drift", "8189")
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    m = re.search(r"^\[4/6\] verify: (OK|SKIP|FAIL) (.*)$", r.stdout, re.M)
    assert m and m.group(1) == "OK", f"步 4 不是 OK: {r.stdout}"
    assert "源镜像" in m.group(2), f"步 4 未用源镜像做基准: {m.group(2)}"

    reports = sorted((tmp_path / "ev").glob("verify-*.txt"))
    assert reports, f"没有 verify 报告: {list((tmp_path / 'ev').iterdir())}"
    body = reports[-1].read_text(encoding="utf-8")
    drift = re.search(r"^content-drift\s*:\s*(\S+)", body, re.M)
    assert drift, f"报告里没有 content-drift 行:\n{body[:600]}"
    assert drift.group(1) == "0", (
        f"content-drift = {drift.group(1)!r} —— 'not evaluated' 意味着没传 --source，"
        f"内容比较这一整个轴被丢掉了（门却会因为源码里有 '--source' 字样而绿）"
    )
    match = re.search(r"^match\s*:\s*(\d+)", body, re.M)
    assert match and int(match.group(1)) > 0, f"match = {match.group(1) if match else '?'} —— 空集比空集也会得 drift 0"


@pytest.mark.skipif(
    not (REPO_ROOT / "canvas-vault" / ".obsidian" / "plugins" / "canvas-learning-system" / "main.js").exists(),
    reason="树上无 gitignored main.js 时 apply 会触发 npm run build",
)
def test_step4_leaves_no_source_mirror_behind(tmp_path: Path):
    """源镜像必须被清掉 —— 清理失败时步 4 应报 FAIL 而不是静默 OK。"""
    before = set(Path(os.environ.get("TMPDIR", "/tmp")).glob("cls-srcmirror-*"))
    r = _apply(tmp_path, "probe_mirror", "8188")
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}"
    after = set(Path(os.environ.get("TMPDIR", "/tmp")).glob("cls-srcmirror-*"))
    assert after <= before, f"步 4 留下了源镜像: {sorted(after - before)}"


def test_preflight_treats_lsof_error_as_unknown_not_free(tmp_path: Path):
    """`lsof` 出错（rc 既非 0 也非 1）时不得当成「端口空闲」（Codex r2 M14 的 NOGATE 补门）。

    r2 变异 M14 把 lsof 的三态退回两态（出错当空闲），当时**没有门能抓**，如实标了 NOGATE。
    这条门用一个假 lsof（恒 rc=2）放进 PATH 最前，验证 preflight 会拒而不是放行。
    """
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_lsof = fake_bin / "lsof"
    fake_lsof.write_text("#!/usr/bin/env bash\nexit 2\n", encoding="utf-8")
    fake_lsof.chmod(0o755)

    r = _run(
        "--vault",
        str(tmp_path / "vaults" / "ok_name"),
        "--harness",
        str(REPO_ROOT),
        "--port",
        "8187",
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={
            "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}",
            "CLS_LIVE_VAULT": str(_fake_live(tmp_path)),
        },
    )
    assert r.returncode == 71, f"lsof rc=2 时应拒（无从断言空闲），实为 rc={r.returncode}: {r.stdout}"
    assert "lsof" in r.stdout and "无从断言" in r.stdout, r.stdout


def test_preflight_still_passes_when_lsof_says_free(tmp_path: Path):
    """控制组：假 lsof 恒 rc=1（无命中 = 空闲）时必须**放行** —— 否则上一条门退化成永远拦。"""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_lsof = fake_bin / "lsof"
    fake_lsof.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    fake_lsof.chmod(0o755)

    r = _run(
        "--vault",
        str(tmp_path / "vaults" / "ok_name"),
        "--harness",
        str(REPO_ROOT),
        "--port",
        "8186",
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={
            "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}",
            "CLS_LIVE_VAULT": str(_fake_live(tmp_path)),
        },
    )
    assert r.returncode == 0, f"lsof 说空闲时被误拒: rc={r.returncode} {r.stdout}"


def test_forbidden_judge_claude_prefix_rule_covers_nonexistent(tmp_path: Path):
    """`.claude*` 的**前缀规则**（覆盖尚不存在的条目）要有定向输入（Codex r3 MEDIUM-5）。

    现有软链样本最终都落在 prot，在这条规则之前就命中了 —— 删掉它样本仍全绿。
    这条门直接打一个 HOME 下**不存在**的 `.claude-*` 目录。
    """
    prot = tmp_path / "prot"
    prot.mkdir()
    target = str(Path.home() / ".claude-nonexistent-gate-probe" / "sub")
    r = _forbid(str(prot), f"p:{target}")
    assert r.returncode == 1, f"前缀规则没拦住尚不存在的 .claude*: {r.stdout}"
    assert ".claude" in r.stdout, r.stdout
    assert not Path(target).exists(), "判据不该创建任何东西"


def test_forbidden_judge_claude_enumeration_rule_is_case_insensitive():
    """`.claude*` **枚举规则**必须大小写不敏感（Codex r3 HIGH-1 第二半）。

    ⚠️ 如实声明局限：这条无法用 HOME 下的真实条目构造（不该往用户 HOME 建 `.CLAUDE-*`
    做测试），故改用源码断言，并把这个局限写在这里 —— 它是**源码门**，对等价重写不敏感。
    """
    src = FORBID_PY.read_text(encoding="utf-8")
    assert 'name.lower().startswith(".claude")' in src, (
        "枚举规则不是大小写不敏感的（`.CLAUDE-cache -> /external/x` 会漏登记）"
    )
    assert "enumerate_failed" in src, "HOME 枚举失败未 fail-closed"


def test_forbidden_judge_fails_closed_when_home_unenumerable(tmp_path: Path):
    """HOME 不可枚举时必须 fail-closed（Codex r3 HIGH-1）。

    把 HOME 指到一个**只有执行权限、没有读权限**的目录：已知子路径仍可访问，
    但 `listdir` 会失败 —— 此时 `.claude*` 的外部软链目标整批登记不上，
    判据不得声称「全部 OK」。
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (fake_home / ".claude").mkdir()
    prot = tmp_path / "prot"
    prot.mkdir()
    (tmp_path / "safe").mkdir()
    fake_home.chmod(0o111)  # --x--x--x：可进入、不可列目录
    try:
        env = dict(os.environ)
        env["HOME"] = str(fake_home)
        r = subprocess.run(
            [sys.executable, str(FORBID_PY), str(prot), f"p:{tmp_path}/safe/ok"],
            capture_output=True,
            text=True,
            env=env,
            timeout=_SUBPROCESS_TIMEOUT,
        )
        assert r.returncode == 1, f"HOME 不可枚举时仍报全 OK（应 fail-closed）: rc={r.returncode} {r.stdout}"
        assert "fail-closed" in r.stdout or "_enumerate" in r.stdout, r.stdout
    finally:
        fake_home.chmod(0o755)


# ═══ Codex r4 BLOCKER-4：路径判据保护不了 inode（硬链接）═════════════════════════
def test_preflight_rejects_hardlinked_env_tmp(tmp_path: Path):
    """⛔ r4 BLOCKER-4：`.env.<vault>.tmp` 与别处共享 inode 时必须拒。

    realpath 给出的是**合法路径**、`-L` 为假 —— 判据看路径完全看不见这一层，
    但 `: >` 截断改的是那个**共享 inode**。三层防线（判据 / -L / 硬链接）各管一件事。
    """
    (tmp_path / "vaults" / "course").mkdir(parents=True)
    env_d = tmp_path / "env"
    env_d.mkdir()
    victim = tmp_path / "victim.txt"
    victim.write_text("原内容\n", encoding="utf-8")
    os.link(victim, env_d / ".env.course.tmp")

    r = _run(
        "--vault",
        str(tmp_path / "vaults" / "course"),
        "--harness",
        str(REPO_ROOT),
        "--port",
        "8191",
        "--hosts",
        "claude",
        "--env-dir",
        str(env_d),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
    )
    assert r.returncode == 71, f"rc={r.returncode}（应为 71 preflight）: {r.stdout}{r.stderr}"
    assert "硬链接" in r.stdout, f"消息没说是硬链接: {r.stdout}"
    # 控制组的一半：受害文件必须一个字节都没动
    assert victim.read_text(encoding="utf-8") == "原内容\n", "共享 inode 已被改动"


def test_preflight_passes_when_env_tmp_has_single_link(tmp_path: Path):
    """控制组（另一个方向）：只有一个链接的既存 tmp 文件必须**放行**。

    只测「该拦的拦住了」会让这条判据退化成「凡文件存在就拦」。
    """
    (tmp_path / "vaults" / "course").mkdir(parents=True)
    env_d = tmp_path / "env"
    env_d.mkdir()
    (env_d / ".env.course.tmp").write_text("残留\n", encoding="utf-8")

    r = _run(
        "--vault",
        str(tmp_path / "vaults" / "course"),
        "--harness",
        str(REPO_ROOT),
        "--port",
        "8192",
        "--hosts",
        "claude",
        "--env-dir",
        str(env_d),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
    )
    assert r.returncode == 0, f"误拦了单链接的既存 tmp: rc={r.returncode} {r.stdout}{r.stderr}"


# ═══ Codex r4 HIGH-2：父路径含空格 ═══════════════════════════════════════════
def test_vault_parent_with_space_survives_name_pipeline(tmp_path: Path):
    """⛔ r4 HIGH-2：我 r3 加 `VAULTS_ROOT` 比较时用了「空格串 + for 拆词」。

    `/tmp/course vaults/course` 会被拆成两项：比较拿到截断的 `VAULTS_ROOT=/tmp/course`
    外加一个游离的 `vaults` —— **合法部署在安装完成后 rc=73**，重跑又被 72 拦住。
    这里只跑 dry-run（不 build），钉的是名字管道：VAULTS_ROOT 必须是完整父路径。
    """
    parent = tmp_path / "course vaults"
    (parent / "course").mkdir(parents=True)
    r = _run(
        "--vault",
        str(parent / "course"),
        "--harness",
        str(REPO_ROOT),
        "--port",
        "8193",
        "--hosts",
        "claude",
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
    )
    assert r.returncode == 0, f"含空格父路径没跑通: rc={r.returncode} {r.stdout}{r.stderr}"
    assert "vault=course" in r.stdout, f"vault 名被空格打断: {r.stdout.splitlines()[0]}"
    m = re.search(r"^\[2/6\] install: SKIP will run: (.*)$", r.stdout, re.M)
    assert m, f"没有 install 预览行: {r.stdout}"
    # 预览行必须**能粘贴执行** ⇒ 含空格的值经过转义, 且解析回来就是那个完整父路径
    argv = shlex.split(m.group(1))
    i = argv.index("--vaults-root")
    assert argv[i + 1] == str(parent), f"--vaults-root 被截断: {argv[i + 1]!r} != {str(parent)!r}"


def test_want_pairs_is_not_word_split(tmp_path: Path):
    """源码反向锚：那份「空格分隔字符串 + for 拆词」的写法不得回来。"""
    src = DEPLOY_SH.read_text(encoding="utf-8")
    assert "for kv in $want_pairs" not in src, "又用回了会按空格拆词的 for（r4 HIGH-2）"
    assert "local -a want_keys=(" in src and "local -a want_vals=(" in src, "A3 一致性比较必须用数组（元素含空格不拆）"


# ═══ Codex r4 MEDIUM-3：dirname/basename 语义 ═════════════════════════════════
def _preview(tmp_path: Path, vault: str, port: str, cwd: Path | None = None):
    full_env = dict(os.environ)
    for _k in _STRIP_ENV:
        full_env.pop(_k, None)
    full_env["CLS_LIVE_VAULT"] = str(_fake_live(tmp_path))
    return subprocess.run(
        [
            str(DEPLOY_SH),
            "--vault",
            vault,
            "--harness",
            str(REPO_ROOT),
            "--port",
            port,
            "--hosts",
            "claude",
            "--env-dir",
            str(tmp_path / "env"),
            "--evidence-dir",
            str(tmp_path / "ev"),
        ],
        capture_output=True,
        text=True,
        env=full_env,
        cwd=str(cwd or REPO_ROOT),
        timeout=120,
    )


def test_trailing_slash_vault_yields_same_name_and_parent(tmp_path: Path):
    """⛔ r4 MEDIUM-3：`${VAULT##*/}` 对尾斜杠给出**空** vault 名。

    我 r3 为了保住 argv 末尾换行（r3 BLOCKER-4）把 `$(dirname)`/`$(basename)` 换成了
    参数展开，但没补 dirname/basename 的两个语义。带不带尾斜杠必须给出同一结果。
    """
    (tmp_path / "vaults" / "course").mkdir(parents=True)
    base = str(tmp_path / "vaults" / "course")
    a = _preview(tmp_path, base, "8194")
    b = _preview(tmp_path, base + "/", "8194")
    assert a.returncode == 0 and b.returncode == 0, f"{a.returncode}/{b.returncode}"
    assert "vault=course" in b.stdout, f"尾斜杠把 vault 名弄空了: {b.stdout.splitlines()[0]}"

    def grab(proc):
        m = re.search(r"^\[2/6\] install: SKIP will run: (.*)$", proc.stdout, re.M)
        assert m, f"没有 install 预览行: {proc.stdout}"
        return m.group(1)

    assert grab(a) == grab(b), f"尾斜杠改变了安装参数:\n{grab(a)}\n{grab(b)}"


def test_relative_vault_is_rejected_at_entry(tmp_path: Path):
    """⛔ Codex r5 HIGH-2：相对 `--vault` 一律 rc 64，不再进六步。

    **本条替换了旧的 `test_single_segment_relative_vault_gets_dot_as_parent`**，
    那条门钉的是 r4 的行为（单段相对路径 ⇒ `--vaults-root .`）。r5 指出该行为本身
    就是缺陷：`.` 由 installer 按**调用 cwd** 解释，而写进 `.env.<vault>` 的
    `VAULTS_ROOT=.` 由 compose 按 `--project-directory "$HARNESS"` 解释
    （`docker-compose.yml` 的 `"${VAULTS_ROOT:-.}:/vaults:…"`）。从非 harness 目录
    部署就会「库建在 cwd、容器却挂 harness」，而步 5 的 config 断言只验容器名与端口，
    **抓不到**。头注本就写「必填绝对路径」，此前只判非空 = 文档与实现不一致。

    ⇒ 统一解析基准的最小做法是让相对路径根本进不来。
    """
    (tmp_path / "relcourse").mkdir()
    r = _preview(tmp_path, "relcourse", "8195", cwd=tmp_path)
    assert r.returncode == 64, f"相对 --vault 未被入口拒: rc={r.returncode} {r.stdout}{r.stderr}"
    assert "绝对路径" in r.stderr, f"消息未点明原因: {r.stderr!r}"


def test_absolute_vault_still_previews_with_absolute_vaults_root(tmp_path: Path):
    """控制组（另一个方向）：绝对 `--vault` 必须照常走完六步，且 `--vaults-root` 绝对。

    ⛔ 只测「该拦的拦住了」会让判据退化成「永远拦」—— 本卡 r2 就是这么把所有正控
    打成 rc 71 的。这条钉住 H-2 的整改**没有**顺手拒掉合法输入。
    """
    (tmp_path / "relcourse").mkdir()
    r = _preview(tmp_path, str(tmp_path / "relcourse"), "8196", cwd=tmp_path)
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    argv = shlex.split(re.search(r"^\[2/6\] install: SKIP will run: (.*)$", r.stdout, re.M).group(1))
    i = argv.index("--vaults-root")
    assert argv[i + 1] == str(tmp_path), f"vaults-root 应是绝对父目录: {argv[i + 1]!r}"
    assert argv[i + 1].startswith("/"), "vaults-root 必须绝对，否则解析基准仍会分裂"


def _fake_python3(tmp_path: Path, c_output: str) -> Path:
    """造一个只劫持 `python3 -c` 的假 python3，其余参数原样转给真 python3。

    只劫持 `-c` 是为了**精确**：脚本还用 python3 跑禁写面判据与名不动点，
    整体替换会让用例因为别的原因红，证明不了想证明的那一条。
    """
    real = shutil.which("python3")
    assert real, "宿主没有 python3"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir(exist_ok=True)
    f = fake_bin / "python3"
    # ⚠️ 用 raw string 写 bash 的 `\n`：普通字符串里它是**真换行**，
    #    生成出来的脚本会 printf 出 `1n` 这样的怪值（本条门第一版就这么红的）。
    f.write_text(
        "#!/usr/bin/env bash\n"
        'for a in "$@"; do\n'
        '  if [ "$a" = "-c" ]; then\n'
        r'    printf "%s\n" ' + shlex.quote(c_output) + "\n"
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exec " + shlex.quote(real) + ' "$@"\n',
        encoding="utf-8",
    )
    f.chmod(0o755)
    return fake_bin


def _preflight_with_existing_env_tmp(tmp_path: Path, port: str, fake_bin: Path | None):
    (tmp_path / "vaults" / "course").mkdir(parents=True, exist_ok=True)
    env_d = tmp_path / "env"
    env_d.mkdir(exist_ok=True)
    (env_d / ".env.course.tmp").write_text("残留\n", encoding="utf-8")
    env = {"CLS_LIVE_VAULT": str(_fake_live(tmp_path))}
    if fake_bin:
        env["PATH"] = f"{fake_bin}:{os.environ.get('PATH', '')}"
    return _run(
        "--vault",
        str(tmp_path / "vaults" / "course"),
        "--harness",
        str(REPO_ROOT),
        "--port",
        port,
        "--hosts",
        "claude",
        "--env-dir",
        str(env_d),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env=env,
    )


def test_preflight_rejects_nonnumeric_nlink(tmp_path: Path):
    """⛔ 链接数「问不出来」必须 fail-closed，**非数字也算问不出来**。

    原写法只判空串，非数字会落到 `[ "$nlink" -gt 1 ]` —— 那会 rc=2、`if` 判假 ⇒
    **静默放行**（该拦的没拦）。三态里最容易漏的就是「拿到了东西但不是我要的东西」。
    """
    r = _preflight_with_existing_env_tmp(tmp_path, "8197", _fake_python3(tmp_path, "not-a-number"))
    assert r.returncode == 71, f"非数字链接数应 fail-closed，实为 rc={r.returncode}: {r.stdout}"
    assert "问不出链接数" in r.stdout, r.stdout


def test_preflight_passes_when_nlink_reads_one(tmp_path: Path):
    """控制组：同一套假 python3 机关、只把 `-c` 的输出换成合法的 `1` —— 必须放行。

    没有这一条，上一条门可能只是证明了「假 python3 把脚本弄坏了」。
    """
    r = _preflight_with_existing_env_tmp(tmp_path, "8198", _fake_python3(tmp_path, "1"))
    assert r.returncode == 0, f"合法链接数 1 被误拦: rc={r.returncode} {r.stdout}{r.stderr}"


# ═══ CARD-DEPLOY-TIMEOUT：步 1 npm build 的墙钟上限（集成期裁定 R-15）════════════
#
# 背景：候选树跑 tests/unit 时，真跑 DEPLOY_SH 的用例**逐个无限挂起** —— 挂点是
# `deploy-vault.sh` 步 1 在缺 gitignored main.js 时触发的 `npm run build`，它原先
# **没有任何墙钟上限**。本节的三条用例钉住修复后的三件事：
#   ① 挂起会在上限到点时被打断，且 STEP_MSG 是**超时专属文案**（不是笼统失败）；
#   ② 秒级 build 不被误杀（正向对照，证明上限不是「永远杀」）；
#   ③ build 因别的原因失败时**不得**报成超时（文案必须能分辨两种失败）。
#
# ⚠️ 三条都用**假 npm + 自洽的假 harness**：不依赖真实前端目录、不联网、也不依赖
#    本机树上是否有 gitignored main.js（假 harness 里恒无 main.js ⇒ 恒走 build 分支）。
#    正因如此，本节**不加**既有那条 `main.js` skipif —— 它是给「真跑真 build」的用例用的。


def _npm_cap_harness(tmp_path: Path, mode: str) -> tuple[Path, Path]:
    """造一棵自洽的假 harness + 假 npm（置于 PATH 最前，手法同 :2220 的假 lsof）。

    harness 只做到「够 step1_preflight 走完、走到 npm build 分支」：四个必需文件 +
    ≥ CLS_MIN_SKILLS 个含 SKILL.md 的目录 + 一个能跑的 venv python + 两个恒等命名函数
    （`sanitize_vault_id` / `vault_key` 的共同不动点判据）+ 一个**空的**前端插件目录。
    `install-vault.sh` 是恒 rc=1 的桩：build 过关后整跑会停在步 2（rc 72），
    不会把真 installer 拉进单测（本节只验步 1）。

    mode:
      hang — 永久挂起, 并 fork 一个孙子进程（验证上限杀的是整个**进程组**）
      fast — 秒级产出 main.js（正向对照）
      fail — 立刻 rc=1（失败 ≠ 超时的对照）
    返回 (harness 根, 假 npm 写 pid 的目录)。
    """
    h = tmp_path / "harness"
    scripts = h / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "install-vault.sh").write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    (scripts / "install-vault.sh").chmod(0o755)
    (scripts / "verify_vault_install.py").write_text("", encoding="utf-8")
    (scripts / "vault-install-manifest.json").write_text("{}\n", encoding="utf-8")
    (scripts / "send_bark.py").write_text("def vault_key(name):\n    return name\n", encoding="utf-8")
    (h / "docker-compose.yml").write_text("", encoding="utf-8")

    app = h / "backend" / "app"
    app.mkdir(parents=True)
    (app / "__init__.py").write_text("", encoding="utf-8")
    (app / "config.py").write_text("def sanitize_vault_id(name):\n    return name\n", encoding="utf-8")
    venv_bin = h / "backend" / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    os.symlink(sys.executable, venv_bin / "python")

    skills = h / "canvas-vault" / ".claude" / "skills"
    for i in range(9):  # 缺省 CLS_MIN_SKILLS=9，零余量
        (skills / f"probe{i}").mkdir(parents=True)
        (skills / f"probe{i}" / "SKILL.md").write_text("# stub\n", encoding="utf-8")
    # 恒无 main.js ⇒ step1 必定 NEED_BUILD=1（不建 .obsidian 子树即可）
    (h / "frontend" / "obsidian-plugin").mkdir(parents=True)
    (h / "frontend" / "obsidian-plugin" / "package.json").write_text(
        '{"name": "stub", "scripts": {"build": "true"}}\n', encoding="utf-8"
    )

    pids = tmp_path / "npm-pids"
    pids.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    body = {
        # 先落 pid 再挂起：孙子进程用来验证「杀到整个进程组」而不只是杀壳
        "hang": 'printf "%s\\n" "$$" > "$CLS_FAKE_NPM_PIDS/npm.pid"\n'
        "sleep 3600 &\n"
        'printf "%s\\n" "$!" > "$CLS_FAKE_NPM_PIDS/grandchild.pid"\n'
        "wait\n",
        # cwd 已被脚本 cd 进 $HARNESS/frontend/obsidian-plugin
        "fast": 'printf "// fake build output\\n" > main.js\n',
        "fail": "exit 1\n",
        # ⛔ Codex r1 MEDIUM-2：build 自己立刻 rc=124 曾与「上限到点」在退出码上无法区分
        "rc124": "exit 124\n",
    }[mode]
    npm = bin_dir / "npm"
    # 每种形态都先记下**脚本真正传进来的 npm 配置**（离线开关是否真到了 npm 手里）——
    # 没有这一笔，删掉脚本里那行 npm_config_offline 也不会有任何一条用例变红（Codex r1 LOW-1）。
    rec = 'printf "offline=%s\\n" "${npm_config_offline-<unset>}" > "$CLS_FAKE_NPM_PIDS/npm-env.txt"\n'
    npm.write_text("#!/usr/bin/env bash\n" + rec + body, encoding="utf-8")
    npm.chmod(0o755)
    return h, pids


def _npm_cap_env(tmp_path: Path, pids: Path, cap: str | int, extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {
        "PATH": f"{tmp_path / 'bin'}:{os.environ.get('PATH', '')}",
        "CLS_LIVE_VAULT": str(_fake_live(tmp_path)),
        "CLS_FAKE_NPM_PIDS": str(pids),
        "CLS_NPM_BUILD_TIMEOUT": str(cap),
    }
    if extra:
        env.update(extra)
    return env


def _npm_cap_run(
    tmp_path: Path,
    h: Path,
    pids: Path,
    port: str,
    cap: str | int = 5,
    extra_env: dict[str, str] | None = None,
):
    return _run(
        "--vault",
        str(tmp_path / "vaults" / "npmcap"),
        "--harness",
        str(h),
        "--port",
        port,
        "--hosts",
        "claude",
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        "--apply",
        env=_npm_cap_env(tmp_path, pids, cap, extra_env),
        timeout=45,
    )


def _npm_was_invoked(pids: Path) -> bool:
    """假 npm 是否真的被调到 —— 用来把「没走到 build 分支」与「上限没生效」分开诊断。"""
    return (pids / "npm-env.txt").is_file()


def _pid_gone(pid: int, deadline: float = 5.0) -> bool:
    """在 deadline 内轮询 `kill(pid, 0)`，进程消失即 True。"""
    end = time.monotonic() + deadline
    while time.monotonic() < end:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:  # 存在但不是我们的 —— 当作还活着
            pass
        time.sleep(0.1)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def _reap(pids: Path) -> None:
    """兜底收尸：先红那跑（脚本还没有上限）假 npm 会活到 3600s，不收会留孤儿。

    ⚠️ 如实声明（Codex r2 LOW-1）：这里只认裸 PID —— 原进程退出后 PID 被同 UID 进程复用，
    信号就会落到无关进程上。窗口极窄但不为零。这里只做两件收窄：① 先看还在不在，不在就
    不发信号；② 直接 KILL 一次而不是 TERM→等→KILL（少一个等待窗口）。
    """
    for f in sorted(pids.glob("*.pid")):
        try:
            pid = int(f.read_text().strip())
        except (OSError, ValueError):
            continue
        try:
            os.kill(pid, 0)  # 已经没了就别再发信号（PID 复用的主要来源）
        except (ProcessLookupError, PermissionError):
            continue
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


def test_preflight_npm_build_is_walltime_capped(tmp_path: Path):
    """⛔ R-15：步 1 的 `npm run build` 必须有墙钟上限，到点以**超时专属文案** FAIL 71。

    先红（脚本无上限）：假 npm 永久挂起 ⇒ `_run` 的 timeout 触发 TimeoutExpired。
    后绿（脚本有上限）：到点 TERM→KILL 整个进程组 ⇒ 步 1 FAIL 71 + 超时文案，秒级返回。
    """
    h, pids = _npm_cap_harness(tmp_path, "hang")
    cap = 5
    t0 = time.monotonic()
    try:
        r = _npm_cap_run(tmp_path, h, pids, "8251", cap)
    except subprocess.TimeoutExpired:
        _reap(pids)  # 先红那跑：假 npm 还在睡 3600s
        raise
    elapsed = time.monotonic() - t0
    # ⛔ 顺序：先测「还活着吗」**再**收尸 —— 反过来是自己把它杀了，下面那条进程组
    #    断言会恒真（典型的自我实现的假绿）。
    assert _npm_was_invoked(pids), f"假 npm 根本没被调到 ⇒ 没走到 build 分支，本条什么都没测: {r.stdout!r}"
    gone = {name: _pid_gone(int((pids / name).read_text().strip())) for name in ("npm.pid", "grandchild.pid")}
    _reap(pids)

    assert r.returncode == 71, f"步 1 应 FAIL(71): rc={r.returncode}\n{r.stdout}{r.stderr}"
    assert "npm run build 超时" in r.stdout, f"未命中超时专属文案（分不出超时与任意失败）: {r.stdout!r}"
    assert elapsed < 30, f"墙钟上限没把它打断: 整跑耗时 {elapsed:.1f}s（上限 {cap}s）"
    assert all(gone.values()), f"上限只杀了壳、没杀到同组后代（它成了孤儿）: {gone}"


def test_preflight_npm_build_cap_does_not_kill_a_fast_build(tmp_path: Path):
    """正向对照：秒级产出 main.js 的 build 必须照常通过 —— 证明上限不是「永远杀」。

    顺带钉住**离线开关真的到了 npm 手里**：假 npm 把收到的 `npm_config_offline` 落盘，
    这里断言它是 `true`。没有这一笔，删掉脚本 env 段那行也不会有任何用例变红
    （Codex r1 LOW-1 后半）。
    """
    h, pids = _npm_cap_harness(tmp_path, "fast")
    r = _npm_cap_run(tmp_path, h, pids, "8252")
    assert _npm_was_invoked(pids), f"假 npm 根本没被调到 ⇒ 没走到 build 分支: {r.stdout!r}"
    assert (pids / "npm-env.txt").read_text().strip() == "offline=true", (
        f"npm_config_offline 没传到 npm: {(pids / 'npm-env.txt').read_text()!r}"
    )
    step1 = next((ln for ln in r.stdout.splitlines() if ln.startswith("[1/6]")), "")
    assert "preflight: OK" in step1, f"秒级 build 被墙钟上限误杀: {r.stdout!r}"
    assert "main.js 已 build 并就位" in step1, step1
    assert "超时" not in r.stdout, f"没超时却报了超时: {r.stdout!r}"
    # 假 harness 的 install-vault.sh 是恒 rc=1 的桩 ⇒ 整跑停在步 2，与步 1 的结论无关
    assert r.returncode == 72, f"应停在步 2（桩 installer）: rc={r.returncode}\n{r.stdout}"


@pytest.mark.parametrize(("mode", "port"), [("fail", "8253"), ("rc124", "8254")])
def test_preflight_npm_build_failure_is_not_reported_as_timeout(tmp_path: Path, mode: str, port: str):
    """对照：build 自己失败（秒级）必须报**失败**而不是超时。

    没有这一条，上面那条的「命中超时文案」可能只是因为脚本把任何 build 失败都叫超时。
    ⛔ `rc124` 那一支是 Codex r1 MEDIUM-2 的回归门：超时信号若用退出码 124 承载，
    则「npm 自己 exit 124」与「上限到点」无法区分 —— 现在超时走带外标记，两者分得开。
    """
    h, pids = _npm_cap_harness(tmp_path, mode)
    r = _npm_cap_run(tmp_path, h, pids, port)
    assert _npm_was_invoked(pids), f"假 npm 根本没被调到 ⇒ 没走到 build 分支: {r.stdout!r}"
    assert r.returncode == 71, f"步 1 应 FAIL(71): rc={r.returncode}\n{r.stdout}"
    assert "npm run build 失败" in r.stdout, f"未命中失败文案: {r.stdout!r}"
    assert "超时" not in r.stdout, f"build 失败被误报成超时 —— 文案分不出两种失败: {r.stdout!r}"


@pytest.mark.parametrize(
    ("cap", "port"),
    [("0", "8255"), ("000", "8256"), ("4294967296", "8257"), ("abc", "8258")],
)
def test_preflight_rejects_cap_values_that_would_silently_disable_it(tmp_path: Path, cap: str, port: str):
    """⛔ Codex r1 HIGH-1：能通过校验却让保护静默消失的取值必须被**拒**，不能放行。

    Perl 的 `alarm 0` 是「取消闹钟」，超过 uint32 的值同样退化为 0（`4294967297` 则截断成
    1 秒）。这些值若只按「非负整数」放行，脚本就悄悄退回「没有上限」——正是本卡要修的状态。
    判据钉「步 1 FAIL 71 + 消息点名该变量」，并且**假 npm 不应被调到**（拒在 build 之前）。
    """
    h, pids = _npm_cap_harness(tmp_path, "hang")
    try:
        r = _npm_cap_run(tmp_path, h, pids, port, cap)
    except subprocess.TimeoutExpired:
        _reap(pids)
        raise AssertionError(f"CLS_NPM_BUILD_TIMEOUT={cap!r} 被放行 ⇒ 假 npm 挂住了整跑（上限静默失效）")
    _reap(pids)
    assert r.returncode == 71, f"步 1 应 FAIL(71): rc={r.returncode}\n{r.stdout}"
    assert "CLS_NPM_BUILD_TIMEOUT" in r.stdout, f"消息未点名该变量: {r.stdout!r}"
    assert not _npm_was_invoked(pids), "取值非法时不该已经启动 build（应拒在调 npm 之前）"


def test_preflight_accepts_leading_zero_cap(tmp_path: Path):
    """控制组：`005` 是合法的 5 秒 —— 上一条不能靠「凡是含 0 就拒」蒙混过关。"""
    h, pids = _npm_cap_harness(tmp_path, "fast")
    r = _npm_cap_run(tmp_path, h, pids, "8259", "005")
    assert _npm_was_invoked(pids), f"005 被误拒，build 没跑: {r.stdout!r}"
    step1 = next((ln for ln in r.stdout.splitlines() if ln.startswith("[1/6]")), "")
    assert "preflight: OK" in step1, f"合法取值 005 被误拒: {r.stdout!r}"


@pytest.mark.parametrize("loc", ["ar_EG.UTF-8", "C"])
def test_preflight_rejects_non_ascii_digits_in_any_locale(tmp_path: Path, loc: str):
    """⛔ Codex r2 HIGH-1：`[0-9]` 的**区间**由 locale 排序决定。

    `LC_ALL=ar_EG.UTF-8` 下阿拉伯数字 `٠٥` 能过区间写法的数字门，随后 `[ -lt ]` 报
    "integer expression expected"（rc=2）被 `if` 判假 ⇒ **放行**，最终 `alarm '٠٥'` = alarm 0
    —— 上限被静默关掉。改成逐字符枚举 `[!0123456789]` 后与 locale 无关。
    两个 locale 都跑：证明拒绝不是「碰巧这台机器的 locale 不认」。
    """
    h, pids = _npm_cap_harness(tmp_path, "hang")
    try:
        r = _npm_cap_run(tmp_path, h, pids, "8260" if loc == "C" else "8264", "٠٥", {"LC_ALL": loc})
    except subprocess.TimeoutExpired:
        _reap(pids)
        raise AssertionError(f"LC_ALL={loc} 下 '٠٥' 被放行 ⇒ 假 npm 挂住了整跑（上限静默失效）")
    _reap(pids)
    assert r.returncode == 71, f"步 1 应 FAIL(71): rc={r.returncode}\n{r.stdout}"
    assert "CLS_NPM_BUILD_TIMEOUT" in r.stdout, f"消息未点名该变量: {r.stdout!r}"
    assert not _npm_was_invoked(pids), "取值非法时不该已经启动 build"


# ═══ CARD-G2-8（BATCH-2026-09-11-第十四批）部署激活事务化 ════════════════════
# 被测面: step5_activate 闸门**之后**那段（真起实例 / 健康断言 / 失败回滚的分阶段
#         记账）+ 三段新增（index journal 隔离 / Lance 首索引计时 / Graphiti
#         readiness skipped-with-reason）+ --also-push 实现 + canvas-vault 名口径。
#
# 语义（决策页 §一 作废了「切换 + 恢复旧 ACTIVE_VAULT」那套）：
#   部署单元 =（vault, 它绑定的后端实例）。激活 = 起/重建**本 vault 自己的**
#   compose 项目 cls-<vault>；失败回滚 = 只拆 cls-<vault>，别的 vault 一动不动。
#
# 桩拓扑（全部落在 tmp_path，绝不碰真 docker daemon / 7691 / 现网）:
#   _tx_harness()  自洽假 harness —— 够真 DEPLOY_SH 走完六步
#   fake_bin/docker  只认 `compose … -p <项目> … <config|up|down>`；
#                    **维护一份「在跑项目」清单** ⇒ 「down 有没有误伤兄弟实例」
#                    是可观测的，不是靠读代码相信。
#   fake_bin/curl    按 URL 的端口与路径分流；兄弟实例端口是否 200 **取决于**
#                    那份清单里还有没有 cls-sibling ⇒ 「只拆本实例」有对照对象。
#
# ⚠️ 本节不证明真态：真 docker daemon / 真容器 / 真 7691 的行为未跑（见验收单
#    「本卡未证明什么」）。桩证明的是脚本的**分支与记账**，不是 docker 的行为。

_TX_SKILLS = 9
#: Lance 首索引轮询上限（秒）—— 桩态取小值，免得门跑成分钟级。
_TX_LANCE_CAP = "2"

_TX_INSTALLER = """#!/usr/bin/env bash
# 假 installer：只造出步 3 Phase A 要求的那几件（带 :8011 占位），rc 0。
set -euo pipefail
name="$1"; shift
root=""
while [ $# -gt 0 ]; do
    case "$1" in
        --vaults-root) root="$2"; shift 2 ;;
        *) shift ;;
    esac
done
v="$root/$name"
mkdir -p "$v/.claude/skills" "$v/.claude/hooks" "$v/.obsidian/plugins/canvas-learning-system"
printf '# stub vault\\n' > "$v/CLAUDE.md"
printf '{"backend":"http://127.0.0.1:8011"}\\n' > "$v/.mcp.json"
printf '{"hook":"curl http://127.0.0.1:8011/x"}\\n' > "$v/.claude/settings.json"
printf 'BACKEND_URL = "http://127.0.0.1:8011"\\n' > "$v/.claude/hooks/session-end-archive.py"
printf '{"backendUrl":"http://127.0.0.1:8011","internalApiKey":""}\\n' \\
    > "$v/.obsidian/plugins/canvas-learning-system/data.json"
"""

_TX_DOCKER = """#!/usr/bin/env bash
# 桩 docker。状态 = $CLS_FAKE_STATE 每行一个「在跑的 compose 项目」。
printf '%s\\n' "$*" >> "$CLS_FAKE_DOCKER_LOG"
proj=""; sub=""
while [ $# -gt 0 ]; do
    case "$1" in
        -p) proj="$2"; shift 2 ;;
        config | up | down) [ -z "$sub" ] && sub="$1"; shift ;;
        *) shift ;;
    esac
done
case "$sub" in
    config)
        printf 'services:\\n'
        printf '  backend:\\n'
        printf '    container_name: %s-backend\\n' "$proj"
        printf '    ports:\\n'
        printf '      - mode: ingress\\n'
        printf '        host_ip: 127.0.0.1\\n'
        printf '        target: 8001\\n'
        printf '        published: "%s"\\n' "$CLS_FAKE_PORT"
        printf '        protocol: tcp\\n'
        exit "${CLS_FAKE_CONFIG_RC:-0}"
        ;;
    up)
        rc="${CLS_FAKE_UP_RC:-0}"
        if [ "$rc" = 0 ]; then
            grep -qxF "$proj" "$CLS_FAKE_STATE" 2> /dev/null \\
                || printf '%s\\n' "$proj" >> "$CLS_FAKE_STATE"
        fi
        exit "$rc"
        ;;
    down)
        rc="${CLS_FAKE_DOWN_RC:-0}"
        if [ "$rc" = 0 ]; then
            if [ -n "$proj" ]; then
                grep -vxF "$proj" "$CLS_FAKE_STATE" > "$CLS_FAKE_STATE.new" 2> /dev/null || true
            else
                : > "$CLS_FAKE_STATE.new"
            fi
            mv "$CLS_FAKE_STATE.new" "$CLS_FAKE_STATE"
        fi
        exit "$rc"
        ;;
esac
exit 0
"""

_TX_CURL = """#!/usr/bin/env bash
# 桩 curl：按 URL 的端口与路径分流。兄弟实例端口是否 200 **取决于**清单里
# 还有没有 cls-sibling —— 这让「只拆本实例」有一个可观测的对照对象。
url=""
for a in "$@"; do
    case "$a" in http*) url="$a" ;; esac
done
printf '%s\\n' "$url" >> "$CLS_FAKE_CURL_LOG"
hostport="${url#http://}"; hostport="${hostport%%/*}"
port="${hostport##*:}"
if [ -n "${CLS_FAKE_SIBLING_PORT:-}" ] && [ "$port" = "$CLS_FAKE_SIBLING_PORT" ]; then
    grep -qxF "cls-sibling" "$CLS_FAKE_STATE" 2> /dev/null || exit 7
    printf '{"vault":"sibling","status":"ok"}\\n'
    exit 0
fi
mode=ok
body='{}'
case "$url" in
    */api/v1/vault/current)
        mode="${CLS_FAKE_CURRENT:-ok}"
        body="{\\"vault\\":\\"${CLS_FAKE_VAULT_NAME:-unknown}\\"}"
        ;;
    */api/v1/health/knowledge-graph)
        mode="${CLS_FAKE_KG:-ok}"
        body='{"status":"ok"}'
        ;;
    */api/v1/health/lancedb)
        mode="${CLS_FAKE_LANCE:-ok}"
        body='{"status":"ok","table_count":3}'
        ;;
esac
case "$mode" in
    ok) printf '%s\\n' "$body"; exit 0 ;;
    fail) exit 28 ;;
    garbage) printf 'not-json\\n'; exit 0 ;;
    notready) printf '{"status":"error"}\\n'; exit 0 ;;
    wrong) printf '{"vault":"someone_else"}\\n'; exit 0 ;;
esac
exit 0
"""

_TX_HARNESS_ENV = """# 假 harness 的 .env（--also-push 的目标面）
NEO4J_HTTP_PORT=7691
ACTIVE_VAULT=canvas-vault
VAULTS_ROOT=/tmp/nowhere
"""

_TX_SOURCE_FILES = {
    "CLAUDE.md": "# stub source\n",
    ".mcp.json": '{"backend":"http://127.0.0.1:8011"}\n',
    ".claude/settings.json": '{"hook":"curl http://127.0.0.1:8011/x"}\n',
    ".claude/hooks/session-end-archive.py": 'BACKEND_URL = "http://127.0.0.1:8011"\n',
}


def _tx_write(p: Path, text: str, *, mode: int | None = None) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    if mode is not None:
        p.chmod(mode)


def _tx_harness(tmp_path: Path, *, with_env: bool = True, env_body: str | None = None) -> Path:
    """自洽假 harness：够真 DEPLOY_SH 走完六步，且全程只写 tmp_path。

    形制沿用 `_npm_cap_harness`，差别是：① 预置 main.js ⇒ 不触发 npm build；
    ② installer 桩**真造出** vault 六件套 ⇒ 步 3/4 能过，跑得到步 5/6；
    ③ 带 `backend/app/core/vault_state_paths.py` 的**真副本**（不是桩）——
       index journal 隔离段要 import 它，桩一个假的等于自己给自己发绿灯。
    """
    h = tmp_path / "tx-harness"
    _tx_write(h / "scripts" / "verify_vault_install.py", "")  # 空文件 ⇒ python3 rc 0
    _tx_write(h / "scripts" / "vault-install-manifest.json", "{}\n")
    _tx_write(h / "scripts" / "send_bark.py", "def vault_key(name):\n    return name\n")
    _tx_write(h / "docker-compose.yml", "services: {}\n")
    _tx_write(h / "scripts" / "install-vault.sh", _TX_INSTALLER, mode=0o755)
    _tx_write(h / "backend" / "app" / "__init__.py", "")
    _tx_write(h / "backend" / "app" / "config.py", "def sanitize_vault_id(name):\n    return name\n")
    _tx_write(h / "backend" / "app" / "core" / "__init__.py", "")
    shutil.copyfile(
        REPO_ROOT / "backend" / "app" / "core" / "vault_state_paths.py",
        h / "backend" / "app" / "core" / "vault_state_paths.py",
    )
    venv_bin = h / "backend" / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    os.symlink(sys.executable, venv_bin / "python")
    for i in range(_TX_SKILLS):
        _tx_write(h / "canvas-vault" / ".claude" / "skills" / f"probe{i}" / "SKILL.md", "# stub\n")
    _tx_write(h / "canvas-vault" / ".obsidian" / "plugins" / "canvas-learning-system" / "main.js", "//\n")
    for rel, body in _TX_SOURCE_FILES.items():
        _tx_write(h / "canvas-vault" / rel, body)
    if with_env:
        _tx_write(h / ".env", _TX_HARNESS_ENV if env_body is None else env_body)
    return h


def _tx_bins(tmp_path: Path) -> Path:
    """PATH 注入的假二进制目录（命名沿用既有 `fake_bin / "<bin>"` 手法）。"""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir(exist_ok=True)
    _tx_write(fake_bin / "docker", _TX_DOCKER, mode=0o755)
    _tx_write(fake_bin / "curl", _TX_CURL, mode=0o755)
    return fake_bin


def _tx_env(
    tmp_path: Path,
    port: str,
    vault_name: str,
    *,
    sibling_port: str | None = None,
    extra: dict[str, str] | None = None,
) -> dict[str, str]:
    fake_bin = _tx_bins(tmp_path)
    state = tmp_path / "docker-state.txt"
    if not state.exists():
        state.write_text("", encoding="utf-8")
    env = {
        "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}",
        "CLS_LIVE_VAULT": str(_fake_live(tmp_path)),
        "CLS_DEPLOY_ALLOW_DOCKER_UP": "1",
        "CLS_DEPLOY_LANCE_READY_TIMEOUT": _TX_LANCE_CAP,
        "CLS_FAKE_STATE": str(state),
        "CLS_FAKE_DOCKER_LOG": str(tmp_path / "docker-calls.txt"),
        "CLS_FAKE_CURL_LOG": str(tmp_path / "curl-calls.txt"),
        "CLS_FAKE_PORT": port,
        "CLS_FAKE_VAULT_NAME": vault_name,
    }
    if sibling_port:
        env["CLS_FAKE_SIBLING_PORT"] = sibling_port
    if extra:
        env.update(extra)
    return env


def _tx_run(
    tmp_path: Path,
    h: Path,
    name: str,
    port: str,
    *extra_args: str,
    env: dict[str, str],
    script: Path | None = None,
):
    return _run(
        "--vault",
        str(tmp_path / "vaults" / name),
        "--harness",
        str(h),
        "--port",
        port,
        "--hosts",
        "claude",
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        "--apply",
        "--activate",
        *extra_args,
        env=env,
        timeout=120,
        script=script,
    )


def _tx_journal(tmp_path: Path) -> str:
    """把本次跑落下的 compose-config-<ts>.txt 与 deploy-<ts>.txt 全拼起来。

    分阶段 rc 行必须落在**已在 preflight 申报过的**写对象里 —— 本卡不新开写面
    （新文件 = preflight PENDING_WRITES 没申报过的写入面，而步 1 禁改）。
    """
    ev = tmp_path / "ev"
    if not ev.is_dir():
        return ""
    return "".join(p.read_text(encoding="utf-8", errors="replace") for p in sorted(ev.glob("*.txt")))


def _tx_state(tmp_path: Path) -> list[str]:
    f = tmp_path / "docker-state.txt"
    if not f.is_file():
        return []
    return [ln for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _tx_sibling_is_200(tmp_path: Path, sibling_port: str) -> bool:
    """直接用**同一个桩 curl** 问兄弟实例端口 —— 与脚本看到的是同一份状态。"""
    fake_bin = _tx_bins(tmp_path)
    r = subprocess.run(
        [str(fake_bin / "curl"), "-sS", "--fail", f"http://127.0.0.1:{sibling_port}/api/v1/vault/current"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "CLS_FAKE_STATE": str(tmp_path / "docker-state.txt"),
            "CLS_FAKE_CURL_LOG": str(tmp_path / "curl-calls.txt"),
            "CLS_FAKE_SIBLING_PORT": sibling_port,
        },
        timeout=_SUBPROCESS_TIMEOUT,
    )
    return r.returncode == 0


# ── (b)① 真 activate 分阶段可审计日志 ────────────────────────────────────────
def test_g2_8_activate_tx_logs_each_stage_with_rc(tmp_path: Path):
    """闸门开 + 桩 docker/curl 全成功 ⇒ 步 5 OK，且**每阶段各一行 `rc=`**。

    改前必红在「功能不存在」：闸门后那段只有 up/health/down 三条裸命令，
    没有任何 `stage=… rc=` 记账 ⇒ 下面四条断言全落空。
    """
    h = _tx_harness(tmp_path)
    env = _tx_env(tmp_path, "8231", "probe_tx1")
    r = _tx_run(tmp_path, h, "probe_tx1", "8231", env=env)
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    m = re.search(r"^\[5/6\] activate: (OK|SKIP|FAIL) (.*)$", r.stdout, re.M)
    assert m and m.group(1) == "OK", f"步 5 未 OK: {r.stdout}"
    jr = _tx_journal(tmp_path)
    assert re.search(r"^stage=up-instance project=cls-probe_tx1 rc=0$", jr, re.M), (
        f"缺「起实例」阶段的 rc 行（真 activate 未事务化）: {jr!r}"
    )
    assert re.search(r"^stage=health-assert .*rc=0$", jr, re.M), f"缺「健康断言」阶段的 rc 行: {jr!r}"
    assert "cls-probe_tx1" in _tx_state(tmp_path), "桩 docker 没记到本实例被起起来"
    # 分阶段记账必须同时进 evidence 报告（步 6 的账），不是只在 compose-config 里
    dep = sorted((tmp_path / "ev").glob("deploy-*.txt"))
    assert dep, "步 6 没落 evidence 报告"
    assert "## 激活分阶段" in dep[-1].read_text(encoding="utf-8"), "evidence 报告没有激活分阶段段"


# ── (b)② + (d) 健康断言失败：只拆本实例，兄弟实例不受影响 ────────────────────
def test_g2_8_health_failure_tears_down_only_this_project(tmp_path: Path):
    """桩 curl 对 /vault/current 超时 ⇒ 回滚只拆 cls-<vault>，cls-sibling 仍 200。

    对照对象是真的：桩 curl 对兄弟端口是否 200 **取决于**桩 docker 那份
    「在跑项目」清单里还有没有 cls-sibling。把 down 的 `-p` 去掉（= down 全部）
    这条变异会让本门红 —— 这正是「只拆本实例」与「拆光」的可分点。
    """
    h = _tx_harness(tmp_path)
    state = tmp_path / "docker-state.txt"
    state.write_text("cls-sibling\n", encoding="utf-8")
    env = _tx_env(tmp_path, "8232", "probe_tx2", sibling_port="8299", extra={"CLS_FAKE_CURRENT": "fail"})
    assert _tx_sibling_is_200(tmp_path, "8299"), "控制组不成立：跑之前兄弟实例就不是 200"
    r = _tx_run(tmp_path, h, "probe_tx2", "8232", env=env)
    assert r.returncode == 75, f"健康断言失败应 FAIL 75: rc={r.returncode}\n{r.stdout}{r.stderr}"
    running = _tx_state(tmp_path)
    assert "cls-probe_tx2" not in running, f"回滚没拆掉本实例: {running}"
    assert "cls-sibling" in running, f"失败只拆 cls-<vault>, 兄弟实例不受影响 —— 实测被误伤: {running}"
    assert _tx_sibling_is_200(tmp_path, "8299"), "失败只拆 cls-<vault>, 兄弟实例不受影响 —— 实测兄弟实例端口已不是 200"
    jr = _tx_journal(tmp_path)
    assert re.search(r"^stage=rollback-down project=cls-probe_tx2 rc=0 ", jr, re.M), (
        f"缺「回滚」阶段的 rc 行（回滚未进分阶段账）: {jr!r}"
    )
    assert "已回滚" in r.stdout, r.stdout


def test_g2_8_rollback_failure_does_not_claim_rolled_back(tmp_path: Path):
    """`down` 也失败时不得仍声称「已回滚」（Codex r1 HIGH-3 的既有分叉，钉住不得退化）。"""
    h = _tx_harness(tmp_path)
    env = _tx_env(tmp_path, "8233", "probe_tx3", extra={"CLS_FAKE_CURRENT": "fail", "CLS_FAKE_DOWN_RC": "1"})
    r = _tx_run(tmp_path, h, "probe_tx3", "8233", env=env)
    assert r.returncode == 75, f"rc={r.returncode}: {r.stdout}"
    line = re.search(r"^\[5/6\] activate: FAIL (.*)$", r.stdout, re.M)
    assert line, r.stdout
    assert "已回滚 down" not in line.group(1), f"down 失败却仍声称已回滚: {line.group(1)}"
    assert "需人工处置" in line.group(1), line.group(1)
    jr = _tx_journal(tmp_path)
    assert re.search(r"^stage=rollback-down project=cls-probe_tx3 rc=1 ", jr, re.M), f"回滚失败也必须落 rc 行: {jr!r}"


# ── (b)③ index journal 隔离 ──────────────────────────────────────────────────
def test_g2_8_index_journal_is_namespaced_per_vault(tmp_path: Path):
    """部署期把 G2-5 的 journal 命名空间化**落到证据上**：本 vault 的两条 journal
    与无维度 legacy 路径不同，且与对照 vault key 算出的路径不同。

    ⚠️ 路径由 harness 自己的 `app.core.vault_state_paths` 算（真模块），
    不是脚本自己拼字符串 —— 拼字符串会与生产实现分叉而门照样绿。
    """
    h = _tx_harness(tmp_path)
    env = _tx_env(tmp_path, "8234", "probe_tx4")
    r = _tx_run(tmp_path, h, "probe_tx4", "8234", env=env)
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    jr = _tx_journal(tmp_path)
    m = re.search(r"^stage=index-journal-isolation rc=0 (.*)$", jr, re.M)
    assert m, f"缺 index journal 隔离段: {jr!r}"
    body = m.group(1)
    assert "lancedb_pending_index__probe_tx4.jsonl" in body, f"lancedb journal 未按 vault 命名空间化: {body}"
    assert "vault_index_pending__probe_tx4.jsonl" in body, f"orchestrator journal 未命名空间化: {body}"
    assert "sibling_distinct=yes" in body, f"未证明与对照 vault 的 journal 不同路: {body}"
    assert "legacy_distinct=yes" in body, f"未证明与无维度 legacy 路径不同: {body}"


# ── (b)④ Lance 首索引计时 + 进度 ─────────────────────────────────────────────
def test_g2_8_lance_first_index_is_timed_with_progress(tmp_path: Path):
    h = _tx_harness(tmp_path)
    env = _tx_env(tmp_path, "8235", "probe_tx5")
    r = _tx_run(tmp_path, h, "probe_tx5", "8235", env=env)
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    jr = _tx_journal(tmp_path)
    m = re.search(r"^stage=lance-first-index rc=0 elapsed_s=(\d+) progress=(\S+)$", jr, re.M)
    assert m, f"缺 Lance 首索引计时段（阶段耗时 + 进度字段）: {jr!r}"
    assert m.group(2) != "unknown", f"桩明确报了 table_count=3, 进度字段却是 unknown: {m.group(0)}"
    assert "table_count=3" in m.group(2), m.group(0)


def test_g2_8_lance_not_ready_is_recorded_not_faked(tmp_path: Path):
    """Lance 一直不 ready ⇒ 如实记 rc≠0 + progress=unknown，**不得**记成就绪。"""
    h = _tx_harness(tmp_path)
    env = _tx_env(tmp_path, "8236", "probe_tx6", extra={"CLS_FAKE_LANCE": "notready"})
    r = _tx_run(tmp_path, h, "probe_tx6", "8236", env=env)
    assert r.returncode == 0, f"Lance 未就绪不该让整跑失败: rc={r.returncode}\n{r.stdout}"
    jr = _tx_journal(tmp_path)
    m = re.search(r"^stage=lance-first-index rc=(\d+) elapsed_s=\d+ progress=(\S+)$", jr, re.M)
    assert m, f"缺 Lance 阶段行: {jr!r}"
    assert m.group(1) != "0", f"Lance 报 error 却记 rc=0（假成功）: {m.group(0)}"
    assert m.group(2) == "unknown", f"拿不到进度却编了一个: {m.group(0)}"


# ── (b)⑤ Graphiti readiness：探测失败必须 skipped-with-reason，禁假成功 ──────
@pytest.mark.parametrize(
    ("mode", "reason"),
    [("fail", "unreachable"), ("garbage", "unparsable"), ("notready", "not-ready")],
)
def test_g2_8_graphiti_readiness_never_reports_fake_success(tmp_path: Path, mode: str, reason: str):
    """三种失败面各一条：不可达 / 解析不出 / 明确未就绪 —— 一律 skipped-with-reason。

    ⛔ 断言必须**两侧都核**：只核 `skipped-with-reason=` 出现的话，
    「恒报 success 又顺手打一行 skipped」的变异体会让门仍绿。
    """
    port = {"fail": "8237", "garbage": "8238", "notready": "8239"}[mode]
    name = f"probe_kg_{mode}"
    h = _tx_harness(tmp_path)
    env = _tx_env(tmp_path, port, name, extra={"CLS_FAKE_KG": mode})
    r = _tx_run(tmp_path, h, name, port, env=env)
    assert r.returncode == 0, f"readiness 探不到不该让整跑失败: rc={r.returncode}\n{r.stdout}"
    jr = _tx_journal(tmp_path)
    m = re.search(r"^stage=graphiti-readiness rc=(\d+) result=(\S+)$", jr, re.M)
    assert m, f"缺 Graphiti readiness 段: {jr!r}"
    assert m.group(2).startswith("skipped-with-reason="), (
        f"readiness 探测失败却没落 skipped-with-reason（假成功）: {m.group(0)}"
    )
    assert reason in m.group(2), f"原因未如实写明: {m.group(0)}"
    assert "result=ready" not in jr, f"同一跑里又出现了 result=ready（两面下注）: {jr!r}"


def test_g2_8_graphiti_readiness_reports_ready_when_it_really_is(tmp_path: Path):
    """正控：桩明确报 status=ok 时必须记 ready —— 否则上面那组门是「恒 skipped」的假门。"""
    h = _tx_harness(tmp_path)
    env = _tx_env(tmp_path, "8240", "probe_kg_ok")
    r = _tx_run(tmp_path, h, "probe_kg_ok", "8240", env=env)
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    jr = _tx_journal(tmp_path)
    assert re.search(r"^stage=graphiti-readiness rc=0 result=ready$", jr, re.M), (
        f"真就绪时没记 ready（上面那组 skipped 门因此不承重）: {jr!r}"
    )


# ── (f) --also-push ─────────────────────────────────────────────────────────
def _tx_alsopush_script(tmp_path: Path, h: Path) -> Path:
    """把 FEATURE_TREE 那行指向假 harness 的**脚本副本**。

    守卫本身（限 harness == FEATURE_TREE，否则 die64）一个字不改 —— 只把它的
    参照点换成 tmp，才能在不碰真 feature 主干树 `.env` 的前提下验实现。
    守卫没被改掉由 `test_g2_8_also_push_guard_still_rejects_foreign_harness`
    在**真脚本**上单独钉。FORBID_PY 取 `dirname($0)` ⇒ 判据模块要一并拷过去。
    """
    dst_dir = tmp_path / "script-copy"
    dst_dir.mkdir(exist_ok=True)
    src = DEPLOY_SH.read_text(encoding="utf-8")
    old = f'FEATURE_TREE="{REPO_ROOT.parent / "feature-obsidian-hybrid-dev"}"'
    assert src.count('FEATURE_TREE="') == 1, "FEATURE_TREE 赋值不止一处, 副本改写会漏"
    new_src = re.sub(r'^FEATURE_TREE="[^"]*"$', f'FEATURE_TREE="{h}"', src, count=1, flags=re.M)
    assert new_src != src, f"FEATURE_TREE 行没被改写（原形态可能变了）: {old}"
    dst = dst_dir / "deploy-vault.sh"
    dst.write_text(new_src, encoding="utf-8")
    dst.chmod(0o755)
    shutil.copyfile(FORBID_PY, dst_dir / "cls_forbidden_paths.py")
    return dst


def test_g2_8_also_push_appends_and_dedups(tmp_path: Path):
    """`--also-push` 把 vault 名追加进 harness `.env` 的 DAILY_REVIEW_VAULTS，去重。"""
    h = _tx_harness(tmp_path)
    script = _tx_alsopush_script(tmp_path, h)
    before = (h / ".env").read_text(encoding="utf-8")
    env = _tx_env(tmp_path, "8241", "probe_ap1")
    r = _tx_run(tmp_path, h, "probe_ap1", "8241", "--also-push", env=env, script=script)
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    after = (h / ".env").read_text(encoding="utf-8")
    line = [ln for ln in after.splitlines() if ln.startswith("DAILY_REVIEW_VAULTS=")]
    assert line == ["DAILY_REVIEW_VAULTS=probe_ap1"], f"追加结果不对: {line} (改前: {before!r})"
    # ACTIVE_VAULT 逐字节不变（(h)③ 负控钉的就是这条）
    assert [ln for ln in after.splitlines() if ln.startswith("ACTIVE_VAULT=")] == [
        ln for ln in before.splitlines() if ln.startswith("ACTIVE_VAULT=")
    ], "--also-push 动了 ACTIVE_VAULT"
    # 去重：同名再来一次不重复追加（第二跑被 install 防覆盖闸门拦成 72，
    # 所以另起一个已在清单里的名字来验去重）
    (h / ".env").write_text(
        before.replace("ACTIVE_VAULT=canvas-vault", "ACTIVE_VAULT=canvas-vault\nDAILY_REVIEW_VAULTS=probe_ap2,x"),
        encoding="utf-8",
    )
    env2 = _tx_env(tmp_path, "8242", "probe_ap2")
    r2 = _tx_run(tmp_path, h, "probe_ap2", "8242", "--also-push", env=env2, script=script)
    assert r2.returncode == 0, f"rc={r2.returncode}: {r2.stdout}{r2.stderr}"
    line2 = [
        ln for ln in (h / ".env").read_text(encoding="utf-8").splitlines() if ln.startswith("DAILY_REVIEW_VAULTS=")
    ]
    assert line2 == ["DAILY_REVIEW_VAULTS=probe_ap2,x"], f"已在清单里却被重复追加: {line2}"


def test_g2_8_also_push_appends_key_when_absent(tmp_path: Path):
    """harness `.env` 里根本没有 DAILY_REVIEW_VAULTS 这一键时（真 feature 树当前
    就是这个形态）必须补出来，而不是静默什么也没做。"""
    h = _tx_harness(tmp_path, env_body="ACTIVE_VAULT=canvas-vault\nNEO4J_HTTP_PORT=7691\n")
    script = _tx_alsopush_script(tmp_path, h)
    env = _tx_env(tmp_path, "8243", "probe_ap3")
    r = _tx_run(tmp_path, h, "probe_ap3", "8243", "--also-push", env=env, script=script)
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout}{r.stderr}"
    txt = (h / ".env").read_text(encoding="utf-8")
    assert "DAILY_REVIEW_VAULTS=probe_ap3" in txt, f"缺键时没补出来: {txt!r}"
    assert txt.count("ACTIVE_VAULT=canvas-vault") == 1, f"ACTIVE_VAULT 被动了: {txt!r}"


def test_g2_8_also_push_guard_still_rejects_foreign_harness(tmp_path: Path):
    """守卫保留不动：harness 不是 feature 主干树时 `--also-push` 仍 rc 64（真脚本上跑）。

    守卫在参数解析之后、六步之前，所以不需要一棵能跑的 harness。
    """
    r = _run(
        "--vault",
        str(tmp_path / "vaults" / "probe_ap4"),
        "--harness",
        str(tmp_path / "not-the-feature-tree"),
        "--port",
        "8244",
        "--apply",
        "--also-push",
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
    )
    assert r.returncode == 64, f"守卫被改掉了: rc={r.returncode}\n{r.stdout}{r.stderr}"
    assert "--also-push" in (r.stdout + r.stderr)


def test_g2_8_also_push_is_no_longer_documented_as_unimplemented():
    """`--also-push` 从「只解析不实现」转实现态 ⇒ 那句登记文案必须绝迹。"""
    src = DEPLOY_SH.read_text(encoding="utf-8")
    assert "未实现,登记 G2-8" not in src, "step6 参数行仍写着「未实现」"
    assert "只解析不实现" not in src, "头注仍写着「只解析不实现」"
    assert "also_push_daily_review" in src, "没有实现体"


def test_g2_8_also_push_never_writes_active_vault():
    """静态门：also-push 实现段里不得出现对 ACTIVE_VAULT 的写。"""
    src = DEPLOY_SH.read_text(encoding="utf-8")
    start = src.index("also_push_daily_review() {")
    end = src.index("\n}\n", start)
    body = src[start:end]
    assert "ACTIVE_VAULT" not in body, f"--also-push 实现段提到了 ACTIVE_VAULT: {body}"
    assert "DAILY_REVIEW_VAULTS" in body, "实现段没提到目标键"


# ── (g) canvas-vault 名口径：连字符名被 preflight 拒（钉现状，不改步 1） ──────
def test_g2_8_hyphenated_vault_name_is_still_rejected_by_preflight(tmp_path: Path):
    """`canvas-vault` 这种连字符名不是 sanitize_vault_id/vault_key 的共同不动点。

    G4 口径（本卡只钉现状、不改步 1 逻辑）：**现网 live 的 `canvas-vault` 不经
    本脚本重建，新库须用下划线名。** 这条门是那句口径的可执行形态 ——
    哪天有人「顺手放宽」不动点 preflight，它会红。

    ⚠️ 用**真 harness** 跑（dry-run，零写）：假 harness 的命名函数是恒等桩，
    连字符名会被放行 —— 那样测的是桩，不是生产的两套口径。
    """
    r = _run(
        "--vault",
        str(tmp_path / "vaults" / "canvas-vault"),
        "--harness",
        str(REPO_ROOT),
        "--port",
        "8245",
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
    )
    assert r.returncode == 71, f"连字符名应被步 1 拒成 71: rc={r.returncode}\n{r.stdout}{r.stderr}"
    assert "共同不动点" in r.stdout, r.stdout


def test_g2_8_underscore_vault_name_passes_the_same_preflight(tmp_path: Path):
    """反向锚：同一份 preflight 对下划线名放行 —— 上面那条不是「恒 71」的假门。"""
    r = _run(
        "--vault",
        str(tmp_path / "vaults" / "canvas_vault"),
        "--harness",
        str(REPO_ROOT),
        "--port",
        "8246",
        "--env-dir",
        str(tmp_path / "env"),
        "--evidence-dir",
        str(tmp_path / "ev"),
        env={"CLS_LIVE_VAULT": str(_fake_live(tmp_path))},
    )
    assert r.returncode == 0, f"下划线名被同一道 preflight 拒了: rc={r.returncode}\n{r.stdout}{r.stderr}"


# ── 写面不扩张：分阶段记账不得新开 preflight 没申报过的写对象 ────────────────
def test_g2_8_activate_tx_opens_no_new_write_surface():
    """步 5/6 的新增记账只许写**已在 PENDING_WRITES 里申报过的**对象。

    步 1 禁改 ⇒ 新开一个文件就等于绕过 preflight 的禁写面判据。
    """
    src = DEPLOY_SH.read_text(encoding="utf-8")
    block = src[src.index("local -a PENDING_WRITES=(") : src.index("local -a DIR_WRITES=")]
    declared = set(re.findall(r'"([a-z0-9-]+):\$', block))
    assert declared == {
        "env-file",
        "env-file-tmp",
        "key-file",
        "key-file-tmp",
        "plugin-data",
        "harness-mainjs",
        "harness-build-out",
        "ev-install-log",
        "ev-verify-report",
        "ev-compose-config",
        "ev-deploy-report",
        "ev-deploy-report-tmp",
        "ev-npm-cache",
        "ev-npm-logs",
    }, f"待写清单变了（步 1 禁改 / 新写面必须先进这份清单）: {sorted(declared)}"
    # 步 5 新增的记账落点必须是 $cfg（= ev-compose-config），不是新文件
    act = src[src.index("step5_activate() {") : src.index("also_push_daily_review() {")]
    news = set(re.findall(r'>{1,2} "\$([A-Za-z_][A-Za-z0-9_]*)"', act))
    assert news <= {"cfg"}, f"步 5 出现了 $cfg 之外的写对象: {sorted(news)}"
    # act_stage 自己那一处写在函数外（写 $ACT_JOURNAL）⇒ 上面那段扫不到它。
    # 把「ACT_JOURNAL 只能被赋成 $cfg」单独钉住，否则改一行就能把账落到新文件里。
    assigns = re.findall(r'^ACT_JOURNAL="([^"]*)"$', src, re.M)
    assert assigns == [""], f"ACT_JOURNAL 的顶层初始化变了: {assigns}"
    inner = re.findall(r'^\s+ACT_JOURNAL="([^"]*)"$', src, re.M)
    assert inner == ["$cfg"], f"ACT_JOURNAL 被赋成了 $cfg 之外的东西: {inner}"
    stage_fn = src[src.index("act_stage() {") : src.index("\n}\n", src.index("act_stage() {"))]
    stage_writes = set(re.findall(r'>{1,2} "\$([A-Za-z_][A-Za-z0-9_]*)"', stage_fn))
    assert stage_writes == {"ACT_JOURNAL"}, f"act_stage 写了别的对象: {sorted(stage_writes)}"
