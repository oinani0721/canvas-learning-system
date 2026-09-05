# CARD-G2-6 (BATCH-2026-09-05-第十二批) — vault 部署清单 + 只读校验器的裁判
#
# 被测物: scripts/vault-install-manifest.json + scripts/verify_vault_install.py
# 真相源: scripts/install-vault.sh MANIFEST 区 (:61-69) 与其隐含部署语义 (:74-109)
#
# 钉死点:
#   1. **集合等价**: manifest 里 action ∈ {copy, skeleton} 的 path 集合, 与 install-vault.sh
#      :63-67 五个 shell 数组按各自前缀展开后的并集**逐项相等**。这是本门的主判据 ——
#      manifest 一旦与脚本漂移, 部署边界就有两份真相。
#      验伪锚: 先断言正则确实解析出 5 个数组 / 27 个元素, 否则「空集 == 空集」会假绿。
#   2. **schema**: version int / items 列表 / 必填键 / action 四枚举 / path 相对·无 `..`·无重复。
#   3. **四类 diff 各自独立承重**: missing / extra / content-drift / intentionally-excluded
#      每类一个反例, 一次只打一类, 断言「该类精确命中该 path」且「其余三类为空」——
#      只断言 rc != 0 是粗判据, 会被任意一类差异喂饱。
#   4. **绝对路径负控**: manifest 里出现绝对 path → 退出码 2 (用法/配置错), 不是 1。
#   5. **零写**: 对 target 跑一次校验器, 前后全树 (文件 sha + 目录条目) 清单逐字相同。
#      校验器有任何写目标 vault 的路径 = 阻断级缺陷。
#
# 本门证明什么: manifest 与脚本数组等价; 校验器的五种分类各自可被单独触发; 校验器不写目标树。
# 本门不证明什么: 不证明 install-vault.sh 真跑起来会产出符合 manifest 的 vault (禁真跑脚本,
#   属 CARD-G2-7 五动作 CLI 的范围); 不证明 live vault 的 extra 项应否进 manifest (未裁);
#   合成 fixture 的「有扩展名 = 文件」启发式只服务于本文件的目录/文件搭建, 不是生产语义。

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
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
    assert _run(target, source=source) == 1


def test_content_drift_is_detected_alone(vault_pair):
    source, target = vault_pair
    (target / "Dashboard.md").write_text("drifted\n", encoding="utf-8")
    _assert_only(_classify(target, source=source), "content_drift", ["Dashboard.md"])
    assert _run(target, source=source) == 1


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
    assert rc == 2


def test_missing_vault_dir_exits_2(tmp_path):
    rc = vv.main(["--vault", str(tmp_path / "nope"), "--manifest", str(MANIFEST)])
    assert rc == 2


def test_report_inside_vault_exits_2(vault_pair):
    source, target = vault_pair
    rc = _run(target, source=source, report=target / "report.txt")
    assert rc == 2
    assert not (target / "report.txt").exists()


def test_report_inside_source_exits_2(vault_pair):
    source, target = vault_pair
    rc = _run(target, source=source, report=source / "report.txt")
    assert rc == 2
    assert not (source / "report.txt").exists()


def test_verifier_exposes_only_readonly_switches():
    """(b) 只读: CLI 参数面是**白名单**, 多一个开关就红。

    不用「文本里不得出现 --fix」那种判据 —— 它既假红 (docstring 里提一嘴就中)
    又假绿 (换个名字叫 --repair-now 就漏)。白名单挡得住没预想到的名字。
    """
    parser = vv._build_parser()
    options = {s for action in parser._actions for s in action.option_strings}
    assert options == {"-h", "--help", "--vault", "--source", "--manifest", "--report"}


def test_verifier_source_has_no_stray_write_calls():
    """(b) 只读: AST 层数写操作 —— 唯一允许的写是 main() 里落 --report。

    看的是调用节点, 不是文本, 所以注释/docstring 里怎么写都不影响判定。
    """
    import ast

    tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
    write_attrs = {
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
    }
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in write_attrs:
                found.append((node.func.attr, node.lineno))
        # open(..., "w") 之类
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "open":
                found.append(("open", node.lineno))
    assert [name for name, _ in found] == ["write_text"], f"校验器出现了预期外的写操作: {found}"
    # 那一次 write_text 必须在 main() 内 (落 --report), 不在比对逻辑里
    main_fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    main_end = main_fn.end_lineno
    assert main_end is not None
    assert main_fn.lineno < found[0][1] <= main_end
    assert "shutil" not in {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    }


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
    assert _run(target, source=source, report=report) == 1
    assert _tree_digest(target) == before_target, "校验器写了目标 vault"
    assert _tree_digest(source) == before_source, "校验器写了模板源"
    assert report.exists()
