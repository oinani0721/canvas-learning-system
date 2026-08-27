"""跨 vault 复习总览聚合 (CARD-C2, BATCH-2026-08-25-跨vault与收束)。

四类锁定: 聚合正确 / 缺投影显式降级 / 损坏 JSON 不 500 / stale 徽标。
CARD-D1 (BATCH-2026-08-27-Anki化与诚实收尾) 追加: 板级聚合与 stats 自洽 /
due_nodes 脏行 corrupt 降级 / Asia/Shanghai 时间人话化 / 无投影深链降级。
真实文件 fixture: tmp_path 里建真 vault 目录 (.obsidian + outputs/今日复习.json
真文件), settings 走 reload_settings 真实配置机器 — 禁 mock 文件系统语义。
"""

import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

_SH = ZoneInfo("Asia/Shanghai")


def _now_local() -> datetime:
    return datetime.now().astimezone()


def _utc_z(dt: datetime) -> str:
    """A2 生产器 fsrs_due 形态: UTC 秒级 Z 后缀。"""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _due_row(node: str, board, *, due_reason: str = "new", fsrs_due: str = ""):
    """daily_review_pick.build_payload due_rows 的全字段真形状。"""
    return {
        "node": node,
        "board": board,
        "state": "new",
        "pick": 1.0,
        "fsrs_due": fsrs_due,
        "due_reason": due_reason,
        "last_examined": "",
        "difficulty": "",
    }


def _projection(
    vault_id: str,
    *,
    generated_at,
    due: list[str] | None = None,
    placeholder: list[str] | None = None,
    board: str | None = "CS 61B",
    stats_due=None,
    **overrides,
) -> dict:
    """schema v3 形状的最小真投影 (字段名与 daily_review_pick.build_payload
    对齐)。stats_due 可与明细长度解耦 (锁定「读 stats 权威计数、不重数明细」);
    overrides 直接覆盖顶层键, 供敌对形状用例注入垃圾。"""
    due = ["节点甲"] if due is None else due
    top_boards = (
        [
            {
                "board": board,
                "top_node": due[0],
                "priority": 1.0,
                "pending": len(due),
                "idle_days": 3,
                "difficulty": "",
                "next_due": "",
            }
        ]
        if board and due
        else []
    )
    payload = {
        "unassigned_nodes": [],
        "schema_version": 3,
        "vault_id": vault_id,
        "date": str(generated_at)[:10],
        "generated_at": generated_at,
        "top_boards": top_boards,
        "upcoming": [],
        "due_nodes": [
            {
                "node": n,
                "board": board,
                "state": "new",
                "pick": 1.0,
                "fsrs_due": "",
                "due_reason": "new",
                "last_examined": "",
                "difficulty": "",
            }
            for n in due
        ],
        "ineligible": {"placeholder": placeholder or [], "test_excluded": [], "corrupt": []},
        "stats": {"due_nodes": len(due) if stats_due is None else stats_due},
        "notification": None,
    }
    payload.update(overrides)
    return payload


def _mk_vault(root, name: str, projection: dict | None = None, raw: str | None = None):
    """真目录 + 真文件 — 不 mock 任何文件系统语义。"""
    vault = root / name
    (vault / ".obsidian").mkdir(parents=True)
    if raw is not None or projection is not None:
        (vault / "outputs").mkdir()
        text = raw if raw is not None else json.dumps(projection, ensure_ascii=False, indent=2)
        (vault / "outputs" / "今日复习.json").write_text(text, encoding="utf-8")
    return vault


@pytest.fixture
def overview_env(tmp_path):
    """VAULTS_ROOT 指向 tmp 的真实 Settings。

    Codex-C2 HIGH: reload_settings 会永久写 os.environ — teardown 必须按
    「键原先是否存在」恢复 (原不存在的键 pop 掉, 不能只回写值), 且用
    try/finally 保证 TestClient 构造失败时同样恢复。
    """
    import os

    import app.config as config_mod
    import app.main as main_mod
    from app.config import reload_settings

    saved = {k: os.environ.get(k) for k in ("VAULTS_ROOT", "ACTIVE_VAULT")}

    def _sync_main_settings():
        # reload_settings 只重绑 app.config.settings; app.main 按值导入了
        # settings (main.py), reload 后两模块指向不同对象 (split-brain,
        # Codex-C2 HIGH round2) — 前后各同步一次, 本 fixture 生命周期内
        # 与 teardown 后两处恒指同一对象
        main_mod.settings = config_mod.settings

    try:
        reload_settings(overrides={"VAULTS_ROOT": str(tmp_path), "ACTIVE_VAULT": "vault-a"})
        _sync_main_settings()
        from app.main import app

        yield tmp_path, TestClient(app)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        reload_settings()  # 无 overrides: 只按恢复后的 env 重建缓存/全局
        _sync_main_settings()


