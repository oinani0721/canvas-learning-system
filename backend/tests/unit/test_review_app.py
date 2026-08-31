"""交互复习壳 (CARD-G6-2, BATCH-2026-09-01-第八批)。

四类锁定:
  A. 单文件自足 —— 零外部 URL / 零 CDN / 零外部资源标签; API 路径来自
     url_for 注入而非硬编码; 只 fetch 同源那两个端点。
  B. 与零 JS 只读页共存 —— 两页同时 200; review_overview.py 的 `<script`
     计数与开工基线 (1, 唯一命中是 :1286 docstring「python <script>」) 相等。
  C. 渲染纯函数 (node --test) —— 四态徽标 / unavailable 不白屏 / 休息日
     空状态 / W6 三字段有无各一 / 轮询 clamp / 隐藏暂停 / XSS 转义。
     ⚠ 被测 JS **从实际 HTTP 响应体里割出来**, 不是模板常量的副本 ——
     测的是注入后的真实产物 (占位符没被替换、注入值走样, 这些门都会红)。
  D. 不重算到期 —— 喂一份 due_count 与 boards 明细刻意不一致的投影,
     页面必须显示服务端权威 due_count; JS 若偷偷重算, 本门变红。

真实 HTTP 响应 + 真 node 进程, 无 mock。TestClient 一律裸构造 (不带 with):
起 lifespan 会连 7691 (第七批 F-3)。
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints.review_app import _PAGE_TEMPLATE
from app.api.v1.endpoints.review_overview import (
    _BUCKET_CN,
    _BUCKET_ORDER,
    _STATUS_META,
    _humanize_due,
)

APP_PATH = "/api/v1/review/overview/app"
PAGE_PATH = "/api/v1/review/overview/page"
OVERVIEW_PATH = "/api/v1/review/overview"
REFRESH_PATH = "/api/v1/review/overview/refresh"

_ENDPOINTS_DIR = Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "endpoints"
#: 开工基线 (2026-09-01 主干 9af18b27 实测): review_overview.py 的 `<script`
#: 计数为 1, 唯一命中是 :1286 docstring 里的「python <script> --vault」——
#: 与 JS 无关。零 JS 页未被本卡改动的判据。
_ZERO_JS_BASELINE = 1


@pytest.fixture
def client():
    """裸 TestClient — 不带 with, 不起 lifespan。

    本端点是纯静态 HTML 渲染 (不读文件系统、不查 settings 的 vault 面),
    所以不需要 VAULTS_ROOT fixture; base_url 用回环地址与
    test_review_overview.py 保持同款 (refresh 端点有 Host 白名单)。
    """
    from app.main import app

    c = TestClient(app, base_url="http://127.0.0.1:8011")
    try:
        yield c
    finally:
        c.close()


@pytest.fixture
def page_html(client):
    resp = client.get(APP_PATH)
    assert resp.status_code == 200, resp.text
    return resp.text


# ════════════════════════════════════════════════════════════════════
# A. 单文件自足 (完成条件 a)
# ════════════════════════════════════════════════════════════════════


def test_app_page_returns_html_200(page_html):
    assert page_html.startswith("<!DOCTYPE html>")
    assert "<title>跨库复习总览 · 交互版</title>" in page_html


def test_zero_external_urls(page_html):
    """核心裁判 1: 页面正文里不得出现任何 http(s) URL。"""
    assert re.findall(r'https?://[^\s"\']+', page_html) == []


def test_no_external_resource_tags(page_html):
    """零 CDN: script/link/img/iframe 一律不得引用外部资源。

    与上一条不同 —— 这条挡的是**协议相对**与**跨源相对**写法
    (`//cdn.x/y.js`, `link href` 指向别的主机), 它们不含 "http" 前缀,
    上一条的正则看不见。
    """
    for tag, attr in (("script", "src"), ("link", "href"), ("img", "src"), ("iframe", "src")):
        for m in re.finditer(rf'<{tag}\b[^>]*\b{attr}\s*=\s*["\']([^"\']*)["\']', page_html, re.I):
            pytest.fail(f"{tag}[{attr}] 引用了外部资源: {m.group(1)!r}")
    # 内联样式表以外不得有 <link>; <script> 必须是内联的 (无 src 属性)
    assert page_html.count("<script>") == 1
    assert "<script " not in page_html


def test_only_obsidian_scheme_and_relative_paths(page_html):
    """允许的绝对 scheme 只有 obsidian://; 不得出现 file:// / data: 外链等。"""
    schemes = {m.group(1).lower() for m in re.finditer(r"\b([a-z][a-z0-9+.-]*)://", page_html, re.I)}
    assert schemes <= {"obsidian"}, f"出现了非白名单 scheme: {schemes}"


