import json,sys,collections
SHARED={"review_service.py","mastery_engine.py","mastery_store.py","multimodal_service.py","difficulty_matcher.py","canvas_service.py","calibration_tracker.py","event_bus.py","mastery_fusion.py","agent_service.py"}
PHASE0_PENDING=lambda d: (d.get("rule")=="reportMissingImports" and ("agentic_rag" in d["message"] or "memory.temporal" in d["message"])) or (d.get("rule")=="reportCallIssue" and "missing for parameter" in d["message"])
d=json.load(open(sys.argv[1])); errs=[x for x in d["generalDiagnostics"] if x["severity"]=="error"]
by_rule=collections.Counter(x.get("rule","-") for x in errs); by_file=collections.Counter(x["file"].split("/backend/app/")[-1] for x in errs)
shared=[x for x in errs if x["file"].rsplit("/",1)[-1] in SHARED]; non=[x for x in errs if x["file"].rsplit("/",1)[-1] not in SHARED]
pend=[x for x in non if PHASE0_PENDING(x)]
sp=[x for x in shared if PHASE0_PENDING(x)]
print("total",len(errs),"shared",len(shared),"non-shared",len(non),"non-shared-excluding-phase0-pending",len(non)-len(pend))
print("shared-phase0-pending",len(sp),"non-shared-phase0-pending",len(pend))
for r,c in by_rule.most_common(): print("rule",c,r)
for f,c in by_file.most_common(): print("file",c,f)
