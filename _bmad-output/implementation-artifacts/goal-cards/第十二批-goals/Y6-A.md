> ⚠️ 本文件是 CARD-TEST-hygiene-vaultinit 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十二批手册 §三 Y6-A 块。
> 批次标记 `[BATCH-2026-09-05-第十二批 / CARD-TEST-hygiene-vaultinit]`。车道：`card-y6-testhygiene`（分支 `card/y6-testhygiene`，HEAD `03ac8bf8`，主 session 已预合主干 03ac8bf8，venv symlink 已建），**无前提**（Y6 车道首卡，之后串 Y6-B → Y6-C）。只读 `--add-dir /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase` = **冻结的污染证据树**（分支 `card/z4-redbase`，HEAD `c8611a89`），只读取证，**禁改禁清**。勘探 2026-09-05 于主干 03ac8bf8。协议：`.claude/rules/card-batch-protocol.md`（§2.1 存档首部 / §2.2 裁判落盘 / §2.3 环境通告 / §5 tests/unit 基线文件用法）。

# CARD-TEST-hygiene-vaultinit — 定位并修复「跑测试把 vault 骨架写进 backend/」（先复现定位，再修守卫面，最后落不变量 fixture；台账归因勘误只写待登记条目）

## 〇 事实
| 事实 | 位置 |
|---|---|
| **冻结证据**（只读实测 2026-09-05）：`git -C card-z4-redbase -c core.quotepath=false status --porcelain backend` → ` M backend/config/subject_mapping.yaml`（+6/−21）、`?? backend/CLAUDE.md`、`?? backend/outputs/`、`?? backend/raw/`、`?? backend/wiki/`；该树 HEAD `c8611a89` | card-z4-redbase |
| **污染内容 ≡ VaultInitService 骨架**：`backend/raw/.gitkeep`、`backend/wiki/{canvases,concepts}/.gitkeep`、`backend/outputs/exam_boards/.gitkeep`、`backend/CLAUDE.md` 首行 `# Canvas Learning System — Vault` —— 逐项对应 `vault_init_service.py:18-23 VAULT_DIRECTORIES`（`raw` / `wiki/concepts` / `wiki/canvases` / `outputs/exam_boards`）+ `:40 CLAUDE_MD_SKELETON` + `:96-98` 写 CLAUDE.md；`backend/.gitignore` 已入库 ⇒ `:109-113 _ensure_gitignore` 早退（所以证据树里无 `.gitignore` 的 M）。**写者只能是 `VaultInitService.initialize_vault(<解析成 backend/ 的路径>)`** | vault_init_service.py |
| `initialize_vault` 在 backend/app 的**唯一**生产调用点：`system.py:449-450`（`setup_wizard`）；`:441 vault = Path(request.vault_path).resolve()` —— 相对路径 / 空串按 **cwd** 解析（pytest 从 `backend/` 起跑 ⇒ cwd = backend/）；`:442-448` 黑名单只拒 `/` `/etc` `/usr` `/var` `/tmp` `/System` 与含 `..`；`SetupWizardRequest`（`:427-428`）`vault_path: str = Field(...)` 无 min_length、无绝对路径校验。`app/main.py` 零引用 VaultInitService | system.py |
| tests/unit 里触及 VaultInitService / setup-wizard 的只有三处：`test_vault_init_service.py`（8 用例**全部**经 `:13-14 vault_dir(tmp_path)`）、`test_kg_health.py:9-40`（全 tmp_path，只调 `_ensure_gitignore` / `has_git_plugin`）、`test_startup_health_check.py:55-57 / :61-63`（POST `/tmp/test-vault` / `/tmp/test-vault-wizard`）。**没有任何 tests/unit 用例传相对或空 vault_path** ⇒ 台账「test_vault_init_service.py 写骨架进 backend/」的归因在主干上找不到写点 | 三文件 |
| `/tmp/test-vault` 与 `/tmp/test-vault-wizard` 本机**实存**（mtime 2026-09-05 06:49），内容 = `.gitignore CLAUDE.md outputs raw wiki` 骨架 ⇒ 裸 TestClient 下 POST setup-wizard **真的走通了**（`system.py:28` router 无 router 级鉴权，只有 `:757` / `:824` 两端点各挂 `require_internal_api_key`）。附带结论（给 Y6-C，本卡只登记）：`test_startup_health_check.py` 的 6 条基线红**不是** auth 503 | /tmp + system.py |
| **第二嫌疑（tests/unit 之外）**：`tests/contract/test_openapi_contract.py:27 schemathesis.openapi.from_asgi(...)` + `:37-43 @schema.parametrize() max_examples=10` 对**全部端点**做属性输入、无 exclude（grep 0 命中）；空串 / `.` 形态的 vault_path 恰会解析成 cwd。旁证：主干**已入库**的 `backend/config/subject_mapping.yaml` 含 7 条 `pattern:`，其中 5 条乱码（`+Nh` 等；`git log -S'+Nh'` → `793cd538`）= 属性输入写进真实配置后被卷进 commit 的形态；`subject_resolver.py:80-100 _find_config_path` 缺省解析到真实 `backend/config/subject_mapping.yaml`，`:473-479` `yaml.dump(...)` 且 `skip_directories: list(self._skip_dirs)`（set → 顺序漂移，与证据树 diff 的重排一致）。tests/api `test_metadata_subject_mapping.py:26-54` 与 tests/unit `test_subject_resolver.py:38 / :64-66` 都用 tmp 配置 —— 都**不是**写者 | contract + subject_resolver.py |
| `backend/tests/unit/conftest.py` 已存在（100 行）；`:19-20` 已有一条 autouse fixture `_stub_vault_identity_registry(monkeypatch)`（形态可照抄）。`backend/tests/conftest.py`（`:83` pytest_configure 装门 / `:142-160` 结账哨兵 / `:471` INTERNAL_API_KEY="test-internal-key" / `:476-494` 共享 client + no_lifespan）是 **Y7-A 独占**，本卡一字不改 | conftest ×2 |
| tests/unit 既有红基线 = 设计稿 §0 文件（247 nodeid / 63 文件，FAILED 209 / ERROR 38）：`_bmad-output/审查/evidence-b12/unit-red-baseline-03ac8bf8.txt`；其中 `test_startup_health_check.py` 6 条、`test_kg_health.py` 1 条在基线内；`test_vault_init_service.py` **不在**基线（全绿）。基线文件头 5 行是采集命令与口径，逐字照做 | evidence-b12 |
| 环境：`backend/pytest.ini:14 asyncio_mode = auto`、`addopts = -v --tb=short`；venv 无 pytest-randomly（`-p no:randomly` 无害）、有 xdist 3.8.0（本卡**不用** `-n`，顺序跑才能二分） | pytest.ini / venv |
| **勘误**：底稿 (e)「主干 298 / 候选树 289」是含 42 行日志噪音的**行数**；本卡分母一律用基线文件的 nodeid 口径 247 | 基线文件头 |

