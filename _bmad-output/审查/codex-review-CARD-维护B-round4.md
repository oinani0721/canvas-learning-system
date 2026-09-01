# Codex 独立复核存档 — CARD-维护B round-4

> ## ⚠️ 存档来源说明（如实）——本轮再次被截断，无终裁
>
> 本轮 codex 进程在复核中途被其 cyber 过滤器拦截（`ERROR: This content was flagged
> for possible cybersecurity risk`），stdout 落盘 **0 字节**、无最终报告与裁决句。
> 本轮为停轮规则上限（round-4）——按卡文：到顶仍有 BLOCKER/HIGH（或无终裁）→
> **验收单显著降级声明 + 登记用户裁决，不宣称清零、不合并、留台账**。
>
> ## 从 stderr 逐字抢救的中途产出（未删改摘要）
>
> - ✅ **目标套件亲跑 246 passed**（本轮时点，round-4 三缝隙整改前）。
> - ⚠️ **四条探针实测**（stderr :4551-4555，逐字）：
>   - `A-indented-blockquote-list-hidden-signals: rc=0` —— ` > - ``` `（引用标记
>     **前**带前导空格）围栏藏信号**放行**；它先用 markdown-it 实证该形态渲染在
>     `<pre><code>` 内 → 真洞。
>   - `B-manifest-appendix-fake-signal: rc=0` —— **manifest 模式**附录伪无来源结论
>     放行（HIGH-4 的③段限定曾只挂 fallback 分支）→ 真洞。
>   - `C-h6-cjk-numbers: rc=0` —— 允许式标题行**中文数词**（`九十八万`）绕过
>     （`\d+` 只抓 ASCII）→ 真洞。
>   - `D-null-value-with-prefix-N: rc=1` —— ⑦ 前置 N 在无据档被正确拦 → 确认修复有效。
> - 车道对 A/B/C **独立复现实锤**（`evidence-maintb-r2/round4-repro.txt` 全部 exit 0）
>   后整改（commit 见 git log）：
>   - A: `_quote_width`/`_indent_after_quotes` 重写为**绝对内容列**口径（前导空白
>     计入引用系），统一与 fence_list_col 比较；
>   - B: ③段限定移出 data_mode 条件（manifest 同样生效）；
>   - C: 允许式行内数字提取加中文数词（`_cjk_to_int` 可解析入池、解析失败 fail-closed）。
>   整改后 `round4-after3.txt`：A/B/C 全拦 + round-3 全矩阵 19/19 无回归 + 放行门不误伤。
> - **⛔ 本轮无终裁 → 按停轮规则不宣称清零**；三条新缝隙的整改**无独立复核轮确认**，
>   与「round-4 截断」一并记入验收单显著降级声明与未合卡台账。
>
> tokens used: 184,529（stderr 尾部）；stderr 全文（331KB）保留于 `.stderr`。