def test_aggregates_multiple_vaults(overview_env):
    """聚合正确: N=2 真投影 → 每库一条 ok 条目; due_count 取 stats 权威值
    (与明细长度刻意解耦 — 重数明细的错误实现会在 vault-b 上露馅)。"""
    root, client = overview_env
    now_iso = _now_local().isoformat(timespec="seconds")
    _mk_vault(
        root,
        "vault-a",
        _projection(
            "vault-a", generated_at=now_iso, due=["甲", "乙"], placeholder=["积压1", "积压2", "积压3"], board="CS 61B"
        ),
    )
    # stats.due_nodes=7 而明细只有 1 条 — 权威计数在 stats (A2 构造同源)
    _mk_vault(root, "vault-b", _projection("vault-b", generated_at=now_iso, due=["丙"], board="数学", stats_due=7))

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert [v["vault_id"] for v in data["vaults"]] == ["vault-a", "vault-b"]
    a, b = data["vaults"]
    assert a["status"] == "ok" and b["status"] == "ok"
    assert a["projection"]["due_count"] == 2
    assert a["projection"]["placeholder_backlog"] == 3
    assert a["projection"]["recommended_board"] == "CS 61B"
    assert b["projection"]["due_count"] == 7, "必须读 stats 权威计数, 不得重数明细"
    assert b["projection"]["recommended_board"] == "数学"


def test_missing_projection_explicit_degraded_entry(overview_env):
    """缺投影 vault 必须以显式 no_projection 条目出现, 禁静默跳过;
    非 vault 目录 (无 .obsidian) 不进列表。"""
    root, client = overview_env
    _mk_vault(root, "vault-a", _projection("vault-a", generated_at=_now_local().isoformat(timespec="seconds")))
    _mk_vault(root, "vault-new")  # 有 .obsidian, 无投影
    (root / "not-a-vault").mkdir()  # 无 .obsidian → 不枚举

    data = client.get("/api/v1/review/overview").json()
    assert [v["vault_id"] for v in data["vaults"]] == ["vault-a", "vault-new"]
    degraded = data["vaults"][1]
    assert degraded["status"] == "no_projection"
    assert degraded["projection"] is None

    # 降级条目在页面上也必须可见 (显式"无投影"卡片)
    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    assert "vault-new" in page.text and "无投影" in page.text


