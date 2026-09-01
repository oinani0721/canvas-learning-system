终裁：**FAIL**。`6c81ebc9` 未清零：B1、B3 仍各有一个可复现 BLOCKER；B2、B4 的题面窄条件及 H5/H6 声明通过。禁改面零越界。

| 项目 | 裁决 |
|---|---|
| B1 required 守卫 | **FAIL / BLOCKER** |
| B2 CI 环境 | **PASS** |
| B3 触发面与并发写 | **FAIL / BLOCKER** |
| B4 fail-closed | **PASS，但有 MEDIUM 残口** |
| H5/H6 声明 | **PASS** |
| 新缺陷/越界 | **功能缺陷有，禁改越界无** |

## 1. B1 — FAIL / BLOCKER

[实现:123](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/scripts/spec-tools/check-openapi-drift.py:123) 的窄验收均通过：

```text
plain enum 内嵌 required 反序 -> clean=False，点名 required[0]/[1]
正常 Schema required 反序     -> clean=True, details=[]
required_string_arrays=281 guarded=281 unguarded=0
```

相关测试：

```text
21 passed, 10 warnings
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0
```

但守卫仍只凭宿主是否含 `type`/`properties` 判断。合法 enum 实例也可把 `type` 当普通数据：

```json
{"enum":[{"type":"instance-tag","required":["first","second"]}]}
```

将 `required` 反序后调用真实 `compare()`：

```text
{"clean": true, "details": []}
```

即继续吞漂移。同类 `example/default/x-value` 也是假绿。新增测试 [test:189](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/contract/test_openapi_snapshot_drift.py:189) 恰好没有给 enum 实例加入 `type/properties`，未承重该边界。`281/281` 只能证明当前快照没触发，不能证明门健全。

## 2. B2 — PASS

Export 与 drift gate 均在 [workflow:79](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/.github/workflows/api-spec-sync.yml:79)、[workflow:99](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/.github/workflows/api-spec-sync.yml:99) 注入三项环境，PyYAML 提取后与 [test.yml:108](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/.github/workflows/test.yml:108) 完全相等：

```text
EXPORT_EQ_TEST=True
DRIFT_EQ_TEST=True
```

更严格的 `env -i`、空 `NEO4J_PASSWORD`、禁用本地 `.env` 加载复验：

```text
CLEAN_IMPORT_OK
exit 0
```

负控 `DEBUG=false`、空 key/password：

```text
exit 1
NEO4J_PASSWORD must be set explicitly...
```

配方足以导入 `app.config`。

## 3. B3 — FAIL / BLOCKER

触发路径方面，当前真实文件已覆盖：PR、push、hook 均覆盖 `api/**`、`models/**`、`mcp/**`、`main.py`、`config.py`。HEAD 不存在 `backend/app/schemas/`；实际 `backend/app/models/schemas.py` 已被 `models/**` 覆盖。若未来新增字面路径 `backend/app/schemas/**`，workflow 尚不覆盖，只有 hook 覆盖。

本机 `lefthook 2.1.6` 及仓库锁定的 `1.13.6` 实测一致，且反证了两条整改注释：

```text
YAML glob 数组                         MATCH（并非失效）
api/**/*.py 对 api/router.py           skip
api/**/*.py 对 api/v1/router.py        MATCH
不存在的花括号备选路径                 MATCH（无需预先存在）
api/*.py 对 api/v1/router.py            MATCH（单 * 跨 /）
```

复制三条真实 glob 全量探针：

```text
expected surface=87
union=87
missing=[]
spec-sync-root=2
spec-sync-flat=85
spec-sync=57
overlap=57
```

因此当前 57 个文件会同时启动两条并行写命令。

更严重的是 [write_snapshot:291](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/scripts/spec-tools/check-openapi-drift.py:291) 为所有写者固定使用同一个 `openapi.json.tmp`。主审以线程屏障调用真实 `write_snapshot()`：

```text
A -> FileNotFoundError: openapi.json.tmp -> openapi.json
B -> ok
final JSON valid
```

独立进程八轮受控碰撞也得到：

```text
trials=8 child_failures=8 corrupt_finals=0
```

