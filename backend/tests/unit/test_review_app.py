"""交互复习壳 (CARD-G6-2, BATCH-2026-09-01-第八批; Codex round-1 整改后形态)。

四类锁定:
  A. 单文件自足 —— 零外部 URL / 零 CDN / 零外部资源标签; API 路径来自
     url_for 注入而非硬编码 (换前缀挂载的行为门); JS 只 fetch 同源两端点。
  B. 与零 JS 只读页共存 —— 两页同时 200; review_overview.py 的 `<script`
     计数与开工基线 (1, 唯一命中是 :1286 docstring「python <script>」) 相等。
  C. 渲染 + 接线 (node --test) —— 四态徽标 / unavailable 不白屏 / 休息日
     空状态 / W6 三字段有无各一 / 轮询 clamp / 隐藏暂停 / XSS 转义 /
     刷新反馈持久化与在飞防抖。
     ⚠ 被测 JS 是**响应里的整个 <script> 原文**, 在受控沙箱 (stub
     document/fetch/timer) 中**直接执行**后从沙箱作用域导出断言 ——
     没有任何按注释标记割取代码的通道, 「注释里藏一份好代码骗提取器、
     浏览器执行另一份」的攻击面不成立 (Codex round-1 HIGH-3); 轮询/点击
     接线也在同一沙箱里以假事件驱动断言。
  D. 不重算到期 —— 喂一份 due_count 与 boards 明细刻意不一致的投影,
     页面必须显示服务端权威 due_count; JS 若偷偷重算, 本门变红。

fail-closed (Codex round-1 HIGH-2): node 不可用时 node_harness fixture
直接 pytest.fail —— 本文件的 JS 门**不允许静默 skip 假绿**, 因此本文件
不存在任何 skip 路径 (裁判命令锁定 skipped == 0 由结构保证)。

真实 HTTP 响应 + 真 node 进程, 无 mock。TestClient 一律裸构造 (不带 with):
起 lifespan 会连 7691 (第七批 F-3)。
"""

import ast
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

_NODE = shutil.which("node") or ""  # 空串 = 不可用 (node_harness 里 fail-closed)


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
    # round-2 M5 补口: 不含 "//" 的资源型 scheme (上一条的正则看不见)
    for bad in ("data:text", "javascript:", "blob:", "file:"):
        assert bad not in page_html, f"出现了非白名单资源协议: {bad}"
    # 协议相对 <a href="//host/..."> (无 scheme 前缀, 上面两道都看不见)
    assert not re.search(r'<a\s[^>]*href\s*=\s*["\']//', page_html), "协议相对链接"
    # CSS url() 资源 — 本页内联样式表零外链, 出现即是回归
    assert "url(" not in page_html, "样式表出现 url() 资源引用"


def test_only_obsidian_scheme_and_relative_paths(page_html):
    """允许的绝对 scheme 只有 obsidian://; 不得出现 file:// / data: 外链等。"""
    schemes = {m.group(1).lower() for m in re.finditer(r"\b([a-z][a-z0-9+.-]*)://", page_html, re.I)}
    assert schemes <= {"obsidian"}, f"出现了非白名单 scheme: {schemes}"


