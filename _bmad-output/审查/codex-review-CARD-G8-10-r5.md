> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p6-skills-w · 卡 CARD-G8-10 round-5
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r5.md)" > _bmad-output/审查/codex-review-CARD-G8-10-r5.md 2> _bmad-output/审查/codex-review-CARD-G8-10-r5.stderr </dev/null`（rc=0；2026-09-20 02:18:31 → 2026-09-20 02:36:11 -0700）
> 审查绑定: `5ae6d75f`（各轮时点绑定；amend 血缘与终态见验收单 §八/§九.6）
> 会话头自证（行号按 .stderr 原文）: 第 2 行 `OpenAI Codex v0.153.3` / 第 5 行 `model: glm-5.3` / 第 9 行 `reasoning effort: max`

---

只读审查完成：未改动任何文件，未连接数据库或网络服务；反例核对通过内存构造/静态调用完成，未落盘。绑定核验为 `1a25a9e6f55fe01565ff10615d194900bd309545`，树内脚本 sha256 = `6841bddf023de9ce439d5610bdc4fe711401a9c958f95f4302742e60ca5f1066`；底账在 `4120e0b6..1a25a9e6..HEAD` 字节不变，sha256 = `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。当前 `1a25a9e6..5ae6d75f` 仅新增 r5 prompt，代码 diff 与底账 diff 均为空，符合“此后仅 `_bmad-output`”的绑定保持规则。

## BLOCKER

无。

## HIGH

- **HIGH — `_bmad-output/审查/evidence-g810/check_g810_refs.py:303-305`；底账 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:265`** — “任何 `pass` 记录一律红”的实现仍只识别冒号/等号后立即出现的裸小写 `pass`，不识别有效 YAML 引号标量如 `outcome: "pass"`。显形：**未被拦下的输入**——保留 canonical summary/YAML 为 `not_yet`，在 criteria 追加 `- {dim: observability-extra, outcome: "pass", coverage: partial}` 并按新底账重锚 `--expect-digest`，不会出现 `pass-unsupported`。

- **HIGH — `_bmad-output/审查/evidence-g810/check_g810_refs.py:34` / `:225-238`** — r4-H2 的“伪 owner 与真 owner 并存”仍未闭合：非 ID 的反引号 token 会被 `findall` 忽略，随后又在 whitelist 前被整段删除。显形：**未被拦下的输入**——把检索链 owner cell 改为 `` `张三` / `G4-3`（总账 v2 …:500） `` 并重锚 digest，提取集仍为 `{G4-3}`，引号外白名单看不到 `张三`，脚本仍绿。

## MEDIUM

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:157-173`** — nodeid 只检查字符串前缀 `backend/tests/`，没有像 `:107-110` 的 file:line 引用一样做 `..`/root 归一化边界。显形：**未被拦下的输入**——把任一机械判据改为 `backend/tests/../app/models/service_status.py::ServiceStatus` 并重锚 digest，`_check_nodeids` 不报错且会把非测试源文件计入 digest。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:97-119` / `:217-221`；底账 `:162-167`** — 无行号的 evidence 目录引用和平文 SHA provenance 不参与“可解引用”或内容绑定；`sha-missing` 只扫描反引号包裹的 exact SHA token。显形：**门未覆盖的路径**——外部移走 `_bmad-output/审查/evidence-g2-8/`，或将平文 `6337e320` 改成无效 SHA 后重锚 digest，脚本仍可 rc=0。

- **MEDIUM — `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:58-60` / `:115`；`collect-final-batch-20260920T005925.txt:1-9`** — UAT 把“真跑”归给 §四，但 §四证据是 `--collect-only`，只能证明 collection/selector 可发现，不能证明测试体执行或断言通过。显形：**对照输入**——把某个已收集 test body 改成无条件 `assert False`，`--collect-only` 仍显示 `1/… tests collected`。

## LOW

- **LOW — `_bmad-output/审查/evidence-g810/check_g810_refs.py:16` / `:316-321`** — usage 仍写 `--expect-digest <16hex>`，实现与输出已经是 32 hex，文档口径漂移。显形：**对照输入**——按 usage 传入旧 16 hex 锚，输出 actual/expect 均为 32 hex 并触发 `digest-drift`。

## 逐项独立核对

- **⓪ 六链假归属**：未发现。六条判据文句均逐字命中标注源行：检索 `service_status.py:108`；复习 `review_overview.py:1044/:2463`，用户可见渲染面 `review_app.py:582-592` 与 `test_review_app.py:2674-2688` 在场；部署 `deploy-vault.sh:3079`；skill 为 2479 行 0 命中且如实登记缺口；freshness `vault_lint.py:887`；DLQ `traces.py:405-406`。owner 档案节行号与允许集一致，且均不在总账 §五 DONE。
- **① r4 HIGH 处置**：H1/H2 的指定锚输入已红，但如上仍有新反例，不能称完全闭合；H3 已闭合——`1a25a9e6` 树内实际包含 v4.3 脚本、99 个 `evidence-g810/` 文件和含实际脚本 sha 的 UAT。
- **② 恒绿面**：有，主要是 YAML 标量语法、owner token 语法、nodeid 归一化路径、无行号 evidence/平文 SHA。
- **③ 内容一致性**：脚本/底账 SHA、commit ② 内容、六链+OBJ-07、`not_yet/partial`、两项缺口、10 锚、三段负控、post-② green/negctl 复跑均与声明相容；`post2b` head 为后续仅文档 commit `5ae6d75f`，但双空判据成立。
- **④ r5 收口**：**不满足 B/H=0**；最小反例见两条 HIGH。
- **⑤ 其它**：`--collect-only` 不能承担“真跑”表述；`vault_lint` open/close 112 passed 与 unit 失败集基线相容，但不能宣称全量改善。
