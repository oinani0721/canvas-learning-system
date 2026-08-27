#!/usr/bin/env python3
"""G5-1 — 信息收集四类触发矩阵静态校验器 (CARD-G5-1, 对照 check_skill_routing_block.py 模式)。

触发矩阵是 prompt 路由的**断言表**, 本身没法单测。本校验器守住可静态断言的部分,
让「哪些话该触发哪个 skill、哪些话不该触发」不至于在后续编辑里悄悄腐烂或造假。
v2 (Codex 一轮审查后加固): 快照 sha 钉死 / attribution 引语归属锚 / 行号界 /
paraphrase 语义重叠 / 文档行级双向同步 / 真实源下限 / 类型枚举硬化。

  T0 YAML 可加载 + 逐条 schema 完整 + id/话语唯一 + 类型枚举与行号界合法
  T1 四类正例齐 (各 ≥3 条) + 各类真实源(verbatim+paraphrase) ≥ meta.real_floor
     (构造语料不得静默顶替真实语料配额 — 差距由 real_floor 显式声明并入文档自陈)
  T2 负例 ≥8 条, 每条带 不触发理由 + 正确去向 + headless: true
  T3 skill 宇宙一致: live 必须在 vault 有 SKILL.md 且登记于 EXPECTED_SKILLS;
     planned 必须**不**在 vault; vault 里出现 EXPECTED_SKILLS 之外的 live skill 同样 FAIL
  T4 斜杠前缀约定 grep 实证: 9 份 skill 的 **frontmatter** description 必须
     写明「当用户消息以 /<name> 开头」(只认首个 --- 块, 防正文冒充)
  T5 trigger_today 自洽: true ⇔ (skill live 且话语以 /<skill> 开头);
     false 但话语带斜杠 → 前缀必须不是 live skill
  T6 负例不得以任何 live skill 的斜杠前缀开头
  T7 来源档诚实性 (⛔ 禁止冒充原话):
     - 语料快照 sha256 必须与 meta 登记逐字节一致 (来源不可变锚)
     - verbatim/doc-demo → 必须带 attribution(引语归属), 话语与 attribution 都要
       出现在声明行号 ±2 行窗口; 话语含空白时按原文精确匹配 (防「导 出 思 维 导 图」式注水)
     - paraphrase → 声明行号 ±5 行窗口须与话语共享 ≥1 个 4 字连续片段 (行号不可乱标),
       且话语**不得**逐字出现在语料 (逐字却标改写 = 标注失真)
     - ⛔ 行号必须落在语料文件行数范围内
  T8 文档-断言表**行级双向**同步: 每条 id 在文档恰有一行表格行且含该话语;
     正例行的 是/否 触发标记与 trigger_today 一致; 文档表格里的 id 集合与 YAML
     全等 (单边增删/翻转即红); 文档含「待用户拍板」节

用法:
    python3 backend/scripts/check_skill_trigger_matrix.py            # 默认 = 运行时 vault
    python3 backend/scripts/check_skill_trigger_matrix.py --vault <path>
退出码: 0 全绿 / 1 有违规 / 2 环境不可用
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
from pathlib import Path

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"

REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX_YAML = Path(__file__).resolve().parent.parent / "tests" / "regression" / "skill_trigger_matrix.yaml"

VALID_SOURCE_TYPES = frozenset({"verbatim", "paraphrase", "constructed", "doc-demo"})
VALID_STATUS = frozenset({"live", "planned", "planned-extension"})
VALID_POLARITY = frozenset({"positive", "negative"})
#: 必须挂语料出处的类型
NEED_REF_TYPES = frozenset({"verbatim", "paraphrase", "doc-demo"})
#: 需要引语归属锚的类型 (防「作者叙述」冒充「用户之口」)
NEED_ATTRIBUTION = frozenset({"verbatim", "doc-demo"})
#: 真实源 = 用户本人语言或已发生事件的改写
REAL_TYPES = frozenset({"verbatim", "paraphrase"})
VERBATIM_WINDOW = 2
PARAPHRASE_WINDOW = 5
PARAPHRASE_NGRAM = 4

#: ⛔ real_floor 目标值锁死在 checker 本体 (Codex 二轮 HIGH: YAML 里的 floor 可被
#: 单边自降级——锚在代码里, 改锚 = 可审查的代码变更而非数据漂移)。语料覆盖实况
#: 与理由见矩阵文档 §语料覆盖自陈: C/D 类真实触发语在语料中不存在 (功能未上线),
#: 该口径由用户验收裁决; floor 上调只能随真实语料回收同批进行。
EXPECTED_REAL_FLOOR = {"拆分收集": 3, "单板当日回顾": 2, "阶段回顾": 2, "待处理清理": 0}

#: 引语归属锚的语义分类 (Codex 二轮 HIGH: verbatim 与 doc-demo 曾走同一逻辑,
#: 互换标注检测不到)。verbatim 必须挂**用户之口**的归属标记; doc-demo 必须挂
#: 作者叙述/演示的标记——两集合互斥, 冒充即红。
USER_ATTRIBUTION_MARKERS = frozenset({"User：", "你的真实原话", "留过一句疑问"})
DOC_ATTRIBUTION_MARKERS = frozenset({"你：", "说一句"})

_DOC_ROW_RE = re.compile(r"^\|\s*([A-Z]\d+)\s*\|")


class Checker:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def add(self, cid: str, ok: bool, detail: str = "") -> None:
        self.results.append((cid, ok, detail))
        mark = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
        print(f"  {mark} {cid}" + (f" — {detail}" if detail and not ok else ""))

    @property
    def failed(self) -> list[tuple[str, bool, str]]:
        return [r for r in self.results if not r[1]]


def load_expected_skills() -> frozenset[str]:
    """从同目录 check_skill_routing_block.py 取 EXPECTED_SKILLS — 单一真相源, 不重抄。"""
    src = Path(__file__).resolve().parent / "check_skill_routing_block.py"
    spec = importlib.util.spec_from_file_location("check_skill_routing_block", src)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 {src}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.EXPECTED_SKILLS


def resolve_vault(cli_vault: str | None) -> Path:
    """与 check_skill_routing_block.py 同款: 默认运行时 vault, 读不到退回本仓副本。"""
    if cli_vault:
        return Path(cli_vault)
    try:
        from app.config import get_settings

        return Path(get_settings().CANVAS_BASE_PATH)
    except Exception:  # noqa: BLE001 — 无后端环境时退回本仓副本, 并明示
        vault = REPO_ROOT / "canvas-vault"
        print(f"{YELLOW}ℹ️ 读不到 CANVAS_BASE_PATH, 退回本仓副本: {vault}{RESET}")
        return vault


def frontmatter_description(skill_dir: Path) -> str:
    """只认首个 --- 块内的 description (正文里冒充的不算)。"""
    lines = (skill_dir / "SKILL.md").read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    fm: list[str] = []
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        fm.append(ln)
    m = re.search(r'^description:\s*"?(.*)$', "\n".join(fm), re.M)
    return m.group(1) if m else ""


def norm(s: str) -> str:
    """空白折叠 — 语料里的换行/缩进不影响逐字判定。"""
    return re.sub(r"\s+", "", s)


def ngrams(s: str, n: int) -> set[str]:
    t = norm(s)
    return {t[i : i + n] for i in range(len(t) - n + 1)} if len(t) >= n else {t}


def main() -> int:
    ap = argparse.ArgumentParser(description="触发矩阵静态校验器 (G5-1 v2)")
    ap.add_argument("--vault", help="vault 根目录 (缺省 = 运行时 CANVAS_BASE_PATH)")
    args = ap.parse_args()

    try:
        import yaml
    except ImportError:
        print(f"{RED}环境不可用: 缺 PyYAML (用 backend/.venv/bin/python3 跑){RESET}")
        return 2

    if not MATRIX_YAML.exists():
        print(f"{RED}环境不可用: 找不到 {MATRIX_YAML}{RESET}")
        return 2

    vault = resolve_vault(args.vault)
    skills_dir = vault / ".claude" / "skills"
    if not skills_dir.is_dir():
        print(f"{RED}环境不可用: 找不到 {skills_dir}{RESET}")
        return 2

    expected_skills = load_expected_skills()
    data = yaml.safe_load(MATRIX_YAML.read_text(encoding="utf-8"))
    print(f"触发矩阵校验 v2 — {MATRIX_YAML.name} · vault={vault}")

    c = Checker()

    meta = data.get("meta") or {}
    entries = data.get("entries") or []
    categories = meta.get("categories") or []
    real_floor = meta.get("real_floor") or {}
    planned_skills = set(meta.get("planned_skills") or [])
    planned_ext = meta.get("planned_extensions") or {}
    corpus_meta = meta.get("corpus") or {}

    # ── T0 schema 硬化 ──
    t0_problems: list[str] = []
    ids = [e.get("id") for e in entries]
    if len(ids) != len(set(ids)):
        t0_problems.append("id 重复")
    utts = [e.get("utterance") for e in entries]
    if len(utts) != len(set(utts)):
        t0_problems.append("utterance 重复 (同话语多条断言 = 回归集合注水)")
    if len(categories) != 4 or len(set(categories)) != 4:
        t0_problems.append(f"meta.categories 必须恰 4 个互异类, 现 {categories}")
    if real_floor != EXPECTED_REAL_FLOOR:
        t0_problems.append(
            f"meta.real_floor 必须与 checker 锁死的 EXPECTED_REAL_FLOOR 全等 "
            f"(现 {real_floor} vs 锚 {EXPECTED_REAL_FLOOR}; 单边降级/放松即红, 调锚须改 checker 代码)"
        )
    for k, v in (real_floor or {}).items():
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            t0_problems.append(f"real_floor[{k}]={v!r} 必须是非负整数")
    for e in entries:
        eid = e.get("id", "?")
        for field in ("polarity", "utterance", "expected_skill", "source"):
            if field not in e:
                t0_problems.append(f"{eid} 缺 {field}")
        if e.get("polarity") not in VALID_POLARITY:
            t0_problems.append(f"{eid} polarity={e.get('polarity')!r} 非法")
        if not isinstance(e.get("utterance"), str) or not e.get("utterance", "").strip():
            t0_problems.append(f"{eid} utterance 空或非字符串")
        if e.get("polarity") == "positive":
            for field in ("category", "skill_status", "trigger_today"):
                if field not in e:
                    t0_problems.append(f"{eid} 正例缺 {field}")
            if e.get("category") not in categories:
                t0_problems.append(f"{eid} category={e.get('category')!r} 不在 meta.categories")
            if e.get("skill_status") not in VALID_STATUS:
                t0_problems.append(f"{eid} skill_status={e.get('skill_status')!r} 非法")
            if not isinstance(e.get("trigger_today"), bool):
                t0_problems.append(f"{eid} trigger_today 必须是布尔 (现 {e.get('trigger_today')!r})")
        else:
            if not isinstance(e.get("headless"), bool):
                t0_problems.append(f"{eid} headless 必须是布尔")
        src = e.get("source") or {}
        if src.get("type") not in VALID_SOURCE_TYPES:
            t0_problems.append(f"{eid} source.type={src.get('type')!r} 非法")
        if "line" in src and (not isinstance(src["line"], int) or src["line"] < 1):
            t0_problems.append(f"{eid} source.line 必须是正整数 (现 {src['line']!r})")
    c.add("T0[schema]", not t0_problems, "; ".join(t0_problems))
    if t0_problems:
        print(f"\n{RED}FAIL — schema 不完整, 先修 T0{RESET}")
        return 1

    positives = [e for e in entries if e["polarity"] == "positive"]
    negatives = [e for e in entries if e["polarity"] == "negative"]

    # ── T1 四类正例齐 + 真实源下限 ──
    by_cat: dict[str, int] = {}
    real_by_cat: dict[str, int] = {}
    for e in positives:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1
        if e["source"]["type"] in REAL_TYPES:
            real_by_cat[e["category"]] = real_by_cat.get(e["category"], 0) + 1
    t1_problems = []
    for cat in categories:
        if by_cat.get(cat, 0) < 3:
            t1_problems.append(f"{cat} 正例 {by_cat.get(cat, 0)} < 3")
        if real_by_cat.get(cat, 0) < int(real_floor.get(cat, 0)):
            t1_problems.append(
                f"{cat} 真实源 {real_by_cat.get(cat, 0)} < real_floor {real_floor.get(cat)} (构造不得顶替真实配额)"
            )
    c.add("T1[四类正例+真实源下限]", not t1_problems, f"{t1_problems} (实况 {by_cat}, 真实 {real_by_cat})")

    # ── T2 负例 ≥8 ──
    t2_problems = []
    if len(negatives) < 8:
        t2_problems.append(f"负例 {len(negatives)} 条 < 8")
    for e in negatives:
        if e["expected_skill"] != "none":
            t2_problems.append(f"{e['id']} 负例 expected_skill 必须 none")
        if not e.get("reject_reason"):
            t2_problems.append(f"{e['id']} 缺 reject_reason")
        if not e.get("correct_destination"):
            t2_problems.append(f"{e['id']} 缺 correct_destination")
        if e.get("headless") is not True:
            t2_problems.append(f"{e['id']} 负例必须 headless: true (全部进回归)")
    c.add("T2[负例契约]", not t2_problems, "; ".join(t2_problems))

    # ── T3 skill 宇宙一致 (含拒收 vault 中的额外 live skill) ──
    t3_problems = []
    vault_live = {p.parent.name for p in skills_dir.glob("*/SKILL.md")}
    extra_live = vault_live - expected_skills
    if extra_live:
        t3_problems.append(f"vault 出现 EXPECTED_SKILLS 之外的 live skill: {sorted(extra_live)} (须同批登记)")
    for e in positives:
        eid, skill, status = e["id"], e["expected_skill"], e["skill_status"]
        if status == "live":
            if skill not in expected_skills:
                t3_problems.append(f"{eid} live skill {skill!r} 不在 EXPECTED_SKILLS")
            if skill not in vault_live:
                t3_problems.append(f"{eid} live skill {skill!r} 在 vault 无 SKILL.md")
        elif status == "planned":
            if skill not in planned_skills:
                t3_problems.append(f"{eid} planned skill {skill!r} 未登记 meta.planned_skills")
            if skill in vault_live:
                t3_problems.append(f"{eid} {skill!r} 已上线但矩阵仍标 planned (断言表过期)")
        elif status == "planned-extension":
            if skill not in planned_ext:
                t3_problems.append(f"{eid} {skill!r} 未登记 meta.planned_extensions")
            if skill not in vault_live:
                t3_problems.append(f"{eid} planned-extension 基座 {skill!r} 不在 vault (基座必须已上线)")
    c.add("T3[skill 宇宙]", not t3_problems, "; ".join(t3_problems))

    # ── T4 斜杠前缀约定 grep 实证 (9 份全查, 只认 frontmatter) ──
    t4_problems = []
    for name in sorted(expected_skills):
        d = skills_dir / name
        if not (d / "SKILL.md").exists():
            t4_problems.append(f"{name} 无 SKILL.md")
            continue
        if f"当用户消息以 /{name} 开头" not in frontmatter_description(d):
            t4_problems.append(f"{name} frontmatter description 未声明「当用户消息以 /{name} 开头」")
    c.add("T4[斜杠约定]", not t4_problems, "; ".join(t4_problems))

    # ── T5 trigger_today 自洽 ──
    t5_problems = []
    for e in positives:
        eid, skill, utt = e["id"], e["expected_skill"], e["utterance"]
        slash_form = utt == f"/{skill}" or utt.startswith(f"/{skill} ")
        if e["trigger_today"] is True:
            if e["skill_status"] != "live":
                t5_problems.append(f"{eid} trigger_today=true 但 skill 非 live")
            if not slash_form:
                t5_problems.append(f"{eid} trigger_today=true 但话语不以 /{skill} 开头")
        else:
            if e["skill_status"] == "live" and slash_form:
                t5_problems.append(f"{eid} live skill 斜杠形话语却标 trigger_today=false")
            if utt.startswith("/"):
                head = utt.split()[0].lstrip("/")
                if head in vault_live:
                    t5_problems.append(f"{eid} 斜杠前缀 {head!r} 是 live skill 却标不触发")
    c.add("T5[trigger_today 自洽]", not t5_problems, "; ".join(t5_problems))

    # ── T6 负例不得踩 live 斜杠前缀 ──
    t6_problems = []
    for e in negatives:
        utt = e["utterance"]
        if utt.startswith("/"):
            head = utt.split()[0].lstrip("/")
            if head in vault_live:
                t6_problems.append(f"{e['id']} 负例以 live skill /{head} 开头 (按约定必触发, 自相矛盾)")
    c.add("T6[负例前缀]", not t6_problems, "; ".join(t6_problems))

    # ── T7 来源档诚实性 ──
    t7_problems = []
    corpus_lines: dict[str, list[str]] = {}
    for key, info in corpus_meta.items():
        path = REPO_ROOT / (info.get("path") or "")
        if not path.exists():
            t7_problems.append(f"语料快照缺失: {key} → {path}")
            continue
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != info.get("sha256"):
            t7_problems.append(f"语料快照 {key} sha256 漂移: 登记 {info.get('sha256', '')[:12]}… 实际 {actual[:12]}…")
            continue
        corpus_lines[key] = raw.decode("utf-8").splitlines()
    for e in entries:
        eid, src, utt = e["id"], e["source"], e["utterance"]
        stype, ckey, line = src.get("type"), src.get("corpus"), src.get("line")
        if stype in NEED_REF_TYPES and (not ckey or not line):
            t7_problems.append(f"{eid} {stype} 必须标 corpus+line")
            continue
        if stype in NEED_ATTRIBUTION:
            attr = src.get("attribution")
            if not attr:
                t7_problems.append(f"{eid} {stype} 必须带 attribution 引语归属锚")
                continue
            # 语义分类互斥: verbatim=用户之口标记, doc-demo=作者叙述标记 (冒充即红)
            if stype == "verbatim" and attr not in USER_ATTRIBUTION_MARKERS:
                t7_problems.append(
                    f"{eid} verbatim 的归属锚 {attr!r} 不在用户之口标记集 {sorted(USER_ATTRIBUTION_MARKERS)} (作者叙述冒充用户逐字?)"
                )
            if stype == "doc-demo" and attr not in DOC_ATTRIBUTION_MARKERS:
                t7_problems.append(
                    f"{eid} doc-demo 的归属锚 {attr!r} 不在作者叙述标记集 {sorted(DOC_ATTRIBUTION_MARKERS)} (正向要求, Codex 三轮 H1)"
                )
        if ckey and ckey not in corpus_lines:
            if ckey not in corpus_meta:
                t7_problems.append(f"{eid} corpus={ckey!r} 未在 meta.corpus 登记")
            continue
        if stype not in NEED_REF_TYPES:
            continue
        lines = corpus_lines[ckey]
        if line > len(lines):
            t7_problems.append(f"{eid} source.line={line} 超出语料行数 {len(lines)}")
            continue
        if stype in ("verbatim", "doc-demo"):
            lo, hi = max(0, line - 1 - VERBATIM_WINDOW), min(len(lines), line + VERBATIM_WINDOW)
            window_raw = "\n".join(lines[lo:hi])
            window_norm = norm(window_raw)
            if re.search(r"\s", utt):
                # 话语自带空白 → 原文精确匹配, 防注水
                if utt not in window_raw:
                    t7_problems.append(f"{eid} 含空白话语未按原文精确出现在 {ckey}:{line}±{VERBATIM_WINDOW}")
            elif norm(utt) not in window_norm:
                t7_problems.append(f"{eid} 逐字话语未出现在 {ckey}:{line}±{VERBATIM_WINDOW} 行窗口 (冒充原话?)")
            if norm(src.get("attribution", "")) not in window_norm:
                t7_problems.append(f"{eid} attribution {src.get('attribution')!r} 未出现在同窗口 (归属锚失效)")
        elif stype == "paraphrase":
            lo, hi = max(0, line - 1 - PARAPHRASE_WINDOW), min(len(lines), line + PARAPHRASE_WINDOW)
            window_norm = norm("\n".join(lines[lo:hi]))
            if not any(g in window_norm for g in ngrams(utt, PARAPHRASE_NGRAM)):
                t7_problems.append(
                    f"{eid} paraphrase 与 {ckey}:{line}±{PARAPHRASE_WINDOW} 无 {PARAPHRASE_NGRAM} 字重叠 (行号乱标?)"
                )
            whole = norm("\n".join(lines))
            if norm(utt) in whole:
                t7_problems.append(f"{eid} 话语逐字存在于语料却标 paraphrase (应改标 verbatim)")
    c.add("T7[来源档诚实]", not t7_problems, "; ".join(t7_problems))

    # ── T8 文档-断言表行级双向同步 ──
    t8_problems = []
    doc_path = REPO_ROOT / meta.get("matrix_doc", "")
    if not doc_path.exists():
        t8_problems.append(f"矩阵文档缺失: {doc_path}")
    else:
        doc_lines = doc_path.read_text(encoding="utf-8").splitlines()
        if not any("待用户拍板" in ln for ln in doc_lines):
            t8_problems.append("矩阵文档缺「待用户拍板」节")
        rows: dict[str, list[str]] = {}
        for ln in doc_lines:
            m = _DOC_ROW_RE.match(ln.strip())
            if m:
                rows.setdefault(m.group(1), []).append(ln)
        yaml_ids = {e["id"] for e in entries}
        doc_only = set(rows) - yaml_ids
        if doc_only:
            t8_problems.append(f"文档表格行存在 YAML 没有的 id: {sorted(doc_only)} (单边删除?)")
        for e in entries:
            eid = e["id"]
            if eid not in rows:
                t8_problems.append(f"{eid} 在文档无表格行")
                continue
            if len(rows[eid]) != 1:
                t8_problems.append(f"{eid} 在文档出现 {len(rows[eid])} 行 (须恰 1 行)")
                continue
            row = rows[eid][0]
            if norm(e["utterance"]) not in norm(row):
                t8_problems.append(f"{eid} 话语未出现在其文档表格行 (两处必须同改)")
            if e["polarity"] == "positive":
                doc_yes = "**是**" in row
                if doc_yes != bool(e["trigger_today"]):
                    t8_problems.append(f"{eid} 文档触发列({'是' if doc_yes else '否'})与 YAML trigger_today 不一致")
            # 来源档类型标记同步 (Codex 三轮 H2: 类型单边漂移曾检测不到)
            marker = {
                "verbatim": "**逐字**",
                "paraphrase": "**语境改写**",
                "constructed": "**构造**",
                "doc-demo": "**文档演示**",
            }[e["source"]["type"]]
            if marker not in row:
                t8_problems.append(f"{eid} 文档行缺来源档标记 {marker} (与 YAML source.type 漂移)")
    c.add("T8[文档同步]", not t8_problems, "; ".join(t8_problems))

    total, failed = len(c.results), len(c.failed)
    print(
        f"\n合计: {total - failed}/{total} 通过 · 正例 {len(positives)} (四类 {by_cat}, 真实 {real_by_cat}) "
        f"· 负例 {len(negatives)}"
    )
    if failed:
        print(f"{RED}FAIL — {failed} 项违规{RESET}")
        for cid, _, detail in c.failed:
            print(f"  {RED}{cid}{RESET}: {detail}")
        return 1
    print(f"{GREEN}PASS — 触发矩阵断言表与文档/skill 宇宙/语料来源全部自洽{RESET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
