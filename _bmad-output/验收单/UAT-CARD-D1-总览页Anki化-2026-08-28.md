# 验收单 · CARD-D1 总览页 Anki 化（库→白板→到期时间三级视图）

> **批次**: BATCH-2026-08-27-Anki化与诚实收尾 · 车道 1
> **分支**: `card/m1-anki`（不 push，等你验收）
> **日期**: 2026-08-28
> **头号驱动**: 你的批注——"就像 anki 一样，我需要清晰看到每个 vault，里面需要我复习哪些白板，然后到期时间是什么"

---

## 一、你需要做什么（用户产品体验）

**本 worktree 阶段没有要你操作的**——live 容器还跑主分支旧代码，**浏览器走查+截图由主 session 部署时执行**（批次纪律新增②）。部署后你会看到：

1. 打开总览页（`http://127.0.0.1:8011/api/v1/review/overview/page`），每个库是一张卡片：
   - 库名 + 四态徽标（今日投影/过期投影/无投影/投影损坏）+ 汇总行（**到期 N · 新卡 M · 待剖析 K**）
   - 卡片里是**白板表格**：`白板名 | 到期 | 新卡 | 待剖析 | 最早到期`
   - 行序 = 该复习的板排前面（按推荐优先级），零到期的板按下次到期时间垫底
2. **最早到期一列说人话**："现在 / 逾期3天 / 明天 / 5天后 / 9月15日"——不再是 UTC 时间串
3. 页面生成时间显示**上海本地时区**（修掉现网差 8 小时的 UTC 缺陷）
4. **点白板名直接跳 Obsidian 对应白板**（`原白板/<板名>.md`）；点库名跳该库

### ⚠️ 两个预告（防误判"没做"）

- **最早到期列今天大多显示"现在/逾期N天"属数据现状**：现网 future_nodes=0（几乎全部节点无未来排期），不是功能坏了。等 FSRS 排期数据积累后才会出现"明天/N天后"。
- **深链现实约束**（你已知情的拍板项 2）：点板名跳 Obsidian 依赖该库**已在你的 Obsidian 里注册**。test-vault 没注册所以链接必死——页面已做诚实降级：无投影库不出链接只出文案，页脚有"需在 Obsidian 打开过该库"提示。根治需要你哪天在 Obsidian 里打开过那个库一次。

---

## 二、技术判据（Claude 已代跑，全部通过）

| 裁判 | 命令 | 结果 |
|---|---|---|
| 总览单测（6 存量 + 6 新增，含 20+ 敌对形状） | `cd backend && .venv/bin/pytest tests/unit/test_review_overview.py -q` | **12 passed** ✅ |
| 投影回归（13 存量 + 3 新增 + 2 恒等断言显式扩） | `cd backend && .venv/bin/pytest tests/regression/test_daily_review_pick.py -q` | **18 passed** ✅ |
| 推送链被动兼容（不改车道 3 文件，只验证） | `cd backend && .venv/bin/pytest tests/regression/test_daily_review_run.py -q` | **22 passed** ✅ |
| router 面 review 相关 | `pytest tests/test_routers.py -k "overview or review"` | **8 passed** ✅（16 个 canvas/agents 404 为存量债，与本卡无关） |
| ruff lint + format | 4 个改动文件 | 全过 ✅ |
| 端到端冒烟（真实生产器→端点→HTML 落盘） | scratchpad/smoke_e2e.py | **SMOKE OK** ✅ |

### P0 完成判据逐条对账

- **(a) 三级视图**：vault 卡片→板表格五列齐全；板级到期数由 due_nodes group-by 派生，测试断言合计==stats.due_nodes（`test_board_table_groupby_matches_stats`）；脏行（board 非法/due_reason 枚举外/fsrs_due 非生产器形态/日历非法/字段不自洽）按既有 corrupt 语义整库降级不 500（`test_due_nodes_dirty_rows_degrade_corrupt_not_500`，7 类敌对形状）✅
- **(b) 时间人话化**：统一 Asia/Shanghai（容器缺 tzdata 退化固定+8，无夏令时语义等价），跨午夜按上海本地日；"现在/逾期N天/明天/N天后/M月D日"；页面 UTC 裸串（+00:00）回归锁定不得出现（`test_time_humanization_asia_shanghai`）✅
- **(c) 深链**：`obsidian://open?vault=<目录名>&file=原白板%2F<板名>.md` percent-encode + HTML 属性 &amp; 转义双层；无投影库不出假链接 + 页脚提示（`test_no_projection_degrades_without_fake_deeplink`）✅
- **(d) curl page 断言**：以 TestClient 写进单测（live 容器跑主分支，live curl 留部署后——你 goal 里已预告）✅

### P1（当日余力项，已完成，未移交）

