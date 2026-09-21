# 路线 A · 「回顾/防遗忘」的量化标准 — Q1 证据收集

> 任务书：`_bmad-output/研究/2026-09-20-收敛文档-量化标准-agent-explore任务书.md` §3 路线 A
> 采集：explore agent（CLS「收敛文档」设计 · 路线 A）· 采集日期：2026-09-20（America/Los_Angeles）
> 边界：只收集，不评 CLS 设计、不改代码/skill、不做终审；社区自述均标来源与日期；无出处不收录。
> 格式：方法/指标名 · 一句话定义 · 如何测量 · 适用问题 · 证据等级 · 链接+日期 · 迁移到 CLS 的具体形态（≤2 句） · 反例/失败边界。

## 0. 采集方法与网络边界（先读）

- 起始检查：`agent-reach doctor --json`（本机）→ `reddit.active_backend: null`（OpenCLI 浏览器扩展未连接、rdt-cli 未安装）；`youtube.active_backend: yt-dlp`。
- 实际检索通道：Anysearch（网页检索/正文摘录）+ r.jina.ai 阅读器（curl，沙箱内 DNS 被拒后经授权脱沙箱）。
- 成功直接打开并引用原文：docs.ankiweb.net、forums.ankiweb.net、supermemo.guru、docs.readwise.io、zettelkasten.de、forum.obsidian.md、stephenmwangi.com、pubmed.ncbi.nlm.nih.gov、journals.plos.org、bjorklab.psych.ucla.edu（PDF）。
- 未能直接打开：① reddit.com 全链路 403（www / old / .rss / .json 均被网络策略拒绝）；② help.supermemo.org 有人机验证（CAPTCHA）。这两处只在「§3 受限来源」按检索快照或同源页面列出，不当作一手核验。
- 证据分级口径（沿用任务书）：**一手官方**（产品官方手册/官方帮助）· **一手（学术）**（同行评议论文/摘要原文）· **社区自述**（论坛/社区帖，带日期与链接）· **二手转述**（第三方总结，本报告尽量少用）。
- 链接日期规则：官方文档无固定发布日，统一标「检索 2026-09-20」；论文/帖子标各自发表日期。

## 1. 总表（指标 × 适用 × 页头候选 × 证据等级 × 主源）

| # | 指标/方法 | 适用 | 页头候选 | 证据等级 | 主源 |
|---|---|---|---|---|---|
| A1 | True Retention（真实通过率） | Q1 | ★ 候选① | 一手官方 | docs.ankiweb.net/stats.html |
| A2 | Desired Retention + 保留–负担曲线 | Q1 | 校准线（配 A1） | 一手官方 | docs.ankiweb.net/deck-options.html |
| A3 | Daily Load（复习负担 Σ1/I） | Q1 | ★ 候选② | 一手官方 | docs.ankiweb.net/stats.html |
| A4 | Backlog/逾期计数 + catch-up 分流 | Q1 | ★ 候选③ | 一手官方 + 社区自述（官方论坛） | docs.ankiweb.net/filtered-decks.html；forums.ankiweb.net/t/adressing-backlog/43842 |
| A5 | Lapse 计数 / Leech 阈值（默认 8） | Q1 | ○ 备选 | 一手官方 | docs.ankiweb.net/leeches.html |
| A6 | Estimated Total Knowledge（预计仍记得的条数） | Q1 | ★ 候选④ | 一手官方 | docs.ankiweb.net/stats.html |
| A7 | Card Stability（回忆概率 100%→90% 用时） | Q1 | ○ 备选 | 一手官方 | docs.ankiweb.net/stats.html |
| A8 | 遗忘指数 FI（requested vs measured） | Q1 | ○（口径须写死） | 一手官方 | supermemo.guru/wiki/Forgetting_index(_in_SuperMemo) |
| A9 | 优先级队列（priority） | Q1 | ○（分栏） | 一手官方 | supermemo.guru/wiki/Priority_queue |
| A10 | 重浮半衰期 / 回忆概率 ≤50% 才重浮 | Q1/Q3 | ★ 候选（重浮侧） | 一手官方 | docs.readwise.io/.../reviewing-highlights |
| A11 | Savings 省时分数 | Q1 | ✗（抽样） | 一手（学术） | journals.plos.org/plosone/article?id=10.1371/journal.pone.0120644 |
| A12 | 最优间隔比（gap / 测试延迟） | Q1 | ○ 排程档位 | 一手（学术） | pubmed.ncbi.nlm.nih.gov/19076480/ |
| A13 | 检索练习 > 重读（测试效应） | Q1 | ✗（方式分级） | 一手（学术） | pubmed.ncbi.nlm.nih.gov/16507066/；25150680 |
| A14 | Zettel/字数产出计量 | Q1 | ○ 触发线 | 社区自述 | zettelkasten.de/posts/measure-your-goals/ |
| A15 | Obsidian 插件统计面板（Forecast/Intervals/Eases/Card Types） | Q1 | ○ | 社区自述/工具文档 | stephenmwangi.com/obsidian-spaced-repetition/flashcards/statistics/ |
| A16 | 创作期 → 巩固期（峰值→成稿的月数） | Q1/Q4 | ○ | 一手官方 | supermemo.guru/wiki/Incremental_writing |

