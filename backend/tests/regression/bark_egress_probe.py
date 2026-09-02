"""Bark 外发负门探针 (CARD-TEST-bark-autostub / R1)。

文件名不带 test_ 前缀 — 目录发现模式 (python_files=test_*.py) 收不到它,
只由 backend/scripts/bark_autostub_negative_control.py 以显式 nodeid 逐跑。
每一道「放行门」都配一道同 nodeid 的「篡改门」(--noconftest 卸下守卫):
门存在 ≠ 门在工作, 只有卸甲必红才证明放行门真的依赖守卫。

  A  (--noconftest, 卸甲) test_probe: 证明「去掉 fixture 就会尝试外发」
     — send_bark 真走 urllib 出网路径, 被本探针自装的双拦截器挡住
     (socket.getaddrinfo + socket.create_connection, 记录 host 并抛
     gaierror — 任何情况下都不出网) → 期望 PASS;
  B  (布防) test_probe: _bark_egress_guard 的拒绝器在 DNS 之前抛
     AssertionError("Bark egress attempted in tests") → 期望 FAIL;
  C/C'  test_keyfile_guarded          — 守卫层① KEY_FILE 重定向 + loopback 内容;
  D/D'  test_osascript_guarded        — 守卫层③ osascript 模块属性打桩;
  E/E'  test_reload_selfheal          — reload 双保险 (三模块各自重打);
  F/F'  test_proxy_first_hop_stays_loopback — 守卫层⑤d/⑤e: 敌对「已建
        opener」(模块全局的与别处握持的) 都不能把 loopback 请求转出机
        (行为门, socket 首跳);
  F2/F2' test_proxy_state_neutralized  — 守卫层⑤a/⑤b/⑤c: env 代理、
        getproxies、_scproxy 三处同时哑火 (状态门);
  H/H'  test_osascript_prebound_alias_blocked — 守卫层⑥: collection 期
        from-import 预绑定的 osascript_fallback 别名也在 spawn 之前被拦;
  S/S'  test_stale_reload_stash + test_stale_reload_refused_before_reload
        — teardown 后的 stale reload wrapper 必须在**执行 reload 之前**
        拒绝, 且拒绝后两个生产 sentinel (KEY_FILE / _urlopen) 都不生效。

三层防线 (抛 / 结账 / 总账) 见下方 _REAL_CALLS 段。
C/D/E/F/F2/H/S 全部零真实副作用 (不出网、不弹通知、不读真 key):
F 的建连在 socket 层被拦, H 的 spawn 在 subprocess.Popen 处被拦,
S 只做 reload 不调 send —— 布防/卸甲两形态都成立。

探针不依赖根 conftest 的 --live/--prompt (卸甲模式下 pytest_addoption
失效), 也不 import test_daily_review_run 取共享 helper — 各 conftest 形态
下跨模块 import 行为不同, 自包含免歧义。

设计约束 (为什么有模块级副作用): 守卫是 function 级 autouse fixture,
测试体里的任何 monkeypatch 都晚于它 —— 想证明「守卫能中和**先于它存在**
的敌对代理态」, 敌对态就只能建在模块 import 期 (collection, 早于一切
fixture)。这就是下面 HOSTILE_PROXY 段与 _PREBOUND_OSASCRIPT 的由来。
"""

import importlib
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import time as dtime
from pathlib import Path

#: 预绑定的真 reload —— 取在任何 fixture 之前, 因此不会被守卫的
#: importlib.reload 包装拦截。这正是 round-3/round-2 两轮审查用来绕开
#: reload 双保险的形态; R 门拿它复核「绕开之后仍然不出机」。
_REAL_RELOAD = importlib.reload

WT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WT / "scripts"))

import daily_review_run as runner  # noqa: E402

NOW_ARG = "2026-07-30T10:00:00+08:00"

