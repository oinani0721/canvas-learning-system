# ⚠️ CARD-G1-5 (BATCH-2026-08-27-第四批) — README 禁夸大声明机械裁判的裁判
#
# 被测物: backend/scripts/check_readme_claims.py + readme_claims_rules.yaml
# 规则真相源: 计划书 §12.7 L633 的 11 类禁夸大声明
#   (_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md)
#
# 语义钉死点 (Codex 一轮 2B+5H 与二轮 3B+5H 的全部处置回归):
#   1. 阳性: 11 条规则各 ≥1 canonical 句必中 (含两轮审查展示的漏报等价句)
#   2. 近邻阴性: 缺任一 L633 conjunct 的表述 0 命中 (防私自扩大)
#   3. hard-forbidden: 证据标注 / legacy / 否定拼接均不放行
#   4. 逃逸五条件: 绑定规则编号 + E 级枚举 + 仓库内 tracked 非空文件 + 非自引用 +
#      不藏在 HTML 注释/code span 里
#   5. 配置面指纹: yaml 任何字节变化 (含正则/legacy) 未同步脚本常量 = 退出 2
#   6. staged-diff: 新增行永不吃 legacy; "++" 行 / diff.noprefix / -diff 属性均不可绕过
#   7. legacy: 上下文指纹 + 行号锚 + 配额, 搬移/复制均失效; hard 类连 legacy 也免疫
#   8. 白名单: scan_paths 外的文件永不扫; --root 指错 = 退出 2 而非伪绿
#   9. 真仓基线: 现行 README = 3 命中全 C9 全 [legacy], G1-4 横幅 0 误伤
#  10. 跨文件同步: lefthook glob 与 workflow paths 与 scan_paths 一致 (契约断言)

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import check_readme_claims as crc  # noqa: E402

REAL_RULES = _SCRIPTS_DIR / "readme_claims_rules.yaml"
REPO_ROOT = Path(__file__).resolve().parents[3]

# 现行 README 中勘探实锤的 3 行 14-Agent 旧声明 (逐字) 与其 legacy 登记行号锚
LEGACY_AGENT_LINES = [
    (
        "Canvas Learning System transforms **passive learning** into an **active learning process**. "
        "With 12-14 specialized AI Agents collaborating, it guides you from confusion to mastery "
        "through the Feynman Learning Method."
    ),
    "- **Personalized Guidance** - 14 specialized AI Agents",
    "### 14 Specialized AI Agents",
]
LEGACY_ANCHORS = [35, 50, 68]

# G1-4 实际落入 README 的新增文本 (横幅 + 5 处就地标注)。
# 非空行与 README 中的新增行逐字一致; 空行布局非严格相同 (裁判是逐行 matcher, 等价)。
G1_4_BANNER_TEXT = """\
> [!WARNING]
> **诚实止血横幅（2026-08-27 · CARD-G1-4）** — 本 README 为历史介绍文档，内容跨越两个架构时代，尚未按当前系统状态重新验证。已知漂移点：
> 1. **Agent 数量前后矛盾** — 下文三处分别写 12-14（Overview）与 14（Our Solution 要点、Features 标题），正文实际列出 11 个；后端 `AgentType` 枚举 15 个值（含 2 个兼容别名）、另一处后端清单 14 项，各处口径互不一致。
> 2. **旧插件目录名** — 安装步骤中的 `.obsidian/plugins/canvas-review-system/` 是旧目录名，与当前插件目录不一致。
> 3. **旧 Quick Start 流程** — 「右键调用 Agent」的 `.canvas` 操作流程在当前插件代码（main.ts）中没有对应事件挂载，按此操作无法复现。
> 4. **端口与监听地址漂移** — 本文写有 8000 与 8001 两种端口；仓库当前 `.env.example` 实际使用宿主端口 8011，与本文不一致；`--host 0.0.0.0` 与 2026-07-31 的 P0-0 安全决策相抵触，请勿照抄。
> 5. **未验证描述** — 「Auto-generated review Canvas」等 Review System 描述未在当前架构下重新验证。
>
> 相对可信的入口：下方 **Docker Deployment** 一节经 2026-08-27 勘探实测相对可信，可作为部署起点；其余章节请以仓库内代码、测试与验收单为准。

> ⚠️ 漂移标注（2026-08-27）：本段 Agent 数量与下文不一致——此处写 12-14，下文 Our Solution 要点与 Features 标题写 14，正文实际列出 11 个；后端多处枚举（15 值含 2 别名 / 14 项清单）口径也互不一致，数字待重新核定。

> ⚠️ 漂移标注（2026-08-27）：本节「Auto-generated review Canvas」等描述未在当前架构下重新验证，实际行为以仓库内代码与测试为准。

   > ⚠️ 漂移标注（2026-08-27）：`canvas-review-system` 是旧插件目录名，与当前插件 manifest ID 及部署目录（`canvas-learning-system`）不一致，按本行操作可能导致插件无法正常加载。

> ⚠️ 漂移标注（2026-08-27）：上方 `--host 0.0.0.0 --port 8000` 与本文 Docker 段的 8001、仓库 `.env.example` 当前的 8011 端口配置互相矛盾；`0.0.0.0` 监听与 2026-07-31 的 P0-0 安全决策相抵触，请勿照抄。

> ⚠️ 漂移标注（2026-08-27）：以下「右键调用 Agent」流程在当前插件代码（main.ts）中没有对应事件挂载，按此步骤操作无法复现；本节属旧架构时代文案。
"""


