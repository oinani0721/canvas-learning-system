"""负控 runner —— 两份 TZ 副本的变异测试（CARD-G6-9c-R3, BATCH-2026-09-18-第十五批）。

这个文件替代了 R2 分支上那个只活在 `_bmad-output/` 里的独立脚本 `negctl.py`（399 行）。
搬进树里不是为了好看，是因为那个脚本有三个让它**报绿而实际没测到东西**的缺陷：

1. **空操作检测缺席** —— `preflight()` 只核「锚点在源码里命中 1 次」，不核 `old != new`，
   更不核变异后 AST 是否真的变了。于是「old 与 new 只差一个注释 / 只差空白」的段会
   一路跑成 PASS，而被测的门**根本没被拆过**。本文件把这三条都变成**预检**，任何一条
   不成立就让该段 **ERROR**（不是 PASS、也不是 skip —— 它是「这段没测成」，
   而「没测成」与「测了没发现问题」必须在报告里长得不一样）。
2. **判红靠 rc + 文本锚** —— 原脚本用 `rc != 0 and not not_found` 加 `must in out` 判定
   「门红了」。`rc != 0` 可能来自 import 失败、收集错误、超时；`must in out` 可能命中
   另一条测试的输出。本文件改成**按 oracle 身份判**：每段点名一个 oracle 函数，
   断言它对**变异体**抛 AssertionError、对**原件**通过。红在别处一律不算。
3. **生产文件落盘** —— 原脚本就地改生产文件再还原，还原窗口内任何并发读者（另一个
   pytest、另一条车道）看到的都是变异态。本文件的变异体只写 `tmp_path`，生产文件
   从头到尾不动，并由测试**自己**断言跑前跑后 sha256 相同。

⛔ 三段在 R2 负控上「存活」（施了变异门却不红）的真因，本卡查清并如实记在这里 ——
   它们**不是**空操作，old/new 确实不同、AST 确实变了：

   · `COLONPOSIX` 拆的是 `display_tz()` 里那道 `if not env_tz.startswith(":")`。
     实测（本卡探针）：把它改成 `if True:` 之后，`parse_posix_tz` 层与 `display_tz` 层
     **都零观测差异**。因为以 `:` 开头的串在正则那一层就已经被 std 名第三支的
     `(?![<:])` 前瞻拒掉了 —— 两层互为冗余，拆任何一层都看不见。
     本文件因此把 COLONPOSIX 的变异改打在**真正承载这条性质的那一层**（正则前瞻），
     并把 oracle 打在 `parse_posix_tz` 上而不是 `display_tz` 上。
   · `ASCII` / `RULEA` 拆的是 ⑤ 与规则字段的两道 `isascii()` 检查。实测：在当前正则下
     它们**恒真**（192 条匹配成功的样本里触发 0 次）—— 因为正则的数字字段写的是
     `[0-9]`（ASCII only），交到它们手里的每一段本来就只可能是 ASCII 数字。
     但它们**不是死代码**：把正则的 `[0-9]` 放宽成 `\\d`（Python 的 `\\d` 连全角与
     阿拉伯数字一起吃）之后，这两道检查**会**接住，而删掉它们就接不住了。
     所以它们是货真价实的**纵深第二层**，只是第一层太严、平时轮不到它们说话。
     本文件为这两段配的 oracle 因此先把**该模块自己的**正则放宽，再问第二层 ——
     这样测到的恰好是它们各自承载的东西，而不是被第一层挡住的东西。

⚠️ 一句方法论，给下一个写负控的人：变异「存活」有三种可能 —— 门真有缺口 / 变异是空操作 /
   **变异拆的不是承载那条性质的那一层**。第三种最容易被读成第一种，然后有人去给一道
   本来就有效的门再加一层，缺口却仍在别处。先问「这条性质是谁在扛」，再决定拆谁。
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import re
import sys
import time
import types
from datetime import datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_COPY = REPO_ROOT / "scripts" / "local_tz.py"
BACKEND_COPY = REPO_ROOT / "backend" / "app" / "core" / "display_tz.py"
COPIES = {"scripts": SCRIPTS_COPY, "backend": BACKEND_COPY}


# ─────────────────────────── 加载与变异基础设施 ───────────────────────────


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_source(src_text: str, mod_name: str, tmp_dir: Path) -> types.ModuleType:
    """把一段源码作为**独立模块**加载。

    ⛔ `sys.modules[mod_name] = mod` 必须在 `exec_module` **之前** —— 模块里任何
    `@dataclass` 或其它需要回查自己模块的自省都会取 `sys.modules[cls.__module__]`，
    先 exec 后登记会在 Python 3.12+ 上抛 KeyError（第十批 X6 的同型坑）。
    """
    path = tmp_dir / f"{mod_name}.py"
    path.write_text(src_text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec is not None and spec.loader is not None, f"无法为 {path} 造 spec"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(mod_name, None)
        raise
    return mod


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    """去掉模块 / 函数 / 类的 docstring —— 只改文案的「变异」必须被认成空操作。"""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None)
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                node.body = body[1:] or [ast.Pass()]
    return tree


def _ast_fingerprint(src_text: str) -> str:
    """源码的**结构**指纹：注释天然不进 AST，docstring 由上面那步剥掉。

    这是「old 与 new 只差注释」这类空操作的检测口径 —— 指纹相同 = 代码没变。
    """
    return ast.dump(_strip_docstrings(ast.parse(src_text)), include_attributes=False)


def _regex_pattern_of(src_text: str) -> str:
    """从源码里取出 `_POSIX_TZ_RE = re.compile(<字面量>)` 的那个模式串。

    用 AST 而不是正则去捞 —— 模式串本身满是括号与转义，用正则捞正则是自找的。
    Python 在解析期就把隐式拼接的相邻字符串字面量合成了一个 `Constant`，
    所以这里 `args[0]` 直接就是完整模式。
    """
    tree = ast.parse(src_text)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "_POSIX_TZ_RE" for t in node.targets):
            call = node.value
            assert isinstance(call, ast.Call), "_POSIX_TZ_RE 不是 re.compile(...) 调用"
            return ast.literal_eval(call.args[0])
    raise AssertionError("源码里找不到 _POSIX_TZ_RE 的赋值 —— 提取器失效（不是被测代码的问题）")


def _widen_digit_class(mod: types.ModuleType, src_text: str) -> None:
    """把**该模块自己的** `_POSIX_TZ_RE` 的 `[0-9]` 放宽成 `\\d`，就地替换。

    只给 ASCII / RULEA 两段的 oracle 用：它们守的是「第一层放宽时第二层要接住」，
    不先放宽第一层就问不到它们头上（这正是 R2 负控里这两段「存活」的原因）。
    """
    pat = _regex_pattern_of(src_text)
    assert "[0-9]" in pat, "正则里没有 [0-9] —— 放宽器的前提不成立，oracle 会跑在错的场景上"
    mod._POSIX_TZ_RE = re.compile(pat.replace("[0-9]", r"\d"))


# ─────────────────────────────── oracle 们 ───────────────────────────────
#
# 约定：oracle(mod, src_text) 通过则正常返回，不通过则抛 AssertionError。
# 每个 oracle 只问**一件**事，且那件事必须是它点名的那段变异所承载的。

_WINTER = datetime(2026, 1, 15, 12)
_SUMMER = datetime(2026, 7, 15, 12)


def _oracle_colonposix(mod, src_text) -> None:
    """前导冒号的语义是「这是一个路径」，不是 POSIX 规格串。

    C 库对 `:AAA-1` / `:EST5EDT,M3.2.0,M11.1.0` 一律给 UTC —— 剥一个冒号当路径找，
    找不到就结束，**不会**再拿整串去试规格。判据打在 `parse_posix_tz` 而不是
    `display_tz`：后者上面还压着一道 `if not env_tz.startswith(":")`，两层互为冗余，
    从 `display_tz` 问过去看不见这一层的死活。
    """
    for spec in (":AAA-1", ":EST5EDT,M3.2.0,M11.1.0", ":ABC5"):
        assert mod.parse_posix_tz(spec) is None, (
            f"前导冒号串 {spec!r} 被当成 POSIX 规格串收下了 —— C 库对它退 UTC。冒号前缀必须只走路径解析这一条路。"
        )


def _oracle_h1_quoted_name(mod, src_text) -> None:
    """r12 H1：引用名扫不到闭合 `>` 时**不得**回退成裸名把 `<` 吃进去。

    libc 对 `<AAA1><BBB2` 全年 UTC（拒）。实现若回退成裸名，会解析成
    「名字 `<AAA`＋偏移 1＋dst 名 `><BBB`＋dst 偏移 2」⇒ 冬 −01:00 夏 −02:00，
    整整差一到两个小时，而且它**不报错**，只是每天把「今天」算偏。
    """
    assert mod.parse_posix_tz("<AAA1><BBB2") is None, (
        "`<AAA1><BBB2` 被接受了 —— libc 对它退 UTC。引用名一旦以 `<` 开头就必须闭合，不能回退成裸名。"
    )
    for spec in ("<AAA1", "<1", "<<AAA1"):
        assert mod.parse_posix_tz(spec) is not None, (
            f"{spec!r} 被拒了 —— 这一族 libc 是**接受**的（扫不到 `>` ⇒ 整个当裸名）。"
            "H1 的修复不能顺手把它们一起拒掉（那是误拒，不是修复）。"
        )


def _oracle_h2_offset_colon(mod, src_text) -> None:
    """r12 H2：偏移里的冒号解析失败后，残形**不得**被重新分词成 dst 名。

    libc 对 `AAA1:` 与 `AAA1:30:BBB2` 都退 UTC —— 偏移之后的 `:` 属于偏移
    （后面必须跟数字）。而偏移**吃满三段**之后多出来的 `:` 才轮到 dst 名，
    C 库的 tzname 对那一族明确打成 `(':', 'ABC')`。两个方向一起断言，修复才不会
    滑到「一律拒冒号」那种过度收紧上去。

    ⛔ 正例**不能**用 `ABC1:30:2:30`（本卡第一版就这么写，被预检④当场抓住）:
       它的 dst 偏移是 `30` ⇒ −30 h，会被 ⑧ 的量级检查拒掉 —— 那是一条**已声明的
       收紧**，与 H2 无关。拿它当正例等于让这道门去红一件生产代码有意为之的事。
       换成 dst 偏移在 ±24h 内的同族串（`ABC1:30:2:3` 等，libc 与本实现都收）。
    """
    for spec in ("AAA1:", "AAA1:30:", "AAA1:30:BBB2", "AAA1:BBB2"):
        assert mod.parse_posix_tz(spec) is None, (
            f"{spec!r} 被接受了 —— libc 对它退 UTC。偏移没吃满三段时，"
            "后面那个 `:` 还属于偏移，不能改判成 dst 名的首字符。"
        )
    for spec in ("ABC1:30:2:3", "ABC1:2:3:4", "ABC0:0:0:1"):
        assert mod.parse_posix_tz(spec) is not None, (
            f"{spec!r} 被拒了 —— libc **接受**它（tzname 打成 (':', 'ABC')，dst 名就是 `:`）。"
            "H2 的修复不能把偏移吃满三段之后的那个冒号也一起禁掉。"
        )


def _oracle_h3_linear(mod, src_text) -> None:
    """r12 H3：分词耗时对输入长度**线性**，不得平方/指数。

    探针是「长名字 + 一个不合法的尾字符」：`'A' + '١'*n + '+'`（阿拉伯数字对正则
    来说是普通名字字符）与纯 ASCII 的 `'A'*n + '+'`。R2 靠占有量词禁止回溯，本卡
    撤掉占有量词之后靠的是「std_off 必填 ⇒ std 名贪婪终点唯一」这条文法性质 ——
    所以这道计时门在本卡是**承重**判据，不是装饰：它是唯一能证明平方没被放回来的东西。

    ⚠️ 别改用 `'A'*n + '!'` 当探针：`!` 是合法名字字符，那串会直接匹配成功，
       量到的是成功路径而不是失败路径。

    ⛔ 判据口径与 `test_g6_9c_single_tz_source.py::test_r12_h3_*` 逐条同步 —— 两边
       必须同口径，否则同一段变异在两个文件里会给出相反结论。要点复述一遍：
       · 主判据是**不依赖比值**的绝对门 `n=3232 ≤ 0.05 s`（基线 ≈0.0001 s，
         平方态 ≈0.53 s）；小 n 上的绝对门抓不住平方（平方态 n=808 才 0.035 s）。
       · 比值按**相邻比**读（线性 ≈1.9 / 平方 ≈3.5~4.0）；`t(808)/t(202) ≤ 3`
         那个读法对真正线性的实现也会红 —— 长度是 4 倍，线性耗时本来就 ≈4 倍。
       · 计时取 **min-of-5**：微秒量级上调度噪声与被测量同量级。
    """

    def _best(mod_, probe, repeat=5):
        best = float("inf")
        for _ in range(repeat):
            start = time.perf_counter()
            mod_.parse_posix_tz(probe)
            best = min(best, time.perf_counter() - start)
        return best

    for label, make in (("arabic", lambda n: "A" + "١" * n + "+"), ("ascii", lambda n: "A" * n + "+")):
        elapsed = {n: _best(mod, make(n)) for n in (202, 404, 808, 3232)}
        assert elapsed[202] <= 0.05, f"[{label}] n=202 耗时 {elapsed[202]:.6f}s > 0.05s —— 分词在回溯。"
        assert elapsed[3232] <= 0.05, (
            f"[{label}] n=3232 耗时 {elapsed[3232]:.6f}s > 0.05s —— 分词不是线性"
            f"（基线约 0.0001s，把 std_off 改回可选的平方态约 0.53s）。"
        )
        for smaller, bigger in ((202, 404), (404, 808)):
            ratio = elapsed[bigger] / max(elapsed[smaller], 1e-9)
            assert ratio <= 3.0, (
                f"[{label}] 长度翻倍耗时比 t({bigger})/t({smaller}) = {ratio:.2f} > 3 —— 不是线性。"
                f"（202:{elapsed[202]:.6f}s 404:{elapsed[404]:.6f}s"
                f" 808:{elapsed[808]:.6f}s 3232:{elapsed[3232]:.6f}s）"
            )


def _oracle_h4_overlong(mod, src_text) -> None:
    """r12 H4：超长数字字段**不得抛**，且要与 libc 同判。

    `AAA` + 4300 个 `0` + `1` 是 C 库接受的合法串（给 −01:00）。Python 3.11+ 对
    >4300 位的整数字符串转换直接抛 `ValueError: Exceeds the limit` ⇒ 不先剥前导零
    就会让 `display_tz()` 整个抛出去，模块级启动校验跟着挂。
    ⛔ 修法必须是「剥零后再限长」而不是「捕获后拒绝」—— 后者会把这条**合法**串误拒。
    """
    spec = "AAA" + "0" * 4300 + "1"
    try:
        tz = mod.parse_posix_tz(spec)
    except Exception as exc:  # noqa: BLE001 — 抛出来本身就是缺陷，类型不重要
        raise AssertionError(
            f"超长数字字段让解析器抛了 {type(exc).__name__}: {exc} —— "
            "libc 接受这条串并给 −01:00，抛异常会让整个 display_tz() 挂掉。"
        ) from exc
    assert tz is not None, (
        "超长前导零串被拒了 —— libc **接受**它（给 −01:00）。H4 的修法是剥零后限长，不是捕获异常后一律拒。"
    )
    assert str(tz.utcoffset(_WINTER)) == "-1 day, 23:00:00", (
        f"超长前导零串算出的偏移是 {tz.utcoffset(_WINTER)}，libc 给的是 −01:00。"
    )


def _oracle_ascii_depth(mod, src_text) -> None:
    """⑤ 的 `isascii()`：当正则的数字类被放宽时，**第二道防线**要接住非 ASCII 数字。

    先把该模块自己的 `_POSIX_TZ_RE` 的 `[0-9]` 换成 `\\d`（Python 的 `\\d` 连全角与
    阿拉伯数字一起吃），再问它收不收 `AAA1,M3.2.0/２,M11.1.0`。libc 对全角一律退 UTC。
    不先放宽第一层就问不到 ⑤ 头上 —— 那正是 R2 负控里这一段「存活」的原因。
    """
    _widen_digit_class(mod, src_text)
    for spec in (
        "AAA1,M3.2.0/２,M11.1.0",  # 全角 ２ 在切换时刻里
        "AAA1,M3.2.0/٢,M11.1.0",  # 阿拉伯 ٢ 在切换时刻里
    ):
        assert mod.parse_posix_tz(spec) is None, (
            f"正则数字类放宽后，{spec!r} 里的非 ASCII 数字没有被 ⑤ 接住 —— "
            "libc 对这一族退 UTC。⑤ 是纵深第二层，第一层一放宽它就必须说话。"
        )
    assert mod.parse_posix_tz("AAA1,M3.2.0/2,M11.1.0") is not None, (
        "正则数字类放宽后，纯 ASCII 的正例也被拒了 —— ⑤ 收得过宽了。"
    )


def _oracle_rulea_depth(mod, src_text) -> None:
    """规则字段的 `isascii()`：同 ⑤，守的是 `Jn` / `Mm.w.d` 里的非 ASCII 数字。

    `J３60`（全角 ３）这一族 libc 退 UTC。同样先放宽第一层再问第二层。
    """
    _widen_digit_class(mod, src_text)
    for spec in (
        "AAA1,J３60,J365",  # 全角 ３ 在 Jn 里
        "AAA1,M３.2.0,M11.1.0",  # 全角 ３ 在 Mm.w.d 里
        "AAA1,３,M11.1.0",  # 全角 ３ 在裸 n 里
    ):
        assert mod.parse_posix_tz(spec) is None, (
            f"正则数字类放宽后，规则字段 {spec!r} 里的非 ASCII 数字没有被接住 —— libc 对这一族退 UTC。"
        )
    assert mod.parse_posix_tz("AAA1,J60,J365") is not None, (
        "正则数字类放宽后，纯 ASCII 的规则正例也被拒了 —— 规则字段校验收得过宽。"
    )


def _oracle_key_utf8(mod, src_text) -> None:
    """既有缺口①：不可严格 UTF-8 编码的 TZ 串不得被接受，代理字符不得进 `.key`。

    `os.environ` 走 `surrogateescape` 解码，坏字节会变成 U+DC80..U+DCFF 的代理字符。
    放行的话它一路进 `.key`、进 API 响应，在 `JSONResponse` 的编码边界才炸 ——
    那是**移位**不是修复（本卡 r5→r6 在这上面栽过两次）。判据打在 encode 那一步，
    不是 `json.dumps`：后者默认 `ensure_ascii=True` 不抛，是现成的假绿。

    ⛔ 断言必须同时盖住「**解析器自己抛**」这一支（本卡第一版漏了，主判据当场报
       `UnicodeEncodeError` 而不是 AssertionError）: 实测拆掉 ④ 之后，代理字符根本
       走不到 `.key`，它在 ⑦ 算名字字节数的 `_strip_name(...).encode("utf-8")` 处
       就炸了。抛异常与放行代理字符是**同一个缺陷的两种落点**，而且抛比放行更糟 ——
       `display_tz()` 是模块级启动路径上的调用，抛出去整条复习链起不来。
    """
    for spec in ("AAA\udcff1", "<AAA\udc80>-1", "AAA1BBB\udcfe2,M3.2.0,M11.1.0", "AAA1\udcff"):
        try:
            tz = mod.parse_posix_tz(spec)
        except Exception as exc:  # noqa: BLE001 — 抛出来本身就是缺陷，类型不重要
            raise AssertionError(
                f"{spec!r} 让解析器抛了 {type(exc).__name__}: {exc} —— "
                "不可编码的 TZ 串必须在入口被**拒**（返回 None），不能抛: "
                "display_tz() 在模块级启动路径上被调用，抛出去整条链起不来。"
            ) from exc
        if tz is None:
            continue
        key = getattr(tz, "key", None)
        assert key is not None, f"{spec!r} 被接受但没有 .key —— 形态意外，判据不成立"
        try:
            key.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise AssertionError(
                f"{spec!r} 的 .key={key!r} 编不成 UTF-8 —— 它会一路进响应，在序列化边界炸。"
                "整串编码校验必须在解析入口就拒，不能靠下游兜。"
            ) from exc


def _oracle_offset_range(mod, src_text) -> None:
    """既有缺口②：|偏移| ≥ 24h 必须在解析期就拒，不能留到 `utcoffset()` 才抛。

    Python 的 `tzinfo` 要求偏移严格小于 24 小时。C 库**不**拒这些串（`AAA24BBB`
    实测 tzset 成功、tm_gmtoff=−82800），所以这是本实现为「全年可表示」做的收紧，
    如实声明。要紧的是它必须发生在**解析期**：留到消费时抛，落点不可预测。

    ⛔ 判据**不能**打在 `tz.utcoffset(dt)` 上（本卡第一版就这么写，主判据报
       DID NOT RAISE）: 实测拆掉 ⑧ 之后 `AAA24` 的 `utcoffset()` 老老实实**返回**
       `-1 day, 0:00:00`，一点不抛 —— 抛的是 `datetime(..., tzinfo=tz)` 在
       `.isoformat()` / `.astimezone()` 里对偏移做范围检查那一步。
       判据必须打在**生产代码真正会走的那一步**上: `daily_review_pick.py` 的
       payload 正是 `now.astimezone(_display_tz()).isoformat(...)`。
    ⛔ 探针也不能随手挑: `AAA999BBB` / `AAA0:60BBB` 在拆掉 ⑧ 之后**仍然被拒**
       （分钟越界等别的检查先拦下了），拿它们当探针这道门永远红不了。
    """
    probed = 0
    for spec in ("AAA24", "AAA25", "AAA24BBB,M3.2.0,M11.1.0"):
        tz = mod.parse_posix_tz(spec)
        if tz is None:
            continue
        probed += 1
        for probe in (_WINTER, _SUMMER):
            try:
                probe.replace(tzinfo=tz).isoformat()
            except Exception as exc:  # noqa: BLE001
                raise AssertionError(
                    f"{spec!r} 被解析器接受，却在 isoformat() 上抛 "
                    f"{type(exc).__name__}: {exc} —— 越界偏移必须在**解析期**拒掉。"
                    "留到消费点才炸是移位不是修复，而消费点就是每天那条推送的 payload。"
                ) from exc
    assert probed == 0, f"越界偏移串里有 {probed} 条被解析器接受了 —— ⑧ 的量级检查必须在解析期拒掉它们。"


# ─────────────────────────────── 变异集 ───────────────────────────────
#
# 每段 = (段名, old, new, oracle, 这段在守什么)。
# ⛔ old 必须在**两份副本**里都恰好命中 1 次 —— 两份是逐字节同源的，命中数不同
#    本身就说明同源已经破了，那时该红的是同源门，不是这里。

_SEG_COLONPOSIX = (
    r"|(?![<:])[^0-9+,\-\x00]*)",
    r"|(?!<)[^0-9+,\-\x00]*)",
)
_SEG_H1BARE = (
    r"|(?![<:])[^0-9+,\-\x00]*)",
    r"|(?!:)[^0-9+,\-\x00]*)",
)

MUTATIONS = [
    (
        "COLONPOSIX",
        _SEG_COLONPOSIX[0],
        _SEG_COLONPOSIX[1],
        _oracle_colonposix,
        "std 名第三支只放开前导 `:` ⇒ `:AAA-1` 会被当成 POSIX 规格串收下",
    ),
    (
        "H1BARE",
        _SEG_H1BARE[0],
        _SEG_H1BARE[1],
        _oracle_h1_quoted_name,
        "std 名第三支只放开前导 `<` ⇒ `<AAA1><BBB2` 回退成裸名被误收",
    ),
    (
        "H2COLON",
        '            if g["std_off"].lstrip("+-").count(":") < 2:\n                return None\n',
        "            if False:\n                return None\n",
        _oracle_h2_offset_colon,
        "拆掉「偏移没吃满三段时 dst 名不得以 `:` 开头」⇒ `AAA1:` 被误收",
    ),
    (
        "H3QUANT",
        '    r"(?P<std_off>[+-]?[0-9]+(?::[0-9]+(?::[0-9]+)?)?)"\n',
        '    r"(?P<std_off>[+-]?[0-9]+(?::[0-9]+(?::[0-9]+)?)?)?"\n',
        _oracle_h3_linear,
        "把 std_off 改回**可选** ⇒ std 名与 dst 名重新能瓜分同一串 ⇒ 平方回溯回来",
    ),
    (
        "H4ZERO",
        '            digits = parts[i].lstrip("0") or "0"\n'
        "            if len(digits) > 10:\n"
        "                return 86400 * 400  # 必被 ⑧ 的 |偏移| < 24h 拒掉\n",
        "            digits = parts[i]\n"
        "            if len(digits) > 10:\n"
        "                return 86400 * 400  # 必被 ⑧ 的 |偏移| < 24h 拒掉\n",
        _oracle_h4_overlong,
        "偏移字段不再剥前导零 ⇒ 合法的 4300 位前导零串被**拒**（oracle 红在「被拒了」那条断言，\n"
        "         不是红在 int() 抛异常 —— 剥零逻辑没了之后 _posix_offset_seconds 会先返回\n"
        "         86400*400 这个必被 ⑧ 拒掉的哨兵值，所以表现是误拒而非抛）",
    ),
    (
        "ASCII",
        "        if not all(x.isascii() and x.isdigit() for x in _f):\n            return None\n",
        "        if False:\n            return None\n",
        _oracle_ascii_depth,
        "拆掉 ⑤ 的纵深第二层 ⇒ 正则一放宽，全角数字就进得来",
    ),
    (
        "RULEA",
        '        if _txt is not None and not _txt.lstrip("JM").replace(".", "").isascii():\n            return None\n',
        "        if False:\n            return None\n",
        _oracle_rulea_depth,
        "拆掉规则字段的纵深第二层 ⇒ 正则一放宽，`J３60` 就进得来",
    ),
    (
        "KEYUTF8",
        '    try:\n        spec.encode("utf-8")\n    except UnicodeEncodeError:\n        return None\n',
        "    try:\n        pass\n    except UnicodeEncodeError:\n        return None\n",
        _oracle_key_utf8,
        "拆掉整串 UTF-8 可编码校验 ⇒ 解析器在 ⑦ 算名字字节数时就抛 UnicodeEncodeError\n"
        "         （oracle 红在「让解析器抛了」那条断言）。代理字符其实走不到 `.key`，\n"
        "         更走不到响应序列化 —— 但抛比放行更糟：display_tz() 在模块级启动路径上",
    ),
    (
        "HMAX",
        "    if abs(std_off) >= 86400:\n        return None\n",
        "    if False:\n        return None\n",
        _oracle_offset_range,
        "拆掉 ⑧ 的量级检查 ⇒ |偏移| ≥ 24h 被接受，红在 `isoformat()`（不是 `utcoffset()` —— \n"
        "         后者老老实实返回 -1 day, 0:00:00 不抛，抛的是 datetime 对偏移做范围检查那一步）",
    ),
]

_IDS = [f"{name}-{copy_id}" for name, *_ in MUTATIONS for copy_id in sorted(COPIES)]
_CASES = [(seg, copy_id) for seg in MUTATIONS for copy_id in sorted(COPIES)]


@pytest.mark.parametrize(("segment", "copy_id"), _CASES, ids=_IDS)
def test_mutation_is_caught_by_its_named_oracle(segment, copy_id, tmp_path):
    """施一段变异，断言它**点名**的那个 oracle 变红；原件同一 oracle 必须是绿的。

    PASS 的含义是「这段变异被抓住了」，不是「测试跑完了」。四道预检任何一条不成立
    都会让本用例 **ERROR**（= 这段没测成），因为「没测成」和「测了没问题」在报告里
    必须长得不一样 —— R2 那个 runner 就是把前者报成了后者。
    """
    name, old, new, oracle, why = segment
    path = COPIES[copy_id]
    sha_before = _sha256(path)
    src = path.read_text(encoding="utf-8")

    # ── 预检 ①：锚点在源码里恰好命中一次 ──────────────────────────────
    hits = src.count(old)
    assert hits == 1, (
        f"[{name}/{copy_id}] 锚点在 {path} 里命中 {hits} 次（须恰 1）——锚点漂移了，这段变异没测成。\n  锚点: {old!r}"
    )

    # ── 预检 ②：old 与 new 真的不同 ─────────────────────────────────
    assert old != new, f"[{name}/{copy_id}] old 与 new 逐字相同 —— 这段是空操作"

    # ── 预检 ③：变异后 AST 真的变了（注释 / docstring 差异不算） ──────────
    mutated_src = src.replace(old, new)
    assert _ast_fingerprint(mutated_src) != _ast_fingerprint(src), (
        f"[{name}/{copy_id}] 变异前后 AST 指纹相同 —— old 与 new 只差注释或空白，代码一行没动，这段是空操作。"
    )

    # ── 预检 ④：原件必须先让这个 oracle 通过 ────────────────────────────
    pristine = _load_source(src, f"negctl_r3_pristine_{name}_{copy_id}", tmp_path)
    try:
        oracle(pristine, src)
    except AssertionError as exc:
        raise AssertionError(
            f"[{name}/{copy_id}] oracle {oracle.__name__} 对**原件**就是红的 —— "
            f"那是生产代码的缺陷或 oracle 写错了，不是这段变异的功劳。\n  原始失败: {exc}"
        ) from exc

    # ── 主判据：变异体必须让**这个** oracle 红 ──────────────────────────
    mutant = _load_source(mutated_src, f"negctl_r3_mutant_{name}_{copy_id}", tmp_path)
    with pytest.raises(AssertionError) as caught:
        oracle(mutant, mutated_src)
    assert str(caught.value), f"[{name}/{copy_id}] oracle 抛了空消息，无法确认红在哪"

    # ── 收尾：生产文件从头到尾没被碰过 ─────────────────────────────────
    assert _sha256(path) == sha_before, (
        f"[{name}/{copy_id}] 生产文件 {path} 的 sha256 变了 —— 变异体泄漏到生产路径上了。\n"
        f"  跑前: {sha_before}\n  跑后: {_sha256(path)}"
    )


def test_every_mutation_anchor_hits_both_copies_exactly_once():
    """所有锚点在**两份副本**里都恰好命中一次 —— 锚点清单与代码不能悄悄脱节。

    ⛔ 这道门不是上面那条的重复：上面是逐段跑的，某段被 skip / ERROR 时它的锚点
    就没人核。这里一次性核全部，让「锚点集体漂移」有一个单一的红点。
    """
    problems = []
    for name, old, _new, _oracle, _why in MUTATIONS:
        for copy_id, path in sorted(COPIES.items()):
            hits = path.read_text(encoding="utf-8").count(old)
            if hits != 1:
                problems.append(f"{name}/{copy_id}: 命中 {hits} 次（须 1）")
    assert not problems, "变异锚点漂移:\n  " + "\n  ".join(problems)


def test_mutation_set_covers_the_r12_high_findings_and_the_three_survivors():
    """覆盖面验伪锚：r12 四条 HIGH 与 R2 存活的三段必须各有**至少一段**变异守着。

    ⛔ 没有这道门的话，删掉任意一段变异都不会有任何东西变红 —— 变异集会在
    「谁也没注意到」的情况下缩水（记忆里「切片改代码会静默删掉整条测试」的同族）。
    """
    names = {name for name, *_ in MUTATIONS}
    required = {
        "H1BARE": "r12 HIGH-1 引用名裸名回溯",
        "H2COLON": "r12 HIGH-2 冒号偏移误判 dst",
        "H3QUANT": "r12 HIGH-3 灾难性回溯",
        "H4ZERO": "r12 HIGH-4 长数字未捕获异常",
        "COLONPOSIX": "R2 存活变异①",
        "ASCII": "R2 存活变异②",
        "RULEA": "R2 存活变异③",
    }
    missing = {k: v for k, v in required.items() if k not in names}
    assert not missing, f"变异集缺了这些段: {missing}"
    assert len(MUTATIONS) >= 7, f"变异段数 {len(MUTATIONS)} < 7（卡文下限）"
    assert len(_CASES) == len(MUTATIONS) * 2, "每段必须对两份副本各跑一次"