#: F/F' 门的敌对前置态 — 必须在任何 fixture 之前 (模块 import 期) 建立:
#: ① env 代理; ② 已经 install 好的 opener (代理已烘焙进它自己的
#: ProxyHandler, 事后改 getproxies 管不着 — round-3 H1 的第二条向量)。
#: 守卫布防时必须把两者都中和 (⑤a 清 env + ⑤d 换无代理 opener), F 的首跳
#: 才会落在 127.0.0.1:9; 卸甲形态下这套前置态原样生效 → 首跳落
#: 127.0.0.1:63128 → F' 必红。哨兵端口 63128 不监听, 且 F/F' 都在 socket
#: 层拦截, 两形态都不会真建连、不出机。
#: no_proxy 一并清掉: 留着它会让 proxy_bypass 走 environment 分支放行
#: loopback, F' 就红不了 (判据依赖机器 env = 假门)。
HOSTILE_PROXY_PORT = 63128
HOSTILE_PROXY = f"http://127.0.0.1:{HOSTILE_PROXY_PORT}"
for _v in ("no_proxy", "NO_PROXY", "https_proxy", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
    os.environ.pop(_v, None)
os.environ["http_proxy"] = HOSTILE_PROXY
os.environ["HTTP_PROXY"] = HOSTILE_PROXY
#: 混合大小写: getproxies_environment() 是 key.lower() 之后才看后缀, 所以这个
#: 名字它照样认。守卫若拿固定枚举清单删 env 就会漏掉它 (round-3 审查击穿点)。
os.environ["Http_Proxy"] = HOSTILE_PROXY
#: 同时留一份**对象引用** —— 换掉 urllib.request._opener 这个模块全局救不了
#: 别处已经握着的 opener 对象 (R1 round-1 审查用 held.open() 实测击穿),
#: F 门第三段就拿它复核层⑤e。
_HOSTILE_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({"http": HOSTILE_PROXY}))
urllib.request.install_opener(_HOSTILE_OPENER)

#: R 门专用: 代理指向一个**机外**地址 (RFC 5737 文档段, 不可路由)。R 门要证的
#: 是「预绑定 reload 抹掉 ②④⑤b⑤d⑤e 之后, 别处握持的 opener 仍不出机」——
#: 判据必须能区分「本机」和「机外」, 用 127.0.0.1 的哨兵端口就区分不出方向。
#: 全程在 socket 层拦截, 两形态都不会真建连。
EXTERNAL_PROXY = "http://198.51.100.1:63128"
_HOSTILE_EXTERNAL_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({"http": EXTERNAL_PROXY}))

#: H/H' 门: collection 期 `from daily_review_run import osascript_fallback`
#: 的预绑定形态 (round-3 MEDIUM 的原型)。守卫层③ 换的是模块属性, 换不掉
#: 这个已经绑定的函数对象 —— 只有层⑥ (subprocess.run 过滤器) 能在 spawn
#: 之前拦住它。
_PREBOUND_OSASCRIPT = runner.osascript_fallback

#: S 门的跨测试信箱: 前置测试在布防期内存一份当次的 importlib.reload
#: wrapper, 该测试 teardown 后它即成为 stale。
_STASHED_RELOAD: dict = {}

#: 本进程的真实 key 位置 —— 取自**守卫改 env 之前**的环境, 与
#: send_bark.py:30-33 同判定。写死默认路径是错的: 生产若用 BARK_KEY_FILE
#: 指到自定义位置, C' 卸甲门的「路径不等」断言会先通过, 然后真的去读那个
#: 自定义的真实 key (round-2 审查实证)。只比较路径, 全文件从不读它的内容。
REAL_KEY = Path(os.environ.get("BARK_KEY_FILE") or Path.home() / ".config" / "canvas-review" / "bark.key")

