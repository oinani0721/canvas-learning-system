# Codex 定向复核存档 — CARD-G5-4 round-5 处置（T2 车道补跑）

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-30
> **产出卡**: BATCH-2026-08-29-第六批 / CARD-收口A **③b**
> **审阅对象**: commit `07ca997c` 落在 `test_recap_scan_signals.py` 与 `recap_scan.py` 上的 delta
>
> ## 为什么有这一轮
>
> 卡文（trunk `a9c8b97c` 更新版）③b：*"round-5 处置台账称 58 条全处置但无终审确认
> （与 S3 round-20 同款缺口）——跑一轮定向 Codex（只审 round-5 处置 delta）产出非空存档。"*
>
> ⚠️ 本卡最初**按旧卡文执行、漏做了 ③b**，是收尾自审（`codex-review-CARD-收口A.md` HIGH-1）
> 点名后补跑的。教训见验收单 §一 的卡文变更说明。
>
> ## 裁决
>
> **需再一轮** · BLOCKER 0 / **HIGH 4** / MEDIUM 1 / LOW 3
>
> ⛔ **4 条 HIGH 全部落在 `recap_scan.py` 的 verifier 上**，而 verifier 是本批硬边界禁改的
> （归维护卡 B）。复核者**自己**也逐条标注了「移交维护卡 B，不要求 CARD-G5-4 本卡修改 verifier」。
> ⇒ 处置 = **确认存在 + 移交**，与 D-1/D-2 同型：**G5-4 不宣称清零、不宣称可验收**。
> 这些发现已写进维护卡 B 的完成条件（它们把该卡从「补裸数字绑定」扩展到了实证的四条缺口）。
>
> ## 最重要的一条：round-5 台账的「全处置」不实
>
> 台账 `codex-review-CARD-G5-4-round5-处置.md` 声称的处置里，本轮实测至少三处与事实不符：
> - `four-fence-short-close` — 台账称「现在 FAIL」，实测 **exit 0（仍被放行）**；
> - `blockquote-indented-code` — 台账称「现在 FAIL」，实测 **exit 0（仍被放行）**；
> - `口径一致` — 台账称「现在 PASS」，实测 **exit 1（误伤仍在）**。
>
> 这正是 ③b 存在的理由：**没有终审确认的「全处置」台账不可信**。

---

# CARD-G5-4 round-5 定向复核报告

## 结论

**需再一轮。**

发现 **4 类 HIGH**：两个台账点名的 M3 绕过仍可 `VERIFY PASS`，H3/H4 的“白名单化”不完整，并有 4 个 mutation survivor 可让完整 105 项套件继续全绿。依照范围约束，所有 verifier 相关问题均标记为 **「移交维护卡 B」**，不要求 CARD-G5-4 本卡修改 verifier。

目标两文件当前字节与 `07ca997c` 完全一致；未审 `recap_exam_build.py`。

## 1. 结构性转向核验

| 项目 | 结论 | 证据 |
|---|---|---|
| H2 无据行 | **PASS** | 五个原因常量位于 [recap_scan.py:861](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:861)，整行首尾锚定且原因只能来自该集合，见 [recap_scan.py:1027](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1027)。这是正向允许集。 |
| H3 尾部 | **PARTIAL** | 任意 `/` 确实被拦；但尾部仍先开放为 `[^【】]*`，再排除数值或 `/`，见 [recap_scan.py:1063](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1063)、[1080](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1080)，本质仍是黑名单。 |
| H4 全局派生行 | **FAIL** | 全局 default-deny 存在，但规模行允许式缺 `$`，`p.match()` 只认合法前缀，见 [recap_scan.py:1340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1340)、[1360](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1360)，不是真正整行匹配。round-6 后实际也已扩为 7 类、8 个正则，并非原称五种。 |
| M3 代码块 | **PARTIAL** | 已先剥引用前缀且不再普遍删除缩进块，见 [recap_scan.py:938](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:938)；但围栏长度和引用内缩进代码仍处理错误。 |

## 2. 发现

### HIGH-1 — 两个 M3 点名反例仍被放行（移交维护卡 B）

- `four-fence-short-close`：四反引号开栏、三反引号短闭合后放入四条信号，`--verify` **exit 0**；Markdown 解析确认信号仍在 `<pre><code>` 内。原因是实现只保存 `bare[:3]` 并接受短闭合，[recap_scan.py:957](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:957)。
- `blockquote-indented-code`：把信号写成 `>     来源覆盖率：…`，`--verify` **exit 0**；Markdown 解析为引用内代码块。负前瞻只拒绝第 0 列四空格，而前缀仍接受 `>` 加五空格，[recap_scan.py:1067](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1067)。

二者均属于 verifier 放过不作为报告陈述的隐藏信号，符合 HIGH。

### HIGH-2 — H4“整行白名单”可由合法前缀穿透（移交维护卡 B）

在正确规模行后追加：

```text
，SeedA 的派生子女共有仨个
```

实测仍为 **exit 0 / VERIFY PASS**。另将 scan 中 `SeedA.tips_count=2` 的 ledger 改成：

```text
- SeedA — 批注 999 条
```

同样 **exit 0**；种子行正则只检查形状，不绑定节点及数字，[recap_scan.py:1322](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1322)。

### HIGH-3 — H3 仍可追加无斜线伪计数（移交维护卡 B）