def _write_readme(root: Path, text: str) -> None:
    (root / "README.md").write_text(text, encoding="utf-8")


def _enforce(root: Path) -> int:
    return crc.main(["--enforce", "--root", str(root), "--rules", str(REAL_RULES)])


def _report(root: Path) -> int:
    return crc.main(["--report", "--root", str(root), "--rules", str(REAL_RULES)])


def _hits(root: Path) -> list:
    cfg = crc.load_rules(REAL_RULES)
    return crc.scan_scan_paths(root, cfg)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


def _init_repo(root: Path, readme: str) -> None:
    _git(root, "init", "-q")
    _write_readme(root, readme)
    _git(root, "add", "README.md")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "base")


# ---------------------------------------------------------------- 阳性 / 阴性


CANONICAL_POSITIVES = [
    ("C1-production-ready", "The system is production-ready."),
    ("C1-production-ready", "Ready for production deployment."),
    ("C2-any-vault-one-click", "Works with any vault, one-click setup."),
    ("C2-any-vault-one-click", "Every vault works with one click."),
    ("C2-any-vault-one-click", "Each vault works out of the box."),
    ("C3-multi-vault-safe", "Fully multi-vault safe."),
    ("C4-graphiti-full-rebuild", "Graphiti data is permanently and fully rebuildable."),
    ("C5-multisource-rag-default", "Full multi-source RAG is the default main chain."),
    ("C6-hit-at-k-as-recall", "Our retrieval recall@5 reached 0.92."),
    ("C6-hit-at-k-as-recall", "The hit@k metric is labeled recall@k."),
    # C6 政策裁定: README 内 recall@k 一律拦 (本仓指标实为 hit rate, G4-12 正名中),
    # 自称"真 recall"也不例外 — 行内豁免曾被证明可拼接洗白 (Codex 二轮 B1')
    ("C6-hit-at-k-as-recall", "Measured true recall@5 over a labeled relevance corpus."),
    ("C6-hit-at-k-as-recall", "We call hit@k recall."),
    ("C6-hit-at-k-as-recall", "Top-5 recall is the fraction of queries with at least one relevant hit."),
    ("C7-fsrs-ui-consistent", "FSRS and UI are fully consistent."),
    ("C8-canvas-excalidraw-lossless", "Canvas↔Excalidraw lossless bidirectional conversion."),
    ("C9-agent-collab", "- **Personalized Guidance** - 14 specialized AI Agents"),
    ("C9-agent-collab", "14 个智能体协同工作。"),
    # C9 政策声明范围: 双位数 Agent 阵容宣称 (不限定恰为 14, 不要求协同字样)
    ("C9-agent-collab", "19 specialized AI Agents available independently."),
    ("C10-mobile-ready", "Available on mobile."),
    ("C11-skipped-as-success", "Skipped checks mean success."),
    ("C11-skipped-as-success", "Degraded is considered successful."),
    ("C11-skipped-as-success", "Skipped checks are successful."),
    ("C11-skipped-as-success", "Skipped checks indicate success."),
    ("C11-skipped-as-success", "CI treats skipped checks as success."),
    # 否定拼接不解除 hard: 第一分句无否定, 仍拦 (Codex 二轮 B1' 反例)
    ("C11-skipped-as-success", "Skipped means success; degraded is not treated as success."),
    # Codex 三轮反例: 直接谓词 / 注释藏否定 / but-indicate 拼接
    ("C11-skipped-as-success", "Skipped checks pass."),
    ("C11-skipped-as-success", "Skipped <!-- not --> means success."),
    ("C11-skipped-as-success", "Skipped checks do not mean failure but indicate success."),
    # Codex 四轮反例: 无关谓词的 not 不解除 / 贪婪吞谓词 / 字面等价 / 过去时
    ("C11-skipped-as-success", "Skipped checks do not fail but indicate success."),
    ("C11-skipped-as-success", "Skipped checks mean success but are not treated as success."),
    ("C11-skipped-as-success", "Skipped checks were successful."),
    ("C6-hit-at-k-as-recall", "Hit@k = recall."),
    ("C6-hit-at-k-as-recall", "Hit@k is recall."),
    # C9 双位数政策边界 (10-99, 不要求协同字样)
    ("C9-agent-collab", "20 specialized AI Agents shipping soon."),
    ("C9-agent-collab", "99 specialized AI Agents in the roadmap."),
    ("C9-agent-collab", "42 AI Agents are available."),
    # Codex 五轮反例: 掩码重扫跨度 / equal 等价族 / 重复等号
    ("C11-skipped-as-success", "Skipped checks are not considered successful but indicate success."),
    ("C11-skipped-as-success", "Skipped checks equal success."),
    ("C6-hit-at-k-as-recall", "Hit@k == recall."),
    # Codex 六轮反例: 系词+等价短语组合 / 主谓间隔等号 / 中文「个 Agent」直接族
    ("C6-hit-at-k-as-recall", "Hit@k is equivalent to recall."),
    ("C6-hit-at-k-as-recall", "Hit@k is equal to recall."),
    ("C11-skipped-as-success", "Skipped checks == success."),
    ("C11-skipped-as-success", "Degraded mode === success."),
    ("C9-agent-collab", "42 个 Agent 可用。"),
    ("C9-agent-collab", "42 个 AI Agents 可用。"),
    # Codex 七轮反例: canonical 主语组合 / Markdown 强调切断 / 中英混排无空格
    ("C6-hit-at-k-as-recall", "The hit@k metric is equivalent to recall."),
    ("C6-hit-at-k-as-recall", "Hit@k metric == recall."),
    ("C6-hit-at-k-as-recall", "`Hit@k` is equivalent to recall."),
    ("C6-hit-at-k-as-recall", "Hit@k is **equivalent to** recall."),
    ("C11-skipped-as-success", "Skipped checks **==** success."),
    ("C11-skipped-as-success", "Skipped checks == **success**."),
    ("C9-agent-collab", "42个Agent可用。"),
    ("C9-agent-collab", "42个AI Agents可用。"),
    # Codex 八轮反例: CJK 前导处 Unicode \b 失效 (当前full / 共有42) + 混排 mobile
    ("C5-multisource-rag-default", "当前full multi-source RAG 是默认主链。"),
    ("C9-agent-collab", "共有42 AI Agents协同。"),
    ("C9-agent-collab", "现有14 Agents协同。"),
    ("C10-mobile-ready", "mobile可用。"),
    # Codex 九轮穷举反例: C11/C2/C10 全部 CJK 紧邻边界端点
    ("C11-skipped-as-success", "Skipped checks mean成功。"),
    ("C11-skipped-as-success", "Skipped checks indicate成功。"),
    ("C11-skipped-as-success", "Skipped checks equal成功。"),
    ("C11-skipped-as-success", "Skipped状态is success。"),
    ("C11-skipped-as-success", "Skipped is 成功了。"),
    ("C11-skipped-as-success", "Skipped检查pass。"),
    ("C11-skipped-as-success", "Skipped checks pass了。"),
    ("C2-any-vault-one-click", "当前any vault 一键可用。"),
    ("C2-any-vault-one-click", "any类 vault 一键可用。"),
    ("C2-any-vault-one-click", "当前 any vault一键可用。"),
    ("C10-mobile-ready", "当前available on mobile。"),
    ("C10-mobile-ready", "available on mobile端。"),
    ("C10-mobile-ready", "当前mobile is available。"),
    ("C10-mobile-ready", "mobile is ready了。"),
    # Codex 十轮反例: 等于 直接等同句 (宾语排除的接管缺口)
    ("C11-skipped-as-success", "Skipped checks 等于成功。"),
]

