"""跨 vault 复习总览聚合 (CARD-C2, BATCH-2026-08-25-跨vault与收束)。

四类锁定: 聚合正确 / 缺投影显式降级 / 损坏 JSON 不 500 / stale 徽标。
CARD-D1 (BATCH-2026-08-27-Anki化与诚实收尾) 追加: 板级聚合与 stats 自洽 /
due_nodes 脏行 corrupt 降级 / Asia/Shanghai 时间人话化 / 无投影深链降级。
CARD-G3-6a (BATCH-2026-08-29-第六批) 追加: 五桶分层计数消费与跨源门禁。
真实文件 fixture: tmp_path 里建真 vault 目录 (.obsidian + outputs/今日复习.json
真文件), settings 走 reload_settings 真实配置机器 — 禁 mock 文件系统语义。
"""

import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

# 与生产代码同款退化 (Codex-D1 L1): 无 tzdata 环境收集不崩, 仍可验固定 +8 回退
try:
    from zoneinfo import ZoneInfo

    _SH = ZoneInfo("Asia/Shanghai")
except Exception:  # noqa: BLE001
    _SH = timezone(timedelta(hours=8))


def _now_local() -> datetime:
    return datetime.now().astimezone()


def _utc_z(dt: datetime) -> str:
    """A2 生产器 fsrs_due 形态: UTC 秒级 Z 后缀。"""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _due_row(
    node: str,
    board,
    *,
    due_reason: str = "new",
    fsrs_due: str = "",
    bucket: str = "new",
    why_due: str = "新卡未排期，视同即刻到期 · 从未考察",
):
    """daily_review_pick.build_payload due_rows 的全字段真形状
    (CARD-G3-6a 起行尾多 bucket/why_due 两个加性字段)。"""
    return {
        "node": node,
        "board": board,
        "state": "new",
        "pick": 1.0,
        "fsrs_due": fsrs_due,
        "due_reason": due_reason,
        "last_examined": "",
        "difficulty": "",
        "bucket": bucket,
        "why_due": why_due,
    }


