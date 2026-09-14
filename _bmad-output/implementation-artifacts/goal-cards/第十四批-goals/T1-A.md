> ⚠️ 本文件是 CARD-G2-9-F2 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十四批手册 §三 T1-A 块。
> 批次标记 `[BATCH-2026-09-11-第十四批 / CARD-G2-9-F2]`。车道：`card-t1-lance`（分支 `card/t1-lance`，**NEW @ `08100483`（B14_BASE）**，venv 目录级 symlink 已建、`backend/.env` 已拷），本车道第 1/2 张（首卡**无前提**，HEAD 必须 = `08100483` 且 `git status --porcelain` 空），之后串 **T1-B CARD-G2-9-F1-canary**。用户已裁：**R-01**（G2-9-F2 = 第十四批第一张、数据丢失面、合并队列 §2 首批）/ **D-15**（有代码改动多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH=0，上限 5）/ **D-32**（纯注释·docstring 尾巴不占轮次不重置，主 session 逐行等价核）；D-12 遗留「轮次上限被当不修挡箭牌」的讨论由本卡的文案类改动落地（A-4/B-9/`:874` docstring）。勘探 2026-09-11 于主干 `08100483`（恢复勘探 C §1 全锚 + 波 0 实测；勘探 A §B.1 F2 顺带项 + 裁定请求 §三）。协议（⛔ 必须读 **feature 主干树 `--add-dir` 那份**）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md`（§1 合并门 + D-15 轮次 / §2.1 存档首部 / §2.2 裁判落盘 + --no-color + ruff zsh 数组 / §2.3 过渡 / §3 最低覆盖）。手册同理只读主干树那份：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-11-第十四批开跑手册-10车道43卡.md`（§零 / §一 / §四）。⚠️ **协议与手册两份都只认 feature 主干 `--add-dir` 那份；车道树自己的 `.claude/rules/card-batch-protocol.md` 是 `08100483` 版，本批的任何回写只发生在 `--add-dir` 那份——别读车道树那份，也别往车道树那份写。**

# CARD-G2-9-F2 — 最长前缀优先归属，解「短 id vault 单向认领长 id vault 的表」跨 vault 删表面（`resolve_table_name` / `_owns_table` / `_fingerprint_table_name` 三处同口径一张卡）

