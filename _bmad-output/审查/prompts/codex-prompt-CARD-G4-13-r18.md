# CARD-G4-13 r18 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 复核对象 = commit `97c71428`（父 `5af89d03`）；批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`。
> 只读复核，**不改任何文件**。

## ① 背景与最小读取面

r17 复核对 `5af89d03`（approve 子命令）报 **B=0/H=2/M=3/L=4**：H-1 测试写真题 manifest（目标态会覆写
真签名）、H-2 pending 门含 shadow 2 条 ⇒ 收尾链必卡；M-1 registry 缩水可签、M-2 临时文件异常逃逸、
M-3 重复签署覆写；L×4（--at/--checklist/测试判别力/证据）。`97c71428` 全数收口（tmp 隔离测试、
pending 门只扫 MAIN_SETS、registry 完整性、异常文案化、拒绝重复签署、参数校验、证据注记）。

最小读取面：
- `git --no-pager diff 5af89d03 97c71428`
- `backend/scripts/gold_set_manifest_tool.py` 的 `approve_manifest`/`_parse_iso_utc`/CLI 段
- `backend/tests/regression/test_gold_set_manifest_g413.py` 的 `_approve_fixture` 与 7 条 approve 测试
- `_bmad-output/审查/codex-review-CARD-G4-13-r17.md`（上一轮全文）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §二十六
- 证据：`_bmad-output/审查/evidence-g413/r19-*`

## ② 核对点（收口判定）

1. H-1/H-2 与 M-1/M-2/M-3、L-1/L-2 逐条复算（相对 r17 源码给「旧 → 新」结论；尤其：**真 manifest
   是否还会被任何测试路径写入**、shadow pending 场景是否真能签成、registry 缩水/重复签署是否真拒）；
2. 是否有**新**的放行/误拒/崩溃（`MAIN_SETS` 口径与 goal「103 条」是否一致；`rel_to_repo` 为 None 的
   边界；`--at` 合法面是否过窄/过宽；`finally` unlink 行为；`tmp.replace` 后 tmp 不存在）；
3. **端到端**：干净副本上 勾选→apply-verdicts→build→approve 全链是否走通（只读复算即可）；
4. gate 89 / 目录级 2002 自洽；7 条 approve 测试判别力（含旧 4 条改写后的判别性）；
5. UAT §二十六 有无 overclaim；§26.3 收尾链是否名副其实。

## ③ 输出格式

逐条 **BLOCKER/HIGH/MEDIUM/LOW**（无则写「未发现」）+ `file:line` + 一句话复现思路；
一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」；末尾「本轮总评：B= / H= / M= / L=」。

## ④ 边界

只读；不改文件；不连 7691/7687/8011；不跑非 shadow runner；不评 G4-14/R-SLO/L-5/103 条语义。
