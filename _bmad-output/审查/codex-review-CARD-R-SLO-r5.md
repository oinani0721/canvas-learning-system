# r5 复核结论

**绑定核验：通过。** 当前分支 `card/p10-docs` 的 `HEAD = 7f6dfeb8bb174d81eb8cf7cec53aa02bb2def663`，与请求绑定一致。指定两类 diff 均已真跑；本轮未改任何文件。

**最终分级：0 BLOCKER / 0 HIGH / 2 MEDIUM / 1 LOW。**

---

## BLOCKER

无。

---

## HIGH

无。因此无需 HIGH 级后续补证。

---

## MEDIUM

### M1 · `code_sha` 候选链条的核心 git 事实成立，但“窗口内所服务代码 = 9c4e7e82”和“重建项代码面同为 9c4e7e82”表述超出证据

**位置：**

- `_bmad-output/审查/evidence-rslo/code-sha-runtime-tree-20260920T131615.txt:14-19`
- `_bmad-output/审查/evidence-rslo/code-sha-runtime-tree-20260920T131615.txt:22-41`
- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:265`
- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:275`

**独立核对成立的部分：**

- FE 树 `67d66672..59e1f494` 对 `backend` / `src` 的 diff 为空。
- FE reflog 在测量窗口前后为：
  - `61b85b5b @ 2026-09-19 16:58:36 PDT`
  - `06a11a46 @ 2026-09-19 17:25:53 PDT`
  - 中间无 reflog 事件，支持“窗口内无 HEAD 移动”。
- `tree(59e1f494:backend) == tree(9c4e7e82:backend) == a5cd759a1f2d46737e337b87cefcf577a353c62c`，独立复算一致。
- `9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680` 在本仓 `git cat-file -t` 为 `commit`。
- FE 树 `git status --short -- backend src` 只有：
  - `backend/tests/fixtures/regression_baselines/board_manifest_last_run.json`
- 该 fixture mtime 为 `2026-08-19 09:53:53`，早于测量窗口；源码检索显示它由 regression 脚本/测试面使用，未见 service runtime 引用。

**超出的部分：**

1. **容器连续性不是同进程连续性证明。**  
   `docker-ps-open-20260919T165812.txt:1-4` 只证明 16:58 时同名 backend 容器 healthy；窗口内 8011 探针和测量档证明端口可用，但不能排除窗口中容器重启或进程替换。  
   取证档自身的 `state.started_at=2026-09-20T20:14:13Z`，即 2026-09-20 13:14 PDT，已经晚于测量窗口，不能回填证明 2026-09-19 17:11–17:16 期间无重启。容器 `created=2026-08-31` 有助于证明未被重建、mount 配置稳定，但仍不等于窗口内 uptime 连续。

2. **“唯一 backend 脏文件”应写成“唯一 tracked backend/src 脏文件”。**  
   FE 树下还存在 ignored runtime/test 面：`backend/.env`、`backend/data/*`、`__pycache__`、`.hypothesis` 等。它们不是 tracked code，也不推翻 backend tree equality，但“唯一脏文件”若不限定 `git status` tracked 口径，会忽略运行时状态面。独立 mtime 扫描还看到测量间隔内有 ignored `__pycache__` 与 `llm_call_logs.db` 变动。

3. **“重建项所用脚本来自本车道树……代码面同为 9c4e7e82”不能按整棵 backend 树理解。**  
   独立复算：
   - current card lane `7f6dfeb8:backend = 78a352945f5d9627c667483fa9e224bdbef216e3`
   - `a03f0ce3:backend = 78a352945f5d9627c667483fa9e224bdbef216e3`
   - `9c4e7e82:backend = a5cd759a1f2d46737e337b87cefcf577a353c62c`  
   两者并不相等；差异来自 P10-B 的 `backend/scripts/freeze_release_candidate.py` 与对应测试。  
   但 `scripts/daily_review_pick.py` 在 `9c4e7e82` 与 `7f6dfeb8` 的 blob 同为 `2d6c745ad7468c6e529299da1a2af7d250c0e0aa`，所以只能说 **该路径/脚本身份等同**，不能说本车道整棵 backend 代码面同为 `9c4e7e82`。

**最小后续补证/修正（docs/evidence-only）：**

