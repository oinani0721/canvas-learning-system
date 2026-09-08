# CARD-G2-6 (BATCH-2026-09-05-第十二批) + CARD-RV-G2-6 (BATCH-2026-09-07-第十三批)
#   — vault 部署清单 + 只读校验器的裁判
#
# 被测物: scripts/vault-install-manifest.json + scripts/verify_vault_install.py
#         + scripts/install-vault.sh 的自检块 (:112-125)
# 真相源: install-vault.sh MANIFEST 区 (:61-69) 与其隐含部署语义 (:74-109);
#         插件命令 id 的真相源是 frontend/obsidian-plugin/src/main.ts (只读, 不构建)。
#
# ⚠️ 头注维护约定 (UAT-CARD-G2-6 「未证明」#19 的债, 由 CARD-RV-G2-6 还上):
#   这份清单写于 round-1, 三轮整改期间钉死点从 5 条扩到下面这些却一直没同步 ——
#   头注与实现不一致会误导后来者。**增删钉死点必须同批改这里。**
#
# 钉死点 (G2-6 三轮累积):
#   1. **集合等价**: manifest 里 action ∈ {copy, skeleton} 的 path 集合, 与 install-vault.sh
#      :63-67 五个 shell 数组按各自前缀展开后的并集**逐项相等** (27 项)。这是本门的主判据。
#      验伪锚: 先断言正则确实解析出 5 个数组 / 27 个元素, 否则「空集 == 空集」会假绿;
#      另有全文扫描门, 防 :63-67 之外新增第 6 个数组对主判据不可见。
#   2. **schema**: version int / source 非空 / items 非空列表 / 必填键 / action 四枚举 /
#      kind 四枚举 / path 相对·无 `..`·无 NUL·可编码 UTF-8·规范化后无重复;
#      extra_scan 的 dir 与 path **共用同一个校验函数** (同一条约束不得只在一半字段生效);
#      match 单层名字不得含 `/`。任何 schema 问题 → 用法错档, 不与内容差异混淆。
#   3. **六类 diff 各自独立承重**: missing / extra / content-drift / intentionally-excluded /
#      unreadable / hotkey-orphan, 每类一个反例, 一次只打一类, 断言「该类精确命中该 path」
#      且「其余各类为空」—— 只断言 rc != 0 是粗判据, 会被任意一类差异喂饱。
#   4. **报告落点的三种别名**: 大小写目录别名 (macOS 默认大小写不敏感, 按 (st_dev,st_ino)
#      身份判) / 两层软链目标 (禁写根递归展开) / 硬链接; 外加「安全性扫描没跑完就拒绝落盘」。
#   5. **写入资源管理**: O_EXCL 失败时只清理本次真正创建的临时文件 (删别人的文件 = 数据丢失);
#      os.write 短写必须循环写满才换目录项 (否则发布截断报告)。
#   6. **unreadable 计入阻断**: 顶层普通文件与目录内叶子两条路径都要登记 ——
#      「我看不见」不等于「一致」, 两侧都读不动而报 0 是假绿。
#   7. **零写**: 对 target 跑一次校验器, 前后全树 (文件 sha + 目录条目) 清单逐字相同。
#      校验器有任何写目标 vault 的路径 = 阻断级缺陷。AST 门另钉「源码里没有写调用」。
#   8. **glob 口径一致**: `[` 在 _has_glob 与 _pattern_to_regex 两处都是字面量;
#      清单里真放一条含方括号的 exclude 声明, 端到端验分类与负例。
#
# 钉死点 (CARD-RV-G2-6 新增):
#   9. **退出码四档**: 0 ok / 1 只缺 (missing) / 2 mismatch (extra 未放行·content-drift·
#      unreadable·hotkey-orphan, 与 missing 并存时也取 2) / 3 用法错。数字写死 ——
#      调用方 (deploy-vault.sh, CARD-G2-7b) 靠它区分「缺东西」与「多东西」。
#      `test_missing_is_detected_alone` 仍期望 **1**, 它是「missing 语义没被 mismatch
#      吞掉」的唯一守门人; 禁止把任何一条 rc 断言弱化成 `!= 0`。
#  10. **extra_allow**: manifest 顶层白名单, 与 item.path 同口径 (相对 / 无 `..` / 可编码 /
#      无重复 / 支持 *? glob); 与 declared 或 exclude 模式**重叠即拒绝加载**;
#      命中的项进 allowed-extra 段, 只报告不计退出码。仓内清单初值必须是 []。
#  11. **hotkeys ↔ 命令 id 交叉核 (两层)**:
#      校验器层 — vault 的 .obsidian/hotkeys.json 里 `canvas-learning-system:` 前缀的键,
#        必须在同一 vault 的 .obsidian/plugins/canvas-learning-system/main.js 里找到
#        对应命令 id 字面量; 找不到 = hotkey-orphan (计 mismatch); main.js 缺 →
#        报告明写 not evaluated, **不计退出码也不静默**; hotkeys.json 非法 JSON → unreadable。
#      测试层 — main.ts 恰 10 个命令 id (数字写死, 防正则退化成空集), 且树内
#        canvas-vault/.obsidian/hotkeys.json 的 CLS 前缀 id ⊂ 该集合 (另断言非空,
#        否则 `∅ ⊆ 任何集合` 恒真)。
#  12. **install-vault.sh:117 的 skills 判据**: 数「含 SKILL.md 的一级子目录」, 不数目录条目
#      (树内 11 个目录只有 9 个含 SKILL.md, 旧 `ls | wc -l` 对半成品 skill 失明)。
#      判据只看 check 的 eval 体, 不看标签 —— 标签里的 "skills " 自带子串 "ls "。
#
# 本门证明什么: manifest 与脚本数组等价; 校验器的六种分类各自可被单独触发且退出码分档正确;
#   校验器不写目标树; 报告落点对三类别名与扫描失败都拒绝; extra_allow 的放行与重叠拒绝;
#   hotkeys 绑定与命令 id 的一致性 (在 main.js 存在时)。
# 本门不证明什么: 不证明 install-vault.sh 真跑起来会产出符合 manifest 的 vault (禁真跑脚本,
#   属 CARD-G2-7 五动作 CLI 的范围); 不证明 live vault 的 extra 项应否进 extra_allow (归 U3-B);
#   不证明构建产物 main.js 与源码 main.ts 的命令集一致 (只读源, 不 build);
#   不证明字面量法对「非命令 id 的同形字符串」没有假放行;
#   合成 fixture 的「有扩展名 = 文件」启发式只服务于本文件的目录/文件搭建, 不是生产语义
#   (该启发式的直接后果: 合成 vault 里没有 main.js, hotkeys 一路走 not evaluated 分支)。
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
VERIFIER = SCRIPTS_DIR / "verify_vault_install.py"
MANIFEST = SCRIPTS_DIR / "vault-install-manifest.json"
INSTALL_SH = SCRIPTS_DIR / "install-vault.sh"

# install-vault.sh 五数组各自的 vault 内前缀 (数组元素是裸名, 部署时拼在这些前缀下)
ARRAY_PREFIX = {
    "SKELETON_DIRS": "",
    "CLAUDE_ITEMS": ".claude/",
    "OBSIDIAN_FILES": ".obsidian/",
    "OBSIDIAN_PLUGINS": ".obsidian/plugins/",
    "ROOT_FILES": "",
}
MANIFEST_BLOCK = (63, 67)  # 卡文锚定的 MANIFEST 数组区间 (1-indexed, 含两端)


def _load_verifier():
    """加载仓根 scripts/verify_vault_install.py。

    照 backend/tests/contract/test_openapi_snapshot_drift.py:39-51 的形态, 另加
    sys.modules 注册 —— 协议 §3: Python 3.14 的 @dataclass 自省要取
    sys.modules[cls.__module__].__dict__, 不先注册则 exec_module 期 KeyError。
    """
    name = "_verify_vault_install"
    spec = importlib.util.spec_from_file_location(name, VERIFIER)
    if spec is None or spec.loader is None:  # pragma: no cover — 路径错时立即失败
        raise RuntimeError(f"无法加载 {VERIFIER}")
    module = importlib.util.module_from_spec(spec)
    previous_dwb = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # 不往仓根 scripts/ 落 __pycache__
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:  # pragma: no cover — 加载失败不留半成品模块
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous_dwb
    return module


vv = _load_verifier()


# ── 集合等价 (钉死点 1) ────────────────────────────────────────────────


def _parse_install_arrays() -> dict[str, list[str]]:
    """正则解析 install-vault.sh:63-67 的五个 shell 数组。"""
    lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    lo, hi = MANIFEST_BLOCK
    block = lines[lo - 1 : hi]
    pattern = re.compile(r"^(?P<name>[A-Z_]+)=\((?P<body>[^)]*)\)\s*$")
    parsed: dict[str, list[str]] = {}
    for line in block:
        m = pattern.match(line)
        if m:
            parsed[m.group("name")] = m.group("body").split()
    return parsed


def test_install_arrays_parse_as_expected():
    """验伪锚: 正则真的解析到 5 个数组 / 27 个元素。

    没有这一条, 解析失败时 test_manifest_matches_install_arrays 会退化成
    「空集 == 空集」的假绿。
    """
    arrays = _parse_install_arrays()
    assert set(arrays) == set(ARRAY_PREFIX), f"解析到的数组名与预期不符: {sorted(arrays)}"
    counts = {k: len(v) for k, v in arrays.items()}
    assert counts == {
        "SKELETON_DIRS": 6,
        "CLAUDE_ITEMS": 8,
        "OBSIDIAN_FILES": 6,
        "OBSIDIAN_PLUGINS": 5,
        "ROOT_FILES": 2,
    }, f"数组元素数与卡文勘探不符: {counts}"
    assert sum(counts.values()) == 27


def test_manifest_matches_install_arrays():
    """主判据: manifest 的 copy+skeleton 集合 == 五数组展开并集, 两侧差集均为空。"""
    arrays = _parse_install_arrays()
    from_script = {f"{ARRAY_PREFIX[name]}{item}" for name, items in arrays.items() for item in items}
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    from_manifest = {i["path"] for i in data["items"] if i["action"] in ("copy", "skeleton")}
    assert from_manifest - from_script == set(), "manifest 多出脚本没有的项"
    assert from_script - from_manifest == set(), "脚本数组有项未进 manifest"
    assert len(from_manifest) == 27


def test_manifest_covers_implicit_and_generated_semantics():
    """:68/:69 的排除语义、:84/:86 两个隐含 exclude、:103-109 的 generate 都要有 item。"""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    origins = {i["origin"] for i in data["items"]}
    for required in (
        "install-vault.sh:68",
        "install-vault.sh:69",
        "install-vault.sh:84",
        "install-vault.sh:86",
        "install-vault.sh:103-109",
    ):
        assert required in origins, f"缺少源自 {required} 的 item"
    by_origin = {}
    for i in data["items"]:
        by_origin.setdefault(i["origin"], []).append(i)
    # :84 的 find 只在 "$TARGET/.claude" 下剪 __pycache__ — 模式必须带该前缀,
    # 写成全树 `**/__pycache__` 就比源语义宽了。
    assert [i["path"] for i in by_origin["install-vault.sh:84"]] == [".claude/**/__pycache__"]
    assert [i["path"] for i in by_origin["install-vault.sh:86"]] == [".claude/hooks/pending_archives*.jsonl"]
    generated = [i for i in data["items"] if i["action"] == "generate"]
    assert [i["path"] for i in generated] == [".canvas-config.yaml"]


def test_manifest_has_no_absolute_paths_and_no_secrets_inline():
    """(c) 0 绝对路径; 两个密钥件必须标 secret-or-local。"""
    raw = MANIFEST.read_text(encoding="utf-8")
    assert "/Users/" not in raw
    data = json.loads(raw)
    roles = {i["path"]: i["role"] for i in data["items"]}
    assert roles[".obsidian/cls-internal-key.txt"] == "secret-or-local"
    assert roles[".claude/settings.local.json"] == "secret-or-local"