#: ── 总账层 (核心裁判 3「socket 与 osascript 实调用为 0」的直接证据) ──
#: 各测试自装的拦截器是第一层 (抛), 每条测试末尾的 _assert_no_real_egress()
#: 是第二层 (结账); 这里是第三层 (总账): 模块 import 期就把三个真实原语换成
#: 记账并抛的版本 —— 于是本进程内**根本不存在**通往真实建连/解析/spawn 的
#: 路径, 而不是「我们相信没走到」。任何逃过前两层的调用都会被计数, 结账断言
#: 随即变红 (单层拦截器 = 假门, 项目教训 reference_test_guard_three_layer_design)。
#: 用 AssertionError 而不是 OSError/gaierror: send_bark 与 urllib 都吞 OSError 族,
#: 吞掉就成了静默放行。
_REAL_CALLS = {"connect": 0, "resolve": 0, "spawn": 0}


def _ledger_create_connection(address, *a, **kw):
    _REAL_CALLS["connect"] += 1
    raise AssertionError(f"BARK-LEDGER-CONNECT: 真实建连抵达 socket.create_connection ({address!r})")


def _ledger_getaddrinfo(host, *a, **kw):
    _REAL_CALLS["resolve"] += 1
    raise AssertionError(f"BARK-LEDGER-RESOLVE: 真实解析抵达 socket.getaddrinfo ({host!r})")


def _ledger_popen(*a, **kw):
    _REAL_CALLS["spawn"] += 1
    raise AssertionError(f"BARK-LEDGER-SPAWN: 真实 spawn 抵达 subprocess.Popen ({a[:1]!r})")


socket.create_connection = _ledger_create_connection
socket.getaddrinfo = _ledger_getaddrinfo
subprocess.Popen = _ledger_popen


def _assert_no_real_egress():
    """结账: 本条测试期间没有任何真实建连 / 解析 / spawn 抵达过总账层。"""
    assert _REAL_CALLS == {"connect": 0, "resolve": 0, "spawn": 0}, (
        f"BARK-LEDGER-NONZERO: 出现真实出网或 spawn 调用 {_REAL_CALLS!r}"
    )


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
    # 本机实测系统代理在)。env + getproxies + 模块级敌对 opener 三处同禁 =
    # 强制直连形态; 拦截器保证两种形态下都不出网。
    # _opener 必须一并复位: 模块 import 期为 F 门装的敌对 opener 会把首跳
    # 抢走 (A 形态下会记到 127.0.0.1:63128 而不是 api.day.app)。
    for var in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(runner.send_bark.urllib.request, "getproxies", lambda: {})
    monkeypatch.setattr(urllib.request, "_opener", None)

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
        f"BARK-GATE-A-RESOLVE: 未观察到对 api.day.app 的解析尝试 (resolved={resolved_hosts!r})"
    )
    assert "push:failed" in out
    _assert_no_real_egress()


def test_keyfile_guarded():
    """C 门 (armed): 守卫层① KEY_FILE 重定向的放行门 — 布防下
    send_bark.KEY_FILE 必须已被移出真实 key 位置, 且其内容 server 段是
    loopback discard (round-3 M: 八跑此前不锁内容, 守卫回退成外网 server
    时 C 仍绿 — 内容断言把「loopback 纵深」本身钉进门里)。只读守卫自己的
    tmp 假 key, 不触真实 key, 布防/卸甲两形态都零副作用。"""
    import send_bark

    kf = Path(send_bark.KEY_FILE)
    assert kf != REAL_KEY, "BARK-GATE-C-KEYFILE: 守卫未布防 — send_bark.KEY_FILE 仍指向真实 key 位置"
    content = kf.read_text(encoding="utf-8").strip()
    server = content.rpartition("/")[0]
    assert server == "http://127.0.0.1:9", (
        f"BARK-GATE-C-LOOPBACK: 守卫假 key 的 server 段不是 loopback discard 端口 (实测 {server!r})"
    )