def test_api_paths_injected_from_url_for_not_hardcoded(client, page_html):
    """路径来自 url_for 注入 —— 模板本体不含任何硬编码 API 路径。"""
    from app.main import app

    urls = json.loads(_group(r"const URLS = (\{.*?\});", page_html))
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
        urls = json.loads(_group(r"const URLS = (\{.*?\});", resp.text))
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

    判据取自结构而非措辞 —— 整页只有一处 method:"POST", 且它在手动刷新
    处理器 onRefreshClick 里; 轮询函数 poll() 的函数体内不含 POST。
    """
    assert page_html.count('method: "POST"') == 1
    poll_body = _group(r"async function poll\(\)\s*\{(.*?)\n\}", page_html, re.S)
    assert "POST" not in poll_body
    assert "URLS.refresh" not in poll_body
    click_body = _group(r"async function onRefreshClick\(ev\)\s*\{(.*?)\n\}", page_html, re.S)
    assert 'method: "POST"' in click_body
    # 点击处理器确实被接到 cards 容器上 (不是只有个没人调用的函数)
    assert 'addEventListener("click", onRefreshClick)' in page_html


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
    injected_meta = json.loads(_group(r"const STATUS_META = (\{.*?\});", page_html))
    assert injected_meta == {k: list(v) for k, v in _STATUS_META.items()}
    assert json.loads(_group(r"const BUCKET_CN = (\{.*?\});", page_html)) == _BUCKET_CN
    assert json.loads(_group(r"const BUCKET_ORDER = (\[.*?\]);", page_html)) == list(_BUCKET_ORDER)
    # 篡改门: 上面三条只证明"注入值正确", 挡不住"JS 里另抄一份字面量"。
    # 模板本体不许出现任何徽标文案 —— 抄一份 = 本门立刻红。
    for label, _color in _STATUS_META.values():
        assert label not in _PAGE_TEMPLATE, f"徽标文案 {label!r} 被硬编码进模板 (应只从注入常量取)"


def test_no_second_due_pipeline_in_python_module():
    """字符串黑名单快门 (便宜的一层) + AST 结构门 (下一道, 不可被措辞绕过)。"""
    src = (_ENDPOINTS_DIR / "review_app.py").read_text(encoding="utf-8")
    for banned in ("subprocess", "read_text(", "_collect(", "_summarize("):
        assert banned not in src, f"review_app.py 出现了它不该有的 {banned!r}"


#: ── AST 结构门的白名单 (round-1 HIGH-4 / round-2 HIGH-4 / round-4 HIGH-4b) ──
#: 三张白名单是**正向合约**: 任何新调用形态都必须先有意识地改这里, 代码评审
#: 必然看见。CARD-G6-2b 把它们从测试函数体提到模块级 —— 检查器要被探针矩阵
#: (test_ast_gate_rejects_shadowing_forms) 复用, 白名单值逐字不变、不放宽。
_ALLOWED_IMPORTS = {
    "__future__.annotations",
    "json",
    "fastapi.APIRouter",
    "fastapi.Request",
    "fastapi.responses.HTMLResponse",
    "app.api.v1.endpoints.review_overview._BUCKET_CN",
    "app.api.v1.endpoints.review_overview._BUCKET_ORDER",
    "app.api.v1.endpoints.review_overview._STATUS_META",
}
_ALLOWED_CALL_NAMES = {"APIRouter", "list", "_js_json", "HTMLResponse"}
_ALLOWED_CALL_ATTRS = {"get", "replace", "url_for", "dumps", "items"}
#: Attribute 调用允许的接收者 (unparse 基名) — 只查尾部方法名不够,
#: 任意对象都能挂同名方法 (round-3 HIGH-4b 实证绕过面)
_ALLOWED_RECEIVERS = {"json", "request", "review_app_router", "_STATUS_META", "_PAGE_TEMPLATE"}
#: 任何形态的重绑定/遮蔽都禁的名字 = 调用名 ∪ 接收者 ∪ 模块级单例
#: (round-4 HIGH-4b: 接收者名可被 `json = evil` 重绑定, 白名单就失效了)
_BANNED_REBINDS = (
    _ALLOWED_CALL_NAMES
    | _ALLOWED_RECEIVERS
    | {
        "_BUCKET_CN",
        "_BUCKET_ORDER",
        "review_overview_router",
    }
)
#: 本模块**自有**的模块级定义名 —— 它们占着受保护名, 但那是这些名字的
#: **定义点**而不是遮蔽。反过来说: 受保护名里**只有这三个**允许在模块级被
#: 定义, 其余 (import 来的 json / 内建的 list / 形参 request / 从
#: review_overview 拿来的常量 …) 在本模块里已经有绑定了, 任何再绑定都是覆盖。
#: 豁免的四重限定, 缺一条就等于开了个后门 (round-5 反例集实证):
#:   1. 只在模块级 —— 函数/类体内再 `def _js_json` 是遮蔽;
#:   2. 只对 `def` 与"字面量/白名单调用"的赋值 —— `class _js_json: pass` 会把
#:      函数换成类, 于是 `_js_json(urls)` 变成构造实例;
#:   3. 每个名字**至多一个定义点** —— 第二个会静默顶掉第一个, 而两者都被豁免;
#:   4. 只对这张表里的名字 —— 否则 `json = 0` / `HTMLResponse = APIRouter()`
#:      这种"看起来像定义"的赋值会把 import 来的绑定整个换掉 (round-5 BLOCKER-2)。
#: 这不是第四张调用白名单 —— 往这里加名字 = 承认模块多了一个自有模块级定义。
_OWN_MODULE_DEFINITIONS = {"_js_json", "_PAGE_TEMPLATE", "review_app_router"}
#: PEP 695 节点 (3.12+)。低版本上取不到时 `isinstance(x, ())` 恒 False,
#: 而低版本也没有对应语法 —— 那正是该有的语义, 门不会因此炸。
_TYPE_ALIAS_NODES = tuple(c for c in (getattr(ast, "TypeAlias", None),) if c is not None)
_TYPE_PARAM_NODES = tuple(
    c for c in (getattr(ast, n, None) for n in ("TypeVar", "ParamSpec", "TypeVarTuple")) if c is not None
)


def _root_name(node: ast.AST) -> str:
    """`json.__dict__["dumps"]` → `"json"`; 取不到根 Name 时返回空串。

    受保护对象的**内部**被改写 (属性 / 下标) 与"重绑定这个名字"是两回事:
    前者一个 Store 位置的 Name 都不产生, 名字检查一个字都看不见, 但改掉的是
    同一个对象 (round-5 BLOCKER-3)。判据只能是"这条写路径的根是谁"。
    """
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else ""


def _assert_module_closed(src: str) -> None:
    """AST 结构门本体 (吃源码文本, 不碰磁盘) —— 违规即 fail/AssertionError。

    与被测模块解耦是为了让探针矩阵能喂「真实源码 + 一段注入片段」的内存
    字符串: 门补的每一条规则都必须有一个「不补就漏、补了就抓」的证据,
    而不是靠肉眼相信枚举完整 (CARD-G6-2b R2/R3 + round-5 反例集)。
    """
    tree = ast.parse(src)
    collected: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                # alias 禁令 (round-4 HIGH-4b): `import x as list` 会把白名单调用名
                # 绑到别的模块上, 拼写检查全部空转 — 本模块不允许任何 asname
                if a.asname is not None:
                    pytest.fail(f"import alias 禁止 (asname={a.asname!r}) — alias 可遮蔽白名单调用名")
                collected.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            # 相对导入禁令 (round-5 反例集): `from . import json` 收进 collected 的
            # 也是字符串 "json", 与标准库那条白名单条目**不可分辨** —— 放它过去等于
            # 让同目录的 json.py 冒充标准库 json。本模块只用绝对导入。
            if node.level:
                pytest.fail(
                    f"相对导入禁止 (from {'.' * node.level}{node.module or ''} import …) — "
                    "相对模块名与白名单里的绝对模块名不可分辨"
                )
            mod = node.module or ""
            for a in node.names:
                if a.asname is not None:
                    pytest.fail(f"import alias 禁止 (asname={a.asname!r}) — alias 可遮蔽白名单调用名")
                collected.add(f"{mod}.{a.name}" if mod else a.name)
    banned = collected - _ALLOWED_IMPORTS
    assert not banned, f"出现白名单外的 import: {sorted(banned)} — 第二套管道的载体"

    def _flag_rebind(name: str, where: str):
        if name in _BANNED_REBINDS:
            pytest.fail(f"受保护名 {name!r} 被{where} — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)")

    def _flag_targets(target: ast.AST, where: str):
        """绑定目标里递归找**写位置**: Name 看名字, Attribute/Subscript 看根名。

        - Name: 只认 Store / Del 上下文 —— 目标里也会出现**读取**位置的 Name,
          例如 `cache[json] = value` 的下标 `json` 是 Load, 它没有绑定任何东西
          (round-5 反例集 false-positive-load; ctx 完备性实证见
          evidence-g62b/ctx-store-completeness.txt)。
        - Attribute / Subscript: 写的是**别的对象的内部**, 一个 Store 位置的 Name
          都不产生。根名受保护 = 改的是受保护对象本体 (`json.dumps = …`、
          `json.__dict__["dumps"] = …`、`_STATUS_META["ok"] = …`); 根名不受保护
          则是普通对象 (`cache[k] = v`、`obj.value = 1`), 放行 (round-5 BLOCKER-3
          与登记级误伤同时收口)。
        """
        for sub in ast.walk(target):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, (ast.Store, ast.Del)):
                _flag_rebind(sub.id, where)
            elif isinstance(sub, (ast.Attribute, ast.Subscript)) and isinstance(sub.ctx, (ast.Store, ast.Del)):
                root = _root_name(sub)
                if root in _BANNED_REBINDS:
                    pytest.fail(
                        f"受保护对象 {root!r} 的内部被写 ({ast.unparse(sub)}) — "
                        "改的是同一个对象, 名字层的拼写检查看不见"
                    )

    #: 享受了"模块级定义豁免"的名字 → 次数。同一个受保护名出现两个定义点时,
    #: 后者静默顶掉前者, 而两者都各自被豁免 —— 计数是这条缝的唯一堵法。
    definitions: dict[str, int] = {}

    # 作用域根的节点集合 — 保护名在函数/类体内被绑定 = 一律红 (参数遮蔽/局部
    # 重绑定); 模块级定义才是合法形态。`sub is not node`: 作用域根自身不算
    # 「在自己里面」, 否则模块级 def 会被当成嵌套 def, 定义豁免永远够不着。
    in_function: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            for sub in ast.walk(node):
                if sub is not node:
                    in_function.add(id(sub))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            # 取别名禁令: `alias = json` 之后 `alias.dumps = …` 改的是受保护模块
            # 本体, 而全程没碰过任何保护名 —— 两步各封一半, 这里封前半步。
            if isinstance(node.value, ast.Name) and node.value.id in _BANNED_REBINDS:
                pytest.fail(f"受保护名 {node.value.id!r} 被取别名 — 别名不受拼写检查约束")
            # 模块级定义豁免: 只对 _OWN_MODULE_DEFINITIONS 里的名字, 且右侧是
            # 字面量 (模板字符串) 或白名单调用 (`review_app_router = APIRouter()`)。
            # AugAssign 永不豁免 —— 读-改-写修改的是既有定义, 不是在定义什么。
            value_is_definition = not isinstance(node, ast.AugAssign) and (
                isinstance(node.value, ast.Constant)
                or (
                    isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id in _ALLOWED_CALL_NAMES
                )
            )
            module_level = id(node) not in in_function
            for tgt in targets:
                exempt = (
                    module_level
                    and value_is_definition
                    and isinstance(tgt, ast.Name)
                    and tgt.id in _OWN_MODULE_DEFINITIONS
                )
                if exempt:
                    definitions[tgt.id] = definitions.get(tgt.id, 0) + 1
                else:
                    _flag_targets(tgt, "重绑定")
        # 赋值语句**之外**的绑定形态 —— 下面每一种都能在不触发任何 Assign 节点
        # 的前提下把保护名绑到别的对象上 (逐类各有一个探针)。
        if isinstance(node, (ast.For, ast.AsyncFor)):
            _flag_targets(node.target, "for 目标绑定")
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is not None:
                    _flag_targets(item.optional_vars, "with…as 绑定")
        if isinstance(node, ast.Delete):
            # `del json` 解绑之后, 后续调用点全部 NameError —— 不是静默绕过,
            # 但它同样让"这个名字指向什么"不再由本文件的其余规则决定。
            for tgt in node.targets:
                _flag_targets(tgt, "del 解绑")
        if isinstance(node, ast.ExceptHandler) and node.name:
            _flag_rebind(node.name, "except…as 绑定")
        if isinstance(node, ast.NamedExpr):
            _flag_targets(node.target, "海象绑定")
        if isinstance(node, ast.comprehension):
            _flag_targets(node.target, "推导式目标绑定")
        if isinstance(node, _TYPE_ALIAS_NODES):
            _flag_targets(node.name, "type 别名绑定")
        if isinstance(node, _TYPE_PARAM_NODES):
            _flag_rebind(node.name, "type 形参遮蔽")
        if isinstance(node, ast.MatchAs) and node.name:
            _flag_rebind(node.name, "match 捕获绑定")
        if isinstance(node, ast.MatchStar) and node.name:
            _flag_rebind(node.name, "match 星号捕获绑定")
        if isinstance(node, ast.MatchMapping) and node.rest:
            _flag_rebind(node.rest, "match **rest 绑定")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for dec in node.decorator_list:
                # 无括号装饰器 = **导入期的隐式调用**, 下面那条 ast.Call 检查看不见它
                # (`@print` 一个 Call 节点都不产生)。形态必须逐类穷举: 下标取内建
                # (`@__builtins__["print"]`) 与 lambda 包裹 (`@(lambda fn: fn)`)
                # 既不是 Name 也不是 Attribute (round-5 BLOCKER-4)。
                if isinstance(dec, ast.Call):
                    continue  # 由下面的 ast.Call 正向合约覆盖
                if isinstance(dec, ast.Name):
                    assert dec.id in _ALLOWED_CALL_NAMES, f"白名单外装饰器 @{dec.id} — 无括号装饰器是导入期的隐式调用"
                elif isinstance(dec, ast.Attribute):
                    assert dec.attr in _ALLOWED_CALL_ATTRS, (
                        f"白名单外装饰器方法 @….{dec.attr} — 无括号装饰器是导入期的隐式调用"
                    )
                    dec_recv = _root_name(dec.value)
                    assert dec_recv in _ALLOWED_RECEIVERS, (
                        f"非白名单装饰器接收者 @{dec_recv}.{dec.attr} — 只查方法名挡不住任意对象"
                    )
                else:
                    pytest.fail(
                        f"非白名单装饰器形态: {type(dec).__name__} — 下标取内建/lambda 包裹 都是导入期隐式调用的载体"
                    )
            # def/class 名也是绑定: `def list(...)` / `class json: ...` 同样
            # 把白名单调用名/接收者绑到别的东西上, 且一个 Assign 节点都不留。
            # 豁免四重限定见 _OWN_MODULE_DEFINITIONS 的注释。
            is_own_def = (
                node.name in _OWN_MODULE_DEFINITIONS
                and isinstance(node, ast.FunctionDef)
                and id(node) not in in_function
            )
            if is_own_def:
                definitions[node.name] = definitions.get(node.name, 0) + 1
            else:
                _flag_rebind(node.name, "def/class 名遮蔽")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            # Lambda 与 FunctionDef 走**同一条**取参路径 —— 原先 Lambda 只取
            # node.args.args, posonlyargs/kwonlyargs/vararg/kwarg 四类都能遮蔽
            a = node.args
            arg_sets = [
                a.args + a.posonlyargs + a.kwonlyargs,
                [x for x in (a.vararg, a.kwarg) if x],
            ]  # round-4: 补 *args/**kwargs
            for group in arg_sets:
                for arg in group:
                    arg_name = getattr(arg, "arg", getattr(arg, "id", ""))
                    # "request" 豁免: FastAPI 依赖注入的形参就是接收者本体
                    # (request.url_for 的合法来源) —— 但必须**真的**被注解成
                    # Request: 不带注解的 `request` 是普通查询参数, 拿到的是
                    # 字符串, `.url_for` 根本不存在 (round-5 BLOCKER-5)。
                    annotated_request = (
                        arg_name == "request"
                        and _root_name(getattr(arg, "annotation", None) or ast.Constant(value=None)) == "Request"
                    )
                    if not annotated_request:
                        _flag_rebind(arg_name, "参数遮蔽")
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                assert f.id in _ALLOWED_CALL_NAMES, f"白名单外调用 {f.id}() — 模板注入之外的第二种行为"
            elif isinstance(f, ast.Attribute):
                assert f.attr in _ALLOWED_CALL_ATTRS, f"白名单外方法 .{f.attr}() — 模板注入之外的第二种行为"
                recv_base = ast.unparse(f.value).split("(", 1)[0]
                assert recv_base in _ALLOWED_RECEIVERS or isinstance(f.value, ast.Call), (
                    f"非白名单接收者 {recv_base}.{f.attr}() — 只查方法名挡不住任意对象挂同名方法"
                )
            else:
                pytest.fail(
                    f"非白名单调用形态: {type(f).__name__} — 动态派发/下标取内建/lambda "
                    f"包裹都是第二套管道的载体 (round-2 HIGH-4 实证绕过面)"
                )

    dupes = sorted(n for n, c in definitions.items() if c > 1)
    assert not dupes, f"受保护名有多个模块级定义点: {dupes} — 后一个静默顶掉前一个, 而两个都各自享受了定义豁免"


def _review_app_src() -> str:
    return (_ENDPOINTS_DIR / "review_app.py").read_text(encoding="utf-8")


def test_review_app_module_imports_are_closed():
    """AST 结构门 (round-1 HIGH-4 新增, round-2 HIGH-4 升级为正向合约):
    本模块只允许「模板注入」这一种依赖形态。

    反面黑名单可被换形绕过 (round-2 实证: `__builtins__["open"](...)` 不新增
    import 也不命中任何名字/属性黑名单)。所以调用侧改成**正向合约**——
    枚举全部允许的调用形态, 任何新调用 (含 getattr/下标取内建/lambda 包裹/
    任何新函数) 都必须先有意识地改这份白名单, 代码评审必然看见。
    """
    _assert_module_closed(_review_app_src())


#: 探针矩阵 (CARD-G6-2b R2/R3 + round-5 反例集): `label → (注入片段, 拒因关键词)`。
#: 每条 = 一段**注入生产源码尾部**的合法 Python, 它踩且只踩被测的那一条规则
#: (片段里的调用全部取自白名单, 否则红的会是「白名单外调用」而不是被测规则 ——
#: 那样探针就分辨不出门补没补)。拒因关键词是**失败身份**的判据: 只断言「被拒了」
#: 会把「因为别的规则而红」也算成绿。只在内存里拼字符串: 不落盘、不改生产文件。
#: 补门前逐条 PASS (门瞎) / 补门后逐条 REJECT 的红绿矩阵见
#: _bmad-output/审查/evidence-g62b/probe-matrix.md。
_AST_PROBES = {
    # ── R3: 赋值语句之外的绑定形态 ──
    "for-目标": ("for json in ():\n    pass\n", "受保护名"),
    "async-for-目标": ("async def _probe_af():\n    async for json in _js_json(1):\n        pass\n", "受保护名"),
    "with-as": ("with _js_json(1) as json:\n    pass\n", "受保护名"),
    "async-with-as": ("async def _probe_aw():\n    async with _js_json(1) as json:\n        pass\n", "受保护名"),
    "except-as": ("try:\n    pass\nexcept Exception as json:\n    pass\n", "受保护名"),
    "海象": ("if (json := 1):\n    pass\n", "受保护名"),
    "推导式目标": ("_probe_comp = [json for json in ()]\n", "受保护名"),
    "def-名遮蔽": ("def json():\n    pass\n", "被def/class 名遮蔽"),
    "class-名遮蔽": ("class list:\n    pass\n", "被def/class 名遮蔽"),
    "嵌套-自有定义遮蔽": (
        "def _probe_nested():\n    def _js_json(x):\n        return x\n    return _js_json\n",
        "被def/class 名遮蔽",
    ),
    "match-捕获": ("match _PAGE_TEMPLATE:\n    case json:\n        pass\n", "受保护名"),
    "match-星号": ("match _PAGE_TEMPLATE:\n    case [*json]:\n        pass\n", "受保护名"),
    "match-rest": ('match _PAGE_TEMPLATE:\n    case {"k": _, **json}:\n        pass\n', "受保护名"),
    # ── R2: Lambda 与 FunctionDef 的参数对称 ──
    "lambda-posonly": ("_probe_l1 = lambda json, /: json\n", "参数遮蔽"),
    "lambda-kwonly": ("_probe_l2 = lambda *, json: json\n", "参数遮蔽"),
    "lambda-vararg": ("_probe_l3 = lambda *json: json\n", "参数遮蔽"),
    "lambda-kwarg": ("_probe_l4 = lambda **json: json\n", "参数遮蔽"),
    # ── round-5 反例集 (从断连那一轮的 stderr 里抢救出的用例, 逐字还原) ──
    # 这 8 条在**本卡第一版**的门下全部放行 —— 补第一版时我以为"绑定形态"补齐了,
    # 其实缺的是另外几个维度: 定义点唯一性、导入的相对性、装饰器的隐式调用、
    # 属性赋值这条完全不碰保护名的通路。
    "重复定义-def": ("def _js_json(value):\n    return json.dumps(value)\n", "多个模块级定义点"),
    "重复定义-class": ("class _js_json:\n    pass\n", "被def/class 名遮蔽"),
    "重复定义-模板": ('_PAGE_TEMPLATE = "wrong"\n', "多个模块级定义点"),
    "模板增量赋值": ('_PAGE_TEMPLATE += "wrong"\n', "受保护名"),
    "相对导入": ("from . import json\n", "相对导入禁止"),
    "无括号装饰器": ("@print\ndef _probe_dec():\n    pass\n", "白名单外装饰器"),
    "type-别名": ("type json = int\n", "受保护名"),
    "取别名改属性": ('alias = json\nalias.dumps = lambda value, **kwargs: "wrong"\n', "被取别名"),
    # ── round-5 报告 (重发那一轮) 的反例: 上面那批补完之后**仍然**放行的 11 条 ──
    # 按维度归类: ①"定义豁免"对谁开放 ②写路径的**根**是谁 ③装饰器形态的穷举
    # ④豁免条件本身要不要验证。补前逐条实测放行, 见 probe-matrix.md。
    "模块级覆盖-import名": ("json = 0\n", "受保护名"),
    "模块级覆盖-内建名": ("list = 0\n", "受保护名"),
    "模块级覆盖-白名单调用名": ("HTMLResponse = APIRouter()\n", "受保护名"),
    "元组内属性目标": ('(json.dumps,) = (lambda value, **kwargs: "wrong",)\n', "受保护对象"),
    "for-属性目标": ("for json.dumps in ():\n    pass\n", "受保护对象"),
    "受保护对象-dunder下标写": ('json.__dict__["dumps"] = 1\n', "受保护对象"),
    "受保护对象-下标写": ('_STATUS_META["ok"] = ("x", "#fff")\n', "受保护对象"),
    "del-保护名": ("del json\n", "受保护名"),
    "装饰器-下标取内建": ('@__builtins__["print"]\ndef _probe_d1():\n    pass\n', "非白名单装饰器形态"),
    "装饰器-lambda包裹": ("@(lambda fn: fn)\ndef _probe_d2():\n    pass\n", "非白名单装饰器形态"),
    "装饰器-非白名单接收者": ("@Foo.get\ndef _probe_d3():\n    pass\n", "非白名单装饰器接收者"),
    "import-alias": ("import json as _probe_j\n", "import alias 禁止"),
    "type-形参": ("def _probe_tp[json]():\n    pass\n", "type 形参遮蔽"),
    "无注解request形参": ("def _probe_r(request):\n    return request\n", "受保护名"),
}

#: 反向探针: 这些**合法**写法必须放行。加严的门只可能在两个方向上错 ——
#: 漏网 (上面那张表) 与误伤 (这张表)。只测漏网 = 只证明了门够严, 没证明它没坏。
_AST_ALLOWED_SHAPES = {
    # 目标里出现的**读取**位置 Name 不是绑定 (round-5 反例集 false-positive-load)
    "下标读取保护名": "def _probe_load(cache, value):\n    cache[json] = value\n",
    # 新端点仍然只用白名单调用形态 —— 门管的是依赖形态, 不是端点数量
    # `request` 必须**带注解** —— 不带注解的 request 在 FastAPI 里是普通查询参数,
    # 拿到的是字符串, `.url_for` 根本不存在; 那不是合法写法 (round-5 BLOCKER-5)
    "新增同形态端点": '@review_app_router.get("/extra")\ndef _probe_extra(request: Request):\n    return HTMLResponse(request.url_for("review_overview"))\n',
    # 写路径的根名不受保护 = 普通对象, 放行 (与「受保护对象内部被写」成对)
    "普通对象属性赋值": "def _probe_attr(obj):\n    obj.value = 1\n",
    "普通对象下标赋值": "def _probe_sub(cache, k, v):\n    cache[k] = v\n",
    # 既不遮蔽也不新增调用的惰性代码 (门不是「见改就红」)
    "惰性代码": "_probe_inert = 1\nfor _i in ():\n    pass\n",
    # 非保护名走全部新补的绑定形态, 一条都不许误伤
    "非保护名走新形态": (
        "for _a in ():\n    pass\n"
        "with _js_json(1) as _b:\n    pass\n"
        "try:\n    pass\nexcept Exception as _c:\n    pass\n"
        "if (_d := 1):\n    pass\n"
        "_probe_c2 = [_e for _e in ()]\n"
    ),
}


def _gate_verdict(src: str) -> "str | None":
    """跑一遍 AST 门: 返回拒因字符串 (None = 放行)。"""
    try:
        _assert_module_closed(src)
    except (AssertionError, pytest.fail.Exception) as exc:
        return str(exc)
    return None


@pytest.mark.parametrize("label", sorted(_AST_PROBES))
def test_ast_gate_rejects_shadowing_forms(label):
    """负向探针: 每一类绕过形态都被门抓住, **且抓的是那条规则**。"""
    snippet, expect = _AST_PROBES[label]
    probe = _review_app_src() + "\n\n" + snippet
    ast.parse(probe)  # 探针本身必须是合法 Python — 否则测的是语法错不是门
    verdict = _gate_verdict(probe)
    assert verdict is not None, f"探针 {label} 未被门拦下 — 该形态仍是绕过通道"
    assert expect in verdict, f"探针 {label} 红的身份不对: 期望含 {expect!r}, 实得 {verdict!r}"


@pytest.mark.parametrize("label", sorted(_AST_ALLOWED_SHAPES))
def test_ast_gate_does_not_reject_legitimate_shapes(label):
    """反向探针: 合法写法不许被误伤 (加严的门在这个方向上一样会错)。"""
    probe = _review_app_src() + "\n\n" + _AST_ALLOWED_SHAPES[label]
    ast.parse(probe)
    verdict = _gate_verdict(probe)
    assert verdict is None, f"合法写法 {label} 被误拒: {verdict}"


def test_ast_gate_probe_harness_is_not_vacuous():
    """探针矩阵的验伪锚: 同一台机器上, **未注入**的真实源码必须放行。

    少了这条, 「25 条负向探针全被拦下」可以由一个恒红的门平凡满足 —— 那不是
    门变严了, 是门坏了。
    """
    assert _gate_verdict(_review_app_src()) is None


# ════════════════════════════════════════════════════════════════════
# C/D. 沙箱执行真实 <script> + node --test 断言 (完成条件 b/c)
# ════════════════════════════════════════════════════════════════════

#: 沙箱 boot 器: node_harness fixture 生成 boot.mjs, 测试文件导入它执行
#: page-script.js (响应里的真实 <script> 原文) 并导出沙箱作用域的函数。
_BOOT_MJS = r"""
import fs from "node:fs";

