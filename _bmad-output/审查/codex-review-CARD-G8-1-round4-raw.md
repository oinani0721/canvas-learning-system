总裁定：**需整改**。

三个冻结对象开跑、收尾 SHA-256 均与指定值完全一致；这证明本报告绑定了正确字节，但不代表规范符合。指定回归门多数有效，仍存在可复现的静默盲区、G9/union 绕过和台账事实矛盾。

## 逐项裁定

| 项目 | 裁定 | 核心结论 |
|---|---|---|
| B1 目录 symlink | **NOT-CLOSED / BLOCKER** | 指定 alias 场景已报 G8；但不可读对象、非解析 symlink、超长路径仍可 `rc=0/findings=[]`，且外部文件 symlink 可被越界读取 |
| B2 frontmatter | **CLOSED（解析器层）** | 真实写侧函数 identity 相同；第三轮 11 形态及额外 corpus 均 0 不等价 |
| H1 repo_docs 数量 | **CLOSED** | 独立复得 `2428 / 1460 / 968` |
| H2 空结构 | **CLOSED** | entry 与 repo_docs 两侧六个对照全部 `ConfigError` |
| H3 事件流措辞 | **NOT-CLOSED / HIGH** | 新说明符合代码，但 YAML 另一行仍声称 frontmatter 可由事件账重放 |
| H4 根级 G9 | **NOT-CLOSED / HIGH** | 指定正反例正确；但 `known_instances` 可改成标量，利用字符串子串绕过 |
| H5 union catch-all | **NOT-CLOSED / HIGH** | 同一行 union 已阻断；拆成多条 entry/divergence 后仍可吞掉 G1/G6 |
| resolution 声明 | **CLOSED** | 两条均显式 `true`；缺字段或 false 无理由均拒绝 |
| 五个 mutation | **CLOSED** | 全部被对应测试杀死，无 survivor |
| 双准入面未被误修 | **CLOSED** | 无业务代码改动，DIV-1/DIV-2 均保留 |

## 冻结锚点与测试

```bash
shasum -a 256 \
  backend/scripts/vault_doc_roles.yaml \
  backend/scripts/check_vault_doc_roles.py \
  backend/tests/unit/test_vault_doc_roles.py
```

开跑和收尾输出相同：

```text
1c90ca3600d11daeea0d28e469d8bb37b8c014b08ea09750ea2e76d5dd57022a  YAML
776223e9d6a1d7a0f93e9bcd0a1a924bb8e0157b97c55e38a48481e467e8eb8c  checker
c817ddab6f76c8685b35b7b1a82c21762053e82dc684881eb7232741f25fb79e  tests
```

完整冻结测试：

```bash
env PYTHONDONTWRITEBYTECODE=1 \
  TMPDIR=/tmp/card-g8-r4-main-tmp \
  backend/.venv/bin/pytest \
  backend/tests/unit/test_vault_doc_roles.py \
  -q -p no:cacheprovider \
  --basetemp /tmp/card-g8-r4-main-pytest
```

```text
collected 85 items
85 passed, 10 warnings in 79.49s
```

但“24 个测试函数”不实：

```bash
rg -c '^def test_' backend/tests/unit/test_vault_doc_roles.py
# 30
```

实际为 **30 个 Python 测试函数、24 个编号语义组、85 个参数化 item**；测试文件头仍写“本文件 11 个”。列为 LOW 文案偏差。

## B1：指定 G8 成功，但扫描完整性仍失守

指定场景：

```bash
backend/.venv/bin/python -B backend/scripts/check_vault_doc_roles.py \
  --enforce --json \
  --vault /tmp/card-g8-r4-agent-a-20260830T1635/dir-symlink
```

```text
exit=1
finding: G8 / 检验白板/alias-node-dir
exempted_by=""
```

G8 位于 [checker.py:762](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:762)，且 `known_gaps` 仅能豁免 G1/G2/G3。

但以下生产 CLI 对照仍静默绿：

```text
不可读子树 d---------:
exit=0, files_seen=0, findings=[]

不可读 Markdown ----------:
exit=0, files_seen=1, findings=[]

broken link / self -> self:
is_symlink=True, is_dir=False, is_file=False
exit=0, findings=[]
```

根因：

- 两轮枚举先分别过滤 `is_dir()`、`is_file()`：[checker.py:762](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:762)、[checker.py:781](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:781)。
- 文件读取 `OSError` 被直接折叠成 `(none)`：[checker.py:635](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:635)。

