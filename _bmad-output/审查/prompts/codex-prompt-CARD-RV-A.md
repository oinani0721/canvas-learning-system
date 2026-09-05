# CARD-RV-A — 三张已合卡的「审后未复审 diff」独立复审

## §一 背景与最小读取面

### 背景

本次是一张**只读复审卡**，零代码改动。背景事实：第十一批有三张卡已经合入主干，但每张卡在它自己那轮外部审查所绑定的 SHA **之后**，又各落了一段没有再送外部审查的改动，合计 568 行。本卡的任务是把这三段补审一遍。

三个面（下称 Z1 / Z4-A / Z4-B）：

| 面 | 区间 | 规模 | 性质 |
|---|---|---|---|
| Z1 | `d9f7b544` → `8e8fd737` | 1 文件 +161/-12（173 行，6 hunk） | 纯测试文件；由两个 commit 组成 |
| Z4-A | `304f03ca` → `7283a8df` | 5 文件 +298/-66（364 行，10 hunk） | 纯测试文件；单 commit |
| Z4-B | `a5e0ce79` → `c8611a89` | 4 文件 +22/-9（31 行，7 hunk） | 3 个源文件的文档字符串 + 1 个生成物 |

三个面涉及的全部文件，在当前 HEAD（`03ac8bf8`）上与各自右端 SHA **逐字节相同**，因此可直接在 HEAD 工作树上读。

### 最小读取面（写死，请只读这些）

请只读下面三条命令的输出、以及本 prompt 内嵌的文件全文。不需要、也请不要展开读取仓库其它源码。

```bash
git diff d9f7b544 8e8fd737 -- backend/tests/unit/test_review_app.py
git diff 304f03ca 7283a8df -- . ':(exclude)_bmad-output'
git diff a5e0ce79 c8611a89 -- . ':(exclude)_bmad-output'
```

（pathspec 的写法 `':(exclude)_bmad-output'` 是本机必须的形式，请原样使用。）

Z1 面的两个 commit 拆分（本卡实测）：

- `3d30bde6` = +62/-12，5 个 hunk（`@@260` / `@@455` / `@@491` / `@@613` / `@@820`），commit 标题自述「R1 外审整改 — 装饰器全路径 + Request 锁绑定 + 门计数不变量」。
- `8e8fd737` = +99/-0，1 个 hunk（`@@2060`），新增**一个** pytest 用例 `test_js_poll_contract_wiring_g63`，其中含 node 侧四条 `test(...)` 断言（下称 ①②③④）。该 commit **属于另一张卡**（CARD-G6-3），不是 Z1-A 自己的。

Z1 面上 `backend/app/api/v1/endpoints/review_app.py` **零字节改动**（`git diff --stat d9f7b544 8e8fd737 -- backend/app/api/v1/endpoints/review_app.py` 为空）。它是 Z1 面测试所针对的生产文件，HEAD 版全文附在本节末尾作为上下文。

### 三份既有审查存档的首部（自证各自绑定了哪个区间）

这三份存档**都没有**本项目 2026-09-05 起要求的六行首部（模型 / reasoning_effort / 工具版本 / 绑定 / 会话头自证），只能从正文首段读出绑定。原文抄录：

**存档 A — `codex-review-CARD-CX-G6-2b-R1.md`（Z1-A 那轮，末行自述「BLOCKER/HIGH 清零：否」）**

> （结论摘要一句省略，本卡只引它的绑定自证部分）当前相对 `HEAD` 的 backend 差异为空；相对 `92734207`，确为测试文件 **+34/-0**，生产文件完全相同。指定测试在使用现成可用的 Node v24.16.0 后得到 **146 passed**；……

该存档末行是「BLOCKER/HIGH 清零：否」，正文列有若干条 HIGH / MEDIUM；`3d30bde6` 正是针对其中三条的回应（见 §三 问题 ②）。

本卡实测 `git diff --stat 92734207 d9f7b544 -- backend/tests/unit/test_review_app.py` 确为 34 行，与该自述一致 → 存档 A 绑定的右端就是 `d9f7b544`。

**存档 B — `codex-review-CARD-REDBASE-R1-round2.md`（Z4-A 那轮，末行「BLOCKER/HIGH 清零: 是」）**