def test_osascript_guarded():
    """D 门 (armed): 守卫层③ osascript_fallback 模块属性打桩的放行门 —
    布防下它必须是守卫的记录桩而非 runner 原始实现。按 __qualname__ 结构性
    断言 (任何测试侧替身都会改 qualname), 不调用函数, 布防/卸甲两形态都零
    副作用 (调真函数 = 卸甲形态下真弹通知, 恰是要避免的事; 预绑定别名那条
    路径由 H 门单独覆盖, 它有自己的 Popen 墙)。"""
    import daily_review_run

    fn = daily_review_run.osascript_fallback
    assert getattr(fn, "__qualname__", "") != "osascript_fallback", (
        "BARK-GATE-D-OSASCRIPT: 守卫未布防 — osascript_fallback 仍是 runner 原始实现"
    )


def test_reload_selfheal():
    """E 门 (armed): reload 双保险 — 对**两个**受保护生产模块各自
    reload 重跑模块顶层 (KEY_FILE/_urlopen / osascript_fallback 被生产值
    重写) 后, 守卫须对两侧都自动重打桩 (round-2 MEDIUM: 只锁 send_bark
    时, 守卫漏 rearm daily_review_run 本门仍绿)。仅 reload 不调 send,
    布防/卸甲两形态都零出网。"""
    import daily_review_run
    import send_bark

    importlib.reload(send_bark)
    assert Path(send_bark.KEY_FILE) != REAL_KEY, "BARK-GATE-E-RELOAD-KEYFILE: reload 后 KEY_FILE 回到真实 key 位置"
    assert getattr(send_bark._urlopen, "__qualname__", "") != "urlopen", (
        "BARK-GATE-E-RELOAD-URLOPEN: reload 后 _urlopen 回到真实 urlopen"
    )

    importlib.reload(daily_review_run)
    assert Path(daily_review_run.send_bark.KEY_FILE) != REAL_KEY, (
        "BARK-GATE-E-RELOAD-RUNNER-KEYFILE: reload runner 后 send_bark.KEY_FILE 回到真实 key 位置"
    )
    assert getattr(daily_review_run.osascript_fallback, "__qualname__", "") != "osascript_fallback", (
        "BARK-GATE-E-RELOAD-OSASCRIPT: reload 后 osascript_fallback 回到 runner 原始实现"
    )

    # round-3 H1 的逃逸链第一步就是 reload(urllib.request) —— 它会把④⑤ 全部
    # 抹掉。属性式调用现在也在双保险名单内, 重打必须覆盖到这两层。
    importlib.reload(urllib.request)
    assert getattr(urllib.request.urlopen, "__qualname__", "") != "urlopen", (
        "BARK-GATE-E-RELOAD-URLLIB-URLOPEN: reload(urllib.request) 后全局 urlopen 未被重打"
    )

    # round-2 审查抓出的同型第二条: subprocess 也被守卫打了桩 (层⑥), 却不在
    # reload 名单里 —— reload 它就把层⑥ 冲掉, 预绑定的通知别名随即抵达真 spawn。
    importlib.reload(subprocess)
    assert getattr(subprocess.run, "__qualname__", "") != "run", (
        "BARK-GATE-E-RELOAD-SUBPROCESS: reload(subprocess) 后层⑥ 未被重打"
    )
    # reload 重跑 subprocess 顶层, 把探针 import 期装的 Popen 总账也冲掉了
    # (round-3 审查指出; E 门自己不 spawn 所以看不见)。用完立刻补装回去。
    subprocess.Popen = _ledger_popen
    assert urllib.request.getproxies() == {}, (
        "BARK-GATE-E-RELOAD-URLLIB-PROXY: reload(urllib.request) 后代理中和未被重打"
    )


