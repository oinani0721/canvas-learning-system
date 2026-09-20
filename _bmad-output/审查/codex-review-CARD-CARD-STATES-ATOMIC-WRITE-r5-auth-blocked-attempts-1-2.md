> 批次: BATCH-2026-09-18-第十五批 · 车道 P4 · 卡 CARD-CARD-STATES-ATOMIC-WRITE round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-CARD-STATES-ATOMIC-WRITE-r5.md)"`
> 审查绑定: **未取得**（目标本应为 `d317b2ee7dd6cad8b68da913642d78cdd25a9e5d`）
> 会话头自证: **不适用** —— 本轮未产生会话，见下。
> 判定: **未取得**

---

# ⛔ round-5 未取得：Codex 鉴权失效（批级环境事件）

按协议「0 字节存档重发一次，再 0 字节 → 主 session 人审替代，不等配额」，本文件记录
两次尝试的实测，**不冒充一次复核**。

## 实测

| 次 | 时刻（+0800） | 产出 | `.stderr` 末行 |
|---|---|---|---|
| 1 | 2026-09-18 21:42 | `.md` **0 字节** | `ERROR: unexpected status 401 Unauthorized: Missing bearer or basic authentication in header, url: https://api.openai.com/v1/responses` |
| 2 | 2026-09-18 21:4x（重发） | `.md` **0 字节** | 同上 |

诊断（只读）：

```
$ codex login status
Not logged in
$ ls -la ~/.codex/auth.json
（文件不存在）
```

> ⚠️ **更正（独立复核指出）**：本文件原写「另一 request id」不可自证 —— 第二次的 `.stderr`
> 被 `2>` **覆盖**了前一次，`grep -oE 'request id: req_[a-f0-9]+' | sort -u` 实测**只有 1 个**
> （`req_33b5137585bf4e90838a36f9f0b94419`）。「两次尝试」这一事实由本 session 的命令历史与
> 两次 `codex rc=1` 佐证，但**在存档内不可自证**，如实更正。

**不是配额问题**，是**未登录**。同机另一车道（`card-p9-testinfra`）的 codex 在 20:48 还在
正常跑，说明鉴权是在那之后掉的 ⇒ 这是**批级事件**，其余车道的 Codex 复核同样会被挡。
恢复动作只能由用户本人在 Claude 之外执行（交互式 `codex login`）。

## 本卡当下的轮次状态（如实）

- **round-4 判定 `BLOCKER=0 HIGH=0 MEDIUM=4 LOW=3`**，绑 `5d69728a1c7964e9f8e09f0c908b59e5fca7ac2a`。
- round-4 之后本卡**只改了测试与 spec 文字**：
  `git diff --stat 5d69728a d317b2ee -- backend/app/services/review_service.py` → **空**
  （生产代码与 r4 所审那份**逐字节相同**）。改动集中在
  `backend/tests/regression/test_g3_7_truth_source.py` 与 `openspec/specs/concept-identity/spec.md`，
  内容是「修掉 r4 指出的 MEDIUM-2 flaky 门 + 用行为门覆盖 r4 MEDIUM-1 + 关掉 r4 LOW-5/LOW-7」。
- 按 D-15「审后再改代码 ⇒ 必再送一轮」，**这一轮是欠的**。协议对此的兜底口径是
  **主 session 人审替代**。

## 已由独立 agent 代行（不冒充 Codex）

按项目 `CLAUDE.md` 铁律 #3「代码审查必须独立 Agent」，本轮由一个**全新上下文的 Claude
独立 agent** 做了对抗性复核，报告在
`_bmad-output/审查/independent-review-CARD-CARD-STATES-ATOMIC-WRITE-r5.md`，
判定 **BLOCKER=0 HIGH=0 MEDIUM=3 LOW=5**、结论「可以收官，无必须在本卡内解决的条目」。
⛔ 它**不是 Codex 判定**，供主 session 裁定时参考。

## 移交给主 session 的复核面（建议聚焦）

1. `_TrackingLock` 包真锁的顺序（`__enter__` 先取真锁再记账、`__exit__` 先记账再放真锁）
   会不会让重叠检测漏判/误判；`entered == 4` 是否确定性。
2. 两条新门 `…s7_seq_is_allocated_before_dispatch` / `…s7_failed_publish_does_not_advance_the_watermark`
   有没有门未覆盖的路径。
3. 十段负控（`negctl-r5-*`）是否各只拆一层；本轮新增的 9/10/11 三段是否精确。
4. spec 对「尝试清理 vs 保证无残留」的新措辞是否仍超出实现。
5. `unit-r5-*.txt` 那条 `>` 的归因（高负载导致的 5s 墙钟超时假红）是否成立——
   对照 `unit-r5b-*.txt` 空载复测。
