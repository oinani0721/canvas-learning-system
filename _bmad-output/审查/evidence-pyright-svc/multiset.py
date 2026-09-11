import json,sys,collections
def load(p):
    d=json.load(open(p)); ms=collections.Counter()
    for x in d['generalDiagnostics']:
        if x['severity']!='error': continue
        f=x['file']; i=f.find('/backend/app/')
        ms[(f[i+1:] if i>=0 else f, x.get('rule','-'), x['message'])]+=1
    return ms,d['summary']['errorCount']
base,bn=load(sys.argv[1]); work,wn=load(sys.argv[2]); new=work-base; gone=base-work
print(f"base={bn} work={wn} NEW={sum(new.values())} GONE={sum(gone.values())}")
for k,c in sorted(new.items()): print("NEW",c,k)
sys.exit(1 if new else 0)
