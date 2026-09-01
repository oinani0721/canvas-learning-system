"""CARD-G3-2 per-vault 复习事件账本落地 — write-ahead 写序 + 单写者语义行为门。

[BATCH-2026-09-01-第八批 / CARD-G3-2]

锁的是 schema v1 §6.2 落进 quiz-answer 静态块 + fsrs_bridge 后的**行为**:
  1. A1 write-ahead (先 durable append 后 apply/发布) — 由耐久序列 spy 门证明
     调用序列, **不**证明掉电后数据存活 (那需要真实断电/故障注入, 不在本卡);
  2. A2 恢复先于新写 (pending 增量重放, 基线=当前 frontmatter; dup 自身的
     FSRS 应用走重放, restore 只补评分链其余副作用, 绝不二次 apply);
  3. A3 等时唯一口径 = 写侧推进 W+1s (bridge 内实现);
  4. A5 整秒 (bridge 入口截断; review_time 与 W 同一瞬间);
  5. A6 UTC 归一 + naive 拒收 (bridge);
  6. A4.5 parsed-field 查重 + LF 守卫 + 短写校验 + envelope 冲突门;
  7. 裁决② degraded: fsrs 不可用 → 事件仍落账、两键成对哨兵、W 不推进;
  8. 裁决③ 残缺卡 fail-closed 零写;
  9. 写点普查不新增第三套实现 (全仓 grep 门)。

fixture 与生产同源 (MEMORY: fixture 形态 ≠ 生产形态):
  - 被测静态块从 SKILL.md **逐字提取** (仅 P 常量重定向, 同 G3-1 范式);
  - 节点 frontmatter 逐字仿 live 真实形态 (裸值/字段顺序/calibration_log 缩进);
  - validator/bridge/decay_beta 经 symlink 引真文件 (漂移即测到);
  - vault_id 故意带连字符+中文 (`canvas-vault-测试`) — 写侧若漏 sanitize
    (事件写原始连字符形式) 校验器绑定比对当场翻红;
  - backend/.venv 必须是**目录** symlink: 文件级 symlink 启动 venv python
    会丢 pyvenv.cfg 探测 (2026-09-01 实测) → fsrs_unavailable 假降级。

契约文档: docs/learning-events-schema-v1.md §6.1-6.3
"""

import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

WT = Path(__file__).resolve().parents[3]
VALIDATOR = WT / "backend" / "scripts" / "validate_learning_events.py"
SKILL = WT / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
VAULT_SCRIPTS = WT / "canvas-vault" / ".claude" / "scripts"

_SKILL_TEXT = SKILL.read_text(encoding="utf-8")
_MAIN_BLOCKS = [
    b
    for b in re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", _SKILL_TEXT, re.DOTALL)
    if 'P = "/tmp/quiz-answer-payload.json"' in b
]
assert len(_MAIN_BLOCKS) == 1, f"SKILL.md 应恰有 1 个主写点 PYEOF 块, 实见 {len(_MAIN_BLOCKS)}"
#: 逐字提取的主写点 (运行时按 P 常量重定向到 tmp fixture)
CODE = _MAIN_BLOCKS[0]

NODE_REL = "节点/测试节点.md"
EID = "测试检验-2026-08-01-1000#q1"
TS1 = "2026-08-01T10:00:00Z"

#: 逐字仿 live 真实节点形态 (裸值; 裸词键第 0 列; calibration_log 条目缩进两格)
NODE_V0 = (
    '---\ntype: concept\nmastery_score: 0.5\ntitle: 测试节点\nsource_board: "[[原白板/CS 61B]]"\n---\n测试节点正文。\n'
)
#: canonical Review 态 (classify_card_state → normal), W = 10:00:00Z
NODE_REVIEW_W10 = (
    "---\n"
    "type: concept\n"
    "mastery_score: 0.5\n"
    "fsrs_due: 2026-08-11T13:56:58Z\n"
    "fsrs_state: 2\n"
    "fsrs_stability: 10.0\n"
    "fsrs_difficulty: 5.0\n"
    "fsrs_last_review: 2026-08-01T10:00:00Z\n"
    "title: 测试节点\n"
    "---\n"
    "测试节点正文。\n"
)


def _payload(**kw):
    base = {
        "node": NODE_REL,
        "grade_norm": 0.752,
        "ts": TS1,
        "event_id": EID,
        "exam_board": "检验白板/测试检验-2026-08-01-1000.md",
        "question_id": "q1",
        "source_board": "[[原白板/CS 61B]]",
        "self_confidence_raw": "半懂",
        "self_confidence_norm": 0.5,
        "abandoned": False,
        "callout": "",
    }
    base.update(kw)
    return base


