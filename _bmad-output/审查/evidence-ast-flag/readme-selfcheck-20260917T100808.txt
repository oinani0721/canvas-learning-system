1. 引用 48 个文件名（含目录前缀/空格/大小写变体），缺失 = （无）
2. 尖括号占位 = （无）
3. 省略号引用 = （无）

验伪锚（三条判据各自必须能看见问题）：
  1) 五种「不存在的引用」形态是否都被同一条提取器判 missing：
       ✓ `no-such-file-20260917.txt`
       ✓ `missing/report.txt`
       ✓ `no such.txt`
       ✓ ` no-such.txt `
       ✓ `NO-SUCH.TXT`
  2) 占位正则对合成的占位样本有命中 = True
  3) 省略号正则对合成的省略号样本有命中 = True

README-SELFCHECK: PASS