def test_api_paths_injected_from_url_for_not_hardcoded(client, page_html):
    """路径来自 url_for 注入 —— 模板本体不含任何硬编码 API 路径。"""
    from app.main import app

    urls = json.loads(re.search(r"const URLS = (\{.*?\});", page_html).group(1))
    assert urls == {
        "overview": app.url_path_for("review_overview"),
        "refresh": app.url_path_for("review_overview_refresh"),
    }
    assert urls["overview"] == OVERVIEW_PATH
    assert urls["refresh"] == REFRESH_PATH
    # 篡改门: 若有人把路径写死进模板, 上面的相等断言仍会过 (值恰好一样) ——
    # 这条才是真正锁"注入"的: 模板常量里连 /api/v1 的影子都不许有。
    assert "/api/v1" not in _PAGE_TEMPLATE
    assert "review/overview" not in _PAGE_TEMPLATE


def test_api_paths_follow_mount_prefix_not_hardcoded():
    """url_for 注入的行为门 (M27 负验证抓出上一条门在**端点函数体**侧的盲区):

    把两个 router 挂到一个**不同前缀**的独立 app 上 — 若路径真从路由表
    派生, 注入值必须跟着新前缀走; 若是硬编码 (哪怕硬编码的值此刻恰好
    等于生产路径), 在换了前缀的 app 里必然对不上, 本门变红。
    """
    from fastapi import FastAPI

    from app.api.v1.endpoints.review_app import review_app_router
    from app.api.v1.endpoints.review_overview import review_overview_router

    alt = FastAPI()
    alt.include_router(review_overview_router, prefix="/alt-prefix")
    alt.include_router(review_app_router, prefix="/alt-prefix")
    c = TestClient(alt, base_url="http://127.0.0.1:8011")
    try:
        resp = c.get("/alt-prefix/overview/app")
        assert resp.status_code == 200, resp.text
        urls = json.loads(re.search(r"const URLS = (\{.*?\});", resp.text).group(1))
        assert urls == {
            "overview": "/alt-prefix/overview",
            "refresh": "/alt-prefix/overview/refresh",
        }, f"注入路径没有跟随挂载前缀 — 疑似硬编码: {urls}"
    finally:
        c.close()


def test_js_fetches_only_the_two_same_origin_endpoints(page_html):
    """JS 里所有 fetch 的目标都必须是注入的那两个常量, 不得有第三个去处。"""
    targets = re.findall(r"fetch\(\s*([^,)\s]+)", page_html)
    assert targets, "没有找到任何 fetch 调用 — 页面不会拉数据?"
    assert set(targets) == {"URLS.overview", "URLS.refresh"}


def test_auto_poll_never_posts_only_manual_button_does(page_html):
    """默认裁决②: 自动轮询绝不 POST refresh。

    判据取自结构而非措辞 —— 整页只有一处 method:"POST", 且它在
    URLS.refresh 的 fetch 里; 轮询函数 poll() 的函数体内不含 POST。
    """
    assert page_html.count('method: "POST"') == 1
    poll_body = re.search(r"async function poll\(\)\s*\{(.*?)\n\}", page_html, re.S).group(1)
    assert "POST" not in poll_body
    assert "URLS.refresh" not in poll_body
    # 唯一的 POST 出现在点击处理器里
    click_body = re.search(r'addEventListener\("click".*?\n\}\);', page_html, re.S).group(0)
    assert 'method: "POST"' in click_body


# ════════════════════════════════════════════════════════════════════
# B. 与零 JS 只读页共存 (完成条件 a / 核心裁判 3)
# ════════════════════════════════════════════════════════════════════


def test_readonly_page_still_works_both_coexist(client):
    """两页共存: 交互版 200, 零 JS 只读页同样 200 (未被替代)。"""
    assert client.get(APP_PATH).status_code == 200
    resp = client.get(PAGE_PATH)
    assert resp.status_code == 200
    assert "<script" not in resp.text  # 只读页仍然零 JS