## 2. 指标详表（A1–A16）

### A1. True Retention（真实通过率）— Anki
- **一句话定义**：到期复习卡的"真实通过率"——按每张卡每天第一次复习计，Again=Fail，Hard/Good/Easy=Pass。
- **如何测量**：Anki → Stats → True Retention Table；成熟卡（interval ≥21 天）与新卡分开看；官方明确"单日数据噪声大，看月数据"；FSRS 下应接近你的 desired retention。
- **适用问题**：Q1（回顾质量的第一主指标）。
- **证据等级**：一手官方。
- **链接+日期**：https://docs.ankiweb.net/stats.html （文档无发布日；检索 2026-09-20）。
- **迁移到 CLS 的形态**：收敛文档页头一行「本月回顾通过率：成熟条目 xx% / 新条目 xx%」；与目标值并排显示差值。
- **反例/失败边界**：单日数字不可用；"把 Hard 当失败、把 Again 当通过"会污染（官方在 FSRS 章节专门警告 Hard 误用）；删除卡片后统计口径会变化（官方：删除的笔记其复习历史仍保留在集合统计里）。

### A2. Desired Retention（目标保留率）与保留–负担曲线 — Anki/FSRS
- **一句话定义**：你设定的"到期时能记住"的目标比例，作为所有回顾数字的校准线；默认 90%。
- **如何测量**：Deck Options → FSRS → Desired Retention；官方给出的换算示例（沿用 SuperMemo 建议）：`新间隔修饰 = log(目标保留%) / log(当前保留%)`，例 log(90%)/log(85%)=0.65；官方提示 90% 以上工作量增长很快、97% 以上可能难以承受。
- **适用问题**：Q1（把"防遗忘"从口号变成可校准的旋钮）。
- **证据等级**：一手官方。
- **链接+日期**：https://docs.ankiweb.net/deck-options.html （检索 2026-09-20）。
- **迁移到 CLS 的形态**：页头给「目标 vs 实际」双值即可，不单独作为成绩；差值 = 该系统是否需要调整的提示。
- **反例/失败边界**：区间修饰公式是 SM-2 时代的工具（FSRS 下不用）；官方 25.07 起移除了 CMRR（最小推荐保留率）自动建议；"保留越高越好"是错误直觉——官方原文："to increase our retention by 5 percentage points, we would have to study 35% more frequently"。

### A3. Daily Load（复习负担）— Anki
- **一句话定义**：若不再加新卡、不再失败，未来平均每日到期卡数的估计值。
- **如何测量**：官方公式 `Daily load = 1/I₁ + 1/I₂ + … + 1/Iₙ`（间隔 <1 天按 1 计，防止短间隔卡把数值拉爆）；Stats → Future Due 图直接显示 daily load；同页还提供"复习用时"图（按分钟）。
- **适用问题**：Q1（防遗忘的可持续性约束）。
- **证据等级**：一手官方。
- **链接+日期**：https://docs.ankiweb.net/stats.html#future-due （检索 2026-09-20）。
- **迁移到 CLS 的形态**：页头第三个数字「预计每日回顾量：N 条 / ≈M 分钟」，让"防遗忘"受负担上限约束。
- **反例/失败边界**：官方明说该公式**不含**当前逾期 backlog（backlog 大时数字反而偏低）；也**不含**新卡；分钟数受条目难度与个人速度影响。官方规则另有经验值："每天 20 张新卡 ≈ 每天约 200 次复习"（10 倍法则，见 A4 反例）。

