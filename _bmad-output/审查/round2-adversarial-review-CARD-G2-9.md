# CARD-G2-9 round-2 独立多维对抗复核

> 触发原因：round-1 的 Codex 复核只有 1 轮，而按其 5 条发现所做的**整改本身**
> 未经任何独立复核（协议 §四 的失绑登记项）。本轮补这个缺口。
> 规模：5 个审查维度 × 独立反驳验证；agent 25 个，
> 提出 17 条，**确认 7 条**
> （其余被反驳者驳回——反驳阶段的作用就是滤掉看似合理但站不住的发现）。

> ⚠️ 3 个验证 agent 因 API 安全过滤未完成（非发现本身的问题），
> 对应的 3 条发现按**未验证**处理，未计入确认清单。

## 确认的发现（逐条已整改，处置见验收单 §五）

### 1. [HIGH] graphiti_delete_is_load_bearing 只数「删前找到几个节点」，不证明删除生效 —— HIGH-1 被移位而非修复（实跑证伪）

**位置**：`backend/scripts/g29_dual_vault_canary.py` 1022（判据）/ 642-647（计数器）/ 835-837（_purge 顺序）/ 555（无 label 的 DETACH DELETE）

**据以判断的事实**：GraphitiFacet.delete: `for node in await cls.get_by_group_ids(self._d, [gid]): await node.delete(self._d); deleted += 1` —— 计数来自 **get_by_group_ids 的返回条数**，只要节点存在就 +1，与 node.delete 是否真的删掉无关。判据 :1022 `verdicts["graphiti_delete_is_load_bearing"] = deleted_a["graphiti"] > 0` 因此等价于「删 A 之前 graphiti 里有节点」——而这在 A_counts_positive 已经成立了。**删后不存在性检查也不承重**：_purge :837 紧接着跑 Neo4jFacet.delete 的 `MATCH (n) WHERE n.group_id = $g DETACH DELETE n`（:555，无 label 限制），而报告 identities 实测 graphiti_group_id 与 neo4j_physical_group_id 逐字相同（均 `vault__g29canary_a`），所以 `A_after_delete` 的 graphiti 归零是**这一刀**干的，不是 GraphitiFacet.delete 干的。Codex HIGH-1 的处置要求是三件事「删前存在 + 实际删除 + 删后隔离」，本次整改只落了第一件。对照作者自己在 UAT §四 记的规矩「变异要拆的是防线，不是判据本身」——这里判据被换成了另一个更容易满足的量。

**失败场景**：把 GraphitiFacet.delete 里的 `await node.delete(self._d)` 整行删掉、只保留 `deleted += 1`（即 graphiti 删除**完全不工作**），其余代码不动。2026-09-06 于 7692 + tmp LanceDB 实跑（探针 scratchpad/g29probe/probe_graphiti_noop_delete.py，monkeypatch 该方法）：**rc=0，13/13 判据全 PASS**，其中 `graphiti_delete_is_load_bearing: PASS`、`A_gone_after_delete: PASS`，报告里照样打印「删 A 时各面实删条数: {'graphiti': 2, 'lancedb': 1}」——正是 UAT §二:110 当作「Codex HIGH-1 闭合证据」引用的那个数字。且该次 normalized 报告与已提交基线 canary-normalized-20260905T184253Z.json **逐字相同**（唯一差异是我关掉的 side_effect_probe 段），所以即便有人把这条写成变异，verify_judges 的 applied 自检（:1089 `normalize(report) != baseline_norm or err is not None`）也会把它判成 NOT_APPLIED（「变异没打进去」），而不是 SURVIVED（「判据不承重」）——归因还会指错方向。

**反驳者的核对结论**：CONFIRMED by direct code reading; I could not refute it.

(1) g29_dual_vault_canary.py:642-647 — `deleted += 1` fires once per node returned by `get_by_group_ids`, after `await node.delete(...)`. A silently no-op delete (one whose Cypher matches nothing) still returns 2; only a *raising* delete would be caught. The counter measures "nodes present", not "nodes removed".

(2) :1022 `verdicts["graphiti_delete_is_load_bearing"] = deleted_a["graphiti"] > 0` is therefore entailed by A_counts_positive (:995 requires graphiti episodic/entity > 0), since nothing deletes A between phases["A_written"] (:964) and the purge at :984.

