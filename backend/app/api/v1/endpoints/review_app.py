"""交互复习壳 (CARD-G6-2, BATCH-2026-09-01-第八批)。

GET /api/v1/review/overview/app — 单文件交互 HTML (内联 CSS/JS, 零 CDN、
零外部 URL, 只允许 obsidian:// 深链与本机相对路径), 与零 JS 只读页
(/overview/page, W6 车道独占) 共存 — 两页并立, 互不替代。

职责边界 (与 review_overview.py 的分工, 防双实现):
- 本页 JS 是 GET /overview JSON 与 POST /overview/refresh 的**纯消费方**:
  不实现任何 due 算法 — 谁到期/计数/排序全部来自服务端投影摘要
  (_summarize 的 due_count 权威口径 / boards 行 / next_upcoming)。JS 只做
  两件事: ①展示层格式化 (把已给定的时间戳渲染成人话, 删掉它页面依然知道
  谁到期); ②轮询节奏 — 周期 = clamp(最近未来 next_upcoming.next_due − now,
  5s, 60s) (默认裁决②), next_due 只决定「下一次去问服务端的时刻」, 不据此
  改任何到期展示。
- 页面隐藏 (visibilitychange) 时暂停轮询, 回到前台立即拉一轮。
- 自动轮询**绝不** POST refresh — 只有手动「刷新投影」按钮才 POST
  (同库重建在飞期间按钮禁用, 不发第二个 POST)。
- 两个 API path 用 request.url_for 注入 (不硬编码) — prefix 改动不漂移。
- 四态徽标字面从 review_overview._STATUS_META **import 后注入** JS (共享
  不复制, W6 改文案本页自动跟随); 前端另有第五态 unavailable: fetch 失败/
  非 200/JSON 解析失败 → 顶部横幅 + 保留最后一次成功数据, 不白屏。
  卡文默认裁决⑥提及的 "unregistered" 在 review_overview 状态枚举中不存在
  (2026-09-01 grep 0 命中, 仅页脚有"未注册的库点击无响应"提示文案) — 本页
  对未知 status 值做防御渲染 (原字面灰徽标), 未来加态不白屏。
- 休息日空状态 (status ok 且 due_count==0): 文案对齐
  scripts/daily_review_pick.py:599「今日无到期节点，休息一天」/ :564
  「按计划推进 · 最近到期 …」 (只对齐字面, 不 import — scripts/ 不在
  app 包路径, 且判定本身用的是投影摘要的 due_count, 无第二套口径)。
- W6 (CARD-G3-6b) 加性三字段按「缺省整块不出现」渲染 (沿 bucket_counts
  缺省纪律): boards[].why_this_board (非空字符串→板行下说明行) /
  boards[].estimated_minutes (有限数→「约 N 分钟」标签) / projection 顶层
  rank_manifest (在场→底部小注, 不解析内部形状)。W6 先合、透传位置以合并
  后主干为准 — 缺省不出现的设计保证位置不符时页面不炸只是不显示。
- 刷新反馈进**持久状态** (state.notes, 15s TTL): 手动刷新的结局 (重建/
  去抖/在跑/失败, 均含 rebuild_count) 写进状态而非只写 DOM —— rebuilt 触发
  的立即重拉、或任何一轮轮询重绘, 都会从状态恢复反馈, 不会被下一帧抹掉
  (Codex round-1 HIGH-1); 在飞期间按钮禁用也是渲染态的一部分, 重绘不会
  意外解锁成可双击。

JS 结构 (测试契约, Codex round-1 HIGH-3 后的形态): tests/unit/test_review_app.py
把响应里的**整个 <script> 原文**放进受控沙箱 (stub document/fetch/timer)
直接执行, 纯函数从执行后的沙箱作用域导出断言 —— 不存在任何「按注释标记
割取代码」的通道, 注释里藏一份好代码骗提取器的攻击面不成立; 副作用壳
(轮询/点击流程) 也在同一沙箱里以假事件驱动做接线断言。node 不可用时该
fixture fail-closed (pytest.fail), 禁止静默 skip 假绿 (Codex round-1 HIGH-2)。
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.api.v1.endpoints.review_overview import _BUCKET_CN, _BUCKET_ORDER, _STATUS_META

review_app_router = APIRouter()


def _js_json(value) -> str:
    """常量 → 可安全内嵌 <script> 的 JSON 字面量。

    值全部来自服务端自有常量与 url_for 路径 (无用户输入), `<` 转义只是
    防御深度: 万一未来有人把含 "</script>" 的字面量塞进 _STATUS_META,
    页面不会在此处被截断。
    """
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")


# ── 页面模板 (r-string: JS 正则的反斜杠原样保留) ─────────────────────
# 占位符 __URLS_JSON__ / __STATUS_META_JSON__ / __BUCKET_CN_JSON__ /
# __BUCKET_ORDER_JSON__ 由端点函数按请求注入。
_PAGE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>跨库复习总览 · 交互版</title>
<style>
  /* 与零 JS 页 (/overview/page) 同族配色 — 交互壳不另起视觉体系 */
  body { font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif;
         background: #f5f5f7; margin: 0; padding: 24px; color: #111827; }
  [hidden] { display: none !important; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  .ver { font-size: 13px; color: #2563eb; font-weight: normal; }
  .sub { color: #6b7280; font-size: 13px; margin-bottom: 12px; }
  .statusbar { display: flex; gap: 14px; align-items: center; flex-wrap: wrap;
               font-size: 13px; color: #6b7280; margin-bottom: 16px; }
  .conn { border-radius: 999px; padding: 2px 10px; font-size: 12px; color: #fff; white-space: nowrap; }
  .conn.ok { background: #16a34a; }
  .conn.down { background: #dc2626; }
  .conn.idle { background: #9ca3af; }
  .banner { background: #fef2f2; border: 1px solid #fecaca; border-radius: 10px;
            padding: 10px 16px; font-size: 14px; color: #991b1b; margin-bottom: 16px; }
  .cards { display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-start; }
  .card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px 20px;
          flex: 1 1 320px; min-width: 0; max-width: 520px; background: #fff;
          box-shadow: 0 1px 3px rgba(0,0,0,.06); }
  .card-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
  .card-head b { font-size: 16px; }
  .badge { border-radius: 999px; padding: 2px 10px; font-size: 12px; color: #fff; white-space: nowrap; }
  .big { font-size: 26px; margin: 8px 0 0; }
  .big small { font-size: 13px; color: #6b7280; font-weight: normal; }
  .layers { font-size: 12px; color: #6b7280; margin: 2px 0 0; }
  .tblwrap { overflow-x: auto; margin: 10px 0 4px; }
  table { border-collapse: collapse; width: 100%; font-size: 13px; }
  th { padding: 4px 8px; border-bottom: 1px solid #e5e7eb; color: #6b7280;
       font-weight: 500; text-align: left; white-space: nowrap; font-size: 12px; }
  td { padding: 5px 8px; border-bottom: 1px solid #f3f4f6; }
  td.num { text-align: center; white-space: nowrap; }
  a { color: #2563eb; text-decoration: none; }
  .why { color: #6b7280; font-size: 12px; padding: 0 8px 6px; }
  .estmin { display: inline-block; background: #eef2ff; color: #4338ca; border-radius: 4px;
            padding: 0 6px; font-size: 11px; margin-left: 6px; white-space: nowrap; }
  .manifest { color: #9ca3af; font-size: 11px; margin-top: 6px; }
  .gen { color: #6b7280; font-size: 12px; margin: 4px 0 6px; }
  .restday { color: #16a34a; font-size: 14px; margin: 14px 0; }
  .degraded { color: #6b7280; margin: 12px 0; font-size: 13px; }
  .corrupt-err { color: #dc2626; margin: 12px 0; }
  .corrupt-err code { font-size: 11px; overflow-wrap: anywhere; }
  .actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 10px; }
  .btn { font-size: 13px; color: #2563eb; background: #eff6ff; border: 1px solid #bfdbfe;
         border-radius: 6px; padding: 3px 10px; cursor: pointer; font-family: inherit; }
  .btn:disabled { opacity: .5; cursor: default; }
  .rnote { font-size: 12px; color: #6b7280; }
  .rnote.ok { color: #16a34a; }
  .rnote.warn { color: #d97706; }
  .rnote.err { color: #dc2626; }
  .nodetag { display: inline-block; background: #f3f4f6; color: #4b5563; border-radius: 4px;
             padding: 0 6px; font-size: 11px; margin-left: 6px; white-space: nowrap; }
  .nodeli { margin: 0 0 6px; list-style: none; line-height: 1.5;
            overflow-wrap: anywhere; word-break: break-word; }
  .whydue { color: #6b7280; font-size: 12px; margin-top: 1px; }
  .empty { color: #6b7280; }
  .lostnote { flex: 1 1 100%; color: #d97706; font-size: 12px; margin: 4px 0 0; }
  .footer { color: #9ca3af; font-size: 12px; margin-top: 24px; }
</style>
</head>
<body>
<h1>📚 跨库复习总览 <span class="ver">交互版</span></h1>
<div class="sub">自动轮询（到点自动重新拉取投影聚合）· 只读聚合，数据来自各库 outputs/今日复习.json
 · 「刷新投影」按需重建该库投影（只写它自己的 outputs/今日复习.*）</div>
<div class="statusbar">
  <span id="conn" class="conn idle">连接中…</span>
  <span id="updated"></span>
  <span id="nextpoll"></span>
</div>
<div id="banner" class="banner" hidden></div>
<div id="cards" class="cards"><span class="empty">加载中…</span></div>
<div class="footer">⚠ obsidian:// 跳转需在 Obsidian 打开过该库（未注册的库点击无响应）；
存在同名库时可能跳到先注册的那个，以 Obsidian 侧库列表为准</div>
<script>
"use strict";
// 服务端注入 (url_for 路径 + review_overview 共享字面 — 单一来源, 不复制)
const URLS = __URLS_JSON__;
const STATUS_META = __STATUS_META_JSON__;
const BUCKET_CN = __BUCKET_CN_JSON__;
const BUCKET_ORDER = __BUCKET_ORDER_JSON__;
const POLL_MIN_MS = 5000;   // 轮询下限 (默认裁决②: clamp 5s)
const POLL_MAX_MS = 60000;  // 轮询上限 (默认裁决②: clamp 60s)
const RETRY_DELAY_MS = 10000;  // unavailable 态的固定重试间隔 (在 clamp 区间内)
const NOTE_TTL_MS = 15000;  // 刷新反馈的可见窗: 足够活过 rebuilt 触发的立即重拉, 不永久占卡片

// ═══ 纯渲染函数: 输入 JSON → 输出 HTML 字符串/数值。无 DOM、无 fetch、
// 无时钟读取 (nowMs 一律显式入参)。 ═══
function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function shDay(ms) {
  // Asia/Shanghai 本地日 YYYY-MM-DD (en-CA locale 恰好输出 ISO 形态);
  // 与服务端 _humanize_due 的"上海本地日差"同一口径
  return new Intl.DateTimeFormat("en-CA", {timeZone: "Asia/Shanghai"}).format(new Date(ms));
}
function parseDueMs(ts) {
  // 生产器 UTC-Z 秒级形态; 非该形态返回 null (显示层容错, 绝不抛)
  if (typeof ts !== "string" || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(ts)) return null;
  const ms = Date.parse(ts);
  return Number.isFinite(ms) ? ms : null;
}
function humanizeDue(ts, nowMs) {
  // ⚠ 纯显示层格式化 — 不是 due 判定: 谁到期/计数/排序全来自投影字段
  // (boards[].due / due_count), 删掉本函数页面依然知道谁到期。
  // 口径对齐服务端 _humanize_due (上海本地日差), 同源锁见 pytest 对拍测试。
  if (ts === null || ts === undefined) return {text: "—", color: "#6b7280"};
  if (ts === "") return {text: "现在", color: "#d97706"};
  const ms = parseDueMs(ts);
  if (ms === null) return {text: "—", color: "#6b7280"};
  const d1 = shDay(ms), d0 = shDay(nowMs);
  const days = Math.round((Date.parse(d1) - Date.parse(d0)) / 86400000);
  if (days < 0) return {text: "逾期" + (-days) + "天", color: "#dc2626"};
  if (days === 0) return {text: "现在", color: "#d97706"};
  if (days === 1) return {text: "明天", color: "#374151"};
  if (days <= 7) return {text: days + "天后", color: "#374151"};
  const parts = d1.split("-").map(Number);
  const y0 = Number(d0.split("-")[0]);
  return {text: (parts[0] === y0 ? "" : parts[0] + "年") + parts[1] + "月" + parts[2] + "日", color: "#6b7280"};
}
function computePollDelayMs(data, nowMs) {
  // 轮询周期 = clamp(最近**未来** next_upcoming.next_due − now, 5s, 60s)。
  // next_due 只定「下一次去问服务端」的节奏; 已过期的 next_due 意味着数据
  // 要等生产器重跑才会变 → 回落上限 60s, 不空转。
  let best = null;
  const vaults = data && Array.isArray(data.vaults) ? data.vaults : [];
  for (const v of vaults) {
    const nu = v && v.projection && v.projection.next_upcoming;
    const ms = nu ? parseDueMs(nu.next_due) : null;
    if (ms !== null && ms > nowMs && (best === null || ms < best)) best = ms;
  }
  const raw = best === null ? POLL_MAX_MS : best - nowMs;
  return Math.min(POLL_MAX_MS, Math.max(POLL_MIN_MS, raw));
}
function visibilityAction(hidden) {
  // 页面隐藏 → 只取消排程; 回到前台 → 取消旧排程并立即拉一轮
  return hidden ? {cancelTimer: true, pollNow: false} : {cancelTimer: true, pollNow: true};
}
function boardLink(vaultId, board) {
  // encodeURIComponent 与服务端 quote(safe="") 同语义: "/" 也编码
  return "obsidian://open?vault=" + encodeURIComponent(vaultId) + "&file=" + encodeURIComponent("原白板/" + board + ".md");
}
function nodeLink(vaultId, node) {
  return "obsidian://open?vault=" + encodeURIComponent(vaultId) + "&file=" + encodeURIComponent("节点/" + node + ".md");
}
function nodeDetailHtml(vaultId, nodes, nowMs) {
  if (!Array.isArray(nodes) || !nodes.length) return "";
  const items = nodes.map(n => {
    const due = humanizeDue(n.fsrs_due, nowMs);
    const tag = n.bucket == null ? "" :
      '<span class="nodetag">' + esc(BUCKET_CN[n.bucket] || n.bucket) + "</span>";
    const why = !n.why_due ? "" : '<div class="whydue">' + esc(n.why_due) + "</div>";
    return '<li class="nodeli"><a href="' + esc(nodeLink(vaultId, n.node)) + '">' + esc(n.node) + "</a>" + tag +
      '<span style="color:' + due.color + ';font-size:12px;margin-left:6px">' + esc(due.text) + "</span>" + why + "</li>";
  });
  return '<details style="margin:2px 0 4px"><summary style="cursor:pointer;color:#6b7280;font-size:12px">节点明细（' +
    nodes.length + '）</summary><ul style="margin:6px 0 0;padding:0 0 0 6px">' + items.join("") + "</ul></details>";
}
function boardTableHtml(vaultId, boards, nowMs) {
  if (!Array.isArray(boards) || !boards.length) return "";
  const head = ["白板名", "到期", "新卡", "待剖析", "最早到期"].map(c => "<th>" + c + "</th>").join("");
  const rows = boards.map(r => {
    const due = humanizeDue(r.earliest, nowMs);
    const ph = r.placeholder == null ? "—" : String(r.placeholder);
    // W6 加性字段: 缺省整块不出现 (沿 bucket_counts 缺省纪律)
    const est = Number.isFinite(r.estimated_minutes) ?
      '<span class="estmin">约 ' + r.estimated_minutes + " 分钟</span>" : "";
    let out = '<tr><td><a href="' + esc(boardLink(vaultId, r.board)) + '">' + esc(r.board) + "</a>" + est + "</td>" +
      '<td class="num">' + (r.due ? "<b>" + r.due + "</b>" : '<span style="color:#9ca3af">0</span>') + "</td>" +
      '<td class="num">' + r.due_new + "</td>" +
      '<td class="num">' + esc(ph) + "</td>" +
      '<td style="white-space:nowrap;color:' + due.color + '">' + esc(due.text) + "</td></tr>";
    if (typeof r.why_this_board === "string" && r.why_this_board)
      out += '<tr><td colspan="5" class="why">💡 ' + esc(r.why_this_board) + "</td></tr>";
    const detail = nodeDetailHtml(vaultId, r.nodes, nowMs);
    if (detail) out += '<tr><td colspan="5" style="padding-top:0">' + detail + "</td></tr>";
    return out;
  }).join("");
  return '<div class="tblwrap"><table><thead><tr>' + head + "</tr></thead><tbody>" + rows + "</tbody></table></div>";
}
function restDayHtml(proj, nowMs) {
  // 休息日空状态 (status ok 且 due_count===0) — 文案对齐
  // daily_review_pick.py:599「今日无到期节点，休息一天」/ :564「按计划推进」
  const nu = proj.next_upcoming;
  // 日期转上海本地日 (UTC 字面日期在上海已跨天时会骗人 — Codex round-2 M4)
  let day = "";
  if (nu) {
    const ms = parseDueMs(nu.next_due);
    day = ms === null ? String(nu.next_due).slice(0, 10) : shDay(ms);
  }
  const tail = nu ? '<div style="color:#6b7280;font-size:13px;margin-top:4px">按计划推进 · 最近到期 ' +
    esc(nu.board) + " · " + esc(day) + "</div>" : "";
  return '<div class="restday">✅ 今日无到期节点，休息一天。' + tail + "</div>";
}
function renderVaultCard(entry, nowMs, noteHtml, isInflight) {
  // 未知 status 防御: 原字面灰徽标 (未来第五态不白屏)。
  // own-key 访问 (round-3 LOW-3): "constructor"/"__proto__" 会命中继承属性,
  // 必须显式判自有键才落灰兜底
  const meta = Object.prototype.hasOwnProperty.call(STATUS_META, entry.status)
    ? STATUS_META[entry.status] : [entry.status, "#6b7280"];
  const vid = entry.vault_id;
  let body = "";
  const proj = entry.projection;
  if (proj) {
    if (entry.status === "ok" && proj.due_count === 0) {
      body = restDayHtml(proj, nowMs);
    } else {
      const bc = proj.bucket_counts;
      const layers = bc == null ? "" :
        '<div class="layers">分层 · ' + BUCKET_ORDER.map(b => esc(BUCKET_CN[b]) + " " + bc[b]).join(" · ") + "</div>";
      body = '<div class="big">到期 <b>' + proj.due_count + "</b><small> · 新卡 " + proj.due_new_count +
        " · 待剖析 " + proj.placeholder_backlog + "</small></div>" + layers +
        boardTableHtml(vid, proj.boards, nowMs);
    }
    body += '<div class="gen">生成于 ' + esc(String(proj.generated_at)) + "</div>" +
      '<a href="obsidian://open?vault=' + esc(encodeURIComponent(vid)) + '">在 Obsidian 中打开 ↗</a>';
    // W6 加性顶层 rank_manifest: 在场才出现, 不解析内部形状
    if (proj.rank_manifest != null) body += '<div class="manifest">📋 本次板序含排序依据（rank_manifest）</div>';
  } else if (entry.status === "no_projection") {
    body = '<div class="degraded">该库尚无今日复习投影 — 推送管道尚未为它跑过<br>' +
      "深链已降级：需在 Obsidian 打开过该库后才提供跳转</div>";
  } else {
    body = '<div class="corrupt-err">投影文件无法解析<br><code>' + esc(String(entry.error || "")) + "</code></div>";
  }
  // noteHtml 是 renderRefreshResult 的成品 HTML (内部已 esc), 由调用方从
  // 持久状态传入 — 重绘后反馈得以恢复 (Codex round-1 HIGH-1)
  return '<div class="card"><div class="card-head"><b>' + esc(vid) + "</b>" +
    '<span class="badge" style="background:' + meta[1] + '">' + esc(meta[0]) + "</span></div>" + body +
    '<div class="actions"><button class="btn"' + (isInflight ? " disabled" : "") +
    ' data-refresh-vault="' + esc(vid) + '">🔄 刷新投影</button>' +
    '<span class="rnote" data-note-for="' + esc(vid) + '">' + (noteHtml || "") + "</span></div></div>";
}
function renderPage(data, nowMs, notes, inflight) {
  const vaults = data && Array.isArray(data.vaults) ? data.vaults : [];
  if (!vaults.length) return '<div class="empty">VAULTS_ROOT 下未发现任何 vault (需含 .obsidian/ 目录)</div>';
  return vaults.map(e => renderVaultCard(e, nowMs, (notes && notes[e.vault_id]) || "",
    !!(inflight && inflight[e.vault_id]))).join("");
}
function renderUnavailableBanner(detail, lastOkText) {
  const keep = lastOkText ? "页面保留 " + esc(lastOkText) + " 的最后一次成功数据。" : "尚未成功获取过数据。";
  return "<b>⚠ 后端离线/不可用</b> — " + esc(detail) + "。" + keep + "自动重试中…";
}
function renderRefreshResult(status, payload) {
  // POST /overview/refresh 响应可见化 — rebuilt/debounced/in_progress/失败
  // 四种结局都尽量带上 rebuild_count (进程内累计); 去抖与失败绝不长得像成功
  // (零 JS 页 round-3 修过的「与成功同形的 303」不许在交互壳还魂)
  const count = payload && payload.rebuild_count !== undefined && payload.rebuild_count !== null
    ? "（本进程累计 " + esc(payload.rebuild_count) + " 次）" : "";
  if (status === 200 && payload && payload.reason === "rebuilt")
    // 不当场声称"数字已更新" — 数字要等受保护的 GET 成功落屏才算数 (round-2 HIGH-1)
    return '<span class="rnote ok">✅ 已重建' + count + " · 正在同步最新数字…</span>";
  if (status === 200 && payload && payload.reason === "debounced") {
    const wait = Number(payload.retry_after_seconds);
    return '<span class="rnote warn">⏱ ' + esc(payload.debounce_ttl_seconds) + " 秒内已重建过" + count +
      "，本次未重算" +
      (Number.isFinite(wait) && wait > 0 ? " · 约 " + Math.ceil(wait) + " 秒后可再试" : "") + "</span>";
  }
  if (status === 200 && payload && payload.reason === "in_progress")
    return '<span class="rnote warn">⏳ 该库已有一次重建在跑' + count + "，本次未重复启动</span>";
  let detail = "";
  if (payload && payload.detail)
    detail = typeof payload.detail === "string" ? payload.detail : (payload.detail.message || JSON.stringify(payload.detail));
  if (status === 0) return '<span class="rnote err">❌ 刷新失败（网络错误）：' + esc(detail || "连接失败") + "</span>";
  return '<span class="rnote err">❌ 刷新失败（HTTP ' + esc(status) + "）" + (detail ? "：" + esc(detail) : "") + "</span>";
}

// ═══ 副作用壳: 只消费上面纯函数的返回值 ═══
const state = {timer: null, lastOkAt: null, lastData: null, pollGen: 0,
  // vault_id 是外部字符串 — Object.create(null) 防 "__proto__"/"constructor" 键注入原型 (round-2 M1)
  notes: Object.create(null), inflight: Object.create(null), pendingSync: Object.create(null)};
const el = id => document.getElementById(id);
function fmtClock(ms) {
  return new Intl.DateTimeFormat("zh-CN", {timeZone: "Asia/Shanghai", hour12: false,
    hour: "2-digit", minute: "2-digit", second: "2-digit"}).format(new Date(ms));
}
function setConn(cls, text) {
  const c = el("conn");
  c.className = "conn " + cls;
  c.textContent = text;
}
function vaultButtons(vid) {
  // getAttribute 比对而非把 vid 插进 CSS 选择器 — vid 是外部字符串,
  // 进选择器会被当选择器语法解析 (引号/反斜杠注入面)
  return Array.from(el("cards").querySelectorAll("[data-refresh-vault]"))
    .filter(b => b.getAttribute("data-refresh-vault") === vid);
}
function applyNote(vid) {
  const n = state.notes[vid];
  if (!n) return false;
  let patched = false;
  for (const span of el("cards").querySelectorAll("[data-note-for]")) {
    if (span.getAttribute("data-note-for") === vid) { span.innerHTML = n.html; patched = true; }
  }
  return patched;
}
function freshNotes(nowMs) {
  // null-prototype: 与 state.notes 同纪律 — 普通对象会被 "__proto__" 键污染 (round-3 M1)
  const out = Object.create(null);
  for (const vid of Object.keys(state.notes)) {
    if (nowMs - state.notes[vid].atMs < NOTE_TTL_MS) out[vid] = state.notes[vid].html;
  }
  return out;
}
function renderCards(nowMs) {
  el("cards").innerHTML = renderPage(state.lastData, nowMs, freshNotes(nowMs), state.inflight);
}
function settlePendingSync(nowMs, ok, renderedVids, startMs) {
  // rebuilt 只发"正在同步…"；数字是否真更新, 由 GET 成败结算 (round-2 HIGH-1)。
  // round-3 HIGH-1: 成功结算绑定 renderedVids 证据 (渲染成功 + projection 可用)。
  // round-4 HIGH-1: 结算还要过**因果锚** — 本次 GET 必须启动于该库重建完成
  // (atMs) 之后; 启动更早的 GET (rebuilt 后切后台导致没有新 GET 时, 旧 GET
  // 仍是最新代际) 看到的是重建前投影, 无权结算 — 跳过并把 pending 留给
  // 下一轮启动更晚的 GET。
  for (const vid of Object.keys(state.pendingSync)) {
    const n = state.pendingSync[vid];
    if (startMs !== undefined && n.atMs !== undefined && startMs < n.atMs) continue;
    delete state.pendingSync[vid];
    const okThis = ok && renderedVids && renderedVids[vid] === true;
    const text = okThis ? "已重建（本进程累计 " + n.count + " 次）· 数字已更新"
      : "已重建（本进程累计 " + n.count + " 次）· 数字同步失败，后端恢复后自动重试";
    state.notes[vid] = {html: okThis
      ? '<span class="rnote ok">✅ ' + esc(text) + "</span>"
      : '<span class="rnote warn">⚠ ' + esc(text) + "</span>", text: text, atMs: nowMs};
    if (!applyNote(vid) && state.lastData) renderCards(nowMs);
  }
}
function lostSyncNotesHtml(data, nowMs) {
  // 结算失败的库若已不在最新聚合里 (目标卡随之消失), 失败反馈不许跟着蒸发 —
  // 在卡片区尾部补一条纯文本失联通知 (round-4 HIGH-1 反例二)
  const present = Object.create(null);
  const vaults = data && Array.isArray(data.vaults) ? data.vaults : [];
  for (const v of vaults) {
    if (v && v.vault_id) present[v.vault_id] = true;
  }
  const parts = [];
  for (const vid of Object.keys(state.notes)) {
    const n = state.notes[vid];
    if (present[vid] || !n || nowMs - n.atMs >= NOTE_TTL_MS) continue;
    if (String(n.text || "").indexOf("同步失败") !== -1) {
      parts.push('<div class="lostnote">⚠ ' + esc(vid) + "：" + esc(n.text) + "（该库已不在当前聚合中）</div>");
    }
  }
  return parts.join("");
}
function schedule(ms) {
  clearTimeout(state.timer);
  state.timer = null;
  if (document.hidden) { el("nextpoll").textContent = "已暂停（页面隐藏）"; return; }
  state.timer = setTimeout(poll, ms);
  el("nextpoll").textContent = "下次自动刷新 ~" + Math.round(ms / 1000) + " 秒后";
}
async function poll() {
  let delay = RETRY_DELAY_MS;
  const gen = ++state.pollGen;  // 代际: 只有最新一次 GET 可以提交状态 (乱序旧响应整包丢弃)
  const startMs = Date.now();   // 启动时刻 — 结算的因果锚 (round-4 HIGH-1)
  try {
    const resp = await fetch(URLS.overview, {cache: "no-store"});
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const data = await resp.json();
    // 形状校验在提交状态之前 — HTTP 200 的坏形状不许清掉旧数据再装"已连接" (round-2 M2)
    if (!data || !Array.isArray(data.vaults)) throw new Error("响应形状坏 (vaults 缺失)");
    if (gen !== state.pollGen) return;  // 过期响应: 不碰状态不排程
    const nowMs = Date.now();
    // 先渲染候选数据当探针 (round-3 HIGH-1: 坏成员让 render 抛错时走 catch —
    // lastData/结算/成功提示都不会被半截提交), 再结算, 再上最终帧
    // (结算会更新 notes, 探针帧里是结算前的反馈, 不能直接用)
    renderPage(data, nowMs, freshNotes(nowMs), state.inflight);
    // 成功结算的绑定证据: 渲染成功, 且该库条目带可用 projection
    // (损坏/缺投影的库不许沾最新 GET 的光说"数字已更新")
    const renderedVids = Object.create(null);
    for (const v of data.vaults) {
      if (v && v.vault_id && v.projection) renderedVids[v.vault_id] = true;
    }
    state.lastData = data;
    settlePendingSync(nowMs, true, renderedVids, startMs);
    el("cards").innerHTML = renderPage(data, nowMs, freshNotes(nowMs), state.inflight) +
      lostSyncNotesHtml(data, nowMs);
    el("banner").hidden = true;
    state.lastOkAt = nowMs;
    el("updated").textContent = "上次更新 " + fmtClock(nowMs);
    setConn("ok", "已连接");
    delay = computePollDelayMs(data, nowMs);
  } catch (e) {
    if (gen !== state.pollGen) return;  // 过期响应的失败同样不碰状态
    settlePendingSync(Date.now(), false, null, startMs);
    el("banner").innerHTML = renderUnavailableBanner(String((e && e.message) || e),
      state.lastOkAt ? fmtClock(state.lastOkAt) : null);
    el("banner").hidden = false;
    setConn("down", "后端不可用");
  }
  schedule(delay);
}
document.addEventListener("visibilitychange", () => {
  const act = visibilityAction(document.hidden);
  if (act.cancelTimer) { clearTimeout(state.timer); state.timer = null; }
  if (act.pollNow) poll();
  else if (document.hidden) el("nextpoll").textContent = "已暂停（页面隐藏）";
});
async function onRefreshClick(ev) {
  const btn = ev.target.closest("[data-refresh-vault]");
  if (!btn) return;
  const vid = btn.getAttribute("data-refresh-vault");
  if (state.inflight[vid]) return;  // 同库重建在飞, 不发第二个 POST
  state.inflight[vid] = true;
  state.notes[vid] = {html: '<span class="rnote">⏳ 重建中…</span>', atMs: Date.now()};
  for (const b of vaultButtons(vid)) b.disabled = true;
  applyNote(vid);
  try {
    // 手动按钮是唯一的 POST 路径 (默认裁决②: 自动轮询绝不 POST)
    const resp = await fetch(URLS.refresh, {method: "POST", body: new URLSearchParams({vault_id: vid})});
    let payload = null;
    try { payload = await resp.json(); } catch (_e) { payload = null; }
    state.notes[vid] = {html: renderRefreshResult(resp.status, payload), atMs: Date.now()};
    // 先就地补; 就地补不到 (反馈期间被轮询重绘换过 DOM) 且手上有数据 →
    // 用持久状态重绘恢复 — 反馈从此不依赖「那个 span 还在不在」
    if (!applyNote(vid) && state.lastData) renderCards(Date.now());
    if (resp.ok && payload && payload.rebuilt) {
      // 数字是否真更新交给 GET 结算 (settlePendingSync) — 不在 POST 结局里预先声称
      state.pendingSync[vid] = {count: payload.rebuild_count, atMs: Date.now()};
      // 隐藏时不触发 GET (round-3 LOW-2): pending 挂着, 回前台 visibilitychange
      // 的 poll 会结算 — 不在用户看不见的时候起网络活动
      if (!document.hidden) poll();
    }
  } catch (e) {
    state.notes[vid] = {html: renderRefreshResult(0, {detail: String((e && e.message) || e)}), atMs: Date.now()};
    if (!applyNote(vid) && state.lastData) renderCards(Date.now());
  } finally {
    delete state.inflight[vid];
    for (const b of vaultButtons(vid)) b.disabled = false;
  }
}
el("cards").addEventListener("click", onRefreshClick);
poll();
</script>
</body>
</html>
"""


@review_app_router.get(
    "/overview/app",
    response_class=HTMLResponse,
    summary="跨 vault 复习总览 · 交互版 (CARD-G6-2; 单文件内联 HTML, 零外部 URL)",
)
async def review_overview_app(request: Request) -> HTMLResponse:
    """交互复习壳: 自动轮询 GET /overview, 手动按钮 POST /overview/refresh。

    与零 JS 只读页 (/overview/page) 共存。API 路径按本次请求的路由表注入
    (url_for), 不硬编码。
    """
    urls = {
        "overview": request.url_for("review_overview").path,
        "refresh": request.url_for("review_overview_refresh").path,
    }
    page = (
        _PAGE_TEMPLATE.replace("__URLS_JSON__", _js_json(urls))
        .replace("__STATUS_META_JSON__", _js_json({k: list(v) for k, v in _STATUS_META.items()}))
        .replace("__BUCKET_CN_JSON__", _js_json(_BUCKET_CN))
        .replace("__BUCKET_ORDER_JSON__", _js_json(list(_BUCKET_ORDER)))
    )
    return HTMLResponse(content=page)
