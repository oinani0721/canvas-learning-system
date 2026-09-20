BLOCKER: 无 / HIGH: 无

**结论：不满足本轮 B/H/M/L = 0/0/0/0；实测为 B/H/M/L = 0/0/4/1。**

## BLOCKER

无。

## HIGH

无。

## MEDIUM

### M-1：merge 源内“非 pass 的非法 outcome 标量”仍可被显式键覆盖后吞掉

- `_bmad-output/审查/evidence-g810/check_g810_refs.py:184-193`
- **问题**：node 层对 `outcome` 标量只做“解码后是否等于 `pass`”判断，非 pass 的非法枚举值、int/bool/timestamp 等非字符串标量不会在 node 层触发 `outcome-enum` / `outcome-type`；若该标量放在 `<<:` merge 源里，再由显式 `outcome: not_yet` 覆盖，constructed 层也只剩合法显式值。
- **未被拦下的输入**：在 fenced YAML 中加入  
  `{dim: observability-extra, outcome: not_yet, coverage: partial, <<: {outcome: !!binary Ym9ndXM=}}`  
  （`Ym9ndXM=` 解码为 `bogus`）；同类可用 `<<: {outcome: !!int 123}`。node 层返回 `"bogus"` / `"123"` 但不等于 pass，constructed merge 又丢弃该源值，因此既无 `outcome-enum` 也无 `outcome-type`。这不是 `pass` 穿透，所以不计 HIGH，但直接违背 v4.7 对 binary 解码值与非字符串标量 fail-closed 的声明。

### M-2：路径归一化只剥字面 `./`，`.//_bmad-output/…` 仍跳出 evidence 绑定面

- `_bmad-output/审查/evidence-g810/check_g810_refs.py:321-335`
- **问题**：`while _norm.startswith("./")` 会把 `.//_bmad-output/…` 变成 `/_bmad-output/…`，随后 `_norm.startswith("_bmad-output/")` 失败而被当作“产品树散文路径”跳过；但原始 `Path(".//_bmad-output/…")` 语义上仍是树内 evidence 路径。
- **负控输入**：把 §2.13 的 evidence token 改为 `` `.//_bmad-output/审查/evidence-g2-8-nope-r9/` `` 并重锚 digest；即使目标不存在，也不会得到 `ref-missing`，也不会把存在目录内容纳入 digest。

### M-3：SHA 槽的“畸形值一律红”仍有 1–3 位 token 盲区

- `_bmad-output/审查/evidence-g810/check_g810_refs.py:296`、`:349-356`
- **问题**：只有先匹配 `_ALNUM_TOKEN_RE = ^[0-9A-Za-z]{4,40}$` 的 token 才进入新的 8–40 lowercase-hex 检查，1–3 位纯字母数字 token 在 SHA provenance 位置会被完全忽略，与“畸形值一律 `sha-missing`”的 r9 口径不一致。
- **未被拦下的输入**：把 §2.13 中任一 `6337e320` SHA provenance 替换为 `abc`（若按旧 docstring 把 token 面严格限定为 4–40 位，这可降为声明文案 LOW；按本轮 UAT/prompt 的“畸形值一律红”口径，它是同一 SHA 槽的 fail-closed 缺口）。

### M-4：sidecar 生成器把 `path_decoded: true` 当断言写，但没有验证相对性、UTF-8 有效性或路径存在

- `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:11`、`:56`、`:86-91`、`:115`
- **问题**：文档声称“解码后必须是可 `Path(...)` 直接解析的相对路径”，但实现只用 `errors="replace"` 解码、只检查 `code_files` 非空，然后无条件写 `path_decoded: true`；绝对路径、`..` 路径或无效 UTF-8 字节都会生成 `field_missing=[]` 且 rc=0。
- **负控输入**：让上游 `code_files` 含 `"/tmp/x.py"`、`"../x.py"` 或 `"\377x.py"`；生成器仍输出 `path_decoded: true` 并成功退出。当前 r9/r8/r7 三个具体 sidecar 实例的路径本身是可解析且存在于 Git 对象中的，但生成器的验证声称未闭合。

## LOW

### L-1：r9 green runner 与存档仍把 v4.7 标成“树内 v4.6”，与 UAT 声称“已修标签”不符

- `_bmad-output/审查/evidence-g810/g810-r9-green.zsh:26`、`:43`；`_bmad-output/审查/evidence-g810/g810-green-r9-20260920T134329.txt:1`
- **问题**：runner 和 13:43:29 存档标题仍写“canonical 底账，树内 v4.6”/`v46@…`，而同文件 `checker_here_sha256=2af0045b…` 明确是 v4.7；UAT §九.39 却登记“修标签后重跑”。
- **对照输入**：并排比较 `g810-green-r9-20260920T134329.txt:1` 与 `:3`，即可看到版本标签与 checker SHA 不一致；数值 digest 链本身仍可读，不影响核心结论，但“标签已修”的声明失真。

---

# ① 四项 open 的逐项判定