def _bucket_row(node: str, board: str, *, fsrs_due: str = "", why: str = "理由"):
    """daily_review_pick buckets 桶内行的真形状 (四字段)。"""
    return {"node": node, "board": board, "why_due": why, "fsrs_due": fsrs_due}


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
        # date 恒为合法日历日期 (生产器 date().isoformat() 产物): 敌对
        # generated_at 用例不许顺带把 date 弄脏 — date 垃圾有专属用例
        "date": _now_local().date().isoformat(),
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
        # ── CARD-D1 round2 (Codex-D1 H2/H5) ──
        # JSON "\ud800" 转义解出孤立 surrogate — 响应 UTF-8 序列化才炸,
        # 必须在解析层折断 (默认 ensure_ascii=True 才能把它写成合法文件)
        "bad-surrogate": json.dumps(_projection("x", generated_at=now_iso, board="孤\ud800板")),
        # 显式 null 不是"旧投影缺省" — 生产器恒产出数组
        "bad-boards-null": json.dumps(_projection("x", generated_at=now_iso, boards=None)),
        # 重复 due 行会被静默重复计数
        "bad-dup-due": json.dumps(_projection("x", generated_at=now_iso, due=["同名", "同名"])),
        "bad-node-empty": json.dumps(_projection("x", generated_at=now_iso, due_nodes=[_due_row("", "板")])),
        # 重复 top 板会让后续板与非 top 板共享排序优先级
        "bad-dup-top": json.dumps(
            _projection(
                "x",
                generated_at=now_iso,
                top_boards=[
                    {"board": "B", "top_node": "n", "pending": 1},
                    {"board": "B", "top_node": "n", "pending": 1},
                ],
            )
        ),
        "bad-dup-upcoming": json.dumps(
            _projection(
                "x",
                generated_at=now_iso,
                upcoming=[
                    {"board": "U", "next_due": "2026-09-01T00:00:00Z", "node": "a"},
                    {"board": "U", "next_due": "2026-09-02T00:00:00Z", "node": "b"},
                ],
            )
        ),
        "bad-placeholder-elems": json.dumps(
            _projection(
                "x", generated_at=now_iso, ineligible={"placeholder": [123], "test_excluded": [], "corrupt": []}
            )
        ),
        # ── round2 (Codex-D1 复核残留) ──
        "bad-date-garbage": json.dumps(_projection("x", generated_at=now_iso, date="不是日期")),
        "bad-date-month13": json.dumps(_projection("x", generated_at=now_iso, date="2026-13-01")),
        "bad-top-empty-board": json.dumps(
            _projection("x", generated_at=now_iso, top_boards=[{"board": "", "top_node": "n", "pending": 1}])
        ),
        "bad-upcoming-node-empty": json.dumps(
            _projection(
                "x", generated_at=now_iso, upcoming=[{"board": "U", "next_due": "2026-09-01T00:00:00Z", "node": ""}]
            )
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
    # "<script" 含内联脚本 (Codex-D1 L2: 只拦 <script src= 挡不住内联 JS)
    for marker in ("<script", "<link ", 'src="http', "src='http", 'href="http', "href='http"):
        assert marker not in text.lower(), f"外部资源/JS 引用泄漏: {marker}"


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
    # 新卡+逾期混板: 最早到期取逾期时间戳 (3 天前比"现在"更紧迫), 不许
    # 被新卡空串 (=现在) 盖掉 — 空串只在全新卡板上成立
    assert by["甲板"]["earliest"] == _utc_z(now - timedelta(days=3))
    assert by["乙板"]["earliest"] == _utc_z(now - timedelta(days=1))
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
                # 日历合法极值: strptime 过门禁但 astimezone(+8) 年份溢出
                # OverflowError — 渲染须降级 "—" 不许 500
                _due_row("极", "极值板", due_reason="scheduled", fsrs_due="9999-12-31T23:59:59Z"),
            ],
            stats={"due_nodes": 3},
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
    assert page.status_code == 200, "日历合法极值不得把页面打成 500"
    text = page.text
    assert "极值板" in text  # 溢出值降级 "—" 成行, 不消失也不 500
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
            # 扁平 6 条 vs 板级归属 5 (2+3) — 差额 1 = 无 source_board 占位符
            placeholder=[f"p{i}" for i in range(6)],
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
    # 跨源一致性 (Codex-D1 H4): rollup 声称的到期板集合/计数必须与 due_nodes
    # 明细相等; 板级 placeholder 合计不得超过扁平总数
    _mk_vault(
        root,
        "bad-rollup-due-drift",
        _projection(
            "bad-rollup-due-drift",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=[_due_row("n1", "甲板")],
            boards=[
                {
                    "board": "甲板",
                    "due": 2,
                    "due_new": 2,
                    "due_scheduled": 0,
                    "future": 0,
                    "next_due": "",
                    "placeholder": 0,
                    "earliest_overdue": "",
                },
            ],
        ),
    )
    _mk_vault(
        root,
        "bad-rollup-ghost-board",
        _projection(
            "bad-rollup-ghost-board",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=[_due_row("n1", "甲板")],
            boards=[],  # 声称无到期板但明细有 — 整板会静默消失
        ),
    )
    _mk_vault(
        root,
        "bad-rollup-ph-overflow",
        _projection(
            "bad-rollup-ph-overflow",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=[_due_row("n1", "甲板")],
            boards=[
                {
                    "board": "甲板",
                    "due": 1,
                    "due_new": 1,
                    "due_scheduled": 0,
                    "future": 0,
                    "next_due": "",
                    "placeholder": 999,
                    "earliest_overdue": "",
                },
            ],
        ),
    )

    # round2 (Codex-D1 复核残留): 构造律旁路四连 — 全零幽灵板 / future 与
    # next_due 不自洽 / due 三分越界 / due_new 与明细漂移
    _base_row = {
        "due": 0,
        "due_new": 0,
        "due_scheduled": 0,
        "future": 0,
        "next_due": "",
        "placeholder": 0,
        "earliest_overdue": "",
    }
    _good_row = {**_base_row, "board": "甲板", "due": 1, "due_new": 1}
    round2_bad = {
        "bad-rollup-allzero": [_good_row, {**_base_row, "board": "幽灵板"}],
        "bad-rollup-no-nextdue": [_good_row, {**_base_row, "board": "怪板", "future": 2}],
        "bad-rollup-partition": [{**_good_row, "due_new": 1, "due_scheduled": 1}],
        "bad-rollup-new-drift": [{**_good_row, "due_new": 0, "due_scheduled": 1}],
    }
    for name, rollup_rows in round2_bad.items():
        _mk_vault(
            root,
            name,
            _projection(
                name,
                generated_at=now.isoformat(timespec="seconds"),
                due_nodes=[_due_row("n1", "甲板")],
                boards=rollup_rows,
            ),
        )
    # 纯无主占位符 (M1 残留): boards 为空数组但扁平列表有 2 条 —
    # 汇总行必须标注差额, 不许因无板行而错误置零
    _mk_vault(
        root,
        "vault-unattr",
        _projection(
            "vault-unattr",
            generated_at=now.isoformat(timespec="seconds"),
            due_nodes=[],
            stats={"due_nodes": 0},
            top_boards=[],
            upcoming=[],
            placeholder=["无主1", "无主2"],
            boards=[],
        ),
    )

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    by_id = {v["vault_id"]: v for v in resp.json()["vaults"]}
    assert by_id["bad-rollup"]["status"] == "corrupt", "rollup 形状垃圾必须 corrupt"
    for name in ("bad-rollup-due-drift", "bad-rollup-ghost-board", "bad-rollup-ph-overflow", *round2_bad):
        assert by_id[name]["status"] == "corrupt", f"{name} 跨源不一致必须 corrupt"
    assert by_id["vault-unattr"]["status"] == "ok"
    assert by_id["vault-unattr"]["projection"]["placeholder_attributed"] == 0
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
    # Codex-D1 M1: 无归属占位符差额必须在汇总行标注, 否则汇总 6 vs 板级
    # 合计 5 无法对账; 纯无主占位符 (boards 空) 时差额同样不许被置零
    assert "含未归板 1" in page.text
    assert "含未归板 2" in page.text, "纯无主占位符 vault 的差额注记不许因板行为空而消失"