def test_zero_js_page_source_untouched():
    """核心裁判 3: review_overview.py 的 `<script` 计数与开工基线相等。"""
    src = (_ENDPOINTS_DIR / "review_overview.py").read_text(encoding="utf-8")
    hits = [ln for ln in src.splitlines() if "<script" in ln]
    assert len(hits) == _ZERO_JS_BASELINE, f"零 JS 页被改动了: {hits}"
    # 唯一命中必须仍是那条与 JS 无关的 docstring
    assert all("python <script>" in ln for ln in hits)


def test_status_meta_and_buckets_shared_not_copied(page_html):
    """四态文案/桶位标签是 import 来的同一份 —— 不新造第二套词汇。"""
    injected_meta = json.loads(re.search(r"const STATUS_META = (\{.*?\});", page_html).group(1))
    assert injected_meta == {k: list(v) for k, v in _STATUS_META.items()}
    assert json.loads(re.search(r"const BUCKET_CN = (\{.*?\});", page_html).group(1)) == _BUCKET_CN
    assert json.loads(re.search(r"const BUCKET_ORDER = (\[.*?\]);", page_html).group(1)) == list(_BUCKET_ORDER)
    # 篡改门: 上面三条只证明"注入值正确", 挡不住"JS 里另抄一份字面量"。
    # 模板本体不许出现任何徽标文案 —— 抄一份 = 本门立刻红。
    for label, _color in _STATUS_META.values():
        assert label not in _PAGE_TEMPLATE, f"徽标文案 {label!r} 被硬编码进模板 (应只从注入常量取)"


def test_no_second_due_pipeline_in_python_module():
    """本模块不得自己算到期 —— 它只做模板注入 (无 json 读盘/无子进程)。"""
    src = (_ENDPOINTS_DIR / "review_app.py").read_text(encoding="utf-8")
    for banned in ("subprocess", "read_text(", "_collect(", "_summarize("):
        assert banned not in src, f"review_app.py 出现了它不该有的 {banned!r}"


# ════════════════════════════════════════════════════════════════════
# C/D. 渲染纯函数断言 (node --test; 完成条件 b/c)
# ════════════════════════════════════════════════════════════════════

_NODE = shutil.which("node")


def _extract_pure_js(html: str) -> str:
    """从**实际响应体**割出常量区 + 纯函数区 (不是模板副本)。"""
    const = re.search(r"// __CONSTANTS_BEGIN__\n(.*?)// __CONSTANTS_END__", html, re.S).group(1)
    pure = re.search(r"// __PURE_RENDER_BEGIN__\n(.*?)// __PURE_RENDER_END__", html, re.S).group(1)
    assert "__URLS_JSON__" not in const, "占位符没被替换 — 页面发出去的是模板本身"
    assert "document" not in pure and "fetch(" not in pure, "纯函数区混入了副作用代码"
    names = re.findall(r"^function (\w+)", pure, re.M)
    return const + "\n" + pure + "\nexport {" + ", ".join(names) + "};\n"


@pytest.fixture
def node_harness(tmp_path, page_html):
    """把真实响应里的纯函数写成 ESM 模块, 供 node --test 导入。"""
    (tmp_path / "render.mjs").write_text(_extract_pure_js(page_html), encoding="utf-8")
    return tmp_path