def test_manifest_is_template_free():
    """(f)「活 vault 即模板」自证: manifest 不含任何内容/哈希基线字段。"""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    banned = {"sha256", "sha", "checksum", "content", "bytes", "size", "hash"}
    for item in data["items"]:
        assert not (set(item) & banned), f"{item['path']} 携带了内容基线字段"
    assert data["source"] == "live-vault"


# ── schema (钉死点 2) ─────────────────────────────────────────────────


def test_repo_manifest_passes_schema():
    vv.load_manifest(MANIFEST)


@pytest.mark.parametrize(
    "mutate,fragment",
    [
        (lambda d: d.__setitem__("version", "1"), "version"),
        (lambda d: d.__setitem__("items", {}), "items"),
        (lambda d: d["items"][0].pop("role"), "role"),
        (lambda d: d["items"][0].__setitem__("action", "symlink"), "action"),
        (lambda d: d["items"][0].__setitem__("path", "/Users/x"), "绝对"),
        (lambda d: d["items"][0].__setitem__("path", "../escape"), ".."),
        (lambda d: d["items"].append(dict(d["items"][0])), "重复"),
    ],
)
def test_schema_rejects_malformed_manifest(tmp_path, mutate, fragment):
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mutate(data)
    bad = tmp_path / "bad-manifest.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(bad)
    assert fragment in str(exc.value)


# ── 合成 vault fixture ────────────────────────────────────────────────


def _looks_like_file(path: str) -> bool:
    """合成 fixture 用的搭建启发式: 末段带扩展名 → 造文件, 否则造目录。

    只服务于本文件的 tmp 树搭建, 不是生产语义 (生产按磁盘实际类型判定)。
    """
    return "." in Path(path).name


def _build_vault(root: Path, manifest: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for item in manifest["items"]:
        if item["action"] == "skeleton":
            (root / item["path"]).mkdir(parents=True, exist_ok=True)
        elif item["action"] == "copy":
            target = root / item["path"]
            if _looks_like_file(item["path"]):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f"content of {item['path']}\n", encoding="utf-8")
            else:
                target.mkdir(parents=True, exist_ok=True)
                (target / "payload.txt").write_text(f"payload of {item['path']}\n", encoding="utf-8")
    (root / ".canvas-config.yaml").write_text('vault_id: "synthetic"\nsubject: "synthetic"\n', encoding="utf-8")


@pytest.fixture
def manifest_data() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture
def vault_pair(tmp_path, manifest_data):
    """一对逐字节相同的 source / target 合成 vault (基线全 match)。"""
    source = tmp_path / "source-vault"
    target = tmp_path / "target-vault"
    _build_vault(source, manifest_data)
    _build_vault(target, manifest_data)
    return source, target


def _run(target: Path, *, source: Path | None = None, report: Path | None = None) -> int:
    argv = ["--vault", str(target), "--manifest", str(MANIFEST)]
    if source is not None:
        argv += ["--source", str(source)]
    if report is not None:
        argv += ["--report", str(report)]
    return vv.main(argv)


def _classify(target: Path, *, source: Path | None = None):
    manifest = vv.load_manifest(MANIFEST)
    return vv.verify(target, manifest, source_dir=source)


def test_clean_pair_is_all_match(vault_pair, tmp_path):
    source, target = vault_pair
    report = tmp_path / "report.txt"
    assert _run(target, source=source, report=report) == 0
    result = _classify(target, source=source)
    assert result.missing == []
    assert result.extra == []
    assert result.content_drift == []
    assert result.intentionally_excluded == []
    assert len(result.match) == 28  # 27 数组项 + .canvas-config.yaml (generate)


# ── 四类 diff 各自独立承重 (钉死点 3) ──────────────────────────────────


def _assert_only(result, bucket: str, expected_paths: list[str]):
    """一次只打一类: 目标桶精确命中, 其余三桶必须为空。"""
    buckets = {
        "missing": result.missing,
        "extra": result.extra,
        "content_drift": result.content_drift,
        "intentionally_excluded": result.intentionally_excluded,
    }
    assert sorted(f.path for f in buckets.pop(bucket)) == sorted(expected_paths)
    for name, findings in buckets.items():
        assert findings == [], f"变异只应触发 {bucket}, 但 {name} 也非空: {findings}"


def test_missing_is_detected_alone(vault_pair):
    source, target = vault_pair
    (target / ".obsidian" / "hotkeys.json").unlink()
    _assert_only(_classify(target, source=source), "missing", [".obsidian/hotkeys.json"])
    assert _run(target, source=source) == 1


def test_extra_is_detected_alone(vault_pair):
    source, target = vault_pair
    (target / ".claude" / "cache").mkdir()
    _assert_only(_classify(target, source=source), "extra", [".claude/cache"])
    assert _run(target, source=source) == 2


def test_content_drift_is_detected_alone(vault_pair):
    source, target = vault_pair
    (target / "Dashboard.md").write_text("drifted\n", encoding="utf-8")
    _assert_only(_classify(target, source=source), "content_drift", ["Dashboard.md"])
    assert _run(target, source=source) == 2


def test_intentionally_excluded_is_detected_alone(vault_pair):
    source, target = vault_pair
    (target / ".obsidian" / "workspace.json").write_text("{}", encoding="utf-8")
    _assert_only(
        _classify(target, source=source),
        "intentionally_excluded",
        [".obsidian/workspace.json"],
    )
    # intentionally-excluded 只报告, 不进退出码
    assert _run(target, source=source) == 0


def test_glob_exclude_matches_nested_pycache(vault_pair):
    """两个隐含 exclude 的实际匹配 (Finding.path = 声明的模式, detail 带命中项)。"""
    source, target = vault_pair
    (target / ".claude" / "scripts" / "__pycache__").mkdir(parents=True)
    (target / ".claude" / "hooks" / "pending_archives_2026.jsonl").write_text("[]", encoding="utf-8")
    result = _classify(target, source=source)
    by_path = {f.path: f for f in result.intentionally_excluded}
    assert sorted(by_path) == [
        ".claude/**/__pycache__",
        ".claude/hooks/pending_archives*.jsonl",
    ]
    assert ".claude/scripts/__pycache__" in by_path[".claude/**/__pycache__"].detail
    assert ".claude/hooks/pending_archives_2026.jsonl" in by_path[".claude/hooks/pending_archives*.jsonl"].detail
    # __pycache__ 落在 .claude 一级之下, 不在 extra 覆盖面 (.claude/* 只看直接子项)
    assert result.extra == []


def test_content_drift_not_evaluated_without_source(vault_pair):
    """(b) content-drift 只在给了 --source 时评估。"""
    _source, target = vault_pair
    (target / "Dashboard.md").write_text("drifted\n", encoding="utf-8")
    result = _classify(target, source=None)
    assert result.content_drift == []
    assert result.drift_evaluated is False
    assert _run(target) == 0


def test_missing_skeleton_dir_is_missing(vault_pair):
    source, target = vault_pair
    (target / "templates").rmdir()
    _assert_only(_classify(target, source=source), "missing", ["templates"])


def test_skeleton_present_as_file_is_missing(vault_pair):
    """骨架项存在但不是目录 —— 由「skeleton 须为目录」那道分支单独承重。

    与上一条不同: 上一条把目录删掉, 两道分支 (不存在 / 不是目录) 都能抓到,
    拆掉任一条另一条都兜得住; 只有这一条能单独把第二道分支打红。
    """
    source, target = vault_pair
    (target / "templates").rmdir()
    (target / "templates").write_text("骨架位置被占成了文件\n", encoding="utf-8")
    result = _classify(target, source=source)
    _assert_only(result, "missing", ["templates"])
    assert "不是目录" in result.missing[0].detail


def test_generate_item_missing_is_reported(vault_pair):
    source, target = vault_pair
    (target / ".canvas-config.yaml").unlink()
    _assert_only(_classify(target, source=source), "missing", [".canvas-config.yaml"])


# ── 退出码 2: 用法/配置错 (钉死点 4) ───────────────────────────────────


def test_absolute_path_in_manifest_exits_2(tmp_path, vault_pair, manifest_data):
    source, target = vault_pair
    manifest_data["items"][0]["path"] = "/Users/x"
    bad = tmp_path / "abs-manifest.json"
    bad.write_text(json.dumps(manifest_data), encoding="utf-8")
    rc = vv.main(["--vault", str(target), "--manifest", str(bad), "--source", str(source)])
    assert rc == 3


def test_missing_vault_dir_exits_2(tmp_path):
    rc = vv.main(["--vault", str(tmp_path / "nope"), "--manifest", str(MANIFEST)])
    assert rc == 3


def test_report_inside_vault_exits_2(vault_pair):
    source, target = vault_pair
    rc = _run(target, source=source, report=target / "report.txt")
    assert rc == 3
    assert not (target / "report.txt").exists()


def test_report_inside_source_exits_2(vault_pair):
    source, target = vault_pair
    rc = _run(target, source=source, report=source / "report.txt")
    assert rc == 3
    assert not (source / "report.txt").exists()


# ── Codex round-1 四条指控的回归门 ────────────────────────────────────
#
# 四条都在本机独立复现成立后才改的代码（证据 evidence-g26/codex-r1-claims-verified-*.txt）。
# 每条配一个能在修复前打红的反例——只写「修好了」不算数。


def test_report_hardlinked_into_vault_is_refused(vault_pair, tmp_path):
    """BLOCKER 回归: 树外报告路径若与树内文件同 inode，必须拒绝（rc=2）且不改那个文件。

    修复前: `is_relative_to` 只看路径不看 inode，检查放行 → `write_text` 原地覆盖，
    树内 Dashboard.md 被报告正文冲掉，且校验器还返回 0。
    """
    source, target = vault_pair
    victim = target / "Dashboard.md"
    before = victim.read_bytes()
    outside = tmp_path / "outside-report.txt"
    os.link(victim, outside)  # 树外路径，与树内文件共享 inode

    assert not outside.is_relative_to(target), "前提: 该路径确实在被查树之外"
    rc = _run(target, source=source, report=outside)
    assert rc == 3
    assert victim.read_bytes() == before, "树内文件被写穿了"


def test_normally_deployed_vault_is_not_reported_as_drift(vault_pair):
    """HIGH 回归: 模板源里有 exclude 件、目标按脚本剪掉了 —— 这是**正确部署**，不是漂移。

    修复前: 目录摘要把 `.claude/scripts/__pycache__` 与 `pending_archives*.jsonl`
    也算进去，于是 `.claude/scripts` 和 `.claude/hooks` 双双被判 content-drift、exit 1。
    """
    source, target = vault_pair
    # 活 vault（模板源）天然带这两类东西 —— live 实测确实有
    (source / ".claude" / "scripts" / "__pycache__").mkdir(parents=True)
    (source / ".claude" / "scripts" / "__pycache__" / "cached.pyc").write_bytes(b"\x00c")
    (source / ".claude" / "hooks" / "pending_archives_2026.jsonl").write_text("[]", encoding="utf-8")
    # target = install-vault.sh 正常部署的结果（:84 剪了 pycache，:86 删了归档队列）
    result = _classify(target, source=source)
    assert result.content_drift == [], "正确部署被误报 drift"
    assert result.missing == []
    assert result.extra == []
    assert result.intentionally_excluded == [], "目标侧本就没有这些件"
    assert _run(target, source=source) == 0


def test_exclude_kind_matches_script_type_conditions(vault_pair):
    """MEDIUM 回归: `:84` 是 `-type d`、`:86` 是 `rm -f` —— 类型不符的同名条目不算 excluded。"""
    source, target = vault_pair
    # __pycache__ 这次是个**普通文件**：脚本的 find -type d 不会删它
    (target / ".claude" / "scripts" / "__pycache__").write_text("not a dir", encoding="utf-8")
    # pending_archives_x.jsonl 这次是个**目录**：rm -f 不会删目录
    (target / ".claude" / "hooks" / "pending_archives_x.jsonl").mkdir(parents=True)
    result = _classify(target, source=source)
    assert result.intentionally_excluded == [], "类型不符却被判 excluded，与脚本的 -type d / rm -f 条件不一致"


