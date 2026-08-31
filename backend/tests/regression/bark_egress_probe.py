"""Bark 外发负门探针 (CARD-TEST-bark-autostub)。

文件名不带 test_ 前缀 — 目录发现模式 (python_files=test_*.py) 收不到它,
只由 backend/scripts/bark_autostub_negative_control.py 以显式 nodeid 八跑:

  A  (--noconftest, 守卫失效) test_probe: 证明「去掉 fixture 就会尝试外发」
     — send_bark 真走 urllib 出网路径, 被本探针自装的双拦截器挡住
     (socket.getaddrinfo + socket.create_connection, 记录 host 并抛
     gaierror — 任何情况下都不出网) → 期望 PASS;
  B  (正常 conftest, 守卫布防) test_probe: _bark_egress_guard 的拒绝器在
     DNS 之前抛 AssertionError("Bark egress attempted in tests") → 期望 FAIL;
  C  (布防) test_keyfile_guarded: 守卫层① KEY_FILE 重定向的放行门;
  C' (--noconftest) 同 nodeid: 层①篡改门 — 证明 C 依赖守卫而非恒真;
  D  (布防) test_osascript_guarded: 守卫层③ osascript 打桩的放行门;
  D' (--noconftest) 同 nodeid: 层③篡改门;
  E  (布防) test_reload_selfheal: reload 双保险放行门 (reload 后三层被重打);
  E' (--noconftest) 同 nodeid: reload 篡改门。

C/D/E 全部结构性断言 (不触发网络也不弹通知), 布防/卸甲两形态下都零副作用。

探针不依赖根 conftest 的 --live/--prompt (A/C'/D'/E' 模式下 pytest_addoption
失效), 也不 import test_daily_review_run 取共享 helper — 各 conftest 形态
下跨模块 import 行为不同, 自包含免歧义。
"""

import socket
import sys
from datetime import time as dtime
from pathlib import Path

WT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WT / "scripts"))

import daily_review_run as runner  # noqa: E402

NOW_ARG = "2026-07-30T10:00:00+08:00"


def _make_vault(tmp_path: Path) -> Path:
    """test_daily_review_run._vault 同款最小 vault: 一张即刻到期节点卡,
    保证 payload 带 notification (否则 push:skip-empty, send 根本不被调,
    探针在 A/B 两种形态下都空转)。live vault 只读 (只 copy decay_beta.py)。"""
    vault = tmp_path / "vault"
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    decay = WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py"
    (scripts / "decay_beta.py").write_bytes(decay.read_bytes())
    (vault / "节点" / "甲.md").write_text(
        '---\ntype: concept\nsource_board: "[[原白板/普通板]]"\n---\n真实内容。\n',
        encoding="utf-8",
    )
    return vault


def test_probe(tmp_path, monkeypatch, capsys):
    # 本探针自身的最后防线: 无论守卫在不在, 双墙 (DNS + 建连) 恒断网。
    # 两墙都记录 host — 任一被触发都满足「观察到解析尝试」的断言; 即便
    # 未来 urllib 绕过 getaddrinfo 直连, create_connection 墙仍拦住
    resolved_hosts = []

    def _intercept_getaddrinfo(host, *args, **kwargs):
        resolved_hosts.append(host)
        raise socket.gaierror(-2, "blocked by bark_egress_probe")

    def _intercept_create_connection(address, *args, **kwargs):
        if isinstance(address, tuple) and address:
            resolved_hosts.append(address[0])
        raise socket.gaierror(-2, "blocked by bark_egress_probe (create_connection)")

    monkeypatch.setattr(socket, "getaddrinfo", _intercept_getaddrinfo)
    monkeypatch.setattr(socket, "create_connection", _intercept_create_connection)
    # 代理会把首跳解析目标换成代理主机, 断言锚点 api.day.app 就失配 —
    # 且 urllib 在 env 之外还读 macOS 系统代理 (getproxies_macosx_sysconf;
    # 本机实测系统代理在, A 模式首跳解析记到 127.0.0.1)。env + getproxies
    # 双禁 = 尽力消除代理首跳 (已建 opener 的缓存形态拦不住, 如实边界 —
    # 上面双墙恒兜底); 拦截器保证两种形态下都不出网
    for var in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(runner.send_bark.urllib.request, "getproxies", lambda: {})

    key_file = tmp_path / "bark.key"
    key_file.write_text("probekey-12345678\n", encoding="utf-8")
    monkeypatch.setattr(runner.send_bark, "KEY_FILE", key_file)
    # 单次尝试足以取证 — 免 RETRIES=2 的 2s+4s 重试空等
    monkeypatch.setattr(runner.send_bark, "RETRIES", 0)
    # A 模式 (无守卫) 下 push:failed 会走 osascript 兜底 subprocess 真弹
    # macOS 通知 — 探针自行打桩 (B 模式守卫已桩, 此处覆盖等价)
    monkeypatch.setattr(runner, "osascript_fallback", lambda noti: True)

    vault = _make_vault(tmp_path)
    monkeypatch.setattr(runner, "VAULT", vault)
    monkeypatch.setattr(runner, "BACKUPS", tmp_path / "backups")
    # 窗口门放行 (机器时区无关) — 既有 _push_harness 同款; 探针证的是
    # 「send 被调后会不会出网」, 不是窗口语义
    monkeypatch.setattr(runner, "PUSH_WINDOW", (dtime(0, 0), dtime(23, 59, 59)))
    monkeypatch.setattr(sys, "argv", ["daily_review_run.py", "--now", NOW_ARG, "--vault", str(vault)])

    assert runner.main() == 0
    out = capsys.readouterr().out
    assert any("api.day.app" in str(h) for h in resolved_hosts), (
        f"未观察到对 api.day.app 的解析尝试 (resolved={resolved_hosts!r})"
    )
    assert "push:failed" in out


