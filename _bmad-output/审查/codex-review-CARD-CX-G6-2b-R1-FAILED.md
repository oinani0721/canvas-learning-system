# CARD-CX-G6-2b-R1 · Codex 外审未产出（两轮 0 字节 · 环境阻断）

> `[BATCH-2026-09-05-第十一批 / CARD-CX-G6-2b-R1]` · 2026-09-05
> 本文件是失败证据的**摘录**。原始 `*.stderr` 按 `.gitignore:257-261`（第八批收官规则）
> 永不入库，留在工作树 `card-x2-g62b/_bmad-output/审查/` 下：
> `codex-review-CARD-CX-G6-2b-R1.stderr`（round-1，10864 字节）
> `codex-review-CARD-CX-G6-2b-R1.round2.stderr`（round-2，协议要求的重发）

## 结论

**外审未达成。** X2 `92734207` 的代码面**仍属零外部复审**——
这正是本卡要消除的状态，请勿据本卡销掉该标记。

## 命令（与协议 `.claude/rules/card-batch-protocol.md` §2 逐字一致）

```
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-CARD-CX-G6-2b-R1.md)" \
  > <树>/_bmad-output/审查/codex-review-CARD-CX-G6-2b-R1.md \
  2> <树>/_bmad-output/审查/codex-review-CARD-CX-G6-2b-R1.stderr </dev/null
```

## 两轮结果

| 轮次 | rc | 输出 .md | stderr 尾部 |
|---|---|---|---|
| round-1 | 0 | **0 字节** | 见下（同一条 400，重复两次） |
| round-2（协议要求的重发） | 1 | **0 字节** | 同上，逐字相同 |

```
warning: Model metadata for `gpt-6-astra` not found. Defaulting to fallback metadata;
this can degrade performance and cause issues.
ERROR: {"type":"error","status":400,"error":{"type":"invalid_request_error",
"message":"The 'gpt-6-astra' model requires a newer version of Codex.
Please upgrade to the latest app or CLI and try again."}}
```

## 诊断

本机 `codex-cli 0.147.0`（`/opt/homebrew/bin/codex`）。

这是**第四种 0 字节成因**，不在既有三因（stdin 挂起未加 `</dev/null` / 被审内容触发
内容过滤 / 网络——`codex` 是 reqwest，不读 macOS 系统代理，只认 `HTTPS_PROXY`）之内：
**CLI 版本旧于服务端对该模型的要求**，服务端直接 400。

分辨要点（写给下一个撞上的人）：

- 三因都不会在 stderr 里留下带 `"status":400` 的结构化 JSON；这一条会。
- 内容过滤的表现是**跑了一段推理之后**才断，stderr 里能捞到推理标题；
  这一条是**请求一发出就 400**，stderr 里只有 prompt 回显 + 报错。
- 网络因的表现是 `tls handshake eof` 之类传输层报错，与 HTTP 状态码无关。
- 两轮**逐字相同**的错误 = 确定性，不是抖动，重发第三次没有意义。

## 「用默认模型」这条退路不存在

在车道树内跑一条不带 `-m` 的最小探测，codex 打印的会话头是：

```
OpenAI Codex v0.147.0
workdir: …/card-x2-g62b
model: gpt-6-astra
provider: openai
reasoning effort: ultra
```

**默认模型就是 `gpt-6-astra`**（已配置在 codex 配置里，与 2026-09-05 的裁定一致）。
所以「省掉 `-m` 用默认」跑的仍是同一个不可用的模型。

## 影响面：批级，不只本卡

第十一批其余车道执行同一条协议命令时会撞上**同一个 400**。
建议主 session 优先处置——升级 `codex` 是 homebrew 全局二进制的变更，
会影响全部并行车道，本车道**未擅自执行**。

裁决点登记在 `_bmad-output/验收单/UAT-CARD-CX-G6-2b-R1-2026-09-05.md` §6 的 **D-1**。

## prompt 已就绪

`_bmad-output/审查/prompts/codex-prompt-CARD-CX-G6-2b-R1.md`（5383 字符，五分节，
末行要求「BLOCKER/HIGH 清零：是/否」）。已过 cyber 触发词自检：
`构造 / 可复现 / 打穿 / 绕过 / 规避 / 攻击` 计数全 0。
环境修好后**原样重跑**即可，不需要改一个字。