@pytest.fixture()
def vault(tmp_path):
    """完整镜像布局: REPO=tmp_path, VAULT=tmp_path/canvas-vault。

    被测代码 (validator/bridge/decay_beta) 全部 symlink 引真文件 —
    主树漂移即被本文件测到, fsrs 真实参与。
    ⚠️ Codex round-1 MEDIUM 如实声明: bridge 是 symlink, 其 `_venv_python()`
    对 `__file__` 调 resolve() 会穿回 WT — re-exec 实际命中 **WT 的 venv**
    (与 fixture 同一解释器, 结果等价), tmp 的目录级 backend/.venv symlink
    **不参与** re-exec 选路 (保留它是为了 bridge 若改为 copy 布局仍可达,
    及文件级 symlink 会丢 pyvenv.cfg 的实测教训)。本 fixture 证明的是
    「bridge re-exec 链可达且 fsrs 真实参与」, 不是「tmp candidate 被选中」。
    """
    repo = tmp_path
    v = repo / "canvas-vault"
    (v / "节点").mkdir(parents=True)
    (v / ".claude" / "scripts").mkdir(parents=True)
    (repo / "backend" / "scripts").mkdir(parents=True)
    (repo / "backend" / ".venv").symlink_to(WT / "backend" / ".venv", target_is_directory=True)
    (repo / "backend" / "scripts" / "validate_learning_events.py").symlink_to(VALIDATOR)
    (v / ".claude" / "scripts" / "fsrs_bridge.py").symlink_to(VAULT_SCRIPTS / "fsrs_bridge.py")
    (v / ".claude" / "scripts" / "decay_beta.py").symlink_to(VAULT_SCRIPTS / "decay_beta.py")
    # 故意连字符+中文: 校验器绑定的是 sanitize 后的 canvas_vault_测试;
    # 写侧漏 sanitize (写原始形式) 会在 validator 绑定比对处翻红
    (v / ".canvas-config.yaml").write_text(
        '# 测试 config\nvault_id: "canvas-vault-测试"\nsubject: cs-61b\n', encoding="utf-8"
    )
    (v / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    return v


def _writer_code(vault: Path, payload: dict) -> str:
    pfile = vault.parent / "payload.json"
    pfile.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return CODE.replace('"/tmp/quiz-answer-payload.json"', json.dumps(str(pfile)))


def _run_writer(vault: Path, payload: dict, env_extra: dict | None = None):
    """生产形态执行: 子进程 + cwd=vault (NODE 相对路径与生产一致)。"""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **(env_extra or {}))
    return subprocess.run(
        [sys.executable, "-c", _writer_code(vault, payload)],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(vault),
        env=env,
    )


def _ledger_lines(vault: Path) -> list[dict]:
    ledger = vault / "learning_events.jsonl"
    if not ledger.exists():
        return []
    return [json.loads(ln) for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _fm(vault: Path) -> str:
    import yaml

    text = (vault / NODE_REL).read_text(encoding="utf-8")
    return text.split("---\n")[1]


def _fm_fields(vault: Path) -> dict:
    """按 bridge 同款正则抽 fsrs_* 行 (值+冒号后文本)。"""
    fm = _fm(vault)
    out = {}
    for key in ("fsrs_due", "fsrs_state", "fsrs_step", "fsrs_stability", "fsrs_difficulty", "fsrs_last_review"):
        m = re.search(rf"^{key}:\s*\"?([^\"\n]+?)\"?\s*$", fm, re.M)
        if m:
            out[key] = m.group(1)
    return out


def _run_validator(vault: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(vault / "learning_events.jsonl")],
        capture_output=True,
        text=True,
        timeout=60,
    )


def _sha(p: Path) -> str:
    import hashlib

    return hashlib.sha256(p.read_bytes()).hexdigest()


# ── 门① 同 event_id 重放两次 → frontmatter 不二次推进、账本一行 ──


