# CARD-G6-8 独立审查请求（round-1）

## 〇 背景

本卡建**五面复习视图一致性契约**：同一份 state 输入喂给复习视图的五个面，
逐字段比对它们对每块板给出的结论（桶位 / 显示日 / 推迟 / 完成），任一字段跨面
不等即判红。目的是把跨 vault 复习 Web UI 的 G6 退出门固化成可重跑回归门。

五面（按设计稿逐字）：
① `review_overview.py`（/overview 聚合）② `review_app.py`（交互页，纯消费方）
③ `daily_review_pick.py`（投影生产器，**本卡只读**）④ 两个 skill 脚本
（`recap_exam_build.py` / `inbox_preview.py`）⑤ 推送 payload（`payload["notification"]`）

交付 = 两个新文件 + CI 白名单一行：
- `backend/scripts/g68_five_view_contract.py`（可重跑脚本）
- `backend/tests/regression/test_g68_five_view_contract.py`（回归门）
- `.github/workflows/test.yml` 加一行把新门纳入 CI 清单

## 一 最小读取面（写死，勿扩）

1. `git diff a8cefab418bd6f83a56168b3edb0e7172156d3c8 d6ecd4ed -- . ':(exclude)_bmad-output'` —— 本卡全部改动
2. `backend/scripts/g68_five_view_contract.py` 全文
3. `backend/tests/regression/test_g68_five_view_contract.py` 全文
4. `_bmad-output/审查/evidence-g68/scripts/g68_negctl.py` —— 负控实跑的就是这一份
5. `review_overview.py` 的 `_BUCKET_ORDER` / `_DUE_BUCKETS` / `_summarize` /
   `_vault_entry` / `_collect` / `_display_day` / `_display_today` / `_display_now` /
   `_gate_buckets` 各段
6. `review_app.py:1-70`（导入与职责注释）
7. `scripts/daily_review_pick.py:29-96`（桶位划分律 S1/S3）与 `:971-1160`
   （`build_payload` 与 notification）—— **只读对照**
8. 两个 skill 脚本的 `main` 段与 `inbox_preview.py` 的 `parse_now` / `_TZ_SHANGHAI`

## 二 作者自述，请独立核对

1. **矩阵真的在比，不是恒绿**：行=板、列=面、值={bucket, display_day, snoozed, done}。
   `bucket` 的值是 `((节点, 桶), …)` 的有序元组（节点级身份，不是板级计数）。
2. **「某面整块板消失」这条路径**：早期版本用「产出该字段的面 < 2 就跳过」，
   于是一个面把板整体改名/丢掉时不报红。已改为按 `FIELD_PRODUCERS` **声明**
   产出方，声明产出却缺某板 ⇒ `MISSING` ⇒ 判红；并加 `check_producers_declaration`
   双向对账（声明却零产出 / 产出却未声明 都抛）。
3. **review_app 不自造 due 算法**：AST 断言（不是 grep —— 页面 JS 是个大字符串，
   里面出现 `fsrs_due` 不算违约），要求它 `import` review_overview 的五个共享常量、
   且不在可执行代码里定义/读取 due 字段。两条验伪锚在门里。
4. **picker 只读**：本卡一个字节都不改 `daily_review_pick.py`；picker 这一面的负控
   只在契约脚本的**提取层**做。
5. **日期口径**：picker `local_tz.display_tz()` 与 review_overview `_display_tz()`
   同源；`inbox_preview` 是**刻意固定的 +08:00**（源码 :423/:430 原话），
   在非 +08:00 机器上与前两者分叉 —— 已按**身份**（面+字段+理由）登记进
   `DECLARED_DIVERGENCES`，并有一条门在 `America/Los_Angeles` 下实测该分叉确实
   发生且被契约看见（不是白名单在给一件不存在的事发豁免）。是否统一交产品。
6. **recap_exam_build 无可比结论**：它的域是检验白板构建，`--ts` 是 UTC 文件戳，
   不产出复习队列的桶位/本地日结论。如实登记为「不纳入矩阵」，但仍**加载它一次**
   并断言入口在场（importlib 加载前已先 `sys.modules[name]=mod` 再 `exec_module`）。
7. **确定性**：被测模块往 stdout 打带时刻的日志，计算期把 stdout 换成缓冲区，
   只有报告写回真 stdout；同输入二跑逐字节相等（门里有断言）。
8. **零 mock / 不连库 / 不写现网**：全部 tmp fixture + `--now` 注入；
   `runner.BACKUPS` 改道 tmp（它默认指向**主仓** `backups/`）。

## 三 按重要性排序的问题

0. **矩阵是否存在「某一面改了却不红」的门未覆盖的路径**？请给出对照输入。
   特别是：某面把值改成与另一面相同、某面少产出一个字段（不是少一块板）、
   某面多产出一块不存在的板。
1. `FIELD_PRODUCERS` 是手写声明，`check_producers_declaration` 是否真能挡住
   「声明与实现各说各话」？有没有一种改法能同时骗过声明与对账？
2. **平局归属**：`bucket` 只有两个面产出，两值不等时是 1:1，`diff_matrix` 的
   「多数派」在平局下按 `FACES` 顺序取第一个 —— 归属是任意的。这会不会让
   负控「红在错误的面」而判据仍认为合格？
3. review_app 的静态断言能否被一个**未被拦下的**裸 due 计算越过（请给对照输入）？
4. `inbox_preview` 的 +08:00 与显示时区分叉时，契约是否能判出「日期不一致」，
   还是会被 `DECLARED_DIVERGENCES` 无差别吞掉？白名单的粒度够不够？
5. snooze/done 并存顺序按 U6-C 现状（D-37）不改 —— 本门如实声明**不覆盖**那条
   顺序（它表达在 `ranked` 分区次序上，不落 payload 字段）。这条声明是否掩盖了
   本应本卡修的 T3 地盘分歧？
6. importlib 加载 skill 脚本是否漏 `sys.modules` 注册？
7. 负控 runner 的判据是「指定 nodeid FAILED **且**输出含指定文本锚」——
   这个口径是否仍有「红在别的原因上却算合格」的缝？

## 四 输出格式与边界

- BLOCKER / HIGH / MEDIUM / LOW + `file:line` + 一句复现思路
- 边界：只读、不连库、不跑完整复习链、不评 picker / display_tz 本体设计
- 措辞：一律用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」