def _run_node(tmp_path: Path, test_src: str) -> subprocess.CompletedProcess:
    (tmp_path / "case.test.mjs").write_text(test_src, encoding="utf-8")
    return subprocess.run(
        [_NODE, "--test", "case.test.mjs"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _assert_node_green(proc: subprocess.CompletedProcess):
    assert proc.returncode == 0, f"node --test 失败:\n{proc.stdout}\n{proc.stderr}"


pytestmark_node = pytest.mark.skipif(_NODE is None, reason="node 不可用")

# ── fixture JSON: 覆盖四态 + 休息日 + W6 三字段 ────────────────────
_NOW_MS = 1_788_000_000_000  # 固定时钟 (2026-08-29T22:40:00Z 附近), 不读真实时间

_FIX_JS = r"""
const NOW = 1788000000000;
const OK_VAULT = {
  vault_id: "cs_61b", status: "ok", error: null,
  projection: {
    due_count: 3, due_new_count: 1, placeholder_backlog: 2,
    generated_at: "2026-08-29T09:05:00+08:00",
    bucket_counts: {new: 1, learning_queue: 1, due_now: 1, due_today: 0, future: 4},
    next_upcoming: {board: "堆", next_due: "2026-09-05T02:00:00Z", node: "二叉堆"},
    boards: [
      {board: "图论基础", due: 2, due_new: 1, placeholder: 1, earliest: "2026-08-28T02:00:00Z",
       nodes: [{node: "Dijkstra", due_reason: "scheduled", fsrs_due: "2026-08-28T02:00:00Z",
                bucket: "due_now", why_due: "已逾期"}]},
      {board: "哈希表", due: 1, due_new: 0, placeholder: null, earliest: "", nodes: []},
    ],
  },
};
const REST_DAY = {
  vault_id: "数学", status: "ok", error: null,
  projection: {
    due_count: 0, due_new_count: 0, placeholder_backlog: 0,
    generated_at: "2026-08-29T09:06:00+08:00", bucket_counts: null, boards: [],
    next_upcoming: {board: "线性代数", next_due: "2026-09-03T01:00:00Z", node: "特征值"},
  },
};
const STALE = {vault_id: "cs188", status: "stale", error: null,
  projection: {due_count: 5, due_new_count: 0, placeholder_backlog: 0,
    generated_at: "2026-08-27T09:05:00+08:00", bucket_counts: null, next_upcoming: null,
    boards: [{board: "搜索", due: 5, due_new: 0, placeholder: null,
              earliest: "2026-08-27T01:00:00Z", nodes: []}]}};
const NO_PROJ = {vault_id: "test-vault", status: "no_projection", error: null, projection: null};
const CORRUPT = {vault_id: "旧库", status: "corrupt",
  error: "ValueError: 仅支持 schema_version 3, 实为 2", projection: null};
"""


@pytestmark_node
def test_js_renders_four_states_and_unknown_state_defense(node_harness):
    """四态徽标各出一条 + 未知态防御 (不白屏, 原字面灰徽标)。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {renderVaultCard} from "./render.mjs";
"""
        + _FIX_JS
        + r"""
test("ok 徽标", () => {
  const h = renderVaultCard(OK_VAULT, NOW);
  assert.match(h, /今日投影/);
  assert.match(h, /#16a34a/);
  assert.match(h, /到期 <b>3<\/b>/);
});
test("stale 徽标", () => {
  const h = renderVaultCard(STALE, NOW);
  assert.match(h, /过期投影/);
  assert.ok(!h.includes("今日投影"), "stale 不许装成 ok");
});
test("no_projection 徽标 + 降级文案, 不做假深链", () => {
  const h = renderVaultCard(NO_PROJ, NOW);
  assert.match(h, /无投影/);
  assert.match(h, /该库尚无今日复习投影/);
  assert.ok(!h.includes("obsidian://open?vault=test-vault"), "无投影不该给库深链");
});
test("corrupt 徽标 + 原始错误可见", () => {
  const h = renderVaultCard(CORRUPT, NOW);
  assert.match(h, /投影损坏/);
  assert.match(h, /schema_version 3/);
  assert.ok(!h.includes("今日投影"));
});
test("未知 status 不白屏 (原字面 + 灰徽标)", () => {
  const h = renderVaultCard({vault_id: "x", status: "unregistered", error: null, projection: null}, NOW);
  assert.match(h, /unregistered/);
  assert.match(h, /#6b7280/);
  assert.ok(h.length > 50);
});
""",
    )
    _assert_node_green(proc)


@pytestmark_node
def test_js_rest_day_empty_state_matches_pick_copy(node_harness):
    """休息日空状态: 文案对齐 daily_review_pick.py:599/:564。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {renderVaultCard} from "./render.mjs";
"""
        + _FIX_JS
        + r"""
test("ok + due_count=0 → 休息日文案, 不显示到期 0 的大数字", () => {
  const h = renderVaultCard(REST_DAY, NOW);
  assert.match(h, /今日无到期节点，休息一天。/);
  assert.match(h, /按计划推进 · 最近到期 线性代数 · 2026-09-03/);
  assert.ok(!/到期 <b>0<\/b>/.test(h), "休息日不该摆一个到期 0 的大数字");
});
test("有到期时不走休息日分支", () => {
  const h = renderVaultCard(OK_VAULT, NOW);
  assert.ok(!h.includes("休息一天"));
});
test("stale 且 due_count=0 也不算休息日 (数据是旧的, 不许说今天没到期)", () => {
  const s = JSON.parse(JSON.stringify(STALE));
  s.projection.due_count = 0; s.projection.boards = [];
  const h = renderVaultCard(s, NOW);
  assert.ok(!h.includes("休息一天"), "过期投影不能冒充『今天没到期』");
});
""",
    )
    _assert_node_green(proc)