const SRC = fs.readFileSync(new URL("./page-script.js", import.meta.url), "utf8");

export function mkNode(id) {
  const node = {
    id, innerHTML: "", textContent: "", hidden: false, className: "", disabled: false,
    _attrs: {}, _desc: null, parentElement: null,
    setAttribute(k, v) { node._attrs[k] = String(v); },
    getAttribute(k) { return node._attrs[k] ?? null; },
    addEventListener() {},
    querySelector() { return null; },
    querySelectorAll() { return []; },
  };
  return node;
}

export function matches(node, sel) {
  if (sel === "[data-refresh-vault]") return node._attrs["data-refresh-vault"] !== undefined;
  if (sel === "[data-note-for]") return node._attrs["data-note-for"] !== undefined;
  return false;
}

export const flush = () => new Promise(r => setTimeout(r, 0));

export function boot({getJson, postJson, hidden = false} = {}) {
  const els = {};
  const handlers = {};
  const timers = [];
  const calls = {get: 0, post: 0};
  function makeEl(id) {
    const node = mkNode(id);
    node.addEventListener = (t, fn) => { handlers[id + "::" + t] = fn; };
    node.querySelectorAll = sel => (node._desc || []).filter(n => matches(n, sel));
    return node;
  }
  const documentStub = {
    hidden,
    getElementById: id => (els[id] ??= makeEl(id)),
    addEventListener: (t, fn) => { handlers["document::" + t] = fn; },
  };
  const fetchStub = async (url, opts = {}) => {
    if (opts && opts.method === "POST") {
      calls.post += 1;
      const h = typeof postJson === "function" ? postJson(url, opts) : postJson;
      return h === undefined || h === null ? {ok: false, status: 0, json: async () => null} : h;
    }
    calls.get += 1;
    const h = typeof getJson === "function" ? getJson(url) : getJson;
    return h === undefined || h === null ? {ok: false, status: 0, json: async () => null} : h;
  };
  const sandbox = new Function(
    "document", "fetch", "setTimeout", "clearTimeout",
    SRC +
    "\n;return {esc, shDay, parseDueMs, humanizeDue, computePollDelayMs, visibilityAction," +
    " boardLink, nodeLink, nodeDetailHtml, boardTableHtml, restDayHtml, renderVaultCard," +
    " renderPage, renderUnavailableBanner, renderRefreshResult, freshNotes};"
  );
  const api = sandbox(
    documentStub, fetchStub,
    (fn, ms) => { timers.push({fn, ms}); return timers.length; },
    () => {},
  );
  return {api, els, handlers, timers, calls, document: documentStub};
}
"""


def _group(pattern: str, text: str, flags: int = 0) -> str:
    """re.search().group(1) 的非 None 断言版 — pyright 严格模式友好。"""
    m = re.search(pattern, text, flags)
    assert m is not None, f"模式未命中: {pattern!r}"
    return m.group(1)


def _extract_script(html: str) -> str:
    """从实际响应体取出**整个** <script> 原文 — 且必须与浏览器 tokenizer 同源。

    HTML 解析对 script 结束符**大小写不敏感**、正文里出现注释开合也会改变
    解析状态 (round-2 HIGH-3 实证: `// </SCRIPT>` 后的"好代码"能骗过大小写
    敏感的正则, 但浏览器根本不会执行它)。所以除定位外, 还要拒绝一切会让
    「正则提取的字节」与「浏览器执行的字节」分叉的序列。
    """
    # 开标签: 大小写不敏感地只允许一个, 且必须恰是字面 <script> (无属性)
    openings = re.findall(r"<script\b[^>]*>", html, flags=re.I)
    assert openings == ["<script>"], f"script 开标签形态变了: {openings!r}"
    _prefix, sep, rest = html.partition("<script>")
    assert sep, "script 开标签未命中"
    # 结束符**总数**恰为 1 (大小写不敏感) — 正文任何位置多出结束符 (哪怕在
    # JS 注释里), 浏览器都会在那里提前终止脚本; maxsplit 截断式提取会把它
    # 当切割点吞掉, 那道门就是死的 (round-3 自查), 数段数才漏不掉。
    # round-3 HIGH-3: 浏览器结束标签语言还接受 solidus 分隔 (`</script/`) 与
    # 携带属性 (`</script x=y>`) — `</script\s*>` 数不到这些形态。
    # round-4 HIGH-3 补口: 前缀后紧跟 ASCII 字母 (`</scriptx`) 不是结束标签,
    # 浏览器不在此闭合 — 计数与切割都带 lookahead 对齐 tokenizer, 否则合法
    # 页面会被假截断, 截断后的字节与浏览器执行的字节分叉
    hits = re.findall(r"</script(?=[\t\n\f\r />])", rest, flags=re.I)
    assert len(hits) == 1, f"script 结束标签出现 {len(hits)} 次 (应恰 1) — 浏览器会在正文处提前终止"
    src = re.split(r"</script(?=[\t\n\f\r />])", rest, maxsplit=1, flags=re.I)[0]
    # 正文分叉面: HTML 注释开合改变 tokenizer 状态 (script data escaped)
    assert "<!--" not in src and "-->" not in src, "script 正文含 HTML 注释开合 — tokenizer 状态分叉面"
    assert "__URLS_JSON__" not in src, "占位符没被替换 — 页面发出去的是模板本身"
    return src


@pytest.fixture
def node_harness(tmp_path, page_html):
    """真实脚本 + 沙箱 boot 器写入 tmp; node 不可用时 fail-closed (不 skip)。"""
    if not _NODE:
        pytest.fail(
            "node 不可用 — 本文件 10+ 道 JS 门禁止静默 skip 假绿 (Codex round-1 "
            "HIGH-2 fail-closed); 本环境必须装 node, 或实现卡文默认裁决④的 "
            "Python 解析 fallback 后再改本门"
        )
    (tmp_path / "page-script.js").write_text(_extract_script(page_html), encoding="utf-8")
    (tmp_path / "boot.mjs").write_text(_BOOT_MJS, encoding="utf-8")
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
    # skipped 必须为 0 — 门不许被 conditional skip 悄悄掏空 (HIGH-2 配套);
    # 零计数 (`# skipped 0` / `skipped 0`) 放行, 非零即红
    assert not re.search(r"\bskipped?\s*[:=]?\s*[1-9]", proc.stdout), f"出现非零 skip:\n{proc.stdout}"


#: 测试公共 fixture JSON: 覆盖四态 + 休息日 + W6 三字段 (固定时钟, 不读真实时间)
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
// 空 vaults 的成功 GET — boot() 首轮 poll 用
const EMPTY_OK = () => ({ok: true, status: 200, json: async () => ({vaults: [OK_VAULT]})});
"""