NEAR_MISS_NEGATIVES = [
    "Many vaults offer one-click import.",
    "Multi-vault safe storage layout.",
    "Graphiti is fully rebuildable.",
    "Graphiti supports permanent partial restore checkpoints.",
    "Limited multi-source RAG is the default main pipeline.",
    "Lossy Excalidraw bidirectional sync.",
    "One-way export into Excalidraw is lossless.",
    "3 specialized AI Agents for a prototype.",
    "3 AI Agents collaborate.",
    "Skipped is not treated as success.",
    "Skipped results must not be treated as success.",
    "Never treat skipped as success.",
    "Degraded mode is available on green environments.",
    # Codex 三轮反例: 缺 Canvas / 跨分句拼接 conjunct
    "Excalidraw provides lossless bidirectional SVG conversion.",
    "This manual is complete; the storage layer is multi-vault safe.",
    "Skipped checks were not successful.",
    # 三位数阵容超出双位数政策范围, 不判 (Codex 五轮 MEDIUM 边界锁)
    "120 个智能体协同工作。",
    "共有120 AI Agents协同。",
    # CJK 紧邻的 not 否定尾正确抑制 (Codex 九轮 MEDIUM false-red 修复)
    "Skipped状态not等同成功。",
    "Skipped状态not等价成功。",
    "当前fuller multi-source RAG 是默认主链。",
    "一行诚实的部署说明。",
]