@pytestmark_node
def test_js_unavailable_banner_never_blank_screen(node_harness):
    """完成条件 b: fetch 失败/非 200/JSON 坏 → 横幅 + 保留旧数据, 不白屏。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {renderUnavailableBanner, renderPage} from "./render.mjs";
"""
        + _FIX_JS
        + r"""
test("有过成功数据 → 说明保留了哪一刻的数据", () => {
  const b = renderUnavailableBanner("HTTP 502", "14:32:05");
  assert.match(b, /后端离线\/不可用/);
  assert.match(b, /HTTP 502/);
  assert.match(b, /保留 14:32:05 的最后一次成功数据/);
});
test("从未成功过 → 诚实说没有数据 (不装成有)", () => {
  const b = renderUnavailableBanner("Failed to fetch", null);
  assert.match(b, /尚未成功获取过数据/);
  assert.ok(!b.includes("保留"));
});
test("空 vaults 列表 → 显式空态文案, 不是空白", () => {
  const h = renderPage({vaults: []}, NOW);
  assert.match(h, /未发现任何 vault/);
});
test("畸形响应 (缺 vaults 键) 不抛异常, 给空态", () => {
  assert.match(renderPage({}, NOW), /未发现任何 vault/);
  assert.match(renderPage(null, NOW), /未发现任何 vault/);
});
""",
    )
    _assert_node_green(proc)


@pytestmark_node
def test_js_w6_additive_fields_present_and_absent(node_harness):
    """W6 (CARD-G3-6b) 三字段: 有 → 渲染; 无 → 整块不出现 (各一条)。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {renderVaultCard} from "./render.mjs";
"""
        + _FIX_JS
        + r"""
function withW6() {
  const v = JSON.parse(JSON.stringify(OK_VAULT));
  v.projection.rank_manifest = {version: 1, rule: "priority desc"};
  v.projection.boards[0].why_this_board = "逾期最久 + 上次暴露最短路径缺口";
  v.projection.boards[0].estimated_minutes = 25;
  return v;
}
test("why_this_board 在场 → 板行下出现说明行", () => {
  assert.match(renderVaultCard(withW6(), NOW), /逾期最久 \+ 上次暴露最短路径缺口/);
});
test("why_this_board 缺省 → 整块不出现", () => {
  const h = renderVaultCard(OK_VAULT, NOW);
  assert.ok(!h.includes('class="why"'), "缺省时不该出现说明行容器");
});
test("estimated_minutes 在场 → 约 N 分钟标签", () => {
  assert.match(renderVaultCard(withW6(), NOW), /约 25 分钟/);
});
test("estimated_minutes 缺省 → 不出现标签", () => {
  assert.ok(!renderVaultCard(OK_VAULT, NOW).includes("分钟"));
});
test("estimated_minutes 非有限数 → 当缺省处理, 不渲染 NaN/Infinity", () => {
  const v = JSON.parse(JSON.stringify(OK_VAULT));
  v.projection.boards[0].estimated_minutes = "25";  // 字符串不是有限数
  const h = renderVaultCard(v, NOW);
  assert.ok(!h.includes("分钟"));
  assert.ok(!h.includes("NaN") && !h.includes("Infinity"));
});
test("rank_manifest 在场 → 底部小注", () => {
  assert.match(renderVaultCard(withW6(), NOW), /rank_manifest/);
});
test("rank_manifest 缺省 → 整块不出现", () => {
  assert.ok(!renderVaultCard(OK_VAULT, NOW).includes("rank_manifest"));
});
""",
    )
    _assert_node_green(proc)