> 增量结论：**M1 成立；M2 环境隔离整改成立，但"唯一路径证明"不成立；L1 成立。新增 2 条 LOW，未找到 BLOCKER/HIGH。**
>
> 审查绑定 `HEAD=304f03cadaec165bb9c13dcb145b4f6aac0cf50c`，当前五文件 diff SHA-256：
>
> ```text
> 0a8ee996ac5efb74de16be74635669aba91ca4542f9d0aeb86a19d9b0b6b0d38
> ```

⚠️ 该 SHA-256 钉值在本卡**无法机械复现**：以三种口径（全树 `':(exclude)_bmad-output'`、五文件显式路径、`--no-color` 全树）跑 `git diff 304f03ca 7283a8df … | shasum -a 256`，三者**一致**地得到

```text
eb3ed96d39380a9cb4eafdad023052441635e115481e5da8112fde70317eb042
```

均不等于存档钉值。合理解释是存档 B 审的是**未提交的工作树状态**（其正文明确说"当前五文件 diff"），而 `7283a8df` 是其后落的 commit。因此「审后是否又改过」不能靠哈希判定 —— 这正是本卡问题 ③ 的一部分。

**存档 C — `codex-review-CARD-REDBASE-R2.md`（Z4-B 那轮，正文自述未找到本轮 BLOCKER/HIGH）**

> 结论：**六处修改本身成立，但 E"全仓裸格式归零"不成立，仍有现行公开契约漏项。未找到本轮 BLOCKER/HIGH。**
>
> 审查绑定 `7283a8df..a5e0ce79d9a70e711934b827d7f62c052d281895`。未修改仓库文件；审查期间外部进程补写的 UAT 内容未纳入结论。

### 上下文文件全文：`backend/app/api/v1/endpoints/review_app.py`（HEAD 版，550 行）

这是 Z1 面四条断言所测的生产文件。它在 Z1 面内**没有任何改动**，附在这里只是为了让你能判断那四条断言测的东西是否真实存在、是否与实现对得上。

```python
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
  // 卡片区**每一帧**的统一形态 = 投影卡 + 失联通知。round-4 HIGH-1 反例二只封了
  // poll 成功路径的最终帧, 而结算兜底重绘 (GET 失败时它就是最后一帧) 与 POST
  // 反馈重绘同样是用户眼前的一帧 — 少拼失联通知 = 失败反馈一闪就没 (G6-2b R1)
  el("cards").innerHTML = renderPage(state.lastData, nowMs, freshNotes(nowMs), state.inflight) +
    lostSyncNotesHtml(state.lastData, nowMs);
}
function settlePendingSync(nowMs, ok, renderedVids, startGen) {
  // rebuilt 只发"正在同步…"；数字是否真更新, 由 GET 成败结算 (round-2 HIGH-1)。
  // round-3 HIGH-1: 成功结算绑定 renderedVids 证据 (渲染成功 + projection 可用)。
  // round-4 HIGH-1: 结算还要过**因果锚** — 本次 GET 必须启动于该库重建完成
  // 之后; 启动更早的 GET (rebuilt 后切后台导致没有新 GET 时, 旧 GET 仍是最新
  // 代际) 看到的是重建前投影, 无权结算 — 跳过并把 pending 留给下一轮启动更晚
  // 的 GET。
  // round-5: 因果锚从**时间戳**换成**代际**。时间戳有同毫秒盲区 —— 重建完成
  // (atMs) 与旧 GET 启动 (startMs) 落在同一毫秒时 `startMs < n.atMs` 为假,
  // 重建前投影就冒充了重建后状态。pollGen 是严格递增的整数, 没有这个盲区:
  // 记下发 POST 时的最新代际 n.gen, 只有代际**更大**的 GET (= 确实在重建完成
  // 之后才启动) 才有权结算。
  for (const vid of Object.keys(state.pendingSync)) {
    const n = state.pendingSync[vid];
    if (startGen !== undefined && n.gen !== undefined && startGen <= n.gen) continue;
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
  // 代际: 只有最新一次 GET 可以提交状态 (乱序旧响应整包丢弃); 同时它就是结算的
  // **因果锚** — 严格递增, 不像时间戳那样有同毫秒盲区 (round-4 HIGH-1 / round-5)
  const gen = ++state.pollGen;
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
    settlePendingSync(nowMs, true, renderedVids, gen);
    // 最终帧与其余重绘共用同一条路径 (state.lastData 上一行刚设为 data) —
    // 帧形态单一来源, 将来新增重绘点不会再漏拼失联通知 (G6-2b R1)
    renderCards(nowMs);
    el("banner").hidden = true;
    state.lastOkAt = nowMs;
    el("updated").textContent = "上次更新 " + fmtClock(nowMs);
    setConn("ok", "已连接");
    delay = computePollDelayMs(data, nowMs);
  } catch (e) {
    if (gen !== state.pollGen) return;  // 过期响应的失败同样不碰状态
    settlePendingSync(Date.now(), false, null, gen);
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
      // gen = 发 POST 这一刻的最新代际; 只有代际更大的 GET 才有权结算
      state.pendingSync[vid] = {count: payload.rebuild_count, gen: state.pollGen};
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
```