def test_proxy_first_hop_stays_loopback(monkeypatch):
    """F 门 (armed, 行为): 模块 import 期就已存在的敌对「已建 opener」
    (ProxyHandler 指向 127.0.0.1:63128) 不得把 loopback 请求转出机 ——
    首跳必须是 loopback discard 端口本身。

    这是 (b) 的行为门: 判据锚 (host, port) 二元组而不是只锚 host ——
    本机系统代理实测就是 127.0.0.1:1082, 与兜底目标同主机不同端口, 只比
    host 会两形态同值 = 假门。
    建连在 socket.create_connection 层被拦并抛 OSError, 布防/卸甲两形态
    都不会真建连、不出机 (63128 也不监听)。
    三段各自覆盖**不同的 opener 来路**, 但**不是**一段对应一层: 层⑤ 的五件套
    在 darwin 上互相兜底 (⑤c 把 proxy settings 换成「一切主机都绕过代理」之后,
    单独撤 ⑤e 或单独撤 ⑤c, 三段首跳都仍是 127.0.0.1:9 —— R1 round-3/round-4
    两轮实测)。所以承重判定只能按「同一向量的全部防线成组拆」做:
    变异 M2 整层⑤ 全拆 → 第一段红; M4 拆 ⑤a+⑤b+⑤c+⑤e → 第二段红;
    M15 翻转 ⑤c 的 settings 语义 → R 门 (预绑定 reload 之后的握持 opener) 红。
    ⑤b/⑤d/⑤e 各自没有独立证伪门, 已在验收单「未证明什么」#3 如实登记。"""
    hops = []

    def _intercept(address, *a, **kw):
        hops.append(tuple(address[:2]) if isinstance(address, tuple) else (str(address), None))
        raise OSError(61, "blocked by bark_egress_probe (first-hop gate)")

    monkeypatch.setattr(socket, "create_connection", _intercept)
    opener = urllib.request._opener
    assert opener is not None, "BARK-GATE-F-NOOPENER: _opener 为空, 前置态未建立"
    try:
        opener.open("http://127.0.0.1:9/push", timeout=1)
    except urllib.error.URLError:
        pass

    assert hops, "BARK-GATE-F-NOHOP: 未观察到任何建连尝试"
    assert hops[0] == ("127.0.0.1", 9), (
        f"BARK-GATE-F-FIRSTHOP: 代理首跳未被中和 (首跳 {hops[0]!r}, 期望 ('127.0.0.1', 9))"
    )

    # 第二段: 现场新建的 opener —— 这是 `_opener is None` 时 urlopen 走的路
    # (reload(urllib.request) 之后就是这个状态)。build_opener() 会在此刻读
    # getproxies(), 于是这段behaviorally 覆盖的是「系统/环境代理」向量,
    # 与上面「已建 opener」向量互补, 合起来才是完成条件 (b) 的两条。
    fresh_hops = []

    def _intercept_fresh(address, *a, **kw):
        fresh_hops.append(tuple(address[:2]) if isinstance(address, tuple) else (str(address), None))
        raise OSError(61, "blocked by bark_egress_probe (fresh-opener gate)")

    monkeypatch.setattr(socket, "create_connection", _intercept_fresh)
    try:
        urllib.request.build_opener().open("http://127.0.0.1:9/push", timeout=1)
    except urllib.error.URLError:
        pass

    assert fresh_hops, "BARK-GATE-F-NOFRESHHOP: 新建 opener 未观察到任何建连尝试"
    assert fresh_hops[0] == ("127.0.0.1", 9), (
        f"BARK-GATE-F-FRESHHOP: 新建 opener 的首跳被代理接管 (首跳 {fresh_hops[0]!r}, 期望 ('127.0.0.1', 9))"
    )

    # 第三段: 直接握着的 opener 对象 —— 不经 urllib.request._opener 这个模块
    # 全局, 所以 ⑤d 换引用对它无效; 承重的是 ⑤e (proxy_bypass 恒 True)。
    # R1 round-1 审查正是用这条路径击穿了只有 ⑤d 的版本。
    held_hops = []

    def _intercept_held(address, *a, **kw):
        held_hops.append(tuple(address[:2]) if isinstance(address, tuple) else (str(address), None))
        raise OSError(61, "blocked by bark_egress_probe (held-opener gate)")

    monkeypatch.setattr(socket, "create_connection", _intercept_held)
    try:
        _HOSTILE_OPENER.open("http://127.0.0.1:9/push", timeout=1)
    except urllib.error.URLError:
        pass

    assert held_hops, "BARK-GATE-F-NOHELDHOP: 握持 opener 未观察到任何建连尝试"
    assert held_hops[0] == ("127.0.0.1", 9), (
        f"BARK-GATE-F-HELDHOP: 别处握持的 opener 首跳被代理接管 (首跳 {held_hops[0]!r}, 期望 ('127.0.0.1', 9))"
    )
    _assert_no_real_egress()