@pytest.mark.parametrize(("rule_id", "sentence"), CANONICAL_POSITIVES)
def test_canonical_positive_per_rule(tmp_path: Path, rule_id: str, sentence: str) -> None:
    """T1 阳性: 11 条规则的 canonical 句 (含两轮审查的漏报等价句) 必中且判到正确规则."""
    _write_readme(tmp_path, sentence + "\n")
    hits = _hits(tmp_path)
    assert hits, f"应命中 {rule_id}: {sentence!r}"
    assert rule_id in {h.rule_id for h in hits}
    assert _enforce(tmp_path) == 1
    assert _report(tmp_path) == 0  # report 是信息档, 永远 0


@pytest.mark.parametrize("sentence", NEAR_MISS_NEGATIVES)
def test_near_miss_negative_zero_hit(tmp_path: Path, sentence: str) -> None:
    """T2 近邻阴性: 缺任一 L633 conjunct / 明确否定 / 个位数表述 0 命中 (防私自扩大)."""
    _write_readme(tmp_path, sentence + "\n")
    assert _hits(tmp_path) == []
    assert _enforce(tmp_path) == 0


# ---------------------------------------------------------------- 逃逸绑定


def test_escape_conditions(tmp_path: Path) -> None:
    """T3 逃逸: 规则编号 + E 级枚举 + docs/evidence/ 下 index 真实 blob + 非自引用 + 非隐藏, 缺一不放行."""
    _init_repo(tmp_path, "placeholder\n")
    evidence = tmp_path / "docs" / "evidence" / "deploy.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("proof\n", encoding="utf-8")
    _git(tmp_path, "add", "docs/evidence/deploy.md")

    # 全部齐备 → 放行 (命中仍被记录)
    _write_readme(tmp_path, "The deploy chain is production-ready [C1:E3](docs/evidence/deploy.md).\n")
    assert _enforce(tmp_path) == 0
    hits = _hits(tmp_path)
    assert len(hits) == 1 and hits[0].escaped is True

    bad_lines = [
        # 裸 [E3] 无规则绑定
        "The deploy chain is production-ready [E3](docs/evidence/deploy.md).\n",
        # 绑错规则编号
        "The deploy chain is production-ready [C9:E3](docs/evidence/deploy.md).\n",
        # 链接文件不存在
        "The deploy chain is production-ready [C1:E3](docs/evidence/nope.md).\n",
        # 不在受控证据目录 (docs/evidence/)
        "The deploy chain is production-ready [C1:E3](docs/other.md).\n",
        # README 自引用
        "The deploy chain is production-ready [C1:E3](README.md).\n",
        # E4+ 不在枚举 (只认 E3/E3+/E4/E5)
        "The deploy chain is production-ready [C1:E4+](docs/evidence/deploy.md).\n",
        # 反斜杠转义的标记 (markdown 渲染为字面文本, 不是链接)
        "The deploy chain is production-ready \\[C1:E3](docs/evidence/deploy.md).\n",
        # 标记藏在 HTML 注释里
        "The deploy chain is production-ready <!-- [C1:E3](docs/evidence/deploy.md) -->.\n",
        # 标记藏在 code span 里
        "The deploy chain is production-ready `[C1:E3](docs/evidence/deploy.md)`.\n",
    ]
    for bad in bad_lines:
        _write_readme(tmp_path, bad)
        assert _enforce(tmp_path) == 1, f"应拒绝逃逸: {bad!r}"

    # untracked 文件 → 不放行
    (tmp_path / "docs" / "evidence" / "untracked.md").write_text("x\n", encoding="utf-8")
    _write_readme(tmp_path, "production-ready [C1:E3](docs/evidence/untracked.md).\n")
    assert _enforce(tmp_path) == 1

    # intent-to-add (git add -N, index 无真实 blob) → 不放行
    (tmp_path / "docs" / "evidence" / "ita.md").write_text("x\n", encoding="utf-8")
    _git(tmp_path, "add", "-N", "docs/evidence/ita.md")
    _write_readme(tmp_path, "production-ready [C1:E3](docs/evidence/ita.md).\n")
    assert _enforce(tmp_path) == 1

    # 空文件 (tracked .gitkeep 式) → 不放行
    (tmp_path / "docs" / "evidence" / "empty.md").write_text("", encoding="utf-8")
    _git(tmp_path, "add", "docs/evidence/empty.md")
    _write_readme(tmp_path, "production-ready [C1:E3](docs/evidence/empty.md).\n")
    assert _enforce(tmp_path) == 1


