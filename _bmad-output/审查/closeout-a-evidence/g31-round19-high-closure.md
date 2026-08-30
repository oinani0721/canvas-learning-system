# ① round-19 遗留 HIGH 的证据闭合

## 一、这条 HIGH 原文

`_bmad-output/审查/codex-review-CARD-G3-1-round19-2026-08-29.md` 残留清单：

> **HIGH：1**
> MAIN 现网 append-only 账本从已存证的 23 条状态回到旧 22 条快照；**原因与缺失内容不可证**。

即：一个声称 append-only 的账本变短了，而当时既说不清**少了什么**，也说不清**为什么**。
对一个 append-only 结构来说这确实该是 HIGH——所以它值得被证据关掉，而不是被再开一轮 Codex 关掉。

---

## 二、闭合证据一：**缺失内容**已可证（本机实测 diff）

```
$ wc -l backups/learning_events.jsonl.pre-s1-cleanup-20260829-061014 canvas-vault/learning_events.jsonl
      23 backups/learning_events.jsonl.pre-s1-cleanup-20260829-061014
      22 canvas-vault/learning_events.jsonl

$ diff backups/learning_events.jsonl.pre-s1-cleanup-20260829-061014 canvas-vault/learning_events.jsonl
23d22
< {"event_id": "callout:c-409-guard", "event_version": 1, "event_type": "callout_ingested",
   "node_id": "n1", "recorded_at": "2026-08-28T11:52:11.120977+00:00",
   "effective_at": "2026-01-01T00:00:00+00:00",
   "payload": {"callout_type": "question", "text": "why?"}}
$ echo $?
1

$ shasum -a 256 backups/learning_events.jsonl.pre-s1-cleanup-20260829-061014 canvas-vault/learning_events.jsonl
f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de  backups/…pre-s1-cleanup-20260829-061014
2a18023e71a046db8a8c52e098cd48bd0b9898596e4ea3024e18695827796cb6  canvas-vault/learning_events.jsonl
```

**唯一差异是第 23 行被删**，且现网内容是备份的**严格字节前缀**（`diff` 只报 `23d22`，无任何 `>` 或 `c` 行）。
被删的那一条 `event_id` 是 `callout:c-409-guard` —— 一条**测试探针**，不是用户学习数据。

这两个 SHA 与 Codex round-22 报告 §2 独立实测的值**逐字符相同**（round-22 亦记录 live `2a18023e…`、backup `f78b99f3…`），
互为交叉验证。

---

## 三、闭合证据二：**原因**已可证（第五批复核裁定的书面记录）

`_bmad-output/审查/2026-08-29-第五批独立复核裁定.md` §二「阻断项：S1 测试污染 live 生产数据」逐条写明：

> - live vault `canvas-vault/learning_events.jsonl` 有 **1 行**测试事件（`event_id: callout:c-409-guard`，08-28 19:52）；
> - 该字符串**全仓只出现于** S1 车道新建的 `test_vault_scope_409.py:336`；
> - 根因：`isolated_event_log` fixture 只 monkeypatch 了 JSONL 路径，**没有隔离 Neo4j**，
>   已 commit 的测试每跑一次就往生产图谱写一条。
>
> **处置结果（用户 2026-08-29 授权后已全部执行）**：
> 2. ✅ **清理**：备份先行（`backups/learning_events.jsonl.pre-s1-cleanup-20260829-061014` …）；
>    执行后图谱 15→0、**账本移除 1 行（23→22 行）**，该 group 剩余 2 节点为用户真实数据未受影响。

于是 round-19 那句「原因与缺失内容不可证」的两个未知项**都已被填实**：

| round-19 的未知 | 现在的答案 | 出处 |
|---|---|---|
| 缺失内容是什么 | 恰好 1 行，`event_id = callout:c-409-guard` 的测试探针 | 本机 `diff` 实测（§二） |
| 为什么会少 | S1 车道测试污染 live 的**授权清理**，备份先行 | 裁定书 §二 处置项 2（§三） |
| 是否影响真实数据 | 否，现网是备份的严格字节前缀；该 group 剩余 2 节点为用户真实数据 | §二 + 裁定书 |
| 是否可恢复 | 是，23 行原件仍在 `backups/` 且 SHA 可核 | §二 |

---

## 四、为什么这足以关掉，而不是再开一轮

round-19 判 HIGH 的依据是**「不可证」**这个状态本身，不是断言"数据被恶意破坏"。
一旦缺失内容与原因双双可证，且现网是备份的严格前缀、原件仍可恢复，
这条 HIGH 的成立前提就消失了——再开一轮 Codex 也只能读到同样这两份材料，
不会产生新信息，只会消耗 40–55 分钟。这与本卡停轮规则的立意一致。

⚠️ **仍如实保留的边界**（继承自 round-22 LOW #7，本卡不代为消除）：
`canvas-vault/learning_events.jsonl` 与 `backups/` 下的原件**均为 untracked**，
因此「可恢复」的准确范围是**当前这台机器上可恢复**，没有版本化持久保证。
这条边界应写进 G3-1 验收单，不要表述成无条件的"完整恢复"。