_BOOT_PRELUDE = r"""
import test from "node:test";
import assert from "node:assert/strict";
import {boot, flush, mkNode, matches} from "./boot.mjs";
"""


def test_js_renders_four_states_and_unknown_state_defense(node_harness):
    """四态徽标各出一条 + 未知态防御 (不白屏, 原字面灰徽标)。"""
    proc = _run_node(
        node_harness,
        _BOOT_PRELUDE
        + _FIX_JS
        + r"""
test("ok 徽标", () => {
  const h = boot().api.renderVaultCard(OK_VAULT, NOW);
  assert.match(h, /今日投影/);
  assert.match(h, /#16a34a/);
  assert.match(h, /到期 <b>3<\/b>/);
});
test("stale 徽标", () => {
  const h = boot().api.renderVaultCard(STALE, NOW);
  assert.match(h, /过期投影/);
  assert.ok(!h.includes("今日投影"), "stale 不许装成 ok");
});
test("no_projection 徽标 + 降级文案, 不做假深链", () => {
  const h = boot().api.renderVaultCard(NO_PROJ, NOW);
  assert.match(h, /无投影/);
  assert.match(h, /该库尚无今日复习投影/);
  assert.ok(!h.includes("obsidian://open?vault=test-vault"), "无投影不该给库深链");
});
test("corrupt 徽标 + 原始错误可见", () => {
  const h = boot().api.renderVaultCard(CORRUPT, NOW);
  assert.match(h, /投影损坏/);
  assert.match(h, /schema_version 3/);
  assert.ok(!h.includes("今日投影"));
});
test("未知 status 不白屏 (原字面 + 灰徽标)", () => {
  const h = boot().api.renderVaultCard({vault_id: "x", status: "unregistered", error: null, projection: null}, NOW);
  assert.match(h, /unregistered/);
  assert.match(h, /#6b7280/);
  assert.ok(h.length > 50);
});
""",
    )
    _assert_node_green(proc)


def test_js_rest_day_empty_state_matches_pick_copy(node_harness):
    """休息日空状态: 文案对齐 daily_review_pick.py:599/:564。"""
    proc = _run_node(
        node_harness,
        _BOOT_PRELUDE
        + _FIX_JS
        + r"""
test("ok + due_count=0 → 休息日文案, 不显示到期 0 的大数字", () => {
  const h = boot().api.renderVaultCard(REST_DAY, NOW);
  assert.match(h, /今日无到期节点，休息一天。/);
  assert.match(h, /按计划推进 · 最近到期 线性代数 · 2026-09-03/);
  assert.ok(!/到期 <b>0<\/b>/.test(h), "休息日不该摆一个到期 0 的大数字");
});
test("有到期时不走休息日分支", () => {
  const h = boot().api.renderVaultCard(OK_VAULT, NOW);
  assert.ok(!h.includes("休息一天"));
});
test("stale 且 due_count=0 也不算休息日 (数据是旧的, 不许说今天没到期)", () => {
  const s = JSON.parse(JSON.stringify(STALE));
  s.projection.due_count = 0; s.projection.boards = [];
  const h = boot().api.renderVaultCard(s, NOW);
  assert.ok(!h.includes("休息一天"), "过期投影不能冒充『今天没到期』");
});
""",
    )
    _assert_node_green(proc)


def test_js_unavailable_banner_never_blank_screen(node_harness):
    """完成条件 b: fetch 失败/非 200/JSON 坏 → 横幅 + 保留旧数据, 不白屏。

    同时用沙箱真实走一遍「首轮 GET 失败」的接线: 横幅真的被写进 DOM stub,
    连接徽标翻红 — 不是只测字符串函数。
    """
    proc = _run_node(
        node_harness,
        _BOOT_PRELUDE
        + _FIX_JS
        + r"""
test("有过成功数据 → 说明保留了哪一刻的数据", () => {
  const b = boot().api.renderUnavailableBanner("HTTP 502", "14:32:05");
  assert.match(b, /后端离线\/不可用/);
  assert.match(b, /HTTP 502/);
  assert.match(b, /保留 14:32:05 的最后一次成功数据/);
});
test("从未成功过 → 诚实说没有数据 (不装成有)", () => {
  const b = boot().api.renderUnavailableBanner("Failed to fetch", null);
  assert.match(b, /尚未成功获取过数据/);
  assert.ok(!b.includes("保留"));
});
test("空 vaults 列表 → 显式空态文案, 不是空白", () => {
  const h = boot().api.renderPage({vaults: []}, NOW);
  assert.match(h, /未发现任何 vault/);
});
test("畸形响应 (缺 vaults 键) 不抛异常, 给空态", () => {
  assert.match(boot().api.renderPage({}, NOW), /未发现任何 vault/);
  assert.match(boot().api.renderPage(null, NOW), /未发现任何 vault/);
});
test("接线: 首轮 GET 503 → 横幅上屏 + 徽标翻红 + 保留重试排程, 不白屏", async () => {
  const b = boot();  // getJson 缺省 → {ok:false,status:0}
  await flush();
  assert.match(b.els["banner"].innerHTML, /后端离线\/不可用/);
  assert.equal(b.els["banner"].hidden, false);
  assert.equal(b.els["conn"].className, "conn down");
  assert.equal(b.els["conn"].textContent, "后端不可用");
  assert.equal(b.timers.length, 1, "必须保留一次重试排程");
  assert.equal(b.timers[0].ms, 10000, "unavailable 态按 10s 重试");
  assert.equal(b.els["cards"].innerHTML, "", "失败路径不得往卡片区塞任何假装成功的内容");
});
""",
    )
    _assert_node_green(proc)


def test_js_w6_additive_fields_present_and_absent(node_harness):
    """W6 (CARD-G3-6b) 三字段: 有 → 渲染; 无 → 整块不出现 (各一条)。"""
    proc = _run_node(
        node_harness,
        _BOOT_PRELUDE
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
  assert.match(boot().api.renderVaultCard(withW6(), NOW), /逾期最久 \+ 上次暴露最短路径缺口/);
});
test("why_this_board 缺省 → 整块不出现", () => {
  const h = boot().api.renderVaultCard(OK_VAULT, NOW);
  assert.ok(!h.includes('class="why"'), "缺省时不该出现说明行容器");
});
test("estimated_minutes 在场 → 约 N 分钟标签", () => {
  assert.match(boot().api.renderVaultCard(withW6(), NOW), /约 25 分钟/);
});
test("estimated_minutes 缺省 → 不出现标签", () => {
  assert.ok(!boot().api.renderVaultCard(OK_VAULT, NOW).includes("分钟"));
});
test("estimated_minutes 非有限数 → 当缺省处理, 不渲染 NaN/Infinity", () => {
  const v = JSON.parse(JSON.stringify(OK_VAULT));
  v.projection.boards[0].estimated_minutes = "25";  // 字符串不是有限数
  const h = boot().api.renderVaultCard(v, NOW);
  assert.ok(!h.includes("分钟"));
  assert.ok(!h.includes("NaN") && !h.includes("Infinity"));
});
test("rank_manifest 在场 → 底部小注", () => {
  assert.match(boot().api.renderVaultCard(withW6(), NOW), /rank_manifest/);
});
test("rank_manifest 缺省 → 整块不出现", () => {
  assert.ok(!boot().api.renderVaultCard(OK_VAULT, NOW).includes("rank_manifest"));
});
""",
    )
    _assert_node_green(proc)


def test_js_poll_interval_clamped_and_visibility_pauses(node_harness):
    """完成条件 c: 轮询周期 clamp(next_due−now, 5s, 60s) + 隐藏暂停。

    clamp 断言一半走纯函数, 一半走真实接线: boot 成功拉取后, 实际排程的
    setTimeout 延迟必须等于 computePollDelayMs 的裁决。
    """
    proc = _run_node(
        node_harness,
        _BOOT_PRELUDE
        + _FIX_JS
        + r"""