def test_hard_forbidden_never_escapes(tmp_path: Path) -> None:
    """T4 名实类: hit@k 误名 recall, 带齐备证据标注也不放行."""
    _init_repo(tmp_path, "placeholder\n")
    (tmp_path / "bench.md").write_text("bench\n", encoding="utf-8")
    _git(tmp_path, "add", "bench.md")
    _write_readme(tmp_path, "Our retrieval recall@5 reached 0.92 [C6:E4](bench.md).\n")
    assert _enforce(tmp_path) == 1
    hits = _hits(tmp_path)
    assert len(hits) == 1
    assert hits[0].severity == "hard-forbidden"
    assert hits[0].escaped is False


def test_hard_forbidden_immune_to_legacy_at_engine_level(tmp_path: Path) -> None:
    """T4b hard 类连 legacy 也免疫 (引擎级: 上下文指纹与文本全匹配仍不吃 legacy)."""
    line = "Our retrieval recall@5 reached 0.92."
    _write_readme(tmp_path, line + "\n")
    all_lines = [line]
    real_cfg = crc.load_rules(REAL_RULES)
    entry = crc.LegacyEntry(
        file="README.md",
        line=line,
        registered_line=1,
        context_sha256=crc.context_digest(all_lines, 1),
        max_occurrences=1,
        reason="attempted laundering",
    )
    cfg = crc.RulesConfig(real_cfg.scan_paths, real_cfg.rules, (entry,))
    hits = crc.scan_lines("README.md", [(1, line)], cfg, tmp_path, all_lines=all_lines)
    assert len(hits) == 1
    assert hits[0].legacy is False and hits[0].effective is True


