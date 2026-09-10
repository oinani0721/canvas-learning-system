# 独立复核请求 — CARD-G3-7-R2（第十三批 · 车道 card-u9-mastery）

你是独立复核者。请**只读**，不要修改任何文件，不要连接数据库，不要运行测试或变异脚本。
下面「作者自述」里的每一句都可能是错的 —— 请按你自己读到的代码判断，不要采信自述。

---

## 一 背景 + 最小读取面（写死，请只读这些）

**仓库树根**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery`
（分支 `card/u9-mastery`。本卡起点 = commit `8f7440ef`，即上一张卡 CARD-RV-G3-7 的末 commit。）

**本卡做了什么（一句话）**：把一个在 `backend/app` 内零调用方的公开方法 `save_card_state` 退役，
把原本按名引用它的两条回归测试改指真实持久化通道 `_save_card_states`；给 mastery 侧的 FSRS 字段
补「这是投影不是调度真相源」的标注并新增一道写边界门；另外产出一份消费方 census。

**请读的东西（不多不少）**：

1. 本卡 diff：
   `git diff 8f7440ef HEAD -- . ':(exclude)_bmad-output'`
2. HEAD 版 `backend/app/services/review_service.py` 的这几段：
   `:105-130`（`_CARD_STATES_FILE` 常量与其上方的降级注释）、
   `:520-640`（`_load_card_states` 与 `_save_card_states` 全文）、
   `:2330-2400`（`load_card_state` 与退役留下的注释块）、
   `:2400-2500`（`get_fsrs_state` 一带，含它对 `load_card_state` 与 `_save_card_states` 的调用）
3. HEAD 版 `backend/app/services/mastery_engine.py`：`:270-370`（`_fsrs_update` 全文含 docstring）、`:660-700`
4. HEAD 版 `backend/app/services/mastery_store.py`：`:1-120`
5. HEAD 版 `backend/tests/unit/test_review_service_fsrs.py`：`:580-650`、`:720-780`
6. HEAD 版 `backend/tests/unit/test_mastery_fsrs_projection_boundary.py`：**全文**（本卡新建的门）
7. `_bmad-output/审查/evidence-g37r2/census-20260908T073936.md`（消费方 census 定表）
8. 主 spec：`openspec/specs/concept-identity/spec.md`（**未改动**，与 `git show 8f7440ef:openspec/specs/concept-identity/spec.md` 逐字相同）
9. `docs/fsrs-truth-source-d0-revision.md`：`:55-90`

（行号是本次改动**之后**的实测值；若与你读到的略有出入，以文件实际内容为准。）

---

## 二 作者自述 —— 请独立核对，不要采信

以下四条是作者的主张。请逐条判断它是否成立，并指出证据在哪一行。

1. **退役 `save_card_state` 后，G-FAKE-007 防复活锁的覆盖面没有变窄。**
   自述理由：被删的方法只是 `_save_card_states` 的一层转调，锁改指被转调者后，
   原调用路径上仍然存在的每一行都还在用例的执行面内。
   请核对：改后的 `test_card_state_persist_paths_touch_no_memory_client` 是否**仍然**能在
   「幻影 LearningMemoryClient 调用被重新引入」时变红？有没有哪条原本被覆盖的路径现在漏掉了？

2. **census 的「在线消费方 = 1」这个口径自洽，且结论没有比证据宽。**
   请核对 `census-20260908T073936.md` §0 的定义与 §一 的取数是否同源；
   特别是：把所有权模块 `review_service.py` 排除、同时把「经所有权模块 API 间接读写」算作消费，
   这两条规则合起来会不会让 N 这个数在某个方向上恒定（从而失去判别力）？
   §七 的不可证边界有没有把「本 census 没看见」写成「不存在」？

3. **新门只禁写、不禁读 frontmatter，边界写死了，不会误拦合法的读。**
   请核对 `test_mastery_fsrs_projection_boundary.py` 里 `BANNED_WRITE_CALLS` 与
   `ALLOWED_READ_CALLS` 的划分，以及 `_open_is_write` 对 `open()` 的处理
   （mode 非字面量时按写处理）。有没有哪种**正常的读**会被这道门判成写？
   反过来，有没有哪种**真实的写**会从这道门下面走过去而不被记为命中？

4. **两条负控真的打在了它们点名的那一道断言上。**
   负控脚本在 `_bmad-output/审查/evidence-g37r2/negctl-N1N2-*.txt` 有完整输出：
   N1 = 把 `mastery_store.py` 的锚点句临时换成别的词；N2 = 在 `_fsrs_update` 末尾临时插一行写盘。
   判定用的是「rc==1 且 失败 nodeid 是点名那条 且 失败正文（只取 `^E` 开头的行）含点名断言串」。
   请核对：这个判定会不会被**更早的防线**或**语法不合法的负控输入**喂饱，
   从而把一次并非由被测断言造成的失败记成「击杀」？

---

## 三 请回答的问题（按重要性排序）

1. 删掉一个「静态 grep 看不到调用方」的方法，有没有可能打断某条**动态/反射**调用链
   （例如 `getattr(svc, "...")`、字符串派发、插件式注册）？本卡只做了静态 grep。
2. 改后的那两条测试，是不是只是「换个名字继续绿」，而实际锁住的东西变少了？
   请特别看 `test_save_card_states_returns_false_when_file_write_fails` 断言的语义是否与改前等价。
3. 行为门 `test_fsrs_update_does_not_write_review_projection` 的两个前提
   （`_CARD_STATES_FILE` 的 patch 生效、`fsrs_manager` 可用）如果不成立，
   这道门会不会静默变成一道恒真的门？门内自带的正控与「跑到底」断言够不够挡住这一点？
4. docs 与 spec 的处置有没有把「登记」写成「已解决」？
   具体看 `docs/fsrs-truth-source-d0-revision.md:68` 的四写点表 ④ 行、
   `docs/known-gotchas.md` 的 G-TRUTH-001 与 G-FAKE-007 两行。
   注意主 spec **没有**被改动（工具拒绝让一个 capability 变成零条要求，本卡按移交处理）。
5. 「本卡未证明什么」的声明有没有覆盖真实边界？尤其是 TOCTOU 与 mastery 侧漂移这两项。

---

## 四 输出格式

请用下面的分级，每条给 `file:line`：

- **BLOCKER** — 数据丢失 / 安全 / 会让线上出错的缺陷
- **HIGH** — 判据不成立、结论比证据宽、覆盖面实际变窄
- **MEDIUM** — 措辞或登记不准确、门的强度不足
- **LOW** — 可读性、命名、注释

最后单列一节 **「已核实成立的部分」** —— 你实际读过并确认无误的主张，逐条列出。
如果某条你没有足够信息判断，请明说「未核实」，不要归入上面任何一级。

---

## 五 边界

- 只读；不连数据库；不运行测试；不运行任何脚本。
- 不评 CARD-G3-5 的键化实现（那是下一张卡 U9-C 的面）。
- 不评 `backend/app` 的 pyright 存量报错（归 U1/U2 的阶段 2；本卡对它带存档跳过 hook，
  并用基线树多重集对照证明 0 新增，证据在 `evidence-g37r2/pyright-multiset-*.txt`）。
- 不评 `test_mastery_fusion.py::TestPearsonCorrelation::test_no_correlation` 这条红
  （主干既有，属 U11-C 的面）。