- 新增 erratum 或 UAT addendum，不重写已入库取证档。
- 把结论收窄为：
  - “8011 容器按取证档 bind 到 FE 树 backend/src；在 tracked backend/src 口径下，FE HEAD 与 `9c4e7e82` 的 backend tree 相同。”
  - “窗口内 8011 连续可用，但同进程/无重启连续性未证明。”
  - “唯一 tracked backend/src 脏文件为测试 fixture；ignored runtime state 不纳入 code_sha。”
  - “review_rebuild 仅 `scripts/daily_review_pick.py` blob 与 `9c4e7e82` 相同；本车道整棵 backend tree 不同。”
- `code_sha` 继续保持 `null`，候选仍待主 session/用户裁定。

---

### M2 · A6 “新增证据档无绝对路径”不成立；`code_sha` 取证档引入用户主目录绝对路径

**位置：**

- `_bmad-output/审查/evidence-rslo/code-sha-runtime-tree-20260920T131615.txt:15-19`

**事实：**

该档 15-16、19 行包含 `/Users/<user>/...` 形式的宿主绝对路径，包括 FE worktree backend/src bind 源和 vault bind 源。

指定新增面中未见 `NEO4J_PASSWORD=` 或显式 key value；UAT 中出现的 `TYPESAFE_API_KEY` 是键名，不是值。因此 A6 不是全盘错误，但“无绝对路径”这部分明确不成立。

**影响：**

- 泄漏等级低于 key value：主要是本机目录结构/worktree 命名。
- 但它直接推翻作者自述 A6 的“新增 README bullet / UAT / 证据档无绝对路径”这一项；若后续脱敏审计只扫 README/yaml，会漏掉该新增证据档。

**最小后续补证/修正：**

- 新增 redacted companion 或 erratum，将 bind 源表示为 `<FE-worktree>/backend`、`<FE-worktree>/src`、`<repo-root>`。
- 在 UAT §14 或脱敏台账登记：“原始 docker inspect 档保留绝对路径，redacted 档为消费面。”
- 不建议在本轮直接改历史证据档；保持证据不可变，新增补充说明即可。

---

## LOW

### L1 · 锁版前置后的 UAT 顶部元数据与 yaml `code_sha_null_reason` 已出现局部过期

**位置：**

- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:5-7`
- `docs/release-evidence/slo-manifest.yaml:33-34`
- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:291-303`

**事实：**

- UAT 顶部仍写“commit 数：5（A/A2/A3/A4/B）”，但当前实际已在 B 后追加 6 个锁版前置 commit，最终 HEAD 为 `7f6dfeb8`。§14 有补充说明，但顶部元数据未更新，单独读头部会得到旧终态。
- yaml `code_sha_null_reason` 仍写“8011 运转的代码树与本车道树的对应关系未证明”，而 UAT §11.14 已登记新的候选取证。由于 yaml 是测量时 draft 面且本轮明确零改动，这可以解释为“主 session 未裁定前的旧理由”，但与 §11.14 的“取证已补齐”存在叙述落差。

**最小修正：**

- 后续授权的 docs-only addendum 中把顶部状态改为：
  - 原 A/B 阶段 5 commits；
  - 锁版前置追加 6 commits；
  - 当前 HEAD `7f6dfeb8`；
  - code_sha 仍 null 的理由改为“已有候选但待主 session/用户裁定”，而不是“对应关系完全未证明”。
- 在裁定前不强制改 yaml；可先在 UAT addendum 澄清，避免触碰 draft 面。

---

# ② 作者自述逐条结论

