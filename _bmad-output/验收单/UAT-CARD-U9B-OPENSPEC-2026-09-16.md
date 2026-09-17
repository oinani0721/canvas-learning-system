# UAT — CARD-U9B-OPENSPEC concept-identity 悬空 Requirement 退役替代

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-U9B-OPENSPEC]` · 车道 `card-t4-g3`（本车道第 3/4 张）
> PREV（T4-B CARD-G6-10 末 commit）= `02f59e5f9b52c1431f42c0bd59b3c7784f4d4cbe`
> commit 链 = `af4793bc` → `1c8d315f` → `86b9aed8` → `52afdb9b`（终审绑定）
> 处置口径 = 设计稿 §4 T4-C「补一条替代 Requirement 让 archive 过」（覆盖 UAT-CARD-G3-7-R2 §8.5
> 当时「分支乙：仅登记移交、spec 一字未动」的裁定）

---

## 〇 卡文事实核对（开工逐条实测）

| 卡文 §〇 | 实测 | 结论 |
|---|---|---|
| validate --strict 改前**本就 PASS**（非本卡鉴别裁判） | `Specification 'concept-identity' is valid` | ✓ |
| spec 现状 1 Requirement / 3 个 4 井号 Scenario / 0 个 3 井号 / 3796 字节 | 1 / 3 / 0 / 3796 | ✓ |
| 双桶模型在生产代码零命中 | `git grep -nE '_legacy_card_states|is_uuid_v4' -- backend/app` = **0** | ✓ |
| 公共方法 `save_card_state` 已退役 | `grep -nE 'def save_card_state\b'` rc=1（不存在） | ✓ |
| `_save_card_states` 是唯一真实持久化通道 | `async def _save_card_states` 在 `:920` | ✓ |
| 三文件裸名字 3 / 1 / 1 | spec 3 / A6 1 / test_g3_7 1 | ✓ |
| CLI = 1.2.0 | 1.2.0 | ✓ |
| 基线 `unit-red-baseline-08100483.txt` = 64 | 64 | ✓ |

⚠️ **一条卡文口径漂移（见 §五 台账 ①）**：卡文 §二 的
`cd "$SBD" && npx --no-install openspec …` **跑不通** —— `npx` 从 CWD 解析 `node_modules`，
仓外直接报 `could not determine executable to run`（已实测）。改用本地已装 CLI 的**绝对路径**
`<repo>/node_modules/.bin/openspec`（**未装任何包**，符合「批中禁装」）。

---

## 一 完成条件逐条

| 条 | 内容 | 结果 |
|---|---|---|
| (a) | 第 0 分钟 + 基线 64 + CLI 1.2.0 + `git status` 空 | ✅ |
| (b) | **先红**：仓外 scratch 复现 archive blocker | ✅ 见下 |
| (c) | 改 spec（替代 Requirement） | ✅ 1 Requirement + **5** 个 4 井号 Scenario |
| (d) | **后绿**：validate + archive 证 | ✅ 见下 |
| (e) | 两处裸名字更正（先红后绿归零） | ✅ 3/1/1 → 0/0/0 |
| (f) | 地盘核 ⊆ 3 文件 | ✅ 恰 3 个 |
| (g) | test_g3_7 不破 | ✅ ast OK / collect-only 21 tests / 0 import 错 |
| (h) | tests/unit diff 只许 `<` | ✅ base 64 / close 64，diff 空 |
| (i) | `ConceptState.fsrs_*` 只登记 | ✅ `backend/app/` diff = 0 行 |
| (j) | 硬边界 | ✅ 见 §六 |
| (k) | Codex 多轮至 B/H = 0 | ✅ 4 轮，终轮 **0/0/0/0** |
| (l) | 验收单 + 独立 commit + 不 push | ✅ 本文件 |

### (b) 先红（`evidence-u9b-openspec/before-archive-20260915T235906.txt`）

在仓外 `mktemp -d` 拷贝内经 CLI 建退役 change（`## REMOVED Requirements` + Reason + Migration），
`archive -y` 输出：

```
Validation errors in rebuilt spec for concept-identity (will not write changes):
  ✗ Spec must have at least one requirement
Aborted. No files were changed.
```

- `ARCHIVE_RC=0` —— **中止却退 0**，卡文 §〇 预告的陷阱已避开：判据用 sha 不用 rc。
- 主 spec sha 前后**逐位相同**（`e5c5c899…` → `e5c5c899…`），Requirement 计数仍 1。