def test_proxy_state_neutralized():
    """F2 门 (armed, 状态): 守卫层⑤a/⑤b/⑤c 三处代理来源同时哑火。

    F 是行为门但只承重 ⑤d; 这三条各自承重一层, 任一层被摘掉本门必红
    (变异负控按层逐条验)。⑤c 分两处断言是因为 darwin 的
    `from _scproxy import _get_proxies` 把补丁点劈成了两个绑定:
    urllib.request 侧管当下, _scproxy 侧管 reload(urllib.request) 之后。"""
    leftover = sorted(k for k in os.environ if k.lower().endswith("_proxy"))
    assert not leftover, f"BARK-GATE-F2-ENVPROXY: 布防期内仍有代理 env 残留 {leftover}"
    assert urllib.request.getproxies() == {}, (
        f"BARK-GATE-F2-GETPROXIES: getproxies() 非空 ({urllib.request.getproxies()!r})"
    )
    if sys.platform == "darwin":
        import _scproxy

        assert _scproxy._get_proxies() == {}, (
            "BARK-GATE-F2-SCPROXY: _scproxy._get_proxies 未中和 — reload(urllib.request) 后代理会复活"
        )
        assert getattr(urllib.request, "_get_proxies", None) is not None and (urllib.request._get_proxies() == {}), (
            "BARK-GATE-F2-URLLIB-GETPROXIES: urllib.request._get_proxies 未中和"
        )


def test_osascript_prebound_alias_blocked(monkeypatch):
    """H 门 (armed): collection 期 from-import 预绑定的 osascript_fallback
    别名, 也必须在**副作用之前**被拦 (round-3 MEDIUM 升级为 R1 完成条件 d)。

    守卫层③ 换的是模块属性, 换不掉 _PREBOUND_OSASCRIPT 这个已绑定对象;
    它执行时仍按模块全局查 subprocess.run —— 层⑥ 就拦在那里。
    探针自装 Popen 墙作最后防线: 卸甲形态下真 subprocess.run 会走到墙,
    抛 AssertionError (osascript_fallback 只吞 OSError/TimeoutExpired,
    AssertionError 必然穿透) → H' 必红, 且两形态都不会真弹通知。"""

    def _wall(*a, **kw):
        raise AssertionError("BARK-GATE-H-OSASCRIPT-SPAWN: 真 osascript spawn 已抵达 subprocess.Popen")

    monkeypatch.setattr(subprocess, "Popen", _wall)
    assert _PREBOUND_OSASCRIPT({"title": "bark-gate-h", "body": "bark-gate-h"}) is True, (
        "BARK-GATE-H-RETURN: 预绑定别名未被守卫层⑥ 接管"
    )

    # 误吞面: basename 不是 osascript 的命令必须原样透传 (会撞上探针的 Popen 墙)。
    # 原来的 substring 判定会把它静默吞成 rc=0, 于是守卫在悄悄改变无关命令的行为。
    # 不用 pytest.raises: 它失败时给的是 "DID NOT RAISE", 消息里没有本门的
    # sentinel, 判据就锚不住红因 (变异 M16 首跑当场暴露)。
    for decoy in (
        ["/tmp/bark-gate-h-not-osascript-helper"],  # basename 只是「含」osascript
        ["/usr/bin/printf", "osascript"],  # osascript 只是个**数据**参数
    ):
        decoy_hit_wall = False
        try:
            subprocess.run(decoy)
        except AssertionError:
            decoy_hit_wall = True
        assert decoy_hit_wall, (
            f"BARK-GATE-H-DECOY: 无关命令 {decoy!r} 被层⑥ 误吞 — 判定必须只认 argv[0] 或 env 转发的首个非赋值参数"
        )

    # 漏判面: /usr/bin/env osascript ... 这种间接形态也必须被层⑥ 接管
    # (round-2 审查实测原判定只看 argv[0], 这条会抵达真 spawn)。
    try:
        indirect = subprocess.run(["/usr/bin/env", "osascript", "-", "t", "b"], capture_output=True)
    except AssertionError as exc:  # 撞上探针的 Popen 墙 = 层⑥ 漏判了这条形态
        raise AssertionError("BARK-GATE-H-INDIRECT: env osascript 未被守卫层⑥ 接管, 已抵达真 spawn") from exc
    assert indirect.returncode == 0, "BARK-GATE-H-INDIRECT: env osascript 未被守卫层⑥ 接管"
    _assert_no_real_egress()


