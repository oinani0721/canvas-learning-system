# Codex 不可用的**最终**归因：配额耗尽（登录问题已解决，但不是唯一原因）
@ 2026-09-18T20:23:06

> 本文件是本卡对 Codex 不可用的**第三次也是最终**归因。
> 前两份（`codex-r1-quota-exhausted-*.txt` / `codex-unavailable-root-cause-*.md`）各对了一半，
> 都已加更正指路。我两次归因都不完整，如实记在这里。

## 完整时间线（五次尝试）

| # | 时刻 | 登录状态 | rc | md | stderr 末行 |
|---|---|---|---|---|---|
| 1 | 19:57:11 | 未登录 | 1 | 0 | `usage limit … try again at Sep 24th` |
| 2 | 19:58:42 | 未登录 | 1 | 0 | 同上（协议 §2.1 的「重发一次」） |
| 3 | 20:05:08 | 未登录 | 1 | 0 | **`401 Unauthorized: Missing bearer`** |
| — | 20:09 | — | — | — | 查出 `codex login status` = `Not logged in`，`~/.codex/auth.json` 缺席 |
| — | 20:14 | — | — | — | 起 `codex login`（本地回调 localhost:1455），**用户在浏览器完成授权** |
| — | 20:19 | **Logged in using ChatGPT** | — | — | `auth.json` 3993 字节 |
| 4 | 20:20:37 | 已登录 | 1 | 0 | **`usage limit … try again at Sep 24th`** |
| 5 | 20:22:12 | 已登录 | 1 | 0 | 同上（登录后的「重发一次」） |

    $ codex login status
    

## 我两次归因都不完整

| 归因 | 我说过 | 实际 |
|---|---|---|
| 第一次 | 「配额耗尽」 | 对了一半 —— 配额**确实**满了，但当时还叠加了 token 失效 |
| 第二次 | 「真因是未登录**不是**配额」 | 也对了一半 —— 登录**确实**掉了，但配额满是更根本的那个 |
| **最终** | — | **两者都有**：token 失效（已解决）+ 账号级配额耗尽（未解决） |

第二次归因的错误更值得记：我看到错误文本从 `usage limit` 变成 `401`，
就断定「usage limit 那两条大概率是过渡态报错，不是真的配额问题」——
**那是一个推断，我把它当成了结论写进存档**。登录之后跑第 4 次，错误又回到 `usage limit`，
才证明配额那一条从头到尾都是真的。

**教训**：错误文本 A 被错误文本 B 取代，不等于 A 是假的。
两个独立的故障可以叠加，修好一个只会让另一个重新显形。
正确的做法是**逐个排除**（修 B 之后重测，看 A 还在不在），而不是用 B 去否定 A。

## 模型可用性（顺带实测，非本卡阻塞）

    $ codex exec -m gpt-5.6 …
    ERROR: The 'gpt-5.6' model is not supported when using Codex with a ChatGPT account.

⇒ ChatGPT 账号下模型集受限；本卡要求的 `gpt-6-astra` 走的是同一账号的配额池。

## 当前阻塞与可行处置

**阻塞**：账号级 Codex 配额耗尽。这不是判据问题、不是登录问题，Claude 侧无法解除。

按协议 §2.1「0 字节存档重发一次，再 0 字节 → **主 session 人审替代，不等配额**」，
本卡已转人审替代（`human-review-substitute-*.md`，逐条回答 prompt 的 8 个问题、每条带判据）。

**用户可选的解除办法**（任一）：
1. 在 https://chatgpt.com/codex/settings/usage 购买 credits，之后我立刻重发；
2. 等配额自然恢复后告诉我 —— ⚠️ 「Sep 24th」是服务端自报，协议 §2.3 的 R-05 有先例
   （报「6 天后」结果 24 分钟就恢复），所以**不必等到那天**，随时可让我复测；
3. 认可人审替代，本卡按协议 §2.1 进合并队列，由主 session 复核时裁定。

## 本卡的 Codex 就绪状态（配额一恢复即可立刻跑，无需任何准备）

| 项 | 值 |
|---|---|
| 登录 | ✅ `Logged in using ChatGPT` |
| 代码定稿 | `c6a7f446` |
| 送审 SHA | `967cf4cf`（prompt 内已填） |
| 末轮绑定判据 | `git diff --stat c6a7f446 HEAD -- . ':(exclude)_bmad-output'` = **空**（恒成立） |
| prompt | `prompts/codex-prompt-CARD-G6-9c-R3-r1.md`，五分节齐全 |
| 存档命名 | `-r1`（撞名核已过） |
| 首部生成器 | 已写好（协议 §2.1 六行 blockquote + stderr 会话头三行括注行号） |

0 字节的 md 与 stderr 每次都已删除，从未入 commit。
