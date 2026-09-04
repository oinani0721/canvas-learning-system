# CARD-G2-4 round-4 定向复核（只读审查）

你是对抗性代码审查员。工作区根目录:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance

本轮是 CARD-G2-4 的 round-4 定向复核（回应你 round-3 的判决），不是全量审查。
只读, 不修改任何文件。

## 背景

你 round-3（_bmad-output/审查/codex-review-CARD-G2-4-round3.md）判「BLOCKER/HIGH 清零：否」:
1. **HIGH 残余**: 摘要只渲染顶层 f.metadata, nested struct 子字段 metadata 不参与 ——
   struct<x:int64> 仅子字段 metadata 不同的两张表 check_metadata=True 为 False 而
   schema_sha16 相同, 对账判同后 drop。
2. **MEDIUM**: ④ test_digest_equality_tracks_arrow_check_metadata 是死门 —— 你的
   「只按 value 排序、完全忽略 key」变异下 7 pair 全绿。
3. LOW×3: export_table 行号漂移（:290-295 → 实际 306-321）; 「297 collected」措辞;
   round-3 变异证据包不含 shasum 对照。

round-4 整改声明见验收单 §8.8（_bmad-output/验收单/UAT-CARD-G2-4-Lance旧表回退删除-2026-08-31.md）:
- 新增 `_render_field()` 递归渲染 struct/map/list 子字段（list value field 名字归一
  elem, 与 _LIST_ELEM_LABELS 同一已声明偏离; nullable/metadata 如实参与）;
- ④ pair 集 7→11（补 key-only ×2 + nested ×3）;
- 新增 ⑦ nested struct 子字段锁、⑧ list value field 锁;
- 机械变异 M-A(value-only)/M-B(no-recursive)/M-C(no-metadata)/M-D(no-elem-label)
  全部按预期变红, 还原 sha256 = cc5b098806bcf809c40e41877a53a4125ea26150ca014b742e8b1af9da704d05。

## 读取范围 (限定)

1. backend/scripts/archive_legacy_lance_tables_g24.py
2. backend/tests/unit/test_archive_legacy_lance_tables_g24.py
3. 验收单 §8.7-§8.10（同文件, 其余章节仅交叉核对时看）
4. 你 round-3 的存档 _bmad-output/审查/codex-review-CARD-G2-4-round3.md
5. evidence-g24/ 下 round-4 新增文件（a-judge-probe-round4.txt, c-mutation-red-round4.txt,
   post-fix-suite-round4.txt, comm-new-failures-round4.txt）

允许只读沙箱内用 backend/.venv/bin/python 与 backend/.venv/bin/pytest 实跑
（pytest 写 tmp 不算改工作区）。

## 任务

1. **round-3 HIGH 残余是否 CONFIRMED-CLOSED**: 用你 round-3 的原反例
   （struct<x:int64> 子字段 metadata {unit:cm} vs {unit:m}, 以及有 vs 无）实测
   _arrow_digest 是否给出不同 schema_sha16; 再实测 export_table 对账能否识别
   「回读丢失子字段 metadata」（你 round-3 的强制回读手法）。给证据行号。
2. **回归检查**: round-2 已 CLOSED 的 BLOCKER-1/2/3、HIGH-2/3 与 round-3 已确认的
   顶层 metadata 修复、⑤ 端到端 —— 本轮改动没有重开/削弱任何一条。
3. **专门审 ⑦⑧ 与扩展后的 ④ 是否死门**: 必须尝试构造「绕过它们仍全绿」的复现
   （在 /tmp 拷贝脚本改后跑）。至少尝试: (i) 递归缺失但 struct 当扁平渲染;
   (ii) 忽略 key 的其它变体; (iii) elem 归一只在顶层、递归层不归一的变体。
   给不出复现才算有效。注意 ⑤ 仍是正向对照, 不拿它的存活当死门证据。
4. LOW×3 处置核对（§8.8 末段与 §8.2 的更正是否落实）。
5. 证据引用核对（round-4 四个新文件存在且内容与 §8.8 声明相符）。

## 输出格式 (严格遵守)

- 逐条: `1. round-3 HIGH 残余 … — CONFIRMED-CLOSED/STILL-OPEN` + 证据 file:line + 说明
- 回归检查逐条一行
- ⑦⑧④ 死门审查: 每条 `有效` / `死门` + 你尝试的复现路径
- LOW×3 处置: 已落实/未落实 + 证据
- 新问题按 BLOCKER/HIGH/MEDIUM/LOW 分级
- 末行必须是: `BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否`
