#!/bin/zsh
# G3-4 负验证 v4 (Codex round-3 整改: 修 v3 三处证据缺陷 —
#   ① 版本探针转义错误导致存档记录 SyntaxError;
#   ② 脚本不校验预期失败, 变体没红也 exit 0;
#   ③ 部分 mutation 命令被 echo 成断裂两行)
# 并补 round-3 点名的三个新变体 (N10 前缀时刻伪装 / N11 retention 重定向 /
# N12 expected 类型伪装)。
#
# 用法: 在 <worktree>/backend 下执行  zsh ../_bmad-output/审查/g3-4-evidence/negverify_v4.sh
# 退出码: 0 = 全部变体按预期红/绿; 1 = 任一变体判定不符预期 (证据无效)。
set -u
GATE=".venv/bin/python -m pytest tests/regression/test_fsrs_golden_vectors.py -q"
RESTORE=".venv/bin/python scripts/generate_fsrs_golden_vectors.py"
FAILURES=0

gate_failed_tests() { eval "$GATE" 2>&1 | grep -E "^FAILED" | sed 's/.*:://' | sort; }
gate_summary() { eval "$GATE" 2>&1 | grep -E "passed|failed" | tail -1; }

# expect_gates <期望红的门数> <期望红的门名(空格分隔, 可为 "-" 表示不校验名单)>
expect_gates() {
  local want_n="$1"; shift
  local want_names="$*"
  local names; names=$(gate_failed_tests | tr '\n' ' ' | sed 's/ $//')
  local n; n=$(gate_failed_tests | grep -c . || true)
  echo "  gate summary : $(gate_summary)"
  echo "  failed gates : ${names:-<none>}"
  if [ "$n" != "$want_n" ]; then
    echo "  ❌ 预期 $want_n 门红, 实为 $n"; FAILURES=$((FAILURES+1)); return
  fi
  if [ "$want_names" != "-" ] && [ "$names" != "$want_names" ]; then
    echo "  ❌ 预期门名 [$want_names], 实为 [$names]"; FAILURES=$((FAILURES+1)); return
  fi
  echo "  ✅ 判定符合预期"
}

mutate() { echo "  mutation:"; printf '%s\n' "$1" | sed 's/^/    | /'; .venv/bin/python -c "$1"; }
restore() { echo "  restore : $RESTORE"; eval "$RESTORE" >/dev/null; }

echo "== G3-4 负验证存档 v4 (Codex round-3 整改) =="
echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "git HEAD: $(git -C .. rev-parse HEAD) (branch $(git -C .. rev-parse --abbrev-ref HEAD))"
echo "python: $(.venv/bin/python -V)"
echo "fsrs installed: $(.venv/bin/python -c 'import importlib.metadata as m; print(m.version("fsrs"))')"
echo "test sha256:     $(shasum -a 256 tests/regression/test_fsrs_golden_vectors.py | cut -d' ' -f1)"
echo "manifest sha256: $(shasum -a 256 tests/regression/fsrs_golden_manifest.json | cut -d' ' -f1)"
echo "vectors sha256:  $(shasum -a 256 tests/regression/fsrs_golden_vectors.json | cut -d' ' -f1)"
echo "gate command: $GATE"
echo "变体总数: 1 基线 (N0) + 12 负例 (N1-N12); 每例校验预期红门数与门名"
echo "注: N5/N11 自 round-6 起各触发 2 门 (曲线门加强后一并覆盖), 预期值已同步"
echo

echo "--- [N0] 基线 → 期望 0 门红 ---"; expect_gates 0 -; echo

echo "--- [N1] manifest params_hash 首字符篡改 ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_manifest.json");m=json.loads(p.read_text());h=m["params_hash"]
m["params_hash"]=("0" if h[0]!="0" else "1")+h[1:]
p.write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
expect_gates 1 test_params_hash_integrity; restore; echo

echo "--- [N2] 向量 stability +0.5 ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_vectors.json");d=json.loads(p.read_text())
d["vectors"][0]["expected"]["stability"]+=0.5
p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
expect_gates 1 test_all_golden_vectors_replay_exact; restore; echo

