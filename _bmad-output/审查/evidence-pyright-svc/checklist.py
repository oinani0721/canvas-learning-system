import json,sys
SHARED={"review_service.py","mastery_engine.py","mastery_store.py","multimodal_service.py","difficulty_matcher.py","canvas_service.py","calibration_tracker.py","event_bus.py","mastery_fusion.py","agent_service.py"}
PEND=lambda d:(d.get("rule")=="reportMissingImports" and ("agentic_rag" in d["message"] or "memory.temporal" in d["message"])) or (d.get("rule")=="reportCallIssue" and "missing for parameter" in d["message"])
d=json.load(open(sys.argv[1]))
errs=[x for x in d["generalDiagnostics"] if x["severity"]=="error"]
rows=[]
for x in errs:
    f=x["file"].rsplit("/",1)[-1]
    if f not in SHARED: continue
    rows.append((f,x["range"]["start"]["line"]+1,x["range"]["start"]["character"]+1,x.get("rule","-"),"PEND0" if PEND(x) else "MINE",x["message"].replace("\n"," | ")))
rows.sort()
for r in rows: print(f"{r[0]}:{r[1]}:{r[2]} [{r[4]}] {r[3]} :: {r[5][:150]}")
print("TOTAL",len(rows),"MINE",sum(1 for r in rows if r[4]=="MINE"),"PEND0",sum(1 for r in rows if r[4]=="PEND0"))
