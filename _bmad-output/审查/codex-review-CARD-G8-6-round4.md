结论：**FAIL，round-4 尚未最终收敛。**

- round-3 三项：**2 RESOLVED / 1 PARTIALLY-RESOLVED / 0 STILL-OPEN**
- 本轮新增：**0 BLOCKER / 3 HIGH**
- 当前复算基线：HEAD `37387a8662e9dd646fad5628841679d777cb7eae`
- 最终协议 SHA-256：`b4a3d3cc47332ae4d8dcd59dc77698d4221801d5bc5150f0a6cbce0e424f9009`

审查中协议曾被外部修改；以下结论已全部针对上述最终 SHA 重新验证。

## 三项整改裁定

| 项 | 裁定 | 当前证据 |
|---|---|---|
| HIGH#1 preflight 漏源、漏单库 | **RESOLVED（原 finding）** | 当前步骤无条件覆盖单/多库、BOOTLOG、child stderr，并明确较早成功不能替代检查：[协议 L92](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:92)、[L95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:95)。与 [push L38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily-review-push.sh:38)、[L75](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily-review-push.sh:75)、[wrapper L112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/launchd/daily-review-wrapper.sh:112)、[plist L19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/launchd/com.canvas.daily-review.plist:19) 一致。但整改命令另引入新的日志证据 HIGH，见下。 |
| HIGH#2 非 active 不跑 C9 | **PARTIALLY-RESOLVED** | 普通目录路径已修：覆盖集为 A3∪active，每个 key 跑 C1/C9，[协议 L89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:89)–[L91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:91)。用户 fixture 独立复算为 A `C1=0/C9=0`、B `C1=0/C9=1`。但 non-active 根内 symlink alias 仍查错 key，见新增 HIGH。 |
| HIGH#3 R-EVD 五项/七项不一致 | **RESOLVED** | §1 七门完整列于 [L34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:34)–[L40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:40)；R-EVD [L209](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:209) 逐名列齐七项、接受清单、理由、签字和受约束结论；[L39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:39) 明确“接受≠验证”。 |

## 本轮新增 3 个 HIGH

1. **HIGH — err.log 没有“当日新增区间”，缺源又会假绿。**

   [协议 L94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:94) 对无时间戳的全历史日志 grep 后 `tail -20`，没有 inode/byte cursor。历史错误每天都会命中，具体当日 preflight 又可能被截出证据窗口；更关键的是，err.log 不存在时实测为：

   ```text
   grep: No such file or directory
   whole pipeline exit 0
   ```

   因文本只规定“命中→登记”，缺失/不可读没有 fail-closed 后果，仍可破坏 degraded 可见门。

   建议措辞：D1 前冻结 err.log inode+byte cursor；每日读取从上一 cursor 起的全部新增字节，禁止 `tail`；文件缺失、不可读、inode 改变或 size 回退一律登记 `degraded/evidence_gap`，并把新 cursor 与切片 SHA-256 入台账。

2. **HIGH — A3 字面 key 与生产物理 key 分叉，HIGH#2 仍有可复现旁路。**

   A3 仍直接对 `<该库目录名>` 算 key：[协议 L19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:19)。但 wrapper 接受根内 symlink，随后改用 `pwd -P` 的真实路径：[wrapper L67](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/launchd/daily-review-wrapper.sh:67)、[L85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/launchd/daily-review-wrapper.sh:85)；child 再按 resolved basename 算 key：[push L29](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily-review-push.sh:29)、[runner L56](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/daily_review_run.py:56)。

   隔离 fixture：

   ```text
   alias-vault -> real-vault
   A3_key=alias-vault
   runtime_key=real-vault
   alias C1=1 / C9=0
   real  C1=0 / C9=1  (push:failed fallback:fail)
   ```

   [协议 L91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:91) 未定义 non-active C1 FAIL 的后果，因此这个假绿不会被兜住。

   建议 A3 冻结 `raw_name / REAL_VAULT / physical VAULT_KEY`，key 必须从真实路径通过 argv 派生；并规定任一 non-active C1 FAIL 必登记事件。

