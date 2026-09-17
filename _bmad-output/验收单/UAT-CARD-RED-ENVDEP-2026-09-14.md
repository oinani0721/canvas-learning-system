# UAT — CARD-RED-ENVDEP（BATCH-2026-09-11-第十四批 / 车道 card-t10-red · 第 2/5 张）

> 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T10-B.md`（feature 主干树）
> 代码 commit：**`ee16b85a`** ｜ PREREQ（T10-A tip）：`8381417b` ｜ B14_BASE：`08100483`
> Codex 轮次：**r1 即 BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 1**，绑定 `ee16b85a`（= 最终代码 HEAD），审后**零代码改动** ⇒ D-15 满足，1 轮收口。
> 证据目录：`_bmad-output/审查/evidence-red-envdep/`

---

## 0. 一句话

`test_agent_service_extraction.py` 的三条红（2 条 `fixture 'mocker' not found` ERROR + 1 条读真 `.env` 的 FAILED）改为**不依赖执行机器的环境**：缺 `pytest-mock` 时干净 SKIPPED，env 档同时隔离 `.env` 文件与进程环境变量。只改两个文件，不碰 `backend/app`。

---

## 1. (a) 第 0 分钟自证

| 项 | 实测 |
|---|---|
| `pwd` | `…/.claude/worktrees/card-t10-red` ✅ |
| `git branch --show-current` | `card/t10-red` ✅ |
| `git log --oneline -1`（开工时） | `8381417b docs(red-mockfix): … [/ CARD-RED-MOCKFIX]` ✅ 含前提卡号 |
| `git status --porcelain \| wc -l` | `0` ✅ |
| `backend/.venv/bin/pytest` / `backend/.env` | 均 `test -e` 通过 ✅ |
| `PREREQ` | `8381417b5a44d07b622f43e15cd77dc6409374a9` |
| 基线自证 `grep -vc '^#' "$BASE"` | **64** ✅（`$BASE` = feature 主干树 `evidence-b14/unit-red-baseline-08100483.txt` 绝对路径） |
| `find_spec('pytest_mock')` | **`None`** ✅（skipif 分支据此生效） |
| `grep -n DEBUG_AGENT_RESPONSE backend/.env` | **`17:DEBUG_AGENT_RESPONSE=true`** ✅ |
| 基线里本卡三条 | 第 **4**、**5** 行 ERROR + 第 **34** 行 FAILED ✅ |

### 1.1 §〇 file:line 锚点逐条核 —— **零漂移**

| 卡文锚点 | 实测 | 结果 |
|---|---|---|
| 文件 358 行 | 358 | ✅ |
| `class TestDebugAgentResponseLogging` :291 | :291 | ✅ |
| `test_extract_with_debug_logging_enabled` :294 | :294 | ✅ |
| `test_extract_without_debug_logging` :312 | :312 | ✅ |
| `test_config_has_debug_agent_response_field` :337 | :337 | ✅ |
| `test_config_has_lowercase_alias` :350 | :350 | ✅ |
| 文件头 docstring :15「测试框架: pytest + pytest-mock」 | :15 | ✅ |
| `mocker` 恰 6 处 `:294 :301 :303 :312 :319 :321` | 逐个相符 | ✅ |
| `requirements.txt:143-146` 四个 pytest 包 | 相符 | ✅ |
| `config.py:137-140` `DEBUG_AGENT_RESPONSE: bool = Field(default=False, …)` | 相符 | ✅ |
| `config.py:943 / :949 / :966` | 相符 | ✅ |
| `app/__init__.py:14-16` `load_dotenv(backend/.env)` | 相符 | ✅ |
| 无 `pytestmark` / `@pytest.mark.skip(` / `skipif` / `importorskip` | 四式全 **0** | ✅ 裸红 |
| `_settings_factory` 只在 `test_sync_batch_auth.py` / `test_system_endpoint_auth.py` | 相符（T10-E 地盘，本卡未碰） | ✅ |

---

## 2. (b) 先红 · (f) 改后绿/跳

**先红** `evidence-red-envdep/envdep-red-20260914T203612.txt`：

```
tests/unit/test_agent_service_extraction.py EEF.                         [100%]
E       fixture 'mocker' not found          ← :294 / :312 两条，setup 期 ERROR
E   AssertionError: 默认值应为 False
E   assert True is False                    ← :348 assert settings.DEBUG_AGENT_RESPONSE is False
============== 1 failed, 1 passed, 10 warnings, 2 errors in 1.15s ==============
```
`test_config_has_lowercase_alias` **passed**（不在红集的对照）✅ ｜ rc=**1**

> ⚠️ **如实声明**：该存档生成时 `rc=` 未随 `tee` 落盘（协议 §2.2 要求末行写 rc）。改前状态已被本卡修复覆盖、**不可原样重跑**，故**不补造 rc 行**，只在存档尾加了标注行（明标「非命令输出」）。同一红态**带 rc 的归档复现**见负控②③（下文 §4），两者红在同一正文。

**改后绿/跳** `envdep-green-20260914T203707.txt`（已重跑补真 rc 末行）：

```
tests/unit/test_agent_service_extraction.py ss..                         [100%]
SKIPPED [1] …:302: pytest-mock 未装（批中禁装；见 requirements.txt 声明 + 台账批级通告候选）
SKIPPED [1] …:324: pytest-mock 未装（批中禁装；见 requirements.txt 声明 + 台账批级通告候选）
================== 2 passed, 2 skipped, 10 warnings in 1.02s ===================
rc=0
```
✅ env 档 passed、两条 `mocker` 档 SKIPPED（`-rsE` 可见 reason）、**无 ERROR/FAILED**、rc=**0**。

---

## 3. (c)(d)(e) 改了什么（改后实测行号）

| 项 | 实测位置 | 内容 |
|---|---|---|
| (d) 模块级探测 | `:32` | `_HAS_PYTEST_MOCK = importlib.util.find_spec("pytest_mock") is not None` |
| (d) 守卫 1 | `:302-305` → 方法 `:306` | `@pytest.mark.skipif(not _HAS_PYTEST_MOCK, reason="pytest-mock 未装（批中禁装；见 requirements.txt 声明 + 台账批级通告候选）")`，**`mocker` 入参与函数体未改** |
| (d) 守卫 2 | `:324-327` → 方法 `:328` | 同上 |
| (e) env 档 | `:353` 签名加 `monkeypatch`；`:362` `monkeypatch.delenv("DEBUG_AGENT_RESPONSE", raising=False)`；`:365` `settings = Settings(_env_file=None)` | 两条断言（字段存在 + 默认 False）**语义不变** |
| (c) requirements | `:147` | `pytest-mock>=3.14.0`（插在 `pytest-xdist>=3.5.0` 后） |

文件 358 → **381** 行。

**(e) 选了哪条等价写法与理由**：选 **delenv + `Settings(_env_file=None)`**，不选 `model_fields[...].default` 写法。理由：后者只读**类**的字段声明，会把原断言里「实例上字段存在（`hasattr`）」这一层覆盖掉；保留实例化额外覆盖了构造路径与运行时属性访问。Codex r1 第 4 点独立复核同结论（并如实指出代价：实例化仍会校验其它环境字段，见 §7 移交）。

**(c) 为何此刻不装**：协议 §2.3 **批中禁装工具**——往共享 venv 装包是批级事件（本批 5 车道共用 `card-v5-lance/backend/.venv`）。故**只声明不 `pip install`**，生效在下次 clean install。

**⛔ 为何不用函数体 `pytest.importorskip`**：`mocker` 在**签名**里，fixture 解析发生在函数体**之前**，缺包会先 ERROR，`importorskip` 永不执行。负控③已实证（删 skipif → 立刻回到 2 条 ERROR）。

---

## 4. (g) 负控三段（各段跑前/跑后全文件 `shasum -a 256` 逐字同；还原用 `git show HEAD:<path>` + `cp`，**未用 `git stash` / `git checkout`**，且带 EXIT trap 无条件还原）

基准 shasum（全三段一致）：`f3784415e2106b8a444110c9fa7076c04a9f21011e81fb014e1dcdd317fc57f1`

### ① A2 §7 验伪锚 — `negctl-1-envvar-20260914T203955.txt`

同一进程环境（`DEBUG_AGENT_RESPONSE=true`，已先自证 `os.environ` 里真有该值）下三行对照：

| 写法 | 读到 |
|---|---|
| 裸 `Settings()` | **True** |
| **仅** `Settings(_env_file=None)` | **True** ← **残缺修法会被这一行抓住** |
| `delenv` + `_env_file=None`（本卡修法） | **False** |

正式跑：env 档在 `DEBUG_AGENT_RESPONSE=true` 进程环境下 **1 passed，rc=0** ✅
⇒ 修法隔离的是**进程环境变量**，不是只关文件。锁住 A2 §7「禁 `.env` ≠ 禁进程环境变量」。

### ② env 还原负控 — `negctl-2-env-revert-20260914T204021.txt`

把 (e) 改回 `Settings()`（去 delenv、去 `_env_file=None`）：
- 变异落地自证：shasum 变为 `c791f409…`（≠ 基准）、`grep` 显示签名回到 `(self)`、`settings = Settings()`
- 红在**指定正文**：`assert settings.DEBUG_AGENT_RESPONSE is False` → `E assert True is False`，`1 failed`，rc=**1** ✅
- 还原后 shasum 回到 `f3784415…` ✅

### ③ skipif 还原负控 — `negctl-3-skipif-revert-20260914T204050.txt`

- 同段验伪锚：先证 `find_spec('pytest_mock') = None`（skip 成立的前提）✅
- 删两处 `@pytest.mark.skipif`（断言锚点恰 2 处，否则不动手）：skipif 计数 2 → **0**，shasum 变为 `758b975a…`
- 红在**指定正文**：2 条 `E fixture 'mocker' not found`，`2 errors`，rc=**1** ✅
- 还原后 shasum 回到 `f3784415…`、skipif 计数回到 **2** ✅

---

## 5. (h) 地盘核 · (j) 硬边界 — `scope-gate-20260914T204120.txt`

`git -c core.quotePath=false diff --name-only --no-color 8381417b ee16b85a -- . ':(exclude)_bmad-output'`：

```
backend/requirements.txt
backend/tests/unit/test_agent_service_extraction.py
```
文件数 = **2**；「非这两个文件」计数 = **0** ✅

**三个验伪锚**（防判据恒 0 假绿）：
- A：改用 `':(exclude)backend/requirements.txt'` → 该文件**消失**，证 pathspec 真在过滤 ✅
- B：不带任何 exclude → 与主判据同（本阶段 `_bmad-output` 尚未 commit）；**真正的 exclude 验伪锚见 §8 终审绑定**（文档 commit 后不带 exclude 会多出 `_bmad-output/` 路径）✅
- C：同一过滤式对已知正例命中 **2**，证过滤式不是恒 0 ✅

(j) 硬边界：`grep -rn 'fsrs_bridge\|decay_beta\|canvas-vault/'` 两文件 → **零命中**（rc=1）✅
未设任何指向现网的环境变量；未连 7691/7687；现网 LanceDB 未读写；live vault 未写。

---

## 6. (i) tests/unit 目录级 diff（R-15 同口径）— `unit-close-20260914T204126.txt` / `unit-diff-20260914T204808.txt`

命令：`pytest tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider`（文件名先定成 `$RUN` 变量，**未用 glob**）

```
= 34 failed, 5105 passed, 50 skipped, 23 xfailed, 171 warnings in 369.80s (0:06:09) =
rc=1
```

| 判据 | 实测 |
|---|---|
| `base.nodeids` 条数 | **64** ✅ |
| `close.nodeids` 条数 | **34** ✅（64 − 30 = 34，算术自洽） |
| `diff base close` 的 **`>` 行数** | **0** ✅ **无任何新增红** |
| `<` 行数 | **30** = 本卡 3 条 + T10-A 已修的 27 条 |
| 本卡 3 条 nodeid 在 `<` 里 | **3** ✅ |
| 验伪锚：`close.nodeids` 里 `test_agent_service_extraction` | **0** ✅（本卡三条真的没了） |
| 验伪锚：`base.nodeids` 里同一式 | **3** ✅（过滤式不是恒 0） |

---

## 7. (k) Codex 轮次表

| 轮 | 模型 | reasoning | codex | 绑定 SHA | B / H / M / L | 存档 |
|---|---|---|---|---|---|---|
| r1 | `gpt-6-astra` | `ultra` | `codex-cli 0.153.3` | `ee16b85a`（= 最终代码 HEAD） | **0 / 0 / 0 / 1** | `codex-review-CARD-RED-ENVDEP-r1.md` |

存档首部三字段（`模型` / `reasoning_effort` / `codex`）齐备，会话头自证抄自 `.stderr` 的 **L4 / L7 / L11**（含版本行 + `model:` 行 + `reasoning effort` 行，行号括注；`.stderr` 本身**不入库**）。审后**零代码改动** ⇒ 无需再送一轮，D-15 满足。

### 7.1 LOW-1（登记不阻断）

> `find_spec` 只检查模块可发现性，未覆盖「装了但版本不足」「装了但插件被 `-p no:pytest_mock` 停用」的路径 — `test_agent_service_extraction.py:32`

**接受，不改**。理由：本卡的门就是「在 / 不在」这一层，且卡文 §四「本卡未证明什么」⑤ 已预先登记同一条。补更强判定（版本比较 / 插件注册检测）会把测试侧逻辑复杂化，收益不抵；真正的收口是**装上 pytest-mock**（见 §9 台账条目 ②）。

### 7.2 ⛔ Codex 抓到的作者判据缺陷 —— **已独立复核成立，本验收单更正**

Codex r1 第 3 点指出：作者引用的 `grep -rln mocker backend/tests/unit/*.py` **取名面被划窄**——`-r` 不扩展 shell glob，它实际只覆盖「`tests/unit` 直属 `.py`」，**不是**「整棵测试树」。

独立复核（`codex-r1-low-verify-*.txt`）：

```
grep -rln '\bmocker\b' backend/tests/ --include='*.py'
  backend/tests/e2e/conftest.py          ← 原判据看不见
  backend/tests/unit/test_agent_service_extraction.py
backend/tests/e2e/conftest.py:402 def mock_agent_responses(mocker)
backend/tests/e2e/conftest.py:433 def mock_agent_with_failures(mocker)
两个 fixture 的静态调用方数 = 0 / 0
验伪锚：同一递归式对本卡文件命中 = 1（不是恒 0）
```

**更正后的准确表述**：整棵测试树的 `mocker` 消费者**不止本文件**，还有 `e2e/conftest.py` 的两个 fixture——但二者**均无静态调用方**（死 fixture），且**本卡未碰该文件**，其 `mocker` 依赖在本卡前后逐字一致 ⇒ **本卡对它们零影响面**，「无外溢」的结论仍成立，但**依据换成了正确的取名面**。

（这正是工程坑「⛔ 搜索面划窄 = 假阴性」与「⛔ 判据取名面必须恰好等于其主张」的又一实例；卡文 §〇 抄的就是这条窄判据 —— 见 §9 台账条目 ⑥。）

---

## 8. (l) 提交 / 绑定 / `ruff format` 豁免

- 代码 commit **`ee16b85a`**：header **95** 字符（`wc -m`，≤100），含 `[BATCH-2026-09-11-第十四批 / CARD-RED-ENVDEP]` 与卡号；最长 body 行 **80** 字符；NUL 检查 **NO-NUL**（带验伪锚：人造含 NUL 文件报 HAS-NUL、纯文本报 NO-NUL）。
- `*.stderr*` **不入库**：`git check-ignore -v` 实测本卡 `.stderr` 命中 `.gitignore:264 _bmad-output/审查/**/*.stderr*`（rc=0），而同名 `.md` **不**被忽略（rc=1，验伪锚证规则不是全覆盖）；staged 清单里 `stderr` 命中 **0**。
  > ⚠️ **一处判据取名面更正（自查）**：收口时我先跑的 `git ls-tree -r HEAD --name-only | grep -c 'stderr'` 得 **3**，那是**子串匹配文件名**、不是 `*.stderr*` 的语义。逐条归因：三条均为**主干既有**的 `.txt`（`G4-9-evidence/census-stderr.txt`、`evidence-g29f1/stderr-not-tracked-*.txt`、`evidence-pyright-svc/stderr-gate-*.txt`），在 **B14_BASE `08100483`** 上就已存在（`git ls-tree -r 08100483 | grep -c stderr` = **3**）；本卡 `8381417b..HEAD` 引入 = **0**，`grep -c 'CARD-RED-ENVDEP.*stderr'` = **0**（验伪锚：同一式对本卡 `codex-review-…-r1.md` 命中 **1**）。结论不变，但判据措辞按实际取名面改写。
- **未 push**（`origin/card/t10-red` 远端分支不存在 = 从未推送）。

**`ruff format --check` 豁免（与前卡 T10-A 同先例）** — `format-drift-attribution-20260914T203926.txt`：

| 段 | 实测 |
|---|---|
| A `ruff check`（lint 面） | `All checks passed!` rc=**0** |
| B `ruff format --check`（改后文件） | rc=**1** |
| C 同一文件在 **B14_BASE `08100483`** 上（`--stdin-filename` 保证 config 同路径解析） | rc=**1** ← **存量** |
| C2 同一文件在 **PREREQ `8381417b`** 上 | rc=**1** |
| C3 验伪锚：一个 already-formatted 文件（`tests/unit/__init__.py`） | `1 file already formatted` rc=**0** ← 证探针**不是恒红** |
| D vs E | 基线与改后的 `--diff` hunk **内容逐字相同**，仅行号位移（+16/+23/+23） |
| F 仓库级存量 | `tests/unit` **164/256** 需重排；`app/` **141/264** 需重排 |

⇒ 本卡新增 ruff format 违规 = **0**。按 **D-40「语义卡不得代劳整仓格式化」**，本卡**不**顺手 `ruff format` 重排既有行；以 `LEFTHOOK_EXCLUDE=python-lint` 提交，**双举证**：
1. 未豁免的提交尝试原始输出 `commit-attempt-20260914T203940.txt`（可见 `ruff check` → `All checks passed! / Lint OK.`，**仅** `ruff format --check` 报 `1 file would be reformatted`）；
2. 上表 C/C2/D 的基线归因。

豁免提交 `commit-done-20260914T203946.txt` 自证：`python-lint (skip) name`，而 **`ghost-files` 与 `mutant-residue-scan` 两门仍实跑并 ✔️**（不是整条 pre-commit 被关掉）。

**终审绑定**（文档 commit `8e188d28` 后实测）：

```
git diff --stat --no-color ee16b85a HEAD -- . ':(exclude)_bmad-output'
  → 输出 0 行（代码面为空 ⇒ Codex r1 仍绑最终 HEAD）✅
```

**⛔ 验伪锚（防「没跑成读成绿」）**：
- 去掉 `':(exclude)_bmad-output'` → **18** 个文件，其中 `_bmad-output/` 下 = **18** ⇒ pathspec 真在过滤，主判据的「0 行」不是命令没跑成 ✅
- 写法自证：`rc(':(exclude)…') = 0` 而 `rc(':!…') = 128` ← **本机实测印证协议 §1 的警告**（zsh + git 2.50 下 `':!…'` 报 `Unimplemented pathspec magic`、rc=128 且 stdout 空，用它会把没跑成读成绿）。本卡全程只用 `':(exclude)…'` ✅

**三条 nodeid 终态复核**（在最终 HEAD `8e188d28` 上实跑）：`2 passed, 2 skipped`，rc=**0** ✅

**存档卫生一处如实声明**：`evidence-red-envdep/.runpath` 是 (i) 的 `$RUN` 路径落盘（协议 §2.2 禁 glob，故先把文件名定成变量并留证）。它本应改名为可见的 `unit-close-runpath.txt`，但**本机用户级只读守卫阻断了 `mv` 与 `rm`**（同 T9-A 遇到的阻断），无法改名或删除；已就地补写说明头如实保留，未伪装成别的东西。

---

## 9. (m) 本卡未证明什么（≥4）

1. **两条 `mocker` 档在本批两个可用 venv 里是 SKIPPED 而非真跑** —— 它们断言的行为（`DEBUG_AGENT_RESPONSE` 开/关时的日志）在本批**完全没有被执行覆盖**。只有装了 `pytest-mock` 的 clean install 才会真跑。本卡把「ERROR 噪音」换成了「诚实的空覆盖」，**没有**增加这两档的实际保护力。
2. **未证明 `pytest-mock>=3.14.0` 这个 floor 在 clean install 上能装成**（批中禁装，未 `pip install` 验证），也未证明装上后那两档就会**通过**——它们此前从未在有插件的环境里跑过。
3. **未证明 `app.config` 的 `@lru_cache get_settings()` 单例路径对本档无影响**：本卡靠「新建实例 + delenv」规避，**未审**单例在别的测试改过 env 后的行为。（Codex r1 第 0 点复核「本档确实没读单例」，但没有覆盖单例本身。）
4. **未证明 `app/__init__.py` 的 import 期 `load_dotenv` 对其它读真 `.env` 的测试（非本卡三条）的影响面** —— 本卡只修自己这三条。
5. **未证明 skipif 的 `find_spec` 对「装了但不兼容版本」「装了但插件被停用」的判定**（= Codex LOW-1，门只覆盖「在 / 不在」）。
6. **未证明 `Settings(_env_file=None)` 完全脱离机器环境** —— Codex r1 第 4 点如实指出：实例化仍会校验**其它**环境字段（例：非法 `MAX_CONCURRENT_REQUESTS` 会导致 `ValidationError`）。这是既有依赖、非本卡新增，但「这一档现在跟环境无关了」的说法**只对 `DEBUG_AGENT_RESPONSE` 这一个字段成立**。
7. **未证明 `ruff format` 存量在本卡两文件之外的归因** —— 只证了本卡文件的 rc=1 在基线已成立 + 仓库级规模数字，未逐文件归因那 164/141。

## 10. 台账待登记条目（≥4，**只主 session 改台账，本卡未动**）

1. **本卡修复 sha 与效果**：代码 `ee16b85a`（+ 文档 commit）；三条 nodeid 状态 = 2 SKIPPED + 1 passed；`tests/unit` diff **`>` 行 = 0**、`<` 行 = 30（本卡 3 + T10-A 27）；目录级 `34 failed, 5105 passed, 50 skipped, 23 xfailed`。
2. **⛔ 批级通告候选（协议 §2.3）**：`pytest-mock>=3.14.0` **已进 `backend/requirements.txt` 但本批未装**。建议第十五批 / clean install 装上，以让两条 `mocker` 档**真跑**（当前是诚实的空覆盖）。装 = 共享 venv 变更 ⇒ **须批级通告 + 手册 §零 追加一行**。
3. **env 测试隐性依赖的通用坑 + 本卡修法作模板**：A2 §7「禁 `.env` ≠ 禁进程环境变量」。模板 = `monkeypatch.delenv(KEY, raising=False)` + `Settings(_env_file=None)`，**两者缺一不可**（负控①三行对照已实证：仅 `_env_file=None` 仍读到 True）。后续 ENVDEP 类卡直接引用。
4. **`_settings_factory` 地盘归属**：`test_sync_batch_auth.py` / `test_system_endpoint_auth.py`（**T10-E**）本卡未碰；其 `debug=True` 等档仍合并真 `.env`（A2 §7 第 7 条移交）仍在 T10-E 面。
5. **Codex 存档**：`codex-review-CARD-RED-ENVDEP-r1.md`，绑定 `ee16b85a`，`gpt-6-astra` / `ultra` / `codex-cli 0.153.3`，**B0 / H0 / M0 / L1**；LOW-1 登记不阻断（理由见 §7.1）。
6. **⛔ 工程坑候选 ×3**：
   - 「函数体 `pytest.importorskip` 对**签名里**的 fixture 无效，必须用 `@pytest.mark.skipif`」（skipping 插件 `tryfirst` 早于 fixture 填充）；
   - 「`grep -rln <pat> <dir>/*.py` 的取名面是**目录直属文件**，不是整棵树 —— `-r` 不扩展 shell glob」（本卡被 Codex 抓到，见 §7.2，卡文 §〇 抄的就是这条窄判据）；
   - 「`LC_ALL=C grep -c $'\0' file` 在 zsh 下是**恒真探针**」（`$'\0'` 被展开成空串，空模式匹配每一行 → 报行数当 NUL 数）；正确写法 `tr -d '\000' < f | cmp -s - f`，并带人造含 NUL 文件做验伪锚。
7. **`python-lint` 门的设计问题（候选移交）**：`ruff format --check` 是**绝对口径**，在 164/256 + 141/264 已违规的仓库里对**每张碰 Python 的卡**恒红 ⇒ 每卡都要豁免、门实际不再挡任何东西。建议随 D-40 整仓格式化一并改成「相对基线无新增」口径。

---

## 11. DoD-3 · 4-A（Claude 已代验，技术证据）

| 完成条件 | 判据 | 结果 |
|---|---|---|
| (a) 第 0 分钟自证 | §1 + §1.1 | ✅ 含基线 64 / `find_spec=None` / `.env:17` / 锚点零漂移 |
| (b) 先红子集 = 2 ERROR + 1 FAILED | §2 | ✅（rc 落盘缺失已如实声明，不补造） |
| (c) requirements 加 `pytest-mock>=3.14.0` 只声明不装 | §3 | ✅ |
| (d) 两 mocker 档 skipif(find_spec None)、保留 `mocker` | §3 | ✅ |
| (e) env 档 delenv + `Settings(_env_file=None)` | §3 | ✅（选型理由 + Codex 复核） |
| (f) 改后 env passed + 两档 SKIPPED，无 ERROR/FAILED | §2 | ✅ rc=0 |
| (g) 负控三段、shasum 前后同、还原非 stash | §4 | ✅ 三段红在指定正文 |
| (h) 地盘核只两文件 | §5 | ✅ + 三验伪锚 |
| (i) tests/unit 同口径 diff 只 `<` | §6 | ✅ `>` 行 = **0** |
| (j) 现网只读 | §5 | ✅ 零命中 |
| (k) Codex 绑最终 HEAD 一轮 B/H = 0 | §7 | ✅ r1 即 0/0 |
| (l) 单独 commit、header ≤100、不 push | §8 | ✅ 95 字符 |
| (m) 两锚各 ≥4 | §9（7 条）/ §10（7 条） | ✅ |

## 12. DoD-3 · 4-B（零技术词，用户视角）

运行测试的时候，有两项会因为我这台机器上缺一个测试小工具而**被干净地跳过**（而不是像以前那样报错打断、在结果里留下红字），报告里还会写清楚"为什么跳过"；另一项不再受**我机器上的一个开关**影响，现在稳定通过。

**felt-sense**：我感觉这些测试终于只看代码本身了 —— 换一台机器、换一个同事的电脑跑，结果应该是一样的，不会再出现"在我这儿是红的、在你那儿是绿的"这种说不清的情况。放心。

不过有件事我要说在前面：**那两项被跳过的测试，现在等于没在检查任何东西**。它们不再碍事了，但也还没开始干活 —— 要让它们真的跑起来，需要把那个小工具装上，这件事我按规矩留到下一批（这一批不允许动大家共用的环境）。所以现在的状态是"**不再假红，但也还没真绿**"，我没有把它说成已经保护好了。
