#!/usr/bin/env python3
"""每日复习选板 (DAILY-REVIEW-PUSH-2026-07-29, ChatGPT 终审 A3 修正版)。

扫 vault 节点/*.md frontmatter → 衰减 Beta 读时时效 pick → 板级 min 聚合
→ outputs/今日复习.md (人读) + outputs/今日复习.json (推送 payload, 终审 A7:
stdout 是瞬时数据, 推送失败补跑必须有持久化 payload)。

schema v3 (CARD-A2, BATCH-2026-08-24-复习闭环): 本 JSON 是全系统到期口径
唯一裁判 — Dashboard.md 直接 dv.io.load 消费 due_nodes 明细 + ineligible
分桶 (占位符待剖析积压单独成桶), 不再独立重算。v2→v3 纯加性, 推送链
(daily_review_run/send_bark 只读 notification) 被动兼容。

三态兼容 (live 实测 18 节点: 新字段 1 / 仅旧 10 / 无字段 7):
  mastery_a/b (+last_examined) → effective() 闲置折扣后 pick
  仅 mastery_score             → from_legacy() 均值继承低置信
  无字段                       → 先验 Beta(0.9,2.1), 从未考 σ 大自动优先

终审 A3 三修正:
  1. eligibility 与 start-exam-board 同规则 — 含「你的 1-2 句精准定义」
     占位符的未剖析节点跳过 (否则推荐无法出题的节点到手机)
  2. 输出命令绑定 node <top_node> — start-exam-board 自己重选点时不含
     闲置折扣, 不绑定会出现「通知说考 A 实际考 B」
  3. min() 并列 tie-break: 板上次被推荐日期(久者先) → 最老 last_examined
     → 板名 (防启动期先验板按扫描顺序永久霸榜)

依赖: 仅 stdlib + vault 内 decay_beta.py (launchd 环境无 pip 包可假设)。

═══════════════════════════════════════════════════════════════════════
CARD-G3-6a 桶位与 why_due (BATCH-2026-08-29-第六批) — 加性扩展语义裁定
═══════════════════════════════════════════════════════════════════════
schema_version 仍为 3。落地前先书面裁定, 审查按本节判 (S1/S2/S3)。

S1 桶位划分律与优先级 (无重叠 · 无遗漏)
  划分域 = 已归板 (source_board 可解析) 且未被 ineligible 拦下的节点 —
  与 stats.due_nodes + stats.future_nodes 的口径域完全同一。未归板节点
  不进桶 (已由 unassigned_nodes 点名); 占位符 / 测试文件名 / 损坏节点不
  进桶 (已由 ineligible 三桶点名) — 不重复点名, 也不静默吞。
  级联优先级 (自上而下先匹配先归, 每个域内节点恰好落一桶):
    1 new            due_reason=="new" — 无 fsrs_due 且非 fail-open 的真新卡
    2 learning_queue 已到期 且 fsrs_state ∈ {0, 1, 3}
    3 due_now        其余已到期 (含 fsrs_state==2 Review 与 malformed fail-open)
    4 due_today      未到期 且 fsrs_due 落在与 now 同一个 Asia/Shanghai 日
    5 future         其余未到期
  完备性: 域内每节点的 due_now 布尔恒二分 — True 侧被 1/2/3 穷尽 (3 = 1
  的否定 ∧ 2 的否定), False 侧被 4/5 穷尽 (同上海日与否)。互斥由级联保证。
  合计恒等 (构造保证 + 契约测试):
    |new| + |learning_queue| + |due_now| == stats.due_nodes
    |due_today| + |future|              == stats.future_nodes
  fsrs_state 取值裁定 (勘探实测: live 14 节点仅 1 个带该字段, 值为 1):
  py-fsrs v6 State 枚举无 New — Learning=1 / Review=2 / Relearning=3;
  历史哨兵 0 已由 fsrs_bridge.py:106-117 在读侧归一为 Learning (CARD-C3
  裁定), 本文件同口径把 0 并入 learning_queue, 与评分侧「刚开始学」语义
  一致 (卡面建议为 {1,3}; 本裁定是其超集, 只影响存量 0 值节点, live 实
  测为 0 个)。非整数 / 无法解析的 fsrs_state 按「无状态」落 due_now —
  未知值不吞节点, 只是不享受分层优待。

S2 加标签不搬移 (R2 高风险面 — 本卡明令禁止搬移)
  新桶只以字段 / 标签表达: due_nodes 行尾加性追加 bucket + why_due, 顶层
  加性追加 buckets 分组。节点仍全部留在 due_nodes 内, stats.due_nodes 口
  径分毫不动。理由: review_overview.py 把 stats.due_nodes 当权威计数并用
  due_nodes group-by 派生板级到期数, Dashboard.md:57-72 直接 dv.io.load
  消费 due_nodes 明细 — 任何「把 learning/new 搬出 due_nodes」的做法都会
  同时改动这两个消费方的数字, 属破坏性变更而非加性扩展。
  加性上界同样是契约: 顶层只加 buckets 一个键; boards rollup 行 / ineligible
  / notification / top_boards / upcoming / stats 一个字段不加不改。

S3 why_due 取值枚举与生成规则
  why_due 是恒非空人话串 (桶位是机器枚举, why_due 是给人看的那一句), 由
  下列 6 个确定性模板生成, 槽位只填投影内已有的真实数据 — fsrs_due /
  fsrs_state / last_examined 派生的闲置天数 / Asia/Shanghai 本地时刻,
  一律不虚构、不估算:
    new            "新卡未排期，视同即刻到期 · <闲置片段>"
    learning_queue "<学习中|重学中> · <到期片段> · <闲置片段>"
    due_now 排期    "到期待复习 · <到期片段> · <闲置片段>"
    due_now 脏日期  "到期待复习 · 到期时间无法解析(<原值安全化摘录>)，保守视同到期 · <闲置片段>"
    due_today      "今天 HH:MM 到期（尚未到点）"
    future         "<明天|N 天后> M月D日 HH:MM 到期"
  片段规则: 闲置片段 = "从未考察" | "已闲置 N 天" (N 取整, 源自
  last_examined); 到期片段 = "已逾期 N 天（M月D日到期）" | "今天 HH:MM
  到期" | 脏日期说明。
  原值安全化摘录 (Codex round-1 MEDIUM): 脏 fsrs_due 原值先按 ISO-8601
  合法字符白名单过滤 (非白名单字符逐个替换为 "?") 再截 40 字 —— why_due
  会被拼进 outputs/今日复习.md 并可能被下游 HTML 渲染, 原样透传等于把
  frontmatter 里的任意串接进渲染面。摘录保留足以认出原值的形状, 但不再是
  逐字原值, 本行即其书面定义。
  极值兜底 (2 条, Codex round-1 MEDIUM 显式纳入规格): 当 fsrs_due 或 now
  的时刻在时区换算中不可表示 (年份极值 astimezone 溢出) 时, 六模板的时间
  槽位无从生成, 改用
    到期片段兜底  "到期时刻超出可显示范围"
    future 兜底   "到期时刻超出可显示范围，按未来排期处理"
  —— 如实说"算不出", 不猜、不静默丢节点。同一情形下判桶的"今天"基准退化
  为 UTC 日 (见 _today_sh)。
  非到期两桶 (due_today/future) 的 why_due 读作「何时到期」— 同一字段名
  承载「为什么今天不用做」的诚实说明, 绝不给未到期节点编造到期理由。
  时区: 人话一律 Asia/Shanghai (与 CARD-D1 总览页同一口径); 落盘的
  fsrs_due / next_due 仍是 UTC-Z 原样, 不动。

═══════════════════════════════════════════════════════════════════════
CARD-G3-6b 板级 why_this_board 与系数版本化 (BATCH-2026-09-01-第八批)
═══════════════════════════════════════════════════════════════════════
schema_version 仍为 3。落地前先书面裁定, 审查按本节判 (S4/S5/S6)。

S4 排序因子清单 + why_this_board 生成律
  排序因子 (真相源 = TIE_FACTOR_KEYS 常量, 自上而下逐级 tie-break;
  _tie 排序键由它逐键派生, sha 指纹摘的也是它 —— 单一真相源, 两处不可
  各自漂移, Codex round-1 HIGH 整改):
    1 priority_pick          round(top pick, 8) — 衰减 Beta μ−σ, 越低越先
    2 board_last_recommended 板上次被推荐日期串, 空串(从未)排最前
    3 min_last_examined      板内到期节点最老 last_examined, 空串排最前
    4 board                  板名字典序 (最终稳定锚)
  ⚠ 本卡对排序逻辑零改动 —— 上表是把 HEAD 既有行为显式化, 不是新规则。
  改序另立卡; 金样门锁住"HEAD 产出与本卡产出的 top_boards 顺序逐字相同"。

  why_this_board 是恒非空人话串, 由 why_this_board(factors) 这一个纯函数
  从 factors 生成 —— 同一份 factors 恒得同一句 (契约测试把落盘 factors 代
  回模板复算比对)。禁 LLM、禁渲染层再算: review_overview 只 html.escape 后
  原样显示, 一个数字都不碰。factors 全部是投影内已有数据的确定性派生:
    due_total       板内到期节点数 (== 同行 pending, 同源)
    due_new         其中真新卡数 (无 fsrs_due 且非 fail-open)
    due_scheduled   其中已排期数 (fsrs_due 非空)
    due_malformed   其中脏日期 fail-open 数
                    ↑ 三者互斥完备, 合计恒 == due_total (与 boards rollup
                      的 due 三分同一条判据, 不另立口径)
    overdue_days    板内已排期到期节点最早 fsrs_due 的逾期天数 (上海日差,
                    取整; None = 无已排期到期节点, 或该时刻不可表示)
    idle_days       top_node 的闲置天数 (== 同行 idle_days, 同源同值)
    never_recommended  该板在 state 的 board_last_recommended 里无记录
    recommend_gap_days 距上次推荐天数 (None = 从未 / 记录不可解析)
  「没有」与「算不出」不混为一谈: overdue_days is None 时看 due_scheduled
  —— 为 0 说明板内压根没有已排期到期节点, 非 0 说明时刻超出可显示范围
  (S3 极值兜底同款诚实降级)。recommend_gap_days 同理配 never_recommended。

  模板 = 至多 5 个片段以 " · " 连接 (缺省片段整段不出现, 不填「无」):
    规模  "N 个节点到期" (+ "（其中 M 张新卡）" 当 due_new > 0)
    紧迫  "最早的已逾期 N 天" | "最早的今天到期" | "最早到期时刻超出可显示范围"
          (due_scheduled == 0 时整段省略 —— 全是新卡的板没有「逾期」可言)
    脏值  "含 N 个到期时间无法解析的节点" (仅 due_malformed > 0)
    闲置  "最该考的从未考察" | "最该考的已闲置 N 天"
    冷却  "这块板从未被推荐过" | "今天已推荐过" | "距上次推荐 N 天"
          | "上次推荐日期无法解析" | "上次推荐日期晚于今天" (记录晚于今天属
          异常状态 —— 不 clamp 成 0 伪装成"今天刚推荐过", Codex round-1
          MEDIUM 整改; recommend_gap_days 允许负值即表达此态)
  字符白名单 (沿 S3 :82 同一条口径): 成句只含 中文 / 数字 / "·" / 空格 /
  "（）" —— 槽位全部是本文件自产的 int 与固定中文, 板名/节点名一律不进句
  (它们已在同一行的 board/top_node 字段里, 拼进来既冗余, 又把 frontmatter
  自由文本引进了渲染面)。契约测试断言 sanitize(句) == 句: 模板将来若引入
  白名单外字符, 该门变红, 而不是静默把不可信串送进 HTML。

S5 系数版本化: manifest 的权威边界 (哪些改了真生效, 哪些只是登记)
  scripts/review_rank_manifest.json (version=2) 分两节, 语义不同 —— 混为
  一谈会造出「看起来能配、改了没用」的假配置:
    authoritative  运行时真相源, 改了下一轮立刻生效。当前只有
                   estimated_minutes 两个常量 (per_due_node / per_new_node)
                   —— 它们只影响本卡新增字段, 不触碰任何 A2 冻结面。
    recorded       登记快照, 改了不改变行为, 只打一行 stderr 漂移告警。
                   ranking_factors (真相源是 _tie 代码) / limits (真相源是
                   ranked[:3], 改它会动 A2 冻结的榜长) / decay_beta_constants
                   (真相源是 vault 内 decay_beta.py 模块, 本卡禁改其本体)。
  payload.rank_manifest = {version, sha256}:
    version  manifest 文件的版本号; 文件缺失/损坏时为 None (诚实说「没有
             版本」而不是假装有), 同时 stderr 告警 + 用内置默认继续 ——
             配置文件丢了不该让每日推送整轮失败, 但也不许静默。
    sha256   ⚠ 指纹算的是「运行时实际生效的系数」的规范序列化, 不是
             manifest 文件的字节。这条是本卡最容易做假的地方: 若只对文件
             取 hash, 那么别人改 decay_beta.py 的 GAMMA (系数真的变了)
             指纹却纹丝不动, 版本化就成了摆设。实际入摘要的是 version +
             因子序 + 生效分钟常量 + 生效上限 + 从模块读到的 decay 六个
             实际值 + (R2 新增) vault 内 decay_beta.py 的整份字节,
             任一变化 → sha 变 (契约测试逐项变异验证)。R2 之前只摘六个
             常量取值, 改 pick_score 函数体可让板序翻转而 sha 不动。

S6 归属与上限裁定 (无归属 / 一节点多板 / 同名板 / 上限 / 去重)
  无归属  _board_name(source_board) 返 None 的节点不进任何板, 点名在
          unassigned_nodes (HEAD 既有语义, 本卡零改动, 只补独立测试)。
  一节点多板  ⚠ 不支持, 且不发明语义。2026-09-01 live 实测 14 个节点的
          source_board 取值分布: 全部是单值 wikilink 串 (`[[原白板/X]]`),
          零个 YAML 数组、零个逗号分隔多值。两种可能的多板写法, 实测行为
          **并不相同** (下列结论由 _fm_str/_board_name 真实调用得出, 非推理):
            a) YAML 数组 `source_board: ["[[A]]", "[[B]]"]`
               → _fm_str 的 `[^"\\n]+?` 跨不过内嵌引号, 整行不匹配 → 该节点
                 视同"无 source_board" → 不进任何板, 点名在 unassigned_nodes。
                 即: 不静默丢弃, 但也拿不到板 —— 用户会在 md 末尾看见它。
            b) 单串多值 `source_board: "[[A]], [[B]]"` (无内嵌引号)
               → 整串当成一个板名, _board_name 的 rsplit("/",1)[-1] 使其归到
                 **最后**一个路径段 (不是第一个) —— 一个既非 A 也非"多板"的
                 板名, 属于会静默错归的形态。
          裁定: 两者均保持现状并登记, 不为现网不存在的形态发明多板归属语义
          (DD-10 防蔓延)。b) 的错归风险如实登记在验收单"未证明什么"节 ——
          修它要动 _board_name 的归一规则, 那会影响全部单值节点的板身份,
          超出本卡加性边界。真出现多板需求时另立卡 —— 届时 due 计数、rollup
          合计恒等、buckets 划分律三处都要同步改, 那不是加性扩展。
  同名板  _board_name 取 wikilink 最后一段 (`原白板/X` → `X`), 因此不同
          路径下的同名板会合并成同一块板。裁定: 保持现状 —— 板名是本系统
          全链路的板身份 (notification 标题 / obsidian 深链 / state 的
          board_last_recommended 键 / rollup 行键全按板名), 只在选点侧改成
          带路径的身份会与其余四处不一致。登记 + 独立测试锁定该行为。
  上限    top_boards / upcoming 各截 [:3] 是 HEAD 既有行为, 本卡不改截断。
          新增顶层 truncated = {"top_boards": bool, "upcoming": bool} ——
          只是把「你看到的不是全部」显式说出来 (ranked 全量仍供 runner 的
          next_due_utc 计算使用, daily_review_run:172-178, 消费面零变化)。
  去重    板内节点按文件 stem 唯一 (同目录同名 .md 不可能共存); 板级按 dict
          键唯一, 同一板名在 ranked / upcoming 二者中至多出现一次且互斥
          (有到期 → ranked, 全员未到期 → upcoming)。本卡补独立测试锁定
          「同一板名不跨 ranked/upcoming 双列」。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

#: 与 start-exam-board SKILL Step 3 完全同一条占位符规则 (终审 A3)
PLACEHOLDER = "你的 1-2 句精准定义"

#: 生产数据污染标记 (对齐 memory-health.sh 批次1'⑥ 审计清单) — 不推测试节点。
#: ⚠ 只匹配文件名: 真实节点 frontmatter 可能引用测试会话 id (live 实测
#: Fundamentals 的 error_candidates 含 m3-e2e-sessionend-test, 按全文匹配会误杀)
TEST_MARKERS = ("TestConcept", "UAT-2.5", "m3-e2e")

#: [Decision-FSRS-2] WHEN/WHAT 分工 (FSRS-V2-2026-07-30):
#: FSRS 管 WHEN — fsrs_due 决定今天谁到期, 无字段 = New 卡即刻到期;
#: 衰减 Beta 管 WHAT — 到期集合内按 pick=μ−σ 排序。
#: 本文件保持纯 stdlib: 只做 UTC 定长字符串日期比较, 不 import fsrs。

#: Bark 通知标题上限 (方案规范: ≤20 全角字符)
TITLE_LIMIT = 20

#: CARD-G3-6a 人话时区: 统一 Asia/Shanghai (与 CARD-D1 总览页同一口径 —
#: launchd/容器跑 UTC 时 astimezone() 的"本地日"会跨午夜误判)。缺 tzdata
#: 时退化为固定 +8 (Asia/Shanghai 自 1991 年起无夏令时, 语义等价)。
try:
    from zoneinfo import ZoneInfo

    _TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")
except Exception:  # noqa: BLE001 — ZoneInfoNotFoundError / ImportError 同一退化
    _TZ_SHANGHAI = timezone(timedelta(hours=8))

#: CARD-G3-6a S1 五桶 — 级联优先级顺序即本元组顺序 (落盘 buckets 键序亦同)
BUCKET_NEW = "new"
BUCKET_LEARNING = "learning_queue"
BUCKET_DUE_NOW = "due_now"
BUCKET_DUE_TODAY = "due_today"
BUCKET_FUTURE = "future"
BUCKET_ORDER = (BUCKET_NEW, BUCKET_LEARNING, BUCKET_DUE_NOW, BUCKET_DUE_TODAY, BUCKET_FUTURE)

#: 人读标签 (仅 render_md 用; JSON 落盘恒用英文键)
BUCKET_CN = {
    BUCKET_NEW: "新卡",
    BUCKET_LEARNING: "学习中",
    BUCKET_DUE_NOW: "到期待复习",
    BUCKET_DUE_TODAY: "今天晚些到期",
    BUCKET_FUTURE: "未来排期",
}

#: S1 fsrs_state 裁定: py-fsrs v6 Learning=1 / Relearning=3; 历史哨兵 0 由
#: fsrs_bridge.py 读侧归一为 Learning (CARD-C3), 本文件同口径并入。
LEARNING_STATES = (0, 1, 3)

#: S3 原值安全化白名单 (Codex round-1 MEDIUM): ISO-8601 时间戳的合法字符集。
#: 脏 fsrs_due 原值进 why_due 前逐字符过滤 —— why_due 会拼进人读 md 并可能
#: 被下游 HTML 渲染, 原样透传等于把 frontmatter 任意串接进渲染面。
_DUE_RAW_UNSAFE = re.compile(r"[^0-9A-Za-z:+. -]")

#: ═══ CARD-G3-6b ═══
#: S4 why_this_board 字符白名单: 中文 / 数字 / "·" / 空格 / 全角括号。
#: 槽位全是本文件自产的 int 与固定中文, 板名/节点名一律不进句 —— 此正则是
#: 该承诺的可执行形态 (契约测试断言 sub 后与原句逐字相同)。
_WHY_BOARD_UNSAFE = re.compile(r"[^0-9一-鿿·（） ]")

#: S5 系数清单文件名 (与本脚本同目录)
MANIFEST_FILENAME = "review_rank_manifest.json"

#: S4 排序因子序 — 单一真相源 (Codex round-1 HIGH 整改): rank_boards 的 _tie
#: 排序键由本元组逐键派生, sha 指纹摘的也是它 —— 两份表达可以各自漂移的形态
#: 被构造性消灭 (原先常量与 _tie 字面元组互不相干, 内存里交换 _tie 因子而指纹
#: 纹丝不动, 版本化成了摆设)。
#: ⚠ R1 round-2 收窄措辞: 改本元组必变 sha (摘的就是它); 至于**排序**变不变要看
#: 数据 —— 追加重复键就是「sha 变而排序不变」(round-2 LOW 实测)。故只宣称
#: 「改它 ⟹ sha 变」这一向, 不宣称「⟺ 排序变」。
TIE_FACTOR_KEYS = (
    "priority_pick",
    "board_last_recommended",
    "min_last_examined",
    "board",
)

#: S4 priority_pick 的取整位数 — 因子「可执行取值规则」的一部分 (Codex
#: round-2 HIGH): 精度收紧会让原本 8 位可分的近邻 pick 变同分而改排序,
#: 故精度本身必须登记进指纹。改此常量必变 sha; **排序变不变取决于数据** ——
#: 只有近邻到该精度级才可分的 pick 才会改序 (R1 round-2 收窄: 原写「排序与
#: sha 同变」把一个数据相关的条件说成了无条件)。
TIE_PICK_ROUND_DIGITS = 8

#: S6 既有截断上限 (HEAD 起就是 3, 本卡零改动 —— 只登记并透出 truncated)
TOP_BOARDS_LIMIT = 3
UPCOMING_LIMIT = 3

#: S5 estimated_minutes 内置默认 — manifest 的 authoritative 节可覆盖。
#: ⚠ 拍脑袋的经验值, 非实测: 新卡首次剖析更慢, 故 5 > 3。
DEFAULT_MINUTES = {"per_due_node": 3, "per_new_node": 5}

#: S5 入指纹的 decay_beta 六常量名 (排序固定 → 指纹稳定)
DECAY_CONSTANT_NAMES = ("BETA_EXPLORE", "FLOOR", "GAMMA", "GAMMA_DAILY", "PRIOR_A", "PRIOR_B")

#: S5-R2 vault 内 decay_beta.py 的位置 —— load_decay 与"指纹取字节"共用这一处。
#: 两处各写一遍路径 = 指纹摘的可能不是真正被 import 的那份 (CARD-G3-6b-R2)。
DECAY_DIR_REL = (".claude", "scripts")
DECAY_MODULE_FILENAME = "decay_beta.py"


def decay_source_path(vault) -> Path:
    """vault 内 decay_beta.py 的路径 (只读用)。

    S5-R2: 指纹要摘 decay_beta.py 的**字节**, 路径必须从 vault 根显式派生
    —— 不走 import, 也不读 decay.__file__ (调用方注入的假 decay 没有该属性,
    静默兜 None 会让指纹在测试路径上恒定 = 新门自身假绿)。
    """
    return Path(vault).joinpath(*DECAY_DIR_REL, DECAY_MODULE_FILENAME)


def _aware(s: str) -> datetime:
    dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _fm_num(fm: str, key: str):
    # 容负号 (Code-Review L5): mastery_a: -3 应进 corrupt 分支而非静默当无字段
    m = re.search(rf'^{key}:\s*"?(-?[0-9]*\.?[0-9]+)"?\s*$', fm, re.M)
    return float(m.group(1)) if m else None


def _fm_str(fm: str, key: str):
    m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
    return m.group(1).strip() if m else None


def _board_name(raw: str | None):
    """source_board 归一化 → 板名 (live 数据实为 wikilink '[[原白板/X]]')。"""
    if not raw:
        return None
    name = raw.strip()
    if name.startswith("[[") and name.endswith("]]"):
        name = name[2:-2]
    name = name.split("|")[0]                 # [[path|alias]] 取 path
    name = name.rsplit("/", 1)[-1].strip()    # 原白板/X → X
    return name or None


def _fm_int(fm: str, key: str):
    """整数型 frontmatter (fsrs_state)。非整数 / 溢出 / 缺失一律 None = 无状态。

    S1: 未知状态不吞节点 — 只是不享受 learning_queue 分层优待, 仍按到期落
    due_now。inf.is_integer() 为 False, 巨值串因此也走 None 分支。
    """
    v = _fm_num(fm, key)
    if v is None or not float(v).is_integer():
        return None
    return int(v)


def _sh_local(ts: str):
    """UTC-Z 定长时间串 → Asia/Shanghai aware datetime; 不可表示时 None。

    ts 已由 scan_nodes 的 fsrs_due 门禁保证形态 (非规范值早被 fail-open
    清空)。年份极值 (9999-12-31T23:59:59Z + 8h) astimezone 会 OverflowError
    — 人话层绝不崩全轮, 交由调用方走兜底文案 / 归 future。
    """
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc).astimezone(_TZ_SHANGHAI)
    except (ValueError, OverflowError, OSError):
        return None


def _today_sh(now: datetime):
    """判桶的「今天」基准 (Asia/Shanghai 日)。

    极值 now (年份边界) 换算会 OverflowError —— 此处退化为 UTC 日而非崩掉
    整轮 (S3 极值兜底同款诚实降级)。注意: HEAD 起 build_payload 的
    payload["date"] 对同类极值本就会抛 OverflowError, main() 已在入口显式
    拒绝这类 --now; 本兜底是给直接调用 build_payload 的路径留的防线。

    Codex round-2 MEDIUM: UTC 回退本身也可能溢出 (如 year=1 且 offset=+14,
    换算要减 14 小时 → 年份下溢), 故最后再退一档到 now 自身表示的日期 ——
    该值恒可得, 三档保证本函数永不抛。
    """
    for tz in (_TZ_SHANGHAI, timezone.utc):
        try:
            return now.astimezone(tz).date()
        except (OverflowError, OSError):
            continue
    return now.date()


def _safe_raw(raw: str) -> str:
    """S3 原值安全化摘录: 非白名单字符 → "?", 再截 40 字。"""
    return _DUE_RAW_UNSAFE.sub("?", raw)[:40]


def _idle_cn(idle_days) -> str:
    """S3 闲置片段: 源自 last_examined, 无则如实说从未考察。"""
    return "从未考察" if idle_days is None else f"已闲置 {int(idle_days)} 天"


def _overdue_cn(n: dict, today_sh) -> str:
    """S3 到期片段 (仅已到期节点)。脏日期如实点名原值摘录, 不装能解析。"""
    if n["due_fail_open"]:
        return f"到期时间无法解析({_safe_raw(n['fsrs_due_raw'])})，保守视同到期"
    due_sh = _sh_local(n["fsrs_due"])
    if due_sh is None:
        return "到期时刻超出可显示范围"
    delta = (due_sh.date() - today_sh).days
    if delta < 0:
        return f"已逾期 {-delta} 天（{due_sh.month}月{due_sh.day}日到期）"
    return f"今天 {due_sh:%H:%M} 到期"


def assign_bucket(n: dict, now: datetime) -> tuple[str, str]:
    """S1 级联判桶 + S3 模板生成 → (bucket, why_due)。

    调用前提: n 已归板 (划分域)。级联顺序即 BUCKET_ORDER — 先匹配先归,
    因此每个域内节点恰好落一桶 (互斥), 且 due_now 布尔二分被五桶穷尽
    (完备)。why_due 恒非空。
    """
    today_sh = _today_sh(now)
    idle = _idle_cn(n["idle_days"])
    if n["due_now"]:
        if not n["fsrs_due"] and not n["due_fail_open"]:
            return BUCKET_NEW, f"新卡未排期，视同即刻到期 · {idle}"
        if n["fsrs_state"] in LEARNING_STATES:
            phase = "重学中" if n["fsrs_state"] == 3 else "学习中"
            return BUCKET_LEARNING, f"{phase} · {_overdue_cn(n, today_sh)} · {idle}"
        return BUCKET_DUE_NOW, f"到期待复习 · {_overdue_cn(n, today_sh)} · {idle}"
    # 未到期两桶: fsrs_due 恒为规范非空串 (空串必定 due_now)
    due_sh = _sh_local(n["fsrs_due"])
    if due_sh is None:
        # 不可表示 = 年份极值远期, 定义上不可能是"今天" → future 兜底
        return BUCKET_FUTURE, "到期时刻超出可显示范围，按未来排期处理"
    delta = (due_sh.date() - today_sh).days
    if delta == 0:
        return BUCKET_DUE_TODAY, f"今天 {due_sh:%H:%M} 到期（尚未到点）"
    when = "明天" if delta == 1 else f"{delta} 天后"
    return BUCKET_FUTURE, f"{when} {due_sh.month}月{due_sh.day}日 {due_sh:%H:%M} 到期"


def scan_nodes(vault: Path, now: datetime, decay):
    """扫描 节点/ 池 → (nodes, stats, ineligible, placeholder_boards)。
    逐节点容错: 单个脏节点不崩全轮。

    ineligible 分桶 (schema v3, CARD-A2): 被跳过的节点按原因点名, 不再只有
    计数 — Dashboard 消费 placeholder 桶显示"待剖析积压"。
    placeholder_boards (CARD-D1 P1): {板名: 占位符数} 板级归属, 供 boards
    rollup; 无 source_board 的占位符不入 (只在扁平列表)。
    """
    stats = {"new": 0, "legacy": 0, "none": 0, "ineligible": 0, "test_excluded": 0, "corrupt": 0}
    ineligible = {"placeholder": [], "test_excluded": [], "corrupt": []}
    placeholder_boards: dict[str, int] = {}  # CARD-D1 P1: 占位符板级归属
    now_z = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    nodes = []
    for path in sorted((vault / "节点").glob("*.md")):
        stem = path.stem
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            stats["corrupt"] += 1
            ineligible["corrupt"].append(stem)
            print(f"[pick] 读取失败跳过 {stem}: {e}", file=sys.stderr)
            continue
        if any(mk in stem for mk in TEST_MARKERS):
            stats["test_excluded"] += 1
            ineligible["test_excluded"].append(stem)
            continue
        m = re.match(r"^﻿?---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
        fm, body = (m.group(1), m.group(2)) if m else ("", text)
        if PLACEHOLDER in body:
            stats["ineligible"] += 1
            ineligible["placeholder"].append(stem)
            # CARD-D1 P1: 占位符按 source_board 归板 (fm 已解析零额外 IO);
            # 无 source_board 的占位符只留扁平列表, 不虚构归属
            ph_board = _board_name(_fm_str(fm, "source_board"))
            if ph_board:
                placeholder_boards[ph_board] = placeholder_boards.get(ph_board, 0) + 1
            continue

        a_raw, b_raw = _fm_num(fm, "mastery_a"), _fm_num(fm, "mastery_b")
        legacy = next(
            (v for k in ("mastery_score", "mastery", "mastery_level")
             if (v := _fm_num(fm, k)) is not None),
            None,
        )
        if a_raw is not None and b_raw is not None:
            a, b, state = a_raw, b_raw, "new"
        elif legacy is not None:
            a, b = decay.from_legacy(legacy)
            state = "legacy"
        else:
            a, b, state = decay.PRIOR_A, decay.PRIOR_B, "none"
        stats[state] += 1

        last_exam = _fm_str(fm, "last_examined")
        idle_days = None
        if last_exam:
            try:
                idle_days = max(0.0, (now - _aware(last_exam)).total_seconds() / 86400.0)
            except ValueError:
                print(f"[pick] last_examined 无法解析, 按从未考: {stem}", file=sys.stderr)
                last_exam = None
        try:
            # pick_score 也在 try 内 (Code-Review M2): 除零/溢出同属脏数据
            a_eff, b_eff = decay.effective(a, b, idle_days or 0.0)
            pick = decay.pick_score(a_eff, b_eff)
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            stats["corrupt"] += 1
            ineligible["corrupt"].append(stem)
            print(f"[pick] Beta 参数损坏跳过 {stem}: {e}", file=sys.stderr)
            continue
        if not math.isfinite(pick):
            # Codex-A2 H1: 巨值 mastery 让 pick 静默算成 NaN/inf 不抛异常 —
            # v3 起每个到期节点的 pick 都进 JSON, 单个 NaN = 全文件非法。
            # 与其余脏数据同语义: 进 corrupt 桶, 不崩全轮。
            stats["corrupt"] += 1
            ineligible["corrupt"].append(stem)
            print(f"[pick] Beta 参数溢出跳过 {stem}: pick={pick}", file=sys.stderr)
            continue

        fsrs_due = _fm_str(fm, "fsrs_due") or ""
        fsrs_due_raw = fsrs_due   # CARD-G3-6a: fail-open 清空前留底, 供 why_due 点名
        due_fail_open = False
        # Code-Review M2: Obsidian Properties 面板可能把 datetime 重新序列化成
        # 带偏移格式, 词法比较会反向误判「永不到期」。非规范格式 fail-open
        # 视同到期 (与 New 语义一致), 不静默消失。
        # Codex-A2 M2: 形状正确但日历非法 (如月份 13) 词法比较会误判成未来,
        # 同样 fail-open — 脏值策略统一为一条。
        if fsrs_due:
            due_ok = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fsrs_due))
            if due_ok:
                try:
                    datetime.strptime(fsrs_due, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    due_ok = False
            if not due_ok:
                print(f"[pick] fsrs_due 非规范格式, 视同到期: {stem} ({fsrs_due})", file=sys.stderr)
                fsrs_due = ""
                due_fail_open = True
        nodes.append({
            "node": stem,
            "board": _board_name(_fm_str(fm, "source_board")),
            "state": state,
            "pick": pick,
            "idle_days": idle_days,          # None = 从未考
            "last_examined": last_exam or "",
            "fsrs_due": fsrs_due,
            "due_now": (not fsrs_due) or fsrs_due <= now_z,  # 无字段 = New 即刻到期
            "due_fail_open": due_fail_open,
            "difficulty": _fm_str(fm, "fsrs_difficulty") or "",
            # CARD-G3-6a 内部字段 (不落盘): S1 判桶 / S3 人话的输入
            "fsrs_due_raw": fsrs_due_raw,
            "fsrs_state": _fm_int(fm, "fsrs_state"),
        })
    return nodes, stats, ineligible, placeholder_boards


def load_rank_manifest(path=None):
    """S5 读系数清单 → (version, minutes, recorded)。缺失/损坏 = 诚实降级。

    返回的 minutes 恒是可用的一对非负 int: manifest 给不出合法值时逐项回落
    内置默认并 stderr 点名 —— 配置文件丢了不该让每日推送整轮失败, 但也绝不
    静默 (静默降级 = 把配置断裂伪装成"就该是这个数")。version 只在文件与
    version 字段双双可用时为整数, 其余一律 None ("没有版本"而非假装有)。
    """
    path = Path(path) if path is not None else Path(__file__).resolve().parent / MANIFEST_FILENAME
    minutes = dict(DEFAULT_MINUTES)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:  # ValueError ⊃ JSONDecodeError
        print(f"[pick] 系数清单不可用, 用内置默认: {path} ({type(e).__name__})", file=sys.stderr)
        return None, minutes, {}
    if not isinstance(raw, dict):
        print(f"[pick] 系数清单不是 object, 用内置默认: {path}", file=sys.stderr)
        return None, minutes, {}

    version = raw.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        print(f"[pick] 系数清单 version 非整数, 记为 None: {version!r}", file=sys.stderr)
        version = None

    auth = raw.get("authoritative")
    # 三层 (authoritative 节 / estimated_minutes 子节 / 叶键) 任何一层缺失、
    # null 或形状不符都必须点名回落, 不许静默 (Codex round-2 MEDIUM: 前一轮
    # 只修了叶键, 父节缺失照样无声 —— 配置断裂被伪装成"就该是这个数")
    if not isinstance(auth, dict):
        print(f"[pick] authoritative 节缺失或形状不符({auth!r}), 分钟用内置默认",
              file=sys.stderr)
        cfg = None
    else:
        cfg = auth.get("estimated_minutes")
        if not isinstance(cfg, dict):
            print(f"[pick] authoritative.estimated_minutes 缺失或形状不符({cfg!r}), "
                  "分钟用内置默认", file=sys.stderr)
            cfg = {}
    if isinstance(cfg, dict):
        for k in DEFAULT_MINUTES:
            v = cfg.get(k)
            if isinstance(v, int) and not isinstance(v, bool) and v >= 0:
                minutes[k] = v
            else:
                # 缺键与非法值同等待遇: 点名后再回落 (Codex round-1 MEDIUM —
                # 只验"在场但坏", 会放过"压根没写"的半份配置, 让静默回落
                # 伪装成用户确实配了)
                print(f"[pick] estimated_minutes.{k} 缺失或非法({v!r}), 用内置默认 {minutes[k]}",
                      file=sys.stderr)

    recorded = raw.get("recorded")
    return version, minutes, (recorded if isinstance(recorded, dict) else {})


def _recorded_claim(recorded: dict, key: str, subkey: str | None = None):
    """recorded 小节取值, 剥掉 "_" 开头的说明键; 形状不符返 None (= 未登记)。"""
    node = recorded.get(key)
    if not isinstance(node, dict):
        return None
    if subkey is not None:
        return node.get(subkey)
    return {k: v for k, v in node.items() if not k.startswith("_")}


def _warn_recorded_drift(recorded: dict, effective: dict):
    """S5: recorded 是快照不是配置 —— 与实际生效值不符时逐项出声, 以实际为准。

    这是"配置断裂会说话"的最小形态: 有人改了 decay_beta 的系数 / 改了榜长
    却没更新登记, 下一轮生成就有一行 stderr 指出来, 而不是让快照悄悄过期。
    """
    for label, claimed, actual in (
        ("ranking_factors.order",
         _recorded_claim(recorded, "ranking_factors", "order"), list(effective["ranking_factors"])),
        ("limits", _recorded_claim(recorded, "limits"), effective["limits"]),
        ("decay_beta_constants",
         _recorded_claim(recorded, "decay_beta_constants"), effective["decay_beta_constants"]),
    ):
        if claimed is not None and claimed != actual:
            print(f"[pick] 系数清单 recorded.{label} 与实际生效值不符 "
                  f"(登记={claimed!r} 实际={actual!r}); 以实际为准", file=sys.stderr)


def _implementation_sha(path=None) -> str:
    """S5 本生成器源码的实现指纹 (Codex round-2 HIGH)。

    因子清单/精度常量只能覆盖「登记过的配置面」, 覆不完取值绑定这类字面
    代码 —— 把 pick.py 自身字节也摘进指纹。

    ⚠ 保证的精确边界 (CARD-G3-6b-R1 **两轮**收窄。第一版写成「源文件字节层」
    仍然过宽 —— Codex R1 轮 HIGH 实测: 只把 vault 内 decay_beta.py 的
    pick_score 函数体改一个符号 (六常量逐字不动), 板序 [B板,A板]→[A板,B板]
    翻转而 rank sha 恒为 503fd4b6…, 全程纯源码演进、无 .pyc 参与):

    1. 摘的**只是本文件 (daily_review_pick.py) 的字节**, 加上
       effective_rank_config 里**明列的那几项生效值** (因子序 / 取整精度 /
       上限 / 分钟 / decay 六常量)。改本文件 (精度/绑定/方向/新因子, 乃至
       一个注释) 必变 sha。粒度是「本文件实现 + 明列系数」, 不是「全部排序
       相关实现」。
    2. **排序还依赖本文件之外的实现, 那部分不在指纹内**: pick 值由 vault 内
       decay_beta.py 的 effective() / pick_score() **函数体**算出 (调用点见
       scan_nodes 内 `decay.effective` / `decay.pick_score`)。该文件的**六个
       常量**在指纹内 (改常量必变 sha, 且 recorded 会打漂移告警), 但它的
       **函数体不在本键内** —— 改函数体可让排序变而**本键**
       (implementation_sha256) 纹丝不动。⚠ CARD-G3-6b-R2 已在同一份
       effective_rank_config 里新增 decay_beta_sha256 摘该文件整份字节, 故
       「改函数体而 **rank_manifest 的 sha** 不动」**已不再成立**; 本键自身
       的边界不变 (它始终只摘 pick.py)。decay_beta.py 本体归 CARD-G6-1b、
       本卡仍禁改, 只读其字节。
    3. **单向保证**: 「本文件或明列系数变 ⟹ sha 变」。逆命题不成立, 且是刻意
       放弃的 —— 摘全文件使指纹对注释也敏感; 追加重复因子键同样「sha 变而
       排序不变」(Codex round-2 LOW 的实测方向)。不可拿 sha 变没变去推断
       「改了什么」, 它只证明「本文件或明列系数变了」。
    4. **不覆盖运行时字节码**: 绕过 .py 直接执行被改的 __pycache__/*.pyc
       (伪造 mtime 使 Python 取旧 pyc) 可让排序变而本 sha 不变 —— round-3
       已实测复现。该面**本卡未评估**, 按威胁模型排除; 本函数**不宣称运行时
       完整性** (见验收单「本卡未证明什么」第 4 条)。
    """
    p = Path(path) if path is not None else Path(__file__).resolve()
    return _file_sha(p)


def _file_sha(path) -> str:
    """字节指纹的唯一实现 —— _implementation_sha 与 _decay_sha 共用。

    只读 Path.read_bytes(): 不 import、不执行被摘的文件。
    """
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _decay_sha(path) -> str:
    """S5-R2 vault 内 decay_beta.py 的字节指纹 (CARD-G3-6b-R2)。

    补的正是 _implementation_sha 边界第 2 条登记的那个缺口: pick 值由
    decay_beta.py 的 effective()/pick_score() **函数体**算出, 而旧指纹只摘
    六个常量的取值 —— 只改函数体一个符号 (六常量逐字不动) 可让板序翻转而
    rank sha 恒为 503fd4b6…(R1 轮 Codex HIGH 实测)。本函数把该文件整份字节
    摘进 effective_rank_config, 该缺口关闭。

    ⚠ 精确边界 (措辞不得放宽):
    1. path **必填**, 没有默认值可回落。给不出路径就 TypeError 当场炸, 而
       不是兜一个常数让指纹在该路径上恒定 —— 那是新门自身假绿。
    2. 摘的是**该路径上的字节**, 不是"排序真正用到的那个模块对象"。
       load_decay 走 `import decay_beta`, 同一进程内再次导入取模块缓存;
       生产是单 vault 单进程故两者同一, 多 vault 同进程 (测试) 时可能不同。
       本函数**不宣称运行时模块身份**。
    3. 与 _implementation_sha 同为**单向**保证:「文件字节变 ⟹ sha 变」。
       逆命题不成立 —— 摘全文件使指纹对注释/空行同样敏感, 不可拿"sha 变了"
       去推断"排序逻辑变了"(契约测试有一条注释变异正例锁住这个方向)。
    4. 同样**不覆盖运行时字节码**: 篡改 __pycache__/*.pyc 并伪造 mtime 的面
       见 _implementation_sha 第 4 条, 本卡未评估。
    """
    return _file_sha(path)


def effective_rank_config(decay, version, minutes: dict, decay_path) -> dict:
    """S5 运行时实际生效的全部系数 —— sha256 的被摘要对象。

    ⚠ 摘要的是"生效值"而不是 manifest 文件字节: 只对文件取 hash 的话, 别人
    改 decay_beta.py 的 GAMMA (系数真的变了) 指纹却纹丝不动, 版本化就成了
    摆设。decay 六常量一律从模块现场读 (getattr 缺失记 None —— 缺了指纹也
    该变), 上限与因子序/取整精度取代码常量, 分钟取 manifest 生效值,
    implementation_sha256 摘本文件字节 (round-2 HIGH: 取值绑定无法全部
    数据化, 由实现指纹兜住「改**源文件**规则而指纹不动」—— 其单向性与
    不覆盖运行时 .pyc 的边界见 _implementation_sha 的四条声明)。

    S5-R2 (CARD-G3-6b-R2): 新增 decay_beta_sha256 —— vault 内 decay_beta.py
    的整份字节。旧版只摘该模块的六个**常量取值**, 于是"只改 pick_score
    函数体一个符号"能让板序翻转而 sha 纹丝不动 (R1 轮实测缺口)。decay_path
    由调用方从 **vault 根**显式派生 (decay_source_path), 必填、无默认值:
    禁 import、禁 decay.__file__ —— 注入的假 decay 没有 __file__, 静默兜
    None 会让指纹在测试路径上恒定, 新门自身就成了假绿。边界见 _decay_sha。
    """
    return {
        "version": version,
        "ranking_factors": list(TIE_FACTOR_KEYS),
        "tie_pick_round_digits": int(TIE_PICK_ROUND_DIGITS),
        "estimated_minutes": {k: int(minutes[k]) for k in sorted(minutes)},
        "limits": {"top_boards": TOP_BOARDS_LIMIT, "upcoming": UPCOMING_LIMIT},
        "decay_beta_constants": {k: getattr(decay, k, None) for k in DECAY_CONSTANT_NAMES},
        "decay_beta_sha256": _decay_sha(decay_path),
        "implementation_sha256": _implementation_sha(),
    }


def build_rank_manifest(
    decay, version, minutes: dict, recorded: dict, decay_path
) -> dict:
    """S5 payload.rank_manifest = {version, sha256}; 顺带发漂移告警。

    S5-R2: decay_path 必填 —— vault 内 decay_beta.py 的路径, 调用方从 vault
    根显式派生 (decay_source_path(vault))。不给就 TypeError, 不静默兜底。
    """
    effective = effective_rank_config(decay, version, minutes, decay_path)
    _warn_recorded_drift(recorded, effective)
    blob = json.dumps(effective, sort_keys=True, ensure_ascii=False, allow_nan=False)
    return {"version": version, "sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest()}


def _board_factors(board: str, due: list, top: dict, today_sh, board_last_recommended: dict) -> dict:
    """S4 因子提取: 全部是投影内已有数据的确定性派生 —— 不虚构、不估算。

    overdue_days 只看板内"已排期且已到期"的最早 fsrs_due (与 rollup 的
    earliest_overdue 同源同判据)。None 有两个来源, 靠 due_scheduled 区分:
    为 0 = 板内压根没有已排期到期节点; 非 0 = 该时刻不可表示 (年份极值)。
    """
    scheduled = [n["fsrs_due"] for n in due if n["fsrs_due"]]
    overdue_days = None
    if scheduled:
        earliest_sh = _sh_local(min(scheduled))
        if earliest_sh is not None:
            # delta > 0 不可达 (到期判定是 UTC 词法 <= now, 上海日差不会为正);
            # 仍夹到 0 —— 真出现时按"今天到期"说, 不吐负数天。
            overdue_days = max(0, (today_sh - earliest_sh.date()).days)

    rec = board_last_recommended.get(board, "")
    gap = None
    if rec:
        try:
            # 不夹负值 (Codex round-1 MEDIUM): 记录晚于今天属异常状态, 如实
            # 上抛负数让模板走诚实分支 —— clamp 成 0 会把「记录异常」伪装成
            # 「今天刚推荐过」, 违反 S4 不虚构。
            gap = (today_sh - date.fromisoformat(rec)).days
        except (ValueError, TypeError):
            # state 里的日期串损坏: 如实说"算不出", 不当作从未推荐 (那会让
            # 一块刚推过的板伪装成冷板, 拿到不该有的解释)
            gap = None
    return {
        "due_total": len(due),
        "due_new": sum(1 for n in due if not n["fsrs_due"] and not n["due_fail_open"]),
        "due_scheduled": sum(1 for n in due if n["fsrs_due"]),
        "due_malformed": sum(1 for n in due if n["due_fail_open"]),
        "overdue_days": overdue_days,
        "idle_days": (None if top["idle_days"] is None else int(top["idle_days"])),
        "never_recommended": not rec,
        "recommend_gap_days": gap,
    }


def why_this_board(f: dict) -> str:
    """S4 模板: factors → 恒非空人话串。纯函数 — 同一 factors 恒得同一句。

    契约测试把落盘的 factors 原样喂回本函数, 要求与落盘的 why_this_board
    逐字相同 —— 解释与数字之间没有第二条通路 (没有 LLM, 没有渲染层再算)。
    """
    scale = f"{int(f['due_total'])} 个节点到期"
    if f["due_new"]:
        scale += f"（其中 {int(f['due_new'])} 张新卡）"
    parts = [scale]
    if f["due_scheduled"]:
        od = f["overdue_days"]
        if od is None:
            parts.append("最早到期时刻超出可显示范围")
        elif od > 0:
            parts.append(f"最早的已逾期 {int(od)} 天")
        else:
            parts.append("最早的今天到期")
    if f["due_malformed"]:
        parts.append(f"含 {int(f['due_malformed'])} 个到期时间无法解析的节点")
    parts.append("最该考的从未考察" if f["idle_days"] is None
                 else f"最该考的已闲置 {int(f['idle_days'])} 天")
    if f["never_recommended"]:
        parts.append("这块板从未被推荐过")
    elif f["recommend_gap_days"] is None:
        parts.append("上次推荐日期无法解析")
    elif f["recommend_gap_days"] < 0:
        # 记录晚于今天 (时钟回拨/时区错乱/手滑改了 state) — 如实说异常,
        # 不 clamp 成 0 伪装成"今天刚推荐过" (Codex round-1 MEDIUM)
        parts.append("上次推荐日期晚于今天")
    elif f["recommend_gap_days"] == 0:
        parts.append("今天已推荐过")
    else:
        parts.append(f"距上次推荐 {int(f['recommend_gap_days'])} 天")
    return " · ".join(parts)


def estimated_minutes(f: dict, minutes: dict) -> int:
    """S5 板级预计工作量: 新卡按 per_new_node, 其余到期按 per_due_node。

    三分互斥完备 (S4), 故 new + scheduled + malformed 恰好覆盖 due_total。
    常量归 manifest 的 authoritative 节 —— 用户改了下一轮立刻生效。
    """
    other = int(f["due_scheduled"]) + int(f["due_malformed"])
    return int(f["due_new"]) * int(minutes["per_new_node"]) + other * int(minutes["per_due_node"])


def rank_boards(nodes, board_last_recommended: dict, now: datetime, minutes: dict | None = None):
    """板级聚合: priority = min(pick), 终审 A3 tie-break。

    CARD-G3-6b 加性 (S4): 行尾追加 why_this_board / estimated_minutes /
    factors 三个字段 —— 排序键 (_tie) 与既有七字段一个不动, 行内新字段
    排在旧字段之后 (落盘键序稳定)。now/minutes 是新增入参: 前者供逾期与
    冷却天数换算 (此前本函数不需要时间), 后者是 manifest 生效的分钟常量。
    """
    minutes = minutes or DEFAULT_MINUTES
    today_sh = _today_sh(now)
    boards: dict[str, list] = {}
    unassigned = []
    for n in nodes:
        if not n["board"]:
            unassigned.append(n["node"])
            continue
        boards.setdefault(n["board"], []).append(n)

    ranked, upcoming = [], []
    for board, members in boards.items():
        due = [n for n in members if n["due_now"]]
        if not due:
            # WHEN: 全员未到期 → 不进推荐榜, 记最近的未来到期 (F1 放假语义)
            nxt = min(members, key=lambda n: n["fsrs_due"])
            upcoming.append({"board": board, "next_due": nxt["fsrs_due"], "node": nxt["node"]})
            continue
        top = min(due, key=lambda n: n["pick"])   # WHAT: 到期集合内衰减 Beta 排序
        factors = _board_factors(board, due, top, today_sh, board_last_recommended)
        # 排序键由 TIE_FACTOR_KEYS 逐键派生 (单一真相源, 见常量处裁定) ——
        # 各键取值与 HEAD 的字面 _tie 元组逐位相同, 初始顺序下排序行为零变化
        tie_parts = {
            "priority_pick": round(top["pick"], TIE_PICK_ROUND_DIGITS),
            "board_last_recommended": board_last_recommended.get(board, ""),  # 空串 = 从未被推荐, 排最前
            "min_last_examined": min(n["last_examined"] for n in due),        # 空串 = 有从未考节点, 排最前
            "board": board,
        }
        ranked.append({
            "board": board,
            "top_node": top["node"],
            "priority": round(top["pick"], 4),
            "pending": len(due),                   # 到期即待复习 (Decision-FSRS-2)
            "idle_days": (None if top["idle_days"] is None else int(top["idle_days"])),
            "difficulty": top["difficulty"],
            "next_due": min((n["fsrs_due"] for n in members if not n["due_now"]), default=""),
            # CARD-G3-6b 加性 (S4): 板级解释三件套 — why 由 factors 单向复算,
            # factors 同时落盘让消费方能自证那句话没跑偏 (禁 UI 再算)
            "why_this_board": why_this_board(factors),
            "estimated_minutes": estimated_minutes(factors, minutes),
            "factors": factors,
            "_tie": tuple(tie_parts[k] for k in TIE_FACTOR_KEYS),
        })
    ranked.sort(key=lambda r: r["_tie"])
    for r in ranked:
        del r["_tie"]
    upcoming.sort(key=lambda u: u["next_due"])
    return ranked, upcoming, unassigned


def _title(board: str) -> str:
    prefix = "📚 今日复习 · "
    room = TITLE_LIMIT - len(prefix)
    return prefix + (board if len(board) <= room else board[: room - 1] + "…")


def _body(top: dict) -> str:
    idle = "从未考察" if top["idle_days"] is None else f"已闲置 {top['idle_days']} 天"
    if top["pending"] >= 2:
        return f"{top['top_node']} 等 {top['pending']} 节点待巩固 · {idle}"
    return f"{top['top_node']} 待巩固 · {idle}"


def build_payload(vault: Path, now: datetime, board_last_recommended: dict, decay,
                  manifest_path=None):
    """CARD-G3-6b: 新增可选 manifest_path (缺省 = 本脚本同目录的系数清单)。

    runner 侧调用形态不变 (daily_review_run:159-160 传四个位置参数) —— 新
    参数是加性关键字, 消费面零变化。
    """
    version, minutes, recorded = load_rank_manifest(manifest_path)
    rank_manifest = build_rank_manifest(
        decay, version, minutes, recorded, decay_source_path(vault)
    )
    nodes, stats, ineligible, placeholder_boards = scan_nodes(vault, now, decay)
    ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended, now, minutes)
    stats["unassigned"] = len(unassigned)
    # CARD-G3-6a S1: 级联判桶 + why_due 一次算好, due_nodes 行与 buckets 分组
    # 同源引用同一对值 (禁两处各算一遍 → 禁口径分裂)。划分域 = 已归板。
    for n in nodes:
        if n["board"]:
            n["bucket"], n["why_due"] = assign_bucket(n, now)
    # v3 (CARD-A2): due_nodes 明细与 stats 数字同源派生 — 自洽靠构造保证,
    # 本投影是全系统到期口径唯一裁判 (Dashboard 只消费不重算)
    due_rows = [
        {
            "node": n["node"],
            "board": n["board"],
            "state": n["state"],
            "pick": round(n["pick"], 4),
            "fsrs_due": n["fsrs_due"],           # 空串 = 新卡即刻到期
            # Codex-A2 M1: 消费方须能区分真新卡与 fail-open 的脏日期卡
            "due_reason": ("malformed" if n["due_fail_open"]
                           else ("scheduled" if n["fsrs_due"] else "new")),
            "last_examined": n["last_examined"],
            "difficulty": n["difficulty"],
            # CARD-G3-6a 加性 (S2 加标签不搬移): 行仍在 due_nodes 内, 只多两
            # 个字段 — 到期三桶之一 + 人话理由。旧字段一个不改。
            "bucket": n["bucket"],
            "why_due": n["why_due"],
            # CARD-G3-6b 加性 (裁决②, 承 G3-6a 移交 #2): 结构化闲置天数 ——
            # 与 why_due 的闲置片段同源同值 (都出自 scan_nodes 的 idle_days),
            # 下游要按闲置排序时不必再从人话串里抠数字。None = 从未考察。
            "idle_days": (None if n["idle_days"] is None else int(n["idle_days"])),
        }
        for n in nodes if n["board"] and n["due_now"]
    ]
    stats["due_nodes"] = len(due_rows)
    stats["future_nodes"] = sum(1 for n in nodes if n["board"] and not n["due_now"])
    # CARD-D1 P1 (BATCH-2026-08-27): 顶层加性 boards 全量 rollup — 补
    # top_boards/upcoming 各截 [:3] 与 placeholder 板级无归属的结构性缺口。
    # schema_version 保持 3; ineligible.placeholder 扁平列表 / notification /
    # top_boards / upcoming 零改动 (A2 冻结)。due 计数与 due_rows 同源分组,
    # 合计恒等 stats.due_nodes。
    members_by_board: dict[str, list] = {}
    for n in nodes:
        if n["board"]:
            members_by_board.setdefault(n["board"], []).append(n)
    boards_rollup = []
    for board in sorted(set(members_by_board) | set(placeholder_boards)):
        members = members_by_board.get(board, [])
        due = [n for n in members if n["due_now"]]
        future = [n for n in members if not n["due_now"]]
        boards_rollup.append({
            "board": board,
            "due": len(due),
            # 三分语义与 due_rows.due_reason 同一判据: new=真新卡 /
            # scheduled=已排期 / malformed=due-new-scheduled 隐含
            "due_new": sum(1 for n in due if not n["fsrs_due"] and not n["due_fail_open"]),
            "due_scheduled": sum(1 for n in due if n["fsrs_due"]),
            "future": len(future),
            "next_due": min((n["fsrs_due"] for n in future), default=""),
            "placeholder": placeholder_boards.get(board, 0),
            "earliest_overdue": min((n["fsrs_due"] for n in due if n["fsrs_due"]), default=""),
        })
    # CARD-G3-6a 加性: 顶层 buckets 五桶节点级分组 — 划分的权威表达。
    # 五键恒在 (空 vault 亦为五个空数组, 与 ineligible 同风格, 消费方不做
    # 存在性分支); 桶内按扫描序 (= due_nodes 行序) 稳定。行只带消费方渲染
    # 队列必需的四字段: 到期三桶与 due_nodes 同源, due_today/future 是
    # due_nodes 结构上装不下的那两桶 (它们不到期, 搬进去就违反 S2)。
    buckets: dict[str, list] = {b: [] for b in BUCKET_ORDER}
    for n in nodes:
        if not n["board"]:
            continue
        buckets[n["bucket"]].append({
            "node": n["node"],
            "board": n["board"],
            "why_due": n["why_due"],
            "fsrs_due": n["fsrs_due"],
        })
    payload = {
        "unassigned_nodes": unassigned,  # Code-Review M3: 点名而非只给数字
        "schema_version": 3,             # v3: +due_nodes 明细 +ineligible 分桶
        #                                  (纯加性; v2: FSRS WHEN 化 upcoming/due 语义)
        # CARD-C1a: 顶层加性新增 — send 侧据此组合 per-vault 有效通知 id,
        # C2 总览页据此标卡片; notification.id 值与其余字段零改动 (A2 冻结)
        "vault_id": Path(vault).resolve().name,
        "date": now.astimezone().date().isoformat(),
        "generated_at": now.astimezone().isoformat(timespec="seconds"),
        # CARD-G3-6b: 字面量 3 换成具名常量 —— 值恒等 (行为零变化), 但让
        # truncated 的判据与截断本身同源, 不给"上限改了一处漏一处"留缝
        "top_boards": ranked[:TOP_BOARDS_LIMIT],
        "upcoming": upcoming[:UPCOMING_LIMIT],
        "due_nodes": due_rows,
        "boards": boards_rollup,  # CARD-D1 P1 加性: 板级全量 rollup
        "buckets": buckets,       # CARD-G3-6a 加性: 五桶节点级分组 (S1 划分)
        "ineligible": ineligible,
        "stats": stats,
        "notification": None,
        # CARD-G3-6b 加性 (S5): 本轮实际生效系数的版本与指纹 — 消费方据此
        # 判断"解释是按哪套系数算的"; version=None 表示清单缺失/损坏
        "rank_manifest": rank_manifest,
        # CARD-G3-6b 加性 (S6): 显式说"你看到的不是全部"。截断行为本身零
        # 改动 (HEAD 起就截 3), 这里只是把它从隐式变成可见。
        "truncated": {
            "top_boards": len(ranked) > TOP_BOARDS_LIMIT,
            "upcoming": len(upcoming) > UPCOMING_LIMIT,
        },
    }
    day_id = f"canvas-review-{payload['date']}"
    if ranked:
        payload["notification"] = {
            "title": _title(ranked[0]["board"]),
            "body": _body(ranked[0]),
            "group": "canvas复习",
            "id": day_id,
        }
    elif upcoming:
        # F1 放假语义: 有调度中的板但今天零到期 → 诚实说不用复习
        nxt = upcoming[0]
        payload["notification"] = {
            "title": "📚 今日无到期节点",
            "body": f"按计划推进，休息一天 · 最近到期 {nxt['board']} · {nxt['next_due'][:10]}",
            "group": "canvas复习",
            "id": day_id,
        }
    return payload, ranked


def render_md(payload, ranked) -> str:
    s = payload["stats"]
    lines = [
        f"# 今日复习 · {payload['date']}",
        "",
        f"> 生成 {payload['generated_at']} · 到期={s['due_nodes']} / 未到期={s['future_nodes']}（不含未归板）"
        f" · 节点状态: new={s['new']} / legacy={s['legacy']}"
        f" / 无字段={s['none']} / 未剖析跳过={s['ineligible']} / 测试排除={s['test_excluded']}"
        f" / 未归板={s['unassigned']} / 损坏={s['corrupt']}",
        "",
        "| 板 | 优先分 | 到期待复习 | 最该考 | 难度 | 闲置 | 板内下次到期 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in ranked:
        idle = "从未考" if r["idle_days"] is None else f"{r['idle_days']} 天"
        nxt = r["next_due"][:10] if r["next_due"] else "-"
        diff = r["difficulty"] or "-"
        lines.append(
            f"| {r['board']} | {r['priority']} | {r['pending']} | {r['top_node']} | {diff} | {idle} | {nxt} |"
        )
    if payload.get("upcoming"):
        for u in payload["upcoming"]:
            lines.append(f"| {u['board']} | - | 0（未到期） | - | - | - | {u['next_due'][:10]} |")
    # CARD-G3-6b 加性段 (S4): 表格零改动, 只在其后追加「为什么是这几块板」
    # —— 与 G3-6a 分层队列段同一条纪律 (加标签不改既有面)。句子由白名单模板
    # 产出; 板名与既有表格行同值同面 (render_md 全文对 board/node 从未转义,
    # 属存量面, 本卡不新增可见面也不单独修 —— 统一转义策略是另一张卡)。
    if any(r.get("why_this_board") for r in ranked):
        lines += ["", "## 为什么是这几块板", ""]
        for r in ranked:
            why = r.get("why_this_board")
            if not why:
                continue
            mins = r.get("estimated_minutes")
            eta = (f" · 预计 {int(mins)} 分钟"
                   if isinstance(mins, int) and not isinstance(mins, bool) else "")
            lines.append(f"- **{r['board']}** — {why}{eta}")
    if ranked:
        lines += ["", "## 一键开考（整行复制到 Claudian）", ""]
        for r in ranked:
            lines.append(f"- `/start-exam-board from {r['board']} node {r['top_node']}`")
    else:
        lines += ["", "> ✅ 今日无到期节点，休息一天。"]
    # CARD-G3-6a: 人读清单加性分层段 — 这是「桶位/why_due」唯一的用户直接
    # 可感面 (JSON 侧给消费方, 这里给人)。表格零改动, 只在末尾追加一段。
    bucketed = payload.get("buckets") or {}
    if any(bucketed.get(b) for b in BUCKET_ORDER):
        lines += [
            "",
            "## 分层队列",
            "",
            " · ".join(f"{BUCKET_CN[b]} {len(bucketed.get(b, []))}" for b in BUCKET_ORDER),
        ]
        for b in BUCKET_ORDER:
            rows = bucketed.get(b, [])
            if not rows:
                continue
            lines += ["", f"**{BUCKET_CN[b]}**（{len(rows)}）"]
            for r in rows:
                lines.append(f"- {r['node']} · {r['board']} — {r['why_due']}")
    if payload.get("unassigned_nodes"):
        lines += ["", "> ⚠ 未归板节点（无 source_board，不参与推荐）: "
                  + "、".join(payload["unassigned_nodes"])]
    lines += [
        "",
        "> WHEN=FSRS 到期（无 fsrs_due 字段 = 新卡即刻到期）；WHAT=到期集合内按 μ−σ 排序",
        "> （含闲置回升，证据质量半衰期 69 天）。未剖析占位节点已跳过；命令已绑定最该考节点。",
    ]
    return "\n".join(lines) + "\n"


def atomic_write(path: Path, content: str):
    """同目录 tmp → os.replace 原子发布 (CARD-G6-1: tmp 名唯一化)。

    旧实现用固定名 `<原名>.tmp`: 两个写者并发时共享同一个 tmp —— 各自按
    自己的 offset 落盘, 内容交错, 总长等于较长那份 (wc -c 看不出), 随后
    双方 os.replace 发布的是同一个拼接损坏物。宿主 launchd runner ×
    后端 refresh 端点恰好是这个形态; VirtioFS 上文件锁行为不可证, 底线
    只能押在「每个写者有独占的 tmp + 单次 rename 发布」上。

    tmp 名仍以 `<原名>.` 开头 (今日复习.json.<pid>.<8hex>.tmp): 与 outputs/
    今日复习.* 同前缀, 不给「只写 今日复习.*」的写面审计新增可见面; 且
    `.tmp` 后缀让 outputs/*.md 一类的 glob 不会误吃它。异常路径清残渣 ——
    落盘失败时留一个半截 tmp 在 vault 里, 同样是写面污染。
    """
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    # O_EXCL | O_NOFOLLOW (CARD-G6-1 round-3): pid+随机后缀已经让撞名几乎不可能,
    # 但"几乎"不是保证 —— O_EXCL 让撞名直接 FileExistsError 而不是两个写者
    # 又共享同一个 tmp; O_NOFOLLOW 让"tmp 名被抢先建成一条指向库外的软链"
    # 这条路失败而不是把内容写到库外 (普通 open 会跟随软链并 truncate)。
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def load_decay(vault: Path):
    # S5-R2: 目录取自 decay_source_path —— 与指纹取字节的路径同源, 防两处
    # 各写一遍导致"摘的不是被 import 的那份"。
    sys.path.insert(0, str(decay_source_path(vault).parent))
    import decay_beta
    return decay_beta


def main():
    # allow_abbrev=False 与 runner/push.sh 同源 (Codex-C1a F1)
    ap = argparse.ArgumentParser(description="每日复习选板", allow_abbrev=False)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--state", help="daily-review.state.json (只读, 取 board_last_recommended)")
    ap.add_argument("--now", help="ISO 时间覆盖 (测试用)")
    ap.add_argument("--write", action="store_true", help="写 outputs/今日复习.md+json")
    args = ap.parse_args()

    vault = Path(args.vault)
    # 裸时间当本地时区, 与 daily_review_run.py 语义统一 (Code-Review L6)
    if args.now:
        dt = datetime.fromisoformat(args.now.replace("Z", "+00:00"))
        now = dt if dt.tzinfo else dt.astimezone()
        # Codex-G3-6a round-1 HIGH: 日历极值时刻 (如 9999-12-31T23:59:59Z)
        # 在本地/上海时区换算时 OverflowError —— HEAD 起就会在
        # payload["date"] 处抛 traceback 中断整轮, 本卡把桶位判定挪到更前
        # 只是让崩点提前。与其抛 traceback, 在入口一次性拒绝并说清原因
        # (不改任何冻结字段的计算)。
        try:
            now.astimezone()
            now.astimezone(_TZ_SHANGHAI)
        except (OverflowError, OSError):
            ap.error(f"--now 超出可换算范围 (本地/上海时区换算溢出): {args.now}")
    else:
        now = datetime.now(timezone.utc)
    blr = {}
    if args.state and Path(args.state).exists():
        try:
            blr = json.loads(Path(args.state).read_text(encoding="utf-8")).get(
                "board_last_recommended", {})
        except (json.JSONDecodeError, OSError):
            pass  # state 损坏由 runner 处置, 选点侧降级为无记录

    payload, ranked = build_payload(vault, now, blr, load_decay(vault))
    if args.write:
        out = vault / "outputs"
        out.mkdir(parents=True, exist_ok=True)
        # CARD-G6-1: 两份内容先全部渲染好, 再连着发布两次 —— md 与 json 是
        # 一对, 两个写者并发时可能各中一半 (md 来自 B、json 来自 A, Codex
        # 探针 PAIR_FINAL 实测成立)。把渲染/序列化挪到两次 rename 之前,
        # 窗口从"一次 json.dumps 的时长"收窄到"一次文件 I/O 的时长"。
        # ⚠ 只是收窄不是消除: 真正的配对原子性要目录级换名或跨进程锁,
        # VirtioFS 上锁行为不可证, 本卡不假装做到 (如实登记)。
        md_text = render_md(payload, ranked)
        json_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        atomic_write(out / "今日复习.md", md_text)
        atomic_write(out / "今日复习.json", json_text)
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