function at(secondsFromNow) {  // 构造一个 now+N 秒的 next_due 投影
  const iso = new Date(NOW + secondsFromNow * 1000).toISOString().replace(/\.\d{3}Z$/, "Z");
  return {vaults: [{vault_id: "v", status: "ok",
    projection: {next_upcoming: {board: "b", next_due: iso, node: "n"}}}]};
}
test("6 秒后到期 → 6 秒后再问 (区间内原样)", () => {
  assert.equal(boot().api.computePollDelayMs(at(6), NOW), 6000);
});
test("2 秒后到期 → 夹到下限 5 秒 (不打爆后端)", () => {
  assert.equal(boot().api.computePollDelayMs(at(2), NOW), 5000);
});
test("1 小时后到期 → 夹到上限 60 秒 (不睡死)", () => {
  assert.equal(boot().api.computePollDelayMs(at(3600), NOW), 60000);
});
test("已过期的 next_due → 回落上限, 不空转", () => {
  assert.equal(boot().api.computePollDelayMs(at(-100), NOW), 60000);
});
test("没有任何 upcoming → 回落上限", () => {
  assert.equal(boot().api.computePollDelayMs({vaults: [NO_PROJ, CORRUPT]}, NOW), 60000);
  assert.equal(boot().api.computePollDelayMs({vaults: []}, NOW), 60000);
  assert.equal(boot().api.computePollDelayMs(null, NOW), 60000);
});
test("多库取最近的那个未来时刻", () => {
  const data = {vaults: [at(50).vaults[0], at(8).vaults[0], at(-5).vaults[0]]};
  assert.equal(boot().api.computePollDelayMs(data, NOW), 8000);
});
test("畸形 next_due 不炸, 按无排期处理", () => {
  const bad = {vaults: [{vault_id: "v", status: "ok",
    projection: {next_upcoming: {board: "b", next_due: "20260901", node: "n"}}}]};
  assert.equal(boot().api.computePollDelayMs(bad, NOW), 60000);
});
test("页面隐藏 → 取消排程且不拉取", () => {
  assert.deepEqual(boot().api.visibilityAction(true), {cancelTimer: true, pollNow: false});
});
test("回到前台 → 取消旧排程并立即拉一轮", () => {
  assert.deepEqual(boot().api.visibilityAction(false), {cancelTimer: true, pollNow: true});
});
test("接线: 成功轮询后实际排程延迟 = clamp 裁决 (60s 上限路径)", async () => {
  const b = boot({getJson: EMPTY_OK()});
  await flush();
  assert.equal(b.calls.get, 1);
  assert.equal(b.timers.length, 1);
  assert.equal(b.timers[0].ms, 60000, "next_due 在远期 → 排程必须落在 60s 上限");
  assert.match(b.els["nextpoll"].textContent, /60 秒后/);
  assert.equal(b.els["conn"].className, "conn ok");
});
test("接线: 页面以隐藏态启动 → 首轮照拉, 但不排下一轮", async () => {
  const b = boot({getJson: EMPTY_OK(), hidden: true});
  await flush();
  assert.equal(b.calls.get, 1, "首轮拉取不受隐藏影响 (数据还是要拿的)");
  assert.equal(b.timers.length, 0, "隐藏期间不得排下一轮");
  assert.match(b.els["nextpoll"].textContent, /已暂停/);
});
""",
    )
    _assert_node_green(proc)


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
        _BOOT_PRELUDE
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
  assert.equal(boot().api.computePollDelayMs(before, NOW), 6000);
});
test("② 到点前那一轮: 休息日, 页面没有该到期卡", () => {
  const h = boot().api.renderPage(before, NOW);
  assert.match(h, /休息一天/);
  assert.ok(!h.includes("二叉堆"), "还没到期就不该出现节点");
});
test("③ 到点后那一轮: 到期卡与节点明细出现", () => {
  const h = boot().api.renderPage(after, NOW + 6000);
  assert.match(h, /到期 <b>1<\/b>/);
  assert.match(h, /堆与优先队列/);
  assert.match(h, /二叉堆/);
  assert.ok(!h.includes("休息一天"));
});
""",
    )
    _assert_node_green(proc)


def test_js_refresh_result_visible_and_never_fakes_success(node_harness):
    """完成条件 c: 手动刷新的 rebuild_count / 去抖态 / 失败在页面可见。

    去抖与失败**都不许长得像成功** —— 那正是零 JS 页 round-3 修过的
    「与成功逐字节同形的 303」的浏览器版本。四个 JSON 分支都带 rebuild_count
    (Codex round-1 HIGH-1 的第三点)。
    """
    proc = _run_node(
        node_harness,
        _BOOT_PRELUDE
        + _FIX_JS
        + r"""
test("真重建 → 显示本进程累计次数", () => {
  const h = boot().api.renderRefreshResult(200, {rebuilt: true, reason: "rebuilt", rebuild_count: 3});
  assert.match(h, /已重建/);
  assert.match(h, /累计 3 次/);
  assert.match(h, /rnote ok/);
});
test("去抖 → 明说本次没重算 + 累计次数 + 还要等多久", () => {
  const h = boot().api.renderRefreshResult(200, {rebuilt: false, reason: "debounced",
    debounce_ttl_seconds: 10, retry_after_seconds: 6.2, rebuild_count: 3});
  assert.match(h, /10 秒内已重建过/);
  assert.match(h, /累计 3 次/);
  assert.match(h, /本次未重算/);
  assert.match(h, /约 7 秒后可再试/);
  assert.match(h, /rnote warn/);
  assert.ok(!h.includes("✅") && !/rnote ok/.test(h), "去抖不许长得像成功");
});
test("in_progress → 说清没重复启动 + 累计次数", () => {
  const h = boot().api.renderRefreshResult(200, {rebuilt: false, reason: "in_progress", rebuild_count: 5});
  assert.match(h, /已有一次重建在跑/);
  assert.match(h, /累计 5 次/);
  assert.ok(!/rnote ok/.test(h));
});
test("rebuild_count 缺省也不显示 undefined", () => {
  const h = boot().api.renderRefreshResult(200, {rebuilt: true, reason: "rebuilt"});
  assert.match(h, /已重建/);
  assert.ok(!h.includes("undefined") && !h.includes("null"));
});
test("503 → 显示状态码与后端给的原因", () => {
  const h = boot().api.renderRefreshResult(503, {detail: {error: "pick_missing", message: "生产器脚本不可用"}});
  assert.match(h, /HTTP 503/);
  assert.match(h, /生产器脚本不可用/);
  assert.match(h, /rnote err/);
});
test("403 同源门 → 原样呈现, 不吞", () => {
  const h = boot().api.renderRefreshResult(403, {detail: {error: "cross_site_blocked", message: "跨站请求被拒"}});
  assert.match(h, /HTTP 403/);
  assert.match(h, /跨站请求被拒/);
});
test("网络错误 (status 0) → 明确说网络失败", () => {
  assert.match(boot().api.renderRefreshResult(0, {detail: "Failed to fetch"}), /网络错误/);
});
test("响应体不是 JSON (payload=null) 也不白, 给状态码", () => {
  assert.match(boot().api.renderRefreshResult(500, null), /HTTP 500/);
});
""",
    )
    _assert_node_green(proc)


def test_js_refresh_wiring_note_survives_rerender_and_inflight_guard(node_harness):
    """Codex round-1 HIGH-1 的接线门: 刷新反馈进持久状态, 不被重绘抹掉。

    场景全部在沙箱里以真实脚本 + 假事件驱动:
      ① POST 去抖结局 → 反馈就地写进 note span (含 rebuild_count);
      ② 之后一轮轮询重绘 → 反馈**仍在** (从 state.notes 恢复, 15s TTL 内);
      ③ TTL 过期后的重绘 → 反馈消失 (不永久占卡片);
      ④ 在飞期间重复点击 → 只发一个 POST;
      ⑤ rebuilt 结局 → 立即补一轮 GET (数字马上更新)。
    """
    proc = _run_node(
        node_harness,
        _BOOT_PRELUDE
        + _FIX_JS
        + r"""
function makeWorld() {
  const b = boot({
    getJson: EMPTY_OK(),
    postJson: () => ({ok: true, status: 200, json: async () =>
      ({rebuilt: false, reason: "debounced", debounce_ttl_seconds: 10,
        retry_after_seconds: 6.6, rebuild_count: 3})}),
  });
  return b;
}
function attachButtonNote(b, vid) {
  const btn = mkNode("btn-" + vid);
  btn._attrs["data-refresh-vault"] = vid;
  const note = mkNode("note-" + vid);
  note._attrs["data-note-for"] = vid;
  b.els["cards"]._desc = [btn, note];
  return {btn, note};
}
const clickEvent = btn => ({target: {closest: sel => (matches(btn, sel) ? btn : null)}});

test("① 去抖反馈就地写进 note (含累计次数), 按钮恢复可用", async () => {
  const b = makeWorld();
  await flush();
  const {btn, note} = attachButtonNote(b, "cs_61b");
  await b.handlers["cards::click"](clickEvent(btn));
  assert.match(note.innerHTML, /未重算/);
  assert.match(note.innerHTML, /累计 3 次/);
  assert.equal(btn.disabled, false, "POST 结束后按钮必须解锁");
  assert.equal(b.calls.post, 1);
});
test("② 反馈不被下一轮重绘抹掉 (HIGH-1 主场景)", async () => {
  const b = makeWorld();
  await flush();
  const {btn} = attachButtonNote(b, "cs_61b");
  await b.handlers["cards::click"](clickEvent(btn));
  // 下一轮轮询 (回前台触发) → renderCards 用 freshNotes 恢复反馈
  b.handlers["document::visibilitychange"]();
  await flush();
  assert.match(b.els["cards"].innerHTML, /未重算/);
  assert.match(b.els["cards"].innerHTML, /累计 3 次/);
});
test("③ TTL 过期后重绘, 反馈退场 (不永久占卡片)", async () => {
  const b = makeWorld();
  await flush();
  const {btn, note} = attachButtonNote(b, "cs_61b");
  await b.handlers["cards::click"](clickEvent(btn));
  assert.equal(Object.keys(b.api.freshNotes(Date.now() + 16000)).length, 0, "15s TTL 后不得再有 note");
  assert.deepEqual(Object.keys(b.api.freshNotes(Date.now())), ["cs_61b"], "TTL 内必须还有 note");
  assert.ok(note.innerHTML.length > 0);
});
test("④ 在飞期间重复点击 → 只发一个 POST", async () => {
  const b = makeWorld();
  await flush();
  const {btn} = attachButtonNote(b, "cs_61b");
  const p1 = b.handlers["cards::click"](clickEvent(btn));
  const p2 = b.handlers["cards::click"](clickEvent(btn));
  await Promise.all([p1, p2]);
  assert.equal(b.calls.post, 1, "同库在飞时第二个点击不得发 POST");
});
test("⑤ rebuilt 结局 → 立即补一轮 GET", async () => {
  const b = boot({
    getJson: EMPTY_OK(),
    postJson: () => ({ok: true, status: 200, json: async () =>
      ({rebuilt: true, reason: "rebuilt", rebuild_count: 4})}),
  });
  await flush();
  assert.equal(b.calls.get, 1);
  const {btn} = attachButtonNote(b, "cs_61b");
  await b.handlers["cards::click"](clickEvent(btn));
  await flush();
  assert.equal(b.calls.get, 2, "真重建后必须立即重拉总览");
  assert.match(b.els["cards"].innerHTML, /已重建/);
});
test("⑥ 反馈期间被重绘换过 DOM → 结局靠重绘恢复 (就地补不到的路径)", async () => {
  const b = makeWorld();
  await flush();
  const {btn} = attachButtonNote(b, "cs_61b");
  const p = b.handlers["cards::click"](clickEvent(btn));
  // POST 在飞时页面被重绘 (模拟一轮轮询), 旧 note span 脱离 DOM
  b.els["cards"]._desc = [];
  await p;
  // 就地补找不到 span → 必须走 renderCards 恢复, 卡片上仍能看到去抖反馈
  assert.match(b.els["cards"].innerHTML, /未重算/);
});
""",
    )
    _assert_node_green(proc)