# ---------------------------------------------------------------- 配置面指纹契约


def _mutated_rules(tmp_path: Path, mutate) -> Path:
    raw = yaml.safe_load(REAL_RULES.read_text(encoding="utf-8"))
    mutate(raw)
    out = tmp_path / "mutated.yaml"
    out.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    return out


@pytest.mark.parametrize(
    "mutate",
    [
        lambda raw: raw["rules"].pop(1),  # 删 C2
        lambda raw: raw["rules"][5].__setitem__("severity", "evidence-escapable"),  # C6 降级
        lambda raw: raw["rules"][10].__setitem__("severity", "evidence-escapable"),  # C11 降级
        lambda raw: raw["rules"][0].__setitem__("patterns", ["(?!)"]),  # C1 正则掏空
        lambda raw: raw["legacy_allowlist"].append(
            {
                "file": "README.md",
                "line": "The system is production-ready.",
                "registered_line": 1,
                "context_sha256": "0" * 64,
                "max_occurrences": 99,
                "reason": "laundering",
            }
        ),  # 注入 legacy
        lambda raw: raw.__setitem__("scan_paths", ["DOES-NOT-EXIST.md"]),
        lambda raw: raw.__setitem__("scan_paths", ["README*.md"]),
        lambda raw: raw.__setitem__("scan_paths", "README.md"),  # 字符串而非列表
        lambda raw: raw["rules"][0].__setitem__("l633", "改口径"),
    ],
    ids=[
        "drop-rule",
        "downgrade-C6",
        "downgrade-C11",
        "gut-pattern",
        "inject-legacy",
        "ghost-path",
        "glob-path",
        "str-path",
        "l633-drift",
    ],
)
def test_any_yaml_mutation_is_error_not_green(tmp_path: Path, mutate) -> None:
    """T5 指纹契约: yaml 任何字节变化 (含正则/legacy) 未同步脚本常量 → 退出 2, 永不伪绿."""
    mutated = _mutated_rules(tmp_path, mutate)
    _write_readme(tmp_path, "The system is production-ready.\n")
    assert crc.main(["--enforce", "--root", str(tmp_path), "--rules", str(mutated)]) == 2


def test_rules_sha_constant_matches_disk() -> None:
    """T5b 自洽: --print-rules-sha 输出 == 脚本 RULES_SHA256 == 磁盘 yaml 实际指纹."""
    import hashlib

    disk = hashlib.sha256(REAL_RULES.read_bytes()).hexdigest()
    assert disk == crc.RULES_SHA256


def test_bad_root_and_missing_rules_exit_2(tmp_path: Path) -> None:
    """T5c: --root 指错 (含 staged 档) / 规则文件缺失 → 2 (拒绝伪绿)."""
    assert crc.main(["--report", "--root", str(tmp_path / "ghost"), "--rules", str(REAL_RULES)]) == 2
    _write_readme(tmp_path, "hello\n")
    assert crc.main(["--report", "--root", str(tmp_path), "--rules", str(tmp_path / "nope.yaml")]) == 2
    # staged 档对缺 README 的 root 同样 2, 不再伪绿 (Codex 二轮 B3')
    empty = tmp_path / "no-readme"
    empty.mkdir()
    assert crc.main(["--staged-diff", "--root", str(empty), "--rules", str(REAL_RULES)]) == 2


