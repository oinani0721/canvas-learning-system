# CARD-G8-2 独立对抗审查（round-12 · 用户授权定向续轮第九轮 · 收敛快审）

你是独立审查者。round-1..11 存档于 codex-review-CARD-G8-2*.md。**本轮为收敛快审**——
round-11 后仅做了小修（词边界/anomaly key/LOW 项），**核心解析未动**；重点是复核小修本身
与确认登记框架，不要求重新扫描全部历史面。工作目录 =
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint`。
**只读审查，不要修改任何文件。**

## 一、round-11 发现的整改声明（逐条快审）

| # | round-11 发现 | 整改 | 快审要点 |
|---|---|---|---|
| H2a | `/AUTO-GENERATED-NESS` 连字符后缀误匹配 END | lookahead 去掉 `\|-` 分支（`(?=$\|\s|-->)`） | 你的 NESS fixture：深度不关，A 报孤儿；新门 test_hyphen_suffix_end_does_not_close |
| 新发现 | BEGIN 同样无词边界（sync…EVIL 误开） | `_AUTO_BEGIN_RE` 同样加 lookahead | EVIL fixture：真实 [[A]] 不盲化（A 不报）；新门 test_evil_suffix_begin_does_not_open |
| r11 M-anomaly | 同文件多条 anomaly 同 key last-write-wins | key 唯一化（含行号/原因）；新门 test_auto_anomaly_keys_are_unique | 多 anomaly fixture 逐条可见 |
| r11 M-\Q | harness `\Q` 转换为死路径 | 删除占位分支 | bash -n 语法过；22 锚全命中 |
| r11 LOW | harness 头注 round-8 过时；测试注释区间法残留 | 头注 round-11；测试注释清理 | 抽查 |
| **登记接受** | H1（AUTO 内 fence 交互）、H3（同名碰撞）、B3（三连反斜杠） | **构造性深水区口径边界**——登记于 UAT 顶部登记表 B1/B2/B3，修复需 orphan 权威口径用户裁决 | 请评审登记的**完备性与理由**是否成立（这是收束框架的核心请求） |

## 二、round-11 M 项落地核对

- M1：UAT §7 登记条目核对（markdown-it 依赖移交；`DEBT-1` 名称误用已更正为直接声明移交）。
- M2：UAT 全文统一 round-12 终态——顶部「终态裁定」重写为唯一权威入口，正文历史段
  标注时点快照；§6.10 轮次史补 r6-r11。
- M3：live sha 覆盖面收窄声明核对 §6.11/登记表。
- M4：权威口径声明（mdit 4.0.0 可渲染文本）入 `_wikilink_targets` docstring + UAT；
  `<span>[[A]]</span>` 场景 mdit 实测 text 内 [[A]] 被扫——与你 r8 实测一致——
  **生产图口径差异**（wikilink_graph_service.Vault.connect）登记为裁决点。

## 三、终态裁判（当前字节，MANIFEST 绑定）

referee1-pytest-full-round12.txt = **208 passed**（89 本卡 + G8-1 119 零回归）+
22/22 锚位 KILLED（M23 锚已按 round-11 字节重锚：含 r9 注释行三行形态）+
live 第十三轮（round-12）取证 sha `a82e3af0…` 前后逐字相同 rc=2（09-02 凌晨结构性 stale）
+ 禁改门空 + MANIFEST 全覆盖（生成于全部证据落定之后）。

## 四、收束框架请求（本轮核心）

**十轮对抗的模式已确认**：r4-r11 每轮修复均在 `_wikilink_targets` 的 Markdown 语义解析上
开新洞——该面的反例空间无限（CommonMark × Obsidian Flavored × 生产图三口径叠加）。
本卡的收束框架：
1. **解析 = markdown-it-py 4.0.0 token 流**（库内语义不重写、不变异、集成测试锁定）；
2. **AUTO 段 = 项目自定义结构**，等行数盲化（保留缩进/纯 fence 标记行）+ 结构异常
   anomalies 显式披露；
3. **构造性深水区登记**（B1 AUTO-fence 交互 / B2 同名碰撞 / B3 三连反斜杠）——真实
   生成器形态不可达 或 需 orphan 权威口径用户裁决；
4. 裁决点：**orphan 权威 = mdit 可渲染文本 vs 生产图边 vs Obsidian 渲染**——需用户裁决，
   裁决后若生产图为准则改用生产图边集合比对（G 系卡范围）。

请评审：(a) 该框架是否构成可接受的收敛状态；(b) 登记表 B1/B2/B3 是否完备（有无遗漏的
同级别构造面）；(c) 小修本身有无新面。若你认定仍有**非构造性**的新 HIGH，请按常规分级报出。

## 五、输出格式

分级 BLOCKER/HIGH/MEDIUM/LOW + file:line + 具体失败场景 + 实跑命令与输出。
最后一行：`BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否（BLOCKER: n, HIGH: m）`。