(3) The confound survives the reorder: _purge :834-837 runs graphiti.delete → lancedb.delete → neo4j.delete with NO count taken between them, and Neo4jFacet.delete:555 is `MATCH (n) WHERE n.group_id = $g DETACH DELETE n` with no label restriction. The committed evidence (evidence-g29/canary-report-20260905T184253Z.json identities) shows graphiti_group_id == neo4j_physical_group_id ("vault__g29canary_a"). The author's own docstring at :823-829 records the measurement that this one statement zeroes episodic/entity. So A_gone_after_delete (:1015) is satisfiable by the neo4j cut alone — exactly the situation Codex flagged, now one step later in the sequence rather than eliminated.

(4) No mutation closes the gap. M9_no_delete mutates the judged quantity itself (early `return 0` at :640-641 / :719-720 and `return` at :553-554), so it cannot separate "delete worked" from "delete found nodes"; no other mutation in MUTATION_SPECS (:189-261) touches graphiti deletion.

(5) Measured against Codex's actual remediation text in _bmad-output/审查/codex-review-CARD-G2-9.md HIGH-1 ("为 Graphiti 删除建立独立的删前存在、实际删除及删后隔离证据"), the fix supplies only the first of three; the second and third remain confounded. UAT-CARD-G2-9-2026-09-05.md:110 and :233 nevertheless cite `{'graphiti': 2, 'lancedb': 1}` as "Codex HIGH-1 的闭合证据".

(6) Not previously disclosed: the UAT "本卡未证明什么" list (9 items) does not contain this; item 9 concerns A_unaffected_by_B_write's blindness to idempotent MERGE, a different judge.

(7) The claim's secondary point also checks out: verify_judges :1087 computes `applied = normalize(report) != baseline_norm or err is not None`. Removing `await node.delete(...)` produces a byte-identical normalized report, so such a mutation would be scored NOT_APPLIED rather than SURVIVED — the applied self-check reads the same channel as the kill judgment, so a genuinely-applied-but-unobservable mutation is indistinguishable from an un-injected one, and the misattribution the claimant describes is real.

Caveat on wording, not substance: "被移位而非修复" is slightly generous to the claimant — the reorder does change which code actually performs the graphiti deletion on the normal path, so the mechanism is arguably fixed. What is not fixed is the proof: the verdict named `graphiti_delete_is_load_bearing` does not bind the property its name asserts, and a HIGH finding is declared closed on it.

Severity: keeping HIGH. The card's entire deliverable is proof, and this is the same class the author themselves rated HIGH-worthy (UAT:229, "报告声称验证过的事其实没验证"). No production impact and the canary's isolation conclusions are unaffected — deletion efficacy is not an isolation property — which is the only argument for MEDIUM.

---

### 2. [HIGH] M9 是唯一点名 graphiti_delete_is_load_bearing 的变异，它把计数器硬编码成 0 —— 打的是判据的输入，不是被测防线

**位置**：`backend/scripts/g29_dual_vault_canary.py` 238-242（M9 spec）/ 640-641、719-720、553-554（三处 `if _MUTATION == "M9_no_delete": return 0/return`）

**据以判断的事实**：MUTATION_SPECS 中只有 M9_no_delete 的 expect_red 含 `graphiti_delete_is_load_bearing`；而 M9 在 GraphitiFacet.delete 的**第一行**就 `return 0`（:640-641），既没执行 get_by_group_ids 也没执行 delete。这条变异证明的只是「返回值 0 会让 >0 判据翻红」——一个恒真的算术事实。同时 M9 把 Neo4j(:553-554) 与 LanceDB(:719-720) 的删除**一起**关掉，所以它也无法分辨 A_gone_after_delete 的 graphiti 部分到底是谁清的。全表 11 条变异里没有任何一条只坏 graphiti 删除、保留 neo4j 删除——而那正是唯一能暴露上一条缺陷的形状。

**失败场景**：未来 graphiti_core 升级后 EpisodicNode.delete 语义变化（例如只删边不删节点、或按 uuid 匹配不到而静默 no-op）：M9 依旧 KILLED（因为它根本不走那段代码），canary 依旧 13/13 PASS，而「三存储各自的删除都被验证过」这句结论已经不成立。这与 round-1 MEDIUM-2 要修的是同一个病（变异点名了判据但没承重），只是从「没点名」变成了「点名了但打空」。

**反驳者的核对结论**：CONFIRMED, not refuted — and corroborated by the author's own in-flight fix.

Against the delivered artifact (HEAD aa26ff9c): `git show HEAD:backend/scripts/g29_dual_vault_canary.py | grep -c 'M12_graphiti_delete_only_broken'` returns 0. In HEAD, MUTATION_SPECS names `graphiti_delete_is_load_bearing` only in M9_no_delete (:238-242), and `GraphitiFacet.delete` short-circuits with `return 0` as its first statement (:640-641), before `get_by_group_ids` and `node.delete`. M9 simultaneously disables the Neo4j delete (:553-554) and LanceDB delete (:719-720). No mutation in HEAD breaks graphiti's delete alone.

