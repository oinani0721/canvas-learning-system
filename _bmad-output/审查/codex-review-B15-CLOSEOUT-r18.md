# BLOCKER

无。

只读绑定与破坏性操作复核：

- 当前 `HEAD = aa8936fb1d372af5b6a065b117672fa720e9706f`；本地 branch、`origin/*` tracking、`backup/*` tracking 均为同一 SHA。按本轮禁网约束未重新 `ls-remote`，采信你给出的 2026-09-21 02:09:51 活态自证。
- `git status --porcelain`：102 项全部为 `??`，tracked staged/unstaged 为 0；与 `g810-checker-final-digest-20260921T001727.txt:9,17-119` 的 dirty 口径一致，未发现 B15-closeout 相关未跟踪碰撞。
- `git fsck --no-dangling` rc=0。reflog 中 2026-09-20 19:57:42 的 reset 是移回当时已有 commit `a5788288`，末见丢提交轨迹；`b31361b1→1e907037` amend 已在 r17 复核存档登记。
- 收口面列出的 commit 均为最终 HEAD 祖先；`ec7d80f2` 与 `aa8936fb` 均只改 `_bmad-output/**`。`59e1f494..aa8936fb` 共 80 commits、0 merge；本地可达 B15 tag 为 35 个，与台账/推送档案口径一致。

# HIGH

无。主要门证据经只读复算或代码面平移核对，未发现假绿：

- **openapi / pyright**：当前静态解析 `backend/openapi.json` 得 paths=199、schemas=357、operations=211；`1e907037..aa8936fb` 对 `backend/app`、frontend、`backend/openapi.json` 零 diff，因此 `openapi-pyright-postP9-20260920T202117.txt:1-9` 的 `DRIFT: none (paths=199 schemas=357)` 与 pyright `0 errors, 83 warnings` 可平移到最终代码面。
- **unit 只减**：独立解析基线与 `unit-FINALPOSTP9` 的 FAILED nodeid，得到 33→32、introduced=`[]`、removed 唯一为 `tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`；`fe19b5bb..aa8936fb` 对 `backend/tests/unit` 和 7692 四文件零 diff。
- **7692 / contract / regression**：7692 FINAL-P9 档为 107 passed / 0 failed；contract 3-file FINALPOSTP9 档为 2 failed / 75 passed，红 nodeid 与既有红集合一致；regression 档为 2289 passed / 6 skipped / 1 xfailed。最终 HEAD 相对证据树仅有 `test_openapi_contract.py` 注释勘误，无行为面变化。
- **G8-10**：在最终 HEAD 只读复放 checker：probe digest=`1a1f5489259ada7346326e2090d6b923` 且唯一 failure 为占位 digest；回填后 `chains=6 obj07=5 failures=0 dirty_tracked=0 head=aa8936fb…` rc=0。checker SHA-256 仍为档案值 `f7c63b3c…`；`3139cef7..aa8936fb` 对 checker、G8-9 底账、v2 总账与 evidence-g810 输入面零 diff。
- **semantic v2.5.1**：当前脚本 SHA-256 复算为 `7c01d736126e2d32ed69363cf251e25721d4828489ea2b1f19ec3a475b57c51c`，与主跑档一致；7 个负控脚本均为单点变异并各有 rc=1 档案。`9229ea54..aa8936fb` 非 `_bmad-output` diff 为空，主跑的代码面结论可平移。
- **D40**：`04eb9a9f` 实为 480 个 `.py` + `backend/openapi.json` 的 `x-generated-at`；独立 AST 对照为 479 全等、1 个 docstring 尾随空白差异，该差异已在 `d40-hook-exclusion-evidence-20260920T225429.txt:50` 明确登记。
- **R-SLO / G4-13 / J07 / G8-7**：`slo-manifest.yaml:5-15` 仍为 locked/r2 且用户锁定记录在案；`gold_set_manifest.yaml:83-101` 为 103 条、pending=0、`status=approved / signed_by=Heishing`；J07 与 G8-7 均维持 Day-0/未签字/non-pass 口径，未冒充 pass。schemathesis 90 op 清单复算为 90 行且全唯一，仍是显式 skip 而非“全门已跑”。
- **轮次指针**：`STATUS.md:42-43` 与未合卡台账 `:178` 为 r17 已完成、r18 待跑；汇报 `:28` 最新“结果行”为 r16 并写 r17 待跑，这与 r18 尚未产生结果行的语义一致。
- 限制：因禁网，本轮未 live 复查远端 tag；35 tag 结论基于本地 tag、Git 祖先关系与已入库推送档案。

# MEDIUM

### MEDIUM-1 —— r17-M1 的“删行/漏轮类闭合”仍可被“删一行 + 补一行”绕过