@pytest.mark.parametrize("bad_action", [[], {}, 123, None])
def test_non_string_action_still_exits_2(tmp_path, vault_pair, manifest_data, bad_action):
    """MEDIUM 回归: unhashable 的 action 曾抛 TypeError 逃出捕获面，CLI 拿不到 rc=2。"""
    source, target = vault_pair
    manifest_data["items"][0]["action"] = bad_action
    bad = tmp_path / "bad-action.json"
    bad.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError):
        vv.load_manifest(bad)
    assert vv.main(["--vault", str(target), "--manifest", str(bad), "--source", str(source)]) == 3


@pytest.mark.parametrize("bad_kind", ["directory", "DIR", 1, []])
def test_invalid_kind_is_rejected(tmp_path, manifest_data, bad_kind):
    manifest_data["items"][0]["kind"] = bad_kind
    bad = tmp_path / "bad-kind.json"
    bad.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(bad)
    assert "kind" in str(exc.value)


def test_manifest_declares_kind_for_the_two_typed_excludes():
    """两个隐含 exclude 必须带类型条件，且类型要对得上脚本命令的实际可删集合。"""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_path = {i["path"]: i for i in data["items"]}
    # :84 是 find -type d —— 只剪目录
    assert by_path[".claude/**/__pycache__"]["kind"] == "dir"
    # :86 的强制删除清掉一切**非目录**条目（软链、悬空软链、FIFO 都删，真目录不删）。
    # 写成 "file" 是错的：is_file() 对后三者为 False。
    assert by_path[".claude/hooks/pending_archives*.jsonl"]["kind"] == "nondir"


def test_manifest_does_not_over_constrain_path_only_excludes():
    """:68/:69 那些按路径声明「不复制」的项**没有**类型条件，不得擅自加 kind。

    早先给 learning_events.jsonl 与 workspace.json 加了 kind=file，反而收窄了语义：
    同名的目录会因类型不符而落到 extra 去。
    """
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_path = {i["path"]: i for i in data["items"]}
    for p in ("learning_events.jsonl", ".obsidian/workspace.json", "outputs/**", "原白板/**"):
        assert "kind" not in by_path[p], f"{p} 不该有类型条件"


def test_verifier_exposes_only_readonly_switches():
    """(b) 只读: CLI 参数面是**白名单**, 多一个开关就红。

    不用「文本里不得出现 --fix」那种判据 —— 它既假红 (docstring 里提一嘴就中)
    又假绿 (换个名字叫 --repair-now 就漏)。白名单挡得住没预想到的名字。
    """
    parser = vv._build_parser()
    options = {s for action in parser._actions for s in action.option_strings}
    assert options == {"-h", "--help", "--vault", "--source", "--manifest", "--report"}
    # 白名单只管带前缀的开关；位置参数和子命令的 option_strings 是空的，会从名单里漏过去
    positional = [a for a in parser._actions if not a.option_strings]
    assert positional == [], f"不得有位置参数或子命令: {positional}"


def _is_stdio_write(node) -> bool:
    """精确豁免 `sys.stdout.write` / `sys.stderr.write` 两个字面形态。

    只豁免这两个：`f.write(...)` 那种对文件对象的写照样要被抓住，
    所以判据不能简单地放过所有名字叫 write 的调用。
    """
    import ast

    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr != "write":
        return False
    owner = func.value
    return (
        isinstance(owner, ast.Attribute)
        and owner.attr in ("stdout", "stderr")
        and isinstance(owner.value, ast.Name)
        and owner.value.id == "sys"
    )


def test_verifier_write_calls_are_confined_to_write_report():
    """(b) 只读: 所有写调用必须落在 `_write_report()` 这一个函数内。

    比早先那条「只允许一次 write_text」强两处：
      ① 调用名面扩大 —— 旧版漏掉 `Path.open("w")`、文件对象 `.write`、`os.*` 全族、
         以及 from-import 形式的 rmtree；
      ② 判据从「计数 + 落在 main 的行号区间」改成「按函数边界圈定」——
         写操作只允许出现在那个专门负责落盘的函数里，别处一个都不许有。
    看的是调用节点，不是文本，所以注释/docstring 里怎么写都不影响判定。
    """
    import ast

    source = VERIFIER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    write_names = {
        "write_text",
        "write_bytes",
        "mkdir",
        "unlink",
        "rmdir",
        "touch",
        "rename",
        "replace",
        "chmod",
        "symlink_to",
        "rmtree",
        "copy",
        "copytree",
        "copy2",
        "move",
        "write",
        "writelines",
        "truncate",
        "makedirs",
        "remove",
        "link",
        "symlink",
        "mknod",
        "mkfifo",
        "chown",
        "utime",
        "open",
    }
    funcs = {
        n.name: (n.lineno, n.end_lineno)
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.end_lineno is not None
    }
    assert "_write_report" in funcs, "落盘应当收敛到 _write_report()"
    lo, hi = funcs["_write_report"]

    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = None
        if isinstance(node.func, ast.Attribute):
            name = node.func.attr
        elif isinstance(node.func, ast.Name):
            name = node.func.id
        if name not in write_names:
            continue
        if _is_stdio_write(node):
            # 缺省报告去处。说明一句边界: 这里只按**语法形态**豁免
            # `sys.stdout` / `sys.stderr` 这两个名字，并**不验证运行时那个文件描述符
            # 指向哪里**（被重定向到文件时它当然会落盘）。这道门证明的是
            # 「源码里没有别处的写调用」，不是「进程一定不写文件」。
            continue
        if not (lo <= node.lineno <= hi):
            offenders.append((name, node.lineno))
    assert offenders == [], f"写调用出现在 _write_report 之外: {offenders}"

    # 危险的整树删除工具一律不许进来，无论 import 形式
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(a.name for a in node.names)
    assert "shutil" not in imported and "rmtree" not in imported


# ── 零写门 (钉死点 5) ─────────────────────────────────────────────────


def _tree_digest(root: Path) -> str:
    entries = []
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        rel = path.relative_to(root).as_posix()
        if path.is_dir():
            entries.append(f"DIR   {rel}")
        else:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append(f"{digest}  {rel}")
    return "\n".join(entries)


def test_verifier_writes_nothing_into_vault_or_source(vault_pair, tmp_path):
    source, target = vault_pair
    # 先制造全部四类差异, 让校验器走遍所有分类分支
    (target / ".obsidian" / "hotkeys.json").unlink()
    (target / ".claude" / "cache").mkdir()
    (target / "Dashboard.md").write_text("drifted\n", encoding="utf-8")
    (target / ".obsidian" / "workspace.json").write_text("{}", encoding="utf-8")

    before_target, before_source = _tree_digest(target), _tree_digest(source)
    report = tmp_path / "zero-write-report.txt"
    assert _run(target, source=source, report=report) == 2
    assert _tree_digest(target) == before_target, "校验器写了目标 vault"
    assert _tree_digest(source) == before_source, "校验器写了模板源"
    assert report.exists()


# ── Codex round-2 + 对抗审查的回归门 ──────────────────────────────────
#
# 这一组同样是「先在本机复现指控成立，再改代码，再补门」的产物。
# 证据：evidence-g26/codex-r2-claims-verified-*.txt


def test_report_via_dev_fd_alias_is_refused(vault_pair, tmp_path):
    """BLOCKER 回归: `--report /dev/fd/N` 曾能写穿被审文件。

    `/dev/fd/N` 的 resolve() 返回它自己（路径判据以为在树外），stat() 又返回被打开
    文件的属性、st_nlink=1（硬链接判据也不触发）——两道早退判据同时失明。
    真正承重的是落盘写法本身：临时文件 + os.replace，绝不原地覆盖已有 inode。
    """
    source, target = vault_pair
    victim = target / "Dashboard.md"
    before = victim.read_bytes()
    fd = os.open(str(victim), os.O_WRONLY)
    try:
        rc = _run(target, source=source, report=Path(f"/dev/fd/{fd}"))
    finally:
        os.close(fd)
    assert rc == 3
    assert victim.read_bytes() == before, "被审文件被写穿了"


def test_report_behind_vault_symlink_is_refused(tmp_path, manifest_data):
    """HIGH 回归: vault 里一条指向树外的目录软链，会让「树外」路径其实就是树内文件。

    只比路径前缀挡不住这个：报告落点在 vault 之外（字符串上成立），但通过 vault 里
    那条软链看得见。落点判据必须把树内软链的解析目标也算作禁写区。
    """
    outside = tmp_path / "outside-claude"
    (outside / "skills").mkdir(parents=True)
    real = outside / "settings.json"
    real.write_text("REAL SETTINGS\n", encoding="utf-8")
    vault = tmp_path / "v"
    _build_vault(vault, manifest_data)
    # 把 vault 里的 .claude 换成指向树外目录的软链
    shutil_free_remove(vault / ".claude")
    os.symlink(str(outside), str(vault / ".claude"))

    assert not real.resolve().is_relative_to(vault.resolve()), "前提: 落点在路径意义上确实在树外"
    rc = _run(vault, report=real)
    assert rc == 3
    assert real.read_text(encoding="utf-8") == "REAL SETTINGS\n"


def shutil_free_remove(path: Path) -> None:
    """删掉一棵测试用的临时目录树（只在 tmp_path 下用；不引入 shutil，AST 门禁它）。"""
    for child in sorted(path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if child.is_dir() and not child.is_symlink():
            child.rmdir()
        else:
            child.unlink()
    path.rmdir()


def test_unreadable_subtree_is_not_reported_as_match(vault_pair):
    """HIGH 回归: 读不进去的子树不得被当成「不存在」而判等。

    `Path.rglob` 静默吞 PermissionError —— 源里一棵 000 权限的子树看起来跟不存在
    一样，与目标的空目录一比就「相等」，exit=0。那是漏报：把「我看不见」说成
    「一致」，比误报危险。
    """
    source, target = vault_pair
    locked = source / ".claude" / "hooks" / "child"
    locked.mkdir(parents=True)
    (locked / "hidden.txt").write_text("SECRET DIFFERENCE\n", encoding="utf-8")
    (target / ".claude" / "hooks" / "child").mkdir(parents=True)  # 目标是空目录
    os.chmod(locked, 0o000)
    try:
        result = _classify(target, source=source)
        assert result.unreadable != [], "不可读条目必须被登记"
        assert result.exit_code != 0, "读不进去就不能报 0"
    finally:
        os.chmod(locked, 0o755)


def test_trailing_newline_name_is_not_excluded(vault_pair):
    """MEDIUM 回归: 正则用 `$` 会匹配「最后一个换行之前」，名字带尾随换行的文件被误排除。

    POSIX 文件名允许换行；shell 的模式不会匹配它，校验器也不该匹配。
    """
    rx = vv._pattern_to_regex(".claude/hooks/pending_archives*.jsonl")
    assert rx.fullmatch(".claude/hooks/pending_archives_keep.jsonl")
    assert not rx.fullmatch(".claude/hooks/pending_archives_keep.jsonl\n")
    source, target = vault_pair
    weird = source / ".claude" / "hooks" / "pending_archives_keep.jsonl\n"
    weird.write_text("[]", encoding="utf-8")
    result = _classify(target, source=source)
    # 源多了一个不该被排除的文件 → 必须体现为 drift，而不是被静默排除
    assert [f.path for f in result.content_drift] == [".claude/hooks"]


@pytest.mark.parametrize(
    "bad_scan",
    [
        {"dir": 123, "match": "*"},
        {"dir": [], "match": "*"},
        {"dir": ".claude", "match": 123},
        {"dir": ".claude", "match": []},
        {"dir": ".claude", "match": ""},
        {"dir": "/absolute", "match": "*"},
        {"dir": "../outside", "match": "*"},
    ],
)
def test_invalid_extra_scan_exits_2(tmp_path, vault_pair, manifest_data, bad_scan):
    """MEDIUM 回归: extra_scan 的 dir/match 曾完全不校验。

    非字符串让校验器以未捕获 TypeError 终止（rc=1 而非承诺的 2）；更糟的是 `dir`
    接受绝对路径与 `..`，扫描面直接逃出 --vault。path 有这套校验、extra_scan.dir
    没有——同一条约束只在一半字段上生效，正是根因。
    """
    source, target = vault_pair
    manifest_data["extra_scan"] = [bad_scan]
    bad = tmp_path / "bad-scan.json"
    bad.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError):
        vv.load_manifest(bad)
    assert vv.main(["--vault", str(target), "--manifest", str(bad), "--source", str(source)]) == 3