def test_keyfile_guarded():
    """自证门 C (armed): 守卫层① KEY_FILE 重定向的放行门 — 布防下
    send_bark.KEY_FILE 必须已被移出真实 key 位置, 且其内容 server 段是
    loopback discard (round-3 M: 八跑此前不锁内容, 守卫回退成外网 server
    时 C 仍绿 — 内容断言把「loopback 纵深」本身钉进门里)。只读守卫自己的
    tmp 假 key, 不触真实 key, 布防/卸甲两形态都零副作用。"""
    import send_bark

    real_key = Path.home() / ".config" / "canvas-review" / "bark.key"
    kf = Path(send_bark.KEY_FILE)
    assert kf != real_key, "守卫未布防: send_bark.KEY_FILE 仍指向真实 key 位置"
    content = kf.read_text(encoding="utf-8").strip()
    assert content.startswith("http://127.0.0.1:9/"), "守卫假 key 的 server 段不是 loopback discard 端口 — 纵深防御回退"


def test_osascript_guarded():
    """自证门 D (armed): 守卫层③ osascript_fallback 打桩的放行门 — 布防下
    它必须是守卫的记录桩而非 runner 原始实现。按 __qualname__ 结构性断言
    (任何测试侧替身都会改 qualname), 不调用函数, 布防/卸甲两形态都零副作用
    (调真函数 = 卸甲形态下真弹通知, 恰是要避免的事)。"""
    import daily_review_run

    fn = daily_review_run.osascript_fallback
    assert getattr(fn, "__qualname__", "") != "osascript_fallback", (
        "守卫未布防: osascript_fallback 仍是 runner 原始实现"
    )


def test_reload_selfheal():
    """自证门 E (armed): reload 双保险 — 对**两个**受保护生产模块各自
    reload 重跑模块顶层 (KEY_FILE/_urlopen / osascript_fallback 被生产值
    重写) 后, 守卫须对两侧都自动重打桩 (round-2 MEDIUM: 只锁 send_bark
    时, 守卫漏 rearm daily_review_run 本门仍绿)。仅 reload 不调 send,
    布防/卸甲两形态都零出网。"""
    import importlib

    import daily_review_run
    import send_bark

    real_key = Path.home() / ".config" / "canvas-review" / "bark.key"

    importlib.reload(send_bark)
    assert Path(send_bark.KEY_FILE) != real_key, "守卫未布防或 reload 自愈失效: reload 后 KEY_FILE 回到真实 key 位置"
    assert getattr(send_bark._urlopen, "__qualname__", "") != "urlopen", (
        "守卫未布防或 reload 自愈失效: reload 后 _urlopen 回到真实 urlopen"
    )

    importlib.reload(daily_review_run)
    assert Path(daily_review_run.send_bark.KEY_FILE) != real_key, (
        "守卫未布防或 reload 自愈失效: reload runner 后 send_bark.KEY_FILE 回到真实 key 位置"
    )
    assert getattr(daily_review_run.osascript_fallback, "__qualname__", "") != "osascript_fallback", (
        "守卫未布防或 reload 自愈失效: reload 后 osascript_fallback 回到 runner 原始实现"
    )
