BLOCKER: 无 / HIGH: 无

## MEDIUM

1. `_bmad-output/审查/evidence-g810/check_g810_refs.py:309` — `_ALNUM_TOKEN_RE` 仍是 `{1,40}`，因此 41 位以上纯字母数字的畸形 SHA provenance token 仍会完全掉出判定面。  
   **未被拦下的输入**：把 §2.13 中任一反引号 SHA 槽从 `6337e320` 改成 41 个连续 `a` 并重锚 digest；`_check_provenance_tokens()` 不会产生 `sha-missing`。我直接调用 v4.8 函数复核，`a*41` 与 `z*50` 均无 SHA 判定，而 `abc`、7 位、8 位非 hex、40 位不可解 hex 均红。

2. `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:281` — 绑定 commit 中的 UAT 声称 `sidecar-g810-r9-9a22c33b.json`「已入库」且为无 `path_validation_failures` / `path_exists_in_worktree` 的 v4.7 字节稳定口径，但 `74d58d14` 中不存在该对象，盘上当前未跟踪版本反而包含这两个新字段和 v4.8 note。  
   **对照输入**：`git cat-file -e 74d58d14:_bmad-output/审查/evidence-g810/sidecar-g810-r9-9a22c33b.json` 返回 “exists on disk, but not in HEAD”；再 grep 盘上同名 JSON，可见两个新字段均在。

## LOW

1. `_bmad-output/审查/evidence-g810/check_g810_refs.py:197` 与 `_bmad-output/审查/evidence-g810/check_g810_refs.py:416` — node 层按 ScalarNode 原文比较 `outcome`，constructed 层按 Python `str` key 精确比较；`!!binary` 构造出的 `b'outcome'` 键在两层都会漏掉。该面在 UAT §十.40 的“键名仍是 outcome”边界之外，但确实是 fenced YAML 内可解析的 fail-open 角落。  
   **未被拦下的输入**：在 fenced YAML 中加入 `{ !!binary b3V0Y29tZQ==: pass }`；v4.8 node/constructed 扫描均无命中，any-line 正则也不命中。

2. `_bmad-output/审查/evidence-g810/g810-r10-green.zsh:3` 与 `_bmad-output/审查/evidence-g810/check_g810_refs.py:325` — 两处说明仍写旧口径：green runner 注释称默认 `ca597bbf`，实际第 16 行默认 `9a22c33b`；checker 当前函数说明仍称“4–40 位”，实际 v4.8 是 1–40 位。  
   **对照输入**：无参数调用 runner 并比较输出的 `PREVS`，或并排读取第 325 行说明与第 309 行 regex，即可看到名实不一致。

## 逐项判定

- **r9-M1：按声明闭合。** 我独立探查 `!!int`、`!!float`、`!!bool`、`!!null`、`!!timestamp`、plain scalar、空字符串、sequence、mapping、anchor、`!!str pass`、binary pass/非法 binary；标量非法值均进 `outcome-enum`，非标量进 `outcome-type`，merge 源内非法值 node 层可见。仅 binary 编码 key 是边界外 LOW。
- **r9-M2：闭合。** `.//`、`./`、重复斜杠、`/./` 归一后均进 evidence 存在性；绝对路径与 `..` 段仍红；symlink 经 `resolve()` 后越 root 也会被 `_resolve_under_root()` 拒绝。反斜杠/百分号编码路径不在 POSIX literal path 声明面内。
- **r9-M3：仅 1–40 声明面闭合，整体不闭合。** `abc` 已红；41+ 纯字母数字仍逃逸，见 MEDIUM-1。
- **r9-M4：按声明闭合。** 绝对、盘符、`..`、NUL、反斜杠、U+FFFD 均会让 `path_decoded=false` 并非 0 退出；三反例与正控证据相符。`path_exists_in_worktree` 不进退出码也符合 §十.42 的声明边界。
- **r9-L1：产出标签闭合，但源注释仍有旧默认值。** committed r10 green 存档标题已改为“树内 checker 见 checker_here_sha256”；r9 已入库失真标签件仍在 `9a22c33b`。runner 注释残留见 LOW-2。

## 证据链核对

- 绑定与血缘核实：HEAD = `74d58d147cc5a51537fd65cca2f10ab069ea600f`，唯一父 = `9a22c33b`；`4120e0b6..74d58d14` 排除 `_bmad-output` 后 product diff 为空；底账在 r9/r10 均为 `cbfd619d…`。
- 脚本哈希核实：checker v4.8 = `7dcfd394…`，v4.7 = `2af0045b…`；sidecar 生成器 v4.8 = `f7bae0dc…`。
- 负控/回归核实：pre/post 各 25 case；4 条 R10 新用例 pre 全 rc=0、post 全 rc=1；20 条旧失败用例 pre/post 同型红；F2 两相位均 rc=0 且 digest 由 `2b89c64a…` 变为 `24b509a5…`；每相位 25 次 `sha_equal=yes`。
- 锚群/YAML 门核实：anchor 8/8 rc=1 + 对照 rc=0；YAML 5/5 rc=1 + 对照 rc=0。
- sidecar 核实：3 反例均 rc=1 且 `path_decoded=false`，正控 rc=0；r10 JEV `calls=2`、两 urgency/risk 值与 sidecar 一致，两条 `path_exists_in_worktree=true`。
- canonical 核实：我在当前 `74d58d14` 只读复跑 v4.8，`source_digest=expect_digest=eb60d83e2ed96b675bdbe87025923f9b`，rc=0。`g810-green-r10-20260920T140018.txt` 目前仍是待收尾件，符合 PENDING-R10，但最终收尾 commit 后仍必须重绑新 HEAD digest。

## 收口判定

**不满足 B/H/M/L = 0/0/0/0；本轮按上述发现为 B/H/M/L = 0/0/2/2。**  
因此不应释放合并门；至少需处理两个 MEDIUM，并在最终收尾 commit 上重跑/重锚 v4.8 digest 后再进入下一轮 0/0/0/0 判定。