def test_corrupt_projection_does_not_500(overview_env):
    """损坏 JSON / schema 形状垃圾 → 单库 corrupt 降级, 全局仍 200,
    健康库不受拖累。敌对形状全清单 (Codex-C2 B3): 非 v3 版本、嵌套容器
    垃圾、bool/字符串计数、非标准 JSON 常量——一个都不许发 ok。"""
    root, client = overview_env
    now_iso = _now_local().isoformat(timespec="seconds")
    _mk_vault(root, "vault-a", _projection("vault-a", generated_at=now_iso))
    hostile = {
        "bad-syntax": "{ 这不是合法 JSON",
        "bad-root": '["根节点不是object"]',
        "bad-version": json.dumps(_projection("x", generated_at=now_iso, schema_version=2)),
        "bad-stats-list": json.dumps(_projection("x", generated_at=now_iso, stats=[])),
        "bad-due-nodes": json.dumps(_projection("x", generated_at=now_iso, due_nodes="garbage")),
        "bad-count-bool": json.dumps(_projection("x", generated_at=now_iso, stats_due=True)),
        "bad-count-str": json.dumps(_projection("x", generated_at=now_iso, stats_due="99")),
        "bad-placeholder": json.dumps(
            _projection(
                "x", generated_at=now_iso, ineligible={"placeholder": "abc", "test_excluded": [], "corrupt": []}
            )
        ),
        "bad-nan": json.dumps(_projection("x", generated_at=now_iso)).replace('"pick": 1.0', '"pick": NaN'),
        "bad-genat-num": json.dumps(_projection("x", generated_at=20260825)),
        # round2: 标准数字 1e999 经 parse_float 变 inf — 非有限数拒收
        "bad-inf": json.dumps(_projection("x", generated_at=now_iso)).replace('"pick": 1.0', '"pick": 1e999'),
        # round2: 嵌套元素形状垃圾 (upcoming[0] 非 object 会被透传进响应)
        "bad-upcoming-elem": json.dumps(_projection("x", generated_at=now_iso, upcoming=["not-an-object"])),
        # round3: upcoming[0] 是 object 但内部字段类型垃圾 — 透传面必须
        # 逐字段门禁, 整对象透传即形状垃圾通道
        "bad-upcoming-fields": json.dumps(
            _projection("x", generated_at=now_iso, upcoming=[{"board": [], "next_due": False, "node": {"a": 1}}])
        ),
        "bad-pending-str": json.dumps(
            _projection("x", generated_at=now_iso, top_boards=[{"board": "B", "top_node": "n", "pending": "many"}])
        ),
    }
    for name, raw in hostile.items():
        _mk_vault(root, name, raw=raw)
    # 权限拒绝 → corrupt (读文件 OSError 路径)。root/提权 CI 无视权限位,
    # 该场景只在普通用户下有效 — root 时跳过此库
    run_perm_case = os.geteuid() != 0
    if run_perm_case:
        denied = _mk_vault(root, "bad-perm", _projection("x", generated_at=now_iso))
        (denied / "outputs" / "今日复习.json").chmod(0o000)
    # 目录冒充投影文件 → corrupt (IsADirectoryError 路径)
    isdir = root / "bad-isdir"
    (isdir / ".obsidian").mkdir(parents=True)
    (isdir / "outputs" / "今日复习.json").mkdir(parents=True)
    hostile["bad-isdir"] = ""
    if run_perm_case:
        hostile["bad-perm"] = ""

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    by_id = {v["vault_id"]: v for v in resp.json()["vaults"]}
    assert by_id["vault-a"]["status"] == "ok", "健康库不得被邻居垃圾拖累"
    for name in hostile:
        assert by_id[name]["status"] == "corrupt", f"{name} 形状垃圾必须 corrupt, 实为 {by_id[name]['status']}"
        assert by_id[name]["error"]

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    assert "投影损坏" in page.text


def test_stale_badge_from_generated_at(overview_env):
    """stale 判定基于投影自带 generated_at (非文件 mtime): 昨天 → stale,
    今天 (mtime 刻意回拨到一周前) → 仍 ok — 证明不读 mtime; 宽松格式
    (纯日期/无时区/畸形/极端溢出值) 一律 stale, 不许冒充今日新鲜
    (Codex-C2 B1/B2), 且极端时区值不得 500。"""
    root, client = overview_env
    now = _now_local()
    today_iso = now.isoformat(timespec="seconds")
    _mk_vault(
        root, "vault-a", _projection("vault-a", generated_at=(now - timedelta(days=1)).isoformat(timespec="seconds"))
    )
    fresh = _mk_vault(root, "vault-b", _projection("vault-b", generated_at=today_iso))
    # runner 会把投影 mtime 回拨到扫描起点 — mtime 一周前 + generated_at
    # 今天, 实现若偷看 mtime 会误判 stale
    week_ago = (now - timedelta(days=7)).timestamp()
    os.utime(fresh / "outputs" / "今日复习.json", (week_ago, week_ago))
    today_naive = now.replace(tzinfo=None).isoformat(timespec="seconds")
    lax = {
        "lax-garbage": "不是时间",
        "lax-date-only": now.date().isoformat(),
        "lax-no-tz": today_naive,
        "lax-overflow": "9999-12-31T23:59:59-23:59",  # astimezone 溢出 → 不得 500
        # round2: 非法 offset 分钟被 fromisoformat 静默归一化 (+08:60→+09:00)
        # — A2 生产器绝不会产出, 必须 stale
        "lax-bad-offset-60": f"{today_naive}+08:60",
        "lax-bad-offset-99": f"{today_naive}+08:99",
        "lax-bad-offset-15h": f"{today_naive}+15:00",
    }
    for name, gen in lax.items():
        _mk_vault(root, name, _projection(name, generated_at=gen))

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200, "极端时区值不得把全局打成 500"
    by_id = {v["vault_id"]: v for v in resp.json()["vaults"]}
    assert by_id["vault-a"]["status"] == "stale"
    assert by_id["vault-b"]["status"] == "ok", "mtime 回拨不得影响判定 (只看 generated_at)"
    for name in lax:
        assert by_id[name]["status"] == "stale", f"{name} 宽松格式必须 stale, 实为 {by_id[name]['status']}"

    page = client.get("/api/v1/review/overview/page").text
    assert "过期投影" in page and "今日投影" in page


