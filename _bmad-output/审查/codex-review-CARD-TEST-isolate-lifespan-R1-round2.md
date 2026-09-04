# round-2 —— 未取得裁定（本文件不是裁定）

⛔ **这份文件不是审查裁定，不含 BLOCKER/HIGH 计数，也没有「清零」判定行。**
它记录的是 round-2 这一轮为什么没有产出裁定。正式裁定在
`codex-review-CARD-TEST-isolate-lifespan-R1-round3.md`。

写这份记录，是因为原本这里躺着一个 **0 字节文件** —— 后人看到只会以为审查跑丢了，
无从判断是"没发"、"发了被拒"还是"发了但内容丢了"。三者的处置完全不同。

## 三次尝试，三种不同的死法

| # | 时间（2026-09-04） | rc | 正文 | stderr | 死因 |
|---|---|---|---|---|---|
| 1 | 09:00 | 0 | 0 字节 | 24,551 B | **网络**：`tls handshake eof` → `Reconnecting… 1/5…5/5` → `stream disconnected before completion`。stderr 里只有 prompt 回显，**零推理正文** |
| 2 | 09:16 | — | 0 字节 | 868,972 B | **被我误杀**：我用忙等循环 `until [ -s "$MD" ]; do :; done` 轮询正文落地，10 分钟工具超时的 SIGTERM 连带杀死了同 session 的 codex 后台任务（`status=killed`）。它当时已连上、零传输错误、正在正常推理 |
| 3 | 09:5x | 0 | 0 字节 | 467,892 B | **内容过滤**：`This content was flagged for possible cybersecurity risk`，且 `tokens used 209,708` —— 审查**跑完了大部分工作**，是在最后交付时被拦 |

三份 stderr 均已留存（scratchpad `round2-attempt{1,2,3}*.stderr`）。

## 这一轮的实际产出：从第 3 次 stderr 抢救的线索

第 3 次的 stderr 第 7489 行留下了审查方自己的阶段性结论，逐字抄录：

> 目前已经出现**可复现的冻结阻断项**，不是"措辞问题"：AST 门对 tuple 解包工厂与同名
> 工厂重定义均返回空违规；runtime shell 门也能在输出 `compgen` 已损坏的同时 rc=0、
> 宣告 `unchanged`。我正在对另外三条运行时护栏反例做主审复核，尤其确认它们是否是
> 真实线程交错/普通 import 路径，而不是只靠人为篡改得出的假象。

⚠️ 注意最后一句：**它的复核没做完**。所以这份抢救清单既不完整、也未经它自己确认。
基于它做出的任何定性都是暂定的 —— 事实上后来 round-3 推翻了其中三条（见验收单
§7.7a）。

抢救出的条目、逐条复现结果与处置，见验收单 §7.6b–§7.6f；被 round-3 推翻的部分见 §7.7a。

## 与完成条件 (i) 的关系（如实说明，不粉饰）

卡文 (i) 要求「round-2 md `wc -c` 非空、B/H 明写、末行清零字样、绑定 = 实现最终态」。

- 本文件现在非空，但它**不含 B/H 计数、没有清零判定行** —— 因为 round-2 从未产出裁定，
  凭空写一个就是伪造。
- 四项**全部成立**的是 `…-round3.md`（17,119 字节，`FAIL（1 BLOCKER / 8 HIGH /
  7 MEDIUM / 2 LOW）`，末行 `BLOCKER/HIGH 清零：否`，审查方自行复核绑定 = `de57e375`
  且 `de57e375..HEAD` 排除 `_bmad-output/` 后代码 diff 为空）。

**所以 (i) 在 round-2 这一轮上无法成立，只在 round-3 上成立。** 这是一处对卡文的偏离，
需要主 session 裁定，不由本 session 自行认定为达成 —— 详见验收单 §7.8。