def test_js_shows_authoritative_due_count_never_recomputes(node_harness):
    """完成条件 (硬边界): JS 内不实现任何 due 算法 —— 只消费投影。

    行为门 (非否定断言): 喂一份 due_count=7 而 boards 明细只有 2+1 的投影
    (服务端 _summarize 允许这种并陈: stats 是权威计数, 明细可因脏行降级),
    页面必须显示 7。若 JS 私下按明细重算, 会显示 3, 本门变红。
    """
    proc = _run_node(
        node_harness,
        _BOOT_PRELUDE
        + _FIX_JS
        + r"""
test("显示服务端权威 due_count, 不按明细重加", () => {
  const v = JSON.parse(JSON.stringify(OK_VAULT));
  v.projection.due_count = 7;   // 权威计数
  // 明细仍是 2+1=3 —— 若 JS 重算就会显示 3
  const h = boot().api.renderVaultCard(v, NOW);
  assert.match(h, /到期 <b>7<\/b>/);
  assert.ok(!/到期 <b>3<\/b>/.test(h), "页面重算了到期数 — 违反『只消费投影』");
});
test("板行到期数直接取 boards[].due, 不按 nodes 长度重数", () => {
  const v = JSON.parse(JSON.stringify(OK_VAULT));
  v.projection.boards[0].due = 9;   // 明细只有 1 个 node
  assert.match(boot().api.renderVaultCard(v, NOW), /<b>9<\/b>/);
});
test("休息日判定读 due_count, 不读 boards 是否为空", () => {
  const v = JSON.parse(JSON.stringify(OK_VAULT));
  v.projection.boards = [];        // 明细空, 但权威计数非零
  const h = boot().api.renderVaultCard(v, NOW);
  assert.ok(!h.includes("休息一天"), "权威计数非零时不许说休息");
  assert.match(h, /到期 <b>3<\/b>/);
});
""",
    )
    _assert_node_green(proc)


def test_js_escapes_hostile_names_and_encodes_deep_links(node_harness):
    """XSS / 深链编码: 库名、板名、节点名、错误串都来自外部 JSON。"""
    proc = _run_node(
        node_harness,
        _BOOT_PRELUDE
        + _FIX_JS
        + r"""
test("恶意库名不产生可执行标签", () => {
  const h = boot().api.renderVaultCard({vault_id: '<img src=x onerror=alert(1)>', status: "corrupt",
    error: '</script><script>alert(2)</script>', projection: null}, 0);
  assert.ok(!h.includes("<img"), "库名未转义");
  assert.ok(!h.includes("<script"), "错误串未转义");
  assert.match(h, /&lt;img/);
});
test("板名里的引号不能撑破 href 属性", () => {
  const h = boot().api.renderVaultCard({vault_id: "v", status: "ok", error: null, projection: {
    due_count: 1, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
    generated_at: "g", next_upcoming: null,
    boards: [{board: '" onmouseover="alert(1)', due: 1, due_new: 0,
              placeholder: null, earliest: "", nodes: []}]}}, 0);
  assert.ok(!h.includes('onmouseover="alert'), "属性被撑破");
});
test("深链把 / & # ? 一并编码 (与服务端 quote(safe='') 同语义)", () => {
  const api = boot().api;
  const l = api.boardLink("v/a", "b&c#d?e");
  assert.ok(l.includes("v%2Fa"));
  assert.ok(l.includes("%26") && l.includes("%23") && l.includes("%3F"));
  assert.ok(!l.slice("obsidian://open?vault=".length).includes("/"));
  assert.ok(api.nodeLink("v", "x/y").includes("%2Fy"));
});
""",
    )
    _assert_node_green(proc)


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
        "import {boot} from './boot.mjs';\n"
        f"const NOW = {_NOW_MS};\nconst CASES = {json.dumps(cases, ensure_ascii=False)};\n"
        r"""
const humanizeDue = boot().api.humanizeDue;
for (const c of CASES) {
  test("与服务端一致: " + c.label, () => {
    assert.equal(humanizeDue(c.ts, NOW).text, c.expected);
  });
}
""",
    )
    _assert_node_green(proc)


#: 固定时钟毫秒 (与 _FIX_JS 的 NOW 同源; 放在文件尾供上面的对拍测试引用)
_NOW_MS = 1_788_000_000_000


# ════════════════════════════════════════════════════════════════════
# E. Codex round-2 整改门 (因果一致性 / 提取同源 / AST 正向合约)
# ════════════════════════════════════════════════════════════════════


def test_script_extraction_rejects_case_insensitive_terminator():
    """HIGH-3 门: 正文里任何大小写形态的 </script / 注释开合都必须被拒绝。

    变异 M38 (往正文塞 `// </SCRIPT>`) 的指定门是
    test_real_page_extracted_script_is_well_formed (真实响应被毒化后提取器
    必须拒绝); 本门用模板构造的毒样本锁定提取器本身的判据。
    """
    base = _PAGE_TEMPLATE.replace("__URLS_JSON__", "{}").replace("__STATUS_META_JSON__", "{}")
    base = base.replace("__BUCKET_CN_JSON__", "{}").replace("__BUCKET_ORDER_JSON__", "[]")
    # 后两种是 round-3 HIGH-3 实证: 浏览器接受 solidus 分隔与携带属性的结束标签,
    # `</script\s*>` 数不到 — 现按 `</script` 前缀计数, 全部必红
    for needle in ("// </SCRIPT>", "</script >", "</script/", "</script x=y>", "/* <!-- */"):
        poisoned = base.replace("const POLL_MIN_MS", f"{needle}\nconst POLL_MIN_MS", 1)
        with pytest.raises(AssertionError):
            _extract_script(poisoned)
    # round-4 补口对齐: `</scriptx` (前缀后跟字母) 不是结束标签 — 浏览器不在此
    # 闭合, 提取器也不许截断 (截断 = 沙箱漏执行尾段字节)
    aligned = base.replace("const POLL_MIN_MS", "</scriptx\nconst POLL_MIN_MS", 1)
    src = _extract_script(aligned)
    assert "</scriptx" in src, "字母后缀的前缀不是结束符, 必须原样保留在正文中"


def test_real_page_extracted_script_is_well_formed(page_html):
    """真实响应的 script 必须能被同源提取且完整 (M38 指定门)。

    正文被塞入任何多出的结束符/注释开合时, _extract_script 会拒绝 —
    那一刻「沙箱执行的字节 == 浏览器执行的字节」就破了, 本门立刻红。
    """
    src = _extract_script(page_html)
    assert "POLL_MIN_MS" in src and "computePollDelayMs" in src, "提取产物被截断 — 不是完整脚本"


def test_js_poll_out_of_order_discards_stale_response(node_harness):
    """HIGH-1 因果门: 旧 GET 晚到必须整包丢弃, 不许把新数据盖回旧投影。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {boot, flush} from "./boot.mjs";
const deferreds = [];
function deferredGet(tag) {
  let resolve;
  const promise = new Promise(r => { resolve = r; });
  deferreds.push({tag, resolve});
  return {ok: true, status: 200, json: () => promise};
}
const dataOf = tag => ({vaults: [{vault_id: "v", status: "ok", error: null,
  projection: {due_count: tag === "new" ? 2 : 1, due_new_count: 0, placeholder_backlog: 0,
    bucket_counts: null, generated_at: tag, next_upcoming: null, boards: []}}]});
const b = boot({getJson: u => deferredGet("old")});   // 首轮 poll 挂起 (gen 1)
const d = deferreds.pop();
b.handlers["document::visibilitychange"]();            // 回前台 → 第二轮 GET (gen 2)
const d2 = deferreds.pop();
d2.resolve(dataOf("new"));  // 新的先回 (deferred 桩的 resolve 喂 json() 的返回值 = 数据)
await flush();
assert.match(b.els["cards"].innerHTML, /生成于 new/, "新数据先落屏");
d.resolve(dataOf("old"));   // 旧的晚到
await flush();
assert.match(b.els["cards"].innerHTML, /生成于 new/, "旧响应晚到必须被代际守卫整包丢弃");
assert.ok(!b.els["cards"].innerHTML.includes("生成于 old"));
assert.match(b.els["nextpoll"].textContent, /秒后/, "乱序丢弃后原有排程不被旧响应重置");
""",
    )
    _assert_node_green(proc)


