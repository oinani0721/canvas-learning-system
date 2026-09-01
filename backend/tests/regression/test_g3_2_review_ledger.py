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


#: R4 字节对拍用: canonical Review 态 + last_examined + W **远晚于**本次评分
#: 时刻 ⇒ A3 把 review_time 推到 W+1s (与 payload ts 差 4 个月)。含 idle 状态
#: 才能让 mastery 的闲置折旧基准差异显形 (门②的新卡无 last_examined, 测不到)。
NODE_IDLE_A3 = (
    "---\n"
    "type: concept\n"
    "mastery_score: 0.5\n"
    "mastery_a: 3.0\n"
    "mastery_b: 3.0\n"
    "attempt_count: 2\n"
    'last_examined: "2026-07-01T00:00:00Z"\n'
    "fsrs_due: 2026-12-11T13:56:58Z\n"
    "fsrs_state: 2\n"
    "fsrs_stability: 10.0\n"
    "fsrs_difficulty: 5.0\n"
    "fsrs_last_review: 2026-12-01T10:00:00Z\n"
    "title: 测试节点\n"
    "---\n"
    "测试节点正文。\n"
)


def _review_row(**over):
    """一条 canonical review/1 durable 行 (与生产写点键集逐字同形)。"""
    row = {
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
    for k, v in over.items():
        if k.startswith("payload."):
            row["payload"][k.split(".", 1)[1]] = v
        else:
            row[k] = v
    return row


def _write_ledger(vault: Path, *rows, trailing_lf=True):
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    if not trailing_lf and text.endswith("\n"):
        text = text[:-1]
    (vault / "learning_events.jsonl").write_text(text, encoding="utf-8")


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


def _run_writer_settled(vault: Path, payload: dict, env_extra: dict | None = None):
    """跑写点；若因「A2 恢复先落定」被要求重跑，就再跑一次并返回合并结果。

    存在 foreign pending 时写点会先把恢复结果原子发布、再以非零码退出要求重跑
    （Codex round-3 BLOCKER 的修法：恢复与新写不在同一次运行里混做，否则被恢复
    事件的 mastery/校准会连同「多 pending 攒在一起」一起变得不可证）。
    只关心「最终有没有写成」的门用这个；专门验证两阶段语义的门直接用 _run_writer。
    """
    r = _run_writer(vault, payload, env_extra)
    if r.returncode != 0 and "恢复已落定" in r.stderr:
        r2 = _run_writer(vault, payload, env_extra)
        return subprocess.CompletedProcess(r2.args, r2.returncode, r.stdout + r2.stdout, r.stderr + r2.stderr)
    return r


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
        # event_version 篡改现被更早的**版本门**接管（未知版本不得按 v1 应用，
        # 也不能跳过——跳过就漏算了）；payload 事实键仍走 envelope。
        assert ("envelope 冲突" in rt.stderr) or ("非 v1" in rt.stderr), rt.stderr
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
    # 两阶段（Codex round-3 BLOCKER 的修法）：第一次跑只把 A 的恢复结果原子
    # 发布下去并要求重跑；第二次跑 pending 已空，B 在干净基线上写入。
    r0 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z", exam_board="检验白板/板B.md"))
    assert r0.returncode != 0, "存在 foreign pending 时不得在同一次运行里既恢复又追加"
    assert "A2 重放已应用" in r0.stdout, "事件 A 必须被重放"
    assert "恢复已落定" in r0.stderr, r0.stderr
    assert "永久丢失" in r0.stdout, "被恢复事件的 mastery/校准无法复放，必须如实告知"
    assert _fm_fields(vault)["fsrs_last_review"] == TS1, "恢复结果必须已落盘（W = A 的时刻）"
    assert len(_ledger_lines(vault)) == 1, "第一阶段不得追加本次事件"
    r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z", exam_board="检验白板/板B.md"))
    assert r.returncode == 0, r.stdout + r.stderr
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


# ══ CARD-G3-2b: Codex round-3 残留 R1-R7 的生产入口反例门 (㉖-㉜) ══
# 全部用**逐字提取的生产 PYEOF 块**驱动 (CODE), 反例态由账本/节点预置构造 —
# 测试内不重写任何一套判定逻辑。


# ── 门㉖ R1 (BLOCKER): durable payload 的未知额外键必须冲突, 不得被自抄放行 ──


def test_r1_unknown_durable_payload_key_conflicts(vault):
    """旧实现的 candidate 以 durable payload 为底 spread (`{**_dpl, ...}`),
    未知额外键被原样抄进 candidate ⇒ 比较退化成「自己比自己」。
    实测穿透链: 给崩溃窗口①的 durable 行加 payload.out_of_order=true →
    envelope 放行, 而 A2 适用集按定义排除该行 ⇒ FSRS 永不应用, writer 仍
    rc=0 写下 calibration/mastery, 节点 fsrs_* 全空、账本仍一行。
    正确行为: 键集本身是等价面的一部分 — 多一键/少一键一律冲突。"""
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    base = _ledger_lines(vault)[0]
    # ⚠️ round-1 后续: `out_of_order` 现被更早的语义门接管 (见门㉞ N1) —— 只有
    # **合法乱序形态**(review_time ≤ W) 的该键才会走到 envelope 门。这里保 W
    # 不回滚地测它, 保证 R1 的原始穿透链仍被本门覆盖: 本次评分事实里没有这个
    # 键, 键集不等即冲突。
    base_oo = json.loads(json.dumps(base))
    base_oo["payload"]["out_of_order"] = True  # review_time == W ⇒ 合法乱序
    _write_ledger(vault, base_oo)
    r_oo = _run_writer(vault, _payload(ts="2026-09-01T07:00:00Z"))
    assert r_oo.returncode != 0, "合法乱序形态的 out_of_order 键仍须 envelope 冲突"
    assert "envelope 冲突" in r_oo.stderr, r_oo.stderr
    assert len(_ledger_lines(vault)) == 1
    for tweak, desc in (
        ({"note": "外部工具注入的备注"}, "任意未知额外键"),
        ({"vault_id": "canvas_vault_测试", "extra_nested": {"a": 1}}, "未知嵌套键"),
    ):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")  # 回到崩溃窗口①前置态
        tampered = json.loads(json.dumps(base))
        tampered["payload"].update(tweak)
        _write_ledger(vault, tampered)
        rt = _run_writer(vault, _payload())
        assert rt.returncode != 0, f"{desc}: 必须 envelope 冲突 (旧实现 rc=0 且 fsrs_* 全空)"
        assert "envelope 冲突" in rt.stderr, rt.stderr
        assert not _fm_fields(vault), f"{desc}: 冲突拒绝不得推进 frontmatter"
        assert len(_ledger_lines(vault)) == 1, f"{desc}: 冲突拒绝不得追加"
    # 反向: durable 行**缺**一个固定生产键 — 旧实现会被 candidate 的覆盖补回,
    # 同样穿透。少键必须与多键同等冲突。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    short = json.loads(json.dumps(base))
    short["payload"].pop("exam_board")
    _write_ledger(vault, short)
    rs = _run_writer(vault, _payload())
    assert rs.returncode != 0 and "envelope 冲突" in rs.stderr, rs.stderr
    # 对照 (验伪): 原样 durable 行必须照常恢复 — 本门不是「恒拒」的假门
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    _write_ledger(vault, base)
    rok = _run_writer(vault, _payload())
    assert rok.returncode == 0, rok.stdout + rok.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == TS1, "未被篡改的 durable 行必须正常恢复"


# ── 门㉗ R2 (BLOCKER): 小数秒 / 非 UTC durable review_time 不得被消费 ──


def test_r2_non_whole_second_durable_review_time_fail_closed(vault):
    """bridge 入口 _whole_second 会把 10:00:00.500Z 截成 10:00:00Z 写进 W,
    而账本那行仍是 .500Z ⇒ 「.500 > .000」恒真, 同一行**每次重跑都判 pending
    并再推进一次 FSRS** (实测: 账本始终一行, W 逐次 +1s = §6.2 A5 禁止的二次
    apply)。修复方向必须是 apply 前只验不改 — 消费时归一化会把损坏行洗成
    合法行, 把缺陷从写入面挪进不可见面。"""
    # 判据必须落在**字面**上, 不是解析后的值 (自查补): '.000000Z' 的
    # microsecond 恰为 0, 只看值会放行它, 而校验器的 _WHOLE_SECOND_RE 按字面
    # 判 FAIL ⇒ 写点放行、validator 拒, 实现与契约又成两个口径。
    for rt_bad, why in (
        ("2026-08-01T10:00:00.500Z", "小数秒"),
        ("2026-08-01T10:00:00.000000Z", "小数秒"),  # 零值小数秒字面: 值合规、字面不合规
        ("2026-08-01T10:00:00.0Z", "小数秒"),
        ("2026-08-01T10:00:00+00:00:00", "小数秒"),  # 非 canonical 偏移字面
        ("2026-08-01T10:00+00:00", "小数秒"),  # 省略秒段 (§6.2 round-4 HIGH#1)
        ("2026-08-01T18:00:00+08:00", "非 UTC"),  # 字面合规但偏移非零
    ):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        _write_ledger(vault, _review_row(**{"payload.review_time": rt_bad, "effective_at": rt_bad}))
        sha = _sha(vault / NODE_REL)
        # ①该行即本次事件 (dup 路径)
        r = _run_writer(vault, _payload(event_id="板A#q1"))
        assert r.returncode != 0, f"{why} durable 行 (dup 路径) 必须 fail-closed"
        assert why in r.stderr, r.stderr
        assert _sha(vault / NODE_REL) == sha and len(_ledger_lines(vault)) == 1, "零写"
        # ②该行是别的事件 (foreign pending 路径) — 同样在重放前拒
        r2 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert r2.returncode != 0, f"{why} durable 行 (foreign pending 路径) 必须 fail-closed"
        assert why in r2.stderr, r2.stderr
        assert _sha(vault / NODE_REL) == sha and len(_ledger_lines(vault)) == 1, "零写"
    # 对照 (验伪): 整秒 UTC 的两种 canonical 字面都必须照常重放 —— 本门不是
    # 「凡带偏移就拒」的假门, Z 与 +00:00 是同一瞬间的两种合法写法。
    for rt_ok in ("2026-08-01T10:00:00Z", "2026-08-01T10:00:00+00:00"):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        _write_ledger(vault, _review_row(**{"payload.review_time": rt_ok, "effective_at": rt_ok}))
        rok = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rok.returncode == 0, f"{rt_ok} 必须照常重放: " + rok.stdout + rok.stderr
        assert "A2 重放已应用" in rok.stdout


# ── 门㉘ R3 (HIGH): 历史事件重跑 (E1→E2→重跑 E1) 必须 no-op, 不得误报冲突 ──


def test_r3_historical_event_replay_is_noop_not_conflict(vault):
    """§6.2:187 要求同 canonical envelope 必须 no-op。旧实现的 attempt 复算
    在已应用态直接取 frontmatter 当前值 (tip), 于是重跑 E1 时把 E2 的计数当
    成 E1 的 ⇒ 合法历史重放被误报 envelope 冲突 (用户翻旧检验白板重跑旧评分
    即触发)。正确口径: 沿账本回推 ordinal。"""
    r1 = _run_writer(vault, _payload())  # E1 @ 10:00
    assert r1.returncode == 0, r1.stdout + r1.stderr
    r2 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z", exam_board="检验白板/板B.md"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    recs = _ledger_lines(vault)
    assert [x["payload"]["attempt_count"] for x in recs] == [1, 2], "durable attempts 应为 [1,2]"
    assert re.search(r"^attempt_count:\s*(\d+)", _fm(vault), re.M).group(1) == "2"
    sha = _sha(vault / NODE_REL)
    # 原样重跑 E1 (仅 recorded_at 变化 — envelope 显式排除)
    r3 = _run_writer(vault, _payload(ts="2026-09-01T12:00:00Z"))
    assert r3.returncode == 0, "历史事件原样重跑必须 no-op, 不得报冲突: " + r3.stdout + r3.stderr
    assert "幂等跳过" in r3.stdout, r3.stdout
    assert _sha(vault / NODE_REL) == sha, "no-op 不得改动节点"
    assert len(_ledger_lines(vault)) == 2, "no-op 不得追加"
    # 验伪: 同一历史事件**换事实**重跑仍必须冲突 (本门不是「恒放行」的假门)
    r4 = _run_writer(vault, _payload(ts="2026-09-01T12:00:00Z", abandoned=True))
    assert r4.returncode != 0 and "envelope 冲突" in r4.stderr, r4.stderr


# ── 门㉙ R4 (HIGH): 含 idle 状态且触发 A3 时, 正常与恢复产物逐字节相同 ──


def test_r4_recovery_byte_identical_with_idle_and_a3_bump(vault):
    """卡文 (d)。旧实现正常路径的 mastery 闲置折旧基准用 payload ts, 恢复路径
    用 durable review_time — 门②的新卡无 last_examined, days_idle 恒 0, 测不
    出差异。本门的节点 W=2026-12-01 远晚于评分时刻 2026-08-01 ⇒ A3 把
    review_time 推到 W+1s, 两个基准相差约 4 个月, mastery_a/b 与整节点 SHA
    必然分叉 (round-3 实测两次 SHA 不同)。"""
    (vault / NODE_REL).write_text(NODE_IDLE_A3, encoding="utf-8")
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    golden = (vault / NODE_REL).read_bytes()
    rec = _ledger_lines(vault)[0]
    assert rec["payload"]["review_time"] == "2026-12-01T10:00:01Z", (
        "fixture 前提: A3 必须把 review_time 推到 W+1s, 实为 " + rec["payload"]["review_time"]
    )
    assert rec["payload"]["review_time"] != TS1, "fixture 前提: review_time 必须 != payload ts"
    # 崩溃窗口①: 回滚 frontmatter 到评分前 (账本保留该事件) → 恢复路径
    (vault / NODE_REL).write_text(NODE_IDLE_A3, encoding="utf-8")
    r2 = _run_writer(vault, _payload(ts="2026-09-15T09:30:00Z"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert len(_ledger_lines(vault)) == 1, "恢复路径不得二次 append"
    assert (vault / NODE_REL).read_bytes() == golden, "含 idle 状态 + A3 bump 时, 恢复产物必须与直接应用逐字节相同"


# ── 门㉚ R5 (HIGH): scored rating 与 grade_norm 不自洽 → apply 前拒绝 ──


def test_r5_inconsistent_scored_rating_rejected_before_apply(vault):
    """answer_scored + grade_norm=0.75 + rating=4: 类型 int、范围 1-4 都合法,
    但 [Decision-FSRS-1] 下 0.75 的契约值是 3。旧实现照单全收 — writer rc=0、
    输出「A2 重放已应用」并追加下一事件, 事后才由 validator 判 rc=1 (损坏基线
    上已叠加一次真实调度)。必须在 apply 前拒绝。"""
    sha = _sha(vault / NODE_REL)
    for bad_rating in (4, 2, 1):
        _write_ledger(vault, _review_row(**{"payload.rating": bad_rating}))
        r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert r.returncode != 0, f"rating={bad_rating} 与 grade_norm=0.75 不自洽, 必须 apply 前拒绝"
        assert "不自洽" in r.stderr, r.stderr
        assert _sha(vault / NODE_REL) == sha, "零写节点"
        assert len(_ledger_lines(vault)) == 1, "零写账本 (不得追加下一事件)"
    # 验伪: 契约值 3 必须照常重放 (本门不是「恒拒」的假门)
    _write_ledger(vault, _review_row())
    rok = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert rok.returncode == 0, rok.stdout + rok.stderr
    assert len(_ledger_lines(vault)) == 2


# ── 门㉛ R7 (MEDIUM): 带终止 LF 的坏末行 = 完整损坏, 不是截断 ──


def test_r7_corrupt_tail_line_with_lf_is_not_truncation(vault):
    """旧实现只看「最后一行解析失败」, 于是**带终止 LF** 的损坏末行也被当
    截断容忍 — 实测 writer 仍 rc=0、自称「截断尾行」、继续追加并推进节点。
    EOF 的 LF 状态是区分「被腰斩的半行」与「完整写入后损坏」的唯一机械证据。"""
    good = _review_row(event_id="quiz:旧板", **{"payload.review_time": "2026-07-01T10:00:00Z"})
    good["effective_at"] = "2026-07-01T10:00:00Z"
    good["node_id"] = "别的节点"  # 不进本节点适用集, 隔离本门的判定面
    bad = '{"event_id": "quiz:损坏行", "event_version": 1, "event_type": "answer_sc'
    ledger = vault / "learning_events.jsonl"
    # ①带终止 LF 的坏末行 → fail-closed 零写
    ledger.write_text(json.dumps(good, ensure_ascii=False) + "\n" + bad + "\n", encoding="utf-8")
    sha = _sha(vault / NODE_REL)
    r = _run_writer(vault, _payload())
    assert r.returncode != 0, "带终止 LF 的坏末行必须 fail-closed (旧实现 rc=0 当截断容忍)"
    assert "完整写入的损坏行" in r.stderr, r.stderr
    assert _sha(vault / NODE_REL) == sha, "零写节点"
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 2, "零写账本"
    # ②同一坏行去掉终止 LF → 仍按截断自愈容忍 (对照, 防本门变成「坏行恒拒」)
    ledger.write_text(json.dumps(good, ensure_ascii=False) + "\n" + bad, encoding="utf-8")
    r2 = _run_writer(vault, _payload())
    assert r2.returncode == 0, "无 LF 的坏末行仍应按截断隔离: " + r2.stdout + r2.stderr
    assert "截断尾行" in r2.stdout
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 3 and json.loads(lines[2])["event_id"] == "quiz:" + EID


# ── 门㉜ R6 (MEDIUM): 身份键归属与 candidate 构造裁决必须回写冻结 schema ──


def test_r6_schema_declares_identity_key_integrity_owner():
    """round-3 MEDIUM: 门㉕锁定的「两个身份键排除出 envelope 等价面」此前只
    活在实现与测试里, 契约 §6.2 原文仍只排除 recorded_at — 实现与契约两个
    口径。本门锁定回写: 归属方 (validator golden manifest 绑定门) 与 candidate
    独立构造的禁令都必须在冻结契约里可查。"""
    doc = (WT / "docs" / "learning-events-schema-v1.md").read_text(encoding="utf-8")
    seg = doc[doc.index("duplicate 命中后的状态推进门") : doc.index("**A5 整秒精度")]
    for needle in (
        "fsrs_library_version",
        "fsrs_params_hash",
        "排除出 envelope 等价面",
        "golden manifest 绑定门",
        "candidate 必须独立字面构造",
        "多一键、少一键或值不同",
    ):
        assert needle in seg, f"§6.2 duplicate 门段落缺「{needle}」— 契约未同步实现裁决"
    # A5 段必须写明 A2 消费侧的机械强制 (R2 的契约面)
    a5 = doc[doc.index("**A5 整秒精度") : doc.index("**三态语义")]
    assert "A2 消费侧同样机械强制" in a5 and "禁止消费时顺手归一化" in a5, a5[:400]
    # A4.5 短写段必须写明「截断 vs 完整损坏」的 LF 判据 (R7 的契约面)
    assert "可容忍的截断 vs 完整损坏" in doc and "不以 LF 结尾" in doc
    # 三态语义段必须写明 out_of_order 的**写点侧** fail-closed 口径 (N1 的契约面)
    # —— proof 侧是「报违规仍计入」, 在线写路径不能照搬, 两个口径必须分开写清楚。
    oo = doc[doc.index("**`out_of_order` 字段冻结") : doc.index("**迟到事件的入账通道**")]
    for needle in ("写点（在线 A2）侧同款语义门", "fail-closed", "被伪装成乱序的真实后继", "唯一合法值布尔 `true`"):
        assert needle in oo, f"§6.2 三态语义段缺「{needle}」— 写点侧口径未回写契约"


# ── 门㉝ write-ahead 六格状态机逐格闭合 (卡文标题判据) ──
# 分诊的自由度是 (dup 有无) × (f1) × (fsrs_applied); fsrs_applied 只在 dup=有
# 时有定义 ⇒ 2 + 4 = 6 格 (Codex round-3 §六格状态机)。round-3 判定 3 格 FAIL
# (历史 attempt 误拒 / 小数秒重复推进 / 额外键跳过 A2 且字节不等) + 1 格
# PARTIAL (foreign pending 输入门不完整)。本门逐格构造并断言终态。


def _strip_calibration(vault: Path) -> None:
    """删掉 frontmatter 的 calibration_log 块 (制造 f1=False 而其余副作用已在)。"""
    text = (vault / NODE_REL).read_text(encoding="utf-8")
    head, fm, body = text.split("---\n", 2)
    lines, out, skipping = fm.split("\n"), [], False
    for ln in lines:
        if ln.startswith("calibration_log:"):
            skipping = True
            continue
        if skipping and (ln.startswith("  ") or ln == ""):
            continue
        skipping = False
        out.append(ln)
    # calibration_log 通常是 frontmatter 最后一个键, 其块尾的空串元素会被上面的
    # skipping 分支吃掉 ⇒ 直接 join 会丢掉收尾换行、把 `---` 粘到末行上。
    new_fm = "\n".join(out).rstrip("\n") + "\n"
    (vault / NODE_REL).write_text(head + "---\n" + new_fm + "---\n" + body, encoding="utf-8")


def test_six_cell_state_machine_closed(vault):
    # ── 格1 dup=None, f1=F: 正常新写 (A2 先把 foreign pending 重放至空)
    foreign = _review_row(event_id="quiz:板A#q1")
    _write_ledger(vault, foreign)
    r1 = _run_writer_settled(vault, _payload(ts="2026-08-02T10:00:00Z"))
    assert r1.returncode == 0, r1.stdout + r1.stderr
    assert "A2 重放已应用" in r1.stdout, "格1: foreign pending 必须在新写前重放"
    assert "恢复已落定" in r1.stderr, "格1: 恢复必须先独立落盘再要求重跑（两阶段）"
    assert len(_ledger_lines(vault)) == 2 and _fm_fields(vault)["fsrs_last_review"] == "2026-08-02T10:00:00Z"

    # ── 格2 dup=None, f1=T: 旧写序孤儿 (frontmatter 已应用而账本无该事件) → 整体 no-op
    _write_ledger(vault, foreign)  # 抹掉本次事件行, calibration 仍在 frontmatter
    sha_before = _sha(vault / NODE_REL)
    r2 = _run_writer(vault, _payload(ts="2026-09-01T08:00:00Z"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "旧写序" in r2.stdout and "不补录" in r2.stdout, r2.stdout
    assert _sha(vault / NODE_REL) == sha_before and len(_ledger_lines(vault)) == 1, "格2: 必须零改动"

    # ── 格3 dup=有, f1=T, applied=T: 完整成功后重放 → envelope 通过 + no-op
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload()).returncode == 0
    sha_full = _sha(vault / NODE_REL)
    r3 = _run_writer(vault, _payload(ts="2026-09-01T08:30:00Z"))
    assert r3.returncode == 0 and "幂等跳过" in r3.stdout, r3.stdout + r3.stderr
    assert _sha(vault / NODE_REL) == sha_full and len(_ledger_lines(vault)) == 1

    # ── 格4 dup=有, f1=F, applied=T: FSRS 已被吸收但校准缺失 → 停下人工裁定
    _strip_calibration(vault)
    sha_stripped = _sha(vault / NODE_REL)
    r4 = _run_writer(vault, _payload(ts="2026-09-01T09:00:00Z"))
    assert r4.returncode != 0, "格4: 顺序错乱无机械判据, 必须 fail-closed"
    assert "缺校准记录" in r4.stderr and "人工核对" in r4.stderr, r4.stderr
    assert _sha(vault / NODE_REL) == sha_stripped and len(_ledger_lines(vault)) == 1, "格4: 零写"

    # ── 格5 dup=有, f1=T, applied=F: degraded 遗留 → 只补 FSRS, 不再吃 EMA
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload(), env_extra={"FSRS_BRIDGE_REEXEC": "1"}).returncode == 0
    assert not _fm_fields(vault), "格5 前置: degraded 后 W 未推进"
    ema_before = {
        k: re.search(rf"^{k}:.*", _fm(vault), re.M).group(0)
        for k in ("mastery_score", "mastery_a", "mastery_b", "attempt_count")
    }
    r5 = _run_writer(vault, _payload(ts="2026-09-01T09:30:00Z"))
    assert r5.returncode == 0 and "degraded 遗留" in r5.stdout, r5.stdout + r5.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == TS1, "格5: FSRS 必须补齐"
    for k, v in ema_before.items():
        assert re.search(rf"^{k}:.*", _fm(vault), re.M).group(0) == v, f"格5: {k} 不得二次吸收"
    assert len(_ledger_lines(vault)) == 1

    # ── 格6 dup=有, f1=F, applied=F: 崩溃窗口① → 全套补齐且与直接应用字节相同
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload()).returncode == 0
    golden = (vault / NODE_REL).read_bytes()
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    r6 = _run_writer(vault, _payload(ts="2026-09-01T10:00:00Z"))
    assert r6.returncode == 0 and "崩溃窗口" in r6.stdout, r6.stdout + r6.stderr
    assert (vault / NODE_REL).read_bytes() == golden, "格6: 恢复产物必须与直接应用逐字节相同"
    assert len(_ledger_lines(vault)) == 1
    assert _run_validator(vault).returncode == 0, "六格走完后账本仍须过校验器"


# ── 门㉞ round-1 后续 N1-N5：审查线索指向的五个残留面 ──
# Codex round-1 正文被内容过滤器拦下（stderr 保留完整推理标题序列），按其
# 标题线索逐条实测，5 条中 4 条复现为真缺陷 + 1 条诊断不精确。本门锁全部五条。


def test_round1_followups_n1_to_n5(vault):
    # ── N1 (BLOCKER) 被伪装成乱序的真实后继：标 out_of_order 但 review_time > W
    # 旧实现无条件排除标记行 ⇒ 该事件的 FSRS 永久丢失且 writer 照常 rc=0
    # （实测 rc=0、W 只反映本次事件、账本 2 行）。§6.2 三态语义 round-17 已冻结
    # 「标记行 review_time 必须不晚于此前适用事件的最大时刻」，本卡补进写点侧。
    late = _review_row(**{"payload.out_of_order": True, "payload.review_time": "2026-08-05T10:00:00Z"})
    late["effective_at"] = "2026-08-05T10:00:00Z"
    _write_ledger(vault, late)
    sha0 = _sha(vault / NODE_REL)
    r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r.returncode != 0, "标 out_of_order 但晚于水位线的行必须 fail-closed（否则静默丢一次评分）"
    assert "伪装成乱序的真实后继" in r.stderr, r.stderr
    assert _sha(vault / NODE_REL) == sha0 and len(_ledger_lines(vault)) == 1, "零写"
    # N1 形态门：唯一合法值是布尔 true（§6.2 冻结），false/"true" 等形态歧义
    for bad_shape in (False, "true", 1, {"v": True}):
        _write_ledger(vault, _review_row(**{"payload.out_of_order": bad_shape}))
        rb = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rb.returncode != 0, f"out_of_order={bad_shape!r} 形态非法必须拒"
        assert "形态非法" in rb.stderr, rb.stderr
    # N1 验伪：合法乱序（review_time ≤ W）必须放行且不进 pending
    (vault / "learning_events.jsonl").unlink()  # 清掉上面留下的坏形态行
    assert _run_writer(vault, _payload()).returncode == 0  # 先把 W 推到 TS1
    w_before = _fm_fields(vault)["fsrs_last_review"]
    early = _review_row(**{"payload.out_of_order": True, "payload.review_time": "2026-07-01T10:00:00Z"})
    early["effective_at"] = "2026-07-01T10:00:00Z"
    early["event_id"] = "quiz:补录旧事件"
    _write_ledger(vault, _ledger_lines(vault)[0], early)
    ro = _run_writer(vault, _payload(event_id="板C#q1", ts="2026-08-03T10:00:00Z"))
    assert ro.returncode == 0, "合法乱序行必须放行: " + ro.stdout + ro.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-03T10:00:00Z", "乱序行不得推进 W 到 07-01"
    assert w_before == TS1

    # ── N2 (HIGH) EOF 的 LF 判据必须落在**字节**上
    # 文本模式的 universal newlines 把裸 \r 读成 \n ⇒ 以裸 \r 结尾的截断文件
    # 被误判成「完整写入的损坏行」而 fail-closed（实测 rc=1）。
    v2 = vault
    (v2 / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    good = _review_row(event_id="quiz:旧板", **{"payload.review_time": "2026-07-01T10:00:00Z"})
    good["effective_at"] = "2026-07-01T10:00:00Z"
    good["node_id"] = "别的节点"
    torn = '{"event_id": "quiz:损坏行", "event_ty'
    (v2 / "learning_events.jsonl").write_bytes(
        (json.dumps(good, ensure_ascii=False) + "\n").encode("utf-8") + torn.encode("utf-8") + b"\r"
    )
    r2 = _run_writer(v2, _payload())
    assert r2.returncode == 0, "裸 \\r 结尾在字节上无 LF ⇒ 应按截断隔离: " + r2.stdout + r2.stderr
    assert "截断尾行" in r2.stdout, r2.stdout
    # 对照：同一坏行改成真正带 LF 结尾 → 仍须 fail-closed（判据没被放松）
    (v2 / "learning_events.jsonl").write_bytes(
        (json.dumps(good, ensure_ascii=False) + "\n").encode("utf-8") + torn.encode("utf-8") + b"\r\n"
    )
    r2b = _run_writer(v2, _payload(event_id="板D#q1", ts="2026-08-04T10:00:00Z"))
    assert r2b.returncode != 0 and "完整写入的损坏行" in r2b.stderr, r2b.stderr

    # ── N3 (MEDIUM) 账本行 JSON 重复键：loads 静默取最后一个，歧义不可证
    (v2 / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    row = _review_row(event_id="quiz:" + EID)
    text = json.dumps(row, ensure_ascii=False)
    dup_text = text.replace('"grade_norm": 0.75', '"grade_norm": 0.11, "grade_norm": 0.75', 1)
    assert dup_text.count('"grade_norm"') == 2, "fixture 前提：必须真有两个同名键"
    (v2 / "learning_events.jsonl").write_text(dup_text + "\n", encoding="utf-8")
    r3 = _run_writer(v2, _payload())
    assert r3.returncode != 0, "含重复键的账本行必须 fail-closed"
    assert "重复键" in r3.stderr, r3.stderr
    assert not _fm_fields(v2), "零写"

    # ── N4 (MEDIUM) 非法 UTF-8 字节：必须 clean fail-closed，不是 traceback
    (v2 / "learning_events.jsonl").write_bytes(b'{"event_id": "quiz:x"}\n\xff\xfe bad\n')
    r4 = _run_writer(v2, _payload())
    assert r4.returncode != 0
    assert "非 UTF-8 字节" in r4.stderr, r4.stderr
    assert "Traceback" not in r4.stderr, "必须是 clean fail-closed，不得抛 traceback"

    # ── N5 (MEDIUM) 多 pending 并存 → attempt 序数不可从账本边界确证
    # A2 保证单写者下至多一个 pending，故此态只可能来自外部写入。旧实现会硬算
    # 一个期望值，碰巧相等就放行 = 在不可证的基线上继续。
    (v2 / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    e1 = _review_row(event_id="quiz:板A#q1", **{"payload.review_time": "2026-08-03T10:00:00Z"})
    e1["effective_at"] = "2026-08-03T10:00:00Z"
    e2 = _review_row(
        event_id="quiz:" + EID,
        **{
            "payload.review_time": "2026-08-04T10:00:00Z",
            "payload.attempt_count": 2,
            "payload.exam_board": "检验白板/测试检验-2026-08-01-1000.md",
        },
    )
    e2["effective_at"] = "2026-08-04T10:00:00Z"
    _write_ledger(v2, e1, e2)
    r5 = _run_writer(v2, _payload())
    assert r5.returncode != 0, "多 pending 并存时必须 fail-closed，不得硬算 attempt 期望值"
    assert "A2「追加前重放至空」不变量已被破坏" in r5.stderr, r5.stderr
    assert not _fm_fields(v2), "零写"


# ── 门㉟ 自测覆盖缺口（round-2 等待期自查，6 条全部实测过）──
# 这些不是新缺陷，是**已有门没覆盖到的面**。补成门，防止后续改动把它们打破。


def test_self_audit_coverage_gaps(vault):
    import subprocess
    import unicodedata

    # ① 分层防线的另一半：门㉕ 只测「篡改身份键的值」，没测「删掉整个键」。
    # 删键后 envelope 照样放行（两键排除出等价面 = 有意），必须由 validator 兜住。
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    base = _ledger_lines(vault)[0]
    assert _run_validator(vault).returncode == 0, "基线：完整行必须过校验器"
    for key in ("fsrs_library_version", "fsrs_params_hash"):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        dropped = json.loads(json.dumps(base))
        dropped["payload"].pop(key)
        _write_ledger(vault, dropped)
        rw = _run_writer(vault, _payload())
        assert rw.returncode == 0, f"删 {key} 后 envelope 应放行（身份键不在等价面）"
        assert _fm_fields(vault), "放行则必须真的恢复了 FSRS"
        v = _run_validator(vault)
        assert v.returncode != 0, f"但删 {key} 必须被校验器拦下 —— 否则分层防线漏空"
        assert key in v.stdout, v.stdout[:300]

    # ② Unicode 归一化差异必须构成冲突。
    # ⚠️ 首版探针用汉字节点名做 NFD 变异，结果「放行」——那是**假阴性**：
    # 汉字没有分解形式，NFD(s) == s，变异根本没改字节。必须用有分解形式的字符。
    assert unicodedata.normalize("NFD", "测试节点") == "测试节点", "汉字无分解形式（本断言防后人重蹈）"
    nfc_name = "café笔记"
    assert unicodedata.normalize("NFD", nfc_name) != nfc_name, "fixture 前提：该名字必须真有分解形式"
    node2 = f"节点/{nfc_name}.md"
    (vault / node2).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    r2 = _run_writer(vault, _payload(node=node2, event_id="nfd#q1"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    base2 = _ledger_lines(vault)[0]
    (vault / node2).write_text(NODE_V0, encoding="utf-8")  # 崩溃窗口①
    nfd = json.loads(json.dumps(base2))
    nfd["node_id"] = unicodedata.normalize("NFD", nfd["node_id"])
    nfd["payload"]["concept_id"] = unicodedata.normalize("NFD", nfd["payload"]["concept_id"])
    assert nfd["node_id"] != base2["node_id"], "变异必须真的改变了字节"
    _write_ledger(vault, nfd)
    r3 = _run_writer(vault, _payload(node=node2, event_id="nfd#q1"))
    assert r3.returncode != 0 and "envelope 冲突" in r3.stderr, r3.stderr

    # ③ payload 键顺序不同**不得**构成冲突（canonical 用 sort_keys，顺序不是事实差异）
    (vault / node2).write_text(NODE_V0, encoding="utf-8")
    reordered = json.loads(json.dumps(base2))
    reordered["payload"] = dict(reversed(list(reordered["payload"].items())))
    assert list(reordered["payload"]) != list(base2["payload"]), "fixture 前提：顺序必须真的变了"
    _write_ledger(vault, reordered)
    r4 = _run_writer(vault, _payload(node=node2, event_id="nfd#q1"))
    assert r4.returncode == 0, "键顺序不是事实差异，不得误报冲突: " + r4.stderr

    # ④ attempt 序数复算成负值时必须 fail-closed（f1=T 但 attempt_count 被人手删）
    v3 = vault
    (v3 / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (v3 / "learning_events.jsonl").unlink()
    assert _run_writer(v3, _payload()).returncode == 0
    assert (
        _run_writer(v3, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z", exam_board="检验白板/板B.md")).returncode
        == 0
    )
    text = (v3 / NODE_REL).read_text(encoding="utf-8")
    (v3 / NODE_REL).write_text(re.sub(r"^attempt_count:.*\n", "", text, flags=re.M), encoding="utf-8")
    sha_before = _sha(v3 / NODE_REL)
    r5 = _run_writer(v3, _payload(ts="2026-09-01T12:00:00Z"))
    assert r5.returncode != 0, "attempt 期望值算成负数时必须 fail-closed，不得放行"
    assert _sha(v3 / NODE_REL) == sha_before, "零写"

    # ⑤ 同节点两个适用事件 review_time 完全相同 → 按行号稳定全序，两条都重放
    v4 = vault
    (v4 / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    a = _review_row(event_id="quiz:板A#q1", **{"payload.review_time": TS1})
    b = _review_row(event_id="quiz:板B#q1", **{"payload.review_time": TS1, "payload.attempt_count": 2})
    _write_ledger(v4, a, b)
    r6 = _run_writer_settled(v4, _payload(event_id="板C#q1", ts="2026-08-05T10:00:00Z"))
    assert r6.returncode == 0, r6.stdout + r6.stderr
    replayed = [ln for ln in r6.stdout.splitlines() if "A2 重放已应用" in ln]
    assert len(replayed) == 2, f"同时刻两事件都应被重放，实得 {len(replayed)}: {replayed}"
    assert "板A" in replayed[0] and "板B" in replayed[1], f"全序必须按行号稳定: {replayed}"

    # ⑥ 整秒门放行的宽松字面量必须都归一到**同一个** UTC 整秒瞬间
    # （小写 t / 空格分隔 / -00:00 都是合法 ISO 写法，语义等价，放行无害）
    sys.path.insert(0, str(WT / "backend" / "scripts"))
    try:
        from validate_learning_events import _WHOLE_SECOND_RE
    finally:
        sys.path.remove(str(WT / "backend" / "scripts"))
    from datetime import datetime, timedelta, timezone

    target = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    for lit in (
        "2026-08-01T10:00:00Z",
        "2026-08-01T10:00:00+00:00",
        "2026-08-01T10:00:00-00:00",
        "2026-08-01t10:00:00Z",
        "2026-08-01 10:00:00Z",
    ):
        assert _WHOLE_SECOND_RE.match(lit.strip()), f"{lit!r} 应过字面门"
        d = datetime.fromisoformat(lit.strip().replace("Z", "+00:00"))
        assert d.utcoffset() == timedelta(0) and d.astimezone(timezone.utc) == target, (
            f"{lit!r} 被放行但不是目标瞬间 —— 宽松字面量必须语义等价才无害"
        )
    for lit in ("2026-08-01T10:00:00.000000Z", "2026-08-01T10:00+00:00", "2026-08-01T10:00:00+00:00:00"):
        assert not _WHOLE_SECOND_RE.match(lit.strip()), f"{lit!r} 不应过字面门"


# ── 门㊱ round-2 线索复核（Codex round-2 正文同样被内容过滤器拦，按 stderr 保留的
# 推理标题逐条实测）。1 条真缺陷（R7-blank）+ 3 条「分层成立」需锁住。


def test_round2_lead_followups(vault):
    import subprocess

    # ① R7-blank（真缺陷，本卡修）：截断的判据是「**最后一个非空行**有没有终止 LF」，
    # 不是「文件末尾有没有 LF」。反例：`坏行\n   `（坏行后跟一个纯空白行、文件不以
    # LF 收尾）——旧判据看文件末尾说「无 LF ⇒ 截断」，可那个坏行后面明明还跟着东西。
    good = _review_row(event_id="quiz:旧板", **{"payload.review_time": "2026-07-01T10:00:00Z"})
    good["effective_at"] = "2026-07-01T10:00:00Z"
    good["node_id"] = "别的节点"
    G = (json.dumps(good, ensure_ascii=False) + "\n").encode("utf-8")
    BAD = b'{"event_id": "quiz:x", "event_ty'
    ledger = vault / "learning_events.jsonl"
    CASES = [
        (G + BAD, True, "坏行无 LF = 真截断"),
        (G + BAD + b"\n", False, "坏行带 LF = 完整损坏"),
        (G + BAD + b"\n   ", False, "坏行带 LF + 末尾空白行(无 LF) —— 旧判据在此失真"),
        (G + BAD + b"\n   \n", False, "坏行带 LF + 末尾空白行(带 LF)"),
        (G + BAD + b"\r\n", False, "坏行带 CRLF"),
        (G + BAD + b"   ", True, "坏行无 LF 但有尾随空格 = 仍是截断"),
        (BAD, True, "坏行是唯一行且无 LF"),
        (BAD + b"\n", False, "坏行是唯一行但带 LF"),
        (G + b"\n   \n" + BAD, True, "坏行无 LF，但它**前面**有空白行（不得误判）"),
    ]
    for i, (content, tolerate, desc) in enumerate(CASES):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        ledger.write_bytes(content)
        r = _run_writer(vault, _payload(event_id=f"blank{i}#q1", ts=f"2026-08-0{i + 1}T10:00:00Z"))
        if tolerate:
            assert r.returncode == 0, f"[{desc}] 应按截断隔离: {r.stdout}{r.stderr}"
            assert "截断尾行" in r.stdout, f"[{desc}] 应留痕: {r.stdout}"
        else:
            assert r.returncode != 0, f"[{desc}] 应 fail-closed（该行是完整落盘后损坏）"
            assert "完整写入的损坏行" in r.stderr, f"[{desc}] {r.stderr}"

    # ② 分层成立（非缺陷，锁住）：写点只重放 node_id 匹配的行，故 node_id 缺失/拼错、
    # schema_ext 非法的 review 行**不会被任何节点重放**。写点放行它们是对的（不越权），
    # 但校验器必须全部拦下——否则这些行就成了无人认领的静默丢失面。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    # ⚠️ 分两类，别混（Codex round-3 HIGH 指出前一版把违约锁成了正确）：
    #   - **缺少可用 node_id** ⇒ schema §一「路由信封冻结」的读方义务明文要求
    #     **fail-closed**：不能因为「它看起来不属于本节点」就跳过，因为恰恰
    #     无法判定归属；
    #   - node_id 拼成**别的合法字符串** / schema_ext 非法 ⇒ 写点放行是对的
    #     （不越权管别的节点的行），由校验器兜底。
    for mut, desc in (
        (lambda r: r.pop("node_id"), "node_id 缺失"),
        (lambda r: r.__setitem__("node_id", None), "node_id 为 null"),
        (lambda r: r.__setitem__("node_id", 123), "node_id 非字符串"),
    ):
        row = _review_row(event_id="quiz:孤儿", **{"payload.review_time": "2026-08-05T10:00:00Z"})
        row["effective_at"] = "2026-08-05T10:00:00Z"
        mut(row)
        _write_ledger(vault, row)
        rw = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rw.returncode != 0, f"[{desc}] 不可路由的行必须 fail-closed（§一 路由信封读方义务）"
        assert "不可路由" in rw.stderr or "路由信封" in rw.stderr, rw.stderr
        assert not _fm_fields(vault), f"[{desc}] 零写"
    for mut, desc in (
        (lambda r: r.__setitem__("node_id", "不存在的节点"), "node_id 指向别的合法名"),
        (lambda r: r["payload"].__setitem__("schema_ext", "review/2"), "schema_ext=review/2"),
        (lambda r: r["payload"].__setitem__("schema_ext", "reviews/1"), "schema_ext=reviews/1"),
    ):
        row = _review_row(event_id="quiz:孤儿", **{"payload.review_time": "2026-08-05T10:00:00Z"})
        row["effective_at"] = "2026-08-05T10:00:00Z"
        mut(row)
        _write_ledger(vault, row)
        rw = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rw.returncode == 0, f"[{desc}] 写点不该越权拒别的节点的行: {rw.stderr}"
        v = _run_validator(vault)
        assert v.returncode != 0, f"[{desc}] 必须被校验器拦下 —— 否则是无人认领的静默丢失面"
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")

    # ②b 分层成立：envelope 只比 5 个顶层键，多出来的顶层键不进比较 —— 写点放行，
    # 校验器按「v1 冻结恰好 7 键」拦下。而 recorded_at 变化被 envelope **显式排除**
    # （重试时自然变化，§6.2:183），两侧都放行，那是设计不是漏网。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload()).returncode == 0
    base_top = _ledger_lines(vault)[0]
    for key, value, validator_must_reject in (
        ("extra_top", "外部注入", True),
        ("recorded_at", "2099-01-01T00:00:00Z", False),
    ):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        row = json.loads(json.dumps(base_top))
        row[key] = value
        _write_ledger(vault, row)
        rw = _run_writer(vault, _payload())
        assert rw.returncode == 0, f"顶层 {key}: envelope 只比 5 键，写点应放行: {rw.stderr}"
        v = _run_validator(vault)
        if validator_must_reject:
            assert v.returncode != 0 and key in v.stdout, f"顶层 {key} 必须被校验器拦: {v.stdout[:200]}"
        else:
            assert v.returncode == 0, f"{key} 变化是设计内的（envelope 显式排除），不得误拦: {v.stdout[:200]}"

    # ②c 契约行为（非缺陷）：未标 out_of_order 的「迟到」事件（review_time ≤ W）
    # 一律不推进 current state —— §6.2 三态语义明写「无论它是已应用还是迟到的乱序
    # 事件，对 current state 的动作完全相同」。
    # ⚠️ 同时如实锁住一个**校验器宽松面**：契约说迟到事件应走补录通道并标
    # out_of_order，但校验器当前**不强制**。validator 本卡禁改，登记为移交事项。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload()).returncode == 0
    late = _review_row(event_id="quiz:迟到事件", **{"payload.review_time": "2026-07-01T10:00:00Z"})
    late["effective_at"] = "2026-07-01T10:00:00Z"
    _write_ledger(vault, _ledger_lines(vault)[0], late)
    rl = _run_writer(vault, _payload(event_id="板C#q1", ts="2026-08-03T10:00:00Z"))
    assert rl.returncode == 0, rl.stdout + rl.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-03T10:00:00Z", (
        "迟到事件（review_time ≤ W）不得推进 current state"
    )
    assert _run_validator(vault).returncode == 0, (
        "如实锁定：校验器当前不强制迟到事件标 out_of_order —— 本断言若某天变红，"
        "说明校验器收紧了该面，届时应同步更新本注释与移交台账，而不是简单改断言"
    )

    # ③ 分层成立（非缺陷，锁住）：rating 自洽门不会误拒任何**旧版合法写入**的行。
    # grade_norm 落盘的是 round(GN,2)，分档边界要 gn = 1/6、1/2、5/6，只有 1/2 是精确
    # 两位小数，而 1.0+3.0*0.5 == 2.5 走 `g < 2.5` 为 False ⇒ 稳定落在 3。
    sys.path.insert(0, str(VAULT_SCRIPTS))
    try:
        import fsrs_bridge as fb

        for cents in range(0, 101):
            gn = cents / 100.0
            direct = fb.rating_from_grade(gn, False)
            roundtrip = fb.rating_from_grade(float(json.loads(json.dumps(gn))), False)
            assert direct == roundtrip, f"grade_norm {gn} 经 JSON 往返后分档改变 {direct}->{roundtrip}"
        assert fb.rating_from_grade(0.5, False) == 3, "边界 gn=0.5 必须稳定落 3"
    finally:
        sys.path.remove(str(VAULT_SCRIPTS))
        sys.modules.pop("fsrs_bridge", None)

    # ④ 分层成立（非缺陷，锁住）：fixture 脚本的写入面守卫不被 symlink 劫持。
    guard_src = (WT / "backend" / "scripts" / "g32b_build_fixture.py").read_text(encoding="utf-8")
    assert "resolve()" in guard_src and "MARKER" in guard_src, "守卫必须同时有 resolve 比对与 marker 检查"
    probe = Path("/private/tmp/g32b-gate-toctou-probe")
    victim = Path("/private/tmp/g32b-gate-toctou-victim")
    for p in (probe, victim):
        if p.is_symlink():
            p.unlink()
        elif p.exists():
            subprocess.run(["rm", "-rf", str(p)], check=True)
    victim.mkdir()
    try:
        probe.symlink_to(victim, target_is_directory=True)
        assert str(probe.resolve()) != str(probe), "symlink 指向别处时 resolve() 必须不等于约定路径 —— 这正是守卫的判据"
    finally:
        if probe.is_symlink():
            probe.unlink()
        subprocess.run(["rm", "-rf", str(victim)], check=True)


# ── 门㊲ 内部对抗审查（8 个核查面并行探测 + 每条 3 票独立复现）找出的 7 条 ──
# 两轮 Codex 正文都被内容过滤器拦下后补跑的内部审查。7 条全部实测复现过。


def test_internal_audit_findings(vault):
    import unicodedata

    # ① BLOCKER：A2 重放的 pending 行必须**评分事实完整**。
    # R5 只挡住「显式 rating 与 grade_norm 不自洽」，挡不住「rating 干脆没有」——
    # 缺 rating 时 bridge 回落到推导，grade_norm 也缺时用默认 0.0 ⇒ 一次可能是
    # 「答对」的评分被当成 Rating.Again（完全忘记）静默应用（实测 rc=0、W 照常推进）。
    for bad, desc in (
        ({"payload.rating": None}, "rating=null"),
        ({"payload.rating": 3.0}, "rating 是 float"),
        ({"payload.grade_norm": 1.5}, "grade_norm 越界"),
        ({"payload.grade_norm": "0.75"}, "grade_norm 是字符串"),
    ):
        _write_ledger(vault, _review_row(event_id="quiz:板A#q1", **bad))
        r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert r.returncode != 0, f"[{desc}] 评分事实不完整的行不得被重放"
        assert len(_ledger_lines(vault)) == 1, f"[{desc}] 零写"
    # 缺键（而非 null）同样拒
    row = _review_row(event_id="quiz:板A#q1")
    row["payload"].pop("rating")
    _write_ledger(vault, row)
    assert _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z")).returncode != 0
    # 验伪：合法行照常重放
    _write_ledger(vault, _review_row(event_id="quiz:板A#q1"))
    rok = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert rok.returncode == 0 and "A2 重放已应用" in rok.stdout, rok.stdout + rok.stderr

    # ② BLOCKER：A2 重放必须同步 attempt_count，否则写点自己破坏 ordinal 回推的前提。
    # E1 崩溃 → 先答 E2 → 重放 E1 不推进 attempt ⇒ E2 以同一基数写出 attempt=1，
    # durable 变成 [1,1]；此后原样重跑 E1，ordinal 回推算出 0 而 durable 是 1 ⇒
    # 合法历史重放被误报冲突（实测复现）。attempt 与 mastery 不同：它**有事件载荷**。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload()).returncode == 0
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")  # 崩溃窗口①
    # 两阶段（恢复先落定 → 重跑写本次）；attempt 的不变量在**最终**状态上验。
    r2 = _run_writer_settled(
        vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z", exam_board="检验白板/板B.md")
    )
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "A2 重放已应用" in r2.stdout
    assert [x["payload"]["attempt_count"] for x in _ledger_lines(vault)] == [1, 2], (
        "A2 重放必须把 attempt 推到 durable 值，否则下一个事件会复用同一序数"
    )
    assert re.search(r'^attempt_count:\s*"?(\d+)"?\s*$', _fm(vault), re.M).group(1) == "2"

    # ③ BLOCKER：账本按**字节**切行再逐行 decode。
    # BOM 首行（别的编辑器存过）整文件 decode 时会让一条**完整合法**的事件行解析
    # 失败、被当截断跳过、那次评分静默丢失；而腰斩一个多字节字符恰恰是最典型的
    # 崩溃产物——整文件 decode 一失败就全盘拒，自愈路径反而对它不可达。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    row = _review_row(event_id="quiz:板A#q1")
    RJ = json.dumps(row, ensure_ascii=False).encode("utf-8")
    good = _review_row(event_id="quiz:旧板", **{"payload.review_time": "2026-07-01T10:00:00Z"})
    good["effective_at"] = "2026-07-01T10:00:00Z"
    good["node_id"] = "别的节点"
    G = json.dumps(good, ensure_ascii=False).encode("utf-8") + b"\n"
    half_cjk = '{"event_id": "quiz:损'.encode("utf-8")[:-1]  # 腰斩「损」字
    for content, expect, desc in (
        (b"\xef\xbb\xbf" + RJ, "replay", "BOM + 完整合法行（无 LF）"),
        (b"\xef\xbb\xbf" + RJ + b"\n", "replay", "BOM + 完整合法行（带 LF）"),
        (G + half_cjk, "tolerate", "腰斩 CJK 的末行（无 LF）= 真截断"),
        (G + half_cjk + b"\n", "reject", "腰斩 CJK 的末行（带 LF）= 完整损坏"),
        (b"\xff\xfe bad\n" + RJ, "reject", "首行非 UTF-8 且不是末行"),
    ):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        (vault / "learning_events.jsonl").write_bytes(content)
        # 合法行会成为 foreign pending ⇒ 走「恢复先落定」两阶段，用 settled 取最终态
        r = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        if expect == "reject":
            assert r.returncode != 0, f"[{desc}] 应 fail-closed"
        else:
            assert r.returncode == 0, f"[{desc}] 应放行: {r.stdout}{r.stderr}"
            if expect == "replay":
                assert "A2 重放已应用" in r.stdout, f"[{desc}] 合法行必须被重放，不得当截断跳过"
            else:
                assert "截断尾行" in r.stdout, f"[{desc}] 应按截断隔离: {r.stdout}"

    # ④ HIGH：适用集必须校验挂载点与身份键。只看 schema_ext + node_id 不够——
    # event_type=session_archived / node_derived、concept_id 指向别节点、
    # vault_id 指向别的 vault 的行都会被当成本节点的一次复习照常重放并推进 FSRS
    # （validator 事后判 FAIL，但拦不回已推进的水位线）。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    for bad, desc in (
        ({"event_type": "session_archived"}, "非评分事件类型"),
        ({"event_type": "node_derived"}, "派生事件类型"),
        ({"payload.concept_id": "别的节点"}, "concept_id 错位"),
        ({"payload.vault_id": "别的_vault"}, "vault_id 错位"),
    ):
        _write_ledger(vault, _review_row(event_id="quiz:板A#q1", **bad))
        r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert r.returncode != 0, f"[{desc}] 不得被当成本节点的一次复习重放"
        assert not _fm_fields(vault), f"[{desc}] 零写（尤其不得推进 W）"
    # 验伪：合法的两种评分事件类型都必须照常重放
    for etype, rating, gn in (("answer_scored", 3, 0.75), ("answer_abandoned", 1, 0.0)):
        row = _review_row(event_id="quiz:板A#q1", **{"payload.rating": rating, "payload.grade_norm": gn})
        row["event_type"] = etype
        _write_ledger(vault, row)
        rok = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rok.returncode == 0, f"[{etype}] 合法评分事件必须照常重放: {rok.stderr}"
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")

    # ⑤ HIGH：event_id 首尾空白 ⇒ 同一次评分的两种写法各算一遍（双写账本 + 双吃
    # mastery + attempt 多加一次），而 validator 看不出问题（两个不同的 id 本来合法）。
    # ⛔ 拒绝而不是静默 strip —— strip 会把上游两个本来不同的 id 撞成一个。
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload(event_id="板X#q1")).returncode == 0
    r5 = _run_writer(vault, _payload(event_id="板X#q1 ", ts="2026-08-02T10:00:00Z"))
    assert r5.returncode != 0 and "首尾含空白" in r5.stderr, r5.stderr
    assert len(_ledger_lines(vault)) == 1, "零写"

    # ⑥ MEDIUM：attempt_count 读取正则须容引号。Obsidian Properties 面板会把数值
    # 写成 "3"，原正则不匹配 ⇒ 计数被当 0、序数倒退，还把一个**已被占用的序数**
    # 写进 append-only 账本。
    (vault / NODE_REL).write_text(
        NODE_V0.replace("mastery_score: 0.5\n", 'mastery_score: 0.5\nattempt_count: "3"\n'), encoding="utf-8"
    )
    (vault / "learning_events.jsonl").unlink()
    r6 = _run_writer(vault, _payload(event_id="板Q#q1"))
    assert r6.returncode == 0, r6.stdout + r6.stderr
    assert _ledger_lines(vault)[0]["payload"]["attempt_count"] == 4, (
        "引号形态的 attempt_count 必须被承接为 3 并写出 4，而不是重置为 1"
    )

    # ⑦ MEDIUM：mastery 的业务量必须取 durable 锁定的 round(GN,2)，不是未舍入的 GN。
    # 否则「首跑 gn=0.752」与「恢复重试 gn=0.7549」被 envelope 判为同一件事
    # （两侧 GN2 都是 0.75），产出的 mastery_a 却不同。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload(grade_norm=0.752)).returncode == 0
    golden = (vault / NODE_REL).read_bytes()
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    r7 = _run_writer(vault, _payload(grade_norm=0.7549, ts="2026-09-01T10:00:00Z"))
    assert r7.returncode == 0, r7.stdout + r7.stderr
    assert (vault / NODE_REL).read_bytes() == golden, (
        "同一 durable 事件（GN2 相同）在两次不同的未舍入输入下必须产出相同的 mastery"
    )


# ── 门㊳ Codex round-3（第一份拿到正文的独立审查）的 BLOCKER/HIGH 修复 ──
# round-1/2 正文都被内容过滤器拦下；round-3 换中性化措辞后拿到 17993 字节正文，
# 判「需整改」：4 BLOCKER + 多条 HIGH。以下逐条锁住修复。


def test_round3_findings(vault):
    # ① HIGH：未知 event_version 的行不得按 v1 语义 apply。
    # §一 说 v2 出现前读方要「跳过并告警，不炸」——但那是对**别的节点**的行；
    # 本节点的未知版本行若被跳过，那次评分就静默漏算了，所以这里 fail-closed。
    row = _review_row(event_id="quiz:板A#q1")
    row["event_version"] = 2
    _write_ledger(vault, row)
    r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r.returncode != 0 and "非 v1" in r.stderr, r.stderr
    assert not _fm_fields(vault), "零写"

    # ② HIGH：effective_at 与 payload.review_time 必须是同一绝对瞬间。
    # 两者脱钩的行在 dup 路径会被 envelope 拦，但走 foreign pending 时没人管
    # （实测 writer rc=0 而 validator rc=1，两侧口径分叉）。
    bad = _review_row(event_id="quiz:板A#q1")
    bad["effective_at"] = "2026-08-01T11:00:00Z"  # payload.review_time 仍是 10:00
    _write_ledger(vault, bad)
    r2 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r2.returncode != 0 and "不是同一瞬间" in r2.stderr, r2.stderr
    # 验伪：同一瞬间的两种合法写法（Z / +00:00）不得误拒
    ok = _review_row(event_id="quiz:板A#q1")
    ok["effective_at"] = "2026-08-01T10:00:00+00:00"
    _write_ledger(vault, ok)
    rok = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert rok.returncode == 0, "同一瞬间的不同合法字面量不得误拒: " + rok.stderr

    # ③ BLOCKER：attempt_count 是 ordinal 回推与恢复的权威值，缺了/非法就无法
    # 证明「这是第几次评分」。旧实现缺键时静默跳过同步（实测 writer rc=0、
    # validator 也 rc=0，账本 attempts=[null,1]：两次评分而笔记计数只有 1）。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    for bad_att, desc in ((None, "缺失"), (0, "为 0"), (-1, "负数"), (True, "bool 伪装"), ("2", "字符串")):
        row = _review_row(event_id="quiz:板A#q1")
        if bad_att is None:
            row["payload"].pop("attempt_count")
        else:
            row["payload"]["attempt_count"] = bad_att
        _write_ledger(vault, row)
        r3 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert r3.returncode != 0, f"[attempt_count {desc}] 必须 fail-closed"
        assert "attempt_count 缺失或非法" in r3.stderr, r3.stderr

    # ④ payload 不是 object 时必须 clean fail-closed，不是裸 AttributeError
    for bad_pl in ("字符串 payload", 123, ["a"]):
        row = _review_row(event_id="quiz:板A#q1")
        row["payload"] = bad_pl
        _write_ledger(vault, row)
        r4 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert r4.returncode != 0, f"payload={bad_pl!r} 必须拒"
        assert "payload 不是 object" in r4.stderr, r4.stderr
        assert "Traceback" not in r4.stderr, "必须是 clean fail-closed"

    # ⑤ BLOCKER：恢复与新写必须分成两次原子发布。
    # 旧实现在同一次运行里既重放 foreign pending 又追加本次事件，两个后果：
    # 被重放事件的 mastery/校准无载荷可复放而永久丢失（rc=0 无信号）；
    # 「连续两次发布前崩溃」在**单进程**下就能攒出 2 条 pending，此时 attempt
    # 序数与 mastery 基线都不可证。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    a = _review_row(event_id="quiz:板A#q1", **{"payload.review_time": "2026-08-03T10:00:00Z"})
    a["effective_at"] = "2026-08-03T10:00:00Z"
    b = _review_row(
        event_id="quiz:板B#q1",
        **{"payload.review_time": "2026-08-04T10:00:00Z", "payload.attempt_count": 2},
    )
    b["effective_at"] = "2026-08-04T10:00:00Z"
    _write_ledger(vault, a, b)
    r5 = _run_writer(vault, _payload(event_id="板C#q1", ts="2026-08-05T10:00:00Z"))
    assert r5.returncode != 0, "两条 pending 时不得在同一次运行里既恢复又追加"
    assert "恢复已落定" in r5.stderr, r5.stderr
    assert len([ln for ln in r5.stdout.splitlines() if "A2 重放已应用" in ln]) == 2, "两条都要重放"
    assert "永久丢失" in r5.stdout, "被恢复事件的评分链副作用无法复放，必须如实告知"
    assert len(_ledger_lines(vault)) == 2, "第一阶段不得追加本次事件"
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-04T10:00:00Z", "恢复结果必须已落盘"
    # 第二阶段：pending 已空，本次评分在干净基线上写入
    r6 = _run_writer(vault, _payload(event_id="板C#q1", ts="2026-08-05T10:00:00Z"))
    assert r6.returncode == 0, r6.stdout + r6.stderr
    assert [x["payload"]["attempt_count"] for x in _ledger_lines(vault)] == [1, 2, 3]
    assert _run_validator(vault).returncode == 0