3. **HIGH — A4 未跟踪内容指纹依赖调用 cwd，且中间失败被掩盖。**

   [协议 L20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:20) 中 `git -C` 输出相对 `$CODE_WT` 的路径，但 `xargs shasum` 相对当前 cwd 打开文件。从 `/tmp` 执行时所有文件均 `No such file`，最终仍返回 exit `0` 和空流摘要 `e3b0c442…`，可形成外观合法但完全未绑定内容的启动指纹。

   建议改为：

   ```sh
   (cd "$CODE_WT" && set -o pipefail &&
     git ls-files --others --exclude-standard -z |
     xargs -0 shasum -a 256 -- |
     shasum -a 256)
   ```

   并明确“任一子命令非零＝A4 采集失败，窗口不得启动”。

**MEDIUM 及以下新增汇总：0 MEDIUM / 1 LOW**——[协议 L92](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:92) 的 wrapper `:52,91` 不是精确写日志行，宜改引 `58–60 / 71–74 / 91–95`。

## 其余 7 项 PARTIAL

结论是 **7/7 仍为 PARTIALLY-RESOLVED**，但其中并非全部只能等待用户或代码：

- **H2 accepted-unverified**：披露已改善，但 [L39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:39)、[L62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:62) 仍允许接受替代验证，模板 [L133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:133) 又没有接受字段。可纯文档闭合状态语义：增加 `VERIFIED_GREEN / OPEN / UNVERIFIABLE / ACCEPTED_UNVERIFIED`，并规定后者永不改写为 verified；总状态分 `VERIFIED_COMPLETE` 与 `ACCEPTED_WITH_UNVERIFIED(N)`。

- **H3 C2 identity**：每日已运行，但 null 仍 PASS、C2 不进日通过、且只跑 active：[协议 L97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:97)、[L103](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:103)、[L157](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:157)。可纯文档严化为：覆盖集每库跑 C2；D1–D14 要求非空且匹配；active C2 纳入日通过；null=`UNVERIFIABLE`；非空错 ID 必登记“串 vault/待裁”，不能只按 [C9 degraded L164](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:164)。

- **B2 Git 回填**：当前 [L99](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:99) 已诚实；实测 Git 仍接受 2000 年 committer date。文档最多标为 `SELF_ATTESTED_GIT：不证明 commit 在 D 日已存在`；真正闭合需外部 TSA/透明日志。

- **B3 C6(a)**：人工记录仍无法 join ingest→board，[协议 L161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:161)、[L189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:189)。用户锁定 `(b)` 即可文档闭合：机械 receipt 上线前 C6/C7 不进硬门；选择 `(a)` 则只能标 `ACCEPTED_UNVERIFIED`。

- **H1 一板(a)**：生产仍无 `board_completed`；[协议 L178](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:178) 选择 `(b) 至少一题` 可文档闭合。保留“一板”则必须新增代码回执。

- **H3 runtime exact bytes**：A4 命令和每次变更字段可在文档层先修；[§3.2 L60](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:60) 应要求每次完整重跑修正后的 A4，并扩展 [模板 L133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:133)。但 `StartedAt` 只能叫部署一致性证据；证明进程已加载 exact bytes 仍需运行时 attestation/不可变镜像。

- **M3 TZ**：当前 [A7 L23](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:23) 同时写“一致才可开窗”与“可接受不一致”，逻辑未闭。可纯文档 fail-closed：`IANA 不一致=A7 FAIL；waiver 只能启动 observation，不计 D1–D14、不得输出正常窗口完成；统一并重采 A7 后方可开窗。`

审查未修改工作树；仅使用隔离 `/tmp` fixture。未访问 live/raw vault、私有 `.env`、backups、真实日志、cache、容器或安装件，因此运行态 exact bytes 仍为 `UNVERIFIABLE`。当前环境未暴露 `graphiti-canvas/search_memory_facts`，故 Graphiti 本轮查询无法执行；Sequential Thinking 已执行，LSP 因无编辑不适用。