@pytest.mark.parametrize("variant", [".claude/skills/", ".claude//skills", ".claude/./skills"])
def test_path_is_normalized_so_match_and_extra_agree(tmp_path, vault_pair, manifest_data, variant):
    """MEDIUM 回归: path 原样入集、extra 检测用规范化路径 → 同一条目同时进 match 与 extra。"""
    source, target = vault_pair
    for item in manifest_data["items"]:
        if item["path"] == ".claude/skills":
            item["path"] = variant
            break
    else:  # pragma: no cover — 清单里一定有这一项
        raise AssertionError("清单里找不到 .claude/skills")
    m = tmp_path / "variant.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    manifest = vv.load_manifest(m)
    assert ".claude/skills" in manifest.declared_paths, "规范化后应当与磁盘上的相对路径一致"
    result = vv.verify(target, manifest, source_dir=source)
    assert result.extra == [], "同一条目不该既是 match 又是 extra"
    assert result.missing == []


@pytest.mark.parametrize(
    "bad_manifest_bytes",
    [b"\xff\xfe not utf-8", b"{ not json", b'{"version": 1'],
)
def test_unreadable_or_malformed_manifest_exits_2(tmp_path, vault_pair, bad_manifest_bytes):
    """MEDIUM 回归: 非 UTF-8 / 坏 JSON 曾以未捕获异常终止，rc=1 而非 2。"""
    source, target = vault_pair
    bad = tmp_path / "bad.json"
    bad.write_bytes(bad_manifest_bytes)
    assert vv.main(["--vault", str(target), "--manifest", str(bad), "--source", str(source)]) == 3


def test_manifest_pointing_at_a_directory_exits_2(tmp_path, vault_pair):
    """`--manifest` 指向一个目录时也必须是 rc=2（曾是 IsADirectoryError 逃出）。"""
    source, target = vault_pair
    assert vv.main(["--vault", str(target), "--manifest", str(tmp_path), "--source", str(source)]) == 3


def test_exclude_kind_nondir_matches_what_the_script_deletes(vault_pair):
    """脚本 `:86` 的强制删除清掉一切非目录条目 —— 软链/悬空软链/FIFO 都算，真目录不算。"""
    _source, target = vault_pair
    hooks = target / ".claude" / "hooks"
    (hooks / "pending_archives_plain.jsonl").write_text("[]", encoding="utf-8")
    os.symlink(str(target / "Dashboard.md"), str(hooks / "pending_archives_link.jsonl"))
    os.symlink(str(target / "nope"), str(hooks / "pending_archives_dangling.jsonl"))
    os.mkfifo(str(hooks / "pending_archives_fifo.jsonl"))
    (hooks / "pending_archives_dir.jsonl").mkdir()

    hits = vv.ExcludeMatcher(vv.load_manifest(MANIFEST).exclude_items).hits_for(
        target,
        next(i for i in vv.load_manifest(MANIFEST).items if i.path == ".claude/hooks/pending_archives*.jsonl"),
    )
    assert "pending_archives_plain.jsonl" in " ".join(hits)
    assert "pending_archives_link.jsonl" in " ".join(hits)
    assert "pending_archives_dangling.jsonl" in " ".join(hits)
    assert "pending_archives_fifo.jsonl" in " ".join(hits)
    assert "pending_archives_dir.jsonl" not in " ".join(hits), "真目录不该被算作已删除"


def test_extra_scan_surface_is_pinned():
    """extra 覆盖面是本卡承诺的一部分，删掉一条不能静默通过。"""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert [(s["dir"], s["match"]) for s in data["extra_scan"]] == [
        (".claude", "*"),
        (".obsidian", "*.json"),
        (".obsidian/plugins", "*"),
    ]


def test_target_side_exclusion_is_also_pinned(vault_pair):
    """exclude 剔除在**目标侧**同样承重（早先只有源侧那一半被钉住）。"""
    source, target = vault_pair
    (target / ".claude" / "scripts" / "__pycache__").mkdir(parents=True)
    (target / ".claude" / "scripts" / "__pycache__" / "x.pyc").write_bytes(b"\x00")
    result = _classify(target, source=source)
    assert result.content_drift == [], "目标侧多出的排除件不该算 drift"
    assert [f.path for f in result.intentionally_excluded] == [".claude/**/__pycache__"]


def test_array_parse_scans_whole_file_not_a_fixed_window():
    """五数组解析不能只盯 :63-67 —— 那一行之下新增第 6 个数组会对主判据不可见。"""
    lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    whole = re.findall(r"^([A-Z_]+)=\(([^)]*)\)\s*$", "\n".join(lines), re.M)
    assert len(whole) == 5, f"全文扫描到的数组数与预期不符: {[n for n, _ in whole]}"
    lo, hi = MANIFEST_BLOCK
    for name, _ in whole:
        hit = [i + 1 for i, ln in enumerate(lines) if ln.startswith(name + "=(")]
        assert hit and lo <= hit[0] <= hi, f"{name} 落在 MANIFEST 区之外: 第 {hit} 行"


def test_bracket_is_literal_in_both_places(vault_pair):
    """`[` 在 _has_glob 与 _pattern_to_regex 两处必须是同一种东西。

    早先 GLOB_CHARS 含 `[`，于是一条写成字符类的模式会被判为 glob（走正则路径），
    而正则里 `[` 又被 re.escape 成字面量 —— 两处口径分裂，模式静默不命中，
    正确部署的 vault 因此被误报 drift。现在统一按字面量。
    """
    assert not vv._has_glob("outputs/[abc].json"), "`[` 不再算通配符"
    rx = vv._pattern_to_regex("outputs/[abc].json")
    assert rx.fullmatch("outputs/[abc].json"), "字面量应当精确命中"
    assert not rx.fullmatch("outputs/a.json"), "不得展开成字符类"
    # 真实文件名里的方括号按字面匹配 —— 这才是这类名字该有的行为
    source, target = vault_pair
    odd = target / "outputs" / "[draft].json"
    odd.write_text("{}", encoding="utf-8")
    result = _classify(target, source=source)
    assert [f.path for f in result.intentionally_excluded] == ["outputs/**"]
    assert odd.name in result.intentionally_excluded[0].detail


def test_duplicate_path_is_caught_after_normalization(tmp_path, manifest_data):
    """`outputs/` 与 `outputs` 是同一个 path —— 查重必须在规范化之后做。"""
    for item in manifest_data["items"]:
        if item["path"] == "outputs/**":
            item["path"] = "outputs/"
            break
    bad = tmp_path / "dup.json"
    bad.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(bad)
    assert "重复" in str(exc.value)


def test_unreadable_alone_still_blocks(vault_pair):
    """unreadable 单独出现时也必须挡住 —— 这条是「计入阻断」的专属门。

    上一条 test_unreadable_subtree_is_not_reported_as_match 里源侧不可读、目标侧空，
    两侧摘要不同 ⇒ content_drift 非空 ⇒ 退出码被它兜成 1，于是「unreadable 计入阻断」
    那段逻辑拆掉也不红（纵深兜住）。这里让**两侧都有同一个读不进去的目录**：
    摘要相同、没有 drift，unreadable 成为唯一的差异来源。
    顺带钉住一件事——两侧都读不进去时摘要会「判等」，所以不假绿全靠 unreadable 这一桶。
    """
    source, target = vault_pair
    locked_src = source / ".claude" / "hooks" / "locked"
    locked_tgt = target / ".claude" / "hooks" / "locked"
    for d in (locked_src, locked_tgt):
        d.mkdir(parents=True)
        (d / "same.txt").write_text("same\n", encoding="utf-8")
    os.chmod(locked_src, 0o000)
    os.chmod(locked_tgt, 0o000)
    try:
        result = _classify(target, source=source)
        assert result.content_drift == [], "两侧同样读不进去，摘要应当判等（无 drift）"
        assert result.missing == [] and result.extra == []
        assert result.unreadable != [], "读不进去必须被登记"
        assert result.exit_code != 0, "unreadable 单独出现时也不能报 0"
        assert _run(target, source=source) == 2
    finally:
        os.chmod(locked_src, 0o755)
        os.chmod(locked_tgt, 0o755)


# ── Codex round-3 的回归门 ────────────────────────────────────────────
#
# 八条都是隔离夹具实测成立后才改的，证据 evidence-g26/codex-r3-claims-AFTER-FIX-*.txt。


def test_case_insensitive_alias_is_refused(vault_pair, tmp_path):
    """BLOCKER 回归: 大小写目录别名曾直接绕过禁写检查。

    本机文件系统默认大小写不敏感——目录实际叫什么大小写都指向同一个对象，
    而 `resolve()` 不做大小写规范化、`is_relative_to` 是纯字符串比较。
    落点判据必须按 `(st_dev, st_ino)` 判，路径这个维度本身不成立。
    """
    _source, target = vault_pair
    if not (target.parent / target.name.upper()).is_dir():
        pytest.skip("本机文件系统大小写敏感，这条形态不适用")
    alias = target.parent / target.name.upper() / "report.txt"
    rc = _run(target, report=alias)
    assert rc == 3
    assert not (target / "report.txt").exists(), "报告被写进了被审树"


def test_exclusive_create_failure_does_not_delete_someone_elses_file(vault_pair, tmp_path):
    """BLOCKER 回归: `O_EXCL` 失败时那个文件不是本次创建的，绝不能清理它。

    早先 except 分支无条件 `unlink(tmp)`——实测会删掉别人的文件，
    指向它的软链因此变悬空。这是本轮整改**自己引入**的缺陷。
    """
    del vault_pair  # 这条只需要一个可写的临时目录, 不用被审树
    outside = tmp_path / "outside"
    outside.mkdir()
    report = outside / "report.txt"

    # 临时名 = .<name>.tmp-<pid>-<随机串>。把随机串固定住，才能预置一个**同名**的
    # 「别人的文件」，让 O_EXCL 真的失败 —— 否则那条 except 分支根本不会被触发，
    # 测试看起来绿其实什么都没验（fixture 形态 ≠ 生产形态）。
    fixed = bytes.fromhex("deadbeef")
    stranger = outside / f".report.txt.tmp-{os.getpid()}-deadbeef"
    stranger.write_text("SOMEONE ELSE'S FILE\n", encoding="utf-8")

    real_urandom = os.urandom
    os.urandom = lambda n: fixed[:n]
    try:
        with pytest.raises(vv.ReportWriteError):
            vv._write_report(report, "报告正文\n")
    finally:
        os.urandom = real_urandom

    assert stranger.exists(), "删掉了不属于本次调用的临时文件"
    assert stranger.read_text(encoding="utf-8") == "SOMEONE ELSE'S FILE\n"
    assert not report.exists(), "O_EXCL 失败后不该产出报告"