### A4. Backlog / 逾期积压 + catch-up 分流 — Anki
- **一句话定义**：已到期但没复习的卡片数量（"cards which you didn't study in time"），代表回顾链断裂程度。
- **如何测量**：搜索 `is:due prop:due<=-1` 计数；官方手册给出的 catching-up 分流法（社区 800 卡案例）：`Just Due: is:due prop:due>-7`（近一周到期的，每天照常做）+ `Over Due: is:due prop:due<=-7`（积压，像新卡一样限量做）；官方论坛标准操作（2024-04-19 帖）：新卡设 0 → 建 Catch-up filtered deck → 用 Descending Retrievability 排序 → 清完再恢复新卡。
- **适用问题**：Q1（回顾断层早发现）。
- **证据等级**：一手官方（手册）+ 社区自述（官方论坛，题"Adressing Backlog"，2024-04-19，Danika_Dakika；2025-06-06 帖 aoanla/Danika 关于 10 倍法则的讨论）。
- **链接+日期**：https://docs.ankiweb.net/filtered-decks.html#catching-up ；https://forums.ankiweb.net/t/adressing-backlog/43842 （2024-04-19）；https://forums.ankiweb.net/t/many-more-reviews-than-expected-with-new-card-settings/62292 （2025-06-06）。
- **迁移到 CLS 的形态**：页头「逾期未回顾条目数 + 最老逾期天数」；积压时把"新条目配额"降为 0（这是官方建议的动作，不是 CLS 设计）。
- **反例/失败边界**：官方警告 backlog 大时 Future Due 图**不显示**逾期卡（会低估）；官方建议"有 backlog 时停止加新卡"；官方论坛用户 aoanla（2025-06-06）实测 20 新卡/天但单日做到 352 张——10 倍法则只是量级估计、首两周常超量。

### A5. Lapse 计数 / Leech 阈值（水蛭卡）— Anki
- **一句话定义**：lapse = 复习卡被按 Again（说明忘了）；每张卡的 lapse 计数达到阈值（默认 8）→ 自动标 leech 并挂起（可配置）。
- **如何测量**：每卡自动累计 lapse；Anki Cards→Info 可查历史；官方阈值 8（可在 deck options 改），之后每 4 次（阈值的一半）再警告一次。
- **适用问题**：Q1（定位"反复忘记"的条目）。
- **证据等级**：一手官方。
- **链接+日期**：https://docs.ankiweb.net/leeches.html （检索 2026-09-20）。
- **迁移到 CLS 的形态**：页头可选「本月反复遗忘条目 Top N（lapse 计数）」，作为"改写法/拆小/删除"的待办入口。
- **反例/失败边界**：leech ≠ 无价值——官方给三条处置（改写、删除、暂停等待干扰消退）；对"值得记"的条目它是**改写信号**，对低价值条目才是删卡信号；阈值 8 是默认值，非科学常数。

### A6. Estimated Total Knowledge（预计仍记得的条数）— Anki/FSRS
- **一句话定义**：你现在大概还"存在脑子里"的条目总数。
- **如何测量**：官方定义 = **平均 retrievability × 至少复习过一次的卡片数**；FSRS 开启后 Stats → Card Retrievability 图直接给出；retrievability 即"回忆概率"。
- **适用问题**：Q1（"防遗忘"的存量口径：还剩多少）。
- **证据等级**：一手官方。
- **链接+日期**：https://docs.ankiweb.net/stats.html#card-retrievability （检索 2026-09-20）。
- **迁移到 CLS 的形态**：页头「预计仍记得 X 条 / 已学 Y 条（= 存量保留比）」，比单看通过率更能反映"总量保住了多少"。
- **反例/失败边界**：依赖 FSRS 参数质量与复习历史完整度（官方有"历史保留"补洞选项）；基数是"至少复习过一次"的卡，长期搁置的条目会被平均口径掩盖（官方口径如此，勿过度解读）。

