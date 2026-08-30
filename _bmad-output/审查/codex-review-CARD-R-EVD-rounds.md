# Codex 对抗审查存档 — CARD-R-EVD Release 证据目录与 manifest 规范

> **批次**: BATCH-2026-08-28-第五批 / CARD-R-EVD
> **审查者**: `codex exec --sandbox read-only`（codex-cli 0.147.0），静态只读 + 实跑校验器复算
> **base HEAD**: `13d44ac10f32d3c82deeedd55dbe9fe859fb7659`（`card/s8-ci`）
> **round-1 结论**: FAIL —— 2 BLOCKER + 4 HIGH + 3 MEDIUM（A/B/C/E 项 FAIL，D/F PARTIAL，G 硬边界 PASS）

## round-1 裁定与整改

| # | 级别 | 发现 | 整改 |
|---|---|---|---|
| 1 | BLOCKER | **路径穿越 + hash oracle**：`repo://../../../../etc/passwd` 被 `--verify-artifacts` 读取，checksum 不符时回显实际摘要 | 三重防线：schema 正则禁绝对路径/`..`/`~`/反斜杠 → A0 解析后 containment 检查（越界即拒）→ 逐级 symlink 拒绝跟随。A0 在**默认档也跑**（越界路径本身即不合格，不用等 `--verify-artifacts`） |
| 2 | BLOCKER | **空心 E5**：E5 + result=pass + rollback fail + 零 artifact + evidence 全悬空 + signoff 只有 `approved` 字符串 + SLO 只有 revision 字符串 → 结构 0 错、语义 0 错 | 补 5 条规则：S3 扩至 rollback、S9 要求实测、S11 E5 硬门（dogfood 跑满/零漏日/rc_sha 一致/恢复演练 pass）、S12 evidence 必须解析到 artifact、S2 扩至 `signoff.at`；schema 侧 `artifacts.minItems=1` + signoff if/then（approved 必带 user+at） |
| 3 | HIGH | artifacts 允许空数组 → L596 的 checksum 要求被架空 | `minItems: 1`；断言的 `evidence` 由 S12 绑定到已登记 artifact |
| 4 | HIGH | S9 只查非空字符串，与 §12.5 L592「J manifest 必须记录阈值与实测」冲突 | `slo` 改为结构化 `{manifest_revision, measurements[{metric,threshold,measured,method,meets,waiver}]}`；E3+ 强制 revision + ≥1 实测；未达标而判 pass 必须附用户 waiver（§12.5 降级规则） |
| 5 | HIGH | **示例 manifest 混入结案报告未证明的事实**，且 candidate `c823a35f`（06:21:32）晚于 `finished_at`（06:20）——它正是归档证据的那个提交，执行时尚不存在 | 改用父提交 `91383b1f`（05:30:03，执行窗口前最后一个提交）；新增 `provenance` 块（mode/reconstructed_from/unproven_fields），把 9 类推定字段逐条列明；起止时间改用三份归档文件的真实 mtime（06:12:24 / 06:20:16） |
| 6 | HIGH | 55 条测试假绿覆盖：基底 fixture 过于宽松，缺 E5/dogfood/路径逃逸/signoff 时间/rollback-pass 等负例 | 测试重写为 105 条：S1–S13 与 A0–A3 逐条负例、两个 BLOCKER 的**原样复现回归**、symlink 与目录 symlink、重复 JSON key、非 UTF-8、RC 完整性门、CLI 三档退出码；基底 fixture 顶部加**诚实声明**说明它是合成件、真实性由仓内示例件把关 |
| 7 | MEDIUM | 退出码不严格：顶层 `[]` 被判 exit 2（应为 exit 1）；编码/权限异常会 traceback；重复 JSON key 静默取后值 | 顶层非对象 → `[json]` 内容不合格（exit 1）；`UnicodeDecodeError`/`OSError` → ConfigError（exit 2）；`object_pairs_hook` 拒收重复 key |
| 8 | MEDIUM | workflow 只能证明"示例 lint 通过"，一份演示件让 CI 长绿 | 新增 `--require-complete <rc>` RC 发布门（J01–J10 齐全且全为 live 实录）；workflow 头部**诚实声明**本门的覆盖边界；示例件因 `mode=reconstructed` 按设计不计入任何 RC 完整性 |
| 9 | MEDIUM | README 裁剪表不完全诚实（artifact/签字标"原样"但可空可缺；SLO 裁剪未说明违背 L592） | 对照表逐行重写为「原样/加严/收窄」并标注加严点；新增「§12.5/§12.6 的额外硬门」一节；SLO 行改为"记录阈值与实测是强制的，只有**阈值定多少**归 R-SLO"；「已知边界」新增 SLO 不做数值比较的声明 |

**round-1 明确 PASS**：schema 通过 Draft 2020-12 metaschema；文件 SHA 与常量一致；结构层短路不产生 exit 0 假绿；硬边界 `test.yml` / `readme-claims.yml` / `backend/.gitignore` 相对 HEAD 零改动；三份归档 artifact 的 SHA/bytes 精确匹配；D5 判据、`partial`、UAT pending 与结案报告一致。

## 整改后自验（存档 `revd-evidence-2026-08-28/local-judge.txt`）

两个 BLOCKER 的**原样复现**现在都被挡：路径穿越在结构层即拒；空心 E5 在**结构层全合法**的前提下由语义层逐条点名 S2/S3/S9/S11/S12。105 条裁判测试在 backend venv 与 CI 等价环境（干净 venv，仅 `jsonschema`+`pytest`，python 3.9.6）双绿。