@pytest.mark.usefixtures("page_html")
def test_js_rebuilt_sync_flow_never_claims_prematurely(node_harness):
    """HIGH-1 结算门: rebuilt 只说『正在同步』, GET 成功才说『数字已更新』,
    GET 失败明说同步失败 — 旧版「同步失败也挂着数字已更新」不许回来。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {boot, flush, mkNode, matches} from "./boot.mjs";
const OK = {vaults: [{vault_id: "cs_61b", status: "ok", error: null,
  projection: {due_count: 3, due_new_count: 1, placeholder_backlog: 0, bucket_counts: null,
    generated_at: "g", next_upcoming: null, boards: []}}]};
function world(getJson) {
  const b = boot({
    getJson,
    postJson: () => ({ok: true, status: 200, json: async () =>
      ({rebuilt: true, reason: "rebuilt", rebuild_count: 4})}),
  });
  return b;
}
function attach(b) {
  const btn = mkNode("btn");
  btn._attrs["data-refresh-vault"] = "cs_61b";
  const note = mkNode("note");
  note._attrs["data-note-for"] = "cs_61b";
  b.els["cards"]._desc = [btn, note];
  return {btn, note};
}
const click = btn => ({target: {closest: sel => (matches(btn, sel) ? btn : null)}});

test("① rebuilt → 先只说正在同步, 不许出现『数字已更新』", async () => {
  // GET 用永不 resolve 的桩 — 「正在同步」态定格, 不与后续 GET 的失败结算赛跑
  const b = world(() => new Promise(() => {}));
  await flush();
  const {btn, note} = attach(b);
  await b.handlers["cards::click"](click(btn));
  assert.match(note.innerHTML, /正在同步最新数字/);
  assert.ok(!note.innerHTML.includes("数字已更新"), "POST 成功不等于数字已落屏");
});
test("② 后续 GET 成功 → 结算成『数字已更新』", async () => {
  const b = world(() => ({ok: true, status: 200, json: async () => OK}));  // GET 一路成功
  await flush();
  assert.match(b.els["cards"].innerHTML, /生成于 g/, "首轮成功, 卡片在屏");
  const {btn, note} = attach(b);
  await b.handlers["cards::click"](click(btn));  // POST rebuilt → 正在同步 → 自动 GET
  await flush();                                 // GET 成功 → settlePendingSync(true)
  assert.match(note.innerHTML, /数字已更新/);
  assert.ok(!note.innerHTML.includes("同步失败"));
  assert.match(b.els["cards"].innerHTML, /数字已更新/, "结算反馈在重绘后仍在");
});
test("②b 同步失败 → 明说失败; 恢复后数据照常更新, 失败反馈按 TTL 退场", async () => {
  let fail = true;
  const b = world(() => fail ? {ok: false, status: 503, json: async () => null}
                            : {ok: true, status: 200, json: async () => OK});
  await flush();
  const {btn, note} = attach(b);
  await b.handlers["cards::click"](click(btn));
  await flush();                              // handler 返回后 fired poll 的失败才结算
  assert.match(note.innerHTML, /同步失败/);   // 第一轮 GET (503) 已把结局结算成失败
  fail = false;
  b.handlers["document::visibilitychange"]();  // 后端恢复 → 重拉成功
  await flush();
  assert.match(b.els["cards"].innerHTML, /生成于 g/, "恢复后数据照常更新");
  assert.match(b.els["cards"].innerHTML, /同步失败/, "失败结算如实挂着 (15s TTL 内)");
  assert.ok(!b.els["cards"].innerHTML.includes("数字已更新"), "失败结算不许被成功轮询洗成成功");
});
test("②c 目标库从聚合消失 → 失败反馈在最终帧可见 (lostnote)", async () => {
  const without = {vaults: [{vault_id: "别的库", status: "ok", error: null,
    projection: {due_count: 1, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
      generated_at: "x", next_upcoming: null, boards: []}}]};
  const b = boot({
    getJson: () => ({ok: true, status: 200, json: async () => without}),
    postJson: () => ({ok: true, status: 200, json: async () =>
      ({rebuilt: true, reason: "rebuilt", rebuild_count: 2})}),
  });
  await flush();
  const btn = mkNode("btn");
  btn._attrs["data-refresh-vault"] = "cs_61b";
  const note = mkNode("note");
  note._attrs["data-note-for"] = "cs_61b";
  b.els["cards"]._desc = [btn, note];
  await b.handlers["cards::click"](click(btn));
  await flush();
  // cs_61b 不在聚合里 → 它的卡消失, 但失败反馈必须在最终帧可见 (round-4 HIGH-1 反例二)
  assert.match(b.els["cards"].innerHTML, /同步失败/);
  assert.match(b.els["cards"].innerHTML, /该库已不在当前聚合中/);
  assert.ok(!b.els["cards"].innerHTML.includes("数字已更新"));
});
""",
    )
    _assert_node_green(proc)


@pytest.mark.usefixtures("page_html")
def test_js_post_repaint_frame_keeps_lost_sync_note(node_harness):
    """R1 门 (CARD-G6-2b): 失联通知不许只活在 poll 的最终帧。

    round-4 HIGH-1 反例二只封住了 poll 成功路径的最终帧 (renderPage +
    lostSyncNotesHtml)。但卡片区还有另外两条重绘路径走 renderCards():
    ①settlePendingSync 的兜底重绘 —— GET 失败时它就是**最后一帧** (catch
    分支之后不再有 renderPage), 失败反馈连同失联通知一起看不见;
    ②onRefreshClick 的 POST 反馈重绘 —— 把上一轮已经上屏的失联通知洗掉,
    要等下一轮轮询才回来 (用户视角: 提示一闪就没)。
    """
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {boot, flush, mkNode, matches} from "./boot.mjs";
// 聚合里只有「别的库」—— cs_61b 已从聚合消失 (它的卡不会被渲染)
const WITHOUT = {vaults: [{vault_id: "别的库", status: "ok", error: null,
  projection: {due_count: 1, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
    generated_at: "g", next_upcoming: null, boards: []}}]};
const okGet = () => ({ok: true, status: 200, json: async () => WITHOUT});
// 按钮挂着但**没有** [data-note-for] span (卡已消失, 就地补必然落空) →
// 强制走 renderCards 兜底重绘, 也就是本门要测的那条路径
function attach(b, ...vids) {
  const nodes = vids.map(v => { const n = mkNode("btn:" + v);
    n._attrs["data-refresh-vault"] = v; return n; });
  b.els["cards"]._desc = nodes;
  return nodes;
}
const click = btn => ({target: {closest: sel => (matches(btn, sel) ? btn : null)}});

test("① 结算兜底重绘 (GET 失败, 这就是最后一帧) 必须保留失联通知", async () => {
  let n = 0;
  const b = boot({
    getJson: () => (++n === 1 ? okGet() : {ok: false, status: 503, json: async () => null}),
    postJson: () => ({ok: true, status: 200, json: async () =>
      ({rebuilt: true, reason: "rebuilt", rebuild_count: 3})}),
  });
  await flush();
  const [btn] = attach(b, "cs_61b");
  await b.handlers["cards::click"](click(btn));
  await flush();   // rebuilt 触发的 GET 失败 → catch → settlePendingSync(false) → 兜底重绘
  assert.equal(b.els["conn"].className, "conn down", "前提: 这一轮 GET 确实失败了");
  assert.match(b.els["cards"].innerHTML, /同步失败/,
    "失败结算是最后一帧的内容 — 用户必须看得见");
  assert.match(b.els["cards"].innerHTML, /该库已不在当前聚合中/);
});

test("② 另一个库的 POST 反馈重绘不许洗掉已上屏的失联通知", async () => {
  const b = boot({
    getJson: okGet,
    postJson: (url, opts) => {
      const vid = opts.body.get("vault_id");
      // cs_61b 触发 rebuilt (→ 失败结算 → 失联通知上屏); 别的库被去抖
      // (rebuilt=false → 不触发新 GET, POST 反馈重绘就是最后一帧)
      return vid === "cs_61b"
        ? {ok: true, status: 200, json: async () => ({rebuilt: true, reason: "rebuilt", rebuild_count: 5})}
        : {ok: true, status: 200, json: async () =>
            ({rebuilt: false, reason: "debounced", debounce_ttl_seconds: 10, rebuild_count: 5})};
    },
  });
  await flush();
  const [lost, other] = attach(b, "cs_61b", "别的库");
  await b.handlers["cards::click"](click(lost));
  await flush();
  assert.match(b.els["cards"].innerHTML, /该库已不在当前聚合中/, "前提: 失联通知已上屏");
  await b.handlers["cards::click"](click(other));   // 去抖 → 不触发 poll, 无后续帧
  assert.match(b.els["cards"].innerHTML, /未重算/, "前提: 这一帧确实是 POST 反馈重绘");
  assert.match(b.els["cards"].innerHTML, /该库已不在当前聚合中/,
    "刷新别的库不该让上一个库的失联提示一闪就没");
});
""",
    )
    _assert_node_green(proc)


@pytest.mark.usefixtures("page_html")
def test_js_malformed_200_keeps_last_data(node_harness):
    """round-2 M2 门: HTTP 200 的坏形状在提交状态之前就被拒 —
    旧数据不清、连接徽标翻红、横幅说话, 绝不清屏装『已连接』。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {boot, flush} from "./boot.mjs";
const GOOD = {vaults: [{vault_id: "v", status: "ok", error: null,
  projection: {due_count: 5, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
    generated_at: "good", next_upcoming: null, boards: []}}]};
let payload = GOOD;
const b = boot({getJson: () => ({ok: true, status: 200, json: async () => payload})});
await flush();
assert.match(b.els["cards"].innerHTML, /good/);
assert.equal(b.els["conn"].className, "conn ok");
payload = {vaults: "bad"};                 // HTTP 200 + 形状坏
b.handlers["document::visibilitychange"]();
await flush();
assert.match(b.els["cards"].innerHTML, /good/, "坏形状不许清掉旧数据");
assert.equal(b.els["conn"].className, "conn down", "不许装已连接");
assert.equal(b.els["banner"].hidden, false);
assert.match(b.els["banner"].innerHTML, /形状坏/);
payload = {root: false};                    // 缺 vaults 键同理
b.handlers["document::visibilitychange"]();
await flush();
assert.match(b.els["cards"].innerHTML, /good/);
""",
    )
    _assert_node_green(proc)


@pytest.mark.usefixtures("page_html")
def test_js_proto_vault_id_and_inflight_disabled_render(node_harness):
    """round-2 M1/M3 门: null-prototype 容器让 "__proto__" 这样的合法库目名
    走正常点击流 (在飞防抖仍然成立); 在飞库的重绘必须渲染 disabled 按钮。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {boot, flush, mkNode, matches} from "./boot.mjs";
const V = vid => ({vaults: [{vault_id: vid, status: "ok", error: null,
  projection: {due_count: 1, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
    generated_at: "g", next_upcoming: null, boards: []}}]});
test('"__proto__" 库目: 点击只发一个 POST, 反馈正常可见 (原型键不吞)', async () => {
  const b = boot({
    getJson: () => ({ok: true, status: 200, json: async () => V("__proto__")}),
    postJson: () => ({ok: true, status: 200, json: async () =>
      ({rebuilt: false, reason: "debounced", debounce_ttl_seconds: 10, rebuild_count: 1})}),
  });
  await flush();
  const btn = mkNode("btn");
  btn._attrs["data-refresh-vault"] = "__proto__";
  const note = mkNode("note");
  note._attrs["data-note-for"] = "__proto__";
  b.els["cards"]._desc = [btn, note];
  const ev = {target: {closest: sel => (matches(btn, sel) ? btn : null)}};
  await Promise.all([b.handlers["cards::click"](ev), b.handlers["cards::click"](ev)]);
  assert.equal(b.calls.post, 1, "在飞防抖对 __proto__ 库目同样生效");
  assert.match(note.innerHTML, /未重算/);
});
test("在飞库重绘 → 按钮渲染 disabled (重绘不解锁成可双击)", () => {
  const b = boot();
  const h = b.api.renderPage(V("v"), 0, {}, {v: true});
  assert.match(h, / disabled /, "inflight 库的按钮必须带 disabled 属性");
  const h2 = b.api.renderPage(V("v"), 0, {}, {});
  assert.ok(!h2.includes(" disabled "), "非在飞库不许误带 disabled");
});
""",
    )
    _assert_node_green(proc)


@pytest.mark.usefixtures("page_html")
def test_js_restday_next_due_uses_shanghai_date(node_harness):
    """round-2 M4 门: 最近到期日期转上海本地日 —
    2026-09-02T16:30:00Z 在上海已是 9 月 3 日, 不许显示 UTC 字面的 9 月 2 日。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {boot} from "./boot.mjs";
const NOW = 1788000000000;
const proj = {due_count: 0, boards: [], bucket_counts: null,
  generated_at: "g", next_upcoming: {board: "线性代数", next_due: "2026-09-02T16:30:00Z", node: "特征值"}};
const v = {vault_id: "数学", status: "ok", error: null, projection: proj};
const h = boot().api.renderVaultCard(v, NOW);
assert.match(h, /最近到期 线性代数 · 2026-09-03/, "上海本地日 (UTC 9/2 16:30 = 上海 9/3 0:30)");
assert.ok(!h.includes("2026-09-02"), "UTC 字面日期不许漏出来");
const bad = {vault_id: "x", status: "ok", error: null, projection: {...proj,
  next_upcoming: {board: "b", next_due: "20260902", node: "n"}}};
