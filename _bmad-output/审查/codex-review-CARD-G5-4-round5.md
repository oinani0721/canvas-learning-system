# Codex 审查存档 — CARD-G5-4 / CARD-G5-9（round-5）

> **状态**: round-5 分析完成、终稿输出**第三次**被 Codex 平台内容过滤器误拦
> （`ERROR: This content was flagged for possible cybersecurity risk`，与 MEMORY
> `reference_codex_exec_gotchas` 记录的已知坑一致——审阅提示词含"绕过路径"等词触发）。
> 本轮发现由完整 transcript（162,942 tokens，`tasks/b9ir7ra3s.output`）提取，
> 其中含 Codex 亲自构造并执行的 **16 行实测反例表**（脚本构造报告 → 跑 `--verify` → 记录 exit code），
> 证据强度与正式报告等同。
>
> **处置**: 见同目录 `codex-review-CARD-G5-4-round5-处置.md`（含 transcript 原始反例表与逐条处置）。

## Codex round-5 已确认的事实（transcript 摘录）

- 指定判据亲跑：**212 passed, 187 warnings**（当时基线；round-5 处置后为 224 passed）
- Codex 自述（transcript L3215）：「现有测试只证明已列举样例；终裁仍需覆盖测试未枚举的合法 Unicode/YAML/Markdown 形态」
- Codex 自述（transcript L2368）：静态检查发现「数值检测实际按 Unicode 类别而非完整 numeric 属性、发布 FD 在 link 前已关闭」
  —— 两点均已在 round-5 处置（前者改文案白名单彻底绕开字符层面，后者改 fd 保持打开取 fstat 后核对）

## 16 行实测反例表与逐条处置

见 `codex-review-CARD-G5-4-round5-处置.md`，其中同时记录了**三例误伤**
（`统计口径尚未一致` / `说明十分清楚` / `legitimate-nested-list` 被误判违规），
这三例与绕过同等重要——它们证明"黑名单式禁令"两头都不可靠，是本轮改为白名单的直接依据。