@pytestmark_node
def test_js_poll_interval_clamped_and_visibility_pauses(node_harness):
    """完成条件 c: 轮询周期 clamp(next_due−now, 5s, 60s) + 隐藏暂停。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {computePollDelayMs, visibilityAction} from "./render.mjs";
"""
        + _FIX_JS
        + r"""
function at(secondsFromNow) {  // 构造一个 now+N 秒的 next_due 投影
  const iso = new Date(NOW + secondsFromNow * 1000).toISOString().replace(/\.\d{3}Z$/, "Z");
  return {vaults: [{vault_id: "v", status: "ok",
    projection: {next_upcoming: {board: "b", next_due: iso, node: "n"}}}]};
}
test("6 秒后到期 → 6 秒后再问 (区间内原样)", () => {
  assert.equal(computePollDelayMs(at(6), NOW), 6000);
});
test("2 秒后到期 → 夹到下限 5 秒 (不打爆后端)", () => {
  assert.equal(computePollDelayMs(at(2), NOW), 5000);
});
test("1 小时后到期 → 夹到上限 60 秒 (不睡死)", () => {
  assert.equal(computePollDelayMs(at(3600), NOW), 60000);
});
test("已过期的 next_due → 回落上限, 不空转", () => {
  assert.equal(computePollDelayMs(at(-100), NOW), 60000);
});
test("没有任何 upcoming → 回落上限", () => {
  assert.equal(computePollDelayMs({vaults: [NO_PROJ, CORRUPT]}, NOW), 60000);
  assert.equal(computePollDelayMs({vaults: []}, NOW), 60000);
  assert.equal(computePollDelayMs(null, NOW), 60000);
});
test("多库取最近的那个未来时刻", () => {
  const data = {vaults: [at(50).vaults[0], at(8).vaults[0], at(-5).vaults[0]]};
  assert.equal(computePollDelayMs(data, NOW), 8000);
});
test("畸形 next_due 不炸, 按无排期处理", () => {
  const bad = {vaults: [{vault_id: "v", status: "ok",
    projection: {next_upcoming: {board: "b", next_due: "20260901", node: "n"}}}]};
  assert.equal(computePollDelayMs(bad, NOW), 60000);
});
test("页面隐藏 → 取消排程且不拉取", () => {
  assert.deepEqual(visibilityAction(true), {cancelTimer: true, pollNow: false});
});
test("回到前台 → 取消旧排程并立即拉一轮", () => {
  assert.deepEqual(visibilityAction(false), {cancelTimer: true, pollNow: true});
});
""",
    )
    _assert_node_green(proc)


@pytestmark_node
def test_js_new_due_card_appears_after_next_due_passes(node_harness):
    """完成条件 c 的行为链: next_due=now+6s → 6 秒后那一轮的响应里出现新到期卡。

    壳的职责分两半, 这里各锁一半:
      ① 节奏 —— computePollDelayMs 让下一次 GET 恰好落在 6 秒后;
      ② 呈现 —— 那一轮服务端返回的新 JSON (生产器已重算) 渲染出该板。
    到期与否由投影裁定, 页面不参与判定 —— 所以第二半喂的是"服务端已经改了
    的数据", 而不是让 JS 自己把未到期算成到期。
    """
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {computePollDelayMs, renderPage} from "./render.mjs";
"""
        + _FIX_JS
        + r"""
const dueAt = new Date(NOW + 6000).toISOString().replace(/\.\d{3}Z$/, "Z");
// 第一轮: 该板未到期 (休息日), next_upcoming 指向 6 秒后
const before = {vaults: [{vault_id: "v", status: "ok", error: null, projection: {
  due_count: 0, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
  generated_at: "2026-08-29T09:05:00+08:00", boards: [],
  next_upcoming: {board: "堆与优先队列", next_due: dueAt, node: "二叉堆"}}}]};
// 第二轮 (6 秒后, 生产器已重算): 同一板成为到期卡
const after = {vaults: [{vault_id: "v", status: "ok", error: null, projection: {
  due_count: 1, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
  generated_at: "2026-08-29T09:05:06+08:00", next_upcoming: null,
  boards: [{board: "堆与优先队列", due: 1, due_new: 0, placeholder: null,
            earliest: dueAt, nodes: [{node: "二叉堆", due_reason: "scheduled",
            fsrs_due: dueAt, bucket: "due_now", why_due: "排期到点"}]}]}}]};

