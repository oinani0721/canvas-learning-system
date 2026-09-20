# 判据 × 负控 覆盖对照（只读清单，实测待 workflow 复核结束后补）

> 口径区分（本卡反复踩到的那条）：
> - **有门覆盖** = 删掉它，35 格里**有某格会红**；
> - **有专属负控** = 十段负控里**有一段专门验证它**。
> 卡文只要求负控 ≥ 2 段（本卡 10 段）。所以「没有专属负控」本身不是缺陷；
> **「删了它没有任何一格会红」才是**（= 门未覆盖的路径）。

## `_harness_tree`（8 条判据）

| 行 | 判据 | 专属负控 | 备注 |
|---|---|---|---|
| :575 | 第一道通用探针 `_probe.get('a') == 1` | ✗ | 它是 T7-A 立的既有判据，本卡未动 |
| :598 | 键级探针（harness_tree ∧ a ∧ b 三项） | **段④**（整条）+ **段⑧**（只 a/b 两项）+ **段⑦**（探针文档改回单行） | 三段从不同侧面 |
| :626 | `if _cf is not None`（打不开 config ⇒ 回退） | ✗ | 由既有门 `..._no_config_falls_back_to_parent` 覆盖 |
| :670 | 词法否决 | **段①** | |
| :680 | `_doc.get('harness_tree') is not None`（采用） | ✗ | 由既有 16 门 + 控制组覆盖 |
| :682 | `if not _tree`（回退） | ✗ | 同上 |
| :685 | `isabs` ⇒ 相对路径补全 | ✗ | 既有门覆盖 |
| :697 | realpath strict ∧ `isdir(<tree>/backend/scripts)` | ✗ | 既有门 `..._nonexistent_tree_refuses` 覆盖 |

## `_harness_contract`（12 条判据）

| 行 | 判据 | 专属负控 | 对应的门 |
|---|---|---|---|
| :755 | 影子门 `abspath` 比较 | ✗ | `..._refuses_shadowed_module` + 控制组 `..._accepts_real_tree` |
| :761 | `EVENT_VERSION` 排 bool ∧ == 1 | **段②** | `[event_version_2]` / `[version_bool]` |
| :766 | `hasattr` 逐名 | ✗ | `[missing_name]` |
| :769 | `callable` 五名 | ✗ | `[vault_id_of_not_callable]`（round-4 L1 补） |
| :772 | `isinstance(..., re.Pattern)` 两名 | **段⑨** | `..._refuses_a_non_pattern_wrapper`（round-4 L2 补） |
| :784 | `_TS_RE` 认 Z 时间戳 | ✗ | `[ts_re_rejects_z]` |
| :786 | `_TS_RE` 拒纯日期 | ✗ | **⚠️ round-4 复核 L1 指出：表里缺这条的专属负控** |
| :788 | `_WHOLE_SECOND_RE` 认整秒 | ✗ | 未见专属格 |
| :790 | `_WHOLE_SECOND_RE` 拒缺秒 | ✗ | 未见专属格 |
| :793 | `classify_card_state({})` ⇒ `('new', …)` | ✗ | 未见专属格 |
| :796 | `validate_record_full('x')` ⇒ 非空错误列表 | ✗ | `[validate_accepts_scalar]` |
| :798 | `_looks_like_review_ext({}) is False` | ✗ | 未见专属格 |

## 待实测（workflow 复核结束后做，避免变异窗口与它的长跑重叠）

逐条删掉上表里标「未见专属格」的判据，看 35 格里**有没有任何一格会红**：
`:786` / `:788` / `:790` / `:793` / `:798`，以及 `:755` / `:766` / `:769` / `:575`。
红 ⇒ 有门覆盖（只是没有专属负控，可接受）；全绿 ⇒ **门未覆盖的路径**，要补。

---

## 实测设计依据（2026-09-19）

**跑哪两个文件、为什么不跑第三个**

判据面 = `test_harness_tree_parse_r2.py`（35 格）+ `test_g3_2_review_ledger.py`（314 格）= **349 格**。

