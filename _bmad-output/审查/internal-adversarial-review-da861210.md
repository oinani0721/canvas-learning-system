# 内部对抗审查 — CARD-G2-11 · 最终代码 `da861210`

> ⛔ **本文件不替代 Codex 轮次。** 协议 §1「不入库的复核不作依据」——本审查已入库，
> 但它是**本 session 自己跑的**，不是外部独立复核。Codex 第 5 轮因对方配额耗尽
> 两次 0 字节存档（已按协议删除不入库），本卡因此**转主 session 人审**；
> 这份文件只作人审时的参考读物。

| 字段 | 值 |
|---|---|
| 审查对象 | `scripts/j01_e2e.sh` @ `da861210`（Codex r4 整改后的版本）|
| 形态 | 5 个不同视角的 reviewer × 每条发现一名独立反驳者（默认判 false，须拿出行文证据）|
| 规模 | 44 agent · 5.08M token · 964 次工具调用 · 22 分钟 |
| 结果 | **确认 34 条 / 驳回 5 条**（去重前）|
| 视角 | up-safety · delete-safety · judge-honesty · seteuo-rc · portability-parsing |

## 确认的发现（按行号）

| 行 | 视角 | 等级 | 标题 |
|---|---|---|---|
| 52 | up-safety | MEDIUM | `no-abs-path` needle is `/Users/` only, so it is structurally blind to the throwaway root/vault path family the harness itself generates |
| 71 | up-safety | LOW | `J01_SECRET_MIN_LEN` is defined and documented as governing the plaintext comparison but is never referenced |
| 71 | seteuo-rc | LOW | J01_SECRET_MIN_LEN is declared and documented but never used; sensitive-key values of any length are used as bare substring needles |
| 232 | judge-honesty | MEDIUM | 行内注释归一的 case 守卫只认空格 + '#'，制表符分隔的合法 .env 行永远归一不出真值 |
| 458 | judge-honesty | MEDIUM | deploy-copy-key 豁免按键名放行 OLLAMA_HOST / LOCAL_EMBEDDER_BASE_URL —— 恰是本脚本自己判为「装着凭据」的那类 URL 值 |
| 542 | judge-honesty | LOW | 含 NUL 的文件在 no-abs-path 里被跳过后既不判红也不登记，n_bin 从不进判定链 |
| 556 | portability-parsing | LOW | `${ff#$absdir/}` uses the scan root unquoted as a glob pattern, so a path containing [ ] * or ? silently stops stripping the prefix |
| 611 | seteuo-rc | MEDIUM | no-abs-path's non-empty-input-surface proof counts enumerated files, not the files it actually greps |
| 672 | seteuo-rc | HIGH | throwaway blacklist silently drops the main-repo + live-vault entries; the fail-closed branch is unreachable |
| 785 | delete-safety | LOW | purge() is unbounded-recursive: a tree deeper than sys.getrecursionlimit() half-deletes the root, then refuses |
| 804 | delete-safety | LOW | Final rmdir still deletes by name — the header's "窗口不再存在" claim (line 743) is overstated |
| 838 | delete-safety | LOW | docker ps -a inside the EXIT trap has no timeout — the run can hang after it has already printed rc= |
| 859 | delete-safety | LOW | Every non-refusal failure collapses to rc=1 and the Python traceback never reaches $LOG |
| 917 | up-safety | LOW | `state-diff` is blind to gitignored writes anywhere in the harness tree outside `canvas-vault/` |
| 963 | seteuo-rc | MEDIUM | snapshot()'s reliability flag can never fire for a failed collection, so state-diff can go green while blind |
| 964 | judge-honesty | HIGH | snapshot 可信度自检是恒真判据 —— state-diff 能绿在「两次都没采到」上 |
| 1020 | up-safety | HIGH | isolation-preflight never inspects the volumes of `backend` — the one service `up -d backend` actually starts |
| 1104 | portability-parsing | MEDIUM | isolation-preflight compares container_name / network name as literal strings and never requires a *resolved* compose config, so rule ① passes on the  |
| 1219 | up-safety | MEDIUM | `evidence-redacted` can go green with an empty needle set — no non-empty-input assertion on the reference secret values |
| 1227 | judge-honesty | HIGH | evidence_has_ref_plaintext 对敏感键名不设长度下限（J01_SECRET_MIN_LEN 是死常量）⇒ 一条合法 .env 行让 evidence-redacted 恒红并静默丢弃全部部署证据 |
| 1246 | judge-honesty | LOW | copy_deploy_evidence 里的 mkdir/cp 无 rc 兜底，失败会在第 13 条断言之前被 set -e 杀掉整跑 |
| 1257 | judge-honesty | MEDIUM | 本跑新生成的实例密钥取不到时，「实例密钥不得出现在证据里」这一条静默变成空操作 |
| 1262 | seteuo-rc | LOW | evidence-redacted inspects $LOG before roughly a quarter of $LOG is written, then SHA256SUMS checksums the longer file |
| 1290 | delete-safety | LOW | dep_n becomes the two-line string "0\n0", making the no-deploy-evidence-file branch dead code |
| 1290 | judge-honesty | LOW | `$(cmd \|\| printf …)` 在 cmd 已经往 stdout 写过东西时会拼出双份值 —— dep_n 的 empty-input-surface 分支因此是死代码 |
| 1290 | up-safety | LOW | `dep_n` is `0\n0` when the deploy-evidence list is empty, making the `no-deploy-evidence-file` branch dead code |
| 1290 | portability-parsing | LOW | `grep -c` on a zero-match input emits "0" AND exits 1, so `\|\| printf 0` appends a second 0 and dep_n becomes the two-line string "0\n0" |
| 1293 | judge-honesty | MEDIUM | evidence-redacted 没有 no-old-secret 那道「参照面为空即 fail-closed」的门 |
| 1407 | portability-parsing | LOW | curl already prints `000` on connection failure, so `\|\| printf '000'` appends and the captured HTTP code becomes the impossible value `000000` |
| 1491 | portability-parsing | HIGH | The authorized --allow-up journey can never succeed: the second deploy re-runs install against an existing vault (exit 66 → deploy exit 72) |
| 1511 | judge-honesty | MEDIUM | first-index 只证明「LanceDB 健康端点回了 ok」，与「本 vault 完成首索引」不是一回事 |
| 1649 | portability-parsing | MEDIUM | rollback-down greens precisely when `up` never happened — the authorized branch never asserts a container was created |
| 1834 | judge-honesty | LOW | evidence-redacted 检查的是主日志的一个前缀，检查之后脚本还在往同一个 $LOG 追加 |