def test_stale_reload_stash():
    """S 门前置: 在布防期内取到当次 importlib.reload 的 wrapper 存进模块级
    信箱; 本条测试 teardown 之后, 它就是一个 stale wrapper。
    卸甲形态下这里存到的是真 importlib.reload —— 正是 S' 要暴露的东西。"""
    _STASHED_RELOAD["fn"] = importlib.reload
    assert callable(_STASHED_RELOAD["fn"])


def test_stale_reload_refused_before_reload():
    """S 门 (armed): 上一条留下的 stale wrapper 必须在**执行 reload 之前**
    拒绝 —— 拒绝之后两个生产 sentinel 都不得生效 (round-3 H2: 先 reload
    后 raise 时模块已被重载, 抛异常并不回滚)。

    卸甲形态下 stale 就是真 reload: 调用直接重新执行模块, 第一条断言即红。
    整条测试不调 send、不读 key 内容, 两形态零外发。

    ⚠️ 判别器为什么是**模块对象身份**而不是 KEY_FILE/_urlopen 的值:
    本条测试自己也在布防中, 所以「先 reload 后 raise」的错误实现里, reload
    重跑模块顶层拿到的 KEY_FILE 仍是当前守卫的 tmp key、_urlopen 仍是当前
    守卫的拒绝器 —— 两种世界给出**同一个观测**, 值断言在此语境下判不出来
    (R1 变异 M7 首跑当场证伪了值断言版本)。reload 必然重建模块里所有 def
    出来的函数对象, 这一点任何重打桩都掩盖不掉, 所以身份比对才是承重判据;
    KEY_FILE/_urlopen 两条保留为卡文字面的 sentinel 复核, 它们是身份判据的
    推论 (模块没被重新执行 → 生产值不可能被写回)。"""
    import send_bark

    stale = _STASHED_RELOAD.get("fn")
    assert stale is not None, "BARK-GATE-S-NOSTASH: S 门前置测试未先跑"
    send_before = send_bark.send
    load_key_before = send_bark.load_key
    key_before = send_bark.KEY_FILE
    urlopen_before = send_bark._urlopen
    try:
        stale(send_bark)
        refused = False
    except RuntimeError:
        refused = True

    assert refused, "BARK-GATE-S-STALE-RELOAD: stale wrapper 未拒绝对受保护模块的 reload"
    assert send_bark.send is send_before and send_bark.load_key is load_key_before, (
        "BARK-GATE-S-MODULE-REEXECUTED: 拒绝之前模块已被重新执行 — reload 已发生, 抛异常并不回滚"
    )
    assert send_bark.KEY_FILE == key_before and Path(send_bark.KEY_FILE) != REAL_KEY, (
        "BARK-GATE-S-KEYFILE-SENTINEL: KEY_FILE 生产 sentinel 已生效"
    )
    assert send_bark._urlopen is urlopen_before, "BARK-GATE-S-URLOPEN-SENTINEL: _urlopen 生产 sentinel 已生效"


