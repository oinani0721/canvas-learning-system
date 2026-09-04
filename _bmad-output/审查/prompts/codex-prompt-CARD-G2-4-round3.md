# CARD-G2-4 round-3 定向复核（只读审查）

你是对抗性代码审查员。工作区根目录:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance

本轮是 CARD-G2-4 的 round-3 定向复核, 不是全量审查。只读, 不修改任何文件。

## 背景

round-2 存档 _bmad-output/审查/codex-review-CARD-G2-4-G2-5-round2.md 的「CARD-G2-4 round-2」
判了 6 条: BLOCKER-1/2/3、HIGH-2/3 = CONFIRMED-CLOSED, 第 4 条 HIGH-1 = STILL-OPEN
(摘要 _arrow_digest 漏 Schema.metadata 与 Field.metadata, 仅 metadata 不同的两张表被
对账判同后 drop 源表)。

第八批 round-3 整改声明见验收单
_bmad-output/验收单/UAT-CARD-G2-4-Lance旧表回退删除-2026-08-31.md 的「## 八、第八批
round-3 整改 (HIGH-1)」一节: _arrow_digest 的 schema_repr 每字段追加 field metadata 的
确定性渲染 + 末尾追加 schema 级 metadata 渲染 (None/{} 归一为 meta=-, 非空按 key 字节序
排序, 每对 repr(k)=repr(v) bytes 不解码), 声称与 pyarrow.Schema.equals(check_metadata=True)
同语义 (顺序无关), 唯一有意偏离 = list 内层 item/element 标签归一。

## 读取范围 (限定, 不要读别的)

1. backend/scripts/archive_legacy_lance_tables_g24.py
2. backend/tests/unit/test_archive_legacy_lance_tables_g24.py
3. 验收单 §八 (_bmad-output/验收单/UAT-CARD-G2-4-Lance旧表回退删除-2026-08-31.md 的
   「## 八、」一节, 其余章节只在需要交叉核对时看)
4. round-2 存档 _bmad-output/审查/codex-review-CARD-G2-4-G2-5-round2.md 的 CARD-G2-4 部分

允许在只读沙箱内用 backend/.venv/bin/python 与 backend/.venv/bin/pytest 实跑验证
(pytest 写 tmp 不算改工作区)。

## 任务

1. **HIGH-1 是否 CONFIRMED-CLOSED**: 用 round-2 的最小反例 (同 x:int64 同数据, 仅
   schema/field metadata 不同) 实测 _arrow_digest 是否给出不同 schema_sha16; 再审
   export_table 的对账是否因此自动覆盖 metadata。给出证据行号。
2. **回归检查 round-2 已 CLOSED 的 5 条未被重开**: BLOCKER-1 (file:// 双解释)、
   BLOCKER-2 (DB 树外归档)、BLOCKER-3 (YAML/脚本 SHA)、HIGH-2 (canonical vault-id)、
   HIGH-3 (unknown_bare)。逐条确认本轮改动没有触碰/削弱其实现与回归锁。
3. **专门审 (b) 六条回归锁是否死门**: ① test_digest_distinguishes_schema_metadata
   ② test_digest_distinguishes_field_metadata ③ test_digest_equal_for_identical_and_key_order_permuted_metadata
   ④ test_digest_equality_tracks_arrow_check_metadata ⑤ test_apply_reconciles_and_drops_metadata_bearing_table
   ⑥ 既有 test_live_shaped_fixture_flags_bare_fingerprints / test_apply_exports_parquet_outside_db_then_drops。
   判死门的标准: 你必须**尝试构造**「把 metadata 渲染改掉/删掉之后这些测试仍全绿」的
   复现路径 (可在只读沙箱里把脚本拷到 /tmp 改后跑); 给不出这样的复现, 才能判门有效。
   注意验收单 §八已声明 ⑤ 是正向对照、变异下允许仍绿 (它锁的是 apply 不假红), 抓变异
   的门是 ①②④——审它们, 不要拿 ⑤ 的存活当死门证据。
4. 顺带核对验收单 §八的证据引用与实际文件是否一致 (evidence-g24/ 下各文件存在且内容
   与声明相符)。

## 输出格式 (严格遵守)

- 逐条列出: `1. HIGH-1 … — CONFIRMED-CLOSED/STILL-OPEN` + 证据 file:line + 一段说明
- 回归检查 5 条各一行: `CONFIRMED-CLOSED (未重开)` 或 `REOPENED` + 证据
- (b) 六锁死门审查结论: 每条 `有效` / `死门` + 你尝试的复现路径描述
- 如发现新问题按 BLOCKER/HIGH/MEDIUM/LOW 分级列出
- 末行必须是: `BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否`