def test_two_hop_symlink_target_is_refused(vault_pair, tmp_path):
    """BLOCKER 回归: 禁写根必须**递归**展开——两层软链能绕开单层解析。"""
    _source, target = vault_pair
    a, b = tmp_path / "outA", tmp_path / "outB"
    a.mkdir()
    b.mkdir()
    os.symlink(str(b), str(a / "link"))
    os.symlink(str(a), str(target / "link"))
    rc = _run(target, report=b / "report.txt")
    assert rc == 3
    assert not (target / "link" / "link" / "report.txt").exists()


def test_incomplete_safety_scan_refuses_to_write(vault_pair, tmp_path):
    """BLOCKER 回归: 安全性扫描没跑完就不能声称落点安全。

    权限 0111 的目录能按名字访问、不能列目录——里面可能藏着指向树外的软链。
    扫不动就必须拒绝落盘，而不是默默放行。
    """
    _source, target = vault_pair
    locked = target / "locked"
    locked.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    os.symlink(str(outside), str(locked / "escape"))
    os.chmod(locked, 0o111)
    try:
        rc = _run(target, report=outside / "r.txt")
        assert rc == 3
        assert not (outside / "r.txt").exists()
    finally:
        os.chmod(locked, 0o755)


def test_both_sides_unreadable_plain_files_still_block(vault_pair):
    """HIGH 回归: 两侧同名普通文件都读不动、内容其实不同时，不得判等且报 0。

    `_leaf_digest` 早先遇到 OSError 只返回一个标记字符串，调用方无从知道发生过
    读取失败——摘要相等、unreadable 为空、rc=0。那是假绿。
    """
    source, target = vault_pair
    (source / "CLAUDE.md").write_text("AAAA\n", encoding="utf-8")
    (target / "CLAUDE.md").write_text("BBBB\n", encoding="utf-8")
    os.chmod(source / "CLAUDE.md", 0o000)
    os.chmod(target / "CLAUDE.md", 0o000)
    try:
        result = _classify(target, source=source)
        assert result.unreadable != [], "读不动的普通文件必须被登记"
        assert result.exit_code != 0, "读不动就不能报 0"
    finally:
        os.chmod(source / "CLAUDE.md", 0o644)
        os.chmod(target / "CLAUDE.md", 0o644)


def test_short_write_is_detected(tmp_path):
    """MEDIUM 回归: `os.write` 会短写，必须循环写满才换目录项。

    用一个只肯接受 1 字节的假 fd 复现——早先单次 `os.write` 正常返回，
    于是发布了一份截断的报告。
    """
    calls = []
    real_write = os.write

    def stingy_write(fd, data):
        calls.append(len(data))
        return real_write(fd, data[:1])

    out = tmp_path / "r.txt"
    original = os.write
    os.write = stingy_write
    try:
        vv._write_report(out, "ABCDE")
    finally:
        os.write = original
    assert out.read_text(encoding="utf-8") == "ABCDE", "短写没有被补齐"
    assert len(calls) >= 5, f"应当循环写满，实际只调了 {len(calls)} 次"