The verdict is `verdicts['graphiti_delete_is_load_bearing'] = deleted_a['graphiti'] > 0` (:1022), whose input is a counter incremented once per node RETURNED by get_by_group_ids (not per verified removal), computed inside the very function M9 mutates. M9 therefore proves only the arithmetic "0 is not > 0".

The failure scenario is concrete: if EpisodicNode.delete became a silent no-op, the counter would still reach 2 (verdict green), and A_gone_after_delete would still be green because `_purge` runs the unlabeled `MATCH (n) WHERE n.group_id = $g DETACH DELETE n` LAST and the graphiti gid is byte-identical to the physical gid (stated in the _purge docstring and demonstrated by the author's own HIGH-1 probe). The canary would report 13/13 PASS with graphiti's delete broken.

Not disclosed: the UAT sheet's "本卡未证明什么" (12 items) covers the sentinel and A_unaffected blind spots but not this one; §四 asserts "判据覆盖：13/13" and "M9 … KILLED" unqualified.

Decisive corroboration: the working-tree copy (mtime 2026-09-06 03:02, uncommitted, +210/-20 vs HEAD) already contains exactly the fix this claim implies — a new `M12_graphiti_delete_only_broken` spec ("只坏 graphiti 删除，业务扫荡照跑 —— 专打「修复是否只是移位」"), the counter moved outside the skip flag with the comment "上一版在这里 return 0，那是在改判据读到的数字——门当然会红，但红得毫无信息量", and a new `residual()` whose docstring reads "这个方法是 HIGH-1 真正的修复点（第一版只是把问题挪了个位置）… 2026-09-06 实测复现：让 graphiti 删除只遍历不真删，计数器仍得 2、业务扫荡之后 graphiti 面仍是 0，两条判据双双被喂饱". That is the claimed failure scenario, reproduced and acknowledged by the author.

Minor imprecision in the claim (a graphiti-only mutation implemented as `return 0` would have been equally tautological; the real fix required both M12 and the in-situ residual evidence) does not invalidate it — it identifies the right defect and the right shape of the missing mutation.

Severity raised from MEDIUM to HIGH: it means round-1's HIGH-1 remediation was cosmetic (problem relocated, not closed) while the UAT reports it closed with "{'graphiti': 2}" as "闭合证据" — the same class and severity Codex assigned the original. Not blocker-level: test-only script, no production code, no data-loss or live-port face. Caveat: the evidence set (evidence-g29/*, 02:41-02:52) and the UAT sheet still document the pre-M12 11-mutation state, so the delivered package retains the defect even while the tree is being fixed.

---

### 3. [MEDIUM] (c) 验伪 harness 的 C3 是被 LOW-4 新增的前提断言杀死的，不是被它声称保护的交叉排除断言杀死的

**位置**：`_bmad-output/审查/evidence-g29/g29_fsrs_test_mutations.py` 51-58（C3 规格：expect_assert="A 的 json 里没有 A 自己的节点"）

**据以判断的事实**：C3 把 `texts_a = _projection_texts(vault_a, backups)` 换成 `_projection_texts(vault_b, backups)`（harness :52-54），期望的断言消息写的是 `"A 的 json 里没有 A 自己的节点"`（:57）。该消息出自测试文件 backend/tests/regression/test_g29_dual_vault_fsrs_isolation.py:126 的 **LOW-4 新增前提断言** `assert A_NODE in texts_a["outputs/今日复习.json"]`，它排在交叉排除循环 `for rel, text in texts_a.items(): assert foreign not in text`（:134-136）**之前**。C3 变异下前提断言先失败，交叉排除循环一次都不执行。

**失败场景**：把测试 :134-136 的整个 A 侧交叉排除循环删掉，重跑 harness：C1/C2/C4 结果不变，C3 仍报 KILLED（同一 nodeid、同一断言消息），harness rc=0。也就是说 MEDIUM-3 号称「判据绑定被哪一层拒的」之后，C3 绑定的是前提层而不是隔离层；A 侧 json/md 的交叉排除断言至今没有任何变异证明过它承重（只有 C1 经 state 文件行使了一次交叉排除断言）。

**反驳者的核对结论**：CONFIRMED by direct execution, not inference.

Facts checked:
- g29_fsrs_test_mutations.py:52-57 — C3 swaps `texts_a = _projection_texts(vault_a, backups)` -> `(vault_b, ...)` and declares expect_assert = "A 的 json 里没有 A 自己的节点".
- That exact message lives at test_g29_dual_vault_fsrs_isolation.py:126, which is the LOW-4-added precondition (its own comment :124-125 attributes it to "LOW-4 的另一半"). The A-side cross-exclusion loop is at :134-136, i.e. AFTER it.

Reproduction (probe copy in tests/regression, deleted afterwards; target file sha still 276ae19243fc… = evidence baseline, untouched):
1. C3 alone -> `tests/regression/test_zzzprobe_c3.py:126: AssertionError: A 的 json 里没有 A 自己的节点` (assert '甲A节点' in '{... "vault_id": "vaultB" ...}'). The :134-136 loop never executes.
2. Deleting the entire A-side loop (:134-136) and keeping C3 -> same nodeid, same assertion message, rc=1, so the harness judge (:95 `rc != 0 and node_ok and msg_ok`) still prints KILLED.
3. With the A-side loop deleted and no mutation -> `2 passed`; with C1 applied -> killed by the B-side loop ("B 的 state 里出现了 A 的独有标识 'A专属板'"), matching C1's expect_assert. So C1/C2/C4 verdicts and harness rc=0 are unchanged. The claim's failure scenario is exact.

Why it is a genuine finding, not a restatement of a disclosed limitation:
- The harness itself prints at :118 (and the UAT sheet reproduces it at UAT-CARD-G2-9-2026-09-05.md:200 plus the C4 row) that "C4 是反向锚…用来证明前三条的红不是被前提喂饱的". That statement is falsified for C3. C4 only removes the md precondition (:127) on the clean tree and cannot speak to which assertion fires under C3; it does not touch :126 (json) or :133 (state).
- "本卡未证明什么" items 1-9 do not mention this; item 5 covers only the same-process limitation.
- This is a partial regression of the MEDIUM-3 remediation itself: the judge is now bound to an exact assertion, but the layer it binds to is the LOW-4 precondition layer, not the isolation layer C3 purports to exercise. One remediation (LOW-4) shadowed the assertion another remediation (MEDIUM-3) was meant to pin. Matches the project's own recorded rule "判据必须绑定被哪一层拒的 / 被更早防线喂饱".

Severity kept at MEDIUM, not higher. Real mitigations: the test still goes red under C3 (the defect IS detected, just by a different assertion); the A-side loop is not vacuous (the new preconditions guarantee non-empty, own-content texts); and its symmetric B-side twin IS proven load-bearing by C1. So the residual is an overstated verification claim baked into the shipped evidence file and the UAT table, not a missed production defect — the same class Codex itself rated MEDIUM as MEDIUM-3.

---

### 4. [MEDIUM] M8 covers read_scope_sentinels_clean by mutating the judge's own argument, not the system — the divergence it exists to detect is still untested

**位置**：`backend/scripts/g29_dual_vault_canary.py` 636 (mutation site), 233-237 (MUTATION_SPECS["M8_sentinel_scope_divergence"])

**据以判断的事实**：L633-637: `eps = await EpisodicNode.get_by_group_ids(self._d, [scope_gid])` … `sentinel_scope = "vault__g29_divergent_scope" if _MUTATION == "M8_sentinel_scope_divergence" else scope_gid` / `outside = sum(1 for node in (*eps, *ens) if not group_in_read_scope(node.group_id, sentinel_scope))`. The mutation substitutes a constant into the *second argument of the judge's own expression*; the graphiti read call (`get_by_group_ids`) and `app.core.vault_scope.group_in_read_scope` are both left untouched. Nothing on the production side is broken. This is the same shape the author explicitly rejected for C3 in UAT §四 ("变异要拆的是防线，不是判据本身") and the shape just removed from GraphitiFacet.delete (L659-663: "上一版在这里 `return 0`，那是在改判据读到的数字——门当然会红，但红得毫无信息量"). It also reduces to what `evidence-g29/sentinel-self-audit-*.txt` step 3 already printed ("把 scope 换成无关值 vault__unrelated_scope → outside_read_scope = 1"), i.e. proof the judge is not dead code, which was never in dispute. UAT 「本卡未证明什么」#10 states "它只在'两套读口径分叉'时才非 0（M8 即造这个情形）" — M8 does not create that情形.

**失败场景**：The sentinel's stated detection target is graphiti's read口径 drifting away from production's (`cypher-read-contract` R4 prefix semantics). Concretely: a graphiti_core upgrade changes `get_by_group_ids` from `WHERE e.group_id IN $group_ids` to a parent/prefix match, so A's scope query starts returning nodes from a *sibling* group. `outside_read_scope` should go non-zero and `read_scope_sentinels_clean` should go red. No mutation in MUTATION_SPECS makes `get_by_group_ids` return an out-of-scope node, so this path is unexercised — if the judge were miswired (e.g. `outside` computed over `eps` only, or `_match`-filtered nodes only) M8 would still report KILLED, because M8 makes *every* returned node fail the comparison regardless of how the set was built. Coverage for this verdict is therefore nominal: `audit_judge_coverage` (L1113-1136) counts it as covered because the name appears in an `expect_red`, and it counts names only.

**反驳者的核对结论**：CONFIRMED — I could not refute it. Every cited line holds.

1. g29_dual_vault_canary.py:633-634 fetches `eps`/`ens` via `get_by_group_ids(self._d, [scope_gid])` with scope_gid UNMUTATED under M8. L636 substitutes `sentinel_scope = "vault__g29_divergent_scope"` only into the second argument of `group_in_read_scope` at L637. `app.core.vault_scope.group_in_read_scope` (vault_scope.py:651-681) is untouched. Since every returned node has group_id == scope_gid, the bogus scope makes 100% of nodes fail the predicate irrespective of how the set `(*eps, *ens)` was constructed — so M8 cannot distinguish a correctly-wired sentinel from one that examined only `eps`, or only `_match`-filtered nodes.

2. The author states the governing rule twice in the same deliverable and M8 violates it: L659-663 ("计数照实增…上一版在这里 return 0，那是在改判据读到的数字——门当然会红，但红得毫无信息量") and UAT-CARD-G2-9 L206-208 for C3 ("变异要拆的是防线，不是判据本身"). M8 is exactly the rejected shape applied to the other operand.

3. M8 is operationally identical to evidence-g29/g29_sentinel_self_audit.py:74-78 (`bogus = "vault__unrelated_scope"`; `outside_bogus = 1`), whose own printed label is "说明判据会算，只是走不到" — proof the judge is not dead code, which was never in dispute. The evidence header was merely edited to "round-2：现已由 M8 覆盖".

4. I enumerated all 12 entries of MUTATION_SPECS (M1-M12, L189-297). None causes `get_by_group_ids` to return an out-of-scope node. M1 (byte-identical identities) still yields nodes with group_id == scope_gid → sentinel stays 0; M2/M3/M10 are Neo4j-business-side; M5/M6/M7 are LanceDB. So the drift class the method's own docstring names at L614-620 ("graphiti 若哪天返回跨组数据也看不出来") is unexercised.

5. audit_judge_coverage (L1111-1136) builds `named` purely from `spec.get("expect_red", ())` and does set-difference on names, so read_scope_sentinels_clean is counted covered by name alone — the "13/13" in UAT L190 is nominal for this verdict.

6. A faithful system-side mutation was available without touching production code (the card's zero-prod-diff constraint does not excuse it): widen the list passed to get_by_group_ids inside the canary to `[scope_gid, other_gid]` (both vault constants are module-level, used at L~700 in LanceDBFacet.write). That reproduces the prefix/parent-match drift and would only be killed if `outside` spans the full returned set.

7. Not a restatement of a disclosure: UAT 「本卡未证明什么」#10 (L321-323) asserts the opposite — "(M8 即造这个情形)" — and the MEDIUM-2 remediation row (L234) claims "其中 M8 专打 sentinel". The finding contradicts an affirmative closure claim. #10's disclosed gap is the 漏返 direction; this is the 越界 direction.

Where the claim is slightly overstated (why MEDIUM, not HIGH): M8 does satisfy MEDIUM-2's literal wording ("outside_read_scope 未被证明能翻红") and is observationally equivalent to one of the two drift directions (production scope resolution narrowing). The sentinel as written today is in fact correctly wired — `outside` spans `(*eps, *ens)` unfiltered — so the defect is that detection capability is unproven, not broken. Impact is confined to verification strength for one verdict the UAT itself classes as a 口径分叉检测器 rather than an isolation judge; no isolation conclusion is falsified and there is no product risk. That is the same class the author escalated HIGH-1 for ("报告声称验证过的事其实没验证"), scaled down for the non-load-bearing target — MEDIUM.

---

### 5. [MEDIUM] Round-2 evidence in evidence-g29/ is no longer bound to the shipped canary: the recorded binding sha does not match the tree, and the UAT's 11-mutation/13-verdict tables contradict the 12-mutation/14-verdict code

**位置**：`_bmad-output/审查/evidence-g29/env-and-binding-20260906T024013.txt` line 9 (`2d5499501a856dfa3c46f76e6ff580227d77616e79d10e21ef3ce5a9ce43ad79  backend/scripts/g29_dual_vault_canary.py`)

**据以判断的事实**：That file declares "本目录全部 round-2 证据绑定这两个值". Measured now: `shasum -a 256 backend/scripts/g29_dual_vault_canary.py` = `446aa01a91b90cc8287ea043a7fe41511fc296f0392e6250ae5459051a65cedf` (file mtime 2026-09-06 03:03:17; every evidence artifact is 02:40–02:52). `canary-verify-judges-20260905T184446Z.json` lists 11 mutations and 13 `baseline_verdicts`; the current script defines 12 entries in MUTATION_SPECS (M12 added at :250) and produces 14 verdicts (`lancedb_delete_is_load_bearing` added at :1086) — confirmed by running the current script: rc=0, 14 PASS lines, `删 A 时的删除取证: {'graphiti_deleted': 2, 'graphiti_residual_before_sweep': 0, 'lancedb_drop_attempted': 1, 'lancedb_residual': 0}`. UAT §一 row 6 ("11 变异 … 覆盖 13/13") and §四's mutation table describe the superseded file; §四 also still says "脚本自带覆盖自检" for a coverage gate whose docstring (:1116-1118) states it did not exist when that sentence was written.

**失败场景**：A reviewer or the merge gate reads §一/§四 and the evidence-g29 artifacts as proof for the code being merged. Judges 3 (two-run report equivalence), 4 (7 negative controls), 6 (verify-judges) and the `ruff/pyright 0 errors` line were all produced against `2d549950…`; the `_purge` return shape, the two `residual()` methods, M12 and the coverage gate are all untested by any archived evidence. The two archived `canary-normalized-*.json` files can no longer be reproduced by the shipped script at all — its report now contains `deleted_when_purging_A` with four keys instead of two — so the "跑两次 diff 为空" judge would have to be re-run to mean anything.

**反驳者的核对结论**：Claim confirmed on every element, all independently verified in the tree.

1) Binding sha: `_bmad-output/审查/evidence-g29/env-and-binding-20260906T024013.txt:12` records `2d5499501a856dfa…` under "本目录全部 round-2 证据绑定这两个值". Measured `shasum -a 256 backend/scripts/g29_dual_vault_canary.py` = `446aa01a91b90cc8287ea043a7fe41511fc296f0392e6250ae5459051a65cedf`, mtime 2026-09-06 03:03:17; newest evidence artifact is 02:52. `grep -rl 446aa01a…` over the repo returns nothing — no artifact binds the shipped file. (HEAD aa26ff9c holds yet a third version, `2827fe0a…`, the one Codex audited. The test file does still match at `276ae192…`.)

2) Content divergence, three ways:
- `canary-verify-judges-20260905T184446Z.json` (02:51) has `len(mutations)==11` and `len(baseline_verdicts)==13`. Shipped `MUTATION_SPECS` (g29_dual_vault_canary.py:188) has 12 entries — `M12_graphiti_delete_only_broken` at :246 — and the script assigns 14 distinct verdicts (14 unique `verdicts["…"] =` sites), the new one `lancedb_delete_is_load_bearing` at :1086.
- `canary-normalized-20260905T184210Z.json` records `phases/deleted_when_purging_A = {"graphiti":2,"lancedb":1}` (2 keys); shipped `_purge` returns 4 keys (:897-901). The archived normalized pair is therefore unreproducible by the shipped script, so judge 3 ("跑两次 diff 为空") is unverifiable against it.
- M12 and `audit_judge_coverage` (:1112) are precisely the two artifacts load-bearing for the HIGH-1 ("修复是否只是移位") and MEDIUM-2 (coverage) remediation claims, and both have zero archived evidence.