def test_humanize_due_shanghai_midnight_semantics():
    """跨午夜语义直测 (Codex-D1 M3): now = 上海 2026-08-28 00:30 (UTC 还在
    08-27 16:30) — 上海本地日与 UTC 日错位的窗口, 按 UTC 日判定的实现在
    这三条上必然翻车。纯函数直测, 不经 HTTP 不读时钟, 零闪断。"""
    from app.api.v1.endpoints.review_overview import _humanize_due

    now_sh = datetime(2026, 8, 27, 16, 30, tzinfo=timezone.utc)  # 上海 08-28 00:30
    # due 上海 08-28 01:00: 同上海日 → 现在 (按 UTC 日会误判成逾期)
    assert _humanize_due("2026-08-27T17:00:00Z", now_sh)[0] == "现在"
    # due 上海 08-27 23:00: 上海昨日 → 逾期1天 (按 UTC 日会误判成"现在")
    assert _humanize_due("2026-08-27T15:00:00Z", now_sh)[0] == "逾期1天"
    # due 上海 08-29 00:30 → 明天
    assert _humanize_due("2026-08-28T16:30:00Z", now_sh)[0] == "明天"
    assert _humanize_due("", now_sh)[0] == "现在"
    assert _humanize_due(None, now_sh)[0] == "—"
    assert _humanize_due("9999-12-31T23:59:59Z", now_sh)[0] == "—", "极值溢出降级不炸"


def _sh_at(day, hour: int, minute: int = 0) -> datetime:
    """指定上海本地日的某时刻 (aware) —— 判桶门禁按上海日算, fixture 必须
    显式构造上海日边界, 不能用 now±N 天糊过去 (Codex round-2 D)。"""
    from datetime import time as _time

    return datetime.combine(day, _time(hour, minute), tzinfo=_SH)