### (d) 后绿（`after-archive-final-*.txt`）

改后树拷到新 scratch，建 `## MODIFIED Requirements` re-state change，`archive -y`：

```
Applying changes to openspec/specs/concept-identity/spec.md:
  ~ 1 modified
Specs updated successfully.
Change 'restate-concept-identity' archived as '2026-09-15-restate-concept-identity'.
```

- blocker 文本命中 **0**；主 spec sha **变了**（证明 archive 真写了，不是又被中止）；
  Requirement 计数仍 1（spec 未变空）。
- **绑定自证**：scratch 输入 sha 与工作树 `spec.md` sha **逐位相同**（`4fb92b1a…`）——
  这份后绿证的就是入库的那份内容，不是别的副本。
- 真实树 `openspec/changes/` 的 `git status` = **0 行**（archive 只在仓外跑，零污染）。

---

## 二 替代 Requirement 是怎么写出来的（本卡最要紧的一段）

替代 Requirement 必须**只陈述已实现、可在 `review_service.py` 验证**的不变式，
发明契约 = 违反 DD-01/DD-04，而这恰恰是被替换那条 Requirement 犯的错。为避免用「读一遍代码
+ 凭印象下笔」换一条新的悬空 Requirement，不变式是这么采的：

**219-agent 工作流**（`5 视角独立读码 → 每条不变式派 3 个不同镜头的反驳者 → 完整性批评`）：

- 5 个视角（序列化契约 / 原子性与并发 / 作用域与身份 / 在 FSRS 体系里的地位 / 反面陷阱）
  各自读 `review_service.py`，产出 **71 条**去重候选 + **72 条**「不保证」清单；
- 每条派 3 路反驳（逐行核对是否措辞过宽 / 找反例执行路径 / DD-13 名实一致），
  **拿不准一律判 refuted**；
- 结果只有 2 条原样存活 —— 但被否的 69 条里带回 **210 条收窄后的正确陈述**，
  那才是真正可用的材料（判据故意从严，产出的是精度而不是通过率）；
- 完整性批评再补 8 条「所有视角都漏了」的保证 + 9 条「不保证」。

最终 Requirement 只采用**经代码复核存活或收窄**的陈述，并在 §三 逐条列出它**不**保证什么。

---

## 三 Codex 轮次（gpt-6-astra · ultra · codex-cli 0.153.3）

| 轮 | 绑定 SHA | B / H / M / L | 处置 |
|---|---|---|---|
| r1 | `af4793bc` | 0 / 0 / 1 / 2 | 三条整改 → `1c8d315f` |
| r2 | `1c8d315f` | 0 / 0 / 2 / 2 | 四条整改 → `86b9aed8` |
| r3 | `86b9aed8` | 0 / 0 / 0 / 1 | 一条整改 → `52afdb9b` |
| r4 | `52afdb9b` | **0 / 0 / 0 / 0** | ✅ 终审，绑最终代码 HEAD |

四份存档首部三字段（`模型` / `reasoning_effort` / `codex`）**全齐**（协议 §2.1）；
旧模型名 `gpt-5.6` 命中 **0**。

### 三.1 四轮里最值钱的三条

1. **r1 M1 —— 我抄了代码注释，而注释本身过宽。** 我在给 agent 的 prompt 里写着
   「docstring 说的和代码做的不一致时以代码为准」，然后自己把生产注释
   「全量快照已落盘 → 所有历史写失败的 concept 同时被治愈」写进了 Requirement。
   实际：`clear()` 是**无条件**的、不核对条目是否真在本次快照里；作用域失败的值从没进内存、
   编码失败的值已被回滚，后续快照根本不含它们。**清的是标记，不是数据。**
   讽刺的是工作流自己的存活项 `success-clears-all-dirty-markers` 早就写明了这一点，
   是我合成时让代码注释的措辞盖过了验证结论。
2. **r2 M2 —— 漏掉的那条恰好是本 capability 的本职。** 脏标记身份是
   `(vault_id, concept_id)` 而非裸 `concept_id`，否则 vault A 的 `c` 写盘失败会让 vault B 的
   **同名** `c` 被误报 `persisted=False`。一个叫 `concept-identity` 的 capability，
   漏掉的正是「同名 concept 的身份要带 vault 维」。