assert.match(boot().api.renderVaultCard(bad, NOW), /20260902/, "畸形时间原样显示, 不炸");
""",
    )
    _assert_node_green(proc)


@pytest.mark.usefixtures("page_html")
def test_js_settle_binds_to_rendered_vault_evidence(node_harness):
    """round-3 HIGH-1 门: 成功结算必须绑定证据 — GET 里没有该库、或该库
    projection 不可用 (corrupt/缺投影), 都不许说「数字已更新」。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {boot, flush, mkNode, matches} from "./boot.mjs";
const vaultOf = (vid, proj) => ({vault_id: vid, status: proj ? "ok" : "corrupt",
  error: proj ? null : "ValueError: 坏投影", projection: proj});
function world(getJson) {
  const b = boot({
    getJson,
    postJson: () => ({ok: true, status: 200, json: async () =>
      ({rebuilt: true, reason: "rebuilt", rebuild_count: 7})}),
  });
  return b;
}
function attach(b, vid) {
  const btn = mkNode("btn");
  btn._attrs["data-refresh-vault"] = vid;
  const note = mkNode("note");
  note._attrs["data-note-for"] = vid;
  b.els["cards"]._desc = [btn, note];
  return {btn, note};
}
const click = btn => ({target: {closest: sel => (matches(btn, sel) ? btn : null)}});

test("① 目标库投影 corrupt → 结算成同步失败, 不许说数字已更新", async () => {
  const badProj = {vaults: [vaultOf("cs_61b", null)]};
  const b = world(() => ({ok: true, status: 200, json: async () => badProj}));
  await flush();
  const {btn, note} = attach(b, "cs_61b");
  await b.handlers["cards::click"](click(btn));
  await flush();
  assert.match(note.innerHTML, /同步失败/, "corrupt 投影不许沾 GET 成功的光");
  assert.ok(!note.innerHTML.includes("数字已更新"));
});
test("② GET 里没有目标库 → 同样结算成同步失败", async () => {
  const without = {vaults: [vaultOf("别的库", {due_count: 1, boards: [], bucket_counts: null,
    generated_at: "g", due_new_count: 0, placeholder_backlog: 0})]};
  const b = world(() => ({ok: true, status: 200, json: async () => without}));
  await flush();
  const {btn, note} = attach(b, "cs_61b");
  await b.handlers["cards::click"](click(btn));
  await flush();
  assert.match(note.innerHTML, /同步失败/, "目标库从聚合里消失 = 没有更新证据");
  assert.ok(!note.innerHTML.includes("数字已更新"));
});
test("③ 有证据 (渲染成功 + projection 在) → 才结算成数字已更新", async () => {
  const okProj = {vaults: [vaultOf("cs_61b", {due_count: 9, boards: [], bucket_counts: null,
    generated_at: "fresh", due_new_count: 0, placeholder_backlog: 0})]};
  const b = world(() => ({ok: true, status: 200, json: async () => okProj}));
  await flush();
  const {btn, note} = attach(b, "cs_61b");
  await b.handlers["cards::click"](click(btn));
  await flush();
  assert.match(note.innerHTML, /数字已更新/);
  assert.match(b.els["cards"].innerHTML, /生成于 fresh/);
});
""",
    )
    _assert_node_green(proc)


@pytest.mark.usefixtures("page_html")
def test_js_stale_get_cannot_settle_rebuild(node_harness):
    """round-4 HIGH-1 因果锚门: GET 启动早于重建完成时, 哪怕它是最新代际、
    哪怕响应合法, 也无权结算「数字已更新」——重建后切后台导致没有新 GET 的
    场景下, 重建前投影不许冒充重建后状态。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {boot, flush, mkNode, matches} from "./boot.mjs";
const OK = {vaults: [{vault_id: "cs_61b", status: "ok", error: null,
  projection: {due_count: 3, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
    generated_at: "pre-rebuild", next_upcoming: null, boards: []}}]};
const deferreds = [];
function deferredGet() {
  let resolve;
  const promise = new Promise(r => { resolve = r; });
  deferreds.push({resolve});
  return {ok: true, status: 200, json: () => promise};
}
// 隐藏态启动: 首轮 GET (gen 1) 照发且挂起 — 这就是那条「启动早于重建」的旧 GET
const b = boot({
  getJson: deferredGet,
  postJson: () => ({ok: true, status: 200, json: async () =>
    ({rebuilt: true, reason: "rebuilt", rebuild_count: 9})}),
  hidden: true,
});
const btn = mkNode("btn");
btn._attrs["data-refresh-vault"] = "cs_61b";
const note = mkNode("note");
note._attrs["data-note-for"] = "cs_61b";
b.els["cards"]._desc = [btn, note];
const click = {target: {closest: sel => (matches(btn, sel) ? btn : null)}};

test("① 旧 GET 在飞时完成 rebuild → 不许结算成功 (因果锚)", async () => {
  await b.handlers["cards::click"](click);   // hidden → rebuilt 不触发新 GET (LOW-2)
  assert.equal(b.calls.get, 1, "隐藏时 rebuilt 不得触发新 GET");
  const stale = deferreds.pop();
  stale.resolve(OK);                          // 旧 GET 此刻才返回重建前投影
  await flush();
  assert.match(note.innerHTML, /正在同步最新数字/, "旧 GET 无权结算 — pending 留着");
  assert.ok(!note.innerHTML.includes("数字已更新"), "重建前投影不许冒充重建后状态");
  assert.ok(!b.els["cards"].innerHTML.includes("数字已更新"));
});
test("② 回前台 → 新 GET (启动晚于重建) 正常结算", async () => {
  b.document.hidden = false;
  b.handlers["document::visibilitychange"]();
  const d2 = deferreds.pop();
  d2.resolve(OK);
  await flush();
  assert.match(b.els["cards"].innerHTML, /数字已更新/, "因果合法的 GET 完成结算");
  assert.ok(!b.els["cards"].innerHTML.includes("正在同步"));
});
""",
    )
    _assert_node_green(proc)


@pytest.mark.usefixtures("page_html")
def test_js_causal_anchor_survives_same_millisecond(node_harness):
    """round-5 BLOCKER-1 门: 因果锚不许依赖时间戳的**分辨率**。

    上一版用 `startMs < n.atMs` 比较毫秒时间戳。重建完成与旧 GET 启动落在
    同一毫秒时该式为假, 于是重建前的投影冒充了重建后状态 —— 而这在本机
    环回 + 快后端下完全可能发生。本门把 `Date.now` 冻结成常量, 把「同毫秒」
    从偶发变成必然: 时间戳实现下本门必红, 代际 (pollGen 严格递增) 实现下才绿。
    """
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {boot, flush, mkNode, matches} from "./boot.mjs";
const OK = {vaults: [{vault_id: "cs_61b", status: "ok", error: null,
  projection: {due_count: 3, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
    generated_at: "pre-rebuild", next_upcoming: null, boards: []}}]};

test("冻结时钟 → 旧 GET 与 rebuild 同毫秒, 仍无权结算", async () => {
  const realNow = Date.now;
  Date.now = () => 1788000000000;   // 重建完成与旧 GET 启动落在同一毫秒
  try {
    const deferreds = [];
    const b = boot({
      getJson: () => {
        let resolve;
        const promise = new Promise(r => { resolve = r; });
        deferreds.push({resolve});
        return {ok: true, status: 200, json: () => promise};
      },
      postJson: () => ({ok: true, status: 200, json: async () =>
        ({rebuilt: true, reason: "rebuilt", rebuild_count: 9})}),
      hidden: true,   // rebuilt 不触发新 GET → 旧 GET 仍是最新代际
    });
    const btn = mkNode("btn");
    btn._attrs["data-refresh-vault"] = "cs_61b";
    const note = mkNode("note");
    note._attrs["data-note-for"] = "cs_61b";
    b.els["cards"]._desc = [btn, note];
    await b.handlers["cards::click"]({target: {closest: sel => (matches(btn, sel) ? btn : null)}});
    assert.equal(b.calls.get, 1, "前提: 隐藏时 rebuilt 不得触发新 GET");
    deferreds.pop().resolve(OK);   // 旧 GET 此刻才返回重建前投影
    await flush();
    assert.match(note.innerHTML, /正在同步最新数字/, "同毫秒不是「更晚」— pending 必须留着");
    assert.ok(!note.innerHTML.includes("数字已更新"),
      "时间戳比较在同毫秒下失效, 重建前投影会冒充重建后状态");
  } finally {
    Date.now = realNow;
  }
});
""",
    )
    _assert_node_green(proc)


@pytest.mark.usefixtures("page_html")
def test_js_hidden_rebuilt_defers_get_and_own_key_status_meta(node_harness):
    """round-3 LOW-2/LOW-3 门: 隐藏时 rebuilt 不触发 GET (pending 留给回前台
    的 poll 结算); "constructor" 这类继承键名走灰徽标兜底; freshNotes 返回
    null-prototype 对象。"""
    proc = _run_node(
        node_harness,
        r"""
import test from "node:test";
import assert from "node:assert/strict";
import {boot, flush, mkNode, matches} from "./boot.mjs";
const OK = {vaults: [{vault_id: "cs_61b", status: "ok", error: null,
  projection: {due_count: 2, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
    generated_at: "g", next_upcoming: null, boards: []}}]};
test("隐藏时 rebuilt → 不发 GET, pending 留给回前台结算", async () => {
  const b = boot({
    getJson: () => ({ok: true, status: 200, json: async () => OK}),
    postJson: () => ({ok: true, status: 200, json: async () =>
      ({rebuilt: true, reason: "rebuilt", rebuild_count: 2})}),
    hidden: true,   // 隐藏态: 首轮 GET 照发 (LOW-3 已声明), 隐藏期间不排程
  });
  await flush();
  const before = b.calls.get;
  const btn = mkNode("btn");
  btn._attrs["data-refresh-vault"] = "cs_61b";
  const note = mkNode("note");
  note._attrs["data-note-for"] = "cs_61b";
  b.els["cards"]._desc = [btn, note];
  await b.handlers["cards::click"]({target: {closest: sel => (matches(btn, sel) ? btn : null)}});
  assert.equal(b.calls.get, before, "隐藏时 rebuilt 不得触发 GET (round-3 LOW-2)");
  b.document.hidden = false;
  b.handlers["document::visibilitychange"]();   // 回前台 → poll → 结算
  await flush();
  assert.match(note.innerHTML, /数字已更新/, "回前台后的 poll 完成结算");
});
test("freshNotes 返回 null-prototype 对象 (round-3 M1 补口)", async () => {
  const b = boot({getJson: () => ({ok: true, status: 200, json: async () => OK})});
  await flush();
  const btn = mkNode("btn");
  btn._attrs["data-refresh-vault"] = "cs_61b";
  const note = mkNode("note");
  note._attrs["data-note-for"] = "cs_61b";
  b.els["cards"]._desc = [btn, note];
  await b.handlers["cards::click"]({target: {closest: sel => (matches(btn, sel) ? btn : null)}});
  const fn = b.api.freshNotes(Date.now());
  assert.equal(Object.getPrototypeOf(fn), null, "freshNotes 产物不得带 Object.prototype");
});
test("status='constructor' → 走灰徽标兜底, 不命中继承属性", () => {
  const b = boot();
  const h = b.api.renderVaultCard({vault_id: "v", status: "constructor", error: null,
    projection: null}, 0);
  assert.match(h, /constructor/, "原字面灰徽标");
  assert.match(h, /#6b7280/);
  assert.ok(!h.includes("今日投影"));
});
""",
    )
    _assert_node_green(proc)