echo "--- [N3] 仅改 manifest library_version=6.4.0 (GOLDEN 不动) ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_manifest.json");m=json.loads(p.read_text())
m["library_version"]="6.4.0"
p.write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
expect_gates 3 test_installed_version_matches_frozen_manifest test_params_hash_integrity test_requirements_pin_exact_version
restore; echo

echo "--- [N4] 末向量替换为首向量副本 (重复+缺格) ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_vectors.json");d=json.loads(p.read_text())
d["vectors"][-1]=d["vectors"][0]
p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
expect_gates 1 test_matrix_structure_frozen; restore; echo

echo "--- [N5] retrievability.at 清空 (round-6 起曲线门也覆盖 → 2 门红) ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_vectors.json");d=json.loads(p.read_text())
d["retrievability"]["at"]=[]
p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
expect_gates 2 test_matrix_structure_frozen test_retrievability_curve_matches_golden; restore; echo

echo "--- [N6] 容差放宽 float_rel=1e-3 ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_manifest.json");m=json.loads(p.read_text())
m["comparison_tolerance"]["float_rel"]=1e-3
p.write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
expect_gates 1 test_tolerance_ceiling_locked; restore; echo

echo "--- [N7] state_before_final_review=999 ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_vectors.json");d=json.loads(p.read_text())
d["vectors"][0]["state_before_final_review"]=999
p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
expect_gates 2 test_all_golden_vectors_replay_exact test_matrix_structure_frozen; restore; echo

echo "--- [N8] manifest algorithm 改任意值 ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_manifest.json");m=json.loads(p.read_text())
m["algorithm"]="arbitrary"
p.write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
expect_gates 1 test_manifest_metadata_frozen; restore; echo

echo "--- [N9] requirements 改 fsrs==6.3.1.post1 ---"
echo "  mutation: sed -i '' 's/^fsrs==6.3.1\$/fsrs==6.3.1.post1/' requirements.txt"
sed -i '' 's/^fsrs==6.3.1$/fsrs==6.3.1.post1/' requirements.txt
expect_gates 1 test_requirements_pin_exact_version
echo "  restore : sed -i '' 's/^fsrs==6.3.1.post1\$/fsrs==6.3.1/' requirements.txt"
sed -i '' 's/^fsrs==6.3.1.post1$/fsrs==6.3.1/' requirements.txt
echo

echo "--- [N10·round-3] 前缀时刻伪装: review_ontime__good 第二步 00:10→00:05, expected 由真实库自洽重算 ---"
mutate 'import json,pathlib
from datetime import datetime,timedelta
from fsrs import Card,Rating,Scheduler
m=json.loads(pathlib.Path("tests/regression/fsrs_golden_manifest.json").read_text())
p=pathlib.Path("tests/regression/fsrs_golden_vectors.json");d=json.loads(p.read_text());cfg=m["scheduler_config"]
s=Scheduler(parameters=cfg["parameters"],desired_retention=cfg["desired_retention"],
 learning_steps=[timedelta(minutes=x) for x in cfg["learning_steps_minutes"]],
 relearning_steps=[timedelta(minutes=x) for x in cfg["relearning_steps_minutes"]],
 maximum_interval=cfg["maximum_interval"],enable_fuzzing=cfg["enable_fuzzing"])
RB={"again":Rating.Again,"hard":Rating.Hard,"good":Rating.Good,"easy":Rating.Easy}
v=[x for x in d["vectors"] if x["id"]=="review_ontime__good"][0]
v["steps"][1]["review_at"]="2026-01-01T00:05:00+00:00"
c=Card(card_id=m["card_id"],due=datetime.fromisoformat(m["base_datetime"]))
for st in v["steps"][:-1]: c,_=s.review_card(c,RB[st["rating"]],datetime.fromisoformat(st["review_at"]))
v["steps"][-1]["review_at"]=c.due.isoformat()
c,_=s.review_card(c,RB[v["steps"][-1]["rating"]],c.due)
v["expected"]={"stability":c.stability,"difficulty":c.difficulty,"due":c.due.isoformat(),
 "last_review":c.last_review.isoformat(),"state":int(c.state),"step":c.step}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