3) UAT contradicts the shipped code and falsifies itself: UAT-CARD-G2-9-2026-09-05.md:74 ("11 变异 … 覆盖 13/13"), :190 and :234 ("脚本自带覆盖自检"), :336 ("13 条判据 + 15 条验伪变异" — a third inconsistent number). The shipped `audit_judge_coverage` docstring (:1114-1118) states outright that 「验收单写着"脚本自带覆盖自检"，而脚本里根本没有这段代码——13/13 是我在 shell 里手算的」, i.e. the code convicts the UAT sentence of having been false when written.

4) Not previously disclosed: §七 失绑登记 (:262-277) discloses only the earlier unbinding (2827fe0a → 2d549950) and closes by asserting env-and-binding-*.txt is the binding anchor; the later 2d549950 → 446aa01a drift is undisclosed and falsifies that closing assertion. 「本卡未证明什么」 (:299-328) does not cover it.

Severity held at MEDIUM rather than raised: the card ships no production code changes and the repair is cheap (re-run judges on the shipped file, correct the three tables), so it stays below the blocking classes (data loss / live-vault or 7691 write / security / named-judge red / negative-control false-green) — registrable, not merge-blocking. Note the finding stands even setting the sha argument aside: the "脚本自带覆盖自检" and 11/13 vs 12/14 statements are wrong on their own terms, per the shipped code's own docstring.

