# CARD-RV-G3-7 复审请求（只读复核，零代码卡）

## 一 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery`
分支 `card/u9-mastery`，HEAD `da690bf8`，工作区干净，本卡**未改动任何代码**（只写 `_bmad-output/`）。

被复核的对象是一次**审后整改**：上一张卡 CARD-G3-7 在收到第二轮外部复核（存档 `codex-review-CARD-G3-7-r2.md`，绑定 `ecfcc3f1`）之后，又提交了 `08fed737`（parent `ecfcc3f1`，标题「fix(review): 按 Codex r2 整改 5 条，定位失败也 fail-closed」），改了 7 个文件 +242/−42。**那 5 条整改从未被第二双眼睛看过**。本卡就是补这次复审。

`08fed737` 不是 HEAD 的祖先（已 squash 进 `afaceb06`），但对象可达；`git diff --stat 08fed737 HEAD` 在这 7 个文件上只剩 `backend/openapi.json`（后续统一再生），其余 6 个与 HEAD 逐字节相同 ⇒ **读 HEAD 即读 08fed737 终态**。

**最小读取面（请只读这些，不要扩散到全仓）**：

1. `_bmad-output/审查/evidence-rv-g37/diff-ecfcc3f1-08fed737.patch` —— 全文（即 `ecfcc3f1..08fed737` 的 6 文件补丁）
2. `backend/app/services/review_service.py` —— `:105-320`、`:540-635`、`:2330-2600`
3. `backend/app/models/schemas.py` —— `:938-1080`
4. `backend/app/api/v1/endpoints/review.py` —— `:1025-1140`、`:1375-1495`
5. `backend/tests/regression/test_g3_7_truth_source.py` —— 全文
6. `_bmad-output/审查/codex-review-CARD-G3-7-r2.md` —— 上一轮复核结论（1 HIGH / 2 MEDIUM / 2 LOW）
7. `_bmad-output/验收单/UAT-CARD-G3-7-2026-09-06.md` —— §12 至 §15
8. `_bmad-output/审查/evidence-rv-g37/review-08fed737.md` —— **本卡的复审结论**（你要核的主要对象）

背景术语：该 concept 的「调度真相源」是节点 `.md` 的 frontmatter `fsrs_due`；`backend/data/fsrs_card_states.json` 及其内存镜像 `_card_states` 是**投影缓存**，已在代码中显式降格。`GET /review/fsrs-state/{concept_id}` 有一道「门锁」：判定该 concept 归 frontmatter 管时，本次读**不推进**投影缓存、不落盘。

## 二 作者自述，请独立核对（不要采信，请自己验）

1. **r2 的 5 条整改是否真的成立**（逐条，不要只看它改了代码就算数）。
2. **「成因与外审归因不同」是否属实**：作者称 r2 把缺陷成因归给 `_read_frontmatter_fsrs` 的 `except OSError` 分支，但实测那条分支不被触发，真实成因是 `Path.exists()` 自己吞掉 OSError 返回 False、于是走 `if path is None`。本卡在 `review-08fed737.md` §3.1 给了独立探针结论，请核这个判断本身。
3. **两处 TOCTOU 的五项定级**（`review-08fed737.md` §五）是否站得住：结论是两处**阻断级都为 0**，一处归后续键化卡、一处归退役卡。
4. **pyright「基线 41 → 最终 38、本卡新增 0」这套方法是否闭合**（`review-08fed737.md` §3.2、§七）：作者用的是基线树诊断多重集对照，理由是行号交集对「改契约让新错落在没动过的行」这一类失明。
5. **本卡自己的结论有没有过宽或过窄**：特别是 §2.1 判为「残留（LOW）」的两条、§四 判为「新引入缺陷（LOW）」的文档数字、§八 判为「主干既有、非本卡引入」的那条 OpenAPI 快照不同步。

## 三 请按重要性排序回答的问题

1. **`_node_lookup_is_blinded`（`review_service.py:169-216`）是否引入了反向缺陷** —— 即把「确实没有这个节点」判成「看不见」，从而让门锁永久拦死某类 concept_id？正控 `test_missing_node_is_still_reported_as_absent` 是否真的承重（改坏被测逻辑它会不会红）？该函数按 errno 分流：`FileNotFoundError` / `NotADirectoryError` → 继续找；`ValueError` → 判「确实没有」；其余 `OSError` → 判「看不见」并 fail-closed。请检查这个分流在各种真实输入下是否都给出正确一侧。
2. **`08fed737` 对 `_read_frontmatter_fsrs` 里 `except ValueError`（`:267-270`）的处置，是否会让某类合法的 concept_id 被永久放行**（即本该拦却放行）？
3. **TOCTOU (a) 的「后果有界」论证是否成立**：作者主张「下一次 GET 必然读到 frontmatter、正确拦截并报分歧」。请核这条链路：缓存命中分支（`:2570` 起）会不会再次写盘？`_unpersisted_concepts` 与脏标记会不会让那张被写入的默认卡固化成别的状态？作者还提出措辞应收紧为「不会**静默**固化」（卡本身确实留在缓存里）—— 这个区分是否必要且准确？
4. **三口径计数与文档漂移**：测试文件实数 21、两份 docs 写 20、上一轮外审正文写 18。本卡结论是：18 在其绑定版本上准确，21 是当前真值，20 是**同一个 commit 内**写错的（18+3=21 被写成 20）。请核这个归因。
5. **证据 rc 缺失对「通过」声明的影响**：上一张卡的 29 份证据里，末行带有效 `rc=<数字>` 的是 0 份，另有 2 份末行是空的 `rc=`。本卡判定它们只能作「跑过」的旁证、不能作「通过」的依据。这个判定是否恰当？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与判断依据。
**请把「已核实成立的部分」单列一节**（不要只列问题）——本卡需要知道哪些结论经你复核后可以承重。
若你认为本卡某条结论定级过轻或过重，请明说应该是哪一级、依据是什么。

## 五 边界

- **只读**：不要修改任何文件，不要运行测试，不要连接任何数据库或网络服务。
- 不评价后续卡的设计（G3-5 键化、mastery 域收敛、`save_card_state` 退役）——那些是本批其他卡的地盘。
- 不需要给出攻击方法或利用步骤；本请求要的是「这段整改是否成立、这份复审结论是否站得住」的判断。
- 本仓 Python 版本为 3.14.4；`ruff` 配置 `line-length = 120`。