@pytest.mark.parametrize("field", ["source", "role", "origin", "note"])
def test_unencodable_string_in_manifest_exits_2(tmp_path, vault_pair, manifest_data, field):
    """MEDIUM 回归: 孤立代理字符能过 json.loads，却在写报告时抛 UnicodeEncodeError。

    那时已经过了 ManifestError 的捕获面，拿不到承诺的 rc=2，还会留下临时文件。
    """
    _source, target = vault_pair
    if field == "source":
        manifest_data["source"] = "\ud800"
    else:
        manifest_data["items"][0][field] = "\ud800"
    bad = tmp_path / "surrogate.json"
    bad.write_text(json.dumps(manifest_data), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    assert vv.main(["--vault", str(target), "--manifest", str(bad), "--report", str(out / "r.txt")]) == 3
    assert list(out.iterdir()) == [], "落点目录留下了临时文件"


@pytest.mark.parametrize("dot", [".", "./", ".//"])
def test_extra_scan_dot_is_normalized_to_root(tmp_path, vault_pair, manifest_data, dot):
    """MEDIUM 回归: `dir="."` 拼接出 `./a`，与 declared_paths 里的 `a` 对不上 → 误报 extra。"""
    _source, target = vault_pair
    manifest_data["extra_scan"] = [{"dir": dot, "match": "*.md"}]
    m = tmp_path / "dot.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    result = vv.verify(target, vv.load_manifest(m))
    assert result.extra == [], f"dir={dot!r} 把已声明的条目误报成了 extra"


def test_dangling_symlink_exclude_is_registered(vault_pair):
    """LOW 回归: `exists()` 对悬空软链是 False，但那个目录项确实在目标里。"""
    _source, target = vault_pair
    os.symlink(str(target / "nowhere"), str(target / "learning_events.jsonl"))
    os.symlink(str(target / "nowhere2"), str(target / ".obsidian" / "workspace.json"))
    result = _classify(target)
    got = [f.path for f in result.intentionally_excluded]
    assert "learning_events.jsonl" in got
    assert ".obsidian/workspace.json" in got
    assert result.extra == [], "悬空的 workspace.json 不该落到 extra"


def test_skeleton_content_excludes_are_pinned(vault_pair):
    """LOW 回归: `raw/**` 与 `templates/**` 删掉后曾仍然全绿——现在钉住它们。

    `:74` 的 mkdir 循环对六个骨架目录一视同仁，清单必须逐个声明「内容不复制」。
    """
    _source, target = vault_pair
    (target / "raw" / "lecture.pdf").write_text("x", encoding="utf-8")
    (target / "templates" / "daily.md").write_text("y", encoding="utf-8")
    result = _classify(target)
    got = [f.path for f in result.intentionally_excluded]
    assert "raw/**" in got, "raw 下的遗留内容必须被登记为「故意不复制」"
    assert "templates/**" in got
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_origin = [i["path"] for i in data["items"] if i["origin"] == "install-vault.sh:74"]
    assert sorted(by_origin) == ["raw/**", "templates/**"]


def test_bracket_exclude_declaration_works_end_to_end(tmp_path, vault_pair, manifest_data):
    """LOW 回归: 之前那条方括号测试用的规则是 `outputs/**`，没有真正含 `[` 的声明。

    这里放一条**真的带方括号**的 exclude，验证分类与负例都对。
    """
    _source, target = vault_pair
    manifest_data["items"].append(
        {"path": "outputs/[draft].json", "role": "build-artifact", "action": "exclude", "origin": "test-only"}
    )
    m = tmp_path / "bracket.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    (target / "outputs" / "[draft].json").write_text("{}", encoding="utf-8")
    (target / "outputs" / "d.json").write_text("{}", encoding="utf-8")
    result = vv.verify(target, vv.load_manifest(m))
    got = [f.path for f in result.intentionally_excluded]
    assert "outputs/[draft].json" in got, "字面方括号声明应当精确命中"
    # 负例：它不该被当成字符类而匹配到 outputs/d.json
    hits = vv.ExcludeMatcher(vv.load_manifest(m).exclude_items).hits_for(
        target,
        next(i for i in vv.load_manifest(m).items if i.path == "outputs/[draft].json"),
    )
    assert hits == ["outputs/[draft].json"]


def test_unreadable_leaf_inside_directory_is_registered(vault_pair):
    """目录**内部**的叶子读不动时也要登记 —— 与顶层文件那条走的是不同分支。

    `_digest` 有两处登记：顶层(被比对的 copy 项本身是文件)和循环内(目录里的子孙)。
    只测其中一处，另一处拆掉也不会红。
    """
    source, target = vault_pair
    for root in (source, target):
        leaf = root / ".claude" / "hooks" / "leaf.txt"
        leaf.write_text("same\n", encoding="utf-8")
    os.chmod(source / ".claude" / "hooks" / "leaf.txt", 0o000)
    os.chmod(target / ".claude" / "hooks" / "leaf.txt", 0o000)
    try:
        result = _classify(target, source=source)
        assert any("leaf.txt" in f.path for f in result.unreadable), "目录内读不动的叶子必须被登记"
        assert result.exit_code != 0
    finally:
        os.chmod(source / ".claude" / "hooks" / "leaf.txt", 0o644)
        os.chmod(target / ".claude" / "hooks" / "leaf.txt", 0o644)


# ── CARD-RV-G2-6: rc 四档 / extra_allow / hotkeys↔命令 id ────────────

PLUGIN_ID_PREFIX = "canvas-learning-system:"
PLUGIN_MAIN_TS = REPO_ROOT / "frontend" / "obsidian-plugin" / "src" / "main.ts"
TREE_HOTKEYS = REPO_ROOT / "canvas-vault" / ".obsidian" / "hotkeys.json"


def _command_ids_from_main_ts() -> set[str]:
    """真相源: main.ts 里 **addCommand 注册点**的 id 字面量。只读 frontend/, 不构建。

    正则绑到 `addCommand({ id: "…"` 而不是任意 `id: "canvas:…"` —— 后者把注释、
    别处的常量、乃至 `console.log` 里的同形字符串一并算进来, 数量锚就只证明了
    「文本里有 10 个这样的串」, 证明不了「真的注册了 10 个命令」(Codex r1 MEDIUM)。
    如实声明其上限: 这仍是文本提取, 不是 TS 语义分析。
    """
    text = PLUGIN_MAIN_TS.read_text(encoding="utf-8")
    return set(re.findall(r'addCommand\(\{\s*id:\s*"(canvas:[a-z0-9-]+)"', text))


def _write_plugin_main_js(vault: Path, ids) -> Path:
    """在合成 vault 里造一份只含指定 id 字面量的 main.js (构建产物的最小替身)。"""
    plugin_dir = vault / ".obsidian" / "plugins" / "canvas-learning-system"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    main_js = plugin_dir / "main.js"
    main_js.write_text("".join('this.addCommand({id:"%s"});' % i for i in sorted(ids)) + "\n", encoding="utf-8")
    return main_js


def _write_hotkeys(vault: Path, keys) -> None:
    (vault / ".obsidian" / "hotkeys.json").write_text(
        json.dumps({k: [{"modifiers": ["Mod"], "key": "X"}] for k in keys}), encoding="utf-8"
    )


def test_exit_codes_are_four_tiered():
    """rc 四档常量门 —— 0 ok / 1 missing / 2 mismatch / 3 usage。

    数字写死: 调用方 (deploy-vault.sh, U3-C) 靠它区分「缺东西」与「多东西」。
    """
    assert (vv.EXIT_OK, vv.EXIT_MISSING, vv.EXIT_MISMATCH, vv.EXIT_USAGE) == (0, 1, 2, 3)


def test_missing_and_mismatch_together_take_mismatch(vault_pair):
    """同时有 missing 与 mismatch 时取 2 —— 且 missing 单独出现仍是 1 (没被吞)。"""
    _source, target = vault_pair
    (target / ".obsidian" / "hotkeys.json").unlink()
    only_missing = _classify(target)
    assert [f.path for f in only_missing.missing] == [".obsidian/hotkeys.json"]
    assert only_missing.exit_code == vv.EXIT_MISSING == 1
    (target / ".claude" / "cache").mkdir(parents=True)
    both = _classify(target)
    assert both.missing and both.extra
    assert both.exit_code == vv.EXIT_MISMATCH == 2


def test_extra_allow_moves_entry_out_of_extra(tmp_path, vault_pair, manifest_data):
    """(g)① extra_allow 放行的项进 allowed-extra 且不计 rc; 未放行仍是 extra(2)。"""
    _source, target = vault_pair
    (target / ".obsidian" / "graph.json").write_text("{}", encoding="utf-8")

    base = tmp_path / "base.json"
    base.write_text(json.dumps(manifest_data), encoding="utf-8")
    before = vv.verify(target, vv.load_manifest(base))
    assert [f.path for f in before.extra] == [".obsidian/graph.json"], "未放行时必须是 extra"
    assert before.exit_code == vv.EXIT_MISMATCH == 2
    assert not before.allowed_extra

    manifest_data["extra_allow"] = [".obsidian/graph.json"]
    allow = tmp_path / "allow.json"
    allow.write_text(json.dumps(manifest_data), encoding="utf-8")
    manifest = vv.load_manifest(allow)
    after = vv.verify(target, manifest)
    assert after.extra == [], "放行后不得再计入 extra"
    assert [f.path for f in after.allowed_extra] == [".obsidian/graph.json"]
    assert after.exit_code == vv.EXIT_OK == 0, "allowed-extra 不计退出码"
    assert "## allowed-extra" in vv.render(after, manifest)


def test_extra_allow_glob_is_supported(tmp_path, vault_pair, manifest_data):
    """extra_allow 支持 *? glob —— 与 item.path 同一套 _pattern_to_regex 口径。"""
    _source, target = vault_pair
    (target / ".claude" / "cache").mkdir(parents=True)
    manifest_data["extra_allow"] = [".claude/cach?"]
    m = tmp_path / "glob.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    result = vv.verify(target, vv.load_manifest(m))
    assert [f.path for f in result.allowed_extra] == [".claude/cache"]
    assert result.exit_code == vv.EXIT_OK


def test_manifest_ships_empty_extra_allow():
    """本卡只造机制不替 U3-B 裁定 —— 仓内清单的初值必须是空列表。"""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["extra_allow"] == [], "extra_allow 初值必须为 [] (live 5 项归 U3-B 裁定)"
    assert "extra_allow" in data["description"], "description 须说明 extra_allow 语义"


@pytest.mark.parametrize("bad", ["not-a-list", {"a": 1}, 5, None])
def test_extra_allow_must_be_a_list(tmp_path, manifest_data, bad):
    manifest_data["extra_allow"] = bad
    m = tmp_path / "bad.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(m)
    assert "extra_allow" in str(exc.value)


@pytest.mark.parametrize(
    "bad, fragment",
    [
        ("/etc/passwd", "绝对路径"),
        ("../outside", ".."),
        ("", "不得为空"),
    ],
)
def test_extra_allow_path_field_uses_same_checks_as_item_path(tmp_path, manifest_data, bad, fragment):
    """同口径: 相对 / 无 .. / 非空 —— 与 item 的 path 共用 _check_relative_segment。"""
    manifest_data["extra_allow"] = [bad]
    m = tmp_path / "bad.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(m)
    assert fragment in str(exc.value)


def test_extra_allow_rejects_duplicates(tmp_path, manifest_data):
    manifest_data["extra_allow"] = [".claude/cache", ".claude/cache"]
    m = tmp_path / "dup.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(m)
    assert "重复" in str(exc.value)


@pytest.mark.parametrize(
    "bad, why",
    [
        (".obsidian/hotkeys.json", "与 declared 精确重叠"),
        ("outputs/**", "与 exclude 模式精确重叠"),
        (".obsidian/*.json", "allow 的 glob 覆盖了已声明的 .obsidian/app.json"),
        (".claude/**/__pycache__", "与 exclude 的 glob 精确重叠"),
        # ↓ 反向覆盖: allow 是字面量, 被 exclude 的 glob 罩住。缺了这一条,
        #   删掉实现里两处 `_pattern_covers(path, allow)` 上面四条仍全绿(Codex r1 LOW 实证)。
        ("outputs/cache.md", "字面 allow 被 exclude 的 glob outputs/** 罩住（反向覆盖）"),
        (".claude/hooks/pending_archives9.jsonl", "字面 allow 被 exclude 的 glob 罩住（反向覆盖）"),
    ],
)
def test_extra_allow_overlapping_declared_or_exclude_is_refused(tmp_path, manifest_data, bad, why):
    """(g)⑥ 同一路径不得有两种语义 —— 重叠即 ManifestError, CLI 侧走用法错档 3。"""
    manifest_data["extra_allow"] = [bad]
    m = tmp_path / "overlap.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(m)
    assert "重叠" in str(exc.value), why
    assert vv.main(["--vault", str(tmp_path), "--manifest", str(m)]) == 3


def test_plugin_command_ids_are_exactly_ten_and_tree_hotkeys_are_a_subset():
    """测试层真相源门: main.ts 恰 10 个命令 id, 树内 hotkeys 全是其中之一。

    10 写死是**防解析退化成空集**的验伪锚 —— 正则一旦失配, `∅ ⊆ 任何集合` 会假绿,
    所以下面还断言了 CLS 前缀的 hotkey 集合非空。
    """
    ids = _command_ids_from_main_ts()
    assert len(ids) == 10, f"main.ts 的命令 id 数与勘探不符: {sorted(ids)}"
    keys = json.loads(TREE_HOTKEYS.read_text(encoding="utf-8"))
    bound = {k[len(PLUGIN_ID_PREFIX) :] for k in keys if k.startswith(PLUGIN_ID_PREFIX)}
    assert bound, "树内 hotkeys 的 CLS 前缀项不得为空 (否则子集断言恒真)"
    assert bound <= ids, f"树内 hotkeys 绑了不存在的命令: {sorted(bound - ids)}"


def test_hotkey_orphan_is_counted_as_mismatch(vault_pair):
    """(g)⑦ 假 id → hotkey-orphan 1 且 rc=2。"""
    _source, target = vault_pair
    _write_plugin_main_js(target, _command_ids_from_main_ts())
    _write_hotkeys(target, [PLUGIN_ID_PREFIX + "canvas:does-not-exist"])
    result = _classify(target)
    assert [f.path for f in result.hotkey_orphan] == [PLUGIN_ID_PREFIX + "canvas:does-not-exist"]
    # 一次只打一类: 其余阻断桶必须为空, 否则 rc=2 会被别的差异喂饱
    assert (result.missing, result.extra, result.content_drift, result.unreadable) == ([], [], [], [])
    assert result.exit_code == vv.EXIT_MISMATCH == 2
    assert "## hotkey-orphan" in vv.render(result, vv.load_manifest(MANIFEST))


def test_hotkey_real_id_is_clean(vault_pair):
    """(g)⑧ 同一夹具换成真 id → orphan 0, rc 0 (对照组, 证 ⑦ 不是恒红)。"""
    _source, target = vault_pair
    ids = _command_ids_from_main_ts()
    _write_plugin_main_js(target, ids)
    _write_hotkeys(target, [PLUGIN_ID_PREFIX + sorted(ids)[0]])
    result = _classify(target)
    assert result.hotkey_orphan == []
    assert result.exit_code == vv.EXIT_OK == 0


def test_hotkeys_not_evaluated_when_main_js_missing(vault_pair):
    """(g)⑨ main.js 缺 → 报告明写 not evaluated, 不计 rc, 不静默。"""
    _source, target = vault_pair
    _write_hotkeys(target, [PLUGIN_ID_PREFIX + "canvas:does-not-exist"])
    assert not (target / ".obsidian" / "plugins" / "canvas-learning-system" / "main.js").exists()
    result = _classify(target)
    assert result.hotkey_orphan == []
    assert result.exit_code == vv.EXIT_OK == 0
    # ⚠️ 判据必须锁到 hotkeys 那一行: 整份报告的 content-drift 段在无 --source 时
    # 也写着 "not evaluated", 拿全文做包含判断会借用它 —— 把 hotkeys 提示删光也照样绿。
    text = vv.render(result, vv.load_manifest(MANIFEST))
    line = next(l for l in text.splitlines() if l.startswith("hotkeys "))
    assert "not evaluated" in line and "main.js" in line, f"hotkeys 行未明写未评估: {line}"


def test_foreign_plugin_hotkeys_are_ignored(vault_pair):
    """别的插件的快捷键不归本校验器管 —— 无 CLS 前缀的键一律忽略。"""
    _source, target = vault_pair
    _write_plugin_main_js(target, _command_ids_from_main_ts())
    _write_hotkeys(target, ["dataview:dataview-force-refresh-views"])
    result = _classify(target)
    assert result.hotkey_orphan == []
    assert result.exit_code == vv.EXIT_OK


def test_invalid_hotkeys_json_is_unreadable(vault_pair):
    """hotkeys.json 非法 JSON → unreadable (计入阻断), 不是静默跳过。"""
    _source, target = vault_pair
    _write_plugin_main_js(target, _command_ids_from_main_ts())
    (target / ".obsidian" / "hotkeys.json").write_text("{not json", encoding="utf-8")
    result = _classify(target)
    assert [f.path for f in result.unreadable] == [".obsidian/hotkeys.json"]
    # 一次只打一类
    assert (result.missing, result.extra, result.content_drift, result.hotkey_orphan) == ([], [], [], [])
    assert result.exit_code == vv.EXIT_MISMATCH == 2


def test_install_sh_skills_check_counts_skill_md_dirs(tmp_path):
    """(f) :117 的判据必须数「含 SKILL.md 的目录」, 不是数目录条目。

    树内 .claude/skills 有 11 个目录但只有 9 个含 SKILL.md —— 旧 `ls | wc -l`
    对「有目录没 SKILL.md」的半成品 skill 失明。
    """
    line = INSTALL_SH.read_text(encoding="utf-8").splitlines()[116]
    # 判据只看 check 的第二个参数(单引号包住的 eval 体), 不看标签 ——
    # 标签里的 "skills " 本身就含子串 "ls ", 拿整行做黑名单会因无关文本假红。
    assert line.count("'") == 2, f":117 不是「check \"标签\" '判据'」的形态: {line}"
    body = line.split("'", 1)[1].rsplit("'", 1)[0]
    assert "find " in body and "-name SKILL.md" in body, f":117 仍是旧判据: {body}"
    assert "-mindepth 2 -maxdepth 2" in body, "必须只数一级子目录下的 SKILL.md"
    assert "$(ls " not in body, "计数命令不得再是 ls | wc -l (那会把无 SKILL.md 的半成品目录算进去)"
    assert "-ge 8" in body, "阈值 8 不改 (决策页 §五「≥9」是 preflight 口径, 归 U3-C)"
    assert "-type f" in body, "SKILL.md 必须是普通文件 —— 同名目录不算一个 skill (Codex r1 MEDIUM)"

    # 行为断言: 只查命令字符串挡不住「给判据加 `|| true`」这类退化, 必须真跑一次。
    # 抽 :113(check 函数定义) + :117 两行喂给 bash, 不跑整个脚本(它会建目录)。
    two_lines = "\n".join(INSTALL_SH.read_text(encoding="utf-8").splitlines()[112:113] + [line])

    def _probe(root: Path) -> str:
        return subprocess.run(
            ["bash", "-c", two_lines],
            env={**os.environ, "TARGET": str(root)},
            capture_output=True,
            text=True,
        ).stdout

    good = tmp_path / "good"
    for i in range(9):
        (good / ".claude" / "skills" / f"s{i}").mkdir(parents=True)
        (good / ".claude" / "skills" / f"s{i}" / "SKILL.md").write_text("# s", encoding="utf-8")
    assert "✅" in _probe(good), "9 个含 SKILL.md 的 skill 应当通过"

    # 负控 A —— 只隔离 `-type f`: 7 个合格文件 + 1 个「SKILL.md 是目录」。
    # 不区分类型时数到 8 会通过, 加上 -type f 是 7 而拦下 ⇒ 这条样例单独承重。
    # (早先写成「6 文件 + 1 scripts + 1 目录」不隔离: 去掉 -type f 也才 7, 照样红,
    #  于是那条负控其实是被别的原因打红的 —— Codex round-2 LOW 实证。)
    dir_entry = tmp_path / "dir-entry"
    for i in range(8):
        (dir_entry / ".claude" / "skills" / f"s{i}").mkdir(parents=True)
        if i < 7:
            (dir_entry / ".claude" / "skills" / f"s{i}" / "SKILL.md").write_text("# s", encoding="utf-8")
    (dir_entry / ".claude" / "skills" / "s7" / "SKILL.md").mkdir()
    assert len(list((dir_entry / ".claude" / "skills").glob("*/SKILL.md"))) == 8, (
        "负控前提: 不区分类型时恰好数到 8, 否则这条样例隔离不出 -type f"
    )
    assert "❌" in _probe(dir_entry), "SKILL.md 是目录的条目不得计为一个 skill"

    # 负控 B —— 只隔离「数目录条目 vs 数入口文件」: 8 个目录, 其中一个只有 scripts/
    shy = tmp_path / "shy"
    for i in range(8):
        (shy / ".claude" / "skills" / f"s{i}").mkdir(parents=True)
        if i < 7:
            (shy / ".claude" / "skills" / f"s{i}" / "SKILL.md").write_text("# s", encoding="utf-8")
    (shy / ".claude" / "skills" / "s7" / "scripts").mkdir()
    assert "❌" in _probe(shy), "无入口文件的半成品 skill 不得计为完成"


# ── CARD-RV-G2-6 round-2 整改的门（Codex round-1 结论）────────────────


def test_copy_item_missing_on_source_is_not_reported_as_match(vault_pair):
    """HIGH 回归: 给了 --source 而模板源没有这一项时, 目标那一项**不得**记 match。

    match 读起来就是「核对过, 一致」—— 而这一项根本没比过。改记 unreadable
    (「看不见不等于一致」的同一条纪律), 计入阻断。
    """
    source, target = vault_pair
    (source / "Dashboard.md").unlink()  # 模板源没有, 目标有
    result = _classify(target, source=source)
    assert "Dashboard.md" not in [f.path for f in result.match], "未比较的项不得记 match"
    assert [f.path for f in result.unreadable] == ["Dashboard.md"]
    assert "模板源没有这一项" in result.unreadable[0].detail
    assert (result.missing, result.extra, result.content_drift) == ([], [], [])
    assert result.exit_code == vv.EXIT_MISMATCH == 2


def test_unreadable_dir_in_exclude_scan_surface_is_registered(vault_pair):
    """HIGH 回归 (= UAT-CARD-G2-6「未证明」#25): exclude 覆盖面读不动时不得静默跳过。

    `outputs/**` 的静态前缀是 `outputs`; 把它设成不可列目录, 旧实现只是跳过,
    报告照样 0 —— 「一个读不进去的目录里藏着 exclude 项」完全看不见。
    """
    _source, target = vault_pair
    locked = target / "outputs"
    (locked / "leftover.bin").write_text("x", encoding="utf-8")
    os.chmod(locked, 0o111)  # 可按名访问, 不可列目录
    try:
        result = _classify(target)
        assert any(f.path == "outputs" for f in result.unreadable), (
            f"exclude 覆盖面读不动必须登记, 实得 {[f.path for f in result.unreadable]}"
        )
        assert "exclude 覆盖面读不进去" in next(f for f in result.unreadable if f.path == "outputs").detail
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        os.chmod(locked, 0o755)


@pytest.mark.parametrize(
    "body, quote",
    [
        ('this.addCommand({id:"canvas:open-dashboard"});', "双引号"),
        ("this.addCommand({id:'canvas:open-dashboard'});", "单引号"),
        ("this.addCommand({id:`canvas:open-dashboard`});", "反引号"),
    ],
)
def test_command_id_literals_accept_every_quote_style(vault_pair, body, quote):
    """MEDIUM 回归: 只认双引号时, 单引号产物会让命令集变空 ⇒ **真实绑定全被误报 orphan**。

    打包器的引号风格不是稳定契约; 误拦一个正确部署的 vault 比漏放更难排查。
    """
    _source, target = vault_pair
    plugin_dir = target / ".obsidian" / "plugins" / "canvas-learning-system"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "main.js").write_text(body, encoding="utf-8")
    _write_hotkeys(target, [PLUGIN_ID_PREFIX + "canvas:open-dashboard"])
    result = _classify(target)
    assert result.hotkey_orphan == [], f"{quote}注册的命令被误判成 orphan"
    assert result.exit_code == vv.EXIT_OK == 0