expect_gates 1 test_matrix_structure_frozen; restore; echo

echo "--- [N11·round-3] scheduler_config 重定向 0.9→0.8 自洽重算 (round-6 起曲线门也覆盖 → 2 门红) ---"
mutate 'import hashlib,json,pathlib
from datetime import datetime,timedelta
from fsrs import Card,Rating,Scheduler
MP=pathlib.Path("tests/regression/fsrs_golden_manifest.json");VP=pathlib.Path("tests/regression/fsrs_golden_vectors.json")
m=json.loads(MP.read_text());d=json.loads(VP.read_text())
m["scheduler_config"]["desired_retention"]=0.8
m["params_hash"]=hashlib.sha256(json.dumps(m["scheduler_config"],sort_keys=True,separators=(",",":")).encode()).hexdigest()
d["params_hash"]=m["params_hash"];cfg=m["scheduler_config"]
def mk(): return Scheduler(parameters=cfg["parameters"],desired_retention=cfg["desired_retention"],
 learning_steps=[timedelta(minutes=x) for x in cfg["learning_steps_minutes"]],
 relearning_steps=[timedelta(minutes=x) for x in cfg["relearning_steps_minutes"]],
 maximum_interval=cfg["maximum_interval"],enable_fuzzing=cfg["enable_fuzzing"])
RB={"again":Rating.Again,"hard":Rating.Hard,"good":Rating.Good,"easy":Rating.Easy}
base=datetime.fromisoformat(m["base_datetime"])
for v in d["vectors"]:
    s=mk();c=Card(card_id=m["card_id"],due=base);steps=[];n=len(v["steps"])
    for i,st in enumerate(v["steps"]):
        off=30 if (i==n-1 and v["scenario"]=="review_overdue_30d") else 0
        at=base if i==0 else c.due+timedelta(days=off)
        steps.append({"rating":st["rating"],"review_at":at.isoformat()})
        if i==n-1: v["state_before_final_review"]=int(c.state)
        c,_=s.review_card(c,RB[st["rating"]],at)
    v["steps"]=steps
    v["expected"]={"stability":c.stability,"difficulty":c.difficulty,"due":c.due.isoformat(),
     "last_review":c.last_review.isoformat() if c.last_review else None,"state":int(c.state),"step":c.step}
s=mk();c=Card(card_id=m["card_id"],due=base)
c,_=s.review_card(c,Rating.Good,base);c,_=s.review_card(c,Rating.Good,c.due)
d["retrievability"]["steps"]=[{"rating":"good","review_at":base.isoformat()},{"rating":"good","review_at":c.last_review.isoformat()}]
d["retrievability"]["at"]=[{"current_datetime":(c.due+timedelta(days=k)).isoformat(),
 "expected":s.get_card_retrievability(c,c.due+timedelta(days=k))} for k in (0,7,30)]
MP.write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
VP.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
expect_gates 2 test_retrievability_curve_matches_golden test_scheduler_config_non_parameter_fields_frozen; restore; echo

echo "--- [N12·round-3] expected 类型伪装 state=true (Python bool 与 1 相等) ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_vectors.json");d=json.loads(p.read_text())
d["vectors"][0]["expected"]["state"]=True
p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
expect_gates 1 test_matrix_structure_frozen; restore; echo

echo "--- 终态: 恢复后 sha256 与基线一致性 + 全绿 ---"
echo "manifest sha256: $(shasum -a 256 tests/regression/fsrs_golden_manifest.json | cut -d' ' -f1)"
echo "vectors sha256:  $(shasum -a 256 tests/regression/fsrs_golden_vectors.json | cut -d' ' -f1)"
echo "requirements fsrs 行: $(grep -n '^fsrs==' requirements.txt)"
expect_gates 0 -
echo
if [ "$FAILURES" -eq 0 ]; then
  echo "RESULT: 全部 13 个判定 (N0 基线 + N1-N12) 均符合预期"
  exit 0
else
  echo "RESULT: $FAILURES 个判定不符预期 — 本次负验证证据无效"
  exit 1
fi