def test_readonly_contract_files_untouched(overview_env):
    """只读契约: 两个端点请求前后, 投影文件字节与 mtime 逐一不变。"""
    root, client = overview_env
    vault = _mk_vault(root, "vault-a", _projection("vault-a", generated_at=_now_local().isoformat(timespec="seconds")))
    proj = vault / "outputs" / "今日复习.json"
    pinned = 1_700_000_000
    os.utime(proj, (pinned, pinned))
    before_bytes = proj.read_bytes()

    assert client.get("/api/v1/review/overview").status_code == 200
    assert client.get("/api/v1/review/overview/page").status_code == 200

    assert proj.read_bytes() == before_bytes
    assert proj.stat().st_mtime == pinned, "端点不得触碰投影文件 (含 mtime)"


def test_page_is_self_contained_with_obsidian_links(overview_env):
    """页面硬约束: 零外部 CDN (无外链 script/css/img), obsidian:// 跳转链接,
    text/html 响应头。"""
    root, client = overview_env
    _mk_vault(root, "vault-a", _projection("vault-a", generated_at=_now_local().isoformat(timespec="seconds")))

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    text = page.text
    assert "obsidian://open?vault=vault-a" in text
    for marker in ("<script src=", "<link ", 'src="http', "src='http", 'href="http', "href='http"):
        assert marker not in text, f"外部资源引用泄漏: {marker}"


# ── CARD-D1: 总览页 Anki 化 (BATCH-2026-08-27-Anki化与诚实收尾) ──


def test_board_table_groupby_matches_stats(overview_env):
    """板级聚合自洽: 到期数由 due_nodes group-by 得出且合计==stats.due_nodes;
    行序 = 有到期板按 top_boards 优先级 (乙板列首位则排前) → 零到期板按
    next_due 垫底; 板名深链 percent-encode 指向 原白板/<板名>.md。"""
    root, client = overview_env
    now = _now_local()
    rows = [
        _due_row("n1", "甲板"),
        _due_row("n2", "甲板", due_reason="scheduled", fsrs_due=_utc_z(now - timedelta(days=3))),
        _due_row("n3", "乙板", due_reason="scheduled", fsrs_due=_utc_z(now - timedelta(days=1))),
    ]
    _mk_vault(
        root,
        "vault-a",
        _projection(
            "vault-a",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=rows,
            stats={"due_nodes": 3},
            top_boards=[
                {"board": "乙板", "top_node": "n3", "pending": 1},
                {"board": "甲板", "top_node": "n1", "pending": 2},
            ],
            upcoming=[{"board": "丙板", "next_due": _utc_z(now + timedelta(days=2)), "node": "nx"}],
        ),
    )

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    entry = resp.json()["vaults"][0]
    assert entry["status"] == "ok"
    p = entry["projection"]
    assert [r["board"] for r in p["boards"]] == ["乙板", "甲板", "丙板"], "top_boards 优先级先行, 零到期垫底"
    by = {r["board"]: r for r in p["boards"]}
    assert by["甲板"]["due"] == 2 and by["甲板"]["due_new"] == 1
    assert by["乙板"]["due"] == 1 and by["乙板"]["due_new"] == 0
    assert by["丙板"]["due"] == 0 and by["丙板"]["due_new"] == 0
    assert sum(r["due"] for r in p["boards"]) == p["due_count"] == 3, "板级合计必须==stats.due_nodes"
    assert p["due_new_count"] == 1

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    text = page.text
    for col in ("白板名", "到期", "新卡", "待剖析", "最早到期"):
        assert col in text, f"板表格缺列头 {col}"
    for board in ("甲板", "乙板", "丙板"):
        # HTML 属性里 & 合法转义为 &amp; — 断言对齐落页形态
        link = "obsidian://open?vault=vault-a&amp;file=" + quote(f"原白板/{board}.md", safe="")
        assert link in text, f"{board} 深链缺失或未按 percent-encode 约定"