⛔ **故意排除 `test_skill_portability_lint.py`**：它持有 SKILL.md 的整文件 sha256 基线
（`skill_portability_lint.py:3270` = `d64d3b8c…`）。任何变异都会改这个 digest ⇒ 它**每一段都红**
⇒ 15 段全报「有门覆盖」——一个**反方向的假结论**，而且长得像好消息。
而且它红了也不构成覆盖：指纹门只说「文件变了」，**不理解变的是哪条判据**。
把它算进来 = 用一道对语义无知的门给所有判据背书。排除它不是放宽判据，是让判据只回答它能回答的问题。
（已实测：`d64d3b8c` 在这两个文件里 0 命中；`test_g3_2` 内的 sha256 是对 tmp vault 树做指纹，与 SKILL.md 无关。）

**判据必须同时断言 rc 与执行数**

`pytest rc=4` = 用法错/路径不存在、`rc=5` = 零收集，**两者都给 0 条 FAILED**。
第一版探针正是因此假绿（见同目录 `probe-uncovered-judges-20260919T043255.txt` 的作废头）。
现行判据：`rc ∈ {0,1}` ∧ `passed + FAILED 条数 == 349`，基线另须 `rc==0` 且零 FAILED。

---

## 实测结论（2026-09-19，存档 `probe-uncovered-judges-20260919T043826.txt`）

15 条判据逐个换成 `if False:`，每段跑 349 格（基线 rc=0 / ran=349 / 0 failed，还原逐字节正确）：

| 档位 | 条数 | 判据 |
|---|---|---|
| ⛔ **门未覆盖**（红 0 格） | **7** | `tree-probe-a1` · `tree-not-isabs` · `ct-ts-rejects-date` · `ct-ws-accepts` · `ct-ws-rejects` · `ct-classify` · `ct-looks-like` |
| ✅ 精准覆盖（恰好 1 格红） | 6 | `ct-shadow` · `ct-hasattr` · `ct-callable` · `ct-isinstance-re` · `ct-ts-accepts-z` · `ct-validate` |
| ⚠️ 崩溃式（判定无效） | 2 | `tree-cf-is-none`(35 红) · `tree-not-tree`(121 红) |

**最有说服力的一对**：`ct-ts-accepts-z`(**有**门) vs `ct-ts-rejects-date`(**没有**门) —— 同一个正则的
两向判据，只锁了「该认的认」。`_WHOLE_SECOND_RE` **两向都没门**。
⇒ 契约是个**合取**（认该认的 ∧ 拒该拒的），门只测一半 ⇒ 一个恒返回 match 的假正则能过掉所有旧格。
⇒ round-4 复核指过这个方向并补了 2 格，但**没人去数还剩几条**。审查指出方向 ≠ 方向上的缺口都补完了。

### 处置：7 条全部补门（只改测试，生产一字不动）

- `_CONTRACT_CASES` +5：`ts_re_accepts_bare_date` / `whole_second_re_rejects_whole_second` /
  `whole_second_re_accepts_missing_seconds` / `classify_says_review_for_empty_frontmatter` /
  `looks_like_returns_zero_not_false`
  （最后一格刻意返回 `0` 而不是 `True` —— 生产判的是 `is not False`，返回 `True` 的话
  `if x:` 写法也会红、区分不出来；`0` 才钉得住。）
- 新增 2 格：`..._first_probe_catches_what_the_key_probe_cannot`（第一道探针未被接替的观测点 =
  **没有结尾换行的单行文档**）、`..._relative_harness_tree_is_resolved_against_the_vault`
  （相对路径补全 —— 删掉它不报错，而是把解析基准悄悄换成进程 CWD）。

### 负控段⑪：证明新门锁住的是它声称的那条判据

存档 `loadbearing-and-negctl11-20260919T053037.txt`。判据不是「有红」，是 **红格集合恰好 == {声称的那一格}**：
- 只断言「有红」⇒ 一次连带崩溃也能过；
- 只断言「那一格红」⇒ 漏掉「顺带把别的格也弄红」这种越界。

结果 **7/7 恰好锁住**，基线 rc=0 / ran=42 / 0 failed，还原逐字节正确。

### 两条崩溃式判据如实登记（未补门）

`tree-cf-is-none`（`if _cf is not None:`）与 `tree-not-tree`（`if not _tree:`）是**控制流型**判据：
换成 `False` 会抽掉后续代码的前提（`_raw` 未赋值 ⇒ NameError），红成一片。
那种红**不构成**「有门看着这条判据」，只证明代码崩了。
⇒ 本卡**没有**证明这两条有专属覆盖，如实登记进「未证明什么」。
要测它们需要换变异手法（如把 `_cf` 换成一个读到空串的假句柄），本卡未做。
