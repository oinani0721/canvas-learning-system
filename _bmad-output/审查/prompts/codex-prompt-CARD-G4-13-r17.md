# CARD-G4-13 r17 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 复核对象 = commit `5af89d03`（父 `66485acb`）；批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`。
> 只读复核，**不改任何文件**。

## ① 背景与最小读取面

goal 收尾要求「manifest status + 用户签字」但此前无受控通道。`5af89d03` 新增 `approve` 子命令：
三道前置（签名非空 / `verify_all` rc=0 / 无 pending verdict）+ 临时文件 `os.replace` 原子替换 +
换前对新内容复验；`MANIFEST_HEADER` 提取为常量（build/approve 共用）。现场：当前 103 pending 下
`approve` 被拒（rc=1）。

最小读取面：
- `git --no-pager diff 66485acb 5af89d03`
- `backend/scripts/gold_set_manifest_tool.py` 的 `MANIFEST_HEADER` / `build_manifest` 写盘段 / `approve_manifest` / CLI 段
- `backend/tests/regression/test_gold_set_manifest_g413.py` 的 4 条 approve 测试
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §二十五
- 证据：`_bmad-output/审查/evidence-g413/r18-*`

## ② 核对点

1. **approve 三道前置与原子性**：逐条构造反例复算（pending 存在 / 签名空白 / verify 红 / manifest 缺 /
   manifest 非映射 / 临时文件写入失败路径 / `signed_at` 非法值 / `checklist` 任意值）；替换是否真原子、
   失败时原文件是否逐字节不变；
2. **header 重构**：`build` 输出与重构前是否逐字同（对同一输入）；`header identical: True` 是否可复算；
3. **是否有新的放行/误拒**：`approve` 后 `verify_all` 是否仍 rc=0；`status` 只能是 approved/pending 的
   口径是否守住；重复 approve（已 approved 再签）行为是否合理；
4. 4 条新测试是否真判别、无空转；gate 86 / 目录级 1999 自洽；
5. UAT §二十五（含「用户 session 完整收尾链」）有无 overclaim。

## ③ 输出格式

逐条 **BLOCKER/HIGH/MEDIUM/LOW**（无则写「未发现」）+ `file:line` + 一句话复现思路；
一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」；末尾「本轮总评：B= / H= / M= / L=」。

## ④ 边界

只读；不改文件；不连 7691/7687/8011；不跑非 shadow runner；不评 G4-14/R-SLO/L-5/103 条语义。
