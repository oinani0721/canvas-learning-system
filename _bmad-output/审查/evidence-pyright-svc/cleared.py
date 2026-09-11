import json,sys,collections
def load(p):
    d=json.load(open(p)); c=collections.Counter()
    for x in d['generalDiagnostics']:
        if x['severity']!='error': continue
        f=x['file']; i=f.find('/backend/app/')
        c[(f[i+1:] if i>=0 else f, x.get('rule','-'), x['message'].split('\n')[0])]+=1
    return c
base=load(sys.argv[1]); fin=load(sys.argv[2])
gone=base-fin; new=fin-base
print("### 阶段 2 services 面：按诊断身份对照（不是编辑处数）")
print(f"base(568de82a)={sum(base.values())}  final(ccd2a4d1)={sum(fin.values())}  CLEARED={sum(gone.values())}  NEW={sum(new.values())}")
print()
byrule=collections.Counter(); byfile=collections.Counter()
for (f,r,m),n in gone.items(): byrule[r]+=n; byfile[f.split('/')[-1]]+=n
print("## 被消掉的 %d 条 按 rule" % sum(gone.values()))
for r,n in byrule.most_common(): print(f"   {n:3d}  {r}")
print("## 被消掉的 按文件")
for f,n in byfile.most_common(): print(f"   {n:3d}  {f}")
print("## NEW = 0 ✅" if not new else "## ⚠️ NEW 非空: %s" % list(new.items()))
