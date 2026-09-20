# Codex 轮次阻塞实证（P1-B 条件 n / P1-C 收尾）

> 批次: BATCH-2026-09-18-第十五批 · 车道 P1 · 卡 CARD-LANCE-INDEX-DELETE-CONTRACT + CARD-G4-5
> 记录时刻: 2026-09-19（复测，非继承先前观测）
> 结论: **gpt-6-astra 在当前 Codex 鉴权态下不可用**，非配额。

## 1. 复测（肯定式判据）

命令（协议 §2 口径，模型/effort 未改）:

```
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "Reply with exactly this token and nothing else: PROBE-OK-B15"
```

- 存档: `model-probe-20260919T043108.txt` / `.stderr`（stderr 不入库）
- `rc=1`
- 肯定式判据 `grep -c 'PROBE-OK-B15'` = **0**（成功串未出现）
- stderr 明文:
  - `warning: Model metadata for 'gpt-6-astra' not found. Defaulting to fallback metadata`
  - `ERROR: {"type":"error","status":400,"error":{"type":"invalid_request_error","message":"The 'gpt-6-astra' model is not supported when using Codex with a ChatGPT account."}}`

⚠️ 首次复测曾用 `timeout 180 ...` 包裹 ⇒ macOS 无 `timeout(1)`，`rc=127`、成功串 0 命中，
**被测命令一次都没跑**。该次结果作废，上表为改用调用方超时后的重跑。

## 2. 鉴权形态（只记键名与类型，不落任何密钥值）

- `codex --version` = `codex-cli 0.153.3`
- `codex login status` = `Logged in using ChatGPT`
- `~/.codex/auth.json`: `auth_mode` 非空；`OPENAI_API_KEY` = **None**；`tokens.*` 非空
- 环境: `OPENAI_API_KEY` 未设置，`CODEX_API_KEY` 未设置

## 3. 已查明的可能出路（需用户裁定，车道不自选）

| # | 路径 | 车道能否自行执行 |
|---|---|---|
| 1 | `codex login --with-api-key`（该子命令存在） | ❌ 缺凭据，只有用户能提供 |
| 2 | 换一个该账号支持的模型 | ❌ 违反用户 2026-09-05 裁定 D（模型固定 gpt-6-astra） |
| 3 | 切回原 Codex 账号 | ❌ 用户操作 |
| 4 | 主 session 人审替代（协议 §1「不等配额」先例） | ⚠️ 需主 session/用户认可 |

## 4. 本轮已做的替代动作（**不是 Codex 轮次，不满足 D-15**）

依根 CLAUDE.md 铁律 3「代码审查必须独立 Agent」，对两卡**绑最终 HEAD**的代码面
做了 5 视角独立对抗审查，结果落 `internal-adversarial-review-*.md`。

明确声明：
- 该结果**不得**充当 D-15 的 Codex 轮次；
- 台账与验收单引用时必须标注「内部 Agent 审查，非 Codex」；
- P1-B 的 Codex 轮次实况仍为 r1/r2/r3（已跑、已整改），**差绑最终 HEAD 的 r4**；
- P1-C 的 Codex 轮次实况为 **0**。