| # | 结论 | 核验要点 |
|---|---|---|
| A1 5×LOW 处置闭环且不越界 | **成立** | `a03f0ce3..7f6dfeb8` 非 `_bmad-output` 面只有 README `13/0` 与 yaml `269/0`；README 累计删除行 0。r4 L1、ZCode L1/L2/L3 均能定位到对应处置。注意：`b0ac7192..7f6dfeb8` 中 README 是 `3 insertions / 1 deletion`，因为 r4 L1 是对本卡早期新增行的就地修正；这不破坏“相对卡前 PREV 纯新增”的口径。 |
| A2 v2 汇总忠实 | **成立** | 五个 raw sha256 逐字一致；四项 HTTP 指标与 rebuild 独立重算全部吻合；cold 口径已明确限定为 19 条 200 样本，且全样本 max=120.0037 单列。 |
| A3 code_sha 取证实证可复核 | **部分** | git 层核心事实成立：0 commit 触达、reflog 无窗口内移动、backend tree equality、candidate 是 commit、唯一 tracked dirty fixture、yaml 仍 null。但候选结论的措辞超出证据，见 M1；live Docker inspect 在本轮沙箱下不可复核，只能采信取证档。 |
| A4 JEV 机制实证 | **成立** | FE 树 `scripts/jev_review_triage.py:46` 默认 pathspec 为 `*.py/*.ts/*.tsx/*.sh/*.js`；`:159-163` 确实按 pathspec 调 `git show`。`e4ef1ebf` 只改 md/README，默认档 `code_files/files/usage` 全空；docs-pathspec 档三者非空。口径仍归主 session，UAT §11.15 已登记。 |
| A5 draft 面未被触动 | **成立** | 独立解析 yaml：`status=draft`、`revision=slo-manifest@2026-09-19-r1`、`locked_by/at=null`、9 个 `threshold.locked` 全 null、4 measured / 5 not_measured、`code_sha=null`。 |
| A6 无新增敏感面 | **部分** | 未见 key value 或 `NEO4J_PASSWORD=`；但新增 `code-sha-runtime-tree` 档含用户主目录绝对路径，“无绝对路径”不成立，见 M2。 |

---

# ③ r5 焦点逐项回答

## ⓪ v2 汇总与原始档 / v1 是否逐一吻合

**结论：吻合。** 我从原始档重新解析样本并重算：

| metric | n / ok | p50 | p95 | max |
|---|---:|---:|---:|---:|
| review_overview_first_paint | 20 / 20 | 0.009911 s | 0.039092 s | 0.039631 s |
| rag_warm | 20 / 20 | 1.668680 s | 1.866504 s | 1.870227 s |
| rag_cold | 20 / 19×200 | 3.286965 s | 5.362801 s | 5.362801 s；全样本 max 120.003677 s |
| kg_read | 20 / 20 | 0.003622 s | 0.027113 s | 0.027765 s |
| review_rebuild | 5 / rc 5×0 | 0.05 s | 0.05 s | 0.05 s |

五个原始档 sha256 独立重算，与 v2 汇总逐字一致：

- `0748b1fa…611c`
- `21e5b9ee…a6fc`
- `5052db19…2244`
- `9dd7f170…8b9a`
- `df98c686…d0350`

**cold 口径强度：** v2 的表述足够收窄：`rows=20`、非 200 样本保留、描述统计只对 19 条 200 样本、全样本 max 单独列出、整项仍 `not_measured`。`quantiles(n=20)[18]` 是分位数算法参数，不是成功样本数声明；行内已明确“仅对 19 条 200 样本”。

---

## ① code_sha 取证链条

### (a) 0-commit 区间是否覆盖 17:11–17:16 PDT

**是。**

- `67d66672..59e1f494 -- backend src` 为空。
- 该区间覆盖窗口前后。
- FE reflog 显示 16:58:36 到 17:25:53 之间无 HEAD 事件。
- 因此“窗口内没有 tracked backend/src commit 变化”成立。

### (b) 唯一脏 fixture 是否与运行时行为无关

**在 tracked backend/src 口径下，基本成立。**

- `git status --short -- backend src` 只有该 fixture。
- mtime `2026-08-19 09:53:53`，早于窗口。
- 检索显示它由 `run_board_manifest_regression.py` / regression 测试面引用，未见 app service runtime 引用。
- 但应限定为“tracked 脏文件”；ignored `.env`、data、pycache、logs 属于另一运行时状态面，不应被“唯一脏文件”措辞吞掉。

### (c) 容器/端口窗口连续性

**部分成立。**

- 16:58 docker-ps 存档 + 17:11 env probe + 17:11–17:15 多组 200 探针，能证明同名服务/端口在窗口内可用。
- 取证档的 Docker inspect 证明当前同名容器 created 于 8/31，并 bind 到 FE backend/src。
- 但不能证明 17:11–17:16 期间没有重启/进程替换；当前 `started_at` 已是 9/20，晚于窗口。
- 本轮我尝试 live `docker inspect`，沙箱无法访问 Docker socket；因此 live mount 状态对我是 **UNVERIFIED**，只能核对存档。

### (d) 是否应收窄措辞

**应该。** 最强可支持表述是：

