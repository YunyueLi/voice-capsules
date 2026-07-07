#!/usr/bin/env python3
import os, shutil
R="/Users/admin/Desktop/Github/作家蒸馏"
V=os.path.join(R,"voices"); N=os.path.join(R,"原文"); IDX=os.path.join(R,"语料索引")
SLUG={'lu-xun-fiction':'鲁迅','hongloumeng':'红楼梦','lao-she-fiction':'老舍'}
WORK={'nahan':'呐喊','panghuang':'彷徨','gushixinbian':'故事新编','duanpian':'短篇小说'}
FLAT={'gutenberg','aozora'}
os.makedirs(N,exist_ok=True)

def mv(src,dst):
    if os.path.exists(dst):
        if os.path.isdir(src) and os.path.isdir(dst):
            for fn in os.listdir(src): mv(os.path.join(src,fn),os.path.join(dst,fn))
            return
        base,ext=os.path.splitext(dst); dst=base+"_dup"+ext
    shutil.move(src,dst)

moved=0
for X in sorted(os.listdir(V)):
    p=os.path.join(V,X)
    if not os.path.isdir(p): continue
    author=SLUG.get(X,X); adir=os.path.join(N,author); os.makedirs(adir,exist_ok=True)
    tx=os.path.join(p,'corpus','text')
    if os.path.isdir(tx):
        for it in sorted(os.listdir(tx)):
            ip=os.path.join(tx,it)
            if os.path.isdir(ip) and it in FLAT:
                for fn in os.listdir(ip): mv(os.path.join(ip,fn),os.path.join(adir,fn));
                moved+=1
            elif os.path.isdir(ip):
                mv(ip,os.path.join(adir,WORK.get(it,it))); moved+=1
            else:
                mv(ip,os.path.join(adir,it)); moved+=1
    raw=os.path.join(p,'corpus','raw')
    if os.path.isdir(raw): mv(raw,os.path.join(adir,'_脂批底本')); moved+=1

# 覆盖索引 -> 语料索引/
os.makedirs(IDX,exist_ok=True)
for f,new in [('_coverage.tsv','中文维基.tsv'),('_coverage_aozora.tsv','日本青空文库.tsv'),
              ('_coverage_foreign.tsv','外国维基.tsv'),('_coverage_gutenberg.tsv','英语古登堡.tsv')]:
    s=os.path.join(V,f)
    if os.path.exists(s): shutil.move(s,os.path.join(IDX,new))
shutil.rmtree(V)

# 生成总览: 每作者 文件数/字数
rows=[]
for a in sorted(os.listdir(N)):
    ad=os.path.join(N,a)
    if not os.path.isdir(ad): continue
    nf=nc=0
    for root,_,files in os.walk(ad):
        for fn in files:
            if fn.endswith('.txt'):
                try: nc+=len(open(os.path.join(root,fn),encoding='utf-8',errors='ignore').read()); nf+=1
                except: pass
    rows.append((a,nf,nc))
rows.sort(key=lambda r:-r[2])
with open(os.path.join(IDX,"总览.tsv"),"w") as f:
    f.write("作者\t文件数\t字数\n")
    for r in rows: f.write(f"{r[0]}\t{r[1]}\t{r[2]}\n")
print(f"重排完成: 移动 {moved} 项; 作者 {len(rows)}; 总文件 {sum(r[1] for r in rows)}; 总字 {sum(r[2] for r in rows)}")
print("字数前10:")
for r in rows[:10]: print(f"  {r[0]:14} {r[1]}文件 {r[2]}字")