def test_buckets_layer_counts_and_cross_source_gate(overview_env):
    """CARD-G3-6a 加性 buckets 消费 (BATCH-2026-08-29-第六批)。

    ① 正常投影: 五桶计数进 JSON (bucket_counts) 与页面「分层」汇总行;
    ② 旧投影无 buckets 键 → 仍 ok 且 bucket_counts=null (加性不倒逼迁移);
    ③ 跨源不一致一律 corrupt 降级 —— 含 Codex round-1/round-2 指出的两类
       身份级旁路: 到期三桶靠与 due_nodes 的成员恒等堵, 非到期两桶在
       due_nodes 里没有对手盘, 改靠「以 generated_at 为参照时钟重算桶判据」
       + 「与 boards rollup 逐板对账」双路堵。

    时钟基准全部由 generated_at 显式给定 (上海今日 08:00), 与运行时刻无关 —
    due_today 取同日 23:00, future 取次日 09:00, 跨午夜运行也不漂。
    """
    root, client = overview_env
    sh_today = datetime.now(_SH).date()
    gen = _sh_at(sh_today, 8)
    gen_iso = gen.isoformat(timespec="seconds")
    overdue = _utc_z(gen - timedelta(days=3))
    today_late = _utc_z(_sh_at(sh_today, 23))
    tomorrow = _utc_z(_sh_at(sh_today + timedelta(days=1), 9))
    W_NEW = "新卡未排期，视同即刻到期 · 从未考察"
    W_LEARN = "学习中 · 已逾期 3 天 · 从未考察"
    W_DUE = "到期待复习 · 已逾期 3 天 · 从未考察"
    rows = [
        _due_row("n1", "甲板"),
        _due_row("n2", "甲板", due_reason="scheduled", fsrs_due=overdue, bucket="learning_queue", why_due=W_LEARN),
        _due_row("n3", "乙板", due_reason="scheduled", fsrs_due=overdue, bucket="due_now", why_due=W_DUE),
    ]
    good = {
        "new": [_bucket_row("n1", "甲板", why=W_NEW)],
        "learning_queue": [_bucket_row("n2", "甲板", fsrs_due=overdue, why=W_LEARN)],
        "due_now": [_bucket_row("n3", "乙板", fsrs_due=overdue, why=W_DUE)],
        "due_today": [_bucket_row("f1", "丙板", fsrs_due=today_late, why="今天 23:00 到期（尚未到点）")],
        "future": [_bucket_row("f2", "丙板", fsrs_due=tomorrow, why="明天 09:00 到期")],
    }
    _blank = {
        "due": 0,
        "due_new": 0,
        "due_scheduled": 0,
        "future": 0,
        "next_due": "",
        "placeholder": 0,
        "earliest_overdue": "",
    }
    rollup = [
        {**_blank, "board": "甲板", "due": 2, "due_new": 1, "due_scheduled": 1, "earliest_overdue": overdue},
        {**_blank, "board": "乙板", "due": 1, "due_scheduled": 1, "earliest_overdue": overdue},
        {**_blank, "board": "丙板", "future": 2, "next_due": today_late},
    ]
    stats = {"due_nodes": 3, "future_nodes": 2}
    tops = [{"board": "甲板", "top_node": "n1", "pending": 2}]
    # 零到期板的最早到期节点 —— 投影内唯一另一处点名非到期节点的地方
    upcoming = [{"board": "丙板", "next_due": today_late, "node": "f1"}]

    def _mk(
        name, *, buckets, due_nodes=rows, st=stats, boards=rollup, generated_at=gen_iso, up=upcoming, drop_boards=False
    ):
        proj = _projection(
            name,
            generated_at=generated_at,
            due_nodes=due_nodes,
            stats=st,
            top_boards=tops,
            upcoming=up,
            boards=boards,
            buckets=buckets,
        )
        if drop_boards:
            proj.pop("boards")
        _mk_vault(root, name, proj)

    _mk("vault-buckets", buckets=good)
    # 旧投影: 无 buckets 键 → 不降级, 只是没有分层数据
    _mk_vault(root, "vault-nobuckets", _projection("vault-nobuckets", generated_at=gen_iso))

    # ── 形状层旁路 ──
    shape_bad: dict[str, object] = {
        "bad-buckets-null": None,  # 显式 null 不是"旧投影缺省", 是形状垃圾
        "bad-buckets-keys": {k: v for k, v in good.items() if k != "future"},
        "bad-buckets-row": {**good, "due_today": [{**good["due_today"][0], "why_due": ""}]},
        # S1 互斥被打破: n1 同时出现在 new 与 due_now
        "bad-buckets-dup": {**good, "due_now": [*good["due_now"], _bucket_row("n1", "甲板", why=W_NEW)]},
        # 未到期桶的 fsrs_due 不得为空 (空串 ⟹ 恒 due_now)
        "bad-buckets-empty-future-ts": {**good, "due_today": [_bucket_row("f1", "丙板", why="x")]},
        # 非到期两桶合计与 stats.future_nodes 漂移
        "bad-buckets-future-drift": {**good, "future": []},
    }
    for name, b in shape_bad.items():
        _mk(name, buckets=b)

    # ── 到期三桶: 身份/语义层旁路 (Codex round-1 HIGH: 逐板计数全不变, 只换身份) ──
    _mk(
        "bad-buckets-identity",
        buckets={
            **good,
            "new": [_bucket_row("FAKE-1", "甲板", why=W_NEW)],
            "learning_queue": [_bucket_row("FAKE-2", "甲板", fsrs_due=overdue, why=W_LEARN)],
            "due_now": [_bucket_row("FAKE-3", "乙板", fsrs_due=overdue, why=W_DUE)],
        },
    )
    # 行内 bucket 与所在桶矛盾 (n2 在 learning_queue, 行却自称 due_now)
    _mk("bad-buckets-label-conflict", buckets=good, due_nodes=[rows[0], {**rows[1], "bucket": "due_now"}, rows[2]])
    # 行内 why_due 与桶内不一致 (两处表示不同源)
    _mk("bad-buckets-why-conflict", buckets=good, due_nodes=[rows[0], {**rows[1], "why_due": "另一套说法"}, rows[2]])
    # new 桶成员实为已排期卡 (语义反例, 且逐板计数不变)
    _mk(
        "bad-buckets-new-semantics",
        buckets={
            **good,
            "new": [_bucket_row("n2", "甲板", fsrs_due=overdue, why=W_LEARN)],
            "learning_queue": [_bucket_row("n1", "甲板", why=W_NEW)],
        },
        due_nodes=[{**rows[0], "bucket": "learning_queue"}, {**rows[1], "bucket": "new"}, rows[2]],
    )
    # 到期三桶合计与 stats.due_nodes 权威计数漂移
    _mk("bad-buckets-stats-drift", buckets=good, st={"due_nodes": 9, "future_nodes": 2})

    # ── 非到期两桶: 身份/语义层旁路 (Codex round-2 HIGH — 上一轮的残留面) ──
    # 纯时间反例: 身份不变、只把 due_today 的时刻挪到远期 → 违反"同上海日"
    # (Codex round-3 LOW: 与身份反例拆开, 一个失败条件不掩盖另一个)
    _mk(
        "bad-buckets-nondue-wrong-day",
        buckets={
            **good,
            "due_today": [_bucket_row("f1", "丙板", fsrs_due="2099-01-01T00:00:00Z", why="x")],
        },
    )
    # 纯身份反例 (Codex round-3 HIGH): 同板、同时刻、同 why_due, 只换节点名 —
    # 时间判据与逐板对账全部通过, 只有 upcoming 身份对账能挡下
    _mk(
        "bad-buckets-nondue-identity",
        buckets={
            **good,
            "due_today": [_bucket_row("FAKE-4", "丙板", fsrs_due=today_late, why="今天 23:00 到期（尚未到点）")],
        },
    )
    # upcoming 的 next_due 与桶内该节点时刻不一致
    _mk("bad-buckets-upcoming-ts-drift", buckets=good, up=[{"board": "丙板", "next_due": tomorrow, "node": "f1"}])
    # 清空 upcoming 想整体跳过身份对账 (Codex round-4 HIGH): 条数必须由 rollup 复算
    _mk("bad-buckets-upcoming-emptied", buckets=good, up=[])
    # upcoming 换成一个「有到期节点」的板 (甲板) —— 不符合零到期资格
    _mk("bad-buckets-upcoming-wrong-board", buckets=good, up=[{"board": "甲板", "next_due": today_late, "node": "n1"}])
    # 未来时刻伪装成 due_now (两处 fsrs_due 同步改, 逐板计数不变) —
    # 靠到期侧时间逆检查挡下 (Codex round-4 HIGH)
    _mk(
        "bad-buckets-due-future-ts",
        buckets={**good, "due_now": [_bucket_row("n3", "乙板", fsrs_due=today_late, why=W_DUE)]},
        due_nodes=[rows[0], rows[1], {**rows[2], "fsrs_due": today_late}],
    )
    # buckets 在场但 boards 缺席 —— 非任何历史形态 (Codex round-3 HIGH)
    _mk("bad-buckets-no-boards", buckets=good, drop_boards=True)
    # 同名节点跨板各落一桶 (Codex round-5 HIGH): 生产器 stem 全局唯一, 用
    # (板, 节点) 复合键去重会放行这类伪造 —— 它直接违反 S1「恰好一桶」且虚增计数
    _mk(
        "bad-buckets-node-dup-across-boards",
        buckets={**good, "future": [*good["future"], _bucket_row("n1", "丙板", fsrs_due=tomorrow, why="x")]},
        st={"due_nodes": 3, "future_nodes": 3},
        boards=[*rollup[:2], {**_blank, "board": "丙板", "future": 3, "next_due": today_late}],
    )
    # due_nodes 侧同名节点跨板重复 (同一收紧的另一半)
    _mk(
        "bad-due-nodes-node-dup-across-boards",
        buckets=good,
        due_nodes=[
            *rows,
            _due_row("n1", "乙板", due_reason="scheduled", fsrs_due=overdue, bucket="due_now", why_due=W_DUE),
        ],
    )
    # future 桶塞已到期时刻 (应属到期侧)
    _mk("bad-buckets-nondue-past", buckets={**good, "future": [_bucket_row("f2", "丙板", fsrs_due=overdue, why="x")]})
    # future 桶塞同上海日时刻 (应属 due_today)
    _mk(
        "bad-buckets-future-same-day",
        buckets={**good, "future": [_bucket_row("f2", "丙板", fsrs_due=today_late, why="x")]},
    )
    # 与 boards rollup 逐板对账: rollup 声称丙板只有 1 个未到期
    _mk(
        "bad-buckets-rollup-future-drift",
        buckets=good,
        boards=[*rollup[:2], {**_blank, "board": "丙板", "future": 1, "next_due": today_late}],
    )
    # buckets 在场却给不出可信参照时钟 → 无从重算桶判据, 按 corrupt 降级
    _mk("bad-buckets-badgen", buckets=good, generated_at="20260830")

    resp = client.get("/api/v1/review/overview")
    assert resp.status_code == 200
    by_id = {v["vault_id"]: v for v in resp.json()["vaults"]}
    for name in (
        *shape_bad,
        "bad-buckets-identity",
        "bad-buckets-label-conflict",
        "bad-buckets-why-conflict",
        "bad-buckets-new-semantics",
        "bad-buckets-stats-drift",
        "bad-buckets-nondue-wrong-day",
        "bad-buckets-nondue-identity",
        "bad-buckets-upcoming-ts-drift",
        "bad-buckets-upcoming-emptied",
        "bad-buckets-upcoming-wrong-board",
        "bad-buckets-due-future-ts",
        "bad-buckets-no-boards",
        "bad-buckets-node-dup-across-boards",
        "bad-due-nodes-node-dup-across-boards",
        "bad-buckets-nondue-past",
        "bad-buckets-future-same-day",
        "bad-buckets-rollup-future-drift",
        "bad-buckets-badgen",
    ):
        assert by_id[name]["status"] == "corrupt", f"{name} 跨源不一致必须 corrupt 降级"
    assert by_id["vault-nobuckets"]["status"] == "ok"
    assert by_id["vault-nobuckets"]["projection"]["bucket_counts"] is None, "旧投影不伪造分层数字"
    entry = by_id["vault-buckets"]
    assert entry["status"] == "ok", entry.get("error")
    assert entry["projection"]["bucket_counts"] == {
        "new": 1,
        "learning_queue": 1,
        "due_now": 1,
        "due_today": 1,
        "future": 1,
    }
    # 分层三桶合计仍等于权威计数, 分层只是标签不是搬移 (生产器 S2)
    assert entry["projection"]["due_count"] == 3

    page = client.get("/api/v1/review/overview/page")
    assert page.status_code == 200
    assert "分层 · 新卡 1 · 学习中 1 · 到期 1 · 今天晚些 1 · 未来 1" in page.text
    assert page.text.count("分层 · ") == 1, "无 buckets 的旧投影卡片不出现分层行"