## 一 完成条件（AND）
- (a) **先定位，再动任何代码**。在本车道树用哨兵法复现，三种污染签名同时盯：① `backend/{raw,wiki,outputs,CLAUDE.md}` 出现；② `/tmp/test-vault*` 出现；③ `backend/config/subject_mapping.yaml` / `backend/.gitignore` 的 sha 变化。假设 H1 = `tests/unit` 目录级；假设 H2 = `tests/contract/test_openapi_contract.py`（门下，`from_asgi` 进程内；`importorskip` 若 skip 则如实记「schemathesis 未装，H2 未执行」）。任一签名复现 → 用 `--co -q` 取 nodeid 列表按文件二分（顺序跑，禁 `-n`）收窄到 **nodeid 级**，每步同判据；全部未复现 → 验收单如实写「**未复现**」+ 逐条命令与输出，**不得凭台账下结论**。跑前把既有 `/tmp/test-vault*` **改名**（`mv /tmp/test-vault /tmp/test-vault.pre-$(date +%s)`，不 rm）并 `ls -ld` 存证，否则 `exist_ok=True` 让重跑不留痕。
- (b) **修两条（不依赖 (a) 结论，是同一守卫面）**：① `SetupWizardRequest.vault_path` 加 pydantic `field_validator`「必须绝对路径」（`Path(v).is_absolute()`，否则 422，detail 说明），`:442-448` 黑名单与 `..` 拒绝**原样保留、不搬动**；同文件 `test_startup_health_check.py` 新增负控：`""` / `"."` / `"relative/x"` → 422，`str(tmp_path / "v")` → 非 422。② `test_startup_health_check.py:55-57 / :61-63` 的 `/tmp/test-vault` / `/tmp/test-vault-wizard` 改为 `str(tmp_path / ...)`；该文件 `:12-16` 的裸 `TestClient(app)` fixture **本卡不改**（那是 RED-A1 面，第十三批）。改了 `backend/app/**` ⇒ **不得** `LEFTHOOK_EXCLUDE=python-typecheck`；pyright 报错若有，须证明不在本卡 diff 行。
- (c) **不变量 fixture 只落 `backend/tests/unit/conftest.py`**：`scope="session", autouse=True`；开始时快照 `backend/{raw,wiki,outputs,CLAUDE.md}` 的存在性（期望不存在）、`backend/.gitignore` 与 `backend/config/subject_mapping.yaml` 的 sha256、`/tmp/test-vault*` 的集合；teardown 时任一「新出现 / sha 变」→ `pytest.fail` 列出路径（session teardown 失败 = 末尾 ERROR，rc 非 0）。fixture 自身：用 `Path(__file__).resolve().parents[2]` 定位 backend/（不依赖 cwd）、不 import `app.*`、不创建/删除任何文件。**负控必做**：临时（不入 commit）让某 tests/unit 用例 `Path("raw/_probe").mkdir(parents=True)` → fixture 红且指名 `backend/raw`；还原后绿；`git status --porcelain backend` 干净。
- (d) **台账归因勘误只写「台账待登记条目」**（车道不改台账）：原文两处 —— `未合卡追踪台账.md:48` Z4-A 行、`2026-09-05-第十一批复核裁定与待裁决登记.md:54`「`test_vault_init_service.py` 目录级运行把 vault 骨架写进 `backend/`」—— 在验收单里**原句保留 + 划改**为 (a) 的实测结论（复现到 nodeid 则写 nodeid；未复现则写「未复现，写者机制 = `system.py:441` 相对路径按 cwd 解析，触发方未定位」）。
- (e) **tests/unit 目录级红按基线逐 nodeid diff**：开工、收工各跑一次基线文件头 5 行的命令与 grep/sed/sort 口径，与基线 diff；差集只允许「减少」（`<` 行），**不得出现新增**（`>` 行）。`test_startup_health_check.py` 6 条基线红改路径后形态可变但 nodeid 不得新增。
- (f) **本卡未证明什么**（必填）：未证明 tests/contract 属性输入的完整污染面（H2 命中也只登记，metadata 保存端点不在本卡地盘）；未证明 (c) 的 fixture 能覆盖 tests/unit 之外的套件（session fixture 只在 tests/unit 被收集时生效）；未证明 `test_startup_health_check.py` 6 条红的真因（auth vs 门哨兵，归 Y6-C）；未清理主干已入库的 5 条乱码 mapping（`793cd538`）。**台账待登记条目**（必填）：① Z4-A 行 + 裁定 §五.5 归因划改（原句 → 实测）；② `subject_mapping.yaml` 5 条乱码 mapping 入库 = 独立卫生卡（第十三批候选）；③ 若 H2 命中：`tests/contract/test_openapi_contract.py` 对写端点无 exclude = 独立卡；④ `system.py:28` router 无鉴权的事实转 Y6-C 分诊线索。