最终文件完整不代表协议安全；共享临时 inode 仍可被并发 truncate/write，且一方 rename 后另一方必可能 ENOENT。它不是“每进程独立 tmp + 最后写者胜”。

另三条 hook 的 `git add` 均未检查退出码，之后还有成功 `echo`（[lefthook:51](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/lefthook.yml:51)）。安全探针证明 `false; printf` 最终 exit 0，因此 index-lock 导致的 staging 失败会被吞并虚报 “staged”（MEDIUM）。

## 4. B4 — PASS，但非完整 fail-closed

题面三项均通过：

- [基线读取:188](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/.github/workflows/api-spec-sync.yml:188) 已无 `{}` fallback；不存在的 ref 实测 exit 128。
- 非法 JSON得到 `PARSE_ERROR`，随后 [exit 1:222](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/.github/workflows/api-spec-sync.yml:222)。
- [summary:470](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/.github/workflows/api-spec-sync.yml:470) 仅 success 才显示绿色 None；skipped/failure 均显示中性结果。

残余 MEDIUM：代码丢弃 oasdiff 退出码，并把任何可解析但非 list 的 JSON（如 `{}`）计为 0。官方当前 CLI 正常输出确为裸数组，所以不改判题面窄项，但这不是严格“状态码 + 输出结构”双重 fail-closed。[官方 JSON formatter](https://github.com/oasdiff/oasdiff/blob/main/formatters/format_json.go)

另有范围外既存风险：安装 URL 当前返回 404；官方发布资产使用带版本文件名。该行 blame 到旧提交 `14f0412d`，不是 `6c81ebc9` 引入，但 PR job 目前可能在运行 oasdiff 前先失败。[官方 installer](https://github.com/oasdiff/oasdiff/blob/main/install.sh)、[当前 releases](https://github.com/oasdiff/oasdiff/releases)

## 5. H5/H6 — PASS

- §三.2 如实声明未锁依赖：[requirements.txt:18](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/requirements.txt:18) 的 FastAPI、[24](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/requirements.txt:24) 的 fastapi-mcp、[46](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/requirements.txt:46) 的 Pydantic 均只有下限。
- §三.3 如实声明 Schemathesis 使用 `importorskip`、`from_asgi`，且不在 `test.yml` 白名单。[workflow:315](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/.github/workflows/api-spec-sync.yml:315) 已明确承认 HTTP/example/hooks 回放面丢失及未接 CI，不再声称覆盖无损。

LOW：summary 中“由 Schemathesis 承担”仍略强，更准确应是“存在未进 CI、可被 importorskip 的本地可选测试”。

## 6. 新缺陷与范围

禁改面实测：

```text
FORBIDDEN_COUNT=0
TOTAL_CHANGED=8
tracked diff exit=0
cached diff exit=0
HEAD=6c81ebc9aa8ce77cc97c4b7b1cd036bd36a617f5
```

其余中低项：

- MEDIUM：[DETAIL_LINE_CAP=50](~/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/scripts/spec-tools/check-openapi-drift.py:73) 仍隐藏第 51 条后的对象名；新增总数不能替代点名，验收单所称“已修正”不成立。
- MEDIUM/隐私卫生：整改提交新增 545,951 字节、7,384 行原始 Codex stderr，含 226 处个人绝对路径及 session id；未发现私钥或常见高熵 token，但不宜把完整会话日志提交为证据。
- LOW：验收单仍写“7 文件”“19 测试”，实际整改 diff 为 8 文件、测试为 21 条。
- LOW：原始 stderr 使 `git diff --check` 因大量 trailing whitespace 返回 exit 2。
- LOW：oasdiff 注释称退出码同时编码 breaking/error，但未传 `--fail-on` 时 breaking 本身不会返回 1。[官方说明](https://github.com/oasdiff/oasdiff/blob/main/docs/BREAKING-CHANGES.md)

未运行 GitHub Actions、TestClient、Neo4j 端口；`graphiti-canvas` 本会话未暴露。工作树 tracked/cached 均保持干净，仅保留开场即存在的三份 Round‑2 未跟踪输出。

BLOCKER/HIGH 清零: 否
