1. 引用 46 个具体文件名，缺失 = ['consumers-after-20260917T094921.txt', 'fixpoint-green-20260917T094921.txt', 'fixpoint-red-20260917T094921.txt', 'green-63-28-20260917T094921.txt', 'negctl-anchors-20260917T094921.txt', 'probe-isolation-boundaries-20260917T094921.txt', 'ruff-r3fix-20260917T094921.txt', 'verify-r3-findings-20260917T094921.txt']
2. 尖括号占位 = （无）
3. 省略号引用 = （无）

验伪锚（三条判据各自必须能看见问题）：
  1) 不存在的名字会被判 missing = True
  2) 占位正则对合成的占位样本有命中 = True
  3) 省略号正则对合成的省略号样本有命中 = True

README-SELFCHECK: FAIL