## 被反驳者驳回的（未确认）

| 行 | 视角 | 驳回理由（节选）|
|---|---|---|
| 52 | judge-honesty | The claim's structural premise is true but its operative assertion is empirically false, including the falsification test the claim itself proposes.  TRUE part: |
| 63 | portability-parsing | The mechanical half of the claim is literally true — `for q in $J01_FORBIDDEN_API_PORTS` word-splits "7691 7692 7478 11434", 7687 is not a member, so `--port 76 |
| 924 | portability-parsing | The claim misidentifies which `main.js` gates the build. `step1_preflight`'s gate variable is `mainjs="$HARNESS/canvas-vault/.obsidian/plugins/canvas-learning-s |
| 1227 | portability-parsing | The claim's mechanical premise is true but its defect conclusion is not, on four independent grounds.  1. THE MISSING FLOOR IS DELIBERATE AND DOCUMENTED, NOT AN |
| 1560 | up-safety | The claim's *code-level* observation is literally true — I reproduced it — but the defect it asserts (wrong verdict + burned timeout window on a real run) is un |

## 本 session 的处置

见 commit `a22ac2e2`：两条 HIGH（隔离预检漏判 backend 的卷 / 授权态因 install 拒覆盖而
永远跑不通）与「代码当前作出了假主张」的那几条已整改；其余登记进验收单 §8。

整改后复跑：fixture 13 条断言 rc=0、livepre 红条数 5/5、负控 50/50 MATCH、
隔离锚 A/B + 敏感度矩阵 5/5、变异负控 VERDICT=KILLED 且四 sha 一致。