def test_due_nodes_dirty_rows_degrade_corrupt_not_500(overview_env):
    """due_nodes 行级门禁: 行不是 object / board 非法 / due_reason 枚举外 /
    fsrs_due 非生产器形态或日历非法 / due_reason 与 fsrs_due 不自洽 —
    一律按既有 corrupt 语义降级, 全局 200, 健康库不受拖累。"""
    root, client = overview_env
    now_iso = _now_local().isoformat(timespec="seconds")
    _mk_vault(root, "vault-a", _projection("vault-a", generated_at=now_iso))
    dirty = {
        "row-not-object": [["不是对象"]],
        "board-not-str": [_due_row("n", 123)],
        "board-empty": [_due_row("n", "")],
        "reason-garbage": [_due_row("n", "板", due_reason="whenever")],
        "fsrs-offset-form": [_due_row("n", "板", due_reason="scheduled", fsrs_due="2026-08-01T00:00:00+08:00")],
        "fsrs-calendar-invalid": [_due_row("n", "板", due_reason="scheduled", fsrs_due="2026-13-01T00:00:00Z")],
        "reason-fsrs-mismatch": [_due_row("n", "板", due_reason="scheduled", fsrs_due="")],
    }
    for name, rows in dirty.items():
        _mk_vault(root, name, _projection(name, generated_at=now_iso, due_nodes=rows))

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    by_id = {v["vault_id"]: v for v in resp.json()["vaults"]}
    assert by_id["vault-a"]["status"] == "ok", "健康库不得被邻居脏行拖累"
    for name in dirty:
        assert by_id[name]["status"] == "corrupt", f"{name} 脏行必须 corrupt, 实为 {by_id[name]['status']}"
        assert by_id[name]["error"]


def test_time_humanization_asia_shanghai(overview_env):
    """时间人话化: 统一转 Asia/Shanghai, 逾期N天/现在/明天/N天后/M月D日;
    页面生成时间显示上海本地时区, UTC 裸串 (+00:00) 不得出现在页面
    (现网容器 UTC 缺陷的回归锁定)。"""
    root, client = overview_env
    now = datetime.now(timezone.utc)
    far = now + timedelta(days=40)
    _mk_vault(
        root,
        "vault-a",
        _projection(
            "vault-a",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=[
                _due_row("逾", "逾期板", due_reason="scheduled", fsrs_due=_utc_z(now - timedelta(days=3))),
                _due_row("新", "新卡板"),
            ],
            stats={"due_nodes": 2},
            top_boards=[
                {"board": "逾期板", "top_node": "逾", "pending": 1},
                {"board": "新卡板", "top_node": "新", "pending": 1},
            ],
            upcoming=[
                {"board": "明日板", "next_due": _utc_z(now + timedelta(days=1)), "node": "a"},
                {"board": "五日板", "next_due": _utc_z(now + timedelta(days=5)), "node": "b"},
                {"board": "远期板", "next_due": _utc_z(far), "node": "c"},
            ],
        ),
    )

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    text = page.text
    assert "逾期3天" in text
    assert "现在" in text  # 新卡板 (fsrs_due 空串 = 即刻到期)
    assert "明天" in text
    assert "5天后" in text
    far_sh = far.astimezone(_SH)
    expected_far = (
        f"{far_sh.month}月{far_sh.day}日"
        if far_sh.year == now.astimezone(_SH).year
        else f"{far_sh.year}年{far_sh.month}月{far_sh.day}日"
    )
    assert expected_far in text, "超过一周的未来到期应显示日历日期"
    assert "(UTC+8)" in text, "页面生成时间必须标注上海本地时区"
    assert now.astimezone(_SH).strftime("%Y-%m-%d") in text
    assert "+00:00" not in text, "UTC 裸串不得漏进页面 (现网缺陷)"