`scripts/daily_review_pick.py` 顶层加性 `boards` 全量 rollup：`[{board, due, due_new, due_scheduled, future, next_due, placeholder, earliest_overdue}]`——补 top_boards/upcoming 各截 [:3] 与 placeholder 板级无归属的结构性缺口。**schema_version 保持 3**，ineligible.placeholder 扁平列表 / notification / top_boards / upcoming / due_nodes / stats 零改动（`test_boards_rollup_additive_old_fields_untouched` 旧字段逐一在位断言；顶层键集合恒等断言按其自身注释要求显式扩 `boards`）。占位符按 source_board 归板，**无 source_board 的占位符只留扁平列表不虚构归属**。

消费侧接线：总览页 rollup 在场时填"待剖析"列 + 零到期板全量；rollup 缺省（旧投影）回落 P0 纯派生路径；rollup 形状垃圾按既有 corrupt 语义（`test_boards_rollup_consumed_when_present`）。

### 冒烟抓到并已修的两个洞（先红后绿入册）

1. **混板紧迫度低估**（`b0028b0f`）：同板"逾期3天节点+新卡"时，字典序 min 把新卡空串（=现在）当最早，显示"现在"盖掉"逾期3天"。改为仅在非空时间戳内取 min，全新卡板才显示"现在"。
2. **人话化极值 500**（`efb7dc4d`）：日历合法极值 `9999-12-31T23:59:59Z` 过门禁后 `astimezone(+8)` 年份溢出 OverflowError 逃逸成 500。astimezone 收进 try，降级"—"。（同族第三处：投影 generated_at 极端 offset `-23:59` 的同款溢出在 P0 首轮即被测试抓到修掉。）

### Codex 对抗审查

- 一轮（ultra，冻结 d1ebea5f 快照）：`_bmad-output/审查/codex-review-CARD-D1.md` — **0 BLOCKER + 6 HIGH + 3 MEDIUM + 3 LOW**
- 其中 H1（astimezone 极值溢出 500）与 H3（混板最早到期）在审查进行期间已被我的端到端冒烟独立抓到并先行修复（efb7dc4d / b0028b0f）——两条独立通道命中同一批洞
- 处置（b923ff67，逐条表见审查存档附录）：H2 孤立 surrogate 500 解析层折断；H4 rollup 跨源一致性门禁（防整板静默消失/999 vs 0 造假）；H5 门禁盲区五处（boards:null / 重复 due 行 / 重复 top 板 / 重复 upcoming 板 / placeholder 垃圾元素）；M1 汇总行"含未归板 N"差额注记；M2 golden 深度全等金样；M3 上海午夜错位窗口纯函数直测；L1-L3 测试加固
- H6（非法 generated_at 归 stale 非 corrupt）：**NO-CHANGE by-design 如实入档**——CARD-C2 前卡冻结语义（"不装新鲜也不丢数据"），三轮经 git 溯源确认非本卡引入，登记接受
- 二轮复核（high，对象 b923ff67）：判 H4/H5/M1 有残留旁路（全零幽灵板/三分越界/空板名/非法 date/纯无主占位符注记）→ 全部在 `8d81ff7f` 闭合（敌对用例 +7）
- 三轮定向确认（high，对象 8d81ff7f）：残留逐条 RESOLVED + 生产器全部可达产物零误杀 + 无新缺陷——**终裁「BLOCKER/HIGH 清零: 是」**（原文见审查存档末尾）

---

## 三、改动清单（6 commits + 文档 commit，不 push）

- `c21b846a` P0：`backend/app/api/v1/endpoints/review_overview.py` 三级视图/门禁/时区/深链 + `tests/unit/test_review_overview.py` 4 新测试
- `d1ebea5f` P1：`scripts/daily_review_pick.py` boards rollup + `tests/regression/test_daily_review_pick.py` 2 新测试 + 消费接线 + 1 新测试
- `b0028b0f` fix：混板最早到期语义（冒烟发现，=Codex H3）
- `efb7dc4d` fix：人话化 astimezone 极值溢出（冒烟发现，=Codex H1）
- `b923ff67` fix：Codex 一轮处置（H2/H4/H5/M1/M2/M3/L1/L2/L3）
- `8d81ff7f` fix：Codex 二轮残留闭合（rollup 构造律四门 + date 门禁 + placeholder_attributed）

最终测试面：overview **12 passed**（含 30+ 敌对形状）+ pick **18 passed** + run **22 passed**（被动兼容）+ 端到端冒烟绿。

## 四、硬边界自查

- 未碰 `scripts/daily_review_run.py` / `send_bark.py`（车道 3）✅ 未碰 `review_service.py` / `fsrs_manager.py`（车道 2）✅
- 未碰 live vault 与容器 ✅ HTML 零外部 CDN 零 JS（既有测试 `test_page_is_self_contained_with_obsidian_links` 持续锁定）✅
- A2 冻结投影仅加性扩展，全量回归绿 ✅