def test_buckets_gate_accepts_real_producer_payload(tmp_path, overview_env):
    """假阳性防线 (Codex round-2 C/D): 不用手搓 fixture —— 直接跑真生产器
    daily_review_pick.build_payload 产出投影, 落成真文件后过总览端点, 必须
    ok 且分层计数与生产器 buckets 逐字相等。门禁若把生产器真实产出判成
    corrupt, 本用例立刻红。"""
    import shutil
    import sys
    from pathlib import Path

    wt = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(wt / "scripts"))
    import daily_review_pick as picker

    root, client = overview_env
    vault = root / "vault-real"
    (vault / ".obsidian").mkdir(parents=True)
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(wt / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)

    now = datetime.now(_SH).replace(hour=9, minute=0, second=0, microsecond=0)
    sh_today = now.date()

    def _node(board, extra=""):
        return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'

    files = {
        "真新卡": _node("甲板"),
        "学习中": _node("甲板", f"fsrs_due: {_utc_z(now - timedelta(days=2))}\nfsrs_state: 1\n"),
        "普通到期": _node("乙板", f"fsrs_due: {_utc_z(now - timedelta(days=1))}\nfsrs_state: 2\n"),
        "今天晚些": _node("丙板", f"fsrs_due: {_utc_z(_sh_at(sh_today, 23))}\n"),
        "远期": _node("丙板", f"fsrs_due: {_utc_z(_sh_at(sh_today + timedelta(days=5), 9))}\n"),
    }
    # 再造 4 个零到期板 —— 共 5 个候选、upcoming 被生产器截断到 3, 逼真跑通
    # 「条数 == min(3, 候选数)」与「未选中的板不得更早」两条新对账
    # (Codex round-4 B: 这正是最容易误伤真实产物的地方)
    for i, day in enumerate((2, 3, 4, 6), start=1):
        files[f"零到期{i}"] = _node(f"板{i}", f"fsrs_due: {_utc_z(_sh_at(sh_today + timedelta(days=day), 9))}\n")
    for name, content in files.items():
        (vault / "节点" / f"{name}.md").write_text(content, encoding="utf-8")
    payload, _ = picker.build_payload(vault, now, {}, picker.load_decay(vault))
    (vault / "outputs").mkdir()
    (vault / "outputs" / "今日复习.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 防门禁分支空跑: 真产物必须同时带 boards / buckets / 非空 upcoming,
    # 否则 (b)(c) 两条对账在本用例里等于没跑
    assert payload["upcoming"] and payload["boards"] and payload["buckets"]
    assert payload["upcoming"][0]["board"] == "丙板", "零到期板才进 upcoming, 且按 next_due 升序"
    assert len(payload["upcoming"]) == 3, "生产器把 upcoming 截断到 3, 候选实为 5 板"
    zero_due = [r["board"] for r in payload["boards"] if r["due"] == 0 and r["future"] > 0]
    assert len(zero_due) == 5, "截断分支必须真的被触发, 否则新对账等于空跑"

    entry = {v["vault_id"]: v for v in client.get("/api/v1/review/overview").json()["vaults"]}["vault-real"]
    assert entry["status"] == "ok", entry.get("error")
    assert entry["projection"]["bucket_counts"] == {
        b: len(payload["buckets"][b]) for b in ("new", "learning_queue", "due_now", "due_today", "future")
    }
    assert entry["projection"]["bucket_counts"] == {
        "new": 1,
        "learning_queue": 1,
        "due_now": 1,
        "due_today": 1,
        "future": 5,
    }
    assert entry["projection"]["due_count"] == payload["stats"]["due_nodes"] == 3