### A7. Card Stability（记忆稳定度）— Anki/FSRS
- **一句话定义**：单条记忆的"保质期"：回忆概率从 100% 降到 90% 所需的时间。
- **如何测量**：FSRS 开启后 Stats → Card Stability 图；可与 desired retention 一起读（当前稳定度决定下次间隔）。
- **适用问题**：Q1（条目/主题级回顾优先级的排序依据）。
- **证据等级**：一手官方。
- **链接+日期**：https://docs.ankiweb.net/stats.html#card-stability （检索 2026-09-20）。
- **迁移到 CLS 的形态**：给条目/主题标一个"记忆保质期"，保质期短的排在收敛文档回顾区前面。
- **反例/失败边界**：需要 FSRS 与足够复习历史；全新内容没有 stability；未启用 FSRS 时该图不显示。

### A8. 遗忘指数 FI（requested vs measured）— SuperMemo
- **一句话定义**：间隔复习时"没想起来"的元素占比；目标值（requested）与实测值（measured）分开记。
- **如何测量**：官方建议新手用 10%（可选范围 3%–20%；"多数情况 8%–13% 最合适"）；Statistics 窗口显示 Measured FI；FI 与平均保留率的换算公式 `retention = -FI / ln(1-FI)`（10%→94.91%，3%→98.49%，5%→97.47%，15%→92.29%，20%→89.62%）。
- **适用问题**：Q1（同一件事的两个口径：到期时点通过率 vs 区间平均保留率——引用时须写死是哪一个）。
- **证据等级**：一手官方（supermemo.guru 为 Wozniak 官方 wiki；产品手册 help.supermemo.org 同源，本链路 CAPTCHA 未直接打开）。
- **链接+日期**：https://supermemo.guru/wiki/Forgetting_index ；https://supermemo.guru/wiki/Forgetting_index_in_SuperMemo ；https://supermemo.guru/wiki/Retention （均检索 2026-09-20）。
- **迁移到 CLS 的形态**：页头保留率数字旁加一行小字注口径（"到期未通过率"或"区间平均遗忘率"），避免同一记录两种读法。
- **反例/失败边界**：官方自述 measured 通常高于 requested（尤其 FI<5%）；拖延复习、跳过某天、Postpone 都会推高 measured；过载时**低优先级条目的 measured FI 按设计变高**——不同优先级数字不能混算平均值；官方还警告"降低 FI 不划算，成本指数级上升"。

### A9. 优先级队列 Priority Queue — SuperMemo
- **一句话定义**：把待复习知识按重要性排序的队列，只对高优先级知识执行严格的遗忘指数；官方称其为"保留率–工作量困境"的最佳解法。
- **如何测量**：逐元素设置 priority（增量阅读流程里会被反复"上浮/下调"——up-prioritize）；官方原文："only top-priority knowledge is subject to strict review (as determined by the forgetting index)"。
- **适用问题**：Q1（不可能全量严格复习时的取舍机制）。
- **证据等级**：一手官方（supermemo.guru 术语页；priority 0%–100% 的具体刻度在 help.supermemo.org，本链路 CAPTCHA 未直接核验）。
- **链接+日期**：https://supermemo.guru/wiki/Priority_queue ；https://supermemo.guru/wiki/Forgetting_index （均检索 2026-09-20）。
- **迁移到 CLS 的形态**：页头拆成「高优先级条目保留率 / 其余条目保留率」两栏，代替一个全局数字。
- **反例/失败边界**：优先级是人给的（半客观），会漂移；SuperMemo 的官方说明也把它定位为困境折中而非质量证据；优先级只解决"先看谁"，不回答"看得对不对"。

### A10. 重浮半衰期与回忆概率（Recall Probability ≤50%）— Readwise Mastery
- **一句话定义**：每条 highlight 有一条"回忆概率半衰期"；概率衰减到 ≤50% 才有资格被重浮到 Daily Review 后半段。
- **如何测量**：官方参数：初始半衰期 soon=7 天 / later=14 天 / someday=28 天；`readwise.io/mastery` 页展示全部卡片的半衰期与回忆概率；重浮时按"回忆概率最低者优先"；文档被抽中的频率 ∝ 该文档 highlight 数占比（官方例子：500 条总量中某书占 100 条 → 20% 概率）。
- **适用问题**：Q1（"什么该被重新看见"的显式规则）；兼 Q3（重浮/推荐策略）。
- **证据等级**：一手官方（Readwise Docs 自述算法"a bit of a black box"，只公开机制骨架）。
- **链接+日期**：https://docs.readwise.io/readwise/docs/faqs/reviewing-highlights ；https://docs.readwise.io/readwise/guides/mastery （均检索 2026-09-20）。
- **迁移到 CLS 的形态**：页头「衰减过半（回忆概率 ≤50%）的条目数」= 待重浮队列长度。
- **反例/失败边界**：官方自认是简化黑箱；初始半衰期是固定档位而非个体校准；频率机制偏向 highlight 多的文档（官方建议用户手动 tune down/up），即"重浮率"天然受资料分布偏置。