def test_zero_command_ids_is_reported_as_unreadable_not_a_wall_of_orphans(vault_pair):
    """MEDIUM 回归: 产物里一个命令 id 都没解析出来时, 不得把每条绑定报成 orphan。

    阻断是对的, 但理由必须是「没法核对」而不是「这些命令不存在」——
    N 条**说错原因**的结论会把人引到错误的排查方向。
    """
    _source, target = vault_pair
    plugin_dir = target / ".obsidian" / "plugins" / "canvas-learning-system"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "main.js").write_text("/* 产物格式变了, 没有任何命令 id 字面量 */", encoding="utf-8")
    _write_hotkeys(target, [PLUGIN_ID_PREFIX + "canvas:open-dashboard", PLUGIN_ID_PREFIX + "canvas:open-node-chat"])
    result = _classify(target)
    assert result.hotkey_orphan == [], "不得报成 orphan"
    assert [f.path for f in result.unreadable] == [".obsidian/plugins/canvas-learning-system/main.js"]
    assert "无法核对 2 条快捷键绑定" in result.unreadable[0].detail
    assert result.exit_code == vv.EXIT_MISMATCH == 2
    line = next(ln for ln in vv.render(result, vv.load_manifest(MANIFEST)).splitlines() if ln.startswith("hotkeys "))
    assert "0 个命令 id" in line


def test_unencodable_hotkey_key_does_not_escape_the_exit_code(tmp_path, vault_pair):
    """MEDIUM 回归: vault 来源的不可编码字符不得让 UnicodeEncodeError 逃出退出码契约。

    JSON 里的 `"\\ud800"` 被 json.loads 解成孤立代理字符, 进了报告文本后
    `text.encode("utf-8")` 会抛 —— 而那个异常**不在** ReportWriteError 的捕获面里
    (那里只捕 OSError), 于是解释器以 1 退出, 被误读成「只有 missing」。
    round-3 已为 manifest 来源修过同一形态, 本卡新开的 vault 输入面把它重开了。
    """
    _source, target = vault_pair
    plugin_dir = target / ".obsidian" / "plugins" / "canvas-learning-system"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "main.js").write_text('addCommand({id:"canvas:open-dashboard"});', encoding="utf-8")
    (target / ".obsidian" / "hotkeys.json").write_text(
        '{"canvas-learning-system:canvas:\\ud800": [{"modifiers":["Mod"],"key":"X"}]}',
        encoding="utf-8",
        errors="surrogatepass",
    )
    out = tmp_path / "out"
    out.mkdir()
    report_path = out / "r.txt"
    rc = vv.main(["--vault", str(target), "--manifest", str(MANIFEST), "--report", str(report_path)])
    assert rc == vv.EXIT_MISMATCH == 2, "必须给出承诺的退出码, 而不是让异常逃逸"
    assert report_path.exists(), "报告必须落得下去"
    text = report_path.read_text(encoding="utf-8")
    assert "\\ud800" in text, "不可编码字符应转义成可见形式而不是丢失"
    assert sorted(p.name for p in out.iterdir()) == ["r.txt"], "不得留下临时文件"


def test_argparse_error_also_uses_the_usage_exit_code(vault_pair, capsys):
    """MEDIUM 回归: argparse 默认用 rc=2 退出 —— 而 2 在四档语义里是 mismatch。

    「命令行没写对」被调用方读成「vault 有多余文件」是最坏的一种混淆。
    """
    with pytest.raises(SystemExit) as exc:
        vv.main(["--vault"])  # 缺参数值
    assert exc.value.code == vv.EXIT_USAGE == 3
    assert "参数错误" in capsys.readouterr().err


def test_declared_paths_has_a_single_source_of_truth():
    """`Manifest.declared_paths` 与 load_manifest 的重叠检查必须共用同一个口径。

    各写一份就会漂: 将来给 declared 加一类 action 而只改一处, extra_allow 就能
    放行一条本该被管住的路径, 而且没有任何门会红。
    """
    manifest = vv.load_manifest(MANIFEST)
    assert vv._declared_paths(manifest.items) == manifest.declared_paths
    # 28 而不是 27: declared 是 copy+skeleton+**generate**, 比集合等价门那 27 项多
    # 一条 .canvas-config.yaml。两个数字各有出处, 不得互抄 —— 抄错正是本条的来历。
    assert len(manifest.declared_paths) == 28
    assert manifest.declared_paths - {
        i["path"]
        for i in json.loads(MANIFEST.read_text(encoding="utf-8"))["items"]
        if i["action"] in ("copy", "skeleton")
    } == {".canvas-config.yaml"}


def test_extra_allow_overlap_check_uses_the_same_declared_set_as_the_property(tmp_path, manifest_data):
    """LOW 回归: 「单一真相源」不能只比 helper 与调用 helper 的 property —— 那是自证。

    要证的是**加载侧**也走同一口径。判据取 `generate` 那一类: 它在 declared 里、
    却不在集合等价门那 27 项里。加载侧若自己另写一份而漏掉 generate,
    `extra_allow=[".canvas-config.yaml"]` 就会被错误接受 —— 本门直接拦这个行为。
    """
    manifest_data["extra_allow"] = [".canvas-config.yaml"]  # action=generate 的那一项
    m = tmp_path / "gen-overlap.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(m)
    assert "重叠" in str(exc.value) and ".canvas-config.yaml" in str(exc.value)


def test_unreachable_exclude_scan_root_is_registered_not_treated_as_absent(tmp_path, vault_pair, manifest_data):
    """HIGH 回归: `Path.exists()` 把「不存在」和「问不出来」都返回 False。

    一个因祖先目录缺搜索权限而 stat 不到的 exclude 目标, 会在**进入** `_walk()` 的
    错误透传链之前就提前返回空 —— 报告照样 0。glob 分支与精确分支两个入口都要盖到。
    """
    _source, target = vault_pair
    guard = target / "outputs"
    (guard / "locked").mkdir(parents=True)
    (guard / "locked" / "x.jsonl").write_text("x", encoding="utf-8")
    manifest_data["items"].append(
        {"path": "outputs/locked/**", "role": "test", "action": "exclude", "origin": "test-only"}
    )
    manifest_data["items"].append(
        {"path": "outputs/locked/x.jsonl", "role": "test", "action": "exclude", "origin": "test-only"}
    )
    m = tmp_path / "unreachable.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    os.chmod(guard, 0o000)  # 祖先无搜索权限 ⇒ 子项 lstat 不到
    try:
        result = vv.verify(target, vv.load_manifest(m))
        paths = [f.path for f in result.unreadable]
        assert "outputs/locked" in paths, f"glob 分支的扫描根问不出来时必须登记, 实得 {paths}"
        assert "outputs/locked/x.jsonl" in paths, f"精确分支同样要登记, 实得 {paths}"
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        os.chmod(guard, 0o755)


def test_exclude_scan_failure_is_registered_exactly_once(vault_pair):
    """LOW 回归: 同一个读不动的位置被多条 exclude 前缀扫到时**只登记一次**。

    `any()` / `next()` 这类断言允许重复登记 —— 要锁去重就得数次数。
    `.claude/hooks` 同时落在 `.claude/**/__pycache__` 与
    `.claude/hooks/pending_archives*.jsonl` 两条 exclude 的扫描面里。
    """
    _source, target = vault_pair
    locked = target / ".claude" / "hooks"
    (locked / "x.txt").write_text("x", encoding="utf-8")
    os.chmod(locked, 0o111)  # 可按名访问, 不可列目录
    try:
        manifest = vv.load_manifest(MANIFEST)
        # 前提: 确实有**两条** exclude 的扫描面覆盖 .claude/hooks —— 否则「只登记一次」
        # 也可能是「只有一个来源到达」, 少扫一个会伪装成去重成功(Codex round-3 LOW)。
        reaching = [
            i.path for i in manifest.exclude_items if vv._static_prefix(i.path) in ("", ".claude", ".claude/hooks")
        ]
        assert len(reaching) >= 2, f"前提不成立: 覆盖 .claude/hooks 的 exclude 只有 {reaching}"
        result = vv.verify(target, manifest)
        hits = [f.path for f in result.unreadable if f.path == ".claude/hooks"]
        assert len(hits) == 1, f"同一位置必须恰好登记一次, 实得 {len(hits)} 次"
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        os.chmod(locked, 0o755)