---

### 6. [MEDIUM] UAT 两处宣称「脚本自带覆盖自检」，脚本里不存在任何覆盖自检代码

**位置**：`_bmad-output/验收单/UAT-CARD-G2-9-2026-09-05.md` 190 与 234（对应 backend/scripts/g29_dual_vault_canary.py:1071-1112 verify_judges 全体）

**据以判断的事实**：UAT:190「**判据覆盖：13/13**（脚本自带覆盖自检；round-1 只有 4/12…）」、UAT:234 MEDIUM-2 整改栏「判据覆盖 **13/13**…；脚本自带覆盖自检」。实读 `verify_judges`（:1047-1112）：只逐条跑 MUTATION_SPECS、按 `expect_red` 判 KILLED/SURVIVED/NOT_APPLIED，`all_killed = not survived`。全文 grep `覆盖|coverage|13/13` 在脚本内**零命中**（只有 R1「全覆盖」与 audit hook「覆盖」两处无关文案）。产出的 `canary-verify-judges-20260905T184446Z.json` 里也没有任何 coverage 字段——只有 baseline_verdicts(13) 与 mutations(11)。13/13 是人工数出来的。

**失败场景**：后人给 run_canary 加第 14 条判据（例如 `verdicts["lancedb_delete_is_load_bearing"]`）而不加对应变异：`verify_judges` 里没有任何一步把 `set(union(expect_red))` 与 `set(report["verdicts"])` 对账，于是 `--verify-judges` 照旧打印 11/11 KILLED、`all_killed: true`、rc=0，验收单可以继续照抄「判据覆盖 N/N（脚本自带覆盖自检）」。MEDIUM-2 被修的是这一版的数字，不是「数字会自己失效」这个机制——而 UAT 把它写成了后者。