### A11. Savings 省时分数 — Ebbinghaus（Murre & Dros 2015 复制）
- **一句话定义**：第二次学习比第一次省下的时间比例，间接口径的"还记得多少"。
- **如何测量**：`savings = (T_初学 − T_重学) / T_初学`；官方论文例：初学 25 次、一天后重学 20 次 → 5/25 = 20%；复制实验中 31 天点的 savings≈0.041（校正干扰后 0.137），短间隔点在 0.20 量级。
- **适用问题**：Q1（"重读成本是否下降"的半客观代理，适合抽样条目）。
- **证据等级**：一手（学术）：Murre & Dros, PLOS ONE 10(7): e0120644。
- **链接+日期**：https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0120644 （2015-07-06；原始方法 Ebbinghaus 1885）。
- **迁移到 CLS 的形态**：抽样测「重读某条目用时 ÷ 首读用时」的比值趋势，作为"回顾有效"的时间证据。
- **反例/失败边界**：论文原文明说 "researchers found the savings method too unreliable compared with other methods"；单被试设计、疲劳/前摄干扰会污染时间测量（论文自曝 31 天点异常低值）；不适合全量自动采集。

### A12. 最优间隔比（spacing：gap / 测试延迟）— Cepeda et al. 2008
- **一句话定义**：复习间隔存在最优值，且最优间隔 ≈ 目标保留时长的固定比例，随目标期限变长而缩小。
- **如何测量**：`optimal gap ÷ test delay` 的实测比例：1 周延迟约 20–40%；1 年延迟约 5–10%（N>1,350 人；间隔最长 3.5 个月、终测延迟最长 1 年；在给定终测延迟下，间隔先增后减）。
- **适用问题**：Q1（"什么时候回顾"的可计算默认档）。
- **证据等级**：一手（学术）：Psychol Sci, 2008-11（PMID 19076480）。
- **链接+日期**：https://pubmed.ncbi.nlm.nih.gov/19076480/ （2008-11；检索 2026-09-20）。
- **迁移到 CLS 的形态**：页头给出「当前条目平均间隔 ÷ 距今时间」的档位（目标保留 1 年 → 约 5–10%）供人工核对。
- **反例/失败边界**：群体最优≠个体最优；材料异质性大；与 Bjork 的"表现–学习"警告叠加时——间隔太短会"当场记得、长期学不到"（见 A13）。

### A13. 检索练习优先于重读（testing effect）— Roediger & Karpicke 2006 / Rowland 2014
- **一句话定义**：回顾动作存在客观"分级"：先回忆（检索练习）>重读；且这个优势只有在**延迟测试**上才显现。
- **如何测量**：实验口径——5 分钟后测：重复学习更好；延迟测（2 天/1 周）：先测试组显著更好（R&K 2006 摘要原文："on the delayed tests, prior testing produced substantially greater retention than studying, even though repeated studying increased students' confidence"）；元分析口径：初始"回忆式测验"的收益大于"再认式测验"（Rowland 2014）。
- **适用问题**：Q1（回顾方式本身的评价标准）。
- **证据等级**：一手（学术）：Psychol Sci 2006-03（PMID 16507066）；Psychol Bull 2014-11（PMID 25150680）；Bjork & Bjork 2011 章节（desirable difficulties，含"interleaving 63% vs 20% 一周后"等数据点）。
- **链接+日期**：https://pubmed.ncbi.nlm.nih.gov/16507066/ ；https://pubmed.ncbi.nlm.nih.gov/25150680/ ；https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/04/EBjork_RBjork_2011.pdf （2011；均检索 2026-09-20）。
- **迁移到 CLS 的形态**：把"回顾"动作默认为先自述/回忆再看原文，并在页头提示行写出这一步（方式标准，不评现有交互）。
- **反例/失败边界**：即时测会输给重读（"表现≠学习"陷阱，Bjork）；无反馈的重复测试可能收益有限；difficulty 只有在学习者已有背景知识时才是"desirable"，否则变成"undesirable difficulty"（Bjork & Bjork 原文明确此边界）。