可解析的祖先循环和指向 vault 外现存目录的 symlink 能正确报 G8；dangling/self/ELOOP 不能。

超长路径在本机 macOS/Python 3.14 也复现：

```text
PATH_MAX=1024
relative_chars=1307
dir_fd 可回读 rogue_long_path
rglob_has_rogue=False
CLI exit=0, files_seen=0, findings=[]
```

该结果为当前平台确定事实，跨平台需重测。

更严重的是外部文件 symlink。主轨独立复跑：

```text
检验白板/external.md -> vault 外 outside-target.md
target type: exam_board
rc 0
is_symlink True
target_outside True
checker_type exam_board
findings []
```

checker 在准入判断前读取 frontmatter（[checker.py:816](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:816)），真实准入到 [checker.py:838](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:838) 才执行。`检验白板` 本来声明 F/F，所以外部目标同为 F/F 时 G5/G6 均不触发。此项是独立 **BLOCKER**。

## B2：解析器对拍关闭

输出确认：

```text
PARSER available=True
identity=True
module=agentic_rag.clients.lancedb_client
qualname=LanceDBClient._parse_frontmatter
```

直接复用位于 [checker.py:606](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:606)，写侧函数在 [lancedb_client.py:2142](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:2142)，最终取值在 [lancedb_client.py:2740](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:2740)。

第三轮 11 形态：

```text
type-space          rogue / rogue
quoted-key          x / x
value-case          concept / concept
upper-key           (none) / (none)
bad-yaml            (none) / (none)
crlf                rogue_crlf / rogue_crlf
open trailing       rogue_open_space / rogue_open_space
close trailing      rogue_close_space / rogue_close_space
dots terminator     (none) / (none)
missing closing     (none) / (none)
after line 400      rogue_after_400 / rogue_after_400
MISMATCHES=0
```

冻结用例 21：

```text
12 passed
```

另测 BOM、重复键、null/数字/bool/list/mapping、多行、merge、NUL 等 14 类，以及组合/随机 corpus 12,584 项，均 `mismatches=0`。

相邻的新 HIGH：checker 用 `errors="replace"`，而真实写侧严格 UTF-8 并在解码失败时跳过文件（[lancedb_client.py:1979](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:1979)）。非法 UTF-8 文件可出现：

```text
checker exit=0/findings=[]
writer strict read -> UnicodeDecodeError / return 0
```

这不推翻字符串解析器层的 CLOSED，但端到端读取语义仍未等价。

## H1、H2 与 resolution

repo_docs 使用 checker 自身 `glob_match` 对 `git ls-files -z '*.md'` 复算：

```text
tracked 2428
covered 1460
uncovered 968
unique 1460
overlaps 0
```

空结构六个对照：

```text
entry.owner=None       | ConfigError
entry.provenance=[]    | ConfigError
entry.retention={}     | ConfigError
repo.owner=None        | ConfigError
repo.provenance=[]     | ConfigError
repo.retention={}      | ConfigError
```

resolution 契约：

```text
frozen:
DIV-1 explicit=True value=True
DIV-2 explicit=True value=True

missing                | ConfigError
false_no_rationale     | ConfigError
false_with_rationale   | ACCEPT
```

对应实现见 [checker.py:434](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:434)、[checker.py:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:464)、[checker.py:507](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:507)。

## H3：台账仍自相矛盾

代码事实支持新表述：

```text
quiz-answer/SKILL.md:316-320  先 tmp + os.replace 写 frontmatter
quiz-answer/SKILL.md:322-343  后追加 event，失败“不影响评分”
payload:333-338              仅 grade_norm/exam_board/attempt_count
learning_event_log.py:68,103-105  异常返回 False
```

但冻结 YAML 同时存在：

```text
339 frontmatter 是 FSRS 与掌握度的真相源
341 retention: ... frontmatter 复习字段可由事件账重放
619-625 二者互不可重建，事件流是尽力而为的侧记
```

矛盾行见 [vault_doc_roles.yaml:341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:341)。因此 H3 为 **NOT-CLOSED / HIGH**。

## H4：指定场景通过，allowlist 契约可绕过

生产 CLI：

```text
machine-generated-report.md:
rc=1
finding=G9

chatgpt-adversarial-review-Q1Q2Q3-2026-05-12.md:
rc=0
findings=[]
```