## §二 作者自述（请独立核对，不要采信）

以下是三段改动各自的 commit message 原文。**它们是作者的自述，不是已核实的事实**，请以你自己读 diff 的结论为准；凡自述与 diff 不符之处，请直接指出。

```text
3d30bde6  fix(review): R1 外审整改 — 装饰器全路径 + Request 锁绑定 + 门计数不变量
          [BATCH-2026-09-05-第十一批 / CARD-CX-G6-2b-R1]

8e8fd737  test(review): G6-3 5 秒闭环取证 — 实测不可达 + 轮询契约接线四断言
          [BATCH-2026-09-05-第十一批 / CARD-G6-3]

7283a8df  test(REDBASE-R1): 主干既有红清账 12 条改期望·零实现改动
          [BATCH-2026-09-05-第十一批 / CARD-REDBASE-R1]

c8611a89  fix(REDBASE-R2): 送审整改·补修第 7 处契约面 + 措辞对齐 Z4-A
          [BATCH-2026-09-05-第十一批 / CARD-REDBASE-R2]
```

另外，`8e8fd737` 新增用例的文档字符串里有一句自述：「本卡零产品代码改动: 只加测试, 一个字节的 JS 都没动」。本卡已实测该面 `review_app.py` diff 为空，与自述一致。

## §三 请回答的四个问题（按重要性排序）

### 问题 ①（最重要）：`8e8fd737` 那四条断言是否承重？

四条断言（node 侧）分别是：

- ① clamp 下限：2 秒后到期 → 期望实际排程 5000ms
- ② clamp 上限：1 小时后到期 → 期望实际排程 60000ms
- ③ 隐藏时不排程；回前台的 visibilitychange 事件真的再拉一轮 GET
- ④ 自动轮询连跑 5 轮 + 可见性切换，沙箱收到的 POST 计数恒为 0

本卡已做的负控与变异，原始结果如下（请独立判断这些结果是否足以支撑「四条都承重」这个结论，以及它**没有**覆盖什么）：

**负控 1 — 把 `review_app.py` 换成上一版 `27e61454`（543 行，即该测试写出之前的生产实现），跑同一个 nodeid：**

```text
1 passed
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
rc=0
```

即四条断言在旧版实现上**也全绿**。本卡对此的读法是：这只证明四条断言不依赖 `92734207` 之后那 17 行生产改动，**不证明它们能红**。（两版之间 `review_app.py` 的差异是 +17/-10；四个轮询相关符号 `computePollDelayMs` / `visibilityAction` / `visibilitychange` / `nextpoll` 在两版中命中数相同，都是 11，所以换版后不会因符号缺失而崩。）

**负控 2 — 四条独立的临时变异（每条从干净基线出发，跑完无条件还原，跑前跑后全文件 shasum 一致）：**

| 变异（施加在 `review_app.py`） | 变红的断言 | 该断言报出的失败身份 | 其余三条 |
|---|---|---|---|
| `POLL_MIN_MS` 5000 → 2000 | ① | `下限没生效 = 会按 2 秒打后端` | 未记录 |
| `POLL_MAX_MS` 60000 → 30000 | ② | `上限没生效 = 一小时不问后端` | ①③④ 全绿 |
| `visibilityAction` 回前台分支 `pollNow: true` → `false` | ③ | `回前台必须立即拉一轮 (pollNow 的接线端)` | ①②④ 全绿 |
| 在 `poll()` 内注入一次 `fetch(URLS.refresh, {method: "POST", …})` | ④ | `Expected values to be strictly equal` | ①②③ 全绿 |

四次都是单杀（一条变异只让一条断言变红，且失败身份就是该断言自己的断言消息）。

