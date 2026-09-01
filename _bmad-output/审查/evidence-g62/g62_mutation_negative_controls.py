#!/usr/bin/env python3
"""CARD-G6-2 负验证: 机械变异 × 指定门必须变红。

为什么需要它: 「21 个测试全绿」不是「门在工作」的证据 —— 一道从不失败的
门与一道不存在的门在绿色输出里完全同形。本脚本对 review_app.py 逐条施加
**破坏被测行为**的变异, 判据是**指定的那一道门变红**(不是"某处有失败":
后者会把"改坏 A 却只有 B 红"这种门错位当成功)。

Codex round-1 HIGH-4 整改: 「变红」的判据不再是 returncode != 0 ——
exit 4 (nodeid 不存在 / collected 0) / collection error 同样非零, 会把
「门根本没跑」误认证成「门抓住了变异」。现在变红必须同时满足:
pytest 退出非零 **且** stdout 含 "1 failed" **且** short summary 里
FAILED 的正是**指定的那个测试节点** (靠 -rf 强制输出 summary)。

纪律 (前几批踩出来的):
  · **串行**执行 —— 脚本原地改被测文件, 并发会让 B 的还原把 A 的变异写回,
    而测试照样全绿 (第六批教训);
  · 还原后**逐字节**比对备份, 不同即硬失败;
  · 变异必须真的**禁掉那条防线**, 而不是叠一层同义写法 —— 纵深防御会让
    测试仍绿, 于是误判"门非承重";
  · 每条变异先验证 old 串在文件里**唯一命中**, 不命中/多命中即硬失败
    (str.replace 不命中不报错 = 静默空转 = 假绿)。

用法: .venv/bin/python ../_bmad-output/审查/evidence-g62/g62_mutation_negative_controls.py
      (cwd 必须是 backend/)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

BACKEND = Path.cwd()
TARGET = BACKEND / "app" / "api" / "v1" / "endpoints" / "review_app.py"
TESTFILE = "tests/unit/test_review_app.py"
PYTEST = [str(BACKEND / ".venv" / "bin" / "pytest"), "-q", "-rf", "-p", "no:cacheprovider", "-x"]

#: (编号, 说明, old, new, 必须变红的测试节点)
MUTATIONS: list[tuple[str, str, str, str, str]] = [
    # ── 轮询 clamp 与隐藏暂停 (完成条件 c / 默认裁决②) ──────────────
    (
        "M01",
        "取消轮询下限 → 可被 next_due 逼成毫秒级打点",
        "return Math.min(POLL_MAX_MS, Math.max(POLL_MIN_MS, raw));",
        "return Math.min(POLL_MAX_MS, raw);",
        "test_js_poll_interval_clamped_and_visibility_pauses",
    ),
    (
        "M02",
        "取消轮询上限 → 远期 next_due 让页面睡死",
        "return Math.min(POLL_MAX_MS, Math.max(POLL_MIN_MS, raw));",
        "return Math.max(POLL_MIN_MS, raw);",
        "test_js_poll_interval_clamped_and_visibility_pauses",
    ),
    (
        "M03",
        "已过期的 next_due 也参与选取 → 负数周期",
        "if (ms !== null && ms > nowMs && (best === null || ms < best)) best = ms;",
        "if (ms !== null && (best === null || ms < best)) best = ms;",
        "test_js_poll_interval_clamped_and_visibility_pauses",
    ),
    (
        "M04",
        "页面隐藏时仍轮询 → 后台空耗",
        "return hidden ? {cancelTimer: true, pollNow: false} : {cancelTimer: true, pollNow: true};",
        "return {cancelTimer: true, pollNow: true};",
        "test_js_poll_interval_clamped_and_visibility_pauses",
    ),
    # ── 休息日空状态 (完成条件 b) ───────────────────────────────────
    (
        "M05",
        "休息日文案改字 → 与 pick.py 口径分家",
        "✅ 今日无到期节点，休息一天。",
        "✅ 今天没有要复习的。",
        "test_js_rest_day_empty_state_matches_pick_copy",
    ),
    (
        "M06",
        "stale 也走休息日分支 → 过期投影冒充『今天没到期』",
        'if (entry.status === "ok" && proj.due_count === 0) {',
        "if (proj.due_count === 0) {",
        "test_js_rest_day_empty_state_matches_pick_copy",
    ),
    # ── 只消费投影, 不重算到期 (硬边界) ─────────────────────────────
    (
        "M07",
        "按板级明细重加到期数 → JS 私设第二套口径",
        'body = \'<div class="big">到期 <b>\' + proj.due_count + "</b><small> · 新卡 " + proj.due_new_count +',
        'body = \'<div class="big">到期 <b>\' + proj.boards.reduce((a, b) => a + b.due, 0) '
        '+ "</b><small> · 新卡 " + proj.due_new_count +',
        "test_js_shows_authoritative_due_count_never_recomputes",
    ),
    (
        "M08",
        "休息日判定改看 boards 是否为空 → 权威计数被架空",
        'if (entry.status === "ok" && proj.due_count === 0) {',
        'if (entry.status === "ok" && !proj.boards.length) {',
        "test_js_shows_authoritative_due_count_never_recomputes",
    ),
    (
        "M09",
        "板行到期数改按 nodes 长度重数",
        '(r.due ? "<b>" + r.due + "</b>" : \'<span style="color:#9ca3af">0</span>\')',
        '((r.nodes || []).length ? "<b>" + (r.nodes || []).length + "</b>" '
        ': \'<span style="color:#9ca3af">0</span>\')',
        "test_js_shows_authoritative_due_count_never_recomputes",
    ),
    # ── 四态与降级 (完成条件 b) ─────────────────────────────────────
    (
        "M10",
        "去掉未知 status 的兜底 → 新增状态白屏/崩 (own-key 版锚点)",
        'const meta = Object.prototype.hasOwnProperty.call(STATUS_META, entry.status)\n'
        '    ? STATUS_META[entry.status] : [entry.status, "#6b7280"];',
        "const meta = STATUS_META[entry.status];",
        "test_js_renders_four_states_and_unknown_state_defense",
    ),
    (
        "M11",
        "no_projection 也给库深链 → 现网死链缺陷复发",
        'body = \'<div class="degraded">该库尚无今日复习投影 — 推送管道尚未为它跑过<br>\' +\n'
        '      "深链已降级：需在 Obsidian 打开过该库后才提供跳转</div>";',
        'body = \'<div class="degraded">该库尚无今日复习投影</div>\' +\n'
        "      '<a href=\"obsidian://open?vault=' + encodeURIComponent(vid) + '\">打开</a>';",
        "test_js_renders_four_states_and_unknown_state_defense",
    ),
    (
        "M12",
        "corrupt 隐去原始错误 → 用户无从判断坏在哪",
        'body = \'<div class="corrupt-err">投影文件无法解析<br><code>\' + esc(String(entry.error || "")) + "</code></div>";',
        'body = \'<div class="corrupt-err">投影文件无法解析</div>\';',
        "test_js_renders_four_states_and_unknown_state_defense",
    ),
    # ── unavailable 不白屏 (完成条件 b) ─────────────────────────────
    (
        "M13",
        "从未成功也声称『保留了数据』 → 假装有数据",
        'const keep = lastOkText ? "页面保留 " + esc(lastOkText) + " 的最后一次成功数据。" : "尚未成功获取过数据。";',
        'const keep = "页面保留 " + esc(lastOkText) + " 的最后一次成功数据。";',
        "test_js_unavailable_banner_never_blank_screen",
    ),
    (
        "M14",
        "空 vaults 返回空串 → 白屏",
        'if (!vaults.length) return \'<div class="empty">VAULTS_ROOT 下未发现任何 vault (需含 .obsidian/ 目录)</div>\';',
        'if (!vaults.length) return "";',
        "test_js_unavailable_banner_never_blank_screen",
    ),
    (
        "M15",
        "畸形响应不再兜底 → 渲染时抛异常",
        "const vaults = data && Array.isArray(data.vaults) ? data.vaults : [];\n"
        "  if (!vaults.length) return",
        "const vaults = data.vaults;\n  if (!vaults.length) return",
        "test_js_unavailable_banner_never_blank_screen",
    ),
    # ── W6 加性三字段「缺省整块不出现」(完成条件 b) ─────────────────
    (
        "M16",
        "why_this_board 无条件渲染 → 缺省时出现空说明行",
        'if (typeof r.why_this_board === "string" && r.why_this_board)',
        "if (true)",
        "test_js_w6_additive_fields_present_and_absent",
    ),
    (
        "M17",
        "estimated_minutes 用宽松判空 → 字符串/NaN 也渲染",
        "const est = Number.isFinite(r.estimated_minutes) ?",
        "const est = (r.estimated_minutes != null) ?",
        "test_js_w6_additive_fields_present_and_absent",
    ),
    (
        "M18",
        "rank_manifest 无条件显示 → 旧投影伪造排序依据",
        "if (proj.rank_manifest != null) body +=",
        "if (true) body +=",
        "test_js_w6_additive_fields_present_and_absent",
    ),
    # ── 刷新反馈不伪装成功 (完成条件 c) ─────────────────────────────
    (
        "M19",
        "去抖走成功分支 → 与真重建同形 (零 JS 页 round-3 缺陷的浏览器版)",
        'if (status === 200 && payload && payload.reason === "rebuilt")',
        "if (status === 200 && payload)",
        "test_js_refresh_result_visible_and_never_fakes_success",
    ),
    (
        "M20",
        "失败吞掉后端原因 → 只剩一个状态码",
        'if (payload && payload.detail)\n'
        "    detail = typeof payload.detail === \"string\" ? payload.detail "
        ': (payload.detail.message || JSON.stringify(payload.detail));',
        "detail = \"\";",
        "test_js_refresh_result_visible_and_never_fakes_success",
    ),
    # ── XSS / 深链编码 ──────────────────────────────────────────────
    (
        "M21",
        "esc 变恒等 → 库名可注入标签",
        'return String(s).replace(/[&<>"\']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'
        '\'"\':"&quot;","\'":"&#39;"}[c]));',
        "return String(s);",
        "test_js_escapes_hostile_names_and_encodes_deep_links",
    ),
    (
        "M22",
        "深链改用 encodeURI → `/` `&` `#` 不再编码, query 被截断",
        'return "obsidian://open?vault=" + encodeURIComponent(vaultId) '
        '+ "&file=" + encodeURIComponent("原白板/" + board + ".md");',
        'return encodeURI("obsidian://open?vault=" + vaultId + "&file=" + "原白板/" + board + ".md");',
        "test_js_escapes_hostile_names_and_encodes_deep_links",
    ),
    # ── 到期人话与服务端同源 ────────────────────────────────────────
    (
        "M23",
        "「明天」改词 → 与服务端 _humanize_due 分家",
        'if (days === 1) return {text: "明天", color: "#374151"};',
        'if (days === 1) return {text: "1天后", color: "#374151"};',
        "test_js_humanize_due_matches_server_side_wording",
    ),
    (
        "M24",
        "逾期按天数取绝对值反向 → 逾期显示成未来",
        'if (days < 0) return {text: "逾期" + (-days) + "天", color: "#dc2626"};',
        'if (days < 0) return {text: (-days) + "天后", color: "#374151"};',
        "test_js_humanize_due_matches_server_side_wording",
    ),
    # ── 单文件自足 / 同源约束 (完成条件 a) ──────────────────────────
    (
        "M25",
        "引入 CDN <script src> → 零外部依赖失守",
        "<script>\n"
        '"use strict";',
        '<script src="https://cdn.jsdelivr.net/npm/x"></script>\n'
        "<script>\n"
        '"use strict";',
        "test_zero_external_urls",
    ),
    (
        "M26",
        "协议相对外链 (不含 http 字样, 只有资源标签门看得见)",
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<link rel="stylesheet" href="//fonts.example.com/x.css">',
        "test_no_external_resource_tags",
    ),
    (
        "M27",
        "硬编码 API 路径 → prefix 一改就漂",
        '"overview": request.url_for("review_overview").path,',
        '"overview": "/api/v1/review/overview",',
        "test_api_paths_follow_mount_prefix_not_hardcoded",
    ),
    (
        "M28",
        "自动轮询里也 POST refresh → 违反默认裁决②",
        'const resp = await fetch(URLS.overview, {cache: "no-store"});',
        'await fetch(URLS.refresh, {method: "POST", body: new URLSearchParams({vault_id: "x"})});\n'
        '    const resp = await fetch(URLS.overview, {cache: "no-store"});',
        "test_auto_poll_never_posts_only_manual_button_does",
    ),
    (
        "M29",
        "JS 里另抄一份徽标文案 → 两页文案将来各走各的 (own-key 版锚点)",
        'const meta = Object.prototype.hasOwnProperty.call(STATUS_META, entry.status)\n'
        '    ? STATUS_META[entry.status] : [entry.status, "#6b7280"];',
        'const LOCAL = {ok: ["今日投影", "#16a34a"]};\n'
        '  const meta = LOCAL[entry.status] || STATUS_META[entry.status] || [entry.status, "#6b7280"];',
        "test_status_meta_and_buckets_shared_not_copied",
    ),
    (
        "M30",
        "端点里 import pathlib → import 白名单失守 (第二套管道的载体)",
        "    urls = {",
        "    import pathlib\n"
        "    urls = {",
        "test_review_app_module_imports_are_closed",
    ),
    (
        "M31",
        "刷新反馈 TTL 归零 → rebuilt 重绘即抹掉反馈 (HIGH-1 回归)",
        "const NOTE_TTL_MS = 15000;",
        "const NOTE_TTL_MS = 0;",
        "test_js_refresh_wiring_note_survives_rerender_and_inflight_guard",
    ),
    (
        "M32",
        "就地补的写入副作用被掏掉 (只置标志不写 DOM) → 按钮旁的『重建中…』永远等不来结局",
        'if (span.getAttribute("data-note-for") === vid) { span.innerHTML = n.html; patched = true; }',
        'if (span.getAttribute("data-note-for") === vid) { patched = true; }',
        "test_js_refresh_wiring_note_survives_rerender_and_inflight_guard",
    ),
    (
        "M33",
        "在飞防抖删除 → 同库连点发多个 POST",
        "if (state.inflight[vid]) return;  // 同库重建在飞, 不发第二个 POST",
        ";",
        "test_js_refresh_wiring_note_survives_rerender_and_inflight_guard",
    ),
    (
        "M34",
        "rebuilt 后不立即重拉 → 数字停在旧投影 (round-3 LOW-2 后: 可见态才重拉)",
        "      if (!document.hidden) poll();",
        ";",
        "test_js_refresh_wiring_note_survives_rerender_and_inflight_guard",
    ),
    (
        "M35",
        "端点里内建 open() 读盘 → AST 正向合约 (白名单外 Name 调用)",
        "    urls = {",
        '    urls = {"probe": open("今日复习.json").read(),',
        "test_review_app_module_imports_are_closed",
    ),
    (
        "M36",
        "下标取内建 open (round-2 HIGH-4 的原始绕过形态) → 非 Name/Attribute 调用形态必红",
        "    urls = {",
        '    urls = {"probe": __builtins__["open"]("今日复习.json").read(),',
        "test_review_app_module_imports_are_closed",
    ),
    (
        "M37",
        "lambda 包裹 open → 白名单外 Name 调用 (包在 lambda 里也一样)",
        "    urls = {",
        '    urls = {"probe": (lambda pth: open(pth).read())("今日复习.json"),',
        "test_review_app_module_imports_are_closed",
    ),
    (
        "M38",
        "script 正文塞 // </SCRIPT> (大小写骗过提取) → 真实页面提取健全性门",
        "const POLL_MIN_MS = 5000;   // 轮询下限 (默认裁决②: clamp 5s)",
        "// </SCRIPT>\nconst POLL_MIN_MS = 5000;   // 轮询下限 (默认裁决②: clamp 5s)",
        "test_real_page_extracted_script_is_well_formed",
    ),
    (
        "M39",
        "删成功路径代际守卫 → 乱序旧响应把新数据盖回旧投影 (round-2 HIGH-1)",
        "    if (gen !== state.pollGen) return;  // 过期响应: 不碰状态不排程",
        ";",
        "test_js_poll_out_of_order_discards_stale_response",
    ),
    (
        "M40",
        "rebuilt 不登记 pendingSync → 数字未同步就永远不说/或乱说结局",
        "      state.pendingSync[vid] = {count: payload.rebuild_count, atMs: Date.now()};",
        ";",
        "test_js_rebuilt_sync_flow_never_claims_prematurely",
    ),
    (
        "M41",
        "GET 成功不结算 pendingSync → 『数字已更新』永不出现",
        "    settlePendingSync(nowMs, true, renderedVids);",
        ";",
        "test_js_rebuilt_sync_flow_never_claims_prematurely",
    ),
    (
        "M42",
        "删 200 坏形状校验 → 坏响应清掉旧数据还装已连接 (round-2 M2)",
        '    if (!data || !Array.isArray(data.vaults)) throw new Error("响应形状坏 (vaults 缺失)");',
        ";",
        "test_js_malformed_200_keeps_last_data",
    ),
    # ── round-3 (Codex 终轮) findings 的门 ─────────────────────────
    (
        "M43",
        "script 正文塞携带属性的结束标签 </script x=y> (round-3 HIGH-3 实证形态)",
        "const POLL_MIN_MS = 5000;   // 轮询下限 (默认裁决②: clamp 5s)",
        "</script x=y>\nconst POLL_MIN_MS = 5000;   // 轮询下限 (默认裁决②: clamp 5s)",
        "test_real_page_extracted_script_is_well_formed",
    ),
    (
        "M44",
        "白名单名重绑定 list = open (round-3 HIGH-4b 实证绕过) → AST 重绑定禁令",
        "    urls = {",
        "    list = open\n    urls = {",
        "test_review_app_module_imports_are_closed",
    ),
    (
        "M45",
        "错误接收者挂同名方法 [].items() → AST 接收者门",
        "    urls = {",
        '    urls = {"probe": [1].items(),',
        "test_review_app_module_imports_are_closed",
    ),
    (
        "M46",
        "结算不绑定渲染证据 → corrupt/缺库也沾 GET 成功的光 (round-3 HIGH-1)",
        "    const okThis = ok && renderedVids && renderedVids[vid] === true;",
        "    const okThis = ok;",
        "test_js_settle_binds_to_rendered_vault_evidence",
    ),
]


def run_gate(node_id: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        PYTEST + [f"{TESTFILE}::{node_id}"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        timeout=600,
    )


def main() -> int:
    if not TARGET.exists():
        print(f"FATAL: 找不到被测文件 {TARGET}", file=sys.stderr)
        return 2
    original = TARGET.read_bytes()
    original_text = original.decode("utf-8")

    # 前置: 基线必须全绿 —— 基线本来就红的话, 后面每条"变红"都不算数
    base = subprocess.run(PYTEST + [TESTFILE], cwd=BACKEND, capture_output=True, text=True, timeout=900)
    if base.returncode != 0:
        print("FATAL: 基线不绿, 负验证无意义\n" + base.stdout[-3000:], file=sys.stderr)
        return 2
    print(f"基线全绿 ✓  ({MUTATIONS.__len__()} 条变异待跑, 串行)")

    failures: list[str] = []
    restore_broken = False
    for idx, (mid, desc, old, new, gate) in enumerate(MUTATIONS, 1):
        hits = original_text.count(old)
        if hits != 1:
            failures.append(f"{mid} 锚点在原文命中 {hits} 次 (须恰好 1) — 变异会静默空转")
            print(f"[{idx:>2}/{len(MUTATIONS)}] {mid} ✗ 锚点命中 {hits} 次: {desc}")
            continue
        mutated = original_text.replace(old, new, 1)
        assert mutated != original_text, f"{mid} 替换后文件未变"
        TARGET.write_text(mutated, encoding="utf-8")
        try:
            proc = run_gate(gate)
            out = proc.stdout + proc.stderr
            # returncode 必须 == 1 (pytest「测试失败」专属退出码): collection
            # error=2 / 内部错误=3 / 用法错误(含 nodeid 不存在)=4 / 未收集=5
            # 一律不许冒充变红 (round-2 HIGH-4: 构造的 ImportError 骗过了 !=0)
            red = (
                proc.returncode == 1
                and re.search(r"\b1 failed\b", out) is not None
                and f"FAILED {TESTFILE}::{gate}" in out
            )
        finally:
            TARGET.write_bytes(original)
            restored = TARGET.read_bytes()
            if restored != original:
                print(f"FATAL: {mid} 还原后字节不一致 — 停止", file=sys.stderr)
                restore_broken = True
        if restore_broken:
            return 2
        mark = "✓ 变红" if red else "✗ 仍绿 (门不承重!)"
        print(f"[{idx:>2}/{len(MUTATIONS)}] {mid} {mark} · {gate} · {desc}")
        if not red:
            failures.append(f"{mid} ({gate}) 未变红: {desc}")

    # 收尾: 还原后基线必须仍然全绿 (证明脚本没留下残渣)
    after = subprocess.run(PYTEST + [TESTFILE], cwd=BACKEND, capture_output=True, text=True, timeout=900)
    if after.returncode != 0:
        print("FATAL: 跑完后基线不绿 — 文件被污染\n" + after.stdout[-3000:], file=sys.stderr)
        return 2

    print()
    if failures:
        print(f"负验证 FAIL: {len(failures)}/{len(MUTATIONS)} 条未按预期变红")
        for f in failures:
            print("  - " + f)
        return 1
    print(f"负验证 PASS: {len(MUTATIONS)}/{len(MUTATIONS)} 条变异均被**指定的那道门**抓住; 还原后基线仍全绿")
    return 0


if __name__ == "__main__":
    sys.exit(main())