def test_files_outside_scan_paths_are_never_scanned(tmp_path: Path) -> None:
    """T6 白名单: scan_paths 外的文件塞满违禁词也是 0 命中."""
    _write_readme(tmp_path, "An honest readme.\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "hype.md").write_text(
        "production-ready! recall@10! 14 specialized AI Agents!\n", encoding="utf-8"
    )
    assert _enforce(tmp_path) == 0
    assert _hits(tmp_path) == []


# ---------------------------------------------------------------- legacy 语义 (引擎级)


def _engine_cfg_with_legacy(entries: tuple) -> object:
    real_cfg = crc.load_rules(REAL_RULES)
    return crc.RulesConfig(real_cfg.scan_paths, real_cfg.rules, entries)


def test_legacy_context_fingerprint_and_quota(tmp_path: Path) -> None:
    """T7 legacy 引擎语义: 指纹匹配处放行; 相同上下文的复制超配额拦; 指纹不符拦."""
    line = LEGACY_AGENT_LINES[2]
    # 两处构造完全相同的 5 行邻域 → 指纹相同, 用于验证配额
    block = ["ctx-a", "ctx-b", line, "ctx-c", "ctx-d"]
    all_lines = block + ["mid"] + block
    entry = crc.LegacyEntry(
        file="README.md",
        line=line,
        registered_line=3,
        context_sha256=crc.context_digest(all_lines, 3),
        max_occurrences=1,
        reason="test",
    )
    cfg = _engine_cfg_with_legacy((entry,))
    numbered = list(enumerate(all_lines, start=1))
    hits = crc.scan_lines("README.md", numbered, cfg, tmp_path, all_lines=all_lines)
    flags = [h.legacy for h in hits if h.line == line]
    assert flags == [True, False]  # 第 1 份吃配额, 复制份被拦

    # 指纹不符 (搬移到新邻域) → 不吃 legacy
    moved = ["x1", "x2", line, "x3", "x4"]
    hits2 = crc.scan_lines("README.md", list(enumerate(moved, start=1)), cfg, tmp_path, all_lines=moved)
    assert [h.legacy for h in hits2] == [False]


def test_legacy_moved_out_of_anchor_loses_grandfather(tmp_path: Path) -> None:
    """T7b 全链: 旧声明搬到文件头 (锚漂移 67 行 + 上下文指纹不符) → enforce fail."""
    _write_readme(tmp_path, LEGACY_AGENT_LINES[2] + "\n")
    hits = _hits(tmp_path)
    assert len(hits) == 1 and hits[0].legacy is False
    assert _enforce(tmp_path) == 1


# ---------------------------------------------------------------- staged-diff 档


def test_staged_diff_scans_only_added_lines(tmp_path: Path) -> None:
    """T8 staged-diff: 只看 staged 新增行; 违禁新增行 fail, 干净新增行 pass."""
    _init_repo(tmp_path, "### 14 Specialized AI Agents\n")

    _write_readme(tmp_path, "### 14 Specialized AI Agents\nThis fork is production-ready.\n")
    _git(tmp_path, "add", "README.md")
    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 1

    _write_readme(tmp_path, "### 14 Specialized AI Agents\n一行诚实的部署说明。\n")
    _git(tmp_path, "add", "README.md")
    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 0


def test_staged_added_lines_never_get_legacy(tmp_path: Path) -> None:
    """T8b: 新增行即使逐字等于 legacy 登记行也被拦 (搬移=新写入)."""
    _init_repo(tmp_path, "start\n")
    _write_readme(tmp_path, "start\n" + LEGACY_AGENT_LINES[2] + "\n")
    _git(tmp_path, "add", "README.md")
    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 1


def test_staged_diff_hostile_content_and_git_config(tmp_path: Path) -> None:
    """T8c: "++" 内容行不被当元数据; noprefix/mnemonic/color/-diff 属性均不可绕过."""
    _init_repo(tmp_path, "start\n")
    _git(tmp_path, "config", "diff.noprefix", "true")
    _git(tmp_path, "config", "diff.mnemonicPrefix", "true")
    _git(tmp_path, "config", "color.ui", "always")
    _write_readme(tmp_path, "start\n++ totally production-ready\n")
    _git(tmp_path, "add", "README.md")
    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 1

    # .gitattributes 把 README 标成 -diff (二进制伪装) → --text 强制解析, 仍拦
    (tmp_path / ".gitattributes").write_text("README.md -diff\n", encoding="utf-8")
    _git(tmp_path, "add", ".gitattributes")
    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 1