请判断：这组证据支持到什么程度？特别是 —— 每条变异是否真的作用在该断言所声称测量的那个语义上，还是可能只是碰巧让它红了？有没有哪条断言即使在这组变异下变红，实际测的东西仍然比它的名字所声称的要窄？

### 问题 ②：`3d30bde6` 的三项整改，是否引入了新的「本该拦下却放行」的路径？

三项整改（都在同一个纯测试文件的 AST 检查器里）：

1. 把名字 `Request` 加进受保护的禁止重绑定集合；
2. 装饰器接收者的比对，从「只取根名」改成「与调用分支同口径地比对 `ast.unparse` 出来的完整接收者路径」；
3. 给 node 测试的通用判绿函数加了三条计数不变量（`tests > 0`、`fail == 0`、`pass == tests`），理由是原判据只看退出码与非零 skip，零条 test 被收集时同样会判绿。

请判断这三项各自是否成立，以及**整改本身**有没有制造出新的漏项 —— 比如第 2 项换用完整路径比对之后，是否有原先能拦下、现在拦不下的输入形态；第 3 项的三条不变量取值是否可能被一个门未覆盖的输出格式满足。

### 问题 ③：`7283a8df` 大量改「期望值」，是否掩盖了真实回归？

这个面把 5 个测试文件里的多条断言从旧期望值改成新期望值（例如 `math54:离散数学` → `vault:<vault>:math54:离散数学`），并把若干处 `reload_settings(overrides=…)` 换成 `patch("app.config.get_current_vault_id", …)`。作者自述是「主干既有红清账，零实现改动」。

请只判断一件事：**这些改动是否掩盖了真实回归** —— 即，是否存在某条断言，它原本的失败是在报告一个真实的实现缺陷，而这次改期望值把那个信号消掉了。请不要评判这些 group_id 格式在产品语义上是否正确（那不在本卡范围）。

一条已知线索：存档 B 在它那轮里就已指出，其中一条测试（`test_explicit_vault_id_still_wins`）的路径证明表述过强 —— 它排除不了「两个参数都被丢弃、走双缺失分支」这类实现，因为那条分支返回相同结果。存档 B 把这一条记为 LOW。而 `7283a8df` 里该测试的文档字符串**已经包含**对这条 LOW 的回应（明确写出了鉴别力边界）。请判断这个回应是否诚实、是否与它所描述的实现事实相符。

### 问题 ④：`c8611a89` 的补修与 `7283a8df` 的措辞是否一致？`openapi.json` 是不是机器再生的？

这个面改了 3 个源文件的文档字符串/字段说明，外加 `backend/openapi.json` 的 10 行。本卡已实测：在 HEAD（这四个文件与 `c8611a89` 逐字节相同）上跑生成器的比对模式，输出

```text
DRIFT: none (paths=193 schemas=353)
rc=0
```

即当前 `openapi.json` 与从源码现场生成的结果一致。请判断这是否足以支持「那 10 行是机器再生、不是手改」；以及这 10 行是否每一行都能对应到三个源文件里的某处改动（其中 `x-generated-at` 是生成时间戳）。另请判断 `c8611a89` 的措辞与 `7283a8df` 的同类措辞是否一致。

## §四 输出格式

请按面分表输出，每个面一张表，列为：`位置(file:line)` / `本卡判定` / `依据`。判定用三态之一：

- **未见** —— 该处改动落在既有审查存档的绑定区间之外，那轮审查不可能看到它；
- **已见且成立** —— 该处是对既有存档某条意见的回应，且回应成立；
- **已见但回应引入新问题** —— 该处是对既有存档某条意见的回应，但回应本身带来了新的缺陷。

四个问题各自给出结论段。全文**最后一行**固定写：

```text
BLOCKER/HIGH 清零：是
```

或

```text
BLOCKER/HIGH 清零：否
```

## §五 边界

- 全程**只读**：不要修改仓库里的任何文件，不要写入任何新文件。
- 不要运行目录级的 pytest（`tests/unit`、`tests/integration`、`tests/e2e` 整目录）。该仓库在这些目录上有大量与本卡无关的既有失败，会淹没结论；单文件与单 nodeid 级别的运行是可以的。
- 不要连接 7691 / 7687 端口的数据库；`canvas-vault/` 目录只读。
- 你的每一条结论请标明是「实测得出」还是「阅读推断」。如果某条你没有能力在只读约束下证实，请直接写「未验证」并说明需要什么才能验证 —— 这比给一个没有依据的判定有用得多。