test("① 下一次 GET 排在 next_due 时刻 (6 秒)", () => {
  assert.equal(computePollDelayMs(before, NOW), 6000);
});
test("② 到点前那一轮: 休息日, 页面没有该到期卡", () => {
  const h = renderPage(before, NOW);
  assert.match(h, /休息一天/);
  assert.ok(!h.includes("二叉堆"), "还没到期就不该出现节点");
});
test("③ 到点后那一轮: 到期卡与节点明细出现", () => {
  const h = renderPage(after, NOW + 6000);
  assert.match(h, /到期 <b>1<\/b>/);
  assert.match(h, /堆与优先队列/);
  assert.match(h, /二叉堆/);
  assert.ok(!h.includes("休息一天"));
});
""",
    )
    _assert_node_green(proc)


@pytestmark_node
def test_js_refresh_result_visible_and_never_fakes_success(node_harness):
    """完成条件 c: 手动刷新的 rebuild_count / 去抖态 / 失败在页面可见。

    去抖与失败**都不许长得像成功** —— 那正是零 JS 页 round-3 修过的
    「与成功逐字节同形的 303」的浏览器版本。
    """
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {renderRefreshResult} from "./render.mjs";
test("真重建 → 显示本进程重建次数", () => {
  const h = renderRefreshResult(200, {rebuilt: true, reason: "rebuilt", rebuild_count: 3});
  assert.match(h, /已重建/);
  assert.match(h, /第 3 次/);
  assert.match(h, /rnote ok/);
});
test("去抖 → 明说本次没重算 + 还要等多久", () => {
  const h = renderRefreshResult(200, {rebuilt: false, reason: "debounced",
    debounce_ttl_seconds: 10, retry_after_seconds: 6.2});
  assert.match(h, /10 秒内已重建过，本次未重算/);
  assert.match(h, /约 7 秒后可再试/);
  assert.match(h, /rnote warn/);
  assert.ok(!h.includes("已重建（"), "去抖不许长得像成功");
});
test("in_progress → 说清没重复启动", () => {
  const h = renderRefreshResult(200, {rebuilt: false, reason: "in_progress"});
  assert.match(h, /已有一次重建在跑/);
  assert.ok(!/rnote ok/.test(h));
});
test("503 → 显示状态码与后端给的原因", () => {
  const h = renderRefreshResult(503, {detail: {error: "pick_missing", message: "生产器脚本不可用"}});
  assert.match(h, /HTTP 503/);
  assert.match(h, /生产器脚本不可用/);
  assert.match(h, /rnote err/);
});
test("403 同源门 → 原样呈现, 不吞", () => {
  const h = renderRefreshResult(403, {detail: {error: "cross_site_blocked", message: "跨站请求被拒"}});
  assert.match(h, /HTTP 403/);
  assert.match(h, /跨站请求被拒/);
});
test("网络错误 (status 0) → 明确说网络失败", () => {
  assert.match(renderRefreshResult(0, {detail: "Failed to fetch"}), /网络错误/);
});
test("响应体不是 JSON (payload=null) 也不白, 给状态码", () => {
  assert.match(renderRefreshResult(500, null), /HTTP 500/);
});
""",
    )
    _assert_node_green(proc)


@pytestmark_node
def test_js_shows_authoritative_due_count_never_recomputes(node_harness):
    """完成条件 (硬边界): JS 内不实现任何 due 算法 —— 只消费投影。

    行为门 (非否定断言): 喂一份 due_count=7 而 boards 明细只有 2 的投影
    (服务端 _summarize 允许这种并陈: stats 是权威计数, 明细可因脏行降级),
    页面必须显示 7。若 JS 私下按明细重算, 会显示 2, 本门变红。
    """
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {renderVaultCard} from "./render.mjs";
"""
        + _FIX_JS
        + r"""
