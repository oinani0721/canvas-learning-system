# 独立代码复核请求（round-2）— CARD-G3-3-R2-writer-boundary

## 一 背景与最小读取面

仓库根（只读）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance`

round-1（存档 `_bmad-output/审查/codex-review-CARD-G3-3-R2-writer-boundary.md`，绑定 `609ce455`）
给出 BLOCKER 0 / HIGH 0 / MEDIUM 5 / LOW 3。作者逐条独立复现后做了整改（L7 实测不砖化，
登记不改；其余全部修改）。本次请复核**整改后的最终态**。

**请只读以下范围**（不需要读别的文件；不要运行任何写操作）：

1. `git diff 609ce455 b060259b -- . ':(exclude)_bmad-output'` —— round-1 整改的全部代码改动
2. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `:290-420`
   （写点门重构：`float()` 前置 + `except (OverflowError, ValueError)` 走同一句拒因——round-1 LOW-6；
   `_harness_tree` 的引号正则改**非贪婪**、裸值 `#` 一律视为注释起点——round-1 MEDIUM-1；
   「不接受数字串」的理由从「strip 重开口子」更正为「类型契约」——round-1 补充判定）
3. 同文件 `:1480-1600`（`:1499/:1513/:1587` 三行仍未改，门在它们上游）
4. `backend/app/services/learning_event_log.py` 的 `:150-290`（形态门本体未动）
5. `backend/tests/regression/test_g3_2_review_ledger.py`：
   - `:6294-6335`（转正测试的 docstring 措辞更正——round-1 LOW-8）
   - `:6740-6800`（零写判据重构——round-1 MEDIUM-2）
   - `:6800-` 起的新增段（两端点对照——round-1 MEDIUM-3；引号+注释回归、注释掉键回退——MEDIUM-1）
6. `backend/tests/regression/test_learning_event_log.py` 的 `:77-` 起全部新增段：
   - 拒绝用例改查 `caplog` 里 `append_event` 自己打出的形态门 warning——round-1 MEDIUM-4
   - 假值分层用例（空判拒、形态门不拒）——MEDIUM-4 的另一半
   - 一致性门的关键码点表逐段覆盖 + 深位孪生体——MEDIUM-5
7. `_bmad-output/审查/evidence-g33r2/low7-scientific-notation-probe-*.txt`（L7 不砖化的实测存档）

## 二 作者自述（round-1 整改声明）——请独立核对，不要采信

1. **M1**：引号正则 `^(['\"])(.*?)\1\s*(?:#.*)?$` 非贪婪后，`"/valid/repo" # use "main"`
   解析出 `/valid/repo`；裸值 `#` 一律视为注释起点后，`harness_tree: # reset` 视同空值回退。
   代价：**裸值路径含 `#` 的用户必须加引号**——这与 YAML 自身规则一致，作者认为可接受。
2. **M2**：零写判据改为全树 `(相对路径 → (类型, 大小, sha256))` 内容指纹逐条比对；
   豁免收窄为两个**精确路径**（`.locks` 目录 + 推算出的锁文件名
   `sha1(realpath(NODE))[:16]`），并断言锁文件 0 字节；另加判据自证探针
   （写一行探针文本后指纹必须变，防指纹函数本身失明）。纯「建后即删」的临时文件
   如实声明为未覆盖（它不改变最终状态）。
3. **M3**：两端点对照。A 端把 vault 父目录的 `backend/` 改名为 `backend-disabled` 并
   **先断言**缺省路径失败（前提成立性检查）；B 端只加一行指向 alt 树的配置必须成功。
   alt 树自带独立的 `.venv` 与 `validate_learning_events.py` symlink。
4. **M4**：拒绝用例改查 `caplog` 中 `append_event` 打出的「拒绝形态非法的 event_id」
   那句 warning——它只在形态门分支产生（空判打「拒绝空 event_id」，未知类型打
   「拒绝未知 event_type」，三者文案互不相同）。假值另有分层用例钉住由空判拒。
5. **M5**：一致性门补三件事：非法样本的**深位孪生体**（坏码点在 45+ 字符处，
   挡截断式遍历）；关键码点表**逐段**覆盖（含 `0xFDD0/FDEF` 与三个平面的末两码点，
   挡「两侧同时删同段」）；误拒方向验伪锚（ASCII/中文/emoji/CJK 扩展 B 不得入集）。
6. **L6**：`float()` 前置；`OverflowError/ValueError` 捕获后置 `inf`，与真 `inf` 走同一句拒因。
7. **L8**：写入分支保留，但 docstring 措辞更正为：当前不可达性由拒绝面用例组间接保证，
   该分支的独立价值在**语义演化**（门将来合法化时）场景。
8. **L7 未改**：实测 `1e-6` 首写/重跑/后续评分/validator 全 rc=0（不砖化），按你的原判
   「不属于本次新增的注入漏洞」登记不改。

## 三 请按重要性排序回答的问题

1. M1 的修复是否引入新的错误形态？特别看：引号不匹配的裸值（如 `"unterminated`）、
   值中间出现引号（如 `a"b`）、以及「裸值含 `#` 必须加引号」这条新规则是否在
   `SKILL.md` 的说明文字里已如实声明。
2. M2 的指纹判据还有没有盲区？特别看：symlink 目标变化（rglob 对 symlink 的枚举行为）、
   目录本身的内容变化（指纹只记 `(“dir”, None, None)`）、以及改名 `backend-disabled`
   在 A/B 两端点之间是否真的不干扰 B 端。
3. M3 的两端点对照里，A 端 `backend-disabled` 留在原地没有恢复——它会不会污染同一 vault
   里后续的其它用例（fixture 是函数级的，理论上不会，请核对）。
4. M4 的 caplog 判据：那句「拒绝形态非法的 event_id」warning 是否**真的**只在形态门分支
   产生？`append_event` 的其它失败路径有没有可能打出同一句。
5. 写点门重构后的逻辑（try/except + `_scn_f`）：对 `float('nan')`/`float('inf')` 输入、
   超大 int、`bool`、字符串、`None` 的行为是否都落在预期分支？`_scn_f is None` 同时
   表示「非数字类型」——有没有某个合法输入会被误归到拒？
6. round-1 你指出「入口到 `:1499` 之间的中间控制流不在许可读取面」。本轮许可面仍然
   不含 `:420-1480` 全段——如有可能请基于 diff 说明该段**本次未被改动**（卡文硬边界
   禁改 `q_()` 本体与拼接链，判据 ④ 只删 REPO 一行），在此前提下你对「唯一上游」
   声明的置信度如何，还差什么才能补全。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：

- 级别
- `file:line`
- 一句话说明问题
- 一句话说明如何观察到它（走哪条路径、什么输入下会显现）

没有问题的级别请明确写「无」。

## 五 边界

- 只读复核，不要修改任何文件，不要运行测试或任何写操作。
- 不要连接任何数据库或网络服务。
- 不评审 `start-exam-board` 与 `ai-linked-doc` 写点（登记项，不在范围）。
- 不评审变异 harness 全量覆盖率（U8-B 的面）。
- `_bmad-output/` 下除第 7 项存档与 round-1 存档外不必阅读。