def test_held_opener_after_prebound_reload(monkeypatch):
    """R 门 (armed): 用预绑定的真 reload 绕开 reload 双保险之后, **别处握持的
    opener** 仍然不得把请求送出本机。

    这是 round-2 审查击穿的那条链: 依次 _REAL_RELOAD(urllib.request) 与
    _REAL_RELOAD(send_bark) 会把 ②④⑤b⑤d⑤e 一并抹掉 (它们都挂在
    urllib.request 的模块属性上); 此刻还站着的只剩 ⑤a (env, 不随模块重载复原)
    与 ⑤c (_scproxy, 同理)。重载后的真 proxy_bypass 在 env 为空时走 macOS
    分支读 _get_proxy_settings —— 那正是 ⑤c 的存根, 返回「一切主机都绕过代理」,
    于是握持的 opener 直连本机 discard 端口。

    判据锚机外地址 198.51.100.1:63128: 只有它能区分「留在本机」与「送出机」。
    卸甲形态下 env 代理还在, 第一条断言 (getproxies 恒空) 即红。
    全程 socket 层拦截, 两形态都不真建连。"""
    hops = []

    def _intercept(address, *a, **kw):
        hops.append(tuple(address[:2]) if isinstance(address, tuple) else (str(address), None))
        raise OSError(61, "blocked by bark_egress_probe (post-reload held-opener gate)")

    monkeypatch.setattr(socket, "create_connection", _intercept)

    import send_bark

    _REAL_RELOAD(urllib.request)
    _REAL_RELOAD(send_bark)

    assert urllib.request.getproxies() == {}, (
        f"BARK-GATE-R-GETPROXIES: 预绑定 reload 之后代理来源复活 ({urllib.request.getproxies()!r})"
    )
    try:
        _HOSTILE_EXTERNAL_OPENER.open("http://127.0.0.1:9/push", timeout=1)
    except urllib.error.URLError:
        pass

    assert hops, "BARK-GATE-R-NOHOP: 未观察到任何建连尝试"
    assert hops[0] == ("127.0.0.1", 9), (
        f"BARK-GATE-R-HELDHOP: 预绑定 reload 之后握持的 opener 又走了代理 (首跳 {hops[0]!r}, 期望 ('127.0.0.1', 9))"
    )


def test_reapply_after_failed_reload(monkeypatch):
    """X 门 (armed): reload **半途抛异常**之后, 六层仍须已被重打。

    模块顶层一旦执行完, 生产值就已经写回模块 (subprocess.run 变回真实现);
    此时 reload 再抛异常, 「正常返回才重打」的实现就会留下一个失防的模块 ——
    与第八批 H2「先 reload 后 raise 不回滚」同形, 只是换了触发路径
    (round-3 审查用 trace 在 subprocess.py 中断 reload 实测)。

    复刻手法: patch loader **类**的 exec_module, 先真执行再抛。必须打在类上 ——
    importlib.reload 内部会 _find_spec 重新造一个 loader **实例**, 打在
    module.__spec__.loader 那个旧实例上完全不生效 (首跑当场证伪)。
    按模块名限定, 不波及同一次调用里别的 import。
    卸甲形态下没有守卫, reload 之后 subprocess.run 就是真实现, 第二条断言即红。
    整条测试不 spawn、不出网。"""
    loader_cls = type(subprocess.__spec__.loader)
    real_exec = loader_cls.exec_module

    def _exec_then_boom(self, mod):
        real_exec(self, mod)
        if getattr(mod, "__name__", "") == "subprocess":
            raise RuntimeError("bark_egress_probe: reload failed midway (audit)")

    monkeypatch.setattr(loader_cls, "exec_module", _exec_then_boom)
    try:
        importlib.reload(subprocess)
        reloaded_cleanly = True
    except RuntimeError:
        reloaded_cleanly = False

    assert not reloaded_cleanly, "BARK-GATE-X-SETUP: 预期中的 reload 失败没有发生"
    assert getattr(subprocess.run, "__qualname__", "") != "run", (
        "BARK-GATE-X-REAPPLY-ON-FAILURE: reload 半途失败后层⑥ 未被重打, 模块停在生产态"
    )
    subprocess.Popen = _ledger_popen