### A14. Zettel/字数产出计量 — zettelkasten.de
- **一句话定义**：用"写下来的条数/字数"衡量知识工作的产出与趋势（非记忆口径的回顾代理）。
- **如何测量**：帖主自述三个数字：① Zettel/天（或每会话）；② 深度工作日字数 2000–3000 →（2017 改进后）4000–10000；③ 年总量 3000 → 6000 个 Zettel；另有"改进后 +10.04%"的对比。
- **适用问题**：Q1（"回顾自己干了什么"的产出面）。
- **证据等级**：社区自述（zettelkasten.de 作者 Sascha；2021-04-15；评论区有 Christian 的补充）。
- **链接+日期**：https://zettelkasten.de/posts/measure-your-goals/ （2021-04-15）；https://zettelkasten.de/posts/count-your-words/ （2014-02-06）。
- **迁移到 CLS 的形态**：页头放「本周新增/改动条目数与字数」作为**回顾触发线**，不作为质量线。
- **反例/失败边界**：同页评论区自曝反例——"同一个数字对甲是生产力，对乙是 vanity metric"；字数增长也可能对应"收藏家谬误"（收藏/书写 ≠ 学会）。

### A15. Obsidian 社区插件的统计面板 — obsidian-spaced-repetition
- **一句话定义**：笔记/闪卡级复习的现成统计视图：Forecast（未来到期数）、Intervals（间隔分布）、Eases（易度分布）、Card Types（New / Young / Mature，Mature = 间隔 > 1 个月）。
- **如何测量**：插件设置 → Statistics 区；配合 `#review` 标签的 note review queue（整个笔记进复习队列）。
- **适用问题**：Q1（"笔记级"复习队列与成熟度分层的社区先例）。
- **证据等级**：社区自述 / 开源工具文档（作者 st3v3n 发布帖 2021-04-14；文档站持续更新，检索 2026-09-20）。
- **链接+日期**：https://stephenmwangi.com/obsidian-spaced-repetition/flashcards/statistics/ ；https://forum.obsidian.md/t/plugin-for-flashcards-note-level-spaced-repetition-all-inside-obsidian/16498 （2021-04-14）。
- **迁移到 CLS 的形态**：页头可做「未来 7 天待回顾队列 + 成熟度分层（新/熟）」两行，对应上面的 Forecast + Card Types。
- **反例/失败边界**：发布帖第 2 楼（davecan，2021-04-14）当场指出：SM 式增量阅读需要的是 **priority** 而不是 difficulty，该插件长期没有内建优先级——"看得见的统计"≠"值得复习的排序"。

### A16. 创作期 → 巩固期（元素峰值 → 成稿月数）— SuperMemo 增量写作
- **一句话定义**：把"回顾/整理"看成一个有峰值的两段过程：创意期元素数上升，巩固期元素合并为成稿；官方示例给出月级节奏。
- **如何测量**：官方案例图描述——创意阶段约 5 个月达到想法峰值，10 个月后合并为 180 章成稿（"ideas for a book peak in 5 months of creative elaborations, only to consolidate into a 180-chapter text 10 months later"）。
- **适用问题**：Q1（"回顾产出"的时间尺度参照）；兼 Q4（给人看的收束节奏）。
- **证据等级**：一手官方（supermemo.guru，"Incremental writing"）。
- **链接+日期**：https://supermemo.guru/wiki/Incremental_writing （检索 2026-09-20）。
- **迁移到 CLS 的形态**：页头标注"本次收敛处于创意期还是巩固期"及距上次峰值的天数——巩固不是单日动作（呼应任务书 §2.3）。
- **反例/失败边界**：示例是作者单案例（自家书稿）非受控数据；"5 个月/10 个月"不可当基准值，只能当"巩固需要以月计"的定性证据。

## 3. 受限来源（未直接打开，仅登记，不当作一手核验）