def test_both_sides_unreadable_is_not_counted_as_match(vault_pair):
    """MEDIUM 回归: 两侧都读不动、摘要标记因此相等时, 该项**不得**同时计入 match。

    登记了 unreadable 却还把它算作「一致」, 等于在同一份报告里既说「没证明」又说「证明了」。
    """
    source, target = vault_pair
    for root in (source, target):
        (root / "Dashboard.md").chmod(0o000)
    try:
        result = _classify(target, source=source)
        assert "Dashboard.md" in [f.path for f in result.unreadable]
        assert "Dashboard.md" not in [f.path for f in result.match], "未证明一致的项不得记 match"
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        for root in (source, target):
            (root / "Dashboard.md").chmod(0o644)


def test_symlink_target_with_undecodable_bytes_does_not_crash_the_digest(vault_pair):
    """MEDIUM 回归: 摘要阶段的编码也不得抛 —— `_printable()` 只守 render 出口, 守不到这里。

    软链目标是任意字节串, `os.readlink` 用 surrogateescape 解码; 严格 `encode("utf-8")`
    会抛 `UnicodeEncodeError`, 而它不在任何捕获面里 —— CLI 会以 1 退出, 被读成「只有 missing」。
    """
    source, target = vault_pair
    link = target / ".claude" / "skills" / "odd-link"
    os.symlink(b"bad\xff-target", os.fsencode(link))
    result = _classify(target, source=source)  # 不抛即为通过
    assert result.exit_code in (vv.EXIT_MISSING, vv.EXIT_MISMATCH)
    text = vv.render(result, vv.load_manifest(MANIFEST))
    text.encode("utf-8")  # 报告仍可编码


def test_tilde_expansion_failure_uses_the_usage_exit_code(vault_pair, capsys):
    """MEDIUM 回归: `~未知用户名` 让 `expanduser()` 抛 `RuntimeError` —— 归用法错档 3, 不是 1。"""
    _source, target = vault_pair
    bogus = "~cls-no-such-user-9c1f/x"
    # 四个调用点逐个覆盖 —— 只测 vault/manifest 时, 把 --report 恢复成直接
    # expanduser 也不会红(Codex round-3 LOW)。
    assert vv.main(["--vault", bogus]) == vv.EXIT_USAGE == 3
    assert "路径展开失败" in capsys.readouterr().err
    assert vv.main(["--vault", str(target), "--source", bogus]) == vv.EXIT_USAGE == 3
    assert vv.main(["--vault", str(target), "--manifest", bogus]) == vv.EXIT_USAGE == 3
    assert vv.main(["--vault", str(target), "--report", bogus]) == vv.EXIT_USAGE == 3


# ── CARD-RV-G2-6 round-4 整改的门（Codex round-3 结论）────────────────


def test_digest_encoding_is_injective_not_merely_total():
    """HIGH 回归: 摘要编码必须**单射**, 「不抛异常」不够。

    round-3 我选了 `backslashreplace`，理由写的是「摘要只需确定性」—— 确定性是必要
    条件不是充分条件。它有损: 一个非法字节经 surrogateescape 解码后, 与字面写出来的
    同名转义串编码后**逐字节相同** ⇒ 两个不同的软链目标判等 = 假绿。
    这条门直接钉住「不同输入 → 不同字节」这个性质本身，而不是钉某个函数名。
    """
    from_bytes = os.fsdecode(b"bad\xff-target")  # → 含 U+DCFF 的字符串
    literal = "bad\\udcff-target"  # 纯 ASCII，字面反斜杠
    assert from_bytes != literal, "前提: 这两个字符串本来就不同"
    assert from_bytes.encode("utf-8", "backslashreplace") == literal.encode("utf-8", "backslashreplace"), (
        "前提: backslashreplace 确实把它们压成同一串 —— 否则这条门在防一个不存在的东西"
    )
    # 判据绑 AST 而不是文本: 这一轮已经被**注释里的词**误伤过三次
    # (标签里的 "ls "、docstring 里的代理转义、这里的 "backslashreplace")。
    # 只看 `.encode(...)` 调用的实参，注释与说明文字怎么写都不影响判定。
    import ast

    tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
    digest_funcs = {"_leaf_digest", "_digest"}
    offenders = []
    for func in ast.walk(tree):
        if not isinstance(func, ast.FunctionDef) or func.name not in digest_funcs:
            continue
        for node in ast.walk(func):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "encode":
                errs = [a.value for a in node.args[1:] if isinstance(a, ast.Constant)]
                errs += [
                    k.value.value for k in node.keywords if k.arg == "errors" and isinstance(k.value, ast.Constant)
                ]
                if "backslashreplace" in errs:
                    offenders.append((func.name, node.lineno))
    assert offenders == [], f"摘要路径上的 encode 不得用有损的 backslashreplace: {offenders}"
    # 验伪锚: 这套 AST 判据确实能看见摘要函数里的 encode 调用（否则它恒真）
    seen = [
        n.lineno
        for f in ast.walk(tree)
        if isinstance(f, ast.FunctionDef) and f.name in digest_funcs
        for n in ast.walk(f)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "encode"
    ]
    assert len(seen) >= 3, f"摘要路径上应当有至少 3 处 encode 调用, 实见 {len(seen)} 处"


def test_two_different_symlink_targets_do_not_collide(tmp_path):
    """HIGH 回归（行为面）: 上一条钉性质，这一条钉后果 —— 两个不同软链目标不得判等。"""
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    os.symlink(b"bad\xff-target", os.fsencode(a / "link"))
    os.symlink(b"bad\\udcff-target", os.fsencode(b / "link"))
    assert vv._digest(a) != vv._digest(b), "不同的软链目标必须给出不同摘要"


def test_entry_state_maps_enotdir_to_absent(tmp_path):
    """MEDIUM 回归: `ENOTDIR` 是**确定的**否定答案，不是「问不出来」。

    `a` 是普通文件时，`a/b` 不可能存在 —— 归 unreadable 会让 exclude 被误阻断。
    """
    plain = tmp_path / "a"
    plain.write_text("x", encoding="utf-8")
    assert vv._entry_state(plain / "b") == "absent"
    assert vv._entry_state(tmp_path / "nope") == "absent"
    assert vv._entry_state(plain) == "present"


def test_unreadable_leaf_in_listable_but_unsearchable_dir_is_registered(tmp_path):
    """HIGH 回归: 目录可列名字但不可 stat 里面的条目（0444）时，叶子摘要不得落到 unknown。

    那几个类型谓词全都吞 OSError ⇒ 权限不足时**全部返回 False** ⇒ 走到 `"?:unknown"`
    且 `bad=False` ⇒ 两侧都这样就判等，unreadable 为空，退出码 0 = 假绿。
    """
    d = tmp_path / "d"
    d.mkdir()
    (d / "f.txt").write_text("AAA", encoding="utf-8")
    os.chmod(d, 0o444)
    try:
        digest, bad = vv._leaf_digest(d / "f.txt")
        assert bad is True, f"读不动的叶子必须回报 bad=True, 实得 ({digest!r}, {bad})"
        assert digest == "U:unreadable"
        collected: list[str] = []
        vv._digest(d, unreadable=collected)
        assert collected == ["f.txt"], f"目录摘要必须把它登记进 unreadable, 实得 {collected}"
    finally:
        os.chmod(d, 0o755)


def test_kind_ok_refuses_to_claim_a_type_it_cannot_query(tmp_path):
    """HIGH 回归: 问不出类型时不得宣称满足任何类型条件 —— 尤其 `nondir`。

    原写法 `not (is_dir() and not is_symlink())` 在谓词被权限吞掉时**恒为 True**,
    于是一个查不动的条目会被当成 nondir 而误判成「故意不复制」。
    """
    guard = tmp_path / "g"
    guard.mkdir()
    (guard / "x").write_text("x", encoding="utf-8")
    os.chmod(guard, 0o000)
    try:
        target = guard / "x"
        for kind in ("dir", "file", "nondir", ""):
            item = vv.Item(path="x", role="t", action="exclude", kind=kind)
            assert vv._kind_ok(item, target) is False, f"kind={kind!r} 时不得宣称命中"
    finally:
        os.chmod(guard, 0o755)


def test_unqueryable_item_target_is_not_downgraded_to_missing(tmp_path, vault_pair, manifest_data):
    """HIGH 回归: item 目标「问不出来」不得降级成 missing（那会给 rc=1「只缺东西」）。"""
    _source, target = vault_pair
    guard = target / ".claude"
    os.chmod(guard, 0o000)
    try:
        result = _classify(target)
        assert not any(f.path.startswith(".claude/") for f in result.missing), (
            f"查询不到的项不得记 missing, 实得 {[f.path for f in result.missing]}"
        )
        assert any(f.path.startswith(".claude/") and "查询不到" in f.detail for f in result.unreadable)
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        os.chmod(guard, 0o755)


def test_unqueryable_extra_scan_root_is_registered(tmp_path, vault_pair):
    """HIGH 回归: extra 覆盖面的根问不出来时不得静默跳过 —— 「没扫」不等于「没有」。"""
    _source, target = vault_pair
    guard = target / ".obsidian"
    os.chmod(guard, 0o000)
    try:
        result = _classify(target)
        assert any(f.path in (".obsidian", ".obsidian/plugins") for f in result.unreadable), (
            f"覆盖面根查询不到必须登记, 实得 {[f.path for f in result.unreadable]}"
        )
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        os.chmod(guard, 0o755)


def test_content_drift_is_not_hidden_by_an_unreadable_sibling(vault_pair):
    """MEDIUM 回归: 同一 copy 项里既有读不动的叶子、又有真实内容差异时，两者都要报。

    round-3 我把「读不动就 continue」放在漂移判断**之前**，于是 content-drift 归 0 ——
    退出码仍是 2，但分类信息退化了，人会照着错误的方向去查。
    """
    source, target = vault_pair
    skills = "skills"
    (source / ".claude" / skills / "readable.txt").write_text("AAA", encoding="utf-8")
    (target / ".claude" / skills / "readable.txt").write_text("BBB", encoding="utf-8")
    for root in (source, target):
        blocked = root / ".claude" / skills / "blocked.txt"
        blocked.write_text("x", encoding="utf-8")
        blocked.chmod(0o000)
    try:
        result = _classify(target, source=source)
        assert ".claude/skills" in [f.path for f in result.content_drift], (
            f"可见的内容差异不得被读不动的兄弟条目遮掉, 实得 drift={[f.path for f in result.content_drift]}"
        )
        assert result.unreadable, "读不动的叶子仍要登记"
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        for root in (source, target):
            (root / ".claude" / skills / "blocked.txt").chmod(0o644)


def test_stdout_encoding_and_broken_pipe_stay_inside_the_exit_contract():
    """MEDIUM 回归: stdout 写不出去也不得脱离四档。

    `PYTHONIOENCODING=ascii` 下报告正文编码失败曾给 rc=1（被读成「只有 missing」）；
    下游关管道曾让解释器退出期 flush 失败给 rc=120。两者都不是「vault 有问题」。
    """
    env = {**os.environ, "PYTHONIOENCODING": "ascii"}
    done = subprocess.run([sys.executable, "-B", str(VERIFIER), "--help"], capture_output=True, env=env)
    assert done.returncode == 0, f"ascii 环境下 --help 应为 0, 实得 {done.returncode}"

    proc = subprocess.Popen(
        [sys.executable, "-B", str(VERIFIER), "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    proc.stdout.close()
    _, err = proc.communicate()
    assert proc.returncode == vv.EXIT_USAGE == 3, f"断管应归用法错档 3, 实得 {proc.returncode}"
    assert b"Exception ignored" not in err, "不得在解释器退出期留下未处理异常"
