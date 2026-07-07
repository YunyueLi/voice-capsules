#!/usr/bin/env python3
# Project Gutenberg: 名录英语作者 -> 匹配PG目录(每作者条目精确) -> 拉英文公版全文
import csv, os, re, urllib.request, time, html as _html
from concurrent.futures import ThreadPoolExecutor
UA="voice-capsules-corpus/0.1 (research; yunyue.li@mirofish.ai)"
CAT="/private/tmp/claude-501/-Users-admin-Desktop-Github-----/f3cfb99f-9da1-4794-8640-8a06ab71ee9b/scratchpad/pg_catalog.csv"
VOICES="/Users/admin/Desktop/Github/作家蒸馏/原文"
IDX="/Users/admin/Desktop/Github/作家蒸馏/语料索引"
ONLY=os.environ.get("ONLY","")
CAP=80

def toks(s): return set(re.findall(r'[a-z]+',s.lower()))
# 名录英语作者
region=None; eng=[]
for ln in open('/Users/admin/Desktop/Github/作家蒸馏/03-作家总名录.md',encoding='utf-8'):
    s=ln.rstrip('\n'); m=re.match(r'^### (.+)',s)
    if m: region=m.group(1); continue
    if not s.startswith('|'): continue
    c=[x.strip() for x in s.strip('|').split('|')]
    if len(c)!=13 or c[0]=='名' or set(c[0])<=set('-: '): continue
    if region and region.startswith('英语') and c[1].strip(): eng.append((c[0],c[1]))
if ONLY: eng=[(n,y) for n,y in eng if n in ONLY.split(",")]
rt=[(n,y,toks(y)) for n,y in eng]

def match_author(authors_field):
    for sub in authors_field.split(';'):          # 逐个作者条目
        at=toks(sub)
        for n,y,tk in rt:
            if tk and tk<=at and len(tk)>=2: return n
    return None

jobs={}
with open(CAT,encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row.get('Language','')!='en' or row.get('Type','')!='Text': continue
        who=match_author(row.get('Authors',''))
        if who: jobs.setdefault(who,[]).append((row['Text#'],row.get('Title','')[:80]))

def strip_pg(txt):
    a=re.search(r'\*\*\* *START OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*',txt,re.I)
    b=re.search(r'\*\*\* *END OF (?:THE|THIS) PROJECT GUTENBERG',txt,re.I)
    s=txt[a.end():b.start()] if a and b else txt
    s=re.sub(r'(?im)^\s*produced by .*$','',s)
    return "\n".join(l.rstrip() for l in s.splitlines() if l.strip())
def _get(url):
    for a in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=50).read()
        except urllib.error.HTTPError as e:
            if e.code==404: return None
            time.sleep(2*(a+1))
        except Exception: time.sleep(2*(a+1))
    return None
def sane(s): return re.sub(r'[ /()（）《》\[\]|:*?"<>]','_',s).strip('_')[:60] or 'x'

log=open(os.path.join(VOICES,"_build_gutenberg_log.txt"),"w")
def emit(m): print(m); log.write(m+"\n"); log.flush()
emit(f"PG匹配作者 {len(jobs)}; 书目合计 {sum(len(v) for v in jobs.values())}\n")
cov=[]
for who,books in jobs.items():
    books=books[:CAP]
    d=os.path.join(VOICES,sane(who)); os.makedirs(d,exist_ok=True)
    def dl(bt):
        tid,title=bt
        fp=os.path.join(d,f"{tid}_{sane(title)}.txt")
        if os.path.exists(fp) and os.path.getsize(fp)>200: return os.path.getsize(fp)
        b=_get(f"https://www.gutenberg.org/cache/epub/{tid}/pg{tid}.txt.utf8") or _get(f"https://www.gutenberg.org/cache/epub/{tid}/pg{tid}.txt")
        if not b: return 0
        body=strip_pg(b.decode('utf-8','ignore'))
        if len(body)<200: return 0
        open(os.path.join(d,f"{tid}_{sane(title)}.txt"),"w").write(body); return len(body)
    with ThreadPoolExecutor(max_workers=8) as ex:
        lens=list(ex.map(dl,books))
    tp=sum(1 for x in lens if x); tc=sum(lens)
    cov.append((who,len(books),tp,tc)); emit(f"{who:18} 书{len(books):3} 存{tp:3} 字{tc:>9}")
os.makedirs(IDX,exist_ok=True)
with open(os.path.join(IDX,"英语古登堡.tsv"),"w") as f:
    f.write("作者\t书目\t已存\t字数\n")
    for r in cov: f.write("\t".join(str(x) for x in r)+"\n")
emit(f"\n完成: {sum(r[2] for r in cov)} 本入库, {sum(r[3] for r in cov)} 字")
log.close()
