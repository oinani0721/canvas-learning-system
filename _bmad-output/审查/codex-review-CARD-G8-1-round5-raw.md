# CARD-G8-1 round-5 —— 被安全过滤拦截，无正式裁定（stderr 轨迹存档）

> 两次尝试（原措辞 / 中性措辞）均在收尾阶段被 codex 侧过滤拦下：
> `ERROR: This content was flagged for possible cybersecurity risk`，产出 0 字节 + EXIT=1。
> 按 MEMORY `codex-exec-gotchas` 的处置：**保留 stderr 并入库**——
> 本轮的两条真发现（G11 判定顺序缺口、拒读断言杀不掉 mutation）就是从下面这段轨迹里捡回来的。
> 整改与自证记录见 `codex-review-CARD-G8-1.md` §11。

```text
2221:   969	            continue
2260:     9	| B1 目录 symlink | **NOT-CLOSED / BLOCKER** | 指定 alias 场景已报 G8；但不可读对象、非解析 symlink、超长路径仍可 `rc=0/findings=[]`，且外部文件 symlink 可被越界读取 |
2647:    41	   这条风险已登记，归属 G4-16 FU-3。
2679:    73	| 根级新 md 必须逐个登记 | 兜底行只能断言**准入行为**，断不了归属 → 新增 **G9**：未登记进 `known_instances` 的根级 md 判红（防机器产物被静默读成"用户手写"） | 测试 23 |
2683:    77	| 越界文件判红**且拒读** | 指向 vault 外的 symlink，其正文此前被照读 → containment 检查移到读取**之前**，新增 **G11**；测试机械断言外部目标的 type 不出现在任何 G3/G4 里 | 测试 26 |
2783:   177	另有一处治理错误：`.quarantine/UAT-2.5.X-test.md` 因解析顺序被读成"可安全删除"，
2796:   190	| HIGH | 根级兜底行会把未来任意根级 md 静默泛化成"用户 wiki / 不可重建" | 新增 **G9** + `known_instances`：逐实例登记，否则判红。承认核心论点——**镜像准入规则只能证明 RAG 行为，证明不了归属** |
2801:   195	最重的一条是**越界读取**：指向 vault 外的 symlink，checker 会在准入判断**之前**
2806:   200	（新增 **G11** 判红并**拒读**）。live vault 计数与旧实现完全一致，无回归。
2835:   372	### BLOCKER-E：扫描完整性仍失守（四类静默盲区 + 一次越界读取）
2853:   390	- 新增 **G11 vault_escape**：文件解析到 vault 之外时**先判红再拒读**——
2857:   394	回归门 = 用例 26 族（dangling symlink → G10；外部 symlink → G11 且断言其
2858:   395	`type: exam_board` **不出现在任何 G3/G4 finding 里**，即"拒读"有机械证据）。
2883:   420	| 去掉 G11 判红与拒读 | 外部 symlink | **FAILED** ✓ |
2939:   318	                continue
2976:   614	# 归属解析
2992:   630	    """文件 → 台账条目。顺序: root_files → derived_artifacts → vault_entries(目录)。"""
3120:  1067	# 26. 枚举盲区与越界读取 (round-4 BLOCKER: G10 / G11)
3154:  1101	    g11 = {f.subject for f in res.findings if f.code == "G11"}
3156:  1103	    # 拒读的证明: 外部目标的 type=exam_board 不得出现在任何 G3/G4 finding 里
3202:  1149	# 10. glob 引擎 (顺序敏感 ruleset 的地基)
3248:  1973	        # P1-05d (V2): containment 门 — symlink/.. 越界一律拒, 目标正文不得被读
3376:冻结哈希已逐字节匹配；当前 `HEAD=cbb20afb…`，三份交付物和审查/UAT材料均为未跟踪文件，`git diff cbb20afb --stat` 为空。静态复开时另注意到一个需继续验证的报告一致性点：JSON 的 `checks_run` 目前仍只列 G1–G7，虽然执行路径已加入 G8–G11；我会判断它是展示缺陷还是影响验收语义。现在开始跑冻结全套 104 items 与生产 CLI。
3471:    25	#     divergence_reason (实测依据 + 归属)。
3481:    35	#   - **顺序敏感, 先匹配先命中** (防火墙式 ruleset): 特化行必须排在容器行之前。
3643:   197	# vault 目录逐条 (顺序敏感: 特化行在前, 容器行在后)
3724:   636	      非 .md, 两面均以 not_markdown 拒; 归属车道 G3-1/G3-2。
3750:   781	      **逐实例登记** (见 known_instances) —— 本行不对未来的根级 md 泛化归属。
3774:   805	      顺序契约: 本行必须是 root_files 的**最后一行**, 否则会抢走前面所有
3972:**Planning G11 bypass with temp fixture**
4196:**Identifying G11 enforcement bypass**
4303:17:#  10. glob 引擎语义 (顺序敏感 ruleset 的地基)
4304:18:#  11. root_files 顺序契约 —— 兜底行 `*.md` 必须在最后, 否则抢走黑名单行的命中
4316:30:#  23. 根级兜底行必须逐实例登记, 不得静默泛化归属 (G9)
4341:1067:# 26. 枚举盲区与越界读取 (round-4 BLOCKER: G10 / G11)
4343:1149:# 10. glob 引擎 (顺序敏感 ruleset 的地基)
4344:1201:# 11. root_files 顺序契约 (兜底行必须最后)
4353:另外，对 G11 的交叉复核已出现更实质的问题：越界检查放在“无法归属则 `continue`”之后，未登记目录中的外逃链接不会产生 G11；若该目录恰由合法 `known_gaps` 豁免 G1，门可无 blocking finding。正在用冻结代码的 `/tmp` 夹具复算该路径，并复核“不读取”回退测试是否真的能杀死单独的读取回归。
4355:冻结哈希、HEAD/状态、基线 104 items 与 live 175/324/0 已复算。静态/对抗轨发现 G11 顺序缺口及拒读测试可疑，进入主审交叉复验。
4357:  → 静态复核 YAML 矛盾、known_instances、glob 判据、UTF-8 与 G10/G11 实现
...
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G8-1-round3-raw.md"
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G8-1-round4-raw.md"
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G8-1-round5-raw.md"
?? "_bmad-output/\345\256\241\346\237\245/codex-review-CARD-G8-1.md"
?? "_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-G8-1-\346\226\207\346\241\243\350\247\222\350\211\262\345\217\260\350\264\246-2026-08-30.md"
?? backend/scripts/check_vault_doc_roles.py
?? backend/scripts/vault_doc_roles.yaml
?? backend/tests/unit/test_vault_doc_roles.py
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead

**Verifying untracked files and test coverage**
**Confirming business code locations**
**Testing file name pattern matching**
**Analyzing contract divergence coverage**
**Planning fixture for contract testing**
2026-08-30T08:46:47.039118Z ERROR codex_core::tools::router: error=timeout_ms must be at least 10000
**Locating and diffing b2 selector copies**
**Identifying symlink race vulnerability**
**Assessing enumeration remediation gaps**
**Determining medium-level metadata risk**
**Planning names pattern experiment**
**Setting up read-only sandbox execution**
**Identifying frontmatter_type validation bug**
**Planning in-memory frontmatter_type reproduction**
**Prioritizing findings with commands and outputs**
**Systematically classifying issue severities**
**Identifying malformed pattern handling defect**
**Classifying medium severity findings as retained**
**Documenting medium severity code locations**
exec
/bin/zsh -lc "env PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -B -c 'import copy,sys; sys.path.insert(0,\"backend/scripts\"); import check_vault_doc_roles as c; d=c.load_rules(); x=copy.deepcopy(d); div=next(v for v in x[\"admission_surfaces\"][\"by_design_divergences\"] if v[\"id\"]==\"DIV-2-md-suffix-case\"); pats=[\"**/*.md\",\"**/*.MD\",\"**/*.Md\",\"**/*.mD\"]; div[\"patterns\"]=pats; c._verify_contract(x); print(\"CONTRACT=ACCEPT\"); print([(p,c.names_something(p),c.is_catch_all(p)) for p in pats]); print(\"union\",c.is_union_catch_all(pats)); print([(p,c._covered_by_declared_divergence([div],p,\"/\" not in p,False,\"not_markdown\",True,\"ok\",True)) for p in [\"x.md\",\"节点/x.md\",\"x.MD\",\"节点/x.Md\",\"节点/x.mD\"]])'" in /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles
 succeeded in 0ms:
CONTRACT=ACCEPT
[('**/*.md', True, False), ('**/*.MD', True, False), ('**/*.Md', True, False), ('**/*.mD', True, False)]
union False
[('x.md', True), ('节点/x.md', True), ('x.MD', True), ('节点/x.Md', True), ('节点/x.mD', True)]

```