test("显示服务端权威 due_count, 不按明细重加", () => {
  const v = JSON.parse(JSON.stringify(OK_VAULT));
  v.projection.due_count = 7;   // 权威计数
  // 明细仍是 2+1=3 —— 若 JS 重算就会显示 3
  const h = renderVaultCard(v, NOW);
  assert.match(h, /到期 <b>7<\/b>/);
  assert.ok(!/到期 <b>3<\/b>/.test(h), "页面重算了到期数 — 违反『只消费投影』");
});
test("板行到期数直接取 boards[].due, 不按 nodes 长度重数", () => {
  const v = JSON.parse(JSON.stringify(OK_VAULT));
  v.projection.boards[0].due = 9;   // 明细只有 1 个 node
  assert.match(renderVaultCard(v, NOW), /<b>9<\/b>/);
});
test("休息日判定读 due_count, 不读 boards 是否为空", () => {
  const v = JSON.parse(JSON.stringify(OK_VAULT));
  v.projection.boards = [];        // 明细空, 但权威计数非零
  const h = renderVaultCard(v, NOW);
  assert.ok(!h.includes("休息一天"), "权威计数非零时不许说休息");
  assert.match(h, /到期 <b>3<\/b>/);
});
""",
    )
    _assert_node_green(proc)


@pytestmark_node
def test_js_escapes_hostile_names_and_encodes_deep_links(node_harness):
    """XSS / 深链编码: 库名、板名、节点名、错误串都来自外部 JSON。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {renderVaultCard, boardLink, nodeLink} from "./render.mjs";
test("恶意库名不产生可执行标签", () => {
  const h = renderVaultCard({vault_id: '<img src=x onerror=alert(1)>', status: "corrupt",
    error: '</script><script>alert(2)</script>', projection: null}, 0);
  assert.ok(!h.includes("<img"), "库名未转义");
  assert.ok(!h.includes("<script"), "错误串未转义");
  assert.match(h, /&lt;img/);
});
test("板名里的引号不能撑破 href 属性", () => {
  const h = renderVaultCard({vault_id: "v", status: "ok", error: null, projection: {
    due_count: 1, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
    generated_at: "g", next_upcoming: null,
    boards: [{board: '" onmouseover="alert(1)', due: 1, due_new: 0,
              placeholder: null, earliest: "", nodes: []}]}}, 0);
  assert.ok(!h.includes('onmouseover="alert'), "属性被撑破");
});
test("深链把 / & # ? 一并编码 (与服务端 quote(safe='') 同语义)", () => {
  const l = boardLink("v/a", "b&c#d?e");
  assert.ok(l.includes("v%2Fa"));
  assert.ok(l.includes("%26") && l.includes("%23") && l.includes("%3F"));
  assert.ok(!l.slice("obsidian://open?vault=".length).includes("/"));
  assert.ok(nodeLink("v", "x/y").includes("%2Fy"));
});
""",
    )
    _assert_node_green(proc)


@pytestmark_node
def test_js_humanize_due_matches_server_side_wording(node_harness):
    """同源锁: JS 的到期人话与服务端 _humanize_due 逐条相同。

    期望值由**服务端函数当场算出**再喂进 node —— 哪天两页文案分家
    (或时区口径漂移), 本门先红。
    """
    from datetime import datetime, timedelta, timezone

    now_utc = datetime.fromtimestamp(_NOW_MS / 1000, tz=timezone.utc)
    cases = []
    for label, ts in (
        ("空串=现在", ""),
        ("逾期2天", (now_utc - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("今天", now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("明天", (now_utc + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("5天后", (now_utc + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("同年月日", (now_utc + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("跨年", (now_utc + timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("畸形", "20260901"),
    ):
        expected, _color = _humanize_due(ts, now_utc)
        cases.append({"label": label, "ts": ts, "expected": expected})
    # None 走 "—" 分支 (板级无数据)
    cases.append({"label": "无数据", "ts": None, "expected": _humanize_due(None, now_utc)[0]})

    proc = _run_node(
        node_harness,
        "import test from 'node:test';\nimport assert from 'node:assert/strict';\n"
        "import {humanizeDue} from './render.mjs';\n"
        f"const NOW = {_NOW_MS};\nconst CASES = {json.dumps(cases, ensure_ascii=False)};\n"
        r"""
for (const c of CASES) {
  test("与服务端一致: " + c.label, () => {
    assert.equal(humanizeDue(c.ts, NOW).text, c.expected);
  });
}
""",
    )
    _assert_node_green(proc)