## 〇 事实
| 事实 | 位置 / 实测命令 |
|---|---|
| **路径**：生产侧唯一文件 `backend/lib/agentic_rag/clients/lancedb_client.py`（4045 行，`find . -name lancedb_client.py` 唯一命中）。在 `backend/lib` **不在 `backend/app`** ⇒ 不触发 lefthook `python-typecheck`（glob `backend/app/*.py`）、不计长度门 ⑩（本批 APP_CARDS 不含 T1-A）。`08100483..HEAD`（e58d5c5c 纯文档 commit）对本文件、测试文件、canary 三者 `git diff --stat` 为空 ⇒ HEAD 树代码 = B14_BASE | `git diff --stat --no-color 08100483 HEAD -- backend/lib/agentic_rag/clients/lancedb_client.py …`（本次写卡实测空） |
| **归属规则三处同形 + 一处拼接侧**（F1 已把规则收成 `_owns_table` 单点，但 `startswith` 口径未改，F2 本卡改它）：`resolve_table_name :768-798`（`:796 if table_name.startswith(f"{vid}_"): return table_name` / `:798 return f"{vid}_{table_name}"`，双前缀幂等守卫）；`_owns_table :841-904`（`:901 vid = self.active_vault_id if vault_id is _UNSET else vault_id` / `:902-903` 裸表分支 `return "_" not in name or name == self.FINGERPRINT_TABLE` / **`:904 return name.startswith(f"{vid}_")`**）；`_fingerprint_table_name :1065-1081`（**无 startswith，是拼接侧** `:1080 return self.FINGERPRINT_TABLE` / `:1081 return f"{vid}_{self.FINGERPRINT_TABLE}"`）；`_UNSET = object()` `:582`（哨兵三态） | `python3 -c "import ast…"` AST 取端点（见 §二.1） |
| ⛔ **口径更正 1（承重）**：勘探 C §1.1 写「`startswith(f"{vid}_")` 字面量实测恰 2 处」——**本次写卡 `grep -cF` 实测 = 3**：`:796`（resolve 活代码）/ **`:874`（`_owns_table` docstring 里描述缺陷的那段）** / `:904`（`_owns_table` 活代码）。⇒ 判据「改前期望」**必须写 3 不是 2**；改后 0（两处活代码换最长前缀 + `:874` 那段「移交 CARD-G2-9-F2 未闭合面」的 docstring 随缺陷闭合一并重写，否则 `grep` 判据卡在 1 不归零）。`_fingerprint_table_name :1081` 是拼接侧、不含 startswith（与 recon 一致） | `grep -nF 'startswith(f"{vid}_")' backend/lib/agentic_rag/clients/lancedb_client.py` → `:796 :874 :904`（本次写卡实测） |
| **缺陷根因（`_owns_table :874` docstring 原文摘）**：前缀口径 `startswith(f"{vid}_")` ⇒ 短 id vault **单向**认领长 id vault 的表——`"a_b_canvas_nodes".startswith("a_")` 为真，vault `a` 的启动自愈会 drop 掉 vault `a_b` 的漂移表；需**下划线边界**（`ab_canvas_nodes` 与 `a` 不碰撞）。本仓可达：`app.config.sanitize_vault_id` 产出含下划线的 id（`cs 61b`→`cs_61b`、`canvas-vault`→`canvas_vault`），vault `cs` 与 `cs_61b` 并存即触发 | `sed -n '841,905p'` + `grep -nF 'sanitize_vault_id' backend/app/config.py`（只读核，不改 config） |
| **消歧必须拿全量 vault 列表**（裁定请求 §三「移交 CARD-G2-9-F2」原文）：`a_canvas_nodes` 既可能是 vault `a` 的 `canvas_nodes`、也可能是 vault `a_canvas` 的 `nodes`——**不知道 vault 列表就无法消歧**；B 方案（保守）已被否。⇒ F2 做**最长前缀优先**：给定 vault 集合 V，`t` 归属 `vid` ⟺ `vid` 是 V 中「`t == v` 或 `t.startswith(v + "_")`」成立的**最长**那个 v。举例 V={`a`,`a_b`}：`_owns_table("a_b_canvas_nodes","a")` → **False**、`_owns_table("a_b_canvas_nodes","a_b")` → **True**、`_owns_table("a_canvas_nodes","a")` → **True** | 裁定请求 `CARD-G2-9-F1-裁定请求.md` §三；本卡 §一 (c) |
| ⛔ **口径更正 2（vault 列表来源未定，必须本卡选定并证明）**：设计稿列三选一——① `.canvas-config.yaml` 枚举 / ② `vaults_root` 目录列举 / ③ **LanceDB 表名反推**（从 `_all_table_names()` 里抽下划线前缀段）。三者各有边界（① 单 vault 配置多半不列全部 vault；② 需文件系统遍历、可能越现网只读线；③ 自包含但「零表 vault」与「active vault 自身」不在表里时要显式并入）。F2 **必须选定一种、在验收单写明依据与边界**，并保证不连现网、不越地盘；active vault 必须恒在 V 里 | 设计稿 §4 T1-A 口径更正；本卡 §一 (c) |
| **缺陷锁（xfail）/ 前提门**（测试文件 `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py`，526 行）：`xfail(strict=True, reason=_OVERLAP_XFAIL_REASON)` 标记**恰 2 处**（`:491` → `test_prefix_overlap_not_touched_by_cache_tables` def `:492`；`:505` → `test_prefix_overlap_not_touched_by_drop_vault_tables` def `:506`）；前提门 1 个函数 `test_prefix_overlap_premises_hold` def **`:464`**（装饰器 `:462 @parametrize(("consumer","table"),_OVERLAP_CASES)` + `:463 @parametrize(("shape","filler"),_OVERLAP_SHAPES)`），前提断言 **`:485 assert env["client"]._owns_table(table, "a")`**（消息「前提失效：… 前缀口径可能已被修好，此时应删掉门⑤ 族的 xfail 标记」） | `grep -cF 'xfail(strict=True, reason=_OVERLAP_XFAIL_REASON)'`（=2）+ `grep -n 'def test_prefix_overlap'`（464/492/506） |
| ⛔ **口径更正 3**：「6 条 `xfail(strict=True)`」「6 条前提门」都是 **nodeid 数**（2 标记 × 参数化 2+4、1 函数 × 2×3）。判据 `grep -cF 'xfail(strict=True, reason=_OVERLAP_XFAIL_REASON)'` 期望 **2**，**不是 6**；`grep -cF 'xfail(strict=True'`（不带 reason）会误命中 `:35` docstring 那行得 3，⛔ 判据必须带 `, reason=_OVERLAP_XFAIL_REASON` 全串 | recon C §1.6；本次写卡实测 `:35`/`:491`/`:505` 三行 |
| **XPASS 三成因（`_OVERLAP_XFAIL_REASON :382-395` 原文，修后分辨）**：(1) F2 把归属修好 ⇒ 同族前提门的 `_owns_table(table,"a")` 断言同时翻红，两者一起变色；(2) 有人撤掉分页收口 ⇒ 只 page-outer 那几例 XPASS 而前提门仍绿；(3) 删除本身失败、异常被 `drop_vault_tables` 的 `except: pass` 吞掉 ⇒ 表保留、归属与分页都没变，只这条锁变绿。⇒ 遇 XPASS 先按三条分辨再动标记，**验收单逐条写明本卡命中的是 (1)** | `sed -n '382,395p' backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py` |
| **参数化常量**：`_OVERLAP_SHAPES :366 = [("page-inner",0),("page-outer",10)]`；`_OVERLAP_CASES :373`（3 项：`("cache","a_b_canvas_nodes")` / `("drop","a_b_canvas_nodes")` / `("drop","a_b_file_fingerprints")`）；`_OVERLAP_DROP_TABLES :379`；`_OVERLAP_XFAIL_REASON :382` | `grep -n '_OVERLAP_' backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py` |
| **`drop_vault_tables :937-948` 吞异常**：`:941 tables = self.list_vault_tables(vault_id)` → `:944 self._db.drop_table(tname, ignore_missing=True)` + `:945 pop` → **`:946 except Exception:` / `:947 pass`**（成因(3) 的来源：删失败被静默吞掉）→ `:948 return len(tables)`（返回的是**尝试**删的数，不是实删数） | `sed -n '937,948p'` |
| **`_cache_tables :1020-1056` 指纹豁免**：`:1045 owner_vault = self.active_vault_id` → **`:1049 if self._owns_table(t, owner_vault) and not t.endswith(self.FINGERPRINT_TABLE)`**（⛔ 勘探稿/早期卡文写的 `:1048` 是 off-by-one——`:1048` 实为 `for t in self._tables_cache`；本次写卡 `grep -nF` 实测归属条件在 `:1049`。⇒ 现场一律按**两字面量**重锚，不按行号）；指纹表 endswith 豁免只在这条路径；源码门 `test_rag_stage1_index_contracts.py` 靠 `endswith`/`FINGERPRINT_TABLE` 两字面量，**禁删** | `grep -nF 'and not t.endswith(self.FINGERPRINT_TABLE)' backend/lib/agentic_rag/clients/lancedb_client.py` → `:1049`（本次写卡实测）；`sed -n '1044,1052p'` |
| ⛔ **口径更正 4（`:3825` 自愈链行号已漂）**：UAT-CARD-G2-9-F1-2026-09-08.md 的『剩余默认分页站点登记』条目写的「剩余默认分页站点 `:896`/`:1080`/`:3825`/`:3834`/`:3938`」取自更早审 SHA，**在 `08100483` 上全部漂移**。实测 `_all_table_names()`（F1 新增全量收口）消费点 `:822 :917 :1028 :3740`；仍走默认分页 `self._db.table_names()`（无 limit、≤10 盲区）的残余站点 = **`:924 :1112 :3857 :3866 :3970`**，另 `:839` 已是 `table_names(limit=10_000)`。⇒ 「顺带 `:3825` 自愈链收口」= **登记不阻断**（属 `_check_and_fix_dimension_mismatch`/`add_documents` 自身面，本卡只读重锚、不硬性要求改；若改须用 `grep -nF '.table_names('` 现场重锚，不照抄 `:3825`） | `grep -nF '.table_names(' backend/lib/agentic_rag/clients/lancedb_client.py`；`grep -nF '_all_table_names' …`（本次写卡实测） |
| **F2 顺带项（勘探 A §B.1 + UAT-G2-9-F1）**：**B-3 MEDIUM** 指纹表夹具用普通向量行、不能证明「健康可用的指纹基线」被删 ⇒ 改夹具为**真实指纹 schema**；**A-4 LOW** 缺陷锁 docstring「三态两两可区分」未同步 §五 撤回；**B-9 LOW**「`-k` 会打乱执行顺序」措辞过宽（`-k` 只筛选不重排）——A-4/B-9 是纯 docstring 文案（D-32 不重置轮次，但主 session 逐行等价核） | UAT-CARD-G2-9-F1-2026-09-08.md 条目「B-3」「A-4/B-9」（行号会漂，按条目名核） |
| ⛔ **排批期裁定（最高优先，与本卡文任何措辞冲突时以裁定为准，开工必读全文）**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-09-14-第十四批排批期裁定-R-B14.md`。与本卡直接相关：**R-B14-2**（`tests/unit` 基线自证唯一口径 `grep -vc '^#' "$BASE"` = **64**；⛔ 禁「按 nodeid 分隔符出现次数计数」那种口径——基线第 3 行注释里逐字引了一条 flaky nodeid，按分隔符计数会得 65）、**R-B14-3**（裁判先 `cd backend`，`--ignore` 必须写相对路径 `tests/unit/test_deploy_vault_sh.py`）、**R-B14-1**（若手工验证 lefthook，一律**裸调用** `/opt/homebrew/bin/lefthook <子命令>`；⛔ 别加 1.x 时代那个抑制自动安装的 flag——brew 2.1.6 已移除它，带上恒 `Incorrect Usage` rc=1 = 假红；仍禁 `npx lefthook`）| 裁定文件 §R-B14-1/2/3；手册 §四.6 摘要 |
| **本批纪律**：本卡不触及 `backend/app`（`lancedb_client` 在 `backend/lib`）故 `pyright app` 门不直接约束本卡，**pyright 保持 0** 的语义纪律照旧（⛔ 不得 `LEFTHOOK_EXCLUDE=python-typecheck`；若 diff 冒出 `backend/app` 文件 = 越界停下）；判据 grep git 输出一律 `--no-color` + 同次验伪锚；evidence 存档用 `.txt` 不用 `.log`（仓根 `.gitignore` 全局吞 `*.log`）；承重裁判末行 `echo rc=$pipestatus[1]`（zsh，`tee` 吞退出码）；ruff 判据用 **zsh 数组**写法（见 §二）；**批中禁装/升任何包**（不往共享 venv 装工具）；`canvas-vault/.claude/scripts/fsrs_bridge.py`/`decay_beta.py` ⛔ 零写者；live vault / 7691 / 7687 / 现网 LanceDB **只读** | 协议 §2.2/§2.3；手册 §零 |

## 一 完成条件（AND）
- **(a) 第 0 分钟**：`pwd` = `…/worktrees/card-t1-lance`；`git branch --show-current` = `card/t1-lance`；`git rev-parse --short=8 HEAD` = `08100483`；`git status --porcelain | wc -l` = 0；`test -e backend/.venv/bin/pytest && test -e backend/.env`；开工先 `sed -n`/`grep -nF`/AST 逐条核 §〇 每个 file:line（漂移则在验收单写「卡文 :X → 实测 :Y」，⛔ 不改卡文行号记忆，以现场实测为准）。**开工基线自证（落档）**：`BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`（⛔ **feature 主干树绝对路径**——该目录在 NEW @ `08100483` 的车道树里可能 untracked/缺席，写成 `$(pwd)/…` 会让 `grep -v '^#' $BASE` 报 No such file、diff 全 `>` 假阻断）；`test -f "$BASE" && grep -vc '^#' "$BASE"` → **64**（不是 64 或文件不在 ⇒ 停下报主 session，不得继续）。
- **(b) 先红·基线（改前，未改任何代码/测试）**：`cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_lancedb_cross_vault_drop_g29f1.py`（tee `g29f2-baseline-<ts>.txt`）→ 期望 **6 xfailed + 6 passed + 4 passed**（2 缺陷锁标记 × 参数化 = 6 xfailed；前提门 `:464` × 2×3 = 6 passed；门①②③④ 等其余 = 4 passed），`rc=0`。这一跑证明「缺陷仍在、前提成立」，是 F2 的起点。
- **(c) 最长前缀优先归属（只碰 `lancedb_client.py`，三处同口径）**：选定 vault 列表来源（§〇 口径更正 2 的三选一，验收单写明依据与边界，active vault 恒在 V 里，不连现网）；把 `_owns_table :904`、`resolve_table_name :796`、`_fingerprint_table_name :1081` 三处的 `startswith(f"{vid}_")` / 拼接口径统一改为**最长前缀优先**语义（`t` 归属 `vid` ⟺ `vid` 是 V 中「`t==v` 或 `t.startswith(v+"_")`」的最长 v）。⛔ **必须保留**：`_owns_table` 的哨兵三态（未传参=active vault / 显式 `None`·`""`·`"default"`=裸表口径 / 显式 vault=该 vault）——裸表分支 `:902-903` 原样不动（既有承重契约 `test_rag_stage1_index_contracts.py`，H3）；`_cache_tables :1049`（按 `grep -nF 'and not t.endswith(self.FINGERPRINT_TABLE)'` 现场重锚，不照抄行号）的 `endswith`/`FINGERPRINT_TABLE` 两字面量原样保留（源码门）。`:874` 那段「已知未闭合面 … 移交 CARD-G2-9-F2」docstring 随缺陷闭合重写为「已闭合（F2 最长前缀）」。
- **(d) 先红·翻转信号（改代码后、暂不动测试标记）**：跑 (b) 同命令（tee `g29f2-xpass-<ts>.txt`）→ 2 缺陷锁标记 **XPASS(strict) ⇒ 报 FAILED（红）** + 6 前提门的 `:485 _owns_table(table,"a")` 断言翻红，合计 **12 红**；按 §〇「XPASS 三成因」逐条分辨——本卡必须命中 **(1)**（缺陷锁与前提门**一起**变色，不是只 page-outer、不是只某一条锁）；若只部分变色 ⇒ 说明改错了层，停下查，验收单把三成因判别过程写全。
- **(e) 后绿·翻转去标**：删 `:491`/`:505` 两处 xfail 标记；`test_prefix_overlap_premises_hold :464` 的前提断言改为**新口径**（`a_b_*` 归 `a_b` 不归 `a`：`assert not client._owns_table("a_b_canvas_nodes","a")` 且 `assert client._owns_table("a_b_canvas_nodes","a_b")` 且 `assert client._owns_table("a_canvas_nodes","a")`，断言消息写死 V 的来源与最长前缀规则）；跑 (b) 同命令 → **全 passed，rc=0**。
- **(f) 双 vault 互前缀真库门（承重）**：在测试文件内新增（或由 (e) 重写后的缺陷锁承担）一条**正向隔离门**：tmp `lancedb.connect`，让 vault `a` 与 `a_b` 都被选定来源发现（按 (c) 的来源在 tmp 里搭出：表名反推则各预置 ≥1 表，config/dir 则在 tmp 建之），预置 `a_canvas_nodes`（drift）+ `a_b_canvas_nodes`（drift）+ `a_b_file_fingerprints`；断言：`a` 的 `_cache_tables`/启动自愈后 `a_b_canvas_nodes` 与 `a_b_file_fingerprints` **仍在**、`a` 自己的 drift 表被自愈（正向对照）；`drop_vault_tables("a")` **不删** `a_b_*`，`drop_vault_tables("a_b")` **不删** `a_*`。表名读回用 `table_names(limit=10_000)`（不用默认分页，否则判据自己只看 10 张）。
- **(g) `drop_vault_tables:946` 吞异常改「记账不吞」**：`except Exception:` 分支不再静默 `pass`——改为记账（返回实删数 / 或结构化日志含**被吞的表名 + 异常**），语义变化写进验收单；新增单测钉：做出一张 drop 会抛的表（只读或被占用的桩），断言「被吞表名出现在返回值/日志」且其它表仍正常删。⛔ 不得把 `:948 return len(tables)`（尝试数）当实删数；若选结构化日志形态，单测用 `caplog` 钉住。
- **(h) 顺带项**：B-3 指纹夹具改真实指纹 schema（证「健康可用的指纹基线被误删」）；A-4「三态两两可区分」docstring 同步 §五 撤回；B-9「`-k` 会打乱执行顺序」措辞收窄为「`-k` 只筛选不重排」。`:3825` 自愈链默认分页残余站点（实测 `:924/:1112/:3857/:3866/:3970`）**登记不阻断**（§〇 口径更正 4）——若本卡顺手收口须现场 `grep -nF '.table_names('` 重锚，不照抄 `:3825`；不收口则写进「台账待登记条目」。
- **(i) 负控 / 验伪锚（承重，EXIT trap 无条件还原 + 全文件 `shasum -a 256` 前后逐字相同；⛔ 禁 `git stash`/`git checkout` 还原，用 `git show HEAD:<path> > <tmp>` 比对）**：① 把 (c) 的最长前缀判定退回 `startswith(f"{vid}_")` → (f) 互前缀门必红且红在「`a_b_*` 被 `a` 碰了」断言；② 把 V 做成**空集 / 只含 active vault** → 最长前缀退化为朴素 startswith、(f) 门同样红（证明「V 的完整性」是防线而非摆设）；③ 把 (g) 的记账改回 `pass` → (g) 单测必红。三段各 tee `g29f2-negctl-<ts>.txt`、末行 rc、跑前跑后两行 shasum 都贴。
- **(j) 既有套件不回退**：`test_lancedb_vault_isolation.py` / `test_lancedb_isolation_assertions.py` / `test_archive_legacy_lance_tables_g24.py`（正向对照仍绿）/ `test_g24_lance_legacy_table_removal.py` / `test_agentic_rag_vault_scope.py` / `tests/regression/test_rag_stage1_index_contracts.py`（源码门 + H3 `list_vault_tables(None)` 裸表口径）**0 failed**（开工 / 收工各一次，passed 数写实测对比）。
- **(k) 目录级**：`tests/unit` 收工跑一次（承重文件名固定成变量、⛔ 禁 glob；⛔ **R-B14-3**：先 `cd backend` 再 `--ignore tests/unit/test_deploy_vault_sh.py` —— 相对路径，写成 `backend/tests/…` 是空操作，该重型文件会被收集真跑、可能挂住整跑，且它不在 64 条基线里 ⇒ 其红会变成假 `>` 阻断；跑法与 `$BASE` 文件头「跑法」行逐字一致），nodeid 口径与 `$BASE`（(a) 那份 64 条、feature 主干树绝对路径）`diff` **只允许 `<` 行**（本卡新文件门转绿后必须不在红集里；任何 `>` = 阻断；⛔ 禁 `wc -l` 当判据）。
- **(l) 地盘核**：`git diff --stat --no-color 08100483 HEAD -- . ':(exclude)_bmad-output'` ⊆ {`backend/lib/agentic_rag/clients/lancedb_client.py`, `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py`, `backend/scripts/g29_dual_vault_canary.py`（本卡**一般不动** canary，canary 复跑是 T1-B；若本卡完全不碰则不应出现）}（验伪锚：去掉 `':(exclude)_bmad-output'` 应多出 `_bmad-output/` 路径）。⛔ `':(exclude)…'` 写法（`':!…'` 在 zsh/本机 git 被吃掉 rc=128 假绿）。
- **(m) 现网只读**：新/改测试里全部 `lancedb.connect(` 行均 `tmp_path` 派生，贴进验收单；不设 `ACTIVE_VAULT`/LanceDB 路径类环境变量指向现网；开工 `touch $EV/sentinel`，收工对现网 LanceDB 目录（路径以 `backend/app/config.py` lancedb 字段 + `backend/.env` 实测为准，只 `ls -la`）`find <dir> -type f -newer $EV/sentinel | wc -l` = 0。
- **(n) Codex**：顺序固定「代码与门全部定稿 → 跑全部裁判 → 送 Codex → 之后只改 `_bmad-output`」；`Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0`（本卡有代码改动 ⇒ 多轮，上限 5；见 §四）；prompt 五分节 + 最小读取面写死；prompt 与存档不得出现协议 §2 的四个禁用措辞。
- **(o)** 「**本卡未证明什么**」必填（≥4，见 §四）+「**台账待登记条目**」必填（≥4，见 §四）；commit 单独一笔（T1-B 开工前工作树必须干净）。

## 二 裁判命令
> 车道树根先 `cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance`；`PYTEST=$(pwd)/backend/.venv/bin/pytest`；**`EV=$(pwd)/_bmad-output/审查/evidence-g29f2`（⛔ 绝对路径——承重裁判带 `cd backend`，相对 `EV` 会解析成不存在的 `backend/_bmad-output/…`，`tee` 落不下来）**；`BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`（feature 主干树绝对路径）。开工 `mkdir -p $EV; touch $EV/sentinel; test -f "$BASE" && grep -vc '^#' "$BASE"`（→ 64）。承重裁判统一 `2>&1 | tee $EV/<name>-$(date +%Y%m%dT%H%M%S).txt; echo rc=$pipestatus[1]`（zsh；`.txt` 不 `.log`）。

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance
PYTEST=$(pwd)/backend/.venv/bin/pytest
EV=$(pwd)/_bmad-output/审查/evidence-g29f2; mkdir -p "$EV"; touch "$EV/sentinel"
BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt
test -f "$BASE" && grep -vc '^#' "$BASE"          # 期望 64

# 1. HEAD / 干净 / 锚点逐字核
git rev-parse --short=8 HEAD                        # 08100483
git status --porcelain | wc -l                      # 0
python3 - <<'PY'
import ast
t=ast.parse(open("backend/lib/agentic_rag/clients/lancedb_client.py").read())
w={"resolve_table_name","_owns_table","list_vault_tables","drop_vault_tables","_cache_tables","_fingerprint_table_name","_all_table_names"}
print(sorted((n.name,n.lineno,n.end_lineno) for n in ast.walk(t) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in w))
PY
# 期望（改前）：[('_all_table_names',826,839),('_cache_tables',1020,1056),('_fingerprint_table_name',1065,1081),
#   ('_owns_table',841,904),('drop_vault_tables',937,948),('list_vault_tables',906,917),('resolve_table_name',768,798)]

# 2. 归属口径计数（⛔ 改前 3 不是 2；改后 0）
grep -cF 'startswith(f"{vid}_")' backend/lib/agentic_rag/clients/lancedb_client.py   # 改前 3 / 改后 0
grep -nF  'startswith(f"{vid}_")' backend/lib/agentic_rag/clients/lancedb_client.py  # 改前 :796 :874 :904
# 2b. 缺陷锁标记（⛔ 带全 reason 串；改前 2 / 改后 0）
grep -cF 'xfail(strict=True, reason=_OVERLAP_XFAIL_REASON)' backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py  # 改前 2 / 改后 0
grep -n 'def test_prefix_overlap' backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py  # 464 / 492 / 506

# 3. 先红·基线（改前，未改代码/测试）
cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_lancedb_cross_vault_drop_g29f1.py 2>&1 \
  | tee "$EV/g29f2-baseline-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
# 期望 6 xfailed + 6 passed + 4 passed, rc=0
cd ..

# 4. 先红·翻转信号（改代码后、暂不动标记）—— 12 红；按三成因分辨
cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_lancedb_cross_vault_drop_g29f1.py 2>&1 \
  | tee "$EV/g29f2-xpass-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
# 期望 6 缺陷锁 nodeid（2 标记×参数化 2+4）XPASS(strict)→FAILED + 6 前提门红 = 12 failed, rc=1；验收单写明命中成因(1)
cd ..

# 5. 后绿·翻转去标（删标记 + 前提门改新口径后）
cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_lancedb_cross_vault_drop_g29f1.py 2>&1 \
  | tee "$EV/g29f2-green-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]   # 全 passed, rc=0
cd ..

# 6. drop 记账单测 + 双 vault 互前缀门（文件名以实测命名为准）
cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider \
  "tests/unit/test_lancedb_cross_vault_drop_g29f1.py" -k "owns or drop or overlap or accounting" 2>&1 \
  | tee "$EV/g29f2-targeted-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]
cd ..

# 7. 负控三段（示意——退回 startswith / V 置空 / drop 记账改回 pass），每段 EXIT trap + shasum 前后
L=backend/lib/agentic_rag/clients/lancedb_client.py
git show HEAD:$L > "$EV/L.head"          # 还原基准（⛔ 不用 git checkout/stash）
shasum -a 256 "$L"                        # 跑前
#   …人工制造负控变异，跑 (f)/(g) 对应门必红…
shasum -a 256 "$L"                        # 跑后（必须与跑前逐字同；否则还原漏了）

# 8. 邻近套件不回退（开工/收工各一次）
cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider \
  tests/unit/test_lancedb_vault_isolation.py tests/unit/test_lancedb_isolation_assertions.py \
  tests/unit/test_archive_legacy_lance_tables_g24.py tests/unit/test_g24_lance_legacy_table_removal.py \
  tests/unit/test_agentic_rag_vault_scope.py tests/regression/test_rag_stage1_index_contracts.py 2>&1 \
  | tee "$EV/g29f2-neighbors-$(date +%Y%m%dT%H%M%S).txt"; echo rc=$pipestatus[1]   # 0 failed
cd ..

# 9. 目录级 diff（只 < ；承重文件名固定变量，⛔ 禁 glob）
TS=$(date +%Y%m%dT%H%M%S); RUN=$EV/unit-close-$TS.txt
# ⛔ R-B14-3：先 cd backend，--ignore 必须是**相对路径**（写 backend/tests/… 不匹配任何被收集文件 = 空操作，
#    该重型文件仍会被收集并真跑、可能挂住整跑；且 $BASE 的 64 条不含它 ⇒ 它的红会变成假 `>` 阻断）。
#    跑法与 $BASE 文件头记录的「跑法」逐字一致。
cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider 2>&1 | tee "$RUN"; echo rc=$pipestatus[1] | tee -a "$RUN"
cd ..
grep -E '^(FAILED|ERROR) tests/' "$RUN" | sed 's/ - .*//' | sort -u > "$EV/close.nodeids"
grep -v '^#' "$BASE" | sort -u > "$EV/base.nodeids"
diff "$EV/base.nodeids" "$EV/close.nodeids"         # 只允许 < 行

# 10. ruff（zsh 数组，设计稿 §0.2 item 2）
F=(${(f)"$(git diff --name-only --diff-filter=AM 08100483 HEAD -- 'backend/**/*.py')"}); print -r -- "files=${#F}"
(( ${#F} )) || print -r -- "no py files"; [[ ${#F} -gt 0 ]] && backend/.venv/bin/ruff check -- "${F[@]}"; echo rc=$?
# 10b. ⛔ 验伪锚（设计稿 §0.2 item 2 明文要求：喂一个已知含 F401 的文件必须 rc=1）——
#      同次执行，先证「这条 ruff 调用在真有 lint 错时会红」，否则上面的 rc=0 只是恒真摆设。
D=$(mktemp -d); BAD=$D/anchor_f401.py; print -r -- 'import os' > "$BAD"      # 已知 F401：导入未使用
backend/.venv/bin/ruff check --select F401 -- "$BAD"; print -r -- "anchor rc=$?"   # 必须 rc=1 且正文含 F401
rm -f "$BAD"; rmdir "$D"   # ⛔ 别写 rm -rf（guard hook 会拦）；rc=0 或未报 F401 ⇒ 判据坏了（二进制/选项/路径），停下查，不得把主判据的 rc=0 当通过
# 写卡时已在 card-v5-lance 的 ruff 上实测：anchor rc=1 + 正文报 F401 imported but unused（Found 1 error.）

# 11. 地盘门（验伪锚：去掉 exclude 应多出 _bmad-output/）
git diff --stat --no-color 08100483 HEAD -- . ':(exclude)_bmad-output'

# 12. 现网只读
grep -nF 'lancedb.connect(' backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py   # 每行含 tmp_path
find <现网 lancedb 目录> -type f -newer "$EV/sentinel" | wc -l                          # 0
```

## 三 禁改与隔离
- **本卡地盘（只允许改这三个文件）**：
  - `backend/lib/agentic_rag/clients/lancedb_client.py`（独占；只改 `_owns_table:904` / `resolve_table_name:796` / `_fingerprint_table_name:1081` 三处归属口径 + `:874` docstring 重写 + `drop_vault_tables:946` 记账 + vault 列表来源新增；⛔ 保留 `_owns_table` 哨兵三态与裸表分支 `:902-903`、保留 `_cache_tables:1049`（字面量重锚）的 `endswith`/`FINGERPRINT_TABLE` 两字面量、不改 `_tables_cache` 装载循环）。
  - `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py`（独占；删 `:491`/`:505` xfail 标记、前提门 `:464` 改新口径、B-3 指纹夹具真 schema、A-4/B-9 docstring、新增双 vault 互前缀正向门与 drop 记账单测）。
  - `backend/scripts/g29_dual_vault_canary.py`（**一般不动**——完整 canary 复跑是 T1-B；本卡若完全不碰则不应出现在地盘 diff 里）。
- ⛔ **禁改 `backend/app/**`**（零文件；`python-typecheck` 不触发；若 diff 冒出 `backend/app` 文件 = 越界，停下在验收单写明，不自作主张扩面）。
- ⛔ 禁改 `tests/regression/test_rag_stage1_index_contracts.py`（源码门保留 `endswith`/`FINGERPRINT_TABLE` 字面量 + H3 `list_vault_tables(None)` 裸表口径；本卡靠它做终判，不得往里塞改动）、`test_archive_legacy_lance_tables_g24.py`（正向对照仍绿）、`test_lancedb_vault_isolation.py`/`test_lancedb_isolation_assertions.py`。
- ⛔ 禁改 `backend/tests/conftest.py`（T9）/ `backend/tests/unit/conftest.py`（T9）/ `lefthook.yml`（T8）/ `pyrightconfig.json`、`backend/app/models/**`。
- **硬边界**：⛔ 禁写 live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/**`；⛔ 禁连 7691 / 7687；⛔ 禁碰 `canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py`（本卡零关联，三个改动文件 `grep -rn fsrs_bridge` 应 0 命中）；⛔ **现网 LanceDB 目录只读**（不 `connect`、不 `initialize`）；⛔ 禁 `git stash`/`git stash pop`（共享栈）；⛔ **不改台账**（只主 session 改；卡在验收单写「台账待登记条目」）；⛔ **不 push**；`*.stderr*` 不入库（`.gitignore` 已覆盖）；⛔ **批中禁装/升任何包**（不往共享 venv 装工具）。
- 禁放宽判据：(f) 互前缀门不得改成「表数量不减」之类计数判据（幂等 MERGE 假绿教训——必须按表名逐个断言）；负控必须红在指定断言消息；`_owns_table` 不得对 default 返回恒 True、不得把显式 `None` 解析成 active vault（否则打红 `test_rag_stage1_index_contracts.py` 的 H3 门）。

## 四 Codex / 验收单
- **命令（协议 §2 固定）**：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F2[-rN].md)" > _bmad-output/审查/codex-review-CARD-G2-9-F2[-rN].md 2> _bmad-output/审查/codex-review-CARD-G2-9-F2[-rN].stderr </dev/null`。
- **轮次**：`Codex gpt-6-astra ultra 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0`（本卡有代码改动 ⇒ **多轮，上限 5**；最后一轮须 `git diff --stat --no-color <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空且 BLOCKER=0、HIGH=0，MEDIUM/LOW 登记；审后再改代码必再送一轮；**纯注释·docstring 尾巴（A-4/B-9/`:874`）按 D-32 不占轮次不重置**，由主 session 逐行等价核；第 5 轮仍有 HIGH 停下交主 session；车道对 HIGH 的驳回写理由但不自判通过；0 字节存档重发一次，再 0 字节 → 主 session 人审）。
- **存档首部（协议 §2.1，缺「模型 / reasoning_effort / codex」任一 = 该轮不计配额）**：首部 blockquote 必须抄含 `codex --version` 实测值、会话头自证里的 **model 行**与 **reasoning 行**（从 `.stderr` 前三行抄，`.stderr` 本身不入库，括注各行行号）；随后一行 `---` 再接正文。
- **prompt 五分节 + 最小读取面写死**：① 背景（F1 已单点化 `_owns_table`，F2 改 `startswith` → 最长前缀优先消歧；数据丢失面 R-01）；最小读取面 = `git diff 08100483 <审SHA> -- . ':(exclude)_bmad-output'` + `lancedb_client.py` `:768-798`/`:841-905`/`:937-948`/`:1020-1056`/`:1065-1081` + 测试文件全文 + 裁定请求 §三。② 作者自述请独立核对：最长前缀规则在 V={a,a_b} 上三个断言成立、vault 列表来源的完整性与边界（零表 vault / active vault 是否恒在 V）、哨兵三态未被改坏、`:874` docstring 已随缺陷闭合、drop 记账不吞。③ 按重要性排序的问题：⓪ vault 列表来源是否有「未被发现的 vault ⇒ 朴素 startswith 回退 ⇒ 缺陷复活」的路径（门②负控是否真锁住）；① default 空前缀有无退化成全表或恒空；② `resolve_table_name` 改最长前缀后是否对既有已建表产生双前缀/漏前缀的回归；③ (f) 互前缀门的表名读回是否走到了门未覆盖的默认分页路径（≤10 盲区）；④ 正向对照（`a` 自己 drift 表仍被自愈）是否证明隔离而非别的原因删掉；⑤ drop 记账新形态是否改变 `return` 契约、有无调用方依赖旧返回值。④ 输出格式（BLOCKER/HIGH/MEDIUM/LOW + file:line + 一句复现思路）。⑤ 边界（只读、不连库、不评完整 canary 与 `_check_and_fix_dimension_mismatch` drop 条件设计）。
- ⛔ **prompt 与存档不得出现协议 §2 点名的那四个禁用措辞**（⛔ 四词的字面写法**只去协议 §2「prompt 里禁止出现…类请求」那句原文里取**，本卡文与短 goal 一律不转抄——转抄本身就把禁用词带进了要被 grep 的文本面）；本卡正面替换用语固定为「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」。送 Codex 前自查：从协议原句逐词取出，对 `_bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F2*.md` 与本卡各轮存档各 `grep -cF` 一遍 = **全 0**（命中即改写后重发，不硬送）。
- **验收单** `_bmad-output/验收单/UAT-CARD-G2-9-F2-<日期>.md`（DoD-3 双段）：4-A Claude 已代验贴证据（各裁判 tee 路径 + 末行 rc + grep 计数对照 + XPASS 三成因判别记录）；4-B 零技术词一句「打开一门课的资料库，再也不会因为另一门课的名字更长或更短，就把别人的资料删掉；过期的旧索引仍会自动重建——我感觉两门课彻底互不打扰、切换时很踏实」+ felt-sense。
- **本卡未证明什么（≥4）**：① 未证明现网 LanceDB 目录里是否已有被误删的长/短 id 互前缀 B 表（只能备份对账，D-41 需授权，本卡不做）；② 未复跑完整 canary（需 Ollama bge-m3 + 7692 容器），隔离只有 tmp 真库门与静态核（完整复跑是 T1-B）；③ 未证明 `resolve_table_name` 最长前缀改动对**存量已建表**（旧朴素前缀命名）的兼容面——只覆盖新建与归属查询；④ 未证明选定的 vault 列表来源在「大量 vault / 深层嵌套前缀」下的性能与正确性上界；⑤ 未证明 `:3825` 自愈链默认分页残余站点（`:924/:1112/:3857/:3866/:3970`）的行为（本卡登记不阻断）；⑥ 未证明 drop 记账新形态对所有调用方（`canvas_service.delete_edge` 链路等）无语义影响，只在本文件面核。
- **台账待登记条目（≥4）**：① G2-9-F2 最长前缀归属修复 sha + 缺陷锁翻转去标 + 前提门改口径的 nodeid；② vault 列表来源的选定依据与边界（含 active vault 恒在 V、零表 vault 处置）；③ `drop_vault_tables` 由「尝试数 + 吞异常」改「记账不吞」的返回/日志契约变化 + 受影响调用方清单；④ `:3825` 自愈链默认分页残余站点（实测 `:924/:1112/:3857/:3866/:3970`，UAT 旧行号 `:896/:1080/:3825/:3834/:3938` 已漂）登记移交；⑤ 完整 canary 复跑（T1-B CARD-G2-9-F1-canary）；⑥ Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数；⑦ tests/unit 目录级 diff 结果（只 `<`）；⑧ A-4/B-9/`:874` 纯文案改动按 D-32 不重置轮次的逐行等价核记录。
- commit：单独一笔，header ≤100 含 `[BATCH-2026-09-11-第十四批 / CARD-G2-9-F2]` 且含卡号，body 行 ≤100（`wc -m`）；`*.stderr*` 不入库；不 push；**独立 commit + `git status --porcelain` 空后同车道继续 T1-B**；跑完说「**复核第十四批 T1**」。