3. **r2 L1 —— 卡文的字面指令会制造新的名实不符。** 见 §四。

---

## 四 ⛔ 与卡文字面指令的一处偏离（依证据执行，交主 session 裁）

**卡文 (e) 要求**：`test_g3_7_truth_source.py:14` 的 `save_card_state` → `_save_card_states`，
并称「描述的 decision.md 裁定④ 语义不变」。

**实读 `_bmad-output/审查/evidence-g37/decision.md` 后，该前提不成立**：

- 裁定④ 的标题是 `## ④ review_service.py:2086 save_card_state → :2119（backend/app 零调用方）`，
  裁定 = **隔离（保留定义 + 标注非真相源 + 登记 G-PIPE 待退役）**，讲的是那个**公共**方法；
- 同文件「统一动作」那行把 `_save_card_states` 与 `:1087` / `:2119` / `:2189` **并列**为
  另外的锚点 —— 它不是裁定④ 的主语。

照卡文字面改，会把「已退役的公共入口」错绑成「活跃的共用落盘方法」= **新的 DD-13 名实不符**，
而本卡的目的正是消灭名实不符。故改用中性且为真的表述：

```
③ mastery grade / ④ 已退役的公共单卡保存入口 → 隔离（仅注释，无行为改动，不在本文件覆盖）。
```

裸名字同样归零，且陈述为真。**Codex r3 独立复核该偏离：「依证据偏离卡文字面指令正确，无需回退」**。
请主 session 裁是否认可，并回写卡文 (e)。

---

## 五 DoD-3 双段

### 5-A Claude 已代验（技术指标，你不必跑）

| 判据 | 结果 | 存档 |
|---|---|---|
| 先红 archive blocker | 文本命中 1 + `Aborted` + 主 spec sha 逐位不变 | `before-archive-*.txt` |
| 后绿 archive | 成功归档、blocker 0 命中、sha 变、输入 sha == 工作树 | `after-archive-final-*.txt` |
| validate --strict | `is valid` | `validate-r4-*.txt` |
| 结构门 | 1 Requirement / 5 个 4 井号 Scenario / **0** 个 3 井号 | 同上 |
| 裸名字归零 | spec 3→0 / A6 1→0 / test 1→0 | `barename-zero-*.txt` |
| 归零验伪锚 | 同一 grep 对地盘外 `test_review_service_fsrs.py` 仍命中 **2** | 同上 |
| A6 ↔ 主 spec Scenario 名 | **程序化**逐条比对 5/5 一致（非肉眼） | `validate-r4-*.txt` |
| `## Purpose` 未动 | 占位符 1 命中 | 同上 |
| 地盘核 | 恰 3 文件；验伪锚：去 exclude 后多出 12 条 `_bmad-output` 路径 | `territory-*.txt` |
| 越界自证 | `backend/app` / `openspec/changes` / `models` / `fsrs_bridge` / `decay_beta` diff 全 **0 行** | 同上 |
| test_g3_7 | ast OK；`--collect-only` 21 tests、0 import 错 | `collect-g37-*.txt` |
| tests/unit | base 64 / close 64，diff **空** | `unit-close-*.txt` + `base/close.nodeids` |
| Codex 终轮 | B0 / H0 / M0 / L0，绑 `52afdb9b` | `codex-review-…-r4.md` |

### 5-B 你来验（零技术词）

> 我打开那份写着「这块功能该怎么表现」的说明，发现它描述的做法和现在这套系统**根本不是一回事**
> ——照着它去验收，只会验出一堆对不上的结论。现在这份说明换成了系统**实际**在做的事：
> 存进度的时候是整份重存、先写到一个临时的地方确认没问题再换上去、认不出是哪门课的时候宁可
> 不存也不乱存、存失败了会退回原样、以及一门课存失败不会连累另一门课里同名的那一块。
> 我感觉这份说明终于可以拿来当验收标准了，而不是一段没人敢信的旧描述。

**felt-sense**：以前看到这类「规格文档」是有点心虚的——不知道它讲的是现在的系统还是三个月前的
某个设想，于是干脆不看。现在这一份，每句话都能在系统里对上号，那种「文档和实物两张皮」的
别扭感没有了。

---

## 六 本卡未证明什么（≥4）