| r8 项 | 判定 | 说明 |
|---|---|---|
| H-1 `!!binary pass` | **指定 PASS，窄口径闭合** | `!!binary cGFzcw==`、binary alias/merge、block-scalar base64、非 UTF-8 binary 在“解出 pass”时会被 node 层或 constructed 层拦下；非 scalar list/map 也会 `outcome-type` 红。原始 H-1 的 pass 穿透没有找到反例。 |
| M-1 `HEAD/main` SHA | **目标 PASS / 广义 PARTIAL** | `HEAD` 与 `main` 确实进入 `sha-missing`；但 M-3 显示 1–3 位 malformed/symbolic token 完全不进入检查。 |
| M-2 `./_bmad-output` | **目标 PASS / 归一化 PARTIAL** | `./`、`..`、绝对路径三类负控均红；但 M-2 的 `.//` 变体仍逃出 `_bmad-output` evidence 面。 |
| L-2 sidecar path | **当前实例 PASS / 生成器声称 PARTIAL** | r9、r8、r7 sidecar 的顶层 `code_files` 均已是 UTF-8 路径，`code_files_raw` 保留，两条 r9 路径在 `9a22c33b` 中存在；但 M-4 显示生成器可对 malformed path 写出假 `path_decoded=true`。 |
| L-1 PREV_REF | **PASS** | `ca597bbf` 中的 r8 green runner 已有 `PREV_REF` 参数且默认 `dce85102`；r8 evidence 的 `prev@dce85102` 与该版本一致。r9 runner 也固定默认 `ca597bbf`，post-commit 链取值正确。 |

# ② v4.7 恒绿面与 UAT 声明边界

- **仍有恒绿面**：M-1 是 fenced YAML 内的 hidden merge 非法标量恒绿；M-2/M-3 是 §2.13 provenance 面的归一化/分类盲区；M-4 是 sidecar 假成功标记。未发现新的 `pass` 自证恒绿输入。
- §十.25 非 fence YAML / 正则次级检查边界：**可接受，不计**；本轮明确不要求扩面。
- §十.26 只扫 §2.13 反引号 token / 产品树散文路径不覆盖：原则边界**可接受**；但 `.//_bmad-output/…` 是 §2.13 内同语义 evidence 路径，仍需计 M-2。
- §十.27 白名单人工门：**可接受**；canonical rc=0 同时证明当前无 dead whitelist item。
- §十.28 有效 commit 替换由人工裁：**可接受**；F2 只证明 digest 绑定，不自动判授权。
- §十.36 custom tag / PyYAML 未来行为未穷举：原本可接受为非穷举声明，但 hidden merge 非法 binary/int 标量是当前可构造反例，**仍需计 M-1**。
- §十.37 `outcome-enum` 仅 fenced 面：边界本身可接受；但 fenced 面内 merge 源枚举仍不完整，**仍需计 M-1**。
- §十.38 r8/r7 sidecar 审后重生成：对当前实例**可接受**，字段变化透明；生成器验证缺口另计 M-4。
- §十.39 未合并/未集成/未触发故障：**可接受，不计**；属本卡明确外包范围。
- §九.39 “green 标签已修”：**不接受**，实际 runner/evidence 仍有 v4.6 标签，计 L-1。

# ③ r9 证据链自洽性

核心证据链自洽：

- commit：`9a22c33b` 的父确为 `ca597bbf`；`ca597bbf → 9a22c33b` 只改 `_bmad-output/**`，`:(exclude)_bmad-output` 的 product diff 为空。
- 先红后绿：pre 文件绑定 v4.6 SHA `3fd00174…`，8 条 R9 新用例全 rc=0；post 文件绑定 v4.7 SHA `2af0045b…`，8 条全 rc=1 且失败类型与声明一致。
- 回归：post 中 21 个应红用例全部符合预期，F2 单独按 rc=0 + digest `aa604ecf… → 15ebec57…` 验证绑定；每个 case 均有 `sha_equal=yes`、control rc=0、evidence 目录恢复记录。
- 锚群：8/8 rc=1，对照 rc=0。
- YAML 门：5/5 rc=1，对照 rc=0。
- digest 两代链一致：`v4.6@ca597bbf = cbf2f7b7…` → `v4.7@ca597bbf = aa604ecf…`；post-commit 再得 `v4.6@9a22c33b = df553078…` → `v4.7@9a22c33b = c70a6184…`。
- JEV/sidecar 数值链一致：`calls=2`、`sha/bound_head=9a22…`、两文件 urgency 2.87/2.37、risk=logic、VERDICT REVIEW 与上游 JSON/stdout 相符；当前顶层 `code_files` 两条路径可解析且对象存在。
- 当前 r9 review、post-green、JEV、sidecar、prompt 仍是 untracked closing face；这与 UAT `PENDING-R9` 和“develop commit + 计划收尾 commit”口径一致，不是隐匿矛盾，但意味着最终 HEAD 绑定尚未完成。

# ④ 本轮 0/0/0/0 收口条件

**不满足。**

最小反例：

1. **MEDIUM**：hidden merge 源 `<<: {outcome: !!binary Ym9ndXM=}` / `!!int 123` 被显式 `not_yet` 覆盖后不红。
2. **MEDIUM**：`.//_bmad-output/审查/evidence-g2-8-nope-r9/` 不做存在性/content digest。
3. **MEDIUM**：SHA provenance 位置的 `abc` 不触发 `sha-missing`。
4. **MEDIUM**：sidecar 输入 `"/tmp/x.py"`、`../x.py` 或无效 UTF-8 quoted path 仍输出 `path_decoded=true` 且 rc=0。
5. **LOW**：r9 green runner/evidence 仍标 v4.6，与 UAT“已修标签”不一致。

因此合并门不应以 r9 当前状态释放；至少需修复上述 M/L、补对应两相位负控、重锚 digest，并以收尾后的最终 HEAD 再取得一轮全零。

# ⑤ 其它观察

- sidecar 的嵌套 `files[].file` 仍是 git quoted/octal 的 raw diff pair；这不计新问题，因为机器路径声明只针对顶层 `code_files`，且 raw 字段本身有 provenance 价值。
- 本轮未连接数据库或网络服务，未修改工作区文件；所有判断来自 Git 对象、存档证据与脚本只读检查。