在正确来源覆盖率行尾追加 `另有仨条`，实测 **exit 0**。`仨` 不在 `_has_numeric` 覆盖面，且没有 `/`，所以开放尾部继续放行无据计数。这直接否定“整体已转为只许什么”。

### HIGH-4 — 4 个完整套件 survivor（移交维护卡 B）

强破坏测试是承重的：无据白名单 `5 failed`、删除 `/` 检查 `3 failed`、关闭派生全局门 `2 failed`、关闭引用剥离 `1 failed`、恢复旧缩进吞噬 `1 failed`。

但以下部分退化后，完整 `test_recap_scan_signals.py` 仍是 **105 passed**：

| Survivor mutation | 原实现/变体行为 |
|---|---|
| `_NODATA_REASONS` 增第六项“任意原因” | 原版拒绝、mutant 放行 |
| 任意 `/` 退化为只拦 CJK/CJK | 尾部 `X/N` 被 mutant 放行 |
| 任意层引用退化为只剥一层 | `> > ```…` 被 mutant 放行 |
| H4 增加自由“备注：…派生…”允许式 | 伪派生断言被 mutant 放行 |

按题设“失效判定让完整套件仍全绿”口径，定为 HIGH。

### MEDIUM — `口径一致` 误伤仍在

```text
> - 来源覆盖率：2/3 成员含来源锚点口径一致【文件】
```

实测 **exit 1**，因为 `_has_numeric` 将“一”无上下文地判作数值，[recap_scan.py:852](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:852)。与台账“现在 PASS”不一致，但不是模板逐字合法行，故不升 HIGH。

## 3. 16 例复跑

| 反例 | 台账 | 实测 |
|---|---:|---:|
| H2 `共有仨条` | FAIL | exit 1 |
| H2 `共有皕条` | FAIL | exit 1 |
| H2 `共有零条` | FAIL | exit 1 |
| H2 `统计口径尚未一致` | PASS | 作为无据原因 exit 1；作为普通散文 exit 0 |
| H2 `说明十分清楚` | PASS | 作为无据原因 exit 1；作为普通散文 exit 0 |
| H3 `仨/仨` | FAIL | exit 1 |
| H3 `皕/皕` | FAIL | exit 1 |
| H3 `零/零` | FAIL | exit 1 |
| H3 `口径一致` | PASS | **exit 1** |
| H4 inline assertion | FAIL | **exit 0** |
| H4 elsewhere assertion | FAIL | **exit 0** |
| H4 fake ledger count | FAIL | **exit 0** |
| M3 four-fence-short-close | FAIL | **exit 0** |
| M3 blockquote-fence | FAIL | exit 1 |
| M3 blockquote-indented-code | FAIL | **exit 0** |
| M3 legitimate-nested-list | PASS | exit 0 |

H2 两句存在台账自相矛盾：若它们是无据原因，五常量白名单要求其必须 FAIL；若只是普通散文，则 PASS，但不再是 H2 无据行案例。原始 16 份 Markdown exact bytes 未存入工作树，因此无法消除该歧义。

## 4. “58 条”核算

算术成立：

```text
6 + 5 + 9 + 19 + 2 + 12 + 5 = 58
```

但 **58 不是可证明去重后的 58 个独立原子发现**：

- round-1 表实际含 `F5a/F5b` 及 `L1/L2`，累计却压成 `F1-F6=6`；
- round-5 把 16 个反例压成 5 类，H2/H3 合并绕过与误伤，M3 又拆分，粒度不一致；
- H2/H3/H4/M3 等根因跨轮反复出现，没有跨轮唯一 ID 去重表；
- 标题写“三轮 workflow”，表内只列 r1/r2；workflow r3 的 22 条在 round-6 才加入，届时累计为 **80**。

因此“58 个按轮次统计的分类桶”属实；“58 条独立发现且全部处置到位”不属实。记 **LOW**。

## 5. 判据复跑

| 判据 | 台账 | 当前实测 |
|---|---:|---:|
| `test_recap_scan_signals.py` | 98 | **105 passed** |
| 合并套件 | 224 | **258 passed, 187 warnings** |
| ROUTING | 66/66 | **66/66** |
| ruff | clean | 两个审阅目标 **All checks passed** |

当前合并构成为 `105 + 64 + 55 + 34 = 258`。相对历史 224：

- G5-4：98 → 105，round-6 增加 7；
- G5-9：28 → 55，CARD-收口A 增加 27；
- board-manifest 64、split-preview 34 不变。

因此 98/224 是中间工作态数字，不是 `07ca997c` 最终目标测试 blob 可独立复现的数字；该 commit 的目标测试 blob与当前相同，当前收集数为105。记 **LOW**。原台账未保存完整 ruff 命令，本轮只确认严格审阅范围内两个 Python 文件。

## 只读与限制

- 所有构造及 mutation 仅位于 `/tmp/card-g5-4-*`。
- 两个目标文件工作树 diff 为零，且与 `07ca997c` blob 相同。
- 未审阅或提出 `recap_exam_build.py` 改动。
- 初始工作树为 clean；审阅期间一份范围外 G5-9 处置文档出现并发修改，未由本轮产生、未回滚，目标文件不受影响。

## 残留清单

- **BLOCKER：0**
- **HIGH：4**
- **MEDIUM：1**
- **LOW：3**

按停轮口径，**HIGH > 0，必须再开一轮；verifier 项统一移交维护卡 B。**