**反驳者的核对结论**：CONFIRMED, not refutable.

(1) Code: `git show HEAD:backend/scripts/g29_dual_vault_canary.py | grep -n "覆盖自检|audit_judge_coverage|coverage"` returns nothing (rc=1). `verify_judges` (HEAD) returns only `{baseline_verdicts, mutations, all_killed}`; the sole cross-check is `missing = [k for k in targets if k not in verdicts]`, which validates the mutation→verdict-name direction (phantom targets), never verdict→named-by-some-mutation. So no coverage self-check existed.

(2) Evidence: `_bmad-output/审查/evidence-g29/canary-verify-judges-20260905T184446Z.json` has keys ['all_killed','baseline_verdicts','mutations','timestamp'] — no coverage field. I recomputed the union of `target_judges` across the 11 mutations myself: 13 verdicts, uncovered=[] — 13/13 is factually true but is a hand-computed number, exactly as the claim states.

(3) UAT: `grep -n 覆盖自检` on the UAT hits :190 and :234, both asserting 脚本自带覆盖自检. Neither line exists in `git show HEAD:...UAT-CARD-G2-9-2026-09-05.md` — they were written after the commit, without the code.

(4) Not a disclosed limitation: the 本卡未证明什么 section (items 1-12) says nothing about the coverage number being manual.