- **位置**：
  - `_bmad-output/审查/evidence-b15-closeout/D-15-r17-整改说明.md:5` 声称 `--min-rows` 防“删行绿”、`--expect-latest` 防“漏轮绿”；
  - `_bmad-output/审查/evidence-b15-closeout/check-report-chronology.py:33-42` 实际只检查“行数下限”和“现存轮次最大值”；
  - `_bmad-output/审查/evidence-b15-closeout/check-report-chronology.py:54-65` 的 self-test 在同时给定 `--min-rows 20` 时只证明“丢最后一行会被行数守卫捕捉”，没有证明 latest-round 守卫、行唯一性或轮次连续性；
  - 当前被保护对象为 `_bmad-output/第十五批-完成的卡-汇报.md:27-28` 的 r15/r16 结果行。
- **一句复现思路**：只读导入该脚本后取 `load_rows()`，删除 r15 结果行再复制一条 r16 结果行，调用 `completeness_failures(mutated, 20, "r16")`，仍得到 `[]`；我在内存复算中得到 `current=20/[]`、`drop_r15_duplicate_r16=20/[]`，而单纯删除 r16 得到 `latest-round mismatch: 期望 r16，实测 r15`。
- **未被拦下的输入**：把“删除 r15 行 + 复制 r16 行”或“删除 r15 行 + 追加任意满足时间格式的非轮次行”提交到一个后续 docs commit 后再跑门；行数仍为 20、最大轮次仍为 r16，重复/替换行的事件时间也早于后续 commit，因此 blame/时序分支同样可 PASS。
- **对照输入**：当前真实报告 rows=20、violations=0；简单删除任意一行会触发 `rows<20`，简单删除最新 r16 行会触发 latest-round mismatch。
- **负控输入**：上述“提交后的 intermediate-round deletion + duplicate/replacement”是 r17-M1 self-test 未覆盖的负控；它演示的是类缺口，不是当前报告已发生该篡改。
- **门未覆盖的路径**：期望行集合或行内容哈希、行唯一性、r4–r16 连续轮次、结果行物理顺序、以及 report 与 STATUS/台账待跑指针的自动对账。`--expect-latest` 仍由调用者手工提供，若沿用旧值也不会发现 STATUS 已推进。
- **判定影响**：r17 指出的“漏 r16 行”实例本身已闭合，简单删行和漏最新轮也有守卫；但“删行/漏轮 vacuous PASS”的类闭合不成立，不能按全零复核。

# LOW

### LOW-1 —— 时序门随行的算法说明仍写着已被弃用的 pickaxe 口径

- **位置**：`_bmad-output/审查/evidence-b15-closeout/check-report-chronology.py:5-6` 写“`git log -S <整行文本>`”，但实际实现 `_bmad-output/审查/evidence-b15-closeout/check-report-chronology.py:70-82` 使用 `git blame --porcelain -L`。
- **一句复现思路**：并排读取 docstring 与实现，即可看到文档算法和执行算法不一致。
- **未被拦下的输入**：未来把实现改回 `git log -S` 时，现有 `--self-test` 仍只测 completeness 函数，不会红；同前缀、行移动或 full-line pickaxe 归属错误可重新进入。
- **对照输入**：r17 整改说明与 commit message 都要求 blame 逐行归属；当前代码主体确实已是 blame。
- **负控输入**：当前没有针对“blame 被替换为 pickaxe”的归属算法负控。
- **门未覆盖的路径**：归属算法语义没有 self-test 或脚本哈希守钉定。

### LOW-2 —— r17 PASS 档的主命令记录不能生成其中附加的 self-test 段

- **位置**：`_bmad-output/审查/evidence-b15-closeout/report-chronology-audit-20260921T020936.txt:1-2` 只记录 `python3 check-report-chronology.py $PWD --min-rows 20 --expect-latest r16`；但 `_bmad-output/审查/evidence-b15-closeout/report-chronology-audit-20260921T020936.txt:28-31` 另含 self-test 输出。脚本 `_bmad-output/审查/evidence-b15-closeout/check-report-chronology.py:54-65` 在 `--self-test` 下会提前返回，只输出 self-test，不会同时输出 `:3-26` 的常规逐行结果。
- **一句复现思路**：按档案 line 2 原命令运行，只能得到常规 PASS；必须再单独运行带 `--self-test` 的第二条命令才能得到 line 28 以后内容。
- **未被拦下的输入**：事后手工追加、拼接或编辑第二段输出不会被该档案自身发现；档案未记录第二命令、HEAD 或脚本 SHA。
- **对照输入**：我在最终 HEAD 分别复跑常规命令与 self-test，均 rc=0，且常规输出与档案 `:3-26` 一致，因此这是证据捕获口径缺口而非结果造假。
- **负控输入**：删除或伪造档案中的 self-test 行，目前没有单独的 transcript-integrity 门会红。
- **门未覆盖的路径**：多命令档案的逐段命令记录与最终 HEAD/脚本哈希绑定。

清零：否  
B/H/M/L = 0/0/1/2
