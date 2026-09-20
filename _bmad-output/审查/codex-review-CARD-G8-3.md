> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p6-skills-w · 卡 CARD-G8-3 round-1
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-3.md)" > _bmad-output/审查/codex-review-CARD-G8-3.md 2> _bmad-output/审查/codex-review-CARD-G8-3.stderr </dev/null`（rc=0；2026-09-19 23:48:56 → 00:09:45 -0700）
> 审查绑定: `2b298383`（本卡末 commit = 最终代码；`git --no-pager diff --stat --no-color 2b298383 HEAD -- . ':(exclude)_bmad-output'` = 空）
> 会话头自证（行号按 .stderr 原文括注）: 第 2 行 `OpenAI Codex v0.153.3` / 第 5 行 `model: glm-5.3` / 第 9 行 `reasoning effort: max`
> Jev 分诊: `evidence-g83/jev-triage-2b298383.json`（vault_lint urgency 2.92 / test 2.18，已并入 prompt ③）

---

BLOCKER: 无 / HIGH: 无

## BLOCKER

无。

## HIGH

无。

## MEDIUM

1. `backend/scripts/vault_lint.py:1199-1237` — DLQ 在 partial/size_capped 时虽然整体进入 degraded，但 `total_backlog` 仍保留 `0`，PermissionError 条目的 `backlog` 也会保留初始 `0`，机读聚合值仍像“已知为零”。  
   **负控输入**：只放一个 `>8 MiB` 的 JSONL（或一条不可读 JSONL），其余七条不存在；当前会报 degraded 但 `details.total_backlog == 0`，应显式为 unknown/`None` 才不弱化“未知不许冒充 0”。

2. `backend/tests/unit/test_vault_lint.py:1629-1632` — “已答”干净 fixture 同一行同时含有 blockquote 回复和 `[[R-Q]]` wikilink，且没有下一条批注/`## ` 边界反例，三个已答形态和窗口边界都没有独立判别力。  
   **门未覆盖的路径**：分别加入纯 `**v1.3 回复**`、纯 `[[R1-Q1]]`、以及“未答批注 → 下一条批注的回复/H2 后回复”三类输入；删掉任一 marker 或边界判断时现有测试仍可全绿。

3. `backend/scripts/vault_lint.py:1444-1462` — recap 子进程只验证 `unsourced_conclusions` 是 dict，未验证 `value/node_ids` 类型；合法 JSON 但 schema 畸形时会在累加或 `list()` 处抛异常，或把字符串 `"0"` 当无积压。  
   **未被拦下的输入**：让 `--recap-scan` 指向输出 `{"signals":{"unsourced_conclusions":{"value":"2","node_ids":3}}}` 的真实脚本；预期应逐板 degraded，当前会 TypeError/退出 1，`"0"` 则会假 ok。

## LOW

1. `backend/scripts/vault_lint.py:959-974` — `_now_dt()` 只捕获 `ValueError`，而边界日期在做时区转换时可抛 `OverflowError/OSError`，与 `resolve_today()` 的配置错误处理不一致。  
   **负控输入**：`--now 9999-12-31T23:59:59+14:00 --only backup_freshness ...`；预期退出 3，当前路径可能裸异常/退出 1。

2. `backend/scripts/vault_lint.py:1590-1602` — `_EPILOG` 的 degraded 文案漏掉实际存在的 `backend_dir` 不可用、`原白板/` 缺席、spawn OSError，以及“合法 JSON 但无 signals”的精确原因。  
   **对照输入**：分别用 file-as-backend、缺 `原白板/`、旧版 recap 脚本跑 CLI，再对照 `--help`；代码会 degraded，但帮助文案没有完整披露这些分支。

3. `backend/tests/unit/test_vault_lint.py:1871-1913` — 同源锁 (B) 的副作用证据只比较 `git status backend/`，不能观察 ignored cache、backend 外写入或出站连接，因此不能证明“无落盘/无网络”。  
   **门未覆盖的路径**：用网络拒绝包装和 backend 外文件快照重跑该子进程；静态看本 traces import 链未发现直接 socket 调用，但现有测试本身无法证明这一点。

## 定点核对

- ⓪ 窗口实现先检查下一条 `**User...**` 和 `^## ` 再检查答案 marker，不会越过这两类边界继承答案；未关联的 `[[R-Q]]` 文本会被当作已答，这是卡内明示的轻量 grep 限制。
- ① size capped 会 `size_capped=True`、`backlog=None`、整体 warn/degraded；PermissionError也会进入 partial/degraded。剩余问题仅是上列聚合字段语义。
- ② 备份检查取最后一条匹配 `OK:` 的日志行，不会被后续 `SKIP:` 遮住。
- ③ recap timeout/rc≠0/json-decode/no-signals 均逐板记录并继续扫描，已取得的 unsourced findings 会保留。
- ④ 静态核对 `vault_lint.py` 无 `from app` / `import app`；DLQ 八键与指定路径一致，测试有 AST 键集加包路由 resolve 两层锁。
- ⑤ 四个主负控的指定断言分别能杀死“已答恒真”“行数恒 0”“新鲜恒真”“阈值放大”一层变异；缺口集中在marker/边界分形和 schema 畸形。
- ⑥ `_EPILOG` 与主分支大体一致，但存在上列低级别遗漏。

本轮只读：未改文件、未连数据库或网络服务、未运行测试/子进程。Git 状态里已有未跟踪审查/evidence 文件，未触碰。