## 二 裁判命令
1. **H1 哨兵复现**（tee 落 `_bmad-output/审查/evidence-hygiene/`）：
   ```bash
   cd <树> && E=_bmad-output/审查/evidence-hygiene && mkdir -p $E && touch $E/sentinel \
     && shasum -a 256 backend/config/subject_mapping.yaml backend/.gitignore > $E/sha-before.txt \
     && (ls -ld /tmp/test-vault* 2>&1 || true) > $E/tmp-before.txt
   cd backend && set -o pipefail && L=../$E/unit-run-h1-$(date +%Y%m%dT%H%M%S).txt \
     && PYTHONDONTWRITEBYTECODE=1 $PYTEST tests/unit -q -p no:cacheprovider -p no:randomly --override-ini='addopts=' 2>&1 | tee $L; echo "rc=${PIPESTATUS[0]}" | tee -a $L
   cd .. && git status --porcelain backend | tee $E/status-after-h1.txt \
     && find backend -maxdepth 1 -newer $E/sentinel -not -name .venv | tee $E/newer-after-h1.txt \
     && shasum -a 256 backend/config/subject_mapping.yaml backend/.gitignore | diff $E/sha-before.txt - ; (ls -ld /tmp/test-vault* 2>&1 || true) | tee $E/tmp-after-h1.txt
   ```
   期望：复现 → 四路径之一出现 / sha 变 / tmp 出现（进入二分）；不复现 → 三处全空，如实记「H1 未复现」。
