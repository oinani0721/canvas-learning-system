# ⛔ 本文件是第二次归因，**不完整** —— 最终归因见同目录 codex-final-attribution-20260918T202306.md
# 真相是「token 失效 + 配额耗尽」两者叠加；本文件只抓到其中一个。
---
# ⛔ 更正：Codex 不可用的真因是**未登录**，不是配额耗尽 @ 2026-09-18T20:07:08

> 本文件**更正**同目录 `codex-r1-quota-exhausted-20260918T200003.txt` 的判断。
> 那一份没有错记事实（两次确实 0 字节、错误文本确实是 usage limit），但**归因错了**。

## 三次尝试的完整时间线

| 时刻 | rc | md | stderr 末行 |
|---|---|---|---|
| 19:57:11 | 1 | 0 字节 | `ERROR: You've hit your usage limit … try again at Sep 24th, 2026 2:05 AM.` |
| 19:58:42 | 1 | 0 字节 | 同上（协议 §2.1 要求的「重发一次」） |
| **20:05:08** | 1 | 0 字节 | **`ERROR: unexpected status 401 Unauthorized: Missing bearer or basic authentication in header`** |

第三次错误**变了形态** ⇒ 顺着查服务端状态：

    $ codex login status
    

    $ ls ~/.codex/auth.json
    不存在

## 真因

**Codex CLI 处于未登录状态**（`~/.codex/auth.json` 缺席）。
`usage limit` 那两条大概率是 token 失效前后的过渡态报错，**不是真的配额问题**。

## 为什么这个更正重要

两种归因导向**完全不同**的处置：

| 归因 | 处置 | 代价 |
|---|---|---|
| 配额耗尽 | 等配额 / 人审替代 | 本卡 Codex 轮次 = 0，需主 session 裁定 |
| **未登录** | **用户跑一次 `codex login`** | 一条命令，之后按 D-15 正常走多轮 |

我照着第一条错误消息走完了协议 §2.1 的「重发一次 → 人审替代」全流程，
直到第三次复测的错误文本变了才发现真因。

## 教训（已进台账）

记忆里原有一条：「外部服务自报的**重置时间**是一次观测，不是不变量」
（协议 §2.3 的 R-05：`dcaaaef9` 报「配额耗尽至 09-15」，24 分钟后实测恢复）。

本次把它推进一步：**外部服务返回的错误文本本身也可能误导**。
判据应当盯住**服务端状态**（`codex login status` / auth 文件是否存在），
而不是它某一次返回的 message 字符串。复测时如果错误**形态变了**，
那是信号 —— 说明第一次的归因需要重新做。

## 当前状态

- 代码定稿 `c6a7f446`，送审 SHA `967cf4cf`，`git diff --stat c6a7f446 HEAD -- . ':(exclude)_bmad-output'` = 空
- prompt 现成：`_bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-R3-r1.md`（已填审查绑定 SHA）
- **阻塞点**：需用户在 Claude 之外执行 `codex login`（交互式登录，Claude 代做不了）
- 登录后即可按 D-15 正常走多轮，人审替代报告 `human-review-substitute-*.md` 保留作为**补充**而非替代