1. **未证明 change 目录的完整 CLI 往返在车道树真实 commit** —— `openspec/changes/*/` 被
   `.gitignore:188` 忽略，archive 证明只在仓外 scratch 跑。
2. **未在真实仓内跑 `openspec archive`**（会往 `changes/archive/` 写 = 越地盘），
   故「主 spec 由 CLI 合入」只在 scratch 验证，真实树是**手改**。
3. **未证明替代 Requirement 的契约在运行期被真实调用覆盖** —— 只静态引 `review_service.py` 的
   符号，未跑 FSRS 端到端；5 个 Scenario 目前**没有对应的自动化测试**（Codex 只判定它们
   「可以写成断言」，不是「已经有断言」）。
4. **未证明 `_save_card_states` 的并发/原子写在真实环境的行为** —— 硬边界只读，未连任何库，
   未做多协程压测，未验 `replace` 在跨设备/权限异常下的实际表现。
5. **未证明 `test_g3_7_truth_source.py` 全量绿** —— 只做了 `--collect-only`（21 tests 收集成功），
   未跑完整 regression。
6. **未覆盖 `_save_card_states` 的失败残留面**：工作流实测到 `write_text` 成功而 `replace` 失败时
   `.json.tmp` 会**残留**（方法内 `finally`/`unlink`/`fsync` 三者零命中），替代 Requirement
   **刻意不写**这条（它是缺陷不是契约），但也因此没有任何门守着它。
7. **未证明 `## Purpose` 占位符何时会被填** —— 用户已裁定不在本卡 scope。
8. **未证明 archive 在真实树上不会产生别的副作用**（只在 scratch 上观察到「写主 spec + 移 change
   到 archive」两件事）。

---

## 七 台账待登记条目（≥4，**台账只主 session 改**）

1. **卡文 §二 口径更正**：`cd "$SBD" && npx --no-install openspec …` 跑不通（npx 从 CWD 解析
   `node_modules`，仓外报 `could not determine executable to run`）。仓外 scratch 必须用
   **绝对路径** `<repo>/node_modules/.bin/openspec`。请回写卡文/手册。
2. **⛔ 与卡文 (e) 字面指令的偏离，请裁**：`test_g3_7:14` 未按卡文改成 `_save_card_states`，
   改为「已退役的公共单卡保存入口」——理由与 `decision.md` 原文见 §四，Codex r3 独立复核认可。
3. **concept-identity 悬空 Requirement 已由替代 Requirement 退役**（手改主 spec，非 CLI archive）；
   退役 change 草稿仍在 `evidence-g37r2/openspec-draft-retire-fsrs-legacy-bucket-spec/`，
   **未用其 REMOVE 方案**，改用替代方案。
4. **两处裸名字已归零**（A6 / test_g3_7）；地盘外 5 处（`test_review_service_fsrs.py` ×2 退役防
   复活断言、`fsrs-truth-source-d0-revision.md` ×1、`known-gotchas.md` ×2）与 `changes/archive/`
   档案 6 处**故意保留**，判据因此必须收窄到三文件，否则全仓 grep 恒红。
5. **`ConceptState.fsrs_*`（`mastery_state.py:69` / `:87-92`）标注需求移交** —— `models/**` 本批
   零写者，本卡一字未碰（`backend/app` diff = 0 行）。
6. **建议主 session 裁**：是否需在真实树补跑一次 CLI archive，把这次退役正式归档进
   `openspec/changes/archive/`（越本卡地盘，故未做）。
7. **新 Requirement 的 5 个 Scenario 目前无自动化测试** —— 建议另立卡把它们落成
   `tests/regression` 断言（尤其第 5 条跨 vault 脏标记，它锁的是 CARD-G3-5 的修复）。
8. **`_save_card_states` 的 `.json.tmp` 残留**（`replace` 失败 / `write_text` 编码失败两条路径，
   方法内无任何清理代码）—— 本卡只在证据里记录，未写进契约、未修，建议登记为独立缺陷卡。
9. **Codex 四轮存档路径与绑定 SHA** 见 §三 表；`*.stderr` 未入库。

---

## 八 收尾状态

- **未 push**（`origin/card/t4-g3` 不存在，无 upstream）。
- 工作树干净，T4-D CARD-U9C-EVAL 可直接开工。
- `*.stderr*` 未入库；台账未改；真实树 `openspec/changes/` 零污染。
- 下一步：**复核第十四批 T4**。