2. **H2 哨兵复现**：同 1，被测换成 `tests/contract/test_openapi_contract.py`，log 名 `unit-run-h2-*.txt`（门下；skip 则记录 skip 原因原文）。
3. **二分**（仅在 1/2 复现时）：`$PYTEST <范围> --co -q | grep '::' > $E/nodeids.txt`，按文件二分逐步跑 `-p no:randomly`，每步重做哨兵判据，记 `$E/bisect.txt`；终点 = nodeid。
4. **修后三文件**：`cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_startup_health_check.py tests/unit/test_vault_init_service.py tests/unit/test_kg_health.py 2>&1 | tee ../$E/three-files-after.txt` → `test_vault_init_service` 8 绿；`test_kg_health` 基线 1 红不增；`test_startup_health_check` 基线 6 红不增 + 新增 422 负控绿；随后 `ls -d /tmp/test-vault /tmp/test-vault-wizard 2>&1` → 两条 `No such file`。
5. **(c) 负控**：临时改一条用例写 `raw/_probe` → 目录级（或单文件 + 该 conftest）→ 末尾 ERROR 指名 `backend/raw`（tee `$E/negctl-red.txt`）；还原 → 绿（`$E/negctl-green.txt`）；`git status --porcelain backend` 为空；变异**不入 commit**。
6. **(e) 基线 diff**：`cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST tests/unit -q -p no:cacheprovider 2>&1 | grep -E '^(FAILED|ERROR) tests/' | sed 's/ - .*//' | sort > ../$E/unit-red-after.txt; grep -E '^(FAILED|ERROR) tests/' ../_bmad-output/审查/evidence-b12/unit-red-baseline-03ac8bf8.txt | sort | diff - ../$E/unit-red-after.txt` → 只允许 `<` 行；`>` 行 = 本卡引入 = 阻断。
7. **地盘门**：`git diff --name-only 03ac8bf8 HEAD -- . ':(exclude)_bmad-output'` ⊆ {`backend/app/api/v1/system.py`, `backend/tests/unit/conftest.py`, `backend/tests/unit/test_startup_health_check.py`}；`git diff --stat 03ac8bf8 HEAD -- backend/app/services/vault_init_service.py backend/tests/conftest.py backend/tests/unit/test_vault_init_service.py; echo rc=$?` → 输出空且 rc=0（`test_vault_init_service.py` 例外仅当 3 的 nodeid 证据指向它，须贴证据）。
8. **pyright**：`cd backend && .venv/bin/pyright app/api/v1/system.py tests/unit/conftest.py tests/unit/test_startup_health_check.py 2>&1 | tail -5 | tee ../$E/pyright.txt`；若有报错，贴 `git diff -U0 03ac8bf8 HEAD -- <文件> | grep '^@@'` 行号区间证明不相交。
9. **契约面不回归**：`tests/api` 目录级开工/收工各一次，nodeid diff 为空（门下，`blocked=0`）。