> 在取证档所述 Docker bind 与 tracked backend/src 内容口径下，8011 所绑定的 FE backend tracked tree 与 `9c4e7e82:backend` 相同；窗口内 8011 连续应答，但同进程/无重启连续性与 ignored runtime state 未证明。候选 commit 待裁定，非已绑定 code_sha。

同时，review_rebuild 只能说 `scripts/daily_review_pick.py` blob 相同，不能说本车道整棵 backend tree 与 `9c4e7e82` 相同。

---

## ② 5×LOW 处置是否闭环，是否留下新歧义

**原 5×LOW 本身闭环：**

- r4 L1：README 新增行内已改为 `method sketch（owner 补实例/实参后复跑）`，YAML 四个写侧项仍是 sketch，口径一致。
- ZCode L1：README 新增第三条 known-boundary bullet，说明“自由文本不承诺普遍数值比较”和“同单位可判向时 S9 尽力而为核对”并存；既有行未改。
- r4 L2 / ZCode L2：
  - §5/§7 已补 commit B 落地时机；
  - §6 A4 evidence index 文件均存在；
  - §5(f)② “行 3 / 出现 5”独立复算成立；
  - 对应权威档确实在 `c2b1fac3` 中。
- ZCode L3：v2 汇总档修正 cold 表述并保留 v1。

**新歧义：**

- 不在原 5×LOW 处置本身，而在后续 code_sha 取证与 UAT 终态元数据：见 M1、M2、L1。

---

## ③ UAT §11.14 / §11.15 / §12 / §14 事实核对

### §11.14

| 事实 | 结论 |
|---|---|
| docker inspect 显示 8011 bind FE backend/src | 存档内成立；live inspect 本轮不可复核 |
| FE `67d66672..HEAD` 0 commit 触达 backend/src | 成立 |
| `tree(HEAD:backend)==tree(9c4e7e82:backend)` | 成立 |
| candidate 是 commit | 成立 |
| 唯一 backend 脏文件 = 测试 fixture | 仅 tracked backend/src 口径成立 |
| 测量窗口内所服务代码 = `9c4e7e82` | 表述过强，应按 M1 收窄 |
| yaml `code_sha=null`，未擅自绑定 | 成立 |

### §11.15

**成立。**

- 默认 pathspec 确为代码扩展名。
- `e4ef1ebf` 是 docs-only commit，默认结果必空。
- docs-pathspec 档 `code_files/files/usage` 非空。
- 该档明确“非门证据”，最终口径待主 session。

### §12

**事实面成立：**

- `status: draft`、`decision.locked_by/at=null`。
- 无用户签字/授权。
- code_sha 候选仍待裁定，未写入 yaml。

但 §12 引用 §11.14 时复用了较强候选表述，应随 M1 一并收窄。

### §14

**核心复核算成立：**

- validator `--all` 在当前 HEAD 重跑：J08 PASS，1 份 / 失败 0，rc=0。
- schema sha256 = `4456e1ad629108d618284d6bd5b717f484a712aa8685615e31f940327922c547`，与 `SCHEMA_SHA256` 一致。
- README 中 `slo-manifest.yaml`：命中 3 行、出现 5 次。
- README 相对 `a03f0ce3` 累计 `13/0`。
- yaml/schema/validator/J08 在锁版前置增量中零改动。
- §14 对 5×LOW 的处置描述与 diff/文件存在性一致。

遗留为 L1 的顶部终态/commit 计数过期问题。

---

# UNVERIFIED

- **live Docker inspect / Docker socket**：本轮沙箱无法访问 Docker API；bind、created、started 状态只能核对已入库取证档。
- **17:11–17:16 同进程/无重启连续性**：现有 docker-ps + HTTP 200 探针不足以证明。
- **无 key value 的绝对断言**：我只确认指定新增表面没有显式 value / `NEO4J_PASSWORD=`，未读取私有 env 或凭据库做全域比对。
- **历史测量时区/时钟本身**：只能采信证据档时间戳与 UAT 的“无回拨”登记，无法从当前机器重建当时时钟状态。

---

# 建议的最小后续动作（均为 docs/evidence-only）

1. **新增 code_sha erratum/redacted companion**：收窄 M1 的四类口径，并处理 M2 的绝对路径消费面。
2. **UAT 锁版前置 addendum**：更新最终 HEAD、commit 计数、code_sha null 的当前理由；不改 yaml、不触发锁版。
3. **保持 `code_sha: null`**，候选 `9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680` 只以“tracked backend tree candidate，待裁定”表述流转。