(5) Decisive: the author is fixing this exact finding in-flight. The working-tree script changed between two greps during this review (mtime 2026-09-06 03:03:17, uncommitted) and now contains `audit_judge_coverage()` at :1113, whose docstring at :1116 reads verbatim: "round-2 复核指出：验收单写着'脚本自带覆盖自检'，而脚本里根本没有这段代码——13/13 是我在 shell 里手算的。" That is the author confirming the claim. The new gate (coverage.complete -> EXIT_ISOLATION_FAILED at :1359) is wired into the return (:1200/:1205) but has NOT been re-run: the newest verify-judges evidence is 02:51 while the code is 03:03, and that JSON still lacks the `coverage` key.

Failure scenario holds on the reviewed artifact: adding a 14th verdict (e.g. lancedb_delete_is_load_bearing) without a matching mutation leaves `--verify-judges` printing 11/11 KILLED, all_killed: true, rc=0, and the UAT template can keep asserting a self-check that does not run.

Severity MEDIUM is right and consistent with this card's own precedent (HIGH-1 was accepted on the same ground — "报告声称验证过的事其实没验证"); it is a claim-wider-than-evidence defect about a gate's strength rather than a live isolation break, so not HIGH.

---

### 7. [LOW] UAT 声称「脚本自带覆盖自检」，脚本里不存在该代码 —— 13/13 是手算的，覆盖回归无门

