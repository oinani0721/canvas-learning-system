# 复核请求 r4 — CARD-G2-9-F1-canary（冻结态终审，绑最终 HEAD）

只读。不写。不执行任何连接数据库的命令。

## 一 前情

| 轮次 | 绑定 | 结果 | 处置 |
|---|---|---|---|
| r1 | `49db0305`（中间） | B0 / H1 / M3 / L2 | 7 条全接受整改 |
| r2 | `98d4943b`（中间） | B0 / H0 / M4 / L1 | 5 条全接受整改 |
| r3 | `77e798c2`（**当时最终 HEAD**，冻结态） | B0 / H0 / M2 / L4 | 6 条全接受整改 |
| 独立多视角审计（非 Codex） | 同上 | 45 条提出 / 15 条存活 | 6 类问题全接受整改 |

r3 之后，作者又做了一轮整改（commit `9a80f991`），本轮请复核**这一轮**。

**本轮是冻结态**：审查对象已全部 commit，运行期间作者不会改动任何文件。

## 二 本轮请重点复核的「新整改」

独立审计抓到两条三轮 Codex 都没碰到的问题，作者的整改是否到位、有没有引入新的过强表述：

1. **HIGH — 「失败告警计数 0」被判定为恒真的假判据**
   作者原先用「`Failed to initialize vectorizer` 计数 0」佐证「4 次嵌入模型预加载全部成功、`except` 分支没被走到」。
   实测：`loguru` 在本 venv **未安装** ⇒ `backend/lib/agentic_rag/clients/lancedb_client.py` 顶部 `LOGURU_ENABLED = False`；而 `_init_vectorizer` 的两个 `except` 分支都写成 `if LOGURU_ENABLED: logger.warning/error(...)` ⇒ 该字样恒不可能出现。
   作者的整改：撤回该佐证，改为「只能主张 ON 态出现 4 次 `Loading weights: 100%` 这个正例本身」，并在「本卡未证明什么」第 9 条写明「**无法从输出区分『预加载成功』与『失败但被静默吞掉』**」。
   **请核**：这个收窄是否彻底？「4 次 `Loading weights: 100%`」这个剩下的主张本身站得住吗？它能不能也被同样的理由质疑（比如这行输出来自哪里、是否也可能被静默吞掉）？验收单别处还有没有依赖那条假判据的推理？

2. **MEDIUM×3 — `xfail→XPASS` 的机制被指写反了**
   作者原先写「xfail→XPASS 的翻转不产生 FAILED/ERROR 行，对 nodeid 红集不可见」，并据此给主 session 下了通则。
   作者的整改依据：① 四态最小实验（`xfail(strict=True)`+通过 → `FAILED`；`strict=False`+通过 → `xpassed`；`xfail`+失败 → `xfailed`；无标记+通过 → `passed`）；② 仓内真实反例 `_bmad-output/审查/evidence-g29f2/g29f2-xpass-20260914T195936.txt`（6 行 `[XPASS(strict)]` 对应同跑 FAILED nodeid、0 xpassed）；③ 本卡两跑 `xpass` 命中均为 0。
   结论改为：真实原因是 F2 **删掉了标记**（基线侧 `xfailed` / 车道侧 `passed`，两侧都不进红集）；通则改为「取决于解锁方式：删标记 ⇒ 不可见；保留 strict 标记而代码修好 ⇒ 可见且表现为新增 FAILED」。
   **请核**：新结论与新通则是否正确？证据链是否完整？有没有反过来又说得太满（例如把「本仓这次」当成「所有情况」）？

3. **MEDIUM — 残留对账 v2**
   v1 的验伪锚被 r3 判为不成立（用「全库查询非空」当锚，证明不了本条查询的前缀参数被正确使用）。v2（`evidence-g29f1-canary/residue-recon-7692-v2-<较晚时间戳>.txt`）把查询正文与参数原样落盘，并改用「同一条查询、只把前缀换成库中已知存在的值」作锚。
   **请核**：v2 的锚这次成立吗？它能支撑到什么程度？验收单对它的表述有没有超出？（注意目录里还有一个**同名但更早时间戳**的 0 字节文件，那是一次失败运行的产物，已就地写入失败说明——请确认作者没有引用错。）

4. **耗时更正**：`--verify-judges` 从「约 40 分钟」改为「实测 1385 秒 ≈ 23.1 分钟」（依据文件时间戳）。**请核算法与数字。**

5. **章节补齐**：新增 §r3 小节与 §独立多视角审计小节；验收结果 (i) 行改为三轮并点明「r3 才是绑最终 HEAD 的那一轮」；台账 8 改为逐轮列首部齐备情况；r3 存档已补首部。
   **请核**：现在还有没有「指向不存在的章节」「数字与正文不符」「声称已整改但实际没改」的情况？

## 三 最小读取面

- 验收单：`_bmad-output/验收单/UAT-CARD-G2-9-F1-canary-20260915.md`
- 三轮存档：`_bmad-output/审查/codex-review-CARD-G2-9-F1-canary-r{1,2,3}.md`
- evidence 目录：`_bmad-output/审查/evidence-g29f1-canary/`，本轮尤其关注新增的
  `loguru-gate-makes-failure-log-unreachable-*.txt`、`xfail-xpass-semantics-probe-*.txt`、`residue-recon-7692-v2-*.txt`、`verify-judges-duration-correction-*.txt`、`zsh-vs-bash-globsubst-*.txt`
- 生产代码（只读）：`backend/lib/agentic_rag/clients/lancedb_client.py` 的 `_init_vectorizer` 与文件顶部的 `LOGURU_ENABLED` 守卫；`backend/scripts/g29_dual_vault_canary.py`
- 绑定：`git diff --stat 60600433 HEAD -- . ':(exclude)_bmad-output'`（作者主张为空）

## 四 也请一并确认（前三轮的结论是否仍然成立）

- 未证明 1–13、台账 1–9、实测更正 ①–⑦ 的编号连续、无重复、无互相矛盾；
- 前三轮已判 PASS 的项有没有在这一轮被改坏；
- 偏差 B-1 / B-2 的登记是否仍如实、有无自我开脱。

## 五 边界

- 只读；不连数据库；不复跑 canary。
- 不评 `_check_and_fix_dimension_mismatch` 的删表条件设计本身。
- 无法从给定读取面证实的，直接说「证据不足」。
- 按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条写清依据的文件与行。**报告开头请明确给出绑定当前 HEAD 的 BLOCKER / HIGH 计数。**
