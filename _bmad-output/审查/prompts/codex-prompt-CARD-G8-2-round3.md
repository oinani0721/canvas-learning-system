# CARD-G8-2 独立对抗审查（round-3 · 终轮复核）

你是独立审查者。round-1/round-2 判 FAIL（存档 codex-review-CARD-G8-2.md 与
codex-review-CARD-G8-2-round2.md）。本轮是**终轮**（卡文停轮规则：BLOCKER/HIGH 续轮最多 3 轮），
复核整改后的车道 `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint`。

工作目录 = 上述车道根。**只读审查，不要修改任何文件。**

## 一、round-2 逐条整改声明（证伪优先，标 REGRESSED 若不成立）

| # | round-2 发现 | 声明的整改 | 验证要点 |
|---|---|---|---|
| HIGH-1 三旁路 | 目录 symlink 后代 / dangling 静默消失 / recap 二次读取 | `_scan_block_reason` 统一边界守卫（复用 cvr `_resolves_inside_vault` realpath 整链判定）接入 orphan 两循环 + recap 循环；`_iter_md` 放宽 `is_file() or is_symlink()` 保 dangling 在列；四段 fixture 配**专属原因断言**（每层防线有专属判别锚） | 乙段（源目录本身 symlink）应仍报孤儿；dangling 显式记盲区原因；recap 越界记 recap_blind；变异 M12a/M12b 已杀 |
| HIGH-4 末项 | AUTO 段与围栏交叉 | **决定不处理**，登记进验收单 §6.1「不比什么」：真实生成器不产出此形态、哨兵块明写"⛔ 请勿手改"、构造它需精确伪造生成器输出——请评估该登记结案是否可接受 | 查 UAT §3 表 + §6.1 |
| HIGH-5 | 空 `[[]]` 用例无判别力 | 用例重写：板里只有空链，A 必须报；空链映射变异可杀 | 隔离实跑 baseline 与变异 |
| HIGH（新） | 存档未绑定当前字节 | evidence-g82/MANIFEST.txt 绑定源码/测试/证据 sha256 + 失效条款 | 核对 MANIFEST 与当前字节 |
| MEDIUM-1 | 子目录同 basename 自贡献假阴；quoted-null | 入链豁免统一「排除自身来源」；null 判定在剥引号前，只认裸 null/Null/NULL/~ | 你的 d1/A→d2/a fixture：A 应报、a 不应报；`"null"` 引号串应豁免 |
| MEDIUM-2 | 时钟测试环境依赖 | patch vl.datetime 固定钟 + 时区对象换 New York（环境无关结构判别） | `TZ=UTC` 环境下重跑该单测应仍绿 |
| MEDIUM-3 | UAT:89 过宽 | 全文统一"排除 今日复习.* 后的全树"；被排除文件显式不在承诺内 | grep UAT |
| MEDIUM-4 | import-as-library pyc；门是测试自设 | docstring/--help/§4-A 如实声明 Python 机制边界；新增**行为门** tmp 副本无环境变量实测 0 pyc | 复跑该行为门 |

## 二、round-2 之后的**新发现与整改**（自查如实申报）

⛔ 如实申报一项本卡自查抓出的**重大缺陷**：round-2 变异 M8/M12a/M12b SURVIVED 的真凶是
本卡测试文件**同名测试函数重复定义**（`test_orphan_symlink_never_read` 旧版残留，
后定义覆盖前定义，pytest collect 只执行无判别力版本）——变异首跑抓出后整改：删旧版 +
`test_no_duplicate_test_names` 防回归门 + MEMORY 条目。请复核该门有效。

## 三、评估基准

- 终态裁判（当前字节，MANIFEST 绑定）：176 passed（57+119）+ 14/14 变异 KILLED（transcripts/）+
  live 三轮取证 sha 逐字相同（round-3 rc=0 全 ok，09:33 实测 = 结构性窗口自愈的实证）+ 禁改门空。
- round-2 你独立复跑过 171 门与 M1-M10 全绿——请对本轮终态（176 门/14 变异）再独立复跑一次
  裁判 1 与抽查变异 transcript。
- round-1/2 每条 HIGH/MEDIUM 的「整改声明表」在 round-3 提示词与 UAT 附 B。

## 四、停轮条款（卡文）

BLOCKER/HIGH 续轮最多 3 轮。round-3 是终轮：若仍有 BLOCKER/HIGH，按卡文「到顶未清零 → 验收单
显著声明、不合并、留台账 §一」处置——请在结论区明确给出：
(a) 清零与否；(b) 若未清零，剩余 BLOCKER/HIGH 是否属于「登记结案可接受」类（如 AUTO-fence 交叉
这类构造性前提），并给出你的分级建议（可合并 / 须再修 / 不可合并）。

## 五、输出格式

BLOCKER/HIGH/MEDIUM/LOW 分级 + file:line + 具体失败场景 + 实跑命令与输出。
round-1/2 各条若整改不成立标 REGRESSED。
最后一行必须是：`BLOCKER/HIGH 清零：是` 或 `BLOCKER-COUNT: n; HIGH-COUNT: m` 形式 + 明确结论。