def test_same_event_id_replay_no_double_advance(vault):
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    w1 = _fm_fields(vault)["fsrs_last_review"]
    ledger = vault / "learning_events.jsonl"
    n1 = len(_ledger_lines(vault))
    # 二跑: recorded_at 变化不构成事实差异 (envelope 显式排除), 必须 no-op
    r2 = _run_writer(vault, _payload(ts="2026-09-01T09:00:00Z"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == w1, "同 event_id 重放不得二次推进 W"
    assert len(_ledger_lines(vault)) == n1 == 1, "账本必须恰 1 行"
    assert "幂等跳过" in r2.stdout


# ── 门② 中断注入: 事件已落账、frontmatter 未推进 → A2 重放恢复 ──


def test_crash_window_ledger_without_frontmatter_recovers(vault):
    """卡文 (c)② 字面判据: 恢复产物与直接应用**逐字节相同** (round-2 HIGH:
    旧版只比 FSRS 子集; 现全部副作用 last_examined/calibration.ts 以 durable
    业务时刻为基准, 整节点字节对拍)。"""
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    golden_bytes = (vault / NODE_REL).read_bytes()
    # 模拟崩溃窗口①: 回滚 frontmatter 到评分前 (账本保留该事件)
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    r2 = _run_writer(vault, _payload(ts="2026-09-01T09:30:00Z"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert len(_ledger_lines(vault)) == 1, "恢复路径不得二次 append"
    assert (vault / NODE_REL).read_bytes() == golden_bytes, (
        "恢复产物必须与直接应用逐字节相同 (side effects 以 durable review_time 为基准)"
    )
    assert "A2 重放已应用" in r2.stdout or "崩溃窗口" in r2.stdout


# ── 门③ 追加即崩 (事件未落账) → 账本与 frontmatter 一致 (零写) ──


def test_fail_before_append_keeps_ledger_and_node_consistent(vault):
    """bridge exit 2 (naive ts) 在 append 之前 fail-closed — 系统保持评分前
    一致态, 重跑即可 (scored_pending_node_update 续跑语义)。"""
    sha_node, sha_ledger_before = _sha(vault / NODE_REL), None
    r = _run_writer(vault, _payload(ts="2026-08-01T10:00:00"))
    assert r.returncode != 0, "naive ts 必须拒绝"
    assert _sha(vault / NODE_REL) == sha_node, "fail-closed 必须零写节点"
    assert not (vault / "learning_events.jsonl").exists(), "fail-closed 必须零写账本"


# ── 门④ 等时 → W+1s (A3 推进口径) ──


def test_equal_timestamp_advances_w_plus_one_second(vault):
    (vault / NODE_REL).write_text(NODE_REVIEW_W10, encoding="utf-8")
    r = _run_writer(vault, _payload(ts="2026-08-01T10:00:00Z"))
    assert r.returncode == 0, r.stdout + r.stderr
    rec = _ledger_lines(vault)[0]
    assert rec["payload"]["review_time"] == "2026-08-01T10:00:01Z", "等时必须推进 W+1s"
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-01T10:00:01Z"
    assert rec["payload"]["review_time"] == rec["effective_at"], "review_time 与 effective_at 同一瞬间"
    assert _run_validator(vault).returncode == 0


# ── 门⑤ 小数秒输入 → 整秒 (A5) ──


def test_fractional_second_input_truncated_to_whole_second(vault):
    r = _run_writer(vault, _payload(ts="2026-08-01T10:00:00.731Z"))
    assert r.returncode == 0, r.stdout + r.stderr
    rec = _ledger_lines(vault)[0]
    assert rec["payload"]["review_time"] == "2026-08-01T10:00:00Z", "小数秒必须入口截断"
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-01T10:00:00Z"
    assert _run_validator(vault).returncode == 0, "整秒产物必须过校验器"


# ── 门⑥ 残缺卡 → fail-closed 零写 (裁决③) ──


def test_degraded_card_fail_closed_zero_write(vault):
    broken = NODE_V0.replace(
        "mastery_score: 0.5\n",
        "mastery_score: 0.5\nfsrs_last_review: 2026-08-01T10:00:00Z\n",
    )  # 只有 W 缺 due/state → classify degraded
    (vault / NODE_REL).write_text(broken, encoding="utf-8")
    sha = _sha(vault / NODE_REL)
    r = _run_writer(vault, _payload())
    assert r.returncode != 0, "残缺卡必须 fail-closed"
    assert "残缺" in r.stderr or "fail-closed" in r.stderr, r.stderr
    assert _sha(vault / NODE_REL) == sha, "残缺卡必须零写节点"
    assert not (vault / "learning_events.jsonl").exists(), "残缺卡必须零写账本"


# ── 门⑦ 截断尾行无 LF → 后续追加不粘连 (LF 守卫) ──


def test_truncated_tail_line_without_lf_guard(vault):
    """§二 截断自愈: 真实崩溃产物是 **半个 JSON** 且无尾 LF — 读取时跳过
    留痕, 追加前 LF 守卫隔离, 新事件必须独立可解析 (Codex round-1 HIGH:
    旧版只测「完整 JSON 缺 LF」, partial-JSON 在读取阶段就 fail-closed,
    自愈路径不可达)。"""
    ledger = vault / "learning_events.jsonl"
    full = json.dumps(
        {
            "event_id": "exam:旧板",
            "event_version": 1,
            "event_type": "exam_created",
            "node_id": "旧节点",
            "recorded_at": TS1,
            "effective_at": TS1,
            "payload": {"exam_board": "检验白板/旧板.md"},
        },
        ensure_ascii=False,
    )
    torn = '{"event_id": "quiz:被截断的事件", "event_version": 1, "event_ty'
    ledger.write_text(full + "\n" + torn, encoding="utf-8")  # 第二行为 partial JSON, 无尾 LF
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    assert "截断尾行" in r.stdout, "截断尾行必须留痕"
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 3, f"新事件必须独立成行 (LF 守卫隔离截断行), 实得 {len(lines)} 行"
    assert json.loads(lines[0])["event_id"] == "exam:旧板", "完整旧行必须原样保留"
    assert json.loads(lines[2])["event_id"] == "quiz:" + EID, "新事件行必须独立可解析"
    # 校验器如实把坏行报 FAIL (审计暴露损坏), 但坏行不连坐新行
    v = _run_validator(vault)
    assert v.returncode == 1 and "JSON 解析失败" in v.stdout, "坏行必须被校验器如实暴露"


# ── 门⑧ envelope 冲突 (同 id 不同 event_type) → 拒绝; 同 envelope → no-op ──


def test_envelope_conflict_rejected_and_same_envelope_noop(vault):
    # ①同 id 同 envelope: 完整成功后再跑, 绝不二次 apply (W 不动即证明)
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    sha = _sha(vault / NODE_REL)
    r2 = _run_writer(vault, _payload(ts="2026-09-01T08:00:00Z"))
    assert r2.returncode == 0
    assert _sha(vault / NODE_REL) == sha, "同 id 同 envelope 重放不得二次 apply"
    # ②同 id 不同事实 (abandoned 翻转 event_type) → fail-closed 拒写
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")  # 回到崩溃窗口①前置态
    r3 = _run_writer(vault, _payload(abandoned=True))
    assert r3.returncode != 0, "同 id 不同 event_type 必须 envelope 冲突拒绝"
    assert "envelope 冲突" in r3.stderr, r3.stderr
    assert len(_ledger_lines(vault)) == 1, "冲突拒绝不得追加"
    assert not _fm_fields(vault), "冲突拒绝不得推进 frontmatter"
    # ③Codex round-1 BLOCKER: 五字段局部比对抓不到的篡改 — durable 行被
    # 改动 payload 事实键 (exam_board) / 顶层 event_version 后, 恢复必须拒。
    base_event = _ledger_lines(vault)[0]
    for tweak, desc in (
        ({"payload.exam_board": "检验白板/被篡改.md"}, "payload 事实键 exam_board"),
        ({"event_version": 2}, "顶层 event_version"),
    ):
        tampered = json.loads(json.dumps(base_event))
        key, val = next(iter(tweak.items()))
        if "." in key:
            tampered["payload"][key.split(".")[1]] = val
        else:
            tampered[key] = val
        ledger = vault / "learning_events.jsonl"
        ledger.write_text(json.dumps(tampered, ensure_ascii=False) + "\n", encoding="utf-8")
        rt = _run_writer(vault, _payload())
        assert rt.returncode != 0, f"篡改 {desc} 后恢复必须拒绝"
        assert "envelope 冲突" in rt.stderr, rt.stderr
    # 恢复正常 durable 行后 (原样回写), 同一续跑必须成功 (崩溃窗口①恢复)
    (vault / "learning_events.jsonl").write_text(json.dumps(base_event, ensure_ascii=False) + "\n", encoding="utf-8")
    r4 = _run_writer(vault, _payload())
    assert r4.returncode == 0, r4.stdout + r4.stderr
    assert "恢复" in r4.stdout and "崩溃窗口" in r4.stdout


# ── 门⑨ 产物过校验器 (含 golden 绑定) + vault_id 规范化 ──


def test_ledger_passes_validator_with_golden_binding(vault):
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    v = _run_validator(vault)
    assert v.returncode == 0, v.stdout + v.stderr
    rec = _ledger_lines(vault)[0]
    pl = rec["payload"]
    assert pl["schema_ext"] == "review/1"
    assert pl["vault_id"] == "canvas_vault_测试", "vault_id 必须是 sanitize 规范化形式"
    assert pl["concept_id"] == rec["node_id"]
    assert pl["review_time"] == rec["effective_at"]
    # golden 绑定: 非 degraded 时与 manifest 真值相等 (校验器已查, 这里锁键存在)
    manifest = json.loads((WT / "backend" / "tests" / "regression" / "fsrs_golden_manifest.json").read_text())
    assert pl["fsrs_library_version"] == manifest["library_version"]
    assert pl["fsrs_params_hash"] == manifest["params_hash"]
    # rating 与 grade_norm 同源 (bridge rating_from_grade 口径, 档界 GN2=0.75→3)
    assert pl["rating"] == 3 and pl["grade_norm"] == 0.75
    assert _fm_fields(vault)["fsrs_last_review"] == pl["review_time"], "W 必须等于 review_time"


# ── 门⑩ 节点除 frontmatter 外 body 逐字节不变 ──


def test_node_body_byte_identical(vault):
    before = (vault / NODE_REL).read_text(encoding="utf-8")
    body_before = before.split("---\n", 2)[2]
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    after = (vault / NODE_REL).read_text(encoding="utf-8")
    body_after = after.split("---\n", 2)[2]
    assert body_after == body_before, "正文必须逐字节不变 (callout 为空时)"


# ── 门⑪ 全仓写点普查: 无第三套实现 ──


def test_write_point_survey_no_third_implementation():
    cmd = (
        "grep -rn 'learning_events.jsonl' backend/app canvas-vault/.claude "
        "--include='*.py' --include='*.md' | grep -v tests | cut -d: -f1 | sort -u"
    )
    r = subprocess.run(["bash", "-c", cmd], cwd=str(WT), capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    files = {ln for ln in r.stdout.strip().splitlines() if ln}
    assert files == {
        "backend/app/services/learning_event_log.py",
        "canvas-vault/.claude/skills/ai-linked-doc/SKILL.md",
        "canvas-vault/.claude/skills/quiz-answer/SKILL.md",
        "canvas-vault/.claude/skills/start-exam-board/SKILL.md",
    }, f"写点普查漂移 (新写点必须先登记 schema 文档 §五): {files}"


# ── 门⑫ 裁决② degraded: 事件仍落账 + 哨兵成对 + W 不推进 ──


def test_fsrs_unavailable_degraded_sentinels_pair_and_w_frozen(vault):
    """FSRS_BRIDGE_REEXEC=1 阻断 re-exec; bridge 子进程用系统 python3
    (无 fsrs, 本机实证) → 诚实 exit 3 → 裁决②路径。"""
    r = _run_writer(vault, _payload(), env_extra={"FSRS_BRIDGE_REEXEC": "1"})
    assert r.returncode == 0, r.stdout + r.stderr
    assert "degraded" in r.stdout
    rec = _ledger_lines(vault)[0]
    pl = rec["payload"]
    assert pl["fsrs_library_version"].startswith("degraded:"), "库版本必须填哨兵"
    assert pl["fsrs_params_hash"].startswith("degraded:"), "参数 hash 必须填哨兵"
    assert pl["fsrs_library_version"] == pl["fsrs_params_hash"], "两键哨兵必须成对 (同因)"
    assert pl["fsrs_library_version"][len("degraded:") :].strip(), "哨兵原因必须非空"
    assert not _fm_fields(vault), "degraded 不得写任何 fsrs_* 字段 (W 不推进)"
    assert "mastery_score" in _fm(vault), "衰减 Beta 照常写"
    assert _run_validator(vault).returncode == 0, "哨兵成对产物必须过校验器"
    # degraded 事件 review_time > W(无 W = -inf) → 留 pending; fsrs 恢复后
    # 下次评分的 A2 会自动补应用 (write-ahead 的价值, 产品可见)


# ── 门⑬ 耐久序列 + 写序 (A4.3/A4.4): spy 调用序列 ──
# ⚠️ 本门证明耐久序列**被调用** (fsync 覆盖账本/temp/父目录, append fsync 先于
# os.replace), 不证明掉电后数据存活 — 后者需真实断电, 不在本卡。


def test_durable_sequence_and_write_ahead_order(vault, monkeypatch):
    events: list[tuple] = []
    real_fsync, real_replace, real_open = os.fsync, os.replace, os.open

    def spy_fsync(fd):
        try:
            st = os.fstat(fd)
            kind = "dir" if stat.S_ISDIR(st.st_mode) else "file"
            events.append(("fsync", kind, st.st_ino))
        except OSError:
            events.append(("fsync", "unknown", -1))
        return real_fsync(fd)

    def spy_replace(src, dst):
        events.append(("replace", str(src), str(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(os, "fsync", spy_fsync)
    monkeypatch.setattr(os, "replace", spy_replace)
    monkeypatch.chdir(vault)
    saved_path = list(sys.path)
    saved_modules = {
        k: sys.modules.pop(k) for k in ("fsrs_bridge", "decay_beta", "validate_learning_events") if k in sys.modules
    }
    try:
        exec(compile(_writer_code(vault, _payload()), "quiz-answer-SKILL-extract", "exec"), {})
    except SystemExit as e:
        assert e.code in (0, None), f"静态块异常退出: {e.code}"
    finally:
        sys.path[:] = saved_path
        sys.modules.pop("fsrs_bridge", None)
        sys.modules.pop("decay_beta", None)
        sys.modules.pop("validate_learning_events", None)
        sys.modules.update(saved_modules)

    ledger, node = vault / "learning_events.jsonl", vault / NODE_REL
    ledger_ino, node_ino = ledger.stat().st_ino, node.stat().st_ino
    fsyncs = [e for e in events if e[0] == "fsync"]
    replaces = [e for e in events if e[0] == "replace"]
    assert len(replaces) == 1, f"恰一次原子发布, 实得 {len(replaces)}"
    replace_idx = events.index(replaces[0])
    # 账本 fsync (file) 与 temp fsync (temp inode == 发布后节点 inode)
    fsynced_files = {e[2] for e in fsyncs if e[1] == "file"}
    assert ledger_ino in fsynced_files, "账本 fd 必须 fsync (A4.3)"
    assert node_ino in fsynced_files, "temp fd 必须 fsync (A4.4; replace 保留 inode)"
    dir_count = sum(1 for e in fsyncs if e[1] == "dir")
    assert dir_count >= 2, f"首建账本父目录 + 节点父目录均须 fsync, 实得 dir fsync {dir_count} 次"
    # Codex round-1 验证限制: dir fsync 必须绑定两个**不同**目录 inode
    # (VAULT 根 = 账本父目录, 节点/ = 节点父目录), 不是同一目录刷两次
    dir_inodes = {e[2] for e in fsyncs if e[1] == "dir"}
    assert len(dir_inodes) >= 2, f"两个不同父目录都要 fsync, 实得 {len(dir_inodes)} 个 inode"
    assert vault.stat().st_ino in dir_inodes, "账本父目录 (VAULT 根) 必须 fsync"
    assert (vault / "节点").stat().st_ino in dir_inodes, "节点父目录必须 fsync"
    # 写序: 账本 durable 必须先于 os.replace (真 write-ahead, 非改名)
    ledger_fsync_idx = max(i for i, e in enumerate(events) if e[0] == "fsync" and e[1] == "file" and e[2] == ledger_ino)
    temp_fsync_idx = max(i for i, e in enumerate(events) if e[0] == "fsync" and e[1] == "file" and e[2] == node_ino)
    assert ledger_fsync_idx < replace_idx, "账本 fsync 必须先于 frontmatter 发布 (A1 write-ahead)"
    assert temp_fsync_idx < replace_idx, "temp fsync 必须先于 os.replace (A4.4)"


# ── 门⑭ 历史行 (无 review/1 扩展) 不进 pending (§6.3) ──


def test_legacy_rows_never_replayed(vault):
    legacy = json.dumps(
        {
            "event_id": "quiz:旧事件",
            "event_version": 1,
            "event_type": "answer_scored",
            "node_id": "测试节点",
            "recorded_at": "2026-07-01T10:00:00Z",
            "effective_at": "2026-07-01T10:00:00Z",
            "payload": {"grade_norm": 1.0, "exam_board": "x", "attempt_count": 1},
        },
        ensure_ascii=False,
    )
    (vault / "learning_events.jsonl").write_text(legacy + "\n", encoding="utf-8")
    r = _run_writer(vault, _payload(ts="2026-08-02T10:00:00Z"))
    assert r.returncode == 0, r.stdout + r.stderr
    # 无 fsrs_* 字段的新卡: 旧事件不可重放 (无 review_time, 视为已应用),
    # W 恰为新事件时刻 — 若旧行被误重放 W 会先落到 2026-07-01
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-02T10:00:00Z"
    assert len(_ledger_lines(vault)) == 2
    assert _run_validator(vault).returncode == 0


# ── 门⑮ 跨事件 A2: 别的事件落账未应用 → 本次评分前重放至空 ──


def test_pending_foreign_event_replayed_before_new_write(vault):
    """run1 为事件 A 落账未应用 (崩溃), run2 换一张板考同一节点 (事件 B):
    A2 必须先重放 A 再计算 B — 单写者下交错窗口由 A2 消灭。"""
    event_a = {
        "event_id": "quiz:板A#q1",
        "event_version": 1,
        "event_type": "answer_scored",
        "node_id": "测试节点",
        "recorded_at": TS1,
        "effective_at": TS1,
        "payload": {
            "schema_ext": "review/1",
            "vault_id": "canvas_vault_测试",
            "concept_id": "测试节点",
            "rating": 3,
            "grade_norm": 0.75,
            "review_time": TS1,
            "fsrs_library_version": "degraded:historic-run",  # 哨兵行
            "fsrs_params_hash": "degraded:historic-run",
            "exam_board": "检验白板/板A.md",
            "attempt_count": 1,
        },
    }
    (vault / "learning_events.jsonl").write_text(json.dumps(event_a, ensure_ascii=False) + "\n", encoding="utf-8")
    r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z", exam_board="检验白板/板B.md"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "A2 重放已应用" in r.stdout, "事件 A 必须在本次写入前被重放"
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-02T10:00:00Z", "W 反映 B"
    recs = _ledger_lines(vault)
    assert [x["event_id"] for x in recs] == ["quiz:板A#q1", "quiz:板B#q1"]
    assert _run_validator(vault).returncode == 0
    # A2 重放 A 后 W=TS1; 若跳过重放直接算 B, B 会从新卡基线出发 — 与正确
    # 基线 (A 已应用) 的 FSRS 六字段必然不同; 对拍 bridge 直调两次的结果:
    sys.path.insert(0, str(VAULT_SCRIPTS))
    try:
        import fsrs_bridge as fb

        base = fb.review({}, 0.75, False, TS1)  # A (rating 3)
        got = _fm_fields(vault)
        expect2 = fb.review({k: v for k, v in base.items() if k != "fm_block"}, 0.75, False, "2026-08-02T10:00:00Z")
        assert float(got["fsrs_stability"]) == expect2["fsrs_stability"], (
            f"A2 重放未生效或基线错: {got['fsrs_stability']} != {expect2['fsrs_stability']}"
        )
    finally:
        sys.path.remove(str(VAULT_SCRIPTS))
        sys.modules.pop("fsrs_bridge", None)


# ── 门⑯ 子串查重陷阱: payload 文本含 JSON 串形不得误判 duplicate ──
# Codex round-1 MEDIUM: 中文 EID + 转义 note 形态下旧子串谓词实测不命中
# (杀不掉旧实现) — 陷阱必须用 ASCII event_id 且 payload 字段值**直接等于**
# 该 event_id 文本, 让 `json.dumps(eid) in line` (旧实现) 确定命中。

TRAP_EID = "trap-eid-123"


def test_substring_dedup_trap(vault):
    """A4.5 parsed-field equality: 预置行的 payload 文本里恰好含
    `"quiz:<新eid>"` 的 JSON 串形时, 子串查重会误判 duplicate 而**零次落账**
    (旧实现的真实缺陷, schema §九登记)。正确行为 = 正常追加第 2 行。
    陷阱载体 = payload **键名** (键名引号不被 JSON 转义, 值内引号恒转义为
    \\" 导致 needle 尾引号匹配不上 — 首版陷阱因此被验伪断言自己抓出)。
    验伪: 该陷阱对旧子串谓词 `json.dumps(evid) in line` 必须命中。"""
    trap_needle = json.dumps("quiz:" + TRAP_EID, ensure_ascii=False)  # "quiz:trap-eid-123"
    other = {
        "event_id": "quiz:另一事件",
        "event_version": 1,
        "event_type": "answer_scored",
        "node_id": "测试节点",
        "recorded_at": TS1,
        "effective_at": TS1,
        "payload": {"quiz:" + TRAP_EID: "字段名恰好等于新事件 id 的 JSON 串形"},  # 不含 schema_ext
    }
    line_text = json.dumps(other, ensure_ascii=False)
    assert trap_needle in line_text, "陷阱行必须真的命中旧子串谓词 (否则本门为假门)"
    (vault / "learning_events.jsonl").write_text(line_text + "\n", encoding="utf-8")
    r = _run_writer(vault, _payload(event_id=TRAP_EID))
    assert r.returncode == 0, r.stdout + r.stderr
    recs = _ledger_lines(vault)
    assert len(recs) == 2, f"parsed 查重不得被子串误判, 实得 {len(recs)} 行: {[x['event_id'] for x in recs]}"
    assert recs[1]["event_id"] == "quiz:" + TRAP_EID


# ── 门⑰ A2 重放失败 → 一律 fail-closed 零写 (Codex round-1 BLOCKER) ──


def test_pending_replay_failure_blocks_everything(vault):
    """存在 pending 且重放失败 (fsrs 不可用) 时: 既不 degraded 落账、也不
    发布 frontmatter — A2 「追加前重放至空」无例外。"""
    event_a = {
        "event_id": "quiz:板A#q1",
        "event_version": 1,
        "event_type": "answer_scored",
        "node_id": "测试节点",
        "recorded_at": TS1,
        "effective_at": TS1,
        "payload": {
            "schema_ext": "review/1",
            "vault_id": "canvas_vault_测试",
            "concept_id": "测试节点",
            "rating": 3,
            "grade_norm": 0.75,
            "review_time": TS1,
            "fsrs_library_version": "degraded:historic-run",
            "fsrs_params_hash": "degraded:historic-run",
            "exam_board": "检验白板/板A.md",
            "attempt_count": 1,
        },
    }
    (vault / "learning_events.jsonl").write_text(json.dumps(event_a, ensure_ascii=False) + "\n", encoding="utf-8")
    sha = _sha(vault / NODE_REL)
    r = _run_writer(
        vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"), env_extra={"FSRS_BRIDGE_REEXEC": "1"}
    )
    assert r.returncode != 0, "pending 重放失败必须 fail-closed"
    assert "重放失败" in r.stderr, r.stderr
    assert _sha(vault / NODE_REL) == sha, "零写节点"
    assert len(_ledger_lines(vault)) == 1, "零写账本 (不得 degraded 追加)"
    # 变体: pending 行 rating 非法 (float 1.5) → bridge 严格 int 拒 → 同 fail-closed
    bad_rating = json.loads(json.dumps(event_a))
    bad_rating["payload"]["rating"] = 1.5
    (vault / "learning_events.jsonl").write_text(json.dumps(bad_rating, ensure_ascii=False) + "\n", encoding="utf-8")
    r2 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r2.returncode != 0, "非法 rating 的 pending 行必须被 bridge 拒绝并 fail-closed"
    assert len(_ledger_lines(vault)) == 1
    # 变体 (round-2 HIGH): abandoned 行 rating=1.5 — abandoned 分支不得绕过类型门
    bad_ab = json.loads(json.dumps(event_a))
    bad_ab["event_type"] = "answer_abandoned"
    bad_ab["payload"]["rating"] = 1.5
    (vault / "learning_events.jsonl").write_text(json.dumps(bad_ab, ensure_ascii=False) + "\n", encoding="utf-8")
    r3 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r3.returncode != 0, "abandoned 行的非法 rating 同样必须被拒"
    # 变体 (round-2 HIGH 自洽): abandoned 行 rating=3 (类型合法但弃答恒 1)
    bad_ab2 = json.loads(json.dumps(bad_ab))
    bad_ab2["payload"]["rating"] = 3
    (vault / "learning_events.jsonl").write_text(json.dumps(bad_ab2, ensure_ascii=False) + "\n", encoding="utf-8")
    r4 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r4.returncode != 0, "abandoned=true 且 rating!=1 必须拒绝 (弃答一票否决)"
    assert len(_ledger_lines(vault)) == 1


# ── 门⑱ degraded 本地 A3 推进的 A7 上界 (Codex round-1 HIGH) ──


def test_degraded_a3_bump_respects_a7_bound(vault):
    """W=8999-12-31T23:59:59Z + fsrs 不可用 + 同秒评分: 本地 W+1s 会推出
    9000-01-01 (A7 排他上界) — 必须零写退出, 不制造非法孤儿事件。"""
    edge = NODE_V0.replace(
        "mastery_score: 0.5\n",
        "mastery_score: 0.5\nfsrs_due: 8999-12-31T23:59:59Z\nfsrs_state: 2\n"
        "fsrs_stability: 10.0\nfsrs_difficulty: 5.0\nfsrs_last_review: 8999-12-31T23:59:59Z\n",
    )
    (vault / NODE_REL).write_text(edge, encoding="utf-8")
    sha = _sha(vault / NODE_REL)
    r = _run_writer(vault, _payload(ts="8999-12-31T23:59:59Z"), env_extra={"FSRS_BRIDGE_REEXEC": "1"})
    assert r.returncode != 0, "A7 上界越界必须 fail-closed"
    assert "A7" in r.stderr, r.stderr
    assert _sha(vault / NODE_REL) == sha, "零写节点"
    assert not (vault / "learning_events.jsonl").exists(), "零写账本"


# ── 门⑲ F1 判定在 Obsidian 规范化形态下仍命中 (live 实证: 引号会被剥掉) ──


def test_f1_detection_survives_obsidian_renormalization(vault):
    """live 实证: Obsidian Properties 面板会把 calibration_log 的引号值规范化
    成裸词形态 — 旧守卫 `json.dumps(eid) in fm` 因此恒不命中 (假幂等)。
    解析层 F1 判定必须在裸词形态下同样命中。"""
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    # 模拟 Obsidian 规范化: 引号值 → 裸词
    text = (vault / NODE_REL).read_text(encoding="utf-8")
    normalized = text.replace('event_id: "测试检验-2026-08-01-1000#q1"', "event_id: 测试检验-2026-08-01-1000#q1")
    assert normalized != text, "fixture 预置必须与规范化形态可区分"
    (vault / NODE_REL).write_text(normalized, encoding="utf-8")
    sha = _sha(vault / NODE_REL)
    r2 = _run_writer(vault, _payload(ts="2026-09-01T07:00:00Z"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "幂等跳过" in r2.stdout, "裸词形态的 calibration_log 必须仍被解析层 F1 命中"
    assert _sha(vault / NODE_REL) == sha, "规范化形态重跑必须零写"
    assert len(_ledger_lines(vault)) == 1


# ── 门⑳ append_event 的 LF 守卫 (Codex round-1 HIGH: 坏尾行连坐新行) ──


def test_append_event_lf_guard_isolates_torn_tail(monkeypatch, tmp_path):
    """backend append_event 在 partial-JSON 无 LF 尾行后追加: 新行必须独立
    可解析、函数返回 True (新行确实落盘) — 不得把两个 JSON 粘成一行。"""
    from app.services import learning_event_log as ev

    ledger = tmp_path / "learning_events.jsonl"
    monkeypatch.setattr(ev, "_log_path", lambda: ledger)
    ledger.write_text('{"event_id": "quiz:被截断", "event_vers', encoding="utf-8")  # partial, 无 LF
    assert ev.append_event("answer_scored", event_id="quiz:fresh-1")
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 2, f"新行必须独立成行, 实得 {len(lines)} 行"
    assert json.loads(lines[1])["event_id"] == "quiz:fresh-1"
    assert ev.append_event("answer_scored", event_id="quiz:fresh-1") is False  # 幂等不因守卫破坏
    # 变体 (round-2 HIGH): 零字节空文件首写 — seek(-1) 守卫必须跳过, 不能炸
    empty = tmp_path / "empty" / "learning_events.jsonl"
    empty.parent.mkdir(parents=True)
    empty.write_text("", encoding="utf-8")
    monkeypatch.setattr(ev, "_log_path", lambda: empty)
    assert ev.append_event("answer_scored", event_id="quiz:first-in-empty"), "空文件首写必须成功"
    assert json.loads(empty.read_text(encoding="utf-8").strip())["event_id"] == "quiz:first-in-empty"


# ── 门㉑ degraded 遗留重试 (round-2 B-1②): F1=T 但 W 未推进 → 恢复只补 FSRS ──


def test_degraded_legacy_retry_restores_fsrs_without_double_ema(vault):
    """首评 fsrs 不可用 → 事件落账(哨兵)+EMA/校准已应用+W 未推进。fsrs 恢复后
    同 ID 重试必须: 补齐 FSRS、**不再吃一次 EMA**、账本仍 1 行。"""
    r1 = _run_writer(vault, _payload(), env_extra={"FSRS_BRIDGE_REEXEC": "1"})
    assert r1.returncode == 0, r1.stdout + r1.stderr
    ema_after_degraded = _fm(vault)
    assert not _fm_fields(vault), "degraded 后 W 必须未推进"
    # fsrs 恢复 (不加 REEXEC env) → 同 ID 重试
    r2 = _run_writer(vault, _payload(ts="2026-09-01T06:00:00Z"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "degraded 遗留" in r2.stdout, r2.stdout + r2.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-01T10:00:00Z", "FSRS 必须补齐推进"
    fm_now = _fm(vault)
    for key in ("mastery_score", "mastery_a", "mastery_b"):
        assert re.search(rf"^{key}:.*", fm_now, re.M).group(0) == re.search(
            rf"^{key}:.*", ema_after_degraded, re.M
        ).group(0), f"{key} 不得二次吸收成绩 (EMA 双吃)"
    assert len(_ledger_lines(vault)) == 1, "恢复不得二次 append"
    assert _run_validator(vault).returncode == 0


# ── 门㉒ 已完整应用 + 冲突事实 → 拒 (round-2 B-1①: F1 不得吞冲突) ──


def test_conflicting_facts_after_full_apply_rejected(vault):
    r1 = _run_writer(vault, _payload())
    assert r1.returncode == 0
    sha = _sha(vault / NODE_REL)
    # 完整应用态 (不回滚 frontmatter) 直接换事实重跑 → envelope 冲突拒绝
    r2 = _run_writer(vault, _payload(abandoned=True))
    assert r2.returncode != 0, "已应用态的冲突事实必须拒绝 (F1 不得吞)"
    assert "envelope 冲突" in r2.stderr
    assert _sha(vault / NODE_REL) == sha and len(_ledger_lines(vault)) == 1


# ── 门㉓ 账本 event_id 重复 → fail-closed (round-2 B-3: 双 pending 行会二次 apply) ──


def test_duplicate_event_id_in_ledger_fail_closed(vault):
    ev_row = json.dumps(
        {
            "event_id": "quiz:重复行",
            "event_version": 1,
            "event_type": "answer_scored",
            "node_id": "测试节点",
            "recorded_at": TS1,
            "effective_at": TS1,
            "payload": {
                "schema_ext": "review/1",
                "vault_id": "canvas_vault_测试",
                "concept_id": "测试节点",
                "rating": 3,
                "grade_norm": 0.75,
                "review_time": TS1,
                "fsrs_library_version": "degraded:x",
                "fsrs_params_hash": "degraded:x",
                "exam_board": "x",
                "attempt_count": 1,
            },
        },
        ensure_ascii=False,
    )
    (vault / "learning_events.jsonl").write_text(ev_row + "\n" + ev_row + "\n", encoding="utf-8")
    r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r.returncode != 0, "全文件 event_id 重复必须 fail-closed (A2 会双 apply)"
    assert "event_id 重复" in r.stderr, r.stderr
    assert not _fm_fields(vault), "零写节点"


# ── 门㉔ 含转义引号的 event_id 幂等 (round-2 HIGH: F1 读取须同源反解) ──


def test_f1_detection_handles_escaped_quotes(vault):
    eid_quoted = '板"引号#q1'
    r = _run_writer(vault, _payload(event_id=eid_quoted))
    assert r.returncode == 0, r.stdout + r.stderr
    # 写侧 json.dumps 落盘为转义形态: event_id: "板\"引号#q1"
    text = (vault / NODE_REL).read_text(encoding="utf-8")
    assert '\\"' in text, "fixture 预置应含转义引号形态"
    sha = _sha(vault / NODE_REL)
    r2 = _run_writer(vault, _payload(event_id=eid_quoted, ts="2026-09-01T05:00:00Z"))
    assert r2.returncode == 0 and "幂等跳过" in r2.stdout, "转义引号 eid 必须经同源反解命中 F1"
    assert _sha(vault / NODE_REL) == sha, "不得重复副作用 (attempt/calibration)"


# ── 门㉕ fsrs 身份键篡改 → envelope 放行 + validator 拦 (分层防线声明) ──


def test_identity_tampering_caught_by_validator_not_envelope(vault):
    """fsrs_library_version/params_hash 是环境快照, 排除在 envelope 等价面外
    (验收单声明); 其完整性由校验器 golden 绑定门承担 — 本门锁这个分层。"""
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    base = _ledger_lines(vault)[0]
    # 回滚 frontmatter → 崩溃窗口① + 身份键被篡改的 durable 行
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    tampered = json.loads(json.dumps(base))
    tampered["payload"]["fsrs_library_version"] = "tampered-library"
    (vault / "learning_events.jsonl").write_text(json.dumps(tampered, ensure_ascii=False) + "\n", encoding="utf-8")
    r2 = _run_writer(vault, _payload())
    assert r2.returncode == 0, "身份键不在 envelope 等价面 (恢复照常)"
    assert _run_validator(vault).returncode == 1, "但被篡改的身份必须被校验器拦下"