但 `known_instances` 没有列表结构校验。内存变异：

```python
known_instances = "chatgpt-...md,future-report.md"
_verify_contract(data)
```

```text
contract ACCEPT
future_membership True
machine_membership False
known_index0 'c'
future-report.md G9=[]
```

扫描处直接执行字符串 membership，见 [checker.py:796](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:796)。该变异还能让用例 23 的“已登记正例”创建单字符文件并保持 G9 断言绿色。因此 H4 整体 **NOT-CLOSED / HIGH**。

## H5：行内关闭，跨行仍绕过

指定同一行反例在 entry 和 divergence 两侧均拒绝：

```text
entry      | ConfigError | dir_glob 并集构成 catch-all
divergence | ConfigError | patterns 并集构成 catch-all
```

其他同行写法如：

```text
[".*", "[!.]*"]
["**/x*", "**/[!x]*"]
["**/[0-9]*", "**/[!0-9]*"]
```

也均识别为 union catch-all。

但把两个模式拆成两行：

```text
ENTRY_CONTRACT=ACCEPT
future          -> split-catch-non-dot
.future         -> split-catch-dot
future/deep     -> split-catch-non-dot
future/.deep    -> split-catch-dot
SPLIT_ENTRY_G1=[]
```

同样拆成两条 `by_design_divergences`：

```text
DIV_CONTRACT=ACCEPT
DIV_COVERED future.MD=True
DIV_COVERED .future.MD=True
DIV_COVERED x/future.MD=True
DIV_COVERED x/.future.MD=True
```

原因是契约只逐行检查 [checker.py:413](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:413)、[checker.py:453](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:453)，而实际覆盖在 [checker.py:964](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:964) 跨行 OR。H5 为 **NOT-CLOSED / HIGH**。

## 五个 mutation

所有变异仅在 `/tmp/card-g8-r4-agent-b-kuzAal/`。用例 21 显式加入 `backend/lib`，避免 `importorskip` 产生假绿。

| 变异 | 对应 selector 输出 |
|---|---|
| 删除 G8 报告 | `rc=1, 1 failed`，G8 集合为空 |
| 删除 G9 检查 | `rc=1, 1 failed`，machine-generated-report 未报 G9 |
| `is_union_catch_all=False` | `rc=1, 4 failed, 3 passed` |
| `_TEXT_FIELDS` 置空 | `rc=1, 1 failed, DID NOT RAISE ConfigError` |
| 默认路径不调用写侧 parser | `rc=1, 1 failed, 11 passed`；失败项 `dots-terminator` |

结论：**五个指定门均有效，无 mutation survivor**。但它们没有覆盖上述跨行 union、标量 `known_instances`、walker 错误和文件 symlink 读界。

## 双准入面与工作树

```bash
git rev-parse HEAD
# cbb20afb572a7b8ce9ebc205082e4be6de076fb8

git diff cbb20afb --stat
git diff cbb20afb --name-only -- backend/app backend/lib frontend
git ls-files --others --exclude-standard -- backend/app backend/lib frontend
# 均无输出
```

`git status --porcelain=v1 --untracked-files=all` 开跑与收尾一致：18 个既有 untracked 文件，即冻结三件、证据、审查稿和 UAT；无 `backend/app`、`backend/lib`、`frontend` 业务工件。

```bash
rg -n 'id: DIV-1-root-level-md|id: DIV-2-md-suffix-case' \
  backend/scripts/vault_doc_roles.yaml
```

```text
148: DIV-1-root-level-md
174: DIV-2-md-suffix-case
```

生产 fixture 同时观察到根级 md 与 `节点/FOO.MD` 两条已登记分歧，`findings=[]`。因此“双准入面分歧未被误当 bug 修”这一卡片重点 **CLOSED**。

另有机器证据问题：JSON 即使实际输出 G8/G9，`checks_run` 仍只列 G1–G7，见 [checker.py:1089](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:1089)，列为 **MEDIUM**。非冻结 UAT/证据 README 也存在 G1–G7、learning_events 角色、旧测试文件名等陈旧口径。

限制：仓库要求的 `graphiti-canvas` 本轮未在工具清单中暴露，因此无法执行 Graphiti 检索；这不影响上述本地生产 CLI、源码和冻结字节复算。所有主动夹具只写 `/tmp`，工作树未修改。