### 3.1 r/Anki（全链路 403；以下为搜索引擎索引快照，取得于 2026-09-20）
| 帖子 | 快照日期 | 快照引文（片段） |
|---|---|---|
| "Too Many Anki Reviews? How to Clear an Overwhelming Backlog of Reviews" | 2021-07-09 | "By multiplying your new cards by seven, you can approximate the number of reviews every day." |
| "How many reviews a day do you guys do?" | 约 2026-08（显示 "1 month ago"） | "You can expect your long-term review load to be up to 10x your daily new card limit." |
| "I have a 4000+ card backlog, and I need help" | 约 2026-05（显示 "4 months ago"） | "how many cards I should do per day to avoid accumulating more reviews … it would be 250+." |
| "do retention rates vary by content matter?" | 2025-03-29 | "in the latest version of Anki you can look at the True Retention table in Stats to find out your real retention." |

链接（仅登记，链接受限）：https://www.reddit.com/r/Anki/comments/oh2tb3/ ；https://www.reddit.com/r/Anki/comments/1vjuy7r/ ；https://www.reddit.com/r/Anki/comments/1t38f7a/ ；https://www.reddit.com/r/Anki/comments/1jmsry1/
获取方式：Anysearch 检索快照 + r.jina.ai（www / old / .rss / .json 四种形态均 403）。**未直接打开原帖，不保证完整上下文。**

### 3.2 help.supermemo.org（CAPTCHA）
- `Incremental_reading`、`Statistics`（含 `action=raw` 尝试）均返回人机验证页；本报告 SuperMemo 指标取自其同源官方 wiki（supermemo.guru，Wozniak 维护），并在此标注差异。
- 待下游核验点：Statistics 窗口中 Measured FI 的确切展示字段；priority 刻度的原文（0%–100% 目前只有检索快照佐证）。

### 3.3 未采到出处的说法（不入库）
- "Readwise 日回顾 ≈ 5 分钟"、"你会忘记 75%"（任务书 §2.4 引用）：在 docs.readwise.io 相关页与 readwise.io 首页本轮均未直接找到原句，故本报告不收录；如需使用请补链。

## 4. 页头候选（≥2，实际给出 5）

| 排序 | 指标 | 为什么够格当页头（一行） |
|---|---|---|
| ★1 | **A1 True Retention（分成熟/新）** | 官方定义明确、公式无歧义、按月读噪声可控，是"防遗忘"最直接的存量指标。 |
| ★2 | **A3 Daily Load（条/分钟）** | 官方公式 Σ1/I 可直接计算；给"防遗忘"配一个可持续负担上限，防止指标反噬。 |
| ★3 | **A4 Backlog（逾期条数 + 最老逾期天数）** | 纯计数、无公式争议；是"回顾链是否断了"的早期警报。 |
| ★4 | **A6 Estimated Total Knowledge（仍记得的条数/占比）** | 官方口径一句话可写清；比"通过率"更贴近"沉淀还剩多少"。 |
| ★5 | **A10 重浮队列长度（回忆概率 ≤50% 的条目数）** | 规则的触发条件由官方公开；与"重浮率"诉求（任务书 §2.4）直接对应。 |
| 备选 | A2 目标保留率 | 只配 A1 作校准线，不单独当成绩；口径：目标 vs 实际差值。 |

## 5. 采集侧自检与未决项（不涉及 CLS 设计判断）

- 底线产出自检：量化标准 **16 条 ≥ 6**；可直接进页头 **5 条 ≥ 2**；每条均含出处链接与日期或检索日期。
- 未决/需复核：
  1. SuperMemo 官方手册（help.supermemo.org）未直接核验，SuperMemo 条目均注明此限制。
  2. r/Anki 仅快照（403）；如需一手引文与准确日期，需走 agent-reach 的 Reddit 登录后端（OpenCLI 扩展或 rdt-cli）。
  3. Readwise 的"5 分钟/75%"说法未找到出处，未收录。
  4. "复习用时/字数/重读时间"这类时间指标在 CLS 侧是否可稳定采集，属实现面，本路线按边界不评估。
  5. GitHub 的 obsidian-spaced-repetition Statistics wiki 页经阅读器访问被 GitHub 反滥用策略拦截（403），改用同项目官方文档站（stephenmwangi.com），两者同源。