def test_staged_diff_unicode_line_separator_not_evaded(tmp_path: Path) -> None:
    """T8e: U+2028 行分隔符不打断 '+' 行归属 (字节级只按 \\n 分行, Codex 三轮 H4'')."""
    _init_repo(tmp_path, "start\n")
    _write_readme(tmp_path, "start\nprefix\u2028our recall@5 reached 0.9\n")
    _git(tmp_path, "add", "README.md")
    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 1


def test_staged_deletion_of_scan_target_refused(tmp_path: Path) -> None:
    """T8f: git rm --cached README (worktree 留副本) → 2, 拒绝在删除状态下裁决."""
    _init_repo(tmp_path, "start\n")
    _git(tmp_path, "rm", "--cached", "-q", "README.md")
    assert crc.main(["--staged-diff", "--root", str(tmp_path), "--rules", str(REAL_RULES)]) == 2


def test_staged_diff_root_must_be_toplevel(tmp_path: Path) -> None:
    """T8d: --root 指到仓库子目录 → 2 (防在错误 root 下伪绿)."""
    _init_repo(tmp_path, "start\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "README.md").write_text("x\n", encoding="utf-8")
    assert crc.main(["--staged-diff", "--root", str(sub), "--rules", str(REAL_RULES)]) == 2


# ---------------------------------------------------------------- 真仓基线 / 阴性对照 / 跨文件同步


def test_real_repo_baseline_three_legacy_c9() -> None:
    """T9 真仓基线: 本 worktree README = 3 命中全 C9 全 [legacy], enforce 绿.

    G1-6 证据化重写 README 时本测试必须随 legacy_allowlist 清空一起更新。
    """
    hits = _hits(REPO_ROOT)
    legacy_hits = [h for h in hits if h.legacy]
    assert sorted(h.line_no for h in legacy_hits) == LEGACY_ANCHORS
    assert {h.rule_id for h in legacy_hits} == {"C9-agent-collab"}
    assert [h for h in hits if h.effective] == []  # 不硬钉总数: 未来合法 escaped 声明不受阻
    assert _enforce(REPO_ROOT) == 0


def test_g1_4_banner_is_zero_hit(tmp_path: Path) -> None:
    """T10 阴性对照: G1-4 横幅+5 标注陈述负面事实, 必须 0 误伤."""
    _write_readme(tmp_path, G1_4_BANNER_TEXT)
    assert _hits(tmp_path) == []
    assert _enforce(tmp_path) == 0


def test_hook_and_workflow_paths_sync_with_scan_paths() -> None:
    """T11 跨文件同步契约: lefthook glob 与 workflow paths 必须覆盖 scan_paths 及裁判链文件."""
    lefthook = yaml.safe_load((REPO_ROOT / "lefthook.yml").read_text(encoding="utf-8"))
    glob = lefthook["pre-commit"]["commands"]["readme-claims-lint"]["glob"]
    assert glob == crc.EXPECTED_SCAN_PATHS[0] == "README.md"

    wf = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "readme-claims.yml").read_text(encoding="utf-8"))
    triggers = wf.get("on") or wf.get(True)  # YAML 1.1 会把 on 解析成布尔 True
    # scan_paths 扩面必须重设计 lefthook glob (单字符串) — 本断言强制该重设计可见
    assert len(crc.EXPECTED_SCAN_PATHS) == 1
    expected_paths = {
        "README.md",
        "backend/scripts/check_readme_claims.py",
        "backend/scripts/readme_claims_rules.yaml",
        "backend/tests/unit/test_check_readme_claims.py",
        ".github/workflows/readme-claims.yml",
        "lefthook.yml",
        "docs/evidence/**",
    }
    for event in ("pull_request", "push"):
        assert expected_paths <= set(triggers[event]["paths"])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