def test_no_projection_degrades_without_fake_deeplink(overview_env):
    """无投影 vault: 显式降级文案, 不做假链接; 页面带"需在 Obsidian 打开过
    该库"提示 (test-vault 死链与同名库跳错的诚实降级)。"""
    root, client = overview_env
    _mk_vault(root, "vault-a", _projection("vault-a", generated_at=_now_local().isoformat(timespec="seconds")))
    _mk_vault(root, "vault-new")  # 有 .obsidian, 无投影

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    text = page.text
    assert "obsidian://open?vault=vault-a" in text
    assert "obsidian://open?vault=vault-new" not in text, "无投影 vault 不得出假链接"
    assert "需在 Obsidian 打开过该库" in text


def test_boards_rollup_consumed_when_present(overview_env):
    """P1 rollup 在场: 待剖析列取板级归属; 零到期板走 rollup 全量 (不再受
    upcoming[:3] 截断); 占位符专属板成行 (最早到期无数据 → null); rollup
    形状垃圾按既有 corrupt 语义降级。rollup 缺省 (旧投影) 时上述回落 P0
    派生路径 — 由其余测试覆盖。"""
    root, client = overview_env
    now = _now_local()
    rollup = [
        {
            "board": "甲板",
            "due": 1,
            "due_new": 1,
            "due_scheduled": 0,
            "future": 0,
            "next_due": "",
            "placeholder": 2,
            "earliest_overdue": "",
        },
        {
            "board": "乙板",
            "due": 0,
            "due_new": 0,
            "due_scheduled": 0,
            "future": 1,
            "next_due": _utc_z(now + timedelta(days=3)),
            "placeholder": 0,
            "earliest_overdue": "",
        },
        {
            "board": "丙板",
            "due": 0,
            "due_new": 0,
            "due_scheduled": 0,
            "future": 1,
            "next_due": _utc_z(now + timedelta(days=2)),
            "placeholder": 0,
            "earliest_overdue": "",
        },
        {
            "board": "丁板",
            "due": 0,
            "due_new": 0,
            "due_scheduled": 0,
            "future": 0,
            "next_due": "",
            "placeholder": 3,
            "earliest_overdue": "",
        },
    ]
    _mk_vault(
        root,
        "vault-a",
        _projection(
            "vault-a",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=[_due_row("n1", "甲板")],
            stats={"due_nodes": 1},
            top_boards=[{"board": "甲板", "top_node": "n1", "pending": 1}],
            # upcoming 只截到丙板 — 乙板/丁板必须由 rollup 补全
            upcoming=[{"board": "丙板", "next_due": rollup[2]["next_due"], "node": "x"}],
            boards=rollup,
        ),
    )
    _mk_vault(
        root,
        "bad-rollup",
        _projection(
            "bad-rollup",
            generated_at=now.isoformat(timespec="seconds"),
            boards=[{"board": "x", "due": -1}],
        ),
    )

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    by_id = {v["vault_id"]: v for v in resp.json()["vaults"]}
    assert by_id["bad-rollup"]["status"] == "corrupt", "rollup 形状垃圾必须 corrupt"
    entry = by_id["vault-a"]
    assert entry["status"] == "ok"
    p = entry["projection"]
    assert [r["board"] for r in p["boards"]] == ["甲板", "丙板", "乙板", "丁板"], (
        "到期板先行, 零到期板按 next_due 升序, 无排期垫底"
    )
    by = {r["board"]: r for r in p["boards"]}
    assert by["甲板"]["placeholder"] == 2 and by["甲板"]["due"] == 1
    assert by["乙板"]["due"] == 0 and by["乙板"]["placeholder"] == 0
    assert by["丁板"]["placeholder"] == 3 and by["丁板"]["earliest"] is None
    assert sum(r["due"] for r in p["boards"]) == p["due_count"] == 1

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    assert "丁板" in page.text and "乙板" in page.text