**位置**：`_bmad-output/验收单/UAT-CARD-G2-9-2026-09-05.md` 190（「判据覆盖：13/13（脚本自带覆盖自检…）」）与 234（MEDIUM-2 整改列「脚本自带覆盖自检」），对应代码 backend/scripts/g29_dual_vault_canary.py:1107-1112

**据以判断的事实**：`grep -n "coverage|覆盖|verdict_names" backend/scripts/g29_dual_vault_canary.py` 在 verify_judges 全段无命中；verify_judges 的返回只有 `{baseline_verdicts, mutations, all_killed}`（:1108-1112），`all_killed = not [r for r in results if r["verdict"] != "KILLED"]`（:1107）只统计变异是否被杀，**从不比对 expect_red 的并集与 verdicts 的键集**。落盘的 canary-verify-judges-20260905T184446Z.json 顶层键实测为 ['all_killed','baseline_verdicts','mutations','timestamp']，同样没有 coverage 字段。全仓除本脚本外无第二处 MUTATION_SPECS/expect_red 消费方（grep 已验）。

**失败场景**：任何人日后往 run_canary 加第 14 条 verdict（或把某条 expect_red 从名单里删掉）而不加对应变异：`--verify-judges` 依旧 all_killed=True、rc=0，验收单模板里「每一条检查都至少被弄坏过一次」这句话静默变假，round-1 MEDIUM-2 的原缺陷（4/12 覆盖）可以原样复发且没有任何门会报警。当前 13/13 是人肉求并集得到的一次性结论，不是可回归的判据。

**反驳者的核对结论**：CANNOT REFUTE — the mechanism claim is verifiably absent, but severity is overstated.

Confirmed with specific lines:
- `grep -rn "MUTATION_SPECS" .` returns exactly one code hit: g29_dual_vault_canary.py:1071 (the loop in verify_judges). The only other repo-wide hit is _bmad-output/审查/prompts/codex-prompt-CARD-G2-9.md:82, prose. So no second consumer could host a coverage check.
- verify_judges returns `{"baseline_verdicts": ..., "mutations": results, "all_killed": not survived}` (:1107-1112). `survived = [r for r in results if r["verdict"] != "KILLED"]` is a per-mutation kill tally only; there is no comparison of the union of `expect_red` against `verdicts.keys()`.
- Neither the CLI printer in `_amain` (:1240-1255) nor `_print_report` (:1195-1216) emits any coverage line.
- The landed artifact `_bmad-output/审查/evidence-g29/canary-verify-judges-20260905T184446Z.json` has top-level keys ['all_killed','baseline_verdicts','mutations','timestamp'] — no coverage field. The .txt transcript ends with the per-mutation list + rc=0 and contains no coverage output.
- UAT-CARD-G2-9-2026-09-05.md:190 and :234 both assert 「脚本自带覆盖自检」. That mechanism does not exist. It is not disclosed in 「本卡未证明什么」 (items 9 and 10 cover individual verdict blind spots, not coverage gating), so this is not a restatement of a disclosed limitation.

Mitigation the claim understates: :1092-1094 has a one-directional guard — `missing = [k for k in targets if k not in verdicts]`; non-empty `missing` forces killed=False → all_killed=False → EXIT_ISOLATION_FAILED. So renaming/removing a verdict that a mutation still names IS caught. The two scenarios the claim names (adding a 14th verdict with no mutation; deleting a name from an expect_red list) are genuinely uncaught.

Substance: I hand-derived the union of the ten expect_red lists (:193-259) against the thirteen verdicts[...] assignments (:994-1023) — the union is exactly those 13 keys. The 13/13 number is therefore true today; no conclusion the card asserts is wrong.

Severity correction: MEDIUM implies something is currently wrong. Nothing is — the coverage figure is accurate and independently re-derivable from the mutation table printed in the UAT itself. The defect reduces to (a) a false attribution of mechanism in the acceptance document (the repo's own 声明比证据宽 class) and (b) absence of a future-regression alarm on a one-shot verification script that is not wired into CI. That is LOW: register, do not block; fix is either a ~3-line union assertion in verify_judges or striking the parenthetical from UAT:190/:234.

---