## 三 禁改与隔离
- 禁改 `vault_init_service.py` 的 `VAULT_DIRECTORIES` / `CLAUDE_MD_SKELETON` / `_ensure_gitignore`（`:18-23` / `:40` / `:109-121`）；禁在无 (a) nodeid 级证据时改 `test_vault_init_service.py`。
- 禁改 `backend/tests/conftest.py`（Y7-A 独占，含 live_port_guard 段 `:83-206` 与共享 client `:476-494`）；不变量 fixture 只进 `backend/tests/unit/conftest.py`。
- 禁改 `metadata.py` / `subject_resolver.py` / `backend/config/subject_mapping.yaml`（H2 命中只登记）；禁改 `tests/contract/**`（Y5 面）。
- **card-z4-redbase 树只读**：禁 `git clean` / `checkout` / `rm` / `stash`；只允许 `status` / `diff` / `ls` / `cat`。
- 禁 `rm -rf /tmp/test-vault*`（改名保留）；禁在 conftest 里 `os.chdir` / `mkdir` / 写任何文件。
- 改了 `backend/app/**` ⇒ 禁 `LEFTHOOK_EXCLUDE=python-typecheck`；若用 `LEFTHOOK_EXCLUDE=python-lint`（存量格式漂移）须按协议 §2.3 贴被跳过 hook 原始输出 + 「报错不在本卡改动行」证明。
- live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/` 只读；禁连 7691/7687；禁跑 `tests/integration` / `tests/e2e`。
- 不 push；台账不改；`*.stderr*` 不入库；本批地盘互斥表（设计稿 §5）里别人的文件一律不碰。

## 四 Codex / 验收单
命令同协议 §2；1 轮；prompt `_bmad-output/审查/prompts/codex-prompt-CARD-TEST-hygiene-vaultinit.md`（五分节：一 背景 + 最小读取面写死 = `system.py` diff、`tests/unit/conftest.py` diff、`test_startup_health_check.py` diff、`evidence-hygiene/*.txt` / 二 作者自述请独立核对 = 定位结论（H1/H2/未复现）、绝对路径校验与 `:442-448` 黑名单的叠加关系、fixture 的零副作用 / 三 按重要性排序的问题 = ① 定位证据是否支持结论、有无把「未跑到」当「不存在」；② 校验器是否会误拒合法输入（macOS tmp_path 形态）或漏放 `.`/空串；③ session fixture 是否依赖 cwd、是否自身写盘、失败是否可见（rc）；④ 负控是否真承重（还原后绿是否因变异未生效）/ 四 输出格式 / 五 边界 = 不评 RED-A1 面的裸 client fixture）。存档 `codex-review-CARD-TEST-hygiene-vaultinit.md` 首部按协议 §2.1 六行 blockquote。顺序固定「代码与门全部定稿 → 跑全部裁判 → 送 Codex → 之后只改 _bmad-output」，审后再改代码 = 失绑须登记。验收单 `_bmad-output/验收单/UAT-CARD-TEST-hygiene-vaultinit-<日期>.md`：DoD-3 双段（4-A Claude 已代验 / 4-B 你来验，4-B 零技术词，一句「无变化（跑测试不再往代码目录里撒文件）」）；「本卡未证明什么」「台账待登记条目」按 (f) 必填。commit header ≤100 含批次标记，body 行 ≤100（wc -m）；不 push；**独立 commit 后同车道继续 Y6-B**；跑完说「复核第十二批 Y6」。
